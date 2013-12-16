# -*- coding: utf-8 -*-
#
# Author: François Rossigneux <francois.rossigneux@inria.fr>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import datetime
import mock

from ceilometer.tests import base
from ceilometer.energy import kwapi
from ceilometer.central import manager
from ceilometer.openstack.common import context

from keystoneclient import exceptions

PROBE_DICT = {
    "probes": {
        "A": {
            "timestamp": 1357730232.68754,
            "w": 107.3,
            "kwh": 0.001058255421506034
        },
        "B": {
            "timestamp": 1357730232.048158,
            "w": 15.0,
            "kwh": 0.029019045026169896
        },
        "C": {
            "timestamp": 1357730232.223375,
            "w": 95.0,
            "kwh": 0.17361822634312918
        }
    }
}


class TestManager(manager.AgentManager):

    def __init__(self):
        super(TestManager, self).__init__()
        self.keystone = None


class TestKwapiPollster(base.TestCase):

    @staticmethod
    def fake_kwapi_iter_probes(self, ksclient):
        probes = PROBE_DICT['probes']
        for key, value in probes.iteritems():
            probe_dict = value
            probe_dict['id'] = key
            yield probe_dict

    @staticmethod
    def fake_kwapi_get_kwapi_client(self, ksclient):
        raise exceptions.EndpointNotFound("fake keystone exception")

    @mock.patch('ceilometer.pipeline.setup_pipeline', mock.MagicMock())
    def setUp(self):
        super(TestKwapiPollster, self).setUp()
        self.context = context.get_admin_context()
        self.manager = TestManager()

    def test_kwapi_endpoint_not_exist(self):
        self.stubs.Set(kwapi._Base, 'get_kwapi_client',
                       self.fake_kwapi_get_kwapi_client)

        counters = list(kwapi.KwapiPollster().get_counters(self.manager))
        self.assertEqual(len(counters), 0)

    def test_kwapi_counter(self):
        self.stubs.Set(kwapi._Base, 'iter_probes', self.fake_kwapi_iter_probes)

        counters = list(kwapi.KwapiPollster().get_counters(self.manager))
        self.assertEqual(len(counters), 6)
        energy_counters = [counter for counter in counters
                           if counter.name == "energy"]
        power_counters = [counter for counter in counters
                          if counter.name == "power"]
        for probe in PROBE_DICT['probes'].values():
            self.assert_(
                any(map(lambda counter: counter.timestamp ==
                    datetime.datetime.fromtimestamp(
                        probe['timestamp']).isoformat(),
                        counters)))
            self.assert_(
                any(map(lambda counter: counter.volume == probe['kwh'],
                        energy_counters)))
            self.assert_(
                any(map(lambda counter: counter.volume == probe['w'],
                        power_counters)))

    def test_kwapi_counter_list(self):
        self.stubs.Set(kwapi._Base, 'iter_probes', self.fake_kwapi_iter_probes)

        counters = list(kwapi.KwapiPollster().get_counters(self.manager))
        self.assertEqual(set([c.name for c in counters]),
                         set(kwapi.KwapiPollster().get_counter_names()))
