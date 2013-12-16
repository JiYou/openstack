# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from sqlalchemy import Boolean, Column, DateTime, ForeignKey
from sqlalchemy import Integer, MetaData, String, Table
from sqlalchemy import Table, Text, Float


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine;
    # bind migrate_engine to your metadata
    meta = MetaData()
    meta.bind = migrate_engine

    compute_nodes = Table('compute_nodes', meta,
        Column('created_at', DateTime(timezone=False)),
        Column('updated_at', DateTime(timezone=False)),
        Column('deleted_at', DateTime(timezone=False)),
        Column('deleted', Boolean(create_constraint=True, name=None)),
        Column('id', Integer(), primary_key=True, nullable=False),
        Column('service_id', Integer(), nullable=False),

        Column('vcpus', Integer(), nullable=False),
        Column('memory_mb', Integer(), nullable=False),
        Column('local_gb', Integer(), nullable=False),
        Column('vcpus_used', Integer(), nullable=False),
        Column('memory_mb_used', Integer(), nullable=False),
        Column('local_gb_used', Integer(), nullable=False),
        Column('disk_available_least', Integer(), default=0),
        Column('free_ram_mb', Integer()),
        Column('free_disk_gb', Integer()),
        Column('current_workload', Integer()),
        Column('cpu_info',
               Text(convert_unicode=False, assert_unicode=None,
                    unicode_error=None, _warn_on_bytestring=False),
               nullable=False),
        Column('cpu_utilization', Float(), default=0.0, nullable=False),
    )

    services = Table(
        'services', meta,
        Column('created_at', DateTime),
        Column('updated_at', DateTime),
        Column('deleted_at', DateTime),
        Column('deleted', Boolean),
        Column('id', Integer, primary_key=True, nullable=False),
        Column('host', String(length=255)),
        Column('binary', String(length=255)),
        Column('topic', String(length=255)),
        Column('report_count', Integer, nullable=False),
        Column('disabled', Boolean),
        Column('availability_zone', String(length=255)),
    )

    try:
        compute_nodes.create()
    except Exception:
        LOG.info(repr(compute_nodes))
        LOG.exception('Exception while creating table')
        meta.drop_all(tables=[compute_nodes])
        raise

    try:
        services.create()
    except Exception:
        LOG.info(repr(services))
        LOG.exception('Exception while creating table')
        meta.drop_all(tables=[services])
        raise

def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine

    compute_nodes = Table('compute_nodes',
                          meta,
                          autoload=True)
    compute_nodes.drop()

    services = Table('services',
                     meta,
                     autoload=True)
    services.drop()
