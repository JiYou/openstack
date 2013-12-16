#!/usr/bin/python
# Copyright 2012 OpenStack, LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from setuptools import setup

import swift3


setup(name='swift3',
      version=swift3.version,
      description='Swift AmazonS3 API emulation Middleware',
      author='OpenStack, LLC.',
      author_email='openstack@lists.launchpad.net',
      url='https://github.com/fujita/swift3',
      packages=['swift3'],
      requires=['swift(>=1.4)'],
      entry_points={'paste.filter_factory':
                        ['swift3=swift3.middleware:filter_factory']})
