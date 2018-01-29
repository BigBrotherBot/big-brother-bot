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

import re
from textwrap import dedent
import unittest2 as unittest
from mock import Mock, DEFAULT, patch, call
from mockito import when, verify
import b3
from b3.clients import Client, Clients
from b3.fake import FakeClient
from b3.parsers.bfh import BfhParser, MAP_NAME_BY_ID, GAME_MODES_BY_MAP_ID, GAME_MODES_NAMES, BFH_PLAYER, BFH_SPECTATOR
from b3.config import XmlConfigParser, CfgConfigParser
from b3.parsers.frostbite2.protocol import CommandFailedError
from b3.parsers.frostbite2.util import MapListBlock
from b3.plugins.admin import AdminPlugin
from tests import logging_disabled


sleep_patcher = None


def setUpModule():
    sleep_patcher = patch("time.sleep")
    sleep_patcher.start()


# make sure to unpatch core B3 stuf
original_getByMagic = Clients.getByMagic
original_message = Client.message
original_disconnect = Clients.disconnect


def tearDownModule():
    Clients.getByMagic = original_getByMagic
    Client.message = original_message
    Clients.disconnect = original_disconnect
    if hasattr(Client, "messagequeueworker"):
        del Client.messagequeueworker
    if sleep_patcher:
        sleep_patcher.stop()


class BFHTestCase(unittest.TestCase):
    """
    Test case that is suitable for testing BFH parser specific features
    """

    @classmethod
    def setUpClass(cls):
        from b3.parsers.frostbite2.abstractParser import AbstractParser
        from b3.fake import FakeConsole

        AbstractParser.__bases__ = (FakeConsole,)
        # Now parser inheritance hierarchy is :
        # BFHParser -> AbstractParser -> FakeConsole -> Parser

    def tearDown(self):
        if hasattr(self, "parser"):
            del self.parser.clients
            self.parser.working = False


class Test_getServerInfo(BFHTestCase):
    def setUp(self):
        self.conf = CfgConfigParser()
        self.conf.loadFromString("""[configuration]""")
        self.parser = BfhParser(self.conf)
        self.parser.startup()

    def test_getServerInfo(self):
        # GIVEN
        when(self.parser).write(('serverInfo',)).thenReturn([
            '[WASP] Hotwire all maps -- Working kick on kills',
            '0',
            '14',
            'Hotwire0',
            'MP_Eastside',
            '0',
            '2',
            '0',
            '0',
            '',
            'true',
            'true',
            'false',
            '428710',
            '6019',
            '108.61.98.177:40000',
            '',
            'true',
            'EU',
            'ams',
            'NL',
            '0',
            'IN_GAME'
        ])

        # WHEN
        self.parser.getServerInfo()
        # THEN
        self.assertEqual('[WASP] Hotwire all maps -- Working kick on kills', self.parser.game.sv_hostname)
        self.assertEqual(14, self.parser.game.sv_maxclients)
        self.assertEqual("MP_Eastside", self.parser.game.mapName)
        self.assertEqual("Hotwire0", self.parser.game.gameType)
        self.assertEqual("108.61.98.177", self.parser._publicIp)
        self.assertEqual('40000', self.parser._gamePort)
        self.assertDictEqual(
            {'punkBusterVersion': '', 'team2score': None, 'numPlayers': '0', 'maxPlayers': '14', 'targetScore': '0',
             'closestPingSite': 'ams', 'blazeGameState': 'IN_GAME', 'onlineState': '',
             'serverName': '[WASP] Hotwire all maps -- Working kick on kills', 'gamemode': 'Hotwire0',
             'hasPunkbuster': 'true', 'hasPassword': 'false', 'numTeams': '0', 'team1score': None, 'roundTime': '6019',
             'blazePlayerCount': '0', 'isRanked': 'true', 'roundsPlayed': '0', 'serverUptime': '428710',
             'team4score': None, 'level': 'MP_Eastside', 'country': 'NL', 'region': 'EU', 'joinQueueEnabled': 'true',
             'roundsTotal': '2', 'gameIpAndPort': '108.61.98.177:40000', 'team3score': None}, self.parser.game.serverinfo)


