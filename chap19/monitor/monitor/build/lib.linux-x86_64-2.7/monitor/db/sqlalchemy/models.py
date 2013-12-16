# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2011 X.commerce, a business unit of eBay Inc.
# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# Copyright 2011 Piston Cloud Computing, Inc.
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
"""
SQLAlchemy models for monitor data.
"""

from sqlalchemy import Column, Integer, String, Text, schema, Float
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship, backref, object_mapper

from monitor.db.sqlalchemy.session import get_session

from monitor import exception
from monitor import flags
from monitor.openstack.common import timeutils

from monitor.openstack.common import log as logging
LOG = logging.getLogger(__name__)

import numpy

FLAGS = flags.FLAGS
BASE = declarative_base()


class MonitorBase(object):
    """Base class for Monitor Models."""
    __table_args__ = {'mysql_engine': 'InnoDB'}
    __table_initialized__ = False
    created_at = Column(DateTime, default=timeutils.utcnow)
    updated_at = Column(DateTime, onupdate=timeutils.utcnow)
    deleted_at = Column(DateTime)
    deleted = Column(Boolean, default=False)
    metadata = None

    def save(self, session=None):
        """Save this object."""
        if not session:
            session = get_session()
        session.add(self)
        try:
            session.flush()
        except IntegrityError, e:
            if str(e).endswith('is not unique'):
                raise exception.Duplicate(str(e))
            else:
                raise

    def delete(self, session=None):
        """Delete this object."""
        self.deleted = True
        self.deleted_at = timeutils.utcnow()
        self.save(session=session)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)

    def get(self, key, default=None):
        return getattr(self, key, default)

    def __iter__(self):
        self._i = iter(object_mapper(self).columns)
        return self

    def next(self):
        n = self._i.next().name
        return n, getattr(self, n)

    def update(self, values):
        """Make the model object behave like a dict."""
        for k, v in values.iteritems():
            setattr(self, k, v)

    def iteritems(self):
        """Make the model object behave like a dict.

        Includes attributes from joins."""
        local = dict(self)
        joined = dict([(k, v) for k, v in self.__dict__.iteritems()
                      if not k[0] == '_'])
        local.update(joined)
        return local.iteritems()


class Service(BASE, MonitorBase):
    """Represents a running service on a host."""

    __tablename__ = 'services'
    id = Column(Integer, primary_key=True)
    host = Column(String(255))  # , ForeignKey('hosts.id'))
    binary = Column(String(255))
    topic = Column(String(255))
    report_count = Column(Integer, nullable=False, default=0)
    disabled = Column(Boolean, default=False)
    availability_zone = Column(String(255), default='monitor')


class MonitorService(BASE, MonitorBase):
    """Represents a running service on a host."""

    __tablename__ = 'monitor_services'
    id = Column(Integer, primary_key=True)
    host = Column(String(255))  # , ForeignKey('hosts.id'))
    binary = Column(String(255))
    report_count = Column(Integer, nullable=False, default=0)
    disabled = Column(Boolean, default=False)
    status = Column(String(255))


def register_models():
    """Register Models and create metadata.

    Called from monitor.db.sqlalchemy.__init__ as part of loading the driver,
    it will never need to be called explicitly elsewhere unless the
    connection is lost and needs to be reestablished.
    """
    from sqlalchemy import create_engine
    models = (Service,)
    engine = create_engine(FLAGS.sql_connection, echo=False)
    for model in models:
        model.metadata.create_all(engine)


class ComputeNode(BASE, MonitorBase):
    """Represents a running compute service on a host."""

    __tablename__ = 'compute_nodes'
    id = Column(Integer, primary_key=True)
    service_id = Column(Integer, ForeignKey('services.id'), nullable=True)
    service = relationship(Service,
                           backref=backref('compute_node'),
                           foreign_keys=service_id,
                           primaryjoin='and_('
                                'ComputeNode.service_id == Service.id,'
                                'ComputeNode.deleted == False)')

    vcpus = Column(Integer)
    memory_mb = Column(Integer)
    local_gb = Column(Integer)
    vcpus_used = Column(Integer)
    memory_mb_used = Column(Integer)
    local_gb_used = Column(Integer)

    # Free Ram, amount of activity (resize, migration, boot, etc) and
    # the number of running VM's are a good starting point for what's
    # important when making scheduling decisions.
    #
    # NOTE(sandy): We'll need to make this extensible for other schedulers.
    free_ram_mb = Column(Integer)
    free_disk_gb = Column(Integer)
    current_workload = Column(Integer)

    # Note(masumotok): Expected Strings example:
    #
    # '{"arch":"x86_64",
    #   "model":"Nehalem",
    #   "topology":{"sockets":1, "threads":2, "cores":3},
    #   "features":["tdtscp", "xtpr"]}'
    #
    # Points are "json translatable" and it must have all dictionary keys
    # above, since it is copied from <cpu> tag of getCapabilities()
    # (See libvirt.virtConnection).
    cpu_info = Column(Text, nullable=True)
    disk_available_least = Column(Integer)
    cpu_utilization = Column(Float(), default=0.0)

