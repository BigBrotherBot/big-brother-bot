#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2011 Courgette
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
from mock import Mock, patch, call
import time
import sys
from mockito import when, any as whatever
from tests import B3TestCase
import unittest2 as unittest
import os

from b3 import __file__ as b3_module__file__
from b3.plugin import Plugin
from b3.plugins.admin import AdminPlugin, Command
from b3.config import XmlConfigParser
from b3.clients import Client, Group, ClientVar, Penalty, ClientBan, ClientTempBan


ADMIN_CONFIG_FILE = os.path.join(os.path.dirname(b3_module__file__), "conf/plugin_admin.xml")

class Admin_TestCase(B3TestCase):
    """ tests from a class inherithing from Admin_TestCase must call self.init() """
    def setUp(self):
        B3TestCase.setUp(self)
        self.conf = XmlConfigParser()
        self.p = AdminPlugin(self.console, self.conf)

    def init(self, config_content=None):
        """ optionally specify a config for the plugin. If called with no parameter, then the default config is loaded """
        if config_content is None:
            if not os.path.isfile(ADMIN_CONFIG_FILE):
                B3TestCase.tearDown(self) # we are skipping the test at a late stage after setUp was called
                raise unittest.SkipTest("%s is not a file" % ADMIN_CONFIG_FILE)
            else:
                self.conf.load(ADMIN_CONFIG_FILE)
        else:
            self.conf.loadFromString(config_content)
        self.p.onLoadConfig()
        self.p.onStartup()


class Test_parseUserCmd(Admin_TestCase):

    def setUp(self):
        Admin_TestCase.setUp(self)
        self.init()

    @unittest.expectedFailure
    def test_clientinfo_bad_arg(self):
        self.assertIsNone(self.p.parseUserCmd(None))

    def test_clientinfo_empty_arg(self):
        self.assertIsNone(self.p.parseUserCmd(''))

    def test_clientinfo_only_1_arg(self):
        self.assertEqual(('someone', None), self.p.parseUserCmd('someone'))
        # see https://github.com/xlr8or/big-brother-bot/issues/54
        self.assertIsNone(self.p.parseUserCmd('someone', req=True))

    def test_clientinfo_2_args(self):
        self.assertEqual(('someone', 'param1'), self.p.parseUserCmd('someone param1'))
        self.assertEqual(('someone', 'param1'), self.p.parseUserCmd('someone param1', req=True))

    def test_clientinfo_3_args(self):
        self.assertEqual(('someone', 'param1 param2'), self.p.parseUserCmd('someone param1 param2'))
        self.assertEqual(('someone', 'param1 param2'), self.p.parseUserCmd('someone param1 param2', req=True))

    def test_clientinfo_int(self):
        self.assertEqual(('45', None), self.p.parseUserCmd('45'))
        self.assertEqual(('45', None), self.p.parseUserCmd("'45'"))
        self.assertEqual(('45', 'some param'), self.p.parseUserCmd("'45' some param"))


class Test_getGroupLevel(Admin_TestCase):

    def setUp(self):
        Admin_TestCase.setUp(self)
        self.init()

    def test_nominal(self):
        for test_data, expected in {
            'NONE': 'none',
            '0': 0,
            '1': 1,
            'guest': 0,
            'user': 1,
            'reg': 2,
            'mod': 20,
            'admin': 40,
            'fulladmin': 60,
            'senioradmin': 80,
            'superadmin': 100,
            '1-20': '1-20',
            '40-20': '40-20',
            'user-admin': '1-40',
        }.items():
            result = self.p.getGroupLevel(test_data)
            if expected != result:
                self.fail("%r, expecting %r but got %r" % (test_data, expected, result))

    def test_failures(self):
        self.p.error = Mock()
        for test_data in ('foo', 'mod-foo', 'foo-mod'):
            self.assertFalse(self.p.getGroupLevel(test_data))
            assert self.p.error.called



