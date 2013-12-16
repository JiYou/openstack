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

#---------------------------------------------
# Set up ENV.
#---------------------------------------------

TOPDIR=$(cd $(dirname "$0") && pwd)
TEMP=`mktemp`;
rm -rfv $TEMP >/dev/null;
mkdir -p $TEMP;
source $TOPDIR/localrc
source $TOPDIR/tools/function
DEST=/opt/stack/


###########################################################
#
#  Clear disk
#
###########################################################

cnt=`mount | grep $SWIFT_DISK_PATH | wc -l`
if [[ $cnt -gt 0 ]]; then
    umount /srv/node/sdb1
    rm -rf /srv/node/sdb1
cat <<"EOF">auto_fdisk.sh
#!/usr/bin/expect -f
spawn fdisk %DISK_PATH%
expect "Command (m for help):"
send "d\r"
expect "Command (m for help):"
send "w\r"
expect eof
EOF
    sed -i "s,%DISK_PATH%,$SWIFT_DISK_PATH,g" auto_fdisk.sh
    chmod a+x auto_fdisk.sh
    ./auto_fdisk.sh
fi



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

nkill swift-account
nkill swift-container
nkill swift-object


############################################################
#
# Install some basic used debs.
#
############################################################


DEBIAN_FRONTEND=noninteractive \
apt-get --option "Dpkg::Options::=--force-confold" --assume-yes \
install -y --force-yes openssh-server build-essential git \
python-dev python-setuptools python-pip \
libxml2-dev libxslt-dev python-pam python-lxml \
memcached openssl expect mysql-client unzip \
python-iso8601 python-prettytable python-requests xfsprogs


[[ -e /usr/include/libxml ]] && rm -rf /usr/include/libxml
ln -s /usr/include/libxml2/libxml /usr/include/libxml


#---------------------------------------------------
# Copy source code to DEST Dir
#---------------------------------------------------

[[ ! -d $DEST ]] && mkdir -p $DEST
install_swift
install_swift3
install_keystone

#---------------------------------------------------
# Create glance user in Linux-System
#---------------------------------------------------



if [[ `cat /etc/passwd | grep swift | wc -l` -eq 0 ]] ; then
    groupadd swift
    useradd -g swift swift
fi

