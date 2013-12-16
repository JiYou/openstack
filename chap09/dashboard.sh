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

BASE_SQL_CONN=mysql://$MYSQL_DASHBOARD_USER:$MYSQL_DASHBOARD_PASSWORD@$MYSQL_HOST

unset OS_USERNAME
unset OS_AUTH_KEY
unset OS_AUTH_TENANT
unset OS_STRATEGY
unset OS_AUTH_STRATEGY
unset OS_AUTH_URL
unset SERVICE_TOKEN
unset SERVICE_ENDPOINT
unset https_proxy
unset http_proxy
unset ftp_proxy

KEYSTONE_AUTH_HOST=$KEYSTONE_HOST
KEYSTONE_AUTH_PORT=35357
KEYSTONE_AUTH_PROTOCOL=http
KEYSTONE_SERVICE_HOST=$KEYSTONE_HOST
KEYSTONE_SERVICE_PORT=5000
KEYSTONE_SERVICE_PROTOCOL=http
SERVICE_ENDPOINT=http://$KEYSTONE_HOST:35357/v2.0


###########################################################
#
#  Your Configurations.
#
###########################################################

DEBIAN_FRONTEND=noninteractive \
apt-get --option \
"Dpkg::Options::=--force-confold" --assume-yes \
install -y --force-yes mysql-client

mysql_cmd "DROP DATABASE IF EXISTS dashboard;"


############################################################
#
# Install some basic used debs.
#
############################################################

apt-get install -y --force-yes openssh-server build-essential git \
python-dev python-setuptools python-pip \
libxml2-dev libxslt-dev tgt lvm2 python-pam python-lxml \
python-iso8601 python-sqlalchemy python-migrate \
unzip python-mysqldb mysql-client memcached openssl expect \
iputils-arping python-xattr \
python-lxml kvm gawk iptables ebtables sqlite3 sudo kvm \
vlan curl socat python-mox  \
python-migrate python-gflags python-greenlet python-libxml2 \
iscsitarget iscsitarget-dkms open-iscsi build-essential libxml2 libxml2-dev \
libxslt1.1 libxslt1-dev vlan gnutls-bin \
libgnutls-dev cdbs debhelper libncurses5-dev \
libreadline-dev libavahi-client-dev libparted0-dev \
libdevmapper-dev libudev-dev libpciaccess-dev \
libcap-ng-dev libnl-3-dev libapparmor-dev \
python-all-dev libxen-dev policykit-1 libyajl-dev \
libpcap0.8-dev libnuma-dev radvd libxml2-utils \
libnl-route-3-200 libnl-route-3-dev libnuma1 numactl \
libnuma-dbg libnuma-dev dh-buildinfo expect \
make fakeroot dkms openvswitch-switch openvswitch-datapath-dkms \
ebtables iptables iputils-ping iputils-arping sudo python-boto \
python-iso8601 python-routes python-suds python-netaddr \
 python-greenlet python-kombu python-eventlet \
python-sqlalchemy python-mysqldb python-pyudev python-qpid dnsmasq-base \
dnsmasq-utils vlan apache2 libapache2-mod-wsgi nodejs python-docutils \
python-requests node-less nodejs-legacy

[[ -e /usr/include/libxml ]] && rm -rf /usr/include/libxml
ln -s /usr/include/libxml2/libxml /usr/include/libxml
[[ -e /usr/include/netlink ]] && rm -rf /usr/include/netlink
ln -s /usr/include/libnl3/netlink /usr/include/netlink

service ssh restart


#---------------------------------------------------
# Solve Dep
#---------------------------------------------------

[[ ! -d $DEST ]] && mkdir -p $DEST
install_dashboard
install_nova

#---------------------------------------------------
# Configuration
#---------------------------------------------------
# create user
cnt=`mysql_cmd "select * from mysql.user;" | grep $MYSQL_DASHBOARD_USER | wc -l`
if [[ $cnt -eq 0 ]]; then
    mysql_cmd "create user '$MYSQL_DASHBOARD_USER'@'%' identified by '$MYSQL_DASHBOARD_PASSWORD';"
    mysql_cmd "flush privileges;"
fi

