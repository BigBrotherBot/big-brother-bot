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

import logging
import os
from textwrap import dedent

from mock import Mock
from mock import patch
from mockito import when
from mockito import mock

from b3 import __file__ as b3_module__file__
from b3 import TEAM_RED
from b3 import TEAM_BLUE
from b3.config import CfgConfigParser
from b3.plugins.xlrstats import XlrstatsPlugin
from b3.fake import FakeClient
from b3.plugins.admin import AdminPlugin
from tests import B3TestCase
from tests import logging_disabled


DEFAULT_XLRSTATS_CONFIG_FILE = os.path.normpath(os.path.join(os.path.dirname(b3_module__file__), "conf", "plugin_xlrstats.ini"))
DEFAULT_ADMIN_CONFIG_FILE = os.path.normpath(os.path.join(os.path.dirname(b3_module__file__), "conf", "plugin_admin.ini"))

# Setup the logging level we'd like to be spammed with during the tests
LOGGER = logging.getLogger('output')
LOGGER.setLevel(logging.DEBUG)


class XlrstatsTestCase(B3TestCase):

    def setUp(self):
        """
        This method is called before each test.
        It is meant to set up the SUT (System Under Test) in a manner that will ease the testing of its features.
        """
        with logging_disabled():
            # The B3TestCase class provides us a working B3 environment that does not require any database connexion.
            # The B3 console is then accessible with self.console
            B3TestCase.setUp(self)

            # set additional B3 console stuff that will be used by the XLRstats plugin
            self.console.gameName = "MyGame"
            self.parser_conf.add_section('b3')
            self.parser_conf.set('b3', 'time_zone', 'GMT')

            # we make our own AdminPlugin and make sure it is the one return in any case
            self.adminPlugin = AdminPlugin(self.console, DEFAULT_ADMIN_CONFIG_FILE)
            when(self.console).getPlugin("admin").thenReturn(self.adminPlugin)
            self.adminPlugin.onLoadConfig()
            self.adminPlugin.onStartup()

            # We need a config for the Xlrstats plugin
            self.conf = CfgConfigParser()  # It is an empty config but we can fill it up later

            # Now we create an instance of the SUT (System Under Test) which is the XlrstatsPlugin
            self.p = XlrstatsPlugin(self.console, self.conf)
            when(self.console).getPlugin("xlrstats").thenReturn(self.p)

            # create a client object to represent the game server
            with patch("b3.clients.Clients.authorizeClients"):  # we patch authorizeClients or it will spawn a thread
                # with a 5 second timer
                self.console.clients.newClient(-1, name="WORLD", guid="WORLD", hide=True)

    def init(self, config_content=None):
        """
        Load the config and starts the xlrstats plugin.
        If no config_content is provided, use the default config file

        :param config_content: optional XLRstats config
        :type config_content: str
        """
        if config_content is None:
            self.conf.load(DEFAULT_XLRSTATS_CONFIG_FILE)
        else:
            self.conf.loadFromString(config_content)
        self.p.onLoadConfig()
        self.p.minlevel = 1  # tests in this module assume unregistered players aren't considered by Xlrstats
        self.p.onStartup()

class Test_get_PlayerAnon(XlrstatsTestCase):

    def setUp(self):
        XlrstatsTestCase.setUp(self)
        self.init()

    def test(self):
        # WHEN
        s = self.p.get_PlayerAnon()
        # THEN
        self.assertIsNotNone(s)
        self.assertEqual(self.p._world_clientid, s.client_id)
        self.assertEqual(0, s.kills)
        self.assertEqual(0, s.deaths)
        self.assertEqual(0, s.teamkills)
        self.assertEqual(0, s.teamdeaths)
        self.assertEqual(0, s.suicides)
        self.assertEqual(0, s.ratio)
        self.assertEqual(1000, s.skill)
        self.assertEqual(0, s.assists)
        self.assertEqual(0, s.assistskill)
        self.assertEqual(0, s.curstreak)
        self.assertEqual(0, s.winstreak)
        self.assertEqual(0, s.losestreak)
        self.assertEqual(0, s.rounds)
        self.assertEqual(0, s.hide)


