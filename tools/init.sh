#!/bin/bash
set -e
set -o xtrace

TOP_DIR=$(cd $(dirname "$0") && pwd)
TEMP=`mktemp`; rm -rfv $TEMP >/dev/null; mkdir -p $TEMP;
DEST=/opt/stack
source ./function
#---------------------------------------------
# Check for apt.
#---------------------------------------------
DEBIAN_FRONTEND=noninteractive \
apt-get --option \
"Dpkg::Options::=--force-confold" --assume-yes \
install -y --force-yes openssh-server
#---------------------------------------------
# Kill process by Name
#---------------------------------------------

cp -rf ./nkill /usr/bin/
chmod +x /usr/bin/nkill

#---------------------------------------------
# Set up iptables.
#---------------------------------------------

setup_iptables

set +o xtrace
