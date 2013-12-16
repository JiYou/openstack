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
"""Test API against MongoDB.
"""
from . import compute_duration_by_resource as cdbr
from . import list_events
from . import list_meters
from . import list_projects
from . import list_resources
from . import list_sources
from . import list_users
from . import max_project_volume
from . import max_resource_volume
from . import sum_project_volume
from . import sum_resource_volume


class TestListEvents(list_events.TestListEvents):
    database_connection = 'mongodb://__test__'


class TestListEventsMetaQuery(list_events.TestListEventsMetaquery):
    database_connection = 'mongodb://__test__'


class TestListEmptyMeters(list_meters.TestListEmptyMeters):
    database_connection = 'mongodb://__test__'


class TestListMeters(list_meters.TestListMeters):
    database_connection = 'mongodb://__test__'


class TestListMetersMetaquery(list_meters.TestListMetersMetaquery):
    database_connection = 'mongodb://__test__'


class TestListEmptyUsers(list_users.TestListEmptyUsers):
    database_connection = 'mongodb://__test__'


class TestListUsers(list_users.TestListUsers):
    database_connection = 'mongodb://__test__'


class TestListEmptyProjects(list_projects.TestListEmptyProjects):
    database_connection = 'mongodb://__test__'


class TestListProjects(list_projects.TestListProjects):
    database_connection = 'mongodb://__test__'


class TestComputeDurationByResource(cdbr.TestComputeDurationByResource):
    database_connection = 'mongodb://__test__'


class TestListEmptyResources(list_resources.TestListEmptyResources):
    database_connection = 'mongodb://__test__'


class TestListResources(list_resources.TestListResources):
    database_connection = 'mongodb://__test__'


class TestListResourcesMetaquery(list_resources.TestListResourcesMetaquery):
    database_connection = 'mongodb://__test__'


class TestListSource(list_sources.TestListSource):
    database_connection = 'mongodb://__test__'


class TestMaxProjectVolume(max_project_volume.TestMaxProjectVolume):
    database_connection = 'mongodb://__test__'


class TestMaxResourceVolume(max_resource_volume.TestMaxResourceVolume):
    database_connection = 'mongodb://__test__'


class TestSumProjectVolume(sum_project_volume.TestSumProjectVolume):
    database_connection = 'mongodb://__test__'


class TestSumResourceVolume(sum_resource_volume.TestSumResourceVolume):
    database_connection = 'mongodb://__test__'
