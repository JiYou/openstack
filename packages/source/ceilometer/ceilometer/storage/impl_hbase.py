# -*- encoding: utf-8 -*-
#
# Copyright © 2012, 2013 Dell Inc.
#
# Author: Stas Maksimov <Stanislav_M@dell.com>
# Author: Shengjie Min <Shengjie_Min@dell.com>
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
"""HBase storage backend
"""
from sets import Set
from urlparse import urlparse
import json
import hashlib
import copy
import datetime
import happybase
import os
import re

from oslo.config import cfg

from ceilometer.openstack.common import log
from ceilometer.openstack.common import timeutils
from ceilometer.storage import base
from ceilometer.storage import models

LOG = log.getLogger(__name__)


class HBaseStorage(base.StorageEngine):
    """Put the data into a HBase database

    Collections:

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
          timestamp: datetime of last update
          user_id: uuid
          project_id: uuid
          meter: [ array of {counter_name: string, counter_type: string} ]
        }
    """

    OPTIONS = [
        cfg.StrOpt('table_prefix',
                   default=None,
                   help='Database table prefix',
                   ),
    ]

    def register_opts(self, conf):
        """Register any configuration options used by this engine.
        """
        conf.register_opts(self.OPTIONS)

    @staticmethod
    def get_connection(conf):
        """Return a Connection instance based on the configuration settings.
        """
        return Connection(conf)


