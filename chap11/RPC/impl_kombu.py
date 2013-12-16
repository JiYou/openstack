import functools
import itertools
import socket
import uuid
import time

import eventlet
import greenlet
import kombu
import kombu.connection
import kombu.entity
import kombu.messaging

import rpc_amqp
import rpc

rabbit_params = {
    'hostname':'10.239.131.181',
    'port':5672,
    'userid': 'guest',
    'password': 'guest',
    'virtual_host': '/',
}

conf = {
    'interval_start': 1,
    'interval_stepping': 2,
    'interval_max': 30,
}

DIRECT = 'feedback_request_'

class ConsumerBase(object):

    def __init__(self, channel, callback, tag, **kwargs):
        self.callback = callback
        self.tag = str(tag)
        self.kwargs = kwargs
        self.queue = None
        self.reconnect(channel)

    def reconnect(self, channel):
        self.channel = channel
        self.kwargs['channel'] = channel
        self.queue = kombu.entity.Queue(**self.kwargs)
        self.queue.declare()

    def consume(self, *args, **kwargs):
        options = {'consumer_tag': self.tag}
        options['nowait'] = False

        def _callback(raw_message):
            message = self.channel.message_to_python(raw_message)
            try:
                msg = message.payload
                self.callback(msg)
                message.ack()
            except Exception:
                print("Failed to process message... skipping it.\n")

        self.queue.consume(*args, callback=_callback, **options)

    def cancel(self):
        try:
            self.queue.cancel(self.tag)
        except KeyError, e:
            if str(e) != "u'%s'" % self.tag:
                raise
        self.queue = None

class DirectConsumer(ConsumerBase):
    def __init__(self, channel, msg_id, callback, tag, **kwargs):
        self.topic = msg_id
        options = {'durable': False,
                   'auto_delete': True,
                   'exclusive': False}
        options.update(kwargs)
        exchange = kombu.entity.Exchange(name=msg_id,
                                         type='direct',
                                         durable=options['durable'],
                                         auto_delete=options['auto_delete'])
        super(DirectConsumer, self).__init__(channel,
                                             callback,
                                             tag,
                                             name=msg_id,
                                             exchange=exchange,
                                             routing_key=msg_id,
                                                 **options)


class TopicConsumer(ConsumerBase):

    def __init__(self, channel, topic, callback, tag, **kwargs):
        self.topic = topic
        options = {'durable': False,
                   'auto_delete': False,
                   'exclusive': False}
        options.update(kwargs)
        exchange = kombu.entity.Exchange(name=topic,
                                         type='topic',
                                         durable=options['durable'],
                                         auto_delete=options['auto_delete'])
        super(TopicConsumer, self).__init__(channel,
                                            callback,
                                            tag,
                                            name=topic,
                                            exchange=exchange,
                                            routing_key=topic,
                                            **options)



class Publisher(object):
    def __init__(self, channel, exchange_name, routing_key, **kwargs):
        self.exchange_name = exchange_name
        self.routing_key = routing_key
        self.type = kwargs.pop('type')
        self.kwargs = kwargs
        self.reconnect(channel)

    def reconnect(self, channel):
        self.exchange = kombu.entity.Exchange(self.exchange_name,
                                              self.type,
                                              **self.kwargs)
        self.producer = kombu.messaging.Producer(channel,
                                                 exchange=self.exchange)

    def send(self, msg):
        self.producer.publish(msg,
                              routing_key=self.routing_key)

class DirectPublisher(Publisher):
    def __init__(self, channel, msg_id, **kwargs):
        options = {'durable': False,
                   'auto_delete': True,
                   'exclusive': False}
        options.update(kwargs)
        super(DirectPublisher, self).__init__(channel, msg_id, msg_id,
                                              type='direct', **options)

class TopicPublisher(Publisher):
    def __init__(self, channel, topic, **kwargs):

        options = {'durable': False,
                   'auto_delete': False,
                   'exclusive': False}
        options.update(kwargs)
        super(TopicPublisher, self).__init__(channel, topic, topic,
                                             type='topic', **options)

