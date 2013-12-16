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
from monitor.openstack.common import log as logging
from monitor import servicemanage


LOG = logging.getLogger(__name__)
authorize = extensions.soft_extension_authorizer('servicemanage',
                                                 'servicemanage_host_attribute')


class ServiceManageHostAttributeController(wsgi.Controller):
    def __init__(self, *args, **kwargs):
        super(ServiceManageHostAttributeController, self).__init__(*args, **kwargs)
        self.servicemanage_api = servicemanage.API()

    def _add_servicemanage_host_attribute(self, context, resp_servicemanage):
        try:
            db_servicemanage = self.servicemanage_api.get(context, resp_servicemanage['id'])
        except Exception:
            return
        else:
            key = "%s:host" % ServiceManage_host_attribute.alias
            resp_servicemanage[key] = db_servicemanage['host']

    @wsgi.extends
    def show(self, req, resp_obj, id):
        context = req.environ['monitor.context']
        if authorize(context):
            resp_obj.attach(xml=ServiceManageHostAttributeTemplate())
            self._add_servicemanage_host_attribute(context, resp_obj.obj['servicemanage'])

    @wsgi.extends
    def detail(self, req, resp_obj):
        context = req.environ['monitor.context']
        if authorize(context):
            resp_obj.attach(xml=ServiceManageListHostAttributeTemplate())
            for servicemanage in list(resp_obj.obj['servicemanages']):
                self._add_servicemanage_host_attribute(context, servicemanage)


class ServiceManage_host_attribute(extensions.ExtensionDescriptor):
    """Expose host as an attribute of a servicemanage."""

    name = "ServiceManageHostAttribute"
    alias = "os-vol-host-attr"
    namespace = ("http://docs.openstack.org/servicemanage/ext/"
                 "servicemanage_host_attribute/api/v1")
    updated = "2011-11-03T00:00:00+00:00"

    def get_controller_extensions(self):
        controller = ServiceManageHostAttributeController()
        extension = extensions.ControllerExtension(self, 'servicemanages', controller)
        return [extension]


def make_servicemanage(elem):
    elem.set('{%s}host' % ServiceManage_host_attribute.namespace,
             '%s:host' % ServiceManage_host_attribute.alias)


class ServiceManageHostAttributeTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('servicemanage', selector='servicemanage')
        make_servicemanage(root)
        alias = ServiceManage_host_attribute.alias
        namespace = ServiceManage_host_attribute.namespace
        return xmlutil.SlaveTemplate(root, 1, nsmap={alias: namespace})


class ServiceManageListHostAttributeTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('servicemanages')
        elem = xmlutil.SubTemplateElement(root, 'servicemanage', selector='servicemanages')
        make_servicemanage(elem)
        alias = ServiceManage_host_attribute.alias
        namespace = ServiceManage_host_attribute.namespace
        return xmlutil.SlaveTemplate(root, 1, nsmap={alias: namespace})
