# -*- encoding: utf-8 -*-
#
# Copyright © 2012 New Dream Network, LLC (DreamHost)
#
# Author: Doug Hellmann <doug.hellmann@dreamhost.com>
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
"""Storage backend management
"""


import urlparse

from oslo.config import cfg
from stevedore import driver

from ceilometer.openstack.common import log
from ceilometer import utils
from ceilometer import service


LOG = log.getLogger(__name__)

STORAGE_ENGINE_NAMESPACE = 'ceilometer.storage'

STORAGE_OPTS = [
    cfg.StrOpt('database_connection',
               secret=True,
               default=None,
               help='DEPRECATED - Database connection string',
               ),
]


cfg.CONF.register_opts(STORAGE_OPTS)
cfg.CONF.import_opt('connection',
                    'ceilometer.openstack.common.db.sqlalchemy.session',
                    group='database')


def register_opts(conf):
    """Register any options for the storage system."""
    p = get_engine(conf)
    p.register_opts(conf)


def get_engine(conf):
    """Load the configured engine and return an instance."""
    if conf.database_connection:
        conf.set_override('connection', conf.database_connection,
                          group='database')
    engine_name = urlparse.urlparse(conf.database.connection).scheme
    LOG.debug('looking for %r driver in %r',
              engine_name, STORAGE_ENGINE_NAMESPACE)
    mgr = driver.DriverManager(STORAGE_ENGINE_NAMESPACE,
                               engine_name,
                               invoke_on_load=True)
    return mgr.driver


def get_connection(conf):
    """Return an open connection to the database."""
    engine = get_engine(conf)
    engine.register_opts(conf)
    db = engine.get_connection(conf)
    return db


class SampleFilter(object):
    """Holds the properties for building a query from a meter/sample filter.

    :param user: The sample owner.
    :param project: The sample project.
    :param start: Earliest timestamp to include.
    :param end: Only include samples with timestamp less than this.
    :param resource: Optional filter for resource id.
    :param meter: Optional filter for meter type using the meter name.
    :param source: Optional source filter.
    :param metaquery: Optional filter on the metadata
    """
    def __init__(self, user=None, project=None, start=None, end=None,
                 resource=None, meter=None, source=None, metaquery={}):
        self.user = user
        self.project = project
        self.start = utils.sanitize_timestamp(start)
        self.end = utils.sanitize_timestamp(end)
        self.resource = resource
        self.meter = meter
        self.source = source
        self.metaquery = metaquery


class EventFilter(object):
    """Properties for building an Event query.

    :param start: UTC start datetime (mandatory)
    :param end: UTC end datetime (mandatory)
    :param event_name: the name of the event. None for all.
    :param traits: the trait filter dict, all of which are optional
                    {'key': <key>,
                    't_string': <value>,
                    't_int': <value>,
                    't_datetime': <value>
                    't_float': <value>}
                   currently, only one trait dict is supported.
    """

    def __init__(self, start, end, event_name=None, traits={}):
        self.start = utils.sanitize_timestamp(start)
        self.end = utils.sanitize_timestamp(end)
        self.event_name = event_name
        self.traits = traits


def dbsync():
    service.prepare_service()
    get_connection(cfg.CONF).upgrade()
