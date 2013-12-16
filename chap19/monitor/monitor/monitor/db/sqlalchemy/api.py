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

"""Implementation of SQLAlchemy backend."""

import datetime
import uuid
import warnings
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import literal_column
from sqlalchemy.sql.expression import desc
from sqlalchemy.sql import func

from monitor.common import sqlalchemyutils
from monitor import db
from monitor.db.sqlalchemy import models
from monitor.db.sqlalchemy.session import get_session
from monitor import exception
from monitor import flags
from monitor.openstack.common import log as logging
from monitor.openstack.common import timeutils
from monitor.openstack.common import uuidutils


FLAGS = flags.FLAGS

LOG = logging.getLogger(__name__)


def is_admin_context(context):
    """Indicates if the request context is an administrator."""
    if not context:
        warnings.warn(_('Use of empty request context is deprecated'),
                      DeprecationWarning)
        raise Exception('die')
    return context.is_admin


def is_user_context(context):
    """Indicates if the request context is a normal user."""
    if not context:
        return False
    if context.is_admin:
        return False
    if not context.user_id or not context.project_id:
        return False
    return True


def authorize_project_context(context, project_id):
    """Ensures a request has permission to access the given project."""
    if is_user_context(context):
        if not context.project_id:
            raise exception.NotAuthorized()
        elif context.project_id != project_id:
            raise exception.NotAuthorized()


def authorize_user_context(context, user_id):
    """Ensures a request has permission to access the given user."""
    if is_user_context(context):
        if not context.user_id:
            raise exception.NotAuthorized()
        elif context.user_id != user_id:
            raise exception.NotAuthorized()


def authorize_quota_class_context(context, class_name):
    """Ensures a request has permission to access the given quota class."""
    if is_user_context(context):
        if not context.quota_class:
            raise exception.NotAuthorized()
        elif context.quota_class != class_name:
            raise exception.NotAuthorized()


def require_admin_context(f):
    """Decorator to require admin request context.

    The first argument to the wrapped function must be the context.

    """

    def wrapper(*args, **kwargs):
        if not is_admin_context(args[0]):
            raise exception.AdminRequired()
        return f(*args, **kwargs)
    return wrapper


def require_context(f):
    """Decorator to require *any* user or admin context.

    This does no authorization for user or project access matching, see
    :py:func:`authorize_project_context` and
    :py:func:`authorize_user_context`.

    The first argument to the wrapped function must be the context.

    """

    def wrapper(*args, **kwargs):
        if not is_admin_context(args[0]) and not is_user_context(args[0]):
            raise exception.NotAuthorized()
        return f(*args, **kwargs)
    return wrapper


def model_query(context, *args, **kwargs):
    """Query helper that accounts for context's `read_deleted` field.

    :param context: context to query under
    :param session: if present, the session to use
    :param read_deleted: if present, overrides context's read_deleted field.
    :param project_only: if present and context is user-type, then restrict
            query to match the context's project_id.
    """
    session = kwargs.get('session') or get_session()
    read_deleted = kwargs.get('read_deleted') or context.read_deleted
    project_only = kwargs.get('project_only')

    query = session.query(*args)

    if read_deleted == 'no':
        query = query.filter_by(deleted=False)
    elif read_deleted == 'yes':
        pass  # omit the filter to include deleted and active
    elif read_deleted == 'only':
        query = query.filter_by(deleted=True)
    else:
        raise Exception(
            _("Unrecognized read_deleted value '%s'") % read_deleted)

    if project_only and is_user_context(context):
        query = query.filter_by(project_id=context.project_id)

    return query


