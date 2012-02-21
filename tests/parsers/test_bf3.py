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
from copy import copy
import unittest
from mock import Mock
from b3.parsers import bf3
from b3.parsers.bf3 import Bf3Parser
from b3.config import XmlConfigParser
from b3.parsers.frostbite2.util import MapListBlock
from tests import B3TestCase

class BF3TestCase(B3TestCase):
    """
    Test case that is suitable for testing BF3 parser specific features
    """

    @classmethod
    def setUpClass(cls):
        from b3.parsers.frostbite2.abstractParser import AbstractParser
        from b3.fake import FakeConsole
        AbstractParser.__bases__ = (FakeConsole,)
        # Now parser inheritance hierarchy is :
        # BF3Parser -> AbstractParser -> FakeConsole -> Parser


class Test_bf3_config_max_say_line_length(unittest.TestCase):

    MAX_SAY_LINE_LENGTH__DEFAULT = bf3.SAY_LINE_MAX_LENGTH
    MAX_SAY_LINE_LENGTH__MIN = 20
    MAX_SAY_LINE_LENGTH__MAX = bf3.SAY_LINE_MAX_LENGTH

    def setUp(self):
        self.parser = Mock(spec=Bf3Parser)
        self.parser._settings = copy(Bf3Parser._settings)

    def _assert(self, conf_data=None, expected=None):
        self.parser.config = XmlConfigParser()
        self.parser.config.loadFromString("""
            <configuration>
                <settings name="bf3">%s</settings>
            </configuration>
            """ % (('<set name="max_say_line_length">%s</set>' % conf_data) if conf_data is not None else ''))
        Bf3Parser.load_conf_max_say_line_length(self.parser)
        if expected:
            self.assertEqual(expected, self.parser._settings['line_length'])


    def test_max_say_line_length__None(self):
        self._assert(conf_data=None, expected=self.MAX_SAY_LINE_LENGTH__DEFAULT)

    def test_max_say_line_length__empty(self):
        self._assert(conf_data='', expected=self.MAX_SAY_LINE_LENGTH__DEFAULT)

    def test_max_say_line_length__nan(self):
        self._assert(conf_data='foo', expected=self.MAX_SAY_LINE_LENGTH__DEFAULT)

    def test_max_say_line_length__too_low(self):
        self._assert(conf_data=self.MAX_SAY_LINE_LENGTH__MIN - 1, expected=self.MAX_SAY_LINE_LENGTH__MIN)

    def test_max_say_line_length__lowest(self):
        self._assert(conf_data=self.MAX_SAY_LINE_LENGTH__MIN, expected=self.MAX_SAY_LINE_LENGTH__MIN)

    def test_max_say_line_length__25(self):
        self._assert(conf_data='25', expected=25)

    def test_max_say_line_length__highest(self):
        self._assert(conf_data=self.MAX_SAY_LINE_LENGTH__MAX, expected=self.MAX_SAY_LINE_LENGTH__MAX)

    def test_max_say_line_length__too_high(self):
        self._assert(conf_data=self.MAX_SAY_LINE_LENGTH__MAX+1, expected=self.MAX_SAY_LINE_LENGTH__MAX)


class Test_bf3_config_message_delay(unittest.TestCase):
    MESSAGE_DELAY__DEFAULT = .8
    MESSAGE_DELAY__MIN = .5
    MESSAGE_DELAY__MAX = 3

    def setUp(self):
        self.parser = Mock(spec=Bf3Parser)
        self.parser._settings = copy(Bf3Parser._settings)

    def _test_message_delay(self, conf_data=None, expected=None):
        self.parser.config = XmlConfigParser()
        self.parser.config.loadFromString("""
            <configuration>
                <settings name="bf3">%s</settings>
            </configuration>
            """ % (('<set name="message_delay">%s</set>' % conf_data) if conf_data is not None else ''))
        Bf3Parser.load_config_message_delay(self.parser)
        if expected:
            self.assertEqual(expected, self.parser._settings['message_delay'])


    def test_message_delay__None(self):
        self._test_message_delay(conf_data=None, expected=self.MESSAGE_DELAY__DEFAULT)

    def test_message_delay__empty(self):
        self._test_message_delay(conf_data='', expected=self.MESSAGE_DELAY__DEFAULT)

    def test_message_delay__nan(self):
        self._test_message_delay(conf_data='foo', expected=self.MESSAGE_DELAY__DEFAULT)

    def test_message_delay__too_low(self):
        self._test_message_delay(conf_data=self.MESSAGE_DELAY__MIN-.1, expected=self.MESSAGE_DELAY__MIN)

    def test_message_delay__minimum(self):
        self._test_message_delay(conf_data=self.MESSAGE_DELAY__MIN, expected=self.MESSAGE_DELAY__MIN)

    def test_message_delay__2(self):
        self._test_message_delay(conf_data='2', expected=2)

    def test_message_delay__maximum(self):
        self._test_message_delay(conf_data=self.MESSAGE_DELAY__MAX, expected=self.MESSAGE_DELAY__MAX)

    def test_message_delay__too_high(self):
        self._test_message_delay(conf_data=self.MESSAGE_DELAY__MAX+1, expected=self.MESSAGE_DELAY__MAX)






