
from monitorclient.v1 import client

ec = client.Client('monitor',
                   'keystone_monitor_password',
                   'service',
                   'http://192.168.111.11:5000/v2.0/')

ret = ec.monitors.test_service()
print ret
