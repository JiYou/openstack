# -*- encoding: utf-8 -*-
#
# Copyright © 2013 eNovance
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
"""Publish a counter using an UDP mechanism
"""

from ceilometer import publisher
from ceilometer.openstack.common import log
from ceilometer.openstack.common import network_utils
from ceilometer.openstack.common.gettextutils import _
import msgpack
import socket
from oslo.config import cfg

cfg.CONF.import_opt('udp_port', 'ceilometer.collector.service',
                    group='collector')

LOG = log.getLogger(__name__)


class UDPPublisher(publisher.PublisherBase):

    def __init__(self, parsed_url):
        self.host, self.port = network_utils.parse_host_port(
            parsed_url.netloc,
            default_port=cfg.CONF.collector.udp_port)
        self.socket = socket.socket(socket.AF_INET,
                                    socket.SOCK_DGRAM)

    def publish_counters(self, context, counters, source):
        """Send a metering message for publishing

        :param context: Execution context from the service or RPC call
        :param counter: Counter from pipeline after transformation
        :param source: counter source
        """

        for counter in counters:
            msg = counter._asdict()
            msg['source'] = source
            host = self.host
            port = self.port
            LOG.debug(_("Publishing counter %(msg)s over "
                        "UDP to %(host)s:%(port)d") % locals())
            try:
                self.socket.sendto(msgpack.dumps(msg),
                                   (self.host, self.port))
            except Exception as e:
                LOG.warn(_("Unable to send counter over UDP"))
                LOG.exception(e)