class Test_bfh_events(BFHTestCase):
    def setUp(self):
        self.conf = CfgConfigParser()
        self.conf.loadFromString("""[configuration]""")
        self.parser = BfhParser(self.conf)
        self.parser.startup()
        # mock parser queueEvent method so we can make assertions on it later on
        self.parser.queueEvent = Mock(name="queueEvent method")
        self.joe = Mock(name="Joe", spec=Client)

        def event_repr(self):
            return "Event(%r, data=%r, client=%r, target=%r)" % (b3.events.eventManager.getName(self.type), self.data,
                                                                 self.client, self.target)
        b3.events.Event.__repr__ = event_repr

    def test_cmd_rotateMap_generates_EVT_GAME_ROUND_END(self):
        # prepare fake BFH server responses
        def fake_write(data):
            if data == ('mapList.getMapIndices', ):
                return [0, 1]
            else:
                return []

        self.parser.write = Mock(side_effect=fake_write)
        self.parser.getFullMapRotationList = Mock(return_value=MapListBlock(
            ['4', '3',
             'MP_007', 'RushLarge0', '4',
             'MP_011', 'RushLarge0', '4',
             'MP_012', 'SquadRush0', '4',
             'MP_013', 'SquadRush0', '4']))
        self.parser.rotateMap()
        self.assertEqual(1, self.parser.queueEvent.call_count)
        self.assertEqual(self.parser.getEventID("EVT_GAME_ROUND_END"), self.parser.queueEvent.call_args[0][0].type)
        self.assertIsNone(self.parser.queueEvent.call_args[0][0].data)

    def test_player_onChat_event_all(self):
        self.parser.getClient = Mock(return_value=self.joe)

        self.parser.routeFrostbitePacket(['player.onChat', 'Cucurbitaceae', 'test all', 'all'])
        self.assertEqual(1, self.parser.queueEvent.call_count)

        event = self.parser.queueEvent.call_args[0][0]
        self.assertEqual("Say", self.parser.getEventName(event.type))
        self.assertEquals('test all', event.data)
        self.assertEqual(self.joe, event.client)

    def test_player_onChat_event_team(self):
        self.parser.getClient = Mock(return_value=self.joe)

        self.parser.routeFrostbitePacket(['player.onChat', 'Cucurbitaceae', 'test team', 'team', '1'])
        self.assertEqual(1, self.parser.queueEvent.call_count)

        event = self.parser.queueEvent.call_args[0][0]
        self.assertEqual("Team Say", self.parser.getEventName(event.type))
        self.assertEquals('test team', event.data)
        self.assertEqual(self.joe, event.client)

    def test_player_onChat_event_squad(self):
        self.parser.getClient = Mock(return_value=self.joe)

        self.parser.routeFrostbitePacket(['player.onChat', 'Cucurbitaceae', 'test squad', 'squad', '1', '1'])
        self.assertEqual(1, self.parser.queueEvent.call_count)

        event = self.parser.queueEvent.call_args[0][0]
        self.assertEqual("Squad Say", self.parser.getEventName(event.type))
        self.assertEquals('test squad', event.data)
        self.assertEqual(self.joe, event.client)

    def test_server_onLevelLoaded(self):
        # GIVEN
        when(self.parser).write(('serverInfo',)).thenReturn([
            '[WASP] Hotwire all maps -- Working kick on kills', '0', '14', 'Hotwire0', 'MP_Eastside', '0', '2', '0', '0',
            '', 'true', 'true', 'false', '428710', '6019', '108.61.98.177:40000', '', 'true', 'EU', 'ams', 'NL', '0',
            'IN_GAME'])
        # WHEN
        with patch.object(self.parser, "warning") as warning_mock:
            self.parser.routeFrostbitePacket(['server.onLevelLoaded', 'MP_Glades', 'TeamDeathMatch0', '0', '1'])
        # THEN
        event = self.parser.queueEvent.call_args[0][0]
        self.assertEqual('Game Warmup', self.parser.getEventName(event.type))
        self.assertEquals('MP_Glades', event.data)
        self.assertListEqual([], warning_mock.mock_calls)


class Test_punkbuster_events(BFHTestCase):
    def setUp(self):
        self.conf = XmlConfigParser()
        self.conf.loadFromString("""
                <configuration>
                </configuration>
            """)
        self.parser = BfhParser(self.conf)
        self.parser.startup()

    def pb(self, msg):
        return self.parser.OnPunkbusterMessage(action=None, data=[msg])

    def assert_pb_misc_evt(self, msg):
        assert str(self.pb(msg)).startswith('Event<EVT_PUNKBUSTER_MISC>')

    def test_PB_SV_BanList(self):
        self.assert_pb_misc_evt(
            'PunkBuster Server: 1   b59ffffffffffffffffffffffffffc7d {13/15} "Cucurbitaceae" "87.45.14.2:3659" retest" ""')
        self.assert_pb_misc_evt(
            'PunkBuster Server: 1   b59ffffffffffffffffffffffffffc7d {0/1440} "Cucurbitaceae" "87.45.14.2:3659" mlkjsqfd" ""')

        self.assertEquals(
            '''Event<EVT_PUNKBUSTER_UNKNOWN>(['PunkBuster Server: 1   (UnBanned) b59ffffffffffffffffffffffffffc7d {15/15} "Cucurbitaceae" "87.45.14.2:3659" retest" ""'], None, None)''',
            str(self.pb(
                'PunkBuster Server: 1   (UnBanned) b59ffffffffffffffffffffffffffc7d {15/15} "Cucurbitaceae" "87.45.14.2:3659" retest" ""')))

        self.assert_pb_misc_evt('PunkBuster Server: Guid=b59ffffffffffffffffffffffffffc7d" Not Found in the Ban List')
        self.assert_pb_misc_evt('PunkBuster Server: End of Ban List (1 of 1 displayed)')

    def test_PB_UCON_message(self):
        result = self.pb(
            'PunkBuster Server: PB UCON "ggc_85.214.107.154"@85.214.107.154:14516 [admin.say "GGC-Stream.com - Welcome Cucurbitaceae with the GUID 31077c7d to our server." all]\n')
        self.assertEqual(
            'Event<EVT_PUNKBUSTER_UCON>({\'ip\': \'85.214.107.154\', \'cmd\': \'admin.say "GGC-Stream.com - Welcome Cucurbitaceae with the GUID 31077c7d to our server." all\', \'from\': \'ggc_85.214.107.154\', \'port\': \'14516\'}, None, None)',
            str(result))

    def test_PB_Screenshot_received_message(self):
        result = self.pb(
            'PunkBuster Server: Screenshot C:\\games\\bf3\\173_199_73_213_25200\\862147\\bf3\\pb\\svss\\pb000709.png successfully received (MD5=4576546546546546546546546543E1E1) from 19 Jaffar [da876546546546546546546546547673(-) 111.22.33.111:3659]\n')
        self.assertEqual(
            r"Event<EVT_PUNKBUSTER_SCREENSHOT_RECEIVED>({'slot': '19', 'name': 'Jaffar', 'ip': '111.22.33.111', 'pbid': 'da876546546546546546546546547673', 'imgpath': 'C:\\games\\bf3\\173_199_73_213_25200\\862147\\bf3\\pb\\svss\\pb000709.png', 'port': '3659', 'md5': '4576546546546546546546546543E1E1'}, None, None)",
            str(result))

    def test_PB_SV_PList(self):
        self.assert_pb_misc_evt(
            "PunkBuster Server: Player List: [Slot #] [GUID] [Address] [Status] [Power] [Auth Rate] [Recent SS] [O/S] [Name]")
        self.assert_pb_misc_evt('PunkBuster Server: End of Player List (0 Players)')

    def test_PB_Ver(self):
        self.assertIsNone(self.pb('PunkBuster Server: PunkBuster Server for BFH (v1.839 | A1386 C2.279) Enabled\n'))

    def test_PB_SV_BanGuid(self):
        self.assert_pb_misc_evt('PunkBuster Server: Ban Added to Ban List')
        self.assert_pb_misc_evt('PunkBuster Server: Ban Failed')

    def test_PB_SV_UnBanGuid(self):
        self.assert_pb_misc_evt('PunkBuster Server: Guid b59f190e5ef725e06531387231077c7d has been Unbanned')

    def test_PB_SV_UpdBanFile(self):
        self.assert_pb_misc_evt("PunkBuster Server: 0 Ban Records Updated in d:\\localuser\\g119142\\pb\\pbbans.dat")

    def test_misc(self):
        self.assertEqual(
            "Event<EVT_PUNKBUSTER_LOST_PLAYER>({'slot': '1', 'ip': 'x.x.x.x', 'port': '3659', 'name': 'joe', 'pbuid': '0837c128293d42aaaaaaaaaaaaaaaaa'}, None, None)",
            str(self.pb(
                "PunkBuster Server: Lost Connection (slot #1) x.x.x.x:3659 0837c128293d42aaaaaaaaaaaaaaaaa(-) joe")))

        self.assert_pb_misc_evt("PunkBuster Server: Invalid Player Specified: None")
        self.assert_pb_misc_evt("PunkBuster Server: Matched: Cucurbitaceae (slot #1)")
        self.assert_pb_misc_evt("PunkBuster Server: Received Master Security Information")
        self.assert_pb_misc_evt("PunkBuster Server: Auto Screenshot 000714 Requested from 25 Goldbat")


