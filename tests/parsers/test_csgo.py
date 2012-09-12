# coding=UTF-8
#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2012 Courgette
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
from mock import Mock, call, patch
from mockito import when, verify
import unittest2 as unittest
from b3 import TEAM_BLUE, TEAM_RED, TEAM_UNKNOWN
from b3.clients import Client
from b3.config import XmlConfigParser
from b3.fake import FakeClient
from b3.parsers.csgo import CsgoParser


STATUS_RESPONSE = '''\
hostname: Courgette's Server
version : 1.17.5.1/11751 5038 secure
udp/ip  : 11.23.32.44:27015  (public ip: 11.23.32.44)
os      :  Linux
type    :  community dedicated
map     : cs_foobar
players : 1 humans, 10 bots (20/20 max) (not hibernating)

# userid name uniqueid connected ping loss state rate adr
#224 "Moe" BOT active
# 194 2 "courgette" STEAM_1:0:1111111 33:48 67 0 active 20000 11.222.111.222:27005
#225 "Quintin" BOT active
#226 "Kurt" BOT active
#227 "Arnold" BOT active
#228 "Rip" BOT active
#229 "Zach" BOT active
#230 "Wolf" BOT active
#231 "Minh" BOT active
#232 "Ringo" BOT active
#233 "Quade" BOT active
#end
L 08/28/2012 - 01:28:40: rcon from "11.222.111.222:4181": command "status"
'''


def client_equal(client_a, client_b):
    if client_a is None and client_b is not None:
        return False
    if client_a is not None and client_b is None:
        return False
#    for p in ('cid', 'guid', 'name', 'ip', 'ping'):
#        if client_a.get(p, None) != client_b.get(p, None):
#            return False
    return all(map(lambda x: getattr(client_a, x, None) == getattr(client_b, x, None), ('cid', 'guid', 'name', 'ip', 'ping')))
#    return True


class CsgoTestCase(unittest.TestCase):
    """
    Test case that is suitable for testing CS:GO parser specific features
    """

    @classmethod
    def setUpClass(cls):
        from b3.fake import FakeConsole
        CsgoParser.__bases__ = (FakeConsole,)
        # Now parser inheritance hierarchy is :
        # CsgoParser -> FakeConsole -> Parser


    def setUp(self):
        self.status_response = None # defaults to STATUS_RESPONSE module attribute
        self.conf = XmlConfigParser()
        self.conf.loadFromString("""<configuration></configuration>""")
        self.parser = CsgoParser(self.conf)
        self.parser.output = Mock()
        self.parser.output.write = Mock(wraps=self.output_write)

        self.evt_queue = []
        def queue_event(evt):
            self.evt_queue.append(evt)
        self.queueEvent_patcher = patch.object(self.parser, "queueEvent", wraps=queue_event)
        self.queueEvent_mock = self.queueEvent_patcher.start()

        self.parser.startup()


    def tearDown(self):
        self.queueEvent_patcher.stop()
        if hasattr(self, "parser"):
            self.parser.working = False


    def clear_events(self):
        """
        clear the event queue, so when assert_has_event is called, it will look only at the newly caught events.
        """
        self.evt_queue = []


    def assert_has_event(self, event_type, data=None, client=None, target=None):
        """
        assert that self.evt_queue contains at least one event for the given type that has the given characteristics.
        """
        assert isinstance(event_type, basestring)
        expected_event = self.parser.getEvent(event_type, data, client, target)

        if not len(self.evt_queue):
            self.fail("expecting %s. Got no event instead" % expected_event)
        elif len(self.evt_queue) == 1:
            actual_event = self.evt_queue[0]
            self.assertEqual(expected_event.type, actual_event.type)
            self.assertEqual(expected_event.data, actual_event.data)
            self.assertTrue(client_equal(expected_event.client, actual_event.client))
            self.assertTrue(client_equal(expected_event.target, actual_event.target))
        else:
            for evt in self.evt_queue:
                if expected_event.type == evt.type \
                    and expected_event.data == evt.data \
                    and client_equal(expected_event.client, evt.client) \
                    and client_equal(expected_event.target, evt.target):
                    return

            self.fail("expecting event %s. Got instead: %s" % (expected_event, map(str, self.evt_queue)))


    def output_write(self, *args, **kwargs):
        """Used to override parser self.output.write method so we can control the response given to the 'status'
        rcon command"""
        if len(args) and args[0] == "status":
            if self.status_response is not None:
                return self.status_response
            else:
                return STATUS_RESPONSE



