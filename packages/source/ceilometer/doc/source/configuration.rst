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

=======================
 Configuration Options
=======================

Ceilometer specific
===================

The following table lists the ceilometer specific options in the global configuration file.
Please note that ceilometer uses openstack-common extensively, which requires that
the other parameters are set appropriately. For information we are listing the configuration
elements that we use after the ceilometer specific elements.

If you use sql alchemy, its specific paramaters will need to be set.


===============================  ====================================  ==============================================================
Parameter                        Default                               Note
===============================  ====================================  ==============================================================
nova_control_exchange            nova                                  Exchange name for Nova notifications
glance_control_exchange          glance                                Exchange name for Glance notifications
cinder_control_exchange          cinder                                Exchange name for Cinder notifications
quantum_control_exchange         quantum                               Exchange name for Quantum notifications
metering_secret                  change this or be hacked              Secret value for signing metering messages
metering_topic                   metering                              the topic ceilometer uses for metering messages
counter_source                   openstack                             The source name of emited counters
control_exchange                 ceilometer                            AMQP exchange to connect to if using RabbitMQ or Qpid
periodic_interval                600                                   seconds between running periodic tasks
database_connection              mongodb://localhost:27017/ceilometer  Database connection string
metering_api_port                8777                                  The port for the ceilometer API server
reseller_prefix                  AUTH\_                                Prefix used by swift for reseller token
===============================  ====================================  ==============================================================

Service polling authentication
==============================

The following options must be placed under a [service_credentials] section
and will be used by Ceilometer to retrieve information from OpenStack
components.

===============================  ====================================  ==============================================================
Parameter                        Default                               Note
===============================  ====================================  ==============================================================
os_username                      ceilometer                            Username to use for openstack service access
os_password                      admin                                 Password to use for openstack service access
os_tenant_id                                                           Tenant ID to use for openstack service access
os_tenant_name                   admin                                 Tenant name to use for openstack service access
os_auth_url                      http://localhost:5000/v2.0            Auth URL to use for openstack service access
===============================  ====================================  ==============================================================

Keystone Middleware Authentication
==================================

The following table lists the Keystone middleware authentication options which are used to get admin token.
Please note that these options need to be under [keystone_authtoken] section.

===============================  ====================================  ==============================================================
Parameter                        Default                               Note
===============================  ====================================  ==============================================================
auth_host                                                              The host providing the Keystone service API endpoint for
                                                                       validating and requesting tokens
auth_port                        35357                                 The port used to validate tokens
auth_protocol                    https                                 The protocol used to validate tokens
auth_uri                         auth_protocol://auth_host:auth_port   The full URI used to validate tokens
admin_token                                                            Either this or the following three options are required. If
                                                                       set, this is a single shared secret with the Keystone
                                                                       configuration used to validate tokens.
admin_user                                                             User name for retrieving admin token
admin_password                                                         Password for retrieving admin token
admin_tenant_name                                                      Tenant name for retrieving admin token
signing_dir                                                            The cache directory for signing certificate
certfile                                                               Required if Keystone server requires client cert
keyfile                                                                Required if Keystone server requires client cert. This can be
                                                                       the same as certfile if the certfile includes the private key.
===============================  ====================================  ==============================================================

SQL Alchemy
===========

==========================  ====================================  ==============================================================
Parameter                   Default                               Note
==========================  ====================================  ==============================================================
sql_connection_debug        0                                     Verbosity of SQL debugging information. 0=None, 100=Everything
sql_connection_trace        False                                 Add python stack traces to SQL as comment strings
sql_idle_timeout            3600                                  timeout before idle sql connections are reaped
sql_max_retries             10                                    maximum db connection retries during startup.
                                                                  (setting -1 implies an infinite retry count)
sql_retry_interval          10                                    interval between retries of opening a sql connection
mysql_engine                InnoDB                                MySQL engine to use
sqlite_synchronous          True                                  If passed, use synchronous mode for sqlite
==========================  ====================================  ==============================================================

HBase
===================

To configure HBase as your database backend:

1. To install an HBase server, for pure development purpose, you can just
download the HBase image from Cloudera and get it up and running. Then the
quickest way to check it is to run the ``HBase shell`` and try a ``list``
command which would return the list of the tables in your HBase server:

 ::

    $ ${HBASE_HOME}/bin/hbase shell

    hbase> list

.. note::
    This driver has been tested against HBase 0.92.1/CDH 4.1.1,
    HBase 0.94.2/CDH 4.2.0, HBase 0.94.4/HDP 1.2 and HBase 0.94.5/Apache.
    Versions earlier than 0.92.1 are not supported due to feature incompatibility.

2. A few HBase tables are expected by Ceilometer.
To create them, run the following:

 ::

    $ ${HBASE_HOME}/bin/hbase shell

    hbase> create 'project', {NAME=>'f'}
    hbase> create 'user', {NAME=>'f'}
    hbase> create 'resource', {NAME=>'f'}
    hbase> create 'meter', {NAME=>'f'}

3. This driver is implemented to use HBase Thrift interface so it's necessary
to have the HBase Thrift server installed and started. When you have HBase
installed, normally, HBase thrift server is turned on by default. If it's not,
turn it on by running command ``hbase thrift start``. The implementation uses
`HappyBase`_ which is a wrapper library used to interact with HBase via Thrift
protocol, you can verify the thrift connection by running a quick test from a
client:

 .. _HappyBase: http://happybase.readthedocs.org/en/latest/index.html#

::

    import happybase

    conn = happybase.Connection(host=$hbase-thrift-server, port=9090, table_prefix=None)
    print conn.tables() # this returns a list of HBase tables in your HBase server

4. The parameter "database_connection" needs to be configured to point to
the Hbase Thrift server.

