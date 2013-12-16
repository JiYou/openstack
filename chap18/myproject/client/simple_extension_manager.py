from novaclient import base

class SimpleExtensionManager(base.ManagerWithFind):

    def is_ok(self):
        url = "/simple_extension/is_ok"
        resp, body = self.api.client.get(url)
        return body

