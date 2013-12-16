# -*- encoding: utf-8 -*-
#
# Copyright © 2012 New Dream Network, LLC (DreamHost)
#
# Author: Julien Danjou <julien@danjou.info>
#         Doug Hellmann <doug.hellmann@dreamhost.com>
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
"""Tests for ceilometer.compute.nova_notifier
"""

import contextlib
import datetime

import mock

from stevedore import extension
from stevedore.tests import manager as test_manager

## NOTE(dhellmann): These imports are not in the generally approved
## alphabetical order, but they are in the order that actually
## works. Please don't change them.
from nova.tests import fake_network
from nova.compute import vm_states
try:
    from nova.compute import flavors
except ImportError:
    from nova.compute import instance_types as flavors

from nova import config
from nova import context
from nova import db
from nova.openstack.common import importutils
from nova.openstack.common import log as logging
from nova.openstack.common.notifier import api as notifier_api

# For nova_CONF.compute_manager, used in the nova_notifier module.
from nova import service

# HACK(dhellmann): Import this before any other ceilometer code
# because the notifier module messes with the import path to force
# nova's version of oslo to be used instead of ceilometer's.
from ceilometer.compute import nova_notifier

from ceilometer import counter
from ceilometer.tests import base

LOG = logging.getLogger(__name__)
nova_CONF = config.cfg.CONF


class TestNovaNotifier(base.TestCase):

    class Pollster(object):
        instances = []
        test_data = counter.Counter(
            name='test',
            type=counter.TYPE_CUMULATIVE,
            unit='units-go-here',
            volume=1,
            user_id='test',
            project_id='test',
            resource_id='test_run_tasks',
            timestamp=datetime.datetime.utcnow().isoformat(),
            resource_metadata={'name': 'Pollster',
                               },
        )

        def get_counters(self, manager, instance):
            self.instances.append((manager, instance))
            return [self.test_data]

        def get_counter_names(self):
            return ['test']

    @mock.patch('ceilometer.pipeline.setup_pipeline', mock.MagicMock())
    def setUp(self):
        super(TestNovaNotifier, self).setUp()
        nova_CONF.compute_driver = 'nova.virt.fake.FakeDriver'
        nova_CONF.notification_driver = [nova_notifier.__name__]
        nova_CONF.rpc_backend = 'nova.openstack.common.rpc.impl_fake'
        nova_CONF.vnc_enabled = False
        nova_CONF.spice.enabled = False
        self.compute = importutils.import_object(nova_CONF.compute_manager)
        self.context = context.get_admin_context()
        fake_network.set_stub_network_methods(self.stubs)

        self.instance = {"name": "instance-1",
                         'OS-EXT-SRV-ATTR:instance_name': 'instance-1',
                         "id": 1,
                         "image_ref": "FAKE",
                         "user_id": "FAKE",
                         "project_id": "FAKE",
                         "display_name": "FAKE NAME",
                         "hostname": "abcdef",
                         "reservation_id": "FAKE RID",
                         "instance_type_id": 1,
                         "architecture": "x86",
                         "memory_mb": "1024",
                         "root_gb": "20",
                         "ephemeral_gb": "0",
                         "vcpus": 1,
                         'node': "fakenode",
                         "host": "fakehost",
                         "availability_zone":
                         "1e3ce043029547f1a61c1996d1a531a4",
                         "created_at": '2012-05-08 20:23:41',
                         "os_type": "linux",
                         "kernel_id": "kernelid",
                         "ramdisk_id": "ramdiskid",
                         "vm_state": vm_states.ACTIVE,
                         "access_ip_v4": "someip",
                         "access_ip_v6": "someip",
                         "metadata": {},
                         "uuid": "144e08f4-00cb-11e2-888e-5453ed1bbb5f",
                         "system_metadata": {}}
        self.stubs.Set(db, 'instance_info_cache_delete', self.do_nothing)
        self.stubs.Set(db, 'instance_destroy', self.do_nothing)
        self.stubs.Set(db, 'instance_system_metadata_get',
                       self.fake_db_instance_system_metadata_get)
        self.stubs.Set(db, 'block_device_mapping_get_all_by_instance',
                       lambda context, instance: {})
        self.stubs.Set(db, 'instance_update_and_get_original',
                       lambda context, uuid, kwargs: (self.instance,
                                                      self.instance))
        self.stubs.Set(flavors, 'extract_flavor',
                       lambda ref: {})

        # Set up to capture the notification messages generated by the
        # plugin and to invoke our notifier plugin.
        self.notifications = []
        notifier_api._reset_drivers()
        notifier_api.add_driver(self)
        notifier_api.add_driver(nova_notifier)

        ext_mgr = test_manager.TestExtensionManager([
            extension.Extension('test',
                                None,
                                None,
                                self.Pollster(),
                                ),
        ])
        self.ext_mgr = ext_mgr
        self.gatherer = nova_notifier.DeletedInstanceStatsGatherer(ext_mgr)
        nova_notifier.initialize_gatherer(self.gatherer)

        # Terminate the instance to trigger the notification.
        with contextlib.nested(
                # Under Grizzly, Nova has moved to no-db access on the
                # compute node. The compute manager uses RPC to talk to
                # the conductor. We need to disable communication between
                # the nova manager and the remote system since we can't
                # expect the message bus to be available, or the remote
                # controller to be there if the message bus is online.
                mock.patch.object(self.compute, 'conductor_api'),
                # The code that looks up the instance uses a global
                # reference to the API, so we also have to patch that to
                # return our fake data.
                mock.patch.object(nova_notifier.instance_info_source,
                                  'instance_get_by_uuid',
                                  self.fake_instance_ref_get),
                ):
            self.compute.terminate_instance(self.context,
                                            instance=self.instance)

    def tearDown(self):
        notifier_api._reset_drivers()
        self.Pollster.instances = []
        super(TestNovaNotifier, self).tearDown()
        nova_notifier._gatherer = None

    def fake_instance_ref_get(self, context, id_):
        if self.instance['uuid'] == id_:
            return self.instance
        return {}

    @staticmethod
    def do_nothing(*args, **kwargs):
        pass

    @staticmethod
    def fake_db_instance_system_metadata_get(context, uuid):
        return dict(meta_a=123, meta_b="foobar")

    def notify(self, context, message):
        self.notifications.append(message)

    def test_pollster_called(self):
        # The notifier plugin sends another notification for the same
        # instance, so we expect to have 2 entries in the list.
        self.assertEqual(len(self.Pollster.instances), 2)

    def test_correct_instance(self):
        for i, (gatherer, inst) in enumerate(self.Pollster.instances):
            self.assertEqual((i, inst.uuid), (i, self.instance['uuid']))

    def test_correct_gatherer(self):
        for i, (gatherer, inst) in enumerate(self.Pollster.instances):
            self.assertEqual((i, gatherer), (i, self.gatherer))

    def test_samples(self):
        # Ensure that the outgoing notification looks like what we expect
        for message in self.notifications:
            event = message['event_type']
            if event != 'compute.instance.delete.samples':
                continue
            payload = message['payload']
            samples = payload['samples']
            self.assertEqual(len(samples), 1)
            s = payload['samples'][0]
            self.assertEqual(s, {'name': 'test',
                                 'type': counter.TYPE_CUMULATIVE,
                                 'unit': 'units-go-here',
                                 'volume': 1,
                                 })
            break
        else:
            assert False, 'Did not find expected event'
