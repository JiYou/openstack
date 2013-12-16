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

=====================
 Installing Manually
=====================

Installing the Collector
========================

.. index::
   double: installing; collector

1. If you want to be able to retrieve image counters, you need to instruct
   Glance to send notifications to the bus by changing ``notifier_strategy``
   to ``rabbit`` or ``qpid`` in ``glance-api.conf`` and restarting the
   service.

2. In order to retrieve object store statistics, ceilometer needs
   access to swift with ``ResellerAdmin`` role. You should give this
   role to your ``os_username`` user for tenant ``os_tenant_name``:

   ::

     $ keystone role-create --name=ResellerAdmin
     +----------+----------------------------------+
     | Property |              Value               |
     +----------+----------------------------------+
     |    id    | 462fa46c13fd4798a95a3bfbe27b5e54 |
     |   name   |          ResellerAdmin           |
     +----------+----------------------------------+

     $ keystone user-role-add --tenant_id $SERVICE_TENANT \
                              --user_id $CEILOMETER_USER \
                              --role_id 462fa46c13fd4798a95a3bfbe27b5e54

   You'll also need to add the Ceilometer middleware to Swift to account for
   incoming and outgoing traffic, adding this lines to
   ``/etc/swift/proxy-server.conf``::

     [filter:ceilometer]
     use = egg:ceilometer#swift

   And adding ``ceilometer`` in the ``pipeline`` of that same file.

3. Install MongoDB.

   Follow the instructions to install the MongoDB_ package for your
   operating system, then start the service.

4. Clone the ceilometer git repository to the management server::

   $ cd /opt/stack
   $ git clone https://github.com/openstack/ceilometer.git

5. As a user with ``root`` permissions or ``sudo`` privileges, run the
   ceilometer installer::

   $ cd ceilometer
   $ sudo python setup.py install

