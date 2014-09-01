# coding=UTF-8
#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2014 Courgette
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
import unittest2 as unittest
from b3 import TEAM_BLUE, TEAM_RED, TEAM_UNKNOWN, TEAM_SPEC
from b3.config import XmlConfigParser
from b3.fake import FakeClient
from b3.parsers.chiv import ChivParser, Packet, MessageType


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

WHATEVER = object()  # sentinel used in CsgoTestCase.assert_has_event


class ChivTestCase(unittest.TestCase):
    """
    Test case that is suitable for testing Chivalry parser specific features
    """
    @classmethod
    def setUpClass(cls):
        from b3.fake import FakeConsole
        ChivParser.__bases__ = (FakeConsole,)
        # Now parser inheritance hierarchy is :
        # ChivParser -> FakeConsole -> Parser

    def setUp(self):
        self.conf = XmlConfigParser()
        self.conf.loadFromString("""<configuration></configuration>""")
        self.parser = ChivParser(self.conf)
        self.parser._client = Mock()

        self.evt_queue = []
        def queue_event(evt):
            self.evt_queue.append(evt)
        self.queueEvent_patcher = patch.object(self.parser, "queueEvent", wraps=queue_event)
        self.queueEvent_mock = self.queueEvent_patcher.start()


    def tearDown(self):
        self.queueEvent_patcher.stop()
        if hasattr(self, "parser"):
            del self.parser.clients
            self.parser.working = False

    def clear_events(self):
        """
        clear the event queue, so when assert_has_event is called, it will look only at the newly caught events.
        """
        self.evt_queue = []

    def assert_has_event(self, event_type, data=WHATEVER, client=WHATEVER, target=WHATEVER):
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
            if data != WHATEVER:
                self.assertEqual(expected_event.data, actual_event.data)
            if client != WHATEVER:
                self.assertTrue(client_equal(expected_event.client, actual_event.client))
            if target != WHATEVER:
                self.assertTrue(client_equal(expected_event.target, actual_event.target))
        else:
            for evt in self.evt_queue:
                if expected_event.type == evt.type \
                        and (expected_event.data == evt.data or data == WHATEVER)\
                        and (client_equal(expected_event.client, evt.client) or client == WHATEVER)\
                        and (client_equal(expected_event.target, evt.target) or target == WHATEVER):
                    return

            self.fail("expecting event %s. Got instead: %s" % (expected_event, map(str, self.evt_queue)))

    def assert_has_not_event(self, event_type, data=None, client=None, target=None):
        """
        assert that self.evt_queue does not contain at least one event for the given type that has the given characteristics.
        """
        assert isinstance(event_type, basestring)
        unexpected_event = self.parser.getEvent(event_type, data, client, target)

        if not len(self.evt_queue):
            return
        else:
            def event_match(evt):
                return (
                    unexpected_event.type == evt.type
                    and (data is None or data == evt.data)
                    and (client is None or client_equal(client, evt.client))
                    and (target is None or client_equal(target, evt.target))
                )
            if any(map(event_match, self.evt_queue)):
                self.fail("not expecting event %s" % (filter(event_match, self.evt_queue)))


