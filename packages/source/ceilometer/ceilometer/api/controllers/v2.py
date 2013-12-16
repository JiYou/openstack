# -*- encoding: utf-8 -*-
#
# Copyright © 2012 New Dream Network, LLC (DreamHost)
#
# Author: Doug Hellmann <doug.hellmann@dreamhost.com>
#         Angus Salkeld <asalkeld@redhat.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
"""Version 2 of the API.
"""

# [GET ] / -- information about this version of the API
#
# [GET   ] /resources -- list the resources
# [GET   ] /resources/<resource> -- information about the resource
# [GET   ] /meters -- list the meters
# [POST  ] /meters -- insert a new sample (and meter/resource if needed)
# [GET   ] /meters/<meter> -- list the samples for this meter
# [PUT   ] /meters/<meter> -- update the meter (not the samples)
# [DELETE] /meters/<meter> -- delete the meter and samples
#
import datetime
import inspect
import pecan
from pecan import rest

import wsme
import wsmeext.pecan as wsme_pecan
from wsme import types as wtypes

from ceilometer.openstack.common import context
from ceilometer.openstack.common import log
from ceilometer.openstack.common import timeutils
from ceilometer import counter
from ceilometer import pipeline
from ceilometer import storage
from ceilometer.api import acl


LOG = log.getLogger(__name__)


operation_kind = wtypes.Enum(str, 'lt', 'le', 'eq', 'ne', 'ge', 'gt')


class _Base(wtypes.Base):

    @classmethod
    def from_db_model(cls, m):
        return cls(**(m.as_dict()))

    @classmethod
    def from_db_and_links(cls, m, links):
        return cls(links=links, **(m.as_dict()))

    def as_dict(self, db_model):
        valid_keys = inspect.getargspec(db_model.__init__)[0]
        if 'self' in valid_keys:
            valid_keys.remove('self')

        return dict((k, getattr(self, k))
                    for k in valid_keys
                    if hasattr(self, k) and
                    getattr(self, k) != wsme.Unset)


class Link(_Base):
    """A link representation
    """

    href = wtypes.text
    "The url of a link"

    rel = wtypes.text
    "The name of a link"

    @classmethod
    def sample(cls):
        return cls(href=('http://localhost:8777/v2/meters/volume?'
                         'q.field=resource_id&'
                         'q.value=bd9431c1-8d69-4ad3-803a-8d4a6b89fd36'),
                   rel='volume'
                   )


class Query(_Base):
    """Sample query filter.
    """

    _op = None  # provide a default

    def get_op(self):
        return self._op or 'eq'

    def set_op(self, value):
        self._op = value

    field = wtypes.text
    "The name of the field to test"

    #op = wsme.wsattr(operation_kind, default='eq')
    # this ^ doesn't seem to work.
    op = wsme.wsproperty(operation_kind, get_op, set_op)
    "The comparison operator. Defaults to 'eq'."

    value = wtypes.text
    "The value to compare against the stored data"

    def __repr__(self):
        # for logging calls
        return '<Query %r %s %r>' % (self.field, self.op, self.value)

    @classmethod
    def sample(cls):
        return cls(field='resource_id',
                   op='eq',
                   value='bd9431c1-8d69-4ad3-803a-8d4a6b89fd36',
                   )


def _sanitize_query(q):
    '''Check the query to see if:
    1) the request is comming from admin - then allow full visibility
    2) non-admin - make sure that the query includes the requester's
    project.
    '''
    auth_project = acl.get_limited_to_project(pecan.request.headers)
    if auth_project:
        proj_q = [i for i in q if i.field == 'project_id']
        for i in proj_q:
            if auth_project != i.value or i.op != 'eq':
                # TODO(asalkeld) in the next version of wsme (0.5b3+)
                # activate this code to be able to return the correct
                # status code (also update api/v2/test_acl.py).
                #return wsme.api.Response([return_type()],
                #                         status_code=401)
                errstr = 'Not Authorized to access project %s %s' % (i.op,
                                                                     i.value)
                raise wsme.exc.ClientSideError(errstr)

        if not proj_q:
            # The user is restricted, but they didn't specify a project
            # so add it for them.
            q.append(Query(field='project_id',
                           op='eq',
                           value=auth_project))
    return q