class Connection(base.Connection):
    """HBase connection.
    """

    def __init__(self, conf):
        """Hbase Connection Initialization"""
        opts = self._parse_connection_url(conf.database.connection)
        opts['table_prefix'] = conf.table_prefix

        if opts['host'] == '__test__':
            url = os.environ.get('CEILOMETER_TEST_HBASE_URL')
            if url:
                # Reparse URL, but from the env variable now
                opts = self._parse_connection_url(url)
            else:
                # This is a in-memory usage for unit tests
                self.conn = MConnection()
                self.project = self.conn.table(self.PROJECT_TABLE)
                self.user = self.conn.table(self.USER_TABLE)
                self.resource = self.conn.table(self.RESOURCE_TABLE)
                self.meter = self.conn.table(self.METER_TABLE)
                return

        self.conn = self._get_connection(opts)
        self.conn.open()
        self.project = self.conn.table(self.PROJECT_TABLE)
        self.user = self.conn.table(self.USER_TABLE)
        self.resource = self.conn.table(self.RESOURCE_TABLE)
        self.meter = self.conn.table(self.METER_TABLE)

    PROJECT_TABLE = "project"
    USER_TABLE = "user"
    RESOURCE_TABLE = "resource"
    METER_TABLE = "meter"

    def upgrade(self, version=None):
        self.conn.create_table(self.PROJECT_TABLE, {'f': dict()})
        self.conn.create_table(self.USER_TABLE, {'f': dict()})
        self.conn.create_table(self.RESOURCE_TABLE, {'f': dict()})
        self.conn.create_table(self.METER_TABLE, {'f': dict()})

    def clear(self):
        LOG.debug('Dropping HBase schema...')
        for table in [self.PROJECT_TABLE,
                      self.USER_TABLE,
                      self.RESOURCE_TABLE,
                      self.METER_TABLE]:
            try:
                self.conn.disable_table(table)
            except Exception:
                LOG.debug('Cannot disable table but ignoring error')
            try:
                self.conn.delete_table(table)
            except Exception:
                LOG.debug('Cannot delete table but ignoring error')

    @staticmethod
    def _get_connection(conf):
        """Return a connection to the database.

        .. note::

          The tests use a subclass to override this and return an
          in-memory connection.
        """
        LOG.debug('connecting to HBase on %s:%s', conf['host'], conf['port'])
        return happybase.Connection(host=conf['host'], port=conf['port'],
                                    table_prefix=conf['table_prefix'])

    @staticmethod
    def _parse_connection_url(url):
        """Parse connection parameters from a database url.

        .. note::

        HBase Thrift does not support authentication and there is no
        database name, so we are not looking for these in the url.
        """
        opts = {}
        result = urlparse(url)
        opts['dbtype'] = result.scheme
        if ':' in result.netloc:
            opts['host'], port = result.netloc.split(':')
        else:
            opts['host'] = result.netloc
            port = 9090
        opts['port'] = port and int(port) or 9090
        return opts

    def record_metering_data(self, data):
        """Write the data to the backend storage system.

        :param data: a dictionary such as returned by
                     ceilometer.meter.meter_message_from_counter
        """
        # Make sure we know about the user and project
        if data['user_id']:
            user = self.user.row(data['user_id'])
            sources = _load_hbase_list(user, 's')
            # Update if source is new
            if data['source'] not in sources:
                user['f:s_%s' % data['source']] = "1"
                self.user.put(data['user_id'], user)

        project = self.project.row(data['project_id'])
        sources = _load_hbase_list(project, 's')
        # Update if source is new
        if data['source'] not in sources:
            project['f:s_%s' % data['source']] = "1"
            self.project.put(data['project_id'], project)

        rts = reverse_timestamp(data['timestamp'])

        resource = self.resource.row(data['resource_id'])
        new_meter = "%s!%s!%s" % (
            data['counter_name'], data['counter_type'], data['counter_unit'])
        new_resource = {'f:resource_id': data['resource_id'],
                        'f:project_id': data['project_id'],
                        'f:user_id': data['user_id'],
                        'f:source': data["source"],
                        # store meters with prefix "m_"
                        'f:m_%s' % new_meter: "1"
                        }
        # store metadata fields with prefix "r_"
        resource_metadata = dict(('f:r_%s' % k, v)
                                 for (k, v)
                                 in data['resource_metadata'].iteritems())
        new_resource.update(resource_metadata)

        # Update if resource has new information
        if new_resource != resource:
            meters = _load_hbase_list(resource, 'm')
            if new_meter not in meters:
                new_resource['f:m_%s' % new_meter] = "1"

            self.resource.put(data['resource_id'], new_resource)

        # Rowkey consists of reversed timestamp, meter and an md5 of
        # user+resource+project for purposes of uniqueness
        m = hashlib.md5()
        m.update("%s%s%s" % (data['user_id'], data['resource_id'],
                             data['project_id']))

        # We use reverse timestamps in rowkeys as they are sorted
        # alphabetically.
        row = "%s_%d_%s" % (data['counter_name'], rts, m.hexdigest())

        # Convert timestamp to string as json.dumps won't
        ts = timeutils.strtime(data['timestamp'])

        record = {'f:timestamp': ts,
                  'f:counter_name': data['counter_name'],
                  'f:counter_type': data['counter_type'],
                  'f:counter_volume': str(data['counter_volume']),
                  'f:counter_unit': data['counter_unit'],
                  # TODO(shengjie) consider using QualifierFilter
                  # keep dimensions as column qualifier for quicker look up
                  # TODO(shengjie) extra dimensions need to be added as CQ
                  'f:user_id': data['user_id'],
                  'f:project_id': data['project_id'],
                  'f:resource_id': data['resource_id'],
                  'f:source': data['source'],
                  # add in reversed_ts here for time range scan
                  'f:rts': str(rts)
                  }
        # Don't want to be changing the original data object.
        data = copy.copy(data)
        data['timestamp'] = ts
        # Save original meter.
        record['f:message'] = json.dumps(data)
        self.meter.put(row, record)

    def get_users(self, source=None):
        """Return an iterable of user id strings.

        :param source: Optional source filter.
        """
        LOG.debug("source: %s" % source)
        scan_args = {}
        if source:
            scan_args['columns'] = ['f:s_%s' % source]
        return sorted(key for key, ignored in self.user.scan(**scan_args))

    def get_projects(self, source=None):
        """Return an iterable of project id strings.

        :param source: Optional source filter.
        """
        LOG.debug("source: %s" % source)
        scan_args = {}
        if source:
            scan_args['columns'] = ['f:s_%s' % source]
        return (key for key, ignored in self.project.scan(**scan_args))

    def get_resources(self, user=None, project=None, source=None,
                      start_timestamp=None, end_timestamp=None,
                      metaquery={}):
        """Return an iterable of models.Resource instances

        :param user: Optional ID for user that owns the resource.
        :param project: Optional ID for project that owns the resource.
        :param source: Optional source filter.
        :param start_timestamp: Optional modified timestamp start range.
        :param end_timestamp: Optional modified timestamp end range.
        :param metaquery: Optional dict with metadata to match on.
        """
        def make_resource(data):
            """Transform HBase fields to Resource model."""
            # convert HBase metadata e.g. f:r_display_name to display_name
            data['f:metadata'] = dict((k[4:], v)
                                      for k, v in data.iteritems()
                                      if k.startswith('f:r_'))

            return models.Resource(
                resource_id=data['f:resource_id'],
                project_id=data['f:project_id'],
                source=data['f:source'],
                user_id=data['f:user_id'],
                metadata=data['f:metadata'],
                meter=[
                    models.ResourceMeter(*(m[4:].split("!")))
                    for m in data
                    if m.startswith('f:m_')
                ],
            )

        q, start_row, stop_row = make_query(user=user,
                                            project=project,
                                            source=source,
                                            start=start_timestamp,
                                            end=end_timestamp,
                                            require_meter=False,
                                            query_only=False)
        LOG.debug("Query Meter table: %s" % q)
        gen = self.meter.scan(filter=q, row_start=start_row, row_stop=stop_row)

        # put all the resource_ids in a Set
        resource_ids = Set()
        for ignored, data in gen:
            resource_ids.add(data['f:resource_id'])

        # handle metaquery
        if len(metaquery) > 0:
            for ignored, data in self.resource.rows(resource_ids):
                for k, v in metaquery.iteritems():
                    # if metaquery matches, yield the resource model
                    # e.g. metaquery: metadata.display_name
                    #      equals
                    #      HBase: f:r_display_name
                    if data['f:r_' + k.split('.', 1)[1]] == v:
                        yield make_resource(data)
        else:
            for ignored, data in self.resource.rows(resource_ids):
                yield make_resource(data)

    def get_meters(self, user=None, project=None, resource=None, source=None,
                   metaquery={}):
        """Return an iterable of models.Meter instances

        :param user: Optional ID for user that owns the resource.
        :param project: Optional ID for project that owns the resource.
        :param resource: Optional resource filter.
        :param source: Optional source filter.
        :param metaquery: Optional dict with metadata to match on.
        """
        q = make_query(user=user, project=project, resource=resource,
                       source=source, require_meter=False, query_only=True)
        LOG.debug("Query Resource table: %s" % q)

        # handle metaquery
        if len(metaquery) > 0:
            meta_q = []
            for k, v in metaquery.iteritems():
                meta_q.append(
                    "SingleColumnValueFilter ('f', '%s', =, 'binary:%s')"
                    % ('r_' + k.split('.', 1)[1], v))
            meta_q = " AND ".join(meta_q)
            # join query and metaquery
            if q is not None:
                q += " AND " + meta_q
            else:
                q = meta_q   # metaquery only

        gen = self.resource.scan(filter=q)

        for ignored, data in gen:
            # Meter columns are stored like this:
            # "m_{counter_name}|{counter_type}|{counter_unit}" => "1"
            # where 'm' is a prefix (m for meter), value is always set to 1
            meter = None
            for m in data:
                if m.startswith('f:m_'):
                    meter = m
                    break
            if meter is None:
                continue
            name, type, unit = meter[4:].split("!")
            yield models.Meter(
                name=name,
                type=type,
                unit=unit,
                resource_id=data['f:resource_id'],
                project_id=data['f:project_id'],
                source=data['f:source'],
                user_id=data['f:user_id'],
            )

    def get_samples(self, sample_filter, limit=None):
        """Return an iterable of models.Sample instances.

        :param sample_filter: Filter.
        :param limit: Maximum number of results to return.
        """
        def make_sample(data):
            """Transform HBase fields to Sample model."""
            data = json.loads(data['f:message'])
            data['timestamp'] = timeutils.parse_strtime(data['timestamp'])
            return models.Sample(**data)

        q, start, stop = make_query_from_filter(sample_filter,
                                                require_meter=False)
        LOG.debug("Query Meter Table: %s" % q)

        gen = self.meter.scan(filter=q, row_start=start, row_stop=stop)

        for ignored, meter in gen:
            # TODO(shengjie) put this implementation here because it's failing
            # the test. bp hbase-meter-table-enhancement will address this
            # properly.
            # handle metaquery
            metaquery = sample_filter.metaquery
            # TODO(jd) implements using HBase capabilities
            if limit == 0:
                break
            if len(metaquery) > 0:
                # metaquery checks resource table
                resource = self.resource.row(meter['f:resource_id'])

                for k, v in metaquery.iteritems():
                    if resource['f:r_' + k.split('.', 1)[1]] != v:
                        break   # if one metaquery doesn't match, break
                else:
                    if limit:
                        limit -= 1
                    yield make_sample(meter)
            else:
                if limit:
                    limit -= 1
                yield make_sample(meter)

    def _update_meter_stats(self, stat, meter):
        """Do the stats calculation on a requested time bucket in stats dict

        :param stats: dict where aggregated stats are kept
        :param index: time bucket index in stats
        :param meter: meter record as returned from HBase
        :param start_time: query start time
        :param period: length of the time bucket
        """
        vol = int(meter['f:counter_volume'])
        ts = timeutils.parse_strtime(meter['f:timestamp'])
        stat.min = min(vol, stat.min or vol)
        stat.max = max(vol, stat.max)
        stat.sum = vol + (stat.sum or 0)
        stat.count += 1
        stat.avg = (stat.sum / float(stat.count))
        stat.duration_start = min(ts, stat.duration_start or ts)
        stat.duration_end = max(ts, stat.duration_end or ts)
        stat.duration = \
            timeutils.delta_seconds(stat.duration_start,
                                    stat.duration_end)

    def get_meter_statistics(self, sample_filter, period=None):
        """Return an iterable of models.Statistics instances containing meter
        statistics described by the query parameters.

        The filter must have a meter value set.

        .. note::

           Due to HBase limitations the aggregations are implemented
           in the driver itself, therefore this method will be quite slow
           because of all the Thrift traffic it is going to create.

        """
        q, start, stop = make_query_from_filter(sample_filter)

        meters = list(meter for (ignored, meter) in
                      self.meter.scan(filter=q,
                                      row_start=start,
                                      row_stop=stop)
                      )

        if sample_filter.start:
            start_time = sample_filter.start
        elif meters:
            start_time = timeutils.parse_strtime(meters[-1]['f:timestamp'])
        else:
            start_time = None

        if sample_filter.end:
            end_time = sample_filter.end
        elif meters:
            end_time = timeutils.parse_strtime(meters[0]['f:timestamp'])
        else:
            end_time = None

        results = []

        if not period:
            period = 0
            period_start = start_time
            period_end = end_time

        # As our HBase meters are stored as newest-first, we need to iterate
        # in the reverse order
        for meter in meters[::-1]:
            ts = timeutils.parse_strtime(meter['f:timestamp'])
            if period:
                offset = int(timeutils.delta_seconds(
                    start_time, ts) / period) * period
                period_start = start_time + datetime.timedelta(0, offset)

            if not len(results) or not results[-1].period_start == \
                    period_start:
                if period:
                    period_end = period_start + datetime.timedelta(
                        0, period)
                results.append(
                    models.Statistics(count=0,
                                      min=0,
                                      max=0,
                                      avg=0,
                                      sum=0,
                                      period=period,
                                      period_start=period_start,
                                      period_end=period_end,
                                      duration=None,
                                      duration_start=None,
                                      duration_end=None)
                )
            self._update_meter_stats(results[-1], meter)
        return results

    def get_alarms(self, name=None, user=None,
                   project=None, enabled=True, alarm_id=None):
        """Yields a lists of alarms that match filters
            raise NotImplementedError('metaquery not implemented')
        """
        raise NotImplementedError('Alarms not implemented')

    def update_alarm(self, alarm):
        """update alarm
        """
        raise NotImplementedError('Alarms not implemented')

    def delete_alarm(self, alarm_id):
        """Delete a alarm
        """
        raise NotImplementedError('Alarms not implemented')

    def record_events(self, events):
        """Write the events.

        :param events: a list of model.Event objects.
        """
        raise NotImplementedError('Events not implemented.')

    def get_events(self, event_filter):
        """Return an iterable of model.Event objects.

        :param event_filter: EventFilter instance
        """
        raise NotImplementedError('Events not implemented.')


