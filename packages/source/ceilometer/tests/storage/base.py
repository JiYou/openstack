# -*- encoding: utf-8 -*-
#
# Copyright © 2013 Intel Corp.
#
# Author: Lianhao Lu <lianhao.lu@intel.com>
# Author: Shane Wang <shane.wang@intel.com>
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

""" Base classes for DB backend implemtation test
"""

import abc
import datetime

from oslo.config import cfg

from ceilometer.publisher import rpc
from ceilometer import counter
from ceilometer import storage
from ceilometer.tests import db as test_db
from ceilometer.storage import models
from ceilometer import utils


class DBTestBase(test_db.TestBase):
    __metaclass__ = abc.ABCMeta

    def setUp(self):
        super(DBTestBase, self).setUp()
        self.prepare_data()

    def prepare_data(self):
        self.msgs = []
        self.counter = counter.Counter(
            'instance',
            counter.TYPE_CUMULATIVE,
            unit='',
            volume=1,
            user_id='user-id',
            project_id='project-id',
            resource_id='resource-id',
            timestamp=datetime.datetime(2012, 7, 2, 10, 40),
            resource_metadata={'display_name': 'test-server',
                               'tag': 'self.counter',
                               }
        )
        self.msg1 = rpc.meter_message_from_counter(
            self.counter,
            cfg.CONF.publisher_rpc.metering_secret,
            'test-1',
        )
        self.conn.record_metering_data(self.msg1)
        self.msgs.append(self.msg1)

        self.counter2 = counter.Counter(
            'instance',
            counter.TYPE_CUMULATIVE,
            unit='',
            volume=1,
            user_id='user-id',
            project_id='project-id',
            resource_id='resource-id-alternate',
            timestamp=datetime.datetime(2012, 7, 2, 10, 41),
            resource_metadata={'display_name': 'test-server',
                               'tag': 'self.counter2',
                               }
        )
        self.msg2 = rpc.meter_message_from_counter(
            self.counter2,
            cfg.CONF.publisher_rpc.metering_secret,
            'test-2',
        )
        self.conn.record_metering_data(self.msg2)
        self.msgs.append(self.msg2)

        self.counter3 = counter.Counter(
            'instance',
            counter.TYPE_CUMULATIVE,
            unit='',
            volume=1,
            user_id='user-id-alternate',
            project_id='project-id',
            resource_id='resource-id-alternate',
            timestamp=datetime.datetime(2012, 7, 2, 10, 41),
            resource_metadata={'display_name': 'test-server',
                               'tag': 'self.counter3',
                               }
        )
        self.msg3 = rpc.meter_message_from_counter(
            self.counter3,
            cfg.CONF.publisher_rpc.metering_secret,
            'test-3',
        )
        self.conn.record_metering_data(self.msg3)
        self.msgs.append(self.msg3)

        for i in range(2, 4):
            c = counter.Counter(
                'instance',
                counter.TYPE_CUMULATIVE,
                unit='',
                volume=1,
                user_id='user-id-%s' % i,
                project_id='project-id-%s' % i,
                resource_id='resource-id-%s' % i,
                timestamp=datetime.datetime(2012, 7, 2, 10, 40 + i),
                resource_metadata={'display_name': 'test-server',
                                   'tag': 'counter-%s' % i},
            )
            msg = rpc.meter_message_from_counter(
                c,
                cfg.CONF.publisher_rpc.metering_secret,
                'test',
            )
            self.conn.record_metering_data(msg)
            self.msgs.append(msg)


class UserTest(DBTestBase):

    def test_get_users(self):
        users = self.conn.get_users()
        assert set(users) == set(['user-id',
                                  'user-id-alternate',
                                  'user-id-2',
                                  'user-id-3',
                                  ])

    def test_get_users_by_source(self):
        users = self.conn.get_users(source='test-1')
        assert list(users) == ['user-id']


class ProjectTest(DBTestBase):

    def test_get_projects(self):
        projects = self.conn.get_projects()
        expected = set(['project-id', 'project-id-2', 'project-id-3'])
        assert set(projects) == expected

    def test_get_projects_by_source(self):
        projects = self.conn.get_projects(source='test-1')
        expected = ['project-id']
        assert list(projects) == expected


