#!/bin/bash
set -e
set -o xtrace

TOPDIR=$(cd $(dirname "$0") && pwd)
cmd_old_dir=`pwd`
cd $TOPDIR

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

cnt=`cat /etc/rc.local | grep iptables | wc -l`
if [[ $cnt -eq 0 ]]; then
    find_and_run init.sh
fi

if [[ ! -e ./chap03/mysql/tools ]]; then
    old_dir=`pwd`
    cd ./chap03/mysql/
    ln -s ../../tools ./tools
    cd $old_dir
fi

if [[ ! -e ./chap08/multiplenodes/m-compute-node/openstacksource ]]; then
  old_dir=`pwd`
  cd ./chap08/multiplenodes/m-compute-node
  ln -s ../../../packages/source/ openstacksource
  cd $old_dir
fi

if [[ ! -e ./chap08/multiplenodes/m-compute-node/swift-storage.sh ]]; then
  old_dir=`pwd`
  cd ./chap08/multiplenodes/m-compute-node
  ln -s ../../../chap04/swift-storage.sh swift-storage.sh
  cd $old_dir
fi

if [[ ! -e ./chap08/multiplenodes/m-compute-node/localrc ]]; then
  old_dir=`pwd`
  cd ./chap08/multiplenodes/m-compute-node
  ln -s ../localrc localrc
  cd $old_dir
fi

if [[ ! -e ./chap08/multiplenodes/m-compute-node/templates ]]; then
  old_dir=`pwd`
  cd ./chap08/multiplenodes/m-compute-node
  ln -s ../../../templates/ templates
  cd $old_dir
fi

if [[ ! -e ./chap08/multiplenodes/m-compute-node/nova-compute.sh ]]; then
  old_dir=`pwd`
  cd ./chap08/multiplenodes/m-compute-node
  ln -s ../../../chap08/nova-compute.sh nova-compute.sh
  cd $old_dir
fi

if [[ ! -e ./chap08/multiplenodes/m-compute-node/packages ]]; then
  old_dir=`pwd`
  cd ./chap08/multiplenodes/m-compute-node
  ln -s ../../../packages/ packages
  cd $old_dir
fi

if [[ ! -e ./chap08/multiplenodes/m-compute-node/init.sh ]]; then
  old_dir=`pwd`
  cd ./chap08/multiplenodes/m-compute-node
  ln -s ../../../chap03/mysql/init.sh init.sh
  cd $old_dir
fi

if [[ ! -e ./chap08/multiplenodes/m-compute-node/tools ]]; then
  old_dir=`pwd`
  cd ./chap08/multiplenodes/m-compute-node
  ln -s ../../../tools/ tools
  cd $old_dir
fi

if [[ ! -e ./chap08/multiplenodes/m-compute-node/cinder-volume.sh ]]; then
  old_dir=`pwd`
  cd ./chap08/multiplenodes/m-compute-node
  ln -s ../../../chap07/cinder-volume.sh cinder-volume.sh
  cd $old_dir
fi

if [[ ! -e ./chap08/multiplenodes/m-compute-node/quantum-agent.sh ]]; then
  old_dir=`pwd`
  cd ./chap08/multiplenodes/m-compute-node
  ln -s ../../../chap06/quantum-agent.sh quantum-agent.sh
  cd $old_dir
fi

if [[ ! -e ./chap08/multiplenodes/m-controller/openstacksource ]]; then
  old_dir=`pwd`
  cd ./chap08/multiplenodes/m-controller
  ln -s ../../../packages/source/ openstacksource
  cd $old_dir
fi

if [[ ! -e ./chap08/multiplenodes/m-controller/quantum-server.sh ]]; then
  old_dir=`pwd`
  cd ./chap08/multiplenodes/m-controller
  ln -s ../../../chap06/quantum.sh quantum-server.sh
  cd $old_dir
fi

if [[ ! -e ./chap08/multiplenodes/m-controller/glance.sh ]]; then
  old_dir=`pwd`
  cd ./chap08/multiplenodes/m-controller
  ln -s ../../../chap05/glance-with-swift.sh glance.sh
  cd $old_dir
fi

if [[ ! -e ./chap08/multiplenodes/m-controller/mysql.sh ]]; then
  old_dir=`pwd`
  cd ./chap08/multiplenodes/m-controller
  ln -s ../../../chap03/mysql/mysql.sh mysql.sh
  cd $old_dir
fi

if [[ ! -e ./chap08/multiplenodes/m-controller/nova-api.sh ]]; then
  old_dir=`pwd`
  cd ./chap08/multiplenodes/m-controller
  ln -s ../../../chap08/nova-api.sh nova-api.sh
  cd $old_dir
fi

