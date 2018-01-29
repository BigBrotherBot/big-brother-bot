# -*- coding: utf-8 -*-

# ################################################################### #
#                                                                     #
#  BigBrotherBot(B3) (www.bigbrotherbot.net)                          #
#  Copyright (C) 2005 Michael "ThorN" Thornton                        #
#                                                                     #
#  This program is free software; you can redistribute it and/or      #
#  modify it under the terms of the GNU General Public License        #
#  as published by the Free Software Foundation; either version 2     #
#  of the License, or (at your option) any later version.             #
#                                                                     #
#  This program is distributed in the hope that it will be useful,    #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of     #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the       #
#  GNU General Public License for more details.                       #
#                                                                     #
#  You should have received a copy of the GNU General Public License  #
#  along with this program; if not, write to the Free Software        #
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA      #
#  02110-1301, USA.                                                   #
#                                                                     #
# ################################################################### #

import thread
import time
import sys

from b3 import TEAM_RED
from mockito import when, any as whatever
from mock import Mock, patch, call, ANY
from b3.fake import FakeClient
from b3.config import CfgConfigParser
from b3.plugins.admin import Command
from b3.clients import Client, Group, ClientVar, ClientBan, ClientTempBan
from tests import InstantTimer
from tests.plugins.admin import Admin_TestCase
from tests.plugins.admin import Admin_functional_test

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
        mock_client.message.assert_called_once_with('^7You must supply a map to change to')
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
        mock_client.message.assert_called_once_with('^7ERROR: could not get map list')

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

        self.p.getMessage = Mock(wraps=self.p.getMessage)


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
        self.assertTrue(self.p.warning.called)
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
        self.mock_client.message.assert_called_once_with('^7You are already a ^2superadmin')


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
        self.mock_client.message.assert_called_once_with('^7You are now a ^2%s' % mock_superadmin_group.name)


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
        self.mock_client.message.assert_called_once_with('^7%s ^7is a masked higher level player, action cancelled' % foo_player.exactName)
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
        self.mock_client.message.assert_called_once_with('^7%s ^7is a masked higher level player, action cancelled' % foo_player.exactName)
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
        self.mock_client.message.assert_called_once_with('^7%s ^7is a masked higher level player, action cancelled' % foo_player.exactName)
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
        self.mock_client.message.assert_called_once_with('^7%s ^7is a masked higher level player, action cancelled' % foo_player.exactName)
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
        self.init(r"""[spamages]
foo: foo
rule1: this is rule #1
rule2: this is rule #2
bar: bar
""")
        self.console.say = Mock(wraps=lambda *args: sys.stdout.write("\t\tSAY: " + str(args) + "\n"))
        self.p._sendRules(None)
        self.console.say.assert_has_calls([call('this is rule #1'), call('this is rule #2')])

    def test_no_rule_1(self, sleep_mock):
        self.init(r"""[spamages]
rule5: this is rule #5
rule2: this is rule #2
""")
        self.console.say = Mock(wraps=lambda *args: sys.stdout.write("\t\tSAY: " + str(args) + "\n"))
        self.p._sendRules(None)
        self.assertFalse(self.console.say.called)


    def test_gap_in_rules(self, sleep_mock):
        self.init(r"""[spamages]
rule1: this is rule #1
rule2: this is rule #2
rule4: this is rule #4
""")
        self.console.say = Mock(wraps=lambda *args: sys.stdout.write("\t\tSAY: " + str(args) + "\n"))
        self.p._sendRules(None)
        self.console.say.assert_has_calls([call('this is rule #1'), call('this is rule #2')])


    def test_no_rule_in_config(self, sleep_mock):
        self.init(r"""[spamages]
foo: foo
bar: bar
""")
        self.console.say = Mock(wraps=lambda *args: sys.stdout.write("\t\tSAY: " + str(args) + "\n"))
        self.p._sendRules(None)
        self.assertFalse(self.console.say.called)


    def test_too_many_rules(self, sleep_mock):
        self.init("""[spamages]\n""" + "\n".join(["""rule%s: this is rule #%s""" % (x, x) for x in range(1, 23)]))
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

class Test_cmd_baninfo(Admin_functional_test):

    def test_no_parameter(self):
        # GIVEN
        self.init()
        self.joe.connects(0)
        # WHEN
        self.joe.says('!baninfo')
        # THEN
        self.assertListEqual(['Invalid parameters'], self.joe.message_history)

    def test_no_ban(self):
        # GIVEN
        self.init()
        self.joe.connects(0)
        self.mike.connects(1)
        # WHEN
        self.joe.says('!baninfo mike')
        # THEN
        self.assertListEqual(['Mike has no active bans'], self.joe.message_history)

    def test_perm_ban(self):
        # GIVEN
        self.init()
        self.joe.connects(0)
        self.mike.connects(1)
        self.joe.says('!permban mike f00')
        # WHEN
        self.joe.says('!baninfo @%s' % self.mike.id)
        # THEN
        self.assertListEqual(['Mike has 1 active bans'], self.joe.message_history)

    def test_temp_ban(self):
        # GIVEN
        self.init()
        self.joe.connects(0)
        self.mike.connects(1)
        self.joe.says('!ban mike f00')
        # WHEN
        self.joe.says('!baninfo @%s' % self.mike.id)
        # THEN
        self.assertListEqual(['Mike has 1 active bans'], self.joe.message_history)

    def test_multiple_bans(self):
        # GIVEN
        self.init()
        self.joe.connects(0)
        self.mike.connects(1)
        self.joe.says('!ban @%s f00' % self.mike.id)
        self.joe.says('!permban @%s f00' % self.mike.id)
        # WHEN
        self.joe.says('!baninfo @%s' % self.mike.id)
        # THEN
        self.assertListEqual(['Mike has 2 active bans'], self.joe.message_history)

    def test_no_ban_custom_message(self):
        # WHEN
        self.init("""
[commands]
baninfo: mod
[messages]
baninfo_no_bans: %(name)s is not banned
""")
        self.joe.connects(0)
        self.mike.connects(1)
        self.joe.says('!baninfo mike')
        # THEN
        self.assertListEqual(['Mike is not banned'], self.joe.message_history)

    def test_perm_ban_custom_message(self):
        # GIVEN
        self.init("""
[commands]
permban: fulladmin
baninfo: mod
[messages]
baninfo: %(name)s is banned
""")
        self.joe.connects(0)
        self.mike.connects(1)
        self.joe.says('!permban mike f00')
        # WHEN
        self.joe.says('!baninfo @%s' % self.mike.id)
        # THEN
        self.assertListEqual(['Mike is banned'], self.joe.message_history)