class Test_bfh_sends_no_guid(BFHTestCase):
    """
    See bug https://github.com/thomasleveil/big-brother-bot/issues/69
    """

    def setUp(self):
        BFHTestCase.setUp(self)
        self.conf = XmlConfigParser()
        self.conf.loadFromString("<configuration/>")
        self.parser = BfhParser(self.conf)
        self.parser.startup()

        self.authorizeClients_patcher = patch.object(self.parser.clients, "authorizeClients")
        self.authorizeClients_patcher.start()

        self.write_patcher = patch.object(self.parser, "write")
        self.write_mock = self.write_patcher.start()

        self.event_raw_data = 'PunkBuster Server: 14 300000aaaaaabbbbbbccccc111223300(-) 11.122.103.24:3659 OK   1 3.0 0 (W) "Snoopy"'
        self.regex_for_OnPBPlistItem = [x for (x, y) in self.parser._punkbusterMessageFormats if y == 'OnPBPlistItem'][
            0]

    def tearDown(self):
        BFHTestCase.tearDown(self)
        self.authorizeClients_patcher.stop()
        self.write_mock = self.write_patcher.stop()

    def test_auth_client_without_guid_but_with_known_pbid(self):
        # GIVEN

        # known superadmin named Snoopy
        superadmin = Client(console=self.parser, name='Snoopy', guid='EA_AAAAAAAABBBBBBBBBBBBBB00000000000012222',
                            pbid='300000aaaaaabbbbbbccccc111223300', group_bits=128, connections=21)
        superadmin.save()

        # bf3 server failing to provide guid
        def write(data):
            if data == ('admin.listPlayers', 'player', 'Snoopy'):
                return ['7', 'name', 'guid', 'teamId', 'squadId', 'kills', 'deaths', 'score', '1', 'Snoopy', '', '2',
                        '8', '0', '0', '0']
            else:
                return DEFAULT

        self.write_mock.side_effect = write

        # WHEN
        self.assertFalse('Snoopy' in self.parser.clients)
        self.parser.OnPBPlayerGuid(match=re.match(self.regex_for_OnPBPlistItem, self.event_raw_data),
                                   data=self.event_raw_data)

        # THEN
        # B3 should have authed Snoopy
        self.assertTrue('Snoopy' in self.parser.clients)
        snoopy = self.parser.clients['Snoopy']
        self.assertTrue(snoopy.authed)
        for attb in ('name', 'pbid', 'guid', 'groupBits'):
            self.assertEqual(getattr(superadmin, attb), getattr(snoopy, attb))

    def test_does_not_auth_client_without_guid_and_unknown_pbid(self):
        # GIVEN
        # bf3 server failing to provide guid
        def write(data):
            if data == ('admin.listPlayers', 'player', 'Snoopy'):
                return ['7', 'name', 'guid', 'teamId', 'squadId', 'kills', 'deaths', 'score', '1', 'Snoopy', '', '2',
                        '8', '0', '0', '0']
            else:
                return DEFAULT

        self.write_mock.side_effect = write

        # WHEN
        self.assertFalse('Snoopy' in self.parser.clients)
        self.parser.OnPBPlayerGuid(match=re.match(self.regex_for_OnPBPlistItem, self.event_raw_data),
                                   data=self.event_raw_data)

        # THEN
        # B3 should have authed Snoopy
        self.assertTrue('Snoopy' in self.parser.clients)
        snoopy = self.parser.clients['Snoopy']
        self.assertFalse(snoopy.authed)


