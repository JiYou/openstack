..
      Copyright 2012 Nicolas Barcet for Canonical
                2013 New Dream Network, LLC (DreamHost)

      Licensed under the Apache License, Version 2.0 (the "License"); you may
      not use this file except in compliance with the License. You may obtain
      a copy of the License at

          http://www.apache.org/licenses/LICENSE-2.0

      Unless required by applicable law or agreed to in writing, software
      distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
      WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
      License for the specific language governing permissions and limitations
      under the License.

================================================
 Installing and Running the Development Version
================================================

Ceilometer has four daemons. The :term:`compute agent` runs on the
Nova compute node(s) while the :term:`central agent` and
:term:`collector` run on the cloud's management node(s). In a
development environment created by devstack_, these two are typically
the same server. They do not have to be, though, so some of the
instructions below are duplicated. Skip the steps you have already
done.

.. _devstack: http://www.devstack.org/

Configuring Devstack
====================

.. index::
   double: installing; devstack

1. Create a ``localrc`` file as input to devstack.

2. Ceilometer makes extensive use of the messaging bus, but has not
   yet been tested with ZeroMQ. We recommend using Rabbit or qpid for
   now.

3. Nova does not generate the periodic notifications for all known
   instances by default. To enable these auditing events, set
   ``instance_usage_audit`` to true in the nova configuration file.

4. Cinder does not generate notifications by default. To enable
   these auditing events, set the following in the cinder configuration file::

      notification_driver=cinder.openstack.common.notifier.rpc_notifier

5. The ceilometer services are not enabled by default, so they must be
   enabled in ``localrc`` before running ``stack.sh``.

This example ``localrc`` file shows all of the settings required for
ceilometer::

   # Enable the ceilometer services
   enable_service ceilometer-acompute,ceilometer-acentral,ceilometer-collector,ceilometer-api