def exact_filter(query, model, filters, legal_keys):
    """Applies exact match filtering to a query.

    Returns the updated query.  Modifies filters argument to remove
    filters consumed.

    :param query: query to apply filters to
    :param model: model object the query applies to, for IN-style
                  filtering
    :param filters: dictionary of filters; values that are lists,
                    tuples, sets, or frozensets cause an 'IN' test to
                    be performed, while exact matching ('==' operator)
                    is used for other values
    :param legal_keys: list of keys to apply exact filtering to
    """

    filter_dict = {}

    # Walk through all the keys
    for key in legal_keys:
        # Skip ones we're not filtering on
        if key not in filters:
            continue

        # OK, filtering on this key; what value do we search for?
        value = filters.pop(key)

        if isinstance(value, (list, tuple, set, frozenset)):
            # Looking for values in a list; apply to query directly
            column_attr = getattr(model, key)
            query = query.filter(column_attr.in_(value))
        else:
            # OK, simple exact match; save for later
            filter_dict[key] = value

    # Apply simple exact matches
    if filter_dict:
        query = query.filter_by(**filter_dict)

    return query


###################


@require_admin_context
def service_destroy(context, service_id):
    session = get_session()
    with session.begin():
        service_ref = service_get(context, service_id, session=session)
        service_ref.delete(session=session)


@require_admin_context
def service_get(context, service_id, session=None):
    result = model_query(
        context,
        models.Service,
        session=session).\
        filter_by(id=service_id).\
        first()
    if not result:
        raise exception.ServiceNotFound(service_id=service_id)

    return result


@require_admin_context
def service_get_all(context, disabled=None):
    query = model_query(context, models.Service)
    if disabled is not None:
        query = query.filter_by(disabled=disabled)

    return query.all()


@require_admin_context
def service_get_all_by_topic(context, topic):
    return model_query(
        context, models.Service, read_deleted="no").\
        filter_by(disabled=False).\
        filter_by(topic=topic).\
        all()


@require_admin_context
def service_get_by_host_and_topic(context, host, topic):
    result = model_query(
        context, models.Service, read_deleted="no").\
        filter_by(disabled=False).\
        filter_by(host=host).\
        filter_by(topic=topic).\
        first()
    if not result:
        raise exception.ServiceNotFound(service_id=None)
    return result


@require_admin_context
def service_get_all_by_host(context, host):
    return model_query(
        context, models.Service, read_deleted="no").\
        filter_by(host=host).\
        all()

@require_admin_context
def service_get_all_bmc_by_host(context, host):
    result = model_query(context, models.Service, read_deleted="no").\
                options(joinedload('compute_node')).\
                filter_by(host=host).\
                filter_by(topic="monitor-bmc").\
                all()

    if not result:
        raise exception.MonitorHostNotFound(host=host)

    return result


@require_admin_context
def _service_get_all_topic_subquery(context, session, topic, subq, label):
    sort_value = getattr(subq.c, label)
    return model_query(context, models.Service,
                       func.coalesce(sort_value, 0),
                       session=session, read_deleted="no").\
        filter_by(topic=topic).\
        filter_by(disabled=False).\
        outerjoin((subq, models.Service.host == subq.c.host)).\
        order_by(sort_value).\
        all()


@require_admin_context
def service_get_all_servicemanage_sorted(context):
    session = get_session()
    with session.begin():
        topic = FLAGS.servicemanage_topic
        label = 'servicemanage_gigabytes'
        subq = model_query(context, models.ServiceManage.host,
                           func.sum(models.ServiceManage.size).label(label),
                           session=session, read_deleted="no").\
            group_by(models.ServiceManage.host).\
            subquery()
        return _service_get_all_topic_subquery(context,
                                               session,
                                               topic,
                                               subq,
                                               label)


@require_admin_context
def service_get_by_args(context, host, binary):
    result = model_query(context, models.Service).\
        filter_by(host=host).\
        filter_by(binary=binary).\
        first()

    if not result:
        raise exception.HostBinaryNotFound(host=host, binary=binary)

    return result


@require_admin_context
def service_create(context, values):
    service_ref = models.Service()
    service_ref.update(values)
    if not FLAGS.enable_new_services:
        service_ref.disabled = True
    service_ref.save()
    return service_ref


