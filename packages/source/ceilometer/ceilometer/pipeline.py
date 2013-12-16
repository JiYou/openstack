# -*- encoding: utf-8 -*-
#
# Copyright © 2013 Intel Corp.
#
# Author: Yunhong Jiang <yunhong.jiang@intel.com>
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

import itertools
import os

from oslo.config import cfg
import yaml

from ceilometer.openstack.common import log
from ceilometer import publisher


OPTS = [
    cfg.StrOpt('pipeline_cfg_file',
               default="pipeline.yaml",
               help="Configuration file for pipeline definition"
               ),
]

cfg.CONF.register_opts(OPTS)

LOG = log.getLogger(__name__)


class PipelineException(Exception):
    def __init__(self, message, pipeline_cfg):
        self.msg = message
        self.pipeline_cfg = pipeline_cfg

    def __str__(self):
        return 'Pipeline %s: %s' % (self.pipeline_cfg, self.msg)


class PublishContext(object):

    def __init__(self, context, source, pipelines=[]):
        self.pipelines = set(pipelines)
        self.context = context
        self.source = source

    def add_pipelines(self, pipelines):
        self.pipelines.update(pipelines)

    def __enter__(self):
        def p(counters):
            for p in self.pipelines:
                p.publish_counters(self.context,
                                   counters,
                                   self.source)
        return p

    def __exit__(self, exc_type, exc_value, traceback):
        for p in self.pipelines:
            p.flush(self.context, self.source)


class Pipeline(object):
    """Sample handling pipeline

    Pipeline describes a chain of handlers. The chain starts with
    tranformer and ends with one or more publishers.

    The first transformer in the chain gets counter from data collector, i.e.
    pollster or notification handler, takes some action like dropping,
    aggregation, changing field etc, then passes the updated counter
    to next step.

    The subsequent transformers, if any, handle the data similarly.

    In the end of the chain, publishers publish the data. The exact publishing
    method depends on publisher type, for example, pushing into data storage
    through message bus, sending to external CW software through CW API call.

    If no transformer is included in the chain, the publishers get counters
    from data collector and publish them directly.

    """

    def __init__(self, cfg, transformer_manager):
        self.cfg = cfg

        try:
            self.name = cfg['name']
            try:
                self.interval = int(cfg['interval'])
            except ValueError:
                raise PipelineException("Invalid interval value", cfg)
            self.counters = cfg['counters']
            # It's legal to have no transformer specified
            self.transformer_cfg = cfg['transformers'] or []
        except KeyError as err:
            raise PipelineException(
                "Required field %s not specified" % err.args[0], cfg)

        if self.interval <= 0:
            raise PipelineException("Interval value should > 0", cfg)

        self._check_counters()

        if not cfg.get('publishers'):
            raise PipelineException("No publisher specified", cfg)

        self.publishers = []
        for p in cfg['publishers']:
            if '://' not in p:
                # Support old format without URL
                p = p + "://"
            try:
                self.publishers.append(publisher.get_publisher(p))
            except Exception:
                LOG.exception("Unable to load publisher %s", p)

        self.transformers = self._setup_transformers(cfg, transformer_manager)

    def __str__(self):
        return self.name

    def _check_counters(self):
        """Counter rules checking

        At least one meaningful counter exist
        Included type and excluded type counter can't co-exist at
        the same pipeline
        Included type counter and wildcard can't co-exist at same pipeline

        """
        counters = self.counters
        if not counters:
            raise PipelineException("No counter specified", self.cfg)

        if [x for x in counters if x[0] not in '!*'] and \
           [x for x in counters if x[0] == '!']:
            raise PipelineException(
                "Both included and excluded counters specified",
                cfg)

        if '*' in counters and [x for x in counters if x[0] not in '!*']:
            raise PipelineException(
                "Included counters specified with wildcard",
                self.cfg)

    def _setup_transformers(self, cfg, transformer_manager):
        transformer_cfg = cfg['transformers'] or []
        transformers = []
        for transformer in transformer_cfg:
            parameter = transformer['parameters'] or {}
            try:
                ext = transformer_manager.get_ext(transformer['name'])
            except KeyError:
                raise PipelineException(
                    "No transformer named %s loaded" % transformer['name'],
                    cfg)
            transformers.append(ext.plugin(**parameter))
            LOG.info("Pipeline %s: Setup transformer instance %s "
                     "with parameter %s",
                     self,
                     transformer['name'],
                     parameter)

        return transformers

    def _transform_counter(self, start, ctxt, counter, source):
        try:
            for transformer in self.transformers[start:]:
                counter = transformer.handle_sample(ctxt, counter, source)
                if not counter:
                    LOG.debug("Pipeline %s: Counter dropped by transformer %s",
                              self, transformer)
                    return
            return counter
        except Exception as err:
            LOG.warning("Pipeline %s: Exit after error from transformer"
                        "%s for %s",
                        self, transformer, counter)
            LOG.exception(err)

    def _publish_counters(self, start, ctxt, counters, source):
        """Push counter into pipeline for publishing.

        param start: the first transformer that the counter will be injected.
                     This is mainly for flush() invocation that transformer
                     may emit counters
        param ctxt: execution context from the manager or service
        param counters: counter list
        param source: counter source

        """

        transformed_counters = []
        for counter in counters:
            LOG.audit("Pipeline %s: Transform counter %s from %s transformer",
                      self, counter, start)
            counter = self._transform_counter(start, ctxt, counter, source)
            if counter:
                transformed_counters.append(counter)

        LOG.audit("Pipeline %s: Publishing counters", self)

        for p in self.publishers:
            try:
                p.publish_counters(ctxt, transformed_counters, source)
            except Exception:
                LOG.exception("Pipeline %s: Continue after error "
                              "from publisher %s", self, p)

        LOG.audit("Pipeline %s: Published counters", self)

    def publish_counter(self, ctxt, counter, source):
        self.publish_counters(ctxt, [counter], source)

    def publish_counters(self, ctxt, counters, source):
        for counter_name, counters in itertools.groupby(
                sorted(counters, key=lambda c: c.name),
                lambda c: c.name):
            if self.support_counter(counter_name):
                self._publish_counters(0, ctxt, counters, source)

    # (yjiang5) To support counters like instance:m1.tiny,
    # which include variable part at the end starting with ':'.
    # Hope we will not add such counters in future.
    def _variable_counter_name(self, name):
        m = name.partition(':')
        if m[1] == ':':
            return m[1].join((m[0], '*'))
        else:
            return name

    def support_counter(self, counter_name):
        counter_name = self._variable_counter_name(counter_name)
        if ('!' + counter_name) in self.counters:
            return False
        if '*' in self.counters:
            return True
        elif self.counters[0][0] == '!':
            return not ('!' + counter_name) in self.counters
        else:
            return counter_name in self.counters

    def flush(self, ctxt, source):
        """Flush data after all counter have been injected to pipeline."""

        LOG.audit("Flush pipeline %s", self)
        for (i, transformer) in enumerate(self.transformers):
            try:
                self._publish_counters(i + 1, ctxt,
                                       list(transformer.flush(ctxt, source)),
                                       source)
            except Exception as err:
                LOG.warning(
                    "Pipeline %s: Error flushing "
                    "transformer %s",
                    self, transformer)
                LOG.exception(err)

    def get_interval(self):
        return self.interval