class ResourceTest(DBTestBase):

    def test_get_resources(self):
        msgs_sources = [msg['source'] for msg in self.msgs]
        resources = list(self.conn.get_resources())
        assert len(resources) == 4
        for resource in resources:
            if resource.resource_id != 'resource-id':
                continue
            assert resource.resource_id == 'resource-id'
            assert resource.project_id == 'project-id'
            self.assertIn(resource.source, msgs_sources)
            assert resource.user_id == 'user-id'
            assert resource.metadata['display_name'] == 'test-server'
            self.assertIn(models.ResourceMeter('instance', 'cumulative', ''),
                          resource.meter)
            break
        else:
            assert False, 'Never found resource-id'

    def test_get_resources_start_timestamp(self):
        timestamp = datetime.datetime(2012, 7, 2, 10, 42)
        resources = list(self.conn.get_resources(start_timestamp=timestamp))
        resource_ids = [r.resource_id for r in resources]
        expected = set(['resource-id-2', 'resource-id-3'])
        assert set(resource_ids) == expected

    def test_get_resources_end_timestamp(self):
        timestamp = datetime.datetime(2012, 7, 2, 10, 42)
        resources = list(self.conn.get_resources(end_timestamp=timestamp))
        resource_ids = [r.resource_id for r in resources]
        expected = set(['resource-id', 'resource-id-alternate'])
        assert set(resource_ids) == expected

    def test_get_resources_both_timestamps(self):
        start_ts = datetime.datetime(2012, 7, 2, 10, 42)
        end_ts = datetime.datetime(2012, 7, 2, 10, 43)
        resources = list(self.conn.get_resources(start_timestamp=start_ts,
                                                 end_timestamp=end_ts))
        resource_ids = [r.resource_id for r in resources]
        assert set(resource_ids) == set(['resource-id-2'])

    def test_get_resources_by_source(self):
        resources = list(self.conn.get_resources(source='test-1'))
        assert len(resources) == 1
        ids = set(r.resource_id for r in resources)
        assert ids == set(['resource-id'])

    def test_get_resources_by_user(self):
        resources = list(self.conn.get_resources(user='user-id'))
        assert len(resources) == 2
        ids = set(r.resource_id for r in resources)
        assert ids == set(['resource-id', 'resource-id-alternate'])

    def test_get_resources_by_project(self):
        resources = list(self.conn.get_resources(project='project-id'))
        assert len(resources) == 2
        ids = set(r.resource_id for r in resources)
        assert ids == set(['resource-id', 'resource-id-alternate'])

    def test_get_resources_by_metaquery(self):
        q = {'metadata.display_name': 'test-server'}
        got_not_imp = False
        try:
            resources = list(self.conn.get_resources(metaquery=q))
            assert len(resources) == 4
        except NotImplementedError:
            got_not_imp = True
            self.assertTrue(got_not_imp)
        #this should work, but it doesn't.
        #actually unless I wrap get_resources in list()
        #it doesn't get called - weird
        #self.assertRaises(NotImplementedError,
        #                  self.conn.get_resources,
        #                  metaquery=q)

    def test_get_resources_by_empty_metaquery(self):
        resources = list(self.conn.get_resources(metaquery={}))
        self.assertTrue(len(resources) == 4)


class MeterTest(DBTestBase):

    def test_get_meters(self):
        msgs_sources = [msg['source'] for msg in self.msgs]
        results = list(self.conn.get_meters())
        assert len(results) == 4
        for meter in results:
            self.assertIn(meter.source, msgs_sources)

    def test_get_meters_by_user(self):
        results = list(self.conn.get_meters(user='user-id'))
        assert len(results) == 1

    def test_get_meters_by_project(self):
        results = list(self.conn.get_meters(project='project-id'))
        assert len(results) == 2

    def test_get_meters_by_metaquery(self):
        q = {'metadata.display_name': 'test-server'}
        got_not_imp = False
        try:
            results = list(self.conn.get_meters(metaquery=q))
            assert results
            assert len(results) == 4
        except NotImplementedError:
            got_not_imp = True
            self.assertTrue(got_not_imp)

    def test_get_meters_by_empty_metaquery(self):
        results = list(self.conn.get_meters(metaquery={}))
        self.assertTrue(len(results) == 4)