if [[ ! -e ./chap08/multiplenodes/m-controller/localrc ]]; then
  old_dir=`pwd`
  cd ./chap08/multiplenodes/m-controller
  ln -s ../localrc localrc
  cd $old_dir
fi

if [[ ! -e ./chap08/multiplenodes/m-controller/keystone.sh ]]; then
  old_dir=`pwd`
  cd ./chap08/multiplenodes/m-controller
  ln -s ../../../chap03/keystone/keystone.sh keystone.sh
  cd $old_dir
fi

if [[ ! -e ./chap08/multiplenodes/m-controller/templates ]]; then
  old_dir=`pwd`
  cd ./chap08/multiplenodes/m-controller
  ln -s ../../../templates/ templates
  cd $old_dir
fi

if [[ ! -e ./chap08/multiplenodes/m-controller/cinder-api.sh ]]; then
  old_dir=`pwd`
  cd ./chap08/multiplenodes/m-controller
  ln -s ../../../chap07/cinder.sh cinder-api.sh
  cd $old_dir
fi

if [[ ! -e ./chap08/multiplenodes/m-controller/swift-proxy.sh ]]; then
  old_dir=`pwd`
  cd ./chap08/multiplenodes/m-controller
  ln -s ../../../chap04/swift.sh swift-proxy.sh
  cd $old_dir
fi

if [[ ! -e ./chap08/multiplenodes/m-controller/dashboard.sh ]]; then
  old_dir=`pwd`
  cd ./chap08/multiplenodes/m-controller
  ln -s ../../../chap09/dashboard.sh dashboard.sh
  cd $old_dir
fi

if [[ ! -e ./chap08/multiplenodes/m-controller/packages ]]; then
  old_dir=`pwd`
  cd ./chap08/multiplenodes/m-controller
  ln -s ../../../packages/ packages
  cd $old_dir
fi

if [[ ! -e ./chap08/multiplenodes/m-controller/init.sh ]]; then
  old_dir=`pwd`
  cd ./chap08/multiplenodes/m-controller
  ln -s ../../../chap03/mysql/init.sh init.sh
  cd $old_dir
fi

if [[ ! -e ./chap08/multiplenodes/m-controller/create_http_repo.sh ]]; then
  old_dir=`pwd`
  cd ./chap08/multiplenodes/m-controller
  ln -s ../../../tools/create_http_repo.sh create_http_repo.sh
  cd $old_dir
fi

if [[ ! -e ./chap08/multiplenodes/m-controller/rabbitmq.sh ]]; then
  old_dir=`pwd`
  cd ./chap08/multiplenodes/m-controller
  ln -s ../../../chap03/rabbitmq/rabbitmq.sh rabbitmq.sh
  cd $old_dir
fi

if [[ ! -e ./chap08/multiplenodes/m-controller/tools ]]; then
  old_dir=`pwd`
  cd ./chap08/multiplenodes/m-controller
  ln -s ../../../tools/ tools
  cd $old_dir
fi

if [[ ! -e ./chap08/allinone/glance-with-swift.sh ]]; then
  old_dir=`pwd`
  cd ./chap08/allinone
  ln -s ../../chap05/glance-with-swift.sh glance-with-swift.sh
  cd $old_dir
fi

if [[ ! -e ./chap08/allinone/quantum-api.sh ]]; then
  old_dir=`pwd`
  cd ./chap08/allinone
  ln -s ../../chap06/quantum.sh quantum-api.sh
  cd $old_dir
fi

if [[ ! -e ./chap08/allinone/openstacksource ]]; then
  old_dir=`pwd`
  cd ./chap08/allinone
  ln -s ../../packages/source/ openstacksource
  cd $old_dir
fi

if [[ ! -e ./chap08/allinone/swift-storage.sh ]]; then
  old_dir=`pwd`
  cd ./chap08/allinone
  ln -s ../../chap04/swift-storage.sh swift-storage.sh
  cd $old_dir
fi

if [[ ! -e ./chap08/allinone/mysql.sh ]]; then
  old_dir=`pwd`
  cd ./chap08/allinone
  ln -s ../../chap03/mysql/mysql.sh mysql.sh
  cd $old_dir
fi

if [[ ! -e ./chap08/allinone/nova-api.sh ]]; then
  old_dir=`pwd`
  cd ./chap08/allinone
  ln -s ../../chap08/nova-api.sh nova-api.sh
  cd $old_dir
fi

if [[ ! -e ./chap08/allinone/keystone.sh ]]; then
  old_dir=`pwd`
  cd ./chap08/allinone
  ln -s ../../chap03/keystone/keystone.sh keystone.sh
  cd $old_dir
fi

if [[ ! -e ./chap08/allinone/templates ]]; then
  old_dir=`pwd`
  cd ./chap08/allinone
  ln -s ../../templates/ templates
  cd $old_dir
