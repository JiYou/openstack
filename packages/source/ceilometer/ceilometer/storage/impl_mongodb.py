# -*- encoding: utf-8 -*-
#
# Copyright © 2012 New Dream Network, LLC (DreamHost)
# Copyright © 2013 eNovance
#
# Author: Doug Hellmann <doug.hellmann@dreamhost.com>
#         Julien Danjou <julien@danjou.info>
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
"""MongoDB storage backend
"""

import copy
import datetime
import operator
import os
import re
import urlparse
import uuid

import bson.code
import bson.objectid
import pymongo

from ceilometer.openstack.common import log
from ceilometer.storage import base
from ceilometer.storage import models


LOG = log.getLogger(__name__)


class MongoDBStorage(base.StorageEngine):
    """Put the data into a MongoDB database

    Collections::

        - user
          - { _id: user id
              source: [ array of source ids reporting for the user ]
              }
        - project
          - { _id: project id
              source: [ array of source ids reporting for the project ]
              }
        - meter
          - the raw incoming data
        - resource
          - the metadata for resources
          - { _id: uuid of resource,
              metadata: metadata dictionaries
              user_id: uuid
              project_id: uuid
              meter: [ array of {counter_name: string, counter_type: string,
                                 counter_unit: string} ]
            }
    """

    OPTIONS = []

    def register_opts(self, conf):
        """Register any configuration options used by this engine.
        """
        conf.register_opts(self.OPTIONS)

    def get_connection(self, conf):
        """Return a Connection instance based on the configuration settings.
        """
        return Connection(conf)


def make_timestamp_range(start, end):
    """Given two possible datetimes, create the query
    document to find timestamps within that range
    using $gte for the lower bound and $lt for the
    upper bound.
    """
    ts_range = {}
    if start:
        ts_range['$gte'] = start
    if end:
        ts_range['$lt'] = end
    return ts_range


def make_query_from_filter(sample_filter, require_meter=True):
    """Return a query dictionary based on the settings in the filter.

    :param filter: SampleFilter instance
    :param require_meter: If true and the filter does not have a meter,
                          raise an error.
    """
    q = {}

    if sample_filter.user:
        q['user_id'] = sample_filter.user
    if sample_filter.project:
        q['project_id'] = sample_filter.project

    if sample_filter.meter:
        q['counter_name'] = sample_filter.meter
    elif require_meter:
        raise RuntimeError('Missing required meter specifier')

    ts_range = make_timestamp_range(sample_filter.start, sample_filter.end)
    if ts_range:
        q['timestamp'] = ts_range

    if sample_filter.resource:
        q['resource_id'] = sample_filter.resource
    if sample_filter.source:
        q['source'] = sample_filter.source

    # so the samples call metadata resource_metadata, so we convert
    # to that.
    q.update(dict(('resource_%s' % k, v)
                  for (k, v) in sample_filter.metaquery.iteritems()))
    return q