class RawSampleTest(DBTestBase):

    def test_get_samples_limit_zero(self):
        f = storage.SampleFilter()
        results = list(self.conn.get_samples(f, limit=0))
        self.assertEqual(len(results), 0)

    def test_get_samples_limit(self):
        f = storage.SampleFilter()
        results = list(self.conn.get_samples(f, limit=3))
        self.assertEqual(len(results), 3)

    def test_get_samples_by_user(self):
        f = storage.SampleFilter(user='user-id')
        results = list(self.conn.get_samples(f))
        assert len(results) == 2
        for meter in results:
            assert meter.as_dict() in [self.msg1, self.msg2]

    def test_get_samples_by_user_limit(self):
        f = storage.SampleFilter(user='user-id')
        results = list(self.conn.get_samples(f, limit=1))
        self.assertEqual(len(results), 1)

    def test_get_samples_by_user_limit_bigger(self):
        f = storage.SampleFilter(user='user-id')
        results = list(self.conn.get_samples(f, limit=42))
        self.assertEqual(len(results), 2)

    def test_get_samples_by_project(self):
        f = storage.SampleFilter(project='project-id')
        results = list(self.conn.get_samples(f))
        assert results
        for meter in results:
            assert meter.as_dict() in [self.msg1, self.msg2, self.msg3]

    def test_get_samples_by_resource(self):
        f = storage.SampleFilter(user='user-id', resource='resource-id')
        results = list(self.conn.get_samples(f))
        assert results
        meter = results[0]
        assert meter is not None
        assert meter.as_dict() == self.msg1

    def test_get_samples_by_metaquery(self):
        q = {'metadata.display_name': 'test-server'}
        f = storage.SampleFilter(metaquery=q)
        got_not_imp = False
        try:
            results = list(self.conn.get_samples(f))
            assert results
            for meter in results:
                assert meter.as_dict() in self.msgs
        except NotImplementedError:
            got_not_imp = True
            self.assertTrue(got_not_imp)

    def test_get_samples_by_start_time(self):
        f = storage.SampleFilter(
            user='user-id',
            start=datetime.datetime(2012, 7, 2, 10, 41),
        )
        results = list(self.conn.get_samples(f))
        assert len(results) == 1
        assert results[0].timestamp == datetime.datetime(2012, 7, 2, 10, 41)

    def test_get_samples_by_end_time(self):
        f = storage.SampleFilter(
            user='user-id',
            end=datetime.datetime(2012, 7, 2, 10, 41),
        )
        results = list(self.conn.get_samples(f))
        length = len(results)
        assert length == 1
        assert results[0].timestamp == datetime.datetime(2012, 7, 2, 10, 40)

    def test_get_samples_by_both_times(self):
        f = storage.SampleFilter(
            start=datetime.datetime(2012, 7, 2, 10, 42),
            end=datetime.datetime(2012, 7, 2, 10, 43),
        )
        results = list(self.conn.get_samples(f))
        length = len(results)
        assert length == 1
        assert results[0].timestamp == datetime.datetime(2012, 7, 2, 10, 42)

    def test_get_samples_by_name(self):
        f = storage.SampleFilter(user='user-id', meter='no-such-meter')
        results = list(self.conn.get_samples(f))
        assert not results

    def test_get_samples_by_name2(self):
        f = storage.SampleFilter(user='user-id', meter='instance')
        results = list(self.conn.get_samples(f))
        assert results

    def test_get_samples_by_source(self):
        f = storage.SampleFilter(source='test-1')
        results = list(self.conn.get_samples(f))
        assert results
        assert len(results) == 1