6. Copy the sample configuration files from the source tree
   to their final location.

   ::

      $ mkdir -p /etc/ceilometer
      $ cp etc/ceilometer/*.json /etc/ceilometer
      $ cp etc/ceilometer/*.yaml /etc/ceilometer
      $ cp etc/ceilometer/ceilometer.conf.sample /etc/ceilometer/ceilometer.conf

7. Edit ``/etc/ceilometer/ceilometer.conf``

   1. Configure RPC

      Set the RPC-related options correctly so ceilometer's daemons
      can communicate with each other and receive notifications from
      the other projects.

      In particular, look for the ``*_control_exchange`` options and
      make sure the names are correct. If you did not change the
      ``control_exchange`` settings for the other components, the
      defaults should be correct.

      .. note::

         Ceilometer makes extensive use of the messaging bus, but has
         not yet been tested with ZeroMQ. We recommend using Rabbit or
         qpid for now.

   2. Set the ``metering_secret`` value.

      Set the ``metering_secret`` value to a large, random, value. Use
      the same value in all ceilometer configuration files, on all
      nodes, so that messages passing between the nodes can be
      validated.

   Refer to :doc:`/configuration` for details about any other options
   you might want to modify before starting the service.

8. Start the collector.

   ::

     $ ceilometer-collector

   .. note:: 

      The default development configuration of the collector logs to
      stderr, so you may want to run this step using a screen session
      or other tool for maintaining a long-running program in the
      background.

.. _MongoDB: http://www.mongodb.org/


Installing the Compute Agent
============================

.. index::
   double: installing; compute agent

.. note:: The compute agent must be installed on each nova compute node.

1. Configure nova.

   The ``nova`` compute service needs the following configuration to
   be set in ``nova.conf``::

      # nova-compute configuration for ceilometer
      instance_usage_audit=True
      instance_usage_audit_period=hour
      notification_driver=nova.openstack.common.notifier.rpc_notifier
      notification_driver=ceilometer.compute.nova_notifier

2. Clone the ceilometer git repository to the server::

   $ cd /opt/stack
   $ git clone https://github.com/openstack/ceilometer.git

4. As a user with ``root`` permissions or ``sudo`` privileges, run the
   ceilometer installer::

   $ cd ceilometer
   $ sudo python setup.py install

5. Copy the sample configuration files from the source tree
   to their final location.

   ::

      $ mkdir -p /etc/ceilometer
      $ cp etc/ceilometer/*.json /etc/ceilometer
      $ cp etc/ceilometer/*.yaml /etc/ceilometer
      $ cp etc/ceilometer/ceilometer.conf.sample /etc/ceilometer/ceilometer.conf

6. Edit ``/etc/ceilometer/ceilometer.conf``

   1. Configure RPC

      Set the RPC-related options correctly so ceilometer's daemons
      can communicate with each other and receive notifications from
      the other projects.

      In particular, look for the ``*_control_exchange`` options and
      make sure the names are correct. If you did not change the
      ``control_exchange`` settings for the other components, the
      defaults should be correct.

      .. note::

         Ceilometer makes extensive use of the messaging bus, but has
         not yet been tested with ZeroMQ. We recommend using Rabbit or
         qpid for now.

   2. Set the ``metering_secret`` value.

      Set the ``metering_secret`` value to a large, random, value. Use
      the same value in all ceilometer configuration files, on all
      nodes, so that messages passing between the nodes can be
      validated.

   Refer to :doc:`/configuration` for details about any other options
   you might want to modify before starting the service.

7. Start the agent.

   ::

     $ ceilometer-agent-compute

   .. note::

      The default development configuration of the agent logs to
      stderr, so you may want to run this step using a screen session
      or other tool for maintaining a long-running program in the
      background.

Installing the Central Agent
============================

.. index::
   double: installing; agent

.. note::

   The central agent needs to be able to talk to keystone and any of
   the services being polled for updates.

1. Clone the ceilometer git repository to the server::

   $ cd /opt/stack
   $ git clone https://github.com/openstack/ceilometer.git

2. As a user with ``root`` permissions or ``sudo`` privileges, run the
   ceilometer installer::

   $ cd ceilometer
   $ sudo python setup.py install

3. Copy the sample configuration files from the source tree
   to their final location.

   ::

      $ mkdir -p /etc/ceilometer
      $ cp etc/ceilometer/*.json /etc/ceilometer
      $ cp etc/ceilometer/*.yaml /etc/ceilometer
      $ cp etc/ceilometer/ceilometer.conf.sample /etc/ceilometer/ceilometer.conf

4. Edit ``/etc/ceilometer/ceilometer.conf``

   1. Configure RPC

      Set the RPC-related options correctly so ceilometer's daemons
      can communicate with each other and receive notifications from
      the other projects.

      In particular, look for the ``*_control_exchange`` options and
      make sure the names are correct. If you did not change the
      ``control_exchange`` settings for the other components, the
      defaults should be correct.

      .. note::

         Ceilometer makes extensive use of the messaging bus, but has
         not yet been tested with ZeroMQ. We recommend using Rabbit or
         qpid for now.

   2. Set the ``metering_secret`` value.

      Set the ``metering_secret`` value to a large, random, value. Use
      the same value in all ceilometer configuration files, on all
      nodes, so that messages passing between the nodes can be
      validated.

   Refer to :doc:`/configuration` for details about any other options
   you might want to modify before starting the service.

5. Start the agent

   ::

    $ ceilometer-agent-central


Installing the API Server
=========================

.. index::
   double: installing; API

.. note::
   The API server needs to be able to talk to keystone and ceilometer's
   database.

1. Clone the ceilometer git repository to the server::

   $ cd /opt/stack
   $ git clone https://github.com/openstack/ceilometer.git

2. As a user with ``root`` permissions or ``sudo`` privileges, run the
   ceilometer installer::

   $ cd ceilometer
   $ sudo python setup.py install

3. Copy the sample configuration files from the source tree
   to their final location.

   ::

      $ mkdir -p /etc/ceilometer
      $ cp etc/ceilometer/*.json /etc/ceilometer
      $ cp etc/ceilometer/*.yaml /etc/ceilometer
      $ cp etc/ceilometer/ceilometer.conf.sample /etc/ceilometer/ceilometer.conf

4. Edit ``/etc/ceilometer/ceilometer.conf``

   1. Configure RPC

      Set the RPC-related options correctly so ceilometer's daemons
      can communicate with each other and receive notifications from
      the other projects.

      In particular, look for the ``*_control_exchange`` options and
      make sure the names are correct. If you did not change the
      ``control_exchange`` settings for the other components, the
      defaults should be correct.

      .. note::

         Ceilometer makes extensive use of the messaging bus, but has
         not yet been tested with ZeroMQ. We recommend using Rabbit or
         qpid for now.

   Refer to :doc:`/configuration` for details about any other options
   you might want to modify before starting the service.

5. Start the API server.

   ::

    $ ceilometer-api

.. note::

   The development version of the API server logs to stderr, so you
   may want to run this step using a screen session or other tool for
   maintaining a long-running program in the background.


Configuring keystone to work with API
=====================================

.. index::
   double: installing; configure keystone

.. note::
   The API server needs to be able to talk to keystone to authenticate.

1. Create a service for ceilometer in keystone::

   $ keystone service-create --name=ceilometer \
                             --type=metering \
                             --description="Ceilometer Service"

2. Create an endpoint in keystone for ceilometer::

   $ keystone endpoint-create --region RegionOne \
                              --service_id $CEILOMETER_SERVICE \
                              --publicurl "http://$SERVICE_HOST:8777/" \
                              --adminurl "http://$SERVICE_HOST:8777/" \
                              --internalurl "http://$SERVICE_HOST:8777/"

.. note::

   CEILOMETER_SERVICE is the id of the service created by the first command
   and SERVICE_HOST is the host where the Ceilometer API is running. The
   default port value for ceilometer API is 8777. If the port value
   has been customized, adjust accordingly.

