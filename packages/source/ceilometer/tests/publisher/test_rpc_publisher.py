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
"""Tests for ceilometer/publish.py
"""

import datetime

from oslo.config import cfg

from ceilometer import counter
from ceilometer.openstack.common import jsonutils
from ceilometer.openstack.common import rpc as oslo_rpc
from ceilometer.publisher import rpc
from ceilometer.tests import base


def test_compute_signature_change_key():
    sig1 = rpc.compute_signature({'a': 'A', 'b': 'B'},
                                 'not-so-secret')
    sig2 = rpc.compute_signature({'A': 'A', 'b': 'B'},
                                 'not-so-secret')
    assert sig1 != sig2


def test_compute_signature_change_value():
    sig1 = rpc.compute_signature({'a': 'A', 'b': 'B'},
                                 'not-so-secret')
    sig2 = rpc.compute_signature({'a': 'a', 'b': 'B'},
                                 'not-so-secret')
    assert sig1 != sig2


def test_compute_signature_same():
    sig1 = rpc.compute_signature({'a': 'A', 'b': 'B'},
                                 'not-so-secret')
    sig2 = rpc.compute_signature({'a': 'A', 'b': 'B'},
                                 'not-so-secret')
    assert sig1 == sig2


def test_compute_signature_signed():
    data = {'a': 'A', 'b': 'B'}
    sig1 = rpc.compute_signature(data, 'not-so-secret')
    data['message_signature'] = sig1
    sig2 = rpc.compute_signature(data, 'not-so-secret')
    assert sig1 == sig2


def test_compute_signature_use_configured_secret():
    data = {'a': 'A', 'b': 'B'}
    sig1 = rpc.compute_signature(data, 'not-so-secret')
    sig2 = rpc.compute_signature(data, 'different-value')
    assert sig1 != sig2


def test_verify_signature_signed():
    data = {'a': 'A', 'b': 'B'}
    sig1 = rpc.compute_signature(data, 'not-so-secret')
    data['message_signature'] = sig1
    assert rpc.verify_signature(data, 'not-so-secret')


def test_verify_signature_unsigned():
    data = {'a': 'A', 'b': 'B'}
    assert not rpc.verify_signature(data, 'not-so-secret')


def test_verify_signature_incorrect():
    data = {'a': 'A', 'b': 'B',
            'message_signature': 'Not the same'}
    assert not rpc.verify_signature(data, 'not-so-secret')


def test_verify_signature_nested():
    data = {'a': 'A',
            'b': 'B',
            'nested': {'a': 'A',
                       'b': 'B',
                       },
            }
    data['message_signature'] = rpc.compute_signature(
        data,
        'not-so-secret')
    assert rpc.verify_signature(data, 'not-so-secret')


def test_verify_signature_nested_json():
    data = {'a': 'A',
            'b': 'B',
            'nested': {'a': 'A',
                       'b': 'B',
                       'c': ('c',),
                       'd': ['d']
                       },
            }
    data['message_signature'] = rpc.compute_signature(
        data,
        'not-so-secret')
    jsondata = jsonutils.loads(jsonutils.dumps(data))
    assert rpc.verify_signature(jsondata, 'not-so-secret')


TEST_COUNTER = counter.Counter(name='name',
                               type='typ',
                               unit='',
                               volume=1,
                               user_id='user',
                               project_id='project',
                               resource_id=2,
                               timestamp='today',
                               resource_metadata={'key': 'value'},
                               )

TEST_NOTICE = {
    u'_context_auth_token': u'3d8b13de1b7d499587dfc69b77dc09c2',
    u'_context_is_admin': True,
    u'_context_project_id': u'7c150a59fe714e6f9263774af9688f0e',
    u'_context_quota_class': None,
    u'_context_read_deleted': u'no',
    u'_context_remote_address': u'10.0.2.15',
    u'_context_request_id': u'req-d68b36e0-9233-467f-9afb-d81435d64d66',
    u'_context_roles': [u'admin'],
    u'_context_timestamp': u'2012-05-08T20:23:41.425105',
    u'_context_user_id': u'1e3ce043029547f1a61c1996d1a531a2',
    u'event_type': u'compute.instance.create.end',
    u'message_id': u'dae6f69c-00e0-41c0-b371-41ec3b7f4451',
    u'payload': {u'created_at': u'2012-05-08 20:23:41',
                 u'deleted_at': u'',
                 u'disk_gb': 0,
                 u'display_name': u'testme',
                 u'fixed_ips': [{u'address': u'10.0.0.2',
                                 u'floating_ips': [],
                                 u'meta': {},
                                 u'type': u'fixed',
                                 u'version': 4}],
                 u'image_ref_url': u'http://10.0.2.15:9292/images/UUID',
                 u'instance_id': u'9f9d01b9-4a58-4271-9e27-398b21ab20d1',
                 u'instance_type': u'm1.tiny',
                 u'instance_type_id': 2,
                 u'launched_at': u'2012-05-08 20:23:47.985999',
                 u'memory_mb': 512,
                 u'state': u'active',
                 u'state_description': u'',
                 u'tenant_id': u'7c150a59fe714e6f9263774af9688f0e',
                 u'user_id': u'1e3ce043029547f1a61c1996d1a531a2'},
    u'priority': u'INFO',
    u'publisher_id': u'compute.vagrant-precise',
    u'timestamp': u'2012-05-08 20:23:48.028195',
}