class StatisticsTest(DBTestBase):

    def prepare_data(self):
        self.counters = []
        for i in range(3):
            c = counter.Counter(
                'volume.size',
                'gauge',
                'GiB',
                5 + i,
                'user-id',
                'project1',
                'resource-id',
                timestamp=datetime.datetime(2012, 9, 25, 10 + i, 30 + i),
                resource_metadata={'display_name': 'test-volume',
                                   'tag': 'self.counter',
                                   }
            )
            self.counters.append(c)
            msg = rpc.meter_message_from_counter(
                c,
                secret='not-so-secret',
                source='test',
            )
            self.conn.record_metering_data(msg)
        for i in range(3):
            c = counter.Counter(
                'volume.size',
                'gauge',
                'GiB',
                8 + i,
                'user-5',
                'project2',
                'resource-6',
                timestamp=datetime.datetime(2012, 9, 25, 10 + i, 30 + i),
                resource_metadata={'display_name': 'test-volume',
                                   'tag': 'self.counter',
                                   }
            )
            self.counters.append(c)
            msg = rpc.meter_message_from_counter(
                c,
                secret='not-so-secret',
                source='test',
            )
            self.conn.record_metering_data(msg)

    def test_by_user(self):
        f = storage.SampleFilter(
            user='user-5',
            meter='volume.size',
        )
        results = list(self.conn.get_meter_statistics(f))[0]
        self.assertEqual(results.duration,
                         (datetime.datetime(2012, 9, 25, 12, 32)
                          - datetime.datetime(2012, 9, 25, 10, 30)).seconds)
        assert results.count == 3
        assert results.min == 8
        assert results.max == 10
        assert results.sum == 27
        assert results.avg == 9

    def test_no_period_in_query(self):
        f = storage.SampleFilter(
            user='user-5',
            meter='volume.size',
        )
        results = list(self.conn.get_meter_statistics(f))[0]
        assert results.period == 0

    def test_period_is_int(self):
        f = storage.SampleFilter(
            meter='volume.size',
        )
        results = list(self.conn.get_meter_statistics(f))[0]
        assert(isinstance(results.period, int))
        assert results.count == 6

    def test_by_user_period(self):
        f = storage.SampleFilter(
            user='user-5',
            meter='volume.size',
            start='2012-09-25T10:28:00',
        )
        results = list(self.conn.get_meter_statistics(f, period=7200))
        self.assertEqual(len(results), 2)
        self.assertEqual(set(r.period_start for r in results),
                         set([datetime.datetime(2012, 9, 25, 10, 28),
                              datetime.datetime(2012, 9, 25, 12, 28)]))
        self.assertEqual(set(r.period_end for r in results),
                         set([datetime.datetime(2012, 9, 25, 12, 28),
                              datetime.datetime(2012, 9, 25, 14, 28)]))
        r = results[0]
        self.assertEqual(r.period_start,
                         datetime.datetime(2012, 9, 25, 10, 28))
        self.assertEqual(r.count, 2)
        self.assertEqual(r.avg, 8.5)
        self.assertEqual(r.min, 8)
        self.assertEqual(r.max, 9)
        self.assertEqual(r.sum, 17)
        self.assertEqual(r.period, 7200)
        self.assertIsInstance(r.period, int)
        expected_end = r.period_start + datetime.timedelta(seconds=7200)
        self.assertEqual(r.period_end, expected_end)
        self.assertEqual(r.duration, 3660)
        self.assertEqual(r.duration_start,
                         datetime.datetime(2012, 9, 25, 10, 30))
        self.assertEqual(r.duration_end,
                         datetime.datetime(2012, 9, 25, 11, 31))

    def test_by_user_period_start_end(self):
        f = storage.SampleFilter(
            user='user-5',
            meter='volume.size',
            start='2012-09-25T10:28:00',
            end='2012-09-25T11:28:00',
        )
        results = list(self.conn.get_meter_statistics(f, period=1800))
        self.assertEqual(len(results), 1)
        r = results[0]
        self.assertEqual(r.period_start,
                         datetime.datetime(2012, 9, 25, 10, 28))
        self.assertEqual(r.count, 1)
        self.assertEqual(r.avg, 8)
        self.assertEqual(r.min, 8)
        self.assertEqual(r.max, 8)
        self.assertEqual(r.sum, 8)
        self.assertEqual(r.period, 1800)
        self.assertEqual(r.period_end,
                         r.period_start
                         + datetime.timedelta(seconds=1800))
        self.assertEqual(r.duration, 0)
        self.assertEqual(r.duration_start,
                         datetime.datetime(2012, 9, 25, 10, 30))
        self.assertEqual(r.duration_end,
                         datetime.datetime(2012, 9, 25, 10, 30))

    def test_by_project(self):
        f = storage.SampleFilter(
            meter='volume.size',
            resource='resource-id',
            start='2012-09-25T11:30:00',
            end='2012-09-25T11:32:00',
        )
        results = list(self.conn.get_meter_statistics(f))[0]
        self.assertEqual(results.duration, 0)
        assert results.count == 1
        assert results.min == 6
        assert results.max == 6
        assert results.sum == 6
        assert results.avg == 6

    def test_one_resource(self):
        f = storage.SampleFilter(
            user='user-id',
            meter='volume.size',
        )
        results = list(self.conn.get_meter_statistics(f))[0]
        self.assertEqual(results.duration,
                         (datetime.datetime(2012, 9, 25, 12, 32)
                          - datetime.datetime(2012, 9, 25, 10, 30)).seconds)
        assert results.count == 3
        assert results.min == 5
        assert results.max == 7
        assert results.sum == 18
        assert results.avg == 6


