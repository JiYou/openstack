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
"""Tests for ceilometer/agent/manager.py
"""

from datetime import datetime
import msgpack
import socket

from mock import patch
from mock import MagicMock
from oslo.config import cfg
from stevedore import extension
from stevedore.tests import manager as test_manager

from ceilometer import counter
from ceilometer.publisher import rpc
from ceilometer.collector import service
from ceilometer.storage import base
from ceilometer.tests import base as tests_base
from ceilometer.compute import notifications


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
                 u'user_id': u'1e3ce043029547f1a61c1996d1a531a2',
                 u'reservation_id': u'1e3ce043029547f1a61c1996d1a531a3',
                 u'vcpus': 1,
                 u'root_gb': 0,
                 u'ephemeral_gb': 0,
                 u'host': u'compute-host-name',
                 u'availability_zone': u'1e3ce043029547f1a61c1996d1a531a4',
                 u'os_type': u'linux?',
                 u'architecture': u'x86',
                 u'image_ref': u'UUID',
                 u'kernel_id': u'1e3ce043029547f1a61c1996d1a531a5',
                 u'ramdisk_id': u'1e3ce043029547f1a61c1996d1a531a6',
                 },
    u'priority': u'INFO',
    u'publisher_id': u'compute.vagrant-precise',
    u'timestamp': u'2012-05-08 20:23:48.028195',
}


class TestCollector(tests_base.TestCase):
    def setUp(self):
        super(TestCollector, self).setUp()
        cfg.CONF.set_override("connection", "log://", group='database')


class TestUDPCollectorService(TestCollector):
    def _make_fake_socket(self, family, type):
        udp_socket = self.mox.CreateMockAnything()
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        udp_socket.bind((cfg.CONF.collector.udp_address,
                         cfg.CONF.collector.udp_port))

        def stop_udp(anything):
            # Make the loop stop
            self.srv.stop()

        udp_socket.recvfrom(64 * 1024).WithSideEffects(
            stop_udp).AndReturn(
                (msgpack.dumps(self.counter),
                 ('127.0.0.1', 12345)))

        self.mox.ReplayAll()

        return udp_socket

    def setUp(self):
        super(TestUDPCollectorService, self).setUp()
        self.srv = service.UDPCollectorService()
        self.counter = dict(counter.Counter(
            name='foobar',
            type='bad',
            unit='F',
            volume=1,
            user_id='jd',
            project_id='ceilometer',
            resource_id='cat',
            timestamp='NOW!',
            resource_metadata={},
        )._asdict())

    def test_udp_receive(self):
        self.srv.storage_conn = self.mox.CreateMock(base.Connection)
        self.counter['source'] = 'mysource'
        self.counter['counter_name'] = self.counter['name']
        self.counter['counter_volume'] = self.counter['volume']
        self.counter['counter_type'] = self.counter['type']
        self.counter['counter_unit'] = self.counter['unit']
        self.srv.storage_conn.record_metering_data(self.counter)
        self.mox.ReplayAll()

        with patch('socket.socket', self._make_fake_socket):
            self.srv.start()

    @staticmethod
    def _raise_error():
        raise Exception

    def test_udp_receive_bad_decoding(self):
        with patch('socket.socket', self._make_fake_socket):
            with patch('msgpack.loads', self._raise_error):
                self.srv.start()

    def test_udp_receive_storage_error(self):
        self.srv.storage_conn = self.mox.CreateMock(base.Connection)
        self.counter['source'] = 'mysource'
        self.counter['counter_name'] = self.counter['name']
        self.counter['counter_volume'] = self.counter['volume']
        self.counter['counter_type'] = self.counter['type']
        self.counter['counter_unit'] = self.counter['unit']
        self.srv.storage_conn.record_metering_data(
            self.counter).AndRaise(IOError)
        self.mox.ReplayAll()

        with patch('socket.socket', self._make_fake_socket):
            self.srv.start()


class TestCollectorService(TestCollector):

    def setUp(self):
        super(TestCollectorService, self).setUp()
        self.srv = service.CollectorService('the-host', 'the-topic')
        self.ctx = None

    @patch('ceilometer.pipeline.setup_pipeline', MagicMock())
    def test_init_host(self):
        # If we try to create a real RPC connection, init_host() never
        # returns. Mock it out so we can establish the manager
        # configuration.
        with patch('ceilometer.openstack.common.rpc.create_connection'):
            self.srv.start()

    def test_valid_message(self):
        msg = {'counter_name': 'test',
               'resource_id': self.id(),
               'counter_volume': 1,
               }
        msg['message_signature'] = rpc.compute_signature(
            msg,
            cfg.CONF.publisher_rpc.metering_secret,
        )

        self.srv.storage_conn = self.mox.CreateMock(base.Connection)
        self.srv.storage_conn.record_metering_data(msg)
        self.mox.ReplayAll()

        self.srv.record_metering_data(self.ctx, msg)
        self.mox.VerifyAll()

    def test_invalid_message(self):
        msg = {'counter_name': 'test',
               'resource_id': self.id(),
               'counter_volume': 1,
               }
        msg['message_signature'] = 'invalid-signature'

        class ErrorConnection:

            called = False

            def record_metering_data(self, data):
                self.called = True

        self.srv.storage_conn = ErrorConnection()

        self.srv.record_metering_data(self.ctx, msg)

        assert not self.srv.storage_conn.called, \
            'Should not have called the storage connection'

    def test_timestamp_conversion(self):
        msg = {'counter_name': 'test',
               'resource_id': self.id(),
               'counter_volume': 1,
               'timestamp': '2012-07-02T13:53:40Z',
               }
        msg['message_signature'] = rpc.compute_signature(
            msg,
            cfg.CONF.publisher_rpc.metering_secret,
        )

        expected = {}
        expected.update(msg)
        expected['timestamp'] = datetime(2012, 7, 2, 13, 53, 40)

        self.srv.storage_conn = self.mox.CreateMock(base.Connection)
        self.srv.storage_conn.record_metering_data(expected)
        self.mox.ReplayAll()

        self.srv.record_metering_data(self.ctx, msg)

    def test_timestamp_tzinfo_conversion(self):
        msg = {'counter_name': 'test',
               'resource_id': self.id(),
               'counter_volume': 1,
               'timestamp': '2012-09-30T15:31:50.262-08:00',
               }
        msg['message_signature'] = rpc.compute_signature(
            msg,
            cfg.CONF.publisher_rpc.metering_secret,
        )

        expected = {}
        expected.update(msg)
        expected['timestamp'] = datetime(2012, 9, 30, 23, 31, 50, 262000)

        self.srv.storage_conn = self.mox.CreateMock(base.Connection)
        self.srv.storage_conn.record_metering_data(expected)
        self.mox.ReplayAll()

        self.srv.record_metering_data(self.ctx, msg)

    @patch('ceilometer.pipeline.setup_pipeline', MagicMock())
    def test_process_notification(self):
        # If we try to create a real RPC connection, init_host() never
        # returns. Mock it out so we can establish the manager
        # configuration.
        with patch('ceilometer.openstack.common.rpc.create_connection'):
            self.srv.start()
        self.srv.pipeline_manager.pipelines[0] = MagicMock()
        self.srv.notification_manager = test_manager.TestExtensionManager(
            [extension.Extension('test',
                                 None,
                                 None,
                                 notifications.Instance(),
                                 ),
             ])
        self.srv.process_notification(TEST_NOTICE)
        self.assertTrue(
            self.srv.pipeline_manager.publisher.called)