def test_meter_message_from_counter_signed():
    msg = rpc.meter_message_from_counter(
        TEST_COUNTER,
        'not-so-secret',
        'src')
    assert 'message_signature' in msg


def test_meter_message_from_counter_field():
    def compare(f, c, msg_f, msg):
        assert msg == c
    msg = rpc.meter_message_from_counter(
        TEST_COUNTER, 'not-so-secret',
        'src')
    name_map = {'name': 'counter_name',
                'type': 'counter_type',
                'unit': 'counter_unit',
                'volume': 'counter_volume',
                }
    for f in TEST_COUNTER._fields:
        msg_f = name_map.get(f, f)
        yield compare, f, getattr(TEST_COUNTER, f), msg_f, msg[msg_f]


class TestPublish(base.TestCase):

    test_data = [
        counter.Counter(
            name='test',
            type=counter.TYPE_CUMULATIVE,
            unit='',
            volume=1,
            user_id='test',
            project_id='test',
            resource_id='test_run_tasks',
            timestamp=datetime.datetime.utcnow().isoformat(),
            resource_metadata={'name': 'TestPublish'},
        ),
        counter.Counter(
            name='test',
            type=counter.TYPE_CUMULATIVE,
            unit='',
            volume=1,
            user_id='test',
            project_id='test',
            resource_id='test_run_tasks',
            timestamp=datetime.datetime.utcnow().isoformat(),
            resource_metadata={'name': 'TestPublish'},
        ),
        counter.Counter(
            name='test2',
            type=counter.TYPE_CUMULATIVE,
            unit='',
            volume=1,
            user_id='test',
            project_id='test',
            resource_id='test_run_tasks',
            timestamp=datetime.datetime.utcnow().isoformat(),
            resource_metadata={'name': 'TestPublish'},
        ),
        counter.Counter(
            name='test2',
            type=counter.TYPE_CUMULATIVE,
            unit='',
            volume=1,
            user_id='test',
            project_id='test',
            resource_id='test_run_tasks',
            timestamp=datetime.datetime.utcnow().isoformat(),
            resource_metadata={'name': 'TestPublish'},
        ),
        counter.Counter(
            name='test3',
            type=counter.TYPE_CUMULATIVE,
            unit='',
            volume=1,
            user_id='test',
            project_id='test',
            resource_id='test_run_tasks',
            timestamp=datetime.datetime.utcnow().isoformat(),
            resource_metadata={'name': 'TestPublish'},
        ),
    ]

    def faux_cast(self, context, topic, msg):
        self.published.append((topic, msg))

    def setUp(self):
        super(TestPublish, self).setUp()
        self.published = []
        self.stubs.Set(oslo_rpc, 'cast', self.faux_cast)
        publisher = rpc.RPCPublisher(None)
        publisher.publish_counters(None,
                                   self.test_data,
                                   'test')

    def test_published(self):
        self.assertEqual(len(self.published), 4)
        for topic, rpc_call in self.published:
            meters = rpc_call['args']['data']
            self.assertIsInstance(meters, list)
            if topic != cfg.CONF.publisher_rpc.metering_topic:
                self.assertEqual(len(set(meter['counter_name']
                                         for meter in meters)),
                                 1,
                                 "Meter are published grouped by name")

    def test_published_topics(self):
        topics = [topic for topic, meter in self.published]
        self.assertIn(cfg.CONF.publisher_rpc.metering_topic, topics)
        self.assertIn(
            cfg.CONF.publisher_rpc.metering_topic + '.' + 'test', topics)
        self.assertIn(
            cfg.CONF.publisher_rpc.metering_topic + '.' + 'test2', topics)
        self.assertIn(
            cfg.CONF.publisher_rpc.metering_topic + '.' + 'test3', topics)
