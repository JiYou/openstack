# -*- encoding: utf-8 -*-
#
# Copyright © 2013 eNovance <licensing@enovance.com>
# Copyright © 2013 Red Hat, Inc.
#
# Author: Mehdi Abaakouk <mehdi.abaakouk@enovance.com>
#         Angus Salkeld <asalkeld@redhat.com>
#
# Licensed under the Apache License, Version 2.0 (the 'License'); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from sqlalchemy import MetaData, Table, Column, Text
from sqlalchemy import Boolean, Integer, String, DateTime, Float

meta = MetaData()

alarm = Table(
    'alarm', meta,
    Column('id', String(255), primary_key=True, index=True),
    Column('enabled', Boolean),
    Column('name', Text()),
    Column('description', Text()),
    Column('timestamp', DateTime(timezone=False)),
    Column('counter_name', String(255), index=True),
    Column('user_id', String(255), index=True),
    Column('project_id', String(255), index=True),
    Column('comparison_operator', String(2)),
    Column('threshold', Float),
    Column('statistic', String(255)),
    Column('evaluation_periods', Integer),
    Column('period', Integer),
    Column('state', String(255)),
    Column('state_timestamp', DateTime(timezone=False)),
    Column('ok_actions', Text()),
    Column('alarm_actions', Text()),
    Column('insufficient_data_actions', Text()),
    Column('matching_metadata', Text()))


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    alarm.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    alarm.drop()
