# -*- encoding: utf-8 -*-
#
# Copyright © 2012 New Dream Network, LLC (DreamHost)
# Copyright © 2013 eNovance
#
# Author: Doug Hellmann <doug.hellmann@dreamhost.com>
#         Julien Danjou <julien@danjou.info>
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
"""Tests for converters for producing compute counter messages from
notification events.
"""

from ceilometer.tests import base
from ceilometer.compute import notifications
from ceilometer import counter


INSTANCE_CREATE_END = {
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

INSTANCE_DELETE_START = {
    u'_context_auth_token': u'3d8b13de1b7d499587dfc69b77dc09c2',
    u'_context_is_admin': True,
    u'_context_project_id': u'7c150a59fe714e6f9263774af9688f0e',
    u'_context_quota_class': None,
    u'_context_read_deleted': u'no',
    u'_context_remote_address': u'10.0.2.15',
    u'_context_request_id': u'req-fb3c4546-a2e5-49b7-9fd2-a63bd658bc39',
    u'_context_roles': [u'admin'],
    u'_context_timestamp': u'2012-05-08T20:24:14.547374',
    u'_context_user_id': u'1e3ce043029547f1a61c1996d1a531a2',
    u'event_type': u'compute.instance.delete.start',
    u'message_id': u'a15b94ee-cb8e-4c71-9abe-14aa80055fb4',
    u'payload': {u'created_at': u'2012-05-08 20:23:41',
                 u'deleted_at': u'',
                 u'disk_gb': 0,
                 u'display_name': u'testme',
                 u'image_ref_url': u'http://10.0.2.15:9292/images/UUID',
                 u'instance_id': u'9f9d01b9-4a58-4271-9e27-398b21ab20d1',
                 u'instance_type': u'm1.tiny',
                 u'instance_type_id': 2,
                 u'launched_at': u'2012-05-08 20:23:47',
                 u'memory_mb': 512,
                 u'state': u'active',
                 u'state_description': u'deleting',
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
    u'timestamp': u'2012-05-08 20:24:14.824743',
}

INSTANCE_EXISTS = {
    u'_context_auth_token': None,
    u'_context_is_admin': True,
    u'_context_project_id': None,
    u'_context_quota_class': None,
    u'_context_read_deleted': u'no',
    u'_context_remote_address': None,
    u'_context_request_id': u'req-659a8eb2-4372-4c01-9028-ad6e40b0ed22',
    u'_context_roles': [u'admin'],
    u'_context_timestamp': u'2012-05-08T16:03:43.760204',
    u'_context_user_id': None,
    u'event_type': u'compute.instance.exists',
    u'message_id': u'4b884c03-756d-4c06-8b42-80b6def9d302',
    u'payload': {u'audit_period_beginning': u'2012-05-08 15:00:00',
                 u'audit_period_ending': u'2012-05-08 16:00:00',
                 u'bandwidth': {},
                 u'created_at': u'2012-05-07 22:16:18',
                 u'deleted_at': u'',
                 u'disk_gb': 0,
                 u'display_name': u'testme',
                 u'image_ref_url': u'http://10.0.2.15:9292/images/UUID',
                 u'instance_id': u'3a513875-95c9-4012-a3e7-f90c678854e5',
                 u'instance_type': u'm1.tiny',
                 u'instance_type_id': 2,
                 u'launched_at': u'2012-05-07 23:01:27',
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
    u'timestamp': u'2012-05-08 16:03:44.122481',
}

INSTANCE_FINISH_RESIZE_END = {
    u'_context_roles': [u'admin'],
    u'_context_request_id': u'req-e3f71bb9-e9b9-418b-a9db-a5950c851b25',
    u'_context_quota_class': None,
    u'event_type': u'compute.instance.finish_resize.end',
    u'_context_user_name': u'admin',
    u'_context_project_name': u'admin',
    u'timestamp': u'2013-01-04 15:10:17.436974',
    u'_context_is_admin': True,
    u'message_id': u'a2f7770d-b85d-4797-ab10-41407a44368e',
    u'_context_auth_token': None,
    u'_context_instance_lock_checked': False,
    u'_context_project_id': u'cea4b25edb484e5392727181b7721d29',
    u'_context_timestamp': u'2013-01-04T15:08:39.162612',
    u'_context_read_deleted': u'no',
    u'_context_user_id': u'01b83a5e23f24a6fb6cd073c0aee6eed',
    u'_context_remote_address': u'10.147.132.184',
    u'publisher_id': u'compute.ip-10-147-132-184.ec2.internal',
    u'payload': {u'state_description': u'',
                 u'availability_zone': None,
                 u'ephemeral_gb': 0,
                 u'instance_type_id': 5,
                 u'deleted_at': u'',
                 u'fixed_ips': [{u'floating_ips': [],
                                 u'label': u'private',
                                 u'version': 4,
                                 u'meta': {},
                                 u'address': u'10.0.0.3',
                                 u'type': u'fixed'}],
                 u'memory_mb': 2048,
                 u'user_id': u'01b83a5e23f24a6fb6cd073c0aee6eed',
                 u'reservation_id': u'r-u3fvim06',
                 u'hostname': u's1',
                 u'state': u'resized',
                 u'launched_at': u'2013-01-04T15:10:14.923939',
                 u'metadata': [],
                 u'ramdisk_id': u'5f23128e-5525-46d8-bc66-9c30cd87141a',
                 u'access_ip_v6': None,
                 u'disk_gb': 20,
                 u'access_ip_v4': None,
                 u'kernel_id': u'571478e0-d5e7-4c2e-95a5-2bc79443c28a',
                 u'host': u'ip-10-147-132-184.ec2.internal',
                 u'display_name': u's1',
                 u'image_ref_url': u'http://10.147.132.184:9292/images/'
                 'a130b9d9-e00e-436e-9782-836ccef06e8a',
                 u'root_gb': 20,
                 u'tenant_id': u'cea4b25edb484e5392727181b7721d29',
                 u'created_at': u'2013-01-04T11:21:48.000000',
                 u'instance_id': u'648e8963-6886-4c3c-98f9-4511c292f86b',
                 u'instance_type': u'm1.small',
                 u'vcpus': 1,
                 u'image_meta': {u'kernel_id':
                                 u'571478e0-d5e7-4c2e-95a5-2bc79443c28a',
                                 u'ramdisk_id':
                                 u'5f23128e-5525-46d8-bc66-9c30cd87141a',
                                 u'base_image_ref':
                                 u'a130b9d9-e00e-436e-9782-836ccef06e8a'},
                 u'architecture': None,
                 u'os_type': None
                 },
    u'priority': u'INFO'
}

INSTANCE_RESIZE_REVERT_END = {
    u'_context_roles': [u'admin'],
    u'_context_request_id': u'req-9da1d714-dabe-42fd-8baa-583e57cd4f1a',
    u'_context_quota_class': None,
    u'event_type': u'compute.instance.resize.revert.end',
    u'_context_user_name': u'admin',
    u'_context_project_name': u'admin',
    u'timestamp': u'2013-01-04 15:20:32.009532',
    u'_context_is_admin': True,
    u'message_id': u'c48deeba-d0c3-4154-b3db-47480b52267a',
    u'_context_auth_token': None,
    u'_context_instance_lock_checked': False,
    u'_context_project_id': u'cea4b25edb484e5392727181b7721d29',
    u'_context_timestamp': u'2013-01-04T15:19:51.018218',
    u'_context_read_deleted': u'no',
    u'_context_user_id': u'01b83a5e23f24a6fb6cd073c0aee6eed',
    u'_context_remote_address': u'10.147.132.184',
    u'publisher_id': u'compute.ip-10-147-132-184.ec2.internal',
    u'payload': {u'state_description': u'resize_reverting',
                 u'availability_zone': None,
                 u'ephemeral_gb': 0,
                 u'instance_type_id': 2,
                 u'deleted_at': u'',
                 u'reservation_id': u'r-u3fvim06',
                 u'memory_mb': 512,
                 u'user_id': u'01b83a5e23f24a6fb6cd073c0aee6eed',
                 u'hostname': u's1',
                 u'state': u'resized',
                 u'launched_at': u'2013-01-04T15:10:14.000000',
                 u'metadata': [],
                 u'ramdisk_id': u'5f23128e-5525-46d8-bc66-9c30cd87141a',
                 u'access_ip_v6': None,
                 u'disk_gb': 0,
                 u'access_ip_v4': None,
                 u'kernel_id': u'571478e0-d5e7-4c2e-95a5-2bc79443c28a',
                 u'host': u'ip-10-147-132-184.ec2.internal',
                 u'display_name': u's1',
                 u'image_ref_url': u'http://10.147.132.184:9292/images/'
                 'a130b9d9-e00e-436e-9782-836ccef06e8a',
                 u'root_gb': 0,
                 u'tenant_id': u'cea4b25edb484e5392727181b7721d29',
                 u'created_at': u'2013-01-04T11:21:48.000000',
                 u'instance_id': u'648e8963-6886-4c3c-98f9-4511c292f86b',
                 u'instance_type': u'm1.tiny',
                 u'vcpus': 1,
                 u'image_meta': {u'kernel_id':
                                 u'571478e0-d5e7-4c2e-95a5-2bc79443c28a',
                                 u'ramdisk_id':
                                 u'5f23128e-5525-46d8-bc66-9c30cd87141a',
                                 u'base_image_ref':
                                 u'a130b9d9-e00e-436e-9782-836ccef06e8a'},
                 u'architecture': None,
                 u'os_type': None
                 },
    u'priority': u'INFO'
}

INSTANCE_DELETE_SAMPLES = {
    u'_context_roles': [u'admin'],
    u'_context_request_id': u'req-9da1d714-dabe-42fd-8baa-583e57cd4f1a',
    u'_context_quota_class': None,
    u'event_type': u'compute.instance.delete.samples',
    u'_context_user_name': u'admin',
    u'_context_project_name': u'admin',
    u'timestamp': u'2013-01-04 15:20:32.009532',
    u'_context_is_admin': True,
    u'message_id': u'c48deeba-d0c3-4154-b3db-47480b52267a',
    u'_context_auth_token': None,
    u'_context_instance_lock_checked': False,
    u'_context_project_id': u'cea4b25edb484e5392727181b7721d29',
    u'_context_timestamp': u'2013-01-04T15:19:51.018218',
    u'_context_read_deleted': u'no',
    u'_context_user_id': u'01b83a5e23f24a6fb6cd073c0aee6eed',
    u'_context_remote_address': u'10.147.132.184',
    u'publisher_id': u'compute.ip-10-147-132-184.ec2.internal',
    u'payload': {u'state_description': u'resize_reverting',
                 u'availability_zone': None,
                 u'ephemeral_gb': 0,
                 u'instance_type_id': 2,
                 u'deleted_at': u'',
                 u'reservation_id': u'r-u3fvim06',
                 u'memory_mb': 512,
                 u'user_id': u'01b83a5e23f24a6fb6cd073c0aee6eed',
                 u'hostname': u's1',
                 u'state': u'resized',
                 u'launched_at': u'2013-01-04T15:10:14.000000',
                 u'metadata': [],
                 u'ramdisk_id': u'5f23128e-5525-46d8-bc66-9c30cd87141a',
                 u'access_ip_v6': None,
                 u'disk_gb': 0,
                 u'access_ip_v4': None,
                 u'kernel_id': u'571478e0-d5e7-4c2e-95a5-2bc79443c28a',
                 u'host': u'ip-10-147-132-184.ec2.internal',
                 u'display_name': u's1',
                 u'image_ref_url': u'http://10.147.132.184:9292/images/'
                 'a130b9d9-e00e-436e-9782-836ccef06e8a',
                 u'root_gb': 0,
                 u'tenant_id': u'cea4b25edb484e5392727181b7721d29',
                 u'created_at': u'2013-01-04T11:21:48.000000',
                 u'instance_id': u'648e8963-6886-4c3c-98f9-4511c292f86b',
                 u'instance_type': u'm1.tiny',
                 u'vcpus': 1,
                 u'image_meta': {u'kernel_id':
                                 u'571478e0-d5e7-4c2e-95a5-2bc79443c28a',
                                 u'ramdisk_id':
                                 u'5f23128e-5525-46d8-bc66-9c30cd87141a',
                                 u'base_image_ref':
                                 u'a130b9d9-e00e-436e-9782-836ccef06e8a'},
                 u'architecture': None,
                 u'os_type': None,
                 u'samples': [{u'name': u'sample-name1',
                               u'type': u'sample-type1',
                               u'unit': u'sample-units1',
                               u'volume': 1},
                              {u'name': u'sample-name2',
                               u'type': u'sample-type2',
                               u'unit': u'sample-units2',
                               u'volume': 2},
                              ],
                 },
    u'priority': u'INFO'
}


INSTANCE_SCHEDULED = {
    u'_context_roles': [u'admin'],
    u'_context_request_id': u'req-9da1d714-dabe-42fd-8baa-583e57cd4f1a',
    u'_context_quota_class': None,
    u'event_type': u'scheduler.run_instance.scheduled',
    u'_context_user_name': u'admin',
    u'_context_project_name': u'admin',
    u'timestamp': u'2013-01-04 15:20:32.009532',
    u'_context_is_admin': True,
    u'message_id': u'c48deeba-d0c3-4154-b3db-47480b52267a',
    u'_context_auth_token': None,
    u'_context_instance_lock_checked': False,
    u'_context_project_id': u'cea4b25edb484e5392727181b7721d29',
    u'_context_timestamp': u'2013-01-04T15:19:51.018218',
    u'_context_read_deleted': u'no',
    u'_context_user_id': u'01b83a5e23f24a6fb6cd073c0aee6eed',
    u'_context_remote_address': u'10.147.132.184',
    u'publisher_id': u'compute.ip-10-147-132-184.ec2.internal',
    u'payload': {
        'instance_id': 'fake-uuid1-1',
        'weighted_host': {
            'host': 'host3',
            'weight': 3.0,
        },
        'request_spec': {
            'instance_properties': {
                'root_gb': 512,
                'ephemeral_gb': 0,
                'launch_index': 0,
                'memory_mb': 512,
                'vcpus': 1,
                'os_type': 'Linux',
                'project_id': 1,
                'system_metadata': {'system': 'metadata'}},
            'instance_type': {'memory_mb': 512,
                              'vcpus': 1,
                              'root_gb': 512,
                              'ephemeral_gb': 0},
            'instance_uuids': ['fake-uuid1-1'],
        },
    },
    u'priority': u'INFO'
}


class TestNotifications(base.TestCase):

    def test_process_notification(self):
        info = notifications.Instance().process_notification(
            INSTANCE_CREATE_END
        )[0]
        for name, actual, expected in [
                ('counter_name', info.name, 'instance'),
                ('counter_type', info.type, counter.TYPE_GAUGE),
                ('counter_volume', info.volume, 1),
                ('timestamp', info.timestamp,
                 INSTANCE_CREATE_END['timestamp']),
                ('resource_id', info.resource_id,
                 INSTANCE_CREATE_END['payload']['instance_id']),
                ('instance_type', info.resource_metadata['instance_type'],
                 INSTANCE_CREATE_END['payload']['instance_type_id']),
                ('host', info.resource_metadata['host'],
                 INSTANCE_CREATE_END['publisher_id']),
        ]:
            self.assertEqual(actual, expected, name)

    @staticmethod
    def _find_counter(counters, name):
        return filter(lambda counter: counter.name == name, counters)[0]

    def test_instance_create_instance(self):
        ic = notifications.Instance()
        counters = ic.process_notification(INSTANCE_CREATE_END)
        self.assertEqual(len(counters), 1)
        c = counters[0]
        self.assertEqual(c.volume, 1)

    def test_instance_create_flavor(self):
        ic = notifications.InstanceFlavor()
        counters = ic.process_notification(INSTANCE_CREATE_END)
        self.assertEqual(len(counters), 1)
        c = counters[0]
        self.assertEqual(c.volume, 1)

    def test_instance_create_memory(self):
        ic = notifications.Memory()
        counters = ic.process_notification(INSTANCE_CREATE_END)
        self.assertEqual(len(counters), 1)
        c = counters[0]
        self.assertEqual(c.volume, INSTANCE_CREATE_END['payload']['memory_mb'])

    def test_instance_create_vcpus(self):
        ic = notifications.VCpus()
        counters = ic.process_notification(INSTANCE_CREATE_END)
        self.assertEqual(len(counters), 1)
        c = counters[0]
        self.assertEqual(c.volume, INSTANCE_CREATE_END['payload']['vcpus'])

    def test_instance_create_root_disk_size(self):
        ic = notifications.RootDiskSize()
        counters = ic.process_notification(INSTANCE_CREATE_END)
        self.assertEqual(len(counters), 1)
        c = counters[0]
        self.assertEqual(c.volume, INSTANCE_CREATE_END['payload']['root_gb'])

    def test_instance_create_ephemeral_disk_size(self):
        ic = notifications.EphemeralDiskSize()
        counters = ic.process_notification(INSTANCE_CREATE_END)
        self.assertEqual(len(counters), 1)
        c = counters[0]
        self.assertEqual(c.volume,
                         INSTANCE_CREATE_END['payload']['ephemeral_gb'])

    def test_instance_exists_instance(self):
        ic = notifications.Instance()
        counters = ic.process_notification(INSTANCE_EXISTS)
        self.assertEqual(len(counters), 1)

    def test_instance_exists_flavor(self):
        ic = notifications.Instance()
        counters = ic.process_notification(INSTANCE_EXISTS)
        self.assertEqual(len(counters), 1)

    def test_instance_delete_instance(self):
        ic = notifications.Instance()
        counters = ic.process_notification(INSTANCE_DELETE_START)
        self.assertEqual(len(counters), 1)

    def test_instance_delete_flavor(self):
        ic = notifications.Instance()
        counters = ic.process_notification(INSTANCE_DELETE_START)
        self.assertEqual(len(counters), 1)

    def test_instance_finish_resize_instance(self):
        ic = notifications.Instance()
        counters = ic.process_notification(INSTANCE_FINISH_RESIZE_END)
        self.assertEqual(len(counters), 1)
        c = counters[0]
        self.assertEqual(c.volume, 1)

    def test_instance_finish_resize_flavor(self):
        ic = notifications.InstanceFlavor()
        counters = ic.process_notification(INSTANCE_FINISH_RESIZE_END)
        self.assertEqual(len(counters), 1)
        c = counters[0]
        self.assertEqual(c.volume, 1)
        self.assertEqual(c.name, 'instance:m1.small')

    def test_instance_finish_resize_memory(self):
        ic = notifications.Memory()
        counters = ic.process_notification(INSTANCE_FINISH_RESIZE_END)
        self.assertEqual(len(counters), 1)
        c = counters[0]
        self.assertEqual(c.volume,
                         INSTANCE_FINISH_RESIZE_END['payload']['memory_mb'])

    def test_instance_finish_resize_vcpus(self):
        ic = notifications.VCpus()
        counters = ic.process_notification(INSTANCE_FINISH_RESIZE_END)
        self.assertEqual(len(counters), 1)
        c = counters[0]
        self.assertEqual(c.volume,
                         INSTANCE_FINISH_RESIZE_END['payload']['vcpus'])

    def test_instance_resize_finish_instance(self):
        ic = notifications.Instance()
        counters = ic.process_notification(INSTANCE_FINISH_RESIZE_END)
        self.assertEqual(len(counters), 1)
        c = counters[0]
        self.assertEqual(c.volume, 1)

    def test_instance_resize_finish_flavor(self):
        ic = notifications.InstanceFlavor()
        counters = ic.process_notification(INSTANCE_RESIZE_REVERT_END)
        self.assertEqual(len(counters), 1)
        c = counters[0]
        self.assertEqual(c.volume, 1)
        self.assertEqual(c.name, 'instance:m1.tiny')

    def test_instance_resize_finish_memory(self):
        ic = notifications.Memory()
        counters = ic.process_notification(INSTANCE_RESIZE_REVERT_END)
        self.assertEqual(len(counters), 1)
        c = counters[0]
        self.assertEqual(c.volume,
                         INSTANCE_RESIZE_REVERT_END['payload']['memory_mb'])

    def test_instance_resize_finish_vcpus(self):
        ic = notifications.VCpus()
        counters = ic.process_notification(INSTANCE_RESIZE_REVERT_END)
        self.assertEqual(len(counters), 1)
        c = counters[0]
        self.assertEqual(c.volume,
                         INSTANCE_RESIZE_REVERT_END['payload']['vcpus'])

    def test_instance_delete_samples(self):
        ic = notifications.InstanceDelete()
        counters = ic.process_notification(INSTANCE_DELETE_SAMPLES)
        self.assertEqual(len(counters), 2)
        names = [c.name for c in counters]
        self.assertEqual(names, ['sample-name1', 'sample-name2'])

    def test_instance_scheduled(self):
        ic = notifications.InstanceScheduled()

        self.assertIn(INSTANCE_SCHEDULED['event_type'],
                      ic.get_event_types())

        counters = ic.process_notification(INSTANCE_SCHEDULED)
        self.assertEqual(len(counters), 1)
        names = [c.name for c in counters]
        self.assertEqual(names, ['instance.scheduled'])
        rid = [c.resource_id for c in counters]
        self.assertEqual(rid, ['fake-uuid1-1'])
