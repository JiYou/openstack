#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# Copyright © 2012 eNovance <licensing@enovance.com>
#
# Author: Guillaume Pernot <gpernot@praksys.org>
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

from ceilometer.central import manager
from ceilometer.objectstore import swift
from ceilometer.tests import base

from keystoneclient import exceptions

ACCOUNTS = [('tenant-000', {'x-account-object-count': 12,
                            'x-account-bytes-used': 321321321,
                            'x-account-container-count': 7,
                            }),
            ('tenant-001', {'x-account-object-count': 34,
                            'x-account-bytes-used': 9898989898,
                            'x-account-container-count': 17,
                            })]


class TestManager(manager.AgentManager):

    def __init__(self):
        super(TestManager, self).__init__()
        self.keystone = mock.MagicMock()


class TestSwiftPollster(base.TestCase):

    @staticmethod
    def fake_ks_service_catalog_url_for(*args, **kwargs):
        raise exceptions.EndpointNotFound("Fake keystone exception")

    @staticmethod
    def fake_iter_accounts(self, ksclient):
        for i in ACCOUNTS:
            yield i

    @mock.patch('ceilometer.pipeline.setup_pipeline', mock.MagicMock())
    def setUp(self):
        super(TestSwiftPollster, self).setUp()
        self.pollster = swift.SwiftPollster()
        self.manager = TestManager()

    def test_objectstore_neaten_url(self):
        test_endpoint = 'http://127.0.0.1:8080'
        test_tenant_id = 'a7fd1695fa154486a647e44aa99a1b9b'
        standard_url = test_endpoint + '/v1/' + 'AUTH_' + test_tenant_id

        self.assertEqual(standard_url,
                         self.pollster._neaten_url(test_endpoint,
                                                   test_tenant_id))
        self.assertEqual(standard_url,
                         self.pollster._neaten_url(test_endpoint + '/',
                                                   test_tenant_id))
        self.assertEqual(standard_url,
                         self.pollster._neaten_url(test_endpoint + '/v1',
                                                   test_tenant_id))

    def test_objectstore_metering(self):
        self.stubs.Set(swift.SwiftPollster, 'iter_accounts',
                       self.fake_iter_accounts)
        counters = list(self.pollster.get_counters(self.manager))
        self.assertEqual(len(counters), 6)

    def test_objectstore_get_counter_names(self):
        self.stubs.Set(swift.SwiftPollster, 'iter_accounts',
                       self.fake_iter_accounts)
        counters = list(self.pollster.get_counters(self.manager))
        self.assertEqual(set([c.name for c in counters]),
                         set(self.pollster.get_counter_names()))

    def test_objectstore_endpoint_notfound(self):
        self.stubs.Set(self.manager.keystone.service_catalog, 'url_for',
                       self.fake_ks_service_catalog_url_for)
        counters = list(self.pollster.get_counters(self.manager))
        self.assertEqual(len(counters), 0)