class Test_misc_cmd(Admin_TestCase):

    def setUp(self):
        Admin_TestCase.setUp(self)
        self.init()
        self.p.console.say = Mock()

    def test_die(self):
        self.console.die = Mock()
        self.p.cmd_die(None, None, Mock())
        assert self.console.die.called

    def test_restart(self):
        self.console.restart = Mock()
        self.p.cmd_restart(None, None, Mock())
        assert self.console.restart.called

    def test_reconfig(self):
        self.console.reloadConfigs = Mock()
        self.p.cmd_reconfig(None, None, Mock())
        assert self.console.reloadConfigs.called

    def test_map(self):
        mock_client = Mock(spec=Client, name="client")
        self.console.changeMap = Mock()

        # no data
        self.p.cmd_map(data=None, client=mock_client, cmd=Mock(spec=Command))
        mock_client.message.assert_called_once_with('^7You must supply a map to change to.')
        assert not self.console.changeMap.called

        # correct data
        mock_client.reset_mock()
        self.console.changeMap = Mock(return_value='foo')
        self.p.cmd_map(data='bar', client=mock_client, cmd=Mock(spec=Command))
        self.console.changeMap.assert_called_once_with('bar')
        assert not mock_client.message.called

        # incorrect data
        mock_client.reset_mock()
        self.console.changeMap = Mock(return_value=['foo1', 'foo2', 'foo3'])
        self.p.cmd_map(data='bar', client=mock_client, cmd=Mock(spec=Command))
        self.console.changeMap.assert_called_once_with('bar')
        assert mock_client.message.called

    def test_maps(self):
        mock_client = Mock(spec=Client, name="client")
        mock_cmd = Mock(spec=Command)

        # None
        self.console.getMaps = Mock(return_value=None)
        self.p.cmd_maps(data=None, client=mock_client, cmd=mock_cmd)
        mock_client.message.assert_called_once_with('^7Error: could not get map list')

        # no map
        self.console.getMaps = Mock(return_value=[])
        self.p.cmd_maps(data=None, client=mock_client, cmd=mock_cmd)
        mock_cmd.sayLoudOrPM.assert_called_once_with(mock_client, '^7Map Rotation list is empty')

        # one map
        mock_cmd.reset_mock()
        self.console.getMaps = Mock(return_value=['foo'])
        self.p.cmd_maps(data=None, client=mock_client, cmd=mock_cmd)
        mock_cmd.sayLoudOrPM.assert_called_once_with(mock_client, '^7Map Rotation: ^2foo')

        # many maps
        mock_cmd.reset_mock()
        self.console.getMaps = Mock(return_value=['foo1', 'foo2', 'foo3'])
        self.p.cmd_maps(data=None, client=mock_client, cmd=mock_cmd)
        mock_cmd.sayLoudOrPM.assert_called_once_with(mock_client, '^7Map Rotation: ^2foo1^7, ^2foo2^7, ^2foo3')

    def test_maprotate(self):
        self.console.rotateMap = Mock()
        self.p.cmd_maprotate(None, None, Mock(spec=Command))
        assert self.console.rotateMap.called

    def test_b3(self):
        self.console.say = Mock()
        self.p.config = Mock(name="config")
        self.p.config.getint = Mock(return_value=10)

        mock_client = Mock(spec=Client, name="client")
        mock_command = Mock(spec=Command, name='cmd')

        mock_client.maxLevel = 0
        self.p.cmd_b3(data='', client=mock_client, cmd=mock_command)
        assert mock_command.sayLoudOrPM.called

        mock_client.maxLevel = 20
        mock_client.reset_mock()
        self.p.cmd_b3(data='', client=mock_client, cmd=mock_command)
        assert mock_command.sayLoudOrPM.called

        for param in ('poke', 'expose', 'stare', 'stab', 'triangulate', 'bite', 'fuck', 'slap', 'fight', 'feed',
                      'throw', 'furniture', 'indeed', 'flog', 'sexor', 'hate', 'smoke', 'maul', 'procreate',
                      'shoot'):
            mock_client.reset_mock()
            self.p.cmd_b3(data=param, client=mock_client, cmd=mock_command)
            if not self.console.say.called:
                self.fail("self.console.say was not called for %r" % param)


    def test_enable(self):
        mock_client = Mock(spec=Client, name="client")
        mock_client.maxLevel = 0
        mock_command = Mock(spec=Command, name='cmd')

        self.p.cmd_enable(data='', client=mock_client, cmd=mock_command)
        mock_client.message.assert_called_once_with('^7You must supply a plugin name to enable.')

        mock_client.reset_mock()
        self.p.cmd_enable(data='admin', client=mock_client, cmd=mock_command)
        mock_client.message.assert_called_once_with('^7You cannot disable/enable the admin plugin.')

        mock_client.reset_mock()
        self.p.console.getPlugin = Mock(return_value=None)
        self.p.cmd_enable(data='foo', client=mock_client, cmd=mock_command)
        mock_client.message.assert_called_once_with('^7No plugin named foo loaded.')

        mock_client.reset_mock()
        mock_pluginA = Mock(spec=Plugin)
        mock_pluginA.isEnabled = Mock(return_value=True)
        self.p.console.getPlugin = Mock(return_value=mock_pluginA)
        self.p.cmd_enable(data='foo', client=mock_client, cmd=mock_command)
        mock_client.message.assert_called_once_with('^7Plugin foo is already enabled.')

        mock_client.reset_mock()
        mock_pluginA = Mock(spec=Plugin)
        mock_pluginA.__class__.__name__ = "MockPlugin"
        mock_pluginA.isEnabled = Mock(return_value=False)
        self.p.console.getPlugin = Mock(return_value=mock_pluginA)
        self.p.cmd_enable(data='foo', client=mock_client, cmd=mock_command)
        self.p.console.say.assert_called_once_with('^7MockPlugin is now ^2ON')


    def test_disable(self):
        mock_client = Mock(spec=Client, name="client")
        mock_client.maxLevel = 0
        mock_command = Mock(spec=Command, name='cmd')

        self.p.cmd_disable(data='', client=mock_client, cmd=mock_command)
        mock_client.message.assert_called_once_with('^7You must supply a plugin name to disable.')

        mock_client.reset_mock()
        self.p.cmd_disable(data='admin', client=mock_client, cmd=mock_command)
        mock_client.message.assert_called_once_with('^7You cannot disable/enable the admin plugin.')

        mock_client.reset_mock()
        self.p.console.getPlugin = Mock(return_value=None)
        self.p.cmd_disable(data='foo', client=mock_client, cmd=mock_command)
        mock_client.message.assert_called_once_with('^7No plugin named foo loaded.')

        mock_client.reset_mock()
        mock_pluginA = Mock(spec=Plugin)
        mock_pluginA.isEnabled = Mock(return_value=False)
        self.p.console.getPlugin = Mock(return_value=mock_pluginA)
        self.p.cmd_disable(data='foo', client=mock_client, cmd=mock_command)
        mock_client.message.assert_called_once_with('^7Plugin foo is already disable.')

        mock_client.reset_mock()
        mock_pluginA = Mock(spec=Plugin)
        mock_pluginA.__class__.__name__ = "MockPlugin"
        mock_pluginA.isEnabled = Mock(return_value=True)
        self.p.console.getPlugin = Mock(return_value=mock_pluginA)
        self.p.cmd_disable(data='foo', client=mock_client, cmd=mock_command)
        self.p.console.say.assert_called_once_with('^7MockPlugin is now ^1OFF')


    def test_rebuild(self):
        mock_client = Mock(spec=Client, name="client")
        mock_client.maxLevel = 0
        mock_command = Mock(spec=Command, name='cmd')
        self.p.console.clients.sync = Mock()

        assert not self.p.console.clients.sync.called
        self.p.cmd_rebuild(data='', client=mock_client, cmd=mock_command)
        assert self.p.console.clients.sync.called


