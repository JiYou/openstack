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
TEMP=`mktemp`; rm -rfv $TEMP >/dev/null; mkdir -p $TEMP;
source $TOPDIR/localrc
source $TOPDIR/tools/function
DEST=/opt/stack/
mkdir -p $DEST

#---------------------------------------------------
# unset some variables
#---------------------------------------------------

unset http_proxy
unset https_proxy
unset ftp_proxy
export OS_USERNAME=""
export OS_AUTH_KEY=""
export OS_AUTH_TENANT=""
export OS_STRATEGY=""
export OS_AUTH_STRATEGY=""
export OS_AUTH_URL=""
export SERVICE_ENDPOINT=""


#---------------------------------------------------
# set some variables
#---------------------------------------------------

BASE_SQL_CONN=mysql://$MYSQL_KEYSTONE_USER:$MYSQL_KEYSTONE_PASSWORD@$MYSQL_HOST
KEYSTONE_AUTH_HOST=$KEYSTONE_HOST
KEYSTONE_AUTH_PORT=35357
KEYSTONE_AUTH_PROTOCOL=http
KEYSTONE_SERVICE_HOST=$KEYSTONE_HOST
KEYSTONE_SERVICE_PORT=5000
KEYSTONE_SERVICE_PROTOCOL=http
SERVICE_ENDPOINT=http://$KEYSTONE_HOST:35357/v2.0
KEYSTONE_DIR=$DEST/keystone
KEYSTONE_CONF_DIR=$DEST/keystone/etc
KEYSTONE_CONF=$KEYSTONE_CONF_DIR/keystone.conf
KEYSTONE_CATALOG_BACKEND=sql
KEYSTONE_LOG_CONFIG="--log-config $KEYSTONE_CONF_DIR/logging.conf"
logfile=/var/log/nova/keystone.log


#---------------------------------------------------
# Clear Front installation
#---------------------------------------------------

DEBIAN_FRONTEND=noninteractive \
apt-get --option \
"Dpkg::Options::=--force-confold" --assume-yes \
install -y --force-yes mysql-client


chmod +x /usr/bin/nkill
nkill keystone