class Test_bfh_maps(BFHTestCase):
    def setUp(self):
        BFHTestCase.setUp(self)
        self.conf = CfgConfigParser()
        self.conf.loadFromString("""[configuration]""")
        self.parser = BfhParser(self.conf)

    def test_each_map_has_at_least_one_gamemode(self):
        for map_id in MAP_NAME_BY_ID:
            self.assertIn(map_id, GAME_MODES_BY_MAP_ID)
            self.assertGreater(len(GAME_MODES_BY_MAP_ID[map_id]), 0)

    def test_each_gamemode_is_valid(self):
        game_modes_found = set()
        map(game_modes_found.update, GAME_MODES_BY_MAP_ID.values())
        self.assertSetEqual(set(GAME_MODES_NAMES.keys()), game_modes_found)
        for game_mode in game_modes_found:
            self.assertIn(game_mode, GAME_MODES_NAMES)

    def test_getEasyName(self):
        # main maps
        self.assertEqual('Bank Job', self.parser.getEasyName('mp_bank'))
        self.assertEqual('The Block', self.parser.getEasyName('mp_bloodout'))
        self.assertEqual('Dust Bowl', self.parser.getEasyName('mp_desert05'))
        self.assertEqual('Downtown', self.parser.getEasyName('mp_downtown'))
        self.assertEqual('Derailed', self.parser.getEasyName('mp_eastside'))
        self.assertEqual('Everglades', self.parser.getEasyName('mp_glades'))
        self.assertEqual('Growhouse', self.parser.getEasyName('mp_growhouse'))
        self.assertEqual('Hollywood Heights', self.parser.getEasyName('mp_hills'))
        self.assertEqual('Riptide', self.parser.getEasyName('mp_offshore'))
        # foo
        self.assertEqual('f00', self.parser.getEasyName('f00'))

    def test_getHardName(self):
        # main maps
        self.assertEqual('mp_bank', self.parser.getHardName('Bank Job'))
        self.assertEqual('mp_bloodout', self.parser.getHardName('The Block'))
        self.assertEqual('mp_desert05', self.parser.getHardName('Dust Bowl'))
        self.assertEqual('mp_downtown', self.parser.getHardName('Downtown'))
        self.assertEqual('mp_eastside', self.parser.getHardName('Derailed'))
        self.assertEqual('mp_glades', self.parser.getHardName('Everglades'))
        self.assertEqual('mp_growhouse', self.parser.getHardName('Growhouse'))
        self.assertEqual('mp_hills', self.parser.getHardName('Hollywood Heights'))
        self.assertEqual('mp_offshore', self.parser.getHardName('Riptide'))
        # foo
        self.assertEqual('f00', self.parser.getHardName('f00'))

    def test_getMapsSoundingLike(self):
        def assertSoundsLike(expected_id, input_value):
            self.assertEqual(expected_id, self.parser.getMapsSoundingLike(input_value), input_value)

        assertSoundsLike(['downtown', 'derailed', 'hollywood heights'], '')
        assertSoundsLike('mp_bank', 'Bank Job')
        assertSoundsLike('mp_bank', 'bankjob')
        assertSoundsLike('mp_bank', 'bancjob')
        assertSoundsLike('mp_bloodout', 'The Block')
        assertSoundsLike('mp_bloodout', 'block')
        assertSoundsLike('mp_desert05', 'Dust Bowl')
        assertSoundsLike('mp_desert05', 'dust')
        assertSoundsLike('mp_desert05', 'bowl')
        assertSoundsLike('mp_downtown', 'Downtown')
        assertSoundsLike('mp_downtown', 'down')
        assertSoundsLike('mp_downtown', 'town')
        assertSoundsLike('mp_eastside', 'Derailed')
        assertSoundsLike('mp_glades', 'Everglades')
        assertSoundsLike('mp_glades', 'ever')
        assertSoundsLike('mp_glades', 'glade')
        assertSoundsLike('mp_growhouse', 'Growhouse')
        assertSoundsLike('mp_growhouse', 'grow')
        assertSoundsLike('mp_growhouse', 'house')
        assertSoundsLike('mp_hills', 'Hollywood Heights')
        assertSoundsLike('mp_hills', 'hollywood')
        assertSoundsLike('mp_hills', 'holly')
        assertSoundsLike('mp_hills', 'height')
        assertSoundsLike('mp_offshore', 'Riptide')
        assertSoundsLike('mp_offshore', 'rip')
        assertSoundsLike('mp_offshore', 'tide')

    def test_getGamemodeSoundingLike(self):
        def assertSoundsLike(expected_id, map_id, input_gamemode):
            self.assertEqual(expected_id, self.parser.getGamemodeSoundingLike(map_id, input_gamemode),
                             "%s:%r" % (map_id, input_gamemode))

        def assertSoundsLikeList(expected_list, map_id, input_gamemode):
            self.assertListEqual(expected_list, self.parser.getGamemodeSoundingLike(map_id, input_gamemode),
                                 "%s:%r" % (map_id, input_gamemode))

        assertSoundsLikeList(['Conquest Large', 'Rescue', 'Heist'],   'mp_bank', '')

        assertSoundsLike('TurfWarLarge0',   'mp_bank', 'TurfWarLarge0')
        assertSoundsLike('TurfWarSmall0',   'mp_bank', 'TurfWarSmall0')
        assertSoundsLike('Heist0',          'mp_bank', 'Heist0')
        assertSoundsLike('Bloodmoney0',     'mp_bank', 'Bloodmoney0')
        assertSoundsLike('Hit0',            'mp_bank', 'Hit0')
        assertSoundsLike('Hostage0',        'mp_bank', 'Hostage0')
        assertSoundsLike('TeamDeathMatch0', 'mp_bank', 'TeamDeathMatch0')

        assertSoundsLike('TurfWarLarge0',   'mp_bank', 'Conquest Large')
        assertSoundsLike('TurfWarLarge0',   'mp_bank', 'cql')
        assertSoundsLike('TurfWarLarge0',   'mp_bank', 'twl')
        assertSoundsLike('TurfWarSmall0',   'mp_bank', 'Conquest Small')
        assertSoundsLike('TurfWarSmall0',   'mp_bank', 'cqs')
        assertSoundsLike('TurfWarSmall0',   'mp_bank', 'tws')
        assertSoundsLike('Heist0',          'mp_bank', 'Heist')
        assertSoundsLike('Heist0',          'mp_bank', 'he')
        assertSoundsLike('Bloodmoney0',     'mp_bank', 'Blood Money')
        assertSoundsLike('Bloodmoney0',     'mp_bank', 'bm')
        assertSoundsLike('Bloodmoney0',     'mp_bank', 'blood')
        assertSoundsLike('Bloodmoney0',     'mp_bank', 'money')
        assertSoundsLike('Hit0',            'mp_bank', 'Crosshair')
        assertSoundsLike('Hit0',            'mp_bank', 'cr')
        assertSoundsLike('Hit0',            'mp_bank', 'ch')
        assertSoundsLike('Hit0',            'mp_bank', 'cross')
        assertSoundsLike('Hostage0',        'mp_bank', 'Rescue')
        assertSoundsLike('Hostage0',        'mp_bank', 're')
        assertSoundsLike('Hostage0',        'mp_bank', 'rescue')
        assertSoundsLike('Hostage0',        'mp_bank', 'hostage')
        assertSoundsLike('TeamDeathMatch0', 'mp_bank', 'Team Deathmatch')
        assertSoundsLike('TeamDeathMatch0', 'mp_bank', 'tdm')

        assertSoundsLike('TurfWarLarge0',   'mp_bloodout', 'TurfWarLarge0')
        assertSoundsLike('TurfWarSmall0',   'mp_bloodout', 'TurfWarSmall0')
        assertSoundsLike('Heist0',          'mp_bloodout', 'Heist0')
        assertSoundsLike('Bloodmoney0',     'mp_bloodout', 'Bloodmoney0')
        assertSoundsLike('Hit0',            'mp_bloodout', 'Hit0')
        assertSoundsLike('Hostage0',        'mp_bloodout', 'Hostage0')
        assertSoundsLike('TeamDeathMatch0', 'mp_bloodout', 'TeamDeathMatch0')

        assertSoundsLike('TurfWarLarge0',   'mp_desert05', 'TurfWarLarge0')
        assertSoundsLike('TurfWarSmall0',   'mp_desert05', 'TurfWarSmall0')
        assertSoundsLike('Heist0',          'mp_desert05', 'Heist0')
        assertSoundsLike('Hotwire0',        'mp_desert05', 'Hotwire0')
        assertSoundsLike('Hotwire0',        'mp_desert05', 'Hot Wire')
        assertSoundsLike('Hotwire0',        'mp_desert05', 'hw')
        assertSoundsLike('Bloodmoney0',     'mp_desert05', 'Bloodmoney0')
        assertSoundsLike('Hit0',            'mp_desert05', 'Hit0')
        assertSoundsLike('Hostage0',        'mp_desert05', 'Hostage0')
        assertSoundsLike('TeamDeathMatch0', 'mp_desert05', 'TeamDeathMatch0')

        assertSoundsLike('TurfWarLarge0',   'mp_downtown', 'TurfWarLarge0')
        assertSoundsLike('TurfWarSmall0',   'mp_downtown', 'TurfWarSmall0')
        assertSoundsLike('Heist0',          'mp_downtown', 'Heist0')
        assertSoundsLike('Hotwire0',        'mp_downtown', 'Hotwire0')
        assertSoundsLike('Bloodmoney0',     'mp_downtown', 'Bloodmoney0')
        assertSoundsLike('Hit0',            'mp_downtown', 'Hit0')
        assertSoundsLike('Hostage0',        'mp_downtown', 'Hostage0')
        assertSoundsLike('TeamDeathMatch0', 'mp_downtown', 'TeamDeathMatch0')

        assertSoundsLike('TurfWarLarge0',   'mp_eastside', 'TurfWarLarge0')
        assertSoundsLike('TurfWarSmall0',   'mp_eastside', 'TurfWarSmall0')
        assertSoundsLike('Heist0',          'mp_eastside', 'Heist0')
        assertSoundsLike('Hotwire0',        'mp_eastside', 'Hotwire0')
        assertSoundsLike('Bloodmoney0',     'mp_eastside', 'Bloodmoney0')
        assertSoundsLike('Hit0',            'mp_eastside', 'Hit0')
        assertSoundsLike('Hostage0',        'mp_eastside', 'Hostage0')
        assertSoundsLike('TeamDeathMatch0', 'mp_eastside', 'TeamDeathMatch0')

        assertSoundsLike('TurfWarLarge0',   'mp_glades', 'TurfWarLarge0')
        assertSoundsLike('TurfWarSmall0',   'mp_glades', 'TurfWarSmall0')
        assertSoundsLike('Heist0',          'mp_glades', 'Heist0')
        assertSoundsLike('Hotwire0',        'mp_glades', 'Hotwire0')
        assertSoundsLike('Bloodmoney0',     'mp_glades', 'Bloodmoney0')
        assertSoundsLike('Hit0',            'mp_glades', 'Hit0')
        assertSoundsLike('Hostage0',        'mp_glades', 'Hostage0')
        assertSoundsLike('TeamDeathMatch0', 'mp_glades', 'TeamDeathMatch0')

        assertSoundsLikeList(['Conquest Small', 'Heist', 'Team Deathmatch'],   'mp_growhouse', '')
        assertSoundsLikeList(['Conquest Small', 'Heist', 'Blood Money'],   'mp_growhouse', 'TurfWarLarge0')
        assertSoundsLike('TurfWarSmall0',   'mp_growhouse', 'TurfWarSmall0')
        assertSoundsLike('Heist0',          'mp_growhouse', 'Heist0')
        assertSoundsLike('Bloodmoney0',     'mp_growhouse', 'Bloodmoney0')
        assertSoundsLike('Hit0',            'mp_growhouse', 'Hit0')
        assertSoundsLike('Hostage0',        'mp_growhouse', 'Hostage0')
        assertSoundsLike('TeamDeathMatch0', 'mp_growhouse', 'TeamDeathMatch0')

        assertSoundsLike('TurfWarLarge0',   'mp_hills', 'TurfWarLarge0')
        assertSoundsLike('TurfWarSmall0',   'mp_hills', 'TurfWarSmall0')
        assertSoundsLike('Heist0',          'mp_hills', 'Heist0')
        assertSoundsLike('Hotwire0',        'mp_hills', 'Hotwire0')
        assertSoundsLike('Bloodmoney0',     'mp_hills', 'Bloodmoney0')
        assertSoundsLike('Hit0',            'mp_hills', 'Hit0')
        assertSoundsLike('Hostage0',        'mp_hills', 'Hostage0')
        assertSoundsLike('TeamDeathMatch0', 'mp_hills', 'TeamDeathMatch0')

        assertSoundsLike('TurfWarLarge0',   'mp_offshore', 'TurfWarLarge0')
        assertSoundsLike('TurfWarSmall0',   'mp_offshore', 'TurfWarSmall0')
        assertSoundsLike('Heist0',          'mp_offshore', 'Heist0')
        assertSoundsLike('Hotwire0',        'mp_offshore', 'Hotwire0')
        assertSoundsLike('Bloodmoney0',     'mp_offshore', 'Bloodmoney0')
        assertSoundsLike('Hit0',            'mp_offshore', 'Hit0')
        assertSoundsLike('Hostage0',        'mp_offshore', 'Hostage0')
        assertSoundsLike('TeamDeathMatch0', 'mp_offshore', 'TeamDeathMatch0')