def _query_to_kwargs(query, db_func):
    # TODO(dhellmann): This function needs tests of its own.
    query = _sanitize_query(query)
    valid_keys = inspect.getargspec(db_func)[0]
    if 'self' in valid_keys:
        valid_keys.remove('self')
    translation = {'user_id': 'user',
                   'project_id': 'project',
                   'resource_id': 'resource'}
    stamp = {}
    trans = {}
    metaquery = {}
    for i in query:
        if i.field == 'timestamp':
            # FIXME(dhellmann): This logic is not consistent with the
            # way the timestamps are treated inside the mongo driver
            # (the end timestamp is always tested using $lt). We
            # should just pass a single timestamp through to the
            # storage layer with the operator and let the storage
            # layer use that operator.
            if i.op in ('lt', 'le'):
                stamp['end_timestamp'] = i.value
            elif i.op in ('gt', 'ge'):
                stamp['start_timestamp'] = i.value
            else:
                LOG.warn('_query_to_kwargs ignoring %r unexpected op %r"' %
                         (i.field, i.op))
        else:
            if i.op != 'eq':
                LOG.warn('_query_to_kwargs ignoring %r unimplemented op %r' %
                         (i.field, i.op))
            elif i.field == 'search_offset':
                stamp['search_offset'] = i.value
            elif i.field.startswith('metadata.'):
                metaquery[i.field] = i.value
            else:
                trans[translation.get(i.field, i.field)] = i.value

    kwargs = {}
    if metaquery and 'metaquery' in valid_keys:
        kwargs['metaquery'] = metaquery
    if stamp:
        q_ts = _get_query_timestamps(stamp)
        if 'start' in valid_keys:
            kwargs['start'] = q_ts['query_start']
            kwargs['end'] = q_ts['query_end']
        elif 'start_timestamp' in valid_keys:
            kwargs['start_timestamp'] = q_ts['query_start']
            kwargs['end_timestamp'] = q_ts['query_end']
        else:
            raise wsme.exc.UnknownArgument('timestamp',
                                           "not valid for this resource")

    if trans:
        for k in trans:
            if k not in valid_keys:
                raise wsme.exc.UnknownArgument(i.field,
                                               "unrecognized query field")
            kwargs[k] = trans[k]

    return kwargs


def _get_query_timestamps(args={}):
    """Return any optional timestamp information in the request.

    Determine the desired range, if any, from the GET arguments. Set
    up the query range using the specified offset.

    [query_start ... start_timestamp ... end_timestamp ... query_end]

    Returns a dictionary containing:

    query_start: First timestamp to use for query
    start_timestamp: start_timestamp parameter from request
    query_end: Final timestamp to use for query
    end_timestamp: end_timestamp parameter from request
    search_offset: search_offset parameter from request

    """
    search_offset = int(args.get('search_offset', 0))

    start_timestamp = args.get('start_timestamp')
    if start_timestamp:
        start_timestamp = timeutils.parse_isotime(start_timestamp)
        start_timestamp = start_timestamp.replace(tzinfo=None)
        query_start = (start_timestamp -
                       datetime.timedelta(minutes=search_offset))
    else:
        query_start = None

    end_timestamp = args.get('end_timestamp')
    if end_timestamp:
        end_timestamp = timeutils.parse_isotime(end_timestamp)
        end_timestamp = end_timestamp.replace(tzinfo=None)
        query_end = end_timestamp + datetime.timedelta(minutes=search_offset)
    else:
        query_end = None

    return {'query_start': query_start,
            'query_end': query_end,
            'start_timestamp': start_timestamp,
            'end_timestamp': end_timestamp,
            'search_offset': search_offset,
            }


def _flatten_metadata(metadata):
    """Return flattened resource metadata without nested structures
    and with all values converted to unicode strings.
    """
    if metadata:
        return dict((k, unicode(v))
                    for k, v in metadata.iteritems()
                    if type(v) not in set([list, dict, set]))
    return {}


