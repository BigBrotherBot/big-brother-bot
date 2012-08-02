# -*- encoding: utf-8 -*-
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
import unittest2 as unittest
from mock import Mock, patch, call
from mockito import when
from b3.fake import FakeClient
from b3.parsers.arma2 import Arma2Parser
from b3.config import XmlConfigParser



class Arma2TestCase(unittest.TestCase):
    """
    Test case that is suitable for testing Arma2 parser specific features
    """

    @classmethod
    def setUpClass(cls):
        from b3.parsers.battleye.abstractParser import AbstractParser
        from b3.fake import FakeConsole
        AbstractParser.__bases__ = (FakeConsole,)
        # Now parser inheritance hierarchy is :
        # Arma2Parser -> AbstractParser -> FakeConsole -> Parser

    def tearDown(self):
        if hasattr(self, "parser"):
            self.parser.working = False





class EventParsingTestCase(Arma2TestCase):

    def setUp(self):
        """ran before each test"""
        self.conf = XmlConfigParser()
        self.conf.loadFromString("""
                <configuration>
                </configuration>
            """)
        self.parser = Arma2Parser(self.conf)
        self.parser.output = Mock() # mock Rcon

        self.evt_queue = []
        def queue_event(evt):
            self.evt_queue.append(evt)
        self.queueEvent_patcher = patch.object(self.parser, "queueEvent", wraps=queue_event)
        self.queueEvent_mock = self.queueEvent_patcher.start()

        self.write_patcher = patch.object(self.parser, "write")
        self.write_mock = self.write_patcher.start()

        self.parser.startup()


    def tearDown(self):
        """ran after each test to clean up"""
        Arma2TestCase.tearDown(self)
        self.queueEvent_patcher.stop()
        self.write_patcher.stop()
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

        def assert_event_equals(expected_event, actual_event):
            if expected_event is None:
                self.assertIsNone(actual_event)
            self.assertEqual(expected_event.type, actual_event.type, "expecting type %s, but got %s" %
                                                                     (self.parser.getEventKey(expected_event.type), self.parser.getEventKey(actual_event.type)))
            self.assertEqual(expected_event.client, actual_event.client, "expecting client %s, but got %s" % (expected_event.client, actual_event.client))
            self.assertEqual(expected_event.target, actual_event.target, "expecting target %s, but got %s" % (expected_event.target, actual_event.target))
            self.assertEqual(expected_event.data, actual_event.data, "expecting data %s, but got %s" % (expected_event.data, actual_event.data))

        expected_event = self.parser.getEvent(event_type, data, client, target)
        if not len(self.evt_queue):
            self.fail("expecting %s. Got no event instead" % expected_event)
        elif len(self.evt_queue) == 1:
            assert_event_equals(expected_event, self.evt_queue[0])
        else:
            for evt in self.evt_queue:
                try:
                    assert_event_equals(expected_event, evt)
                    return
                except Exception:
                    pass
            self.fail("expecting event %s. Got instead: %s" % (expected_event, map(str, self.evt_queue)))


    ################################################################################################################



