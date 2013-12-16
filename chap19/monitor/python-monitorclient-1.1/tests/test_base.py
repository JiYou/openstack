from monitorclient import base
from monitorclient import exceptions
from monitorclient.v1 import monitors
from tests import utils
from tests.v1 import fakes


cs = fakes.FakeClient()


class BaseTest(utils.TestCase):

    def test_resource_repr(self):
        r = base.Resource(None, dict(foo="bar", baz="spam"))
        self.assertEqual(repr(r), "<Resource baz=spam, foo=bar>")

    def test_getid(self):
        self.assertEqual(base.getid(4), 4)

        class TmpObject(object):
            id = 4
        self.assertEqual(base.getid(TmpObject), 4)

    def test_eq(self):
        # Two resources of the same type with the same id: equal
        r1 = base.Resource(None, {'id': 1, 'name': 'hi'})
        r2 = base.Resource(None, {'id': 1, 'name': 'hello'})
        self.assertEqual(r1, r2)

        # Two resoruces of different types: never equal
        r1 = base.Resource(None, {'id': 1})
        r2 = monitors.ServiceManage(None, {'id': 1})
        self.assertNotEqual(r1, r2)

        # Two resources with no ID: equal if their info is equal
        r1 = base.Resource(None, {'name': 'joe', 'age': 12})
        r2 = base.Resource(None, {'name': 'joe', 'age': 12})
        self.assertEqual(r1, r2)

    def test_findall_invalid_attribute(self):
        # Make sure findall with an invalid attribute doesn't cause errors.
        # The following should not raise an exception.
        cs.monitors.findall(vegetable='carrot')

        # However, find() should raise an error
        self.assertRaises(exceptions.NotFound,
                          cs.monitors.find,
                          vegetable='carrot')
