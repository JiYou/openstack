from tests import utils
from tests.v1 import fakes


cs = fakes.FakeClient()


class ServiceManagesTest(utils.TestCase):

    def test_delete_monitor(self):
        v = cs.monitors.list()[0]
        v.delete()
        cs.assert_called('DELETE', '/monitors/1234')
        cs.monitors.delete('1234')
        cs.assert_called('DELETE', '/monitors/1234')
        cs.monitors.delete(v)
        cs.assert_called('DELETE', '/monitors/1234')

    def test_create_monitor(self):
        cs.monitors.create(1)
        cs.assert_called('POST', '/monitors')

    def test_attach(self):
        v = cs.monitors.get('1234')
        cs.monitors.attach(v, 1, '/dev/vdc')
        cs.assert_called('POST', '/monitors/1234/action')

    def test_detach(self):
        v = cs.monitors.get('1234')
        cs.monitors.detach(v)
        cs.assert_called('POST', '/monitors/1234/action')

    def test_reserve(self):
        v = cs.monitors.get('1234')
        cs.monitors.reserve(v)
        cs.assert_called('POST', '/monitors/1234/action')

    def test_unreserve(self):
        v = cs.monitors.get('1234')
        cs.monitors.unreserve(v)
        cs.assert_called('POST', '/monitors/1234/action')

    def test_begin_detaching(self):
        v = cs.monitors.get('1234')
        cs.monitors.begin_detaching(v)
        cs.assert_called('POST', '/monitors/1234/action')

    def test_roll_detaching(self):
        v = cs.monitors.get('1234')
        cs.monitors.roll_detaching(v)
        cs.assert_called('POST', '/monitors/1234/action')

    def test_initialize_connection(self):
        v = cs.monitors.get('1234')
        cs.monitors.initialize_connection(v, {})
        cs.assert_called('POST', '/monitors/1234/action')

    def test_terminate_connection(self):
        v = cs.monitors.get('1234')
        cs.monitors.terminate_connection(v, {})
        cs.assert_called('POST', '/monitors/1234/action')

    def test_set_metadata(self):
        cs.monitors.set_metadata(1234, {'k1': 'v1'})
        cs.assert_called('POST', '/monitors/1234/metadata',
                         {'metadata': {'k1': 'v1'}})

    def test_delete_metadata(self):
        keys = ['key1']
        cs.monitors.delete_metadata(1234, keys)
        cs.assert_called('DELETE', '/monitors/1234/metadata/key1')
