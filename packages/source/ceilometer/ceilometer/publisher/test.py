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
"""Publish a counter in memory, useful for testing
"""

from ceilometer import publisher


class TestPublisher(publisher.PublisherBase):
    """Publisher used in unit testing."""

    def __init__(self, parsed_url):
        self.counters = []

    def publish_counters(self, context, counters, source):
        """Send a metering message for publishing

        :param context: Execution context from the service or RPC call
        :param counter: Counter from pipeline after transformation
        :param source: counter source
        """
        self.counters.extend(counters)
