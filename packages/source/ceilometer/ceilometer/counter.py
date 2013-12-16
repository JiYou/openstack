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
"""Counter class for holding data about a metering event.

A Counter doesn't really do anything, but we need a way to
ensure that all of the appropriate fields have been filled
in by the plugins that create them.
"""

import collections

from oslo.config import cfg


OPTS = [
    cfg.StrOpt('counter_source',
               default='openstack',
               help='Source for counters emited on this instance'),
]

cfg.CONF.register_opts(OPTS)


# Fields explanation:
#
# Name: the name of the counter, must be unique
# Type: the type of the counter, must be either:
#       - cumulative: the value is incremented and never reset to 0
#       - delta: the value is reset to 0 each time it is sent
#       - gauge: the value is an absolute value and is not a counter
# Unit: the unit of the counter
# Volume: the counter value
# User ID: the user ID
# Project ID: the project ID
# Resource ID: the resource ID
# Timestamp: when the counter has been read
# Resource metadata: various metadata
Counter = collections.namedtuple('Counter',
                                 ' '.join([
                                     'name',
                                     'type',
                                     'unit',
                                     'volume',
                                     'user_id',
                                     'project_id',
                                     'resource_id',
                                     'timestamp',
                                     'resource_metadata',
                                 ]))


TYPE_GAUGE = 'gauge'
TYPE_DELTA = 'delta'
TYPE_CUMULATIVE = 'cumulative'
