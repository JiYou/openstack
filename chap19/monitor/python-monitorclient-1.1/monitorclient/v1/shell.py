# Copyright 2010 Jacob Kaplan-Moss

# Copyright 2011 OpenStack LLC.
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

import argparse
import os
import sys
import time

from monitorclient import exceptions
from monitorclient import utils


def _poll_for_status(poll_fn, obj_id, action, final_ok_states,
                     poll_period=5, show_progress=True):
    """Block while an action is being performed, periodically printing
    progress.
    """
    def print_progress(progress):
        if show_progress:
            msg = ('\rInstance %(action)s... %(progress)s%% complete'
                   % dict(action=action, progress=progress))
        else:
            msg = '\rInstance %(action)s...' % dict(action=action)

        sys.stdout.write(msg)
        sys.stdout.flush()

    print
    while True:
        obj = poll_fn(obj_id)
        status = obj.status.lower()
        progress = getattr(obj, 'progress', None) or 0
        if status in final_ok_states:
            print_progress(100)
            print "\nFinished"
            break
        elif status == "error":
            print "\nError %(action)s instance" % locals()
            break
        else:
            print_progress(progress)
            time.sleep(poll_period)


def _find_monitor(cs, monitor):
    """Get a monitor by ID."""
    return utils.find_resource(cs.monitors, monitor)


def _find_monitor_snapshot(cs, snapshot):
    """Get a monitor snapshot by ID."""
    return utils.find_resource(cs.monitor_snapshots, snapshot)


def _find_backup(cs, backup):
    """Get a backup by ID."""
    return utils.find_resource(cs.backups, backup)


def _print_monitor(monitor):
    utils.print_dict(monitor._info)


def _print_monitor_snapshot(snapshot):
    utils.print_dict(snapshot._info)


def _translate_keys(collection, convert):
    for item in collection:
        keys = item.__dict__.keys()
        for from_key, to_key in convert:
            if from_key in keys and to_key not in keys:
                setattr(item, to_key, item._info[from_key])


def _translate_monitor_keys(collection):
    convert = [('displayName', 'display_name'), ('monitorType', 'monitor_type')]
    _translate_keys(collection, convert)


def _translate_monitor_snapshot_keys(collection):
    convert = [('displayName', 'display_name'), ('monitorId', 'monitor_id')]
    _translate_keys(collection, convert)


def _extract_metadata(args):
    metadata = {}
    for metadatum in args.metadata:
        # unset doesn't require a val, so we have the if/else
        if '=' in metadatum:
            (key, value) = metadatum.split('=', 1)
        else:
            key = metadatum
            value = None

        metadata[key] = value
    return metadata


@utils.arg(
    '--all-tenants',
    dest='all_tenants',
    metavar='<0|1>',
    nargs='?',
    type=int,
    const=1,
    default=0,
    help='Display information from all tenants (Admin only).')
@utils.arg(
    '--all_tenants',
    nargs='?',
    type=int,
    const=1,
    help=argparse.SUPPRESS)
@utils.arg(
    '--display-name',
    metavar='<display-name>',
    default=None,
    help='Filter results by display-name')
@utils.arg(
    '--status',
    metavar='<status>',
    default=None,
    help='Filter results by status')
@utils.service_type('monitor')
def do_list(cs, args):
    """List all the monitors."""
    all_tenants = int(os.environ.get("ALL_TENANTS", args.all_tenants))
    search_opts = {
        'all_tenants': all_tenants,
        'display_name': args.display_name,
        'status': args.status,
    }
    monitors = cs.monitors.list(search_opts=search_opts)
    _translate_monitor_keys(monitors)

    # Create a list of servers to which the monitor is attached
    for vol in monitors:
        servers = [s.get('server_id') for s in vol.attachments]
        setattr(vol, 'attached_to', ','.join(map(str, servers)))
    utils.print_list(monitors, ['ID', 'Status', 'Display Name',
                     'Size', 'ServiceManage Type', 'Bootable', 'Attached to'])


@utils.arg('monitor', metavar='<monitor>', help='ID of the monitor.')
@utils.service_type('monitor')
def do_show(cs, args):
    """Show details about a monitor."""
    monitor = _find_monitor(cs, args.monitor)
    _print_monitor(monitor)


