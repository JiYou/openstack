# Server Specific Configurations
server = {
    'port': '8777',
    'host': '0.0.0.0'
}

# Pecan Application Configurations
app = {
    'root': 'ceilometer.api.controllers.root.RootController',
    'modules': ['ceilometer.api'],
    'static_root': '%(confdir)s/public',
    'template_path': '%(confdir)s/ceilometer/api/templates',
    'debug': False,
    'enable_acl': True,
}

# Custom Configurations must be in Python dictionary format::
#
# foo = {'bar':'baz'}
#
# All configurations are accessible at::
# pecan.conf
