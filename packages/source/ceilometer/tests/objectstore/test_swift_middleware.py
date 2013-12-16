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

import cStringIO as StringIO

from oslo.config import cfg
from webob import Request

from ceilometer.tests import base
from ceilometer.objectstore import swift_middleware
from ceilometer import pipeline


class FakeApp(object):
    def __init__(self, body=['This string is 28 bytes long']):
        self.body = body

    def __call__(self, env, start_response):
        start_response('200 OK', [
            ('Content-Type', 'text/plain'),
            ('Content-Length', str(sum(map(len, self.body))))
        ])
        while env['wsgi.input'].read(5):
            pass
        return self.body


class TestSwiftMiddleware(base.TestCase):

    class _faux_pipeline_manager(object):
        class _faux_pipeline(object):
            def __init__(self, pipeline_manager):
                self.pipeline_manager = pipeline_manager
                self.counters = []

            def publish_counters(self, ctxt, counters, source):
                self.counters.extend(counters)

            def flush(self, context, source):
                pass

        def __init__(self):
            self.pipelines = [self._faux_pipeline(self)]

            def flush(self, ctx, source):
                pass

    def _faux_setup_pipeline(self, transformer_manager):
        return self.pipeline_manager

    def setUp(self):
        super(TestSwiftMiddleware, self).setUp()
        self.pipeline_manager = self._faux_pipeline_manager()
        self.stubs.Set(pipeline, 'setup_pipeline', self._faux_setup_pipeline)

    @staticmethod
    def start_response(*args):
            pass

    def test_rpc_setup(self):
        swift_middleware.CeilometerMiddleware(FakeApp(), {})
        self.assertEqual(cfg.CONF.control_exchange, 'ceilometer')

    def test_get(self):
        app = swift_middleware.CeilometerMiddleware(FakeApp(), {})
        req = Request.blank('/1.0/account/container/obj',
                            environ={'REQUEST_METHOD': 'GET'})
        resp = app(req.environ, self.start_response)
        self.assertEqual(list(resp), ["This string is 28 bytes long"])
        counters = self.pipeline_manager.pipelines[0].counters
        self.assertEqual(len(counters), 2)
        data = counters[0]
        self.assertEqual(data.volume, 28)
        self.assertEqual(data.resource_metadata['version'], '1.0')
        self.assertEqual(data.resource_metadata['container'], 'container')
        self.assertEqual(data.resource_metadata['object'], 'obj')

        # test the # of request and the request method
        data = counters[1]
        self.assertEqual(data.name, 'storage.api.request')
        self.assertEqual(data.volume, 1)
        self.assertEqual(data.resource_metadata['method'], 'get')

    def test_put(self):
        app = swift_middleware.CeilometerMiddleware(FakeApp(body=['']), {})
        req = Request.blank('/1.0/account/container/obj',
                            environ={'REQUEST_METHOD': 'PUT',
                                     'wsgi.input':
                                     StringIO.StringIO('some stuff')})
        list(app(req.environ, self.start_response))
        counters = self.pipeline_manager.pipelines[0].counters
        self.assertEqual(len(counters), 2)
        data = counters[0]
        self.assertEqual(data.volume, 10)
        self.assertEqual(data.resource_metadata['version'], '1.0')
        self.assertEqual(data.resource_metadata['container'], 'container')
        self.assertEqual(data.resource_metadata['object'], 'obj')

        # test the # of request and the request method
        data = counters[1]
        self.assertEqual(data.name, 'storage.api.request')
        self.assertEqual(data.volume, 1)
        self.assertEqual(data.resource_metadata['method'], 'put')

    def test_post(self):
        app = swift_middleware.CeilometerMiddleware(FakeApp(body=['']), {})
        req = Request.blank('/1.0/account/container/obj',
                            environ={'REQUEST_METHOD': 'POST',
                                     'wsgi.input':
                                     StringIO.StringIO('some other stuff')})
        list(app(req.environ, self.start_response))
        counters = self.pipeline_manager.pipelines[0].counters
        self.assertEqual(len(counters), 2)
        data = counters[0]
        self.assertEqual(data.volume, 16)
        self.assertEqual(data.resource_metadata['version'], '1.0')
        self.assertEqual(data.resource_metadata['container'], 'container')
        self.assertEqual(data.resource_metadata['object'], 'obj')

        # test the # of request and the request method
        data = counters[1]
        self.assertEqual(data.name, 'storage.api.request')
        self.assertEqual(data.volume, 1)
        self.assertEqual(data.resource_metadata['method'], 'post')

    def test_head(self):
        app = swift_middleware.CeilometerMiddleware(FakeApp(body=['']), {})
        req = Request.blank('/1.0/account/container/obj',
                            environ={'REQUEST_METHOD': 'HEAD'})
        list(app(req.environ, self.start_response))
        counters = self.pipeline_manager.pipelines[0].counters
        self.assertEqual(len(counters), 1)
        data = counters[0]
        self.assertEqual(data.resource_metadata['version'], '1.0')
        self.assertEqual(data.resource_metadata['container'], 'container')
        self.assertEqual(data.resource_metadata['object'], 'obj')
        self.assertEqual(data.resource_metadata['method'], 'head')

        self.assertEqual(data.name, 'storage.api.request')
        self.assertEqual(data.volume, 1)

    def test_bogus_request(self):
        """Test even for arbitrary request method, this will still work."""
        app = swift_middleware.CeilometerMiddleware(FakeApp(body=['']), {})
        req = Request.blank('/1.0/account/container/obj',
                            environ={'REQUEST_METHOD': 'BOGUS'})
        list(app(req.environ, self.start_response))
        counters = self.pipeline_manager.pipelines[0].counters

        self.assertEqual(len(counters), 1)
        data = counters[0]
        self.assertEqual(data.resource_metadata['version'], '1.0')
        self.assertEqual(data.resource_metadata['container'], 'container')
        self.assertEqual(data.resource_metadata['object'], 'obj')
        self.assertEqual(data.resource_metadata['method'], 'bogus')

        self.assertEqual(data.name, 'storage.api.request')
        self.assertEqual(data.volume, 1)

    def test_get_container(self):
        app = swift_middleware.CeilometerMiddleware(FakeApp(), {})
        req = Request.blank('/1.0/account/container',
                            environ={'REQUEST_METHOD': 'GET'})
        list(app(req.environ, self.start_response))
        counters = self.pipeline_manager.pipelines[0].counters
        self.assertEqual(len(counters), 2)
        data = counters[0]
        self.assertEqual(data.volume, 28)
        self.assertEqual(data.resource_metadata['version'], '1.0')
        self.assertEqual(data.resource_metadata['container'], 'container')
        self.assertEqual(data.resource_metadata['object'], None)

    def test_no_metadata_headers(self):
        app = swift_middleware.CeilometerMiddleware(FakeApp(), {})
        req = Request.blank('/1.0/account/container',
                            environ={'REQUEST_METHOD': 'GET'})
        list(app(req.environ, self.start_response))
        counters = self.pipeline_manager.pipelines[0].counters
        self.assertEqual(len(counters), 2)
        data = counters[0]
        http_headers = [k for k in data.resource_metadata.keys()
                        if k.startswith('http_header_')]
        self.assertEqual(len(http_headers), 0)
        self.assertEqual(data.resource_metadata['version'], '1.0')
        self.assertEqual(data.resource_metadata['container'], 'container')
        self.assertEqual(data.resource_metadata['object'], None)

    def test_metadata_headers(self):
        app = swift_middleware.CeilometerMiddleware(FakeApp(), {
            'metadata_headers': 'X_VAR1, x-var2, x-var3'
        })
        req = Request.blank('/1.0/account/container',
                            environ={'REQUEST_METHOD': 'GET'},
                            headers={
                                'X_VAR1': 'value1',
                                'X_VAR2': 'value2'
                            })
        list(app(req.environ, self.start_response))
        counters = self.pipeline_manager.pipelines[0].counters
        self.assertEqual(len(counters), 2)
        data = counters[0]
        http_headers = [k for k in data.resource_metadata.keys()
                        if k.startswith('http_header_')]
        self.assertEqual(len(http_headers), 2)
        self.assertEqual(data.resource_metadata['version'], '1.0')
        self.assertEqual(data.resource_metadata['container'], 'container')
        self.assertEqual(data.resource_metadata['object'], None)
        self.assertEqual(data.resource_metadata['http_header_x_var1'],
                         'value1')
        self.assertEqual(data.resource_metadata['http_header_x_var2'],
                         'value2')
        self.assertFalse('http_header_x_var3' in data.resource_metadata)

    def test_metadata_headers_on_not_existing_header(self):
        app = swift_middleware.CeilometerMiddleware(FakeApp(), {
            'metadata_headers': 'x-var3'
        })
        req = Request.blank('/1.0/account/container',
                            environ={'REQUEST_METHOD': 'GET'})
        list(app(req.environ, self.start_response))
        counters = self.pipeline_manager.pipelines[0].counters
        self.assertEqual(len(counters), 2)
        data = counters[0]
        http_headers = [k for k in data.resource_metadata.keys()
                        if k.startswith('http_header_')]
        self.assertEqual(len(http_headers), 0)
        self.assertEqual(data.resource_metadata['version'], '1.0')
        self.assertEqual(data.resource_metadata['container'], 'container')
        self.assertEqual(data.resource_metadata['object'], None)
