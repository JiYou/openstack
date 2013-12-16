#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# Copyright © 2012 eNovance <licensing@enovance.com>
#
# Author: Julien Danjou <julien@danjou.info>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""
Ceilometer Middleware for Swift Proxy

Configuration:

In /etc/swift/proxy-server.conf on the main pipeline add "ceilometer" just
before "proxy-server" and add the following filter in the file:

[filter:ceilometer]
use = egg:ceilometer#swift

# Some optional configuration
# this allow to publish additional metadata
metadata_headers = X-TEST
"""

from __future__ import absolute_import

from oslo.config import cfg
from swift.common.utils import split_path
import webob

REQUEST = webob
try:
    # Swift >= 1.7.5
    import swift.common.swob
    REQUEST = swift.common.swob
except ImportError:
    pass

try:
    # Swift > 1.7.5 ... module exists but doesn't contain class.
    from swift.common.utils import InputProxy
except ImportError:
    # Swift <= 1.7.5 ... module exists and has class.
    from swift.common.middleware.proxy_logging import InputProxy

from ceilometer import counter
from ceilometer.openstack.common import context
from ceilometer.openstack.common import timeutils
from ceilometer import pipeline
from ceilometer import service
from ceilometer import transformer


class CeilometerMiddleware(object):
    """Ceilometer middleware used for counting requests."""

    def __init__(self, app, conf):
        self.app = app

        self.metadata_headers = [h.strip().replace('-', '_').lower()
                                 for h in conf.get(
                                     "metadata_headers",
                                     "").split(",") if h.strip()]

        service.prepare_service([])

        self.pipeline_manager = pipeline.setup_pipeline(
            transformer.TransformerExtensionManager(
                'ceilometer.transformer',
            ),
        )

    def __call__(self, env, start_response):
        start_response_args = [None]
        input_proxy = InputProxy(env['wsgi.input'])
        env['wsgi.input'] = input_proxy

        def my_start_response(status, headers, exc_info=None):
            start_response_args[0] = (status, list(headers), exc_info)

        def iter_response(iterable):
            if start_response_args[0]:
                start_response(*start_response_args[0])
            bytes_sent = 0
            try:
                for chunk in iterable:
                    if chunk:
                        bytes_sent += len(chunk)
                    yield chunk
            finally:
                self.publish_counter(env,
                                     input_proxy.bytes_received,
                                     bytes_sent)

        try:
            iterable = self.app(env, my_start_response)
        except Exception:
            self.publish_counter(env, input_proxy.bytes_received, 0)
            raise
        else:
            return iter_response(iterable)

    def publish_counter(self, env, bytes_received, bytes_sent):
        req = REQUEST.Request(env)
        version, account, container, obj = split_path(req.path, 1, 4, True)
        now = timeutils.utcnow().isoformat()

        resource_metadata = {
            "path": req.path,
            "version": version,
            "container": container,
            "object": obj,
        }

        for header in self.metadata_headers:
            if header.upper() in req.headers:
                resource_metadata['http_header_%s' % header] = req.headers.get(
                    header.upper())

        with pipeline.PublishContext(
                context.get_admin_context(),
                cfg.CONF.counter_source,
                self.pipeline_manager.pipelines,
        ) as publisher:
            if bytes_received:
                publisher([counter.Counter(
                    name='storage.objects.incoming.bytes',
                    type=counter.TYPE_DELTA,
                    unit='B',
                    volume=bytes_received,
                    user_id=env.get('HTTP_X_USER_ID'),
                    project_id=env.get('HTTP_X_TENANT_ID'),
                    resource_id=account.partition('AUTH_')[2],
                    timestamp=now,
                    resource_metadata=resource_metadata)])

            if bytes_sent:
                publisher([counter.Counter(
                    name='storage.objects.outgoing.bytes',
                    type=counter.TYPE_DELTA,
                    unit='B',
                    volume=bytes_sent,
                    user_id=env.get('HTTP_X_USER_ID'),
                    project_id=env.get('HTTP_X_TENANT_ID'),
                    resource_id=account.partition('AUTH_')[2],
                    timestamp=now,
                    resource_metadata=resource_metadata)])

            # publish the event for each request
            # request method will be recorded in the metadata
            resource_metadata['method'] = req.method.lower()
            publisher([counter.Counter(
                name='storage.api.request',
                type=counter.TYPE_DELTA,
                unit='request',
                volume=1,
                user_id=env.get('HTTP_X_USER_ID'),
                project_id=env.get('HTTP_X_TENANT_ID'),
                resource_id=account.partition('AUTH_')[2],
                timestamp=now,
                resource_metadata=resource_metadata)])


def filter_factory(global_conf, **local_conf):
    conf = global_conf.copy()
    conf.update(local_conf)

    def ceilometer_filter(app):
        return CeilometerMiddleware(app, conf)
    return ceilometer_filter