class Test_getPlayerPings(BFHTestCase):
    def setUp(self):
        BFHTestCase.setUp(self)
        self.conf = XmlConfigParser()
        self.conf.loadFromString("""
                <configuration>
                </configuration>
            """)
        self.parser = BfhParser(self.conf)
        self.p1 = FakeClient(self.parser, name="Player1")
        self.p2 = FakeClient(self.parser, name="Player2")

    def test_no_player(self):
        # WHEN
        actual_result = self.parser.getPlayerPings()
        # THEN
        self.assertDictEqual({}, actual_result)

    def test_one_player(self):
        # GIVEN
        self.p1.connects("Player1")
        when(self.parser).write(('admin.listPlayers', 'all')).thenReturn(
            ['10', 'name', 'guid', 'teamId', 'squadId', 'kills', 'deaths', 'score', 'rank', 'ping', 'type',
             '1', 'Player1', 'EA_XXX', '1', '1', '0', '0', '0', '1', '140', '0']
        )
        # WHEN
        actual_result = self.parser.getPlayerPings()
        # THEN
        self.assertDictEqual({self.p1.cid: 140}, actual_result)

    def test_two_player(self):
        # GIVEN
        self.p1.connects("Player1")
        self.p2.connects("Player2")
        when(self.parser).write(('admin.listPlayers', 'all')).thenReturn(
            ['10', 'name', 'guid', 'teamId', 'squadId', 'kills', 'deaths', 'score', 'rank', 'ping', 'type',
             '2', 'Player1', 'EA_XXX', '1', '1', '0', '0', '0', '1', '140', '0',
             'Player2', 'EA_XXY', '1', '1', '0', '0', '0', '1', '450', '0']
        )
        # WHEN
        actual_result = self.parser.getPlayerPings()
        # THEN
        self.assertDictEqual({self.p1.cid: 140, self.p2.cid: 450}, actual_result)

    def test_two_player_filter_client_ids(self):
        # GIVEN
        self.p1.connects("Player1")
        self.p2.connects("Player2")
        when(self.parser).write(('admin.listPlayers', 'all')).thenReturn(
            ['10', 'name', 'guid', 'teamId', 'squadId', 'kills', 'deaths', 'score', 'rank', 'ping', 'type',
             '2', 'Player1', 'EA_XXX', '1', '1', '0', '0', '0', '1', '140', '0',
             'Player2', 'EA_XXY', '1', '1', '0', '0', '0', '1', '450', '0']
        )
        # WHEN
        actual_result = self.parser.getPlayerPings(filter_client_ids=[self.p1.cid])
        # THEN
        self.assertDictEqual({self.p1.cid: 140}, actual_result)

    def test_bad_data_filter_client_ids(self):
        # GIVEN
        self.p1.connects("Player1")
        self.p2.connects("Player2")
        when(self.parser).write(('admin.listPlayers', 'all')).thenReturn(
            ['10', 'name', 'guid', 'teamId', 'squadId', 'kills', 'deaths', 'score', 'rank', 'ping', 'type',
             '1', 'Player1', 'EA_XXX', '1', '1', '0', '0', '0', '1', '140', '0',
             'Player2', 'EA_XYZ', '1', '1', '0', '0', '0', '1', 'f00', '0']
        )
        # WHEN
        actual_result = self.parser.getPlayerPings(filter_client_ids=[self.p1.cid, self.p2.cid])
        # THEN
        self.assertDictEqual({self.p1.cid: 140}, actual_result)

    def test_bad_data(self):
        # GIVEN
        self.p1.connects("Player1")
        self.p2.connects("Player2")
        when(self.parser).write(('admin.listPlayers', 'all')).thenReturn(
            ['10', 'name', 'guid', 'teamId', 'squadId', 'kills', 'deaths', 'score', 'rank', 'ping', 'type',
             '1', 'Player1', 'EA_XXX', '1', '1', '0', '0', '0', '1', '140', '0',
             'Player2', 'EA_XYZ', '1', '1', '0', '0', '0', '1', 'f00', '0']
        )
        # WHEN
        actual_result = self.parser.getPlayerPings()
        # THEN
        self.assertDictEqual({self.p1.cid: 140}, actual_result)

    def test_exception(self):
        # GIVEN
        self.p1.connects("Player1")
        self.p2.connects("Player2")
        when(self.parser).write(('admin.listPlayers', 'all')).thenReturn(
            ['10', 'name', 'guid', 'teamId', 'squadId', 'kills', 'deaths', 'score', 'rank', 'ping', 'type',
             '1', 'Player1', 'EA_XXX', '1', '1', '0', '0', '0', '1', '140', '0',
             'Player2', 'EA_XYZ', '1', '1', '0', '0', '0', '1', 'f00', '0']
        )
        # WHEN
        actual_result = self.parser.getPlayerPings(filter_client_ids=[self.p1.cid, self.p2.cid])
        # THEN
        self.assertDictEqual({self.p1.cid: 140}, actual_result)