class CommandTestCase(Admin_TestCase):
    """ tests from a class inherithing from CommandTestCase must call self.init() """
    def setUp(self):
        Admin_TestCase.setUp(self)
        self.mock_client = Mock(spec=Client, name="client")
        self.mock_client.maxLevel = 0
        self.mock_client.exactName = "MockClient"
        self.mock_command = Mock(spec=Command, name='cmd')

        self.p.getMessage = Mock(return_value='')


class Test_cmd_iamgod(CommandTestCase):

    def setUp(self):
        CommandTestCase.setUp(self)
        self.init()
        self._commands_patcher = patch.object(self.p, '_commands')
        self._commands_patcher.start()

    def tearDown(self):
        CommandTestCase.tearDown(self)
        self._commands_patcher.stop()

    def iamgod(self, data=''):
        return self.p.cmd_iamgod(data=data, client=self.mock_client, cmd=self.mock_command)


    def test_when_there_is_already_a_superadmin(self):
        self.p._commands['iamgod'] = 'foo'
        self.p.warning = Mock()
        self.p.console.clients.lookupSuperAdmins = Mock(return_value=[Mock(spec=Client)])

        self.iamgod()
        self.p.warning.assert_called()
        self.assertNotIn('iamgod', self.p._commands)


    def test_is_already_superadmin(self):
        mock_iamgod_cmd = Mock(spec=Command, name="iamgod command")
        mock_superadmin_group = Mock(spec=Group)
        mock_superadmin_group.exactName = "superadmin"
        self.p._commands['iamgod'] = mock_iamgod_cmd
        self.p.console.clients.lookupSuperAdmins = Mock(return_value=[])
        self.p.console.storage.getGroup = Mock(return_value=mock_superadmin_group)
        self.mock_client.groups = [mock_superadmin_group]

        self.iamgod()
        self.mock_client.message.assert_called_once_with('^7You are already a superadmin')


    def test_when_there_is_no_superadmin(self):
        mock_iamgod_cmd = Mock(spec=Command, name="iamgod command")
        mock_superadmin_group = Mock(spec=Group)
        self.p._commands['iamgod'] = mock_iamgod_cmd
        self.p.console.clients.lookupSuperAdmins = Mock(return_value=[])
        self.p.console.storage.getGroup = Mock(return_value=mock_superadmin_group)
        self.mock_client.groups = []

        self.iamgod()
        self.mock_client.setGroup.assert_called_once_with(mock_superadmin_group)
        self.mock_client.save.assert_called_once_with()
        self.mock_client.message.assert_called_once_with('^7You are now a %s' % mock_superadmin_group.name)


