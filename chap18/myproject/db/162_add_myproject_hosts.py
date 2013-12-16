# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack Foundation
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

from sqlalchemy import Column, DateTime
from sqlalchemy import Boolean, Float, MetaData, Integer, String, Table

from nova.openstack.common import log as logging

LOG = logging.getLogger(__name__)


def upgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine

    # Create new table
    myproject_hosts = Table('myproject_hosts', meta,
            Column('created_at', DateTime(timezone=False)),
            Column('updated_at', DateTime(timezone=False)),
            Column('deleted_at', DateTime(timezone=False)),
            Column('deleted', Boolean(create_constraint=True, name=None)),
            Column('id', Integer(), primary_key=True, nullable=False),
            Column('host_name', String(36), nullable=False),
            Column('cpu_usage', Float()),
            mysql_engine='InnoDB',
            mysql_charset='utf8'
    )

    try:
        myproject_hosts.create()
    except Exception:
        LOG.exception("Exception while creating table 'myproject_hosts'")
        meta.drop_all(tables=[myproject_hosts])
        raise


def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine

    myproject_hosts = Table('myproject_hosts', meta, autoload=True)
    try:
        myproject_hosts.drop()
    except Exception:
        LOG.error(_("myproject_hosts table not dropped"))
        raise
