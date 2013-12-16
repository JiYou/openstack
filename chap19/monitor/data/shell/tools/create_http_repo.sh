#!/bin/bash

#set -e
set -o xtrace

#---------------------------------------------------
# Prepare ENV
#---------------------------------------------------

TOPDIR=$(cd $(dirname "$0") && pwd)
TEMP=`mktemp`; rm -rfv $TEMP >/dev/null;mkdir -p $TEMP;

mkdir -p /var/www/
[[ ! -e /var/www/debs ]] && cp -rf $TOPDIR/../packages/debs /var/www/
[[ ! -e /var/www/pip ]] && cp -rf $TOPDIR/../packages/pip /var/www/
echo "" > /etc/apt/apt.conf
echo "deb file:///var/www/ debs/" > /etc/apt/sources.list
apt-get clean all
apt-get update

#---------------------------------------------------
# Install apt packages
#---------------------------------------------------

apt-get install -y --force-yes openssh-server build-essential git \
python-dev python-setuptools python-pip libxml2-dev \
libxslt1.1 libxslt1-dev libgnutls-dev libnl-3-dev \
python-virtualenv libnspr4-dev libnspr4 pkg-config \
apache2 unzip


[[ -e /usr/include/libxml ]] && rm -rf /usr/include/libxml
ln -s /usr/include/libxml2/libxml /usr/include/libxml
[[ -e /usr/include/netlink ]] && rm -rf /usr/include/netlink
ln -s /usr/include/libnl3/netlink /usr/include/netlink

#---------------------------------------------------
# Collect pip packages
#---------------------------------------------------

set +o xtrace