# create database
cnt=`mysql_cmd "show databases;" | grep dashboard | wc -l`
if [[ $cnt -eq 0 ]]; then
    mysql_cmd "create database dashboard CHARACTER SET utf8;"
    mysql_cmd "grant all privileges on dashboard.* to '$MYSQL_DASHBOARD_USER'@'%' identified by '$MYSQL_DASHBOARD_PASSWORD';"
    mysql_cmd "GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' identified by '$MYSQL_ROOT_PASSWORD'; FLUSH PRIVILEGES;"
    mysql_cmd "GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' identified by '$MYSQL_ROOT_PASSWORD'  WITH GRANT OPTION; FLUSH PRIVILEGES;"
    mysql_cmd "flush privileges;"
fi



#---------------------------------------------------
# Change local setting configuration.
#---------------------------------------------------

HORIZON_DIR=$DEST/horizon
local_settings=$HORIZON_DIR/openstack_dashboard/local/local_settings.py
cp $TOPDIR/tools/horizon_settings.py $local_settings
sed -i "s,%MYSQL_DASHBOARD_USER%,$MYSQL_DASHBOARD_USER,g" $local_settings
sed -i "s,%MYSQL_DASHBOARD_PASSWORD%,$MYSQL_DASHBOARD_PASSWORD,g" $local_settings
sed -i "s,%MYSQL_HOST%,$MYSQL_HOST,g" $local_settings
sed -i "s,%KEYSTONE_HOST%,$KEYSTONE_HOST,g" $local_settings

rm -f $HORIZON_DIR/openstack_dashboard/local/dashboard_openstack.sqlite3

cd $HORIZON_DIR
python manage.py syncdb --noinput
cd $TOPDIR
mkdir -p $HORIZON_DIR/.blackhole


#---------------------------------------------------
# Configure for Apache2
#---------------------------------------------------

APACHE_NAME=apache2
APACHE_CONF=sites-available/horizon
rm -f /etc/apache2/sites-enabled/000-default
[[ -e /etc/apache2/sites-enabled/horizon ]] && rm -rf /etc/apache2/sites-enabled/horizon
touch /etc/$APACHE_NAME/$APACHE_CONF
a2ensite horizon


#---------------------------------------------------
# Add user stack:stack
#---------------------------------------------------




cp -rf $TOPDIR/tools/apache-horizon.template /etc/$APACHE_NAME/$APACHE_CONF

if [[ $EUID -eq 0 ]]; then
    if ! getent group stack >/dev/null; then
        groupadd stack
    fi
    if ! getent passwd stack >/dev/null; then
        useradd -g stack -s /bin/bash -d $DEST -m stack
    fi

    grep -q "^#includedir.*/etc/sudoers.d" /etc/sudoers ||
        echo "#includedir /etc/sudoers.d" >> /etc/sudoers

fi


#---------------------------------------------------
# Change configure for apache2
#---------------------------------------------------


cp -rf $TOPDIR/tools/secret_key.py  $DEST/horizon/horizon/utils/secret_key.py
file=/etc/$APACHE_NAME/$APACHE_CONF
sed -i "s,%USER%,stack,g" $file
sed -i "s,%GROUP%,stack,g" $file
sed -i "s,%HORIZON_DIR%,$HORIZON_DIR,g" $file
sed -i "s,%APACHE_NAME%,$APACHE_NAME,g" $file
sed -i "s,%DEST%,$DEST,g" $file

chown -R stack:stack /opt/stack/horizon


#---------------------------------------------------
# Start VNC Server
#---------------------------------------------------

file=/etc/nova/nova.conf
scp -pr $NOVA_HOST:/etc/nova /etc/
sed -i "s,vncserver_proxyclient_address=.*,vncserver_proxyclient_address=$DASHBOARD_HOST,g" $file
sed -i "s,my_ip=.*,my_ip=$DASHBOARD_HOST,g" $file

cat <<"EOF" > /root/dashboard.sh

mkdir -p /var/log/nova
nkill nova-novncproxy 
nkill nova-xvpvncproxy

cd /opt/stack/noVNC/
python ./utils/nova-novncproxy --config-file /etc/nova/nova.conf --web . >/var/log/nova/nova-novncproxy.log 2>&1 &

python /opt/stack/nova/bin/nova-xvpvncproxy --config-file /etc/nova/nova.conf >/var/log/nova/nova-xvpvncproxy.log 2>&1 &

service apache2 restart

EOF

chmod a+x /root/dashboard.sh
/root/dashboard.sh

rm -rf /tmp/pip*; rm -rf /tmp/tmp*

set +o xtrace
