..
      Copyright 2012 Nicolas Barcet for Canonical

      Licensed under the Apache License, Version 2.0 (the "License"); you may
      not use this file except in compliance with the License. You may obtain
      a copy of the License at

          http://www.apache.org/licenses/LICENSE-2.0

      Unless required by applicable law or agreed to in writing, software
      distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
      WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
      License for the specific language governing permissions and limitations
      under the License.

====================
Version 0.1 (Folsom)
====================

This is the first release of ceilometer. Please take all appropriate caution
in using it, as it is a technology preview at this time.

Version of OpenStack
   It is curently tested to work with OpenStack 2012.2 Folsom. Due to its use of
   openstack-common, and the modification that were made in term of notification
   to many other components (glance, cinder, quantum), it will not easily work
   with any prior version of OpenStack.

Components
   Currently covered components are: Nova, Nova-network, Glance, Cinder and
   Quantum. Notably, there is no support yet for Swift and it was decided not
   to support nova-volume in favor of Cinder. A detailed list of meters covered
   per component can be found at in :doc:`../measurements`.

Nova with libvirt only
   Most of the Nova meters will only work with libvirt fronted hypervisors at the
   moment, and our test coverage was mostly done on KVM. Contributors are welcome
   to implement other virtualization backends' meters.

Quantum delete events
   Quantum delete notifications do not include the same metadata as the other
   messages, so we ignore them for now. This isn't ideal, since it may mean we
   miss charging for some amount of time, but it is better than throwing away the
   existing metadata for a resource when it is deleted.

Database backend
   The only tested and complete database backend is currently MongoDB, the
   SQLAlchemy one is still work in progress.

Installation
   The current best source of information on how to deploy this project is found
   as the devstack implementation but feel free to come to #openstack-metering on
   freenode for more info.

Volume of data
   Please note that metering can generate lots of data very quickly. Have a look
   at the following spreadsheet to evaluate what you will end up with.

      http://wiki.openstack.org/EfficientMetering#Volume_of_data
