# -*- encoding: utf-8 -*-
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
import logging
import unittest2 as unittest
from mock import Mock, patch
from mockito import when
from b3.clients import Client
from b3.parsers.arma3 import Arma3Parser
from b3.config import XmlConfigParser
from tests import logging_disabled

ANY = object()


class Arma3TestCase(unittest.TestCase):
    """
    Test case that is suitable for testing Arma3 parser specific features
    """

    @classmethod
    def setUpClass(cls):
        from b3.parsers.battleye.abstractParser import AbstractParser
        from b3.fake import FakeConsole
        AbstractParser.__bases__ = (FakeConsole,)
        # Now parser inheritance hierarchy is :
        # Arma3Parser -> AbstractParser -> FakeConsole -> Parser

        logging.getLogger('output').setLevel(logging.DEBUG)

    def tearDown(self):
        if hasattr(self, "parser"):
            self.parser.working = False


class EventParsingTestCase(Arma3TestCase):

    def setUp(self):
        """ran before each test"""
        self.conf = XmlConfigParser()
        self.conf.loadFromString("""
                <configuration>
                </configuration>
            """)
        with logging_disabled():
            self.parser = Arma3Parser(self.conf)
        self.parser.output = Mock()  # mock Rcon

        self.evt_queue = []

        def queue_event(evt):
            self.evt_queue.append(evt)

        self.queueEvent_patcher = patch.object(self.parser, "queueEvent", wraps=queue_event)
        self.queueEvent_mock = self.queueEvent_patcher.start()

        self.write_patcher = patch.object(self.parser, "write")
        self.write_mock = self.write_patcher.start()

        with logging_disabled():
            self.parser.startup()

    def tearDown(self):
        """ran after each test to clean up"""
        Arma3TestCase.tearDown(self)
        self.queueEvent_patcher.stop()
        self.write_patcher.stop()
        if hasattr(self, "parser"):
            self.parser.working = False

    def clear_events(self):
        """
        clear the event queue, so when assert_has_event is called, it will look only at the newly caught events.
        """
        self.evt_queue = []

    def assert_has_event(self, event_type, data=ANY, client=ANY, target=ANY):
        """
        assert that self.evt_queue contains at least one event for the given type that has the given characteristics.
        """
        assert isinstance(event_type, basestring)

        def assert_event_equals(expected_event, actual_event):
            if expected_event is None:
                self.assertIsNone(actual_event)
            self.assertEqual(expected_event.type, actual_event.type, "expecting type %s, but got %s" %
                                                                     (self.parser.getEventKey(expected_event.type), self.parser.getEventKey(actual_event.type)))
            if client is not ANY:
                self.assertEqual(expected_event.client, actual_event.client, "expecting client %s, but got %s" % (expected_event.client, actual_event.client))
            if target is not ANY:
                self.assertEqual(expected_event.target, actual_event.target, "expecting target %s, but got %s" % (expected_event.target, actual_event.target))
            if data is not ANY:
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
                except AssertionError:
                    pass
            self.fail("expecting event %s. Got instead: %s" % (expected_event, map(str, self.evt_queue)))


    ################################################################################################################


