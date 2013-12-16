# -*- encoding: utf-8 -*-
#
# Copyright © 2012 eNovance <licensing@enovance.com>
# Copyright © 2012 Red Hat, Inc
#
# Author: Julien Danjou <julien@danjou.info>
# Author: Eoghan Glynn <eglynn@redhat.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import copy
import datetime

from ceilometer.compute import instance as compute_instance
from ceilometer.compute import plugin
from ceilometer import counter
from ceilometer.openstack.common import log
from ceilometer.openstack.common import timeutils

LOG = log.getLogger(__name__)


def _instance_name(instance):
    """Shortcut to get instance name."""
    return getattr(instance, 'OS-EXT-SRV-ATTR:instance_name', None)


def make_counter_from_instance(instance, name, type, unit, volume):
    return counter.Counter(
        name=name,
        type=type,
        unit=unit,
        volume=volume,
        user_id=instance.user_id,
        project_id=instance.tenant_id,
        resource_id=instance.id,
        timestamp=timeutils.isotime(),
        resource_metadata=compute_instance.get_metadata_from_object(instance),
    )


class InstancePollster(plugin.ComputePollster):

    @staticmethod
    def get_counter_names():
        # Instance type counter is specific because it includes
        # variable. We don't need such format in future
        return ['instance', 'instance:*']

    def get_counters(self, manager, instance):
        yield make_counter_from_instance(instance,
                                         name='instance',
                                         type=counter.TYPE_GAUGE,
                                         unit='instance',
                                         volume=1)
        yield make_counter_from_instance(instance,
                                         name='instance:%s' %
                                         instance.flavor['name'],
                                         type=counter.TYPE_GAUGE,
                                         unit='instance',
                                         volume=1)


class DiskIOPollster(plugin.ComputePollster):

    LOG = log.getLogger(__name__ + '.diskio')

    DISKIO_USAGE_MESSAGE = ' '.join(["DISKIO USAGE:",
                                     "%s %s:",
                                     "read-requests=%d",
                                     "read-bytes=%d",
                                     "write-requests=%d",
                                     "write-bytes=%d",
                                     "errors=%d",
                                     ])

    @staticmethod
    def get_counter_names():
        return ['disk.read.requests',
                'disk.read.bytes',
                'disk.write.requests',
                'disk.write.bytes']

    def get_counters(self, manager, instance):
        instance_name = _instance_name(instance)
        try:
            r_bytes = 0
            r_requests = 0
            w_bytes = 0
            w_requests = 0
            for disk, info in manager.inspector.inspect_disks(instance_name):
                self.LOG.info(self.DISKIO_USAGE_MESSAGE,
                              instance, disk.device, info.read_requests,
                              info.read_bytes, info.write_requests,
                              info.write_bytes, info.errors)
                r_bytes += info.read_bytes
                r_requests += info.read_requests
                w_bytes += info.write_bytes
                w_requests += info.write_requests
            yield make_counter_from_instance(instance,
                                             name='disk.read.requests',
                                             type=counter.TYPE_CUMULATIVE,
                                             unit='request',
                                             volume=r_requests,
                                             )
            yield make_counter_from_instance(instance,
                                             name='disk.read.bytes',
                                             type=counter.TYPE_CUMULATIVE,
                                             unit='B',
                                             volume=r_bytes,
                                             )
            yield make_counter_from_instance(instance,
                                             name='disk.write.requests',
                                             type=counter.TYPE_CUMULATIVE,
                                             unit='request',
                                             volume=w_requests,
                                             )
            yield make_counter_from_instance(instance,
                                             name='disk.write.bytes',
                                             type=counter.TYPE_CUMULATIVE,
                                             unit='B',
                                             volume=w_bytes,
                                             )
        except Exception as err:
            self.LOG.warning('Ignoring instance %s: %s',
                             instance_name, err)
            self.LOG.exception(err)