fi

if [[ ! -e ./chap08/allinone/cinder-api.sh ]]; then
  old_dir=`pwd`
  cd ./chap08/allinone
  ln -s ../../chap07/cinder.sh cinder-api.sh
  cd $old_dir
fi

if [[ ! -e ./chap08/allinone/swift-proxy.sh ]]; then
  old_dir=`pwd`
  cd ./chap08/allinone
  ln -s ../../chap04/swift.sh swift-proxy.sh
  cd $old_dir
fi

if [[ ! -e ./chap08/allinone/nova-compute.sh ]]; then
  old_dir=`pwd`
  cd ./chap08/allinone
  ln -s ../../chap08/nova-compute.sh nova-compute.sh
  cd $old_dir
fi

if [[ ! -e ./chap08/allinone/packages ]]; then
  old_dir=`pwd`
  cd ./chap08/allinone
  ln -s ../../packages/ packages
  cd $old_dir
fi

if [[ ! -e ./chap08/allinone/init.sh ]]; then
  old_dir=`pwd`
  cd ./chap08/allinone
  ln -s ../../chap03/mysql/init.sh init.sh
  cd $old_dir
fi

if [[ ! -e ./chap08/allinone/create_http_repo.sh ]]; then
  old_dir=`pwd`
  cd ./chap08/allinone
  ln -s ../../tools/create_http_repo.sh create_http_repo.sh
  cd $old_dir
fi

if [[ ! -e ./chap08/allinone/rabbitmq.sh ]]; then
  old_dir=`pwd`
  cd ./chap08/allinone
  ln -s ../../chap03/rabbitmq/rabbitmq.sh rabbitmq.sh
  cd $old_dir
fi

if [[ ! -e ./chap08/allinone/tools ]]; then
  old_dir=`pwd`
  cd ./chap08/allinone
  ln -s ../../tools/ tools
  cd $old_dir
fi

if [[ ! -e ./chap08/allinone/cinder-volume.sh ]]; then
  old_dir=`pwd`
  cd ./chap08/allinone
  ln -s ../../chap07/cinder-volume.sh cinder-volume.sh
  cd $old_dir
fi

if [[ ! -e ./chap08/allinone/quantum-agent.sh ]]; then
  old_dir=`pwd`
  cd ./chap08/allinone
  ln -s ../../chap06/quantum-agent.sh quantum-agent.sh
  cd $old_dir
fi

if [[ ! -e ./chap05/glance.sh ]]; then
  old_dir=`pwd`
  cd ./chap05
  ln -s glance-with-swift.sh glance.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/easydeploy/m-compute-node/openstacksource ]]; then
  old_dir=`pwd`
  cd ./chap10/easydeploy/m-compute-node
  ln -s ../../../packages/source/ openstacksource
  cd $old_dir
fi

if [[ ! -e ./chap10/easydeploy/m-compute-node/swift-storage.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/easydeploy/m-compute-node
  ln -s ../../../chap04/swift-storage.sh swift-storage.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/easydeploy/m-compute-node/localrc ]]; then
  old_dir=`pwd`
  cd ./chap10/easydeploy/m-compute-node
  ln -s ../localrc localrc
  cd $old_dir
fi

if [[ ! -e ./chap10/easydeploy/m-compute-node/templates ]]; then
  old_dir=`pwd`
  cd ./chap10/easydeploy/m-compute-node
  ln -s ../../../templates/ templates
  cd $old_dir
fi

if [[ ! -e ./chap10/easydeploy/m-compute-node/nova-compute.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/easydeploy/m-compute-node
  ln -s ../../../chap08/nova-compute.sh nova-compute.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/easydeploy/m-compute-node/packages ]]; then
  old_dir=`pwd`
  cd ./chap10/easydeploy/m-compute-node
  ln -s ../../../packages/ packages
  cd $old_dir
fi

if [[ ! -e ./chap10/easydeploy/m-compute-node/init.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/easydeploy/m-compute-node
  ln -s ../../../chap03/mysql/init.sh init.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/easydeploy/m-compute-node/tools ]]; then
  old_dir=`pwd`
  cd ./chap10/easydeploy/m-compute-node
  ln -s ../../../tools/ tools
  cd $old_dir
fi

if [[ ! -e ./chap10/easydeploy/m-compute-node/cinder-volume.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/easydeploy/m-compute-node
  ln -s ../../../chap07/cinder-volume.sh cinder-volume.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/easydeploy/m-compute-node/quantum-agent.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/easydeploy/m-compute-node
  ln -s ../../../chap06/quantum-agent.sh quantum-agent.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/easydeploy/m-controller/openstacksource ]]; then
  old_dir=`pwd`
  cd ./chap10/easydeploy/m-controller
  ln -s ../../../packages/source/ openstacksource
  cd $old_dir
