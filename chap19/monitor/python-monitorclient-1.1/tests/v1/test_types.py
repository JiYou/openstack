from monitorclient import exceptions
from monitorclient.v1 import monitor_types
from tests import utils
from tests.v1 import fakes

cs = fakes.FakeClient()


class TypesTest(utils.TestCase):
    def test_list_types(self):
        tl = cs.monitor_types.list()
        cs.assert_called('GET', '/types')
        for t in tl:
            self.assertTrue(isinstance(t, monitor_types.ServiceManageType))

    def test_create(self):
        t = cs.monitor_types.create('test-type-3')
        cs.assert_called('POST', '/types')
        self.assertTrue(isinstance(t, monitor_types.ServiceManageType))

    def test_set_key(self):
        t = cs.monitor_types.get(1)
        t.set_keys({'k': 'v'})
        cs.assert_called('POST',
                         '/types/1/extra_specs',
                         {'extra_specs': {'k': 'v'}})

    def test_unsset_keys(self):
        t = cs.monitor_types.get(1)
        t.unset_keys(['k'])
        cs.assert_called('DELETE', '/types/1/extra_specs/k')

    def test_delete(self):
        cs.monitor_types.delete(1)
        cs.assert_called('DELETE', '/types/1')
