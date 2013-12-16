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
"""Tests for ceilometer.compute.instance
"""

import mock

from ceilometer.compute import instance
from ceilometer.compute import manager
from ceilometer.tests import base


class FauxInstance(object):

    def __init__(self, **kwds):
        for name, value in kwds.items():
            setattr(self, name, value)

    def __getitem__(self, key):
        return getattr(self, key)

    def get(self, key, default):
        try:
            return getattr(self, key)
        except AttributeError:
            return default


class TestLocationMetadata(base.TestCase):

    @mock.patch('ceilometer.pipeline.setup_pipeline', mock.MagicMock())
    def setUp(self):
        self.manager = manager.AgentManager()
        super(TestLocationMetadata, self).setUp()

        # Mimics an instance returned from nova api call
        self.INSTANCE_PROPERTIES = {'name': 'display name',
                                    'OS-EXT-SRV-ATTR:instance_name':
                                    'instance-000001',
                                    'reservation_id': 'reservation id',
                                    'architecture': 'x86_64',
                                    'availability_zone': 'zone1',
                                    'kernel_id': 'kernel id',
                                    'os_type': 'linux',
                                    'ramdisk_id': 'ramdisk id',
                                    'disk_gb': 10,
                                    'ephemeral_gb': 7,
                                    'memory_mb': 2048,
                                    'root_gb': 3,
                                    'vcpus': 1,
                                    'image': {'id': 1,
                                              'links': [{"rel": "bookmark",
                                                         'href': 2}]},
                                    'flavor': {'id': 1},
                                    'hostId': '1234-5678'}

        self.instance = FauxInstance(**self.INSTANCE_PROPERTIES)
        self.instance.host = 'made-up-hostname'
        m = mock.MagicMock()
        m.flavorid = 1
        self.instance.instance_type = m

    def test_metadata(self):
        md = instance.get_metadata_from_object(self.instance)
        iprops = self.INSTANCE_PROPERTIES
        for name in md.keys():
            actual = md[name]
            print 'checking', name, actual
            if name == 'name':
                assert actual == iprops['OS-EXT-SRV-ATTR:instance_name']
            elif name == 'host':
                assert actual == iprops['hostId']
            elif name == 'display_name':
                assert actual == iprops['name']
            elif name == 'instance_type':
                assert actual == iprops['flavor']['id']
            elif name == 'image_ref':
                assert actual == iprops['image']['id']
            elif name == 'image_ref_url':
                assert actual == iprops['image']['links'][0]['href']
            else:
                assert actual == iprops[name]

    def test_metadata_empty_image(self):
        self.INSTANCE_PROPERTIES['image'] = ''
        self.instance = FauxInstance(**self.INSTANCE_PROPERTIES)
        md = instance.get_metadata_from_object(self.instance)
        self.assertEqual(md['image_ref'], None)
        self.assertEqual(md['image_ref_url'], None)