class Test_cmd_warn(CommandTestCase):

    def setUp(self):
        CommandTestCase.setUp(self)
        self.init()
        self.p.warnClient = Mock()

    def warn(self, data=''):
        return self.p.cmd_warn(data=data, client=self.mock_client, cmd=self.mock_command)

    def test_no_parameter(self):
        self.warn()
        self.mock_client.message.assert_called_once_with('^7Invalid parameters')
        assert not self.p.warnClient.called

    def test_player_not_found(self):
        self.p.findClientPrompt = Mock(return_value=None)
        self.warn('foo')
        self.p.findClientPrompt.assert_called_once_with('foo', self.mock_client)
        assert not self.p.warnClient.called

    def test_prevent_warn_self(self):
        foo_player = self.mock_client
        self.p.findClientPrompt = Mock(return_value=foo_player)
        self.warn('foo')
        self.p.getMessage.assert_called_once_with('warn_self', self.mock_client.exactName)
        assert not self.p.warnClient.called

    def test_player_is_higher_level(self):
        foo_player = Mock(spec=Client, name="foo")
        foo_player.maxLevel = 20
        self.mock_client.maxLevel = 0
        self.p.findClientPrompt = Mock(return_value=foo_player)
        self.warn('foo')
        self.p.getMessage.assert_called_once_with('warn_denied', self.mock_client.exactName, foo_player.exactName)
        assert not self.p.warnClient.called

    def test_already_warned_recently(self):
        self.p.console.time = Mock(return_value=8)
        foo_player = Mock(spec=Client, name="foo")
        foo_player.maxLevel = 0
        foo_player.var = Mock(return_value=ClientVar(5))
        self.mock_client.maxLevel = 20
        self.p.findClientPrompt = Mock(return_value=foo_player)
        self.warn('foo')
        self.mock_client.message.assert_called_once_with('^7Only one warning per 15 seconds can be issued')
        assert not self.p.warnClient.called

    def test_nominal_no_keyword(self):
        self.p.console.time = Mock(return_value=16)
        foo_player = Mock(spec=Client, name="foo")
        foo_player.maxLevel = 0
        foo_player.var = Mock(return_value=ClientVar(None))
        self.mock_client.maxLevel = 20
        self.p.findClientPrompt = Mock(return_value=foo_player)
        self.warn('foo')
        self.p.warnClient.assert_called_once_with(foo_player, None, self.mock_client)

    def test_nominal_with_keyword(self):
        self.p.console.time = Mock(return_value=16)
        foo_player = Mock(spec=Client, name="foo")
        foo_player.maxLevel = 0
        foo_player.var = Mock(return_value=ClientVar(None))
        self.mock_client.maxLevel = 20
        self.p.findClientPrompt = Mock(return_value=foo_player)
        self.warn('foo thekeyword')
        self.p.warnClient.assert_called_once_with(foo_player, 'thekeyword', self.mock_client)



class Test_cmd_kick(CommandTestCase):

    def setUp(self):
        CommandTestCase.setUp(self)
        self.init()
        self.p._noreason_level = 2

    def kick(self, data=''):
        return self.p.cmd_kick(data=data, client=self.mock_client, cmd=self.mock_command)

    def test_no_parameter(self):
        self.kick()
        self.mock_client.message.assert_called_once_with('^7Invalid parameters')
        assert not self.mock_client.kick.called

    def test_no_reason(self):
        self.p.config.getint = Mock(return_value=4)
        self.mock_client.maxLevel = 1
        assert self.mock_client.maxLevel < self.p._noreason_level
        self.kick('foo')
        self.mock_client.message.assert_called_once_with('^1ERROR: ^7You must supply a reason')
        assert not self.mock_client.kick.called

    def test_player_not_found(self):
        self.p.findClientPrompt = Mock(return_value=None)
        self.mock_client.maxLevel = 3
        self.kick('foo')
        self.p.findClientPrompt.assert_called_once_with('foo', self.mock_client)
        assert not self.mock_client.kick.called

    def test_prevent_kick_self(self):
        foo_player = self.mock_client
        self.mock_client.maxLevel = 3
        self.p.findClientPrompt = Mock(return_value=foo_player)
        self.kick('foo')
        self.p.getMessage.assert_called_once_with('kick_self', self.mock_client.exactName)
        assert not self.mock_client.kick.called

    def test_player_is_higher_level(self):
        foo_player = Mock(spec=Client, name="foo")
        foo_player.maxLevel = 20
        foo_player.maskGroup = None
        self.mock_client.maxLevel = 5
        self.p.findClientPrompt = Mock(return_value=foo_player)
        self.kick('foo')
        self.p.getMessage.assert_called_once_with('kick_denied', foo_player.exactName, self.mock_client.exactName, foo_player.exactName)
        assert not self.mock_client.kick.called

    def test_player_is_higher_level_but_masked(self):
        foo_player = Mock(spec=Client, name="foo")
        foo_player.maxLevel = 20
        foo_player.maskGroup = Mock()
        foo_player.exactName = "Foo"
        self.mock_client.maxLevel = 5
        self.p.findClientPrompt = Mock(return_value=foo_player)
        self.kick('foo')
        self.mock_client.message.assert_called_once_with('^7%s ^7is a masked higher level player, can\'t kick' % foo_player.exactName)
        assert not self.mock_client.kick.called

    def test_nominal_no_reason(self):
        foo_player = Mock(spec=Client, name="foo")
        foo_player.maxLevel = 0
        self.mock_client.maxLevel = 20
        self.p.findClientPrompt = Mock(return_value=foo_player)
        self.kick('foo')
        foo_player.kick.assert_called_once_with('', None, self.mock_client)

    def test_nominal_with_reason(self):
        foo_player = Mock(spec=Client, name="foo")
        foo_player.maxLevel = 0
        self.mock_client.maxLevel = 20
        self.p.findClientPrompt = Mock(return_value=foo_player)
        self.kick('foo theReason')
        foo_player.kick.assert_called_once_with('theReason', 'theReason', self.mock_client)

    def test_nominal_with_reason_keyword(self):
        foo_player = Mock(spec=Client, name="foo")
        foo_player.maxLevel = 0
        self.mock_client.maxLevel = 20
        self.p.findClientPrompt = Mock(return_value=foo_player)
        self.p.getReason = Mock(return_value="aReason")
        self.kick('foo theKeyword')
        foo_player.kick.assert_called_once_with('aReason', 'theKeyword', self.mock_client)