class Test_gamelog_parsing(CsgoTestCase):

    def test_server_cvars_start(self):
        self.queueEvent_mock.reset_mock()
        self.parser.parseLine("""L 08/26/2012 - 05:46:50: server cvars start""")
        self.assertFalse(self.queueEvent_mock.called)


    def test_server_cvars_end(self):
        self.queueEvent_mock.reset_mock()
        self.parser.parseLine("""L 08/26/2012 - 05:46:50: server cvars end""")
        self.assertFalse(self.queueEvent_mock.called)


    def test_killed(self):
        # GIVEN
        bot22 = FakeClient(self.parser, name="Pheonix", guid="BOT_22")
        bot17 = FakeClient(self.parser, name="Ringo", guid="BOT_17")
        bot22.connects("22")
        bot17.connects("17")

        # WHEN
        self.clear_events()
        self.parser.parseLine('''L 08/26/2012 - 03:46:44: "Pheonix<22><BOT><TERRORIST>" killed "Ringo<17><BOT><CT>" with "glock" (headshot)''')
        # THEN
        self.assert_has_event("EVT_CLIENT_KILL", client=bot22, target=bot17, data=(100, 'glock', 'head', None))

        # WHEN
        self.clear_events()
        self.parser.parseLine('''L 08/26/2012 - 03:46:44: "Pheonix<22><BOT><TERRORIST>" killed "Ringo<17><BOT><CT>" with "glock"''')
        # THEN
        self.assert_has_event("EVT_CLIENT_KILL", client=bot22, target=bot17, data=(100, 'glock', 'body', None))


    def test_killed_but_really_is_teamkill(self):
        # GIVEN
        bot22 = FakeClient(self.parser, name="Pheonix", guid="BOT_22")
        bot17 = FakeClient(self.parser, name="Ringo", guid="BOT_17")
        bot22.connects("22")
        bot17.connects("17")
        # WHEN
        self.clear_events()
        self.parser.parseLine('''L 08/26/2012 - 03:46:44: "Pheonix<22><BOT><TERRORIST>" killed "Ringo<17><BOT><TERRORIST>" with "glock"''')
        # THEN
        self.assert_has_event("EVT_CLIENT_KILL_TEAM", client=bot22, target=bot17, data=(100, 'glock', 'body', None))


    def test_killed_but_really_is_suicide(self):
        # GIVEN
        bot22 = FakeClient(self.parser, name="Pheonix", guid="BOT_22")
        bot22.connects("22")
        # WHEN
        self.clear_events()
        self.parser.parseLine('''L 08/26/2012 - 03:46:44: "Pheonix<22><BOT><TERRORIST>" killed "Pheonix<22><BOT><TERRORIST>" with "glock"''')
        # THEN
        self.assert_has_event("EVT_CLIENT_SUICIDE", client=bot22, target=bot22, data=(100, 'glock', 'body', None))


    def test_committed_suicide(self):
        # GIVEN
        bot22 = FakeClient(self.parser, name="Pheonix", guid="BOT_22")
        bot22.connects("22")
        # WHEN
        self.clear_events()
        self.parser.parseLine('''L 08/26/2012 - 03:38:04: "Pheonix<22><BOT><TERRORIST>" committed suicide with "world"''')
        # THEN
        self.assert_has_event("EVT_CLIENT_SUICIDE", client=bot22, target=bot22, data=(100, 'world', 'body', None))



    def test_server_cvar(self):
        # GIVEN
        self.parser.game.cvar = {}
        # WHEN
        self.parser.parseLine('''L 08/26/2012 - 03:49:58: server_cvar: "mp_freezetime" "5"''')
        # THEN
        self.assertDictEqual({'mp_freezetime': "5"}, self.parser.game.cvar)


    def test_cvar(self):
        # GIVEN
        self.parser.game.cvar = {}
        # WHEN
        self.parser.parseLine('''L 08/26/2012 - 03:49:56: "decalfrequency" = "10"''')
        # THEN
        self.assertDictEqual({'decalfrequency': "10"}, self.parser.game.cvar)


    def test_map_change(self):
        # GIVEN
        self.parser.game.mapName = "old"
        # WHEN
        self.parser.parseLine('''L 08/27/2012 - 23:57:14: -------- Mapchange to de_dust --------''')
        # THEN
        self.assertEqual("de_dust", self.parser.game.mapName)


    def test_loading_map(self):
        # GIVEN
        self.parser.game.mapName = "old"
        # WHEN
        self.parser.parseLine('''L 08/26/2012 - 03:49:56: Loading map "de_nuke"''')
        # THEN
        self.assertEqual("de_nuke", self.parser.game.mapName)


    def test_started_map(self):
        # GIVEN
        self.parser.game.mapName = "old"
        # WHEN
        self.parser.parseLine('''L 08/26/2012 - 03:22:35: Started map "de_dust" (CRC "1592693790")''')
        # THEN
        self.assertEqual("de_dust", self.parser.game.mapName)


    def test_userid_validated(self):
        # GIVEN
        self.assertIsNone(self.parser.clients.getByCID("2"))
        # WHEN
        self.parser.parseLine('''L 08/26/2012 - 03:22:36: "courgette<2><STEAM_1:0:1111111><>" STEAM USERID validated''')
        # THEN
        client = self.parser.clients.getByCID("2")
        self.assertIsNotNone(client)
        self.assertEqual("courgette", client.name)
        self.assertEqual("STEAM_1:0:1111111", client.guid)
        self.assert_has_event("EVT_CLIENT_CONNECT", data=client, client=client)
        self.assert_has_event("EVT_CLIENT_AUTH", data=client, client=client)


    def test_player_connected(self):
        # GIVEN
        self.assertIsNone(self.parser.clients.getByCID("2"))
        # WHEN
        self.clear_events()
        self.parser.parseLine('''L 08/26/2012 - 03:22:36: "courgette<2><STEAM_1:0:1111111><>" connected, address "11.222.111.222:27005"''')
        # THEN
        client = self.parser.clients.getByCID("2")
        self.assertIsNotNone(client)
        self.assertEqual("courgette", client.name)
        self.assertEqual("STEAM_1:0:1111111", client.guid)
        self.assertEqual("11.222.111.222", client.ip)
        self.assert_has_event("EVT_CLIENT_CONNECT", data=client, client=client)
        self.assert_has_event("EVT_CLIENT_AUTH", data=client, client=client)


    def test_player_connected__unicode(self):
        # GIVEN
        self.assertIsNone(self.parser.clients.getByCID("2"))
        # WHEN
        self.clear_events()
        self.parser.parseLine(b'''L 08/26/2012 - 03:22:36: "Spoon\xc2\xab\xc2\xab<2><STEAM_1:0:1111111><>" connected, address "11.222.111.222:27005"''')
        # THEN
        client = self.parser.clients.getByCID("2")
        self.assertIsNotNone(client)
        self.assertEqual(u"Spoon««", client.name)
        self.assertEqual("STEAM_1:0:1111111", client.guid)
        self.assertEqual("11.222.111.222", client.ip)
        self.assert_has_event("EVT_CLIENT_CONNECT", data=client, client=client)
        self.assert_has_event("EVT_CLIENT_AUTH", data=client, client=client)


    def test_bot_connected(self):
        # GIVEN
        self.assertIsNone(self.parser.clients.getByCID("3"))
        # WHEN
        self.clear_events()
        self.parser.parseLine('''L 08/26/2012 - 03:22:36: "Moe<3><BOT><>" connected, address "none"''')
        # THEN
        client = self.parser.clients.getByCID("3")
        self.assertIsNotNone(client)
        self.assertEqual("Moe", client.name)
        self.assertEqual("BOT_3", client.guid)
        self.assertEqual("", client.ip)
        self.assert_has_event("EVT_CLIENT_CONNECT", data=client, client=client)
        self.assert_has_event("EVT_CLIENT_AUTH", data=client, client=client)


    def test_kicked_by_console(self):
        # GIVEN
        bot22 = FakeClient(self.parser, name="Pheonix", guid="BOT_22")
        bot22.connects("22")
        # WHEN
        self.clear_events()
        self.parser.parseLine('''L 08/26/2012 - 04:45:04: "Pheonix<22><BOT><TERRORIST>" disconnected (reason "Kicked by Console")''')
        # THEN
        self.assert_has_event("EVT_CLIENT_KICK", data='Kicked by Console', client=bot22)
        self.assert_has_event("EVT_CLIENT_DISCONNECT", data='22', client=bot22)


    def test_player_entered(self):
        # GIVEN
        player = FakeClient(self.parser, name="courgette", guid="STEAM_1:0:1111111")
        player.connects("2")
        # WHEN
        self.clear_events()
        self.parser.parseLine('''L 08/26/2012 - 05:38:36: "courgette<2><STEAM_1:0:1111111><>" entered the game''')
        # THEN
        self.assert_has_event("EVT_CLIENT_JOIN", client=player)


    def test_bot_entered(self):
        # GIVEN
        bot22 = FakeClient(self.parser, name="Pheonix", guid="BOT_22")
        bot22.connects("22")
        # WHEN
        self.clear_events()
        self.parser.parseLine('''L 08/26/2012 - 05:29:48: "Pheonix<22><BOT><>" entered the game''')
        # THEN
        self.assert_has_event("EVT_CLIENT_JOIN", client=bot22)



    def test_player_join_team(self):
        # GIVEN
        player = FakeClient(self.parser, name="courgette", guid="STEAM_1:0:1111111")
        player.connects("2")
        # WHEN
        self.clear_events()
        self.parser.parseLine('''L 08/26/2012 - 03:22:36: "courgette<2><STEAM_1:0:1111111><Unassigned>" joined team "CT"''')
        # THEN
        self.assert_has_event("EVT_CLIENT_TEAM_CHANGE", data=TEAM_RED, client=player)
        self.assertEqual(TEAM_RED, player.team)


    def test_bot_join_team(self):
        # GIVEN
        bot22 = FakeClient(self.parser, name="Pheonix", guid="BOT_11")
        bot22.connects("11")
        # WHEN
        self.clear_events()
        self.parser.parseLine('''L 08/26/2012 - 03:22:36: "Pheonix<11><BOT><Unassigned>" joined team "TERRORIST"''')
        # THEN
        self.assert_has_event("EVT_CLIENT_TEAM_CHANGE", data=TEAM_BLUE, client=bot22)
        self.assertEqual(TEAM_BLUE, bot22.team)


    def test_world_triggered_event__Round_End(self):
        # GIVEN
        # WHEN
        self.clear_events()
        self.parser.parseLine('''L 08/26/2012 - 03:22:36: World triggered "Round_End"''')
        # THEN
        self.assert_has_event("EVT_GAME_ROUND_END")


    def test_world_triggered_event__Round_Start(self):
        # GIVEN
        with patch.object(self.parser.game, "startRound") as startRound_mock:
            # WHEN
            self.assertFalse(startRound_mock.called)
            self.parser.parseLine('''L 08/26/2012 - 03:22:36: World triggered "Round_Start"''')
            # THEN
            self.assertTrue(startRound_mock.called)


    def test_world_triggered_event__Game_Commencing(self):
        # GIVEN
        with patch.object(self.parser, "warning") as warning_mock:
            # WHEN
            self.clear_events()
            self.parser.parseLine('''L 08/26/2012 - 03:22:36: World triggered "Game_Commencing"''')
            # THEN
            self.assertEqual([], self.evt_queue)
            self.assertFalse(warning_mock.called)


    def test_world_triggered_event__killlocation(self):
        # GIVEN
        with patch.object(self.parser, "warning") as warning_mock:
            # WHEN
            self.clear_events()
            self.assertIsNone(self.parser.last_killlocation_properties)
            self.parser.parseLine('''L 08/29/2012 - 22:26:59: World triggered "killlocation" (attacker_position "-282 749 -21") (victim_position "68 528 64")''')
            # THEN
            self.assertEqual([], self.evt_queue)
            self.assertEqual(''' (attacker_position "-282 749 -21") (victim_position "68 528 64")''', self.parser.last_killlocation_properties)
            self.assertFalse(warning_mock.called)


    def test_world_triggered_event__unknown_event(self):
        # GIVEN
        with patch.object(self.parser, "warning") as warning_mock:
            # WHEN
            self.clear_events()
            self.parser.parseLine('''L 08/26/2012 - 03:22:36: World triggered "f00"''')
            # THEN
            self.assertEqual([], self.evt_queue)
            self.assertTrue(warning_mock.called)
            warning_mock.assert_has_calls([call("unexpected world event : 'f00'. Please report this on the B3 forums")])


    def test_client_triggered_event__known(self):
        # GIVEN
        player = FakeClient(self.parser, name="courgette", guid="STEAM_1:0:1111111")
        player.connects("2")

        def assertEvent(event_name):
            # WHEN
            self.clear_events()
            self.parser.parseLine('''L 08/26/2012 - 05:04:55: "courgette<2><STEAM_1:0:1111111><CT>" triggered "%s"''' % event_name)
            # THEN
            self.assert_has_event("EVT_CLIENT_ACTION", data=event_name, client=player)

        assertEvent("Got_The_Bomb")
        assertEvent("Dropped_The_Bomb")
        assertEvent("Begin_Bomb_Defuse_Without_Kit")
        assertEvent("Planted_The_Bomb")
        assertEvent("headshot")


    def test_client_triggered_event__unknown(self):
        # GIVEN
        player = FakeClient(self.parser, name="courgette", guid="STEAM_1:0:1111111", team=TEAM_RED)
        player.connects("2")

        with patch.object(self.parser, "warning") as warning_mock:
            # WHEN
            self.clear_events()
            self.parser.parseLine('''L 08/26/2012 - 05:04:55: "courgette<2><STEAM_1:0:1111111><CT>" triggered "f00"''')
            # THEN
            self.assertEqual([], self.evt_queue)
            self.assertTrue(warning_mock.called)
            warning_mock.assert_has_calls([call("unknown client event : 'f00'. Please report this on the B3 forums")])


    def test_team_triggered_event__known(self):
        def assert_unknown_event_warning_called(event_name, expect_unknown=True):
            with patch.object(self.parser, "warning") as warning_mock:
                # WHEN
                self.clear_events()
                self.parser.parseLine('''L 08/26/2012 - 03:48:09: Team "CT" triggered "%s" (CT "3") (T "5")''' % event_name)
                # THEN
            self.assertEqual([], self.evt_queue)
            self.assertEqual(expect_unknown, warning_mock.called, warning_mock.mock_calls)
            if expect_unknown:
                warning_mock.assert_has_calls([call("unexpected team event : '%s'. Please report this on the B3 forums" % event_name)])

        assert_unknown_event_warning_called("bar")
        assert_unknown_event_warning_called("SFUI_Notice_Target_Saved", expect_unknown=False)
        assert_unknown_event_warning_called("SFUI_Notice_Target_Bombed", expect_unknown=False)
        assert_unknown_event_warning_called("SFUI_Notice_Terrorists_Win", expect_unknown=False)
        assert_unknown_event_warning_called("SFUI_Notice_CTs_Win", expect_unknown=False)
        assert_unknown_event_warning_called("SFUI_Notice_Bomb_Defused", expect_unknown=False)


    def test_client_say(self):
        # GIVEN
        player = FakeClient(self.parser, name="courgette", guid="STEAM_1:0:1111111", team=TEAM_BLUE)
        player.connects("2")
        # WHEN
        self.clear_events()
        self.parser.parseLine('''L 08/26/2012 - 05:09:55: "courgette<2><STEAM_1:0:1111111><CT>" say "!iamgod"''')
        # THEN
        self.assert_has_event("EVT_CLIENT_SAY", "!iamgod", player)


    def test_client_teamsay(self):
        # GIVEN
        player = FakeClient(self.parser, name="courgette", guid="STEAM_1:0:1111111", team=TEAM_BLUE)
        player.connects("2")
        # WHEN
        self.clear_events()
        self.parser.parseLine('''L 08/26/2012 - 05:04:44: "courgette<2><STEAM_1:0:1111111><CT>" say_team "team say"''')
        # THEN
        self.assert_has_event("EVT_CLIENT_TEAM_SAY", "team say", player)


    def test_bad_rcon_password(self):
        # GIVEN
        with patch.object(self.parser, "error") as error_mock:
            # WHEN
            self.parser.parseLine('''L 08/26/2012 - 05:21:23: rcon from "78.207.134.100:15073": Bad Password''')
            # THEN
            self.assertTrue(error_mock.called)
            error_mock.assert_has_calls([call('Bad RCON password, check your b3.xml file')])


    def test_clantag(self):
        # GIVEN
        player = FakeClient(self.parser, name="courgette", guid="STEAM_1:0:1111111", team=TEAM_BLUE)
        player.connects("2")
        # WHEN
        self.assertFalse(hasattr(player, "clantag"))
        self.parser.parseLine('''L 08/26/2012 - 05:43:31: "courgette<2><STEAM_1:0:1111111><CT>" triggered "clantag" (value "f00")''')
        # THEN
        self.assertEqual("f00", player.clantag)


    def test_Banid(self):
        # GIVEN
        player = FakeClient(self.parser, name="courgette", guid="STEAM_1:0:1111111")
        player.connects("2")
        # WHEN
        player.disconnects() # ban
        self.clear_events()
        self.parser.parseLine('''L 08/28/2012 - 00:03:01: Banid: "courgette<91><STEAM_1:0:1111111><>" was banned "for 1.00 minutes" by "Console"''')
        # THEN
        self.assert_has_event("EVT_CLIENT_BAN_TEMP", {'reason': None, 'duration': '1.00 minutes', 'admin': 'Console'}, player)


    def test_kick(self):
        # GIVEN
        player = FakeClient(self.parser, name="courgette", guid="STEAM_1:0:1111111")
        player.connects("2")
        # WHEN
        player.disconnects() # kick
        self.clear_events()
        self.parser.parseLine('''L 08/28/2012 - 00:12:07: [basecommands.smx] "Console<0><Console><Console>" kicked "courgette<91><STEAM_1:0:1111111><>" (reason "f00")''')
        # THEN
        self.assert_has_event("EVT_CLIENT_KICK", 'f00', player)


    def test_EVT_SUPERLOGS_WEAPONSTATS(self):
        # GIVEN
        bot48 = FakeClient(self.parser, name="Gunner", guid="BOT_48", team=TEAM_RED)
        bot48.connects("48")
        # WHEN
        self.clear_events()
        self.parser.parseLine('''L 08/28/2012 - 14:58:55: "Gunner<48><BOT><CT>" triggered "weaponstats" (weapon "m4a1") (shots "13") (hits "2") (kills "0") (headshots "0") (tks "0") (damage "42") (deaths "0")''')
        # THEN
        self.assert_has_event("EVT_SUPERLOGS_WEAPONSTATS", client=bot48, data={
            'weapon': "m4a1",
            'shots': "13",
            'hits': "2",
            'kills': "0",
            'headshots': "0",
            'tks': "0",
            'damage': "42",
            'deaths': "0",
        })


    def test_EVT_SUPERLOGS_WEAPONSTATS2(self):
        # GIVEN
        bot = FakeClient(self.parser, name="Vitaliy", guid="BOT_51", team=TEAM_RED)
        bot.connects("51")
        # WHEN
        self.clear_events()
        self.parser.parseLine('''L 08/28/2012 - 14:58:55: "Vitaliy<51><BOT><CT>" triggered "weaponstats2" (weapon "famas") (head "0") (chest "0") (stomach "1") (leftarm "0") (rightarm "0") (leftleg "0") (rightleg "0")''')
        # THEN
        self.assert_has_event("EVT_SUPERLOGS_WEAPONSTATS2", client=bot, data={
            'weapon': "famas",
            'head': "0",
            'chest': "0",
            'stomach': "1",
            'leftarm': "0",
            'rightarm': "0",
            'leftleg': "0",
            'rightleg': "0",
        })


    def test_unknown_line(self):
        # GIVEN
        with patch.object(self.parser, "warning") as warning_mock:
            # WHEN
            self.clear_events()
            self.parser.parseLine('''L 08/26/2012 - 05:04:55: f00''')
            # THEN
            self.assertEqual([], self.evt_queue)
            self.assertTrue(warning_mock.called)
            warning_mock.assert_has_calls([call('unhandled log line : f00. Please report this on the B3 forums')])


    def test_killed_with_SuperLogs_plugin(self):
        # GIVEN
        bot22 = FakeClient(self.parser, name="Pheonix", guid="BOT_22", team=TEAM_BLUE)
        bot17 = FakeClient(self.parser, name="Ringo", guid="BOT_17", team=TEAM_RED)
        bot4 = FakeClient(self.parser, name="F00", guid="BOT_4", team=TEAM_BLUE)
        bot22.connects("22")
        bot17.connects("17")
        bot4.connects("4")

        # WHEN
        self.clear_events()
        self.parser.parseLine('''L 08/29/2012 - 22:26:59: World triggered "killlocation" (attacker_position "-282 749 -21") (victim_position "68 528 64")''')
        self.parser.parseLine('''L 08/26/2012 - 03:46:44: "Pheonix<22><BOT><TERRORIST>" killed "Ringo<17><BOT><CT>" with "glock" (headshot)''')
        self.parser.parseLine('''L 08/26/2012 - 03:46:44: "F00<4><BOT><TERRORIST>" killed "Ringo<17><BOT><CT>" with "glock" (headshot)''')
        # THEN
        self.assert_has_event("EVT_CLIENT_KILL", client=bot22, target=bot17, data=(100, 'glock', 'head', None, {'attacker_position': "-282 749 -21", 'victim_position': "68 528 64"}))
        self.assert_has_event("EVT_CLIENT_KILL", client=bot4, target=bot17, data=(100, 'glock', 'head', None))


    def test_basechat_smx(self):
        # WHEN
        self.clear_events()
        self.parser.parseLine('''L 09/12/2012 - 23:15:47: [basechat.smx] "Console<0><Console><Console>" triggered sm_say (text f00)''')
        # THEN
        self.assertListEqual([], self.evt_queue)


    def test_rcon_from(self):
        # WHEN
        self.clear_events()
        self.parser.parseLine('''L 09/12/2012 - 23:24:02: rcon from "78.207.134.100:3804": command "sm_say fOO)"''')
        # THEN
        self.assertListEqual([], self.evt_queue)