class Test_cmd_putgroup(Admin_functional_test):

    def setUp(self):
        Admin_functional_test.setUp(self)
        # GIVEN
        self.init("""
[commands]
putgroup: admin
[messages]
group_unknown: Unkonwn group: %(group_name)s
group_beyond_reach: You can't assign players to group %(group_name)s
""")
        self.joe.connects(0)
        self.mike.connects(1)
        self.assertEqual('user', self.mike.maxGroup.keyword)

    def test_nominal(self):
        # WHEN
        self.joe.clearMessageHistory()
        self.joe.says('!putgroup mike fulladmin')
        # THEN
        self.assertListEqual(['Mike put in group Full Admin'], self.joe.message_history)
        self.assertEqual('fulladmin', self.mike.maxGroup.keyword)

    def test_non_existing_group(self):
        # WHEN
        self.joe.clearMessageHistory()
        self.joe.says('!putgroup mike f00')
        # THEN
        self.assertListEqual(['Unkonwn group: f00'], self.joe.message_history)
        self.assertEqual('user', self.mike.maxGroup.keyword)

    def test_non_existing_player(self):
        # WHEN
        self.joe.clearMessageHistory()
        self.joe.says('!putgroup f00 admin')
        # THEN
        self.assertListEqual(['No players found matching f00'], self.joe.message_history)
        self.assertEqual('user', self.mike.maxGroup.keyword)

    def test_no_parameter(self):
        # WHEN
        self.joe.clearMessageHistory()
        self.joe.says('!putgroup')
        # THEN
        self.assertListEqual(['Invalid parameters'], self.joe.message_history)
        self.assertEqual('user', self.mike.maxGroup.keyword)

    def test_one_parameter(self):
        # WHEN
        self.joe.clearMessageHistory()
        self.joe.says('!putgroup mike')
        # THEN
        self.assertListEqual(['Invalid parameters'], self.joe.message_history)
        self.assertEqual('user', self.mike.maxGroup.keyword)

    def test_too_many_parameters(self):
        # WHEN
        self.joe.clearMessageHistory()
        self.joe.says('!putgroup mike fulladmin 5')
        # THEN
        self.assertListEqual(['Invalid parameters'], self.joe.message_history)
        self.assertEqual('user', self.mike.maxGroup.keyword)

    def test_already_in_group(self):
        # WHEN
        self.joe.clearMessageHistory()
        self.joe.says('!putgroup mike user')
        # THEN
        self.assertListEqual(['Mike is already in group User'], self.joe.message_history)
        self.assertEqual('user', self.mike.maxGroup.keyword)

    def test_group_beyond_reach(self):
        # GIVEN
        jack = FakeClient(self.console, name="Jack", guid="jackguid", groupBits=40, team=TEAM_RED)
        jack.connects(3)
        self.assertEqual('fulladmin', jack.maxGroup.keyword)
        # WHEN
        jack.clearMessageHistory()
        jack.says('!putgroup mike fulladmin')
        # THEN
        self.assertEqual('user', self.mike.maxGroup.keyword)
        self.assertListEqual(["You can't assign players to group Full Admin"], jack.message_history)
        # WHEN
        jack.clearMessageHistory()
        jack.says('!putgroup mike admin')
        # THEN
        self.assertEqual('admin', self.mike.maxGroup.keyword)
        self.assertListEqual(['Mike put in group Admin'], jack.message_history)


class Test_cmd_tempban(Admin_functional_test):

    def setUp(self):
        Admin_functional_test.setUp(self)
        self.init()
        self.joe.message = Mock()
        self.joe.connects(0)

    def test_no_duration(self):
        self.mike.connects(1)
        self.joe.says('!tempban mike')
        self.joe.message.assert_called_with('^7Invalid parameters')

    def test_bad_duration(self):
        self.mike.connects(1)
        self.mike.tempban = Mock()
        self.joe.says('!tempban mike 5hour')
        self.joe.message.assert_called_with('^7Invalid parameters')
        assert not self.mike.tempban.called

    def test_non_existing_player(self):
        self.mike.connects(1)
        self.joe.says('!tempban foo 5h')
        self.joe.message.assert_called_with('^7No players found matching foo')

    def test_no_reason(self):
        self.mike.connects(1)
        self.mike.tempban = Mock()
        self.joe.says('!tempban mike 5h')
        self.mike.tempban.assert_called_with('', None, 5*60, self.joe)


class Test_cmd_lastbans(Admin_functional_test):

    def setUp(self):
        Admin_functional_test.setUp(self)
        self.init()
        self.joe.message = Mock()
        self.joe.connects(0)

    def test_no_ban(self):
        self.joe.says('!lastbans')
        self.joe.message.assert_called_with('^7There are no active bans')

    @patch('time.time', return_value=0)
    def test_one_tempban(self, mock_time):
        # GIVEN
        self.mike.connects(1)
        # WHEN
        self.joe.says('!tempban mike 5h test reason')
        self.joe.says('!lastbans')
        # THEN
        self.joe.message.assert_called_with(u'^2@2^7 Mike^7^7 (5 hours remaining) test reason')
        # WHEN
        self.joe.says('!unban @2')
        self.joe.says('!lastbans')
        # THEN
        self.joe.message.assert_called_with('^7There are no active bans')


class Test_cmd_help(Admin_functional_test):

    def setUp(self):
        Admin_functional_test.setUp(self)
        self.p._commands = {}  # make sure to empty the commands list as _commands is a wrongly a class property
        self.init()
        self.joe.message = Mock()
        self.joe.connects(0)

    def test_non_existing_cmd(self):
        self.joe.says('!help fo0')
        self.joe.message.assert_called_with('^7Command not found fo0')

    def test_existing_cmd(self):
        self.joe.says('!help help')
        self.joe.message.assert_called_with('^2!help ^7%s' % self.p.cmd_help.__doc__.strip())

    def test_no_arg(self):
        self.joe.says('!help')
        self.joe.message.assert_called_with('^7Available commands: admins, admintest, aliases, b3, ban, banall, baninfo'
                                            ', clear, clientinfo, die, find, help, iamgod, kick, kicka'
                                            'll, lastbans, leveltest, list, longlist, lookup, makereg, map, maprotate, maps, '
                                            'mask, nextmap, notice, pause, permban, poke, putgroup, rebuild, reco'
                                            'nfig, regtest, regulars, rules, runas, say, scream, seen, spam, s'
                                            'pams, spank, spankall, status, tempban, time, unban, ungroup, unmask, unre'
                                            'g, warn, warnclear, warninfo, warnremove, warns, warntest')
        self.mike.message = Mock()
        self.mike.connects(0)
        self.mike.says('!help')
        self.mike.message.assert_called_with('^7Available commands: help, iamgod, nextmap, regtest, regulars, rules, time')

    def test_joker(self):
        self.joe.says('!help *ban')
        self.joe.message.assert_called_with('^7Available commands: ban, banall, baninfo, lastbans, permban, tempban, unban')