class CounterDataTypeTest(DBTestBase):

    def prepare_data(self):
        c = counter.Counter(
            'dummyBigCounter',
            counter.TYPE_CUMULATIVE,
            unit='',
            volume=3372036854775807,
            user_id='user-id',
            project_id='project-id',
            resource_id='resource-id',
            timestamp=datetime.datetime(2012, 7, 2, 10, 40),
            resource_metadata={}
        )
        msg = rpc.meter_message_from_counter(
            c,
            cfg.CONF.publisher_rpc.metering_secret,
            'test-1',
        )

        self.conn.record_metering_data(msg)

        c = counter.Counter(
            'dummySmallCounter',
            counter.TYPE_CUMULATIVE,
            unit='',
            volume=-3372036854775807,
            user_id='user-id',
            project_id='project-id',
            resource_id='resource-id',
            timestamp=datetime.datetime(2012, 7, 2, 10, 40),
            resource_metadata={}
        )
        msg = rpc.meter_message_from_counter(
            c,
            cfg.CONF.publisher_rpc.metering_secret,
            'test-1',
        )
        self.conn.record_metering_data(msg)

        c = counter.Counter(
            'floatCounter',
            counter.TYPE_CUMULATIVE,
            unit='',
            volume=1938495037.53697,
            user_id='user-id',
            project_id='project-id',
            resource_id='resource-id',
            timestamp=datetime.datetime(2012, 7, 2, 10, 40),
            resource_metadata={}
        )
        msg = rpc.meter_message_from_counter(
            c,
            cfg.CONF.publisher_rpc.metering_secret,
            'test-1',
        )
        self.conn.record_metering_data(msg)

    def test_storage_can_handle_large_values(self):
        f = storage.SampleFilter(
            meter='dummyBigCounter',
        )
        results = list(self.conn.get_samples(f))
        self.assertEqual(results[0].counter_volume, 3372036854775807)

        f = storage.SampleFilter(
            meter='dummySmallCounter',
        )
        results = list(self.conn.get_samples(f))
        self.assertEqual(results[0].counter_volume, -3372036854775807)

    def test_storage_can_handle_float_values(self):
        f = storage.SampleFilter(
            meter='floatCounter',
        )
        results = list(self.conn.get_samples(f))
        self.assertEqual(results[0].counter_volume, 1938495037.53697)


