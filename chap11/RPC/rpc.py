import impl_kombu

def create_connection():
    return impl_kombu.Connection()

def call(topic, msg, timeout=None):
    return impl_kombu.call(topic, msg, timeout)
