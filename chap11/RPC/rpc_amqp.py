import impl_kombu

def msg_reply(msg_id, reply):
    msg = {'result': reply}
    conn = impl_kombu.Connection()
    conn.direct_send(msg_id, msg)

class ProxyCallback(object):

    def __init__(self, proxy):
        self.proxy = proxy

    def __call__(self, message_data):
        method = message_data.get('method')
        args = message_data.get('args', {})
        msg_id = message_data.get('msg_id')
        print('Receive RPC request. method is %s.\n' % method)

        self._process_data(msg_id, method, args)

    def _process_data(self, msg_id, method, args):
        rval = self.proxy.dispatch(method, **args)
        msg_reply(msg_id, rval)