class Test_parser_API(CsgoTestCase):

    def setUp(self):
        self.conf = XmlConfigParser()
        self.conf.loadFromString("""<configuration></configuration>""")
        self.parser = CsgoParser(self.conf)
        self.parser.output = Mock()
        when(self.parser.output).write("status").thenReturn(STATUS_RESPONSE)
        self.parser.startup()

    def tearDown(self):
        if hasattr(self, "parser"):
            self.parser.working = False


    def test_getPlayerList(self):
        # GIVEN
        with patch.object(self.parser, "queryServerInfo") as queryServerInfo_Mock:
            # WHEN
            c3 = Mock()
            c4 = Mock()
            c12 = Mock()
            queryServerInfo_Mock.return_value = {'3': c3, '4': c4, '12': c12, }
            rv = self.parser.getPlayerList()
            # THEN
            self.assertDictEqual({'3': c3, '4': c4, '12': c12, }, rv)


    def test_say(self):
        self.parser.msgPrefix = "[Pre]"
        with patch.object(self.parser.output, 'write') as write_mock:
            self.parser.say("f00")
            write_mock.assert_has_calls([call('sm_say [Pre] f00')])


    def test_saybig(self):
        self.parser.msgPrefix = "[Pre]"
        with patch.object(self.parser.output, 'write') as write_mock:
            self.parser.saybig("f00")
            write_mock.assert_has_calls([call('sm_hsay [Pre] f00')])

    @unittest.skip("there is some kind of conflict with another test in another module :s")
    def test_message(self):
        self.parser.msgPrefix = "[Pre]"
        player = Client(console=self.parser, guid="theGuid")
        with patch.object(self.parser.output, 'write') as write_mock:
            player.message("f00")
            write_mock.assert_has_calls([call('sm_psay #theGuid [Pre] f00')])


    def test_kick(self):
        player = Client(console=self.parser, cid="4", guid="theGuid")
        with patch.object(self.parser.output, 'write') as write_mock:
            player.kick(reason="f00")
            write_mock.assert_has_calls([call('sm_kick #4 f00')])


    @unittest.skip("TODO")
    def test_ban(self):
        pass


    @unittest.skip("TODO")
    def test_unban(self):
        pass


    @unittest.skip("TODO")
    def test_tempban(self):
        pass


    def test_getMap(self):
        # WHEN
        rv = self.parser.getMap()
        # THEN
        self.assertEqual('cs_foobar', rv)


    def test_getMaps(self):
        when(self.parser.output).write("listmaps").thenReturn('''Map Cycle:
cs_italy
de_dust
de_aztec
cs_office
de_dust2
de_train
de_inferno
de_nuke
L 08/28/2012 - 01:16:28: rcon from "11.222.111.222:4107": command "listmaps"
''')
        maps = self.parser.getMaps()
        verify(self.parser.output).write("listmaps")
        self.assertListEqual(["cs_italy",
                              "de_dust",
                              "de_aztec",
                              "cs_office",
                              "de_dust2",
                              "de_train",
                              "de_inferno",
                              "de_nuke",
                              ], maps)


    @unittest.skip("TODO")
    def test_rotateMap(self):
        pass


    def test_changeMap(self):
        with patch.object(self.parser.output, 'write') as write_mock:
            self.parser.changeMap("f00")
            write_mock.assert_has_calls([call('sm_map f00')])


    def test_getPlayerPings(self):
        # GIVEN
        with patch.object(self.parser, "queryServerInfo") as queryServerInfo_Mock:
            # WHEN
            queryServerInfo_Mock.return_value = {
                '3': Client(ping="45"),
                '4': Client(ping="112"),
                '12': Client(ping="54"),
            }
            rv = self.parser.getPlayerPings()
            # THEN
            self.assertEqual(3, len(rv))
            self.assertEqual("45", rv['3'])
            self.assertEqual("112", rv['4'])
            self.assertEqual("54", rv['12'])


    @unittest.skip("TODO")
    def test_getPlayerScores(self):
        pass


    @unittest.skip("TODO")
    def test_inflictCustomPenalty(self):
        pass




