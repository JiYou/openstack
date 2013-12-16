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

BASE_SQL_CONN=mysql://$MYSQL_NOVA_USER:$MYSQL_NOVA_PASSWORD@$MYSQL_HOST

unset OS_USERNAME
unset OS_AUTH_KEY
unset OS_AUTH_TENANT
unset OS_STRATEGY
unset OS_AUTH_STRATEGY
unset OS_AUTH_URL
unset SERVICE_TOKEN
unset SERVICE_ENDPOINT
unset http_proxy
unset https_proxy
unset ftp_proxy

KEYSTONE_AUTH_HOST=$KEYSTONE_HOST
KEYSTONE_AUTH_PORT=35357
KEYSTONE_AUTH_PROTOCOL=http
KEYSTONE_SERVICE_HOST=$KEYSTONE_HOST
KEYSTONE_SERVICE_PORT=5000
KEYSTONE_SERVICE_PROTOCOL=http
SERVICE_ENDPOINT=http://$KEYSTONE_HOST:35357/v2.0

#---------------------------------------------------
# Clear Front installation
#---------------------------------------------------

DEBIAN_FRONTEND=noninteractive \
apt-get --option \
"Dpkg::Options::=--force-confold" --assume-yes \
install -y --force-yes mysql-client
nkill nova-api
nkill nova-cer
nkill nova-conductor
nkill nova-scheduler
nkill nova-consoleauth