class Test_game_events_parsing(EventParsingTestCase):

    def test_player_connected(self):
        # GIVEN
        self.clear_events()
        # WHEN
        self.parser.routeBattleyeEvent("""Player #0 Bravo17 (76.108.91.78:2304) connected""")
        # THEN
        self.assertEqual(1, len(self.evt_queue))
        event = self.evt_queue[0]
        self.assertEqual(self.parser.getEventID("EVT_CLIENT_CONNECT"), event.type)
        self.assertEqual("Bravo17", event.client.name)
        self.assertEqual("0", event.client.cid)
        self.assertEqual("76.108.91.78", event.client.ip)


    def test_Verified_guid__with_connected_player(self):
        # GIVEN
        bravo17 = FakeClient(self.parser, name="Bravo17")
        bravo17.connects("0")
        self.clear_events()
        # WHEN
        self.parser.routeBattleyeEvent("""Verified GUID (80a5885ebe2420bab5e158a310fcbc7d) of player #0 Bravo17""")
        # THEN
        self.assert_has_event("EVT_CLIENT_AUTH", data=bravo17, client=bravo17)


    def test_Verified_guid__with_unknown_player(self):
        # GIVEN
        self.clear_events()
        # WHEN
        self.parser.routeBattleyeEvent("""Verified GUID (80a5885ebe2420bab5e158a310fcbc7d) of player #0 Bravo17""")
        # THEN
        self.assertTrue(len(self.evt_queue))
        event = self.evt_queue[0]
        self.assertEqual(self.parser.getEventID("EVT_CLIENT_CONNECT"), event.type)
        self.assertEqual("Bravo17", event.client.name)
        self.assertEqual("0", event.client.cid)
        bravo17 = event.client
        self.assert_has_event("EVT_CLIENT_AUTH", data=bravo17, client=bravo17)


    def test_player_disconnect(self):
        # GIVEN
        bravo17 = FakeClient(self.parser, name="Bravo17", guid="80a5885ebe2420bab5e158a310fcbc7d")
        bravo17.connects("12")
        self.clear_events()
        # WHEN
        self.parser.routeBattleyeEvent("""Player #12 Bravo17 disconnected""")
        # THEN
        self.assert_has_event("EVT_CLIENT_DISCONNECT", client=bravo17, data='12')


    def test_Lobby_chat(self):
        # GIVEN
        bravo17 = FakeClient(self.parser, name="Bravo17", guid="80a5885ebe2420bab5e158a310fcbc7d")
        bravo17.connects("12")
        self.clear_events()
        # WHEN
        self.parser.routeBattleyeEvent("""(Lobby) Bravo17: hello b3""")
        # THEN
        self.assert_has_event("EVT_CLIENT_SAY", client=bravo17, data='hello b3 (Lobby)')


    def test_Global_chat(self):
        # GIVEN
        bravo17 = FakeClient(self.parser, name="Bravo17", guid="80a5885ebe2420bab5e158a310fcbc7d")
        bravo17.connects("12")
        self.clear_events()
        # WHEN
        self.parser.routeBattleyeEvent("""(Global) Bravo17: global channel""")
        # THEN
        self.assert_has_event("EVT_CLIENT_SAY", client=bravo17, data='global channel (Global)')


    def test_Direct_chat(self):
        # GIVEN
        bravo17 = FakeClient(self.parser, name="Bravo17", guid="80a5885ebe2420bab5e158a310fcbc7d")
        bravo17.connects("12")
        self.clear_events()
        # WHEN
        self.parser.routeBattleyeEvent("""(Direct) Bravo17: test direct channel""")
        # THEN
        self.assert_has_event("EVT_CLIENT_SAY", client=bravo17, data='test direct channel (Direct)')


    def test_Vehicule_chat(self):
        # GIVEN
        bravo17 = FakeClient(self.parser, name="Bravo17", guid="80a5885ebe2420bab5e158a310fcbc7d")
        bravo17.connects("12")
        self.clear_events()
        # WHEN
        self.parser.routeBattleyeEvent("""(Vehicle) Bravo17: test vehicle channel""")
        # THEN
        self.assert_has_event("EVT_CLIENT_SAY", client=bravo17, data='test vehicle channel (Vehicle)')


    def test_Group_chat(self):
        # GIVEN
        bravo17 = FakeClient(self.parser, name="Bravo17", guid="80a5885ebe2420bab5e158a310fcbc7d")
        bravo17.connects("12")
        self.clear_events()
        # WHEN
        self.parser.routeBattleyeEvent("""(Group) Bravo17: test group channel""")
        # THEN
        self.assert_has_event("EVT_CLIENT_SAY", client=bravo17, data='test group channel (Group)')


    def test_Side_chat(self):
        # GIVEN
        bravo17 = FakeClient(self.parser, name="Bravo17", guid="80a5885ebe2420bab5e158a310fcbc7d")
        bravo17.connects("12")
        self.clear_events()
        # WHEN
        self.parser.routeBattleyeEvent("""(Side) Bravo17: test side channel""")
        # THEN
        self.assert_has_event("EVT_CLIENT_SAY", client=bravo17, data='test side channel (Side)')


    def test_Command_chat(self):
        # GIVEN
        bravo17 = FakeClient(self.parser, name="Bravo17", guid="80a5885ebe2420bab5e158a310fcbc7d")
        bravo17.connects("12")
        self.clear_events()
        # WHEN
        self.parser.routeBattleyeEvent("""(Command) Bravo17: test command channel""")
        # THEN
        self.assert_has_event("EVT_CLIENT_SAY", client=bravo17, data='test command channel (Command)')


