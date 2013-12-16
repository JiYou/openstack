# Copyright 2011 OpenStack, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import setuptools


from monitorclient.openstack.common import setup

requires = setup.parse_requirements()
depend_links = setup.parse_dependency_links()
tests_require = setup.parse_requirements(['tools/test-requires'])
project = 'python-monitorclient'


def read_file(file_name):
    return open(os.path.join(os.path.dirname(__file__), file_name)).read()


setuptools.setup(
    name=project,
    version=setup.get_version(project),
    author="OpenStack Contributors",
    author_email="openstack-dev@lists.openstack.org",
    description="Client library for OpenStack Monitor API.",
    long_description=read_file("README.rst"),
    license="Apache License, Version 2.0",
    url="https://github.com/openstack/python-monitorclient",
    packages=setuptools.find_packages(exclude=['tests', 'tests.*']),
    cmdclass=setup.get_cmdclass(),
    install_requires=requires,
    tests_require=tests_require,
    setup_requires=['setuptools-git>=0.4'],
    include_package_data=True,
    dependency_links=depend_links,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Environment :: OpenStack",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python"
    ],
    entry_points={
        "console_scripts": ["monitor = monitorclient.shell:main"]
    }
)
