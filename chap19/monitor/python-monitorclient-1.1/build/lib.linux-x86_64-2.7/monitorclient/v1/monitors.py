# Copyright 2011 Denali Systems, Inc.
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
ServiceManage interface (1.1 extension).
"""

import urllib
from monitorclient import base


class ServiceManage(base.Resource):
    """A monitor is an extra block level storage to the OpenStack instances."""
    def __repr__(self):
        return "<ServiceManage: %s>" % self.id

    def delete(self):
        """Delete this monitor."""
        self.manager.delete(self)

    def update(self, **kwargs):
        """Update the display_name or display_description for this monitor."""
        self.manager.update(self, **kwargs)

    def attach(self, instance_uuid, mountpoint):
        """Set attachment metadata.

        :param instance_uuid: uuid of the attaching instance.
        :param mountpoint: mountpoint on the attaching instance.
        """
        return self.manager.attach(self, instance_uuid, mountpoint)

    def detach(self):
        """Clear attachment metadata."""
        return self.manager.detach(self)

    def reserve(self, monitor):
        """Reserve this monitor."""
        return self.manager.reserve(self)

    def unreserve(self, monitor):
        """Unreserve this monitor."""
        return self.manager.unreserve(self)

    def begin_detaching(self, monitor):
        """Begin detaching monitor."""
        return self.manager.begin_detaching(self)

    def roll_detaching(self, monitor):
        """Roll detaching monitor."""
        return self.manager.roll_detaching(self)

    def initialize_connection(self, monitor, connector):
        """Initialize a monitor connection.

        :param connector: connector dict from nova.
        """
        return self.manager.initialize_connection(self, connector)

    def terminate_connection(self, monitor, connector):
        """Terminate a monitor connection.

        :param connector: connector dict from nova.
        """
        return self.manager.terminate_connection(self, connector)

    def set_metadata(self, monitor, metadata):
        """Set or Append metadata to a monitor.

        :param type : The :class: `ServiceManage` to set metadata on
        :param metadata: A dict of key/value pairs to set
        """
        return self.manager.set_metadata(self, metadata)

    def upload_to_image(self, force, image_name, container_format,
                        disk_format):
        """Upload a monitor to image service as an image."""
        self.manager.upload_to_image(self, force, image_name, container_format,
                                     disk_format)

    def force_delete(self):
        """Delete the specified monitor ignoring its current state.

        :param monitor: The UUID of the monitor to force-delete.
        """
        self.manager.force_delete(self)


class ServiceManageManager(base.ManagerWithFind):
    """
    Manage :class:`ServiceManage` resources.
    """
    resource_class = ServiceManage

    def create(self, size, snapshot_id=None, source_volid=None,
               display_name=None, display_description=None,
               monitor_type=None, user_id=None,
               project_id=None, availability_zone=None,
               metadata=None, imageRef=None):
        """
        Create a monitor.

        :param size: Size of monitor in GB
        :param snapshot_id: ID of the snapshot
        :param display_name: Name of the monitor
        :param display_description: Description of the monitor
        :param monitor_type: Type of monitor
        :rtype: :class:`ServiceManage`
        :param user_id: User id derived from context
        :param project_id: Project id derived from context
        :param availability_zone: Availability Zone to use
        :param metadata: Optional metadata to set on monitor creation
        :param imageRef: reference to an image stored in glance
        :param source_volid: ID of source monitor to clone from
        """

        if metadata is None:
            monitor_metadata = {}
        else:
            monitor_metadata = metadata

        body = {'monitor': {'size': size,
                           'snapshot_id': snapshot_id,
                           'display_name': display_name,
                           'display_description': display_description,
                           'monitor_type': monitor_type,
                           'user_id': user_id,
                           'project_id': project_id,
                           'availability_zone': availability_zone,
                           'status': "creating",
                           'attach_status': "detached",
                           'metadata': monitor_metadata,
                           'imageRef': imageRef,
                           'source_volid': source_volid,
                           }}
        return self._create('/monitors', body, 'monitor')

    def get(self, monitor_id):
        """
        Get a monitor.

        :param monitor_id: The ID of the monitor to delete.
        :rtype: :class:`ServiceManage`
        """
        return self._get("/monitors/%s" % monitor_id, "monitor")

    def list(self, detailed=True, search_opts=None):
        """
        Get a list of all monitors.

        :rtype: list of :class:`ServiceManage`
        """
        if search_opts is None:
            search_opts = {}

        qparams = {}

        for opt, val in search_opts.iteritems():
            if val:
                qparams[opt] = val

        query_string = "?%s" % urllib.urlencode(qparams) if qparams else ""

        detail = ""
        if detailed:
            detail = "/detail"

        ret = self._list("/dbservice%s%s" % (detail, query_string),
                          "dbservice")
        return ret

    def delete(self, monitor):
        """
        Delete a monitor.

        :param monitor: The :class:`ServiceManage` to delete.
        """
        self._delete("/monitors/%s" % base.getid(monitor))

    def update(self, monitor, **kwargs):
        """
        Update the display_name or display_description for a monitor.

        :param monitor: The :class:`ServiceManage` to delete.
        """
        if not kwargs:
            return

        body = {"monitor": kwargs}

        self._update("/monitors/%s" % base.getid(monitor), body)

    def _action(self, action, monitor, info=None, **kwargs):
        """
        Perform a monitor "action."
        """
        body = {action: info}
        self.run_hooks('modify_body_for_action', body, **kwargs)
        url = '/monitors/%s/action' % base.getid(monitor)
        return self.api.client.post(url, body=body)

    def host_status(self, req=None):
        """
        Perform a monitor "action."
        """
        body = {'request': req}
        url = '/dbservice/host_status'
        return self.api.client.post(url, body=body)

    def resource_info(self, req=None):
        """
        Perform a monitor "action."
        """
        body = {'request': req}
        url = '/dbservice/resource_info'
        return self.api.client.post(url, body=body)

    def asm_settings(self, req=None):
        """
        Perform a monitor "action."
        """
        body = {'request': req}
        url = '/dbservice/asm_settings'
        return self.api.client.post(url, body=body)

    def asm_settings_update(self, req=None):
        """
        Perform a monitor "action."
        """
        body = {'request': req}
        url = '/dbservice/asm_settings_update'
        return self.api.client.post(url, body=body)

    def asm_start_host(self, req=None):
        """
        Perform a monitor "action."
        """
        body = {'request': req}
        url = '/asm/asm_start_host'
        return self.api.client.post(url, body=body)

    def pas_host_select(self, req=None):
        """
        Perform a pas "action."
        """
        body = {'request': req}
        url = '/pas/pas_host_select'
        return self.api.client.post(url, body=body)

    def attach(self, monitor, instance_uuid, mountpoint):
        """
        Set attachment metadata.

        :param monitor: The :class:`ServiceManage` (or its ID)
                       you would like to attach.
        :param instance_uuid: uuid of the attaching instance.
        :param mountpoint: mountpoint on the attaching instance.
        """
        return self._action('os-attach',
                            monitor,
                            {'instance_uuid': instance_uuid,
                             'mountpoint': mountpoint})

    def detach(self, monitor):
        """
        Clear attachment metadata.

        :param monitor: The :class:`ServiceManage` (or its ID)
                       you would like to detach.
        """
        return self._action('os-detach', monitor)

    def reserve(self, monitor):
        """
        Reserve this monitor.

        :param monitor: The :class:`ServiceManage` (or its ID)
                       you would like to reserve.
        """
        return self._action('os-reserve', monitor)

    def unreserve(self, monitor):
        """
        Unreserve this monitor.

        :param monitor: The :class:`ServiceManage` (or its ID)
                       you would like to unreserve.
        """
        return self._action('os-unreserve', monitor)

    def begin_detaching(self, monitor):
        """
        Begin detaching this monitor.

        :param monitor: The :class:`ServiceManage` (or its ID)
                       you would like to detach.
        """
        return self._action('os-begin_detaching', monitor)

    def roll_detaching(self, monitor):
        """
        Roll detaching this monitor.

        :param monitor: The :class:`ServiceManage` (or its ID)
                       you would like to roll detaching.
        """
        return self._action('os-roll_detaching', monitor)

    def initialize_connection(self, monitor, connector):
        """
        Initialize a monitor connection.

        :param monitor: The :class:`ServiceManage` (or its ID).
        :param connector: connector dict from nova.
        """
        return self._action('os-initialize_connection', monitor,
                            {'connector': connector})[1]['connection_info']

    def terminate_connection(self, monitor, connector):
        """
        Terminate a monitor connection.

        :param monitor: The :class:`ServiceManage` (or its ID).
        :param connector: connector dict from nova.
        """
        self._action('os-terminate_connection', monitor,
                     {'connector': connector})

    def set_metadata(self, monitor, metadata):
        """
        Update/Set a monitors metadata.

        :param monitor: The :class:`ServiceManage`.
        :param metadata: A list of keys to be set.
        """
        body = {'metadata': metadata}
        return self._create("/monitors/%s/metadata" % base.getid(monitor),
                            body, "metadata")

    def delete_metadata(self, monitor, keys):
        """
        Delete specified keys from monitors metadata.

        :param monitor: The :class:`ServiceManage`.
        :param metadata: A list of keys to be removed.
        """
        for k in keys:
            self._delete("/monitors/%s/metadata/%s" % (base.getid(monitor), k))

    def upload_to_image(self, monitor, force, image_name, container_format,
                        disk_format):
        """
        Upload monitor to image service as image.

        :param monitor: The :class:`ServiceManage` to upload.
        """
        return self._action('os-monitor_upload_image',
                            monitor,
                            {'force': force,
                            'image_name': image_name,
                            'container_format': container_format,
                            'disk_format': disk_format})

    def force_delete(self, monitor):
        return self._action('os-force_delete', base.getid(monitor))
