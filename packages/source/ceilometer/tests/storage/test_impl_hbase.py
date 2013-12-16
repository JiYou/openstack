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
"""Tests for ceilometer/storage/impl_hbase.py

.. note::
  In order to run the tests against real HBase server set the environment
  variable CEILOMETER_TEST_HBASE_URL to point to that HBase instance before
  running the tests. Make sure the Thrift server is running on that server.

"""
from tests.storage import base


class HBaseEngineTestBase(base.DBTestBase):
    database_connection = 'hbase://__test__'


class UserTest(base.UserTest, HBaseEngineTestBase):
    pass


class ProjectTest(base.ProjectTest, HBaseEngineTestBase):
    pass


class ResourceTest(base.ResourceTest, HBaseEngineTestBase):
    pass


class MeterTest(base.MeterTest, HBaseEngineTestBase):
    pass


class RawSampleTest(base.RawSampleTest, HBaseEngineTestBase):
    pass


class StatisticsTest(base.StatisticsTest, HBaseEngineTestBase):
    pass


class CounterDataTypeTest(base.CounterDataTypeTest, HBaseEngineTestBase):
    pass
