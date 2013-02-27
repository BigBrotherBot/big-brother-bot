#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2013 Courgette
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
import unittest2 as unittest
from mock import patch
from mockito import when
from b3.clients import Client, Clients
from b3.fake import FakeClient
from b3.parsers.frostbite2.util import MapListBlockError
from b3.parsers.mohw import MohwParser, MAP_NAME_BY_ID, GAME_MODES_BY_MAP_ID, GAME_MODES_NAMES, NewMapListBlock
from b3.config import XmlConfigParser


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


class MohwTestCase(unittest.TestCase):
    """
    Test case that is suitable for testing BF3 parser specific features
    """

    @classmethod
    def setUpClass(cls):
        from b3.parsers.frostbite2.abstractParser import AbstractParser
        from b3.fake import FakeConsole
        AbstractParser.__bases__ = (FakeConsole,)
        # Now parser inheritance hierarchy is :
        # MohwParser -> AbstractParser -> FakeConsole -> Parser

    def tearDown(self):
        if hasattr(self, "parser"):
            del self.parser.clients
            self.parser.working = False


class Test_getServerInfo(unittest.TestCase):

    def test_decodeServerinfo(self):
        self.assertDictEqual({
            'serverName': 'BigBrotherBot #1 MOHW',
            'numPlayers': '0',
            'maxPlayers': '20',
            'gamemode': 'TeamDeathMatch',
            'level': 'MP_10',
            'roundsPlayed': '0',
            'roundsTotal': '1',
            'numTeams': '2',
            'team1score': '0',
            'team2score': '0',
            'targetScore': '75',
            'onlineState': '',
            'isRanked': 'true',
            'hasPunkbuster': 'true',
            'hasPassword': 'false',
            'serverUptime': '86755',
            'roundTime': '84003',
            'gameIpAndPort': '',
            'punkBusterVersion': '',
            'joinQueueEnabled': '',
            'region': 'EU',
            'closestPingSite': 'i3d-ams',
            'country': 'GB',
        }, MohwParser.decodeServerinfo(
            ['BigBrotherBot #1 MOHW', '0', '20', 'TeamDeathMatch', 'MP_10', '0', '1', '2', '0', '0', '75', '', 'true',
             'true', 'false', '86755', '84003', '', '', '', 'EU', 'i3d-ams', 'GB']
        ))


class Test_events(MohwTestCase):
    """
    class holding tests that assert the correct B3 was fired given a particular input or action
    """

    def setUp(self):
        MohwTestCase.setUp(self)
        self.conf = XmlConfigParser()
        self.conf.loadFromString("""
                <configuration>
                </configuration>
            """)
        self.parser = MohwParser(self.conf)
        self.parser.startup()
        # patch parser queueEvent method so we can make assertions on it later on
        self.queueEvent_patcher = patch.object(self.parser, 'queueEvent')
        self.queueEvent_mock = self.queueEvent_patcher.start()

    def tearDown(self):
        MohwTestCase.tearDown(self)
        self.queueEvent_patcher.stop()

    def assert_event_was_fired(self, expected_event):
        """
        Assert that last event fired is of the given type and return it
        :param expected_event: expected event as an string, i.e. :  "EVT_GAME_ROUND_END"
        :return: fired event or will raise AssertError when appropriate
        """
        self.assertTrue(self.queueEvent_mock.called, "no event was fired")
        event = self.queueEvent_mock.call_args[0][0]
        self.assertEqual(self.parser.getEventID(expected_event), event.type)
        return event

    def test_cmd_rotateMap_generate_EVT_GAME_ROUND_END(self):
        # GIVEN
        when(self.parser).write(('mapList.getMapIndices', )).thenReturn([0, 1])
        when(self.parser).getFullMapRotationList().thenReturn(
            NewMapListBlock(['4', 'CustomPL', '3', 'MP_03', 'CombatMission', '1', 'MP_05', 'BombSquad', '1', 'MP_10',
                             'Sport', '4', 'MP_013', 'SectorControl', '4']))
        # WHEN
        self.parser.rotateMap()
        # THEN
        event = self.assert_event_was_fired("EVT_GAME_ROUND_END")
        self.assertEqual('Event<EVT_GAME_ROUND_END>(None, None, None)', str(event))

    def test_player_onChat_generate_EVT_CLIENT_SAY(self):
        # GIVEN
        joe = FakeClient(console=self.parser, name="Joe", guid="Joe")
        when(self.parser).getClient("Joe").thenReturn(joe)
        # WHEN
        self.parser.routeFrostbitePacket(['player.onChat', 'Joe', 'test all', 'all'])
        # THEN
        event = self.assert_event_was_fired("EVT_CLIENT_SAY")
        self.assertEqual('test all', event.data)
        self.assertEqual(joe, event.client)


