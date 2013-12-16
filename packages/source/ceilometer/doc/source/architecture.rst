.. _architecture:

=====================
 System Architecture
=====================

High Level Description
======================

.. index::
   single: agent; architecture
   double: compute agent; architecture
   double: collector; architecture
   double: data store; architecture
   double: database; architecture
   double: API; architecture

The following diagram summarizes ceilometer logical architecture:

.. The image source can be found at https://docs.google.com/drawings/d/1-6-DxU5ITyRcVJtJtPsc_zeiqzafZlir0AF7AkG4ZeQ/edit

.. image:: ./Ceilometer_Architecture.png

As shown in the above diagram, there are 5 basic components to the system:

1. A :term:`compute agent` runs on each compute node and polls for
   resource utilization statistics. There may be other types of agents
   in the future, but for now we will focus on creating the compute
   agent.

2. A :term:`central agent` runs on a central management server to
   poll for resource utilization statistics for resources not tied
   to instances or compute nodes.

3. A :term:`collector` runs on one or more central management
   servers to monitor the message queues (for notifications and for
   metering data coming from the agent). Notification messages are
   processed and turned into metering messages and sent back out onto
   the message bus using the appropriate topic. Metering messages are
   written to the data store without modification.

4. A :term:`data store` is a database capable of handling concurrent
   writes (from one or more collector instances) and reads (from the
   API server).

5. An :term:`API server` runs on one or more central management
   servers to provide access to the data from the data store. See
   `API Description`_ for details.

.. _API Description: api.html

These services communicate using the standard OpenStack messaging
bus. Only the collector and API server have access to the data store.

Detailed Description
====================

.. warning::

   These details cover only the compute agent and collector, as well
   as their communication via the messaging bus. More work is needed
   before the data store and API server designs can be documented.

Plugins
-------

.. index::
   double: plugins; architecture
   single: plugins; setuptools
   single: plugins; entry points

Although we have described a list of the metrics ceilometer should
collect, we cannot predict all of the ways deployers will want to
measure the resources their customers use. This means that ceilometer
needs to be easy to extend and configure so it can be tuned for each
installation. A plugin system based on `setuptools entry points`_
makes it easy to add new monitors in the collector or subagents for
polling.

.. _setuptools entry points: http://packages.python.org/distribute/setuptools.html#dynamic-discovery-of-services-and-plugins

Each daemon provides basic essential services in a framework to be
shared by the plugins, and the plugins do the specialized work.  As a
general rule, the plugins are asked to do as little work as
possible. This makes them more efficient as greenlets, maximizes code
reuse, and makes them simpler to implement.

Installing a plugin automatically activates it the next time the
ceilometer daemon starts. A global configuration option can be used to
disable installed plugins (for example, one or more of the "default"
set of plugins provided as part of the ceilometer package).

Plugins may require configuration options, so when the plugin is
loaded it is asked to add options to the global flags object, and the
results are made available to the plugin before it is asked to do any
work.

Rather than running and reporting errors or simply consuming cycles
for no-ops, plugins may disable themselves at runtime based on
configuration settings defined by other components (for example, the
plugin for polling libvirt does not run if it sees that the system is
configured using some other virtualization tool). The plugin is
asked once at startup, after it has been loaded and given the
configuration settings, if it should be enabled. Plugins should not
define their own flags for enabling or disabling themselves.

.. warning:: Plugin self-deactivation is not implemented, yet.

Each plugin API is defined by the namespace and an abstract base class
for the plugin instances. Plugins are not required to subclass from
the API definition class, but it is encouraged as a way to discover
API changes.

.. note::

   There is ongoing work to add a generic plugin system to Nova.  If
   that is implemented as part of the common library, ceilometer may
   use it (or adapt it as necessary for our use). If it remains part
   of Nova for Folsom we should probably not depend on it because
   loading plugins is trivial with setuptools.

Polling
-------

.. index::
   double: polling; architecture

Metering data comes from two sources: through notifications built into
the existing OpenStack components and by polling the infrastructure
(such as via libvirt). Polling for compute resources is handled by an
agent running on the compute node (where communication with the
hypervisor is more efficient).  The compute agent daemon is configured
to run one or more *pollster* plugins using the
``ceilometer.poll.compute`` namespace.  Polling for resources not tied
to the compute node is handled by the central agent.  The central
agent daemon is configured to run one or more *pollster* plugins using
the ``ceilometer.poll.central`` namespace.

The agents periodically asks each pollster for instances of
``Counter`` objects. The agent framework converts the Counters to
metering messages, which it then signs and transmits on the metering
message bus.

The pollster plugins do not communicate with the message bus directly,
unless it is necessary to do so in order to collect the information
for which they are polling.

All polling happens with the same frequency, controlled by a global
setting for the agent.

Handling Notifications
----------------------

.. index::
   double: notifications; architecture

The heart of the system is the collector, which monitors the message
bus for data being provided by the pollsters via the agent as well as
notification messages from other OpenStack components such as nova,
glance, quantum, and swift.

The collector loads one or more *listener* plugins, using the namespace
``ceilometer.collector``. Each plugin can listen to any topics, but by
default it will listen to ``notifications.info``.

The plugin provides a method to list the event types it wants and a
callback for processing incoming messages. The registered name of the
callback is used to enable or disable it using the global
configuration option of the collector daemon.  The incoming messages
are filtered based on their event type value before being passed to
the callback so the plugin only receives events it has expressed an
interest in seeing. For example, a callback asking for
``compute.instance.create.end`` events under
``ceilometer.collector.compute`` would be invoked for those
notification events on the ``nova`` exchange using the
``notifications.info`` topic.

The listener plugin returns an iterable with zero or more Counter
instances based on the data in the incoming message. The collector
framework code converts the Counter instances to metering messages and
publishes them on the metering message bus. Although ceilomter
includes a default storage solution to work with the API service, by
republishing on the metering message bus we can support installations
that want to handle their own data storage.

Handling Metering Messages
--------------------------

The listener for metering messages also runs in the collector
daemon. It validates the incoming data and (if the signature is valid)
then writes the messages to the data store.

.. note::

   Because this listener uses ``openstack.common.rpc`` instead of
   notifications, it is implemented directly in the collector code
   instead of as a plugin.

Metering messages are signed using the hmac_ module in Python's
standard library. A shared secret value can be provided in the
ceilometer configuration settings. The messages are signed by feeding
the message key names and values into the signature generator in
sorted order. Non-string values are converted to unicode and then
encoded as UTF-8. The message signature is included in the message for
verification by the collector, and stored in the database for future
verification by consumers who access the data via the API.

.. _hmac: http://docs.python.org/library/hmac.html

RPC
---

Ceilomter uses ``openstack.common.rpc`` to cast messages from the
agent to the collector.

.. seealso::

   * http://wiki.openstack.org/EfficientMetering/ArchitectureProposalV1
   * http://wiki.openstack.org/EfficientMetering#Architecture
   * `Bug 1010037`_ : allow different polling interval for each pollster

.. _Bug 1010037: https://bugs.launchpad.net/ceilometer/+bug/1010037
