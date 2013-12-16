# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 OpenStack LLC.
# Copyright 2011 United States Government as represented by the
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
WSGI middleware for OpenStack ServiceManage API.
"""

from monitor.api import extensions
import monitor.api.openstack
from monitor.api.v1 import limits
from monitor.api.v1 import types
from monitor.api.v1 import conductor
from monitor.api import versions
from monitor.openstack.common import log as logging


LOG = logging.getLogger(__name__)


class APIRouter(monitor.api.openstack.APIRouter):
    """
    Routes requests on the OpenStack API to the appropriate controller
    and method.
    """
    ExtensionManager = extensions.ExtensionManager

    def _setup_routes(self, mapper, ext_mgr):
        self.resources['versions'] = versions.create_resource()
        mapper.connect("versions", "/",
                       controller=self.resources['versions'],
                       action='show')

        mapper.redirect("", "/")

        self.resources['types'] = types.create_resource()
        mapper.resource("type", "types",
                        controller=self.resources['types'])


        self.resources['limits'] = limits.create_resource()
        mapper.resource("limit", "limits",
                        controller=self.resources['limits'])

        self.resources['conductor'] = conductor.create_resource(ext_mgr)
        mapper.resource("conductor", "conductor",
                        controller=self.resources['conductor'],
                        collection={'detail': 'GET',
                                    'test_service': "POST"},
                        member={'action': 'POST'})