class Test_maps(MohwTestCase):

    def setUp(self):
        MohwTestCase.setUp(self)
        self.conf = XmlConfigParser()
        self.conf.loadFromString("""
                <configuration>
                </configuration>
            """)
        self.parser = MohwParser(self.conf)

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
        self.assertEqual('Somalia Stronghold', self.parser.getEasyName('MP_03'))
        self.assertEqual('Novi Grad Warzone', self.parser.getEasyName('MP_05'))
        self.assertEqual('Sarajevo Stadium', self.parser.getEasyName('MP_10'))
        self.assertEqual('Basilan Aftermath', self.parser.getEasyName('MP_12'))
        self.assertEqual('Hara Dunes', self.parser.getEasyName('MP_13'))
        self.assertEqual('Al Fara Cliffside', self.parser.getEasyName('MP_16'))
        self.assertEqual('Shogore Valley', self.parser.getEasyName('MP_18'))
        self.assertEqual('Tungunan Jungle', self.parser.getEasyName('MP_19'))
        self.assertEqual('Darra Gun Market', self.parser.getEasyName('MP_20'))
        self.assertEqual('Chitrail Compound', self.parser.getEasyName('MP_21'))
        self.assertEqual('f00', self.parser.getEasyName('f00'))

    def test_getHardName(self):
        self.assertEqual('MP_03', self.parser.getHardName('Somalia Stronghold'))
        self.assertEqual('MP_05', self.parser.getHardName('Novi Grad Warzone'))
        self.assertEqual('MP_10', self.parser.getHardName('Sarajevo Stadium'))
        self.assertEqual('MP_12', self.parser.getHardName('Basilan Aftermath'))
        self.assertEqual('MP_13', self.parser.getHardName('Hara Dunes'))
        self.assertEqual('MP_16', self.parser.getHardName('Al Fara Cliffside'))
        self.assertEqual('MP_18', self.parser.getHardName('Shogore Valley'))
        self.assertEqual('MP_19', self.parser.getHardName('Tungunan Jungle'))
        self.assertEqual('MP_20', self.parser.getHardName('Darra Gun Market'))
        self.assertEqual('MP_21', self.parser.getHardName('Chitrail Compound'))
        self.assertEqual('f00', self.parser.getHardName('f00'))


