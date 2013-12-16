from novaclient import base

class MyProjectExtensionManager(base.ManagerWithFind):
    # 19.4.2

    def cpu_usage(self, host):
        url = "/myproject_hosts/%s/cpu_usage" % host
        resp, body = self.api.client.get(url)
        return body

    # 19.4.3

    def cpu_usage2(self, host):
        url = "/myproject_hosts/%s/cpu_usage2" % host
        resp, body = self.api.client.get(url)
        return body

    # 19.4.4

    def cpu_usage_all(self):
        url = "/myproject_hosts/cpu_usage_all"
        resp, body = self.api.client.get(url)
        return body