class Test_gameevent_parsing(ChivTestCase):

    def test_PLAYER_CHAT(self):  # 3
        # GIVEN
        player = FakeClient(self.parser, name="Pheonix", guid="76561198038608801")
        player.connects("1")
        self.clear_events()
        # WHEN
        self.parser.handlePacket(Packet.decode(
            '\x00\x03\x00\x00\x00\x17\x01\x10\x00\x01\x04\xabk\xa1\x00\x00\x00\x07 sorry \x00\x00\x00\x00'))
        # THEN
        self.assert_has_event("EVT_CLIENT_SAY", data='sorry', client=player)

    def test_PLAYER_CHAT_team(self):  # 3
        # GIVEN
        player = FakeClient(self.parser, name="Pheonix", guid="76561198038608801")
        player.connects("1")
        self.clear_events()
        player.team = 0  # ugly, until chiv team ids got converted into b3 team ids
        # WHEN
        self.parser.handlePacket(Packet.decode(
            '\x00\x03\x00\x00\x00\x17\x01\x10\x00\x01\x04\xabk\xa1\x00\x00\x00\x07 sorry \x00\x00\x00\x00'))
        # THEN
        self.assert_has_event("EVT_CLIENT_TEAM_SAY", data='sorry', client=player)

    def test_PLAYER_CONNECT(self):  # 4
        # GIVEN
        self.assertIsNone(self.parser.clients.getByGUID("1234567890"))
        # WHEN
        self.parser.handlePacket(Packet.decode(
            '\x00\x04\x00\x00\x00\x13\x00\x00\x00\x00I\x96\x02\xd2\x00\x00\x00\x07player1'
        ))
        # THEN
        player = self.parser.clients.getByGUID("1234567890")
        self.assertIsNotNone(player)
        self.assertEqual('player1', player.name)

    def test_PLAYER_DISCONNECT(self):  # 5
        # GIVEN
        player = FakeClient(self.parser, name="Pheonix", guid="76561198036015889")
        player.connects("1")
        self.clear_events()
        # WHEN
        self.parser.handlePacket(Packet.decode(
            '\x00\x05\x00\x00\x00\x08\x01\x10\x00\x01\x04\x83\xdb\x11'
        ))
        # THEN
        self.assert_has_event("EVT_CLIENT_DISCONNECT", data='1', client=player)


    def test_MAP_CHANGED(self):  # 9
        # GIVEN
        self.parser.game.mapName = "old"
        # WHEN
        self.parser.handlePacket(Packet.decode('\x00\t\x00\x00\x00\x0f\x00\x00\x00#\x00\x00\x00\x07TD-Isle'))
        # THEN
        self.assertEqual("TD-Isle", self.parser.game.mapName)
        self.assertEqual("TD-Isle", self.parser.getMap())

    def test_MAP_LIST(self):  # 10
        # GIVEN
        self.parser._mapList = None
        # WHEN
        self.parser.handlePacket(Packet.decode(
            '\x00\n\x00\x00\x00E\x00\x00\x00ATD-Bamboo_small?game=CDW.AOCTD?numteams=2?class0=Open?class1=Open'
        ))
        self.parser.handlePacket(Packet.decode(
            '\x00\n\x00\x00\x00O\x00\x00\x00KPTB-Valley_small?game=CDW.PlantTheBanner?numteams=2?class0=Open?class1=Open'
        ))
        # THEN
        self.assertListEqual(['TD-Bamboo_small', 'PTB-Valley_small'], self.parser._mapList)

    def test_TEAM_CHANGED_0(self):  # 13
        # GIVEN
        player = FakeClient(self.parser, name="Pheonix", guid="76561198070138838")
        player.connects("1")
        self.assertEqual(TEAM_UNKNOWN, player.team)
        # WHEN
        self.parser.handlePacket(Packet.decode('\x00\r\x00\x00\x00\x0c\x01\x10\x00\x01\x06\x8c\x87\xd6\x00\x00\x00\x00'))
        # THEN
        self.assertEqual(0, player.team)

    def test_TEAM_CHANGED_1(self):  # 13
        # GIVEN
        player = FakeClient(self.parser, name="Pheonix", guid="76561198070138838")
        player.connects("1")
        self.assertEqual(TEAM_UNKNOWN, player.team)
        # WHEN
        self.parser.handlePacket(Packet.decode('\x00\r\x00\x00\x00\x0c\x01\x10\x00\x01\x06\x8c\x87\xd6\x00\x00\x00\x01'))
        # THEN
        self.assertEqual(1, player.team)

    def test_NAME_CHANGED(self):  # 14
        # GIVEN
        player = FakeClient(self.parser, name="Pheonix", guid="123456789")
        player.connects("1")
        # WHEN
        self.parser.handlePacket(Packet.decode(
            '\x00\x0e\x00\x00\x00\x14\x00\x00\x00\x00\x07[\xcd\x15\x00\x00\x00\x08new name'
        ))
        # THEN
        self.assertEqual('new name', player.name)

    def test_KILL(self):  # 15
        # GIVEN
        attacker = FakeClient(self.parser, name="attacker_name", guid='76561198036015889')
        attacker.connects("1")
        victim = FakeClient(self.parser, name="victim_name", guid='76561198021620061')
        victim.connects("2")
        # WHEN
        self.parser.handlePacket(Packet.decode(
            '\x00\x0f\x00\x00\x00\x1e\x01\x10\x00\x01\x04\x83\xdb\x11\x01\x10\x00\x01\x03\xa81]\x00\x00\x00\nTekko Kagi'
        ))
        # THEN
        self.assert_has_event("EVT_CLIENT_KILL", client=attacker, target=victim, data=(100, u'Tekko Kagi', 'body'))

    def test_KILL_teamkill(self):  # 15
        # GIVEN
        attacker = FakeClient(self.parser, name="attacker_name", guid='76561198036015889', team=TEAM_BLUE)
        attacker.connects("1")
        victim = FakeClient(self.parser, name="victim_name", guid='76561198021620061', team=TEAM_BLUE)
        victim.connects("2")
        # WHEN
        self.parser.handlePacket(Packet.decode(
            '\x00\x0f\x00\x00\x00\x1e\x01\x10\x00\x01\x04\x83\xdb\x11\x01\x10\x00\x01\x03\xa81]\x00\x00\x00\nTekko Kagi'
        ))
        # THEN
        self.assert_has_event("EVT_CLIENT_KILL_TEAM", client=attacker, target=victim, data=(100, u'Tekko Kagi', 'body'))

    def test_SUICIDE(self):  # 16
        # GIVEN
        poorguy = FakeClient(self.parser, name="attacker_name", guid='76561198070138838')
        poorguy.connects("1")
        # WHEN
        self.parser.handlePacket(Packet.decode('\x00\x10\x00\x00\x00\x08\x01\x10\x00\x01\x06\x8c\x87\xd6'))
        # THEN
        self.assert_has_event("EVT_CLIENT_SUICIDE", client=poorguy, target=poorguy, data=(100, None, None))

    def test_unknown_msgType(self):
        # WHEN
        with patch.object(self.parser, "warning") as warning_mock:
            self.parser.handlePacket(
                Packet.decode('\x00c\x00\x00\x00\x0f\x00\x00\x00\x00I\x96\x02\xd2\x00\x00\x00\x03f00'))
        # THEN
        self.assertListEqual([], self.evt_queue)
        self.assertListEqual([
             call("unkown RCON message type: 99. REPORT THIS TO THE B3 FORUMS. Packet.decode('\\x00c\\x00\\x00\\x00\\x0f\\x00\\x00\\x00\\x00I\\x96\\x02\\xd2\\x00\\x00\\x00\\x03f00')  # {'msgType': 99, 'dataLength': 15, 'data': '\\x00\\x00\\x00\\x00I\\x96\\x02\\xd2\\x00\\x00\\x00\\x03f00'}")
                             ], warning_mock.mock_calls)


