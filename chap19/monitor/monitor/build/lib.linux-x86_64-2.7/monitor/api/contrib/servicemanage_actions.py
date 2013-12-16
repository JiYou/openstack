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

import webob

from monitor.api import extensions
from monitor.api.openstack import wsgi
from monitor.api import xmlutil
from monitor import exception
from monitor import flags
from monitor.openstack.common import log as logging
from monitor.openstack.common.rpc import common as rpc_common
from monitor import utils
from monitor import servicemanage


FLAGS = flags.FLAGS
LOG = logging.getLogger(__name__)


def authorize(context, action_name):
    action = 'servicemanage_actions:%s' % action_name
    extensions.extension_authorizer('servicemanage', action)(context)


class ServiceManageToImageSerializer(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('os-servicemanage_upload_image',
                                       selector='os-servicemanage_upload_image')
        root.set('id')
        root.set('updated_at')
        root.set('status')
        root.set('display_description')
        root.set('size')
        root.set('servicemanage_type')
        root.set('image_id')
        root.set('container_format')
        root.set('disk_format')
        root.set('image_name')
        return xmlutil.MasterTemplate(root, 1)


class ServiceManageToImageDeserializer(wsgi.XMLDeserializer):
    """Deserializer to handle xml-formatted requests."""
    def default(self, string):
        dom = utils.safe_minidom_parse_string(string)
        action_node = dom.childNodes[0]
        action_name = action_node.tagName

        action_data = {}
        attributes = ["force", "image_name", "container_format", "disk_format"]
        for attr in attributes:
            if action_node.hasAttribute(attr):
                action_data[attr] = action_node.getAttribute(attr)
        if 'force' in action_data and action_data['force'] == 'True':
            action_data['force'] = True
        return {'body': {action_name: action_data}}


class ServiceManageActionsController(wsgi.Controller):
    def __init__(self, *args, **kwargs):
        super(ServiceManageActionsController, self).__init__(*args, **kwargs)
        self.servicemanage_api = servicemanage.API()

    @wsgi.action('os-attach')
    def _attach(self, req, id, body):
        """Add attachment metadata."""
        context = req.environ['monitor.context']
        servicemanage = self.servicemanage_api.get(context, id)

        instance_uuid = body['os-attach']['instance_uuid']
        mountpoint = body['os-attach']['mountpoint']

        self.servicemanage_api.attach(context, servicemanage,
                               instance_uuid, mountpoint)
        return webob.Response(status_int=202)

    @wsgi.action('os-detach')
    def _detach(self, req, id, body):
        """Clear attachment metadata."""
        context = req.environ['monitor.context']
        servicemanage = self.servicemanage_api.get(context, id)
        self.servicemanage_api.detach(context, servicemanage)
        return webob.Response(status_int=202)

    @wsgi.action('os-reserve')
    def _reserve(self, req, id, body):
        """Mark servicemanage as reserved."""
        context = req.environ['monitor.context']
        servicemanage = self.servicemanage_api.get(context, id)
        self.servicemanage_api.reserve_servicemanage(context, servicemanage)
        return webob.Response(status_int=202)

    @wsgi.action('os-unreserve')
    def _unreserve(self, req, id, body):
        """Unmark servicemanage as reserved."""
        context = req.environ['monitor.context']
        servicemanage = self.servicemanage_api.get(context, id)
        self.servicemanage_api.unreserve_servicemanage(context, servicemanage)
        return webob.Response(status_int=202)

    @wsgi.action('os-begin_detaching')
    def _begin_detaching(self, req, id, body):
        """Update servicemanage status to 'detaching'."""
        context = req.environ['monitor.context']
        servicemanage = self.servicemanage_api.get(context, id)
        self.servicemanage_api.begin_detaching(context, servicemanage)
        return webob.Response(status_int=202)

    @wsgi.action('os-roll_detaching')
    def _roll_detaching(self, req, id, body):
        """Roll back servicemanage status to 'in-use'."""
        context = req.environ['monitor.context']
        servicemanage = self.servicemanage_api.get(context, id)
        self.servicemanage_api.roll_detaching(context, servicemanage)
        return webob.Response(status_int=202)

    @wsgi.action('os-initialize_connection')
    def _initialize_connection(self, req, id, body):
        """Initialize servicemanage attachment."""
        context = req.environ['monitor.context']
        servicemanage = self.servicemanage_api.get(context, id)
        connector = body['os-initialize_connection']['connector']
        info = self.servicemanage_api.initialize_connection(context,
                                                     servicemanage,
                                                     connector)
        return {'connection_info': info}

    @wsgi.action('os-terminate_connection')
    def _terminate_connection(self, req, id, body):
        """Terminate servicemanage attachment."""
        context = req.environ['monitor.context']
        servicemanage = self.servicemanage_api.get(context, id)
        connector = body['os-terminate_connection']['connector']
        self.servicemanage_api.terminate_connection(context, servicemanage, connector)
        return webob.Response(status_int=202)

    @wsgi.response(202)
    @wsgi.action('os-servicemanage_upload_image')
    @wsgi.serializers(xml=ServiceManageToImageSerializer)
    @wsgi.deserializers(xml=ServiceManageToImageDeserializer)
    def _servicemanage_upload_image(self, req, id, body):
        """Uploads the specified servicemanage to image service."""
        context = req.environ['monitor.context']
        try:
            params = body['os-servicemanage_upload_image']
        except (TypeError, KeyError):
            msg = _("Invalid request body")
            raise webob.exc.HTTPBadRequest(explanation=msg)

        if not params.get("image_name"):
            msg = _("No image_name was specified in request.")
            raise webob.exc.HTTPBadRequest(explanation=msg)

        force = params.get('force', False)
        try:
            servicemanage = self.servicemanage_api.get(context, id)
        except exception.ServiceManageNotFound, error:
            raise webob.exc.HTTPNotFound(explanation=unicode(error))
        authorize(context, "upload_image")
        image_metadata = {"container_format": params.get("container_format",
                                                         "bare"),
                          "disk_format": params.get("disk_format", "raw"),
                          "name": params["image_name"]}
        try:
            response = self.servicemanage_api.copy_servicemanage_to_image(context,
                                                            servicemanage,
                                                            image_metadata,
                                                            force)
        except exception.InvalidServiceManage, error:
            raise webob.exc.HTTPBadRequest(explanation=unicode(error))
        except ValueError, error:
            raise webob.exc.HTTPBadRequest(explanation=unicode(error))
        except rpc_common.RemoteError as error:
            msg = "%(err_type)s: %(err_msg)s" % {'err_type': error.exc_type,
                                                 'err_msg': error.value}
            raise webob.exc.HTTPBadRequest(explanation=msg)
        return {'os-servicemanage_upload_image': response}


class ServiceManage_actions(extensions.ExtensionDescriptor):
    """Enable servicemanage actions
    """

    name = "ServiceManageActions"
    alias = "os-servicemanage-actions"
    namespace = "http://docs.openstack.org/servicemanage/ext/servicemanage-actions/api/v1.1"
    updated = "2012-05-31T00:00:00+00:00"

    def get_controller_extensions(self):
        controller = ServiceManageActionsController()
        extension = extensions.ControllerExtension(self, 'servicemanages', controller)
        return [extension]