class Test_get_PlayerStats(XlrstatsTestCase):

    def setUp(self):
        XlrstatsTestCase.setUp(self)
        self.init()
        self.p1 = FakeClient(console=self.console, name="P1", guid="P1_GUID")
        self.p1.connects("1")

    def test_unregistered_player(self):
        # WHEN
        s = self.p.get_PlayerStats(client=self.p1)
        # THEN
        self.assertIsNone(s)

    def test_newly_registered_player(self):
        # GIVEN
        self.p1.says("!register")
        self.assertGreaterEqual(self.p1.maxLevel, self.p.minlevel)
        # WHEN
        s = self.p.get_PlayerStats(client=self.p1)
        # THEN
        self.assertIsNotNone(s)
        self.assertEqual(self.p1.id, s.client_id)
        self.assertEqual(0, s.kills)
        self.assertEqual(0, s.deaths)
        self.assertEqual(0, s.teamkills)
        self.assertEqual(0, s.teamdeaths)
        self.assertEqual(0, s.suicides)
        self.assertEqual(0, s.ratio)
        self.assertEqual(1000, s.skill)
        self.assertEqual(0, s.assists)
        self.assertEqual(0, s.assistskill)
        self.assertEqual(0, s.curstreak)
        self.assertEqual(0, s.winstreak)
        self.assertEqual(0, s.losestreak)
        self.assertEqual(0, s.rounds)
        self.assertEqual(0, s.hide)
        self.assertEqual("", s.fixed_name)
        self.assertEqual("", s.id_token)

    def test_player_having_existing_stats(self):
        # GIVEN
        self.p1.says("!register")
        self.assertGreaterEqual(self.p1.maxLevel, self.p.minlevel)
        s = self.p.get_PlayerStats(client=self.p1)
        s.kills = 4
        self.p.save_Stat(s)
        # WHEN
        s2 = self.p.get_PlayerStats(client=self.p1)
        # THEN
        self.assertIsNotNone(s2)
        self.assertEqual(self.p1.id, s2.client_id)
        self.assertEqual(4, s2.kills)
        self.assertEqual(0, s2.deaths)
        self.assertEqual(0, s2.teamkills)
        self.assertEqual(0, s2.teamdeaths)
        self.assertEqual(0, s2.suicides)
        self.assertEqual(0, s2.ratio)
        self.assertEqual(1000, s2.skill)
        self.assertEqual(0, s2.assists)
        self.assertEqual(0, s2.assistskill)
        self.assertEqual(0, s2.curstreak)
        self.assertEqual(0, s2.winstreak)
        self.assertEqual(0, s2.losestreak)
        self.assertEqual(0, s2.rounds)
        self.assertEqual(0, s2.hide)
        self.assertEqual("", s2.fixed_name)
        self.assertEqual("", s2.id_token)


class Test_cmd_xlrstats(XlrstatsTestCase):

    def setUp(self):
        XlrstatsTestCase.setUp(self)
        self.init()
        self.p1 = FakeClient(console=self.console, name="P1", guid="P1_GUID")
        self.p1.connects("1")
        self.p2 = FakeClient(console=self.console, name="P2", guid="P2_GUID")
        self.p2.connects("2")

    def test_unregistered_player(self):
        # GIVEN
        self.console.getPlugin('admin')._warn_command_abusers = True
        self.p1.clearMessageHistory()
        # WHEN
        self.p1.says("!xlrstats")
        # THEN
        self.assertEqual(['You need to be in group User to use !xlrstats'], self.p1.message_history)

    def test_registered_player(self):
        # GIVEN
        self.console.getPlugin('admin')._warn_command_abusers = True
        self.p1.says("!register")
        self.p1.clearMessageHistory()
        # WHEN
        self.p1.says("!xlrstats")
        # THEN
        self.assertEqual(['XLR Stats: P1 : K 0 D 0 TK 0 Ratio 0.00 Skill 1000.00'], self.p1.message_history)

    def test_for_unknown_player(self):
        # GIVEN
        self.p1.says("!register")
        self.p1.clearMessageHistory()
        # WHEN
        self.p1.says("!xlrstats spiderman")
        # THEN
        self.assertEqual(['No players found matching spiderman'], self.p1.message_history)

    def test_for_other_unregistered_player(self):
        # GIVEN
        self.p1.says("!register")
        self.p1.clearMessageHistory()
        # WHEN
        self.p1.says("!xlrstats P2")
        # THEN
        self.assertEqual(['XLR Stats: could not find stats for P2'], self.p1.message_history)

    def test_for_other_registered_player(self):
        # GIVEN
        self.p1.says("!register")
        self.p2.says("!register")
        self.p1.clearMessageHistory()
        # WHEN
        self.p1.says("!xlrstats P2")
        # THEN
        self.assertEqual(['XLR Stats: P2 : K 0 D 0 TK 0 Ratio 0.00 Skill 1000.00'], self.p1.message_history)


