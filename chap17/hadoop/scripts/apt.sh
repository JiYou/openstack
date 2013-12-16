#!/bin/bash

# load proxy
TOP_DIR=$(cd $(dirname "$0") && pwd)
TOP_DIR=$TOP_DIR/..

source $TOP_DIR/localrc

#apt-get clean
#apt-get update

apt-get -f install -y --force-yes \
cpp-4.6 binutils libquadmath0 libmpc2 libmpfr4 libc-bin libc6 libc-dev-bin linux-libc-dev \
tcl8.5 cpp gcc-4.6 libc6-dev libcroco3 libgomp1 libunistring0 libgettextpo0 libc-bin libcap2 libopts25 \
expect gcc make gettext ntp unzip
