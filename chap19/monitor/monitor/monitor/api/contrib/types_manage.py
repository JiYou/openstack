# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2011 Zadara Storage Inc.
# Copyright (c) 2011 OpenStack LLC.
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

"""The servicemanage types manage extension."""

import webob

from monitor.api import extensions
from monitor.api.openstack import wsgi
from monitor.api.v1 import types
from monitor.api.views import types as views_types
from monitor import exception
from monitor.servicemanage import servicemanage_types


authorize = extensions.extension_authorizer('servicemanage', 'types_manage')


class ServiceManageTypesManageController(wsgi.Controller):
    """The servicemanage types API controller for the OpenStack API."""

    _view_builder_class = views_types.ViewBuilder

    @wsgi.action("create")
    @wsgi.serializers(xml=types.ServiceManageTypeTemplate)
    def _create(self, req, body):
        """Creates a new servicemanage type."""
        context = req.environ['monitor.context']
        authorize(context)

        if not self.is_valid_body(body, 'servicemanage_type'):
            raise webob.exc.HTTPBadRequest()

        vol_type = body['servicemanage_type']
        name = vol_type.get('name', None)
        specs = vol_type.get('extra_specs', {})

        if name is None or name == "":
            raise webob.exc.HTTPBadRequest()

        try:
            servicemanage_types.create(context, name, specs)
            vol_type = servicemanage_types.get_servicemanage_type_by_name(context, name)
        except exception.ServiceManageTypeExists as err:
            raise webob.exc.HTTPConflict(explanation=str(err))
        except exception.NotFound:
            raise webob.exc.HTTPNotFound()

        return self._view_builder.show(req, vol_type)

    @wsgi.action("delete")
    def _delete(self, req, id):
        """Deletes an existing servicemanage type."""
        context = req.environ['monitor.context']
        authorize(context)

        try:
            vol_type = servicemanage_types.get_servicemanage_type(context, id)
            servicemanage_types.destroy(context, vol_type['id'])
        except exception.NotFound:
            raise webob.exc.HTTPNotFound()

        return webob.Response(status_int=202)


class Types_manage(extensions.ExtensionDescriptor):
    """Types manage support."""

    name = "TypesManage"
    alias = "os-types-manage"
    namespace = "http://docs.openstack.org/servicemanage/ext/types-manage/api/v1"
    updated = "2011-08-24T00:00:00+00:00"

    def get_controller_extensions(self):
        controller = ServiceManageTypesManageController()
        extension = extensions.ControllerExtension(self, 'types', controller)
        return [extension]
