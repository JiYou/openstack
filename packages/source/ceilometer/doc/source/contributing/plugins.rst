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

=======================
 Writing Agent Plugins
=======================

This documentation gives you some clues on how to write a new agent or
plugin for Ceilometer if you wish to instrument a measurement which
has not yet been covered by an existing plugin.

Agents
======

The compute agent runs on each compute node to poll for resource
usage. Each metric collected is tagged with the resource ID (such as
an instance) and the owner, including tenant and user IDs. The metrics
are then reported to the collector via the message bus. More detailed
information follows.

The compute agent is implemented in ``ceilometer/compute/manager.py``. As
you will see in the manager, the computeagent loads all plugins defined in
the namespace ``ceilometer.poll.compute``, then periodically calls their
:func:`get_counters` method.

The central agent polls other types of resources from a management server.
The central agent is defined in ``ceilometer/central/manager.py``. It loads
plugins from the ``ceilometer.poll.central`` namespace and polls them by
calling their :func:`get_counters` method.

Plugins
=======

An agent can support multiple plugins to retrieve different
information and send them to the collector. As stated above, an agent
will automatically activate all plugins of a given class. For example,
the compute agent will load all plugins of class
``ceilometer.poll.compute``.  This will load, among others, the
:class:`ceilometer.compute.pollsters.CPUPollster`, which is defined in
the file ``ceilometer/compute/pollsters.py`` as well as the
:class:`ceilometer.compute.notifications.InstanceNotifications` plugin
which is defined in the file ``ceilometer/compute/notifications.py``

We are using these two existing plugins as examples as the first one provides
an example of how to interact when you need to retrieve information from an
external system (pollster) and the second one is an example of how to forward
an existing event notification on the standard OpenStack queue to ceilometer.

Pollster
--------

Compute plugins are defined as subclasses of the
:class:`ceilometer.compute.plugin.ComputePollster` class as defined in
the ``ceilometer/compute/plugin.py`` file. Pollsters must implement one
method: ``get_counters(self, manager, context)``, which returns a
sequence of ``Counter`` objects as defined in the
``ceilometer/counter.py`` file.

In the ``CPUPollster`` plugin, the ``get_counters`` method is implemented as a loop
which, for each instances running on the local host, retrieves the cpu_time
from the hypervisor and sends back two ``Counter`` objects.  The first one, named
"cpu", is of type "cumulative", meaning that between two polls, its value is
not reset, or in other word that the cpu value is always provided as a duration
that continuously increases since the creation of the instance. The second one,
named "cpu_util", is of type "gauge", meaning that its value is the percentage
of cpu utilization.

Note that the ``LOG`` method is only used as a debugging tool and does not
participate in the actual metering activity.

Notifications
-------------

Notifications are defined as subclass of the
:class:`ceilometer.plugin.NotificationBase` meta class as defined in
the ``ceilometer/plugin.py`` file.  Notifications must implement two
methods:

   ``get_event_types(self)`` which should return a sequence of strings defining the event types to be given to the plugin and

   ``process_notification(self, message)`` which receives an event message from the list provided to get_event_types and returns a sequence of Counter objects as defined in the ``ceilometer/counter.py`` file.

In the ``InstanceNotifications`` plugin, it listens to three events:

* compute.instance.create.end

* compute.instance.exists

* compute.instance.delete.start

using the ``get_event_type`` method and subsequently the method
``process_notification`` will be invoked each time such events are happening which
generates the appropriate counter objects to be sent to the collector.

Tests
=====
Any new plugin or agent contribution will only be accepted into the project if
provided together with unit tests.  Those are defined for the compute agent
plugins in the directory ``tests/compute`` and for the agent itself in ``test/agent``.
Unit tests are run in a continuous integration process for each commit made to
the project, thus ensuring as best as possible that a given patch has no side
effect to the rest of the project.