def _make_link(rel_name, url, type, type_arg, query=None):
    query_str = ''
    if query:
        query_str = '?q.field=%s&q.value=%s' % (query['field'],
                                                query['value'])
    return Link(href=('%s/v2/%s/%s%s') % (url, type, type_arg, query_str),
                rel=rel_name)


class Sample(_Base):
    """A single measurement for a given meter and resource.
    """

    source = wtypes.text
    "An identity source ID"

    counter_name = wtypes.text
    "The name of the meter"
    # FIXME(dhellmann): Make this meter_name?

    counter_type = wtypes.text
    "The type of the meter (see :ref:`measurements`)"
    # FIXME(dhellmann): Make this meter_type?

    counter_unit = wtypes.text
    "The unit of measure for the value in counter_volume"
    # FIXME(dhellmann): Make this meter_unit?

    counter_volume = float
    "The actual measured value"

    user_id = wtypes.text
    "The ID of the user who last triggered an update to the resource"

    project_id = wtypes.text
    "The ID of the project or tenant that owns the resource"

    resource_id = wtypes.text
    "The ID of the :class:`Resource` for which the measurements are taken"

    timestamp = datetime.datetime
    "UTC date and time when the measurement was made"

    resource_metadata = {wtypes.text: wtypes.text}
    "Arbitrary metadata associated with the resource"

    message_id = wtypes.text
    "A unique identifier for the sample"

    def __init__(self, counter_volume=None, resource_metadata={},
                 timestamp=None, **kwds):
        if counter_volume is not None:
            counter_volume = float(counter_volume)
        resource_metadata = _flatten_metadata(resource_metadata)
        # this is to make it easier for clients to pass a timestamp in
        if timestamp and isinstance(timestamp, basestring):
            timestamp = timeutils.parse_isotime(timestamp)

        super(Sample, self).__init__(counter_volume=counter_volume,
                                     resource_metadata=resource_metadata,
                                     timestamp=timestamp, **kwds)
        # Seems the mandatory option doesn't work so do it manually
        for m in ('counter_volume', 'counter_unit',
                  'counter_name', 'counter_type', 'resource_id'):
            if getattr(self, m) in (wsme.Unset, None):
                raise wsme.exc.MissingArgument(m)

        if self.resource_metadata in (wtypes.Unset, None):
            self.resource_metadata = {}

    @classmethod
    def sample(cls):
        return cls(source='openstack',
                   counter_name='instance',
                   counter_type='gauge',
                   counter_unit='instance',
                   counter_volume=1,
                   resource_id='bd9431c1-8d69-4ad3-803a-8d4a6b89fd36',
                   project_id='35b17138-b364-4e6a-a131-8f3099c5be68',
                   user_id='efd87807-12d2-4b38-9c70-5f5c2ac427ff',
                   timestamp=datetime.datetime.utcnow(),
                   resource_metadata={'name1': 'value1',
                                      'name2': 'value2'},
                   message_id='5460acce-4fd6-480d-ab18-9735ec7b1996',
                   )


class Statistics(_Base):
    """Computed statistics for a query.
    """

    min = float
    "The minimum volume seen in the data"

    max = float
    "The maximum volume seen in the data"

    avg = float
    "The average of all of the volume values seen in the data"

    sum = float
    "The total of all of the volume values seen in the data"

    count = int
    "The number of samples seen"

    duration = float
    "The difference, in minutes, between the oldest and newest timestamp"

    duration_start = datetime.datetime
    "UTC date and time of the earliest timestamp, or the query start time"

    duration_end = datetime.datetime
    "UTC date and time of the oldest timestamp, or the query end time"

    period = int
    "The difference, in seconds, between the period start and end"

    period_start = datetime.datetime
    "UTC date and time of the period start"

    period_end = datetime.datetime
    "UTC date and time of the period end"

    def __init__(self, start_timestamp=None, end_timestamp=None, **kwds):
        super(Statistics, self).__init__(**kwds)
        self._update_duration(start_timestamp, end_timestamp)

    def _update_duration(self, start_timestamp, end_timestamp):
        # "Clamp" the timestamps we return to the original time
        # range, excluding the offset.
        if (start_timestamp and
                self.duration_start and
                self.duration_start < start_timestamp):
            self.duration_start = start_timestamp
            LOG.debug('clamping min timestamp to range')
        if (end_timestamp and
                self.duration_end and
                self.duration_end > end_timestamp):
            self.duration_end = end_timestamp
            LOG.debug('clamping max timestamp to range')

        # If we got valid timestamps back, compute a duration in minutes.
        #
        # If the min > max after clamping then we know the
        # timestamps on the samples fell outside of the time
        # range we care about for the query, so treat them as
        # "invalid."
        #
        # If the timestamps are invalid, return None as a
        # sentinal indicating that there is something "funny"
        # about the range.
        if (self.duration_start and
                self.duration_end and
                self.duration_start <= self.duration_end):
            self.duration = timeutils.delta_seconds(self.duration_start,
                                                    self.duration_end)
        else:
            self.duration_start = self.duration_end = self.duration = None

    @classmethod
    def sample(cls):
        return cls(min=1,
                   max=9,
                   avg=4.5,
                   sum=45,
                   count=10,
                   duration_start=datetime.datetime(2013, 1, 4, 16, 42),
                   duration_end=datetime.datetime(2013, 1, 4, 16, 47),
                   period=7200,
                   period_start=datetime.datetime(2013, 1, 4, 16, 00),
                   period_end=datetime.datetime(2013, 1, 4, 18, 00),
                   )


