# -*- encoding: utf-8 -*-
#
# Copyright © 2013 eNovance
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

from ceilometer import pipeline
from ceilometer import transformer
from ceilometer.openstack.common import context as req_context
from ceilometer.openstack.common import log as logging
from oslo.config import cfg
from stevedore import extension


LOG = logging.getLogger(__name__)

cfg.CONF.import_opt('counter_source', 'ceilometer.counter')


_notification_manager = None
_pipeline_manager = None


def _load_notification_manager():
    global _notification_manager

    namespace = 'ceilometer.collector'

    LOG.debug('loading notification handlers from %s', namespace)

    _notification_manager = extension.ExtensionManager(
        namespace=namespace,
        invoke_on_load=True)

    if not list(_notification_manager):
        LOG.warning('Failed to load any notification handlers for %s',
                    namespace)


def _load_pipeline_manager():
    global _pipeline_manager

    _pipeline_manager = pipeline.setup_pipeline(
        transformer.TransformerExtensionManager(
            'ceilometer.transformer',
        ),
    )


def _process_notification_for_ext(ext, context, notification):
    handler = ext.obj
    if notification['event_type'] in handler.get_event_types():

        with _pipeline_manager.publisher(context,
                                         cfg.CONF.counter_source) as p:
            # FIXME(dhellmann): Spawn green thread?
            p(list(handler.process_notification(notification)))


def notify(context, message):
    """Sends a notification as a meter using Ceilometer pipelines."""
    if not _notification_manager:
        _load_notification_manager()
    if not _pipeline_manager:
        _load_pipeline_manager()
    _notification_manager.map(
        _process_notification_for_ext,
        context=context or req_context.get_admin_context(),
        notification=message)
