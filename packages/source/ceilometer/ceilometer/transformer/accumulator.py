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

from ceilometer import transformer


class TransformerAccumulator(transformer.TransformerBase):
    """Transformer that accumulates counter until a threshold, and then flush
    them out in the wild.

    """

    def __init__(self, size=1, **kwargs):
        if size >= 1:
            self.counters = []
        self.size = size
        super(TransformerAccumulator, self).__init__(**kwargs)

    def handle_sample(self, context, counter, source):
        if self.size >= 1:
            self.counters.append(counter)
        else:
            return counter

    def flush(self, context, source):
        if len(self.counters) >= self.size:
            x = self.counters
            self.counters = []
            return x
        return []