[[ -d $DEST/nova ]] && cp -rf $TOPDIR/openstacksource/nova/etc/nova/* $DEST/nova/etc/nova/
mysql_cmd "DROP DATABASE IF EXISTS nova;"

############################################################
#
# Install some basic used debs.
#
############################################################

apt-get install -y --force-yes  \
build-essential curl dnsmasq-base dnsmasq-base dnsmasq-utils \
ebtables expect gawk git iptables iputils-arping kpartx libxml2-dev \
libxslt-dev memcached mysql-client openssh-server openssl parted \
python-boto python-carrot python-cheetah python-dev python-docutils \
python-eventlet python-eventlet python-feedparser python-gflags \
python-greenlet python-greenlet python-iso8601 python-iso8601 \
python-kombu python-libxml2 python-lockfile python-lxml python-lxml \
python-m2crypto python-migrate python-migrate python-mox python-mysqldb \
python-mysqldb python-netaddr python-netifaces python-netifaces-dbg \
python-pam python-passlib python-pip python-prettytable python-qpid \
python-requests python-routes python-routes python-setuptools \
python-sqlalchemy python-sqlalchemy python-stevedore python-suds \
python-tempita python-xattr socat sqlite3 sudo unzip vlan websockify

service ssh restart

#---------------------------------------------------
# Copy source code to DEST Dir
#---------------------------------------------------

[[ ! -d $DEST ]] && mkdir -p $DEST
install_keystone
install_nova

#---------------------------------------------------
# Create User in Keystone
#---------------------------------------------------

export SERVICE_TOKEN=$ADMIN_TOKEN
export SERVICE_ENDPOINT=http://$KEYSTONE_HOST:35357/v2.0

get_tenant SERVICE_TENANT service
get_role ADMIN_ROLE admin


if [[ `keystone user-list | grep nova | wc -l` -eq 0 ]]; then
NOVA_USER=$(get_id keystone user-create \
    --name=nova \
    --pass="$KEYSTONE_NOVA_SERVICE_PASSWORD" \
    --tenant_id $SERVICE_TENANT \
    --email=nova@example.com)
keystone user-role-add \
    --tenant_id $SERVICE_TENANT \
    --user_id $NOVA_USER \
    --role_id $ADMIN_ROLE
NOVA_SERVICE=$(get_id keystone service-create \
    --name=nova \
    --type=compute \
    --description="Nova Compute Service")
keystone endpoint-create \
    --region RegionOne \
    --service_id $NOVA_SERVICE \
    --publicurl "http://$NOVA_HOST:\$(compute_port)s/v2/\$(tenant_id)s" \
    --adminurl "http://$NOVA_HOST:\$(compute_port)s/v2/\$(tenant_id)s" \
    --internalurl "http://$NOVA_HOST:\$(compute_port)s/v2/\$(tenant_id)s"
RESELLER_ROLE=$(get_id keystone role-create --name=ResellerAdmin)
keystone user-role-add \
    --tenant_id $SERVICE_TENANT \
    --user_id $NOVA_USER \
    --role_id $RESELLER_ROLE

EC2_SERVICE=$(get_id keystone service-create \
    --name=ec2 \
    --type=ec2 \
    --description="EC2 Compatibility Layer")
keystone endpoint-create \
    --region RegionOne \
    --service_id $EC2_SERVICE \
    --publicurl "http://$NOVA_HOST:8773/services/Cloud" \
    --adminurl "http://$NOVA_HOST:8773/services/Admin" \
    --internalurl "http://$NOVA_HOST:8773/services/Cloud"
fi

unset SERVICE_TOKEN
unset SERVICE_ENDPOINT

#---------------------------------------------------
# Create glance user in Mysql
#---------------------------------------------------

# create user
cnt=`mysql_cmd "select * from mysql.user;" | grep $MYSQL_NOVA_USER | wc -l`
if [[ $cnt -eq 0 ]]; then
    mysql_cmd "create user '$MYSQL_NOVA_USER'@'%' identified by '$MYSQL_NOVA_PASSWORD';"
    mysql_cmd "flush privileges;"
fi

# create database
cnt=`mysql_cmd "show databases;" | grep nova | wc -l`

if [[ $cnt -eq 0 ]]; then
    mysql_cmd "create database nova CHARACTER SET latin1;"
    mysql_cmd "grant all privileges on nova.* to '$MYSQL_NOVA_USER'@'%' identified by '$MYSQL_NOVA_PASSWORD';"
    mysql_cmd "GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' identified by '$MYSQL_ROOT_PASSWORD'; FLUSH PRIVILEGES;"
    mysql_cmd "GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' identified by '$MYSQL_ROOT_PASSWORD'  WITH GRANT OPTION; FLUSH PRIVILEGES;"
    mysql_cmd "flush privileges;"
fi

#################################################
#
# Change configuration file.
#
#################################################

[[ -d /etc/nova ]] && rm -rf /etc/nova/*
mkdir -p /etc/nova
cp -rf $TOPDIR/openstacksource/nova/etc/nova/* /etc/nova/


file=/etc/nova/nova.conf
cp -rf $TOPDIR/templates/nova.conf $file
HOST_IP=$NOVA_HOST

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

file=/etc/nova/api-paste.ini
sed -i "s,auth_host = 127.0.0.1,auth_host = $KEYSTONE_HOST,g" $file
sed -i "s,%SERVICE_TENANT_NAME%,$SERVICE_TENANT_NAME,g" $file
sed -i "s,%SERVICE_USER%,nova,g" $file
sed -i "s,%SERVICE_PASSWORD%,$KEYSTONE_NOVA_SERVICE_PASSWORD,g" $file

file=/etc/nova/rootwrap.conf
sed -i "s,filters_path=.*,filters_path=/etc/nova/rootwrap.d,g" $file

############################################################
#
# SYNC the DataBase.
#
############################################################

nova-manage db version
nova-manage db sync


############################################################
#
# Create a script to kill all the services with the name.
#
############################################################


cat <<"EOF" > /root/nova-api.sh
#!/bin/bash
cd /opt/stack/nova
mkdir -p /var/log/nova
mkdir -p /opt/stack/data/nova
mkdir -p /opt/stack/data/nova/instances

nkill nova-api
nkill nova-cert
nkill nova-conductor
nkill nova-scheduler
nkill nova-consoleauth

for n in nova-api nova-cert nova-conductor nova-scheduler nova-consoleauth; do
    nohup python ./bin/$n \
        --config-file=/etc/nova/nova.conf \
        >/var/log/nova/$n.log 2>&1 &
done
EOF

cp -rf $TOPDIR/tools/novarc /root/
sed -i "s,%KEYSTONE_NOVA_SERVICE_PASSWORD%,$KEYSTONE_NOVA_SERVICE_PASSWORD,g" /root/novarc
sed -i "s,%KEYSTONE_HOST%,$KEYSTONE_HOST,g" /root/novarc

chmod +x /root/nova-api.sh
/root/nova-api.sh
rm -rf /tmp/pip*
rm -rf /tmp/tmp*

set +o xtrace