class Test_cmd_xlrid(XlrstatsTestCase):

    def setUp(self):
        XlrstatsTestCase.setUp(self)
        self.init()
        self.p1 = FakeClient(console=self.console, name="P1", guid="P1_GUID", groupBits=1)
        self.p1.connects("1")

    def test_no_parameters(self):
        # WHEN
        self.p1.says("!xlrid")
        # THEN
        self.assertEqual(['Invalid/missing data, try !help xlrid'], self.p1.message_history)

    def test_with_parameters(self):
        # WHEN
        self.p1.says("!xlrid 12345")
        pstats = self.p.get_PlayerStats(self.p1)
        # THEN
        self.assertEqual('12345', pstats.id_token)
        self.assertEqual(['Token saved!'], self.p1.message_history)


class Test_kill(XlrstatsTestCase):
    """
    Validates that the stats get updated as expected upon kill events
    """

    def setUp(self):
        XlrstatsTestCase.setUp(self)
        self.init()
        # GIVEN two players P1 and P2 (P1 being a registered user)
        self.p1 = FakeClient(console=self.console, name="P1", guid="P1_GUID", team=TEAM_BLUE)
        self.p1.connects("1")
        self.p1.says("!register")
        self.p2 = FakeClient(console=self.console, name="P2", guid="P2_GUID", team=TEAM_RED)
        self.p2.connects("2")
        self.p._xlrstats_active = True

    def test_p1_kills_p2(self):
        # GIVEN
        self.p1.kills(self.p2)
        s = self.p.get_PlayerStats(self.p1)
        # WHEN
        self.p1.clearMessageHistory()
        self.p1.says("!xlrstats")
        # THEN
        self.assertEqual(['XLR Stats: P1 : K 1 D 0 TK 0 Ratio 0.00 Skill 1024.00'], self.p1.message_history)

    def test_p1_teamkills_p2(self):
        # GIVEN
        self.p2.team = self.p1.team
        self.p1.kills(self.p2)
        s = self.p.get_PlayerStats(self.p1)
        # WHEN
        self.p1.clearMessageHistory()
        self.p1.says("!xlrstats")
        # THEN
        self.assertEqual(['XLR Stats: P1 : K 0 D 0 TK 1 Ratio 0.00 Skill 999.00'], self.p1.message_history)

    def test_p1_kills_p2_twice(self):
        # GIVEN
        self.p1.kills(self.p2)
        self.p1.kills(self.p2)
        s = self.p.get_PlayerStats(self.p1)
        # WHEN
        self.p1.clearMessageHistory()
        self.p1.says("!xlrstats")
        # THEN
        self.assertEqual(['XLR Stats: P1 : K 2 D 0 TK 0 Ratio 0.00 Skill 1035.45'], self.p1.message_history)

    def test_p1_kills_p2_then_p2_kills_p1(self):
        # GIVEN
        self.p1.kills(self.p2)
        self.p2.kills(self.p1)
        s = self.p.get_PlayerStats(self.p1)
        # WHEN
        self.p1.clearMessageHistory()
        self.p1.says("!xlrstats")
        # THEN
        self.assertEqual(['XLR Stats: P1 : K 1 D 1 TK 0 Ratio 1.00 Skill 1015.63'], self.p1.message_history)


    def test_p1_kills_bot(self):
        # GIVEN
        self.p2.bot = True
        self.p.exclude_bots = True
        self.console.verbose = Mock()
        # WHEN
        self.p1.kills(self.p2)
        # THEN
        self.console.verbose.assert_called_with("XlrstatsPlugin: bot involved: do not process!")


