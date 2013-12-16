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
"""Simple logging storage backend.
"""

from ceilometer.openstack.common import log
from ceilometer.storage import base

LOG = log.getLogger(__name__)


class LogStorage(base.StorageEngine):
    """Log the data
    """

    def register_opts(self, conf):
        """Register any configuration options used by this engine.
        """

    def get_connection(self, conf):
        """Return a Connection instance based on the configuration settings.
        """
        return Connection(conf)


class Connection(base.Connection):
    """Base class for storage system connections.
    """

    def __init__(self, conf):
        pass

    def upgrade(self, version=None):
        pass

    def clear(self):
        pass

    def record_metering_data(self, data):
        """Write the data to the backend storage system.

        :param data: a dictionary such as returned by
                     ceilometer.meter.meter_message_from_counter
        """
        LOG.info('metering data %s for %s: %s',
                 data['counter_name'],
                 data['resource_id'],
                 data['counter_volume'])

    def get_users(self, source=None):
        """Return an iterable of user id strings.

        :param source: Optional source filter.
        """
        return []

    def get_projects(self, source=None):
        """Return an iterable of project id strings.

        :param source: Optional source filter.
        """
        return []

    def get_resources(self, user=None, project=None, source=None,
                      start_timestamp=None, end_timestamp=None,
                      metaquery={}, resource=None):
        """Return an iterable of dictionaries containing resource information.

        { 'resource_id': UUID of the resource,
          'project_id': UUID of project owning the resource,
          'user_id': UUID of user owning the resource,
          'timestamp': UTC datetime of last update to the resource,
          'metadata': most current metadata for the resource,
          'meter': list of the meters reporting data for the resource,
          }

        :param user: Optional ID for user that owns the resource.
        :param project: Optional ID for project that owns the resource.
        :param source: Optional source filter.
        :param start_timestamp: Optional modified timestamp start range.
        :param end_timestamp: Optional modified timestamp end range.
        :param metaquery: Optional dict with metadata to match on.
        :param resource: Optional resource filter.
        """
        return []

    def get_meters(self, user=None, project=None, resource=None, source=None,
                   limit=None, metaquery={}):
        """Return an iterable of dictionaries containing meter information.

        { 'name': name of the meter,
          'type': type of the meter (guage, counter),
          'resource_id': UUID of the resource,
          'project_id': UUID of project owning the resource,
          'user_id': UUID of user owning the resource,
          }

        :param user: Optional ID for user that owns the resource.
        :param project: Optional ID for project that owns the resource.
        :param resource: Optional resource filter.
        :param source: Optional source filter.
        :param limit: Maximum number of results to return.
        :param metaquery: Optional dict with metadata to match on.
        """
        return []

    def get_samples(self, sample_filter):
        """Return an iterable of samples as created by
        :func:`ceilometer.meter.meter_message_from_counter`.
        """
        return []

    def get_meter_statistics(self, sample_filter, period=None):
        """Return a dictionary containing meter statistics.
        described by the query parameters.

        The filter must have a meter value set.

        { 'min':
          'max':
          'avg':
          'sum':
          'count':
          'period':
          'period_start':
          'period_end':
          'duration':
          'duration_start':
          'duration_end':
          }

        """
        return []

    def get_alarms(self, name=None, user=None,
                   project=None, enabled=True, alarm_id=None):
        """Yields a lists of alarms that match filters
        """
        return []

    def update_alarm(self, alarm):
        """update alarm
        """
        return alarm

    def delete_alarm(self, alarm_id):
        """Delete a alarm
        """

    def record_events(self, events):
        """Write the events.

        :param events: a list of model.Event objects.
        """
        raise NotImplementedError('Events not implemented.')

    def get_events(self, event_filter):
        """Return an iterable of model.Event objects.

        :param event_filter: EventFilter instance
        """
        raise NotImplementedError('Events not implemented.')
