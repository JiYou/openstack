..
      Copyright 2012 New Dream Network (DreamHost)

      Licensed under the Apache License, Version 2.0 (the "License"); you may
      not use this file except in compliance with the License. You may obtain
      a copy of the License at

          http://www.apache.org/licenses/LICENSE-2.0

      Unless required by applicable law or agreed to in writing, software
      distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
      WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
      License for the specific language governing permissions and limitations
      under the License.

.. _measurements:

==============
 Measurements
==============

Three type of meters are defined in ceilometer:

.. index::
   double: meter; cumulative
   double: meter; gauge
   double: meter; delta

==========  ==============================================================================
Type        Definition
==========  ==============================================================================
Cumulative  Increasing over time (instance hours)
Gauge       Discrete items (floating IPs, image uploads) and fluctuating values (disk I/O)
Delta       Changing over time (bandwidth)
==========  ==============================================================================

Units
=====

1. Whenever a volume is to be measured, SI approved units and their
   approved symbols or abbreviations should be used. Information units
   should be expressed in bits ('b') or bytes ('B').
2. For a given meter, the units should NEVER, EVER be changed.
3. When the measurement does not represent a volume, the unit
   description should always described WHAT is measured (ie: apples,
   disk, routers, floating IPs, etc.).
4. When creating a new meter, if another meter exists measuring
   something similar, the same units and precision should be used.
5. Samples (aka "meters" or "counters") should always document their
   units in Ceilometer (API and Documentation) and new sampling code
   should not be merged without the appropriate documentation.

============  ========  ==============  =====
Dimension     Unit      Abbreviations   Note
============  ========  ==============  =====
None          N/A                       Dimension-less variable
Volume        byte                   B
Time          seconds                s
============  ========  ==============  =====

Here are the meter types by components that are currently implemented:

Compute (Nova)
==============

========================  ==========  ========  ========  ============  =======================================================
Name                      Type        Unit      Resource  Origin        Note
========================  ==========  ========  ========  ============  =======================================================
instance                  Gauge       instance  inst ID   both          Duration of instance
instance:<type>           Gauge       instance  inst ID   both          Duration of instance <type> (openstack types)
memory                    Gauge             MB  inst ID   notification  Volume of RAM in MB
cpu                       Cumulative        ns  inst ID   pollster      CPU time used
cpu_util                  Gauge              %  inst ID   pollster      CPU utilisation
vcpus                     Gauge           vcpu  inst ID   notification  Number of VCPUs
disk.read.request         Cumulative   request  inst ID   pollster      Number of read requests
disk.write.request        Cumulative   request  inst ID   pollster      Number of write requests
disk.read.bytes           Cumulative         B  inst ID   pollster      Volume of read in B
disk.write.bytes          Cumulative         B  inst ID   pollster      Volume of write in B
disk.root.size            Gauge             GB  inst ID   notification  Size of root disk in GB
disk.ephemeral.size       Gauge             GB  inst ID   notification  Size of ephemeral disk in GB
network.incoming.bytes    Cumulative         B  iface ID  pollster      number of incoming bytes on the network
network.outgoing.bytes    Cumulative         B  iface ID  pollster      number of outgoing bytes on the network
network.incoming.packets  Cumulative   packets  iface ID  pollster      number of incoming packets
network.outgoing.packets  Cumulative   packets  iface ID  pollster      number of outgoing packets

========================  ==========  ========  ========  ============  =======================================================

At present, most of the Nova meters will only work with libvirt front-end
hypervisors while test coverage was mostly done based on KVM. Contributors
are welcome to implement other virtualization backends’ meters or complete
the existing ones.

Network (Quantum)
=================