class MeterController(rest.RestController):
    """Manages operations on a single meter.
    """
    _custom_actions = {
        'statistics': ['GET'],
    }

    def __init__(self, meter_id):
        pecan.request.context['meter_id'] = meter_id
        self._id = meter_id

    @wsme_pecan.wsexpose([Sample], [Query], int)
    def get_all(self, q=[], limit=None):
        """Return samples for the meter.

        :param q: Filter rules for the data to be returned.
        :param limit: Maximum number of samples to return.
        """
        if limit and limit < 0:
            raise ValueError("Limit must be positive")
        kwargs = _query_to_kwargs(q, storage.SampleFilter.__init__)
        kwargs['meter'] = self._id
        f = storage.SampleFilter(**kwargs)
        return [Sample.from_db_model(e)
                for e in pecan.request.storage_conn.get_samples(f, limit=limit)
                ]

    @wsme.validate([Sample])
    @wsme_pecan.wsexpose([Sample], body=[Sample])
    def post(self, body):
        """Post a list of new Samples to Ceilometer.

        :param body: a list of samples within the request body.
        """
        # Note:
        #  1) the above validate decorator seems to do nothing.
        #  2) the mandatory options seems to also do nothing.
        #  3) the body should already be in a list of Sample's

        def get_consistent_source():
            '''Find a source that can be applied across the sample group
            or raise InvalidInput if the sources are inconsistent.
            If all are None - use the configured counter_source
            If any sample has source set then the others must be the same
            or None.
            '''
            source = None
            for s in samples:
                if source and s.source:
                    if source != s.source:
                        raise wsme.exc.InvalidInput('source', s.source,
                                                    'can not post Samples %s' %
                                                    'with different sources')
                if s.source and not source:
                    source = s.source
            return source or pecan.request.cfg.counter_source

        samples = [Sample(**b) for b in body]
        now = timeutils.utcnow()
        auth_project = acl.get_limited_to_project(pecan.request.headers)
        source = get_consistent_source()
        for s in samples:
            if self._id != s.counter_name:
                raise wsme.exc.InvalidInput('counter_name', s.counter_name,
                                            'should be %s' % self._id)
            if auth_project and auth_project != s.project_id:
                # non admin user trying to cross post to another project_id
                auth_msg = 'can not post samples to other projects'
                raise wsme.exc.InvalidInput('project_id', s.project_id,
                                            auth_msg)

            if s.timestamp is None or s.timestamp is wsme.Unset:
                s.timestamp = now
            s.source = '%s:%s' % (s.project_id, source)

        with pipeline.PublishContext(
                context.get_admin_context(),
                source,
                pecan.request.pipeline_manager.pipelines,
        ) as publisher:
            publisher([counter.Counter(
                name=s.counter_name,
                type=s.counter_type,
                unit=s.counter_unit,
                volume=s.counter_volume,
                user_id=s.user_id,
                project_id=s.project_id,
                resource_id=s.resource_id,
                timestamp=s.timestamp.isoformat(),
                resource_metadata=s.resource_metadata) for s in samples])

        # TODO(asalkeld) this is not ideal, it would be nice if the publisher
        # returned the created sample message with message id (or at least the
        # a list of message_ids).
        return samples

    @wsme_pecan.wsexpose([Statistics], [Query], int)
    def statistics(self, q=[], period=None):
        """Computes the statistics of the samples in the time range given.

        :param q: Filter rules for the data to be returned.
        :param period: Returned result will be an array of statistics for a
                       period long of that number of seconds.
        """
        kwargs = _query_to_kwargs(q, storage.SampleFilter.__init__)
        kwargs['meter'] = self._id
        f = storage.SampleFilter(**kwargs)
        computed = pecan.request.storage_conn.get_meter_statistics(f, period)
        LOG.debug('computed value coming from %r', pecan.request.storage_conn)
        # Find the original timestamp in the query to use for clamping
        # the duration returned in the statistics.
        start = end = None
        for i in q:
            if i.field == 'timestamp' and i.op in ('lt', 'le'):
                end = timeutils.parse_isotime(i.value).replace(tzinfo=None)
            elif i.field == 'timestamp' and i.op in ('gt', 'ge'):
                start = timeutils.parse_isotime(i.value).replace(tzinfo=None)

        return [Statistics(start_timestamp=start,
                           end_timestamp=end,
                           **c.as_dict())
                for c in computed]


