..
      Copyright 2013 New Dream Network, LLC (DreamHost)

      Licensed under the Apache License, Version 2.0 (the "License"); you may
      not use this file except in compliance with the License. You may obtain
      a copy of the License at

          http://www.apache.org/licenses/LICENSE-2.0

      Unless required by applicable law or agreed to in writing, software
      distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
      WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
      License for the specific language governing permissions and limitations
      under the License.

====================================
 Installing the API Behind mod_wsgi
====================================

Ceilometer comes with a few example files for configuring the API
service to run behind Apache with ``mod_wsgi``.

app.wsgi
========

The file ``ceilometer/api/app.wsgi`` sets up the V2 API WSGI
application. The file is installed with the rest of the ceilometer
application code, and should not need to be modified.

etc/apache2/ceilometer
======================

The ``etc/apache2/ceilometer`` file contains example settings that
work with a copy of ceilometer installed via devstack.

.. literalinclude:: ../../../etc/apache2/ceilometer

1. Copy or symlink the file to ``/etc/apache2/sites-avilable``.

2. Modify the ``VirtualHost`` directive, setting a hostname or IP for
   the service. The default settings assume that the ceilometer API is
   the only service running on the local Apache instance, which
   conflicts with Horizon's default configuration.

3. Modify the ``WSGIDaemonProcess`` directive to set the
  ``user`` and ``group`` values to a user available on your server.

4. Modify the ``APACHE_RUN_USER`` and ``APACHE_RUN_GROUP`` values to
   the name of a user and group available on your server.

5. Enable the ceilometer site.

   ::

      $ a2ensite ceilometer
      $ service apache2 reload
