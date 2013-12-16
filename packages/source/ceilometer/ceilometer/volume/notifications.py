# -*- encoding: utf-8 -*-
#
# Copyright © 2012 New Dream Network, LLC (DreamHost)
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
"""Converters for producing volume counter messages from cinder notification
events.
"""

from oslo.config import cfg

from ceilometer import counter
from ceilometer import plugin


OPTS = [
    cfg.StrOpt('cinder_control_exchange',
               default='cinder',
               help="Exchange name for Cinder notifications"),
]


cfg.CONF.register_opts(OPTS)


class _Base(plugin.NotificationBase):
    """Convert volume notifications into Counters
    """

    metadata_keys = [
        "status",
        "display_name",
        "volume_type",
        "size",
    ]

    @staticmethod
    def get_exchange_topics(conf):
        """Return a sequence of ExchangeTopics defining the exchange and
        topics to be connected for this plugin.
        """
        return [
            plugin.ExchangeTopics(
                exchange=conf.cinder_control_exchange,
                topics=set(topic + ".info"
                           for topic in conf.notification_topics)),
        ]

    @staticmethod
    def get_event_types():
        return ['volume.exists',
                'volume.create.end',
                'volume.delete.start']


class Volume(_Base):

    def process_notification(self, message):
        return [
            counter.Counter(name='volume',
                            type=counter.TYPE_GAUGE,
                            unit='volume',
                            volume=1,
                            user_id=message['payload']['user_id'],
                            project_id=message['payload']['tenant_id'],
                            resource_id=message['payload']['volume_id'],
                            timestamp=message['timestamp'],
                            resource_metadata=self.notification_to_metadata(
                                message),
                            ),
        ]


class VolumeSize(_Base):

    def process_notification(self, message):
        return [
            counter.Counter(name='volume.size',
                            type=counter.TYPE_GAUGE,
                            unit='GB',
                            volume=message['payload']['size'],
                            user_id=message['payload']['user_id'],
                            project_id=message['payload']['tenant_id'],
                            resource_id=message['payload']['volume_id'],
                            timestamp=message['timestamp'],
                            resource_metadata=self.notification_to_metadata(
                                message),
                            ),
        ]
