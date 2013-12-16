from nova.api.openstack import wsgi
from nova.api.openstack import extensions

class Controller(wsgi.Controller):
    def is_ok(self, req):
        return {'key':'ok'}

class Simple_extension(extensions.ExtensionDescriptor):
    """self-defined Nova-api"""
    name = "simple_extension"
    alias = "simple_extension"
    
    def get_resources(self):
        resources = [extensions.ResourceExtension('simple_extension',
                     Controller(),
                     collection_actions = {
                     'is_ok':'GET',
                     })]
        return resources