class Test_cmd_mask(Admin_functional_test):

    def setUp(self):
        Admin_functional_test.setUp(self)
        self.init()

    def test_nominal(self):
        self.joe.message = Mock(wraps=lambda x: sys.stdout.write("\t\t" + x + "\n"))
        self.joe.connects(0)
        # only superadmin joe is connected
        self.joe.says('!admins')
        self.joe.message.assert_called_with('^7Admins online: Joe^7^7 [^3100^7]')
        # introducing mike (senioradmin)
        self.mike.connects(1)
        self.joe.says('!putgroup mike senioradmin')
        # we know have 2 admins connected
        self.joe.says('!admins')
        self.joe.message.assert_called_with('^7Admins online: Joe^7^7 [^3100^7], Mike^7^7 [^380^7]')
        # joe masks himself as a user
        self.joe.says('!mask user')
        self.joe.says('!admins')
        self.joe.message.assert_called_with('^7Admins online: Mike^7^7 [^380^7]')
        # joe unmasks himself
        self.joe.says('!unmask')
        self.joe.says('!admins')
        self.joe.message.assert_called_with('^7Admins online: Joe^7^7 [^3100^7], Mike^7^7 [^380^7]')
        # joe masks mike as a user
        self.joe.says('!mask user mike')
        self.joe.says('!admins')
        self.joe.message.assert_called_with('^7Admins online: Joe^7^7 [^3100^7]')
        # joe unmasks mike
        self.joe.says('!unmask mike')
        self.joe.says('!admins')
        self.joe.message.assert_called_with('^7Admins online: Joe^7^7 [^3100^7], Mike^7^7 [^380^7]')

    def _test_persistence_for_group(self, group_keyword):
        """
        Makes sure that a user with group 'superadmin', when masked as the given group is still masked with
        that given group once he reconnects. Hence making sure we persists the mask group between connections.
        :param group_keyword: str
        """
        group_to_mask_as = self.console.storage.getGroup(Group(keyword=group_keyword))
        self.assertIsNotNone(group_to_mask_as)
        ## GIVEN that joe masks himself
        self.joe.connects(0)
        self.joe.says('!mask ' + group_keyword)
        self.assertEqual(128, self.joe.maxGroup.id)
        self.assertEqual(100, self.joe.maxGroup.level)
        self.assertIsNotNone(self.joe.maskGroup, "expecting Joe to have a masked group")
        self.assertEqual(group_to_mask_as.id, self.joe.maskGroup.id, "expecting Joe2 to have %s for the mask group id" % group_to_mask_as.id)
        self.assertEqual(group_to_mask_as.level, self.joe.maskGroup.level, "expecting Joe2 to have %s for the mask group level" % group_to_mask_as.level)
        self.assertEqual(group_to_mask_as.id, self.joe.maskedGroup.id, "expecting Joe2 to have %s for the masked group id" % group_to_mask_as.id)
        self.assertEqual(group_to_mask_as.level, self.joe.maskedGroup.level, "expecting Joe2 to have %s for the masked group level" % group_to_mask_as.level)
        ## WHEN joe reconnects
        self.joe.disconnects()
        client = self.console.storage.getClient(Client(id=self.joe.id))
        joe2 = FakeClient(self.console, **client.__dict__)
        joe2.connects(1)
        ## THEN joe is still masked
        self.assertEqual(128, joe2.maxGroup.id)
        self.assertEqual(100, joe2.maxGroup.level)
        self.assertIsNotNone(joe2.maskGroup, "expecting Joe2 to have a masked group")
        self.assertEqual(group_to_mask_as.id, joe2.maskGroup.id, "expecting Joe2 to have %s for the mask group id" % group_to_mask_as.id)
        self.assertEqual(group_to_mask_as.level, joe2.maskGroup.level, "expecting Joe2 to have %s for the mask group level" % group_to_mask_as.level)
        self.assertEqual(group_to_mask_as.id, joe2.maskedGroup.id, "expecting Joe2 to have %s for the masked group id" % group_to_mask_as.id)
        self.assertEqual(group_to_mask_as.level, joe2.maskedGroup.level, "expecting Joe2 to have %s for the masked group level" % group_to_mask_as.level)
        ## THEN the content of the mask_level column in the client table must be correct
        client_data = self.console.storage.getClient(Client(id=joe2.id))
        self.assertIsNotNone(client_data)
        self.assertEqual(group_to_mask_as.level, client_data._maskLevel, "expecting %s to be the value in the mask_level column in database" % group_to_mask_as.level)

    def test_persistence(self):
        self._test_persistence_for_group("user")
        self._test_persistence_for_group("reg")
        self._test_persistence_for_group("mod")
        self._test_persistence_for_group("admin")
        self._test_persistence_for_group("fulladmin")
        self._test_persistence_for_group("senioradmin")
        self._test_persistence_for_group("superadmin")


class Test_cmd_makereg_unreg(Admin_functional_test):
    def setUp(self):
        Admin_functional_test.setUp(self)
        self.init()
        self.group_user = self.console.storage.getGroup(Group(keyword='user'))
        self.group_reg = self.console.storage.getGroup(Group(keyword='reg'))
        self.joe.message = Mock(wraps=lambda x: sys.stdout.write("\t\t" + x + "\n"))
        self.joe.connects(0)
        self.mike.connects(1)

    def test_nominal(self):
        # GIVEN
        self.assertTrue(self.mike.inGroup(self.group_user))
        self.assertFalse(self.mike.inGroup(self.group_reg))
        # WHEN
        self.joe.says("!makereg mike")
        # THEN
        self.assertFalse(self.mike.inGroup(self.group_user))
        self.assertTrue(self.mike.inGroup(self.group_reg))
        self.joe.message.assert_called_with('^7Mike^7 ^7put in group Regular')
        # WHEN
        self.joe.says("!unreg mike")
        # THEN
        self.assertTrue(self.mike.inGroup(self.group_user))
        self.assertFalse(self.mike.inGroup(self.group_reg))
        self.joe.message.assert_called_with('^7Mike^7^7 removed from group Regular')


    def test_unreg_when_not_regular(self):
        # GIVEN
        self.assertTrue(self.mike.inGroup(self.group_user))
        self.assertFalse(self.mike.inGroup(self.group_reg))
        # WHEN
        self.joe.says("!unreg mike")
        # THEN
        self.assertTrue(self.mike.inGroup(self.group_user))
        self.assertFalse(self.mike.inGroup(self.group_reg))
        self.joe.message.assert_called_with('^7Mike^7^7 is not in group Regular')


    def test_makereg_when_already_regular(self):
        # GIVEN
        self.mike.addGroup(self.group_reg)
        self.mike.remGroup(self.group_user)
        self.assertTrue(self.mike.inGroup(self.group_reg))
        # WHEN
        self.joe.says("!makereg mike")
        # THEN
        self.assertFalse(self.mike.inGroup(self.group_user))
        self.assertTrue(self.mike.inGroup(self.group_reg))
        self.joe.message.assert_called_with('^7Mike^7^7 is already in group Regular')


    def test_makereg_no_parameter(self):
        # WHEN
        self.joe.says("!makereg")
        # THEN
        self.joe.message.assert_called_with('^7Invalid parameters')


    def test_unreg_no_parameter(self):
        # WHEN
        self.joe.says("!unreg")
        # THEN
        self.joe.message.assert_called_with('^7Invalid parameters')


    def test_makereg_unknown_player(self):
        # WHEN
        self.joe.says("!makereg foo")
        # THEN
        self.joe.message.assert_called_with('^7No players found matching foo')


    def test_unreg_unknown_player(self):
        # WHEN
        self.joe.says("!unreg foo")
        # THEN
        self.joe.message.assert_called_with('^7No players found matching foo')