========================  ==========  ========  ========  ============  ======================================================
Name                      Type        Unit      Resource  Origin        Note
========================  ==========  ========  ========  ============  ======================================================
network                   Gauge       network   netw ID   notification  Duration of network
network.create            Delta       network   netw ID   notification  Creation requests for this network
network.update            Delta       network   netw ID   notification  Update requests for this network
subnet                    Gauge       subnet    subnt ID  notification  Duration of subnet
subnet.create             Delta       subnet    subnt ID  notification  Creation requests for this subnet
subnet.update             Delta       subnet    subnt ID  notification  Update requests for this subnet
port                      Gauge       port      port ID   notification  Duration of port
port.create               Delta       port      port ID   notification  Creation requests for this port
port.update               Delta       port      port ID   notification  Update requests for this port
router                    Gauge       router    rtr ID    notification  Duration of router
router.create             Delta       router    rtr ID    notification  Creation requests for this router
router.update             Delta       router    rtr ID    notification  Update requests for this router
ip.floating               Gauge       ip        ip ID     both          Duration of floating ip
ip.floating.create        Delta       ip        ip ID     notification  Creation requests for this floating ip
ip.floating.update        Delta       ip        ip ID     notification  Update requests for this floating ip
========================  ==========  ========  ========  ============  ======================================================

Image (Glance)
==============

========================  ==========  =======  ========  ============  =======================================================
Name                      Type        Unit     Resource  Origin        Note
========================  ==========  =======  ========  ============  =======================================================
image                     Gauge         image  image ID  both          Image polling -> it (still) exists
image.size                Gauge             B  image ID  both          Uploaded image size
image.update              Delta         image  image ID  notification  Number of update on the image
image.upload              Delta         image  image ID  notification  Number of upload of the image
image.delete              Delta         image  image ID  notification  Number of delete on the image
image.download            Delta             B  image ID  notification  Image is downloaded
image.serve               Delta             B  image ID  notification  Image is served out
========================  ==========  =======  ========  ============  =======================================================

Volume (Cinder)
===============

========================  ==========  =======  ========  ============  =======================================================
Name                      Type        Unit     Resource  Origin        Note
========================  ==========  =======  ========  ============  =======================================================
volume                    Gauge        volume  vol ID    notification  Duration of volune
volume.size               Gauge            GB  vol ID    notification  Size of volume
========================  ==========  =======  ========  ============  =======================================================

Object Storage (Swift)
======================

==============================  ==========  ==========  ========  ============  ==============================================
Name                            Type        Volume      Resource  Origin        Note
==============================  ==========  ==========  ========  ============  ==============================================
storage.objects                 Gauge          objects  store ID  pollster      Number of objects
storage.objects.size            Gauge                B  store ID  pollster      Total size of stored objects
storage.objects.containers      Gauge       containers  store ID  pollster      Number of containers
storage.objects.incoming.bytes  Delta                B  store ID  notification  Number of incoming bytes
storage.objects.outgoing.bytes  Delta                B  store ID  notification  Number of outgoing bytes
storage.api.request             Delta          request  store ID  notification  Number of API requests against swift
==============================  ==========  ==========  ========  ============  ==============================================

Energy (Kwapi)
==============

==========================  ==========  ==========  ========  ========= ==============================================
Name                        Type        Volume      Resource  Origin    Note
==========================  ==========  ==========  ========  ========= ==============================================
energy                      Cumulative         kWh  probe ID  pollster  Amount of energy
power                       Gauge                W  probe ID  pollster  Power consumption
==========================  ==========  ==========  ========  ========= ==============================================

Dynamically retrieving the Meters via ceilometer client
=======================================================

To retrieve the available meters that can be queried given the actual
resource instances available, use the ``meter-list`` command:

::

    $ ceilometer meter-list -s openstack
    +------------+-------+--------------------------------------+---------+----------------------------------+
    | Name       | Type  | Resource ID                          | User ID | Project ID                       |
    +------------+-------+--------------------------------------+---------+----------------------------------+
    | image      | gauge | 09e84d97-8712-4dd2-bcce-45970b2430f7 |         | 57cf6d93688e4d39bf2fe3d3c03eb326 |


Naming convention
=================
If you plan on adding meters, please follow the convention bellow:

1. Always use '.' as separator and go from least to most discriminent word.
   For example, do not use ephemeral_disk_size but disk.ephemeral.size

2. When a part of the name is a variable, it should always be at the end and start with a ':'.
   For example do not use <type>.image but image:<type>, where type is your variable name.

3. If you have any hesitation, come and ask in #openstack-metering
