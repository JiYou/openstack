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
apache2 unzip


[[ -e /usr/include/libxml ]] && rm -rf /usr/include/libxml
ln -s /usr/include/libxml2/libxml /usr/include/libxml
[[ -e /usr/include/netlink ]] && rm -rf /usr/include/netlink
ln -s /usr/include/libnl3/netlink /usr/include/netlink

#---------------------------------------------------
# Collect pip packages
#---------------------------------------------------

cd $TOPDIR/../openstacksource
source ~/proxy
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
                    --download-cache=/tmp
                cd /tmp/; ./ch.sh
                mv /tmp/*z /tmp/pip/$n
                mv /tmp/*zip /tmp/pip/$n
            done

            deactivate
        fi
    fi
    cd $TOPDIR/../openstacksource
done

unset http_proxy
unset https_proxy
unset ftp_proxy

#---------------------------------------------------
# Delete some packages
#---------------------------------------------------

cd /tmp/pip/ceilometer
[[ `ls | grep master | wc -l` -gt 0 ]] && ls | grep master | xargs -i rm -rf {}
rm -rf swift-1.8.0.tar.gz

#---------------------------------------------------
# Create pip resources
#---------------------------------------------------

mkdir -p /var/www/pip
cd /tmp/pip

for n in `find . -name "*"`; do
    if [[ ! -d $n ]]; then
        package_name=${n##*/}
        dir_name=${package_name%-*}
        mkdir -p /var/www/pip/$dir_name
        cp -rf $n /var/www/pip/$dir_name

        olddir=`pwd`
        cd /var/www/pip/$dir_name
        TEMP_DIR=`mktemp`; rm -rfv $TEMP_DIR >/dev/null;mkdir -p $TEMP_DIR;
        cp -rf $package_name $TEMP_DIR/
        cd $TEMP_DIR

        if [[ `echo $package_name | grep zip| wc -l` -gt 0 ]]; then
            unzip $package_name
        else
            tar zxf $package_name
        fi

        rm -rf $package_name
        temp_dir_name=`ls`
        cd `ls`;
        if [[ `ls | grep "egg-info"| wc -l` -gt 0 ]]; then
            source /root/proxy
            python setup.py egg_info; python setup.py build
            unset http_proxy; unset https_proxy; unset ftp_proxy
        fi
        cd ..
        if [[ `echo $package_name | grep zip| wc -l` -gt 0 ]]; then
            zip -r $package_name $temp_dir_name
        else
            tar zcf $package_name $temp_dir_name
        fi

        rm -rf $temp_dir_name
        cp -rf $package_name /var/www/pip/$dir_name/

        cd $olddir
        rm -rf $TEMP_DIR
    fi
done
chmod -R a+r /var/www

set +o xtrace
