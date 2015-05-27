#
# FirstKill Plugin for BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2015 Daniele Pantaleone <fenix@bigbrotherbot.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA

import unittest2

from textwrap import dedent
from mock import Mock
from mockito import when
from b3 import TEAM_RED, TEAM_BLUE
from b3.cvar import Cvar
from b3.config import MainConfig
from b3.config import XmlConfigParser
from b3.config import CfgConfigParser
from b3.parsers.iourt42 import Iourt42Parser
from b3.plugins.admin import AdminPlugin
from b3.plugins.firstkill import FirstkillPlugin
from tests import logging_disabled


class FirstKillCase(unittest2.TestCase):

    @classmethod
    def setUpClass(cls):
        with logging_disabled():
            from b3.parsers.q3a.abstractParser import AbstractParser
            from b3.fake import FakeConsole
            AbstractParser.__bases__ = (FakeConsole,)
            # Now parser inheritance hierarchy is :
            # Iourt41Parser -> abstractParser -> FakeConsole -> Parser

    def setUp(self):
        # create a Iourt42 parser
        parser_conf = XmlConfigParser()
        parser_conf.loadFromString(dedent(r"""
            <configuration>
                <settings name="server">
                    <set name="game_log"></set>
                </settings>
            </configuration>
        """))

        self.parser_conf = MainConfig(parser_conf)
        self.console = Iourt42Parser(self.parser_conf)

        # initialize some fixed cvars which will be used by both the plugin and the iourt42 parser
        when(self.console).getCvar('auth').thenReturn(Cvar('auth', value='0'))
        when(self.console).getCvar('fs_basepath').thenReturn(Cvar('fs_basepath', value='/fake/basepath'))
        when(self.console).getCvar('fs_homepath').thenReturn(Cvar('fs_homepath', value='/fake/homepath'))
        when(self.console).getCvar('fs_game').thenReturn(Cvar('fs_game', value='q3ut4'))
        when(self.console).getCvar('gamename').thenReturn(Cvar('gamename', value='q3urt42'))

        # start the parser
        self.console.startup()

        with logging_disabled():
            self.adminPlugin = AdminPlugin(self.console, '@b3/conf/plugin_admin.ini')
            self.adminPlugin.onLoadConfig()
            self.adminPlugin.onStartup()

        # make sure the admin plugin obtained by other plugins is our admin plugin
        when(self.console).getPlugin('admin').thenReturn(self.adminPlugin)

        self.conf = CfgConfigParser()
        self.conf.loadFromString(dedent(r"""
            [settings]
            firstkill: on
            firsttk: on
            firsths: on

            [commands]
            firstkill: superadmin
            firsttk: superadmin
            firsths: superadmin

            [messages]
            ## $client = the client who made the kill
            ## $target = the client who suffered the kill
            first_kill: ^2First Kill^3: $client killed $target
            first_kill_by_headshot: ^2First Kill ^5by Headshot^3: $client killed $target
            first_teamkill: ^1First TeamKill^3: $client teamkilled $target
        """))

        self.p = FirstkillPlugin(self.console, self.conf)
        self.p.onLoadConfig()
        self.p.onStartup()

    def tearDown(self):
        self.console.working = False