[[ -d $DEST/keystone/etc ]] && cp -rf $TOPDIR/openstacksource/keystone/etc/* $DEST/keystone/etc/
mysql_cmd "DROP DATABASE IF EXISTS keystone;"

#---------------------------------------------------
# Begin new installation.
#---------------------------------------------------

DEBIAN_FRONTEND=noninteractive \
apt-get --option \
"Dpkg::Options::=--force-confold" --assume-yes \
install -y --force-yes openssh-server build-essential git \
python-dev python-setuptools python-pip \
libxml2-dev libxslt-dev unzip python-mysqldb mysql-client

[[ -e /usr/include/libxml ]] && rm -rf /usr/include/libxml  
ln -s /usr/include/libxml2/libxml /usr/include/libxml

#---------------------------------------------------
# Install Keystone
#---------------------------------------------------

[[ ! -d $DEST ]] && mkdir -p $DEST
install_keystone

mkdir -p /etc/keystone
cp -rf $DEST/keystone/etc/* /etc/keystone/

#---------------------------------------------------
# Create Data Base for keystone.
#---------------------------------------------------

# create user
cnt=`mysql_cmd "select * from mysql.user;" | grep $MYSQL_KEYSTONE_USER | wc -l`
if [[ $cnt -eq 0 ]]; then
    mysql_cmd "create user '$MYSQL_KEYSTONE_USER'@'%' identified by '$MYSQL_KEYSTONE_PASSWORD';"
    mysql_cmd "flush privileges;"
fi

# create database
cnt=`mysql_cmd "show databases;" | grep keystone | wc -l`
if [[ $cnt -eq 0 ]]; then
    mysql_cmd "create database keystone CHARACTER SET utf8;"
fi
mysql_cmd "use mysql; delete from user where user=''; flush privileges;"
mysql_cmd "grant all privileges on keystone.* to '$MYSQL_KEYSTONE_USER'@'%' identified by '$MYSQL_KEYSTONE_PASSWORD';"
mysql_cmd "grant all privileges on keystone.* to '$MYSQL_KEYSTONE_USER'@'%' identified by '$MYSQL_KEYSTONE_PASSWORD';"
mysql_cmd "GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' identified by '$MYSQL_ROOT_PASSWORD'; FLUSH PRIVILEGES;"
mysql_cmd "GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' identified by '$MYSQL_ROOT_PASSWORD'  WITH GRANT OPTION; FLUSH PRIVILEGES;"
mysql_cmd "flush privileges;"


#---------------------------------------------------
# Change keystone.conf
#---------------------------------------------------

mkdir -p /etc/keystone
mkdir -p /etc/keystone/ssl
file=/etc/keystone/keystone.conf
cp -rf $KEYSTONE_CONF_DIR/keystone.conf.sample $file
sed -i "s,# admin_token = ADMIN,admin_token = $ADMIN_TOKEN,g" $file
sed -i "s,# connection = sqlite:///keystone.db,connection = $BASE_SQL_CONN/keystone?charset=utf8,g" $file
sed -i "s,# driver = keystone.catalog.backends.sql.Catalog,driver = keystone.catalog.backends.sql.Catalog,g" $file
sed -i "s,#token_format = PKI,token_format = UUID,g" $file
sed -i "s,# driver = keystone.contrib.ec2.backends.kvs.Ec2,driver = keystone.contrib.ec2.backends.sql.Ec2,g" $file

#---------------------------------------------------
# Change logging.conf
#---------------------------------------------------

file=/etc/keystone/logging.conf
TONE_LOG_CONFIG="--log-config $file"
cp $KEYSTONE_DIR/etc/logging.conf.sample $file
sed -i "s,level=WARNING,level=DEBUG,g" $file
sed -i "s/handlers=file/handlers=devel,production/g" $file

[[ -d /var/log/nova ]] && rm -rf /var/log/nova/keytone*
mkdir -p /var/log/nova
logfile=/var/log/nova/keystone.log


#---------------------------------------------------
# Sync Data Base
#---------------------------------------------------

$KEYSTONE_DIR/bin/keystone-manage \
--config-file /etc/keystone/keystone.conf db_sync


#---------------------------------------------------
# Start service of Keystone
#---------------------------------------------------


cd $KEYSTONE_DIR
nohup python ./bin/keystone-all \
--config-file /etc/keystone/keystone.conf \
--log-config /etc/keystone/logging.conf \
-d --debug >$logfile 2>&1 &

#---------------------------------------------------
# Wait the service to startup
#---------------------------------------------------

sleep 20
ps aux | grep keystone
sleep 10
echo $SERVICE_ENDPOINT
if ! timeout 5 sh -c "while ! curl -s $SERVICE_ENDPOINT/ >/dev/null; do sleep 1; done"; then
      echo "keystone did not start"
      echo "ERROR occur!"
      exit 1
fi

#---------------------------------------------------
# Init the databases and endpoints.
#---------------------------------------------------

cp -rf $TOPDIR/tools/keystone_data.sh /tmp/
sed -i "s,%KEYSTONE_HOST%,$KEYSTONE_HOST,g" /tmp/keystone_data.sh
sed -i "s,%SERVICE_TOKEN%,$SERVICE_TOKEN,g" /tmp/keystone_data.sh
sed -i "s,%ADMIN_PASSWORD%,$ADMIN_PASSWORD,g" /tmp/keystone_data.sh
sed -i "s,%SERVICE_TENANT_NAME%,$SERVICE_TENANT_NAME,g" /tmp/keystone_data.sh
sed -i "s,%KEYSTONE_CATALOG_BACKEND%,$KEYSTONE_CATALOG_BACKEND,g" /tmp/keystone_data.sh
sed -i "s,%SERVICE_ENDPOINT%,$SERVICE_ENDPOINT,g" /tmp/keystone_data.sh

chmod +x /tmp/keystone_data.sh
/tmp/keystone_data.sh
rm -rf /tmp/keystone_data.sh

#---------------------------------------------------
# Test the service
#---------------------------------------------------

curl -d "{\"auth\": {\"tenantName\": \"$ADMIN_USER\", \"passwordCredentials\":{\"username\": \"$ADMIN_USER\", \"password\": \"$ADMIN_PASSWORD\"}}}" -H "Content-type: application/json" $SERVICE_ENDPOINT/tokens | python -mjson.tool

TOKEN=`curl -s -d  "{\"auth\":{\"passwordCredentials\": {\"username\": \"$ADMIN_USER\", \"password\": \"$ADMIN_PASSWORD\"}, \"tenantName\": \"admin\"}}" -H "Content-type: application/json" $SERVICE_ENDPOINT/tokens | python -c "import sys; import json; tok = json.loads(sys.stdin.read()); print tok['access']['token']['id'];"`
echo $TOKEN


#---------------------------------------------------
# Generate Keystone RC
#---------------------------------------------------

cat <<EOF > ~/keyrc
export OS_TENANT_NAME=$ADMIN_USER
export OS_USERNAME=$ADMIN_USER
export OS_PASSWORD=$ADMIN_PASSWORD
export OS_AUTH_URL="http://$KEYSTONE_HOST:5000/v2.0/"
EOF


#---------------------------------------------------
# Create service control script
#---------------------------------------------------

cp -rf $TOPDIR/tools/keystone /etc/init.d/
temp_file=/etc/init.d/keystone

sed -i "s,%ADMIN_USER%,$ADMIN_USER,g" $temp_file
sed -i "s,%ADMIN_TOKEN%,$ADMIN_TOKEN,g" $temp_file
sed -i "s,%ADMIN_PASSWORD%,$ADMIN_PASSWORD,g" $temp_file
sed -i "s,%KEYSTONE_HOST%,$KEYSTONE_HOST,g" $temp_file
sed -i "s,%SERVICE_ENDPOINT%,$SERVICE_ENDPOINT,g" $temp_file
sed -i "s,%logfile%,$logfile,g" $temp_file
sed -i "s,%KEYSTONE_DIR%,$KEYSTONE_DIR,g" $temp_file

chmod +x /etc/init.d/keystone

rm -rf /tmp/tmp*

set +o xtrace
