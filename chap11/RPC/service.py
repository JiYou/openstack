import rpc
import manager
import dispatcher

TOPIC = 'sendout_request'

class Service(object):
    def __init__(self):
        self.topic = TOPIC
        self.manager = manager.Manager()

    def start(self):
        self.conn = rpc.create_connection()
        rpc_dispatcher = dispatcher.RpcDispatcher(self.manager)
        self.conn.create_consumer(self.topic, rpc_dispatcher)
        self.conn.consume()

    def drain_events(self):
        self.conn.drain_events()