class Test_events(FirstKillCase):

    def setUp(self):
        FirstKillCase.setUp(self)
        with logging_disabled():
            from b3.fake import FakeClient

        # create some clients
        self.mike = FakeClient(console=self.console, name="Mike", guid="mikeguid", team=TEAM_BLUE, groupBits=1)
        self.mark = FakeClient(console=self.console, name="Mark", guid="markguid", team=TEAM_BLUE, groupBits=1)
        self.bill = FakeClient(console=self.console, name="Bill", guid="billguid", team=TEAM_RED, groupBits=1)
        self.mike.connects("1")
        self.bill.connects("2")
        self.mark.connects("3")

    def tearDown(self):
        self.mike.disconnects()
        self.bill.disconnects()
        self.mark.disconnects()
        FirstKillCase.tearDown(self)

    ####################################################################################################################
    #                                                                                                                  #
    #   FIRSTKILL                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def test_first_kill(self):
        # GIVEN
        self.p._firsths = False
        self.p._firstkill = True
        self.p._kill = 0
        # WHEN
        self.p.announce_first_kill = Mock()
        self.p.announce_first_kill_by_headshot = Mock()
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_KILL', client=self.mike, target=self.bill, data=(100, self.console.UT_MOD_DEAGLE, self.console.HL_HEAD)))
        # THEN
        self.p.announce_first_kill.assert_called_with(self.mike, self.bill)
        self.assertFalse(self.p.announce_first_kill_by_headshot.called)

    def test_first_kill_already_broadcasted(self):
        # GIVEN
        self.p._firsths = False
        self.p._firstkill = True
        self.p._kill = 1
        # WHEN
        self.p.announce_first_kill = Mock()
        self.p.announce_first_kill_by_headshot = Mock()
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_KILL', client=self.mike, target=self.bill, data=(100, self.console.UT_MOD_DEAGLE, self.console.HL_HEAD)))
        # THEN
        self.assertFalse(self.p.announce_first_kill.called)
        self.assertFalse(self.p.announce_first_kill_by_headshot.called)

    def test_first_kill_disabled(self):
        # GIVEN
        self.p._firsths = False
        self.p._firstkill = False
        self.p._kill = 0
        # WHEN
        self.p.announce_first_kill = Mock()
        self.p.announce_first_kill_by_headshot = Mock()
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_KILL', client=self.mike, target=self.bill, data=(100, self.console.UT_MOD_DEAGLE, self.console.HL_HEAD)))
        # THEN
        self.assertFalse(self.p.announce_first_kill.called)
        self.assertFalse(self.p.announce_first_kill_by_headshot.called)

    ####################################################################################################################
    #                                                                                                                  #
    #   FIRSTKILL BY HEADSHOT                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    def test_first_kill_by_headshot(self):
        # GIVEN
        self.p._firsths = True
        self.p._firstkill = True
        self.p._kill = 0
        # WHEN
        self.p.announce_first_kill = Mock()
        self.p.announce_first_kill_by_headshot = Mock()
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_KILL', client=self.mike, target=self.bill, data=(100, self.console.UT_MOD_DEAGLE, self.console.HL_HEAD)))
        # THEN
        self.p.announce_first_kill_by_headshot.assert_called_with(self.mike, self.bill)
        self.assertFalse(self.p.announce_first_kill.called)

    def test_first_kill_by_headshot_already_broadcasted(self):
        # GIVEN
        self.p._firsths = True
        self.p._firstkill = True
        self.p._kill = 1
        # WHEN
        self.p.announce_first_kill = Mock()
        self.p.announce_first_kill_by_headshot = Mock()
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_KILL', client=self.mike, target=self.bill, data=(100, self.console.UT_MOD_DEAGLE, self.console.HL_HEAD)))
        # THEN
        self.assertFalse(self.p.announce_first_kill.called)
        self.assertFalse(self.p.announce_first_kill_by_headshot.called)

    def test_first_kill_by_headshot_disabled(self):
        # GIVEN
        self.p._firsths = True
        self.p._firstkill = False
        self.p._kill = 0
        # WHEN
        self.p.announce_first_kill = Mock()
        self.p.announce_first_kill_by_headshot = Mock()
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_KILL', client=self.mike, target=self.bill, data=(100, self.console.UT_MOD_DEAGLE, self.console.HL_HEAD)))
        # THEN
        self.assertFalse(self.p.announce_first_kill.called)
        self.assertFalse(self.p.announce_first_kill_by_headshot.called)

    ####################################################################################################################
    #                                                                                                                  #
    #   FIRST TEAMKILL                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def test_first_teamkill(self):
        # GIVEN
        self.p._firsttk = True
        self.p._tk = 0
        # WHEN
        self.p.announce_first_teamkill = Mock()
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_KILL_TEAM', client=self.mike, target=self.mark, data=(100, self.console.UT_MOD_DEAGLE, self.console.HL_HEAD)))
        # THEN
        self.p.announce_first_teamkill.assert_called_with(self.mike, self.mark)

    def test_first_teamkill_already_broadcasted(self):
        # GIVEN
        self.p._firsttk = True
        self.p._tk = 1
        # WHEN
        self.p.announce_first_teamkill = Mock()
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_KILL_TEAM', client=self.mike, target=self.mark, data=(100, self.console.UT_MOD_DEAGLE, self.console.HL_HEAD)))
        # THEN
        self.assertFalse(self.p.announce_first_teamkill.called)

    def test_first_teamkill_disabled(self):
        # GIVEN
        self.p._firsttk = False
        self.p._tk = 0
        # WHEN
        self.p.announce_first_teamkill = Mock()
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_KILL_TEAM', client=self.mike, target=self.mark, data=(100, self.console.UT_MOD_DEAGLE, self.console.HL_HEAD)))
        # THEN
        self.assertFalse(self.p.announce_first_teamkill.called)