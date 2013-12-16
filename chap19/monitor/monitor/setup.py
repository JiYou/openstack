# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import setuptools

from monitor.openstack.common import setup as common_setup

requires = common_setup.parse_requirements()
depend_links = common_setup.parse_dependency_links()
project = 'monitor'

filters = [
    "AvailabilityZoneFilter = "
    "monitor.openstack.common.scheduler.filters."
    "availability_zone_filter:AvailabilityZoneFilter",
    "CapabilitiesFilter = "
    "monitor.openstack.common.scheduler.filters."
    "capabilities_filter:CapabilitiesFilter",
    "CapacityFilter = "
    "monitor.scheduler.filters.capacity_filter:CapacityFilter",
    "JsonFilter = "
    "monitor.openstack.common.scheduler.filters.json_filter:JsonFilter",
    "RetryFilter = "
    "monitor.scheduler.filters.retry_filter:RetryFilter",
]

weights = [
    "CapacityWeigher = monitor.scheduler.weights.capacity:CapacityWeigher",
]

setuptools.setup(
    name=project,
    version=common_setup.get_version(project, '2013.1.1'),
    description='ServiceManage Manage Service',
    author='OpenStack',
    author_email='monitor@lists.launchpad.net',
    url='http://www.openstack.org/',
    classifiers=[
        'Environment :: OpenStack',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ],
    cmdclass=common_setup.get_cmdclass(),
    packages=setuptools.find_packages(exclude=['bin', 'smoketests']),
    install_requires=requires,
    dependency_links=depend_links,
    entry_points={
        'monitor.scheduler.filters': filters,
        'monitor.scheduler.weights': weights,
    },
    include_package_data=True,
    test_suite='nose.collector',
    setup_requires=['setuptools_git>=0.4'],
    scripts=['bin/monitor-all',
             'bin/monitor-api',
             'bin/monitor-conductor',
             'bin/monitor-agent',
             'bin/monitor-manage'],
    py_modules=[])