class Test_patch_b3_Client_isAlive(BFHTestCase):
    def setUp(self):
        BFHTestCase.setUp(self)
        self.conf = XmlConfigParser()
        self.conf.loadFromString("""
                <configuration>
                </configuration>
            """)
        self.parser = BfhParser(self.conf)
        self.foobar = self.parser.clients.newClient(cid='Foobar', name='Foobar', guid="FoobarGuid")

    def test_unknown(self):
        # GIVEN
        when(self.parser).write(('player.isAlive', 'Foobar')).thenReturn()
        # THEN
        self.assertEqual(b3.STATE_UNKNOWN, self.foobar.state)

    def test_alive(self):
        # GIVEN
        when(self.parser).write(('player.isAlive', 'Foobar')).thenReturn(['true'])
        # THEN
        self.assertEqual(b3.STATE_ALIVE, self.foobar.state)

    def test_dead(self):
        # GIVEN
        when(self.parser).write(('player.isAlive', 'Foobar')).thenReturn(['false'])
        # THEN
        self.assertEqual(b3.STATE_DEAD, self.foobar.state)

    def test_exception_InvalidPlayerName(self):
        when(self.parser).write(('player.isAlive', 'Foobar')).thenRaise(CommandFailedError(['InvalidPlayerName']))
        self.assertEqual(b3.STATE_UNKNOWN, self.foobar.state)


