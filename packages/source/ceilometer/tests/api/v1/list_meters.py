# -*- encoding: utf-8 -*-
#
# Copyright 2012 Red Hat, Inc.
#
# Author: Angus Salkeld <asalkeld@redhat.com>
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
"""Test listing meters.
"""

import datetime
import logging

from oslo.config import cfg

from ceilometer.publisher import rpc
from ceilometer import counter

from ceilometer.tests import api as tests_api

LOG = logging.getLogger(__name__)


class TestListEmptyMeters(tests_api.TestBase):

    def test_empty(self):
        data = self.get('/meters')
        self.assertEquals({'meters': []}, data)


class TestListMeters(tests_api.TestBase):

    def setUp(self):
        super(TestListMeters, self).setUp()

        for cnt in [
                counter.Counter(
                    'meter.test',
                    'cumulative',
                    '',
                    1,
                    'user-id',
                    'project-id',
                    'resource-id',
                    timestamp=datetime.datetime(2012, 7, 2, 10, 40),
                    resource_metadata={'display_name': 'test-server',
                                       'tag': 'self.counter'}),
                counter.Counter(
                    'meter.test',
                    'cumulative',
                    '',
                    3,
                    'user-id',
                    'project-id',
                    'resource-id',
                    timestamp=datetime.datetime(2012, 7, 2, 11, 40),
                    resource_metadata={'display_name': 'test-server',
                                       'tag': 'self.counter'}),
                counter.Counter(
                    'meter.mine',
                    'gauge',
                    '',
                    1,
                    'user-id',
                    'project-id',
                    'resource-id2',
                    timestamp=datetime.datetime(2012, 7, 2, 10, 41),
                    resource_metadata={'display_name': 'test-server',
                                       'tag': 'two.counter'}),
                counter.Counter(
                    'meter.test',
                    'cumulative',
                    '',
                    1,
                    'user-id2',
                    'project-id2',
                    'resource-id3',
                    timestamp=datetime.datetime(2012, 7, 2, 10, 42),
                    resource_metadata={'display_name': 'test-server',
                                       'tag': 'three.counter'}),
                counter.Counter(
                    'meter.mine',
                    'gauge',
                    '',
                    1,
                    'user-id4',
                    'project-id2',
                    'resource-id4',
                    timestamp=datetime.datetime(2012, 7, 2, 10, 43),
                    resource_metadata={'display_name': 'test-server',
                                       'tag': 'four.counter'})]:
            msg = rpc.meter_message_from_counter(
                cnt,
                cfg.CONF.publisher_rpc.metering_secret,
                'test_list_resources')
            self.conn.record_metering_data(msg)

    def test_list_meters(self):
        data = self.get('/meters')
        self.assertEquals(4, len(data['meters']))
        self.assertEquals(set(r['resource_id'] for r in data['meters']),
                          set(['resource-id',
                               'resource-id2',
                               'resource-id3',
                               'resource-id4']))
        self.assertEquals(set(r['name'] for r in data['meters']),
                          set(['meter.test',
                               'meter.mine']))

    def test_list_meters_non_admin(self):
        data = self.get('/meters',
                        headers={"X-Roles": "Member",
                                 "X-Tenant-Id": "project-id"})
        self.assertEquals(2, len(data['meters']))
        self.assertEquals(set(r['resource_id'] for r in data['meters']),
                          set(['resource-id',
                               'resource-id2']))
        self.assertEquals(set(r['name'] for r in data['meters']),
                          set(['meter.test',
                               'meter.mine']))

    def test_with_resource(self):
        data = self.get('/resources/resource-id/meters')
        ids = set(r['name'] for r in data['meters'])
        self.assertEquals(set(['meter.test']), ids)

    def test_with_source(self):
        data = self.get('/sources/test_list_resources/meters')
        ids = set(r['resource_id'] for r in data['meters'])
        self.assertEquals(set(['resource-id',
                               'resource-id2',
                               'resource-id3',
                               'resource-id4']), ids)

    def test_with_source_non_admin(self):
        data = self.get('/sources/test_list_resources/meters',
                        headers={"X-Roles": "Member",
                                 "X-Tenant-Id": "project-id2"})
        ids = set(r['resource_id'] for r in data['meters'])
        self.assertEquals(set(['resource-id3',
                               'resource-id4']), ids)

    def test_with_source_non_existent(self):
        data = self.get('/sources/test_list_resources_dont_exist/meters')
        self.assertEquals(data['meters'], [])

    def test_with_user(self):
        data = self.get('/users/user-id/meters')

        nids = set(r['name'] for r in data['meters'])
        self.assertEquals(set(['meter.mine', 'meter.test']), nids)

        rids = set(r['resource_id'] for r in data['meters'])
        self.assertEquals(set(['resource-id', 'resource-id2']), rids)

    def test_with_user_non_admin(self):
        data = self.get('/users/user-id/meters',
                        headers={"X-Roles": "Member",
                                 "X-Tenant-Id": "project-id"})
        nids = set(r['name'] for r in data['meters'])
        self.assertEquals(set(['meter.mine', 'meter.test']), nids)

        rids = set(r['resource_id'] for r in data['meters'])
        self.assertEquals(set(['resource-id', 'resource-id2']), rids)

    def test_with_user_wrong_tenant(self):
        data = self.get('/users/user-id/meters',
                        headers={"X-Roles": "Member",
                                 "X-Tenant-Id": "project666"})

        self.assertEquals(data['meters'], [])

    def test_with_user_non_existent(self):
        data = self.get('/users/user-id-foobar123/meters')
        self.assertEquals(data['meters'], [])

    def test_with_project(self):
        data = self.get('/projects/project-id2/meters')
        ids = set(r['resource_id'] for r in data['meters'])
        self.assertEquals(set(['resource-id3', 'resource-id4']), ids)

    def test_with_project_non_admin(self):
        data = self.get('/projects/project-id2/meters',
                        headers={"X-Roles": "Member",
                                 "X-Tenant-Id": "project-id2"})
        ids = set(r['resource_id'] for r in data['meters'])
        self.assertEquals(set(['resource-id3', 'resource-id4']), ids)

    def test_with_project_wrong_tenant(self):
        data = self.get('/projects/project-id2/meters',
                        headers={"X-Roles": "Member",
                                 "X-Tenant-Id": "project-id"})
        self.assertEqual(data.status_code, 404)

    def test_with_project_non_existent(self):
        data = self.get('/projects/jd-was-here/meters')
        self.assertEquals(data['meters'], [])