class Test_getMapsSoundingLike(MohwTestCase):
    """
    make sure that getMapsSoundingLike returns expected results
    """

    def setUp(self):
        MohwTestCase.setUp(self)
        self.conf = XmlConfigParser()
        self.conf.loadFromString("""
                <configuration>
                </configuration>
            """)
        self.parser = MohwParser(self.conf)

    def test_MP_03(self):
        self.assertEqual('MP_03', self.parser.getMapsSoundingLike('somalia stronghold'))
        self.assertEqual('MP_03', self.parser.getMapsSoundingLike('somaliastronghold'))
        self.assertEqual('MP_03', self.parser.getMapsSoundingLike('somalia'))
        self.assertEqual('MP_03', self.parser.getMapsSoundingLike('stronghold'))

    def test_MP_05(self):
        self.assertEqual('MP_05', self.parser.getMapsSoundingLike('novi grad warzone'))
        self.assertEqual('MP_05', self.parser.getMapsSoundingLike('novigradwarzone'))
        self.assertEqual('MP_05', self.parser.getMapsSoundingLike('novi'))
        self.assertEqual('MP_05', self.parser.getMapsSoundingLike('WARZONE'))

    def test_MP_10(self):
        self.assertEqual('MP_10', self.parser.getMapsSoundingLike('sarajevo stadium'))
        self.assertEqual('MP_10', self.parser.getMapsSoundingLike('sarajevostadium'))
        self.assertEqual('MP_10', self.parser.getMapsSoundingLike('sarajevo'))
        self.assertEqual('MP_10', self.parser.getMapsSoundingLike('stadium'))

    def test_MP_12(self):
        self.assertEqual('MP_12', self.parser.getMapsSoundingLike('basilan aftermath'))
        self.assertEqual('MP_12', self.parser.getMapsSoundingLike('basilanaftermath'))
        self.assertEqual('MP_12', self.parser.getMapsSoundingLike('basilan'))
        self.assertEqual('MP_12', self.parser.getMapsSoundingLike('aftermath'))

    def test_MP_13(self):
        self.assertEqual('MP_13', self.parser.getMapsSoundingLike('hara dunes'))
        self.assertEqual('MP_13', self.parser.getMapsSoundingLike('haradunes'))
        self.assertEqual('MP_13', self.parser.getMapsSoundingLike('hara'))
        self.assertEqual('MP_13', self.parser.getMapsSoundingLike('dunes'))

    def test_MP_16(self):
        self.assertEqual('MP_16', self.parser.getMapsSoundingLike('al fara cliffside'))
        self.assertEqual('MP_16', self.parser.getMapsSoundingLike('alfaracliffside'))
        self.assertEqual('MP_16', self.parser.getMapsSoundingLike('alfara'))
        self.assertEqual('MP_16', self.parser.getMapsSoundingLike('faracliffside'))
        self.assertEqual('MP_16', self.parser.getMapsSoundingLike('fara'))
        self.assertEqual('MP_16', self.parser.getMapsSoundingLike('cliffside'))

    def test_MP_18(self):
        self.assertEqual('MP_18', self.parser.getMapsSoundingLike('shogore valley'))
        self.assertEqual('MP_18', self.parser.getMapsSoundingLike('shogorevalley'))
        self.assertEqual('MP_18', self.parser.getMapsSoundingLike('shogore'))
        self.assertEqual('MP_18', self.parser.getMapsSoundingLike('valley'))

    def test_MP_19(self):
        self.assertEqual('MP_19', self.parser.getMapsSoundingLike('tungunan jungle'))
        self.assertEqual('MP_19', self.parser.getMapsSoundingLike('tungunanjungle'))
        self.assertEqual('MP_19', self.parser.getMapsSoundingLike('tungunan'))
        self.assertEqual('MP_19', self.parser.getMapsSoundingLike('jungle'))

    def test_MP_20(self):
        self.assertEqual('MP_20', self.parser.getMapsSoundingLike('darra gun market'))
        self.assertEqual('MP_20', self.parser.getMapsSoundingLike('darragunmarket'))
        self.assertEqual('MP_20', self.parser.getMapsSoundingLike('darra'))
        self.assertEqual('MP_20', self.parser.getMapsSoundingLike('darragun'))
        self.assertEqual('MP_20', self.parser.getMapsSoundingLike('market'))

    def test_MP_21(self):
        self.assertEqual('MP_21', self.parser.getMapsSoundingLike('chitrail compound'))
        self.assertEqual('MP_21', self.parser.getMapsSoundingLike('chitrailcompound'))
        self.assertEqual('MP_21', self.parser.getMapsSoundingLike('chitrail'))
        self.assertEqual('MP_21', self.parser.getMapsSoundingLike('compound'))

    def test_suggestions(self):
        self.assertEqual(['novi grad warzone', 'shogore valley', 'darra gun market'], self.parser.getMapsSoundingLike(''))


