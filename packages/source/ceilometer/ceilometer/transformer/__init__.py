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

import abc
from stevedore import extension


class TransformerExtensionManager(extension.ExtensionManager):

    def __init__(self, namespace):
        super(TransformerExtensionManager, self).__init__(
            namespace=namespace,
            invoke_on_load=False,
            invoke_args=(),
            invoke_kwds={}
        )
        self.by_name = dict((e.name, e) for e in self.extensions)

    def get_ext(self, name):
        return self.by_name[name]


class TransformerBase(object):
    """Base class for plugins that transform the counter."""

    __metaclass__ = abc.ABCMeta

    def __init__(self, **kwargs):
        """Setup transformer.

        Each time a transformed is involved in a pipeline, a new transformer
        instance is created and chained into the pipeline. i.e. transformer
        instance is per pipeline. This helps if transformer need keep some
        cache and per-pipeline information.

        :param kwargs: The parameters that are defined in pipeline config file.
        """
        super(TransformerBase, self).__init__()

    @abc.abstractmethod
    def handle_sample(self, context, counter, source):
        """Transform a counter.

        :param context: Passed from the data collector.
        :param counter: A counter.
        :param source: Passed from data collector.
        """

    def flush(self, context, source):
        """Flush counters cached previously.

        :param context: Passed from the data collector.
        :param source: Source of counters that are being published.
        """
        return []
