..
      Copyright 2010-2011 United States Government as represented by the
      Administrator of the National Aeronautics and Space Administration.
      All Rights Reserved.

      Licensed under the Apache License, Version 2.0 (the "License"); you may
      not use this file except in compliance with the License. You may obtain
      a copy of the License at

          http://www.apache.org/licenses/LICENSE-2.0

      Unless required by applicable law or agreed to in writing, software
      distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
      WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
      License for the specific language governing permissions and limitations
      under the License.

API Endpoint
============

Vsm has a system for managing multiple APIs on different subdomains.
Currently there is support for the OpenStack API, as well as the Amazon EC2
API.

Common Components
-----------------

The :mod:`monitor.api` Module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. automodule:: monitor.api
    :noindex:
    :members:
    :undoc-members:
    :show-inheritance:

The :mod:`monitor.api.cloud` Module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: monitor.api.cloud
    :noindex:
    :members:
    :undoc-members:
    :show-inheritance:

OpenStack API
-------------

The :mod:`openstack` Module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. automodule:: monitor.api.openstack
    :noindex:
    :members:
    :undoc-members:
    :show-inheritance:

The :mod:`auth` Module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. automodule:: monitor.api.openstack.auth
    :noindex:
    :members:
    :undoc-members:
    :show-inheritance:

EC2 API
-------

The :mod:`monitor.api.ec2` Module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: monitor.api.ec2
    :noindex:
    :members:
    :undoc-members:
    :show-inheritance:

The :mod:`cloud` Module
~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: monitor.api.ec2.cloud
    :noindex:
    :members:
    :undoc-members:
    :show-inheritance:

The :mod:`metadatarequesthandler` Module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: monitor.api.ec2.metadatarequesthandler
    :noindex:
    :members:
    :undoc-members:
    :show-inheritance:

Tests
-----

The :mod:`api_unittest` Module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: monitor.tests.api_unittest
    :noindex:
    :members:
    :undoc-members:
    :show-inheritance:

The :mod:`api_integration` Module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: monitor.tests.api_integration
    :noindex:
    :members:
    :undoc-members:
    :show-inheritance:

The :mod:`cloud_unittest` Module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: monitor.tests.cloud_unittest
    :noindex:
    :members:
    :undoc-members:
    :show-inheritance:

The :mod:`api.fakes` Module
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: monitor.tests.api.fakes
    :noindex:
    :members:
    :undoc-members:
    :show-inheritance:

The :mod:`api.test_wsgi` Module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: monitor.tests.api.test_wsgi
    :noindex:
    :members:
    :undoc-members:
    :show-inheritance:

The :mod:`test_api` Module
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: monitor.tests.api.openstack.test_api
    :noindex:
    :members:
    :undoc-members:
    :show-inheritance:

The :mod:`test_auth` Module
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: monitor.tests.api.openstack.test_auth
    :noindex:
    :members:
    :undoc-members:
    :show-inheritance:

The :mod:`test_faults` Module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: monitor.tests.api.openstack.test_faults
    :noindex:
    :members:
    :undoc-members:
    :show-inheritance:
