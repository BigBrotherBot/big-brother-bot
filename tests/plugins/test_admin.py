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
from mock import Mock
from tests import B3TestCase
import unittest

import b3
from b3.plugin import Plugin
from b3.plugins.admin import AdminPlugin, Command
from b3.config import XmlConfigParser
from b3.clients import Client, Group, ClientVar

 
class Test_parseUserCmd(B3TestCase):

    def setUp(self):
        B3TestCase.setUp(self)
        self.conf = XmlConfigParser()
        self.conf.setXml("""
            <configuration plugin="admin">
            </configuration>
        """)
        self.p = AdminPlugin(b3.console, self.conf)


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


class Test_getGroupLevel(B3TestCase):

    def setUp(self):
        from b3.fake import fakeConsole
        B3TestCase.setUp(self)
        self.conf = XmlConfigParser()
        self.conf.setXml("""
                <configuration plugin="admin">
                </configuration>
            """)
        self.p = AdminPlugin(fakeConsole, self.conf)

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



class Test_misc_cmd(B3TestCase):

    def setUp(self):
        B3TestCase.setUp(self)
        self.conf = XmlConfigParser()
        self.conf.setXml("""
            <configuration plugin="admin">
            </configuration>
        """)
        self.p = AdminPlugin(b3.console, self.conf)


    def test_die(self):
        self.p.cmd_die(None, None, Mock())
        assert b3.console.die.called

    def test_restart(self):
        self.p.cmd_restart(None, None, Mock())
        assert b3.console.restart.called

    def test_reconfig(self):
        self.p.cmd_reconfig(None, None, Mock())
        assert b3.console.reloadConfigs.called

    def test_map(self):
        mock_client = Mock(spec=Client, name="client")

        # no data
        self.p.cmd_map(data=None, client=mock_client, cmd=Mock(spec=Command))
        mock_client.message.assert_called_once_with('^7You must supply a map to change to.')
        assert not b3.console.changeMap.called

        # correct data
        mock_client.reset_mock()
        b3.console.reset_mock()
        b3.console.changeMap = Mock(return_value='foo')
        self.p.cmd_map(data='bar', client=mock_client, cmd=Mock(spec=Command))
        b3.console.changeMap.assert_called_once_with('bar')
        assert not mock_client.message.called

        # incorrect data
        mock_client.reset_mock()
        b3.console.reset_mock()
        b3.console.changeMap = Mock(return_value=['foo1', 'foo2', 'foo3'])
        self.p.cmd_map(data='bar', client=mock_client, cmd=Mock(spec=Command))
        b3.console.changeMap.assert_called_once_with('bar')
        assert mock_client.message.called

    def test_maprotate(self):
        self.p.cmd_maprotate(None, None, Mock(spec=Command))
        assert b3.console.rotateMap.called

    def test_b3(self):
        self.p.config = Mock(name="config")
        self.p.config.getint = Mock(return_value=10)

        mock_client = Mock(spec=Client, name="client")
        mock_command = Mock(spec=Command, name='cmd')

        mock_client.maxLevel = 0
        self.p.cmd_b3(data='', client=mock_client, cmd=mock_command)
        assert mock_command.sayLoudOrPM.called

        mock_client.maxLevel = 20
        mock_client.reset_mock()
        b3.console.reset_mock()
        self.p.cmd_b3(data='', client=mock_client, cmd=mock_command)
        assert mock_command.sayLoudOrPM.called

        for param in ('poke', 'expose', 'stare', 'stab', 'triangulate', 'bite', 'fuck', 'slap', 'fight', 'feed',
                      'throw', 'furniture', 'indeed', 'flog', 'sexor', 'hate', 'smoke', 'maul', 'procreate',
                      'shoot'):
            mock_client.reset_mock()
            b3.console.reset_mock()
            self.p.cmd_b3(data=param, client=mock_client, cmd=mock_command)
            if not b3.console.say.called:
                self.fail("b3.console.say was not called for %r" % param)


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

        assert not self.p.console.clients.sync.called
        self.p.cmd_rebuild(data='', client=mock_client, cmd=mock_command)
        assert self.p.console.clients.sync.called