class Test_patch_b3_admin_plugin(BFHTestCase):
    def setUp(self):
        BFHTestCase.setUp(self)
        with logging_disabled():
            self.conf = CfgConfigParser()
            self.conf.loadFromString("""[configuration]""")
            self.parser = BfhParser(self.conf)
            adminPlugin_conf = CfgConfigParser()
            adminPlugin_conf.loadFromString(dedent(r"""
                [commands]
                map: 20
            """))
            adminPlugin = AdminPlugin(self.parser, adminPlugin_conf)
            adminPlugin.onLoadConfig()
            adminPlugin.onStartup()
            when(self.parser).getPlugin('admin').thenReturn(adminPlugin)
            self.parser.patch_b3_admin_plugin()
            self.joe = FakeClient(self.parser, name="Joe", guid="joeguid", groupBits=128)
            self.joe.connects(cid="joe")
            self.parser.game.gameType = "TurfWarSmall0"
            self.parser.game.serverinfo = {'roundsTotal': 2}

    def test_map_known_on_correct_gamemode(self):
        # GIVEN
        self.parser.game.gameType = "TurfwarLarge0"
        # WHEN
        with patch.object(self.parser, 'changeMap') as changeMap_mock:
            self.joe.says("!map Downtown")
        # THEN
        self.assertListEqual([call('mp_downtown', gamemode_id='TurfwarLarge0', number_of_rounds=2)],
                             changeMap_mock.mock_calls)
        self.assertListEqual([], self.joe.message_history)

    def test_map_InvalidGameModeOnMap(self):
        self.parser.game.gameType = "Hotwire0"
        # WHEN
        when(self.parser).changeMap('mp_bank', gamemode_id="Hotwire0", number_of_rounds=2).thenRaise(
            CommandFailedError(["InvalidGameModeOnMap"]))
        self.joe.says("!map bank")
        # THEN
        self.assertListEqual(
            ['Bank Job cannot be played with gamemode Hotwire',
             'supported gamemodes are : Conquest Large, Conquest Small, Heist, Blood Money, Crosshair, Rescue, Team Deathmatch'],
            self.joe.message_history)

    def test_map_InvalidRoundsPerMap(self):
        # WHEN
        when(self.parser).changeMap('mp_bank', gamemode_id="TurfWarSmall0", number_of_rounds=2).thenRaise(
            CommandFailedError(["InvalidRoundsPerMap"]))
        self.joe.says("!map bank")
        # THEN
        self.assertListEqual(['number of rounds must be 1 or greater'], self.joe.message_history)

    def test_map_Full(self):
        # WHEN
        with patch.object(self.parser, "changeMap", side_effect=CommandFailedError(["Full"])):
            self.joe.says("!map bank")
        # THEN
        self.assertListEqual(['map list maximum size has been reached'], self.joe.message_history)

    def test_map_unknown(self):
        # WHEN
        with patch.object(self.parser, 'changeMap') as changeMap_mock:
            self.joe.says("!map xxxxxxxxf00xxxxxxxxx")
        # THEN
        self.assertListEqual([], changeMap_mock.mock_calls)
        self.assertEqual(1, len(self.joe.message_history))
        self.assertTrue(self.joe.message_history[0].startswith("do you mean"))


class Test_Client_player_type(BFHTestCase):
    def setUp(self):
        BFHTestCase.setUp(self)
        self.conf = XmlConfigParser()
        self.conf.loadFromString("""
                <configuration>
                </configuration>
            """)
        self.parser = BfhParser(self.conf)
        self.foobar = self.parser.clients.newClient(cid='Foobar', name='Foobar', guid="FoobarGuid")

    def test_player_type_player(self):
        # GIVEN
        when(self.parser).write(('admin.listPlayers', 'player', 'Foobar')).thenReturn(
            ['10', 'name', 'guid', 'teamId', 'squadId', 'kills', 'deaths', 'score', 'rank', 'ping', 'type', '1',
             'Foobar', 'xxxxy', '1', '0', '0', '0', '0', '71', '65535', '0'])
        # THEN
        self.assertEqual(BFH_PLAYER, self.foobar.player_type)

    def test_player_type_spectator(self):
        # GIVEN
        when(self.parser).write(('admin.listPlayers', 'player', 'Foobar')).thenReturn(
            ['10', 'name', 'guid', 'teamId', 'squadId', 'kills', 'deaths', 'score', 'rank', 'ping', 'type', '1',
             'Foobar', 'xxxxy', '0', '0', '0', '0', '0', '71', '65535', '1'])
        # THEN
        self.assertEqual(BFH_SPECTATOR, self.foobar.player_type)

