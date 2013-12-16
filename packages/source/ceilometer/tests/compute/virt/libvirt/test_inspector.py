#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# Copyright © 2012 Red Hat, Inc
#
# Author: Eoghan Glynn <eglynn@redhat.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
"""Tests for libvirt inspector.
"""

from ceilometer.compute.virt.libvirt import inspector as libvirt_inspector
from ceilometer.tests import base as test_base


class TestLibvirtInspection(test_base.TestCase):

    def setUp(self):
        super(TestLibvirtInspection, self).setUp()
        self.instance_name = 'instance-00000001'
        self.inspector = libvirt_inspector.LibvirtInspector()
        self.inspector.connection = self.mox.CreateMockAnything()
        self.inspector.connection.getCapabilities()
        self.domain = self.mox.CreateMockAnything()
        self.inspector.connection.lookupByName(self.instance_name).AndReturn(
            self.domain)

    def test_inspect_cpus(self):
        self.domain.info().AndReturn((0L, 0L, 0L, 2L, 999999L))
        self.mox.ReplayAll()

        cpu_info = self.inspector.inspect_cpus(self.instance_name)
        self.assertEqual(cpu_info.number, 2L)
        self.assertEqual(cpu_info.time, 999999L)

    def test_inspect_vnics(self):
        dom_xml = """
             <domain type='kvm'>
                 <devices>
                    <interface type='bridge'>
                       <mac address='fa:16:3e:71:ec:6d'/>
                       <source bridge='br100'/>
                       <target dev='vnet0'/>
                       <filterref filter=
                        'nova-instance-00000001-fa163e71ec6d'>
                         <parameter name='DHCPSERVER' value='10.0.0.1'/>
                         <parameter name='IP' value='10.0.0.2'/>
                         <parameter name='PROJMASK' value='255.255.255.0'/>
                         <parameter name='PROJNET' value='10.0.0.0'/>
                       </filterref>
                       <alias name='net0'/>
                     </interface>
                     <interface type='bridge'>
                       <mac address='fa:16:3e:71:ec:6e'/>
                       <source bridge='br100'/>
                       <target dev='vnet1'/>
                       <filterref filter=
                        'nova-instance-00000001-fa163e71ec6e'>
                         <parameter name='DHCPSERVER' value='192.168.0.1'/>
                         <parameter name='IP' value='192.168.0.2'/>
                         <parameter name='PROJMASK' value='255.255.255.0'/>
                         <parameter name='PROJNET' value='192.168.0.0'/>
                       </filterref>
                       <alias name='net1'/>
                     </interface>
                     <interface type='bridge'>
                       <mac address='fa:16:3e:96:33:f0'/>
                       <source bridge='qbr420008b3-7c'/>
                       <target dev='vnet2'/>
                       <model type='virtio'/>
                       <address type='pci' domain='0x0000' bus='0x00' \
                       slot='0x03' function='0x0'/>
                    </interface>
                 </devices>
             </domain>
        """

        self.domain.XMLDesc(0).AndReturn(dom_xml)
        self.domain.interfaceStats('vnet0').AndReturn((1L, 2L, 0L, 0L,
                                                       3L, 4L, 0L, 0L))
        self.domain.interfaceStats('vnet1').AndReturn((5L, 6L, 0L, 0L,
                                                       7L, 8L, 0L, 0L))
        self.domain.interfaceStats('vnet2').AndReturn((9L, 10L, 0L, 0L,
                                                       11L, 12L, 0L, 0L))
        self.mox.ReplayAll()

        interfaces = list(self.inspector.inspect_vnics(self.instance_name))

        self.assertEquals(len(interfaces), 3)
        vnic0, info0 = interfaces[0]
        self.assertEqual(vnic0.name, 'vnet0')
        self.assertEqual(vnic0.mac, 'fa:16:3e:71:ec:6d')
        self.assertEqual(vnic0.fref,
                         'nova-instance-00000001-fa163e71ec6d')
        self.assertEqual(vnic0.parameters.get('projmask'), '255.255.255.0')
        self.assertEqual(vnic0.parameters.get('ip'), '10.0.0.2')
        self.assertEqual(vnic0.parameters.get('projnet'), '10.0.0.0')
        self.assertEqual(vnic0.parameters.get('dhcpserver'), '10.0.0.1')
        self.assertEqual(info0.rx_bytes, 1L)
        self.assertEqual(info0.rx_packets, 2L)
        self.assertEqual(info0.tx_bytes, 3L)
        self.assertEqual(info0.tx_packets, 4L)

        vnic1, info1 = interfaces[1]
        self.assertEqual(vnic1.name, 'vnet1')
        self.assertEqual(vnic1.mac, 'fa:16:3e:71:ec:6e')
        self.assertEqual(vnic1.fref,
                         'nova-instance-00000001-fa163e71ec6e')
        self.assertEqual(vnic1.parameters.get('projmask'), '255.255.255.0')
        self.assertEqual(vnic1.parameters.get('ip'), '192.168.0.2')
        self.assertEqual(vnic1.parameters.get('projnet'), '192.168.0.0')
        self.assertEqual(vnic1.parameters.get('dhcpserver'), '192.168.0.1')
        self.assertEqual(info1.rx_bytes, 5L)
        self.assertEqual(info1.rx_packets, 6L)
        self.assertEqual(info1.tx_bytes, 7L)
        self.assertEqual(info1.tx_packets, 8L)

        vnic2, info2 = interfaces[2]
        self.assertEqual(vnic2.name, 'vnet2')
        self.assertEqual(vnic2.mac, 'fa:16:3e:96:33:f0')
        self.assertEqual(vnic2.fref, None)
        self.assertEqual(vnic2.parameters, dict())
        self.assertEqual(info2.rx_bytes, 9L)
        self.assertEqual(info2.rx_packets, 10L)
        self.assertEqual(info2.tx_bytes, 11L)
        self.assertEqual(info2.tx_packets, 12L)

    def test_inspect_disks(self):
        dom_xml = """
             <domain type='kvm'>
                 <devices>
                     <disk type='file' device='disk'>
                         <driver name='qemu' type='qcow2' cache='none'/>
                         <source file='/path/instance-00000001/disk'/>
                         <target dev='vda' bus='virtio'/>
                         <alias name='virtio-disk0'/>
                         <address type='pci' domain='0x0000' bus='0x00'
                                  slot='0x04' function='0x0'/>
                     </disk>
                 </devices>
             </domain>
        """

        self.domain.XMLDesc(0).AndReturn(dom_xml)

        self.domain.blockStats('vda').AndReturn((1L, 2L, 3L, 4L, -1))
        self.mox.ReplayAll()

        disks = list(self.inspector.inspect_disks(self.instance_name))

        self.assertEquals(len(disks), 1)
        disk0, info0 = disks[0]
        self.assertEqual(disk0.device, 'vda')
        self.assertEqual(info0.read_requests, 1L)
        self.assertEqual(info0.read_bytes, 2L)
        self.assertEqual(info0.write_requests, 3L)
        self.assertEqual(info0.write_bytes, 4L)