class CPUPollster(plugin.ComputePollster):

    LOG = log.getLogger(__name__ + '.cpu')

    utilization_map = {}

    def get_cpu_util(self, instance, cpu_info):
        prev_times = self.utilization_map.get(instance.id)
        self.utilization_map[instance.id] = (cpu_info.time,
                                             datetime.datetime.now())
        cpu_util = 0.0
        if prev_times:
            prev_cpu = prev_times[0]
            prev_timestamp = prev_times[1]
            delta = self.utilization_map[instance.id][1] - prev_timestamp
            elapsed = (delta.seconds * (10 ** 6) + delta.microseconds) * 1000
            cores_fraction = 1.0 / cpu_info.number
            # account for cpu_time being reset when the instance is restarted
            time_used = (cpu_info.time - prev_cpu
                         if prev_cpu <= cpu_info.time else cpu_info.time)
            cpu_util = 100 * cores_fraction * time_used / elapsed
        return cpu_util

    @staticmethod
    def get_counter_names():
        return ['cpu', 'cpu_util']

    def get_counters(self, manager, instance):
        self.LOG.info('checking instance %s', instance.id)
        instance_name = _instance_name(instance)
        try:
            cpu_info = manager.inspector.inspect_cpus(instance_name)
            self.LOG.info("CPUTIME USAGE: %s %d",
                          instance.__dict__, cpu_info.time)
            cpu_util = self.get_cpu_util(instance, cpu_info)
            self.LOG.info("CPU UTILIZATION %%: %s %0.2f",
                          instance.__dict__, cpu_util)
            # FIXME(eglynn): once we have a way of configuring which measures
            #                are published to each sink, we should by default
            #                disable publishing this derived measure to the
            #                metering store, only publishing to those sinks
            #                that specifically need it
            yield make_counter_from_instance(instance,
                                             name='cpu_util',
                                             type=counter.TYPE_GAUGE,
                                             unit='%',
                                             volume=cpu_util,
                                             )
            yield make_counter_from_instance(instance,
                                             name='cpu',
                                             type=counter.TYPE_CUMULATIVE,
                                             unit='ns',
                                             volume=cpu_info.time,
                                             )
        except Exception as err:
            self.LOG.error('could not get CPU time for %s: %s',
                           instance.id, err)
            self.LOG.exception(err)


class NetPollster(plugin.ComputePollster):

    LOG = log.getLogger(__name__ + '.net')

    NET_USAGE_MESSAGE = ' '.join(["NETWORK USAGE:", "%s %s:", "read-bytes=%d",
                                  "write-bytes=%d"])

    @staticmethod
    def make_vnic_counter(instance, name, type, unit, volume, vnic_data):
        metadata = copy.copy(vnic_data)
        resource_metadata = dict(zip(metadata._fields, metadata))
        resource_metadata['instance_id'] = instance.id
        resource_metadata['instance_type'] = \
            instance.flavor['id'] if instance.flavor else None

        if vnic_data.fref is not None:
            rid = vnic_data.fref
        else:
            instance_name = _instance_name(instance)
            rid = "%s-%s-%s" % (instance_name, instance.id, vnic_data.name)

        return counter.Counter(
            name=name,
            type=type,
            unit=unit,
            volume=volume,
            user_id=instance.user_id,
            project_id=instance.tenant_id,
            resource_id=rid,
            timestamp=timeutils.isotime(),
            resource_metadata=resource_metadata
        )

    @staticmethod
    def get_counter_names():
        return ['network.incoming.bytes',
                'network.incoming.packets',
                'network.outgoing.bytes',
                'network.outgoing.packets']

    def get_counters(self, manager, instance):
        instance_name = _instance_name(instance)
        self.LOG.info('checking instance %s', instance.id)
        try:
            for vnic, info in manager.inspector.inspect_vnics(instance_name):
                self.LOG.info(self.NET_USAGE_MESSAGE, instance_name,
                              vnic.name, info.rx_bytes, info.tx_bytes)
                yield self.make_vnic_counter(instance,
                                             name='network.incoming.bytes',
                                             type=counter.TYPE_CUMULATIVE,
                                             unit='B',
                                             volume=info.rx_bytes,
                                             vnic_data=vnic,
                                             )
                yield self.make_vnic_counter(instance,
                                             name='network.outgoing.bytes',
                                             type=counter.TYPE_CUMULATIVE,
                                             unit='B',
                                             volume=info.tx_bytes,
                                             vnic_data=vnic,
                                             )
                yield self.make_vnic_counter(instance,
                                             name='network.incoming.packets',
                                             type=counter.TYPE_CUMULATIVE,
                                             unit='packet',
                                             volume=info.rx_packets,
                                             vnic_data=vnic,
                                             )
                yield self.make_vnic_counter(instance,
                                             name='network.outgoing.packets',
                                             type=counter.TYPE_CUMULATIVE,
                                             unit='packet',
                                             volume=info.tx_packets,
                                             vnic_data=vnic,
                                             )
        except Exception as err:
            self.LOG.warning('Ignoring instance %s: %s',
                             instance_name, err)
            self.LOG.exception(err)
