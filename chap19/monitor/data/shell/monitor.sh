#!/bin/bash

set -e
set -o xtrace

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

BASE_SQL_CONN=mysql://$MYSQL_MONITOR_USER:$MYSQL_MONITOR_PASSWORD@$MYSQL_HOST

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

nkill monitor
mysql_cmd "DROP DATABASE IF EXISTS monitor;"

############################################################
#
# Install some basic used debs.
#
############################################################



apt-get install -y --force-yes openssh-server build-essential git \
python-dev python-setuptools python-pip \
libxml2-dev libxslt-dev \
unzip python-mysqldb mysql-client memcached openssl expect \
python-lxml gawk iptables ebtables sqlite3 curl socat python-mox  \
python-migrate python-requests python-numpy

service ssh restart

#---------------------------------------------------
# Copy source code to DEST Dir
#---------------------------------------------------

[[ ! -e $DEST/monitor ]] && cp -rf $TOPDIR/../../monitor $DEST/
[[ ! -e $DEST/python-monitorclient-1.1 ]] && cp -rf $TOPDIR/../../python-monitorclient-1.1 $DEST/
install_package monitor ./tools/ pip-requires
install_package python-monitorclient-1.1 ./tools/ pip-requires
source_install monitor
source_install python-monitorclient-1.1


#---------------------------------------------------
# Create User in Keystone
#---------------------------------------------------

export SERVICE_TOKEN=$ADMIN_TOKEN
export SERVICE_ENDPOINT=http://$KEYSTONE_HOST:35357/v2.0

get_tenant SERVICE_TENANT service
get_role ADMIN_ROLE admin


if [[ `keystone user-list | grep monitor | wc -l` -eq 0 ]]; then
MONITOR_USER=$(get_id keystone user-create --name=monitor \
                                          --pass="$KEYSTONE_MONITOR_SERVICE_PASSWORD" \
                                          --tenant_id $SERVICE_TENANT \
                                          --email=monitor@example.com)
keystone user-role-add --tenant_id $SERVICE_TENANT \
                       --user_id $MONITOR_USER \
                       --role_id $ADMIN_ROLE
MONITOR_SERVICE=$(get_id keystone service-create \
    --name=monitor \
    --type=monitor \
    --description="Energy Service")
keystone endpoint-create \
    --region RegionOne \
    --service_id $MONITOR_SERVICE \
    --publicurl "http://$MONITOR_HOST:$MONITOR_PORT/v1/\$(tenant_id)s" \
    --adminurl "http://$MONITOR_HOST:$MONITOR_PORT/v1/\$(tenant_id)s" \
    --internalurl "http://$MONITOR_HOST:$MONITOR_PORT/v1/\$(tenant_id)s"
fi


unset SERVICE_TOKEN
unset SERVICE_ENDPOINT

#---------------------------------------------------
# Create glance user in Mysql
#---------------------------------------------------

# create user
cnt=`mysql_cmd "select * from mysql.user;" | grep $MYSQL_MONITOR_USER | wc -l`
if [[ $cnt -eq 0 ]]; then
    mysql_cmd "create user '$MYSQL_MONITOR_USER'@'%' identified by '$MYSQL_MONITOR_PASSWORD';"
    mysql_cmd "flush privileges;"
fi

# create database
cnt=`mysql_cmd "show databases;" | grep monitor | wc -l`
if [[ $cnt -eq 0 ]]; then
    mysql_cmd "create database monitor CHARACTER SET utf8;"
    mysql_cmd "grant all privileges on monitor.* to '$MYSQL_MONITOR_USER'@'%' identified by '$MYSQL_MONITOR_PASSWORD';"
    mysql_cmd "grant all privileges on monitor.* to 'root'@'%' identified by '$MYSQL_ROOT_PASSWORD';"
    mysql_cmd "flush privileges;"
fi

#################################################
#
# Change configuration file.
#
#################################################

[[ -d /etc/monitor ]] && rm -rf /etc/monitor/*
mkdir -p /etc/monitor
cp -rf $TOPDIR/../../monitor/etc/monitor/* /etc/monitor/

file=/etc/monitor/api-paste.ini
sed -i "s,%KEYSTONE_HOST%,$KEYSTONE_HOST,g" $file
sed -i "s,%SERVICE_TENANT_NAME%,$SERVICE_TENANT_NAME,g" $file
sed -i "s,%SERVICE_USER%,monitor,g" $file
sed -i "s,%SERVICE_PASSWORD%,$KEYSTONE_MONITOR_SERVICE_PASSWORD,g" $file

file=/etc/monitor/rootwrap.conf
sed -i "s,filters_path=.*,filters_path=/etc/monitor/rootwrap.d,g" $file

file=/etc/monitor/monitor.conf

mkdir -p /opt/stack/data/monitor
rm -rf /etc/monitor/monitor.conf*
cat <<"EOF">$file
[DEFAULT]
rabbit_password = %RABBITMQ_PASSWORD%
rabbit_host = %RABBITMQ_HOST%
state_path = /opt/stack/data/monitor
osapi_servicemanage_extension = monitor.api.openstack.servicemanage.contrib.standard_extensions
root_helper = sudo /usr/local/bin/monitor-rootwrap /etc/monitor/rootwrap.conf
api_paste_config = /etc/monitor/api-paste.ini
sql_connection = mysql://%MYSQL_MONITOR_USER%:%MYSQL_MONITOR_PASSWORD%@%MYSQL_HOST%/monitor?charset=utf8
verbose = True
auth_strategy = keystone
osapi_servicemanage_listen_port=%MONITOR_PORT%
EOF
sed -i "s,%RABBITMQ_PASSWORD%,$RABBITMQ_PASSWORD,g" $file
sed -i "s,%RABBITMQ_HOST%,$RABBITMQ_HOST,g" $file
sed -i "s,%MYSQL_MONITOR_USER%,$MYSQL_MONITOR_USER,g" $file
sed -i "s,%MYSQL_MONITOR_PASSWORD%,$MYSQL_MONITOR_PASSWORD,g" $file
sed -i "s,%MYSQL_HOST%,$MYSQL_HOST,g" $file
sed -i "s,%MONITOR_PORT%,$MONITOR_PORT,g" $file


###########################################################
#
# SYNC the DataBase.
#
############################################################


monitor-manage db sync

############################################################
#
# Create a script to kill all the services with the name.
#
############################################################

cp -rf $TOPDIR/../etc/init.d/* /etc/init.d/

service monitor-api restart


rm -rf /tmp/pip*
rm -rf /tmp/tmp*

set +o xtrace
