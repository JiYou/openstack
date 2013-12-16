#!/bin/bash

set -e
set -o xtrace

apt-get install -y --force-yes openssh-server build-essential git \
python-dev python-setuptools python-pip \
libxml2-dev libxslt-dev tgt lvm2 python-pam python-lxml \
python-iso8601 python-sqlalchemy python-migrate \
unzip python-mysqldb mysql-client memcached openssl expect \
iputils-arping python-xattr \
python-lxml kvm gawk iptables ebtables sqlite3 sudo kvm \
vlan curl socat python-mox  \
python-migrate python-gflags python-greenlet python-libxml2 \
iscsitarget iscsitarget-dkms open-iscsi build-essential libxml2 libxml2-dev \
libxslt1.1 libxslt1-dev vlan gnutls-bin \
libgnutls-dev cdbs debhelper libncurses5-dev \
libreadline-dev libavahi-client-dev libparted0-dev \
libdevmapper-dev libudev-dev libpciaccess-dev \
libcap-ng-dev libnl-3-dev libapparmor-dev \
python-all-dev libxen-dev policykit-1 libyajl-dev \
libpcap0.8-dev libnuma-dev radvd libxml2-utils \
libnl-route-3-200 libnl-route-3-dev libnuma1 numactl \
libnuma-dbg libnuma-dev dh-buildinfo expect \
make fakeroot dkms openvswitch-switch openvswitch-datapath-dkms \
ebtables iptables iputils-ping iputils-arping sudo python-boto \
python-iso8601 python-routes python-suds python-netaddr \
 python-greenlet python-kombu python-eventlet \
python-sqlalchemy python-mysqldb python-pyudev python-qpid dnsmasq-base \
dnsmasq-utils vlan python-qpid websockify \
python-stevedore python-docutils python-requests \
libvirt-bin python-prettytable python-cheetah \
python-requests alembic python-libvirt \
mongodb-clients mongodb mysql-client \
mongodb-server mongodb-dev python-pymongo

[[ -e /usr/include/libxml ]] && rm -rf /usr/include/libxml
ln -s /usr/include/libxml2/libxml /usr/include/libxml
[[ -e /usr/include/netlink ]] && rm -rf /usr/include/netlink
ln -s /usr/include/libnl3/netlink /usr/include/netlink

service ssh restart
set +o xtrace
