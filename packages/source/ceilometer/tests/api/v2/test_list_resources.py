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
"""Test listing resources.
"""

import datetime
import logging

from oslo.config import cfg

from ceilometer.publisher import rpc
from ceilometer import counter

from .base import FunctionalTest

LOG = logging.getLogger(__name__)


class TestListResources(FunctionalTest):

    SOURCE_DATA = {'test_list_resources': {}}

    def test_empty(self):
        data = self.get_json('/resources')
        self.assertEquals([], data)

    def test_instance_no_metadata(self):
        counter1 = counter.Counter(
            'instance',
            'cumulative',
            '',
            1,
            'user-id',
            'project-id',
            'resource-id',
            timestamp=datetime.datetime(2012, 7, 2, 10, 40),
            resource_metadata=None
        )
        msg = rpc.meter_message_from_counter(
            counter1,
            cfg.CONF.publisher_rpc.metering_secret,
            'test',
        )
        self.conn.record_metering_data(msg)

        data = self.get_json('/resources')
        self.assertEquals(1, len(data))

    def test_instances(self):
        counter1 = counter.Counter(
            'instance',
            'cumulative',
            '',
            1,
            'user-id',
            'project-id',
            'resource-id',
            timestamp=datetime.datetime(2012, 7, 2, 10, 40),
            resource_metadata={'display_name': 'test-server',
                               'tag': 'self.counter',
                               }
        )
        msg = rpc.meter_message_from_counter(
            counter1,
            cfg.CONF.publisher_rpc.metering_secret,
            'test',
        )
        self.conn.record_metering_data(msg)

        counter2 = counter.Counter(
            'instance',
            'cumulative',
            '',
            1,
            'user-id',
            'project-id',
            'resource-id-alternate',
            timestamp=datetime.datetime(2012, 7, 2, 10, 41),
            resource_metadata={'display_name': 'test-server',
                               'tag': 'self.counter2',
                               }
        )
        msg2 = rpc.meter_message_from_counter(
            counter2,
            cfg.CONF.publisher_rpc.metering_secret,
            'test',
        )
        self.conn.record_metering_data(msg2)

        data = self.get_json('/resources')
        self.assertEquals(2, len(data))

    def test_instances_one(self):
        counter1 = counter.Counter(
            'instance',
            'cumulative',
            '',
            1,
            'user-id',
            'project-id',
            'resource-id',
            timestamp=datetime.datetime(2012, 7, 2, 10, 40),
            resource_metadata={'display_name': 'test-server',
                               'tag': 'self.counter',
                               }
        )
        msg = rpc.meter_message_from_counter(
            counter1,
            cfg.CONF.publisher_rpc.metering_secret,
            'test',
        )
        self.conn.record_metering_data(msg)

        counter2 = counter.Counter(
            'instance',
            'cumulative',
            '',
            1,
            'user-id',
            'project-id',
            'resource-id-alternate',
            timestamp=datetime.datetime(2012, 7, 2, 10, 41),
            resource_metadata={'display_name': 'test-server',
                               'tag': 'self.counter2',
                               }
        )
        msg2 = rpc.meter_message_from_counter(
            counter2,
            cfg.CONF.publisher_rpc.metering_secret,
            'test',
        )
        self.conn.record_metering_data(msg2)

        data = self.get_json('/resources/resource-id')
        self.assertEquals('resource-id', data['resource_id'])

    def test_with_source(self):
        counter1 = counter.Counter(
            'instance',
            'cumulative',
            '',
            1,
            'user-id',
            'project-id',
            'resource-id',
            timestamp=datetime.datetime(2012, 7, 2, 10, 40),
            resource_metadata={'display_name': 'test-server',
                               'tag': 'self.counter',
                               }
        )
        msg = rpc.meter_message_from_counter(
            counter1,
            cfg.CONF.publisher_rpc.metering_secret,
            'test_list_resources',
        )
        self.conn.record_metering_data(msg)

        counter2 = counter.Counter(
            'instance',
            'cumulative',
            '',
            1,
            'user-id2',
            'project-id',
            'resource-id-alternate',
            timestamp=datetime.datetime(2012, 7, 2, 10, 41),
            resource_metadata={'display_name': 'test-server',
                               'tag': 'self.counter2',
                               }
        )
        msg2 = rpc.meter_message_from_counter(
            counter2,
            cfg.CONF.publisher_rpc.metering_secret,
            'not-test',
        )
        self.conn.record_metering_data(msg2)

        data = self.get_json('/resources', q=[{'field': 'source',
                                               'value': 'test_list_resources',
                                               }])
        ids = [r['resource_id'] for r in data]
        self.assertEquals(['resource-id'], ids)

    def test_with_user(self):
        counter1 = counter.Counter(
            'instance',
            'cumulative',
            '',
            1,
            'user-id',
            'project-id',
            'resource-id',
            timestamp=datetime.datetime(2012, 7, 2, 10, 40),
            resource_metadata={'display_name': 'test-server',
                               'tag': 'self.counter',
                               }
        )
        msg = rpc.meter_message_from_counter(
            counter1,
            cfg.CONF.publisher_rpc.metering_secret,
            'test_list_resources',
        )
        self.conn.record_metering_data(msg)

        counter2 = counter.Counter(
            'instance',
            'cumulative',
            '',
            1,
            'user-id2',
            'project-id',
            'resource-id-alternate',
            timestamp=datetime.datetime(2012, 7, 2, 10, 41),
            resource_metadata={'display_name': 'test-server',
                               'tag': 'self.counter2',
                               }
        )
        msg2 = rpc.meter_message_from_counter(
            counter2,
            cfg.CONF.publisher_rpc.metering_secret,
            'not-test',
        )
        self.conn.record_metering_data(msg2)

        data = self.get_json('/resources', q=[{'field': 'user_id',
                                               'value': 'user-id',
                                               }])
        ids = [r['resource_id'] for r in data]
        self.assertEquals(['resource-id'], ids)

    def test_with_project(self):
        counter1 = counter.Counter(
            'instance',
            'cumulative',
            '',
            1,
            'user-id',
            'project-id',
            'resource-id',
            timestamp=datetime.datetime(2012, 7, 2, 10, 40),
            resource_metadata={'display_name': 'test-server',
                               'tag': 'self.counter',
                               }
        )
        msg = rpc.meter_message_from_counter(
            counter1,
            cfg.CONF.publisher_rpc.metering_secret,
            'test_list_resources',
        )
        self.conn.record_metering_data(msg)

        counter2 = counter.Counter(
            'instance',
            'cumulative',
            '',
            1,
            'user-id2',
            'project-id2',
            'resource-id-alternate',
            timestamp=datetime.datetime(2012, 7, 2, 10, 41),
            resource_metadata={'display_name': 'test-server',
                               'tag': 'self.counter2',
                               }
        )
        msg2 = rpc.meter_message_from_counter(
            counter2,
            cfg.CONF.publisher_rpc.metering_secret,
            'not-test',
        )
        self.conn.record_metering_data(msg2)

        data = self.get_json('/resources', q=[{'field': 'project_id',
                                               'value': 'project-id',
                                               }])
        ids = [r['resource_id'] for r in data]
        self.assertEquals(['resource-id'], ids)

    def test_with_user_non_admin(self):
        counter1 = counter.Counter(
            'instance',
            'cumulative',
            '',
            1,
            'user-id2',
            'project-id2',
            'resource-id-alternate',
            timestamp=datetime.datetime(2012, 7, 2, 10, 41),
            resource_metadata={'display_name': 'test-server',
                               'tag': 'self.counter1',
                               }
        )
        msg2 = rpc.meter_message_from_counter(
            counter1,
            cfg.CONF.publisher_rpc.metering_secret,
            'not-test',
        )
        self.conn.record_metering_data(msg2)

        data = self.get_json('/resources',
                             headers={"X-Roles": "Member",
                                      "X-Tenant-Id": "project-id2"})
        ids = set(r['resource_id'] for r in data)
        self.assertEquals(set(['resource-id-alternate']), ids)

    def test_with_user_wrong_tenant(self):
        counter1 = counter.Counter(
            'instance',
            'cumulative',
            '',
            1,
            'user-id2',
            'project-id2',
            'resource-id-alternate',
            timestamp=datetime.datetime(2012, 7, 2, 10, 41),
            resource_metadata={'display_name': 'test-server',
                               'tag': 'self.counter1',
                               }
        )
        msg2 = rpc.meter_message_from_counter(
            counter1,
            cfg.CONF.publisher_rpc.metering_secret,
            'not-test',
        )
        self.conn.record_metering_data(msg2)

        data = self.get_json('/resources',
                             headers={"X-Roles": "Member",
                                      "X-Tenant-Id": "project-wrong"})
        ids = set(r['resource_id'] for r in data)
        self.assertEquals(set(), ids)

    def test_metadata(self):
        counter1 = counter.Counter(
            'instance',
            'cumulative',
            '',
            1,
            'user-id',
            'project-id',
            'resource-id',
            timestamp=datetime.datetime(2012, 7, 2, 10, 40),
            resource_metadata={'display_name': 'test-server',
                               'tag': 'self.counter',
                               'ignored_dict': {'key': 'value'},
                               'ignored_list': ['not-returned'],
                               }
        )
        msg = rpc.meter_message_from_counter(
            counter1,
            cfg.CONF.publisher_rpc.metering_secret,
            'test',
        )
        self.conn.record_metering_data(msg)

        data = self.get_json('/resources')
        metadata = data[0]['metadata']
        self.assertEqual(
            list(sorted(metadata.iteritems())),
            [('display_name', 'test-server'),
             ('tag', 'self.counter'),
             ])

    def test_resource_meter_links(self):
        counter1 = counter.Counter(
            'instance',
            'cumulative',
            '',
            1,
            'user-id',
            'project-id',
            'resource-id',
            timestamp=datetime.datetime(2012, 7, 2, 10, 40),
            resource_metadata={'display_name': 'test-server',
                               'tag': 'self.counter',
                               }
        )
        msg = rpc.meter_message_from_counter(
            counter1,
            cfg.CONF.publisher_rpc.metering_secret,
            'test_list_resources',
        )
        self.conn.record_metering_data(msg)

        data = self.get_json('/resources')
        links = data[0]['links']
        self.assertEqual(len(links), 2)
        self.assertEqual(links[0]['rel'], 'self')
        self.assertTrue((self.PATH_PREFIX + '/resources/resource-id')
                        in links[0]['href'])
        self.assertEqual(links[1]['rel'], 'instance')
        self.assertTrue((self.PATH_PREFIX + '/meters/instance?'
                         'q.field=resource_id&q.value=resource-id')
                        in links[1]['href'])
