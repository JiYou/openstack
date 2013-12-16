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
"""Publish a counter using the preferred RPC mechanism.
"""

import hashlib
import hmac
import itertools
import uuid

from oslo.config import cfg

from ceilometer.openstack.common import log
from ceilometer.openstack.common import rpc
from ceilometer import publisher
from ceilometer import utils


LOG = log.getLogger(__name__)

METER_PUBLISH_OPTS = [
    cfg.StrOpt('metering_topic',
               default='metering',
               help='the topic ceilometer uses for metering messages',
               deprecated_group="DEFAULT",
               ),
    cfg.StrOpt('metering_secret',
               secret=True,
               default='change this or be hacked',
               help='Secret value for signing metering messages',
               deprecated_group="DEFAULT",
               ),
]


def register_opts(config):
    """Register the options for publishing metering messages.
    """
    config.register_opts(METER_PUBLISH_OPTS, group="publisher_rpc")


register_opts(cfg.CONF)


def compute_signature(message, secret):
    """Return the signature for a message dictionary.
    """
    digest_maker = hmac.new(secret, '', hashlib.sha256)
    for name, value in utils.recursive_keypairs(message):
        if name == 'message_signature':
            # Skip any existing signature value, which would not have
            # been part of the original message.
            continue
        digest_maker.update(name)
        digest_maker.update(unicode(value).encode('utf-8'))
    return digest_maker.hexdigest()


def verify_signature(message, secret):
    """Check the signature in the message against the value computed
    from the rest of the contents.
    """
    old_sig = message.get('message_signature')
    new_sig = compute_signature(message, secret)
    return new_sig == old_sig


def meter_message_from_counter(counter, secret, source):
    """Make a metering message ready to be published or stored.

    Returns a dictionary containing a metering message
    for a notification message and a Counter instance.
    """
    msg = {'source': source,
           'counter_name': counter.name,
           'counter_type': counter.type,
           'counter_unit': counter.unit,
           'counter_volume': counter.volume,
           'user_id': counter.user_id,
           'project_id': counter.project_id,
           'resource_id': counter.resource_id,
           'timestamp': counter.timestamp,
           'resource_metadata': counter.resource_metadata,
           'message_id': str(uuid.uuid1()),
           }
    msg['message_signature'] = compute_signature(msg, secret)
    return msg


class RPCPublisher(publisher.PublisherBase):
    def publish_counters(self, context, counters, source):
        """Send a metering message for publishing

        :param context: Execution context from the service or RPC call
        :param counter: Counter from pipeline after transformation
        :param source: counter source
        """

        meters = [
            meter_message_from_counter(
                counter,
                cfg.CONF.publisher_rpc.metering_secret,
                source)
            for counter in counters
        ]

        topic = cfg.CONF.publisher_rpc.metering_topic
        msg = {
            'method': 'record_metering_data',
            'version': '1.0',
            'args': {'data': meters},
        }
        LOG.debug('PUBLISH: %s', str(msg))
        rpc.cast(context, topic, msg)

        for meter_name, meter_list in itertools.groupby(
                sorted(meters, key=lambda m: m['counter_name']),
                lambda m: m['counter_name']):
            msg = {
                'method': 'record_metering_data',
                'version': '1.0',
                'args': {'data': list(meter_list)},
            }
            rpc.cast(context, topic + '.' + meter_name, msg)