fi

if [[ ! -e ./chap10/easydeploy/m-controller/quantum-server.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/easydeploy/m-controller
  ln -s ../../../chap06/quantum.sh quantum-server.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/easydeploy/m-controller/glance.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/easydeploy/m-controller
  ln -s ../../../chap05/glance-with-swift.sh glance.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/easydeploy/m-controller/mysql.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/easydeploy/m-controller
  ln -s ../../../chap03/mysql/mysql.sh mysql.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/easydeploy/m-controller/nova-api.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/easydeploy/m-controller
  ln -s ../../../chap08/nova-api.sh nova-api.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/easydeploy/m-controller/localrc ]]; then
  old_dir=`pwd`
  cd ./chap10/easydeploy/m-controller
  ln -s ../localrc localrc
  cd $old_dir
fi

if [[ ! -e ./chap10/easydeploy/m-controller/keystone.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/easydeploy/m-controller
  ln -s ../../../chap03/keystone/keystone.sh keystone.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/easydeploy/m-controller/templates ]]; then
  old_dir=`pwd`
  cd ./chap10/easydeploy/m-controller
  ln -s ../../../templates/ templates
  cd $old_dir
fi

if [[ ! -e ./chap10/easydeploy/m-controller/cinder-api.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/easydeploy/m-controller
  ln -s ../../../chap07/cinder.sh cinder-api.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/easydeploy/m-controller/swift-proxy.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/easydeploy/m-controller
  ln -s ../../../chap04/swift.sh swift-proxy.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/easydeploy/m-controller/dashboard.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/easydeploy/m-controller
  ln -s ../../../chap09/dashboard.sh dashboard.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/easydeploy/m-controller/packages ]]; then
  old_dir=`pwd`
  cd ./chap10/easydeploy/m-controller
  ln -s ../../../packages/ packages
  cd $old_dir
fi

