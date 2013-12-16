#!/bin/bash
#set -o xtrace

#######################################
# Check current user
#######################################
USER=`id -un`
if [[ $USER != "root" ]]; then
    echo "This script should be run as root user!"
    exit 1
fi

#######################################
# Load the basic configuration
#######################################

TOP_DIR=$(cd $(dirname "$0") && pwd)
cd $TOP_DIR/..
PAR_DIR=`pwd`

cp -rf $TOP_DIR/nkill /usr/bin/

HOSTNAME=`hostname`
IP=`ifconfig eth0 | grep "inet addr" | sed "s/:/ /g" | awk '{print $3}'`
source $TOP_DIR/localrc
source $TOP_DIR/scripts/function

# Add MASTER var into localrc, so that to install slave nodes correctly
if [[ "$MASTER" = "" ]]; then
    MASTER=$HOSTNAME 
    echo "MASTER=$MASTER" >> $TOP_DIR/localrc
fi

# Set default configuration
SLAVES=${SLAVES:-$HOSTNAME}
AGENTS=${AGENTS:-$HOSTNAME}
RUN_USER=${RUN_USER:-hadoop}

# Check login password of Hadoop & Chukwa nodes
if [[ "$LOGIN_PASSWORD" = "" ]]; then
    echo "LOGIN_PASSWORD is not set!"
    exit 1
fi

echo "Configuration of Hadoop & Chukwa:"
echo "MASTER=$MASTER"
echo "SLAVES=$SLAVES"
echo "AGENTS=$AGENTS"
echo "COLLECTORS=$COLLECTORS"

# Check the configuration
echo -n "Start to install?( yes or no): "
read -a DO_INSTALL
if [[ $DO_INSTALL != 'yes' ]]; then
    exit 1
fi

#########################################
# Install apt-get package
######################################### 

# Get all hosts
ALL_HOSTS=`get_all_hosts "$SLAVES $MASTER $AGENTS $COLLECTORS"`

$TOP_DIR/scripts/apt.sh

# instal apt-get packages in other nodes
for HOST in $ALL_HOSTS; do
    if [[ $HOST != $HOSTNAME ]]; then
        $TOP_DIR/scripts/run_ssh.sh $HOST $LOGIN_PASSWORD "$TOP_DIR/scripts/apt.sh"
    fi
done

#########################################
# /etc/hosts configuration
#########################################


# Add local host into hadoop/hosts
if [[ `grep $HOSTNAME $TOP_DIR/hosts | grep -v '#' | wc -l` -eq 0 ]]; then
    echo "$IP    $HOSTNAME" >> $TOP_DIR/hosts
fi

# Check the configuration of hadoop/hosts
for HOST in $ALL_HOSTS; do
    if [[ `grep $HOST $TOP_DIR/hosts | grep -v '#' | wc -l` -eq 0 ]]; then
        echo "$HOST is not set in $TOP_DIR/hosts!"
        exit 1
    fi
done

# Backup /etc/hosts
[[ -e /etc/hosts_bak ]] || cp /etc/hosts /etc/hosts_bak

# configure /etc/hosts
$TOP_DIR/scripts/configure_hosts.sh

# Check the Connection of hosts
for HOST in $ALL_HOSTS; do
    CONN_RES=`ping -c 4 $HOST | grep "100% packet loss" | wc -l`
    if [[ $CONN_RES -ne 0 ]]; then
        echo "Failed to connect to $HOST, please check the network connection!"
        exit 1
    fi
done

# Configure /etc/hosts on other nodes
for HOST in $ALL_HOSTS; do
    if [[ $HOST != $HOSTNAME ]]; then
        $TOP_DIR/scripts/run_scp.sh $LOGIN_PASSWORD "$TOP_DIR/localrc" "root@$HOST:$TOP_DIR/localrc"
        $TOP_DIR/scripts/run_scp.sh $LOGIN_PASSWORD "$TOP_DIR/hosts" "root@$HOST:$TOP_DIR/hosts"
        $TOP_DIR/scripts/run_ssh.sh $HOST $LOGIN_PASSWORD "$TOP_DIR/scripts/configure_hosts.sh"
    fi
done

##########################################
# Configure /etc/hosts in other hosts
#########################################

for HOST in $ALL_HOSTS; do
    if [[ $HOST != $HOSTNAME ]]; then
        $TOP_DIR/scripts/run_ssh.sh $HOST $LOGIN_PASSWORD "$TOP_DIR/scripts/configure_hosts.sh"
    fi
