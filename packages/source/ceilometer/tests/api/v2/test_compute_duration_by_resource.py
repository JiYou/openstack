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
"""Test listing raw events.
"""

import datetime
import logging

from ceilometer.openstack.common import timeutils
from ceilometer.storage import impl_mongodb
from ceilometer.storage import models
from .base import FunctionalTest

LOG = logging.getLogger(__name__)


class TestComputeDurationByResource(FunctionalTest):

    def setUp(self):
        super(TestComputeDurationByResource, self).setUp()

        # Create events relative to the range and pretend
        # that the intervening events exist.

        self.early1 = datetime.datetime(2012, 8, 27, 7, 0)
        self.early2 = datetime.datetime(2012, 8, 27, 17, 0)

        self.start = datetime.datetime(2012, 8, 28, 0, 0)

        self.middle1 = datetime.datetime(2012, 8, 28, 8, 0)
        self.middle2 = datetime.datetime(2012, 8, 28, 18, 0)

        self.end = datetime.datetime(2012, 8, 28, 23, 59)

        self.late1 = datetime.datetime(2012, 8, 29, 9, 0)
        self.late2 = datetime.datetime(2012, 8, 29, 19, 0)

    def _stub_interval_func(self, func):
        self.stubs.Set(impl_mongodb.Connection,
                       'get_meter_statistics',
                       func)

    def _set_interval(self, start, end):
        def get_interval(ignore_self, event_filter, period):
            assert event_filter.start
            assert event_filter.end
            if (event_filter.start > end or event_filter.end < start):
                return []
            duration_start = max(event_filter.start, start)
            duration_end = min(event_filter.end, end)
            duration = timeutils.delta_seconds(duration_start, duration_end)
            return [
                models.Statistics(
                    min=0,
                    max=0,
                    avg=0,
                    sum=0,
                    count=0,
                    period=None,
                    period_start=None,
                    period_end=None,
                    duration=duration,
                    duration_start=duration_start,
                    duration_end=duration_end,
                )
            ]
        self._stub_interval_func(get_interval)

    def _invoke_api(self):
        return self.get_json('/meters/instance:m1.tiny/statistics',
                             q=[{'field': 'timestamp',
                                 'op': 'ge',
                                 'value': self.start.isoformat()},
                                {'field': 'timestamp',
                                 'op': 'le',
                                 'value': self.end.isoformat()},
                                {'field': 'search_offset',
                                 'value': 10}])

    def test_before_range(self):
        self._set_interval(self.early1, self.early2)
        data = self._invoke_api()
        self.assertEqual(data, [])

    def _assert_times_match(self, actual, expected):
        if actual:
            actual = timeutils.parse_isotime(actual)
        actual = actual.replace(tzinfo=None)
        assert actual == expected

    def test_overlap_range_start(self):
        self._set_interval(self.early1, self.middle1)
        data = self._invoke_api()
        self._assert_times_match(data[0]['duration_start'], self.start)
        self._assert_times_match(data[0]['duration_end'], self.middle1)
        self.assertEqual(data[0]['duration'], 8 * 60 * 60)

    def test_within_range(self):
        self._set_interval(self.middle1, self.middle2)
        data = self._invoke_api()
        self._assert_times_match(data[0]['duration_start'], self.middle1)
        self._assert_times_match(data[0]['duration_end'], self.middle2)
        self.assertEqual(data[0]['duration'], 10 * 60 * 60)

    def test_within_range_zero_duration(self):
        self._set_interval(self.middle1, self.middle1)
        data = self._invoke_api()
        self._assert_times_match(data[0]['duration_start'], self.middle1)
        self._assert_times_match(data[0]['duration_end'], self.middle1)
        self.assertEqual(data[0]['duration'], 0)

    def test_overlap_range_end(self):
        self._set_interval(self.middle2, self.late1)
        data = self._invoke_api()
        self._assert_times_match(data[0]['duration_start'], self.middle2)
        self._assert_times_match(data[0]['duration_end'], self.end)
        self.assertEqual(data[0]['duration'], ((6 * 60) - 1) * 60)

    def test_after_range(self):
        self._set_interval(self.late1, self.late2)
        data = self._invoke_api()
        self.assertEqual(data, [])

    def test_without_end_timestamp(self):
        def get_interval(ignore_self, event_filter, period):
            return [
                models.Statistics(
                    count=0,
                    min=None,
                    max=None,
                    avg=None,
                    duration=None,
                    duration_start=self.late1,
                    duration_end=self.late2,
                    sum=0,
                    period=None,
                    period_start=None,
                    period_end=None,
                )
            ]
        self._stub_interval_func(get_interval)
        data = self.get_json('/meters/instance:m1.tiny/statistics',
                             q=[{'field': 'timestamp',
                                 'op': 'ge',
                                 'value': self.late1.isoformat()},
                                {'field': 'resource_id',
                                 'value': 'resource-id'},
                                {'field': 'search_offset',
                                 'value': 10}])
        self._assert_times_match(data[0]['duration_start'], self.late1)
        self._assert_times_match(data[0]['duration_end'], self.late2)

    def test_without_start_timestamp(self):
        def get_interval(ignore_self, event_filter, period):
            return [
                models.Statistics(
                    count=0,
                    min=None,
                    max=None,
                    avg=None,
                    duration=None,
                    duration_start=self.early1,
                    duration_end=self.early2,
                    #
                    sum=0,
                    period=None,
                    period_start=None,
                    period_end=None,
                )
            ]
            return (self.early1, self.early2)
        self._stub_interval_func(get_interval)
        data = self.get_json('/meters/instance:m1.tiny/statistics',
                             q=[{'field': 'timestamp',
                                 'op': 'le',
                                 'value': self.early2.isoformat()},
                                {'field': 'resource_id',
                                 'value': 'resource-id'},
                                {'field': 'search_offset',
                                 'value': 10}])
        self._assert_times_match(data[0]['duration_start'], self.early1)
        self._assert_times_match(data[0]['duration_end'], self.early2)
