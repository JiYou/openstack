# Copyright (c) 2011 X.commerce, a business unit of eBay Inc.
# Copyright 2011 OpenStack, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import urlparse

from monitorclient import client as base_client
from monitorclient.v1 import client
from tests import fakes
import tests.utils as utils


def _stub_monitor(**kwargs):
    monitor = {
        'id': '1234',
        'display_name': None,
        'display_description': None,
        "attachments": [],
        "bootable": "false",
        "availability_zone": "monitor",
        "created_at": "2012-08-27T00:00:00.000000",
        "display_description": None,
        "display_name": None,
        "id": '00000000-0000-0000-0000-000000000000',
        "metadata": {},
        "size": 1,
        "snapshot_id": None,
        "status": "available",
        "monitor_type": "None",
    }
    monitor.update(kwargs)
    return monitor


def _stub_snapshot(**kwargs):
    snapshot = {
        "created_at": "2012-08-28T16:30:31.000000",
        "display_description": None,
        "display_name": None,
        "id": '11111111-1111-1111-1111-111111111111',
        "size": 1,
        "status": "available",
        "monitor_id": '00000000-0000-0000-0000-000000000000',
    }
    snapshot.update(kwargs)
    return snapshot


def _self_href(base_uri, tenant_id, backup_id):
    return '%s/v1/%s/backups/%s' % (base_uri, tenant_id, backup_id)


def _bookmark_href(base_uri, tenant_id, backup_id):
    return '%s/%s/backups/%s' % (base_uri, tenant_id, backup_id)


def _stub_backup_full(id, base_uri, tenant_id):
    return {
        'id': id,
        'name': 'backup',
        'description': 'nightly backup',
        'monitor_id': '712f4980-5ac1-41e5-9383-390aa7c9f58b',
        'container': 'monitorbackups',
        'object_count': 220,
        'size': 10,
        'availability_zone': 'az1',
        'created_at': '2013-04-12T08:16:37.000000',
        'status': 'available',
        'links': [
            {
                'href': _self_href(base_uri, tenant_id, id),
                'rel': 'self'
            },
            {
                'href': _bookmark_href(base_uri, tenant_id, id),
                'rel': 'bookmark'
            }
        ]
    }


def _stub_backup(id, base_uri, tenant_id):
    return {
        'id': id,
        'name': 'backup',
        'links': [
            {
                'href': _self_href(base_uri, tenant_id, id),
                'rel': 'self'
            },
            {
                'href': _bookmark_href(base_uri, tenant_id, id),
                'rel': 'bookmark'
            }
        ]
    }


def _stub_restore():
    return {'monitor_id': '712f4980-5ac1-41e5-9383-390aa7c9f58b'}


class FakeClient(fakes.FakeClient, client.Client):

    def __init__(self, *args, **kwargs):
        client.Client.__init__(self, 'username', 'password',
                               'project_id', 'auth_url',
                               extensions=kwargs.get('extensions'))
        self.client = FakeHTTPClient(**kwargs)


