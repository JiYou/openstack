# -*- encoding: utf-8 -*-
#
# Copyright 2012 Red Hat, Inc.
#
# Author: Angus Salkeld <asalkeld@redhat.com>
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

from .base import FunctionalTest

LOG = logging.getLogger(__name__)


class TestListEmptyMeters(FunctionalTest):

    def test_empty(self):
        data = self.get_json('/meters')
        self.assertEquals([], data)


class TestListMeters(FunctionalTest):

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
                                       'tag': 'self.counter2'}),
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
                                       'tag': 'self.counter3'}),
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
                                       'tag': 'self.counter4'})]:
            msg = rpc.meter_message_from_counter(
                cnt,
                cfg.CONF.publisher_rpc.metering_secret,
                'test_source')
            self.conn.record_metering_data(msg)

    def test_list_meters(self):
        data = self.get_json('/meters')
        self.assertEquals(4, len(data))
        self.assertEquals(set(r['resource_id'] for r in data),
                          set(['resource-id',
                               'resource-id2',
                               'resource-id3',
                               'resource-id4']))
        self.assertEquals(set(r['name'] for r in data),
                          set(['meter.test',
                               'meter.mine']))

    def test_with_resource(self):
        data = self.get_json('/meters', q=[{'field': 'resource_id',
                                            'value': 'resource-id',
                                            }])
        ids = set(r['name'] for r in data)
        self.assertEquals(set(['meter.test']), ids)

    def test_with_source(self):
        data = self.get_json('/meters', q=[{'field': 'source',
                                            'value': 'test_source',
                                            }])
        ids = set(r['resource_id'] for r in data)
        self.assertEquals(set(['resource-id',
                               'resource-id2',
                               'resource-id3',
                               'resource-id4']), ids)

    def test_with_source_non_existent(self):
        data = self.get_json('/meters',
                             q=[{'field': 'source',
                                 'value': 'test_source_doesnt_exist',
                                 }],
                             )
        assert not data

    def test_with_user(self):
        data = self.get_json('/meters',
                             q=[{'field': 'user_id',
                                 'value': 'user-id',
                                 }],
                             )

        uids = set(r['user_id'] for r in data)
        self.assertEquals(set(['user-id']), uids)

        nids = set(r['name'] for r in data)
        self.assertEquals(set(['meter.mine', 'meter.test']), nids)

        rids = set(r['resource_id'] for r in data)
        self.assertEquals(set(['resource-id', 'resource-id2']), rids)

    def test_with_user_non_existent(self):
        data = self.get_json('/meters',
                             q=[{'field': 'user_id',
                                 'value': 'user-id-foobar123',
                                 }],
                             )
        self.assertEquals(data, [])

    def test_with_project(self):
        data = self.get_json('/meters',
                             q=[{'field': 'project_id',
                                 'value': 'project-id2',
                                 }],
                             )
        ids = set(r['resource_id'] for r in data)
        self.assertEquals(set(['resource-id3', 'resource-id4']), ids)

    def test_with_project_non_existent(self):
        data = self.get_json('/meters',
                             q=[{'field': 'project_id',
                                 'value': 'jd-was-here',
                                 }],
                             )
        self.assertEquals(data, [])