class AlarmTest(DBTestBase):

    def test_empty(self):
        alarms = list(self.conn.get_alarms())
        self.assertEquals([], alarms)

    def add_some_alarms(self):
        alarms = [models.Alarm('red-alert',
                               'test.one', 'eq', 36, 'count',
                               'me', 'and-da-boys',
                               evaluation_periods=1,
                               period=60,
                               alarm_actions=['http://nowhere/alarms']),
                  models.Alarm('orange-alert',
                               'test.fourty', 'gt', 75, 'avg',
                               'me', 'and-da-boys',
                               period=60,
                               alarm_actions=['http://nowhere/alarms']),
                  models.Alarm('yellow-alert',
                               'test.five', 'lt', 10, 'min',
                               'me', 'and-da-boys',
                               alarm_actions=['http://nowhere/alarms'])]
        for a in alarms:
            self.conn.update_alarm(a)

    def test_add(self):
        self.add_some_alarms()
        alarms = list(self.conn.get_alarms())
        self.assertEquals(len(alarms), 3)

    def test_defaults(self):
        self.add_some_alarms()
        yellow = list(self.conn.get_alarms(name='yellow-alert'))[0]

        self.assertEquals(yellow.evaluation_periods, 1)
        self.assertEquals(yellow.period, 60)
        self.assertEquals(yellow.enabled, True)
        self.assertEquals(yellow.description,
                          'Alarm when test.five is lt %s' %
                          'a min of 10 over 60 seconds')
        self.assertEquals(yellow.state, models.Alarm.ALARM_INSUFFICIENT_DATA)
        self.assertEquals(yellow.ok_actions, [])
        self.assertEquals(yellow.insufficient_data_actions, [])

    def test_update(self):
        self.add_some_alarms()
        orange = list(self.conn.get_alarms(name='orange-alert'))[0]
        orange.enabled = False
        orange.state = models.Alarm.ALARM_INSUFFICIENT_DATA
        updated = self.conn.update_alarm(orange)
        self.assertEquals(updated.enabled, False)
        self.assertEquals(updated.state, models.Alarm.ALARM_INSUFFICIENT_DATA)

    def test_update_llu(self):
        llu = models.Alarm('llu',
                           'counter_name', 'lt', 34, 'max',
                           'bla', 'ffo')
        updated = self.conn.update_alarm(llu)
        updated.state = models.Alarm.ALARM_OK
        updated.description = ':)'
        self.conn.update_alarm(updated)

        all = list(self.conn.get_alarms())
        self.assertEquals(len(all), 1)

    def test_delete(self):
        self.add_some_alarms()
        victim = list(self.conn.get_alarms(name='orange-alert'))[0]
        self.conn.delete_alarm(victim.alarm_id)
        survivors = list(self.conn.get_alarms())
        self.assertEquals(len(survivors), 2)
        for s in survivors:
            self.assertNotEquals(victim.name, s.name)


class EventTestBase(test_db.TestBase):
    """Separate test base class because we don't want to
    inherit all the Meter stuff.
    """
    __metaclass__ = abc.ABCMeta

    def setUp(self):
        super(EventTestBase, self).setUp()
        self.prepare_data()

    def prepare_data(self):
        # Add some data ...
        pass