===========================  ====================================  ==============================================================
Parameter                    Value                                 Note
===========================  ====================================  ==============================================================
database_connection          hbase://$hbase-thrift-server:9090     Database connection string
===========================  ====================================  ==============================================================

.. note::

    If you are changing the configuration on the fly, you will need to restart
    the Ceilometer services that use the database to allow the changes to take
    affect, i.e. the collector and API services.

General options
===============

The following is the list of openstack-common options that we use:

===========================  ====================================  ==============================================================
Parameter                    Default                               Note
===========================  ====================================  ==============================================================
default_notification_level   INFO                                  Default notification level for outgoing notifications
default_publisher_id         $host                                 Default publisher_id for outgoing notifications
bind_host                    0.0.0.0                               IP address to listen on
bind_port                    9292                                  Port numver to listen on
port                         5672                                  Rabbit MQ port to liste on
fake_rabbit                  False                                 If passed, use a fake RabbitMQ provider
publish_errors               False                                 publish error events
use_stderr                   True                                  Log output to standard error
logfile_mode                 0644                                  Default file mode used when creating log files
log_dir                                                            Log output to a per-service log file in named directory
log_file                                                           Log output to a named file
log_format                   date-time level name msg              Log format
log_date_format              YYYY-MM-DD hh:mm:ss                   Log date format
log_config                                                         Logging configuration file used. The options specified in that
                                                                    config file will override any other logging options specified
                                                                    in Ceilometer config file.
default_log_levels           ['amqplib=WARN',sqlalchemy=WARN,...]  Default log level per components
notification_topics          ['notifications', ]                   AMQP topic used for openstack notifications
enabled_apis                 ['ec2', 'osapi_compute']              List of APIs to enable by default
verbose                      False                                 Print more verbose output
debug                        False                                 Print debugging output
state_path                   currentdir                            Top-level directory for maintaining nova state
sqlite_db                    nova.sqlite                           file name for sqlite
sql_connection               sqlite:///$state_path/$sqlite_db      connection string for sql database
matchmaker_ringfile          /etc/nova/matchmaker_ring.json        Matchmaker ring file (JSON)
rpc_zmq_bind_address         '*'                                   ZeroMQ bind address
rpc_zmq_matchmaker           ceilometer.openstack.common.rpc.      MatchMaker drivers
                             matchmaker.MatchMakerLocalhost
rpc_zmq_port                 9501                                  ZeroMQ receiver listening port
rpc_zmq_port_pub             9502                                  ZeroMQ fanout publisher port
rpc_zmq_contexts             1                                     Number of ZeroMQ contexts
rpc_zmq_ipc_dir              /var/run/openstack                    Directory for holding IPC sockets
rabbit_port                  5672                                  The RabbitMQ broker port where a single node is used
rabbit_host                  localhost                             The RabbitMQ broker address where a single node is used
rabbit_hosts                 ['$rabbit_host:$rabbit_port']         The list of rabbit hosts to listen to
rabbit_userid                guest                                 the RabbitMQ userid
rabbit_password              guest                                 the RabbitMQ password
rabbit_virtual_host          /                                     the RabbitMQ virtual host
rabbit_retry_interval        1                                     how frequently to retry connecting with RabbitMQ
rabbit_retry_backoff         2                                     how long to backoff for between retries when connecting
rabbit_max_retries           0                                     maximum retries with trying to connect to RabbitMQ
                                                                   (the default of 0 implies an infinite retry count)
rabbit_durable_queues        False                                 use durable queues in RabbitMQ
rabbit_use_ssl               False                                 connect over SSL for RabbitMQ
rabbit_durable_queues        False                                 use durable queues in RabbitMQ
rabbit_ha_queues             False                                 use H/A queues in RabbitMQ (x-ha-policy: all).
kombu_ssl_version                                                  SSL version to use (valid only if SSL enabled)
kombu_ssl_keyfile                                                  SSL key file (valid only if SSL enabled)
kombu_ssl_certfile                                                 SSL cert file (valid only if SSL enabled)
kombu_ssl_ca_certs                                                 SSL certification authority file
qpid_hostname                localhost                             Qpid broker hostname
qpid_port                    5672                                  Qpid broker port
qpid_username                                                      Username for qpid connection
qpid_password                                                      Password for qpid connection
qpid_sasl_mechanisms                                               Space separated list of SASL mechanisms to use for auth
qpid_reconnect_timeout       0                                     Reconnection timeout in seconds
qpid_reconnect_limit         0                                     Max reconnections before giving up
qpid_reconnect_interval_min  0                                     Minimum seconds between reconnection attempts
qpid_reconnect_interval_max  0                                     Maximum seconds between reconnection attempts
qpid_reconnect_interval      0                                     Equivalent to setting max and min to the same value
qpid_heartbeat               60                                    Seconds between connection keepalive heartbeats
qpid_protocol                tcp                                   Transport to use, either 'tcp' or 'ssl'
qpid_reconnect               True                                  Automatically reconnect
qpid_tcp_nodelay             True                                  Disable Nagle algorithm
rpc_backend                  kombu                                 The messaging module to use, defaults to kombu.
rpc_thread_pool_size         64                                    Size of RPC thread pool
rpc_conn_pool_size           30                                    Size of RPC connection pool
rpc_response_timeout         60                                    Seconds to wait for a response from call or multicall
rpc_cast_timeout             30                                    Seconds to wait before a cast expires (TTL).
                                                                   Only supported by impl_zmq.
===========================  ====================================  ==============================================================

A sample configuration file can be found in `ceilometer.conf.sample`_.

.. _ceilometer.conf.sample: https://github.com/openstack/ceilometer/blob/master/etc/ceilometer/ceilometer.conf.sample
