
from monitorclient import exceptions
from monitorclient import utils
from monitorclient import base
from tests import utils as test_utils

UUID = '8e8ec658-c7b0-4243-bdf8-6f7f2952c0d0'


class FakeResource(object):

    def __init__(self, _id, properties):
        self.id = _id
        try:
            self.name = properties['name']
        except KeyError:
            pass
        try:
            self.display_name = properties['display_name']
        except KeyError:
            pass


class FakeManager(base.ManagerWithFind):

    resource_class = FakeResource

    resources = [
        FakeResource('1234', {'name': 'entity_one'}),
        FakeResource(UUID, {'name': 'entity_two'}),
        FakeResource('4242', {'display_name': 'entity_three'}),
        FakeResource('5678', {'name': '9876'})
    ]

    def get(self, resource_id):
        for resource in self.resources:
            if resource.id == str(resource_id):
                return resource
        raise exceptions.NotFound(resource_id)

    def list(self):
        return self.resources


class FindResourceTestCase(test_utils.TestCase):

    def setUp(self):
        super(FindResourceTestCase, self).setUp()
        self.manager = FakeManager(None)

    def test_find_none(self):
        self.assertRaises(exceptions.CommandError,
                          utils.find_resource,
                          self.manager,
                          'asdf')

    def test_find_by_integer_id(self):
        output = utils.find_resource(self.manager, 1234)
        self.assertEqual(output, self.manager.get('1234'))

    def test_find_by_str_id(self):
        output = utils.find_resource(self.manager, '1234')
        self.assertEqual(output, self.manager.get('1234'))

    def test_find_by_uuid(self):
        output = utils.find_resource(self.manager, UUID)
        self.assertEqual(output, self.manager.get(UUID))

    def test_find_by_str_name(self):
        output = utils.find_resource(self.manager, 'entity_one')
        self.assertEqual(output, self.manager.get('1234'))

    def test_find_by_str_displayname(self):
        output = utils.find_resource(self.manager, 'entity_three')
        self.assertEqual(output, self.manager.get('4242'))
