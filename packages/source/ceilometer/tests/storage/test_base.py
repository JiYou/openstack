# -*- encoding: utf-8 -*-
#
# Copyright © 2013 eNovance
#
# Author: Julien Danjou <julien@danjou.info>
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
import datetime
import math

from ceilometer.storage import base
from ceilometer.tests import base as test_base


class BaseTest(test_base.TestCase):

    def test_iter_period(self):
        times = list(base.iter_period(
            datetime.datetime(2013, 1, 1, 12, 0),
            datetime.datetime(2013, 1, 1, 13, 0),
            60))
        self.assertEqual(len(times), 60)
        self.assertEqual(times[10],
                         (datetime.datetime(2013, 1, 1, 12, 10),
                          datetime.datetime(2013, 1, 1, 12, 11)))
        self.assertEqual(times[21],
                         (datetime.datetime(2013, 1, 1, 12, 21),
                          datetime.datetime(2013, 1, 1, 12, 22)))

    def test_iter_period_bis(self):
        times = list(base.iter_period(
            datetime.datetime(2013, 1, 2, 13, 0),
            datetime.datetime(2013, 1, 2, 14, 0),
            55))
        self.assertEqual(len(times), math.ceil(3600 / 55.0))
        self.assertEqual(times[10],
                         (datetime.datetime(2013, 1, 2, 13, 9, 10),
                          datetime.datetime(2013, 1, 2, 13, 10, 5)))
        self.assertEqual(times[21],
                         (datetime.datetime(2013, 1, 2, 13, 19, 15),
                          datetime.datetime(2013, 1, 2, 13, 20, 10)))