###############
# This is a very crude version of "in-memory HBase", which implements just
# enough functionality of HappyBase API to support testing of our driver.
#
class MTable(object):
    """HappyBase.Table mock
    """
    def __init__(self, name, families):
        self.name = name
        self.families = families
        self._rows = {}

    def row(self, key):
        return self._rows.get(key, {})

    def rows(self, keys):
        return ((k, self.row(k)) for k in keys)

    def put(self, key, data):
        self._rows[key] = data

    def scan(self, filter=None, columns=[], row_start=None, row_stop=None):
        sorted_keys = sorted(self._rows)
        # copy data between row_start and row_stop into a dict
        rows = {}
        for row in sorted_keys:
            if row_start and row < row_start:
                continue
            if row_stop and row > row_stop:
                break
            rows[row] = copy.copy(self._rows[row])
        if columns:
            ret = {}
            for row in rows.keys():
                data = rows[row]
                for key in data:
                    if key in columns:
                        ret[row] = data
            rows = ret
        elif filter:
            # TODO(jdanjou): we should really parse this properly,
            # but at the moment we are only going to support AND here
            filters = filter.split('AND')
            for f in filters:
                # Extract filter name and its arguments
                g = re.search("(.*)\((.*),?\)", f)
                fname = g.group(1).strip()
                fargs = [s.strip().replace('\'', '').replace('\"', '')
                         for s in g.group(2).split(',')]
                m = getattr(self, fname)
                if callable(m):
                    # overwrite rows for filtering to take effect
                    # in case of multiple filters
                    rows = m(fargs, rows)
                else:
                    raise NotImplementedError("%s filter is not implemented, "
                                              "you may want to add it!")
        for k in sorted(rows):
            yield k, rows[k]

    @staticmethod
    def SingleColumnValueFilter(args, rows):
        """This method is called from scan() when 'SingleColumnValueFilter'
        is found in the 'filter' argument
        """
        op = args[2]
        column = "%s:%s" % (args[0], args[1])
        value = args[3]
        if value.startswith('binary:'):
            value = value[7:]
        r = {}
        for row in rows:
            data = rows[row]

            if op == '=':
                if column in data and data[column] == value:
                    r[row] = data
            elif op == '<=':
                if column in data and data[column] <= value:
                    r[row] = data
            elif op == '>=':
                if column in data and data[column] >= value:
                    r[row] = data
            else:
                raise NotImplementedError("In-memory "
                                          "SingleColumnValueFilter "
                                          "doesn't support the %s operation "
                                          "yet" % op)
        return r


