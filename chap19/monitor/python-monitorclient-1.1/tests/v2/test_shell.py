# Copyright 2013 OpenStack LLC.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import fixtures

from monitorclient import client
from monitorclient import shell
from tests import utils
from tests.v2 import fakes


class ShellTest(utils.TestCase):

    FAKE_ENV = {
        'ENERGY_USERNAME': 'username',
        'ENERGY_PASSWORD': 'password',
        'ENERGY_PROJECT_ID': 'project_id',
        'OS_VOLUME_API_VERSION': '2',
        'ENERGY_URL': 'http://no.where',
    }

    # Patch os.environ to avoid required auth info.
    def setUp(self):
        """Run before each test."""
        super(ShellTest, self).setUp()
        for var in self.FAKE_ENV:
            self.useFixture(fixtures.EnvironmentVariable(var,
                                                         self.FAKE_ENV[var]))

        self.shell = shell.OpenStackMonitorShell()

        #HACK(bcwaldon): replace this when we start using stubs
        self.old_get_client_class = client.get_client_class
        client.get_client_class = lambda *_: fakes.FakeClient

    def tearDown(self):
        # For some method like test_image_meta_bad_action we are
        # testing a SystemExit to be thrown and object self.shell has
        # no time to get instantatiated which is OK in this case, so
        # we make sure the method is there before launching it.
        if hasattr(self.shell, 'cs'):
            self.shell.cs.clear_callstack()

        #HACK(bcwaldon): replace this when we start using stubs
        client.get_client_class = self.old_get_client_class
        super(ShellTest, self).tearDown()

    def run_command(self, cmd):
        self.shell.main(cmd.split())

    def assert_called(self, method, url, body=None, **kwargs):
        return self.shell.cs.assert_called(method, url, body, **kwargs)

    def assert_called_anytime(self, method, url, body=None):
        return self.shell.cs.assert_called_anytime(method, url, body)

    def test_list(self):
        self.run_command('list')
        # NOTE(jdg): we default to detail currently
        self.assert_called('GET', '/monitors/detail')

    def test_list_filter_status(self):
        self.run_command('list --status=available')
        self.assert_called('GET', '/monitors/detail?status=available')

    def test_list_filter_name(self):
        self.run_command('list --name=1234')
        self.assert_called('GET', '/monitors/detail?name=1234')

    def test_list_all_tenants(self):
        self.run_command('list --all-tenants=1')
        self.assert_called('GET', '/monitors/detail?all_tenants=1')

    def test_show(self):
        self.run_command('show 1234')
        self.assert_called('GET', '/monitors/1234')

    def test_delete(self):
        self.run_command('delete 1234')
        self.assert_called('DELETE', '/monitors/1234')

    def test_snapshot_list_filter_monitor_id(self):
        self.run_command('snapshot-list --monitor-id=1234')
        self.assert_called('GET', '/snapshots/detail?monitor_id=1234')

    def test_snapshot_list_filter_status_and_monitor_id(self):
        self.run_command('snapshot-list --status=available --monitor-id=1234')
        self.assert_called('GET', '/snapshots/detail?'
                           'status=available&monitor_id=1234')

    def test_rename(self):
        # basic rename with positional agruments
        self.run_command('rename 1234 new-name')
        expected = {'monitor': {'name': 'new-name'}}
        self.assert_called('PUT', '/monitors/1234', body=expected)
        # change description only
        self.run_command('rename 1234 --description=new-description')
        expected = {'monitor': {'description': 'new-description'}}
        self.assert_called('PUT', '/monitors/1234', body=expected)
        # rename and change description
        self.run_command('rename 1234 new-name '
                         '--description=new-description')
        expected = {'monitor': {
            'name': 'new-name',
            'description': 'new-description',
        }}
        self.assert_called('PUT', '/monitors/1234', body=expected)
        # noop, the only all will be the lookup
        self.run_command('rename 1234')
        self.assert_called('GET', '/monitors/1234')

    def test_rename_snapshot(self):
        # basic rename with positional agruments
        self.run_command('snapshot-rename 1234 new-name')
        expected = {'snapshot': {'name': 'new-name'}}
        self.assert_called('PUT', '/snapshots/1234', body=expected)
        # change description only
        self.run_command('snapshot-rename 1234 '
                         '--description=new-description')
        expected = {'snapshot': {'description': 'new-description'}}
        self.assert_called('PUT', '/snapshots/1234', body=expected)
        # snapshot-rename and change description
        self.run_command('snapshot-rename 1234 new-name '
                         '--description=new-description')
        expected = {'snapshot': {
            'name': 'new-name',
            'description': 'new-description',
        }}
        self.assert_called('PUT', '/snapshots/1234', body=expected)
        # noop, the only all will be the lookup
        self.run_command('snapshot-rename 1234')
        self.assert_called('GET', '/snapshots/1234')

    def test_set_metadata_set(self):
        self.run_command('metadata 1234 set key1=val1 key2=val2')
        self.assert_called('POST', '/monitors/1234/metadata',
                           {'metadata': {'key1': 'val1', 'key2': 'val2'}})

    def test_set_metadata_delete_dict(self):
        self.run_command('metadata 1234 unset key1=val1 key2=val2')
        self.assert_called('DELETE', '/monitors/1234/metadata/key1')
        self.assert_called('DELETE', '/monitors/1234/metadata/key2', pos=-2)

    def test_set_metadata_delete_keys(self):
        self.run_command('metadata 1234 unset key1 key2')
        self.assert_called('DELETE', '/monitors/1234/metadata/key1')
        self.assert_called('DELETE', '/monitors/1234/metadata/key2', pos=-2)
