#   Copyright 2012 OpenStack, LLC.
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.

from monitor.api import extensions
from monitor.api.openstack import wsgi
from monitor.api import xmlutil
from monitor import servicemanage


authorize = extensions.soft_extension_authorizer('servicemanage',
                                                 'servicemanage_tenant_attribute')


class ServiceManageTenantAttributeController(wsgi.Controller):
    def __init__(self, *args, **kwargs):
        super(ServiceManageTenantAttributeController, self).__init__(*args, **kwargs)
        self.servicemanage_api = servicemanage.API()

    def _add_servicemanage_tenant_attribute(self, context, resp_servicemanage):
        try:
            db_servicemanage = self.servicemanage_api.get(context, resp_servicemanage['id'])
        except Exception:
            return
        else:
            key = "%s:tenant_id" % ServiceManage_tenant_attribute.alias
            resp_servicemanage[key] = db_servicemanage['project_id']

    @wsgi.extends
    def show(self, req, resp_obj, id):
        context = req.environ['monitor.context']
        if authorize(context):
            resp_obj.attach(xml=ServiceManageTenantAttributeTemplate())
            self._add_servicemanage_tenant_attribute(context, resp_obj.obj['servicemanage'])

    @wsgi.extends
    def detail(self, req, resp_obj):
        context = req.environ['monitor.context']
        if authorize(context):
            resp_obj.attach(xml=ServiceManageListTenantAttributeTemplate())
            for servicemanage in list(resp_obj.obj['servicemanages']):
                self._add_servicemanage_tenant_attribute(context, servicemanage)


class ServiceManage_tenant_attribute(extensions.ExtensionDescriptor):
    """Expose the internal project_id as an attribute of a servicemanage."""

    name = "ServiceManageTenantAttribute"
    alias = "os-vol-tenant-attr"
    namespace = ("http://docs.openstack.org/servicemanage/ext/"
                 "servicemanage_tenant_attribute/api/v1")
    updated = "2011-11-03T00:00:00+00:00"

    def get_controller_extensions(self):
        controller = ServiceManageTenantAttributeController()
        extension = extensions.ControllerExtension(self, 'servicemanages', controller)
        return [extension]


def make_servicemanage(elem):
    elem.set('{%s}tenant_id' % ServiceManage_tenant_attribute.namespace,
             '%s:tenant_id' % ServiceManage_tenant_attribute.alias)


class ServiceManageTenantAttributeTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('servicemanage', selector='servicemanage')
        make_servicemanage(root)
        alias = ServiceManage_tenant_attribute.alias
        namespace = ServiceManage_tenant_attribute.namespace
        return xmlutil.SlaveTemplate(root, 1, nsmap={alias: namespace})


class ServiceManageListTenantAttributeTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('servicemanages')
        elem = xmlutil.SubTemplateElement(root, 'servicemanage', selector='servicemanages')
        make_servicemanage(elem)
        alias = ServiceManage_tenant_attribute.alias
        namespace = ServiceManage_tenant_attribute.namespace
        return xmlutil.SlaveTemplate(root, 1, nsmap={alias: namespace})
