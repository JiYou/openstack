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

import abc
import itertools

from oslo.config import cfg

from ceilometer.openstack.common import context
from ceilometer.openstack.common import log
from ceilometer import pipeline
from ceilometer import transformer

LOG = log.getLogger(__name__)


class PollingTask(object):
    """Polling task for polling counters and inject into pipeline.
    A polling task can be invoked periodically or only once.

    """

    def __init__(self, agent_manager):
        self.manager = agent_manager
        self.pollsters = set()
        self.publish_context = pipeline.PublishContext(
            agent_manager.context,
            cfg.CONF.counter_source)

    def add(self, pollster, pipelines):
        self.publish_context.add_pipelines(pipelines)
        self.pollsters.update([pollster])

    @abc.abstractmethod
    def poll_and_publish(self):
        """Polling counter and publish into pipeline."""


class AgentManager(object):

    def __init__(self, extension_manager):
        self.pipeline_manager = pipeline.setup_pipeline(
            transformer.TransformerExtensionManager(
                'ceilometer.transformer',
            ),
        )

        self.pollster_manager = extension_manager

        self.context = context.RequestContext('admin', 'admin', is_admin=True)

    @abc.abstractmethod
    def create_polling_task(self):
        """Create an empty polling task."""

    def setup_polling_tasks(self):
        polling_tasks = {}
        for pipeline, pollster in itertools.product(
                self.pipeline_manager.pipelines,
                self.pollster_manager.extensions):
            for counter in pollster.obj.get_counter_names():
                if pipeline.support_counter(counter):
                    polling_task = polling_tasks.get(pipeline.interval, None)
                    if not polling_task:
                        polling_task = self.create_polling_task()
                        polling_tasks[pipeline.interval] = polling_task
                    polling_task.add(pollster, [pipeline])
                    break

        return polling_tasks

    def initialize_service_hook(self, service):
        self.service = service
        for interval, task in self.setup_polling_tasks().iteritems():
            self.service.tg.add_timer(interval,
                                      self.interval_task,
                                      task=task)

    @staticmethod
    def interval_task(task):
        task.poll_and_publish()
