# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2011 X.commerce, a business unit of eBay Inc.
# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""Defines interface for DB access.

The underlying driver is loaded as a :class:`LazyPluggable`.

Functions in this module are imported into the monitor.db namespace. Call these
functions from monitor.db namespace, not the monitor.db.api namespace.

All functions in this module return objects that implement a dictionary-like
interface. Currently, many of these objects are sqlalchemy objects that
implement a dictionary interface. However, a future goal is to have all of
these objects be simple dictionaries.


**Related Flags**

:db_backend:  string to lookup in the list of LazyPluggable backends.
              `sqlalchemy` is the only supported backend right now.

:sql_connection:  string specifying the sqlalchemy connection to use, like:
                  `sqlite:///var/lib/monitor/monitor.sqlite`.

:enable_new_services:  when adding a new service to the database, is it in the
                       pool of available servicemanage (Default: True)

"""

from oslo.config import cfg

from monitor import exception
from monitor import flags
from monitor import utils

db_opts = [
    cfg.StrOpt('db_backend',
               default='sqlalchemy',
               help='The backend to use for db'),
    cfg.BoolOpt('enable_new_services',
                default=True,
                help='Services to be added to the available pool on create'),
    cfg.StrOpt('servicemanage_name_template',
               default='servicemanage-%s',
               help='Template string to be used to generate servicemanage names'),
]

FLAGS = flags.FLAGS
FLAGS.register_opts(db_opts)

IMPL = utils.LazyPluggable('db_backend',
                           sqlalchemy='monitor.db.sqlalchemy.api')


class NoMoreTargets(exception.MonitorException):
    """No more available targets"""
    pass


###################


def service_destroy(context, service_id):
    """Destroy the service or raise if it does not exist."""
    return IMPL.service_destroy(context, service_id)


def service_get(context, service_id):
    """Get a service or raise if it does not exist."""
    return IMPL.service_get(context, service_id)


def service_get_by_host_and_topic(context, host, topic):
    """Get a service by host it's on and topic it listens to."""
    return IMPL.service_get_by_host_and_topic(context, host, topic)


def service_get_all(context, disabled=None):
    """Get all services."""
    return IMPL.service_get_all(context, disabled)


def service_get_all_by_topic(context, topic):
    """Get all services for a given topic."""
    return IMPL.service_get_all_by_topic(context, topic)


def service_get_all_by_host(context, host):
    """Get all services for a given host."""
    return IMPL.service_get_all_by_host(context, host)


def service_get_all_bmc_by_host(context, host):
    """Get all compute services for a given host."""
    return IMPL.service_get_all_bmc_by_host(context, host)


def service_get_all_servicemanage_sorted(context):
    """Get all servicemanage services sorted by servicemanage count.

    :returns: a list of (Service, servicemanage_count) tuples.

    """
    return IMPL.service_get_all_servicemanage_sorted(context)


def service_get_by_args(context, host, binary):
    """Get the state of an service by node name and binary."""
    return IMPL.service_get_by_args(context, host, binary)


def service_create(context, values):
    """Create a service from the values dictionary."""
    return IMPL.service_create(context, values)


def service_update(context, service_id, values):
    """Set the given properties on an service and update it.

    Raises NotFound if service does not exist.

    """
    return IMPL.service_update(context, service_id, values)

###################

def compute_node_get(context, compute_id):
    """Get an computeNode or raise if it does not exist."""
    return IMPL.compute_node_get(context, compute_id)


def compute_node_get_all(context):
    """Get all computeNodes."""
    return IMPL.compute_node_get_all(context)


def compute_node_create(context, values):
    """Create a computeNode from the values dictionary."""
    return IMPL.compute_node_create(context, values)


def compute_node_update(context, compute_id, values, auto_adjust=True):
    """Set the given properties on an computeNode and update it.

    Raises NotFound if computeNode does not exist.
    """
    return IMPL.compute_node_update(context, compute_id, values, auto_adjust)


def compute_node_get_by_host(context, host):
    return IMPL.compute_node_get_by_host(context, host)


def compute_node_utilization_update(context, host, free_ram_mb_delta=0,
                          free_disk_gb_delta=0, work_delta=0, vm_delta=0):
    return IMPL.compute_node_utilization_update(context, host,
                          free_ram_mb_delta, free_disk_gb_delta, work_delta,
                          vm_delta)


def compute_node_utilization_set(context, host, free_ram_mb=None,
                                 free_disk_gb=None, work=None, vms=None):
    return IMPL.compute_node_utilization_set(context, host, free_ram_mb,
                                             free_disk_gb, work, vms)


###############
# Monitor Services

def monitor_service_get(context, monitor_service_id, session=None):
    return IMPL.monitor_service_get(context,
                                    monitor_service_id,
                                    session)


def monitor_service_create(context, values, session=None):
    return IMPL.monitor_service_create(context, values, session)


def monitor_service_get_all(context, session=None):
    return IMPL.monitor_service_get_all(context, session)


def monitor_service_update(context, monitor_service_id, values):
    return IMPL.monitor_service_update(context, monitor_service_id, values)


def monitor_service_delete(context, monitor_service_id):
    return IMPL.monitor_service_delete(context, monitor_service_id)
