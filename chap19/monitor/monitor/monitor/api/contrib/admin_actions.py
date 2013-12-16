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
from webob import exc

from monitor.api import extensions
from monitor.api.openstack import wsgi
from monitor import db
from monitor import exception
from monitor.openstack.common import log as logging
from monitor import servicemanage


LOG = logging.getLogger(__name__)


class AdminController(wsgi.Controller):
    """Abstract base class for AdminControllers."""

    collection = None  # api collection to extend

    # FIXME(clayg): this will be hard to keep up-to-date
    # Concrete classes can expand or over-ride
    valid_status = set([
        'creating',
        'available',
        'deleting',
        'error',
        'error_deleting',
    ])

    def __init__(self, *args, **kwargs):
        super(AdminController, self).__init__(*args, **kwargs)
        # singular name of the resource
        self.resource_name = self.collection.rstrip('s')
        self.servicemanage_api = servicemanage.API()

    def _update(self, *args, **kwargs):
        raise NotImplementedError()

    def _get(self, *args, **kwargs):
        raise NotImplementedError()

    def _delete(self, *args, **kwargs):
        raise NotImplementedError()

    def validate_update(self, body):
        update = {}
        try:
            update['status'] = body['status']
        except (TypeError, KeyError):
            raise exc.HTTPBadRequest("Must specify 'status'")
        if update['status'] not in self.valid_status:
            raise exc.HTTPBadRequest("Must specify a valid status")
        return update

    def authorize(self, context, action_name):
        # e.g. "snapshot_admin_actions:reset_status"
        action = '%s_admin_actions:%s' % (self.resource_name, action_name)
        extensions.extension_authorizer('servicemanage', action)(context)

    @wsgi.action('os-reset_status')
    def _reset_status(self, req, id, body):
        """Reset status on the resource."""
        context = req.environ['monitor.context']
        self.authorize(context, 'reset_status')
        update = self.validate_update(body['os-reset_status'])
        msg = _("Updating %(resource)s '%(id)s' with '%(update)r'")
        LOG.debug(msg, {'resource': self.resource_name, 'id': id,
                        'update': update})
        try:
            self._update(context, id, update)
        except exception.NotFound, e:
            raise exc.HTTPNotFound(e)
        return webob.Response(status_int=202)

    @wsgi.action('os-force_delete')
    def _force_delete(self, req, id, body):
        """Delete a resource, bypassing the check that it must be available."""
        context = req.environ['monitor.context']
        self.authorize(context, 'force_delete')
        try:
            resource = self._get(context, id)
        except exception.NotFound:
            raise exc.HTTPNotFound()
        self._delete(context, resource, force=True)
        return webob.Response(status_int=202)


class ServiceManageAdminController(AdminController):
    """AdminController for ServiceManages."""

    collection = 'servicemanages'
    valid_status = AdminController.valid_status.union(
        set(['attaching', 'in-use', 'detaching']))

    def _update(self, *args, **kwargs):
        db.servicemanage_update(*args, **kwargs)

    def _get(self, *args, **kwargs):
        return self.servicemanage_api.get(*args, **kwargs)

    def _delete(self, *args, **kwargs):
        return self.servicemanage_api.delete(*args, **kwargs)

    def validate_update(self, body):
        update = super(ServiceManageAdminController, self).validate_update(body)
        if 'attach_status' in body:
            if body['attach_status'] not in ('detached', 'attached'):
                raise exc.HTTPBadRequest("Must specify a valid attach_status")
            update['attach_status'] = body['attach_status']
        return update

    @wsgi.action('os-force_detach')
    def _force_detach(self, req, id, body):
        """
        Roll back a bad detach after the servicemanage been disconnected from
        the hypervisor.
        """
        context = req.environ['monitor.context']
        self.authorize(context, 'force_detach')
        try:
            servicemanage = self._get(context, id)
        except exception.NotFound:
            raise exc.HTTPNotFound()
        self.servicemanage_api.terminate_connection(context, servicemanage,
                                             {}, force=True)
        self.servicemanage_api.detach(context, servicemanage)
        return webob.Response(status_int=202)


class SnapshotAdminController(AdminController):
    """AdminController for Snapshots."""

    collection = 'snapshots'

    def _update(self, *args, **kwargs):
        db.snapshot_update(*args, **kwargs)

    def _get(self, *args, **kwargs):
        return self.servicemanage_api.get_snapshot(*args, **kwargs)

    def _delete(self, *args, **kwargs):
        return self.servicemanage_api.delete_snapshot(*args, **kwargs)


class Admin_actions(extensions.ExtensionDescriptor):
    """Enable admin actions."""

    name = "AdminActions"
    alias = "os-admin-actions"
    namespace = "http://docs.openstack.org/servicemanage/ext/admin-actions/api/v1.1"
    updated = "2012-08-25T00:00:00+00:00"

    def get_controller_extensions(self):
        exts = []
        for class_ in (ServiceManageAdminController, SnapshotAdminController):
            controller = class_()
            extension = extensions.ControllerExtension(
                self, class_.collection, controller)
            exts.append(extension)
        return exts
