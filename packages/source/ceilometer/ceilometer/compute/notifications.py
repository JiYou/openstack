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
"""Converters for producing compute counter messages from notification events.
"""

from oslo.config import cfg

from ceilometer.compute import instance
from ceilometer import counter
from ceilometer import plugin
from ceilometer import utils


OPTS = [
    cfg.StrOpt('nova_control_exchange',
               default='nova',
               help="Exchange name for Nova notifications"),
]


cfg.CONF.register_opts(OPTS)


class ComputeNotificationBase(plugin.NotificationBase):

    @staticmethod
    def get_exchange_topics(conf):
        """Return a sequence of ExchangeTopics defining the exchange and
        topics to be connected for this plugin.
        """
        return [
            plugin.ExchangeTopics(
                exchange=conf.nova_control_exchange,
                topics=set(topic + ".info"
                           for topic in conf.notification_topics)),
        ]


class InstanceScheduled(ComputeNotificationBase):

    metadata_keys = ['request_spec']

    @staticmethod
    def get_event_types():
        return ['scheduler.run_instance.scheduled']

    def notification_to_metadata(self, event):
        metadata = super(InstanceScheduled,
                         self).notification_to_metadata(event)
        metadata['weighted_host'] = event['payload']['weighted_host']['host']
        metadata['weight'] = event['payload']['weighted_host']['weight']
        return metadata

    def process_notification(self, message):
        return [
            counter.Counter(
                name='instance.scheduled',
                type=counter.TYPE_DELTA,
                volume=1,
                unit='instance',
                user_id=None,
                project_id=
                message['payload']['request_spec']
                ['instance_properties']['project_id'],
                resource_id=message['payload']['instance_id'],
                timestamp=message['timestamp'],
                resource_metadata=dict(
                    utils.recursive_keypairs(message['payload'])),
            )
        ]


class ComputeInstanceNotificationBase(ComputeNotificationBase):
    """Convert compute.instance.* notifications into Counters
    """
    metadata_keys = instance.INSTANCE_PROPERTIES

    def notification_to_metadata(self, event):
        metadata = super(ComputeInstanceNotificationBase,
                         self).notification_to_metadata(event)
        metadata['instance_type'] = event['payload']['instance_type_id']
        return metadata

    @staticmethod
    def get_event_types():
        return ['compute.instance.create.end',
                'compute.instance.exists',
                'compute.instance.delete.start',
                'compute.instance.finish_resize.end',
                'compute.instance.resize.revert.end']


class Instance(ComputeInstanceNotificationBase):

    def process_notification(self, message):
        return [
            counter.Counter(name='instance',
                            type=counter.TYPE_GAUGE,
                            unit='instance',
                            volume=1,
                            user_id=message['payload']['user_id'],
                            project_id=message['payload']['tenant_id'],
                            resource_id=message['payload']['instance_id'],
                            timestamp=message['timestamp'],
                            resource_metadata=self.notification_to_metadata(
                                message),
                            ),
        ]


class Memory(ComputeInstanceNotificationBase):

    def process_notification(self, message):
        return [
            counter.Counter(name='memory',
                            type=counter.TYPE_GAUGE,
                            unit='MB',
                            volume=message['payload']['memory_mb'],
                            user_id=message['payload']['user_id'],
                            project_id=message['payload']['tenant_id'],
                            resource_id=message['payload']['instance_id'],
                            timestamp=message['timestamp'],
                            resource_metadata=self.notification_to_metadata(
                                message)),
        ]


class VCpus(ComputeInstanceNotificationBase):

    def process_notification(self, message):
        return [
            counter.Counter(name='vcpus',
                            type=counter.TYPE_GAUGE,
                            unit='vcpu',
                            volume=message['payload']['vcpus'],
                            user_id=message['payload']['user_id'],
                            project_id=message['payload']['tenant_id'],
                            resource_id=message['payload']['instance_id'],
                            timestamp=message['timestamp'],
                            resource_metadata=self.notification_to_metadata(
                                message)),
        ]


class RootDiskSize(ComputeInstanceNotificationBase):

    def process_notification(self, message):
        return [
            counter.Counter(name='disk.root.size',
                            type=counter.TYPE_GAUGE,
                            unit='GB',
                            volume=message['payload']['root_gb'],
                            user_id=message['payload']['user_id'],
                            project_id=message['payload']['tenant_id'],
                            resource_id=message['payload']['instance_id'],
                            timestamp=message['timestamp'],
                            resource_metadata=self.notification_to_metadata(
                                message)),
        ]


class EphemeralDiskSize(ComputeInstanceNotificationBase):

    def process_notification(self, message):
        return [
            counter.Counter(name='disk.ephemeral.size',
                            type=counter.TYPE_GAUGE,
                            unit='GB',
                            volume=message['payload']['ephemeral_gb'],
                            user_id=message['payload']['user_id'],
                            project_id=message['payload']['tenant_id'],
                            resource_id=message['payload']['instance_id'],
                            timestamp=message['timestamp'],
                            resource_metadata=self.notification_to_metadata(
                                message)),
        ]


class InstanceFlavor(ComputeInstanceNotificationBase):

    def process_notification(self, message):
        counters = []
        instance_type = message.get('payload', {}).get('instance_type')
        if instance_type:
            counters.append(
                counter.Counter(
                    name='instance:%s' % instance_type,
                    type=counter.TYPE_GAUGE,
                    unit='instance',
                    volume=1,
                    user_id=message['payload']['user_id'],
                    project_id=message['payload']['tenant_id'],
                    resource_id=message['payload']['instance_id'],
                    timestamp=message['timestamp'],
                    resource_metadata=self.notification_to_metadata(
                        message),
                )
            )
        return counters


class InstanceDelete(ComputeInstanceNotificationBase):
    """Handle the messages sent by the nova notifier plugin
    when an instance is being deleted.
    """

    @staticmethod
    def get_event_types():
        return ['compute.instance.delete.samples']

    def process_notification(self, message):
        return [
            counter.Counter(name=sample['name'],
                            type=sample['type'],
                            unit=sample['unit'],
                            volume=sample['volume'],
                            user_id=message['payload']['user_id'],
                            project_id=message['payload']['tenant_id'],
                            resource_id=message['payload']['instance_id'],
                            timestamp=message['timestamp'],
                            resource_metadata=self.notification_to_metadata(
                                message),
                            )
            for sample in message['payload'].get('samples', [])
        ]
