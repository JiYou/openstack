..
      Copyright 2012 New Dream Network, LLC (DreamHost)

      Licensed under the Apache License, Version 2.0 (the "License"); you may
      not use this file except in compliance with the License. You may obtain
      a copy of the License at

          http://www.apache.org/licenses/LICENSE-2.0

      Unless required by applicable law or agreed to in writing, software
      distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
      WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
      License for the specific language governing permissions and limitations
      under the License.

=========================
 Working with the Source
=========================

Setting up a Development Sandbox
================================

1. Set up a server or virtual machine to run OpenStack using
   devstack_.

.. _devstack: http://www.devstack.org/

2. Clone the ceilometer project to the machine::

    $ cd /opt/stack
    $ git clone https://github.com/openstack/ceilometer.git
    $ cd ./ceilometer

3. Once this is done, you need to setup the review process::

    $ git remote add gerrit ssh://<username>@review.openstack.org:29418/openstack/ceilometer.git

4. If you are preparing a patch, create a topic branch and switch to
   it before making any changes::

    $ git checkout -b TOPIC-BRANCH

Running the Tests
=================

Ceiloemter includes an extensive set of automated unit tests which are
run through tox_.

1. Install ``tox``::

   $ sudo pip install tox

2. Install the test dependencies::

   $ sudo pip install -r /opt/stack/ceilometer/test-requirements.txt

3. Run the unit and code-style tests::

   $ cd /opt/stack/ceilometer
   $ tox -e py27,pep8

   As tox is a wrapper around nose, it also accepts the same flags as nosetests.
   See the `nose options documentation`_ for details about these additional flags.

.. _nose options documentation: http://readthedocs.org/docs/nose/en/latest/usage.html#options

   Use a double hyphen to pass options to nose. For example, to set verbose
   flag and to run only tests under tests/api/v2::

      $ tox -e py27 -- -v api/v2

.. seealso::

   * tox_

.. _tox: http://tox.testrun.org/latest/

Code Reviews
============

Ceilometer uses the OpenStack review process for all code and
developer documentation contributions. Code reviews are managed
through gerrit.

.. seealso::

   * http://wiki.openstack.org/GerritWorkflow
   * `OpenStack Gerrit instance`_.

.. _OpenStack Gerrit instance: https://review.openstack.org/#/q/status:open+project:openstack/ceilometer,n,z