class Connection(object):

    def __init__(self):
        self.consumers = []
        self.connection = None
        self.reconnect()

    def reconnect(self):
        sleep_time = conf.get('interval_start', 1)
        stepping = conf.get('interval_stepping', 2)
        interval_max = conf.get('interval_max', 30)
        sleep_time -= stepping

        while True:
            try:
                self._connect()
                return
            except Exception, e:
                if 'timeout' not in str(e):
                    raise

            sleep_time += stepping
            sleep_time = min(sleep_time, interval_max)
            print("AMQP Server is unreachable,"
                  "trying to connect %d seconds later\n" % sleep_time)
            time.sleep(sleep_time)

    def _connect(self):
        hostname = rabbit_params.get('hostname')
        port = rabbit_params.get('port')

        if self.connection:
            print("Reconnecting to AMQP Server on "
                  "%(hostname)s:%(port)d\n" % locals())
            self.connection.release()
            self.connection = None

        self.connection = kombu.connection.BrokerConnection(**rabbit_params)
        self.consumer_num = itertools.count(1)
        self.connection.connect()
        self.channel = self.connection.channel()
        for consumer in self.consumers:
            consumer.reconnect(self.channel)

    def create_consumer(self, topic, proxy):
        proxy_cb = rpc_amqp.ProxyCallback(proxy)
        self.declare_topic_consumer(topic, proxy_cb)

    def declare_consumer(self, consumer_cls, topic, callback):
        def _declare_consumer():
            consumer = consumer_cls(self.channel, 
                                    topic, callback,
                                    self.consumer_num.next())
            self.consumers.append(consumer)
            print('Succed declaring consumer for topic %s\n' % topic)
            return consumer
        return self.ensure(_declare_consumer, topic)

    def ensure(self, method, topic):
        while True:
            try:
                return method()
            except Exception, e:
                if 'timeout' not in str(e):
                    raise
                print('Failed to declare consumer for topic %s: '
                      '%s\n' % (topic, str(e)))

            self.reconnect()

    def declare_direct_consumer(self, topic, callback):
        print('declaring direct consumer for topic %s...\n' % topic)
        self.declare_consumer(DirectConsumer, topic, callback)

    def declare_topic_consumer(self, topic, callback):
        print('declaring topic consumer for topic %s...\n' % topic)
        self.declare_consumer(TopicConsumer, topic, callback)

    def consume(self, limit=None):
        for consumer in self.consumers:
            consumer.consume()

    def drain_events(self):
        if self.connection:
            return self.connection.drain_events()
        
    def publisher_send(self, cls, topic, msg, **kwargs):
        def _publish():
            publisher = cls(self.channel, topic, **kwargs)
            publisher.send(msg)

        self.ensure(_publish, topic)

    def direct_send(self, msg_id, msg):
        self.publisher_send(DirectPublisher, msg_id, msg)

    def topic_send(self, topic, msg):
        self.publisher_send(TopicPublisher, topic, msg)

    def close(self):
        self.connection.release()
        self.connection = None

    def get_consumers(self):
        return self.consumers

class CallWaiter(object):
    def __init__(self, connection, timeout=None):
        self._connection = connection
        self._result = None

    def __call__(self, data):
        if data['result']:
            self._result = data['result']

    def wait_reply(self):
        self._connection.consume()
        self._connection.drain_events()
        return self._result


def call(topic, msg, timeout):
    print('Making synchronous call on %s ...\n' % topic)
    msg_id = DIRECT + str(uuid.uuid4())
    msg.update({'msg_id': msg_id})
    print('MSG_ID is %s\n' % msg_id)

    conn = rpc.create_connection() 
    wait_msg = CallWaiter(conn)
    conn.declare_direct_consumer(msg_id, wait_msg)
    conn.topic_send(topic, msg)
    return wait_msg.wait_reply()
