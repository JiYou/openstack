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
source $TOPDIR/localrc; cp -rf $TOPDIR/localrc /root/
source $TOPDIR/tools/function
DEST=/opt/stack/

###########################################################
#
#  Your Configurations.
#
###########################################################

BASE_SQL_CONN=mysql://$MYSQL_GLANCE_USER:$MYSQL_GLANCE_PASSWORD@$MYSQL_HOST

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
nkill glance
[[ -d $DEST/glance ]] && cp -rf $TOPDIR/openstacksource/glance/etc/* $DEST/glance/etc/
mysql_cmd "DROP DATABASE IF EXISTS glance;"



############################################################
#
# Install some basic used debs.
#
############################################################



apt-get install -y --force-yes openssh-server build-essential git \
python-dev python-setuptools python-pip \
unzip mysql-client memcached openssl expect \
libxml2-dev libxslt-dev unzip python-mysqldb mysql-client

[[ -e /usr/include/libxml ]] && rm -rf /usr/include/libxml
ln -s /usr/include/libxml2/libxml /usr/include/libxml

service ssh restart

#---------------------------------------------------
# Copy source code to DEST Dir
#---------------------------------------------------

[[ ! -d $DEST ]] && mkdir -p $DEST
install_glance

#---------------------------------------------------
# Create User in Keystone
#---------------------------------------------------

export SERVICE_TOKEN=$ADMIN_TOKEN
export SERVICE_ENDPOINT=http://$KEYSTONE_HOST:35357/v2.0

get_tenant SERVICE_TENANT service
get_role ADMIN_ROLE admin


if [[ `keystone user-list | grep glance | wc -l` -eq 0 ]]; then
GLANCE_USER=$(get_id keystone user-create \
    --name=glance \
    --pass="$KEYSTONE_GLANCE_SERVICE_PASSWORD" \
    --tenant_id $SERVICE_TENANT \
    --email=glance@example.com)

keystone user-role-add \
    --tenant_id $SERVICE_TENANT \
    --user_id $GLANCE_USER \
    --role_id $ADMIN_ROLE

GLANCE_SERVICE=$(get_id keystone service-create \
    --name=glance \
    --type=image \
    --description="Glance Image Service")

keystone endpoint-create \
    --region RegionOne \
    --service_id $GLANCE_SERVICE \
    --publicurl "http://$GLANCE_HOST:9292" \
    --adminurl "http://$GLANCE_HOST:9292" \
    --internalurl "http://$GLANCE_HOST:9292"

fi

unset SERVICE_TOKEN
unset SERVICE_ENDPOINT

#---------------------------------------------------
# Create glance user in Mysql
#---------------------------------------------------

# create user
cnt=`mysql_cmd "select * from mysql.user;" | grep $MYSQL_GLANCE_USER | wc -l`
if [[ $cnt -eq 0 ]]; then
    mysql_cmd "create user '$MYSQL_GLANCE_USER'@'%' identified by '$MYSQL_GLANCE_PASSWORD';"
    mysql_cmd "flush privileges;"
fi

# create database
cnt=`mysql_cmd "show databases;" | grep glance | wc -l`
if [[ $cnt -eq 0 ]]; then
    mysql_cmd "create database glance CHARACTER SET utf8;"
    mysql_cmd "grant all privileges on glance.* to '$MYSQL_GLANCE_USER'@'%' identified by '$MYSQL_GLANCE_PASSWORD';"
    mysql_cmd "GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' identified by '$MYSQL_ROOT_PASSWORD'; FLUSH PRIVILEGES;"
    mysql_cmd "GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' identified by '$MYSQL_ROOT_PASSWORD'  WITH GRANT OPTION; FLUSH PRIVILEGES;"
    mysql_cmd "flush privileges;"
fi


#################################################
#
# Change configuration file.
#
#################################################

[[ -d /etc/glance ]] && rm -rf /etc/glance/*
mkdir -p /etc/glance

file=/etc/glance/glance-api.conf
cp -rf $TOPDIR/openstacksource/glance/etc/* /etc/glance/
reg=/etc/glance/glance-registry.conf

# configure for log.
sed -i "s,debug = False,debug = True,g" $file
sed -i "s,debug = False,debug = True,g" $reg
sed -i "s,log_file = /var/log/glance/api.log,log_file = /var/log/glance/glance-api.log,g" $file
sed -i "s,log_file = /var/log/glance/registry.log,log_file = /var/log/glance/glance-registry.log", $reg
mkdir -p /var/log/glance

# for mysql
sed -i "s,sql_connection = sqlite:///glance.sqlite,sql_connection = $BASE_SQL_CONN/glance?charset=utf8,g" $file
sed -i "s,sql_connection = sqlite:///glance.sqlite,sql_connection = $BASE_SQL_CONN/glance?charset=utf8,g" $reg

# rabbitmq
sed -i "s,rabbit_host = localhost,rabbit_host = $RABBITMQ_HOST,g" $file
sed -i "s,notifier_strategy = noop,notifier_strategy = rabbit,g" $file
sed -i "s,rabbit_password = guest,rabbit_password = $RABBITMQ_PASSWORD,g" $file

# Storage dir
sed -i "s,filesystem_store_datadir = /var/lib/glance/images/,filesystem_store_datadir = /opt/stack/data/images/,g" $file
mkdir -p /opt/stack/data/images
sed -i "s,image_cache_dir = /var/lib/glance/image-cache/,image_cache_dir = /opt/stack/data/cache/,g" $file
mkdir -p /opt/stack/data/cache


# Glance use Swift
sed -i "s,default_store = file,default_store = swift,g" $file
sed -i "s,swift_store_auth_address = 127.0.0.1:5000/v2.0/,swift_store_auth_address = http://$KEYSTONE_HOST:5000/v2.0/,g" $file
sed -i "s,swift_store_user = jdoe:jdoe,swift_store_user = service:glance,g" $file
sed -i "s,swift_store_key = a86850deb2742ec3cb41518e26aa2d89,swift_store_key = $KEYSTONE_GLANCE_SERVICE_PASSWORD,g" $file


# Keystone dir
mkdir -p /opt/stack/data/cache/glance
add_line $file "keystone_authtoken" "signing_dir = /opt/stack/data/cache/glance"
add_line $file "keystone_authtoken" "auth_uri = http://$KEYSTONE_HOST:5000/"
sed -i "s,auth_host = 127.0.0.1,auth_host = $KEYSTONE_HOST,g" $file
sed -i "s,%SERVICE_TENANT_NAME%,$SERVICE_TENANT_NAME,g" $file
sed -i "s,%SERVICE_USER%,glance,g" $file
sed -i "s,%SERVICE_PASSWORD%,$KEYSTONE_GLANCE_SERVICE_PASSWORD,g" $file
add_line $file "paste_deploy" "flavor = keystone+cachemanagement"

sed -i "s,swift_store_create_container_on_put = False,swift_store_create_container_on_put = True,g" $file

add_line $reg "keystone_authtoken" "auth_uri = http://$KEYSTONE_HOST:5000/"
sed -i "s,auth_host = 127.0.0.1,auth_host = $KEYSTONE_HOST,g" $reg
sed -i "s,%SERVICE_TENANT_NAME%,$SERVICE_TENANT_NAME,g" $reg
sed -i "s,%SERVICE_USER%,glance,g" $reg
sed -i "s,%SERVICE_PASSWORD%,$KEYSTONE_GLANCE_SERVICE_PASSWORD,g" $reg
add_line $reg "paste_deploy" "flavor = keystone"


############################################################
#
# SYNC the DataBase.
#
############################################################

glance-manage db_sync #--config-file /etc/glance/glance-api.conf


############################################################
#
# Create a script to kill all the services with the name.
#
############################################################


cat <<"EOF" > /root/glance.sh
#!/bin/bash
nkill glance-api
nkill glance-registry
cd /opt/stack/glance
nohup python ./bin/glance-registry --config-file=/etc/glance/glance-registry.conf >/var/log/glance/glance-registry.log 2>&1 &

nohup python ./bin/glance-api      --config-file=/etc/glance/glance-api.conf      >/var/log/glance/glance-api.log  2>&1 &

EOF

#---------------------------------------------------
# Create service control script
#---------------------------------------------------

cp -rf $TOPDIR/tools/glance /etc/init.d
SERVICE_FILE=/etc/init.d/glance
sed -i "s,%TENANT_NAME%,$SERVICE_TENANT_NAME,g" $SERVICE_FILE
sed -i "s,%USERNAME%,glance,g" $SERVICE_FILE
sed -i "s,%PASSWORD%,$KEYSTONE_GLANCE_SERVICE_PASSWORD,g" $SERVICE_FILE
sed -i "s,%AUTH_URL%,http://$KEYSTONE_HOST:5000/v2.0,g" $SERVICE_FILE
sed -i "s,%API_LOGFILE%,/var/log/glance/glance-api.log,g" $SERVICE_FILE
sed -i "s,%REGISTRY_LOGFILE%,/var/log/glance/glance-registry.log,g" $SERVICE_FILE
sed -i "s,%GLANCE_DIR%,/opt/stack/glance,g" $SERVICE_FILE
chmod +x /etc/init.d/glance 


cp -rf $TOPDIR/tools/glancerc /root/
sed -i "s,%KEYSTONE_GLANCE_SERVICE_PASSWORD%,$KEYSTONE_GLANCE_SERVICE_PASSWORD,g" /root/glancerc
sed -i "s,%KEYSTONE_HOST%,$KEYSTONE_HOST,g" /root/glancerc


chmod +x /root/glance.sh
/root/glance.sh
rm -rf /tmp/pip*
rm -rf /tmp/tmp*

set +o xtrace
