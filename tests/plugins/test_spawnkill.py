#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2015 Daniele Pantaleone <fenix@bigbrotherbot.net>
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
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
#

import time
import os
import unittest2 as unittest

from textwrap import dedent
from mockito import when
from b3.plugins.admin import AdminPlugin
from b3.plugins.spawnkill import SpawnkillPlugin
from b3.config import CfgConfigParser
from b3.config import XmlConfigParser
from b3.cvar import Cvar
from b3.parsers.iourt42 import Iourt42Parser
from b3 import __file__ as b3_module__file__
from b3 import TEAM_BLUE, TEAM_RED
from tests import logging_disabled

ADMIN_CONFIG_FILE = os.path.normpath(os.path.join(os.path.dirname(b3_module__file__), "conf/plugin_admin.ini"))

@unittest.skipUnless(os.path.exists(ADMIN_CONFIG_FILE), reason="cannot get default plugin config file at %s" % ADMIN_CONFIG_FILE)
class SpawnkillTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with logging_disabled():
            from b3.parsers.q3a.abstractParser import AbstractParser
            from b3.fake import FakeConsole
            AbstractParser.__bases__ = (FakeConsole,)
            # Now parser inheritance hierarchy is :
            # Iourt42Parser -> abstractParser -> FakeConsole -> Parser

    def setUp(self):
        # create a Iourt42 parser
        self.parser_conf = XmlConfigParser()
        self.parser_conf.loadFromString(dedent(r"""
            <configuration>
                <settings name="server">
                    <set name="game_log"></set>
                </settings>
            </configuration>
        """))

        self.console = Iourt42Parser(self.parser_conf)

        # initialize some fixed cvars which will be used by both the plugin and the iourt42 parser
        when(self.console).getCvar('auth').thenReturn(Cvar('auth', value='0'))
        when(self.console).getCvar('fs_basepath').thenReturn(Cvar('g_maxGameClients', value='/fake/basepath'))
        when(self.console).getCvar('fs_homepath').thenReturn(Cvar('sv_maxclients', value='/fake/homepath'))
        when(self.console).getCvar('fs_game').thenReturn(Cvar('fs_game', value='q3ut4'))
        when(self.console).getCvar('gamename').thenReturn(Cvar('gamename', value='q3urt42'))

        # start the parser
        self.console.startup()

        self.admin_plugin_conf = CfgConfigParser()
        self.admin_plugin_conf.loadFromString(dedent(r"""
            [warn]
            pm_global: yes
            alert_kick_num: 3
            instant_kick_num: 5
            tempban_num: 6
            tempban_duration: 1d
            max_duration: 1d
            message: ^1WARNING^7 [^3$warnings^7]: $reason
            warn_delay: 15
            reason: ^7too many warnings: $reason
            duration_divider: 30
            alert: ^1ALERT^7: $name^7 auto-kick from warnings if not cleared [^3$warnings^7] $reason
            warn_command_abusers: no"""))

        with logging_disabled():
            self.adminPlugin = AdminPlugin(self.console, self.admin_plugin_conf)
            self.adminPlugin.onLoadConfig()
            self.adminPlugin.onStartup()

        # make sure the admin plugin obtained by other plugins is our admin plugin
        when(self.console).getPlugin('admin').thenReturn(self.adminPlugin)

    def tearDown(self):
        self.console.working = False