class Test_utf8_issues(EventParsingTestCase):

    def test_player_connected_utf8(self):
        # GIVEN
        self.clear_events()
        # WHEN routeBattleyeMessagePacket is given a UTF-8 encoded message
        self.parser.routeBattleyeEvent(u"""Player #0 F00Åéxx (11.1.1.8:2304) connected""")
        # THEN
        self.assertEqual(1, len(self.evt_queue))
        event = self.evt_queue[0]
        self.assertEqual(self.parser.getEventID("EVT_CLIENT_CONNECT"), event.type)
        self.assertEqual(u"F00Åéxx", event.client.name)


    def test_player_connected_utf8_2(self):
        # GIVEN
        self.clear_events()
        # WHEN
        self.parser.routeBattleyeEvent(u'Player #1 étoiléàtèsté (77.205.193.131:2304) connected')
        # THEN
        self.assertEqual(1, len(self.evt_queue))
        event = self.evt_queue[0]
        self.assertEqual(self.parser.getEventID("EVT_CLIENT_CONNECT"), event.type)
        self.assertEqual(u"étoiléàtèsté", event.client.name)


    def test_verified_guid(self):
        # GIVEN
        self.clear_events()
        # WHEN
        self.parser.routeBattleyeEvent(u'Verified GUID (a4c3eba0a790300fd7d9d39e26e00eb0) of player #1 étoiléàtèsté')
        # THEN
        self.assertTrue(len(self.evt_queue))
        event = self.evt_queue[0]
        self.assertEqual(self.parser.getEventID("EVT_CLIENT_CONNECT"), event.type)
        self.assertEqual(u"étoiléàtèsté", event.client.name)





