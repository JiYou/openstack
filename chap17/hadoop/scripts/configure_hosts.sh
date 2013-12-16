#!/bin/bash

TOP_DIR=$(cd $(dirname "$0") && pwd)
TOP_DIR=$TOP_DIR/..

source $TOP_DIR/localrc
source $TOP_DIR/scripts/function

ALL_HOSTS=`get_all_hosts "$MASTER $SLAVES $AGENTS $COLLECTORS"`

for HOST in $ALL_HOSTS; do
    sed -i "/$HOST/d" /etc/hosts
    grep $HOST $TOP_DIR/hosts | grep -v '#' >> /etc/hosts
done