class Test_getGamemodeSoundingLike(MohwTestCase):
    """
    make sure that getGamemodeSoundingLike returns expected results
    """

    def setUp(self):
        MohwTestCase.setUp(self)
        self.conf = XmlConfigParser()
        self.conf.loadFromString("""
                <configuration>
                </configuration>
            """)
        self.parser = MohwParser(self.conf)

    def test_CombatMission(self):
        self.assertEqual('CombatMission', self.parser.getGamemodeSoundingLike('MP_03', 'CombatMission'))
        self.assertEqual('CombatMission', self.parser.getGamemodeSoundingLike('MP_03', 'Combat Mission'))
        self.assertEqual('CombatMission', self.parser.getGamemodeSoundingLike('MP_03', 'Combt Mission'))
        self.assertEqual('CombatMission', self.parser.getGamemodeSoundingLike('MP_03', 'Mission'))
        self.assertEqual('CombatMission', self.parser.getGamemodeSoundingLike('MP_03', 'combat'))
        self.assertEqual('CombatMission', self.parser.getGamemodeSoundingLike('MP_03', 'cm'))

    def test_Sport(self):
        self.assertEqual('Sport', self.parser.getGamemodeSoundingLike('MP_03', 'Sport'))
        self.assertEqual('Sport', self.parser.getGamemodeSoundingLike('MP_03', 'Home Run'))
        self.assertEqual('Sport', self.parser.getGamemodeSoundingLike('MP_03', 'Home'))
        self.assertEqual('Sport', self.parser.getGamemodeSoundingLike('MP_03', 'run'))
        self.assertEqual('Sport', self.parser.getGamemodeSoundingLike('MP_03', 'homerun'))
        self.assertEqual('Sport', self.parser.getGamemodeSoundingLike('MP_03', 'hr'))

    def test_SectorControl(self):
        self.assertEqual('SectorControl', self.parser.getGamemodeSoundingLike('MP_03', 'SectorControl'))
        self.assertEqual('SectorControl', self.parser.getGamemodeSoundingLike('MP_03', 'Sector Control'))
        self.assertEqual('SectorControl', self.parser.getGamemodeSoundingLike('MP_03', 'Sector'))
        self.assertEqual('SectorControl', self.parser.getGamemodeSoundingLike('MP_03', 'control'))
        self.assertEqual('SectorControl', self.parser.getGamemodeSoundingLike('MP_03', 'sc'))

    def test_TeamDeathMatch(self):
        self.assertEqual('TeamDeathMatch', self.parser.getGamemodeSoundingLike('MP_03', 'TeamDeathMatch'))
        self.assertEqual('TeamDeathMatch', self.parser.getGamemodeSoundingLike('MP_03', 'Team DeathMatch'))
        self.assertEqual('TeamDeathMatch', self.parser.getGamemodeSoundingLike('MP_03', 'Team Death Match'))
        self.assertEqual('TeamDeathMatch', self.parser.getGamemodeSoundingLike('MP_03', 'Death Match'))
        self.assertEqual('TeamDeathMatch', self.parser.getGamemodeSoundingLike('MP_03', 'team'))
        self.assertEqual('TeamDeathMatch', self.parser.getGamemodeSoundingLike('MP_03', 'death'))
        self.assertEqual('TeamDeathMatch', self.parser.getGamemodeSoundingLike('MP_03', 'Match'))
        self.assertEqual('TeamDeathMatch', self.parser.getGamemodeSoundingLike('MP_03', 'tdm'))

    def test_BombSquad(self):
        self.assertEqual('BombSquad', self.parser.getGamemodeSoundingLike('MP_03', 'BombSquad'))
        self.assertEqual('BombSquad', self.parser.getGamemodeSoundingLike('MP_03', 'Hot Spot'))
        self.assertEqual('BombSquad', self.parser.getGamemodeSoundingLike('MP_03', 'Hotspot'))
        self.assertEqual('BombSquad', self.parser.getGamemodeSoundingLike('MP_03', 'hot'))
        self.assertEqual('BombSquad', self.parser.getGamemodeSoundingLike('MP_03', 'spot'))
        self.assertEqual('BombSquad', self.parser.getGamemodeSoundingLike('MP_03', 'Bomb'))
        self.assertEqual('BombSquad', self.parser.getGamemodeSoundingLike('MP_03', 'hs'))

    def test_suggestions(self):
        # unrecognizable input, falling back on available gamemodes for current map
        self.assertEqual(['Sector Control', 'Team Death Match', 'Home Run'],
                         self.parser.getGamemodeSoundingLike('MP_12', ''))


