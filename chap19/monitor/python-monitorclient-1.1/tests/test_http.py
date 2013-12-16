import mock

import requests

from monitorclient import client
from monitorclient import exceptions
from tests import utils


fake_response = utils.TestResponse({
    "status_code": 200,
    "text": '{"hi": "there"}',
})
mock_request = mock.Mock(return_value=(fake_response))

bad_400_response = utils.TestResponse({
    "status_code": 400,
    "text": '{"error": {"message": "n/a", "details": "Terrible!"}}',
})
bad_400_request = mock.Mock(return_value=(bad_400_response))

bad_401_response = utils.TestResponse({
    "status_code": 401,
    "text": '{"error": {"message": "FAILED!", "details": "DETAILS!"}}',
})
bad_401_request = mock.Mock(return_value=(bad_401_response))

bad_500_response = utils.TestResponse({
    "status_code": 500,
    "text": '{"error": {"message": "FAILED!", "details": "DETAILS!"}}',
})
bad_500_request = mock.Mock(return_value=(bad_500_response))


def get_client(retries=0):
    cl = client.HTTPClient("username", "password",
                           "project_id", "auth_test", retries=retries)
    return cl


def get_authed_client(retries=0):
    cl = get_client(retries=retries)
    cl.management_url = "http://example.com"
    cl.auth_token = "token"
    return cl


class ClientTest(utils.TestCase):

    def test_get(self):
        cl = get_authed_client()

        @mock.patch.object(requests, "request", mock_request)
        @mock.patch('time.time', mock.Mock(return_value=1234))
        def test_get_call():
            resp, body = cl.get("/hi")
            headers = {"X-Auth-Token": "token",
                       "X-Auth-Project-Id": "project_id",
                       "User-Agent": cl.USER_AGENT,
                       'Accept': 'application/json', }
            mock_request.assert_called_with(
                "GET",
                "http://example.com/hi",
                headers=headers,
                **self.TEST_REQUEST_BASE)
            # Automatic JSON parsing
            self.assertEqual(body, {"hi": "there"})

        test_get_call()

    def test_get_reauth_0_retries(self):
        cl = get_authed_client(retries=0)

        self.requests = [bad_401_request, mock_request]

        def request(*args, **kwargs):
            next_request = self.requests.pop(0)
            return next_request(*args, **kwargs)

        def reauth():
            cl.management_url = "http://example.com"
            cl.auth_token = "token"

        @mock.patch.object(cl, 'authenticate', reauth)
        @mock.patch.object(requests, "request", request)
        @mock.patch('time.time', mock.Mock(return_value=1234))
        def test_get_call():
            resp, body = cl.get("/hi")

        test_get_call()
        self.assertEqual(self.requests, [])

    def test_get_retry_500(self):
        cl = get_authed_client(retries=1)

        self.requests = [bad_500_request, mock_request]

        def request(*args, **kwargs):
            next_request = self.requests.pop(0)
            return next_request(*args, **kwargs)

        @mock.patch.object(requests, "request", request)
        @mock.patch('time.time', mock.Mock(return_value=1234))
        def test_get_call():
            resp, body = cl.get("/hi")

        test_get_call()
        self.assertEqual(self.requests, [])

    def test_retry_limit(self):
        cl = get_authed_client(retries=1)

        self.requests = [bad_500_request, bad_500_request, mock_request]

        def request(*args, **kwargs):
            next_request = self.requests.pop(0)
            return next_request(*args, **kwargs)

        @mock.patch.object(requests, "request", request)
        @mock.patch('time.time', mock.Mock(return_value=1234))
        def test_get_call():
            resp, body = cl.get("/hi")

        self.assertRaises(exceptions.ClientException, test_get_call)
        self.assertEqual(self.requests, [mock_request])

    def test_get_no_retry_400(self):
        cl = get_authed_client(retries=0)

        self.requests = [bad_400_request, mock_request]

        def request(*args, **kwargs):
            next_request = self.requests.pop(0)
            return next_request(*args, **kwargs)

        @mock.patch.object(requests, "request", request)
        @mock.patch('time.time', mock.Mock(return_value=1234))
        def test_get_call():
            resp, body = cl.get("/hi")

        self.assertRaises(exceptions.BadRequest, test_get_call)
        self.assertEqual(self.requests, [mock_request])

    def test_get_retry_400_socket(self):
        cl = get_authed_client(retries=1)

        self.requests = [bad_400_request, mock_request]

        def request(*args, **kwargs):
            next_request = self.requests.pop(0)
            return next_request(*args, **kwargs)

        @mock.patch.object(requests, "request", request)
        @mock.patch('time.time', mock.Mock(return_value=1234))
        def test_get_call():
            resp, body = cl.get("/hi")

        test_get_call()
        self.assertEqual(self.requests, [])

    def test_post(self):
        cl = get_authed_client()

        @mock.patch.object(requests, "request", mock_request)
        def test_post_call():
            cl.post("/hi", body=[1, 2, 3])
            headers = {
                "X-Auth-Token": "token",
                "X-Auth-Project-Id": "project_id",
                "Content-Type": "application/json",
                'Accept': 'application/json',
                "User-Agent": cl.USER_AGENT
            }
            mock_request.assert_called_with(
                "POST",
                "http://example.com/hi",
                headers=headers,
                data='[1, 2, 3]',
                **self.TEST_REQUEST_BASE)

        test_post_call()

    def test_auth_failure(self):
        cl = get_client()

        # response must not have x-server-management-url header
        @mock.patch.object(requests, "request", mock_request)
        def test_auth_call():
            self.assertRaises(exceptions.AuthorizationFailure, cl.authenticate)

        test_auth_call()
