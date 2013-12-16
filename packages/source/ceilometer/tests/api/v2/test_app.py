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

from ceilometer.api import app
from ceilometer.api import acl
from ceilometer import service
from ceilometer.tests import base
from .base import FunctionalTest


class TestApp(base.TestCase):

    def tearDown(self):
        super(TestApp, self).tearDown()
        cfg.CONF.reset()

    def test_keystone_middleware_conf(self):
        cfg.CONF.set_override("auth_protocol", "foottp",
                              group=acl.OPT_GROUP_NAME)
        cfg.CONF.set_override("auth_version", "v2.0", group=acl.OPT_GROUP_NAME)
        cfg.CONF.set_override("pipeline_cfg_file",
                              self.path_get("etc/ceilometer/pipeline.yaml"))
        api_app = app.setup_app()
        self.assertEqual(api_app.auth_protocol, 'foottp')

    def test_keystone_middleware_parse_conffile(self):
        tmpfile = self.temp_config_file_path()
        with open(tmpfile, "w") as f:
            f.write("[DEFAULT]\n")
            f.write("pipeline_cfg_file = %s\n" %
                    self.path_get("etc/ceilometer/pipeline.yaml"))
            f.write("[%s]\n" % acl.OPT_GROUP_NAME)
            f.write("auth_protocol = barttp\n")
            f.write("auth_version = v2.0\n")
        service.prepare_service(['ceilometer-api',
                                 '--config-file=%s' % tmpfile])
        api_app = app.setup_app()
        self.assertEqual(api_app.auth_protocol, 'barttp')
        os.unlink(tmpfile)


class TestApiMiddleware(FunctionalTest):

    def test_json_parsable_error_middleware_404(self):
        response = self.get_json('/invalid_path',
                                 expect_errors=True,
                                 headers={"Accept":
                                          "application/json"}
                                 )
        self.assertEqual(response.status_int, 404)
        self.assertEqual(response.content_type, "application/json")
        self.assertTrue(response.json['error_message'])
        response = self.get_json('/invalid_path',
                                 expect_errors=True,
                                 headers={"Accept":
                                          "application/json,application/xml"}
                                 )
        self.assertEqual(response.status_int, 404)
        self.assertEqual(response.content_type, "application/json")
        self.assertTrue(response.json['error_message'])
        response = self.get_json('/invalid_path',
                                 expect_errors=True,
                                 headers={"Accept":
                                          "application/xml;q=0.8, \
                                          application/json"}
                                 )
        self.assertEqual(response.status_int, 404)
        self.assertEqual(response.content_type, "application/json")
        self.assertTrue(response.json['error_message'])
        response = self.get_json('/invalid_path',
                                 expect_errors=True
                                 )
        self.assertEqual(response.status_int, 404)
        self.assertEqual(response.content_type, "application/json")
        self.assertTrue(response.json['error_message'])
        response = self.get_json('/invalid_path',
                                 expect_errors=True,
                                 headers={"Accept":
                                          "text/html,*/*"}
                                 )
        self.assertEqual(response.status_int, 404)
        self.assertEqual(response.content_type, "application/json")
        self.assertTrue(response.json['error_message'])

    def test_xml_parsable_error_middleware_404(self):
        response = self.get_json('/invalid_path',
                                 expect_errors=True,
                                 headers={"Accept":
                                          "application/xml,*/*"}
                                 )
        self.assertEqual(response.status_int, 404)
        self.assertEqual(response.content_type, "application/xml")
        self.assertEqual(response.xml.tag, 'error_message')
        response = self.get_json('/invalid_path',
                                 expect_errors=True,
                                 headers={"Accept":
                                          "application/json;q=0.8 \
                                          ,application/xml"}
                                 )
        self.assertEqual(response.status_int, 404)
        self.assertEqual(response.content_type, "application/xml")
        self.assertEqual(response.xml.tag, 'error_message')
