..
      Copyright 2010-2011 United States Government as represented by the
      Administrator of the National Aeronautics and Space Administration.
      All Rights Reserved.

      Licensed under the Apache License, Version 2.0 (the "License"); you may
      not use this file except in compliance with the License. You may obtain
      a copy of the License at

          http://www.apache.org/licenses/LICENSE-2.0

      Unless required by applicable law or agreed to in writing, software
      distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
      WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
      License for the specific language governing permissions and limitations
      under the License.

Storage ServiceManages, Disks
======================

.. todo:: rework after iSCSI merge (see 'Old Docs') (todd or vish)


The :mod:`monitor.servicemanage.manager` Module
-------------------------------------

.. automodule:: monitor.servicemanage.manager
    :noindex:
    :members:
    :undoc-members:
    :show-inheritance:

The :mod:`monitor.servicemanage.driver` Module
-------------------------------------

.. automodule:: monitor.servicemanage.driver
    :noindex:
    :members:
    :undoc-members:
    :show-inheritance:
    :exclude-members: FakeAOEDriver

Tests
-----

The :mod:`servicemanage_unittest` Module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: monitor.tests.servicemanage_unittest
    :noindex:
    :members:
    :undoc-members:
    :show-inheritance:

Old Docs
--------

Vsm uses iSCSI to export storage servicemanages from multiple storage nodes. These iSCSI exports are attached (using libvirt) directly to running instances.

Vsm servicemanages are exported over the primary system VLAN (usually VLAN 1), and not over individual VLANs.

The underlying servicemanages by default are LVM logical servicemanages, created on demand within a single large servicemanage group.


