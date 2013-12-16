# -*- encoding: utf-8 -*-
#
# Copyright © 2013 Intel Corp.
#
# Authors: Yunhong Jiang <yunhong.jiang@intel.com>
#          Julien Danjou <julien@danjou.info>
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

from stevedore import extension

from ceilometer import counter
from ceilometer import publisher
from ceilometer.publisher import test as test_publisher
from ceilometer import transformer
from ceilometer.transformer import accumulator
from ceilometer.openstack.common import timeutils
from ceilometer import pipeline
from ceilometer.tests import base


class TestPipeline(base.TestCase):
    def fake_tem_init(self):
        """Fake a transformerManager for pipeline
           The faked entry point setting is below:
           update: TransformerClass
           except: TransformerClassException
           drop:   TransformerClassDrop
        """
        pass

    def fake_tem_get_ext(self, name):
        class_name_ext = {
            'update': self.TransformerClass,
            'except': self.TransformerClassException,
            'drop': self.TransformerClassDrop,
            'cache': accumulator.TransformerAccumulator}

        if name in class_name_ext:
            return extension.Extension(name, None,
                                       class_name_ext[name],
                                       None,
                                       )

        raise KeyError(name)

    def get_publisher(self, url, namespace=''):
        fake_drivers = {'test://': test_publisher.TestPublisher,
                        'new://': test_publisher.TestPublisher,
                        'except://': self.PublisherClassException}
        return fake_drivers[url](url)

    class PublisherClassException(publisher.PublisherBase):
        def publish_counters(self, ctxt, counters, source):
            raise Exception()

    class TransformerClass(transformer.TransformerBase):
        samples = []

        def __init__(self, append_name='_update'):
            self.__class__.samples = []
            self.append_name = append_name

        def flush(self, ctxt, source):
            return []

        def handle_sample(self, ctxt, counter, source):
            self.__class__.samples.append(counter)
            newname = getattr(counter, 'name') + self.append_name
            return counter._replace(name=newname)

    class TransformerClassDrop(transformer.TransformerBase):
        samples = []

        def __init__(self):
            self.__class__.samples = []

        def handle_sample(self, ctxt, counter, source):
            self.__class__.samples.append(counter)

    class TransformerClassException(object):
        def handle_sample(self, ctxt, counter, source):
            raise Exception()

    def setUp(self):
        super(TestPipeline, self).setUp()

        self.test_counter = counter.Counter(
            name='a',
            type=counter.TYPE_GAUGE,
            volume=1,
            unit='B',
            user_id="test_user",
            project_id="test_proj",
            resource_id="test_resource",
            timestamp=timeutils.utcnow().isoformat(),
            resource_metadata={}
        )

        self.stubs.Set(transformer.TransformerExtensionManager,
                       "__init__",
                       self.fake_tem_init)

        self.stubs.Set(transformer.TransformerExtensionManager,
                       "get_ext",
                       self.fake_tem_get_ext)

        self.stubs.Set(publisher, 'get_publisher', self.get_publisher)

        self.transformer_manager = transformer.TransformerExtensionManager()

        self.pipeline_cfg = [{
            'name': "test_pipeline",
            'interval': 5,
            'counters': ['a'],
            'transformers': [
                {'name': "update",
                 'parameters': {}}
            ],
            'publishers': ["test://"],
        }, ]

    def _exception_create_pipelinemanager(self):
        self.assertRaises(pipeline.PipelineException,
                          pipeline.PipelineManager,
                          self.pipeline_cfg,
                          self.transformer_manager)

    def test_no_counters(self):
        del self.pipeline_cfg[0]['counters']
        self._exception_create_pipelinemanager()

    def test_no_transformers(self):
        del self.pipeline_cfg[0]['transformers']
        self._exception_create_pipelinemanager()

    def test_no_name(self):
        del self.pipeline_cfg[0]['name']
        self._exception_create_pipelinemanager()

    def test_no_interval(self):
        del self.pipeline_cfg[0]['interval']
        self._exception_create_pipelinemanager()

    def test_no_publishers(self):
        del self.pipeline_cfg[0]['publishers']
        self._exception_create_pipelinemanager()

    def test_check_counters_include_exclude_same(self):
        counter_cfg = ['a', '!a']
        self.pipeline_cfg[0]['counters'] = counter_cfg
        self._exception_create_pipelinemanager()

    def test_check_counters_include_exclude(self):
        counter_cfg = ['a', '!b']
        self.pipeline_cfg[0]['counters'] = counter_cfg
        self._exception_create_pipelinemanager()

    def test_check_counters_wildcard_included(self):
        counter_cfg = ['a', '*']
        self.pipeline_cfg[0]['counters'] = counter_cfg
        self._exception_create_pipelinemanager()

    def test_check_publishers_invalid_publisher(self):
        publisher_cfg = ['test_invalid']
        self.pipeline_cfg[0]['publishers'] = publisher_cfg

    def test_invalid_string_interval(self):
        self.pipeline_cfg[0]['interval'] = 'string'
        self._exception_create_pipelinemanager()

    def test_check_transformer_invalid_transformer(self):
        transformer_cfg = [
            {'name': "test_invalid",
             'parameters': {}}
        ]
        self.pipeline_cfg[0]['transformers'] = transformer_cfg
        self._exception_create_pipelinemanager()

    def test_get_interval(self):
        pipeline_manager = pipeline.PipelineManager(self.pipeline_cfg,
                                                    self.transformer_manager)

        pipe = pipeline_manager.pipelines[0]
        self.assertTrue(pipe.get_interval() == 5)

    def test_publisher_transformer_invoked(self):
        pipeline_manager = pipeline.PipelineManager(self.pipeline_cfg,
                                                    self.transformer_manager)

        with pipeline_manager.publisher(None, None) as p:
            p([self.test_counter])

        publisher = pipeline_manager.pipelines[0].publishers[0]
        self.assertEqual(len(publisher.counters), 1)
        self.assertTrue(len(self.TransformerClass.samples) == 1)
        self.assertEqual(getattr(publisher.counters[0], "name"), 'a_update')
        self.assertTrue(getattr(self.TransformerClass.samples[0], "name")
                        == 'a')

    def test_multiple_included_counters(self):
        counter_cfg = ['a', 'b']
        self.pipeline_cfg[0]['counters'] = counter_cfg
        pipeline_manager = pipeline.PipelineManager(self.pipeline_cfg,
                                                    self.transformer_manager)

        with pipeline_manager.publisher(None, None) as p:
            p([self.test_counter])

        publisher = pipeline_manager.pipelines[0].publishers[0]
        self.assertEqual(len(publisher.counters), 1)

        self.test_counter = self.test_counter._replace(name='b')
        with pipeline_manager.publisher(None, None) as p:
            p([self.test_counter])

        self.assertEqual(len(publisher.counters), 2)
        self.assertTrue(len(self.TransformerClass.samples) == 2)
        self.assertEqual(getattr(publisher.counters[0], "name"), 'a_update')
        self.assertEqual(getattr(publisher.counters[1], "name"), 'b_update')

    def test_wildcard_counter(self):
        counter_cfg = ['*']
        self.pipeline_cfg[0]['counters'] = counter_cfg
        pipeline_manager = pipeline.PipelineManager(self.pipeline_cfg,
                                                    self.transformer_manager)
        with pipeline_manager.publisher(None, None) as p:
            p([self.test_counter])

        publisher = pipeline_manager.pipelines[0].publishers[0]
        self.assertEqual(len(publisher.counters), 1)
        self.assertTrue(len(self.TransformerClass.samples) == 1)
        self.assertEqual(getattr(publisher.counters[0], "name"), 'a_update')

    def test_wildcard_excluded_counters(self):
        counter_cfg = ['*', '!a']
        self.pipeline_cfg[0]['counters'] = counter_cfg
        pipeline_manager = pipeline.PipelineManager(self.pipeline_cfg,
                                                    self.transformer_manager)
        self.assertFalse(pipeline_manager.pipelines[0].support_counter('a'))

    def test_wildcard_excluded_counters_not_excluded(self):
        counter_cfg = ['*', '!b']
        self.pipeline_cfg[0]['counters'] = counter_cfg
        pipeline_manager = pipeline.PipelineManager(self.pipeline_cfg,
                                                    self.transformer_manager)
        with pipeline_manager.publisher(None, None) as p:
            p([self.test_counter])
        publisher = pipeline_manager.pipelines[0].publishers[0]
        self.assertEqual(len(publisher.counters), 1)
        self.assertEqual(len(self.TransformerClass.samples), 1)
        self.assertEqual(getattr(publisher.counters[0], "name"),
                         'a_update')

    def test_all_excluded_counters_not_excluded(self):
        counter_cfg = ['!b', '!c']
        self.pipeline_cfg[0]['counters'] = counter_cfg
        pipeline_manager = pipeline.PipelineManager(self.pipeline_cfg,
                                                    self.transformer_manager)
        with pipeline_manager.publisher(None, None) as p:
            p([self.test_counter])

        publisher = pipeline_manager.pipelines[0].publishers[0]
        self.assertEqual(len(publisher.counters), 1)
        self.assertTrue(len(self.TransformerClass.samples) == 1)
        self.assertEqual(getattr(publisher.counters[0], "name"), 'a_update')
        self.assertTrue(getattr(self.TransformerClass.samples[0], "name")
                        == 'a')

    def test_all_excluded_counters_is_excluded(self):
        counter_cfg = ['!a', '!c']
        self.pipeline_cfg[0]['counters'] = counter_cfg
        pipeline_manager = pipeline.PipelineManager(self.pipeline_cfg,
                                                    self.transformer_manager)
        self.assertFalse(pipeline_manager.pipelines[0].support_counter('a'))
        self.assertTrue(pipeline_manager.pipelines[0].support_counter('b'))
        self.assertFalse(pipeline_manager.pipelines[0].support_counter('c'))

    def test_multiple_pipeline(self):
        self.pipeline_cfg.append({
            'name': 'second_pipeline',
            'interval': 5,
            'counters': ['b'],
            'transformers': [{
                'name': 'update',
                'parameters':
                {
                    "append_name": "_new",
                }
            }],
            'publishers': ['new'],
        })

        pipeline_manager = pipeline.PipelineManager(self.pipeline_cfg,
                                                    self.transformer_manager)
        with pipeline_manager.publisher(None, None) as p:
            p([self.test_counter])

        self.test_counter = self.test_counter._replace(name='b')

        with pipeline_manager.publisher(None, None) as p:
            p([self.test_counter])

        publisher = pipeline_manager.pipelines[0].publishers[0]
        self.assertEqual(len(publisher.counters), 1)
        self.assertEqual(getattr(publisher.counters[0], "name"), 'a_update')
        new_publisher = pipeline_manager.pipelines[1].publishers[0]
        self.assertEqual(len(new_publisher.counters), 1)
        self.assertEqual(getattr(new_publisher.counters[0], "name"), 'b_new')
        self.assertTrue(getattr(self.TransformerClass.samples[0], "name")
                        == 'a')

        self.assertTrue(len(self.TransformerClass.samples) == 2)
        self.assertTrue(getattr(self.TransformerClass.samples[0], "name")
                        == 'a')
        self.assertTrue(getattr(self.TransformerClass.samples[1], "name")
                        == 'b')

    def test_multiple_pipeline_exception(self):
        self.pipeline_cfg.append({
            'name': "second_pipeline",
            "interval": 5,
            'counters': ['b'],
            'transformers': [{
                'name': 'update',
                'parameters':
                {
                    "append_name": "_new",
                }
            }],
            'publishers': ['except'],
        })
        pipeline_manager = pipeline.PipelineManager(self.pipeline_cfg,
                                                    self.transformer_manager)

        with pipeline_manager.publisher(None, None) as p:
            p([self.test_counter])

        self.test_counter = self.test_counter._replace(name='b')

        with pipeline_manager.publisher(None, None) as p:
            p([self.test_counter])

        publisher = pipeline_manager.pipelines[0].publishers[0]
        self.assertEqual(len(publisher.counters), 1)
        self.assertEqual(getattr(publisher.counters[0], "name"), 'a_update')
        self.assertTrue(len(self.TransformerClass.samples) == 2)
        self.assertTrue(getattr(self.TransformerClass.samples[0], "name")
                        == 'a')
        self.assertTrue(getattr(self.TransformerClass.samples[1], "name")
                        == 'b')

    def test_none_transformer_pipeline(self):
        self.pipeline_cfg[0]['transformers'] = None
        pipeline_manager = pipeline.PipelineManager(self.pipeline_cfg,
                                                    self.transformer_manager)
        with pipeline_manager.publisher(None, None) as p:
            p([self.test_counter])
        publisher = pipeline_manager.pipelines[0].publishers[0]
        self.assertEqual(len(publisher.counters), 1)
        self.assertEqual(getattr(publisher.counters[0], 'name'), 'a')

    def test_empty_transformer_pipeline(self):
        self.pipeline_cfg[0]['transformers'] = []
        pipeline_manager = pipeline.PipelineManager(self.pipeline_cfg,
                                                    self.transformer_manager)
        with pipeline_manager.publisher(None, None) as p:
            p([self.test_counter])
        publisher = pipeline_manager.pipelines[0].publishers[0]
        self.assertEqual(len(publisher.counters), 1)
        self.assertEqual(getattr(publisher.counters[0], 'name'), 'a')

    def test_multiple_transformer_same_class(self):
        self.pipeline_cfg[0]['transformers'] = [
            {
                'name': 'update',
                'parameters': {}
            },
            {
                'name': 'update',
                'parameters': {}
            },
        ]
        pipeline_manager = pipeline.PipelineManager(self.pipeline_cfg,
                                                    self.transformer_manager)

        with pipeline_manager.publisher(None, None) as p:
            p([self.test_counter])

        publisher = pipeline_manager.pipelines[0].publishers[0]
        self.assertEqual(len(publisher.counters), 1)
        self.assertEqual(getattr(publisher.counters[0], 'name'),
                         'a_update_update')
        self.assertTrue(len(self.TransformerClass.samples) == 2)
        self.assertTrue(getattr(self.TransformerClass.samples[0], 'name')
                        == 'a')
        self.assertTrue(getattr(self.TransformerClass.samples[1], 'name')
                        == 'a_update')

    def test_multiple_transformer_same_class_different_parameter(self):
        self.pipeline_cfg[0]['transformers'] = [
            {
                'name': 'update',
                'parameters':
                {
                    "append_name": "_update",
                }
            },
            {
                'name': 'update',
                'parameters':
                {
                    "append_name": "_new",
                }
            },
        ]
        pipeline_manager = pipeline.PipelineManager(self.pipeline_cfg,
                                                    self.transformer_manager)
        with pipeline_manager.publisher(None, None) as p:
            p([self.test_counter])

        self.assertTrue(len(self.TransformerClass.samples) == 2)
        self.assertTrue(getattr(self.TransformerClass.samples[0], 'name')
                        == 'a')
        self.assertTrue(getattr(self.TransformerClass.samples[1], 'name')
                        == 'a_update')
        publisher = pipeline_manager.pipelines[0].publishers[0]
        self.assertEqual(len(publisher.counters), 1)
        self.assertEqual(getattr(publisher.counters[0], 'name'),
                         'a_update_new')

    def test_multiple_transformer_drop_transformer(self):
        self.pipeline_cfg[0]['transformers'] = [
            {
                'name': 'update',
                'parameters':
                {
                    "append_name": "_update",
                }
            },
            {
                'name': 'drop',
                'parameters': {}
            },
            {
                'name': 'update',
                'parameters':
                {
                    "append_name": "_new",
                }
            },
        ]
        pipeline_manager = pipeline.PipelineManager(self.pipeline_cfg,
                                                    self.transformer_manager)
        with pipeline_manager.publisher(None, None) as p:
            p([self.test_counter])

        publisher = pipeline_manager.pipelines[0].publishers[0]
        self.assertEqual(len(publisher.counters), 0)
        self.assertTrue(len(self.TransformerClass.samples) == 1)
        self.assertTrue(getattr(self.TransformerClass.samples[0], 'name')
                        == 'a')
        self.assertTrue(len(self.TransformerClassDrop.samples) == 1)
        self.assertTrue(getattr(self.TransformerClassDrop.samples[0], 'name')
                        == 'a_update')

    def test_multiple_publisher(self):
        self.pipeline_cfg[0]['publishers'] = ['test://', 'new://']
        pipeline_manager = pipeline.PipelineManager(self.pipeline_cfg,
                                                    self.transformer_manager)

        with pipeline_manager.publisher(None, None) as p:
            p([self.test_counter])

        publisher = pipeline_manager.pipelines[0].publishers[0]
        new_publisher = pipeline_manager.pipelines[0].publishers[1]
        self.assertEqual(len(publisher.counters), 1)
        self.assertEqual(len(new_publisher.counters), 1)
        self.assertEqual(getattr(new_publisher.counters[0], 'name'),
                         'a_update')
        self.assertEqual(getattr(publisher.counters[0], 'name'),
                         'a_update')

    def test_multiple_publisher_isolation(self):
        self.pipeline_cfg[0]['publishers'] = ['except://', 'new://']
        pipeline_manager = pipeline.PipelineManager(self.pipeline_cfg,
                                                    self.transformer_manager)
        with pipeline_manager.publisher(None, None) as p:
            p([self.test_counter])

        new_publisher = pipeline_manager.pipelines[0].publishers[1]
        self.assertEqual(len(new_publisher.counters), 1)
        self.assertEqual(getattr(new_publisher.counters[0], 'name'),
                         'a_update')

    def test_multiple_counter_pipeline(self):
        self.pipeline_cfg[0]['counters'] = ['a', 'b']
        pipeline_manager = pipeline.PipelineManager(self.pipeline_cfg,
                                                    self.transformer_manager)
        with pipeline_manager.publisher(None, None) as p:
            p([self.test_counter,
               self.test_counter._replace(name='b')])

        publisher = pipeline_manager.pipelines[0].publishers[0]
        self.assertEqual(len(publisher.counters), 2)
        self.assertEqual(getattr(publisher.counters[0], 'name'), 'a_update')
        self.assertEqual(getattr(publisher.counters[1], 'name'), 'b_update')

    def test_flush_pipeline_cache(self):
        CACHE_SIZE = 10
        self.pipeline_cfg[0]['transformers'].extend([
            {
                'name': 'cache',
                'parameters': {
                    'size': CACHE_SIZE,
                }
            },
            {
                'name': 'update',
                'parameters':
                {
                    'append_name': '_new'
                }
            }, ]
        )
        pipeline_manager = pipeline.PipelineManager(self.pipeline_cfg,
                                                    self.transformer_manager)
        pipe = pipeline_manager.pipelines[0]

        pipe.publish_counter(None, self.test_counter, None)
        publisher = pipeline_manager.pipelines[0].publishers[0]
        self.assertEqual(len(publisher.counters), 0)
        pipe.flush(None, None)
        self.assertEqual(len(publisher.counters), 0)
        pipe.publish_counter(None, self.test_counter, None)
        pipe.flush(None, None)
        self.assertEqual(len(publisher.counters), 0)
        for i in range(CACHE_SIZE - 2):
            pipe.publish_counter(None, self.test_counter, None)
        pipe.flush(None, None)
        self.assertEqual(len(publisher.counters), CACHE_SIZE)
        self.assertTrue(getattr(publisher.counters[0], 'name')
                        == 'a_update_new')

    def test_flush_pipeline_cache_multiple_counter(self):
        CACHE_SIZE = 3
        self.pipeline_cfg[0]['transformers'].extend([
            {
                'name': 'cache',
                'parameters': {
                    'size': CACHE_SIZE
                }
            },
            {
                'name': 'update',
                'parameters':
                {
                    'append_name': '_new'
                }
            }, ]
        )
        self.pipeline_cfg[0]['counters'] = ['a', 'b']
        pipeline_manager = pipeline.PipelineManager(self.pipeline_cfg,
                                                    self.transformer_manager)
        with pipeline_manager.publisher(None, None) as p:
            p([self.test_counter,
               self.test_counter._replace(name='b')])

        publisher = pipeline_manager.pipelines[0].publishers[0]
        self.assertEqual(len(publisher.counters), 0)

        with pipeline_manager.publisher(None, None) as p:
            p([self.test_counter])

        self.assertEqual(len(publisher.counters), CACHE_SIZE)
        self.assertEqual(getattr(publisher.counters[0], 'name'),
                         'a_update_new')
        self.assertEqual(getattr(publisher.counters[1], 'name'),
                         'b_update_new')

    def test_flush_pipeline_cache_before_publisher(self):
        self.pipeline_cfg[0]['transformers'].append({
            'name': 'cache',
            'parameters': {}
        })
        pipeline_manager = pipeline.PipelineManager(self.pipeline_cfg,
                                                    self.transformer_manager)
        pipe = pipeline_manager.pipelines[0]

        publisher = pipe.publishers[0]
        pipe.publish_counter(None, self.test_counter, None)
        self.assertEqual(len(publisher.counters), 0)
        pipe.flush(None, None)
        self.assertEqual(len(publisher.counters), 1)
        self.assertEqual(getattr(publisher.counters[0], 'name'),
                         'a_update')

    def test_variable_counter(self):
        self.pipeline_cfg = [{
            'name': "test_pipeline",
            'interval': 5,
            'counters': ['a:*'],
            'transformers': [
                {'name': "update",
                 'parameters': {}}
            ],
            'publishers': ["test://"],
        }, ]
        pipeline_manager = pipeline.PipelineManager(self.pipeline_cfg,
                                                    self.transformer_manager)

        self.test_counter = self.test_counter._replace(name='a:b')

        with pipeline_manager.publisher(None, None) as p:
            p([self.test_counter])

        publisher = pipeline_manager.pipelines[0].publishers[0]
        self.assertEqual(len(publisher.counters), 1)
        self.assertTrue(len(self.TransformerClass.samples) == 1)
        self.assertEqual(getattr(publisher.counters[0], "name"),
                         'a:b_update')
        self.assertTrue(getattr(self.TransformerClass.samples[0], "name")
                        == 'a:b')
