# -*- encoding: utf-8 -*-
#
# Copyright © 2012 New Dream Network, LLC (DreamHost)
#
# Author: Doug Hellmann <doug.hellmann@dreamhost.com>
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
"""Tests for ceilometer/storage/impl_mongodb.py

.. note::

  (dhellmann) These tests have some dependencies which cannot be
  installed in the CI environment right now.

  Ming is necessary to provide the Mongo-in-memory implementation for
  of MongoDB. The original source for Ming is at
  http://sourceforge.net/project/merciless but there does not seem to
  be a way to point to a "zipball" of the latest HEAD there, and we
  need features present only in that version. I forked the project to
  github to make it easier to install, and put the URL into the
  test-requires file. Then I ended up making some changes to it so it
  would be compatible with PyMongo's API.

    https://github.com/dreamhost/Ming/zipball/master#egg=Ming

  In order to run the tests that use map-reduce with MIM, some
  additional system-level packages are required::

    apt-get install nspr-config
    apt-get install libnspr4-dev
    apt-get install pkg-config
    pip install python-spidermonkey

  To run the tests *without* mim, set the environment variable
  CEILOMETER_TEST_MONGODB_URL to a MongoDB URL before running tox.

"""

import copy
import datetime

from tests.storage import base

from ceilometer.publisher import rpc
from ceilometer import counter
from ceilometer.storage.impl_mongodb import require_map_reduce


class MongoDBEngineTestBase(base.DBTestBase):
    database_connection = 'mongodb://__test__'


class IndexTest(MongoDBEngineTestBase):

    def test_indexes_exist(self):
        # ensure_index returns none if index already exists
        assert not self.conn.db.resource.ensure_index('foo',
                                                      name='resource_idx')
        assert not self.conn.db.meter.ensure_index('foo',
                                                   name='meter_idx')


class UserTest(base.UserTest, MongoDBEngineTestBase):
    pass


class ProjectTest(base.ProjectTest, MongoDBEngineTestBase):
    pass


class ResourceTest(base.ResourceTest, MongoDBEngineTestBase):
    pass


class MeterTest(base.MeterTest, MongoDBEngineTestBase):
    pass


class RawSampleTest(base.RawSampleTest, MongoDBEngineTestBase):
    pass


class StatisticsTest(base.StatisticsTest, MongoDBEngineTestBase):

    def setUp(self):
        super(StatisticsTest, self).setUp()
        require_map_reduce(self.conn)


class AlarmTest(base.AlarmTest, MongoDBEngineTestBase):
    pass


class CompatibilityTest(MongoDBEngineTestBase):

    def prepare_data(self):
        def old_record_metering_data(self, data):
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
            received_timestamp = datetime.datetime.utcnow()
            self.db.resource.update(
                {'_id': data['resource_id']},
                {'$set': {'project_id': data['project_id'],
                          'user_id': data['user_id'],
                          # Current metadata being used and when it was
                          # last updated.
                          'timestamp': data['timestamp'],
                          'received_timestamp': received_timestamp,
                          'metadata': data['resource_metadata'],
                          'source': data['source'],
                          },
                 '$addToSet': {'meter': {'counter_name': data['counter_name'],
                                         'counter_type': data['counter_type'],
                                         },
                               },
                 },
                upsert=True,
            )

            record = copy.copy(data)
            self.db.meter.insert(record)
            return

        # Stubout with the old version DB schema, the one w/o 'counter_unit'
        self.stubs.Set(self.conn,
                       'record_metering_data',
                       old_record_metering_data)
        self.counters = []
        c = counter.Counter(
            'volume.size',
            'gauge',
            'GiB',
            5,
            'user-id',
            'project1',
            'resource-id',
            timestamp=datetime.datetime(2012, 9, 25, 10, 30),
            resource_metadata={'display_name': 'test-volume',
                               'tag': 'self.counter',
                               }
        )
        self.counters.append(c)
        msg = rpc.meter_message_from_counter(
            c,
            secret='not-so-secret',
            source='test')
        self.conn.record_metering_data(self.conn, msg)

    def test_counter_unit(self):
        meters = list(self.conn.get_meters())
        self.assertEqual(len(meters), 1)


class CounterDataTypeTest(base.CounterDataTypeTest, MongoDBEngineTestBase):
    pass
