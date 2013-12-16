#!/bin/bash
TOPDIR=$(cd $(dirname "$0") && pwd)

version=`lsb_release -c -s`
RAND="fa-92-$(dd if=/dev/urandom count=1 2>/dev/null | md5sum | sed 's/^\(..\)\(..\)\(..\)\(..\).*$/\1-\2-\3-\4/')";
mv /etc/apt/sources.list /etc/apt/sources.list_bak${RAND}

[[ ! -d /media/sda7 ]] && cp -rf $TOPDIR/../sda7 /media/
echo "deb file:///media/sda7/Backup/Ubuntu/ $version main" > /etc/apt/sources.list