@utils.arg('size',
           metavar='<size>',
           type=int,
           help='Size of monitor in GB')
@utils.arg(
    '--snapshot-id',
    metavar='<snapshot-id>',
    default=None,
    help='Create monitor from snapshot id (Optional, Default=None)')
@utils.arg(
    '--snapshot_id',
    help=argparse.SUPPRESS)
@utils.arg(
    '--source-volid',
    metavar='<source-volid>',
    default=None,
    help='Create monitor from monitor id (Optional, Default=None)')
@utils.arg(
    '--source_volid',
    help=argparse.SUPPRESS)
@utils.arg(
    '--image-id',
    metavar='<image-id>',
    default=None,
    help='Create monitor from image id (Optional, Default=None)')
@utils.arg(
    '--image_id',
    help=argparse.SUPPRESS)
@utils.arg(
    '--display-name',
    metavar='<display-name>',
    default=None,
    help='ServiceManage name (Optional, Default=None)')
@utils.arg(
    '--display_name',
    help=argparse.SUPPRESS)
@utils.arg(
    '--display-description',
    metavar='<display-description>',
    default=None,
    help='ServiceManage description (Optional, Default=None)')
@utils.arg(
    '--display_description',
    help=argparse.SUPPRESS)
@utils.arg(
    '--monitor-type',
    metavar='<monitor-type>',
    default=None,
    help='ServiceManage type (Optional, Default=None)')
@utils.arg(
    '--monitor_type',
    help=argparse.SUPPRESS)
@utils.arg(
    '--availability-zone',
    metavar='<availability-zone>',
    default=None,
    help='Availability zone for monitor (Optional, Default=None)')
@utils.arg(
    '--availability_zone',
    help=argparse.SUPPRESS)
@utils.arg('--metadata',
           type=str,
           nargs='*',
           metavar='<key=value>',
           help='Metadata key=value pairs (Optional, Default=None)',
           default=None)
@utils.service_type('monitor')
def do_create(cs, args):
    """Add a new monitor."""

    monitor_metadata = None
    if args.metadata is not None:
        monitor_metadata = _extract_metadata(args)

    monitor = cs.monitors.create(args.size,
                               args.snapshot_id,
                               args.source_volid,
                               args.display_name,
                               args.display_description,
                               args.monitor_type,
                               availability_zone=args.availability_zone,
                               imageRef=args.image_id,
                               metadata=monitor_metadata)
    _print_monitor(monitor)


@utils.arg('monitor', metavar='<monitor>', help='ID of the monitor to delete.')
@utils.service_type('monitor')
def do_delete(cs, args):
    """Remove a monitor."""
    monitor = _find_monitor(cs, args.monitor)
    monitor.delete()


@utils.arg('monitor', metavar='<monitor>', help='ID of the monitor to delete.')
@utils.service_type('monitor')
def do_force_delete(cs, args):
    """Attempt forced removal of a monitor, regardless of its state."""
    monitor = _find_monitor(cs, args.monitor)
    monitor.force_delete()


@utils.arg('monitor', metavar='<monitor>', help='ID of the monitor to rename.')
@utils.arg('display_name', nargs='?', metavar='<display-name>',
           help='New display-name for the monitor.')
@utils.arg('--display-description', metavar='<display-description>',
           help='Optional monitor description. (Default=None)',
           default=None)
@utils.service_type('monitor')
def do_rename(cs, args):
    """Rename a monitor."""
    kwargs = {}
    if args.display_name is not None:
        kwargs['display_name'] = args.display_name
    if args.display_description is not None:
        kwargs['display_description'] = args.display_description
    _find_monitor(cs, args.monitor).update(**kwargs)


@utils.arg('monitor',
           metavar='<monitor>',
           help='ID of the monitor to update metadata on.')
@utils.arg('action',
           metavar='<action>',
           choices=['set', 'unset'],
           help="Actions: 'set' or 'unset'")
@utils.arg('metadata',
           metavar='<key=value>',
           nargs='+',
           default=[],
           help='Metadata to set/unset (only key is necessary on unset)')
@utils.service_type('monitor')
def do_metadata(cs, args):
    """Set or Delete metadata on a monitor."""
    monitor = _find_monitor(cs, args.monitor)
    metadata = _extract_metadata(args)

    if args.action == 'set':
        cs.monitors.set_metadata(monitor, metadata)
    elif args.action == 'unset':
        cs.monitors.delete_metadata(monitor, metadata.keys())


