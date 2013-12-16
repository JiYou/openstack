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
"""Set up the API server application instance."""

import flask
import flask.helpers
from oslo.config import cfg

from ceilometer.api import acl
from ceilometer.api.v1 import blueprint as v1_blueprint
from ceilometer.openstack.common import jsonutils
from ceilometer import storage

# Replace the json module used by flask with the one from
# openstack.common so we can take advantage of the fact that it knows
# how to serialize more complex objects.
flask.helpers.json = jsonutils

storage.register_opts(cfg.CONF)


def make_app(conf, enable_acl=True, attach_storage=True,
             sources_file='sources.json'):
    app = flask.Flask('ceilometer.api')
    app.register_blueprint(v1_blueprint.blueprint, url_prefix='/v1')

    try:
        with open(sources_file, "r") as f:
            sources = jsonutils.load(f)
    except IOError:
        sources = {}

    @app.before_request
    def attach_config():
        flask.request.cfg = conf
        flask.request.sources = sources

    if attach_storage:
        @app.before_request
        def attach_storage():
            storage_engine = storage.get_engine(conf)
            flask.request.storage_engine = storage_engine
            flask.request.storage_conn = \
                storage_engine.get_connection(conf)

    # Install the middleware wrapper
    if enable_acl:
        app.wsgi_app = acl.install(app.wsgi_app, conf)

    return app

# For documentation
app = make_app(cfg.CONF, enable_acl=False, attach_storage=False)
