#
# Jumper Plugin for BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2013 Daniele Pantaleone <fenix@bigbrotherbot.net>
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

import json
import unittest2

from textwrap import dedent
from mock import Mock
from mockito import when
from b3 import TEAM_FREE, TEAM_SPEC
from b3.cvar import Cvar
from b3.config import MainConfig
from b3.config import XmlConfigParser
from b3.config import CfgConfigParser
from b3.parsers.iourt42 import Iourt42Parser
from b3.plugins.admin import AdminPlugin
from b3.plugins.jumper import JumperPlugin
from b3.plugins.jumper import JumpRun
from tests import logging_disabled

MAPDATA_JSON = '''{"ut4_uranus_beta1a": {"size": 1841559, "nom": "Uranus", "njump": "22", "mdate": "2013-01-16", "pk3":
"ut4_uranus_beta1a", "level": 50, "id": 308, "utversion": 2, "nway": 1, "howjump": "", "mapper": "Levant"},
"ut4_crouchtraining_a1": {"size": 993461, "nom": "Crouch Training", "njump": "11", "mdate": "2010-12-31",
"pk3": "ut4_crouchtraining_a1", "level": 79, "id": 346, "utversion": 2, "nway": 1, "howjump": "", "mapper": "spidercochon"}}'''


class JumperTestCase(unittest2.TestCase):

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
            demorecord: no
            skipstandardmaps: yes
            minleveldelete: senioradmin

            [commands]
            delrecord: guest
            maprecord: guest
            mapinfo: guest
            record: guest
            setway: senioradmin
            topruns: guest
            map: fulladmin
            maps: user
            setnextmap: admin
        """))

        self.p = JumperPlugin(self.console, self.conf)
        self.p.onLoadConfig()
        self.p.onStartup()

        # load fixed json data (do not contact urtjumpers api for testing)
        when(self.p).getMapsDataFromApi().thenReturn(json.loads(MAPDATA_JSON))

    def tearDown(self):
        self.console.working = False


class Test_events(JumperTestCase):

    def setUp(self):
        JumperTestCase.setUp(self)
        with logging_disabled():
            from b3.fake import FakeClient

        # create some clients
        self.mike = FakeClient(console=self.console, name="Mike", guid="mikeguid", team=TEAM_FREE, groupBits=1)
        self.bill = FakeClient(console=self.console, name="Bill", guid="billguid", team=TEAM_FREE, groupBits=1)
        self.mike.connects("1")
        self.bill.connects("2")

        # force fake mapname
        self.console.game.mapName = 'ut42_bstjumps_u2'

    def tearDown(self):
        self.mike.disconnects()
        self.bill.disconnects()
        JumperTestCase.tearDown(self)

    ####################################################################################################################
    #                                                                                                                  #
    #   JUMPRUN EVENTS                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def test_event_client_jumprun_started(self):
        # WHEN
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_JUMP_RUN_START', client=self.mike, data={'way_id' : '1'}))
        # THEN
        self.assertEqual(True, self.mike.isvar(self.p, 'jumprun'))
        self.assertIsNone(self.mike.var(self.p, 'jumprun').value.demo)
        self.assertIsInstance(self.mike.var(self.p, 'jumprun').value, JumpRun)

    def test_event_client_jumprun_stopped(self):
        # WHEN
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_JUMP_RUN_STOP', client=self.mike, data={'way_id' : '1', 'way_time' : '12345'}))
        # THEN
        self.assertEqual(False, self.mike.isvar(self.p, 'jumprun'))
        self.assertListEqual([], self.p.getClientRecords(self.mike, self.console.game.mapName))

    def test_event_client_jumprun_canceled(self):
        # WHEN
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_JUMP_RUN_CANCEL', client=self.mike, data={'way_id' : '1'}))
        # THEN
        self.assertEqual(False, self.mike.isvar(self.p, 'jumprun'))
        self.assertListEqual([], self.p.getClientRecords(self.mike, self.console.game.mapName))

    def test_event_client_jumprun_started_stopped(self):
        # WHEN
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_JUMP_RUN_START', client=self.mike, data={'way_id' : '1'}))
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_JUMP_RUN_STOP', client=self.mike, data={'way_id' : '1', 'way_time' : '12345'}))
        # THEN
        self.assertEqual(False, self.mike.isvar(self.p, 'jumprun'))
        self.assertEqual(1, len(self.p.getClientRecords(self.mike, self.console.game.mapName)))

    def test_event_client_jumprun_started_canceled(self):
        # WHEN
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_JUMP_RUN_START', client=self.mike, data={'way_id' : '1'}))
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_JUMP_RUN_CANCEL', client=self.mike, data={'way_id' : '1'}))
        # THEN
        self.assertEqual(False, self.mike.isvar(self.p, 'jumprun'))
        self.assertEqual(0, len(self.p.getClientRecords(self.mike, self.console.game.mapName)))

    def test_event_client_jumprun_started_stopped_multiple_clients(self):
        # WHEN
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_JUMP_RUN_START', client=self.mike, data={'way_id' : '1'}))
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_JUMP_RUN_STOP', client=self.mike, data={'way_id' : '1', 'way_time' : '12345'}))
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_JUMP_RUN_START', client=self.bill, data={'way_id' : '1'}))
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_JUMP_RUN_STOP', client=self.bill, data={'way_id' : '1', 'way_time' : '12345'}))
        # THEN
        self.assertEqual(False, self.mike.isvar(self.p, 'jumprun'))
        self.assertEqual(False, self.bill.isvar(self.p, 'jumprun'))
        self.assertEqual(1, len(self.p.getClientRecords(self.mike, self.console.game.mapName)))
        self.assertEqual(1, len(self.p.getClientRecords(self.bill, self.console.game.mapName)))

    def test_event_client_jumprun_started_stopped_multiple_ways(self):
        # WHEN
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_JUMP_RUN_START', client=self.mike, data={'way_id' : '1'}))
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_JUMP_RUN_STOP', client=self.mike, data={'way_id' : '1', 'way_time' : '12345'}))
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_JUMP_RUN_START', client=self.mike, data={'way_id' : '2'}))
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_JUMP_RUN_STOP', client=self.mike, data={'way_id' : '2', 'way_time' : '12345'}))
        # THEN
        self.assertEqual(False, self.mike.isvar(self.p, 'jumprun'))
        self.assertEqual(2, len(self.p.getClientRecords(self.mike, self.console.game.mapName)))

    def test_event_client_jumprun_started_stopped_multiple_clients_multiple_ways(self):
        # WHEN
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_JUMP_RUN_START', client=self.mike, data={'way_id' : '1'}))
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_JUMP_RUN_STOP', client=self.mike, data={'way_id' : '1', 'way_time' : '12345'}))
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_JUMP_RUN_START', client=self.mike, data={'way_id' : '2'}))
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_JUMP_RUN_STOP', client=self.mike, data={'way_id' : '2', 'way_time' : '12345'}))
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_JUMP_RUN_START', client=self.bill, data={'way_id' : '1'}))
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_JUMP_RUN_STOP', client=self.bill, data={'way_id' : '1', 'way_time' : '12345'}))
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_JUMP_RUN_START', client=self.bill, data={'way_id' : '2'}))
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_JUMP_RUN_STOP', client=self.bill, data={'way_id' : '2', 'way_time' : '12345'}))
        # THEN
        self.assertEqual(False, self.mike.isvar(self.p, 'jumprun'))
        self.assertEqual(False, self.bill.isvar(self.p, 'jumprun'))
        self.assertEqual(2, len(self.p.getClientRecords(self.mike, self.console.game.mapName)))
        self.assertEqual(2, len(self.p.getClientRecords(self.bill, self.console.game.mapName)))

    ####################################################################################################################
    #                                                                                                                  #
    #   OTHER EVENTS                                                                                                   #
    #                                                                                                                  #
    ####################################################################################################################

    def test_event_game_map_change(self):
        # WHEN
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_JUMP_RUN_START', client=self.mike, data={'way_id' : '1'}))
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_JUMP_RUN_START', client=self.bill, data={'way_id' : '1'}))
        self.console.queueEvent(self.console.getEvent('EVT_GAME_MAP_CHANGE', data='\sv_allowdownload\0\g_matchmode\0\g_gametype\9\sv_maxclients\32\sv_floodprotect\1'))
        # THEN
        self.assertEqual(False, self.mike.isvar(self.p, 'jumprun'))
        self.assertEqual(False, self.bill.isvar(self.p, 'jumprun'))
        self.assertListEqual([], self.p.getClientRecords(self.mike, self.console.game.mapName))
        self.assertListEqual([], self.p.getClientRecords(self.bill, self.console.game.mapName))

    def test_event_client_disconnect(self):
        # WHEN
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_JUMP_RUN_START', client=self.mike, data={'way_id' : '1'}))
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_DISCONNECT', client=self.mike, data=None))
        # THEN
        self.assertEqual(False, self.mike.isvar(self.p, 'jumprun'))

    def test_event_client_team_change(self):
        # WHEN
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_JUMP_RUN_START', client=self.mike, data={'way_id' : '1'}))
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_JUMP_RUN_START', client=self.bill, data={'way_id' : '1'}))
        self.mike.team = TEAM_SPEC  # will raise EVT_CLIENT_TEAM_CHANGE
        self.bill.team = TEAM_FREE  # will not raise EVT_CLIENT_TEAM_CHANGE
        # THEN
        self.assertEqual(TEAM_SPEC, self.mike.team)
        self.assertEqual(TEAM_FREE, self.bill.team)
        self.assertEqual(False, self.mike.isvar(self.p, 'jumprun'))
        self.assertEqual(True, self.bill.isvar(self.p, 'jumprun'))
        self.assertIsInstance(self.bill.var(self.p, 'jumprun').value, JumpRun)

    ####################################################################################################################
    #                                                                                                                  #
    #   PLUGIN HOOKS                                                                                                   #
    #                                                                                                                  #
    ####################################################################################################################

    def test_plugin_disable(self):
        # WHEN
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_JUMP_RUN_START', client=self.mike, data={'way_id' : '1'}))
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_JUMP_RUN_START', client=self.bill, data={'way_id' : '1'}))
        self.p.disable()
        # THEN
        self.assertEqual(False, self.mike.isvar(self.p, 'jumprun'))
        self.assertEqual(False, self.bill.isvar(self.p, 'jumprun'))

    def test_plugin_enable(self):
        # GIVEN
        self.p.console.write = Mock()
        self.p.disable()
        self.p._cycle_count = 0
        self.console.game.mapName = 'ut4_casa'
        # WHEN
        self.p.enable()
        self.p.console.write.assert_called_with('cyclemap')
        self.assertEqual(1, self.p._cycle_count)


class Test_commands(JumperTestCase):

    def setUp(self):
        JumperTestCase.setUp(self)
        with logging_disabled():
            from b3.fake import FakeClient

        # create some clients
        self.mike = FakeClient(console=self.console, name="Mike", guid="mikeguid", team=TEAM_FREE, groupBits=128)
        self.bill = FakeClient(console=self.console, name="Bill", guid="billguid", team=TEAM_FREE, groupBits=1)
        self.mark = FakeClient(console=self.console, name="Mark", guid="markguid", team=TEAM_FREE, groupBits=1)
        self.mike.connects("1")
        self.bill.connects("2")
        self.mark.connects("3")

        self.console.game.mapName = 'ut42_bstjumps_u2'
        self.console.parseLine('''ClientJumpRunStarted: 1 - way: 1''')
        self.console.parseLine('''ClientJumpRunStopped: 1 - way: 1 - time: 537000''')
        self.console.parseLine('''ClientJumpRunStarted: 2 - way: 1''')
        self.console.parseLine('''ClientJumpRunStopped: 2 - way: 1 - time: 349000''')
        self.console.parseLine('''ClientJumpRunStarted: 3 - way: 1''')
        self.console.parseLine('''ClientJumpRunStopped: 3 - way: 1 - time: 122000''')
        self.console.parseLine('''ClientJumpRunStarted: 1 - way: 2''')
        self.console.parseLine('''ClientJumpRunStopped: 1 - way: 2 - time: 84000''')
        self.console.parseLine('''ClientJumpRunStarted: 2 - way: 2''')
        self.console.parseLine('''ClientJumpRunStopped: 2 - way: 2 - time: 91000''')
        self.console.parseLine('''ClientJumpRunStarted: 3 - way: 2''')
        self.console.parseLine('''ClientJumpRunStopped: 3 - way: 2 - time: 177000''')

        self.console.game.mapName = 'ut42_jupiter'
        self.console.parseLine('''ClientJumpRunStarted: 1 - way: 1''')
        self.console.parseLine('''ClientJumpRunStopped: 1 - way: 1 - time: 123000''')
        self.console.parseLine('''ClientJumpRunStarted: 2 - way: 1''')
        self.console.parseLine('''ClientJumpRunStopped: 2 - way: 1 - time: 543000''')
        self.console.parseLine('''ClientJumpRunStarted: 1 - way: 2''')
        self.console.parseLine('''ClientJumpRunStopped: 1 - way: 2 - time: 79000''')

        when(self.console).getMaps().thenReturn(['ut4_abbey', 'ut4_abbeyctf', 'ut4_algiers', 'ut4_ambush',
            'ut4_austria', 'ut42_bstjumps_u2', 'ut4_bohemia', 'ut4_casa', 'ut4_cascade', 'ut4_commune',
            'ut4_company', 'ut4_crossing', 'ut4_docks', 'ut4_dressingroom', 'ut4_eagle', 'ut4_elgin',
            'ut4_firingrange', 'ut4_ghosttown_rc4', 'ut4_harbortown', 'ut4_herring', 'ut4_horror', 'ut42_jupiter',
            'ut4_kingdom', 'ut4_kingpin', 'ut4_mandolin', 'ut4_mars_b1', 'ut4_maya', 'ut4_oildepot', 'ut4_prague',
            'ut4_prague_v2', 'ut4_raiders', 'ut4_ramelle', 'ut4_ricochet', 'ut4_riyadh', 'ut4_sanc', 'ut4_snoppis',
            'ut4_suburbs', 'ut4_subway', 'ut4_swim', 'ut4_thingley', 'ut4_tombs', 'ut4_toxic',
            'ut4_tunis', 'ut4_turnpike', 'ut4_uptown'])

    def tearDown(self):
        self.mike.disconnects()
        self.bill.disconnects()
        self.mark.disconnects()
        JumperTestCase.tearDown(self)

    ####################################################################################################################
    #                                                                                                                  #
    #   CLIENT RECORD COMMAND                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    def test_cmd_client_record_no_arguments(self):
        # GIVEN
        self.console.game.mapName = 'ut42_bstjumps_u2'
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says('!record')
        # THEN
        self.assertListEqual(['listing records for Mike (@%s) on ut42_bstjumps_u2:' % self.mike.id,
                              '[1] 0:08:57.000 since %s' % JumperPlugin.getDateString(self.console.time()),
                              '[2] 0:01:24.000 since %s' % JumperPlugin.getDateString(self.console.time())], self.mike.message_history)

    def test_cmd_client_record_single_argument(self):
        # GIVEN
        self.console.game.mapName = 'ut42_bstjumps_u2'
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says('!record bill')
        # THEN
        self.assertListEqual(['listing records for Bill (@%s) on ut42_bstjumps_u2:' % self.bill.id,
                              '[1] 0:05:49.000 since %s' % JumperPlugin.getDateString(self.console.time()),
                              '[2] 0:01:31.000 since %s' % JumperPlugin.getDateString(self.console.time())], self.mike.message_history)

    def test_cmd_client_record_double_arguments(self):
        # GIVEN
        self.console.game.mapName = 'ut42_bstjumps_u2'
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says('!record bill jupiter')
        # THEN
        self.assertListEqual(['[1] 0:09:03.000 since %s' % JumperPlugin.getDateString(self.console.time())], self.mike.message_history)

    def test_cmd_client_record_double_arguments_no_record(self):
        # GIVEN
        self.console.game.mapName = 'ut42_bstjumps_u2'
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says('!record mark jupiter')
        # THEN
        self.assertListEqual(['no record found for Mark (@%s) on ut42_jupiter' % self.mark.id], self.mike.message_history)

    ####################################################################################################################
    #                                                                                                                  #
    #   MAP RECORD COMMAND                                                                                             #
    #                                                                                                                  #
    ####################################################################################################################

    def test_cmd_maprecord_no_arguments(self):
        # GIVEN
        self.console.game.mapName = 'ut42_bstjumps_u2'
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says('!maprecord')
        # THEN
        self.assertListEqual(['listing map records on ut42_bstjumps_u2:',
                              '[1] Mark (@%s) with 0:02:02.000' % self.mark.id,
                              '[2] Mike (@%s) with 0:01:24.000' % self.mike.id], self.mike.message_history)

    def test_cmd_maprecord_with_arguments(self):
        # GIVEN
        self.console.game.mapName = 'ut42_bstjumps_u2'
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says('!maprecord jupiter')
        # THEN
        self.assertListEqual(['listing map records on ut42_jupiter:',
                              '[1] Mike (@%s) with 0:02:03.000' % self.mike.id,
                              '[2] Mike (@%s) with 0:01:19.000' % self.mike.id], self.mike.message_history)

    def test_cmd_maprecord_with_arguments_no_record(self):
        # GIVEN
        self.console.game.mapName = 'ut42_bstjumps_u2'
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says('!maprecord mars')
        # THEN
        self.assertListEqual(['no record found on ut4_mars_b1'], self.mike.message_history)

    ####################################################################################################################
    #                                                                                                                  #
    #   TOPRUNS COMMAND                                                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    def test_cmd_topruns_no_arguments(self):
        # GIVEN
        self.console.game.mapName = 'ut42_bstjumps_u2'
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says('!topruns')
        # THEN
        self.assertListEqual(['listing top runs on ut42_bstjumps_u2:',
                              '[1] #1 Mark (@%s) with 0:02:02.000' % self.mark.id,
                              '[1] #2 Bill (@%s) with 0:05:49.000' % self.bill.id,
                              '[1] #3 Mike (@%s) with 0:08:57.000' % self.mike.id,
                              '[2] #1 Mike (@%s) with 0:01:24.000' % self.mike.id,
                              '[2] #2 Bill (@%s) with 0:01:31.000' % self.bill.id,
                              '[2] #3 Mark (@%s) with 0:02:57.000' % self.mark.id], self.mike.message_history)

    def test_cmd_topruns_with_arguments(self):
        # GIVEN
        self.console.game.mapName = 'ut42_bstjumps_u2'
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says('!topruns jupiter')
        # THEN
        self.assertListEqual(['listing top runs on ut42_jupiter:',
                              '[1] #1 Mike (@%s) with 0:02:03.000' % self.mike.id,
                              '[1] #2 Bill (@%s) with 0:09:03.000' % self.bill.id,
                              '[2] #1 Mike (@%s) with 0:01:19.000' % self.mike.id], self.mike.message_history)

    def test_cmd_topruns_with_arguments_no_record(self):
        # GIVEN
        self.console.game.mapName = 'ut42_bstjumps_u2'
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says('!topruns mars')
        # THEN
        self.assertListEqual(['no record found on ut4_mars_b1'], self.mike.message_history)

    ####################################################################################################################
    #                                                                                                                  #
    #   DELRECORD COMMAND                                                                                              #
    #                                                                                                                  #
    ####################################################################################################################

    def test_cmd_delrecord_no_arguments(self):
        # GIVEN
        self.console.game.mapName = 'ut42_bstjumps_u2'
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says('!delrecord')
        # THEN
        self.assertListEqual(['removed 2 records for Mike (@%s) on ut42_bstjumps_u2' % self.mike.id], self.mike.message_history)
        self.assertListEqual([], self.p.getClientRecords(self.mike, 'ut42_bstjumps_u2'))

    def test_cmd_delrecord_with_one_argument(self):
        # GIVEN
        self.console.game.mapName = 'ut42_bstjumps_u2'
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says('!delrecord bill')
        # THEN
        self.assertListEqual(['removed 2 records for Bill (@%s) on ut42_bstjumps_u2' % self.bill.id], self.mike.message_history)
        self.assertListEqual([], self.p.getClientRecords(self.bill, 'ut42_bstjumps_u2'))

    def test_cmd_delrecord_with_two_arguments(self):
        # GIVEN
        self.console.game.mapName = 'ut42_bstjumps_u2'
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says('!delrecord bill jupiter')
        # THEN
        self.assertListEqual(['removed 1 record for Bill (@%s) on ut42_jupiter' % self.bill.id], self.mike.message_history)
        self.assertListEqual([], self.p.getClientRecords(self.bill, 'ut42_jupiter'))

    def test_cmd_delrecord_with_two_arguments_no_record(self):
        # GIVEN
        self.console.game.mapName = 'ut42_bstjumps_u2'
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says('!delrecord mark jupiter')
        # THEN
        self.assertListEqual(['no record found for Mark (@%s) on ut42_jupiter' % self.mark.id], self.mike.message_history)

    ####################################################################################################################
    #                                                                                                                #
    #   MAPINFO COMMAND                                                                                              #
    #                                                                                                                #
    ####################################################################################################################

    # def test_cmd_mapinfo_no_arguments(self):
    #     # GIVEN
    #     self.console.game.mapName = 'ut4_uranus_beta1a'
    #     # WHEN
    #     self.mike.clearMessageHistory()
    #     self.mike.says('!mapinfo')
    #     # THEN
    #     self.assertListEqual([u'''Uranus has been created by Levant''',
    #                           u'''it has been released on Tue, 15 Jan 2013''',
    #                           u'''it's composed of 22 jumps and 1 way''',
    #                           u'''level: 50/100'''], self.mike.message_history)

    # def test_cmd_mapinfo_with_arguments(self):
    #     # GIVEN
    #     self.console.game.mapName = 'ut4_uranus_beta1a'
    #     # WHEN
    #     self.mike.clearMessageHistory()
    #     self.mike.says('!mapinfo crouch')
    #     # THEN
    #     self.assertListEqual([u'''Crouch Training has been created by spidercochon''',
    #                           u'''it has been released on Thu, 30 Dec 2010''',
    #                           u'''it's composed of 11 jumps and 1 way''',
    #                           u'''level: 79/100'''], self.mike.message_history)

    # def test_cmd_mapinfo_no_result(self):
    #     # GIVEN
    #     self.console.game.mapName = 'ut4_turnpike'
    #     # WHEN
    #     self.mike.clearMessageHistory()
    #     self.mike.says('!mapinfo')
    #     # THEN
    #     self.assertListEqual(['could not find info for map ut4_turnpike'], self.mike.message_history)

    ####################################################################################################################
    #                                                                                                                  #
    #   SETWAY COMMAND                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def test_cmd_setway(self):
        # GIVEN
        self.console.game.mapName = 'ut42_bstjumps_u2'
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says('!setway 1 Rookie')
        self.mike.says('!setway 2 Explorer')
        self.mike.clearMessageHistory()
        self.mike.says('!maprecord')
        # THEN
        self.assertListEqual(['listing map records on ut42_bstjumps_u2:',
                              '[Rookie] Mark (@%s) with 0:02:02.000' % self.mark.id,
                              '[Explorer] Mike (@%s) with 0:01:24.000' % self.mike.id], self.mike.message_history)

    ####################################################################################################################
    #                                                                                                                  #
    #   OTHER COMMANDS                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def test_cmd_maps(self):
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says('!maps')
        # THEN
        self.assertListEqual(['map rotation: ut42_bstjumps_u2, ut42_jupiter, ut4_mars_b1'], self.mike.message_history)

    def test_cmd_map_valid_name(self):
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says('!map jup')
        # THEN
        self.assertListEqual(['changing map to ut42_jupiter'], self.mike.message_history)

    def test_cmd_map_invalid_name(self):
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says('!map f00')
        # THEN
        self.assertListEqual(['do you mean: ut42_bstjumps_u2, ut4_mars_b1, ut42_jupiter?'], self.mike.message_history)