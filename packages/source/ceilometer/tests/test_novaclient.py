#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# Copyright © 2013 eNovance <licensing@enovance.com>
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

import mock

from ceilometer.tests import base
from ceilometer import nova_client


class TestNovaClient(base.TestCase):

    def setUp(self):
        super(TestNovaClient, self).setUp()
        self.nv = nova_client.Client()

    @staticmethod
    def fake_flavors_list():
        a = mock.MagicMock()
        a.id = 1
        a.name = 'm1.tiny'
        b = mock.MagicMock()
        b.id = 2
        b.name = 'm1.large'
        return [a, b]

    @staticmethod
    def fake_servers_list(*args, **kwargs):
        a = mock.MagicMock()
        a.id = 42
        a.flavor = {'id': 1}
        return [a]

    def test_instance_get_all_by_host(self):
        self.stubs.Set(self.nv.nova_client.flavors, 'list',
                       self.fake_flavors_list)
        self.stubs.Set(self.nv.nova_client.servers, 'list',
                       self.fake_servers_list)

        instances = self.nv.instance_get_all_by_host('foobar')
        self.assertEqual(len(instances), 1)
        self.assertEqual(instances[0].flavor['name'], 'm1.tiny')

    @staticmethod
    def fake_servers_list_unknown_flavor(*args, **kwargs):
        a = mock.MagicMock()
        a.id = 42
        a.flavor = {'id': 666}
        return [a]

    def test_instance_get_all_by_host_unknown_flavor(self):
        self.stubs.Set(self.nv.nova_client.flavors, 'list',
                       self.fake_flavors_list)
        self.stubs.Set(self.nv.nova_client.servers, 'list',
                       self.fake_servers_list_unknown_flavor)

        instances = self.nv.instance_get_all_by_host('foobar')
        self.assertEqual(len(instances), 1)
        self.assertEqual(instances[0].flavor['name'], 'unknown-id-666')