class Test_MapListBlock(unittest.TestCase):

    def test_no_param(self):
        self.assertEqual(0, len(NewMapListBlock()))

    def test_none(self):
        self.assertRaises(MapListBlockError, NewMapListBlock, (None,))

    def test_empty_list(self):
        self.assertRaises(MapListBlockError, NewMapListBlock, ([],))

    def test_bad_list(self):
        self.assertRaises(MapListBlockError, NewMapListBlock, ('foo',))
        self.assertRaises(MapListBlockError, NewMapListBlock, (['x'],))
        self.assertRaises(MapListBlockError, NewMapListBlock, ([None],))
        self.assertRaises(MapListBlockError, NewMapListBlock, ([0],))
        self.assertRaises(MapListBlockError, NewMapListBlock, ([0,1],))
        self.assertRaises(MapListBlockError, NewMapListBlock, ([0,'x'],))
        self.assertRaises(MapListBlockError, NewMapListBlock, (['a','b','c','d'],))
        self.assertRaises(MapListBlockError, NewMapListBlock, (['1','3', 'a1','b1','1', 'a2'],))
        self.assertRaises(MapListBlockError, NewMapListBlock, (['1','3', 'a1','b1','xxx'],))

    def test_minimal(self):
        self.assertEqual(0, len(NewMapListBlock([0, "CustomPL", 3])))
        self.assertEqual('NewMapListBlock[]', repr(NewMapListBlock([0, "CustomPL", 3])))
        self.assertEqual(0, len(NewMapListBlock(['0', "CustomPL", '3'])))
        tmp = NewMapListBlock(['1', "CustomPL", '3', 'test', 'mode', '2'])
        self.assertEqual(1, len(tmp), repr(tmp))
        self.assertEqual('NewMapListBlock[]', repr(NewMapListBlock(['0', "CustomPL", '3'])))
        self.assertEqual(0, len(NewMapListBlock(['0', "CustomPL", '3']).getByName('MP_003')))

    def test_1(self):
        bloc = NewMapListBlock(['1', "CustomPL", '3', 'test', 'mode', '2'])
        self.assertEqual(1, len(bloc))
        self.assertEqual('test', bloc[0]['name'])
        self.assertEqual('mode', bloc[0]['gamemode'])
        self.assertEqual(2, bloc[0]['num_of_rounds'])
        self.assertEqual("NewMapListBlock[test:mode:2]", repr(bloc))
        self.assertEqual(0, len(bloc.getByName('MP_003')))
        self.assertEqual(1, len(bloc.getByName('test')))

    def test_2(self):
        bloc = NewMapListBlock(['2', "CustomPL", '3', 'map1', 'mode1', '1', 'map2', 'mode2', '2'])
        self.assertEqual(2, len(bloc))
        self.assertEqual('map1', bloc[0]['name'])
        self.assertEqual('mode1', bloc[0]['gamemode'])
        self.assertEqual(1, bloc[0]['num_of_rounds'])
        self.assertEqual('map2', bloc[1]['name'])
        self.assertEqual('mode2', bloc[1]['gamemode'])
        self.assertEqual(2, bloc[1]['num_of_rounds'])
        self.assertEqual("NewMapListBlock[map1:mode1:1, map2:mode2:2]", repr(bloc))
        self.assertEqual(0, len(bloc.getByName('MP_003')))
        self.assertEqual(1, len(bloc.getByName('map1')))
        self.assertEqual(1, len(bloc.getByName('map2')))
        self.assertIn(0, bloc.getByName('map1'))
        self.assertIn(1, bloc.getByName('map2'))
        self.assertTrue(bloc.getByName('map1')[0]['gamemode'] == 'mode1')
        self.assertTrue(bloc.getByName('map2')[1]['gamemode'] == 'mode2')
        self.assertEqual(0, len(bloc.getByNameAndGamemode('map1', 'mode?')))
        self.assertEqual(1, len(bloc.getByNameAndGamemode('map1', 'mode1')))
        self.assertEqual(0, len(bloc.getByNameAndGamemode('map2', 'mode?')))
        self.assertEqual(1, len(bloc.getByNameAndGamemode('map2', 'mode2')))
        self.assertIn(0, bloc.getByNameAndGamemode('map1', 'mode1'))
        self.assertIn(1, bloc.getByNameAndGamemode('map2', 'mode2'))

    def test_3(self):
        bloc = NewMapListBlock(['3', "CustomPL", '3', 'map1', 'mode1', '1', 'map2', 'mode2', '2', 'map1', 'mode2', '2'])
        self.assertEqual(3, len(bloc))
        self.assertEqual('map1', bloc[2]['name'])
        self.assertEqual('mode2', bloc[2]['gamemode'])
        self.assertEqual(0, len(bloc.getByName('MP_003')))
        self.assertEqual(2, len(bloc.getByName('map1')))
        self.assertEqual(1, len(bloc.getByName('map2')))
        self.assertEqual("NewMapListBlock[map1:mode1:1, map2:mode2:2, map1:mode2:2]", repr(bloc))
        self.assertIn(0, bloc.getByName('map1'))
        self.assertIn(1, bloc.getByName('map2'))
        self.assertIn(2, bloc.getByName('map1'))
        self.assertTrue(bloc.getByName('map1')[0]['gamemode'] == 'mode1')
        self.assertTrue(bloc.getByName('map1')[2]['gamemode'] == 'mode2')
        self.assertTrue(bloc.getByName('map2')[1]['gamemode'] == 'mode2')
        self.assertEqual(0, len(bloc.getByNameAndGamemode('map1', 'mode?')))
        self.assertEqual(1, len(bloc.getByNameAndGamemode('map1', 'mode1')))
        self.assertEqual(1, len(bloc.getByNameAndGamemode('map1', 'mode2')))
        self.assertEqual(0, len(bloc.getByNameAndGamemode('map2', 'mode?')))
        self.assertEqual(0, len(bloc.getByNameAndGamemode('map2', 'mode1')))
        self.assertEqual(1, len(bloc.getByNameAndGamemode('map2', 'mode2')))
        self.assertIn(0, bloc.getByNameAndGamemode('map1', 'mode1'))
        self.assertIn(1, bloc.getByNameAndGamemode('map2', 'mode2'))
        self.assertIn(2, bloc.getByNameAndGamemode('map1', 'mode2'))
        self.assertIn(2, bloc.getByNameGamemodeAndRounds('map1', 'mode2', '2'))


