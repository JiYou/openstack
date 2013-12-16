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
"""Test listing raw events.
"""

import datetime
import logging
import webtest.app

from oslo.config import cfg

from ceilometer.publisher import rpc
from ceilometer import counter

from .base import FunctionalTest

LOG = logging.getLogger(__name__)


class TestListEvents(FunctionalTest):

    def setUp(self):
        super(TestListEvents, self).setUp()
        self.counter1 = counter.Counter(
            'instance',
            'cumulative',
            '',
            1,
            'user-id',
            'project1',
            'resource-id',
            timestamp=datetime.datetime(2012, 7, 2, 10, 40),
            resource_metadata={'display_name': 'test-server',
                               'tag': 'self.counter',
                               'ignored_dict': {'key': 'value'},
                               'ignored_list': ['not-returned'],
                               }
        )
        msg = rpc.meter_message_from_counter(
            self.counter1,
            cfg.CONF.publisher_rpc.metering_secret,
            'test_source',
        )
        self.conn.record_metering_data(msg)

        self.counter2 = counter.Counter(
            'instance',
            'cumulative',
            '',
            1,
            'user-id2',
            'project2',
            'resource-id-alternate',
            timestamp=datetime.datetime(2012, 7, 2, 10, 41),
            resource_metadata={'display_name': 'test-server',
                               'tag': 'self.counter2',
                               }
        )
        msg2 = rpc.meter_message_from_counter(
            self.counter2,
            cfg.CONF.publisher_rpc.metering_secret,
            'source2',
        )
        self.conn.record_metering_data(msg2)

    def test_all(self):
        data = self.get_json('/meters/instance')
        self.assertEquals(2, len(data))

    def test_all_limit(self):
        data = self.get_json('/meters/instance?limit=1')
        self.assertEquals(1, len(data))

    def test_all_limit_negative(self):
        self.assertRaises(webtest.app.AppError,
                          self.get_json,
                          '/meters/instance?limit=-2')

    def test_all_limit_bigger(self):
        data = self.get_json('/meters/instance?limit=42')
        self.assertEquals(2, len(data))

    def test_empty_project(self):
        data = self.get_json('/meters/instance',
                             q=[{'field': 'project_id',
                                 'value': 'no-such-project',
                                 }])
        self.assertEquals([], data)

    def test_by_project(self):
        data = self.get_json('/meters/instance',
                             q=[{'field': 'project_id',
                                 'value': 'project1',
                                 }])
        self.assertEquals(1, len(data))

    def test_empty_resource(self):
        data = self.get_json('/meters/instance',
                             q=[{'field': 'resource_id',
                                 'value': 'no-such-resource',
                                 }])
        self.assertEquals([], data)

    def test_by_resource(self):
        data = self.get_json('/meters/instance',
                             q=[{'field': 'resource_id',
                                 'value': 'resource-id',
                                 }])
        self.assertEquals(1, len(data))

    def test_empty_source(self):
        data = self.get_json('/meters/instance',
                             q=[{'field': 'source',
                                 'value': 'no-such-source',
                                 }])
        self.assertEquals(0, len(data))

    def test_by_source(self):
        data = self.get_json('/meters/instance',
                             q=[{'field': 'source',
                                 'value': 'test_source',
                                 }])
        self.assertEquals(1, len(data))

    def test_empty_user(self):
        data = self.get_json('/meters/instance',
                             q=[{'field': 'user_id',
                                 'value': 'no-such-user',
                                 }])
        self.assertEquals([], data)

    def test_by_user(self):
        data = self.get_json('/meters/instance',
                             q=[{'field': 'user_id',
                                 'value': 'user-id',
                                 }])
        self.assertEquals(1, len(data))

    def test_metadata(self):
        data = self.get_json('/meters/instance',
                             q=[{'field': 'resource_id',
                                 'value': 'resource-id',
                                 }])
        sample = data[0]
        self.assert_('resource_metadata' in sample)
        self.assertEqual(
            list(sorted(sample['resource_metadata'].iteritems())),
            [('display_name', 'test-server'),
             ('tag', 'self.counter'),
             ])