class Test_Client_is_commander(BFHTestCase):
    def setUp(self):
        BFHTestCase.setUp(self)
        self.conf = XmlConfigParser()
        self.conf.loadFromString("""
                <configuration>
                </configuration>
            """)
        self.parser = BfhParser(self.conf)
        self.foobar = self.parser.clients.newClient(cid='Foobar', name='Foobar', guid="FoobarGuid")


class Test_getClient(BFHTestCase):
    def setUp(self):
        BFHTestCase.setUp(self)
        self.conf = XmlConfigParser()
        self.conf.loadFromString("""<configuration/>""")
        self.parser = BfhParser(self.conf)

    @staticmethod
    def build_listPlayer_response(cid, team_id, type_id):
        """
        :param type_id: {0: player, 1: spectator, 2: commander}
        :type cid: str
        :type team_id: str
        :type type_id: str
        :rtype : list of str
        """
        return ['10', 'name', 'guid', 'teamId', 'squadId', 'kills', 'deaths', 'score', 'rank', 'ping', 'type', '1',
                cid, 'xxxxy', team_id, '0', '0', '0', '0', '71', '65535', type_id]

    def test_team_red_player(self):
        # GIVEN
        when(self.parser).write(('admin.listPlayers', 'player', 'Foobar')).thenReturn(
            self.build_listPlayer_response('Foobar', '1', '0'))
        # WHEN
        player = self.parser.getClient('Foobar')
        # THEN
        self.assertEqual(b3.TEAM_RED, player.team)

    def test_team_blue_player(self):
        # GIVEN
        when(self.parser).write(('admin.listPlayers', 'player', 'Foobar')).thenReturn(
            self.build_listPlayer_response('Foobar', '2', '0'))
        # WHEN
        player = self.parser.getClient('Foobar')
        # THEN
        self.assertEqual(b3.TEAM_BLUE, player.team)

    def test_team_red_commander(self):
        # GIVEN
        when(self.parser).write(('admin.listPlayers', 'player', 'Foobar')).thenReturn(
            self.build_listPlayer_response('Foobar', '1', '2'))
        # WHEN
        player = self.parser.getClient('Foobar')
        # THEN
        self.assertEqual(b3.TEAM_RED, player.team)

    def test_team_blue_commander(self):
        # GIVEN
        when(self.parser).write(('admin.listPlayers', 'player', 'Foobar')).thenReturn(
            self.build_listPlayer_response('Foobar', '2', '2'))
        # WHEN
        player = self.parser.getClient('Foobar')
        # THEN
        self.assertEqual(b3.TEAM_BLUE, player.team)

    def test_team_spectator(self):
        # GIVEN
        when(self.parser).write(('admin.listPlayers', 'player', 'Foobar')).thenReturn(
            self.build_listPlayer_response('Foobar', '0', '1'))
        # WHEN
        player = self.parser.getClient('Foobar')
        # THEN
        self.assertEqual(b3.TEAM_SPEC, player.team)


class Test_config(BFHTestCase):
    def setUp(self):
        with logging_disabled():
            self.conf = CfgConfigParser()
            self.parser = BfhParser(self.conf)

    def assert_big_b3_private_responses(self, expected, config):
        self.parser._big_b3_private_responses = None
        self.conf.loadFromString(config)
        self.parser.load_conf_big_b3_private_responses()
        self.assertEqual(expected, self.parser._big_b3_private_responses)

    def test_big_b3_private_responses_on(self):
        self.assert_big_b3_private_responses(True, dedent("""
            [bfh]
            big_b3_private_responses: on"""))
        self.assert_big_b3_private_responses(False, dedent("""
            [bfh]
            big_b3_private_responses: off"""))
        self.assert_big_b3_private_responses(False, dedent("""
            [bfh]
            big_b3_private_responses: f00"""))
        self.assert_big_b3_private_responses(False, dedent("""
            [bfh]
            big_b3_private_responses:"""))

    def assert_big_msg_duration(self, expected, config):
        self.parser._big_msg_duration = None
        self.conf.loadFromString(config)
        self.parser.load_conf_big_msg_duration()
        self.assertEqual(expected, self.parser._big_msg_duration)

    def test_big_msg_duration(self):
        default_value = 4
        self.assert_big_msg_duration(0, dedent("""
            [bfh]
            big_msg_duration: 0"""))
        self.assert_big_msg_duration(5, dedent("""
            [bfh]
            big_msg_duration: 5"""))
        self.assert_big_msg_duration(default_value, dedent("""
            [bfh]
            big_msg_duration: 5.6"""))
        self.assert_big_msg_duration(30, dedent("""
            [bfh]
            big_msg_duration: 30"""))
        self.assert_big_msg_duration(default_value, dedent("""
            [bfh]
            big_msg_duration: f00"""))
        self.assert_big_msg_duration(default_value, dedent("""
            [bfh]
            big_msg_duration:"""))

    def assert_big_msg_repeat(self, expected, config):
        self.parser._big_msg_repeat = None
        self.conf.loadFromString(config)
        self.parser.load_conf_big_b3_private_responses()
        self.parser.load_conf_big_msg_repeat()
        self.assertEqual(expected, self.parser._big_msg_repeat)

    def test_big_msg_repeat(self):
        default_value = 'pm'
        self.assert_big_msg_repeat('all', dedent("""
            [bfh]
            big_b3_private_responses: on
            big_msg_repeat: all"""))
        self.assert_big_msg_repeat('off', dedent("""
            [bfh]
            big_msg_repeat: off"""))
        self.assert_big_msg_repeat(default_value, dedent("""
            [bfh]
            big_b3_private_responses: on
            big_msg_repeat: pm"""))
        self.assert_big_msg_repeat(default_value, dedent("""
            [bfh]
            big_b3_private_responses: on
            big_msg_repeat:"""))
        self.assert_big_msg_repeat('off', dedent("""
            [bfh]
            big_msg_repeat: OFF"""))
        self.assert_big_msg_repeat(default_value, dedent("""
            [bfh]
            big_b3_private_responses: on
            big_msg_repeat: junk"""))