class Test_MapListBlock_append(unittest.TestCase):

    def test_append_list_with_different_num_words(self):
        data1 = [1, "CustomPL", 3, 'a1', 'a2', 1]
        data2 = [1, "CustomPL", 4, 'b1', 'b2', 1, 'b4']
        # check both data lists make valid NewMapListBlock individually
        self.assertEqual(1, len(NewMapListBlock(data1)))
        self.assertEqual(1, len(NewMapListBlock(data2)))
        # check both 2nd list cannot be appended to the 1st one.
        mlb1 = NewMapListBlock(data1)
        self.assertEqual(3, mlb1._num_words)
        try:
            mlb1.append(data2)
        except MapListBlockError, err:
            self.assertIn('cannot append data', str(err),
                          "expecting error message to contain 'cannot append data' but got %r instead" % err)
        except Exception, err:
            self.fail("expecting MapListBlockError but got %r instead" % err)
        else:
            self.fail("expecting MapListBlockError")

    def test_append_list_with_same_num_words(self):
        data1 = [1, "CustomPL", 3, 'a1', 'a2', 1]
        data2 = [1, "CustomPL", 3, 'b1', 'b2', 2]
        # check both data lists make valid NewMapListBlock individually
        mlb1 = NewMapListBlock(data1)
        self.assertEqual(1, len(mlb1))
        mlb2 = NewMapListBlock(data2)
        self.assertEqual(1, len(mlb2))
        # check both 2nd list can be appended to the 1st one.
        mlb3 = NewMapListBlock(data1)
        mlb3.append(data2)
        # check new list length
        self.assertEqual(len(mlb1) + len(mlb2), len(mlb3))