class Meter(_Base):
    """One category of measurements.
    """

    name = wtypes.text
    "The unique name for the meter"

    type = wtypes.Enum(str, counter.TYPE_GAUGE,
                       counter.TYPE_CUMULATIVE,
                       counter.TYPE_DELTA)
    "The meter type (see :ref:`measurements`)"

    unit = wtypes.text
    "The unit of measure"

    resource_id = wtypes.text
    "The ID of the :class:`Resource` for which the measurements are taken"

    project_id = wtypes.text
    "The ID of the project or tenant that owns the resource"

    user_id = wtypes.text
    "The ID of the user who last triggered an update to the resource"

    @classmethod
    def sample(cls):
        return cls(name='instance',
                   type='gauge',
                   unit='instance',
                   resource_id='bd9431c1-8d69-4ad3-803a-8d4a6b89fd36',
                   project_id='35b17138-b364-4e6a-a131-8f3099c5be68',
                   user_id='efd87807-12d2-4b38-9c70-5f5c2ac427ff',
                   )


class MetersController(rest.RestController):
    """Works on meters."""

    @pecan.expose()
    def _lookup(self, meter_id, *remainder):
        return MeterController(meter_id), remainder

    @wsme_pecan.wsexpose([Meter], [Query])
    def get_all(self, q=[]):
        """Return all known meters, based on the data recorded so far.

        :param q: Filter rules for the meters to be returned.
        """
        kwargs = _query_to_kwargs(q, pecan.request.storage_conn.get_meters)
        return [Meter.from_db_model(m)
                for m in pecan.request.storage_conn.get_meters(**kwargs)]


class Resource(_Base):
    """An externally defined object for which samples have been received.
    """

    resource_id = wtypes.text
    "The unique identifier for the resource"

    project_id = wtypes.text
    "The ID of the owning project or tenant"

    user_id = wtypes.text
    "The ID of the user who created the resource or updated it last"

    timestamp = datetime.datetime
    "UTC date and time of the last update to any meter for the resource"

    metadata = {wtypes.text: wtypes.text}
    "Arbitrary metadata associated with the resource"

    links = [Link]
    "A list containing a self link and associated meter links"

    def __init__(self, metadata={}, **kwds):
        metadata = _flatten_metadata(metadata)
        super(Resource, self).__init__(metadata=metadata, **kwds)

    @classmethod
    def sample(cls):
        return cls(resource_id='bd9431c1-8d69-4ad3-803a-8d4a6b89fd36',
                   project_id='35b17138-b364-4e6a-a131-8f3099c5be68',
                   user_id='efd87807-12d2-4b38-9c70-5f5c2ac427ff',
                   timestamp=datetime.datetime.utcnow(),
                   metadata={'name1': 'value1',
                             'name2': 'value2'},
                   links=[Link(href=('http://localhost:8777/v2/resources/'
                                     'bd9431c1-8d69-4ad3-803a-8d4a6b89fd36'),
                               rel='self'),
                          Link(href=('http://localhost:8777/v2/meters/volume?'
                                     'q.field=resource_id&'
                                     'q.value=bd9431c1-8d69-4ad3-803a-'
                                     '8d4a6b89fd36'),
                               rel='volume')],
                   )