@require_admin_context
def service_update(context, service_id, values):
    session = get_session()
    with session.begin():
        service_ref = service_get(context, service_id, session=session)
        service_ref.update(values)
        service_ref.save(session=session)


###################
def convert_datetimes(values, *datetime_keys):
    for key in values:
        if key in datetime_keys and isinstance(values[key], basestring):
            values[key] = timeutils.parse_strtime(values[key])
    return values

@require_admin_context
def compute_node_get(context, compute_id, session=None):
    result = model_query(context, models.ComputeNode, session=session).\
                     filter_by(id=compute_id).\
                     first()

    if not result:
        raise exception.MonitorHostNotFound(host=compute_id)

    return result


@require_admin_context
def compute_node_get_all(context, session=None):
    return model_query(context, models.ComputeNode, session=session).\
                    options(joinedload('service')).\
                    all()


def _get_host_utilization(context, host, ram_mb, disk_gb):
    """Compute the current utilization of a given host."""
    instances = instance_get_all_by_host(context, host)
    vms = len(instances)
    free_ram_mb = ram_mb - FLAGS.reserved_host_memory_mb
    free_disk_gb = disk_gb - (FLAGS.reserved_host_disk_mb * 1024)

    work = 0
    for instance in instances:
        free_ram_mb -= instance.memory_mb
        free_disk_gb -= instance.root_gb
        free_disk_gb -= instance.ephemeral_gb
        if instance.vm_state in [vm_states.BUILDING, vm_states.REBUILDING,
                                 vm_states.MIGRATING, vm_states.RESIZING]:
            work += 1
    return dict(free_ram_mb=free_ram_mb,
                free_disk_gb=free_disk_gb,
                current_workload=work,
                running_vms=vms)


def _adjust_compute_node_values_for_utilization(context, values, session):
    service_ref = service_get(context, values['service_id'], session=session)
    host = service_ref['host']
    ram_mb = values['memory_mb']
    disk_gb = values['local_gb']
    #values.update(_get_host_utilization(context, host, ram_mb, disk_gb))


@require_admin_context
def compute_node_create(context, values, session=None):
    """Creates a new ComputeNode and populates the capacity fields
    with the most recent data."""
    if not session:
        session = get_session()

    _adjust_compute_node_values_for_utilization(context, values, session)
    with session.begin(subtransactions=True):
        compute_node_ref = models.ComputeNode()
        session.add(compute_node_ref)
        compute_node_ref.update(values)
    return compute_node_ref


@require_admin_context
def compute_node_update(context, compute_id, values, auto_adjust):
    """Creates a new ComputeNode and populates the capacity fields
    with the most recent data."""
    session = get_session()
    if auto_adjust:
        _adjust_compute_node_values_for_utilization(context, values, session)
    with session.begin(subtransactions=True):
        values['updated_at'] = timeutils.utcnow()
        convert_datetimes(values, 'created_at', 'deleted_at', 'updated_at')
        compute_ref = compute_node_get(context, compute_id, session=session)
        for (key, value) in values.iteritems():
            compute_ref[key] = value
        compute_ref.save(session=session)


def compute_node_get_by_host(context, host):
    """Get all capacity entries for the given host."""
    session = get_session()
    with session.begin():
        service = session.query(models.Service).\
                            filter_by(host=host, binary="monitor-bmc").first()
        node = session.query(models.ComputeNode).\
                             options(joinedload('service')).\
                             filter_by(deleted=False,service_id=service.id)
        return node.first()


