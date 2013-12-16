The :program:`monitor` shell utility
=========================================

.. program:: monitor
.. highlight:: bash

The :program:`monitor` shell utility interacts with the OpenStack Vsm API
from the command line. It supports the entirety of the OpenStack Vsm API.

You'll need to provide :program:`monitor` with your OpenStack username and
API key. You can do this with the :option:`--os-username`, :option:`--os-password`
and :option:`--os-tenant-name` options, but it's easier to just set them as
environment variables by setting two environment variables:

.. envvar:: OS_USERNAME or CINDER_USERNAME

    Your OpenStack Vsm username.

.. envvar:: OS_PASSWORD or CINDER_PASSWORD

    Your password.

.. envvar:: OS_TENANT_NAME or CINDER_PROJECT_ID

    Project for work.

.. envvar:: OS_AUTH_URL or CINDER_URL

    The OpenStack API server URL.

.. envvar:: OS_VOLUME_API_VERSION

    The OpenStack Block Storage API version.

For example, in Bash you'd use::

    export OS_USERNAME=yourname
    export OS_PASSWORD=yadayadayada
    export OS_TENANT_NAME=myproject
    export OS_AUTH_URL=http://...
    export OS_VOLUME_API_VERSION=1

From there, all shell commands take the form::

    monitor <command> [arguments...]

Run :program:`monitor help` to get a full list of all possible commands,
and run :program:`monitor help <command>` to get detailed help for that
command.