class ResourcesController(rest.RestController):
    """Works on resources."""

    def _resource_links(self, resource_id):
        links = [_make_link('self', pecan.request.host_url, 'resources',
                            resource_id)]
        for meter in pecan.request.storage_conn.get_meters(resource=
                                                           resource_id):
            query = {'field': 'resource_id', 'value': resource_id}
            links.append(_make_link(meter.name, pecan.request.host_url,
                                    'meters', meter.name, query=query))
        return links

    @wsme_pecan.wsexpose(Resource, unicode)
    def get_one(self, resource_id):
        """Retrieve details about one resource.

        :param resource_id: The UUID of the resource.
        """
        authorized_project = acl.get_limited_to_project(pecan.request.headers)
        r = list(pecan.request.storage_conn.get_resources(
                 resource=resource_id, project=authorized_project))[0]
        return Resource.from_db_and_links(r,
                                          self._resource_links(resource_id))

    @wsme_pecan.wsexpose([Resource], [Query])
    def get_all(self, q=[]):
        """Retrieve definitions of all of the resources.

        :param q: Filter rules for the resources to be returned.
        """
        kwargs = _query_to_kwargs(q, pecan.request.storage_conn.get_resources)
        resources = [
            Resource.from_db_and_links(r,
                                       self._resource_links(r.resource_id))
            for r in pecan.request.storage_conn.get_resources(**kwargs)]
        return resources


class Alarm(_Base):
    """One category of measurements.
    """

    alarm_id = wtypes.text
    "The UUID of the alarm"

    name = wtypes.text
    "The name for the alarm"

    description = wtypes.text
    "The description of the alarm"

    counter_name = wtypes.text
    "The name of counter"

    project_id = wtypes.text
    "The ID of the project or tenant that owns the alarm"

    user_id = wtypes.text
    "The ID of the user who created the alarm"

    comparison_operator = wtypes.Enum(str, 'lt', 'le', 'eq', 'ne', 'ge', 'gt')
    "The comparison against the alarm threshold"

    threshold = float
    "The threshold of the alarm"

    statistic = wtypes.Enum(str, 'max', 'min', 'avg', 'sum', 'count')
    "The statistic to compare to the threshold"

    enabled = bool
    "This alarm is enabled?"

    evaluation_periods = int
    "The number of periods to evaluate the threshold"

    period = float
    "The time range in seconds over which to evaluate the threshold"

    timestamp = datetime.datetime
    "The date of the last alarm definition update"

    state = wtypes.Enum(str, 'ok', 'alarm', 'insufficient data')
    "The state offset the alarm"

    state_timestamp = datetime.datetime
    "The date of the last alarm state changed"

    ok_actions = [wtypes.text]
    "The actions to do when alarm state change to ok"

    alarm_actions = [wtypes.text]
    "The actions to do when alarm state change to alarm"

    insufficient_data_actions = [wtypes.text]
    "The actions to do when alarm state change to insufficient data"

    matching_metadata = {wtypes.text: wtypes.text}
    "The matching_metadata of the alarm"

    def __init__(self, **kwargs):
        super(Alarm, self).__init__(**kwargs)

    @classmethod
    def sample(cls):
        return cls(alarm_id=None,
                   name="SwiftObjectAlarm",
                   description="An alarm",
                   counter_name="storage.objects",
                   comparison_operator="gt",
                   threshold=200,
                   statistic="avg",
                   user_id="c96c887c216949acbdfbd8b494863567",
                   project_id="c96c887c216949acbdfbd8b494863567",
                   evaluation_periods=2,
                   period=240,
                   enabled=True,
                   timestamp=datetime.datetime.utcnow(),
                   state="ok",
                   state_timestamp=datetime.datetime.utcnow(),
                   ok_actions=["http://site:8000/ok"],
                   alarm_actions=["http://site:8000/alarm"],
                   insufficient_data_actions=["http://site:8000/nodata"],
                   matching_metadata={"key_name":
                                      "key_value"}
                   )


