#    Copyright 2012 IBM Corp.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""Client side of the conductor RPC API."""
import logging
from oslo.config import cfg

from monitor.openstack.common import jsonutils
from monitor.openstack.common import rpc
import monitor.openstack.common.rpc.proxy

CONF = cfg.CONF

LOG = logging.getLogger(__name__)


class ConductorAPI(monitor.openstack.common.rpc.proxy.RpcProxy):
    """Client side of the conductor RPC API"""

    BASE_RPC_API_VERSION = '1.0'

    def __init__(self, topic=None):
        super(ConductorAPI, self).__init__(
            topic = topic or CONF.conductor_topic,
            default_version=self.BASE_RPC_API_VERSION)

    def test_service(self, ctxt):
        ret = self.call(ctxt, self.make_msg('test_service'))
        return ret
