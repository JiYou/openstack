How to use this dashboard?
==========================

Assume your horizon is deployed in /opt/stack/horizon/

Follow the commands below:


    $ visualizations# ls

    dashboard.py  flocking  __init__.py  README.rst  settings.py  static  templates

    $ mv settings.py /opt/stack/horizon/openstack_dashboard/

    $ cd ..

    $ ls

    visualizations

    $ mv visualizations /opt/stack/horizon/openstack_dashboard/dashboards/

    $ service apache2 restart


Then you can see the added new dashboards.