def _start_new_thread(callable, args_list, kwargs_dict):
    """ used to patch thread.start_new_thread so it won't create a new thread but call the callable synchronously """
    callable(*args_list, **kwargs_dict)

@patch.object(time, "sleep")
@patch.object(thread, "start_new_thread", wraps=_start_new_thread)
class Test_cmd_rules(Admin_functional_test):
    def setUp(self):
        Admin_functional_test.setUp(self)
        self.init()

    def test_nominal(self, start_new_thread_mock, sleep_mock):
        self.joe.message = Mock(wraps=lambda x: sys.stdout.write("\t\t" + x + "\n"))
        self.joe.connects(0)
        self.joe.says('!rules')
        self.joe.message.assert_has_calls([call('^3Rule #1: No racism of any kind'),
                                           call('^3Rule #2: No clan stacking, members must split evenly between the teams'),
                                           call('^3Rule #3: No arguing with admins (listen and learn or leave)'),
                                           call('^3Rule #4: No abusive language or behavior towards admins or other players'),
                                           call('^3Rule #5: No offensive or potentially offensive names, annoying names, or in-game (double caret (^)) color in names'),
                                           call('^3Rule #6: No recruiting for your clan, your server, or anything else'),
                                           call('^3Rule #7: No advertising or spamming of websites or servers'),
                                           call('^3Rule #8: No profanity or offensive language (in any language)'),
                                           call('^3Rule #9: Do ^1NOT ^3fire at teammates or within 10 seconds of spawning'),
                                           call('^3Rule #10: Offense players must play for the objective and support their team')])

    def test_nominal_loud(self, start_new_thread_mock, sleep_mock):
        self.console.say = Mock(wraps=lambda x: sys.stdout.write("\t\t" + x + "\n"))
        self.joe.connects(0)
        self.joe.says('@rules')
        self.console.say.assert_has_calls([call('^3Rule #1: No racism of any kind'),
                                           call('^3Rule #2: No clan stacking, members must split evenly between the teams'),
                                           call('^3Rule #3: No arguing with admins (listen and learn or leave)'),
                                           call('^3Rule #4: No abusive language or behavior towards admins or other players'),
                                           call('^3Rule #5: No offensive or potentially offensive names, annoying names, or in-game (double caret (^)) color in names'),
                                           call('^3Rule #6: No recruiting for your clan, your server, or anything else'),
                                           call('^3Rule #7: No advertising or spamming of websites or servers'),
                                           call('^3Rule #8: No profanity or offensive language (in any language)'),
                                           call('^3Rule #9: Do ^1NOT ^3fire at teammates or within 10 seconds of spawning'),
                                           call('^3Rule #10: Offense players must play for the objective and support their team')])

    def test_nominal_bigtext(self, start_new_thread_mock, sleep_mock):
        self.console.saybig = Mock(wraps=lambda x: sys.stdout.write("\t\t" + x + "\n"))
        self.joe.connects(0)
        self.joe.says('&rules')
        self.console.saybig.assert_has_calls([call('^3Rule #1: No racism of any kind'),
                                           call('^3Rule #2: No clan stacking, members must split evenly between the teams'),
                                           call('^3Rule #3: No arguing with admins (listen and learn or leave)'),
                                           call('^3Rule #4: No abusive language or behavior towards admins or other players'),
                                           call('^3Rule #5: No offensive or potentially offensive names, annoying names, or in-game (double caret (^)) color in names'),
                                           call('^3Rule #6: No recruiting for your clan, your server, or anything else'),
                                           call('^3Rule #7: No advertising or spamming of websites or servers'),
                                           call('^3Rule #8: No profanity or offensive language (in any language)'),
                                           call('^3Rule #9: Do ^1NOT ^3fire at teammates or within 10 seconds of spawning'),
                                           call('^3Rule #10: Offense players must play for the objective and support their team')])

    def test_nominal_to_player(self, start_new_thread_mock, sleep_mock):
        self.joe.message = Mock(wraps=lambda x: sys.stdout.write("\t\t" + x + "\n"))
        self.joe.connects(0)
        self.mike.message = Mock(wraps=lambda x: sys.stdout.write("\t\t" + x + "\n"))
        self.mike.connects(1)
        self.joe.says('!rules mike')
        self.mike.message.assert_has_calls([call('^3Rule #1: No racism of any kind'),
                                           call('^3Rule #2: No clan stacking, members must split evenly between the teams'),
                                           call('^3Rule #3: No arguing with admins (listen and learn or leave)'),
                                           call('^3Rule #4: No abusive language or behavior towards admins or other players'),
                                           call('^3Rule #5: No offensive or potentially offensive names, annoying names, or in-game (double caret (^)) color in names'),
                                           call('^3Rule #6: No recruiting for your clan, your server, or anything else'),
                                           call('^3Rule #7: No advertising or spamming of websites or servers'),
                                           call('^3Rule #8: No profanity or offensive language (in any language)'),
                                           call('^3Rule #9: Do ^1NOT ^3fire at teammates or within 10 seconds of spawning'),
                                           call('^3Rule #10: Offense players must play for the objective and support their team')])

    def test_unknown_player(self, start_new_thread_mock, sleep_mock):
        self.joe.message = Mock(wraps=lambda x: sys.stdout.write("\t\t" + x + "\n"))
        self.joe.connects(0)
        self.joe.says('!rules fOO')
        self.joe.message.assert_has_calls([call('^7No players found matching fOO')])


class Test_cmd_warns(Admin_functional_test):

    def setUp(self):
        Admin_functional_test.setUp(self)
        self.init()

    def test_nominal(self):
        self.joe.message = Mock(wraps=lambda x: sys.stdout.write("\t\t" + x + "\n"))
        self.joe.connects(0)
        self.joe.says('!warns')
        self.joe.message.assert_called_once_with('^7Warnings: adv, afk, argue, badname, camp, ci, color, cuss, fakecmd,'
        ' jerk, lang, language, name, nocmd, obj, profanity, racism, recruit, rule1, rule10, rule2, rule3, rule4, rule5'
        ', rule6, rule7, rule8, rule9, sfire, spam, spawnfire, spec, spectator, stack, tk')