class Test_cmd_spank(CommandTestCase):

    def setUp(self):
        CommandTestCase.setUp(self)
        self.init()
        self.p._noreason_level = 2

    def spank(self, data=''):
        return self.p.cmd_spank(data=data, client=self.mock_client, cmd=self.mock_command)

    def test_no_parameter(self):
        self.spank()
        self.mock_client.message.assert_called_once_with('^7Invalid parameters')
        assert not self.mock_client.kick.called

    def test_no_reason(self):
        self.p.config.getint = Mock(return_value=4)
        self.mock_client.maxLevel = 1
        assert self.mock_client.maxLevel < self.p._noreason_level
        self.spank('foo')
        self.mock_client.message.assert_called_once_with('^1ERROR: ^7You must supply a reason')
        assert not self.mock_client.kick.called

    def test_player_not_found(self):
        self.p.findClientPrompt = Mock(return_value=None)
        self.mock_client.maxLevel = 3
        self.spank('foo')
        self.p.findClientPrompt.assert_called_once_with('foo', self.mock_client)
        assert not self.mock_client.kick.called

    def test_prevent_kick_self(self):
        foo_player = self.mock_client
        self.mock_client.maxLevel = 3
        self.p.findClientPrompt = Mock(return_value=foo_player)
        self.spank('foo')
        self.p.getMessage.assert_called_once_with('kick_self', self.mock_client.exactName)
        assert not self.mock_client.kick.called

    def test_player_is_higher_level(self):
        foo_player = Mock(spec=Client, name="foo")
        foo_player.maxLevel = 20
        foo_player.maskGroup = None
        self.mock_client.maxLevel = 5
        self.p.findClientPrompt = Mock(return_value=foo_player)
        self.spank('foo')
        self.p.getMessage.assert_called_once_with('kick_denied', foo_player.exactName, self.mock_client.exactName, foo_player.exactName)
        assert not self.mock_client.kick.called

    def test_player_is_higher_level_but_masked(self):
        foo_player = Mock(spec=Client, name="foo")
        foo_player.maxLevel = 20
        foo_player.maskGroup = Mock()
        foo_player.exactName = "Foo"
        self.mock_client.maxLevel = 5
        self.p.findClientPrompt = Mock(return_value=foo_player)
        self.spank('foo')
        self.mock_client.message.assert_called_once_with('^7%s ^7is a masked higher level player, can\'t spank' % foo_player.exactName)
        assert not self.mock_client.kick.called

    def test_nominal_no_reason(self):
        foo_player = Mock(spec=Client, name="foo")
        foo_player.maxLevel = 0
        self.mock_client.maxLevel = 20
        self.p.findClientPrompt = Mock(return_value=foo_player)
        self.spank('foo')
        foo_player.kick.assert_called_once_with('', None, self.mock_client, silent=True)

    def test_nominal_with_reason(self):
        foo_player = Mock(spec=Client, name="foo")
        foo_player.maxLevel = 0
        self.mock_client.maxLevel = 20
        self.p.findClientPrompt = Mock(return_value=foo_player)
        self.spank('foo theReason')
        foo_player.kick.assert_called_once_with('theReason', 'theReason', self.mock_client, silent=True)

    def test_nominal_with_reason_keyword(self):
        foo_player = Mock(spec=Client, name="foo")
        foo_player.maxLevel = 0
        self.mock_client.maxLevel = 20
        self.p.findClientPrompt = Mock(return_value=foo_player)
        self.p.getReason = Mock(return_value="aReason")
        self.spank('foo theKeyword')
        foo_player.kick.assert_called_once_with('aReason', 'theKeyword', self.mock_client, silent=True)