class CommandTestCase(B3TestCase):
    def setUp(self):
        B3TestCase.setUp(self)
        self.conf = XmlConfigParser()
        self.conf.setXml("""
            <configuration plugin="admin">
                <settings name="warn">
                    <set name="warn_delay">5</set>
                </settings>
            </configuration>
        """)
        self.p = AdminPlugin(b3.console, self.conf)
        self.mock_client = Mock(spec=Client, name="client")
        self.mock_client.maxLevel = 0
        self.mock_client.exactName = "MockClient"
        self.mock_command = Mock(spec=Command, name='cmd')



class Test_cmd_iamgod(CommandTestCase):

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
        self.p.warnClient = Mock()
        self.p.getMessage = Mock()

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
        self.mock_client.message.assert_called_once_with('^7Only one warning per 5 seconds can be issued')
        assert not self.p.warnClient.called

    def test_nominal_no_keyword(self):
        self.p.console.time = Mock(return_value=8)
        foo_player = Mock(spec=Client, name="foo")
        foo_player.maxLevel = 0
        foo_player.var = Mock(return_value=ClientVar(None))
        self.mock_client.maxLevel = 20
        self.p.findClientPrompt = Mock(return_value=foo_player)
        self.warn('foo')
        self.p.warnClient.assert_called_once_with(foo_player, None, self.mock_client)

    def test_nominal_with_keyword(self):
        self.p.console.time = Mock(return_value=8)
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
        self.p.getMessage = Mock()

        def my_getint(section, option):
            if section == "settings" and option == "noreason_level":
                return 2
            else:
                return self.p.config.getint(section, option)
        self.p.config.getint = Mock(side_effect=my_getint)

    def kick(self, data=''):
        return self.p.cmd_kick(data=data, client=self.mock_client, cmd=self.mock_command)

    def test_no_parameter(self):
        self.kick()
        self.mock_client.message.assert_called_once_with('^7Invalid parameters')
        assert not self.mock_client.kick.called

    def test_no_reason(self):
        self.p.config.getint = Mock(return_value=4)
        self.mock_client.maxLevel = 3
        assert self.mock_client.maxLevel < self.p.config.getint('whatever')
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
        self.p.getMessage = Mock()

        def my_getint(section, option):
            if section == "settings" and option == "noreason_level":
                return 2
            else:
                return self.p.config.getint(section, option)
        self.p.config.getint = Mock(side_effect=my_getint)

    def spank(self, data=''):
        return self.p.cmd_spank(data=data, client=self.mock_client, cmd=self.mock_command)

    def test_no_parameter(self):
        self.spank()
        self.mock_client.message.assert_called_once_with('^7Invalid parameters')
        assert not self.mock_client.kick.called

    def test_no_reason(self):
        self.p.config.getint = Mock(return_value=4)
        self.mock_client.maxLevel = 3
        assert self.mock_client.maxLevel < self.p.config.getint('whatever')
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
        self.p.getMessage = Mock()

        def my_getint(section, option):
            if section == "settings" and option == "noreason_level":
                return 2
            else:
                return self.p.config.getint(section, option)
        self.p.config.getint = Mock(side_effect=my_getint)

    def permban(self, data=''):
        return self.p.cmd_permban(data=data, client=self.mock_client, cmd=self.mock_command)

    def test_no_parameter(self):
        self.permban()
        self.mock_client.message.assert_called_once_with('^7Invalid parameters')
        assert not self.mock_client.ban.called

    def test_no_reason(self):
        self.p.config.getint = Mock(return_value=4)
        self.mock_client.maxLevel = 3
        assert self.mock_client.maxLevel < self.p.config.getint('whatever')
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
        self.p.getMessage = Mock()

        original_getint = self.p.config.getint
        def my_getint(section, option):
            if section == "settings" and option == "noreason_level":
                return 2
            elif section == "settings" and option == "long_tempban_level":
                return 2
            else:
                return original_getint(section, option)
        self.p.config.getint = my_getint

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
        self.mock_client.maxLevel = 3
        assert self.mock_client.maxLevel < self.p.config.getint('whatever')
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



if __name__ == '__main__':
    unittest.main()