class Test_cmd_admins(Admin_functional_test):

    def test_no_admin(self):
        # GIVEN
        self.init("""
[commands]
admins: user
""")
        self.mike.connects(0)
        # only user Mike is connected
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says('!admins')
        # THEN
        self.assertListEqual(['There are no admins online'], self.mike.message_history)

    def test_no_admin_custom_message(self):
        # GIVEN
        self.init("""
[commands]
admins: user
[messages]
no_admins: no admins
""")
        self.mike.connects(0)
        # only user Mike is connected
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says('!admins')
        # THEN
        self.assertListEqual(['no admins'], self.mike.message_history)

    def test_no_admin_blank_message(self):
        # GIVEN
        self.init("""
[commands]
admins: user
[messages]
no_admins:
""")
        self.mike.connects(0)
        # only user Mike is connected
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says('!admins')
        # THEN
        self.assertListEqual([], self.mike.message_history)

    def test_one_admin(self):
        # GIVEN
        self.init()
        self.joe.connects(0)
        # only superadmin joe is connected
        # WHEN
        self.joe.clearMessageHistory()
        self.joe.says('!admins')
        # THEN
        self.assertListEqual(['Admins online: Joe [100]'], self.joe.message_history)

    def test_one_admin_custom_message(self):
        # GIVEN
        self.init("""
[commands]
admins: mod
[messages]
admins: online admins: %s
""")
        self.joe.connects(0)
        # WHEN
        self.joe.clearMessageHistory()
        self.joe.says('!admins')
        # THEN
        self.assertListEqual(['online admins: Joe [100]'], self.joe.message_history)

    def test_two_admins(self):
        # GIVEN
        self.init()
        self.joe.connects(0)
        self.mike.connects(1)
        self.joe.says('!putgroup mike senioradmin')
        # WHEN
        self.joe.clearMessageHistory()
        self.joe.says('!admins')
        # THEN
        self.assertListEqual(['Admins online: Joe [100], Mike [80]'], self.joe.message_history)


class Test_cmd_regulars(Admin_functional_test):
    def setUp(self):
        Admin_functional_test.setUp(self)
        self.init()
        self.joe.message = Mock(wraps=lambda x: sys.stdout.write("\t\t" + x + "\n"))
        self.joe.connects(0)

    def test_no_regular(self):
        # only superadmin joe is connected
        self.joe.says('!regulars')
        self.joe.message.assert_called_with('^7There are no regular players online')

    def test_one_regular(self):
        # GIVEN
        self.mike.connects(1)
        self.joe.says('!makereg mike')
        # WHEN
        self.joe.says('!regs')
        # THEN
        self.joe.message.assert_called_with('^7Regular players online: Mike^7')

    def test_two_regulars(self):
        # GIVEN
        self.mike.connects(1)
        self.joe.says('!makereg mike')
        self.jack = FakeClient(self.console, name="Jack", guid="jackguid", groupBits=1)
        self.jack.connects(2)
        self.joe.says('!makereg jack')
        # WHEN
        self.joe.says('!regs')
        # THEN
        self.joe.message.assert_called_with('^7Regular players online: Mike^7, Jack^7')


class Test_cmd_map(Admin_functional_test):
    
    def setUp(self):
        Admin_functional_test.setUp(self)
        self.init()

    def test_missing_param(self):
        self.joe.message = Mock(wraps=lambda x: sys.stdout.write("\t\t" + x + "\n"))
        self.joe.connects(0)
        self.joe.says('!map')
        self.joe.message.assert_called_once_with('^7You must supply a map to change to')

    def test_suggestions(self):
        self.joe.message = Mock(wraps=lambda x: sys.stdout.write("\t\t" + x + "\n"))
        self.joe.connects(0)
        when(self.console).changeMap('f00').thenReturn(["bar1", "bar2", "bar3", "bar4", "bar5", "bar6", "bar7", "bar8", "bar9", "bar10", "bar11", "bar"])
        self.joe.says('!map f00')
        self.joe.message.assert_called_once_with('do you mean: bar1, bar2, bar3, bar4, bar5?')

    def test_nominal(self):
        self.joe.message = Mock(wraps=lambda x: sys.stdout.write("\t\t" + x + "\n"))
        self.joe.connects(0)
        when(self.console).changeMap('f00').thenReturn(None)
        self.joe.says('!map f00')
        self.assertEqual(0, self.joe.message.call_count)
        
        
class Test_cmd_register(Admin_functional_test):
    def setUp(self):
        Admin_functional_test.setUp(self)
        self.p._commands = {}  # make sure to empty the commands list as _commands is a wrongly a class property
        self.say_patcher = patch.object(self.console, "say")
        self.say_mock = self.say_patcher.start()
        self.player = FakeClient(self.console, name="TestPlayer", guid="player_guid", groupBits=0)
        self.player.connects("0")

    def tearDown(self):
        Admin_functional_test.tearDown(self)
        self.say_patcher.stop()

    def test_nominal_with_defaults(self):
        # GIVEN
        self.init(r"""
[commands]
register: guest
[messages]
regme_annouce: %s put in group %s
""")
        # WHEN
        self.player.says('!register')
        # THEN
        self.assertListEqual(['Thanks for your registration. You are now a member of the group User'],
                             self.player.message_history)
        self.assertListEqual([call('TestPlayer^7 put in group User')], self.say_mock.mock_calls)

    def test_custom_messages(self):
        # GIVEN
        self.init(r"""
[commands]
register: guest
[settings]
announce_registration: yes
[messages]
regme_confirmation: You are now a member of the group %s
regme_annouce: %s is now a member of group %s
""")
        # WHEN
        self.player.says('!register')
        # THEN
        self.assertListEqual(['You are now a member of the group User'], self.player.message_history)
        self.assertListEqual([call('TestPlayer^7 is now a member of group User')], self.say_mock.mock_calls)

    def test_no_announce(self):
        # GIVEN
        self.init(r"""
[commands]
register: guest
[settings]
announce_registration: no
[messages]
regme_confirmation: You are now a member of the group %s
regme_annouce: %s is now a member of group %s
""")
        # WHEN
        self.player.says('!register')
        # THEN
        self.assertListEqual(['You are now a member of the group User'], self.player.message_history)
        self.assertListEqual([], self.say_mock.mock_calls)


@patch("time.sleep")
class Test_cmd_spams(Admin_functional_test):

    def test_nominal(self, sleep_mock):
        # GIVEN
        self.init(r"""
[commands]
spams: 20
[spamages]
foo: foo
rule1: this is rule #1
rule2: this is rule #2
bar: bar
""")
        self.joe.connects(0)
        # WHEN
        self.joe.says('!spams')
        # THEN
        self.assertListEqual(['Spamages: bar, foo, rule1, rule2'], self.joe.message_history)

    def test_no_spamage(self, sleep_mock):
        # GIVEN
        self.init(r"""
[commands]
spams: 20
[spamages]
""")
        self.joe.connects(0)
        # WHEN
        self.joe.says('!spams')
        # THEN
        self.assertListEqual(['No spamage message defined'], self.joe.message_history)

    def test_reconfig_loads_new_spamages(self, sleep_mock):
        # GIVEN
        first_config = r"""
[commands]
spams: 20
[spamages]
foo: foo
rule1: this is rule #1
"""
        second_config = r"""
[commands]
spams: 20
[spamages]
bar: bar
rule2: this is rule #2
"""
        self.init(first_config)
        self.joe.connects(0)
        self.joe.says('!spams')
        self.assertListEqual(['Spamages: foo, rule1'], self.joe.message_history)
        # WHEN the config file content is changed
        self.p.config = CfgConfigParser()
        self.p.config.loadFromString(second_config)
        # THEN
        self.joe.clearMessageHistory()
        self.joe.says('!spams')
        self.assertListEqual(['Spamages: bar, rule2'], self.joe.message_history)