done

#########################################
# Add run_user in each hosts
#########################################

# local host
#[[ `cat /etc/passwd | grep $RUN_USER | wc -l` -eq 0 ]] && deluser $RUN_USER --remove-home --remove-all-files
$TOP_DIR/scripts/add_user.sh $RUN_USER $LOGIN_PASSWORD

# other hosts
for HOST in $ALL_HOSTS; do
    if [[ $HOST != $HOSTNAME ]]; then
        #$TOP_DIR/scripts/run_ssh.sh $HOST $LOGIN_PASSWORD "[[ `cat /etc/passwd | grep $RUN_USER | wc -l` -eq 0 ]] && deluser $RUN_USER --remove-home --remove-all-files"
        $TOP_DIR/scripts/run_ssh.sh $HOST $LOGIN_PASSWORD "$TOP_DIR/scripts/add_user.sh $RUN_USER $LOGIN_PASSWORD"
    fi
done

        
#########################################
#     Configure SSH & HOSTS
#########################################

# generate ssh key
$TOP_DIR/scripts/ssh-keygen.sh $RUN_USER
for HOST in $ALL_HOSTS; do
    if [[ $HOST != $HOSTNAME ]]; then
        $TOP_DIR/scripts/run_ssh.sh $HOST $LOGIN_PASSWORD "$TOP_DIR/scripts/ssh-keygen.sh $RUN_USER"
    fi
done

# collect all pub keys
tempfile=`mktemp`
rm $tempfile
mkdir -p $tempfile

cp /home/$RUN_USER/.ssh/id_rsa.pub $tempfile/$HOSTNAME

for HOST in $ALL_HOSTS; do
    if [[ $HOST != $HOSTNAME ]]; then
        $TOP_DIR/scripts/run_scp.sh $LOGIN_PASSWORD "root@$HOST:/home/$RUN_USER/.ssh/id_rsa.pub" $tempfile/$HOST
    fi
done

# create authorized_keys file
cd $tempfile
rm /home/$RUN_USER/.ssh/authorized_keys
ls | xargs -i cat {} >> /home/$RUN_USER/.ssh/authorized_keys
rm -r $tempfile

# cpoy authorized_keys file to other hosts
for HOST in $ALL_HOSTS; do
    if [[ $HOST != $HOSTNAME ]]; then
        $TOP_DIR/scripts/run_scp.sh $LOGIN_PASSWORD "/home/$RUN_USER/.ssh/authorized_keys" "root@$HOST:/home/$RUN_USER/.ssh/"
    fi
done

# change permmision of authorized_keys file
chown -R $RUN_USER:$RUN_USER /home/$RUN_USER/.ssh
chmod 0700 /home/$RUN_USER/.ssh/authorized_keys

for HOST in $ALL_HOSTS; do
    if [[ $HOST != $HOSTNAME ]]; then
        $TOP_DIR/scripts/run_ssh.sh $HOST $LOGIN_PASSWORD "chown -R $RUN_USER:$RUN_USER /home/$RUN_USER/.ssh;chmod 0700 /home/$RUN_USER/.ssh/authorized_keys"
    fi
done

#########################################
#     JDK installation
#########################################
$TOP_DIR/scripts/java_install.sh

for HOST in $ALL_HOSTS; do
    if [[ $HOST != $HOSTNAME ]]; then
        $TOP_DIR/scripts/run_ssh.sh $HOST $LOGIN_PASSWORD "$TOP_DIR/scripts/java_install.sh"
    fi
done


#########################################
# Hadoop install
#########################################

$TOP_DIR/hadoop-install.sh

for HOST in $ALL_HOSTS; do
    if [[ $HOST != $HOSTNAME ]]; then
        $TOP_DIR/scripts/run_ssh.sh $HOST $LOGIN_PASSWORD "$TOP_DIR/hadoop-install.sh"
    fi
done

#########################################
# Chukwa install
#########################################
if [[ -z $COLLECTORS ]]; then
    echo "COLLECTORS is not set in localrc, skip Hitune installation."
    exit 0
fi

$TOP_DIR/chukwa-install.sh

for HOST in $ALL_HOSTS; do
    if [[ $HOST != $HOSTNAME ]]; then
        $TOP_DIR/scripts/run_ssh.sh $HOST $LOGIN_PASSWORD "$TOP_DIR/chukwa-install.sh"
    fi
done


#set +o xtrace
