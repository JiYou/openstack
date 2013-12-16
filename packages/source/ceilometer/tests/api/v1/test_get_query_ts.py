# -*- encoding: utf-8 -*-
#
# Copyright © 2012 New Dream Network, LLC (DreamHost)
#
# Author: Steven Berler <steven.berler@dreamhost.com>
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
"""Test the _get_query_timestamps helper function.
"""

import datetime

from ceilometer.api.v1 import blueprint


def test_get_query_timestamps_none_specified():
    result = blueprint._get_query_timestamps()
    expected = {'start_timestamp': None,
                'end_timestamp': None,
                'query_start': None,
                'query_end': None,
                'search_offset': 0,
                }

    assert result == expected


def test_get_query_timestamps_start():
    args = {'start_timestamp': '2012-09-20T12:13:14'}
    result = blueprint._get_query_timestamps(args)
    expected = {'start_timestamp': datetime.datetime(2012, 9, 20, 12, 13, 14),
                'end_timestamp': None,
                'query_start': datetime.datetime(2012, 9, 20, 12, 13, 14),
                'query_end': None,
                'search_offset': 0,
                }

    assert result == expected


def test_get_query_timestamps_end():
    args = {'end_timestamp': '2012-09-20T12:13:14'}
    result = blueprint._get_query_timestamps(args)
    expected = {'end_timestamp': datetime.datetime(2012, 9, 20, 12, 13, 14),
                'start_timestamp': None,
                'query_end': datetime.datetime(2012, 9, 20, 12, 13, 14),
                'query_start': None,
                'search_offset': 0,
                }

    assert result == expected


def test_get_query_timestamps_with_offset():
    args = {'start_timestamp': '2012-09-20T12:13:14',
            'end_timestamp': '2012-09-20T13:24:25',
            'search_offset': '20',
            }
    result = blueprint._get_query_timestamps(args)
    expected = {'query_end': datetime.datetime(2012, 9, 20, 13, 44, 25),
                'query_start': datetime.datetime(2012, 9, 20, 11, 53, 14),
                'end_timestamp': datetime.datetime(2012, 9, 20, 13, 24, 25),
                'start_timestamp': datetime.datetime(2012, 9, 20, 12, 13, 14),
                'search_offset': 20,
                }

    assert result == expected