@patch("time.sleep")
class Test_cmd_warn_and_clear(Admin_functional_test):

    def setUp(self):
        Admin_functional_test.setUp(self)
        # GIVEN
        self.init(r"""
[commands]
warn: user
clear: user
[messages]
warn_too_fast: Only one warning every %(num_second)s seconds can be given
warn_self: %s, you cannot give yourself a warning
warn_denied: %s, %s is a higher level admin, you can't warn him
cleared_warnings: %(admin)s has cleared %(player)s of all warnings
cleared_warnings_for_all: %(admin)s has cleared everyone's warnings and tk points
[warn]
tempban_num: 3
duration_divider: 30
max_duration: 1d
alert: ^1ALERT^7: $name^7 auto-kick from warnings if not cleared [^3$warnings^7] $reason
alert_kick_num: 3
reason: ^7too many warnings: $reason
message: ^1WARNING^7 [^3$warnings^7]: $reason
""")
        self.joe.connects(0)
        self.mike.connects(1)
        self.say_patcher = patch.object(self.console, "say")
        self.say_mock = self.say_patcher.start()
        self.mike_warn_patcher = patch.object(self.mike, "warn", wraps=self.mike.warn)
        self.mike_warn_mock = self.mike_warn_patcher.start()

    def tearDown(self):
        Admin_functional_test.tearDown(self)
        self.say_patcher.stop()
        self.mike_warn_patcher.stop()

    def test_warn(self, sleep_mock):
        # GIVEN
        self.joe.says('!warn mike')
        # THEN
        self.assertEqual(1, self.mike.numWarnings)
        self.assertListEqual([call(60.0, '^7behave yourself', None, self.joe, '')], self.mike_warn_mock.mock_calls)
        self.assertListEqual([call('^1WARNING^7 [^31^7]: Mike^7^7, ^7behave yourself')], self.say_mock.mock_calls)
        self.assertListEqual([], self.joe.message_history)
        self.assertListEqual([], self.mike.message_history)

    @patch('threading.Timer', new_callable=lambda: InstantTimer)
    def test_warn_then_auto_kick(self, instant_timer, sleep_mock):
        # GIVEN
        self.p.warn_delay = 0
        self.assertEqual(0, self.mike.numWarnings)
        # WHEN
        with patch.object(self.mike, 'tempban') as mike_tempban_mock:
            self.joe.says('!warn mike')
            self.joe.says('!warn mike')
            self.joe.says('!warn mike')
        # THEN Mike has 3 active warnings
        self.assertEqual(3, self.mike.numWarnings)
        # THEN appropriate messages were sent
        self.assertListEqual([
            call('^1WARNING^7 [^31^7]: Mike^7^7, ^7behave yourself'),
            call('^1WARNING^7 [^32^7]: Mike^7^7, ^7behave yourself'),
            call('^1WARNING^7 [^33^7]: Mike^7^7, ^7behave yourself'),
            call(u'^1ALERT^7: Mike^7^7 auto-kick from warnings if not cleared [^33^7] ^7behave yourself'),
        ], self.say_mock.mock_calls)
        # THEN Mike was kicked for having too many warnings
        self.assertListEqual([
            call(u'^7too many warnings: ^7behave yourself', u'None', 6, self.joe, False, '')
        ], mike_tempban_mock.mock_calls)
        # THEN No private message was sent
        self.assertListEqual([], self.joe.message_history)
        self.assertListEqual([], self.mike.message_history)


    @patch('threading.Timer', new_callable=lambda: InstantTimer)
    def test_warn_then_auto_kick_duration_divider_60(self, instant_timer, sleep_mock):
        # GIVEN
        self.p.config._sections['warn']['duration_divider'] = '60'
        self.p.warn_delay = 0
        self.assertEqual(0, self.mike.numWarnings)
        # WHEN
        with patch.object(self.mike, 'tempban') as mike_tempban_mock:
            self.joe.says('!warn mike')
            self.joe.says('!warn mike')
            self.joe.says('!warn mike')
        # THEN Mike has 3 active warnings
        self.assertEqual(3, self.mike.numWarnings)
        # THEN appropriate messages were sent
        self.assertListEqual([
            call('^1WARNING^7 [^31^7]: Mike^7^7, ^7behave yourself'),
            call('^1WARNING^7 [^32^7]: Mike^7^7, ^7behave yourself'),
            call('^1WARNING^7 [^33^7]: Mike^7^7, ^7behave yourself'),
            call(u'^1ALERT^7: Mike^7^7 auto-kick from warnings if not cleared [^33^7] ^7behave yourself'),
        ], self.say_mock.mock_calls)
        # THEN Mike was kicked for having too many warnings
        self.assertListEqual([
            call(u'^7too many warnings: ^7behave yourself', u'None', 3, self.joe, False, '')
        ], mike_tempban_mock.mock_calls)
        # THEN No private message was sent
        self.assertListEqual([], self.joe.message_history)
        self.assertListEqual([], self.mike.message_history)

    def test_warn_self(self, sleep_mock):
        # GIVEN
        self.joe.says('!warn joe')
        # THEN
        self.assertEqual(0, self.joe.numWarnings)
        self.assertListEqual(['Joe, you cannot give yourself a warning'], self.joe.message_history)

    def test_warn_denied(self, sleep_mock):
        # GIVEN
        self.mike.says('!warn joe')
        # THEN
        self.assertEqual(0, self.joe.numWarnings)
        self.assertListEqual(["Mike, Joe is a higher level admin, you can't warn him"], self.mike.message_history)

    def test_clear_player(self, sleep_mock):
        # GIVEN
        self.joe.says('!warn mike')
        self.assertEqual(1, self.mike.numWarnings)
        # WHEN
        self.joe.says('!clear mike')
        # THEN
        self.assertListEqual([call('^1WARNING^7 [^31^7]: Mike^7^7, ^7behave yourself'),
                              call('Joe^7 has cleared Mike^7 of all warnings')], self.say_mock.mock_calls)
        self.assertEqual(0, self.mike.numWarnings)

    def test_clear__all_players(self, sleep_mock):
        # GIVEN
        self.joe.says('!warn mike')
        self.assertEqual(1, self.mike.numWarnings)
        # WHEN
        self.joe.says('!clear')
        # THEN
        self.assertListEqual([call('^1WARNING^7 [^31^7]: Mike^7^7, ^7behave yourself'),
                              call("Joe^7 has cleared everyone's warnings and tk points")], self.say_mock.mock_calls)
        self.assertEqual(0, self.mike.numWarnings)


