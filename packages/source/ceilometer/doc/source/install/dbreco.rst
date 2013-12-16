..
      Copyright 2013 Nicolas Barcet for eNovance

      Licensed under the Apache License, Version 2.0 (the "License"); you may
      not use this file except in compliance with the License. You may obtain
      a copy of the License at

          http://www.apache.org/licenses/LICENSE-2.0

      Unless required by applicable law or agreed to in writing, software
      distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
      WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
      License for the specific language governing permissions and limitations
      under the License.

=============================
 Choosing a database backend
=============================

Selecting a database backend for Ceilometer should not be done lightly for
numerous reasons:

1. Not all backend drivers are equally implemented and tested.  To help you
   make your choice, the table below will give you some idea of the
   status of each of the drivers available in trunk.  Note that we do welcome
   patches to improve completeness and quality of drivers.

2. It may not be a good idea to use the same host as another database as
   Ceilometer can generate a LOT OF WRITES. For this reason it is generally
   recommended, if the deployment is targeting going into production, to use
   a dedicated host, or at least a VM which will be migratable to another
   physical host if needed. The following spreadsheet can help you get an
   idea of the volumes that ceilometer can generate:
   `Google spreadsheet <https://docs.google.com/a/enovance.com/spreadsheet/ccc?key=0AtziNGvs-uPudDhRbEJJOHFXV3d0ZGc1WE9NLTVPX0E#gid=0>`_

3. If you are relying on this backend to bill customers, you will note that
   your capacity to generate revenue is very much linked to its reliability,
   which seems to be a factor dear to many managers.

The following is a table indicating the status of each database drivers:

================== ============= ================= ==============
Driver             API Complete  Storage Complete  Production Use
================== ============= ================= ==============
MongoDB            Yes           Yes               Multiple
mysql, postgresql  No            Yes               None known
HBASE              No            Yes               None known
================== ============= ================= ==============