class AlarmsController(rest.RestController):
    """Works on alarms."""

    @wsme.validate(Alarm)
    @wsme_pecan.wsexpose(Alarm, body=Alarm, status_code=201)
    def post(self, data):
        """Create a new alarm."""
        conn = pecan.request.storage_conn

        data.user_id = pecan.request.headers.get('X-User-Id')
        data.project_id = pecan.request.headers.get('X-Project-Id')
        data.alarm_id = wsme.Unset
        data.state_timestamp = wsme.Unset
        data.timestamp = timeutils.utcnow()

        # make sure alarms are unique by name per project.
        alarms = list(conn.get_alarms(name=data.name,
                                      project=data.project_id))
        if len(alarms) > 0:
            raise wsme.exc.ClientSideError(_("Alarm with that name exists"))

        try:
            kwargs = data.as_dict(storage.models.Alarm)
            alarm_in = storage.models.Alarm(**kwargs)
        except Exception as ex:
            LOG.exception(ex)
            raise wsme.exc.ClientSideError(_("Alarm incorrect"))

        alarm = conn.update_alarm(alarm_in)
        return Alarm.from_db_model(alarm)

    @wsme.validate(Alarm)
    @wsme_pecan.wsexpose(Alarm, wtypes.text, body=Alarm)
    def put(self, alarm_id, data):
        """Modify an alarm."""
        conn = pecan.request.storage_conn
        data.state_timestamp = wsme.Unset
        data.alarm_id = alarm_id
        data.user_id = pecan.request.headers.get('X-User-Id')
        data.project_id = pecan.request.headers.get('X-Project-Id')

        alarms = list(conn.get_alarms(alarm_id=alarm_id,
                                      project=data.project_id))
        if len(alarms) < 1:
            raise wsme.exc.ClientSideError(_("Unknown alarm"))

        # merge the new values from kwargs into the current
        # alarm "alarm_in".
        alarm_in = alarms[0]
        kwargs = data.as_dict(storage.models.Alarm)
        for k, v in kwargs.iteritems():
            setattr(alarm_in, k, v)
            if k == 'state':
                alarm_in.state_timestamp = timeutils.utcnow()

        alarm = conn.update_alarm(alarm_in)
        return Alarm.from_db_model(alarm)

    @wsme_pecan.wsexpose(None, wtypes.text, status_code=204)
    def delete(self, alarm_id):
        """Delete an alarm."""
        conn = pecan.request.storage_conn
        auth_project = acl.get_limited_to_project(pecan.request.headers)
        alarms = list(conn.get_alarms(alarm_id=alarm_id,
                                      project=auth_project))
        if len(alarms) < 1:
            raise wsme.exc.ClientSideError(_("Unknown alarm"))

        conn.delete_alarm(alarm_id)

    @wsme_pecan.wsexpose(Alarm, wtypes.text)
    def get_one(self, alarm_id):
        """Return one alarm."""
        conn = pecan.request.storage_conn
        auth_project = acl.get_limited_to_project(pecan.request.headers)
        alarms = list(conn.get_alarms(alarm_id=alarm_id,
                                      project=auth_project))
        if len(alarms) < 1:
            raise wsme.exc.ClientSideError(_("Unknown alarm"))

        return Alarm.from_db_model(alarms[0])

    @wsme_pecan.wsexpose([Alarm], [Query])
    def get_all(self, q=[]):
        """Return all alarms, based on the query provided.

        :param q: Filter rules for the alarms to be returned.
        """
        kwargs = _query_to_kwargs(q,
                                  pecan.request.storage_conn.get_alarms)
        return [Alarm.from_db_model(m)
                for m in pecan.request.storage_conn.get_alarms(**kwargs)]


class V2Controller(object):
    """Version 2 API controller root."""

    resources = ResourcesController()
    meters = MetersController()
    alarms = AlarmsController()
