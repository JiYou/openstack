..
      Copyright 2012 Nicolas Barcet for Canonical

      Licensed under the Apache License, Version 2.0 (the "License"); you may
      not use this file except in compliance with the License. You may obtain
      a copy of the License at

          http://www.apache.org/licenses/LICENSE-2.0

      Unless required by applicable law or agreed to in writing, software
      distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
      WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
      License for the specific language governing permissions and limitations
      under the License.

==================================================
Welcome to the Ceilometer developer documentation!
==================================================

The :term:`ceilometer` project aims to deliver a unique point of
contact for billing systems to acquire all of the measurements they
need to establish customer billing, across all current OpenStack core
components with work underway to support future OpenStack components.

What is the purpose of the project and vision for it?
=====================================================

* Provide efficient collection of metering data, in terms of CPU and
  network costs.
* Allow deployers to integrate with the metering system directly or by
  replacing components.
* Data may be collected by monitoring notifications sent from existing
  services or by polling the infrastructure.
* Allow deployers to configure the type of data collected to meet
  their operating requirements.
* The data collected by the metering system is made visible to some
  users through a REST API.
* The metering messages are signed and :term:`non-repudiable`.

This documentation offers information on how ceilometer works and how to
contribute to the project.

Table of contents
=================

.. toctree::
   :maxdepth: 2

   architecture
   measurements
   install/index
   configuration
   webapi/index
   contributing/index
   releasenotes/index
   glossary

.. - installation
..   - devstack
..   - take content from "initial setup"
.. - configuration
..   - talk about copying nova config file
.. - running the services
..   - agent on compute node
..   - collector on controller (non-compute) node
.. - contributing
..   - joining the project (take this from another set of docs?)
..   - reporting bugs
..   - running tests
..   - submitting patches for review
.. - writing plugins
..   - general plugin-based architecture information
..     - reference to setuptools entry points docs
..   - pollsters
..   - notifications
..   - database engine

.. update index

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

To Do
=====

.. todolist::
