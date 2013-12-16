#!/bin/bash

set -e
set +o xtrace

#---------------------------------------------
# Set up Env.
#---------------------------------------------

TOPDIR=$(cd $(dirname "$0") && pwd)
source $TOPDIR/localrc
source $TOPDIR/tools/function
TEMP=`mktemp`; rm -rfv $TEMP >/dev/null; mkdir -p $TEMP;

#---------------------------------------------
# source localrc
#---------------------------------------------

set_password RABBITMQ_PASSWORD

apt-get install -y --force-yes rabbitmq-server
rabbitmqctl change_password guest $RABBITMQ_PASSWORD

set -o xtrace
