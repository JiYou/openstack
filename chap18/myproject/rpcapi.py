from nova.myproject import myproject_opts
import nova.openstack.common.rpc.proxy
from nova.openstack.common import rpc

CONF = myproject_opts.CONF

class MyProjectAPI(nova.openstack.common.rpc.proxy.RpcProxy):
    # 19.4.2

    BASE_RPC_API_VERSION = '1.0'

    def __init__(self):
        super(MyProjectAPI, self).__init__(topic=CONF.myproject_topic,
                                           default_version=self.BASE_RPC_API_VERSION)

    def get_cpu_usage(self, ctxt, host):
        topic = rpc.queue_get_for(ctxt, CONF.myproject_topic, host)
        return self.call(ctxt, self.make_msg('get_cpu_usage'),
                         topic=topic)

    # 19.4.3

    def get_cpu_usage2(self, ctxt, host):
        topic = rpc.queue_get_for(ctxt, CONF.myproject_topic, host)
        return self.call(ctxt, self.make_msg('get_cpu_usage2'),
                         topic=topic)

