#!/bin/bash

set -e
set -o xtrace

#---------------------------------------------
# We should create link file first.
#---------------------------------------------

function find_and_run() {
    old_dir=`pwd`
    fl=$1
    num=`find . -name "$fl" | wc -l`
    while [ $num -eq 0 ]; do
        cd ..
        num=`find . -name "$fl" | wc -l`
        if [[ $num -gt 0 ]]; then
            for x in `find . -name "$fl"`; do
                ./$x
            done
        fi
    done
    cd $old_dir
}

find_and_run create_link.sh

#---------------------------------------------------
# Set up global ENV
#---------------------------------------------------


TOPDIR=$(cd $(dirname "$0") && pwd)
TEMP=`mktemp`;
rm -rfv $TEMP >/dev/null;
mkdir -p $TEMP;
source $TOPDIR/localrc
source $TOPDIR/tools/function
DEST=/opt/stack/

###########################################################
#
#  Your Configurations.
#
###########################################################

HOST_IP=`nic_ip $NOVA_COMPUTE_NIC_CARD`

DEBIAN_FRONTEND=noninteractive \
apt-get --option \
"Dpkg::Options::=--force-confold" --assume-yes \
install -y --force-yes mysql-client

nkill nova-compute
nkill nova-novncproxy
nkill nova-xvpvncproxy

############################################################
#
# Install some basic used debs.
#
############################################################


apt-get install -y --force-yes \
alembic build-essential cdbs curl debhelper dh-buildinfo dkms \
dnsmasq-base dnsmasq-utils ebtables expect fakeroot gawk git \
gnutls-bin iptables iputils-arping iputils-ping iscsitarget \
iscsitarget-dkms kvm libapparmor-dev libavahi-client-dev libcap-ng-dev \
libdevmapper-dev libgnutls-dev libncurses5-dev libnl-3-dev libnl-route-3-200 \
libnl-route-3-dev libnuma1 libnuma-dbg libnuma-dev libparted0-dev \
libpcap0.8-dev libpciaccess-dev libreadline-dev libudev-dev \
libvirt-bin libxen-dev libxml2 libxml2-dev libxml2-utils libxslt1.1 \
libxslt1-dev libxslt-dev libyajl-dev lvm2 make memcached mongodb \
mongodb-clients mongodb-dev mongodb-server mysql-client numactl \
open-iscsi openssh-server openssl openvswitch-datapath-dkms \
openvswitch-switch policykit-1 python-all-dev python-boto python-cheetah \
python-dev python-docutils python-eventlet python-gflags python-greenlet \
python-iso8601 python-kombu python-libvirt python-libxml2 python-lxml \
python-migrate python-mox python-mysqldb python-netaddr python-pam \
python-pip python-prettytable python-pymongo python-pyudev python-qpid \
python-requests python-routes python-setuptools python-sqlalchemy \
python-stevedore python-suds python-xattr radvd socat sqlite3

[[ -e /usr/include/libxml ]] && rm -rf /usr/include/libxml
ln -s /usr/include/libxml2/libxml /usr/include/libxml
[[ -e /usr/include/netlink ]] && rm -rf /usr/include/netlink
ln -s /usr/include/libnl3/netlink /usr/include/netlink

service ssh restart


#---------------------------------------------------
# Copy source code to DEST Dir
#---------------------------------------------------

[[ ! -d $DEST ]] && mkdir -p $DEST
install_keystone
install_nova

#---------------------------------------------------
# Configuration file
#---------------------------------------------------
[[ -d /etc/nova ]] && rm -rf /etc/nova/*
mkdir -p /etc/nova
cp -rf $TOPDIR/openstacksource/nova/etc/nova/* /etc/nova/

file=/etc/nova/nova.conf
cp -rf $TOPDIR/templates/nova.conf $file

sed -i "s,%HOST_IP%,$HOST_IP,g" $file
sed -i "s,%GLANCE_HOST%,$GLANCE_HOST,g" $file
sed -i "s,%MYSQL_NOVA_USER%,$MYSQL_NOVA_USER,g" $file
sed -i "s,%MYSQL_NOVA_PASSWORD%,$MYSQL_NOVA_PASSWORD,g" $file
sed -i "s,%MYSQL_HOST%,$MYSQL_HOST,g" $file
sed -i "s,%NOVA_HOST%,$NOVA_HOST,g" $file
sed -i "s,%KEYSTONE_QUANTUM_SERVICE_PASSWORD%,$KEYSTONE_QUANTUM_SERVICE_PASSWORD,g" $file
sed -i "s,%KEYSTONE_HOST%,$KEYSTONE_HOST,g" $file
sed -i "s,%QUANTUM_HOST%,$QUANTUM_HOST,g" $file
sed -i "s,%DASHBOARD_HOST%,$DASHBOARD_HOST,g" $file
sed -i "s,%RABBITMQ_HOST%,$RABBITMQ_HOST,g" $file
sed -i "s,%RABBITMQ_PASSWORD%,$RABBITMQ_PASSWORD,g" $file
sed -i "s,%LIBVIRT_TYPE%,$LIBVIRT_TYPE,g" $file
sed -i "s,VNCSERVER_PROXYCLIENT_ADDRESS=.*,VNCSERVER_PROXYCLIENT_ADDRESS=$HOST_IP,g" $file

file=/etc/nova/api-paste.ini
sed -i "s,auth_host = 127.0.0.1,auth_host = $KEYSTONE_HOST,g" $file
sed -i "s,%SERVICE_TENANT_NAME%,$SERVICE_TENANT_NAME,g" $file
sed -i "s,%SERVICE_USER%,nova,g" $file
sed -i "s,%SERVICE_PASSWORD%,$KEYSTONE_NOVA_SERVICE_PASSWORD,g" $file

file=/etc/nova/rootwrap.conf
sed -i "s,filters_path=.*,filters_path=/etc/nova/rootwrap.d,g" $file

mkdir -p $DEST/data/nova/instances/

#---------------------------------------------------
# Ceilometer Service
#---------------------------------------------------

cat <<"EOF" > /root/nova-compute.sh
#!/bin/bash

nkill nova-compute
nkill nova-novncproxy
nkill nova-xvpvncproxy

mkdir -p /var/log/nova
cd /opt/stack/noVNC/

python ./utils/nova-novncproxy --config-file /etc/nova/nova.conf --web . >/var/log/nova/nova-novncproxy.log 2>&1 &

python /opt/stack/nova/bin/nova-xvpvncproxy --config-file /etc/nova/nova.conf >/var/log/nova/nova-xvpvncproxy.log 2>&1 &

nohup python /opt/stack/nova/bin/nova-compute --config-file=/etc/nova/nova.conf >/var/log/nova/nova-compute.log 2>&1 &

EOF

chmod +x /root/nova-compute.sh
/root/nova-compute.sh
rm -rf /tmp/pip*
rm -rf /tmp/tmp*

cp -rf $TOPDIR/tools/novarc /root/
sed -i "s,%KEYSTONE_NOVA_SERVICE_PASSWORD%,$KEYSTONE_NOVA_SERVICE_PASSWORD,g" /root/novarc
sed -i "s,%KEYSTONE_HOST%,$KEYSTONE_HOST,g" /root/novarc

set +o xtrace
