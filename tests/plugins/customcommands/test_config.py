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
import b3
import os
from mock import patch, call
from b3.plugins.admin import Command
from b3.config import CfgConfigParser
from b3.plugins.customcommands import CustomcommandsPlugin
from tests import logging_disabled
from tests.plugins.customcommands import CustomcommandsTestCase

with logging_disabled():
    from b3.fake import FakeClient


class ConfTestCase(CustomcommandsTestCase):

    def setUp(self):
        CustomcommandsTestCase.setUp(self)
        self.conf = CfgConfigParser()
        self.p = CustomcommandsPlugin(self.console, self.conf)
        self.player1 = FakeClient(console=self.console, name="Player1", guid="player1GUID", pbid="player1PBID")
        self.player2 = FakeClient(console=self.console, name="Player2", guid="player2GUID", pbid="player2PBID")
        self.player1.connects(cid="slot1")
        self.player2.connects(cid="slot2")
        self.write_patcher = patch.object(self.console, "write", wrap=self.console.write)
        self.write_mock = self.write_patcher.start()

    def tearDown(self):
        CustomcommandsTestCase.tearDown(self)
        self.write_mock = self.write_patcher.stop()


class Test_default_conf(ConfTestCase):

    def setUp(self):
        ConfTestCase.setUp(self)
        self.conf.load(b3.getAbsolutePath('@b3/conf/plugin_customcommands.ini'))
        self.p.onLoadConfig()
        self.p.onStartup()

    def test_cmd_are_registered(self):
        self.assertIn("cookie", self.p._adminPlugin._commands)
        self.assertIn("sry", self.p._adminPlugin._commands)
        self.assertIn("ns", self.p._adminPlugin._commands)

    def test_help_cookie(self):
        # WHEN
        self.player1.says("!help cookie")
        # THEN
        self.assertListEqual(['!cookie <player> - give a cookie to a player'], self.player1.message_history)

    def test_cmd_cookie(self):
        # WHEN
        self.player1.says("!cookie")
        # THEN
        self.assertListEqual(['Error: missing parameter'], self.player1.message_history)

    def test_cmd_cookie_unknown_player(self):
        # WHEN
        self.player1.says("!cookie f00")
        # THEN
        self.assertListEqual(['No players found matching f00'], self.player1.message_history)

    def test_cmd_cookie_nominal(self):
        # WHEN
        self.player1.says("!cookie Player2")
        # THEN
        self.assertListEqual([call('tell slot2 ^1Player1 ^7 gave you a ^2COOKIE^7')], self.write_mock.mock_calls)
        self.assertListEqual([], self.player1.message_history)

    def test_help_sry(self):
        # WHEN
        self.player1.says("!help sry")
        # THEN
        self.assertListEqual(['!sry - say you are sorry to your last victim'], self.player1.message_history)

    def test_cmd_sry_no_victim(self):
        # WHEN
        self.player1.says("!sry")
        # THEN
        self.assertListEqual(['Error: your last victim is unknown'], self.player1.message_history)
        self.assertListEqual([], self.write_mock.mock_calls)

    def test_cmd_sry_nominal(self):
        # GIVEN
        self.player1.kills(self.player2)
        # WHEN
        self.player1.says("!sry")
        # THEN
        self.assertListEqual([call('tell slot2 sorry mate :|')], self.write_mock.mock_calls)
        self.assertListEqual([], self.player1.message_history)

    def test_help_ns(self):
        # WHEN
        self.player1.says("!help ns")
        # THEN
        self.assertListEqual(["!ns - say 'Nice shot' to your killer"], self.player1.message_history)

    def test_cmd_n1_no_killer(self):
        # WHEN
        self.player1.says("!ns")
        # THEN
        self.assertListEqual(['Error: your last killer is unknown'], self.player1.message_history)
        self.assertListEqual([], self.write_mock.mock_calls)

    def test_cmd_n1_nominal(self):
        # GIVEN
        self.player2.kills(self.player1)
        # WHEN
        self.player1.says("!ns")
        # THEN
        self.assertListEqual([call('tell slot2 nice shot !')], self.write_mock.mock_calls)
        self.assertListEqual([], self.player1.message_history)


class Test_load_conf(ConfTestCase):

    def test_invalid_command_name(self):
        # GIVEN
        self.conf.loadFromString("""
[guest commands]
# define in this section commands that will be available to all players
!cookie = tell <ARG:FIND_PLAYER:PID> ^1<PLAYER:NAME> ^7 gave you a ^2COOKIE^7
        """)
        # WHEN
        with patch.object(self.p, "error") as error_mock:
            self.p.onLoadConfig()
        # THEN
        self.assertListEqual([call("command name '!cookie' is invalid: command names must start by a letter, must be at"
                                   " least two characters long and have no space in them")], error_mock.mock_calls)

    def test_command_already_registered(self):
        # GIVEN
        self.console.getPlugin('admin')._commands["cookie"] = Command(self.p._adminPlugin, "cookie", 0, lambda x: None)
        self.conf.loadFromString("""
[guest commands]
# define in this section commands that will be available to all players
cookie = tell <ARG:FIND_PLAYER:PID> ^1<PLAYER:NAME> ^7 gave you a ^2COOKIE^7
        """)
        # WHEN
        with patch.object(self.p, "error") as error_mock:
            self.p.onLoadConfig()
        # THEN
        self.assertListEqual([call("a command with name 'cookie' is already registered by plugin No")],
                             error_mock.mock_calls)