# Copyright 2010 Jacob Kaplan-Moss
# Copyright 2011 OpenStack LLC.
# Copyright 2011 Piston Cloud Computing, Inc.

# All Rights Reserved.
"""
OpenStack Client interface. Handles the REST calls and responses.
"""

import logging
import os
import urlparse
try:
    from eventlet import sleep
except ImportError:
    from time import sleep

try:
    import json
except ImportError:
    import simplejson as json

# Python 2.5 compat fix
if not hasattr(urlparse, 'parse_qsl'):
    import cgi
    urlparse.parse_qsl = cgi.parse_qsl

import requests

from monitorclient import exceptions
from monitorclient import service_catalog
from monitorclient import utils


class HTTPClient(object):

    USER_AGENT = 'python-monitorclient'

    def __init__(self, user, password, projectid, auth_url, insecure=False,
                 timeout=None, tenant_id=None, proxy_tenant_id=None,
                 proxy_token=None, region_name=None,
                 endpoint_type='publicURL', service_type=None,
                 service_name=None, monitor_service_name=None, retries=None,
                 http_log_debug=False, cacert=None):
        self.user = user
        self.password = password
        self.projectid = projectid
        self.tenant_id = tenant_id
        self.auth_url = auth_url.rstrip('/')
        self.version = 'v1'
        self.region_name = region_name
        self.endpoint_type = endpoint_type
        self.service_type = service_type
        self.service_name = service_name
        self.monitor_service_name = monitor_service_name
        self.retries = int(retries or 0)
        self.http_log_debug = http_log_debug

        self.management_url = None
        self.auth_token = None
        self.proxy_token = proxy_token
        self.proxy_tenant_id = proxy_tenant_id

        if insecure:
            self.verify_cert = False
        else:
            if cacert:
                self.verify_cert = cacert
            else:
                self.verify_cert = True

        self._logger = logging.getLogger(__name__)
        if self.http_log_debug:
            ch = logging.StreamHandler()
            self._logger.setLevel(logging.DEBUG)
            self._logger.addHandler(ch)
            if hasattr(requests, 'logging'):
                requests.logging.getLogger(requests.__name__).addHandler(ch)

    def http_log_req(self, args, kwargs):
        if not self.http_log_debug:
            return

        string_parts = ['curl -i']
        for element in args:
            if element in ('GET', 'POST', 'DELETE', 'PUT'):
                string_parts.append(' -X %s' % element)
            else:
                string_parts.append(' %s' % element)

        for element in kwargs['headers']:
            header = ' -H "%s: %s"' % (element, kwargs['headers'][element])
            string_parts.append(header)

        if 'data' in kwargs:
            string_parts.append(" -d '%s'" % (kwargs['data']))
        self._logger.debug("\nREQ: %s\n" % "".join(string_parts))

    def http_log_resp(self, resp):
        if not self.http_log_debug:
            return
        self._logger.debug(
            "RESP: [%s] %s\nRESP BODY: %s\n",
            resp.status_code,
            resp.headers,
            resp.text)

    def request(self, url, method, **kwargs):
        kwargs.setdefault('headers', kwargs.get('headers', {}))
        kwargs['headers']['User-Agent'] = self.USER_AGENT
        kwargs['headers']['Accept'] = 'application/json'
        if 'body' in kwargs:
            kwargs['headers']['Content-Type'] = 'application/json'
            kwargs['data'] = json.dumps(kwargs['body'])
            del kwargs['body']

        self.http_log_req((url, method,), kwargs)

        print 'JIYOU in client.py'
        print url
        print method

        resp = requests.request(
            method,
            url,
            verify=self.verify_cert,
            **kwargs)

        print 'JIYOU resp'
        print resp
        self.http_log_resp(resp)

        if resp.text:
            try:
                body = json.loads(resp.text)
            except ValueError:
                pass
                body = None
        else:
            body = None
        if resp.status_code >= 400:
            raise exceptions.from_response(resp, body)
        #print 'JIYOU resp, body'
        #print resp
        #print body
        return resp, body

    def _cs_request(self, url, method, **kwargs):
        print 'JIYOU in _cs_request() in client.py'
        auth_attempts = 0
        attempts = 0
        backoff = 1
        while True:
            attempts += 1
            if not self.management_url or not self.auth_token:
                self.authenticate()
            kwargs.setdefault('headers', {})['X-Auth-Token'] = self.auth_token
            if self.projectid:
                kwargs['headers']['X-Auth-Project-Id'] = self.projectid
            try:
                resp, body = self.request(self.management_url + url, method,
                                          **kwargs)
                print 'JIYOU in _cs_request in client.py after respo'
                return resp, body
            except exceptions.BadRequest as e:
                if attempts > self.retries:
                    raise
            except exceptions.Unauthorized:
                if auth_attempts > 0:
                    raise
                self._logger.debug("Unauthorized, reauthenticating.")
                self.management_url = self.auth_token = None
                # First reauth. Discount this attempt.
                attempts -= 1
                auth_attempts += 1
                continue
            except exceptions.ClientException as e:
                if attempts > self.retries:
                    raise
                if 500 <= e.code <= 599:
                    pass
                else:
                    raise
            except requests.exceptions.ConnectionError as e:
                # Catch a connection refused from requests.request
                self._logger.debug("Connection refused: %s" % e)
                raise
            self._logger.debug(
                "Failed attempt(%s of %s), retrying in %s seconds" %
                (attempts, self.retries, backoff))
            sleep(backoff)
            backoff *= 2

    def get(self, url, **kwargs):
        print 'JIYOU get fun'
        ret = self._cs_request(url, 'GET', **kwargs)
        print 'JIYOU after _cs_request in def get() in client.opy'
        return ret

    def post(self, url, **kwargs):
        print 'JIYOU post fun'
        return self._cs_request(url, 'POST', **kwargs)

    def put(self, url, **kwargs):
        print 'JIYOU put fun'
        return self._cs_request(url, 'PUT', **kwargs)

    def delete(self, url, **kwargs):
        return self._cs_request(url, 'DELETE', **kwargs)

    def _extract_service_catalog(self, url, resp, body, extract_token=True):
        """See what the auth service told us and process the response.
        We may get redirected to another site, fail or actually get
        back a service catalog with a token and our endpoints."""

        if resp.status_code == 200:  # content must always present
            try:
                self.auth_url = url
                self.service_catalog = \
                    service_catalog.ServiceCatalog(body)
                print 'JIYOU in _extract_service_catalog'
                print self.service_catalog
                print self.service_type
                print self.service_name
                if extract_token:
                    self.auth_token = self.service_catalog.get_token()

                management_url = self.service_catalog.url_for(
                    attr='region',
                    filter_value=self.region_name,
                    endpoint_type=self.endpoint_type,
                    service_type=self.service_type,
                    service_name=self.service_name,
                    monitor_service_name=self.monitor_service_name)
                self.management_url = management_url.rstrip('/')
                return None
            except exceptions.AmbiguousEndpoints:
                print "Found more than one valid endpoint. Use a more " \
                      "restrictive filter"
                raise
            except KeyError:
                raise exceptions.AuthorizationFailure()
            except exceptions.EndpointNotFound:
                print "Could not find any suitable endpoint. Correct region?"
                raise

        elif resp.status_code == 305:
            return resp['location']
        else:
            raise exceptions.from_response(resp, body)

    def _fetch_endpoints_from_auth(self, url):
        """We have a token, but don't know the final endpoint for
        the region. We have to go back to the auth service and
        ask again. This request requires an admin-level token
        to work. The proxy token supplied could be from a low-level enduser.

        We can't get this from the keystone service endpoint, we have to use
        the admin endpoint.

        This will overwrite our admin token with the user token.
        """

        # GET ...:5001/v2.0/tokens/#####/endpoints
        url = '/'.join([url, 'tokens', '%s?belongsTo=%s'
                        % (self.proxy_token, self.proxy_tenant_id)])
        self._logger.debug("Using Endpoint URL: %s" % url)
        resp, body = self.request(url, "GET",
                                  headers={'X-Auth-Token': self.auth_token})
        return self._extract_service_catalog(url, resp, body,
                                             extract_token=False)

    def authenticate(self):
        magic_tuple = urlparse.urlsplit(self.auth_url)
        scheme, netloc, path, query, frag = magic_tuple
        port = magic_tuple.port
        if port is None:
            port = 80
        path_parts = path.split('/')
        for part in path_parts:
            if len(part) > 0 and part[0] == 'v':
                self.version = part
                break

        # TODO(sandy): Assume admin endpoint is 35357 for now.
        # Ideally this is going to have to be provided by the service catalog.
        new_netloc = netloc.replace(':%d' % port, ':%d' % (35357,))
        admin_url = urlparse.urlunsplit((scheme, new_netloc,
                                         path, query, frag))

        auth_url = self.auth_url
        if self.version == "v2.0":
            while auth_url:
                if "ENERGY_RAX_AUTH" in os.environ:
                    auth_url = self._rax_auth(auth_url)
                else:
                    auth_url = self._v2_auth(auth_url)

            # Are we acting on behalf of another user via an
            # existing token? If so, our actual endpoints may
            # be different than that of the admin token.
            if self.proxy_token:
                self._fetch_endpoints_from_auth(admin_url)
                # Since keystone no longer returns the user token
                # with the endpoints any more, we need to replace
                # our service account token with the user token.
                self.auth_token = self.proxy_token
        else:
            try:
                while auth_url:
                    auth_url = self._v1_auth(auth_url)
            # In some configurations monitor makes redirection to
            # v2.0 keystone endpoint. Also, new location does not contain
            # real endpoint, only hostname and port.
            except exceptions.AuthorizationFailure:
                if auth_url.find('v2.0') < 0:
                    auth_url = auth_url + '/v2.0'
                self._v2_auth(auth_url)

    def _v1_auth(self, url):
        if self.proxy_token:
            raise exceptions.NoTokenLookupException()

        headers = {'X-Auth-User': self.user,
                   'X-Auth-Key': self.password}
        if self.projectid:
            headers['X-Auth-Project-Id'] = self.projectid

        resp, body = self.request(url, 'GET', headers=headers)
        if resp.status_code in (200, 204):  # in some cases we get No Content
            try:
                mgmt_header = 'x-server-management-url'
                self.management_url = resp.headers[mgmt_header].rstrip('/')
                self.auth_token = resp.headers['x-auth-token']
                self.auth_url = url
            except (KeyError, TypeError):
                raise exceptions.AuthorizationFailure()
        elif resp.status_code == 305:
            return resp.headers['location']
        else:
            raise exceptions.from_response(resp, body)

    def _v2_auth(self, url):
        """Authenticate against a v2.0 auth service."""
        body = {"auth": {
            "passwordCredentials": {"username": self.user,
                                    "password": self.password}}}

        if self.projectid:
            body['auth']['tenantName'] = self.projectid
        elif self.tenant_id:
            body['auth']['tenantId'] = self.tenant_id

        self._authenticate(url, body)

    def _rax_auth(self, url):
        """Authenticate against the Rackspace auth service."""
        body = {"auth": {
                "RAX-KSKEY:apiKeyCredentials": {
                    "username": self.user,
                    "apiKey": self.password,
                    "tenantName": self.projectid}}}

        self._authenticate(url, body)

    def _authenticate(self, url, body):
        """Authenticate and extract the service catalog."""
        token_url = url + "/tokens"

        # Make sure we follow redirects when trying to reach Keystone
        resp, body = self.request(
            token_url,
            "POST",
            body=body,
            allow_redirects=True)

        return self._extract_service_catalog(url, resp, body)


def get_client_class(version):
    version_map = {
        '1': 'monitorclient.v1.client.Client',
        '2': 'monitorclient.v2.client.Client',
    }
    try:
        client_path = version_map[str(version)]
    except (KeyError, ValueError):
        msg = "Invalid client version '%s'. must be one of: %s" % (
            (version, ', '.join(version_map.keys())))
        raise exceptions.UnsupportedVersion(msg)

    return utils.import_class(client_path)


def Client(version, *args, **kwargs):
    client_class = get_client_class(version)
    return client_class(*args, **kwargs)