class Test_getServerInfo(unittest.TestCase):

    def test_decodeServerinfo_pre_R9(self):
        self.assertDictContainsSubset({
            'serverName': 'BigBrotherBot #2',
            'numPlayers': '0',
            'maxPlayers': '16',
            'gamemode': 'ConquestLarge0',
            'level': 'MP_012',
            'roundsPlayed': '0',
            'roundsTotal': '2',
            'numTeams': '0',
            'team1score': None,
            'team2score': None,
            'team3score': None,
            'team4score': None,
            'targetScore': '0',
            'onlineState': '',
            'isRanked': 'true',
            'hasPunkbuster': 'true',
            'hasPassword': 'false',
            'serverUptime': '5148',
            'roundTime': '455',
        }, Bf3Parser.decodeServerinfo(('BigBrotherBot #2', '0', '16', 'ConquestLarge0', 'MP_012', '0', '2', '0', '0', '', 'true', 'true', 'false', '5148', '455')))

        self.assertDictContainsSubset({
            'serverName': 'BigBrotherBot #2',
            'numPlayers': '0',
            'maxPlayers': '16',
            'gamemode': 'ConquestLarge0',
            'level': 'MP_012',
            'roundsPlayed': '0',
            'roundsTotal': '2',
            'numTeams': '1',
            'team1score': '47',
            'team2score': None,
            'team3score': None,
            'team4score': None,
            'targetScore': '0',
            'onlineState': '',
            'isRanked': 'true',
            'hasPunkbuster': 'true',
            'hasPassword': 'false',
            'serverUptime': '5148',
            'roundTime': '455',
        }, Bf3Parser.decodeServerinfo(('BigBrotherBot #2', '0', '16', 'ConquestLarge0', 'MP_012', '0', '2', '1', '47', '0', '', 'true', 'true', 'false', '5148', '455')))

        self.assertDictContainsSubset({
            'serverName': 'BigBrotherBot #2',
            'numPlayers': '0',
            'maxPlayers': '16',
            'gamemode': 'ConquestLarge0',
            'level': 'MP_012',
            'roundsPlayed': '0',
            'roundsTotal': '2',
            'numTeams': '2',
            'team1score': '300',
            'team2score': '300',
            'team3score': None,
            'team4score': None,
            'targetScore': '0',
            'onlineState': '',
            'isRanked': 'true',
            'hasPunkbuster': 'true',
            'hasPassword': 'false',
            'serverUptime': '5148',
            'roundTime': '455',
        }, Bf3Parser.decodeServerinfo(('BigBrotherBot #2', '0', '16', 'ConquestLarge0', 'MP_012', '0', '2', '2', '300', '300', '0', '', 'true', 'true', 'false', '5148', '455')))

        self.assertDictContainsSubset({
            'serverName': 'BigBrotherBot #2',
            'numPlayers': '0',
            'maxPlayers': '16',
            'gamemode': 'ConquestLarge0',
            'level': 'MP_012',
            'roundsPlayed': '1',
            'roundsTotal': '2',
            'numTeams': '3',
            'team1score': '300',
            'team2score': '215',
            'team3score': '25',
            'team4score': None,
            'targetScore': '0',
            'onlineState': '',
            'isRanked': 'true',
            'hasPunkbuster': 'true',
            'hasPassword': 'false',
            'serverUptime': '5148',
            'roundTime': '455',
        }, Bf3Parser.decodeServerinfo(('BigBrotherBot #2', '0', '16', 'ConquestLarge0', 'MP_012', '1', '2', '3', '300', '215', '25', '0', '', 'true', 'true', 'false', '5148', '455')))

        self.assertDictContainsSubset({
            'serverName': 'BigBrotherBot #2',
            'numPlayers': '0',
            'maxPlayers': '16',
            'gamemode': 'ConquestLarge0',
            'level': 'MP_012',
            'roundsPlayed': '1',
            'roundsTotal': '2',
            'numTeams': '4',
            'team1score': '300',
            'team2score': '215',
            'team3score': '25',
            'team4score': '84',
            'targetScore': '0',
            'onlineState': '',
            'isRanked': 'true',
            'hasPunkbuster': 'true',
            'hasPassword': 'false',
            'serverUptime': '5148',
            'roundTime': '455',
        }, Bf3Parser.decodeServerinfo(('BigBrotherBot #2', '0', '16', 'ConquestLarge0', 'MP_012', '1', '2', '4', '300', '215', '25', '84', '0', '', 'true', 'true', 'false', '5148', '455')))

    def test_decodeServerinfo_R9(self):
        self.maxDiff = None
        self.assertDictEqual({
            'serverName': 'BigBrotherBot #2',
            'numPlayers': '0',
            'maxPlayers': '16',
            'gamemode': 'ConquestLarge0',
            'level': 'MP_012',
            'roundsPlayed': '0',
            'roundsTotal': '2',
            'numTeams': '0',
            'team1score': None,
            'team2score': None,
            'team3score': None,
            'team4score': None,
            'targetScore': '0',
            'onlineState': '',
            'isRanked': 'true',
            'hasPunkbuster': 'true',
            'hasPassword': 'false',
            'serverUptime': '5148',
            'roundTime': '455',
            'gameIpAndPort': '1.2.3.4:5445',
            'punkBusterVersion': '1.5',
            'joinQueueEnabled': 'false',
            'region': 'EU',
            'closestPingSite': '45',
            'country': 'FR',
        }, Bf3Parser.decodeServerinfo(('BigBrotherBot #2', '0', '16', 'ConquestLarge0', 'MP_012', '0', '2', '0', '0', '', 'true', 'true', 'false', '5148', '455', '1.2.3.4:5445', '1.5', 'false', 'EU', '45', 'FR')))

        self.assertDictEqual({
            'serverName': 'BigBrotherBot #2',
            'numPlayers': '0',
            'maxPlayers': '16',
            'gamemode': 'ConquestLarge0',
            'level': 'MP_012',
            'roundsPlayed': '0',
            'roundsTotal': '2',
            'numTeams': '1',
            'team1score': '47',
            'team2score': None,
            'team3score': None,
            'team4score': None,
            'targetScore': '0',
            'onlineState': '',
            'isRanked': 'true',
            'hasPunkbuster': 'true',
            'hasPassword': 'false',
            'serverUptime': '5148',
            'roundTime': '455',
            'gameIpAndPort': '1.2.3.4:5445',
            'punkBusterVersion': '1.5',
            'joinQueueEnabled': 'false',
            'region': 'EU',
            'closestPingSite': '45',
            'country': 'FR',
        }, Bf3Parser.decodeServerinfo(('BigBrotherBot #2', '0', '16', 'ConquestLarge0', 'MP_012', '0', '2', '1', '47', '0', '', 'true', 'true', 'false', '5148', '455', '1.2.3.4:5445', '1.5', 'false', 'EU', '45', 'FR')))

        self.assertDictEqual({
            'serverName': 'BigBrotherBot #2',
            'numPlayers': '0',
            'maxPlayers': '16',
            'gamemode': 'ConquestLarge0',
            'level': 'MP_012',
            'roundsPlayed': '0',
            'roundsTotal': '2',
            'numTeams': '2',
            'team1score': '300',
            'team2score': '300',
            'team3score': None,
            'team4score': None,
            'targetScore': '0',
            'onlineState': '',
            'isRanked': 'true',
            'hasPunkbuster': 'true',
            'hasPassword': 'false',
            'serverUptime': '5148',
            'roundTime': '455',
            'gameIpAndPort': '1.2.3.4:5445',
            'punkBusterVersion': '1.5',
            'joinQueueEnabled': 'false',
            'region': 'EU',
            'closestPingSite': '45',
            'country': 'FR',
        }, Bf3Parser.decodeServerinfo(('BigBrotherBot #2', '0', '16', 'ConquestLarge0', 'MP_012', '0', '2', '2', '300', '300', '0', '', 'true', 'true', 'false', '5148', '455', '1.2.3.4:5445', '1.5', 'false', 'EU', '45', 'FR')))

        self.assertDictEqual({
            'serverName': 'BigBrotherBot #2',
            'numPlayers': '0',
            'maxPlayers': '16',
            'gamemode': 'ConquestLarge0',
            'level': 'MP_012',
            'roundsPlayed': '1',
            'roundsTotal': '2',
            'numTeams': '3',
            'team1score': '300',
            'team2score': '215',
            'team3score': '25',
            'team4score': None,
            'targetScore': '0',
            'onlineState': '',
            'isRanked': 'true',
            'hasPunkbuster': 'true',
            'hasPassword': 'false',
            'serverUptime': '5148',
            'roundTime': '455',
            'gameIpAndPort': '1.2.3.4:5445',
            'punkBusterVersion': '1.5',
            'joinQueueEnabled': 'false',
            'region': 'EU',
            'closestPingSite': '45',
            'country': 'FR',
        }, Bf3Parser.decodeServerinfo(('BigBrotherBot #2', '0', '16', 'ConquestLarge0', 'MP_012', '1', '2', '3', '300', '215', '25', '0', '', 'true', 'true', 'false', '5148', '455', '1.2.3.4:5445', '1.5', 'false', 'EU', '45', 'FR')))

        self.assertDictEqual({
            'serverName': 'BigBrotherBot #2',
            'numPlayers': '0',
            'maxPlayers': '16',
            'gamemode': 'ConquestLarge0',
            'level': 'MP_012',
            'roundsPlayed': '1',
            'roundsTotal': '2',
            'numTeams': '4',
            'team1score': '300',
            'team2score': '215',
            'team3score': '25',
            'team4score': '84',
            'targetScore': '0',
            'onlineState': '',
            'isRanked': 'true',
            'hasPunkbuster': 'true',
            'hasPassword': 'false',
            'serverUptime': '5148',
            'roundTime': '455',
            'gameIpAndPort': '1.2.3.4:5445',
            'punkBusterVersion': '1.5',
            'joinQueueEnabled': 'false',
            'region': 'EU',
            'closestPingSite': '45',
            'country': 'FR',
        }, Bf3Parser.decodeServerinfo(('BigBrotherBot #2', '0', '16', 'ConquestLarge0', 'MP_012', '1', '2', '4', '300', '215', '25', '84', '0', '', 'true', 'true', 'false', '5148', '455', '1.2.3.4:5445', '1.5', 'false', 'EU', '45', 'FR')))

    def test_getServerInfo_pre_R9(self):
        self.maxDiff = None
        bf3_response = ('BigBrotherBot #2', '0', '16', 'ConquestLarge0', 'MP_012', '1', '2',
                                  '4', '300', '215', '25', '84',
                                  '0', '', 'true', 'true', 'false', '5148', '455')
        parser = Mock(spec=Bf3Parser)
        parser.write = lambda x: bf3_response

        data = Bf3Parser.getServerInfo(parser)
        self.assertEqual(bf3_response, data)
        self.assertEqual(parser.game.sv_hostname, 'BigBrotherBot #2')
        self.assertEqual(parser.game.sv_maxclients, 16)
        self.assertEqual(parser.game.gameType, 'ConquestLarge0')
        self.assertFalse(parser._publicIp.called)
        self.assertFalse(parser._port.called)

        self.assertEqual({
            'serverName': 'BigBrotherBot #2',
            'numPlayers': '0',
            'maxPlayers': '16',
            'gamemode': 'ConquestLarge0',
            'level': 'MP_012',
            'roundsPlayed': '1',
            'roundsTotal': '2',
            'numTeams': '4',
            'team1score': '300',
            'team2score': '215',
            'team3score': '25',
            'team4score': '84',
            'targetScore': '0',
            'onlineState': '',
            'isRanked': 'true',
            'hasPunkbuster': 'true',
            'hasPassword': 'false',
            'serverUptime': '5148',
            'roundTime': '455',
            'gameIpAndPort': None,
            'punkBusterVersion': None,
            'joinQueueEnabled': None,
            'region': None,
            'closestPingSite': None,
            'country': None,
        }, parser.game.serverinfo)

    def test_getServerInfo_R9(self):

        bf3_response = ['i3D.net - BigBrotherBot #3 (FR)', '0', '16', 'SquadDeathMatch0', 'MP_013',
                        '0', '1','4', '0', '0', '0', '0', '50', '', 'true', 'true', 'false', '92480',
                        '4832', '4.5.6.7:542', '', '', 'EU', 'ams', 'DE']
        parser = Mock(spec=Bf3Parser)
        parser.write = lambda x: bf3_response

        data = Bf3Parser.getServerInfo(parser)
        self.assertEqual(bf3_response, data)
        self.assertEqual(parser.game.sv_hostname, 'i3D.net - BigBrotherBot #3 (FR)')
        self.assertEqual(parser.game.sv_maxclients, 16)
        self.assertEqual(parser.game.gameType, 'SquadDeathMatch0')
        self.assertEqual(parser._publicIp, '4.5.6.7')
        self.assertEqual(parser._gamePort, '542')
        self.assertEqual({
            'serverName': 'i3D.net - BigBrotherBot #3 (FR)',
            'numPlayers': '0',
            'maxPlayers': '16',
            'gamemode': 'SquadDeathMatch0',
            'level': 'MP_013',
            'roundsPlayed': '0',
            'roundsTotal': '1',
            'numTeams': '4',
            'team1score': '0',
            'team2score': '0',
            'team3score': '0',
            'team4score': '0',
            'targetScore': '50',
            'onlineState': '',
            'isRanked': 'true',
            'hasPunkbuster': 'true',
            'hasPassword': 'false',
            'serverUptime': '92480',
            'roundTime': '4832',
            'gameIpAndPort': '4.5.6.7:542',
            'punkBusterVersion': '',
            'joinQueueEnabled': '',
            'region': 'EU',
            'closestPingSite': 'ams',
            'country': 'DE',
        }, parser.game.serverinfo)



