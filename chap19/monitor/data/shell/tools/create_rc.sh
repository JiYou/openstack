#!/bin/bash

if [[ ! $# -eq 1 ]]; then
    echo "Usage: ./create_rc.sh PATH_OF_localrc"
    exit 0
fi


source $1

function _template() {
    mkdir -p ~/rc
    cat <<"EOF" >~/rc/template
export OS_TENANT_NAME=%TENANT_NAME%
export OS_USERNAME=%USER_NAME%
export OS_PASSWORD=%PASSWORD%
export OS_AUTH_URL="http://%KEYSTONE_HOST%:5000/v2.0/"
EOF
    sed -i "s,%KEYSTONE_HOST%,$KEYSTONE_HOST,g" ~/rc/template
}


function _keystone_rc() {
    cp -rf ~/rc/template ~/rc/keystonerc
    sed -i "s,%TENANT_NAME%,admin,g" ~/rc/keystonerc
    sed -i "s,%USER_NAME%,admin,g" ~/rc/keystonerc
    sed -i "s,%PASSWORD%,$ADMIN_PASSWORD,g" ~/rc/keystonerc

    echo "export SERVICE_TOKEN=$ADMIN_TOKEN" > ~/rc/adminrc
    echo "export SERVICE_ENDPOINT=http://$KEYSTONE_HOST:35357/v2.0" >> \
            ~/rc/adminrc
}

function _swift_rc() {
    cp -rf ~/rc/template ~/rc/swiftrc
    sed -i "s,%TENANT_NAME%,service,g" ~/rc/swiftrc
    sed -i "s,%USER_NAME%,swift,g" ~/rc/swiftrc
    sed -i "s,%PASSWORD%,$KEYSTONE_SWIFT_SERVICE_PASSWORD,g" ~/rc/swiftrc
}

function _glance_rc() {
    cp -rf ~/rc/template ~/rc/glancerc
    sed -i "s,%TENANT_NAME%,service,g" ~/rc/glancerc
    sed -i "s,%USER_NAME%,glance,g" ~/rc/glancerc
    sed -i "s,%PASSWORD%,$KEYSTONE_GLANCE_SERVICE_PASSWORD,g" ~/rc/glancerc
}

function _cinder_rc() {
    cp -rf ~/rc/template ~/rc/cinderrc
    sed -i "s,%TENANT_NAME%,service,g" ~/rc/cinderrc
    sed -i "s,%USER_NAME%,cinder,g" ~/rc/cinderrc
    sed -i "s,%PASSWORD%,$KEYSTONE_CINDER_SERVICE_PASSWORD,g" ~/rc/cinderrc
}

function _quantum_rc() {
    cp -rf ~/rc/template ~/rc/quantumrc
    sed -i "s,%TENANT_NAME%,service,g" ~/rc/quantumrc
    sed -i "s,%USER_NAME%,quantum,g" ~/rc/quantumrc
    sed -i "s,%PASSWORD%,$KEYSTONE_QUANTUM_SERVICE_PASSWORD,g" ~/rc/quantumrc
}

function _nova_rc() {
    cp -rf ~/rc/template ~/rc/novarc
    sed -i "s,%TENANT_NAME%,service,g" ~/rc/novarc
    sed -i "s,%USER_NAME%,nova,g" ~/rc/novarc
    sed -i "s,%PASSWORD%,$KEYSTONE_NOVA_SERVICE_PASSWORD,g" ~/rc/novarc
}
_template
_keystone_rc
_swift_rc
_glance_rc
_cinder_rc
_quantum_rc
_nova_rc
