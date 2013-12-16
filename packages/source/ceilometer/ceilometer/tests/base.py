#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# Copyright © 2012 New Dream Network (DreamHost)
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
"""Test base classes.
"""
import fixtures
import mox
from oslo.config import cfg
import os.path
import stubout
import testtools

cfg.CONF.import_opt('pipeline_cfg_file', 'ceilometer.pipeline')


class TestCase(testtools.TestCase):

    def setUp(self):
        super(TestCase, self).setUp()
        self.mox = mox.Mox()
        self.stubs = stubout.StubOutForTesting()
        self.tempdir = self.useFixture(fixtures.TempDir())
        self.useFixture(fixtures.FakeLogger())

        # Set a default location for the pipeline config file so the
        # tests work even if ceilometer is not installed globally on
        # the system.
        cfg.CONF.set_override(
            'pipeline_cfg_file',
            self.path_get('etc/ceilometer/pipeline.yaml'),
        )

    def path_get(self, project_file=None):
        root = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                            '..',
                                            '..',
                                            )
                               )
        if project_file:
            return os.path.join(root, project_file)
        else:
            return root

    def temp_config_file_path(self, name='ceilometer.conf'):
        return os.path.join(self.tempdir.path, name)

    def tearDown(self):
        self.mox.UnsetStubs()
        self.stubs.UnsetAll()
        self.stubs.SmartUnsetAll()
        self.mox.VerifyAll()
        super(TestCase, self).tearDown()
