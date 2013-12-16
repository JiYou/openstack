#!/bin/bash

cp -rf win7.template win7
sed -i "s,%VM_NAME%,win7,g" win7

UUID=`uuidgen`
sed -i "s,%UUID%,$UUID,g" win7

machine=`qemu-system-x86_64 -M ? | grep default | awk '{print $1}'`
sed -i "s,pc-1.0,$machine,g" win7.spice

sed -i "s,%IMAGE_PATH%,/image/win7.raw,g" win7
sed -i "s,%ISO_PATH%,/iso/win7.iso,g" win7
sed -i "s,%ISO_PATH2%,/iso/virtio-win-0.1-52.iso,g" win7

MAC="fa:92:$(dd if=/dev/urandom count=1 2>/dev/null | md5sum | sed 's/^\(..\)\(..\)\(..\)\(..\).*$/\1:\2:\3:\4/')";
sed -i "s,%MAC%,$MAC,g" win7

virsh define win7
virsh start win7
