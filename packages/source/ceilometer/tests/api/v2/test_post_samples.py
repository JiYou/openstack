# -*- encoding: utf-8 -*-
#
# Copyright © 2013 Red Hat, Inc
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
"""Test listing raw events.
"""

import copy
import datetime
import logging

from ceilometer.openstack.common import rpc
from ceilometer.openstack.common import timeutils

from .base import FunctionalTest

LOG = logging.getLogger(__name__)


class TestPostSamples(FunctionalTest):

    def faux_cast(self, context, topic, msg):
        self.published.append((topic, msg))

    def setUp(self):
        super(TestPostSamples, self).setUp()
        self.published = []
        self.stubs.Set(rpc, 'cast', self.faux_cast)

    def test_one(self):
        s1 = [{'counter_name': 'apples',
               'counter_type': 'gauge',
               'counter_unit': 'instance',
               'counter_volume': 1,
               'resource_id': 'bd9431c1-8d69-4ad3-803a-8d4a6b89fd36',
               'project_id': '35b17138-b364-4e6a-a131-8f3099c5be68',
               'user_id': 'efd87807-12d2-4b38-9c70-5f5c2ac427ff',
               'resource_metadata': {'name1': 'value1',
                                     'name2': 'value2'}}]

        data = self.post_json('/meters/apples/', s1)

        # timestamp not given so it is generated.
        s1[0]['timestamp'] = data.json[0]['timestamp']
        # source is generated if not provided.
        s1[0]['source'] = '%s:openstack' % s1[0]['project_id']

        self.assertEquals(s1, data.json)

    def test_wrong_project_id(self):
        """Do not accept cross posting samples to different projects."""
        s1 = [{'counter_name': 'my_counter_name',
               'counter_type': 'gauge',
               'counter_unit': 'instance',
               'counter_volume': 1,
               'source': 'closedstack',
               'resource_id': 'bd9431c1-8d69-4ad3-803a-8d4a6b89fd36',
               'project_id': '35b17138-b364-4e6a-a131-8f3099c5be68',
               'user_id': 'efd87807-12d2-4b38-9c70-5f5c2ac427ff',
               'resource_metadata': {'name1': 'value1',
                                     'name2': 'value2'}}]

        data = self.post_json('/meters/my_counter_name/', s1,
                              expect_errors=True,
                              headers={
                                  "X-Roles": "Member",
                                  "X-Tenant-Name": "lu-tenant",
                                  "X-Tenant-Id":
                                  "bc23a9d531064583ace8f67dad60f6bb",
                              })

        self.assertEquals(data.status_int, 400)

    def test_multiple_samples(self):
        """Send multiple samples.
        The usecase here is to reduce the chatter and send the counters
        at a slower cadence.
        """
        samples = []
        stamps = []
        for x in range(6):
            dt = datetime.datetime(2012, 8, 27, x, 0, tzinfo=None)
            stamps.append(dt)
            s = {'counter_name': 'apples',
                 'counter_type': 'gauge',
                 'counter_unit': 'instance',
                 'counter_volume': float(x * 3),
                 'source': 'evil',
                 'timestamp': dt.isoformat(),
                 'resource_id': 'bd9431c1-8d69-4ad3-803a-8d4a6b89fd36',
                 'project_id': '35b17138-b364-4e6a-a131-8f3099c5be68',
                 'user_id': 'efd87807-12d2-4b38-9c70-5f5c2ac427ff',
                 'resource_metadata': {'name1': str(x),
                                       'name2': str(x + 4)}}
            samples.append(s)

        data = self.post_json('/meters/apples/', samples)

        # source is modified to include the project_id.
        for x in range(6):
            for (k, v) in samples[x].iteritems():
                if k == 'timestamp':
                    timestamp = timeutils.parse_isotime(data.json[x][k])
                    self.assertEquals(stamps[x].replace(tzinfo=None),
                                      timestamp.replace(tzinfo=None))
                elif k == 'source':
                    self.assertEquals(data.json[x][k],
                                      '%s:%s' % (samples[x]['project_id'],
                                                 samples[x]['source']))
                else:
                    self.assertEquals(v, data.json[x][k])

    def test_missing_mandatory_fields(self):
        """Do not accept posting samples with missing mandatory fields."""
        s1 = [{'counter_name': 'my_counter_name',
               'counter_type': 'gauge',
               'counter_unit': 'instance',
               'counter_volume': 1,
               'source': 'closedstack',
               'resource_id': 'bd9431c1-8d69-4ad3-803a-8d4a6b89fd36',
               'project_id': '35b17138-b364-4e6a-a131-8f3099c5be68',
               'user_id': 'efd87807-12d2-4b38-9c70-5f5c2ac427ff',
               'resource_metadata': {'name1': 'value1',
                                     'name2': 'value2'}}]

        # one by one try posting without a mandatory field.
        for m in ['counter_volume', 'counter_unit', 'counter_type',
                  'resource_id', 'counter_name']:
            s_broke = copy.copy(s1)
            del s_broke[0][m]
            print('posting without %s' % m)
            data = self.post_json('/meters/my_counter_name/', s_broke,
                                  expect_errors=True)
            self.assertEquals(data.status_int, 400)

    def test_multiple_sources(self):
        """Do not accept a single post of mixed sources."""
        s1 = [{'counter_name': 'my_counter_name',
               'counter_type': 'gauge',
               'counter_unit': 'instance',
               'counter_volume': 1,
               'source': 'closedstack',
               'project_id': '35b17138-b364-4e6a-a131-8f3099c5be68',
               'user_id': 'efd87807-12d2-4b38-9c70-5f5c2ac427ff',
               'resource_id': 'bd9431c1-8d69-4ad3-803a-8d4a6b89fd36',
               },
              {'counter_name': 'my_counter_name',
               'counter_type': 'gauge',
               'counter_unit': 'instance',
               'counter_volume': 2,
               'source': 'not this',
               'project_id': '35b17138-b364-4e6a-a131-8f3099c5be68',
               'user_id': 'efd87807-12d2-4b38-9c70-5f5c2ac427ff',
               'resource_id': 'bd9431c1-8d69-4ad3-803a-8d4a6b89fd36',
               'resource_metadata': {'name1': 'value1',
                                     'name2': 'value2'}}]
        data = self.post_json('/meters/my_counter_name/', s1,
                              expect_errors=True)
        self.assertEquals(data.status_int, 400)

    def test_multiple_samples_some_null_sources(self):
        """Do accept a single post with some null sources
        this is a convience feature so you only have to set
        one of the sample's source field.
        """
        s1 = [{'counter_name': 'my_counter_name',
               'counter_type': 'gauge',
               'counter_unit': 'instance',
               'counter_volume': 1,
               'source': 'paperstack',
               'project_id': '35b17138-b364-4e6a-a131-8f3099c5be68',
               'user_id': 'efd87807-12d2-4b38-9c70-5f5c2ac427ff',
               'resource_id': 'bd9431c1-8d69-4ad3-803a-8d4a6b89fd36',
               },
              {'counter_name': 'my_counter_name',
               'counter_type': 'gauge',
               'counter_unit': 'instance',
               'counter_volume': 2,
               'project_id': '35b17138-b364-4e6a-a131-8f3099c5be68',
               'user_id': 'efd87807-12d2-4b38-9c70-5f5c2ac427ff',
               'resource_id': 'bd9431c1-8d69-4ad3-803a-8d4a6b89fd36',
               'resource_metadata': {'name1': 'value1',
                                     'name2': 'value2'}}]
        data = self.post_json('/meters/my_counter_name/', s1,
                              expect_errors=True)
        self.assertEquals(data.status_int, 200)
        for x in range(2):
            for (k, v) in s1[x].iteritems():
                if k == 'source':
                    self.assertEquals(data.json[x][k],
                                      '%s:%s' % (s1[x]['project_id'],
                                                 'paperstack'))