class Test_storage(XlrstatsTestCase):

    def setUp(self):
        XlrstatsTestCase.setUp(self)
        self.init()

    def test_PlayerStats(self):
        # GIVEN
        client = mock()
        client.id = 43
        
        # getting empty stats
        s = self.p.get_PlayerStats(client)
        self.assertIsNotNone(s)
        self.assertEqual(client.id, s.client_id)

        # saving stats
        s.kills = 56
        s.deaths = 64
        s.teamkills = 6
        s.teamdeaths = 4
        s.suicides = 5
        s.ratio = .12
        s.skill = 455
        s.assists = 23
        s.assistskill = 543
        s.curstreak = 4
        s.winstreak = 32
        s.losestreak = 74
        s.rounds = 874
        s.hide = 1
        s.fixed_name = 'the name'
        s.id_token = 'the token'
        self.p.save_Stat(s)

        # checking modified stats
        s2 = self.p.get_PlayerStats(client)
        self.assertIsNotNone(s2)
        self.assertEqual(client.id, s2.client_id)

        self.assertEqual(56, s2.kills)
        self.assertEqual(64, s2.deaths)
        self.assertEqual(6, s2.teamkills)
        self.assertEqual(4, s2.teamdeaths)
        self.assertEqual(5, s2.suicides)
        self.assertEqual(.12, s2.ratio)
        self.assertEqual(455, s2.skill)
        self.assertEqual(23, s2.assists)
        self.assertEqual(543, s2.assistskill)
        self.assertEqual(4, s2.curstreak)
        self.assertEqual(32, s2.winstreak)
        self.assertEqual(74, s2.losestreak)
        self.assertEqual(874, s2.rounds)
        self.assertEqual(1, s2.hide)
        self.assertEqual('the name', s2.fixed_name)
        self.assertEqual('the token', s2.id_token)

    def test_WeaponStats(self):
        # GIVEN
        name = "the weapon"

        # getting empty stats
        s = self.p.get_WeaponStats(name)
        self.assertIsNotNone(s)

        # saving stats
        s.kills = 64
        s.suicides = 6
        s.teamkills = 4
        self.p.save_Stat(s)

        # checking modified stats
        s2 = self.p.get_WeaponStats(name)
        self.assertIsNotNone(s2)

        self.assertEqual(s.name, s2.name)
        self.assertEqual(s.kills, s2.kills)
        self.assertEqual(s.suicides, s2.suicides)
        self.assertEqual(s.teamkills, s2.teamkills)


    def test_Bodypart(self):
        # GIVEN
        name = "the body part"

        # getting empty stats
        s = self.p.get_Bodypart(name)
        self.assertIsNotNone(s)

        # saving stats
        s.kills = 64
        s.suicides = 6
        s.teamkills = 4
        self.p.save_Stat(s)

        # checking modified stats
        s2 = self.p.get_Bodypart(name)
        self.assertIsNotNone(s2)

        self.assertEqual(s.name, s2.name)
        self.assertEqual(s.kills, s2.kills)
        self.assertEqual(s.suicides, s2.suicides)
        self.assertEqual(s.teamkills, s2.teamkills)

    def test_MapStats(self):
        # GIVEN
        name = "the map"

        # getting empty stats
        s = self.p.get_MapStats(name)
        self.assertIsNotNone(s)

        # saving stats
        s.kills = 64
        s.suicides = 6
        s.teamkills = 4
        s.rounds = 84
        self.p.save_Stat(s)

        # checking modified stats
        s2 = self.p.get_MapStats(name)
        self.assertIsNotNone(s2)

        self.assertEqual(s.name, s2.name)
        self.assertEqual(s.kills, s2.kills)
        self.assertEqual(s.suicides, s2.suicides)
        self.assertEqual(s.teamkills, s2.teamkills)
        self.assertEqual(s.rounds, s2.rounds)

    def test_WeaponUsage(self):
        # GIVEN
        weapon_id = 841
        client_id = 84556

        # getting empty stats
        s = self.p.get_WeaponUsage(weapon_id, client_id)
        self.assertIsNotNone(s)

        # saving stats
        s.kills = 10
        s.deaths = 11
        s.suicides = 12
        s.teamkills = 13
        s.teamdeaths = 14
        self.p.save_Stat(s)

        # checking modified stats
        s2 = self.p.get_WeaponUsage(weapon_id, client_id)
        self.assertIsNotNone(s2)

        self.assertEqual(s.kills, s2.kills)
        self.assertEqual(s.deaths, s2.deaths)
        self.assertEqual(s.suicides, s2.suicides)
        self.assertEqual(s.teamkills, s2.teamkills)
        self.assertEqual(s.teamdeaths, s2.teamdeaths)

    def test_Opponent(self):
        # GIVEN
        killerid = 841
        targetid = 84556

        # getting empty stats
        s = self.p.get_Opponent(killerid, targetid)
        self.assertIsNotNone(s)

        # saving stats
        s.kills = 10
        s.retals = 11
        self.p.save_Stat(s)

        # checking modified stats
        s2 = self.p.get_Opponent(killerid, targetid)
        self.assertIsNotNone(s2)

        self.assertEqual(s.kills, s2.kills)
        self.assertEqual(s.retals, s2.retals)

    def test_PlayerBody(self):
        # GIVEN
        playerid = 841
        bodypartid = 84556

        # getting empty stats
        s = self.p.get_PlayerBody(playerid, bodypartid)
        self.assertIsNotNone(s)

        # saving stats
        s.kills = 10
        s.deaths = 11
        s.suicides = 12
        s.teamkills = 13
        s.teamdeaths = 14
        self.p.save_Stat(s)

        # checking modified stats
        s2 = self.p.get_PlayerBody(playerid, bodypartid)
        self.assertIsNotNone(s2)

        self.assertEqual(s.kills, s2.kills)
        self.assertEqual(s.deaths, s2.deaths)
        self.assertEqual(s.suicides, s2.suicides)
        self.assertEqual(s.teamkills, s2.teamkills)
        self.assertEqual(s.teamdeaths, s2.teamdeaths)

    def test_PlayerMaps(self):
        # GIVEN
        playerid = 841
        mapid = 84556

        # getting empty stats
        s = self.p.get_PlayerMaps(playerid, mapid)
        self.assertIsNotNone(s)

        # saving stats
        s.kills = 10
        s.suicides = 12
        s.teamkills = 13
        s.rounds = 14
        self.p.save_Stat(s)

        # checking modified stats
        s2 = self.p.get_PlayerMaps(playerid, mapid)
        self.assertIsNotNone(s2)

        self.assertEqual(s.kills, s2.kills)
        self.assertEqual(s.suicides, s2.suicides)
        self.assertEqual(s.teamkills, s2.teamkills)
        self.assertEqual(s.rounds, s2.rounds)

    def test_PlayerMaps_with_unkown_map(self):
        # GIVEN
        playerid = 841
        mapid = None

        # getting empty stats
        s = self.p.get_PlayerMaps(playerid, mapid)
        self.assertIsNotNone(s)

        # saving stats
        s.kills = 10
        s.suicides = 12
        s.teamkills = 13
        s.rounds = 14
        self.p.save_Stat(s)

        # checking modified stats
        s2 = self.p.get_PlayerMaps(playerid, mapid)
        self.assertIsNotNone(s2)

        self.assertEqual(s.kills, s2.kills)
        self.assertEqual(s.suicides, s2.suicides)
        self.assertEqual(s.teamkills, s2.teamkills)
        self.assertEqual(s.rounds, s2.rounds)

    def test_ActionStats(self):
        # GIVEN
        name = "the action name"

        # getting empty stats
        s = self.p.get_ActionStats(name)
        self.assertIsNotNone(s)

        # saving stats
        s.count = 10
        self.p.save_Stat(s)

        # checking modified stats
        s2 = self.p.get_ActionStats(name)
        self.assertIsNotNone(s2)

        self.assertEqual(s.count, s2.count)

    def test_PlayerActions(self):
        # GIVEN
        playerid = 74564
        actionid = 74

        # getting empty stats
        s = self.p.get_PlayerActions(playerid, actionid)
        self.assertIsNotNone(s)

        # saving stats
        s.count = 10
        self.p.save_Stat(s)

        # checking modified stats
        s2 = self.p.get_PlayerActions(playerid, actionid)
        self.assertIsNotNone(s2)

        self.assertEqual(s.count, s2.count)