class TestListMetersMetaquery(TestListMeters):

    def test_metaquery1(self):
        data = self.get('/meters?metadata.tag=self.counter')
        self.assertEquals(1, len(data['meters']))

    def test_metaquery1_non_admin(self):
        data = self.get('/meters?metadata.tag=self.counter',
                        headers={"X-Roles": "Member",
                                 "X-Tenant-Id": "project-id"})
        self.assertEquals(1, len(data['meters']))

    def test_metaquery1_wrong_tenant(self):
        data = self.get('/meters?metadata.tag=self.counter',
                        headers={"X-Roles": "Member",
                                 "X-Tenant-Id": "project-666"})
        self.assertEquals(0, len(data['meters']))

    def test_metaquery2(self):
        data = self.get('/meters?metadata.tag=four.counter')
        self.assertEquals(1, len(data['meters']))

    def test_metaquery2_non_admin(self):
        data = self.get('/meters?metadata.tag=four.counter',
                        headers={"X-Roles": "Member",
                                 "X-Tenant-Id": "project-id2"})
        self.assertEquals(1, len(data['meters']))

    def test_metaquery2_non_admin_wrong_project(self):
        data = self.get('/meters?metadata.tag=four.counter',
                        headers={"X-Roles": "Member",
                                 "X-Tenant-Id": "project-666"})
        self.assertEquals(0, len(data['meters']))
