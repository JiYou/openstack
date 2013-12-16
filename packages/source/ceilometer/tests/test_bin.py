#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# Copyright © 2012 eNovance <licensing@enovance.com>
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

import httplib2
import json
import random
import socket
import subprocess
import time

from ceilometer.tests import base


class BinDbsyncTestCase(base.TestCase):
    def setUp(self):
        super(BinDbsyncTestCase, self).setUp()
        self.tempfile = self.temp_config_file_path()
        with open(self.tempfile, 'w') as tmp:
            tmp.write("[database]\n")
            tmp.write("connection=log://localhost\n")

    def test_dbsync_run(self):
        subp = subprocess.Popen(['ceilometer-dbsync',
                                 "--config-file=%s" % self.tempfile])
        self.assertEqual(subp.wait(), 0)


class BinSendCounterTestCase(base.TestCase):
    def setUp(self):
        super(BinSendCounterTestCase, self).setUp()
        self.tempfile = self.temp_config_file_path()
        pipeline_cfg_file = self.path_get('etc/ceilometer/pipeline.yaml')
        with open(self.tempfile, 'w') as tmp:
            tmp.write("[DEFAULT]\n")
            tmp.write(
                "rpc_backend=ceilometer.openstack.common.rpc.impl_fake\n")
            tmp.write(
                "pipeline_cfg_file=%s\n" % pipeline_cfg_file)

    def test_send_counter_run(self):
        subp = subprocess.Popen([self.path_get('bin/ceilometer-send-counter'),
                                 "--config-file=%s" % self.tempfile,
                                 "--counter-resource=someuuid",
                                 "--counter-name=mycounter"])
        self.assertEqual(subp.wait(), 0)


class BinApiTestCase(base.TestCase):

    def setUp(self):
        super(BinApiTestCase, self).setUp()
        self.api_port = random.randint(10000, 11000)
        self.http = httplib2.Http()
        self.tempfile = self.temp_config_file_path()
        pipeline_cfg_file = self.path_get('etc/ceilometer/pipeline.yaml')
        policy_file = self.path_get('tests/policy.json')
        with open(self.tempfile, 'w') as tmp:
            tmp.write("[DEFAULT]\n")
            tmp.write(
                "rpc_backend=ceilometer.openstack.common.rpc.impl_fake\n")
            tmp.write(
                "auth_strategy=noauth\n")
            tmp.write(
                "debug=true\n")
            tmp.write(
                "pipeline_cfg_file=%s\n" % pipeline_cfg_file)
            tmp.write(
                "policy_file=%s\n" % policy_file)
            tmp.write("[api]\n")
            tmp.write(
                "port=%s\n" % self.api_port)
            tmp.write("[database]\n")
            tmp.write("connection=log://localhost\n")
        self.subp = subprocess.Popen(['ceilometer-api',
                                      "--config-file=%s" % self.tempfile])

    def tearDown(self):
        super(BinApiTestCase, self).tearDown()
        self.subp.kill()
        self.subp.wait()

    def get_response(self, path):
        url = 'http://%s:%d/%s' % ('127.0.0.1', self.api_port, path)

        for x in range(10):
            try:
                r, c = self.http.request(url, 'GET')
            except socket.error:
                time.sleep(.5)
                self.assertEqual(self.subp.poll(), None)
            else:
                return r, c
        return (None, None)

    def test_v1(self):
        response, content = self.get_response('v1/meters')
        self.assertEqual(response.status, 200)
        self.assertEqual(json.loads(content), {'meters': []})

    def test_v2(self):
        response, content = self.get_response('v2/meters')
        self.assertEqual(response.status, 200)
        self.assertEqual(json.loads(content), [])