class Test_bf3_events(BF3TestCase):

    def setUp(self):
        self.conf = XmlConfigParser()
        self.conf.loadFromString("""
                <configuration>
                </configuration>
            """)
        self.parser = Bf3Parser(self.conf)
        self.parser.startup()

    def test_cmd_rotateMap_generates_EVT_GAME_ROUND_END(self):
        # prepare fake BF3 server responses
        def fake_write(data):
            if data ==  ('mapList.getMapIndices', ):
                return [0, 1]
            else:
                return []
        self.parser.write = Mock(side_effect=fake_write)
        self.parser.getFullMapRotationList = Mock(return_value=MapListBlock(['4', '3', 'MP_007', 'RushLarge0', '4', 'MP_011', 'RushLarge0', '4', 'MP_012',
                                                                             'SquadRush0', '4', 'MP_013', 'SquadRush0', '4']))

        # mock parser queueEvent method so we can make assertions on it later on
        self.parser.queueEvent = Mock(name="queueEvent method")

        self.parser.rotateMap()
        self.assertEqual(1, self.parser.queueEvent.call_count)
        self.assertEqual(self.parser.getEventID("EVT_GAME_ROUND_END"), self.parser.queueEvent.call_args[0][0].type)
        self.assertIsNone(self.parser.queueEvent.call_args[0][0].data)