if [[ ! -e ./chap10/easydeploy/m-controller/init.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/easydeploy/m-controller
  ln -s ../../../chap03/mysql/init.sh init.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/easydeploy/m-controller/create_http_repo.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/easydeploy/m-controller
  ln -s ../../../tools/create_http_repo.sh create_http_repo.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/easydeploy/m-controller/rabbitmq.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/easydeploy/m-controller
  ln -s ../../../chap03/rabbitmq/rabbitmq.sh rabbitmq.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/easydeploy/m-controller/tools ]]; then
  old_dir=`pwd`
  cd ./chap10/easydeploy/m-controller
  ln -s ../../../tools/ tools
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/openstacksource ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode
  ln -s ../../packages/source/ openstacksource
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/vm.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode
  ln -s ../../chap03/cloud/vm.sh vm.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-nova-api/openstacksource ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-nova-api
  ln -s ../../../packages/source/ openstacksource
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-nova-api/nova-api.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-nova-api
  ln -s ../../../chap08/nova-api.sh nova-api.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-nova-api/localrc ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-nova-api
  ln -s ../localrc localrc
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-nova-api/templates ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-nova-api
  ln -s ../../../templates/ templates
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-nova-api/init.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-nova-api
  ln -s ../../../chap03/mysql/init.sh init.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-nova-api/tools ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-nova-api
  ln -s ../../../tools/ tools
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-cinder-api/openstacksource ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-cinder-api
  ln -s ../../../packages/source/ openstacksource
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-cinder-api/localrc ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-cinder-api
  ln -s ../localrc localrc
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-cinder-api/templates ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-cinder-api
  ln -s ../../../templates/ templates
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-cinder-api/cinder-api.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-cinder-api
  ln -s ../../../chap07/cinder.sh cinder-api.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-cinder-api/init.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-cinder-api
  ln -s ../../../chap03/mysql/init.sh init.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-cinder-api/tools ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-cinder-api
  ln -s ../../../tools/ tools
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-quantum-api/quantum-api.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-quantum-api
  ln -s ../../../chap06/quantum.sh quantum-api.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-quantum-api/openstacksource ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-quantum-api
  ln -s ../../../packages/source/ openstacksource
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-quantum-api/localrc ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-quantum-api
  ln -s ../localrc localrc
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-quantum-api/templates ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-quantum-api
  ln -s ../../../templates/ templates
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-quantum-api/init.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-quantum-api
  ln -s ../../../chap03/mysql/init.sh init.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-quantum-api/tools ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-quantum-api
  ln -s ../../../tools/ tools
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-rabbitmq/openstacksource ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-rabbitmq
  ln -s ../../../packages/ openstacksource
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-rabbitmq/localrc ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-rabbitmq
  ln -s ../localrc localrc
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-rabbitmq/templates ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-rabbitmq
  ln -s ../../../templates/ templates
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-rabbitmq/init.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-rabbitmq
  ln -s ../../../chap03/mysql/init.sh init.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-rabbitmq/rabbitmq.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-rabbitmq
  ln -s ../../../chap03/rabbitmq/rabbitmq.sh rabbitmq.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-rabbitmq/tools ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-rabbitmq
  ln -s ../../../tools/ tools
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-cinder-volume/openstacksource ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-cinder-volume
  ln -s ../../../packages/source/ openstacksource
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-cinder-volume/localrc ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-cinder-volume
  ln -s ../localrc localrc
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-cinder-volume/templates ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-cinder-volume
  ln -s ../../../templates/ templates
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-cinder-volume/init.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-cinder-volume
  ln -s ../../../chap03/mysql/init.sh init.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-cinder-volume/tools ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-cinder-volume
  ln -s ../../../tools/ tools
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-cinder-volume/cinder-volume.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-cinder-volume
  ln -s ../../../chap07/cinder-volume.sh cinder-volume.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-swift-storage/openstacksource ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-swift-storage
  ln -s ../../../packages/source/ openstacksource
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-swift-storage/swift-storage.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-swift-storage
  ln -s ../../../chap04/swift-storage.sh swift-storage.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-swift-storage/localrc ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-swift-storage
  ln -s ../localrc localrc
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-swift-storage/templates ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-swift-storage
  ln -s ../../../templates/ templates
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-swift-storage/init.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-swift-storage
  ln -s ../../../chap03/mysql/init.sh init.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-swift-storage/tools ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-swift-storage
  ln -s ../../../tools/ tools
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-glance/openstacksource ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-glance
  ln -s ../../../packages/source/ openstacksource
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-glance/glance.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-glance
  ln -s ../../../chap05/glance-with-swift.sh glance.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-glance/localrc ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-glance
  ln -s ../localrc localrc
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-glance/templates ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-glance
  ln -s ../../../templates/ templates
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-glance/init.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-glance
  ln -s ../../../chap03/mysql/init.sh init.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-glance/tools ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-glance
  ln -s ../../../tools/ tools
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/templates ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode
  ln -s ../../templates/ templates
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-nova-compute/openstacksource ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-nova-compute
  ln -s ../../../packages/source/ openstacksource
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-nova-compute/localrc ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-nova-compute
  ln -s ../localrc localrc
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-nova-compute/templates ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-nova-compute
  ln -s ../../../templates/ templates
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-nova-compute/nova-compute.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-nova-compute
  ln -s ../../../chap08/nova-compute.sh nova-compute.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-nova-compute/init.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-nova-compute
  ln -s ../../../chap03/mysql/init.sh init.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-nova-compute/tools ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-nova-compute
  ln -s ../../../tools/ tools
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-nova-compute/quantum-agent.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-nova-compute
  ln -s ../../../chap06/quantum-agent.sh quantum-agent.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-dashboard/openstacksource ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-dashboard
  ln -s ../../../packages/source/ openstacksource
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-dashboard/localrc ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-dashboard
  ln -s ../localrc localrc
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-dashboard/templates ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-dashboard
  ln -s ../../../templates/ templates
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-dashboard/dashboard.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-dashboard
  ln -s ../../../chap09/dashboard.sh dashboard.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-dashboard/init.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-dashboard
  ln -s ../../../chap03/mysql/init.sh init.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-dashboard/tools ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-dashboard
  ln -s ../../../tools/ tools
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/repo-server/localrc ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/repo-server
  ln -s ../localrc localrc
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/repo-server/packages ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/repo-server
  ln -s ../../../packages/ packages
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/repo-server/init.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/repo-server
  ln -s ../../../chap03/mysql/init.sh init.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/repo-server/create_http_repo.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/repo-server
  ln -s ../../../tools/create_http_repo.sh create_http_repo.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/repo-server/tools ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/repo-server
  ln -s ../../../tools/ tools
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-mysql/openstacksource ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-mysql
  ln -s ../../../packages/ openstacksource
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-mysql/mysql.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-mysql
  ln -s ../../../chap03/mysql/mysql.sh mysql.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-mysql/localrc ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-mysql
  ln -s ../localrc localrc
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-mysql/templates ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-mysql
  ln -s ../../../templates/ templates
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-mysql/init.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-mysql
  ln -s ../../../chap03/mysql/init.sh init.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-mysql/tools ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-mysql
  ln -s ../../../tools/ tools
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/packages ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode
  ln -s ../../packages/ packages
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/tools ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode
  ln -s ../../tools/ tools
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-swift-proxy/openstacksource ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-swift-proxy
  ln -s ../../../packages/source/ openstacksource
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-swift-proxy/localrc ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-swift-proxy
  ln -s ../localrc localrc
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-swift-proxy/templates ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-swift-proxy
  ln -s ../../../templates/ templates
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-swift-proxy/swift-proxy.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-swift-proxy
  ln -s ../../../chap04/swift.sh swift-proxy.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-swift-proxy/init.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-swift-proxy
  ln -s ../../../chap03/mysql/init.sh init.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-swift-proxy/tools ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-swift-proxy
  ln -s ../../../tools/ tools
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-keystone/openstacksource ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-keystone
  ln -s ../../../packages/source/ openstacksource
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-keystone/localrc ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-keystone
  ln -s ../localrc localrc
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-keystone/keystone.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-keystone
  ln -s ../../../chap03/keystone/keystone.sh keystone.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-keystone/templates ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-keystone
  ln -s ../../../templates/ templates
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-keystone/init.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-keystone
  ln -s ../../../chap03/mysql/init.sh init.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/multiplenode/m-keystone/tools ]]; then
  old_dir=`pwd`
  cd ./chap10/multiplenode/m-keystone
  ln -s ../../../tools/ tools
  cd $old_dir