def compute_node_utilization_update(context, host, free_ram_mb_delta=0,
                          free_disk_gb_delta=0, work_delta=0, vm_delta=0):
    """Update a specific ComputeNode entry by a series of deltas.
    Do this as a single atomic action and lock the row for the
    duration of the operation. Requires that ComputeNode record exist."""
    session = get_session()
    compute_node = None
    with session.begin(subtransactions=True):
        compute_node = session.query(models.ComputeNode).\
                              options(joinedload('service')).\
                              filter(models.Service.host == host).\
                              filter_by(deleted=False).\
                              with_lockmode('update').\
                              first()
        if compute_node is None:
            raise exception.NotFound(_("No ComputeNode for %(host)s") %
                                     locals())

        # This table thingy is how we get atomic UPDATE x = x + 1
        # semantics.
        table = models.ComputeNode.__table__
        if free_ram_mb_delta != 0:
            compute_node.free_ram_mb = table.c.free_ram_mb + free_ram_mb_delta
        if free_disk_gb_delta != 0:
            compute_node.free_disk_gb = (table.c.free_disk_gb +
                                         free_disk_gb_delta)
        if work_delta != 0:
            compute_node.current_workload = (table.c.current_workload +
                                             work_delta)
        if vm_delta != 0:
            compute_node.running_vms = table.c.running_vms + vm_delta
    return compute_node


def compute_node_utilization_set(context, host, free_ram_mb=None,
                                 free_disk_gb=None, work=None, vms=None):
    """Like compute_node_utilization_update() modify a specific host
    entry. But this function will set the metrics absolutely
    (vs. a delta update).
    """
    session = get_session()
    compute_node = None
    with session.begin(subtransactions=True):
        compute_node = session.query(models.ComputeNode).\
                              options(joinedload('service')).\
                              filter(models.Service.host == host).\
                              filter_by(deleted=False).\
                              with_lockmode('update').\
                              first()
        if compute_node is None:
            raise exception.NotFound(_("No ComputeNode for %(host)s") %
                                     locals())

        if free_ram_mb != None:
            compute_node.free_ram_mb = free_ram_mb
        if free_disk_gb != None:
            compute_node.free_disk_gb = free_disk_gb
        if work != None:
            compute_node.current_workload = work
        if vms != None:
            compute_node.running_vms = vms

    return compute_node

# Operations on monitor_services table.
@require_admin_context
def monitor_service_get(context, monitor_service_id, session=None):
    result = model_query(context, models.MonitorService, session=session).\
                     filter_by(id=monitor_service_id).\
                     first()

    if not result:
        raise exception.MonitorServiceNotFound(
                            monitor_service=monitor_service_id)

    return result

@require_admin_context
def monitor_service_get_all(context, session=None):
    return model_query(context, models.MonitorService, session=session).\
                    all()


@require_admin_context
def monitor_service_create(context, values, session=None):
    if not session:
        session = get_session()

    with session.begin(subtransactions=True):
        monitor_service_ref = models.MonitorService()
        session.add(monitor_service_ref)
        monitor_service_ref.update(values)

    return monitor_service_ref

@require_admin_context
def monitor_service_update(context, monitor_service_id, values):
    session = get_session()
    monitor_service_ref = None
    with session.begin(subtransactions=True):
        values['updated_at'] = timeutils.utcnow()
        convert_datetimes(values, 'created_at', 'deleted_at', 'updated_at')
        monitor_service_ref = monitor_service_get(
                                   context,
                                   monitor_service_id,
                                   session=session)

        if monitor_service_ref is None:
            msg = "No Service Monitored with %s" % monitor_service_id
            raise exception.NotFound(msg)

        for (key, value) in values.iteritems():
            monitor_service_ref[key] = value
        monitor_service_ref.save(session=session)

    return monitor_service_ref


@require_admin_context
def monitor_service_delete(context, monitor_service_id):
    session = get_session()

    with session.begin(subtransactions=True):
        monitor_service_ref = monitor_service_get(context,
                                                  monitor_service_id,
                                                  session=session)

        if monitor_service_ref is None:
            msg = "No Service Monitored with %s" % monitor_service_id
            raise exception.NotFound(msg)

        monitor_service_ref['deleted_at'] = timeutils.utcnow()
        monitor_service_ref['updated_at'] = monitor_service_ref['deleted_at']
        monitor_service_ref['deleted'] = True
        convert_datetimes(monitor_service_ref,
                          'created_at',
                          'deleted_at',
                          'updated_at')

        monitor_service_ref.save(session=session)