class Test_cmd_permban(CommandTestCase):

    def setUp(self):
        CommandTestCase.setUp(self)
        self.init()
        self.p._noreason_level = 2

    def permban(self, data=''):
        return self.p.cmd_permban(data=data, client=self.mock_client, cmd=self.mock_command)

    def test_no_parameter(self):
        self.permban()
        self.mock_client.message.assert_called_once_with('^7Invalid parameters')
        assert not self.mock_client.ban.called

    def test_no_reason(self):
        self.p.config.getint = Mock(return_value=4)
        self.mock_client.maxLevel = 1
        assert self.mock_client.maxLevel < self.p._noreason_level
        self.permban('foo')
        self.mock_client.message.assert_called_once_with('^1ERROR: ^7You must supply a reason')
        assert not self.mock_client.ban.called

    def test_player_not_found(self):
        self.p.findClientPrompt = Mock(return_value=None)
        self.mock_client.maxLevel = 3
        self.permban('foo')
        self.p.findClientPrompt.assert_called_once_with('foo', self.mock_client)
        assert not self.mock_client.ban.called

    def test_prevent_permban_self(self):
        foo_player = self.mock_client
        self.mock_client.maxLevel = 3
        self.p.findClientPrompt = Mock(return_value=foo_player)
        self.permban('foo')
        self.p.getMessage.assert_called_once_with('ban_self', self.mock_client.exactName)
        assert not self.mock_client.ban.called

    def test_player_is_higher_level(self):
        foo_player = Mock(spec=Client, name="foo")
        foo_player.maxLevel = 20
        foo_player.maskGroup = None
        self.mock_client.maxLevel = 5
        self.p.findClientPrompt = Mock(return_value=foo_player)
        self.permban('foo')
        self.p.getMessage.assert_called_once_with('ban_denied', self.mock_client.exactName, foo_player.exactName)
        assert not self.mock_client.ban.called

    def test_player_is_higher_level_but_masked(self):
        foo_player = Mock(spec=Client, name="foo")
        foo_player.maxLevel = 20
        foo_player.maskGroup = Mock()
        foo_player.exactName = "Foo"
        self.mock_client.maxLevel = 5
        self.p.findClientPrompt = Mock(return_value=foo_player)
        self.permban('foo')
        self.mock_client.message.assert_called_once_with('^7%s ^7is a masked higher level player, can\'t ban' % foo_player.exactName)
        assert not self.mock_client.ban.called

    def test_nominal_no_reason(self):
        foo_player = Mock(spec=Client, name="foo")
        foo_player.maxLevel = 0
        self.mock_client.maxLevel = 20
        self.p.findClientPrompt = Mock(return_value=foo_player)
        self.permban('foo')
        foo_player.ban.assert_called_once_with('', None, self.mock_client)

    def test_nominal_with_reason(self):
        foo_player = Mock(spec=Client, name="foo")
        foo_player.maxLevel = 0
        self.mock_client.maxLevel = 20
        self.p.findClientPrompt = Mock(return_value=foo_player)
        self.permban('foo theReason')
        foo_player.ban.assert_called_once_with('theReason', 'theReason', self.mock_client)

    def test_nominal_with_reason_keyword(self):
        foo_player = Mock(spec=Client, name="foo")
        foo_player.maxLevel = 0
        self.mock_client.maxLevel = 20
        self.p.findClientPrompt = Mock(return_value=foo_player)
        self.p.getReason = Mock(return_value="aReason")
        self.permban('foo theKeyword')
        foo_player.ban.assert_called_once_with('aReason', 'theKeyword', self.mock_client)


