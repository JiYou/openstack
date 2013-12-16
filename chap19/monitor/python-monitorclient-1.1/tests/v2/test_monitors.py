# Copyright (c) 2013 OpenStack, LLC.
#
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from tests import utils
from tests.v2 import fakes


cs = fakes.FakeClient()


class ServiceManagesTest(utils.TestCase):

    def test_delete_monitor(self):
        v = cs.monitors.list()[0]
        v.delete()
        cs.assert_called('DELETE', '/monitors/1234')
        cs.monitors.delete('1234')
        cs.assert_called('DELETE', '/monitors/1234')
        cs.monitors.delete(v)
        cs.assert_called('DELETE', '/monitors/1234')

    def test_create_monitor(self):
        cs.monitors.create(1)
        cs.assert_called('POST', '/monitors')

    def test_attach(self):
        v = cs.monitors.get('1234')
        cs.monitors.attach(v, 1, '/dev/vdc')
        cs.assert_called('POST', '/monitors/1234/action')

    def test_detach(self):
        v = cs.monitors.get('1234')
        cs.monitors.detach(v)
        cs.assert_called('POST', '/monitors/1234/action')

    def test_reserve(self):
        v = cs.monitors.get('1234')
        cs.monitors.reserve(v)
        cs.assert_called('POST', '/monitors/1234/action')

    def test_unreserve(self):
        v = cs.monitors.get('1234')
        cs.monitors.unreserve(v)
        cs.assert_called('POST', '/monitors/1234/action')

    def test_begin_detaching(self):
        v = cs.monitors.get('1234')
        cs.monitors.begin_detaching(v)
        cs.assert_called('POST', '/monitors/1234/action')

    def test_roll_detaching(self):
        v = cs.monitors.get('1234')
        cs.monitors.roll_detaching(v)
        cs.assert_called('POST', '/monitors/1234/action')

    def test_initialize_connection(self):
        v = cs.monitors.get('1234')
        cs.monitors.initialize_connection(v, {})
        cs.assert_called('POST', '/monitors/1234/action')

    def test_terminate_connection(self):
        v = cs.monitors.get('1234')
        cs.monitors.terminate_connection(v, {})
        cs.assert_called('POST', '/monitors/1234/action')

    def test_set_metadata(self):
        cs.monitors.set_metadata(1234, {'k1': 'v2'})
        cs.assert_called('POST', '/monitors/1234/metadata',
                         {'metadata': {'k1': 'v2'}})

    def test_delete_metadata(self):
        keys = ['key1']
        cs.monitors.delete_metadata(1234, keys)
        cs.assert_called('DELETE', '/monitors/1234/metadata/key1')
