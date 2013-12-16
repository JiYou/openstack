#!/bin/bash
TOP_DIR=$(cd $(dirname "$0") && pwd)
TOP_DIR=$TOP_DIR/..

source $TOP_DIR/localrc
JAVA_HOME=${JAVA_HOME:-/usr/java}

mkdir -p $JAVA_HOME
jdk_file=jdk-6u26-linux-x64.bin
JAVADIR=jdk1.6.0_26

if [[ ! -e $JAVA_HOME/$jdk_file ]]; then
    cp $TOP_DIR/$jdk_file $JAVA_HOME
    cd $JAVA_HOME
    chmod +x $jdk_file
    ./$jdk_file
    echo "export JAVA_HOME=$JAVA_HOME/$JAVADIR" >> /etc/profile
    echo "export PATH=\$JAVA_HOME/bin:\$JAVA_HOME/jre/bin:\$PATH" >> /etc/profile
    echo "export CLASSPATH=\$CLASSPATH:\$JAVA_HOME/lib:\$JAVA_HOME/jre/lib" >> /etc/profile
    source /etc/profile
fi