class Test_events(SpawnkillTestCase):

    def setUp(self):

        SpawnkillTestCase.setUp(self)

        with logging_disabled():
            from b3.fake import FakeClient

        # create some clients
        self.mike = FakeClient(console=self.console, name="Mike", guid="mikeguid", team=TEAM_RED,  groupBits=1)
        self.bill = FakeClient(console=self.console, name="Bill", guid="billguid", team=TEAM_BLUE, groupBits=1)
        self.mark = FakeClient(console=self.console, name="Mark", guid="markguid", team=TEAM_BLUE, groupBits=128)

        self.conf = CfgConfigParser()
        self.p = SpawnkillPlugin(self.console, self.conf)

    def init(self, config_content=None):
        if config_content:
            self.conf.loadFromString(config_content)
        else:
            self.conf.loadFromString(dedent(r"""
                [hit]
                maxlevel: admin
                delay: 2
                penalty: warn
                duration: 3m
                reason: do not shoot to spawning players!

                [kill]
                maxlevel: admin
                delay: 3
                penalty: warn
                duration: 5m
                reason: spawnkilling is not allowed on this server!
            """))

        self.p.onLoadConfig()
        self.p.onStartup()

    def tearDown(self):
        self.mike.disconnects()
        self.bill.disconnects()
        self.mark.disconnects()
        SpawnkillTestCase.tearDown(self)

    ####################################################################################################################
    #                                                                                                                  #
    #   MIXED TESTS                                                                                                    #
    #                                                                                                                  #
    ####################################################################################################################

    def test_client_spawntime_mark(self):
        # GIVEN
        self.init()
        self.mike.connects("1")
        self.bill.connects("2")
        # WHEN
        self.console.parseLine('''ClientSpawn: 1''')
        self.console.parseLine('''ClientSpawn: 2''')
        # THEN
        self.assertEqual(True, self.mike.isvar(self.p, 'spawntime'))
        self.assertEqual(True, self.bill.isvar(self.p, 'spawntime'))

    ####################################################################################################################
    #                                                                                                                  #
    #   TEST SPAWN HIT                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def test_client_spawn_hit_admin_level_bypass(self):
        # GIVEN
        self.init(dedent(r"""
            [hit]
            maxlevel: admin
            delay: 10
            penalty: warn
            duration: 3m
            reason: do not shoot to spawning players!
        """))
        self.mark.connects("1")
        self.bill.connects("2")
        self.mark.setvar(self.p, 'spawntime', time.time() - 5)
        self.bill.setvar(self.p, 'spawntime', time.time() - 5)
        # WHEN
        self.mark.damages(self.bill)
        # THEN
        self.assertEqual(0, self.console.storage.numPenalties(self.mark, 'Warning'))

    def test_client_spawn_hit_no_spawntime_marked(self):
        # GIVEN
        self.init(dedent(r"""
            [hit]
            maxlevel: admin
            delay: 10
            penalty: warn
            duration: 3m
            reason: do not shoot to spawning players!
        """))
        self.mike.connects("1")
        self.bill.connects("2")
        # WHEN
        self.mike.damages(self.bill)
        # THEN
        self.assertEqual(0, self.console.storage.numPenalties(self.mike, 'Warning'))

    def test_client_spawn_hit_warn(self):
        # GIVEN
        self.init(dedent(r"""
            [hit]
            maxlevel: admin
            delay: 10
            penalty: warn
            duration: 3m
            reason: do not shoot to spawning players!
        """))
        self.mike.connects("1")
        self.bill.connects("2")
        self.mike.setvar(self.p, 'spawntime', time.time() - 5)
        self.bill.setvar(self.p, 'spawntime', time.time() - 5)
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.damages(self.bill)
        # THEN
        self.assertEqual(1, self.console.storage.numPenalties(self.mike, 'Warning'))
        self.assertListEqual(['WARNING [1]: Mike,  do not shoot to spawning players!'], self.mike.message_history)

    def test_client_spawn_hit_kick(self):
        # GIVEN
        self.init(dedent(r"""
            [hit]
            maxlevel: admin
            delay: 10
            penalty: kick
            duration: 3m
            reason: do not shoot to spawning players!
        """))
        self.mike.connects("1")
        self.bill.connects("2")
        self.mike.setvar(self.p, 'spawntime', time.time() - 5)
        self.bill.setvar(self.p, 'spawntime', time.time() - 5)
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.damages(self.bill)
        # THEN
        self.assertEqual(1, self.console.storage.numPenalties(self.mike, 'Kick'))

    def test_client_spawn_hit_tempban(self):
        # GIVEN
        self.init(dedent(r"""
            [hit]
            maxlevel: admin
            delay: 10
            penalty: tempban
            duration: 3m
            reason: do not shoot to spawning players!
        """))
        self.mike.connects("1")
        self.bill.connects("2")
        self.mike.setvar(self.p, 'spawntime', time.time() - 5)
        self.bill.setvar(self.p, 'spawntime', time.time() - 5)
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.damages(self.bill)
        # THEN
        self.assertEqual(1, self.console.storage.numPenalties(self.mike, 'TempBan'))

    def test_client_spawn_hit_slap(self):
        # TODO: implement test case
        pass

    def test_client_spawn_hit_nuke(self):
        # TODO: implement test case
        pass

    def test_client_spawn_hit_kill(self):
        # TODO: implement test case
        pass

    ####################################################################################################################
    #                                                                                                                  #
    #   TEST SPAWN KILL                                                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    def test_client_spawn_kill_admin_level_bypass(self):
        # GIVEN
        self.init(dedent(r"""
            [hit]
            maxlevel: admin
            delay: 10
            penalty: warn
            duration: 3m
            reason: do not shoot to spawning players!
        """))
        self.mark.connects("1")
        self.bill.connects("2")
        self.mark.setvar(self.p, 'spawntime', time.time() - 5)
        self.bill.setvar(self.p, 'spawntime', time.time() - 5)
        # WHEN
        self.mark.kills(self.bill)
        # THEN
        self.assertEqual(0, self.console.storage.numPenalties(self.mark, 'Warning'))

    def test_client_spawn_kill_no_spawntime_marked(self):
        # GIVEN
        self.init(dedent(r"""
            [hit]
            maxlevel: admin
            delay: 10
            penalty: warn
            duration: 3m
            reason: do not shoot to spawning players!
        """))
        self.mike.connects("1")
        self.bill.connects("2")
        # WHEN
        self.mike.kills(self.bill)
        # THEN
        self.assertEqual(0, self.console.storage.numPenalties(self.mike, 'Warning'))

    def test_client_spawn_kill_warn(self):
        # GIVEN
        self.init(dedent(r"""
            [kill]
            maxlevel: admin
            delay: 10
            penalty: warn
            duration: 5m
            reason: spawnkilling is not allowed on this server!
        """))
        self.mike.connects("1")
        self.bill.connects("2")
        self.mike.setvar(self.p, 'spawntime', time.time() - 5)
        self.bill.setvar(self.p, 'spawntime', time.time() - 5)
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.kills(self.bill)
        # THEN
        self.assertEqual(1, self.console.storage.numPenalties(self.mike, 'Warning'))
        self.assertListEqual(['WARNING [1]: Mike,  spawnkilling is not allowed on this server!'], self.mike.message_history)

    def test_client_spawn_kill_kick(self):
        # GIVEN
        self.init(dedent(r"""
            [kill]
            maxlevel: admin
            delay: 10
            penalty: kick
            duration: 5m
            reason: spawnkilling is not allowed on this server!
        """))
        self.mike.connects("1")
        self.bill.connects("2")
        self.mike.setvar(self.p, 'spawntime', time.time() - 5)
        self.bill.setvar(self.p, 'spawntime', time.time() - 5)
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.kills(self.bill)
        # THEN
        self.assertEqual(1, self.console.storage.numPenalties(self.mike, 'Kick'))

    def test_client_spawn_kill_tempban(self):
        # GIVEN
        self.init(dedent(r"""
            [kill]
            maxlevel: admin
            delay: 10
            penalty: tempban
            duration: 5m
            reason: spawnkilling is not allowed on this server!
        """))
        self.mike.connects("1")
        self.bill.connects("2")
        self.mike.setvar(self.p, 'spawntime', time.time() - 5)
        self.bill.setvar(self.p, 'spawntime', time.time() - 5)
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.kills(self.bill)
        # THEN
        self.assertEqual(1, self.console.storage.numPenalties(self.mike, 'TempBan'))

    def test_client_spawn_kill_slap(self):
        # TODO: implement test case
        pass

    def test_client_spawn_kill_nuke(self):
        # TODO: implement test case
        pass

    def test_client_spawn_kill_kill(self):
        # TODO: implement test case
        pass