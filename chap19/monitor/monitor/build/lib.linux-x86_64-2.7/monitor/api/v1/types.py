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

"""The servicemanage type & servicemanage types extra specs extension."""

from webob import exc

from monitor.api.openstack import wsgi
from monitor.api.views import types as views_types
from monitor.api import xmlutil
from monitor import exception


def make_voltype(elem):
    elem.set('id')
    elem.set('name')
    extra_specs = xmlutil.make_flat_dict('extra_specs', selector='extra_specs')
    elem.append(extra_specs)


class ServiceManageTypeTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('servicemanage_type', selector='servicemanage_type')
        make_voltype(root)
        return xmlutil.MasterTemplate(root, 1)


class ServiceManageTypesTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('servicemanage_types')
        elem = xmlutil.SubTemplateElement(root, 'servicemanage_type',
                                          selector='servicemanage_types')
        make_voltype(elem)
        return xmlutil.MasterTemplate(root, 1)


class ServiceManageTypesController(wsgi.Controller):
    """The servicemanage types API controller for the OpenStack API."""

    _view_builder_class = views_types.ViewBuilder

    @wsgi.serializers(xml=ServiceManageTypesTemplate)
    def index(self, req):
        """Returns the list of servicemanage types."""
        context = req.environ['monitor.context']
        vol_types = servicemanage_types.get_all_types(context).values()
        return self._view_builder.index(req, vol_types)

    @wsgi.serializers(xml=ServiceManageTypeTemplate)
    def show(self, req, id):
        """Return a single servicemanage type item."""
        context = req.environ['monitor.context']

        try:
            vol_type = servicemanage_types.get_servicemanage_type(context, id)
        except exception.NotFound:
            raise exc.HTTPNotFound()

        # TODO(bcwaldon): remove str cast once we use uuids
        vol_type['id'] = str(vol_type['id'])
        return self._view_builder.show(req, vol_type)


def create_resource():
    return wsgi.Resource(ServiceManageTypesController())
