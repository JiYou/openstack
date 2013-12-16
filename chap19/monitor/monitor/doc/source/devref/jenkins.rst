Continuous Integration with Jenkins
===================================

Vsm uses a `Jenkins`_ server to automate development tasks. The Jenkins
front-end is at http://jenkins.openstack.org. You must have an
account on `Launchpad`_ to be able to access the OpenStack Jenkins site.

Jenkins performs tasks such as:

`gate-monitor-unittests`_
    Run unit tests on proposed code changes that have been reviewed.

`gate-monitor-pep8`_
    Run PEP8 checks on proposed code changes that have been reviewed.

`gate-monitor-merge`_
    Merge reviewed code into the git repository.

`monitor-coverage`_
    Calculate test coverage metrics.

`monitor-docs`_
    Build this documentation and push it to http://monitor.openstack.org.

`monitor-pylint`_
    Run `pylint <http://www.logilab.org/project/pylint>`_ on the monitor code and
    report violations.

`monitor-tarball`_
    Do ``python setup.py sdist`` to create a tarball of the monitor code and upload
    it to http://monitor.openstack.org/tarballs

.. _Jenkins: http://jenkins-ci.org
.. _Launchpad: http://launchpad.net
.. _gate-monitor-merge: https://jenkins.openstack.org/view/Vsm/job/gate-monitor-merge
.. _gate-monitor-pep8: https://jenkins.openstack.org/view/Vsm/job/gate-monitor-pep8
.. _gate-monitor-unittests: https://jenkins.openstack.org/view/Vsm/job/gate-monitor-unittests
.. _monitor-coverage: https://jenkins.openstack.org/view/Vsm/job/monitor-coverage
.. _monitor-docs: https://jenkins.openstack.org/view/Vsm/job/monitor-docs
.. _monitor-pylint: https://jenkins.openstack.org/job/monitor-pylint
.. _monitor-tarball: https://jenkins.openstack.org/job/monitor-tarball
