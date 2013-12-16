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
"""Test API against SQLAlchemy.
"""
import compute_duration_by_resource as cdbr
import list_events
import list_meters
import list_projects
import list_resources
import list_sources
import list_users
import max_project_volume
import max_resource_volume
import sum_project_volume
import sum_resource_volume


class TestListEvents(list_events.TestListEvents):
    database_connection = 'sqlite://'


class TestListEmptyMeters(list_meters.TestListEmptyMeters):
    database_connection = 'sqlite://'


class TestListMeters(list_meters.TestListMeters):
    database_connection = 'sqlite://'


class TestListEmptyUsers(list_users.TestListEmptyUsers):
    database_connection = 'sqlite://'


class TestListUsers(list_users.TestListUsers):
    database_connection = 'sqlite://'


class TestListEmptyProjects(list_projects.TestListEmptyProjects):
    database_connection = 'sqlite://'


class TestListProjects(list_projects.TestListProjects):
    database_connection = 'sqlite://'


class TestComputeDurationByResource(cdbr.TestComputeDurationByResource):
    database_connection = 'sqlite://'


class TestListEmptyResources(list_resources.TestListEmptyResources):
    database_connection = 'sqlite://'


class TestListResources(list_resources.TestListResources):
    database_connection = 'sqlite://'


class TestListSource(list_sources.TestListSource):
    database_connection = 'sqlite://'


class TestMaxProjectVolume(max_project_volume.TestMaxProjectVolume):
    database_connection = 'sqlite://'


class TestMaxResourceVolume(max_resource_volume.TestMaxResourceVolume):
    database_connection = 'sqlite://'


class TestSumProjectVolume(sum_project_volume.TestSumProjectVolume):
    database_connection = 'sqlite://'


class TestSumResourceVolume(sum_resource_volume.TestSumResourceVolume):
    database_connection = 'sqlite://'
