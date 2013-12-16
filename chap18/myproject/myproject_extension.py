from nova.api.openstack import wsgi
from nova.api.openstack import extensions

from nova.myproject import rpcapi as myproject_rpcapi
from nova.myproject import api as myproject_api

class Controller(wsgi.Controller):
    # 19.4.2

    def __init__(self, **kwargs):
        super(Controller, self).__init__(**kwargs)
        self.myproject_rpcapi = myproject_rpcapi.MyProjectAPI()
        self.myproject_api = myproject_api.API()

    def cpu_usage(self, req, id):
        ctxt = req.environ['nova.context']
        return self.myproject_rpcapi.get_cpu_usage(ctxt, id)

    # 19.4.3

    def cpu_usage2(self, req, id):
        ctxt = req.environ['nova.context']
        return self.myproject_rpcapi.get_cpu_usage2(ctxt, id)

    # 19.4.4

    def cpu_usage_all(self, req):
        ctxt = req.environ['nova.context']
        return self.myproject_api.get_all_cpu_usage(ctxt)


class Myproject_extension(extensions.ExtensionDescriptor):
    """self-defined Nova-api"""
    name = "myproject_extension"
    alias = "myproject_extension"
    
    def get_resources(self):
        resources = [extensions.ResourceExtension('myproject_hosts',
                     Controller(),
                     member_actions = {
                     'cpu_usage':'GET',                     # 19.4.2
                     'cpu_usage2':'GET',                    # 19.4.3
                     },
                     collection_actions = {
                     'cpu_usage_all':'GET',                     # 19.4.4
                     })]
        return resources