@utils.arg(
    '--all-tenants',
    dest='all_tenants',
    metavar='<0|1>',
    nargs='?',
    type=int,
    const=1,
    default=0,
    help='Display information from all tenants (Admin only).')
@utils.arg(
    '--all_tenants',
    nargs='?',
    type=int,
    const=1,
    help=argparse.SUPPRESS)
@utils.arg(
    '--display-name',
    metavar='<display-name>',
    default=None,
    help='Filter results by display-name')
@utils.arg(
    '--status',
    metavar='<status>',
    default=None,
    help='Filter results by status')
@utils.arg(
    '--monitor-id',
    metavar='<monitor-id>',
    default=None,
    help='Filter results by monitor-id')
@utils.service_type('monitor')
def do_snapshot_list(cs, args):
    """List all the snapshots."""
    all_tenants = int(os.environ.get("ALL_TENANTS", args.all_tenants))
    search_opts = {
        'all_tenants': all_tenants,
        'display_name': args.display_name,
        'status': args.status,
        'monitor_id': args.monitor_id,
    }

    snapshots = cs.monitor_snapshots.list(search_opts=search_opts)
    _translate_monitor_snapshot_keys(snapshots)
    utils.print_list(snapshots,
                     ['ID', 'ServiceManage ID', 'Status', 'Display Name', 'Size'])


@utils.arg('snapshot', metavar='<snapshot>', help='ID of the snapshot.')
@utils.service_type('monitor')
def do_snapshot_show(cs, args):
    """Show details about a snapshot."""
    snapshot = _find_monitor_snapshot(cs, args.snapshot)
    _print_monitor_snapshot(snapshot)


@utils.arg('monitor_id',
           metavar='<monitor-id>',
           help='ID of the monitor to snapshot')
@utils.arg('--force',
           metavar='<True|False>',
           help='Optional flag to indicate whether '
           'to snapshot a monitor even if it\'s '
           'attached to an instance. (Default=False)',
           default=False)
@utils.arg(
    '--display-name',
    metavar='<display-name>',
    default=None,
    help='Optional snapshot name. (Default=None)')
@utils.arg(
    '--display_name',
    help=argparse.SUPPRESS)
@utils.arg(
    '--display-description',
    metavar='<display-description>',
    default=None,
    help='Optional snapshot description. (Default=None)')
@utils.arg(
    '--display_description',
    help=argparse.SUPPRESS)
@utils.service_type('monitor')
def do_snapshot_create(cs, args):
    """Add a new snapshot."""
    snapshot = cs.monitor_snapshots.create(args.monitor_id,
                                          args.force,
                                          args.display_name,
                                          args.display_description)
    _print_monitor_snapshot(snapshot)


@utils.arg('snapshot_id',
           metavar='<snapshot-id>',
           help='ID of the snapshot to delete.')
@utils.service_type('monitor')
def do_snapshot_delete(cs, args):
    """Remove a snapshot."""
    snapshot = _find_monitor_snapshot(cs, args.snapshot_id)
    snapshot.delete()


@utils.arg('snapshot', metavar='<snapshot>', help='ID of the snapshot.')
@utils.arg('display_name', nargs='?', metavar='<display-name>',
           help='New display-name for the snapshot.')
@utils.arg('--display-description', metavar='<display-description>',
           help='Optional snapshot description. (Default=None)',
           default=None)
@utils.service_type('monitor')
def do_snapshot_rename(cs, args):
    """Rename a snapshot."""
    kwargs = {}
    if args.display_name is not None:
        kwargs['display_name'] = args.display_name
    if args.display_description is not None:
        kwargs['display_description'] = args.display_description
    _find_monitor_snapshot(cs, args.snapshot).update(**kwargs)


def _print_monitor_type_list(vtypes):
    utils.print_list(vtypes, ['ID', 'Name'])


def _print_type_and_extra_specs_list(vtypes):
    formatters = {'extra_specs': _print_type_extra_specs}
    utils.print_list(vtypes, ['ID', 'Name', 'extra_specs'], formatters)


@utils.service_type('monitor')
def do_type_list(cs, args):
    """Print a list of available 'monitor types'."""
    vtypes = cs.monitor_types.list()
    _print_monitor_type_list(vtypes)


