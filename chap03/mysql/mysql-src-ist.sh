#!/bin/bash

set -e
set +o xtrace

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
# Prepare directories for installation.
#---------------------------------------------

TOPDIR=$(cd $(dirname "$0") && pwd)
source $TOPDIR/localrc
DIR=/opt

set_password MYSQL_ROOT_PASSWORD

#---------------------------------------------
# install some dep-packages
#---------------------------------------------

DEBIAN_FRONTEND=noninteractive \
apt-get --option "Dpkg::Options::=--force-confold" --assume-yes \
install -y --force-yes openssh-server binutils cpp fetchmail \
flex gcc libarchive-zip-perl libc6-dev  \
libpcre3 libpopt-dev lynx m4 make ncftp \
nmap perl perl-modules unzip zip zlib1g-dev \
autoconf automake1.9 libtool bison autotools-dev \
g++ build-essential libncurses5-dev


#---------------------------------------------
#       Cmake
#---------------------------------------------

if [[ ! -d $DIR/cmake ]]; then
    cd $TEMPDIR
    tar zxvf $TOPDIR/tarfile/cmake-2.8.8.tar.gz
    cd cmake-2.8.8
    ./configure --prefix=$DIR/cmake
    make ; make install
fi


#---------------------------------------------
#       MySQL
#---------------------------------------------

if [[ ! -d $DIR/mysql ]]; then
    # add mysql:mysql user
    if [[ `cat /etc/passwd | grep mysql | wc -l` -eq 0 ]]; then
	    groupadd mysql
	    useradd -g mysql mysql
    fi

    # untar mysql source packages.
    cd $TEMPDIR
    tar zxvf $TOPDIR/tarfile/mysql-5.5.20.tar.gz
    cd mysql-5.5.20

    # compile source code.
    $DIR/cmake/bin/cmake \
    -DCMAKE_INSTALL_PREFIX=$DIR/mysql \
    -DMYSQL_DATADIR=$DIR/mysql/data \
    -DEXTRA_CHARSETS=utf8
    make ; make install

    chmod +w $DIR/mysql
    chown -R mysql:mysql $DIR/mysql

    # Configure the configuration file.
    cp $DIR/mysql/support-files/my-large.cnf /etc/my.cnf
    cp $DIR/mysql/support-files/mysql.server /etc/init.d/mysql
    chmod +x /etc/init.d/mysql
    chmod a+w $DIR/mysql
    mkdir -p $DIR/mysql/var/mysql
    mkdir -p $DIR/mysql/var/mysql/data
    mkdir -p $DIR/mysql/var/mysql/log
    mkdir -p $DIR/mysql/var/mysql/lock
    mkdir -p $DIR/mysql/var/run/mysqld
    chown -R mysql:mysql $DIR/mysql

    # init database
    $DIR/mysql/scripts/mysql_install_db \
    --basedir=$DIR/mysql/ \
    --datadir=$DIR/mysql/data \
    --user=mysql

    service mysql restart

    # Set mysql admin's password
    $DIR/mysql/bin/mysqladmin -u root password $MYSQL_ROOT_PASSWORD
    rm -rf /usr/bin/mysql
    ln -s /opt/mysql/bin/mysql /usr/bin/mysql

    # give root's right
    mysql -uroot -p$MYSQL_ROOT_PASSWORD  -e "GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' identified by '$MYSQL_ROOT_PASSWORD'; FLUSH PRIVILEGES;"
    mysql -uroot -p$MYSQL_ROOT_PASSWORD  -e "GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' identified by '$MYSQL_ROOT_PASSWORD'  WITH GRANT OPTION; FLUSH PRIVILEGES;"
fi


set -o xtrace