class Test_punkbuster_events(BF3TestCase):

    def setUp(self):
        self.conf = XmlConfigParser()
        self.conf.loadFromString("""
                <configuration>
                </configuration>
            """)
        self.parser = Bf3Parser(self.conf)
        self.parser.startup()

    def pb(self, msg):
        return self.parser.OnPunkbusterMessage(action=None, data=[msg])

    def assert_pb_misc_evt(self, msg):
        assert str(self.pb(msg)).startswith('Event<PunkBuster misc>')

    def test_PB_SV_BanList(self):
        self.assert_pb_misc_evt('PunkBuster Server: 1   b59ffffffffffffffffffffffffffc7d {13/15} "Cucurbitaceae" "87.45.14.2:3659" retest" ""')
        self.assert_pb_misc_evt('PunkBuster Server: 1   b59ffffffffffffffffffffffffffc7d {0/1440} "Cucurbitaceae" "87.45.14.2:3659" mlkjsqfd" ""')

        self.assertEquals(
            '''Event<PunkBuster unknown>(['PunkBuster Server: 1   (UnBanned) b59ffffffffffffffffffffffffffc7d {15/15} "Cucurbitaceae" "87.45.14.2:3659" retest" ""'], None, None)''',
            str(self.pb('PunkBuster Server: 1   (UnBanned) b59ffffffffffffffffffffffffffc7d {15/15} "Cucurbitaceae" "87.45.14.2:3659" retest" ""')))

        self.assert_pb_misc_evt('PunkBuster Server: Guid=b59ffffffffffffffffffffffffffc7d" Not Found in the Ban List')
        self.assert_pb_misc_evt('PunkBuster Server: End of Ban List (1 of 1 displayed)')

    def test_PB_UCON_message(self):
        result = self.pb('PunkBuster Server: PB UCON "ggc_85.214.107.154"@85.214.107.154:14516 [admin.say "GGC-Stream.com - Welcome Cucurbitaceae with the GUID 31077c7d to our server." all]\n')
        self.assertEqual('Event<PunkBuster UCON>({\'ip\': \'85.214.107.154\', \'cmd\': \'admin.say "GGC-Stream.com - Welcome Cucurbitaceae with the GUID 31077c7d to our server." all\', \'from\': \'ggc_85.214.107.154\', \'port\': \'14516\'}, None, None)', str(result))

    def test_PB_Screenshot_received_message(self):
        result = self.pb('PunkBuster Server: Screenshot C:\\games\\bf3\\173_199_73_213_25200\\862147\\bf3\\pb\\svss\\pb000709.png successfully received (MD5=4576546546546546546546546543E1E1) from 19 Jaffar [da876546546546546546546546547673(-) 111.22.33.111:3659]\n')
        self.assertEqual(r"Event<PunkBuster Screenshot received>({'slot': '19', 'name': 'Jaffar', 'ip': '111.22.33.111', 'pbid': 'da876546546546546546546546547673', 'imgpath': 'C:\\games\\bf3\\173_199_73_213_25200\\862147\\bf3\\pb\\svss\\pb000709.png', 'port': '3659', 'md5': '4576546546546546546546546543E1E1'}, None, None)", str(result))

    def test_PB_SV_PList(self):
        self.assert_pb_misc_evt("PunkBuster Server: Player List: [Slot #] [GUID] [Address] [Status] [Power] [Auth Rate] [Recent SS] [O/S] [Name]")
        self.assert_pb_misc_evt('PunkBuster Server: End of Player List (0 Players)')

    def test_PB_Ver(self):
        self.assertIsNone(self.pb('PunkBuster Server: PunkBuster Server for BF3 (v1.839 | A1386 C2.279) Enabled\n'))

    def test_PB_SV_BanGuid(self):
        self.assert_pb_misc_evt('PunkBuster Server: Ban Added to Ban List')
        self.assert_pb_misc_evt('PunkBuster Server: Ban Failed')

    def test_PB_SV_UnBanGuid(self):
        self.assert_pb_misc_evt('PunkBuster Server: Guid b59f190e5ef725e06531387231077c7d has been Unbanned')

    def test_PB_SV_UpdBanFile(self):
        self.assert_pb_misc_evt("PunkBuster Server: 0 Ban Records Updated in d:\\localuser\\g119142\\pb\\pbbans.dat")

    def test_misc(self):
        self.assertEqual("Event<PunkBuster client connection lost>({'slot': '1', 'ip': 'x.x.x.x', 'port': '3659', 'name': 'joe', 'pbuid': '0837c128293d42aaaaaaaaaaaaaaaaa'}, None, None)",
            str(self.pb("PunkBuster Server: Lost Connection (slot #1) x.x.x.x:3659 0837c128293d42aaaaaaaaaaaaaaaaa(-) joe")))

        self.assert_pb_misc_evt("PunkBuster Server: Invalid Player Specified: None")
        self.assert_pb_misc_evt("PunkBuster Server: Matched: Cucurbitaceae (slot #1)")
        self.assert_pb_misc_evt("PunkBuster Server: Received Master Security Information")
        self.assert_pb_misc_evt("PunkBuster Server: Auto Screenshot 000714 Requested from 25 Goldbat")