class Test_parser_other(ChivTestCase):

    def test_getNextMap(self):
        # GIVEN
        self.parser._mapList = None
        self.parser.handlePacket(Packet.decode(
            '\x00\n\x00\x00\x00E\x00\x00\x00ATD-Bamboo_small?game=CDW.AOCTD?numteams=2?class0=Open?class1=Open'
        ))
        self.parser.handlePacket(Packet.decode(
            '\x00\n\x00\x00\x00O\x00\x00\x00KPTB-Valley_small?game=CDW.PlantTheBanner?numteams=2?class0=Open?class1=Open'
        ))
        self.parser.handlePacket(Packet.decode('\x00\t\x00\x00\x00\x17\x00\x00\x00\x00\x00\x00\x00\x0fTD-Bamboo_small'))
        # WHEN
        self.assertEqual("TD-Bamboo_small", self.parser.getMap())
        # THEN
        self.assertEqual('PTB-Valley_small', self.parser.getNextMap())

    def test_getNextMap_current_map_is_last(self):
        # GIVEN
        self.parser._mapList = None
        self.parser.handlePacket(Packet.decode(
            '\x00\n\x00\x00\x00E\x00\x00\x00ATD-Bamboo_small?game=CDW.AOCTD?numteams=2?class0=Open?class1=Open'
        ))
        self.parser.handlePacket(Packet.decode(
            '\x00\n\x00\x00\x00O\x00\x00\x00KPTB-Valley_small?game=CDW.PlantTheBanner?numteams=2?class0=Open?class1=Open'
        ))
        self.parser.handlePacket(Packet.decode('\x00\t\x00\x00\x00\x18\x00\x00\x00\x01\x00\x00\x00\x10PTB-Valley_small'))
        # WHEN
        self.assertEqual("PTB-Valley_small", self.parser.getMap())
        # THEN
        self.assertEqual('TD-Bamboo_small', self.parser.getNextMap())

