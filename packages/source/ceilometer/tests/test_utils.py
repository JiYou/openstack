# -*- encoding: utf-8 -*-
#
# Copyright © 2012 New Dream Network, LLC (DreamHost)
# Copyright (c) 2013 OpenStack Foundation
#
# Author: Doug Hellmann <doug.hellmann@dreamhost.com>
# All Rights Reserved.
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
"""Tests for ceilometer/utils.py
"""
import decimal
import datetime

from ceilometer.tests import base as tests_base
from ceilometer import utils


def test_recursive_keypairs():
    data = {'a': 'A',
            'b': 'B',
            'nested': {'a': 'A',
                       'b': 'B',
                       },
            }
    pairs = list(utils.recursive_keypairs(data))
    assert pairs == [('a', 'A'),
                     ('b', 'B'),
                     ('nested:a', 'A'),
                     ('nested:b', 'B'),
                     ]


class TestUtils(tests_base.TestCase):
    def test_datetime_to_decimal(self):
        expected = 1356093296.12
        utc_datetime = datetime.datetime.utcfromtimestamp(expected)
        actual = utils.dt_to_decimal(utc_datetime)
        self.assertEqual(float(actual), expected)

    def test_decimal_to_datetime(self):
        expected = 1356093296.12
        dexpected = decimal.Decimal(str(expected))  # Python 2.6 wants str()
        expected_datetime = datetime.datetime.utcfromtimestamp(expected)
        actual_datetime = utils.decimal_to_dt(dexpected)
        self.assertEqual(actual_datetime, expected_datetime)