class Test_parser_other(CsgoTestCase):

    def test_getTeam(self):
        self.assertEqual(TEAM_RED, self.parser.getTeam('CT'))
        self.assertEqual(TEAM_BLUE, self.parser.getTeam('TERRORIST'))
        self.assertEqual(TEAM_UNKNOWN, self.parser.getTeam('Unassigned'))


    def test_getNextMap(self):
        when(self.parser.output).write("nextmap").thenReturn("""\
[SM] Next Map: de_inferno
L 08/28/2012 - 01:05:46: rcon from "11.222.111.222:4026": command "nextmap"
""")
        nextmap = self.parser.getNextMap()
        verify(self.parser.output).write("nextmap")
        self.assertEqual('de_inferno', nextmap)



    def test_getAvailableMaps(self):
        when(self.parser.output).write("maps *").thenReturn("""\
-------------
PENDING:   (fs) ar_baggage.bsp
PENDING:   (fs) ar_shoots.bsp
PENDING:   (fs) cs_italy.bsp
PENDING:   (fs) cs_italy_se.bsp
PENDING:   (fs) cs_office.bsp
PENDING:   (fs) training1.bsp""")
        maps = self.parser.getAvailableMaps()
        verify(self.parser.output).write("maps *")
        self.assertListEqual(["ar_baggage", "ar_shoots", "cs_italy", "cs_italy_se", "cs_office", "training1"], maps)


    def test_queryServerInfo(self):
        # WHEN
        rv = self.parser.queryServerInfo()
        # THEN
        self.assertEqual('cs_foobar', self.parser.game.mapName)
        self.assertEqual("Courgette's Server", self.parser.game.sv_hostname)
        self.assertEqual(1, len(rv))
        client = rv["194"]
        self.assertEqual("194", client.cid)
        self.assertEqual("courgette", client.name)
        self.assertEqual("STEAM_1:0:1111111", client.guid)
        self.assertEqual("67", client.ping)
        self.assertEqual("11.222.111.222", client.ip)


    def test_status_response_utf8_encoded(self):
        def assert_client(rv, cid, name, guid, ping, ip):
            self.assertIn(cid, rv)
            client = rv[cid]
            self.assertEqual(cid, client.cid)
            self.assertEqual(name, client.name)
            self.assertEqual(guid, client.guid)
            self.assertEqual(ping, client.ping)
            self.assertEqual(ip, client.ip)

        # GIVEN
        self.status_response = b'''\
hostname: UK - #2 Zombie Escape || FastDL - EHDGaming.co.uk [B3]
version : 1.18.0.3/11803 5045 secure
udp/ip  : 109.70.148.17:27017  (public ip: 109.70.148.17)
os      :  Windows
type    :  community dedicated
players : 14 humans, 0 bots (56/56 max) (not hibernating)

# userid name uniqueid connected ping loss state rate adr
# 12 1 "nooky treac" STEAM_1:1:00000807 28:23 505 6 spawning 30000 111.111.181.248:27005
#  4 2 "karta218" STEAM_1:0:00000003 34:30 548 0 spawning 10000 111.111.114.142:27005
# 30 3 "\xe9\xaa\xa8 xX Assassine Xx \xe9\xaa\xa8 ;)" STEAM_1:0:00000823 00:05 111 82 spawning 30000 194.208.143.16:27005
#  6 4 "Spoon" STEAM_1:0:00000181 33:33 43 0 active 30000 111.111.82.35:27005
#  7 5 "MercenarianWolf" STEAM_1:1:00000526 30:31 320 0 spawning 10000 111.111.13.88:27005
# 10 6 "eci" STEAM_1:0:00000740 28:47 35 16 active 30000 111.111.74.202:27005
# 11 8 "The Artist" STEAM_1:1:00000719 28:37 64 0 active 30000 111.111.93.239:27005
# 27 9 "=LIS=" STEAM_1:1:00000643 03:41 61 0 active 30000 111.111.30.26:27005
# 15 10 "ErayTR" STEAM_1:1:00000976 25:32 108 0 active 30000 111.111.117.145:27005
# 28 11 "ackop6uhka96" STEAM_1:1:00000052 02:16 90 0 active 30000 111.111.229.26:27005
# 25 12 "\xd0\xba\xd1\x80\xd0\xbe\xd0\xb2\xd0\xbe\xd1\x81\xd0\xbe\xd1\x81\xd1\x83\xd1\x88\xd0\xb8\xd0\xb9" STEAM_1:1:00000018 04:11 91 0 active 20000 111.111.237.162:27594
# 29 13 "WahOO" STEAM_1:1:00000678 00:22 69 0 active 20000 111.111.98.248:27005
# 23 14 "M\xe1\xb9\xa2 Xilver" STEAM_1:0:00000813 09:22 131 0 spawning 30000 111.111.215.27:27005
# 26 15 "Argon" STEAM_1:1:00000243 04:04 163 0 spawning 30000 111.111.197.113:27005
#end
L 09/10/2012 - 15:21:28: rcon from "109.70.148.17:3552": command "status"'''.decode('UTF-8')
        # WHEN
        rv = self.parser.queryServerInfo()
        # THEN
        self.assertEqual('cs_foobar', self.parser.game.mapName)
        self.assertEqual('UK - #2 Zombie Escape || FastDL - EHDGaming.co.uk [B3]', self.parser.game.sv_hostname)
        self.assertEqual(14, len(rv))
        assert_client(rv, "12", "nooky treac", "STEAM_1:1:00000807", "505", "111.111.181.248")
        assert_client(rv, "4", "karta218", "STEAM_1:0:00000003", "548", "111.111.114.142")
        assert_client(rv, "30", u"骨 xX Assassine Xx 骨 ;)", "STEAM_1:0:00000823", "111", "194.208.143.16")
        self.assertIn("6", rv)
        self.assertIn("7", rv)
        self.assertIn("10", rv)
        self.assertIn("11", rv)
        self.assertIn("27", rv)
        self.assertIn("15", rv)
        self.assertIn("28", rv)
        assert_client(rv, "25", u"кровососуший", "STEAM_1:1:00000018", "91", "111.111.237.162")
        assert_client(rv, "23", u"MṢ Xilver", "STEAM_1:0:00000813", "131", "111.111.215.27")
        self.assertIn("26", rv)