fi

if [[ ! -e ./chap10/allinone/glance-with-swift.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/allinone
  ln -s ../../chap05/glance-with-swift.sh glance-with-swift.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/allinone/quantum-api.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/allinone
  ln -s ../../chap06/quantum.sh quantum-api.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/allinone/openstacksource ]]; then
  old_dir=`pwd`
  cd ./chap10/allinone
  ln -s ../../packages/source/ openstacksource
  cd $old_dir
fi

if [[ ! -e ./chap10/allinone/swift-storage.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/allinone
  ln -s ../../chap04/swift-storage.sh swift-storage.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/allinone/mysql.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/allinone
  ln -s ../../chap03/mysql/mysql.sh mysql.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/allinone/nova-api.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/allinone
  ln -s ../../chap08/nova-api.sh nova-api.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/allinone/keystone.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/allinone
  ln -s ../../chap03/keystone/keystone.sh keystone.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/allinone/templates ]]; then
  old_dir=`pwd`
  cd ./chap10/allinone
  ln -s ../../templates/ templates
  cd $old_dir
fi

if [[ ! -e ./chap10/allinone/cinder-api.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/allinone
  ln -s ../../chap07/cinder.sh cinder-api.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/allinone/swift-proxy.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/allinone
  ln -s ../../chap04/swift.sh swift-proxy.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/allinone/nova-compute.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/allinone
  ln -s ../../chap08/nova-compute.sh nova-compute.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/allinone/dashboard.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/allinone
  ln -s ../../chap09/dashboard.sh dashboard.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/allinone/packages ]]; then
  old_dir=`pwd`
  cd ./chap10/allinone
  ln -s ../../packages/ packages
  cd $old_dir
fi

if [[ ! -e ./chap10/allinone/init.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/allinone
  ln -s ../../chap03/mysql/init.sh init.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/allinone/create_http_repo.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/allinone
  ln -s ../../tools/create_http_repo.sh create_http_repo.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/allinone/rabbitmq.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/allinone
  ln -s ../../chap03/rabbitmq/rabbitmq.sh rabbitmq.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/allinone/tools ]]; then
  old_dir=`pwd`
  cd ./chap10/allinone
  ln -s ../../tools/ tools
  cd $old_dir
fi

