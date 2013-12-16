
import monitorclient.client
import monitorclient.v1.client
import monitorclient.v2.client
from tests import utils


class ClientTest(utils.TestCase):

    def test_get_client_class_v1(self):
        output = monitorclient.client.get_client_class('1')
        self.assertEqual(output, monitorclient.v1.client.Client)

    def test_get_client_class_v2(self):
        output = monitorclient.client.get_client_class('2')
        self.assertEqual(output, monitorclient.v2.client.Client)

    def test_get_client_class_unknown(self):
        self.assertRaises(monitorclient.exceptions.UnsupportedVersion,
                          monitorclient.client.get_client_class, '0')