class Connection(base.Connection):
    """MongoDB connection.
    """

    _mim_instance = None

    MAP_STATS = bson.code.Code("""
    function () {
        emit('statistics', { min : this.counter_volume,
                             max : this.counter_volume,
                             sum : this.counter_volume,
                             count : NumberInt(1),
                             duration_start : this.timestamp,
                             duration_end : this.timestamp,
                             period_start : this.timestamp,
                             period_end : this.timestamp} )
    }
    """)

    MAP_STATS_PERIOD = bson.code.Code("""
    function () {
        var period = %d * 1000;
        var period_first = %d * 1000;
        var period_start = period_first
                           + (Math.floor(new Date(this.timestamp.getTime()
                                         - period_first) / period)
                              * period);
        emit(period_start,
             { min : this.counter_volume,
               max : this.counter_volume,
               sum : this.counter_volume,
               count : NumberInt(1),
               duration_start : this.timestamp,
               duration_end : this.timestamp,
               period_start : new Date(period_start),
               period_end : new Date(period_start + period) } )
    }
    """)

    REDUCE_STATS = bson.code.Code("""
    function (key, values) {
        var res = values[0];
        for ( var i=1; i<values.length; i++ ) {
            if ( values[i].min < res.min )
               res.min = values[i].min;
            if ( values[i].max > res.max )
               res.max = values[i].max;
            res.count += values[i].count;
            res.sum += values[i].sum;
            if ( values[i].duration_start < res.duration_start )
               res.duration_start = values[i].duration_start;
            if ( values[i].duration_end > res.duration_end )
               res.duration_end = values[i].duration_end;
        }
        return res;
    }
    """)

    FINALIZE_STATS = bson.code.Code("""
    function (key, value) {
        value.avg = value.sum / value.count;
        value.duration = (value.duration_end - value.duration_start) / 1000;
        value.period = NumberInt((value.period_end - value.period_start)
                                  / 1000);
        return value;
    }""")

    def __init__(self, conf):
        opts = self._parse_connection_url(conf.database.connection)
        LOG.info('connecting to MongoDB on %s:%s', opts['host'], opts['port'])

        if opts['host'] == '__test__':
            url = os.environ.get('CEILOMETER_TEST_MONGODB_URL')
            if url:
                opts = self._parse_connection_url(url)
                self.conn = pymongo.Connection(opts['host'],
                                               opts['port'],
                                               safe=True)
            else:
                # MIM will die if we have too many connections, so use a
                # Singleton
                if Connection._mim_instance is None:
                    try:
                        from ming import mim
                    except ImportError:
                        import testtools
                        raise testtools.testcase.TestSkipped('requires mim')
                    LOG.debug('Creating a new MIM Connection object')
                    Connection._mim_instance = mim.Connection()
                self.conn = Connection._mim_instance
                LOG.debug('Using MIM for test connection')
        else:
            self.conn = pymongo.Connection(opts['host'],
                                           opts['port'],
                                           safe=True)

        self.db = getattr(self.conn, opts['dbname'])
        if 'username' in opts:
            self.db.authenticate(opts['username'], opts['password'])

        # Establish indexes
        #
        # We need variations for user_id vs. project_id because of the
        # way the indexes are stored in b-trees. The user_id and
        # project_id values are usually mutually exclusive in the
        # queries, so the database won't take advantage of an index
        # including both.
        for primary in ['user_id', 'project_id']:
            self.db.resource.ensure_index([
                (primary, pymongo.ASCENDING),
                ('source', pymongo.ASCENDING),
            ], name='resource_idx')
            self.db.meter.ensure_index([
                ('resource_id', pymongo.ASCENDING),
                (primary, pymongo.ASCENDING),
                ('counter_name', pymongo.ASCENDING),
                ('timestamp', pymongo.ASCENDING),
                ('source', pymongo.ASCENDING),
            ], name='meter_idx')

    @staticmethod
    def upgrade(version=None):
        pass

    def clear(self):
        if self._mim_instance is not None:
            # Don't want to use drop_database() because
            # may end up running out of spidermonkey instances.
            # http://davisp.lighthouseapp.com/projects/26898/tickets/22
            self.db.clear()
        else:
            self.conn.drop_database(self.db)

    @staticmethod
    def _parse_connection_url(url):
        opts = {}
        result = urlparse.urlparse(url)
        opts['dbtype'] = result.scheme
        opts['dbname'] = result.path.replace('/', '')
        netloc_match = re.match(r'(?:(\w+:\w+)@)?(.*)', result.netloc)
        auth = netloc_match.group(1)
        netloc = netloc_match.group(2)
        if auth:
            opts['username'], opts['password'] = auth.split(':')
        if ':' in netloc:
            opts['host'], port = netloc.split(':')
        else:
            opts['host'] = netloc
            port = 27017
        opts['port'] = port and int(port) or 27017
        return opts

    def record_metering_data(self, data):
        """Write the data to the backend storage system.

        :param data: a dictionary such as returned by
                     ceilometer.meter.meter_message_from_counter
        """
        # Make sure we know about the user and project
        self.db.user.update(
            {'_id': data['user_id']},
            {'$addToSet': {'source': data['source'],
                           },
             },
            upsert=True,
        )
        self.db.project.update(
            {'_id': data['project_id']},
            {'$addToSet': {'source': data['source'],
                           },
             },
            upsert=True,
        )

        # Record the updated resource metadata
        self.db.resource.update(
            {'_id': data['resource_id']},
            {'$set': {'project_id': data['project_id'],
                      'user_id': data['user_id'],
                      'metadata': data['resource_metadata'],
                      'source': data['source'],
                      },
             '$addToSet': {'meter': {'counter_name': data['counter_name'],
                                     'counter_type': data['counter_type'],
                                     'counter_unit': data['counter_unit'],
                                     },
                           },
             },
            upsert=True,
        )

        # Record the raw data for the meter. Use a copy so we do not
        # modify a data structure owned by our caller (the driver adds
        # a new key '_id').
        record = copy.copy(data)
        self.db.meter.insert(record)

    def get_users(self, source=None):
        """Return an iterable of user id strings.

        :param source: Optional source filter.
        """
        q = {}
        if source is not None:
            q['source'] = source
        return sorted(self.db.user.find(q).distinct('_id'))

    def get_projects(self, source=None):
        """Return an iterable of project id strings.

        :param source: Optional source filter.
        """
        q = {}
        if source is not None:
            q['source'] = source
        return sorted(self.db.project.find(q).distinct('_id'))

    def get_resources(self, user=None, project=None, source=None,
                      start_timestamp=None, end_timestamp=None,
                      metaquery={}, resource=None):
        """Return an iterable of models.Resource instances

        :param user: Optional ID for user that owns the resource.
        :param project: Optional ID for project that owns the resource.
        :param source: Optional source filter.
        :param start_timestamp: Optional modified timestamp start range.
        :param end_timestamp: Optional modified timestamp end range.
        :param metaquery: Optional dict with metadata to match on.
        :param resource: Optional resource filter.
        """
        q = {}
        if user is not None:
            q['user_id'] = user
        if project is not None:
            q['project_id'] = project
        if source is not None:
            q['source'] = source
        if resource is not None:
            q['resource_id'] = resource
        # Add resource_ prefix so it matches the field in the db
        q.update(dict(('resource_' + k, v)
                      for (k, v) in metaquery.iteritems()))

        # FIXME(dhellmann): This may not perform very well,
        # but doing any better will require changing the database
        # schema and that will need more thought than I have time
        # to put into it today.
        if start_timestamp or end_timestamp:
            # Look for resources matching the above criteria and with
            # samples in the time range we care about, then change the
            # resource query to return just those resources by id.
            ts_range = make_timestamp_range(start_timestamp, end_timestamp)
            if ts_range:
                q['timestamp'] = ts_range

        # FIXME(jd): We should use self.db.meter.group() and not use the
        # resource collection, but that's not supported by MIM, so it's not
        # easily testable yet. Since it was bugged before anyway, it's still
        # better for now.
        resource_ids = self.db.meter.find(q).distinct('resource_id')
        q = {'_id': {'$in': resource_ids}}
        for resource in self.db.resource.find(q):
            yield models.Resource(
                resource_id=resource['_id'],
                project_id=resource['project_id'],
                source=resource['source'],
                user_id=resource['user_id'],
                metadata=resource['metadata'],
                meter=[
                    models.ResourceMeter(
                        counter_name=meter['counter_name'],
                        counter_type=meter['counter_type'],
                        counter_unit=meter['counter_unit'],
                    )
                    for meter in resource['meter']
                ],
            )

    def get_meters(self, user=None, project=None, resource=None, source=None,
                   metaquery={}):
        """Return an iterable of models.Meter instances

        :param user: Optional ID for user that owns the resource.
        :param project: Optional ID for project that owns the resource.
        :param resource: Optional resource filter.
        :param source: Optional source filter.
        :param metaquery: Optional dict with metadata to match on.
        """
        q = {}
        if user is not None:
            q['user_id'] = user
        if project is not None:
            q['project_id'] = project
        if resource is not None:
            q['_id'] = resource
        if source is not None:
            q['source'] = source
        q.update(metaquery)

        for r in self.db.resource.find(q):
            for r_meter in r['meter']:
                yield models.Meter(
                    name=r_meter['counter_name'],
                    type=r_meter['counter_type'],
                    # Return empty string if 'counter_unit' is not valid for
                    # backward compaitiblity.
                    unit=r_meter.get('counter_unit', ''),
                    resource_id=r['_id'],
                    project_id=r['project_id'],
                    source=r['source'],
                    user_id=r['user_id'],
                )

    def get_samples(self, sample_filter, limit=None):
        """Return an iterable of model.Sample instances.

        :param sample_filter: Filter.
        :param limit: Maximum number of results to return.
        """
        if limit == 0:
            return
        q = make_query_from_filter(sample_filter, require_meter=False)
        samples = self.db.meter.find(q).limit(limit or 0)
        for s in samples:
            # Remove the ObjectId generated by the database when
            # the sample was inserted. It is an implementation
            # detail that should not leak outside of the driver.
            del s['_id']
            yield models.Sample(**s)

    def get_meter_statistics(self, sample_filter, period=None):
        """Return an iterable of models.Statistics instance containing meter
        statistics described by the query parameters.

        The filter must have a meter value set.

        """
        q = make_query_from_filter(sample_filter)

        if period:
            map_stats = self.MAP_STATS_PERIOD % \
                (period,
                 int(sample_filter.start.strftime('%s'))
                 if sample_filter.start else 0)
        else:
            map_stats = self.MAP_STATS

        results = self.db.meter.map_reduce(
            map_stats,
            self.REDUCE_STATS,
            {'inline': 1},
            finalize=self.FINALIZE_STATS,
            query=q,
        )

        return sorted((models.Statistics(**(r['value']))
                       for r in results['results']),
                      key=operator.attrgetter('period_start'))

    def _fix_interval_min_max(self, a_min, a_max):
        if hasattr(a_min, 'valueOf') and a_min.valueOf is not None:
            # NOTE (dhellmann): HACK ALERT
            #
            # The real MongoDB server can handle Date objects and
            # the driver converts them to datetime instances
            # correctly but the in-memory implementation in MIM
            # (used by the tests) returns a spidermonkey.Object
            # representing the "value" dictionary and there
            # doesn't seem to be a way to recursively introspect
            # that object safely to convert the min and max values
            # back to datetime objects. In this method, we know
            # what type the min and max values are expected to be,
            # so it is safe to do the conversion
            # here. JavaScript's time representation uses
            # different units than Python's, so we divide to
            # convert to the right units and then create the
            # datetime instances to return.
            #
            # The issue with MIM is documented at
            # https://sourceforge.net/p/merciless/bugs/3/
            #
            a_min = datetime.datetime.fromtimestamp(
                a_min.valueOf() // 1000)
            a_max = datetime.datetime.fromtimestamp(
                a_max.valueOf() // 1000)
        return (a_min, a_max)

    def get_alarms(self, name=None, user=None,
                   project=None, enabled=True, alarm_id=None):
        """Yields a lists of alarms that match filters
        """
        q = {}
        if user is not None:
            q['user_id'] = user
        if project is not None:
            q['project_id'] = project
        if name is not None:
            q['name'] = name
        if enabled is not None:
            q['enabled'] = enabled
        if alarm_id is not None:
            q['alarm_id'] = alarm_id

        for alarm in self.db.alarm.find(q):
            a = {}
            a.update(alarm)
            del a['_id']
            yield models.Alarm(**a)

    def update_alarm(self, alarm):
        """update alarm
        """
        if alarm.alarm_id is None:
            # This is an insert, generate an id
            alarm.alarm_id = str(uuid.uuid1())
        data = alarm.as_dict()
        self.db.alarm.update(
            {'alarm_id': alarm.alarm_id},
            {'$set': data},
            upsert=True)

        stored_alarm = self.db.alarm.find({'alarm_id': alarm.alarm_id})[0]
        del stored_alarm['_id']
        return models.Alarm(**stored_alarm)

    def delete_alarm(self, alarm_id):
        """Delete a alarm
        """
        self.db.alarm.remove({'alarm_id': alarm_id})

    @staticmethod
    def record_events(events):
        """Write the events.

        :param events: a list of model.Event objects.
        """
        raise NotImplementedError('Events not implemented.')

    @staticmethod
    def get_events(event_filter):
        """Return an iterable of model.Event objects.

        :param event_filter: EventFilter instance
        """
        raise NotImplementedError('Events not implemented.')


def require_map_reduce(conn):
    """Raises SkipTest if the connection is using mim.
    """
    # NOTE(dhellmann): mim requires spidermonkey to implement the
    # map-reduce functions, so if we can't import it then just
    # skip these tests unless we aren't using mim.
    try:
        import spidermonkey  # noqa
    except BaseException:
        try:
            from ming import mim
            if hasattr(conn, "conn") and isinstance(conn.conn, mim.Connection):
                import testtools
                raise testtools.testcase.TestSkipped('requires spidermonkey')
        except ImportError:
            import testtools
            raise testtools.testcase.TestSkipped('requires mim')
