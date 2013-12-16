# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 Red Hat, Inc.
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

from monitor.api import common


class ViewBuilder(common.ViewBuilder):

    def show(self, request, servicemanage_type, brief=False):
        """Trim away extraneous servicemanage type attributes."""
        trimmed = dict(id=servicemanage_type.get('id'),
                       name=servicemanage_type.get('name'),
                       extra_specs=servicemanage_type.get('extra_specs'))
        return trimmed if brief else dict(servicemanage_type=trimmed)

    def index(self, request, servicemanage_types):
        """Index over trimmed servicemanage types"""
        servicemanage_types_list = [self.show(request, servicemanage_type, True)
                             for servicemanage_type in servicemanage_types]
        return dict(servicemanage_types=servicemanage_types_list)