class Test_cmd_tempban(CommandTestCase):

    def setUp(self):
        CommandTestCase.setUp(self)
        self.init()
        self.p._noreason_level = 2
        self.p._long_tempban_level = 2

    def tempban(self, data=''):
        return self.p.cmd_tempban(data=data, client=self.mock_client, cmd=self.mock_command)

    def test_no_parameter(self):
        self.tempban()
        self.mock_client.message.assert_called_once_with('^7Invalid parameters')
        assert not self.mock_client.tempban.called

    def test_invalid_duration(self):
        self.p.config.getint = Mock(return_value=4)
        self.mock_client.maxLevel = 3
        assert self.mock_client.maxLevel < self.p.config.getint('whatever')
        self.tempban('foo sdf')
        self.mock_client.message.assert_called_once_with('^7Invalid parameters')
        assert not self.mock_client.tempban.called

    def test_no_duration(self):
        self.p.config.getint = Mock(return_value=4)
        self.mock_client.maxLevel = 3
        assert self.mock_client.maxLevel < self.p.config.getint('whatever')
        self.tempban('foo')
        self.mock_client.message.assert_called_once_with('^7Invalid parameters')
        assert not self.mock_client.tempban.called

    def test_no_reason(self):
        self.p.config.getint = Mock(return_value=4)
        self.mock_client.maxLevel = 1
        assert self.mock_client.maxLevel < self.p._noreason_level
        self.tempban('foo 3h')
        self.mock_client.message.assert_called_once_with('^1ERROR: ^7You must supply a reason')
        assert not self.mock_client.tempban.called

    def test_player_not_found(self):
        self.p.findClientPrompt = Mock(return_value=None)
        self.mock_client.maxLevel = 3
        self.tempban('foo 3h')
        self.p.findClientPrompt.assert_called_once_with('foo', self.mock_client)
        assert not self.mock_client.tempban.called

    def test_prevent_tempban_self(self):
        foo_player = self.mock_client
        self.mock_client.maxLevel = 3
        self.p.findClientPrompt = Mock(return_value=foo_player)
        self.tempban('foo 3h')
        self.p.getMessage.assert_called_once_with('temp_ban_self', self.mock_client.exactName)
        assert not self.mock_client.tempban.called

    def test_player_is_higher_level(self):
        foo_player = Mock(spec=Client, name="foo")
        foo_player.maxLevel = 20
        foo_player.maskGroup = None
        self.mock_client.maxLevel = 5
        self.p.findClientPrompt = Mock(return_value=foo_player)
        self.tempban('foo 3h')
        self.p.getMessage.assert_called_once_with('temp_ban_denied', self.mock_client.exactName, foo_player.exactName)
        assert not self.mock_client.tempban.called

    def test_player_is_higher_level_but_masked(self):
        foo_player = Mock(spec=Client, name="foo")
        foo_player.maxLevel = 20
        foo_player.maskGroup = Mock()
        foo_player.exactName = "Foo"
        self.mock_client.maxLevel = 5
        self.p.findClientPrompt = Mock(return_value=foo_player)
        self.tempban('foo 3h')
        self.mock_client.message.assert_called_once_with('^7%s ^7is a masked higher level player, can\'t temp ban' % foo_player.exactName)
        assert not self.mock_client.tempban.called

    def test_nominal_no_reason(self):
        foo_player = Mock(spec=Client, name="foo")
        foo_player.maxLevel = 0
        self.mock_client.maxLevel = 20
        self.p.findClientPrompt = Mock(return_value=foo_player)
        self.tempban('foo 3h')
        foo_player.tempban.assert_called_once_with('', None, 3*60, self.mock_client)

    def test_nominal_with_reason(self):
        foo_player = Mock(spec=Client, name="foo")
        foo_player.maxLevel = 0
        self.mock_client.maxLevel = 20
        self.p.findClientPrompt = Mock(return_value=foo_player)
        self.tempban('foo 3h theReason')
        foo_player.tempban.assert_called_once_with('theReason', 'theReason', 3*60, self.mock_client)

    def test_nominal_with_reason_keyword(self):
        foo_player = Mock(spec=Client, name="foo")
        foo_player.maxLevel = 0
        self.mock_client.maxLevel = 20
        self.p.findClientPrompt = Mock(return_value=foo_player)
        self.p.getReason = Mock(return_value="aReason")
        self.tempban('foo 3h theKeyword')
        foo_player.tempban.assert_called_once_with('aReason', 'theKeyword', 3*60, self.mock_client)


class Test_cmd_mask(CommandTestCase):

    def setUp(self):
        CommandTestCase.setUp(self)
        self.init()
        self.player = Client(console=self.console, name="joe", _maxLevel=0)
        self.player.message = Mock()
        self.assertEqual(0, self.player.maskedLevel)
        self.assertIsNone(self.player.maskedGroup)

    def mask(self, data=''):
        return self.p.cmd_mask(data=data, client=self.player, cmd=self.mock_command)

    def test_no_parameter(self):
        self.mask()
        self.player.message.assert_called_once_with('^7Invalid parameters')
        self.assertEqual(0, self.player.maskedLevel)
        self.assertIsNone(self.player.maskedGroup)

    def test_invalid_group(self):
        self.mask('foo')
        self.player.message.assert_called_once_with('^7Group foo does not exist')
        self.assertEqual(0, self.player.maskedLevel)
        self.assertIsNone(self.player.maskedGroup)

    def test_valid_group(self):
        self.mask('senioradmin')
        self.player.message.assert_called_once_with('^7Masked as Senior Admin')
        self.assertEqual(80, self.player.maskedLevel)
        self.assertIsNotNone(self.player.maskedGroup)


