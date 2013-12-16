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
"""Base classes for storage engines
"""

import abc
import datetime
import math

from ceilometer.openstack.common import timeutils


def iter_period(start, end, period):
    """Split a time from start to end in periods of a number of seconds. This
    function yield the (start, end) time for each period composing the time
    passed as argument.

    :param start: When the period set start.
    :param end: When the period end starts.
    :param period: The duration of the period.

    """
    period_start = start
    increment = datetime.timedelta(seconds=period)
    for i in xrange(int(math.ceil(
            timeutils.delta_seconds(start, end)
            / float(period)))):
        next_start = period_start + increment
        yield (period_start, next_start)
        period_start = next_start


class StorageEngine(object):
    """Base class for storage engines."""

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def register_opts(self, conf):
        """Register any configuration options used by this engine."""

    @abc.abstractmethod
    def get_connection(self, conf):
        """Return a Connection instance based on the configuration settings."""


class Connection(object):
    """Base class for storage system connections."""

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self, conf):
        """Constructor."""

    @abc.abstractmethod
    def upgrade(self, version=None):
        """Migrate the database to `version` or the most recent version."""

    @abc.abstractmethod
    def record_metering_data(self, data):
        """Write the data to the backend storage system.

        :param data: a dictionary such as returned by
                     ceilometer.meter.meter_message_from_counter

        All timestamps must be naive utc datetime object.
        """

    @abc.abstractmethod
    def get_users(self, source=None):
        """Return an iterable of user id strings.

        :param source: Optional source filter.
        """

    @abc.abstractmethod
    def get_projects(self, source=None):
        """Return an iterable of project id strings.

        :param source: Optional source filter.
        """

    @abc.abstractmethod
    def get_resources(self, user=None, project=None, source=None,
                      start_timestamp=None, end_timestamp=None,
                      metaquery={}, resource=None):
        """Return an iterable of models.Resource instances containing
        resource information.

        :param user: Optional ID for user that owns the resource.
        :param project: Optional ID for project that owns the resource.
        :param source: Optional source filter.
        :param start_timestamp: Optional modified timestamp start range.
        :param end_timestamp: Optional modified timestamp end range.
        :param metaquery: Optional dict with metadata to match on.
        :param resource: Optional resource filter.
        """

    @abc.abstractmethod
    def get_meters(self, user=None, project=None, resource=None, source=None,
                   metaquery={}):
        """Return an iterable of model.Meter instances containing meter
        information.

        :param user: Optional ID for user that owns the resource.
        :param project: Optional ID for project that owns the resource.
        :param resource: Optional resource filter.
        :param source: Optional source filter.
        :param metaquery: Optional dict with metadata to match on.
        """

    @abc.abstractmethod
    def get_samples(self, sample_filter, limit=None):
        """Return an iterable of model.Sample instances.

        :param sample_filter: Filter.
        :param limit: Maximum number of results to return.
        """

    @abc.abstractmethod
    def get_meter_statistics(self, sample_filter, period=None):
        """Return an iterable of model.Statistics instances.

        The filter must have a meter value set.
        """

    @abc.abstractmethod
    def get_alarms(self, name=None, user=None,
                   project=None, enabled=True, alarm_id=None):
        """Yields a lists of alarms that match filters
        """

    @abc.abstractmethod
    def update_alarm(self, alarm):
        """update alarm
        """

    @abc.abstractmethod
    def delete_alarm(self, alarm_id):
        """Delete a alarm
        """

    @abc.abstractmethod
    def clear(self):
        """Clear database."""

    @abc.abstractmethod
    def record_events(self, events):
        """Write the events to the backend storage system.

        :param events: a list of model.Event objects.
        """

    @abc.abstractmethod
    def get_events(self, event_filter):
        """Return an iterable of model.Event objects.
        """
