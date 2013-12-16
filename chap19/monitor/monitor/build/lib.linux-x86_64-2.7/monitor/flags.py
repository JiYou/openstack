# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
# Copyright 2012 Red Hat, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""Command-line flag library.

Emulates gflags by wrapping cfg.ConfigOpts.

The idea is to move fully to cfg eventually, and this wrapper is a
stepping stone.

"""

import os
import socket
import sys

from oslo.config import cfg

from monitor import version

FLAGS = cfg.CONF


def parse_args(argv, default_config_files=None):
    FLAGS(argv[1:], project='monitor',
          version=version.version_string(),
          default_config_files=default_config_files)


class UnrecognizedFlag(Exception):
    pass


def DECLARE(name, module_string, flag_values=FLAGS):
    if module_string not in sys.modules:
        __import__(module_string, globals(), locals())
    if name not in flag_values:
        raise UnrecognizedFlag('%s not defined by %s' % (name, module_string))


def _get_my_ip():
    """
    Returns the actual ip of the local machine.

    This code figures out what source address would be used if some traffic
    were to be sent out to some well known address on the Internet. In this
    case, a Google DNS server is used, but the specific address does not
    matter much.  No traffic is actually sent.
    """
    try:
        csock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        csock.connect(('8.8.8.8', 80))
        (addr, port) = csock.getsockname()
        csock.close()
        return addr
    except socket.error:
        return "127.0.0.1"


core_opts = [
    cfg.StrOpt('connection_type',
               default=None,
               help='Virtualization api connection type : libvirt, xenapi, '
                    'or fake'),
    cfg.StrOpt('sql_connection',
               default='sqlite:///$state_path/$sqlite_db',
               help='The SQLAlchemy connection string used to connect to the '
                    'database',
               secret=True),
    cfg.IntOpt('sql_connection_debug',
               default=0,
               help='Verbosity of SQL debugging information. 0=None, '
                    '100=Everything'),
    cfg.StrOpt('api_paste_config',
               default="api-paste.ini",
               help='File name for the paste.deploy config for monitor-api'),
    cfg.StrOpt('pybasedir',
               default=os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                    '../')),
               help='Directory where the monitor python module is installed'),
    cfg.StrOpt('bindir',
               default='$pybasedir/bin',
               help='Directory where monitor binaries are installed'),
    cfg.StrOpt('state_path',
               default='$pybasedir',
               help="Top-level directory for maintaining monitor's state"), ]

debug_opts = [
]

tests_opts = [
    cfg.StrOpt('testdb_manager',
               default='monitor.tests.db.manager.TestDBManager',
               help='full class name for the Manager for servicemanage backup'),
    cfg.StrOpt('testdb_topic',
               default='monitor-testdb',
               help='the topic testdb nodes listen on'),
]


FLAGS.register_cli_opts(core_opts)
FLAGS.register_cli_opts(debug_opts)
FLAGS.register_cli_opts(tests_opts)

global_opts = [
    cfg.StrOpt('my_ip',
               default=_get_my_ip(),
               help='ip address of this host'),
    cfg.StrOpt('conductor_topic',
               default='monitor-conductor',
               help='the topic conductor nodes listen on'),
    cfg.StrOpt('scheduler_topic',
               default='monitor-scheduler',
               help='the topic scheduler nodes listen on'),
    cfg.BoolOpt('enable_v1_api',
                default=True,
                help=_("Deploy v1 of the Monitor API. ")),
    cfg.BoolOpt('enable_v2_api',
                default=True,
                help=_("Deploy v2 of the Monitor API. ")),
    cfg.BoolOpt('api_rate_limit',
                default=True,
                help='whether to rate limit the api'),
    cfg.ListOpt('osapi_servicemanage_ext_list',
                default=[],
                help='Specify list of extensions to load when using osapi_'
                     'servicemanage_extension option with monitor.api.contrib.'
                     'select_extensions'),
    cfg.MultiStrOpt('osapi_servicemanage_extension',
                    default=['monitor.api.contrib.standard_extensions'],
                    help='osapi servicemanage extension to load'),
    cfg.StrOpt('osapi_servicemanage_base_URL',
               default=None,
               help='Base URL that will be presented to users in links '
                    'to the OpenStack ServiceManage API',
               deprecated_name='osapi_compute_link_prefix'),
    cfg.IntOpt('osapi_max_limit',
               default=1000,
               help='the maximum number of items returned in a single '
                    'response from a collection resource'),
    cfg.StrOpt('sqlite_db',
               default='monitor.sqlite',
               help='the filename to use with sqlite'),
    cfg.BoolOpt('sqlite_synchronous',
                default=True,
                help='If passed, use synchronous mode for sqlite'),
    cfg.IntOpt('sql_idle_timeout',
               default=3600,
               help='timeout before idle sql connections are reaped'),
    cfg.IntOpt('sql_max_retries',
               default=10,
               help='maximum db connection retries during startup. '
                    '(setting -1 implies an infinite retry count)'),
    cfg.IntOpt('sql_retry_interval',
               default=10,
               help='interval between retries of opening a sql connection'),
    cfg.StrOpt('conductor_manager',
               default='monitor.conductor.manager.ConductorManager',
               help='full class name for the Manager for Conductor'),
    cfg.StrOpt('scheduler_manager',
               default='monitor.scheduler.manager.SchedulerManager',
               help='full class name for the Manager for Scheduler'),
    cfg.StrOpt('host',
               default=socket.gethostname(),
               help='Name of this node.  This can be an opaque identifier.  '
                    'It is not necessarily a hostname, FQDN, or IP address.'),
    cfg.ListOpt('memcached_servers',
                default=None,
                help='Memcached servers or None for in process cache.'),
    cfg.StrOpt('default_servicemanage_type',
               default=None,
               help='default servicemanage type to use'),
    cfg.StrOpt('servicemanage_usage_audit_period',
               default='month',
               help='time period to generate servicemanage usages for.  '
                    'Time period must be hour, day, month or year'),
    cfg.StrOpt('root_helper',
               default='sudo',
               help='Deprecated: command to use for running commands as root'),
    cfg.StrOpt('rootwrap_config',
               default=None,
               help='Path to the rootwrap configuration file to use for '
                    'running commands as root'),
    cfg.BoolOpt('monkey_patch',
                default=False,
                help='Whether to log monkey patching'),
    cfg.ListOpt('monkey_patch_modules',
                default=[],
                help='List of modules/decorators to monkey patch'),
    cfg.IntOpt('service_down_time',
               default=60,
               help='maximum time since last check-in for up service'),
    cfg.StrOpt('servicemanage_api_class',
               default='monitor.servicemanage.api.API',
               help='The full class name of the servicemanage API class to use'),
    cfg.StrOpt('auth_strategy',
               default='noauth',
               help='The strategy to use for auth. Supports noauth, keystone, '
                    'and deprecated.'),
    cfg.ListOpt('enabled_backends',
                default=None,
                help='A list of backend names to use. These backend names '
                     'should be backed by a unique [CONFIG] group '
                     'with its options'), ]

FLAGS.register_opts(global_opts)