class FakeHTTPClient(base_client.HTTPClient):

    def __init__(self, **kwargs):
        self.username = 'username'
        self.password = 'password'
        self.auth_url = 'auth_url'
        self.callstack = []

    def _cs_request(self, url, method, **kwargs):
        # Check that certain things are called correctly
        if method in ['GET', 'DELETE']:
            assert 'body' not in kwargs
        elif method == 'PUT':
            assert 'body' in kwargs

        # Call the method
        args = urlparse.parse_qsl(urlparse.urlparse(url)[4])
        kwargs.update(args)
        munged_url = url.rsplit('?', 1)[0]
        munged_url = munged_url.strip('/').replace('/', '_').replace('.', '_')
        munged_url = munged_url.replace('-', '_')

        callback = "%s_%s" % (method.lower(), munged_url)

        if not hasattr(self, callback):
            raise AssertionError('Called unknown API method: %s %s, '
                                 'expected fakes method name: %s' %
                                 (method, url, callback))

        # Note the call
        self.callstack.append((method, url, kwargs.get('body', None)))
        status, headers, body = getattr(self, callback)(**kwargs)
        r = utils.TestResponse({
            "status_code": status,
            "text": body,
            "headers": headers,
        })
        return r, body

        if hasattr(status, 'items'):
            return utils.TestResponse(status), body
        else:
            return utils.TestResponse({"status": status}), body

    #
    # Snapshots
    #

    def get_snapshots_detail(self, **kw):
        return (200, {}, {'snapshots': [
            _stub_snapshot(),
        ]})

    def get_snapshots_1234(self, **kw):
        return (200, {}, {'snapshot': _stub_snapshot(id='1234')})

    def put_snapshots_1234(self, **kw):
        snapshot = _stub_snapshot(id='1234')
        snapshot.update(kw['body']['snapshot'])
        return (200, {}, {'snapshot': snapshot})

    #
    # ServiceManages
    #

    def put_monitors_1234(self, **kw):
        monitor = _stub_monitor(id='1234')
        monitor.update(kw['body']['monitor'])
        return (200, {}, {'monitor': monitor})

    def get_monitors(self, **kw):
        return (200, {}, {"monitors": [
            {'id': 1234, 'name': 'sample-monitor'},
            {'id': 5678, 'name': 'sample-monitor2'}
        ]})

    # TODO(jdg): This will need to change
    # at the very least it's not complete
    def get_monitors_detail(self, **kw):
        return (200, {}, {"monitors": [
            {'id': 1234,
             'name': 'sample-monitor',
             'attachments': [{'server_id': 1234}]},
        ]})

    def get_monitors_1234(self, **kw):
        r = {'monitor': self.get_monitors_detail()[2]['monitors'][0]}
        return (200, {}, r)

    def post_monitors_1234_action(self, body, **kw):
        _body = None
        resp = 202
        assert len(body.keys()) == 1
        action = body.keys()[0]
        if action == 'os-attach':
            assert body[action].keys() == ['instance_uuid', 'mountpoint']
        elif action == 'os-detach':
            assert body[action] is None
        elif action == 'os-reserve':
            assert body[action] is None
        elif action == 'os-unreserve':
            assert body[action] is None
        elif action == 'os-initialize_connection':
            assert body[action].keys() == ['connector']
            return (202, {}, {'connection_info': 'foos'})
        elif action == 'os-terminate_connection':
            assert body[action].keys() == ['connector']
        elif action == 'os-begin_detaching':
            assert body[action] is None
        elif action == 'os-roll_detaching':
            assert body[action] is None
        else:
            raise AssertionError("Unexpected server action: %s" % action)
        return (resp, {}, _body)

    def post_monitors(self, **kw):
        return (202, {}, {'monitor': {}})

    def delete_monitors_1234(self, **kw):
        return (202, {}, None)

    #
    # Quotas
    #

    def get_os_quota_sets_test(self, **kw):
        return (200, {}, {'quota_set': {
                          'tenant_id': 'test',
                          'metadata_items': [],
                          'monitors': 1,
                          'snapshots': 1,
                          'gigabytes': 1}})

    def get_os_quota_sets_test_defaults(self):
        return (200, {}, {'quota_set': {
                          'tenant_id': 'test',
                          'metadata_items': [],
                          'monitors': 1,
                          'snapshots': 1,
                          'gigabytes': 1}})

    def put_os_quota_sets_test(self, body, **kw):
        assert body.keys() == ['quota_set']
        fakes.assert_has_keys(body['quota_set'],
                              required=['tenant_id'])
        return (200, {}, {'quota_set': {
                          'tenant_id': 'test',
                          'metadata_items': [],
                          'monitors': 2,
                          'snapshots': 2,
                          'gigabytes': 1}})

    #
    # Quota Classes
    #

    def get_os_quota_class_sets_test(self, **kw):
        return (200, {}, {'quota_class_set': {
                          'class_name': 'test',
                          'metadata_items': [],
                          'monitors': 1,
                          'snapshots': 1,
                          'gigabytes': 1}})

    def put_os_quota_class_sets_test(self, body, **kw):
        assert body.keys() == ['quota_class_set']
        fakes.assert_has_keys(body['quota_class_set'],
                              required=['class_name'])
        return (200, {}, {'quota_class_set': {
                          'class_name': 'test',
                          'metadata_items': [],
                          'monitors': 2,
                          'snapshots': 2,
                          'gigabytes': 1}})

    #
    # ServiceManageTypes
    #
    def get_types(self, **kw):
        return (200, {}, {
            'monitor_types': [{'id': 1,
                              'name': 'test-type-1',
                              'extra_specs':{}},
                             {'id': 2,
                              'name': 'test-type-2',
                              'extra_specs':{}}]})

    def get_types_1(self, **kw):
        return (200, {}, {'monitor_type': {'id': 1,
                          'name': 'test-type-1',
                          'extra_specs': {}}})

    def post_types(self, body, **kw):
        return (202, {}, {'monitor_type': {'id': 3,
                          'name': 'test-type-3',
                          'extra_specs': {}}})

    def post_types_1_extra_specs(self, body, **kw):
        assert body.keys() == ['extra_specs']
        return (200, {}, {'extra_specs': {'k': 'v'}})

    def delete_types_1_extra_specs_k(self, **kw):
        return(204, {}, None)

    def delete_types_1(self, **kw):
        return (202, {}, None)

    #
    # Set/Unset metadata
    #
    def delete_monitors_1234_metadata_test_key(self, **kw):
        return (204, {}, None)

    def delete_monitors_1234_metadata_key1(self, **kw):
        return (204, {}, None)

    def delete_monitors_1234_metadata_key2(self, **kw):
        return (204, {}, None)

    def post_monitors_1234_metadata(self, **kw):
        return (204, {}, {'metadata': {'test_key': 'test_value'}})

    #
    # List all extensions
    #
    def get_extensions(self, **kw):
        exts = [
            {
                "alias": "FAKE-1",
                "description": "Fake extension number 1",
                "links": [],
                "name": "Fake1",
                "namespace": ("http://docs.openstack.org/"
                              "/ext/fake1/api/v1.1"),
                "updated": "2011-06-09T00:00:00+00:00"
            },
            {
                "alias": "FAKE-2",
                "description": "Fake extension number 2",
                "links": [],
                "name": "Fake2",
                "namespace": ("http://docs.openstack.org/"
                              "/ext/fake1/api/v1.1"),
                "updated": "2011-06-09T00:00:00+00:00"
            },
        ]
        return (200, {}, {"extensions": exts, })

    #
    # ServiceManageBackups
    #

    def get_backups_76a17945_3c6f_435c_975b_b5685db10b62(self, **kw):
        base_uri = 'http://localhost:8776'
        tenant_id = '0fa851f6668144cf9cd8c8419c1646c1'
        backup1 = '76a17945-3c6f-435c-975b-b5685db10b62'
        return (200, {},
                {'backup': _stub_backup_full(backup1, base_uri, tenant_id)})

    def get_backups_detail(self, **kw):
        base_uri = 'http://localhost:8776'
        tenant_id = '0fa851f6668144cf9cd8c8419c1646c1'
        backup1 = '76a17945-3c6f-435c-975b-b5685db10b62'
        backup2 = 'd09534c6-08b8-4441-9e87-8976f3a8f699'
        return (200, {},
                {'backups': [
                    _stub_backup_full(backup1, base_uri, tenant_id),
                    _stub_backup_full(backup2, base_uri, tenant_id)]})

    def delete_backups_76a17945_3c6f_435c_975b_b5685db10b62(self, **kw):
        return (202, {}, None)

    def post_backups(self, **kw):
        base_uri = 'http://localhost:8776'
        tenant_id = '0fa851f6668144cf9cd8c8419c1646c1'
        backup1 = '76a17945-3c6f-435c-975b-b5685db10b62'
        return (202, {},
                {'backup': _stub_backup(backup1, base_uri, tenant_id)})

    def post_backups_76a17945_3c6f_435c_975b_b5685db10b62_restore(self, **kw):
        return (200, {},
                {'restore': _stub_restore()})
