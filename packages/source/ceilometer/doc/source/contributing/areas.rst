..
      Copyright 2012 New Dream Network, LLC (DreamHost)

      Licensed under the Apache License, Version 2.0 (the "License"); you may
      not use this file except in compliance with the License. You may obtain
      a copy of the License at

          http://www.apache.org/licenses/LICENSE-2.0

      Unless required by applicable law or agreed to in writing, software
      distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
      WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
      License for the specific language governing permissions and limitations
      under the License.

=====================
 Areas to Contribute
=====================

The Ceilometer project maintains a list of things that need to be worked on at:
http://wiki.openstack.org/EfficientMetering/RoadMap but feel free to work on
something else.

Plugins
=======

Ceilometer's architecture is based heavily on the use of plugins to
make it easy to extend to collect new sorts of data or store them in
different databases.

.. seealso::

   * :ref:`architecture`
   * :doc:`plugins`

Core
====

The core parts of ceilometer, not separated into a plugin, are fairly
simple but depend on code that is part of ``nova`` right now. One
project goal is to move the rest of those dependencies out of ``nova``
and into ``openstack-common``. Logging and RPC are already done, but
the service and manager base classes still need to move.

.. seealso::

   * https://launchpad.net/nova
   * https://launchpad.net/openstack-common

Testing
=======

The first version of ceilometer has extensive unit tests, but
has not seen much run-time in real environments. Setting up a copy of
ceilometer to monitor a real OpenStack installation or to perform some
load testing would be especially helpful.

.. seealso::

   * :ref:`install`
