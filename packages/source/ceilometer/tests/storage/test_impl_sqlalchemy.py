# -*- encoding: utf-8 -*-
#
# Author: John Tran <jhtran@att.com>
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
"""Tests for ceilometer/storage/impl_sqlalchemy.py

.. note::
  In order to run the tests against real SQL server set the environment
  variable CEILOMETER_TEST_SQL_URL to point to a SQL server before running
  the tests.

"""

from oslo.config import cfg

from ceilometer.storage.sqlalchemy.models import table_args

from tests.storage import base


class SQLAlchemyEngineTestBase(base.DBTestBase):
    database_connection = 'sqlite://'


class UserTest(base.UserTest, SQLAlchemyEngineTestBase):
    pass


class ProjectTest(base.ProjectTest, SQLAlchemyEngineTestBase):
    pass


class ResourceTest(base.ResourceTest, SQLAlchemyEngineTestBase):
    pass


class MeterTest(base.MeterTest, SQLAlchemyEngineTestBase):
    pass


class RawSampleTest(base.RawSampleTest, SQLAlchemyEngineTestBase):
    pass


class StatisticsTest(base.StatisticsTest, SQLAlchemyEngineTestBase):
    pass


class CounterDataTypeTest(base.CounterDataTypeTest, SQLAlchemyEngineTestBase):
    pass


class AlarmTest(base.AlarmTest, SQLAlchemyEngineTestBase):
    pass


class EventTestBase(base.EventTestBase):
    # Note: Do not derive from SQLAlchemyEngineTestBase, since we
    # don't want to automatically inherit all the Meter setup.
    database_connection = 'sqlite://'


class UniqueNameTest(base.EventTest, EventTestBase):
    # UniqueName is a construct specific to sqlalchemy.
    # Not applicable to other drivers.

    def test_unique_exists(self):
        u1 = self.conn._get_or_create_unique_name("foo")
        self.assertTrue(u1.id >= 0)
        u2 = self.conn._get_or_create_unique_name("foo")
        self.assertEqual(u1.id, u2.id)
        self.assertEqual(u1.key, u2.key)

    def test_new_unique(self):
        u1 = self.conn._get_or_create_unique_name("foo")
        self.assertTrue(u1.id >= 0)
        u2 = self.conn._get_or_create_unique_name("blah")
        self.assertNotEqual(u1.id, u2.id)
        self.assertNotEqual(u1.key, u2.key)


class EventTest(base.EventTest, EventTestBase):
    pass


class GetEventTest(base.GetEventTest, EventTestBase):
    pass


def test_model_table_args():
    cfg.CONF.database.connection = 'mysql://localhost'
    assert table_args()
