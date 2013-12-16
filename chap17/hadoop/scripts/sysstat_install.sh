#!/bin/bash
TOP_DIR=$(cd $(dirname "$0") && pwd)
TOP_DIR=$TOP_DIR/..

#Check whether systat has been installed.
if [[ ! -e /usr/bin/sar ]]; then
    [[ ! -e $TOP_DIR/sysstat-9.0.6 ]] && tar zxvf $TOP_DIR/sysstat-9.0.6.tar.gz -C $TOP_DIR
    cd $TOP_DIR/sysstat-9.0.6
    ./configure
    make
    make install
fi