@patch("time.sleep")
class Test_warn_command_abusers(Admin_functional_test):

    def setUp(self):
        Admin_functional_test.setUp(self)
        self.player = FakeClient(self.console, name="ThePlayer", guid="theplayerguid", groupBits=0)
        self.player_warn_patcher = patch.object(self.player, "warn")
        self.player_warn_mock = self.player_warn_patcher.start()

    def tearDown(self):
        Admin_functional_test.tearDown(self)
        self.player_warn_patcher.stop()

    def test_conf_empty(self, sleep_mock):
        # WHEN
        self.init(r"""
[commands]
[warn]
""")
        # THEN
        self.assertFalse(self.p._warn_command_abusers)
        self.assertIsNone(self.p.getWarning("fakecmd"))
        self.assertIsNone(self.p.getWarning("nocmd"))

    def test_warn_reasons(self, sleep_mock):
        # WHEN
        self.init(r"""
[warn_reasons]
fakecmd: 1h, ^7do not use fake commands
nocmd: 1h, ^7do not use commands that you do not have access to, try using !help
""")
        # THEN
        self.assertTupleEqual((60.0, '^7do not use commands that you do not have access to, try using !help'),
                              self.p.getWarning("nocmd"))
        self.assertTupleEqual((60.0, '^7do not use fake commands'), self.p.getWarning("fakecmd"))

    def test_warn_no__no_sufficient_access(self, sleep_mock):
        # WHEN
        self.init(r"""
[commands]
help: 2
[warn]
warn_command_abusers: no
""")
        self.assertFalse(self.p._warn_command_abusers)
        self.player.connects("0")
        # WHEN
        with patch.object(self.p, "info") as info_mock:
            self.player.says("!help")
        # THEN
        self.assertListEqual([call('ThePlayer does not have sufficient rights to use !help. Required level: 2')], info_mock.mock_calls)
        # message section not loaded so this will fallback on the default warn message
        self.assertListEqual(['You do not have sufficient access to use !help'], self.player.message_history)
        self.assertFalse(self.player_warn_mock.called)

    def test_warn_yes__no_sufficient_access(self, sleep_mock):
        # GIVEN
        self.init(r"""
[commands]
help: 2
[warn]
warn_command_abusers: yes
""")
        self.assertTrue(self.p._warn_command_abusers)
        self.player.connects("0")
        # WHEN
        with patch.object(self.p, "info") as info_mock:
            self.player.says("!help")
        # THEN
        self.assertListEqual([call('ThePlayer does not have sufficient rights to use !help. Required level: 2')], info_mock.mock_calls)
        # message section not loaded so this will fallback on the default warn message
        self.assertListEqual(['You do not have sufficient access to use !help'], self.player.message_history)
        self.assertFalse(self.player_warn_mock.called)

    def test_warn_yes__no_sufficient_access_abuser(self, sleep_mock):
        # GIVEN
        self.init(r"""
[commands]
help: 2
[warn]
warn_command_abusers: yes
[warn_reasons]
nocmd: 90s, do not use commands you do not have access to, try using !help
""")
        self.player.connects("0")
        # WHEN
        with patch.object(self.p, "info") as info_mock:
            self.player.says("!help")
            self.player.says("!help")
            self.player.says("!help")
        # THEN
        self.assertListEqual([call('ThePlayer does not have sufficient rights to use !help. Required level: 2'),
                              call('ThePlayer does not have sufficient rights to use !help. Required level: 2')], info_mock.mock_calls)
        # message section not loaded so this will fallback on the default warn message
        self.assertListEqual(['You do not have sufficient access to use !help',
                              'You do not have sufficient access to use !help'], self.player.message_history)
        self.assertListEqual([call(1.5, 'do not use commands you do not have access to, try using !help',
                                   'nocmd', ANY, ANY)], self.player_warn_mock.mock_calls)


    def test_warn_no__unknown_cmd(self, sleep_mock):
        # GIVEN
        self.init(r"""
[commands]
help: 0
[warn]
warn_command_abusers: no
""")
        self.assertFalse(self.p._warn_command_abusers)
        self.player.connects("0")
        # WHEN
        self.player.says("!hzlp")
        # THEN
        self.assertListEqual(['Unrecognized command hzlp. Did you mean !help?'], self.player.message_history)
        self.assertFalse(self.player_warn_mock.called)

    def test_warn_yes__unknown_cmd(self, sleep_mock):
        # GIVEN
        self.init(r"""
[commands]
help: 0
[warn]
warn_command_abusers: yes
""")
        self.assertTrue(self.p._warn_command_abusers)
        self.player.connects("0")
        # WHEN
        self.player.says("!hzlp")
        # THEN
        self.assertListEqual(['Unrecognized command hzlp. Did you mean !help?'], self.player.message_history)
        self.assertFalse(self.player_warn_mock.called)

    def test_warn_yes__unknown_cmd_abuser(self, sleep_mock):
        # GIVEN
        self.init(r"""
[commands]
help: 0
[warn]
warn_command_abusers: yes
[warn_reasons]
fakecmd: 2h, do not use fake commands
""")
        self.assertTrue(self.p._warn_command_abusers)
        self.player.connects("0")
        self.player.setvar(self.p, 'fakeCommand', 2)  # simulate already 2 use of the !help command
        # WHEN
        self.player.says("!hzlp")
        self.player.says("!hzlp")
        self.player.says("!hzlp")
        # THEN
        self.assertListEqual(['Unrecognized command hzlp. Did you mean !help?',
                              'Unrecognized command hzlp. Did you mean !help?',
                              'Unrecognized command hzlp. Did you mean !help?'], self.player.message_history)
        self.assertListEqual([call(120.0, 'do not use fake commands', 'fakecmd', ANY, ANY)],
                             self.player_warn_mock.mock_calls)


@patch("time.sleep")
class Test_command_parsing(Admin_functional_test):

    def setUp(self):
        Admin_functional_test.setUp(self)
        self.init(r"""
[commands]
help: 0
""")
        self.joe.connects("0")

    def test_normal_chat(self, sleep_mock):
        # GIVEN
        self.joe.says("f00")
        self.assertListEqual([], self.joe.message_history)
        # WHEN
        self.joe.says("!help")
        # THEN
        self.assertListEqual(["Available commands: help, iamgod"], self.joe.message_history)

    def test_team_chat(self, sleep_mock):
        # GIVEN
        self.joe.says("f00")
        self.assertListEqual([], self.joe.message_history)
        # WHEN
        self.joe.says2team("!help")
        # THEN
        self.assertListEqual(["Available commands: help, iamgod"], self.joe.message_history)

    def test_squad_chat(self, sleep_mock):
        # GIVEN
        self.joe.says("f00")
        self.assertListEqual([], self.joe.message_history)
        # WHEN
        self.joe.says2squad("!help")
        # THEN
        self.assertListEqual(["Available commands: help, iamgod"], self.joe.message_history)

    def test_private_chat(self, sleep_mock):
        # GIVEN
        self.joe.says("f00")
        self.assertListEqual([], self.joe.message_history)
        # WHEN
        self.joe.says2private("!help")
        # THEN
        self.assertListEqual(["Available commands: help, iamgod"], self.joe.message_history)



