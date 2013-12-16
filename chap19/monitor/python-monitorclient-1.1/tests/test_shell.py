import cStringIO
import os
import re
import sys

import fixtures
from testtools import matchers

from monitorclient import exceptions
import monitorclient.shell
from tests import utils


class ShellTest(utils.TestCase):

    FAKE_ENV = {
        'OS_USERNAME': 'username',
        'OS_PASSWORD': 'password',
        'OS_TENANT_NAME': 'tenant_name',
        'OS_AUTH_URL': 'http://no.where',
    }

    # Patch os.environ to avoid required auth info.
    def setUp(self):
        super(ShellTest, self).setUp()
        for var in self.FAKE_ENV:
            self.useFixture(fixtures.EnvironmentVariable(var,
                                                         self.FAKE_ENV[var]))

    def shell(self, argstr):
        orig = sys.stdout
        try:
            sys.stdout = cStringIO.StringIO()
            _shell = monitorclient.shell.OpenStackMonitorShell()
            _shell.main(argstr.split())
        except SystemExit:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            self.assertEqual(exc_value.code, 0)
        finally:
            out = sys.stdout.getvalue()
            sys.stdout.close()
            sys.stdout = orig

        return out

    def test_help_unknown_command(self):
        self.assertRaises(exceptions.CommandError, self.shell, 'help foofoo')

    def test_help(self):
        required = [
            '.*?^usage: ',
            '.*?(?m)^\s+create\s+Add a new monitor.',
            '.*?(?m)^See "monitor help COMMAND" for help on a specific command',
        ]
        help_text = self.shell('help')
        for r in required:
            self.assertThat(help_text,
                            matchers.MatchesRegex(r, re.DOTALL | re.MULTILINE))

    def test_help_on_subcommand(self):
        required = [
            '.*?^usage: monitor list',
            '.*?(?m)^List all the monitors.',
        ]
        help_text = self.shell('help list')
        for r in required:
            self.assertThat(help_text,
                            matchers.MatchesRegex(r, re.DOTALL | re.MULTILINE))