@patch('time.sleep')
class Test_parser_API(Arma2TestCase):

    def setUp(self):
        self.conf = XmlConfigParser()
        self.conf.loadFromString("""<configuration></configuration>""")
        self.parser = Arma2Parser(self.conf)
        self.parser.output = Mock()

        self.parser.sayqueue.put = Mock(side_effect=self.parser._say)

        self.parser.startup()

        self.player = self.parser.clients.newClient(cid="4", guid="theGuid", name="theName", ip="11.22.33.44")


    def test_getPlayerList(self, sleep_mock):
        # GIVEN
        when(self.parser.output).write('players').thenReturn(u'''\
Players on server:
[#] [IP Address]:[Port] [Ping] [GUID] [Name]
--------------------------------------------------
0   11.111.11.11:2304     63   80a5885eb00000000000000000000000(OK) étoiléàÄ
0   192.168.0.100:2316    0    80a5885eb00000000000000000000000(OK) étoiléàÄ (Lobby)
(1 players in total)
''')
        # WHEN
        players = self.parser.getPlayerList()
        # THEN
        self.maxDiff = 1024
        self.assertDictEqual({u'0': {'cid': u'0',
                                     'guid': u'80a5885eb00000000000000000000000',
                                     'ip': u'192.168.0.100',
                                     'lobby': True,
                                     'name': u'étoiléàÄ',
                                     'ping': u'0',
                                     'port': u'2316',
                                     'verified': u'OK'}}, players)


    def test_say(self, sleep_mock):
        # GIVEN
        self.parser.msgPrefix = "[Pre]"
        # WHEN
        self.parser.say("f00")
        # THEN
        self.parser.output.write.assert_has_calls([call('say -1 [Pre] f00')])


    def test_saybig(self, sleep_mock):
        # GIVEN
        self.parser.msgPrefix = "[Pre]"
        # WHEN
        self.parser.saybig("f00")
        # THEN
        self.parser.output.write.assert_has_calls([call('say -1 [Pre] f00')])


    def test_message(self, sleep_mock):
        # GIVEN
        self.parser.msgPrefix = "[Pre]"
        # WHEN
        self.parser.message(self.player, "f00")
        # THEN
        self.parser.output.write.assert_has_calls([call('say 4 [Pre] f00')])


    def test_kick(self, sleep_mock):
        self.parser.kick(self.player, reason="f00")
        self.parser.output.write.assert_has_calls([call('kick 4 f00')])


    def test_ban__by_cid(self, sleep_mock):
        self.assertIsNotNone(self.player.cid)
        self.parser.ban(self.player, reason="f00")
        self.parser.output.write.assert_has_calls([call('ban 4 0 f00'), call('writeBans')])


    def test_ban__by_guid(self, sleep_mock):
        self.player.cid = None
        self.assertIsNone(self.player.cid)
        self.parser.ban(self.player, reason="f00")
        self.parser.output.write.assert_has_calls([call('addBan theGuid 0 f00'), call('writeBans')])


    def test_unban(self, sleep_mock):
        # GIVEN
        self.player.cid = None
        self.assertIsNone(self.player.cid)
        when(self.parser).getBanlist().thenReturn({
            'theGuid': {'ban_index': '152', 'guid': 'theGuid', 'reason': 'the ban reason', 'min_left': 'perm'},
            })
        # WHEN
        self.parser.unban(self.player, reason="f00")
        # THEN
        self.parser.output.write.assert_has_calls([call('removeBan 152'), call('writeBans')])


    def test_tempban__by_cid(self, sleep_mock):
        self.assertIsNotNone(self.player.cid)
        self.parser.tempban(self.player, reason="f00", duration='2h')
        self.parser.output.write.assert_has_calls([call('ban 4 120 f00'),
                                                   call('writeBans')])


    def test_tempban__by_guid(self, sleep_mock):
        self.player.cid = None
        self.assertIsNone(self.player.cid)
        self.parser.tempban(self.player, reason="f00", duration='2h')
        self.parser.output.write.assert_has_calls([call('addBan theGuid 120 f00'),
                                                   call('writeBans')])

#
#    def test_getMap(self, sleep_mock):
#        pass
#
#
#    def test_getMaps(self, sleep_mock):
#        pass
#
#
#    def test_rotateMap(self, sleep_mock):
#        pass
#
#
#    def test_changeMap(self, sleep_mock):
#        pass


    def test_getPlayerPings(self, sleep_mock):
        # GIVEN
        when(self.parser.output).write('players').thenReturn(u'''\
Players on server:
[#] [IP Address]:[Port] [Ping] [GUID] [Name]
--------------------------------------------------
0   76.108.91.78:2304     63   80a5885ebe2420bab5e158a310fcbc7d(OK) Bravo17
0   192.168.0.100:2316    0    80a5885ebe2420bab5e158a310fcbc7d(OK) Bravo17 (Lobby)
2   111.22.3.4:2316       47   80a50000000000000000000000fcbc7d(?)  bob
(1 players in total)
''')
        # WHEN
        pings = self.parser.getPlayerPings()
        # THEN
        self.maxDiff = 1024
        self.assertDictEqual({u'0': 63, u'2': 47}, pings)

#
#    def test_getPlayerScores(self, sleep_mock):
#        pass


