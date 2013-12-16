# -*- encoding: utf-8 -*-
#
# Copyright © 2012 New Dream Network, LLC (DreamHost)
# Copyright © 2013 Intel corp.
# Copyright © 2013 eNovance
#
# Author: Yunhong Jiang <yunhong.jiang@intel.com>
#         Julien Danjou <julien@danjou.info>
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
import datetime
import mock

from stevedore import extension
from stevedore.tests import manager as extension_tests

from ceilometer import counter
from ceilometer import pipeline
from ceilometer.tests import base
from ceilometer import transformer


default_test_data = counter.Counter(
    name='test',
    type=counter.TYPE_CUMULATIVE,
    unit='',
    volume=1,
    user_id='test',
    project_id='test',
    resource_id='test_run_tasks',
    timestamp=datetime.datetime.utcnow().isoformat(),
    resource_metadata={'name': 'Pollster'},
)


class TestPollster:
    test_data = default_test_data

    @classmethod
    def get_counter_names(self):
        return [self.test_data.name]

    def get_counters(self, manager, instance=None):
        self.counters.append((manager, instance))
        return [self.test_data]


class TestPollsterException(TestPollster):
    def get_counters(self, manager, instance=None):
        # Put an instance parameter here so that it can be used
        # by both central manager and compute manager
        # In future, we possibly don't need such hack if we
        # combin the get_counters() function again
        self.counters.append((manager, instance))
        raise Exception()


class BaseAgentManagerTestCase(base.TestCase):

    class Pollster(TestPollster):
        counters = []
        test_data = default_test_data

    class PollsterAnother(TestPollster):
        counters = []
        test_data = default_test_data._replace(name='testanother')

    class PollsterException(TestPollsterException):
        counters = []
        test_data = default_test_data._replace(name='testexception')

    class PollsterExceptionAnother(TestPollsterException):
        counters = []
        test_data = default_test_data._replace(name='testexceptionanother')

    def setup_pipeline(self):
        self.transformer_manager = transformer.TransformerExtensionManager(
            'ceilometer.transformer',
        )
        self.mgr.pipeline_manager = pipeline.PipelineManager(
            self.pipeline_cfg,
            self.transformer_manager)

    def create_extension_manager(self):
        return extension_tests.TestExtensionManager(
            [
                extension.Extension(
                    'test',
                    None,
                    None,
                    self.Pollster(), ),
                extension.Extension(
                    'testanother',
                    None,
                    None,
                    self.PollsterAnother(), ),
                extension.Extension(
                    'testexception',
                    None,
                    None,
                    self.PollsterException(), ),
                extension.Extension(
                    'testexceptionanother',
                    None,
                    None,
                    self.PollsterExceptionAnother(), ),
            ],
            'fake',
            invoke_on_load=False,
        )

    @abc.abstractmethod
    def setup_manager(self):
        """Setup subclass specific managers."""

    @mock.patch('ceilometer.pipeline.setup_pipeline', mock.MagicMock())
    def setUp(self):
        super(BaseAgentManagerTestCase, self).setUp()
        self.setup_manager()
        self.mgr.pollster_manager = self.create_extension_manager()
        self.pipeline_cfg = [{
            'name': "test_pipeline",
            'interval': 60,
            'counters': ['test'],
            'transformers': [],
            'publishers': ["test"],
        }, ]
        self.setup_pipeline()

    def tearDown(self):
        self.Pollster.counters = []
        self.PollsterAnother.counters = []
        self.PollsterException.counters = []
        self.PollsterExceptionAnother.counters = []
        super(BaseAgentManagerTestCase, self).tearDown()

    def test_setup_polling_tasks(self):
        polling_tasks = self.mgr.setup_polling_tasks()
        self.assertEqual(len(polling_tasks), 1)
        self.assertTrue(60 in polling_tasks.keys())
        self.mgr.interval_task(polling_tasks.values()[0])
        pub = self.mgr.pipeline_manager.pipelines[0].publishers[0]
        self.assertEqual(pub.counters[0], self.Pollster.test_data)

    def test_setup_polling_tasks_multiple_interval(self):
        self.pipeline_cfg.append({
            'name': "test_pipeline",
            'interval': 10,
            'counters': ['test'],
            'transformers': [],
            'publishers': ["test"],
        })
        self.setup_pipeline()
        polling_tasks = self.mgr.setup_polling_tasks()
        self.assertEqual(len(polling_tasks), 2)
        self.assertTrue(60 in polling_tasks.keys())
        self.assertTrue(10 in polling_tasks.keys())

    def test_setup_polling_tasks_mismatch_counter(self):
        self.pipeline_cfg.append(
            {
                'name': "test_pipeline_1",
                'interval': 10,
                'counters': ['test_invalid'],
                'transformers': [],
                'publishers': ["test"],
            })
        polling_tasks = self.mgr.setup_polling_tasks()
        self.assertEqual(len(polling_tasks), 1)
        self.assertTrue(60 in polling_tasks.keys())

    def test_setup_polling_task_same_interval(self):
        self.pipeline_cfg.append({
            'name': "test_pipeline",
            'interval': 60,
            'counters': ['testanother'],
            'transformers': [],
            'publishers': ["test"],
        })
        self.setup_pipeline()
        polling_tasks = self.mgr.setup_polling_tasks()
        self.assertEqual(len(polling_tasks), 1)
        pollsters = polling_tasks.get(60).pollsters
        self.assertEqual(len(pollsters), 2)

    def test_interval_exception_isolation(self):
        self.pipeline_cfg = [
            {
                'name': "test_pipeline_1",
                'interval': 10,
                'counters': ['testexceptionanother'],
                'transformers': [],
                'publishers': ["test"],
            },
            {
                'name': "test_pipeline_2",
                'interval': 10,
                'counters': ['testexception'],
                'transformers': [],
                'publishers': ["test"],
            },
        ]
        self.mgr.pipeline_manager = pipeline.PipelineManager(
            self.pipeline_cfg,
            self.transformer_manager)

        polling_tasks = self.mgr.setup_polling_tasks()
        self.assertEqual(len(polling_tasks.keys()), 1)
        polling_tasks.get(10)
        self.mgr.interval_task(polling_tasks.get(10))
        pub = self.mgr.pipeline_manager.pipelines[0].publishers[0]
        self.assertEqual(len(pub.counters), 0)
