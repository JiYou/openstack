# -*- encoding: utf-8 -*-
#
# Copyright © 2013 Julien Danjou
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
"""Test basic ceilometer-api app
"""
import os

from oslo.config import cfg

from ceilometer.api.v1 import app
from ceilometer.api import acl
from ceilometer import service
from ceilometer.tests import base


class TestApp(base.TestCase):

    def tearDown(self):
        super(TestApp, self).tearDown()
        cfg.CONF.reset()

    def test_keystone_middleware_conf(self):
        cfg.CONF.set_override("auth_protocol", "foottp",
                              group=acl.OPT_GROUP_NAME)
        cfg.CONF.set_override("auth_version", "v2.0", group=acl.OPT_GROUP_NAME)
        api_app = app.make_app(cfg.CONF, attach_storage=False)
        self.assertEqual(api_app.wsgi_app.auth_protocol, 'foottp')

    def test_keystone_middleware_parse_conffile(self):
        tmpfile = self.temp_config_file_path()
        with open(tmpfile, "w") as f:
            f.write("[%s]\nauth_protocol = barttp" % acl.OPT_GROUP_NAME)
            f.write("\nauth_version = v2.0")
        service.prepare_service(['ceilometer-api',
                                 '--config-file=%s' % tmpfile])
        api_app = app.make_app(cfg.CONF, attach_storage=False)
        self.assertEqual(api_app.wsgi_app.auth_protocol, 'barttp')
        os.unlink(tmpfile)