@utils.service_type('monitor')
def do_extra_specs_list(cs, args):
    """Print a list of current 'monitor types and extra specs' (Admin Only)."""
    vtypes = cs.monitor_types.list()
    _print_type_and_extra_specs_list(vtypes)


@utils.arg('name',
           metavar='<name>',
           help="Name of the new monitor type")
@utils.service_type('monitor')
def do_type_create(cs, args):
    """Create a new monitor type."""
    vtype = cs.monitor_types.create(args.name)
    _print_monitor_type_list([vtype])


@utils.arg('id',
           metavar='<id>',
           help="Unique ID of the monitor type to delete")
@utils.service_type('monitor')
def do_type_delete(cs, args):
    """Delete a specific monitor type"""
    cs.monitor_types.delete(args.id)


@utils.arg('vtype',
           metavar='<vtype>',
           help="Name or ID of the monitor type")
@utils.arg('action',
           metavar='<action>',
           choices=['set', 'unset'],
           help="Actions: 'set' or 'unset'")
@utils.arg('metadata',
           metavar='<key=value>',
           nargs='*',
           default=None,
           help='Extra_specs to set/unset (only key is necessary on unset)')
@utils.service_type('monitor')
def do_type_key(cs, args):
    "Set or unset extra_spec for a monitor type."""
    vtype = _find_monitor_type(cs, args.vtype)

    if args.metadata is not None:
        keypair = _extract_metadata(args)

        if args.action == 'set':
            vtype.set_keys(keypair)
        elif args.action == 'unset':
            vtype.unset_keys(keypair.keys())


def do_endpoints(cs, args):
    """Discover endpoints that get returned from the authenticate services"""
    catalog = cs.client.service_catalog.catalog
    for e in catalog['access']['serviceCatalog']:
        utils.print_dict(e['endpoints'][0], e['name'])


def do_credentials(cs, args):
    """Show user credentials returned from auth"""
    catalog = cs.client.service_catalog.catalog
    utils.print_dict(catalog['access']['user'], "User Credentials")
    utils.print_dict(catalog['access']['token'], "Token")

_quota_resources = ['monitors', 'snapshots', 'gigabytes']


def _quota_show(quotas):
    quota_dict = {}
    for resource in _quota_resources:
        quota_dict[resource] = getattr(quotas, resource, None)
    utils.print_dict(quota_dict)


def _quota_update(manager, identifier, args):
    updates = {}
    for resource in _quota_resources:
        val = getattr(args, resource, None)
        if val is not None:
            updates[resource] = val

    if updates:
        manager.update(identifier, **updates)


@utils.arg('tenant', metavar='<tenant_id>',
           help='UUID of tenant to list the quotas for.')
@utils.service_type('monitor')
def do_quota_show(cs, args):
    """List the quotas for a tenant."""

    _quota_show(cs.quotas.get(args.tenant))


@utils.arg('tenant', metavar='<tenant_id>',
           help='UUID of tenant to list the default quotas for.')
@utils.service_type('monitor')
def do_quota_defaults(cs, args):
    """List the default quotas for a tenant."""

    _quota_show(cs.quotas.defaults(args.tenant))


@utils.arg('tenant', metavar='<tenant_id>',
           help='UUID of tenant to set the quotas for.')
@utils.arg('--monitors',
           metavar='<monitors>',
           type=int, default=None,
           help='New value for the "monitors" quota.')
@utils.arg('--snapshots',
           metavar='<snapshots>',
           type=int, default=None,
           help='New value for the "snapshots" quota.')
@utils.arg('--gigabytes',
           metavar='<gigabytes>',
           type=int, default=None,
           help='New value for the "gigabytes" quota.')
@utils.service_type('monitor')
def do_quota_update(cs, args):
    """Update the quotas for a tenant."""

    _quota_update(cs.quotas, args.tenant, args)


@utils.arg('class_name', metavar='<class>',
           help='Name of quota class to list the quotas for.')
@utils.service_type('monitor')
def do_quota_class_show(cs, args):
    """List the quotas for a quota class."""

    _quota_show(cs.quota_classes.get(args.class_name))


@utils.arg('class_name', metavar='<class>',
           help='Name of quota class to set the quotas for.')
