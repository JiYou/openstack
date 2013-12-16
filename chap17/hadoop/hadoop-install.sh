#!/bin/bash
#################################
#
# Load local aruguments
#
#################################

TOP_DIR=$(cd $(dirname "$0") && pwd)
unset JAVA_HOME
source $TOP_DIR/localrc

RUN_USER=${RUNN_USER:-hadoop}
HADOOP_INSTALL_DIR=${HADOOP_INSTALL_DIR:-/home/$RUN_USER}
HADOOP_CONF_DIR=${HADOOP_CONF_DIR:-/etc/hadoop}
JAVA_HOME=${JAVA_HOME:-/usr/java}
HADOOP_LOG_DIR=${HADOOP_LOG_DIR:-/var/log/hadoop}
HADOOP_PID_DIR=${HADOOP_PID_DIR:-/var/hadoop/pids}

#############################################
#
# Copy Hadoop source dirs
#
############################################

#Copy Hadoop source file
[[ -e $HADOOP_INSTALL_DIR ]] || mkdir -p $HADOOP_INSTALL_DIR
[[ -e $HADOOP_INSTALL_DIR/hadoop-0.20.2-cdh3u5 ]] || tar zxvf $TOP_DIR/hadoop-0.20.2-cdh3u5.tar.gz -C $HADOOP_INSTALL_DIR
[[ -e $HADOOP_INSTALL_DIR/hadoop ]] && rm -r $HADOOP_INSTALL_DIR/hadoop
mkdir -p $HADOOP_INSTALL_DIR/hadoop

RUN_USER=${RUNN_USER:-hadoop}
cp -r $HADOOP_INSTALL_DIR/hadoop-0.20.2-cdh3u5/* $HADOOP_INSTALL_DIR/hadoop
HADOOP_HOME=$HADOOP_INSTALL_DIR/hadoop

#Create symbolic file of Hadoop conf dir
[[ -e $HADOOP_CONF_DIR ]] || mkdir -p $HADOOP_CONF_DIR
[[ -e $HADOOP_CONF_DIR/conf ]] && rm $HADOOP_CONF_DIR/conf
ln -s $HADOOP_HOME/conf $HADOOP_CONF_DIR/conf
chown -R $RUN_USER:$RUN_USER $HADOOP_CONF_DIR
HADOOP_CONF=$HADOOP_CONF_DIR/conf

########################################
#
# Configure Hadoop
#
########################################

# slaves
rm $HADOOP_CONF/slaves
for n in $SLAVES; do
    echo $n >> $HADOOP_CONF/slaves
done

# master
echo $MASTER > $HADOOP_CONF/masters

# hadoop-env.sh
sed -i "/export JAVA_HOME=/d" $HADOOP_CONF/hadoop-env.sh 
sed -i "/export HADOOP_LOG_DIR=/d" $HADOOP_CONF/hadoop-env.sh 
sed -i "/export HADOOP_PID_DIR=/d" $HADOOP_CONF/hadoop-env.sh 

JAVA_HOME=$JAVA_HOME/jdk1.6.0_26
echo "export JAVA_HOME=$JAVA_HOME" >> $HADOOP_CONF/hadoop-env.sh
echo "export HADOOP_LOG_DIR=$HADOOP_LOG_DIR" >> $HADOOP_CONF/hadoop-env.sh
echo "export HADOOP_PID_DIR=$HADOOP_PID_DIR" >> $HADOOP_CONF/hadoop-env.sh

function init_xml(){
cat <<"EOF"> $1
<?xml version="1.0"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
EOF
}

# core-site.xml
file=$HADOOP_CONF/core-site.xml
init_xml $file
cat <<"EOFF">> $file
<configuration>
    <property>
        <name>hadoop.tmp.dir</name>
        <value>/hadoop/tmp</value>
    </property>
    <property>
        <name>fs.default.name</name>
        <value>hdfs://%master%:9000/</value>
    </property>
</configuration>
EOFF
sed -i "s,%master%,$MASTER,g" $file

# hdfs-site.xml
file=$HADOOP_CONF/hdfs-site.xml
init_xml $file

cat <<"EOFF">> $file
<configuration>
    <property>
        <name>dfs.replication</name>
        <value>1</value>
    </property>
</configuration>
EOFF

# mapred-site.xml
file=$HADOOP_CONF/mapred-site.xml
init_xml $file
cat <<"EOFF">> $file
<configuration>
    <property>/
        <name>mapred.job.tracker</name>
        <value>%master%:9001</value>
        <final>true</final>
    </property>
</configuration>
EOFF
sed -i "s,%master%,$MASTER,g" $file

#####################################################
#
# Grant the permission of some folders to $RUN_USER
#
#####################################################

chown -R $RUN_USER:$RUN_USER $HADOOP_HOME
chown -R $RUN_USER:$RUN_USER $HADOOP_CONF

if [[ ! -e /hadoop/tmp ]]; then
    mkdir -p /hadoop/tmp
fi
rm -r /hadoop/tmp/*
chown -R $RUN_USER:$RUN_USER /hadoop/tmp

if [[ ! -e $HADOOP_PID_DIR ]]; then
    mkdir -p $HADOOP_PID_DIR
fi
chown -R $RUN_USER:$RUN_USER $HADOOP_PID_DIR

if [[ ! -e $HADOOP_LOG_DIR ]]; then
    mkdir -p $HADOOP_LOG_DIR
fi
chown -R $RUN_USER:$RUN_USER $HADOOP_LOG_DIR

##################################################
#
# Add "hadoop" command
#
##################################################

[[ -e /usr/bin/hadoop ]] && rm /usr/bin/hadoop    
echo "#!/bin/sh" >> /usr/bin/hadoop
echo "export HADOOP_HOME=$HADOOP_HOME" >> /usr/bin/hadoop
echo "exec $HADOOP_HOME/bin/hadoop \"\$@\"" >> /usr/bin/hadoop
chmod a+x /usr/bin/hadoop


