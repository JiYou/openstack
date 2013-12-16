# Copyright (c) 2011 Rackspace US, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""
ServiceManage Type interface.
"""

from monitorclient import base


class ServiceManageType(base.Resource):
    """
    A ServiceManage Type is the type of monitor to be created
    """
    def __repr__(self):
        return "<ServiceManageType: %s>" % self.name

    def get_keys(self):
        """
        Get extra specs from a monitor type.

        :param vol_type: The :class:`ServiceManageType` to get extra specs from
        """
        _resp, body = self.manager.api.client.get(
            "/types/%s/extra_specs" %
            base.getid(self))
        return body["extra_specs"]

    def set_keys(self, metadata):
        """
        Set extra specs on a monitor type.

        :param type : The :class:`ServiceManageType` to set extra spec on
        :param metadata: A dict of key/value pairs to be set
        """
        body = {'extra_specs': metadata}
        return self.manager._create(
            "/types/%s/extra_specs" % base.getid(self),
            body,
            "extra_specs",
            return_raw=True)

    def unset_keys(self, keys):
        """
        Unset extra specs on a volue type.

        :param type_id: The :class:`ServiceManageType` to unset extra spec on
        :param keys: A list of keys to be unset
        """

        # NOTE(jdg): This wasn't actually doing all of the keys before
        # the return in the loop resulted in ony ONE key being unset.
        # since on success the return was NONE, we'll only interrupt the loop
        # and return if there's an error
        resp = None
        for k in keys:
            resp = self.manager._delete(
                "/types/%s/extra_specs/%s" % (
                base.getid(self), k))
            if resp is not None:
                return resp


class ServiceManageTypeManager(base.ManagerWithFind):
    """
    Manage :class:`ServiceManageType` resources.
    """
    resource_class = ServiceManageType

    def list(self):
        """
        Get a list of all monitor types.

        :rtype: list of :class:`ServiceManageType`.
        """
        return self._list("/types", "monitor_types")

    def get(self, monitor_type):
        """
        Get a specific monitor type.

        :param monitor_type: The ID of the :class:`ServiceManageType` to get.
        :rtype: :class:`ServiceManageType`
        """
        return self._get("/types/%s" % base.getid(monitor_type), "monitor_type")

    def delete(self, monitor_type):
        """
        Delete a specific monitor_type.

        :param monitor_type: The ID of the :class:`ServiceManageType` to get.
        """
        self._delete("/types/%s" % base.getid(monitor_type))

    def create(self, name):
        """
        Create a monitor type.

        :param name: Descriptive name of the monitor type
        :rtype: :class:`ServiceManageType`
        """

        body = {
            "monitor_type": {
                "name": name,
            }
        }

        return self._create("/types", body, "monitor_type")