class Test_game_events_parsing(EventParsingTestCase):

    def setUp(self):
        EventParsingTestCase.setUp(self)

    def test_player_connecting_with_unverified_guid_at_first(self):
        # GIVEN
        self.clear_events()
        # WHEN
        self.parser.routeBattleyeEvent(u'Player #8 Max (111.222.200.50:2304) connected')
        self.parser.routeBattleyeEvent(u'Player #8 Max - GUID: 73c5e50a7860475f0000000000000000 (unverified)')
        self.parser.routeBattleyeEvent(u'Verified GUID (73c5e50a7860475f0000000000000000) of player #8 Max')
        # THEN
        self.assertEqual(2, len(self.evt_queue))
        event1, event2 = self.evt_queue
        # check EVT_CLIENT_CONNECT
        self.assertEqual(self.parser.getEventID("EVT_CLIENT_CONNECT"), event1.type)
        self.assertEqual("Max", event1.client.name)
        self.assertEqual("8", event1.client.cid)
        self.assertEqual("73c5e50a7860475f0000000000000000", event1.client.guid)
        self.assertEqual("111.222.200.50", event1.client.ip)
        # check EVT_CLIENT_CONNECT
        self.assertEqual(self.parser.getEventID("EVT_CLIENT_AUTH"), event2.type)
        self.assertEqual("Max", event2.client.name)
        self.assertEqual("8", event2.client.cid)
        self.assertEqual("73c5e50a7860475f0000000000000000", event2.client.guid)
        self.assertEqual("111.222.200.50", event2.client.ip)
        # check player info in database
        client_from_db = self.parser.storage.getClient(Client(guid="73c5e50a7860475f0000000000000000"))
        self.assertIsNotNone(client_from_db)
        self.assertEqual("Max", client_from_db.name)
        self.assertEqual("73c5e50a7860475f0000000000000000", client_from_db.guid)
        self.assertEqual("111.222.200.50", client_from_db.ip)

    def test_player_connecting_with_unverified_guid_at_first_and_sync(self):
        # GIVEN
        self.clear_events()
        # WHEN
        self.parser.routeBattleyeEvent(u'Player #8 Max (111.222.200.50:2304) connected')
        self.parser.routeBattleyeEvent(u'Player #8 Max - GUID: 73c5e50a7860475f0000000000000000 (unverified)')
        when(self.parser.output).write('players').thenReturn(u'''Players on server:
[#] [IP Address]:[Port] [Ping] [GUID] [Name]
--------------------------------------------------
8   111.222.200.50:2304   -1   73c5e50a7860475f0000000000000000(?)  Max (Lobby)
(14 players in total)''')
        self.parser.sync()
        self.parser.routeBattleyeEvent(u'Verified GUID (73c5e50a7860475f0000000000000000) of player #8 Max')
        # THEN check events were raised
        self.assert_has_event("EVT_CLIENT_CONNECT")
        self.assert_has_event("EVT_CLIENT_AUTH")
        # check player info in database
        client_from_db = self.parser.storage.getClient(Client(guid="73c5e50a7860475f0000000000000000"))
        self.assertIsNotNone(client_from_db)
        self.assertEqual("Max", client_from_db.name)
        self.assertEqual("73c5e50a7860475f0000000000000000", client_from_db.guid)
        self.assertEqual("111.222.200.50", client_from_db.ip)


