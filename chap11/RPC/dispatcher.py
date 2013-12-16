class RpcDispatcher(object):
    def __init__(self, callback):
        self.callback = callback

    def dispatch(self, method, **kwargs):
        if hasattr(self.callback, method):
            return getattr(self.callback, method)(**kwargs)
        print('No such RPC method: %s\n' % method)