class PipelineManager(object):
    """Pipeline Manager

    Pipeline manager sets up pipelines according to config file

    Usually only one pipeline manager exists in the system.

    """

    def __init__(self, cfg,
                 transformer_manager):
        """Setup the pipelines according to config.

        The top of the cfg is a list of pipeline definitions.

        Pipeline definition is an dictionary specifying the target counters,
        the tranformers involved, and the target publishers:
        {
            "name": pipeline_name
            "interval": interval_time
            "counters" :  ["counter_1", "counter_2"],
            "tranformers":[
                              {"name": "Transformer_1",
                               "parameters": {"p1": "value"}},

                               {"name": "Transformer_2",
                               "parameters": {"p1": "value"}},
                           ]
            "publishers": ["publisher_1", "publisher_2"]
        }

        Interval is how many seconds should the counters be injected to
        the pipeline.

        Valid counter format is '*', '!counter_name', or 'counter_name'.
        '*' is wildcard symbol means any counters; '!counter_name' means
        "counter_name" will be excluded; 'counter_name' means 'counter_name'
        will be included.

        The 'counter_name" is Counter namedtuple's name field. For counter
        names with variable like "instance:m1.tiny", it's "instance:*", as
        returned by get_counter_list().

        Valid counters definition is all "included counter names", all
        "excluded counter names", wildcard and "excluded counter names", or
        only wildcard.

        Transformer's name is plugin name in setup.py.

        Publisher's name is plugin name in setup.py

        """
        self.pipelines = [Pipeline(pipedef, transformer_manager)
                          for pipedef in cfg]

    def publisher(self, context, source):
        """Build a new Publisher for these manager pipelines.

        :param context: The context.
        :param source: Counter source.
        """
        return PublishContext(context, source, self.pipelines)


def setup_pipeline(transformer_manager):
    """Setup pipeline manager according to yaml config file."""
    cfg_file = cfg.CONF.pipeline_cfg_file
    if not os.path.exists(cfg_file):
        cfg_file = cfg.CONF.find_file(cfg_file)

    LOG.debug("Pipeline config file: %s", cfg_file)

    with open(cfg_file) as fap:
        data = fap.read()

    pipeline_cfg = yaml.safe_load(data)
    LOG.info("Pipeline config: %s", pipeline_cfg)

    return PipelineManager(pipeline_cfg,
                           transformer_manager)
