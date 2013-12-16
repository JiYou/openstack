# -*- encoding: utf-8 -*-
#
# Copyright © 2012 New Dream Network, LLC (DreamHost)
#
# Author: Doug Hellmann <doug.hellmann@dreamhost.com>
#         Angus Salkeld <asalkeld@redhat.com>
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

from oslo.config import cfg
from pecan import hooks

from ceilometer import pipeline
from ceilometer import storage
from ceilometer import transformer


class ConfigHook(hooks.PecanHook):
    """Attach the configuration object to the request
    so controllers can get to it.
    """

    def before(self, state):
        state.request.cfg = cfg.CONF


class DBHook(hooks.PecanHook):

    def before(self, state):
        storage_engine = storage.get_engine(state.request.cfg)
        state.request.storage_engine = storage_engine
        state.request.storage_conn = storage_engine.get_connection(
            state.request.cfg)

    # def after(self, state):
    #     print 'method:', state.request.method
    #     print 'response:', state.response.status


class PipelineHook(hooks.PecanHook):
    '''Create and attach a pipeline to the request so that
    new samples can be posted via the /v2/meters/ API.
    '''

    pipeline_manager = None

    def __init__(self):
        if self.__class__.pipeline_manager is None:
            # this is done here as the cfg options are not available
            # when the file is imported.
            self.__class__.pipeline_manager = pipeline.setup_pipeline(
                transformer.TransformerExtensionManager(
                    'ceilometer.transformer'))

    def before(self, state):
        state.request.pipeline_manager = self.pipeline_manager
