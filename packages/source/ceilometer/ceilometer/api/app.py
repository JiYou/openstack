# -*- encoding: utf-8 -*-
#
# Copyright © 2012 New Dream Network, LLC (DreamHost)
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

import logging
import os
from oslo.config import cfg
import pecan

from ceilometer.api import acl
from ceilometer.api import config as api_config
from ceilometer.api import hooks
from ceilometer.api import middleware
from ceilometer import service
from ceilometer.openstack.common import log
from wsgiref import simple_server

LOG = log.getLogger(__name__)

auth_opts = [
    cfg.StrOpt('auth_strategy',
               default='keystone',
               help='The strategy to use for auth: noauth or keystone.'),
    cfg.BoolOpt('enable_v1_api',
                default=True,
                help='Deploy the deprecated v1 API.'),
]

CONF = cfg.CONF
CONF.register_opts(auth_opts)


def get_pecan_config():
    # Set up the pecan configuration
    filename = api_config.__file__.replace('.pyc', '.py')
    return pecan.configuration.conf_from_file(filename)


def setup_app(pecan_config=None, extra_hooks=None):
    # FIXME: Replace DBHook with a hooks.TransactionHook
    app_hooks = [hooks.ConfigHook(),
                 hooks.DBHook(),
                 hooks.PipelineHook()]
    if extra_hooks:
        app_hooks.extend(extra_hooks)

    if not pecan_config:
        pecan_config = get_pecan_config()

    pecan.configuration.set_config(dict(pecan_config), overwrite=True)

    app = pecan.make_app(
        pecan_config.app.root,
        static_root=pecan_config.app.static_root,
        template_path=pecan_config.app.template_path,
        debug=CONF.debug,
        force_canonical=getattr(pecan_config.app, 'force_canonical', True),
        hooks=app_hooks,
        wrap_app=middleware.ParsableErrorMiddleware,
    )

    if pecan_config.app.enable_acl:
        return acl.install(app, cfg.CONF)

    return app


class VersionSelectorApplication(object):
    def __init__(self):
        pc = get_pecan_config()
        pc.app.enable_acl = (CONF.auth_strategy == 'keystone')
        if cfg.CONF.enable_v1_api:
            from ceilometer.api.v1 import app as v1app
            self.v1 = v1app.make_app(cfg.CONF, enable_acl=pc.app.enable_acl)
        else:
            def not_found(environ, start_response):
                start_response('404 Not Found', [])
                return []
            self.v1 = not_found
        self.v2 = setup_app(pecan_config=pc)

    def __call__(self, environ, start_response):
        if environ['PATH_INFO'].startswith('/v1/'):
            return self.v1(environ, start_response)
        return self.v2(environ, start_response)


def start():
    service.prepare_service()

    # Build the WSGI app
    root = VersionSelectorApplication()

    # Create the WSGI server and start it
    host, port = cfg.CONF.api.host, cfg.CONF.api.port
    srv = simple_server.make_server(host, port, root)

    LOG.info('Starting server in PID %s' % os.getpid())
    LOG.info("Configuration:")
    cfg.CONF.log_opt_values(LOG, logging.INFO)

    if host == '0.0.0.0':
        LOG.info('serving on 0.0.0.0:%s, view at http://127.0.0.1:%s' %
                 (port, port))
    else:
        LOG.info("serving on http://%s:%s" % (host, port))

    srv.serve_forever()