class test_sync(EventParsingTestCase):

    def test_new_client_with_unverified_guid(self):
        # GIVEN
        self.assertDictContainsSubset({'clients': 1}, self.parser.storage.getCounts())
        self.assertNotIn('8', self.parser.clients)
        # WHEN
        when(self.parser.output).write('players').thenReturn('''\
Players on server:
[#] [IP Address]:[Port] [Ping] [GUID] [Name]
--------------------------------------------------
8   111.222.200.50:2304   -1   73c5e50a7860475f49db400000000000(?)  Max (Lobby)
(1 players in total)
''')
        rv = self.parser.sync()
        # THEN no new client is saved to database
        self.assertDictContainsSubset({'clients': 1}, self.parser.storage.getCounts())
        # THEN sync return correct info
        self.assertIn('8', rv)
        client = rv["8"]
        self.assertEqual("Max", client.name)
        self.assertEqual("8", client.cid)
        self.assertEqual("111.222.200.50", client.ip)
        self.assertEqual('', client.guid)
        self.assertFalse(client.authed)
        # THEN connected client list is updated
        self.assertIn('8', self.parser.clients)
        client = self.parser.clients['8']
        self.assertEqual("Max", client.name)
        self.assertEqual("111.222.200.50", client.ip)
        self.assertEqual('', client.guid)
        self.assertFalse(client.authed)

    def test_connected_client_with_unverified_guid(self):
        # GIVEN
        self.parser.routeBattleyeEvent(u'Player #8 Max (111.222.200.50:2304) connected')
        self.parser.routeBattleyeEvent(u'Player #8 Max - GUID: 73c5e50a7860475f0000000000000000 (unverified)')
        self.assertDictContainsSubset({'clients': 1}, self.parser.storage.getCounts())
        self.assertIn('8', self.parser.clients)
        self.clear_events()
        # WHEN
        when(self.parser.output).write('players').thenReturn('''\
Players on server:
[#] [IP Address]:[Port] [Ping] [GUID] [Name]
--------------------------------------------------
8   111.222.200.50:2304   -1   73c5e50a7860475f49db400000000000(?)  Max (Lobby)
(1 players in total)
''')
        rv = self.parser.sync()
        # THEN no new client is saved to database
        self.assertDictContainsSubset({'clients': 1}, self.parser.storage.getCounts())
        # THEN sync return correct info
        self.assertIn('8', rv)
        client = rv["8"]
        self.assertEqual("Max", client.name)
        self.assertEqual("8", client.cid)
        self.assertEqual("111.222.200.50", client.ip)
        self.assertEqual('', client.guid)
        self.assertFalse(client.authed)
        # THEN connected client list is updated
        self.assertIn('8', self.parser.clients)
        client = self.parser.clients['8']
        self.assertEqual("Max", client.name)
        self.assertEqual("111.222.200.50", client.ip)
        self.assertEqual('', client.guid)
        self.assertFalse(client.authed)


    def test_connected_client_with_verified_guid(self):
        # GIVEN
        self.parser.routeBattleyeEvent(u'Player #8 Max (111.222.200.50:2304) connected')
        self.parser.routeBattleyeEvent(u'Player #8 Max - GUID: 73c5e50a7860475f0000000000000000 (unverified)')
        self.parser.routeBattleyeEvent(u'Verified GUID (73c5e50a7860475f0000000000000000) of player #8 Max')
        self.assertDictContainsSubset({'clients': 2}, self.parser.storage.getCounts())
        self.assertIn('8', self.parser.clients)
        # GIVEN that the player exists in database
        client_from_db = self.parser.storage.getClient(Client(guid="73c5e50a7860475f0000000000000000"))
        self.assertIsNotNone(client_from_db)
        self.assertEqual("Max", client_from_db.name)
        self.assertEqual("73c5e50a7860475f0000000000000000", client_from_db.guid)
        self.assertEqual("111.222.200.50", client_from_db.ip)
        self.clear_events()
        # WHEN
        when(self.parser.output).write('players').thenReturn('''\
Players on server:
[#] [IP Address]:[Port] [Ping] [GUID] [Name]
--------------------------------------------------
8   111.222.200.50:2304   62   73c5e50a7860475f0000000000000000(OK) Max (Lobby)
(1 players in total)
''')
        rv = self.parser.sync()
        # THEN no new client is saved to database
        self.assertDictContainsSubset({'clients': 2}, self.parser.storage.getCounts())
        # THEN sync return correct info
        self.assertIn('8', rv)
        client = rv["8"]
        self.assertEqual("Max", client.name)
        self.assertEqual("8", client.cid)
        self.assertEqual("111.222.200.50", client.ip)
        self.assertEqual('73c5e50a7860475f0000000000000000', client.guid)
        self.assertTrue(client.authed)
        # THEN connected client list is updated
        self.assertIn('8', self.parser.clients)
        client = self.parser.clients['8']
        self.assertEqual("Max", client.name)
        self.assertEqual("111.222.200.50", client.ip)
        self.assertEqual('73c5e50a7860475f0000000000000000', client.guid)
        self.assertTrue(client.authed)
        # THEN player info in database is correct
        client_from_db = self.parser.storage.getClient(Client(guid="73c5e50a7860475f0000000000000000"))
        self.assertIsNotNone(client_from_db)
        self.assertEqual("Max", client_from_db.name)
        self.assertEqual("73c5e50a7860475f0000000000000000", client_from_db.guid)
        self.assertEqual("111.222.200.50", client_from_db.ip)