class MConnection(object):
    """HappyBase.Connection mock
    """
    def __init__(self):
        self.tables = {}

    def open(self):
        LOG.debug("Opening in-memory HBase connection")

    def create_table(self, n, families={}):
        if n in self.tables:
            return self.tables[n]
        t = MTable(n, families)
        self.tables[n] = t
        return t

    def delete_table(self, name, use_prefix=True):
        self.tables.remove(self.tables[name])

    def table(self, name):
        return self.create_table(name)


#################################################
# Here be various HBase helpers
def reverse_timestamp(dt):
    """Reverse timestamp so that newer timestamps are represented by smaller
    numbers than older ones.

    Reverse timestamps is a technique used in HBase rowkey design. When period
    queries are required the HBase rowkeys must include timestamps, but as
    rowkeys in HBase are ordered lexicographically, the timestamps must be
    reversed.
    """
    epoch = datetime.datetime(1970, 1, 1)
    td = dt - epoch
    ts = (td.microseconds +
          (td.seconds + td.days * 24 * 3600) * 100000) / 100000
    return 0x7fffffffffffffff - ts


def make_query(user=None, project=None, meter=None,
               resource=None, source=None, start=None, end=None,
               require_meter=True, query_only=False):
    """Return a filter query string based on the selected parameters.

    :param user: Optional user-id
    :param project: Optional project-id
    :param meter: Optional counter-name
    :param resource: Optional resource-id
    :param source: Optional source-id
    :param start: Optional start timestamp
    :param end: Optional end timestamp
    :param require_meter: If true and the filter does not have a meter,
            raise an error.
    :param query_only: If true only returns the filter query,
            otherwise also returns start and stop rowkeys
    """
    q = []

    if user:
        q.append("SingleColumnValueFilter ('f', 'user_id', =, 'binary:%s')"
                 % user)
    if project:
        q.append("SingleColumnValueFilter ('f', 'project_id', =, 'binary:%s')"
                 % project)
    if resource:
        q.append("SingleColumnValueFilter ('f', 'resource_id', =, 'binary:%s')"
                 % resource)
    if source:
        q.append("SingleColumnValueFilter "
                 "('f', 'source', =, 'binary:%s')" % source)

    start_row, end_row = "", ""
    rts_start = str(reverse_timestamp(start) + 1) if start else ""
    rts_end = str(reverse_timestamp(end) + 1) if end else ""

    # when start_time and end_time is provided,
    #    if it's filtered by meter,
    #         rowkey will be used in the query;
    #    else it's non meter filter query(e.g. project_id, user_id etc),
    #         SingleColumnValueFilter against rts will be appended to the query
    #    query other tables should have no start and end passed in
    if meter:
        start_row, end_row = _make_rowkey_scan(meter, rts_start, rts_end)
    elif require_meter:
        raise RuntimeError('Missing required meter specifier')
    else:
        if rts_start:
            q.append("SingleColumnValueFilter ('f', 'rts', <=, 'binary:%s')" %
                     rts_start)
        if rts_end:
            q.append("SingleColumnValueFilter ('f', 'rts', >=, 'binary:%s')" %
                     rts_end)

    sample_filter = None
    if len(q):
        sample_filter = " AND ".join(q)

    if query_only:
        return sample_filter
    else:
        return sample_filter, start_row, end_row


def make_query_from_filter(sample_filter, require_meter=True):
    """Return a query dictionary based on the settings in the filter.

    :param sample_filter: SampleFilter instance
    :param require_meter: If true and the filter does not have a meter,
                          raise an error.
    """
    return make_query(sample_filter.user, sample_filter.project,
                      sample_filter.meter, sample_filter.resource,
                      sample_filter.source, sample_filter.start,
                      sample_filter.end, require_meter)


def _make_rowkey_scan(meter, rts_start=None, rts_end=None):
    """If it's meter filter without start and end,
        start_row = meter while end_row = meter + MAX_BYTE
    """
    if not rts_start:
        rts_start = chr(127)
    end_row = "%s_%s" % (meter, rts_start)
    start_row = "%s_%s" % (meter, rts_end)

    return start_row, end_row


def _load_hbase_list(d, prefix):
    """Deserialise dict stored as HBase column family
    """
    ret = []
    prefix = 'f:%s_' % prefix
    for key in (k for k in d if k.startswith(prefix)):
        ret.append(key[len(prefix):])
    return ret
