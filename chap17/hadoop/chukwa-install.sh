#!/bin/bash
#set -o xtrace


#Load local aruguments
TOP_DIR=$(cd $(dirname "$0") && pwd)
source $TOP_DIR/localrc
# HOST IP of local host
HOST_IP=`ifconfig eth0 | grep "inet addr" | sed "s/:/ /g" | awk '{print $3}'`
HOSTNAME=`hostname`
# IP address of NTP server
NTP_SERVER=${NTP_SERVER:-$MASTER}

# load self-defined functions
source $TOP_DIR/scripts/function

###############################
#
# NTP configuration
#
##############################

if [[ $NTP_SERVER = 127.0.0.1 || $NTP_SERVER = $HOST_IP || $NTP_SERVER = $HOSTNAME ]]; then #ntp server
   $TOP_DIR/scripts/ntp.sh
   service ntp stop
   service ntp start
   if [[  `ntpq -c pe | grep "LOCL" | awk '{print $3}'` -ne 8 ]]; then
       echo "NTP server is not started correctly!"
       exit 1
   fi
else                # NTP client
    if [[ `grep "ntpdate" /etc/crontab | wc -l` -eq 0 ]]; then
	    echo "10 * * * * /usr/sbin/ntpdate $NTP_SERVER" >> /etc/crontab
    fi
fi

###############################
#
#Install systat
#
##############################

$TOP_DIR/scripts/sysstat_install.sh

###############################
#
# Install Hitune
#
###############################

# normalize HADOOP_HOME & HADOOP_CONF
RUN_USER=${RUN_USER:-hadoop}
HADOOP_INSTALL_DIR=${HADOOP_INSTALL_DIR:-/home/$RUN_USER}
HADOOP_CONF_DIR=${HADOOP_CONF_DIR:-/etc/hadoop}
HADOOP_HOME=${HADOOP_HOME:-$HADOOP_INSTALL_DIR/hadoop}
HADOOP_CONF=${HADOOP_CONF:-$HADOOP_CONF_DIR/conf}
CLUSTER_ROLE=${CLUSTER_ROLE:-chukwa}
HDFS_DEFAULT=`read_xml "fs.default.name" "$HADOOP_CONF/core-site.xml"`
AGENT_LIST=${AGENTS:-$HOSTNAME}
AGENTS=`echo $AGENT_LIST | sed 's/ /,/g'`
COLLECTOR_LIST=${COLLECTORS:-$HOSTNAME}
COLLECTORS=`echo $COLLECTOR_LIST | sed 's/ /,/g'`
JAVA_HOME=${JAVA_HOME:-/usr/java/jdk1.6.0_26}
JAVA_PLATFORM=${JAVA_PATFORM:-Linux-amd64-64}
CHUKWA_INSTALL_DIR=${CHUKWA_INSTALL_DIR:-/home/$RUN_USER}
HDFS_URI=${HDFS_URI:-$HDFS_DEFAULT}
HADOOP_CORE_JAR=${HADOOP_CORE_JAR:-$HADOOP_HOME/hadoop-core-0.20.2-cdh3u5.jar}
HADOOP_LOG_DIR=${HADOOP_LOG_DIR:-/var/log/hadoop}
CHUKWA_LOG_DIR=${CHUKWA_LOG_DIR:-$HADOOP_LOG_DIR/chukwa}
HADOOP_HISTORY_DIR=${HADOOP_HISTORY_DIR:-$HADOOP_LOG_DIR/history/done}

#Check chukwa install package
[[ ! -e $TOP_DIR/HiTune-master ]] && unzip $TOP_DIR/hitune.zip -d $TOP_DIR
chmod +x $TOP_DIR/HiTune-master/configure 


#Configure chukwa
cat << EOF > $TOP_DIR/configure-chukwa.sh
#!/usr/bin/expect -f