class Test_cmd_kick_functional(Admin_functional_test):

    def setUp(self):
        Admin_functional_test.setUp(self)
        self.init()
        # superadmin joe is connected on slot '0'
        self.joe.connects('0')
        self.kick_patcher = patch.object(self.console, 'kick')
        self.kick_mock = self.kick_patcher.start()

    def tearDown(self):
        Admin_functional_test.tearDown(self)
        self.kick_patcher.stop()

    def test_no_parameter(self):
        # WHEN
        self.joe.says('!kick')
        # THEN
        self.assertListEqual(['Invalid parameters'], self.joe.message_history)
        self.assertListEqual([], self.kick_mock.mock_calls)

    def test_self_kick(self):
        # WHEN
        with patch.object(self.console, "say") as say_mock:
            self.joe.says('!kick joe')
        # THEN
        self.assertListEqual([], self.kick_mock.mock_calls)
        self.assertListEqual([call("^7Joe^7 ^7Can't kick yourself newb!")], say_mock.mock_calls)

    def test_no_reason_when_required(self):
        # GIVEN
        self.joe._groupBits = 16
        # WHEN
        self.joe.says('!kick f00')
        # THEN
        self.assertListEqual(['ERROR: You must supply a reason'], self.joe.message_history)
        self.assertListEqual([], self.kick_mock.mock_calls)

    def test_kick_higher_level_admin(self):
        # GIVEN
        self.mike._groupBits = 16
        self.mike.connects("1")
        # WHEN
        with patch.object(self.console, "say") as say_mock:
            self.mike.says('!kick joe reason1')
        # THEN
        self.assertListEqual([call("^7Joe^7^7 gets 1 point, Mike^7^7 gets none, Joe^7^7 wins, can't kick")], say_mock.mock_calls)
        self.assertListEqual([], self.kick_mock.mock_calls)

    def test_kick_masked_higher_level_admin(self):
        # GIVEN
        self.mike._groupBits = 16
        self.mike.connects("1")
        self.joe.says("!mask reg")
        # WHEN
        self.mike.says('!kick joe reason1')
        # THEN
        self.assertListEqual(["Joe is a masked higher level player, action cancelled"], self.mike.message_history)
        self.assertListEqual([], self.kick_mock.mock_calls)

    def test_existing_player_name(self):
        # GIVEN
        self.mike.connects('1')
        # WHEN
        self.joe.says('!kick mike the reason')
        # THEN
        self.assertListEqual([call(self.mike, 'the reason', self.joe, False)], self.kick_mock.mock_calls)
        self.assertEqual(1, self.console.storage.numPenalties(self.mike, 'Kick'))

    def test_unknown_player_name(self):
        # GIVEN
        self.mike.connects('6')
        # WHEN
        self.joe.says('!kick f00')
        # THEN
        self.assertListEqual(['No players found matching f00'], self.joe.message_history)
        self.assertListEqual([], self.kick_mock.mock_calls)

    def test_kick_by_slot_id(self):
        # GIVEN
        self.mike.connects('6')
        # WHEN
        self.joe.says('!kick 6')
        # THEN
        self.assertListEqual([call(self.mike, '', self.joe, False)], self.kick_mock.mock_calls)
        self.assertEqual(1, self.console.storage.numPenalties(self.mike, 'Kick'))

    def test_kick_by_slot_id_when_no_known_player_is_on_that_slot(self):
        # GIVEN
        self.mike.connects('6')
        # WHEN
        self.joe.says('!kick 4')
        # THEN
        self.assertListEqual([call('4', '', self.joe)], self.kick_mock.mock_calls)

    def test_kick_by_database_id(self):
        # GIVEN
        self.mike.connects('6')
        mike_from_db = self.console.storage.getClient(Client(guid=self.mike.guid))
        self.assertIsNotNone(mike_from_db)
        # WHEN
        self.joe.says('!kick @%s' % mike_from_db.id)
        # THEN
        self.assertListEqual([call(ANY, '', self.joe, False)], self.kick_mock.mock_calls)
        kick_call = self.kick_mock.mock_calls[0]
        kicked_player = kick_call[1][0]
        self.assertIsNotNone(kicked_player)
        self.assertIsNotNone(kicked_player.cid)

    def test_existing_player_by_name_containing_spaces(self):
        # GIVEN
        self.mike.connects('1')
        self.mike.name = "F 0 0"
        # WHEN
        self.joe.says('!kick f00 the reason')
        # THEN
        self.assertListEqual([call(self.mike, 'the reason', self.joe, False)], self.kick_mock.mock_calls)

    def test_existing_player_by_name_containing_spaces_2(self):
        # GIVEN
        self.mike.connects('1')
        self.mike.name = "F 0 0"
        # WHEN
        self.joe.says("!kick 'f 0 0' the reason")
        # THEN
        self.assertListEqual([call(self.mike, 'the reason', self.joe, False)], self.kick_mock.mock_calls)


class Test_cmd_spam(Admin_functional_test):

    def setUp(self):
        Admin_functional_test.setUp(self)
        self.init()
        self.joe.connects(0)
        self.mike.connects(1)

    def test_no_parameter(self):
        with patch.object(self.console, "say") as say_mock:
            self.joe.says('!spam')
        self.assertListEqual([], say_mock.mock_calls)
        self.assertListEqual(['Invalid parameters'], self.joe.message_history)

    def test_unknown_spammage_keyword(self):
        with patch.object(self.console, "say") as say_mock:
            self.joe.says('!spam f00')
        self.assertListEqual([], say_mock.mock_calls)
        self.assertListEqual(['Could not find spam message f00'], self.joe.message_history)

    def test_nominal_to_all_players(self):
        with patch.object(self.console, "say") as say_mock:
            self.joe.says('!spam rule1')
        self.assertListEqual([call('^3Rule #1: No racism of any kind')], say_mock.mock_calls)
        self.assertListEqual([], self.joe.message_history)

    def test_nominal_to_mike(self):
        with patch.object(self.console, "say") as say_mock:
            self.joe.says('!spam mike rule1')
        self.assertListEqual([], say_mock.mock_calls)
        self.assertListEqual([], self.joe.message_history)
        self.assertListEqual(['Rule #1: No racism of any kind'], self.mike.message_history)

    def test_nominal_to_unknown_player(self):
        with patch.object(self.console, "say") as say_mock:
            self.joe.says('!spam f00 rule1')
        self.assertListEqual([], say_mock.mock_calls)
        self.assertListEqual(["No players found matching f00"], self.joe.message_history)
        self.assertListEqual([], self.mike.message_history)

    def test_nominal_to_all_players_big(self):
        with patch.object(self.console, "saybig") as saybig_mock:
            self.joe.says('&spam rule1')
        self.assertListEqual([call('^3Rule #1: No racism of any kind')], saybig_mock.mock_calls)
        self.assertListEqual([], self.joe.message_history)