if [[ ! -e ./chap10/allinone/cinder-volume.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/allinone
  ln -s ../../chap07/cinder-volume.sh cinder-volume.sh
  cd $old_dir
fi

if [[ ! -e ./chap10/allinone/quantum-agent.sh ]]; then
  old_dir=`pwd`
  cd ./chap10/allinone
  ln -s ../../chap06/quantum-agent.sh quantum-agent.sh
  cd $old_dir
fi

if [[ ! -e ./chap04/openstacksource ]]; then
  old_dir=`pwd`
  cd ./chap04
  ln -s ../packages/source/ openstacksource
  cd $old_dir
fi

if [[ ! -e ./chap04/pip ]]; then
  old_dir=`pwd`
  cd ./chap04
  ln -s ../packages/pip/ pip
  cd $old_dir
fi

if [[ ! -e ./chap04/templates ]]; then
  old_dir=`pwd`
  cd ./chap04
  ln -s ../templates/ templates
  cd $old_dir
fi

if [[ ! -e ./chap04/tools ]]; then
  old_dir=`pwd`
  cd ./chap04
  ln -s ../tools/ tools
  cd $old_dir
fi

if [[ ! -e ./chap03/keystone/openstacksource ]]; then
  old_dir=`pwd`
  cd ./chap03/keystone
  ln -s ../../packages/source/ openstacksource
  cd $old_dir
fi

if [[ ! -e ./chap03/keystone/pip ]]; then
  old_dir=`pwd`
  cd ./chap03/keystone
  ln -s ../../packages/pip/ pip
  cd $old_dir
fi

if [[ ! -e ./chap03/keystone/tools ]]; then
  old_dir=`pwd`
  cd ./chap03/keystone
  ln -s ../../tools/ tools
  cd $old_dir
fi

if [[ ! -e ./chap07/openstacksource ]]; then
  old_dir=`pwd`
  cd ./chap07
  ln -s ../packages/source/ openstacksource
  cd $old_dir
fi

if [[ ! -e ./chap07/pip ]]; then
  old_dir=`pwd`
  cd ./chap07
  ln -s ../packages/pip/ pip
  cd $old_dir
fi

if [[ ! -e ./chap07/templates ]]; then
  old_dir=`pwd`
  cd ./chap07
  ln -s ../templates/ templates
  cd $old_dir
fi

if [[ ! -e ./chap07/multiplenode/openstacksource ]]; then
  old_dir=`pwd`
  cd ./chap07/multiplenode
  ln -s ../../packages/source/ openstacksource
  cd $old_dir
fi

if [[ ! -e ./chap07/multiplenode/mysql.sh ]]; then
  old_dir=`pwd`
  cd ./chap07/multiplenode
  ln -s ../../chap03/mysql/mysql.sh mysql.sh
  cd $old_dir
fi

if [[ ! -e ./chap07/multiplenode/keystone.sh ]]; then
  old_dir=`pwd`
  cd ./chap07/multiplenode
  ln -s ../../chap03/keystone/keystone.sh keystone.sh
  cd $old_dir
fi

if [[ ! -e ./chap07/multiplenode/templates ]]; then
  old_dir=`pwd`
  cd ./chap07/multiplenode
  ln -s ../../templates/ templates
  cd $old_dir
fi

if [[ ! -e ./chap07/multiplenode/cinder-api.sh ]]; then
  old_dir=`pwd`
  cd ./chap07/multiplenode
  ln -s ../cinder.sh cinder-api.sh
  cd $old_dir
fi

if [[ ! -e ./chap07/multiplenode/init.sh ]]; then
  old_dir=`pwd`
  cd ./chap07/multiplenode
  ln -s ../../chap03/mysql/init.sh init.sh
  cd $old_dir
fi

if [[ ! -e ./chap07/multiplenode/rabbitmq.sh ]]; then
  old_dir=`pwd`
  cd ./chap07/multiplenode
  ln -s ../../chap03/rabbitmq/rabbitmq.sh rabbitmq.sh
  cd $old_dir
fi

if [[ ! -e ./chap07/multiplenode/tools ]]; then
  old_dir=`pwd`
  cd ./chap07/multiplenode
  ln -s ../../tools/ tools
  cd $old_dir
fi

if [[ ! -e ./chap07/multiplenode/cinder-volume.sh ]]; then
  old_dir=`pwd`
  cd ./chap07/multiplenode
  ln -s ../cinder-volume.sh cinder-volume.sh
  cd $old_dir
fi

if [[ ! -e ./chap07/allinone/openstacksource ]]; then
  old_dir=`pwd`
  cd ./chap07/allinone
  ln -s ../../packages/source/ openstacksource
  cd $old_dir
fi

if [[ ! -e ./chap07/allinone/mysql.sh ]]; then
  old_dir=`pwd`
  cd ./chap07/allinone
  ln -s ../../chap03/mysql/mysql.sh mysql.sh
  cd $old_dir
fi

if [[ ! -e ./chap07/allinone/keystone.sh ]]; then
  old_dir=`pwd`
  cd ./chap07/allinone
  ln -s ../../chap03/keystone/keystone.sh keystone.sh
  cd $old_dir
fi

if [[ ! -e ./chap07/allinone/templates ]]; then
  old_dir=`pwd`
  cd ./chap07/allinone
  ln -s ../../templates/ templates
  cd $old_dir
fi

if [[ ! -e ./chap07/allinone/cinder-api.sh ]]; then
  old_dir=`pwd`
  cd ./chap07/allinone
  ln -s ../cinder.sh cinder-api.sh
  cd $old_dir
fi

if [[ ! -e ./chap07/allinone/init.sh ]]; then
  old_dir=`pwd`
  cd ./chap07/allinone
  ln -s ../../chap03/mysql/init.sh init.sh
  cd $old_dir
fi

if [[ ! -e ./chap07/allinone/rabbitmq.sh ]]; then
  old_dir=`pwd`
  cd ./chap07/allinone
  ln -s ../../chap03/rabbitmq/rabbitmq.sh rabbitmq.sh
  cd $old_dir
fi

if [[ ! -e ./chap07/allinone/tools ]]; then
  old_dir=`pwd`
  cd ./chap07/allinone
  ln -s ../../tools/ tools
  cd $old_dir
fi

if [[ ! -e ./chap07/allinone/cinder-volume.sh ]]; then
  old_dir=`pwd`
  cd ./chap07/allinone
  ln -s ../cinder-volume.sh cinder-volume.sh
  cd $old_dir
fi

if [[ ! -e ./chap07/tools ]]; then
  old_dir=`pwd`
  cd ./chap07
  ln -s ../tools/ tools
  cd $old_dir
fi

if [[ ! -e ./chap06/init.sh ]]; then
  old_dir=`pwd`
  cd ./chap06
  ln -s ../chap03/mysql/init.sh init.sh
  cd $old_dir
fi

if [[ ! -e ./chap06/tools ]]; then
  old_dir=`pwd`
  cd ./chap06
  ln -s ../tools/ tools
  cd $old_dir
fi

if [[ ! -e ./chap05/init.sh ]]; then
  old_dir=`pwd`
  cd ./chap05
  ln -s ../chap03/mysql/init.sh init.sh
  cd $old_dir
fi

if [[ ! -e ./chap05/tools ]]; then
  old_dir=`pwd`
  cd ./chap05
  ln -s ../tools/ tools
  cd $old_dir
fi

if [[ ! -e ./chap09/init.sh ]]; then
  old_dir=`pwd`
  cd ./chap09
  ln -s ../chap03/mysql/init.sh init.sh
  cd $old_dir
fi

if [[ ! -e ./chap09/tools ]]; then
  old_dir=`pwd`
  cd ./chap09
  ln -s ../tools/ tools
  cd $old_dir
fi

if [[ ! -e ./chap04/init.sh ]]; then
  old_dir=`pwd`
  cd ./chap04
  ln -s ../chap03/mysql/init.sh init.sh
  cd $old_dir
fi

if [[ ! -e ./chap03/keystone/mysql.sh ]]; then
  old_dir=`pwd`
  cd ./chap03/keystone
  ln -s ../mysql/mysql.sh mysql.sh
  cd $old_dir
fi

if [[ ! -e ./chap03/keystone/init.sh ]]; then
  old_dir=`pwd`
  cd ./chap03/keystone
  ln -s ../mysql/init.sh init.sh
  cd $old_dir
fi

if [[ ! -e ./chap03/keystone/rabbitmq.sh ]]; then
  old_dir=`pwd`
  cd ./chap03/keystone
  ln -s ../rabbitmq/rabbitmq.sh rabbitmq.sh
  cd $old_dir
fi

if [[ ! -e ./chap03/keystone/tools ]]; then
  old_dir=`pwd`
  cd ./chap03/keystone
  ln -s ../../tools/ tools
  cd $old_dir
fi

if [[ ! -e ./chap03/keystone/mysql-src-ist.sh ]]; then
  old_dir=`pwd`
  cd ./chap03/keystone
  ln -s ../mysql/mysql-src-ist.sh mysql-src-ist.sh
  cd $old_dir
fi

if [[ ! -e ./chap03/rabbitmq/mysql.sh ]]; then
  old_dir=`pwd`
  cd ./chap03/rabbitmq
  ln -s ../mysql/mysql.sh mysql.sh
  cd $old_dir
fi

if [[ ! -e ./chap03/rabbitmq/init.sh ]]; then
  old_dir=`pwd`
  cd ./chap03/rabbitmq
  ln -s ../mysql/init.sh init.sh
  cd $old_dir
fi

if [[ ! -e ./chap03/rabbitmq/tools ]]; then
  old_dir=`pwd`
  cd ./chap03/rabbitmq
  ln -s ../../tools/ tools
  cd $old_dir
fi

if [[ ! -e ./chap03/rabbitmq/mysql-src-ist.sh ]]; then
  old_dir=`pwd`
  cd ./chap03/rabbitmq
  ln -s ../mysql/mysql-src-ist.sh mysql-src-ist.sh
  cd $old_dir
fi

if [[ ! -e ./chap03/mysql/tools ]]; then
  old_dir=`pwd`
  cd ./chap03/mysql
  ln -s ../../tools/ tools
  cd $old_dir
fi

if [[ ! -e ./chap07/init.sh ]]; then
  old_dir=`pwd`
  cd ./chap07
  ln -s ../chap03//mysql/init.sh init.sh
  cd $old_dir
fi

if [[ ! -e ./chap05/tools ]]; then
  old_dir=`pwd`
  cd ./chap05
  ln -s ../tools tools
  cd $old_dir
fi


if [[ ! -e ./chap05/openstacksource ]]; then
  old_dir=`pwd`
  cd ./chap05
  ln -s ../packages/source/ openstacksource
  cd $old_dir
fi


cd $cmd_old_dir
set +o xtrace
