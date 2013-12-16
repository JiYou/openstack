#!/bin/bash
# This script mainly based on win7 & win7.raw file to create virtual machine.

cp -rf win7 win7.spice
sed -i "s,<name>win7</name>,<name>win7.spice</name>,g" win7.spice

UUID=`uuidgen`
sed -i "s,<uuid>.*</uuid>,<uuid>$UUID</uuid>,g" win7.spice

machine=`qemu-system-x86_64 -M ? | grep default | awk '{print $1}'`
sed -i "s,pc-1.0,$machine,g" win7.spice

begin_line=`grep -n "disk.*cdrom" win7 | awk '{print $1}' | head -1`
begin_line=${begin_line%:*}
end_line=`grep -n "/disk" win7 | awk '{print $1}' | tail -1`
end_line=${end_line%:*}
sed -i "${begin_line},${end_line}d" win7.spice

sed -i "s,type='raw',type='qcow2',g" win7.spice
sed -i "s,win7.raw,win7.spice.qcow2,g" win7.spice

virsh define win7.spice
virsh start win7.spice
