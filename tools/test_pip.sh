#!/bin/bash

#set -e
set -o xtrace


#---------------------------------------------------
# Prepare ENV
#---------------------------------------------------

TOPDIR=$(cd $(dirname "$0") && pwd)
TEMP=`mktemp`; rm -rfv $TEMP >/dev/null;mkdir -p $TEMP;

#---------------------------------------------------
# Install apt packages
#---------------------------------------------------

apt-get install -y --force-yes openssh-server build-essential git \
python-dev python-setuptools python-pip libxml2-dev \
libxslt1.1 libxslt1-dev libgnutls-dev libnl-3-dev \
python-virtualenv libnspr4-dev libnspr4 pkg-config \
apache2 unzip zip


[[ -e /usr/include/libxml ]] && rm -rf /usr/include/libxml
ln -s /usr/include/libxml2/libxml /usr/include/libxml
[[ -e /usr/include/netlink ]] && rm -rf /usr/include/netlink
ln -s /usr/include/libnl3/netlink /usr/include/netlink

#---------------------------------------------------
# Collect pip packages
#---------------------------------------------------

cd $TOPDIR/../openstacksource
mkdir -p /tmp/pip
cp -rf $TOPDIR/ch.sh /tmp/

for n in `ls`; do
    if [[ ! -d /tmp/pip/$n ]]; then
        cnt=`find ./$n -name "*txt" | grep require | grep -v build| wc -l`

        if [[ $cnt -gt 0 ]]; then
            mkdir -p /tmp/pip/$n
            file=`find ./$n -name "*txt" | grep require | grep -v build`
            cd $TEMP; virtualenv $n; source $n/bin/activate

            for f in $file; do
                pip install \
                    -r $TOPDIR/../openstacksource/$f \
                    -i http://testpip/pip
            done

            deactivate
        fi
    fi
    cd $TOPDIR/../openstacksource
done


set +o xtrace
