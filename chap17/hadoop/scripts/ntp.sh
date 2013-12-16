#!/bin/bash

##########################
#
# Load setting arguments
#
##########################

# localrc
TOP_DIR=$(cd $(dirname "$0") && pwd)
TOP_DIR=$TOP_DIR/..
source $TOP_DIR/localrc

# HOST IP of local host
HOST_IP=`ifconfig eth0 | grep "inet addr" | sed "s/:/ /g" | awk '{print $3}'`
# Network address of legal NTP clients
NETWORK_CIDR=${NETWORK_CIDR:-${HOST_IP%.*}.0}

#############################
#
# Configure ntp.conf
#
#############################

sed -i "/ kod /d" /etc/ntp.conf

content="restrict default nomodify noquery notrap"
if [[ `grep "$content" /etc/ntp.conf | wc -l` -eq 0 ]]; then
    echo "$content" >> /etc/ntp.conf
fi

if [[ `grep "$NETWORK_CIDR" /etc/ntp.conf | wc -l` -eq 0 ]]; then
    echo "restrict $NETWORK_CIDR mask 255.255.255.0 nomodify notrap" >> /etc/ntp.conf
fi

if [[ `grep "server 127.127.1.0" /etc/ntp.conf | wc -l` -eq 0 ]]; then
    echo "server 127.127.1.0" >> /etc/ntp.conf
    echo "fudge  127.127.1.0  stratum 8" >> /etc/ntp.conf
fi
