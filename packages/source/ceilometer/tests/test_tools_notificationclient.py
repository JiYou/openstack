import os
import cPickle as pickle
from StringIO import StringIO
import sys
import types

import mox

from ceilometer.openstack.common.rpc import impl_kombu

# The module being tested is part of the tools directory,
# so make sure it is in our import path.
sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(__file__),
                                                 '..', 'tools')))
import notificationclient


def test_send_messages():
    message = {'timestamp': 'date goes here',
               'event_type': 'compute.instance.exists',
               # real messages have more fields...
               }
    input = StringIO(pickle.dumps(message))
    conn = mox.MockObject(impl_kombu.Connection)
    conn.topic_send('notifications.info', message)
    mox.Replay(conn)
    notificationclient.send_messages(conn, 'notifications.info', input)
    mox.Verify(conn)


def test_record_messages():
    conn = mox.MockObject(impl_kombu.Connection)
    conn.declare_topic_consumer('notifications.info',
                                mox.IsA(types.FunctionType))
    conn.consume()
    mox.Replay(conn)
    notificationclient.record_messages(conn, 'notifications.info', StringIO())
    mox.Verify(conn)