spawn $TOP_DIR/HiTune-master/configure
expect {
"The role of the cluster*]:" {send "\r"; exp_continue}
"The folder to install HiTune*]:" {send "${CHUKWA_INSTALL_DIR}\r";exp_continue}
"Hadoop cluster*]:" {send "$AGENTS\r";exp_continue}
"collector nodes*]:" {send "$COLLECTORS\r";exp_continue}
"HDFS URI*]:" {send "$HDFS_URI\r";exp_continue}
"Java home*]:" {send "$JAVA_HOME\r";exp_continue}
"Java platform*]:" {send "$JAVA_PLATFORM\r";exp_continue}
"Hadoop home*]:" {send "$HADOOP_HOME\r";exp_continue}
"Hadoop configuration folder*]:" {send "$HADOOP_CONF\r";exp_continue}
"Hadoop core jar file*]:" {send "$HADOOP_CORE_JAR\r";exp_continue}
"hadoop_log_dir*]:" {send "$CHUKWA_LOG_DIR\r";exp_continue}
"Hadoop history log folder - *]:" {send "$HADOOP_HISTORY_DIR\r"}
}

expect eof

EOF

chmod +x $TOP_DIR/configure-chukwa.sh
$TOP_DIR/configure-chukwa.sh 
[[ ! -e $CHUKWA_INSTALL_DIR ]] && mkdir -p $CHUKWA_INSTALL_DIR
[[ -e $CHUKWA_INSTALL_DIR/chukwa-hitune-dist ]] && rm -rf $CHUKWA_INSTALL_DIR/chukwa-hitune-dist

#Install chukwa
rm -rf $HADOOP_HOME/lib/json.jar
rm -if $HADOOP_HOME/lib/json-lib-2.2.3-jdk15.jar
$TOP_DIR/HiTune-master/install.sh -f $TOP_DIR/HiTune-master/chukwa-cluster.conf -r $CLUSTER_ROLE
CHUKWA_HOME=$CHUKWA_INSTALL_DIR/chukwa-hitune-dist

#Copy necessary jar ball
cp -f $CHUKWA_HOME/chukwa-agent-0.4.0.jar $HADOOP_HOME/lib
cp -f $CHUKWA_HOME/chukwa-hadoop-0.4.0-client.jar $HADOOP_HOME/lib
cp -f $CHUKWA_HOME/tools-0.4.0.jar $HADOOP_HOME/lib
cp -f $HADOOP_HOME/lib/guava-r09-jarjar.jar $CHUKWA_HOME/lib

#Configure hadoop
mkdir $CHUKWA_HOME/hitune_output
cp -f $CHUKWA_HOME/conf/hadoop-log4j.properties $HADOOP_HOME/conf/log4j.properties
cp -f $CHUKWA_HOME/conf/hadoop-metrics.properties $HADOOP_HOME/conf/hadoop-metrics.properties

if [[ `grep "mapred.job.reuse.jvm.num.tasks" $HADOOP_CONF/mapred-site.xml | wc -l` -eq 0 ]]; then
   append_to_xml "mapred.job.reuse.jvm.num.tasks" "1" "$HADOOP_CONF/mapred-site.xml"
fi

if [[ `grep "mapred.child.java.opts" $HADOOP_CONF/mapred-site.xml | wc -l` -eq 0 ]]; then
   append_to_xml "mapred.child.java.opts" "-Xmx200m -javaagent:$CHUKWA_HOME/hitune/HiTuneInstrumentAgent-0.9.jar=traceoutput=$CHUKWA_HOME/hitune_output,taskid=@taskid@" "$HADOOP_CONF/mapred-site.xml"
fi
if [[ `grep "mapreduce.job.counters.limit" $HADOOP_CONF/mapred-site.xml | wc -l` -eq 0 ]]; then
   append_to_xml "mapreduce.job.counters.limit" "32000" "$HADOOP_CONF/mapred-site.xml"
fi
if [[ `grep "dfs.datanode.max.xcievers" $HADOOP_CONF/hdfs-site.xml | wc -l` -eq 0 ]]; then
   append_to_xml "dfs.datanode.max.xcievers" "4096" "$HADOOP_CONF/hdfs-site.xml"
fi

#Configure chukwa
sed -i 's/\*_\*_job_\*_\*_\*_\*/job_\*_\*_\*_\*/g' $CHUKWA_HOME/conf/initial_adaptors

#Change the owner of coresponding directories
chown -R $RUN_USER:$RUN_USER $CHUKWA_HOME
CHUKWA_PID_DIR=`read_conf "CHUKWA_PID_DIR" "$CHUKWA_HOME/conf/chukwa-env.sh"`
[[ ! -e $CHUKWA_PID_DIR ]] && mkdir -p $CHUKWA_PID_DIR
chown -R $RUN_USER:$RUN_USER $CHUKWA_PID_DIR
#set +o xtrace
