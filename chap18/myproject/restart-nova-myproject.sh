#!/bin/bash
set -e
set -o xtrace
#chmod a+w /opt/stack/nova/networks


ps  aux | grep -v "grep" | grep -v "res"| grep "nova-myproject" | awk '{print $2}' | xargs -i kill -9 {} ;
rm -rfv /var/log/nova/nova-myproject.log >/dev/null
#if [[ $1 =~ (compute) ]]; then
#    nohup sg libvirtd /opt/stack/nova/bin/nova-compute >/var/log/nova/nova-compute.log 2>&1 &
#fi    
nohup python /opt/stack/nova/nova/myproject/nova-myproject --config-file=/etc/nova/nova.conf >/var/log/nova/nova-myproject.log 2>&1 &
set +o xtrace