@utils.arg('--monitors',
           metavar='<monitors>',
           type=int, default=None,
           help='New value for the "monitors" quota.')
@utils.arg('--snapshots',
           metavar='<snapshots>',
           type=int, default=None,
           help='New value for the "snapshots" quota.')
@utils.arg('--gigabytes',
           metavar='<gigabytes>',
           type=int, default=None,
           help='New value for the "gigabytes" quota.')
@utils.service_type('monitor')
def do_quota_class_update(cs, args):
    """Update the quotas for a quota class."""

    _quota_update(cs.quota_classes, args.class_name, args)


@utils.service_type('monitor')
def do_absolute_limits(cs, args):
    """Print a list of absolute limits for a user"""
    limits = cs.limits.get().absolute
    columns = ['Name', 'Value']
    utils.print_list(limits, columns)


@utils.service_type('monitor')
def do_rate_limits(cs, args):
    """Print a list of rate limits for a user"""
    limits = cs.limits.get().rate
    columns = ['Verb', 'URI', 'Value', 'Remain', 'Unit', 'Next_Available']
    utils.print_list(limits, columns)


def _print_type_extra_specs(vol_type):
    try:
        return vol_type.get_keys()
    except exceptions.NotFound:
        return "N/A"


def _find_monitor_type(cs, vtype):
    """Get a monitor type by name or ID."""
    return utils.find_resource(cs.monitor_types, vtype)


@utils.arg('monitor_id',
           metavar='<monitor-id>',
           help='ID of the monitor to upload to an image')
@utils.arg('--force',
           metavar='<True|False>',
           help='Optional flag to indicate whether '
           'to upload a monitor even if it\'s '
           'attached to an instance. (Default=False)',
           default=False)
@utils.arg('--container-format',
           metavar='<container-format>',
           help='Optional type for container format '
           '(Default=bare)',
           default='bare')
@utils.arg('--disk-format',
           metavar='<disk-format>',
           help='Optional type for disk format '
           '(Default=raw)',
           default='raw')
@utils.arg('image_name',
           metavar='<image-name>',
           help='Name for created image')
@utils.service_type('monitor')
def do_upload_to_image(cs, args):
    """Upload monitor to image service as image."""
    monitor = _find_monitor(cs, args.monitor_id)
    monitor.upload_to_image(args.force,
                           args.image_name,
                           args.container_format,
                           args.disk_format)


@utils.arg('monitor', metavar='<monitor>',
           help='ID of the monitor to backup.')
@utils.arg('--container', metavar='<container>',
           help='Optional Backup container name. (Default=None)',
           default=None)
@utils.arg('--display-name', metavar='<display-name>',
           help='Optional backup name. (Default=None)',
           default=None)
@utils.arg('--display-description', metavar='<display-description>',
           help='Optional backup description. (Default=None)',
           default=None)
@utils.service_type('monitor')
def do_backup_create(cs, args):
    """Creates a backup."""
    cs.backups.create(args.monitor,
                      args.container,
                      args.display_name,
                      args.display_description)


@utils.arg('backup', metavar='<backup>', help='ID of the backup.')
@utils.service_type('monitor')
def do_backup_show(cs, args):
    """Show details about a backup."""
    backup = _find_backup(cs, args.backup)
    info = dict()
    info.update(backup._info)

    if 'links' in info:
        info.pop('links')

    utils.print_dict(info)


@utils.service_type('monitor')
def do_backup_list(cs, args):
    """List all the backups."""
    backups = cs.backups.list()
    columns = ['ID', 'ServiceManage ID', 'Status', 'Name', 'Size', 'Object Count',
               'Container']
    utils.print_list(backups, columns)


@utils.arg('backup', metavar='<backup>',
           help='ID of the backup to delete.')
@utils.service_type('monitor')
def do_backup_delete(cs, args):
    """Remove a backup."""
    backup = _find_backup(cs, args.backup)
    backup.delete()


@utils.arg('backup', metavar='<backup>',
           help='ID of the backup to restore.')
@utils.arg('--monitor-id', metavar='<monitor-id>',
           help='Optional ID of the monitor to restore to.',
           default=None)
@utils.service_type('monitor')
def do_backup_restore(cs, args):
    """Restore a backup."""
    cs.restores.restore(args.backup,
                        args.monitor_id)
