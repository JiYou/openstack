# -*- encoding: utf-8 -*-
#
# Author: John Tran <jhtran@att.com>
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

import functools

from novaclient.v1_1 import client as nova_client
from oslo.config import cfg

from ceilometer.openstack.common import log

cfg.CONF.import_group('service_credentials', 'ceilometer.service')

LOG = log.getLogger(__name__)


def logged(func):

    @functools.wraps(func)
    def with_logging(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            LOG.exception(e)
            raise

    return with_logging


class Client(object):

    def __init__(self):
        """Returns a nova Client object."""
        conf = cfg.CONF.service_credentials
        tenant = conf.os_tenant_id and conf.os_tenant_id or conf.os_tenant_name
        self.nova_client = nova_client.Client(
            username=cfg.CONF.service_credentials.os_username,
            api_key=cfg.CONF.service_credentials.os_password,
            project_id=tenant,
            auth_url=cfg.CONF.service_credentials.os_auth_url,
            no_cache=True)

    def _with_flavor(self, instances):
        flavors = dict((f.id, f) for f in self.nova_client.flavors.list())
        for instance in instances:
            fid = instance.flavor['id']
            try:
                instance.flavor['name'] = flavors[fid].name
            except KeyError:
                instance.flavor['name'] = 'unknown-id-%s' % fid
        return instances

    @logged
    def instance_get_all_by_host(self, hostname):
        """Returns list of instances on particular host."""
        search_opts = {'host': hostname, 'all_tenants': True}
        return self._with_flavor(self.nova_client.servers.list(
            detailed=True,
            search_opts=search_opts))

    @logged
    def floating_ip_get_all(self):
        """Returns all floating ips."""
        return self.nova_client.floating_ips.list()
