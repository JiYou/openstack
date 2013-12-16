# -*- encoding: utf-8 -*-
#
# Copyright © 2013 eNovance
#
# Author: Julien Danjou <julien@danjou.info>
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
"""Tests for ceilometer/publisher/udp.py
"""

import datetime
import mock
import msgpack
from oslo.config import cfg
import urlparse

from ceilometer import counter
from ceilometer.publisher import udp
from ceilometer.tests import base


class TestUDPPublisher(base.TestCase):

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

    def _make_fake_socket(self, published):
        def _fake_socket_socket(family, type):
            def record_data(msg, dest):
                published.append((msg, dest))
            udp_socket = self.mox.CreateMockAnything()
            udp_socket.sendto = record_data
            self.mox.ReplayAll()
            return udp_socket
        return _fake_socket_socket

    COUNTER_SOURCE = 'testsource'

    def test_published(self):
        self.data_sent = []
        with mock.patch('socket.socket',
                        self._make_fake_socket(self.data_sent)):
            publisher = udp.UDPPublisher(urlparse.urlparse('udp://somehost'))
        publisher.publish_counters(None,
                                   self.test_data,
                                   self.COUNTER_SOURCE)

        self.assertEqual(len(self.data_sent), 5)

        sent_counters = []

        for data, dest in self.data_sent:
            counter = msgpack.loads(data)
            self.assertEqual(counter['source'], self.COUNTER_SOURCE)
            # Remove source because our test Counters don't have it, so the
            # comparison would fail later
            del counter['source']
            sent_counters.append(counter)

            # Check destination
            self.assertEqual(dest, ('somehost',
                                    cfg.CONF.collector.udp_port))

        # Check that counters are equal
        self.assertEqual(sorted(sent_counters),
                         sorted([dict(d._asdict()) for d in self.test_data]))

    @staticmethod
    def _raise_ioerror():
        raise IOError

    def _make_broken_socket(self, family, type):
        udp_socket = self.mox.CreateMockAnything()
        udp_socket.sendto = self._raise_ioerror
        self.mox.ReplayAll()

    def test_publish_error(self):
        with mock.patch('socket.socket',
                        self._make_broken_socket):
            publisher = udp.UDPPublisher(urlparse.urlparse('udp://localhost'))
        publisher.publish_counters(None,
                                   self.test_data,
                                   self.COUNTER_SOURCE)
