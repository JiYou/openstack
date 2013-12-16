# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010 OpenStack, LLC.
# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
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

"""
Conductor Service
"""

from oslo.config import cfg
import datetime
from monitor import context
from monitor import db
from monitor import exception
from monitor import flags
from monitor import manager
from monitor.openstack.common import excutils
from monitor.openstack.common import importutils
from monitor.openstack.common import log as logging
from monitor.openstack.common.notifier import api as notifier
from monitor.openstack.common import timeutils


LOG = logging.getLogger(__name__)
FLAGS = flags.FLAGS


class ConductorManager(manager.Manager):

    RPC_API_VERSION = '1.2'

    def __init__(self, service_name=None, *args, **kwargs):
        super(ConductorManager, self).__init__(*args, **kwargs)

    def init_host(self):
        LOG.info('init_host in ConductorManager.')

    def service_get_all(self, context):
        service_list = db.service_get_all(context)
        for x in service_list:
            LOG.debug('x.id = %s' % x.id)
            LOG.debug('x.topic = %s' % x.topic)

    def test_service(self, context):
        LOG.info('test_service in conductor')
        return {'key': 'test_server_in_conductor'}