@patch.object(time, "sleep")
class Test_sendRules(Admin_TestCase):

    def test_nominal(self, sleep_mock):
        self.init(r"""<configuration><settings name="spamages">
                        <set name="foo">foo</set>
                        <set name="rule1">this is rule #1</set>
                        <set name="rule2">this is rule #2</set>
                        <set name="bar">bar</set>
                    </settings></configuration>""")
        self.console.say = Mock(wraps=lambda *args: sys.stdout.write("\t\tSAY: " + str(args) + "\n"))
        self.p._sendRules(None)
        self.console.say.assert_has_calls([call('this is rule #1'), call('this is rule #2')])

    def test_no_rule_1(self, sleep_mock):
        self.init(r"""<configuration><settings name="spamages">
                        <set name="rule5">this is rule #5</set>
                        <set name="rule2">this is rule #2</set>
                    </settings></configuration>""")
        self.console.say = Mock(wraps=lambda *args: sys.stdout.write("\t\tSAY: " + str(args) + "\n"))
        self.p._sendRules(None)
        self.assertFalse(self.console.say.called)


    def test_gap_in_rules(self, sleep_mock):
        self.init(r"""<configuration><settings name="spamages">
                        <set name="rule1">this is rule #1</set>
                        <set name="rule2">this is rule #2</set>
                        <set name="rule4">this is rule #4</set>
                    </settings></configuration>""")
        self.console.say = Mock(wraps=lambda *args: sys.stdout.write("\t\tSAY: " + str(args) + "\n"))
        self.p._sendRules(None)
        self.console.say.assert_has_calls([call('this is rule #1'), call('this is rule #2')])


    def test_no_rule_in_config(self, sleep_mock):
        self.init(r"""<configuration><settings name="spamages">
                        <set name="foo">foo</set>
                        <set name="bar">bar</set>
                    </settings></configuration>""")
        self.console.say = Mock(wraps=lambda *args: sys.stdout.write("\t\tSAY: " + str(args) + "\n"))
        self.p._sendRules(None)
        self.assertFalse(self.console.say.called)


    def test_too_many_rules(self, sleep_mock):
        self.init(r"""<configuration><settings name="spamages">""" +
            "\n".join(["""<set name="rule%s">this is rule #%s</set>""" % (x, x) for x in range(1, 23)]) +
            """</settings></configuration>""")
        self.console.say = Mock(wraps=lambda *args: sys.stdout.write("\t\tSAY: " + str(args) + "\n"))
        self.p._sendRules(None)
        self.console.say.assert_has_calls([call('this is rule #%s' % x) for x in range(1, 20)])


class Test_cmd_lastbans(CommandTestCase):

    def setUp(self):
        CommandTestCase.setUp(self)
        self.init()
        self.player = Client(console=self.console, name="joe", _maxLevel=0)
        self.player.message = Mock()

    def lastbans(self):
        self.p.cmd_lastbans(data='', client=self.player, cmd=self.mock_command)

    def test_no_ban(self):
        self.lastbans()
        self.mock_command.sayLoudOrPM.assert_called_once_with(self.player, '^7There are no active bans')

    def test_one_ban(self):
        # GIVEN
        player1 = Client(console=self.console, guid='BillGUID', name="Bill")
        player1.save()
        penalty1 = ClientBan(clientId=player1.id, timeExpire=-1, adminId=0)
        when(self.console.storage).getLastPenalties(types=whatever(), num=whatever()).thenReturn([penalty1])
        # WHEN
        self.lastbans()
        # THEN
        self.mock_command.sayLoudOrPM.assert_called_once_with(self.player, u'^2@1^7 Bill^7^7 (Perm)')

    def test_one_ban_with_reason(self):
        # GIVEN
        player1 = Client(console=self.console, guid='BillGUID', name="Bill")
        player1.save()
        penalty1 = ClientBan(clientId=player1.id, timeExpire=-1, adminId=0, reason="test reason")
        when(self.console.storage).getLastPenalties(types=whatever(), num=whatever()).thenReturn([penalty1])
        # WHEN
        self.lastbans()
        # THEN
        self.mock_command.sayLoudOrPM.assert_called_once_with(self.player, u'^2@1^7 Bill^7^7 (Perm) test reason')

    def test_two_bans_with_reason(self):
        # GIVEN
        when(self.console).time().thenReturn(0)
        player1 = Client(console=self.console, guid='player1GUID', name="P1")
        player1.save()
        penalty1 = ClientBan(clientId=player1.id, timeExpire=-1, adminId=0, reason="test reason")

        player2 = Client(console=self.console, guid='player2GUID', name="P2")
        player2.save()
        penalty2 = ClientTempBan(clientId=player2.id, timeExpire=self.console.time() + 60*2, adminId=0, reason="test reason f00")

        when(self.console.storage).getLastPenalties(types=whatever(), num=whatever()).thenReturn([penalty1, penalty2])
        # WHEN
        self.lastbans()
        # THEN
        self.mock_command.sayLoudOrPM.assert_has_calls([
            call(self.player, u'^2@1^7 P1^7^7 (Perm) test reason'),
            call(self.player, u'^2@2^7 P2^7^7 (2 minutes remaining) test reason f00'),
        ])




if __name__ == '__main__':
    unittest.main()