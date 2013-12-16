# Copyright (C) 2013 Hewlett-Packard Development Company, L.P.
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
ServiceManage Backups interface (1.1 extension).
"""

from monitorclient import base


class ServiceManageBackup(base.Resource):
    """A monitor backup is a block level backup of a monitor."""
    def __repr__(self):
        return "<ServiceManageBackup: %s>" % self.id

    def delete(self):
        """Delete this monitor backup."""
        return self.manager.delete(self)


class ServiceManageBackupManager(base.ManagerWithFind):
    """Manage :class:`ServiceManageBackup` resources."""
    resource_class = ServiceManageBackup

    def create(self, monitor_id, container=None,
               name=None, description=None):
        """Create a monitor backup.

        :param monitor_id: The ID of the monitor to backup.
        :param container: The name of the backup service container.
        :param name: The name of the backup.
        :param description: The description of the backup.
        :rtype: :class:`ServiceManageBackup`
        """
        body = {'backup': {'monitor_id': monitor_id,
                           'container': container,
                           'name': name,
                           'description': description}}
        return self._create('/backups', body, 'backup')

    def get(self, backup_id):
        """Show details of a monitor backup.

        :param backup_id: The ID of the backup to display.
        :rtype: :class:`ServiceManageBackup`
        """
        return self._get("/backups/%s" % backup_id, "backup")

    def list(self, detailed=True):
        """Get a list of all monitor backups.

        :rtype: list of :class:`ServiceManageBackup`
        """
        if detailed is True:
            return self._list("/backups/detail", "backups")
        else:
            return self._list("/backups", "backups")

    def delete(self, backup):
        """Delete a monitor backup.

        :param backup: The :class:`ServiceManageBackup` to delete.
        """
        self._delete("/backups/%s" % base.getid(backup))