class Test_events(XlrstatsTestCase):

    def setUp(self):
        XlrstatsTestCase.setUp(self)
        self.init(dedent("""
            [settings]
            minplayers: 1
            prematch_maxtime: 0
        """))
        self.p1 = FakeClient(console=self.console, name="P1", guid="P1_GUID", groupBits=1)
        self.p1.connects("1")

        map_stats = self.p.get_MapStats("Map1")
        self.p.save_Stat(map_stats)
        self.map1_id = map_stats.id

        map_stats = self.p.get_MapStats("Map1")
        self.p.save_Stat(map_stats)
        self.map2_id = map_stats.id

        player_stats = self.p.get_PlayerStats(client=self.p1)
        self.p.save_Stat(player_stats)
        self.p1stats_id = player_stats.id

        self.console.game.mapName = "Map1"

    def fireEvent(self, event_name, *args, **kwargs):
        self.console.queueEvent(self.console.getEvent(event_name, *args, **kwargs))

    def test_map_rounds_get_saved(self):
        # WHEN the player plays 3 complete rounds
        self.console.game.mapName = "Map1"
        self.fireEvent('EVT_GAME_ROUND_END')
        self.fireEvent('EVT_GAME_ROUND_START')
        self.fireEvent('EVT_GAME_ROUND_END')
        self.fireEvent('EVT_GAME_ROUND_START')
        self.fireEvent('EVT_GAME_ROUND_END')
        self.console.game.mapName = "Map2"
        self.fireEvent('EVT_GAME_ROUND_START')
        self.fireEvent('EVT_GAME_ROUND_END')
        self.console.game.mapName = "Map3"
        self.fireEvent('EVT_GAME_ROUND_START')
        # THEN
        map_stats = self.p.get_MapStats("Map1")
        self.assertEqual(2, map_stats.rounds)
        map_stats = self.p.get_MapStats("Map2")
        self.assertEqual(1, map_stats.rounds)

    def test_playermaps_rounds_get_saved(self):
        # WHEN a player plays 3 complete rounds
        self.fireEvent('EVT_GAME_ROUND_START')
        self.fireEvent("EVT_CLIENT_JOIN", client=self.p1)
        self.fireEvent('EVT_GAME_ROUND_END')
        self.fireEvent('EVT_GAME_ROUND_START')
        self.fireEvent("EVT_CLIENT_JOIN", client=self.p1)
        # THEN
        playermap_stats = self.p.get_PlayerMaps(self.p1stats_id, self.map1_id)
        self.assertEqual(2, playermap_stats.rounds)

    def test_player_rounds_get_saved(self):
        # WHEN a player plays 3 complete rounds
        self.fireEvent('EVT_GAME_ROUND_START')
        self.fireEvent("EVT_CLIENT_JOIN", client=self.p1)
        self.fireEvent('EVT_GAME_ROUND_END')
        self.fireEvent('EVT_GAME_ROUND_START')
        self.fireEvent("EVT_CLIENT_JOIN", client=self.p1)
        # THEN
        player_stats = self.p.get_PlayerStats(client=self.p1)
        self.assertEqual(2, player_stats.rounds)