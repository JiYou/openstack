# -*- encoding: utf-8 -*-
#
# Copyright © 2013 New Dream Network, LLC (DreamHost)
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

from ceilometer.storage import models
from ceilometer.tests import base


class FakeModel(models.Model):
    def __init__(self, arg1, arg2):
        models.Model.__init__(self, arg1=arg1, arg2=arg2)


class ModelTest(base.TestCase):

    def test_create_attributes(self):
        m = FakeModel(1, 2)
        self.assertEqual(m.arg1, 1)
        self.assertEqual(m.arg2, 2)

    def test_as_dict(self):
        m = FakeModel(1, 2)
        d = m.as_dict()
        self.assertEqual(d, {'arg1': 1, 'arg2': 2})

    def test_as_dict_recursive(self):
        m = FakeModel(1, FakeModel('a', 'b'))
        d = m.as_dict()
        self.assertEqual(d, {'arg1': 1,
                             'arg2': {'arg1': 'a',
                                      'arg2': 'b'}})

    def test_as_dict_recursive_list(self):
        m = FakeModel(1, [FakeModel('a', 'b')])
        d = m.as_dict()
        self.assertEqual(d, {'arg1': 1,
                             'arg2': [{'arg1': 'a',
                                       'arg2': 'b'}]})