class test_sync(EventParsingTestCase):

    def test_known_client_with_unverified_guid_but_same_ip_is_auth(self):
        # GIVEN a known client Bob
        bob = FakeClient(self.parser, name="bob", guid="80a50000000000000000000000fcbc7d", ip="111.22.3.4")
        bob.save()
        # WHEN
        when(self.parser.output).write('players').thenReturn('''\
Players on server:
[#] [IP Address]:[Port] [Ping] [GUID] [Name]
--------------------------------------------------
2   111.22.3.4:2316       47   80a50000000000000000000000fcbc7d(?)  bob
(1 players in total)
''')
        rv = self.parser.sync()
        # THEN
        self.assertIn('2', rv)
        client = rv["2"]
        self.assertEqual(bob.guid, client.guid)
        self.assertEqual(bob.ip, client.ip)
        self.assertTrue(client.authed)


    def test_known_client_with_unverified_guid_and_different_ip_is_not_auth(self):
        # GIVEN a known client Bob
        bob = FakeClient(self.parser, name="bob", guid="80a50000000000000000000000fcbc7d", ip="1.2.3.4")
        bob.save()
        # WHEN
        when(self.parser.output).write('players').thenReturn('''\
Players on server:
[#] [IP Address]:[Port] [Ping] [GUID] [Name]
--------------------------------------------------
2   4.6.8.10:2316       47   80a50000000000000000000000fcbc7d(?)  bob
(1 players in total)
''')
        rv = self.parser.sync()
        # THEN
        self.assertIn('2', rv)
        client = rv["2"]
        self.assertEqual("bob", client.name)
        self.assertEqual("4.6.8.10", client.ip)
        self.assertEqual('', client.guid)
        self.assertFalse(client.authed)


    def test_unknown_client_with_unverified_guid(self):
        # WHEN
        when(self.parser.output).write('players').thenReturn('''\
Players on server:
[#] [IP Address]:[Port] [Ping] [GUID] [Name]
--------------------------------------------------
2   4.6.8.10:2316       47   80a50000000000000000000000fcbc7d(?)  bob
(1 players in total)
''')
        rv = self.parser.sync()
        # THEN
        self.assertIn('2', rv)
        client = rv["2"]
        self.assertEqual("bob", client.name)
        self.assertEqual("4.6.8.10", client.ip)
        self.assertEqual('', client.guid)
        self.assertFalse(client.authed)

    def test_unknown_client_with_verified_guid(self):
        # WHEN
        when(self.parser.output).write('players').thenReturn('''\
Players on server:
[#] [IP Address]:[Port] [Ping] [GUID] [Name]
--------------------------------------------------
2   4.6.8.10:2316       47   80a50000000000000000000000fcbc7d(OK)  bob
(1 players in total)
''')
        rv = self.parser.sync()
        # THEN
        self.assertIn('2', rv)
        client = rv["2"]
        self.assertEqual("bob", client.name)
        self.assertEqual("4.6.8.10", client.ip)
        self.assertEqual('80a50000000000000000000000fcbc7d', client.guid)
        self.assertTrue(client.authed)



class test_others(Arma2TestCase):

    def setUp(self):
        self.conf = XmlConfigParser()
        self.conf.loadFromString("""<configuration></configuration>""")
        self.parser = Arma2Parser(self.conf)
        self.parser.output = Mock()
        self.parser.startup()
        self.player = self.parser.clients.newClient(cid="4", guid="theGuid", name="theName", ip="11.22.33.44")


    def test_getBanlist(self):
        # GIVEN
        self.maxDiff = 1024
        when(self.parser.output).write("bans").thenReturn("""\
GUID Bans:
[#] [GUID] [Minutes left] [Reason]
----------------------------------------
0  b57c222222a76f458893641000000005 perm Script Detection: Gerk
1  8ac61111111cd2ff4235140000000026 perm Script Detection: setVehicleInit DoThis;""")
        # WHEN
        rv = self.parser.getBanlist()
        # THEN
        self.assertDictEqual({
            'b57c222222a76f458893641000000005': {'ban_index': '0', 'guid': 'b57c222222a76f458893641000000005', 'reason': 'Script Detection: Gerk', 'min_left': 'perm'},
            '8ac61111111cd2ff4235140000000026': {'ban_index': '1', 'guid': '8ac61111111cd2ff4235140000000026', 'reason': 'Script Detection: setVehicleInit DoThis;', 'min_left': 'perm'},
        }, rv)
