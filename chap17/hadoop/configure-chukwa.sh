#!/usr/bin/expect -f

spawn /root/hadoop/HiTune-master/configure
expect {
"The role of the cluster*]:" {send "\r"; exp_continue}
"The folder to install HiTune*]:" {send "/home/hadoop\r";exp_continue}
"Hadoop cluster*]:" {send "master,slave\r";exp_continue}
"collector nodes*]:" {send "master\r";exp_continue}
"HDFS URI*]:" {send "hdfs://master:9000/\r";exp_continue}
"Java home*]:" {send "/usr/java/jdk1.6.0_26\r";exp_continue}
"Java platform*]:" {send "Linux-amd64-64\r";exp_continue}
"Hadoop home*]:" {send "/home/hadoop/hadoop\r";exp_continue}
"Hadoop configuration folder*]:" {send "/etc/hadoop/conf\r";exp_continue}
"Hadoop core jar file*]:" {send "/home/hadoop/hadoop/hadoop-core-0.20.2-cdh3u5.jar\r";exp_continue}
"hadoop_log_dir*]:" {send "/var/log/hadoop/chukwa\r";exp_continue}
"Hadoop history log folder - *]:" {send "/var/log/hadoop/history/done\r"}
}

expect eof