mkdir -p /etc/swift
scp -pr $SWIFT_HOST:/etc/swift/* /etc/swift/
chown -R swift:swift /etc/swift

#---------------------------------------------------
# Swift Configurations - Sync
#---------------------------------------------------

HOST_IP=`nic_ip $SWIFT_NODE_NIC_CARD`

STOR_PATH=/srv/node/
cat <<"EOF">/etc/rsyncd.conf
uid = swift
gid = swift
log file = /var/log/rsyncd.log
pid file = /var/run/rsyncd.pid
address = %HOST_IP%

[account]
max_connections = 2
path = %STOR_PATH%
read only = false
lock file = /var/lock/account.lock

[container]
max_connections = 2
path = %STOR_PATH%
read only = false
lock file = /var/lock/container.lock

[object]
max_connections = 2
path = %STOR_PATH%
read only = false
lock file = /var/lock/object.lock
EOF
sed -i "s,%HOST_IP%, $HOST_IP,g" /etc/rsyncd.conf
sed -i "s,%STOR_PATH%,$STOR_PATH,g" /etc/rsyncd.conf
sed -i 's/RSYNC_ENABLE=false/RSYNC_ENABLE=true/g' /etc/default/rsync
service rsync restart


#---------------------------------------------------
# Swift Configurations - Account
#---------------------------------------------------

cat <<"EOF">/etc/swift/account-server.conf
[DEFAULT]
bind_ip = 0.0.0.0
bind_port = 6012
workers = 1
user = swift
swift_dir = /etc/swift
devices = %STOR_PATH%

[pipeline:main]
pipeline = recon account-server

[filter:recon]
use = egg:swift#recon

[app:account-server]
use = egg:swift#account

[account-replicator]

[account-auditor]

[account-reaper]
EOF
sed -i "s,%HOST_IP%,$HOST_IP,g" /etc/swift/account-server.conf
sed -i "s,%STOR_PATH%,$STOR_PATH,g" /etc/swift/account-server.conf


#---------------------------------------------------
# Swift Configurations - Container
#---------------------------------------------------

cat <<"EOF">/etc/swift/container-server.conf
[DEFAULT]
bind_ip = 0.0.0.0
bind_port = 6011
workers = 1
user = swift
swift_dir = /etc/swift
devices = %STOR_PATH%

[pipeline:main]
pipeline = recon container-server

[app:container-server]
use = egg:swift#container

[filter:recon]
use = egg:swift#recon

[container-replicator]
vm_test_mode = yes

[container-updater]

[container-auditor]

[container-sync]
EOF
sed -i "s,%HOST_IP%,$HOST_IP,g"     /etc/swift/container-server.conf
sed -i "s,%STOR_PATH%,$STOR_PATH,g" /etc/swift/container-server.conf


#---------------------------------------------------
# Object Services
#---------------------------------------------------



cat <<"EOF"> /etc/swift/object-server.conf
[DEFAULT]
bind_ip = 0.0.0.0
bind_port = 6010
workers = 1
user = swift
swift_dir = /etc/swift
devices = %STOR_PATH%

[pipeline:main]
pipeline = recon object-server

[app:object-server]
use = egg:swift#object

[filter:recon]
use = egg:swift#recon
recon_cache_path = /var/cache/swift

[object-replicator]

[object-updater]

[object-auditor]
EOF

sed -i "s,%HOST_IP%,$HOST_IP,g"     /etc/swift/object-server.conf
sed -i "s,%STOR_PATH%,$STOR_PATH,g" /etc/swift/object-server.conf


#---------------------------------------------------
# Format disk
#---------------------------------------------------


DISK_PATH=$SWIFT_DISK_PATH
cat <<"EOF">auto_fdisk.sh
#!/usr/bin/expect -f
spawn fdisk %DISK_PATH%
expect "Command (m for help):"
send "n\r"

expect "Select*:"
send "p\r"

expect "Partition number*:"
send "\r"

expect "First sector*:"
send "\r"

expect "Last sector, +sectors or +size*:"
send "\r"

expect "Command (m for help):"
send "w\r"

expect eof
EOF
sed -i "s,%DISK_PATH%,$DISK_PATH,g" auto_fdisk.sh
chmod a+x auto_fdisk.sh

cd $TOPDIR
./auto_fdisk.sh

cnt=`fdisk -l | grep ${DISK_PATH#*dev/*} | grep Linux | awk '{print $1}' | wc -l`
if [[ $cnt -eq 0 ]]; then
    DEV_PATH=$DISK_PATH
else
    DEV_PATH=`fdisk -l | grep ${DISK_PATH#*dev/*} | grep Linux | awk '{print $1}'`
fi

mkfs.xfs -f  -i size=1024 $DEV_PATH
n=${DEV_PATH#*dev/*}
echo "$DEV_PATH /srv/node/sdb1 xfs noatime,nodiratime,nobarrier,logbufs=8 0 0" >> /etc/fstab

mkdir -p /srv/node/sdb1
mount /srv/node/sdb1
chown -R swift:swift /srv/node
chmod a+w -R /srv

#---------------------------------------------------
# Build Rings
#---------------------------------------------------

mkdir -p /var/log/swift
chown -R swift /var/log/swift
mkdir -p /var/cache/swift/
chown -R swift /var/cache/swift/

cat << "EOF" > /root/swift-storage.sh
#!/bin/bash

set -e
set +o xtrace
cd /opt/stack/swift/bin

nkill swift-account
nkill swift-container
nkill swift-object


# Account
nohup ./swift-account-auditor /etc/swift/account-server.conf -v >/var/log/swift/account-auditor.log 2>&1 &
nohup ./swift-account-server /etc/swift/account-server.conf -v >/var/log/swift/account-server.log 2>&1 &
nohup ./swift-account-reaper /etc/swift/account-server.conf -v >/var/log/swift/account-reaper.log 2>&1 &
nohup ./swift-account-replicator /etc/swift/account-server.conf -v >/var/log/swift/account-replicator.log 2>&1 &


# container
nohup ./swift-container-updater /etc/swift/container-server.conf -v >/var/log/swift/container-updater.log 2>&1 &
nohup ./swift-container-replicator /etc/swift/container-server.conf -v >/var/log/swift/container-replicator.log 2>&1 &
nohup ./swift-container-auditor /etc/swift/container-server.conf -v >/var/log/swift/container-auditor.log 2>&1 &
nohup ./swift-container-sync /etc/swift/container-server.conf -v >/var/log/swift/container-sync.log 2>&1 &
nohup ./swift-container-server /etc/swift/container-server.conf -v >/var/log/swift/container-server.log 2>&1 &

# Object

nohup ./swift-object-replicator /etc/swift/object-server.conf -v >/var/log/swift/object-replicator.log 2>&1 &
nohup ./swift-object-auditor    /etc/swift/object-server.conf -v >/var/log/swift/object-auditor.log 2>&1 &
nohup ./swift-object-updater    /etc/swift/object-server.conf -v >/var/log/swift/object-updater.log 2>&1 &
nohup ./swift-object-server    /etc/swift/object-server.conf -v >/var/log/swift/object-server.log 2>&1 &

set -o xtrace

EOF
chmod +x /root/swift-storage.sh
/root/swift-storage.sh

set +o xtrace