class EventTest(EventTestBase):
    def test_save_events_no_traits(self):
        now = datetime.datetime.utcnow()
        m = [models.Event("Foo", now, None), models.Event("Zoo", now, [])]
        self.conn.record_events(m)
        for model in m:
            self.assertTrue(model.id >= 0)
        self.assertNotEqual(m[0].id, m[1].id)

    def test_string_traits(self):
        model = models.Trait("Foo", models.Trait.TEXT_TYPE, "my_text")
        trait = self.conn._make_trait(model, None)
        self.assertEquals(trait.t_type, models.Trait.TEXT_TYPE)
        self.assertIsNone(trait.t_float)
        self.assertIsNone(trait.t_int)
        self.assertIsNone(trait.t_datetime)
        self.assertEquals(trait.t_string, "my_text")
        self.assertIsNotNone(trait.name)

    def test_int_traits(self):
        model = models.Trait("Foo", models.Trait.INT_TYPE, 100)
        trait = self.conn._make_trait(model, None)
        self.assertEquals(trait.t_type, models.Trait.INT_TYPE)
        self.assertIsNone(trait.t_float)
        self.assertIsNone(trait.t_string)
        self.assertIsNone(trait.t_datetime)
        self.assertEquals(trait.t_int, 100)
        self.assertIsNotNone(trait.name)

    def test_float_traits(self):
        model = models.Trait("Foo", models.Trait.FLOAT_TYPE, 123.456)
        trait = self.conn._make_trait(model, None)
        self.assertEquals(trait.t_type, models.Trait.FLOAT_TYPE)
        self.assertIsNone(trait.t_int)
        self.assertIsNone(trait.t_string)
        self.assertIsNone(trait.t_datetime)
        self.assertEquals(trait.t_float, 123.456)
        self.assertIsNotNone(trait.name)

    def test_datetime_traits(self):
        now = datetime.datetime.utcnow()
        model = models.Trait("Foo", models.Trait.DATETIME_TYPE, now)
        trait = self.conn._make_trait(model, None)
        self.assertEquals(trait.t_type, models.Trait.DATETIME_TYPE)
        self.assertIsNone(trait.t_int)
        self.assertIsNone(trait.t_string)
        self.assertIsNone(trait.t_float)
        self.assertEquals(trait.t_datetime, utils.dt_to_decimal(now))
        self.assertIsNotNone(trait.name)

    def test_save_events_traits(self):
        event_models = []
        for event_name in ['Foo', 'Bar', 'Zoo']:
            now = datetime.datetime.utcnow()
            trait_models = \
                [models.Trait(name, dtype, value)
                    for name, dtype, value in [
                        ('trait_A', models.Trait.TEXT_TYPE, "my_text"),
                        ('trait_B', models.Trait.INT_TYPE, 199),
                        ('trait_C', models.Trait.FLOAT_TYPE, 1.23456),
                        ('trait_D', models.Trait.DATETIME_TYPE, now)]]
            event_models.append(
                models.Event(event_name, now, trait_models))

        self.conn.record_events(event_models)
        for model in event_models:
            for trait in model.traits:
                self.assertTrue(trait.id >= 0)


class GetEventTest(EventTestBase):
    def prepare_data(self):
        event_models = []
        base = 0
        self.start = datetime.datetime(2013, 12, 31, 5, 0)
        now = self.start
        for event_name in ['Foo', 'Bar', 'Zoo']:
            trait_models = \
                [models.Trait(name, dtype, value)
                    for name, dtype, value in [
                        ('trait_A', models.Trait.TEXT_TYPE,
                            "my_%s_text" % event_name),
                        ('trait_B', models.Trait.INT_TYPE,
                            base + 1),
                        ('trait_C', models.Trait.FLOAT_TYPE,
                            float(base) + 0.123456),
                        ('trait_D', models.Trait.DATETIME_TYPE, now)]]
            event_models.append(
                models.Event(event_name, now, trait_models))
            base += 100
            now = now + datetime.timedelta(hours=1)
        self.end = now

        self.conn.record_events(event_models)

    def test_simple_get(self):
        event_filter = storage.EventFilter(self.start, self.end)
        events = self.conn.get_events(event_filter)
        self.assertEquals(3, len(events))
        start_time = None
        for i, name in enumerate(["Foo", "Bar", "Zoo"]):
            self.assertEquals(events[i].event_name, name)
            self.assertEquals(4, len(events[i].traits))
            # Ensure sorted results ...
            if start_time is not None:
                # Python 2.6 has no assertLess :(
                self.assertTrue(start_time < events[i].generated)
            start_time = events[i].generated

    def test_simple_get_event_name(self):
        event_filter = storage.EventFilter(self.start, self.end, "Bar")
        events = self.conn.get_events(event_filter)
        self.assertEquals(1, len(events))
        self.assertEquals(events[0].event_name, "Bar")
        self.assertEquals(4, len(events[0].traits))

    def test_get_event_trait_filter(self):
        trait_filters = {'key': 'trait_B', 't_int': 101}
        event_filter = storage.EventFilter(self.start, self.end,
                                           traits=trait_filters)
        events = self.conn.get_events(event_filter)
        self.assertEquals(1, len(events))
        self.assertEquals(events[0].event_name, "Bar")
        self.assertEquals(4, len(events[0].traits))
