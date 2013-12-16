# -*- encoding: utf-8 -*-
#
# Author: John Tran <jhtran@att.com>
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

"""
SQLAlchemy models for Ceilometer data.
"""

import json
import urlparse

from oslo.config import cfg
from sqlalchemy import Column, Integer, String, Table, ForeignKey, DateTime
from sqlalchemy import Float, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator, VARCHAR

from ceilometer.openstack.common import timeutils
from ceilometer.storage import models as api_models
from ceilometer import utils

sql_opts = [
    cfg.StrOpt('mysql_engine',
               default='InnoDB',
               help='MySQL engine')
]

cfg.CONF.register_opts(sql_opts)


def table_args():
    engine_name = urlparse.urlparse(cfg.CONF.database.connection).scheme
    if engine_name == 'mysql':
        return {'mysql_engine': cfg.CONF.mysql_engine,
                'mysql_charset': "utf8"}
    return None


class JSONEncodedDict(TypeDecorator):
    "Represents an immutable structure as a json-encoded string."

    impl = VARCHAR

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


class CeilometerBase(object):
    """Base class for Ceilometer Models."""
    __table_args__ = table_args()
    __table_initialized__ = False

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)

    def update(self, values):
        """Make the model object behave like a dict."""
        for k, v in values.iteritems():
            setattr(self, k, v)


Base = declarative_base(cls=CeilometerBase)


sourceassoc = Table('sourceassoc', Base.metadata,
                    Column('meter_id', Integer,
                           ForeignKey("meter.id")),
                    Column('project_id', String(255),
                           ForeignKey("project.id")),
                    Column('resource_id', String(255),
                           ForeignKey("resource.id")),
                    Column('user_id', String(255),
                           ForeignKey("user.id")),
                    Column('source_id', String(255),
                           ForeignKey("source.id")))


class Source(Base):
    __tablename__ = 'source'
    id = Column(String(255), primary_key=True)


class Meter(Base):
    """Metering data."""

    __tablename__ = 'meter'
    id = Column(Integer, primary_key=True)
    counter_name = Column(String(255))
    sources = relationship("Source", secondary=lambda: sourceassoc)
    user_id = Column(String(255), ForeignKey('user.id'))
    project_id = Column(String(255), ForeignKey('project.id'))
    resource_id = Column(String(255), ForeignKey('resource.id'))
    resource_metadata = Column(JSONEncodedDict)
    counter_type = Column(String(255))
    counter_unit = Column(String(255))
    counter_volume = Column(Float(53))
    timestamp = Column(DateTime, default=timeutils.utcnow)
    message_signature = Column(String)
    message_id = Column(String)


class User(Base):
    __tablename__ = 'user'
    id = Column(String(255), primary_key=True)
    sources = relationship("Source", secondary=lambda: sourceassoc)
    resources = relationship("Resource", backref='user')
    meters = relationship("Meter", backref='user')


class Project(Base):
    __tablename__ = 'project'
    id = Column(String(255), primary_key=True)
    sources = relationship("Source", secondary=lambda: sourceassoc)
    resources = relationship("Resource", backref='project')
    meters = relationship("Meter", backref='project')


class Resource(Base):
    __tablename__ = 'resource'
    id = Column(String(255), primary_key=True)
    sources = relationship("Source", secondary=lambda: sourceassoc)
    resource_metadata = Column(JSONEncodedDict)
    user_id = Column(String(255), ForeignKey('user.id'))
    project_id = Column(String(255), ForeignKey('project.id'))
    meters = relationship("Meter", backref='resource')


class Alarm(Base):
    """Define Alarm data."""
    __tablename__ = 'alarm'
    id = Column(String(255), primary_key=True)
    enabled = Column(Boolean)
    name = Column(Text)
    description = Column(Text)
    timestamp = Column(DateTime, default=timeutils.utcnow)
    counter_name = Column(Text)

    user_id = Column(String(255), ForeignKey('user.id'))
    project_id = Column(String(255), ForeignKey('project.id'))

    comparison_operator = Column(String(2))
    threshold = Column(Float)
    statistic = Column(String(255))
    evaluation_periods = Column(Integer)
    period = Column(Integer)

    state = Column(String(255))
    state_timestamp = Column(DateTime, default=timeutils.utcnow)

    ok_actions = Column(JSONEncodedDict)
    alarm_actions = Column(JSONEncodedDict)
    insufficient_data_actions = Column(JSONEncodedDict)

    matching_metadata = Column(JSONEncodedDict)


class UniqueName(Base):
    """Key names should only be stored once.
    """
    __tablename__ = 'unique_name'
    id = Column(Integer, primary_key=True)
    key = Column(String(255), index=True, unique=True)

    def __init__(self, key):
        self.key = key

    def __repr__(self):
        return "<UniqueName: %s>" % self.key


class Event(Base):
    __tablename__ = 'event'
    id = Column(Integer, primary_key=True)
    generated = Column(Float(asdecimal=True), index=True)

    unique_name_id = Column(Integer, ForeignKey('unique_name.id'))
    unique_name = relationship("UniqueName", backref=backref('unique_name',
                               order_by=id))

    def __init__(self, event, generated):
        self.unique_name = event
        self.generated = generated

    def __repr__(self):
        return "<Event %d('Event: %s, Generated: %s')>" % \
               (self.id, self.unique_name, self.generated)


class Trait(Base):
    __tablename__ = 'trait'
    id = Column(Integer, primary_key=True)

    name_id = Column(Integer, ForeignKey('unique_name.id'))
    name = relationship("UniqueName", backref=backref('name', order_by=id))

    t_type = Column(Integer, index=True)
    t_string = Column(String(255), nullable=True, default=None, index=True)
    t_float = Column(Float, nullable=True, default=None, index=True)
    t_int = Column(Integer, nullable=True, default=None, index=True)
    t_datetime = Column(Float(asdecimal=True), nullable=True, default=None,
                        index=True)

    event_id = Column(Integer, ForeignKey('event.id'))
    event = relationship("Event", backref=backref('event', order_by=id))

    _value_map = {api_models.Trait.TEXT_TYPE: 't_string',
                  api_models.Trait.FLOAT_TYPE: 't_float',
                  api_models.Trait.INT_TYPE: 't_int',
                  api_models.Trait.DATETIME_TYPE: 't_datetime'}

    def __init__(self, name, event, t_type, t_string=None, t_float=None,
                 t_int=None, t_datetime=None):
        self.name = name
        self.t_type = t_type
        self.t_string = t_string
        self.t_float = t_float
        self.t_int = t_int
        self.t_datetime = t_datetime
        self.event = event

    def get_value(self):
        if self.t_type == api_models.Trait.INT_TYPE:
            return self.t_int
        if self.t_type == api_models.Trait.FLOAT_TYPE:
            return self.t_float
        if self.t_type == api_models.Trait.DATETIME_TYPE:
            return utils.decimal_to_dt(self.t_datetime)
        if self.t_type == api_models.Trait.TEXT_TYPE:
            return self.t_string
        return None

    def __repr__(self):
        return "<Trait(%s) %d=%s/%s/%s/%s on %s>" % (self.name, self.t_type,
               self.t_string, self.t_float, self.t_int, self.t_datetime,
               self.event)
