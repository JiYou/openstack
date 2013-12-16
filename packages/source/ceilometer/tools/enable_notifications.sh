#!/bin/bash
#
# Ceilometer depends on having notifications enabled for all monitored
# services.  This script demonstrates the configuration changes needed
# in order to enable the rabbit notifier for the supported services.

bindir=$(dirname $0)
devstackdir=${bindir}/../../devstack

devstack_funcs=${devstackdir}/functions
if [ ! -f "$devstack_funcs" ]
then
    echo "Could not find $devstack_funcs"
    exit 1
fi
source ${devstack_funcs}

CINDER_CONF=/etc/cinder/cinder.conf
if ! grep -q "notification_driver=cinder.openstack.common.notifier.rabbit_notifier" $CINDER_CONF
then
    echo "notification_driver=cinder.openstack.common.notifier.rabbit_notifier" >> $CINDER_CONF
fi

QUANTUM_CONF=/etc/quantum/quantum.conf
if ! grep -q "notification_driver=quantum.openstack.common.notifier.rabbit_notifier" $QUANTUM_CONF
then
    echo "notification_driver=quantum.openstack.common.notifier.rabbit_notifier" >> $QUANTUM_CONF
fi

# For nova we set both the rabbit notifier and the special ceilometer
# notifier that forces one more poll to happen before an instance is
# removed.
NOVA_CONF=/etc/nova/nova.conf
if ! grep -q "notification_driver=ceilometer.compute.nova_notifier" $NOVA_CONF
then
    echo "notification_driver=ceilometer.compute.nova_notifier" >> $NOVA_CONF
fi
if ! grep -q "notification_driver=nova.openstack.common.notifier.rabbit_notifier" $NOVA_CONF
then
    echo "notification_driver=nova.openstack.common.notifier.rabbit_notifier" >> $NOVA_CONF
fi

# SPECIAL CASE
# Glance does not use the openstack common notifier library,
# so we have to set a different option.
GLANCE_CONF=/etc/glance/glance-api.conf
iniuncomment $GLANCE_CONF DEFAULT notifier_strategy
iniset $GLANCE_CONF DEFAULT notifier_strategy rabbit
