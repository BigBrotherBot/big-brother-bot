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

import b3

from b3.clients import Clients, Client
from tests import B3TestCase
from mock import Mock, patch


class TestClients(B3TestCase):
    clients = None
    joe = None
    
    def setUp(self):
        B3TestCase.setUp(self)
        Clients.authorizeClients = Mock()
        self.clients = self.console.clients
        self.clients.newClient(1, name='joe', guid="joe_guid")
        self.clients.newClient(2, name=' H a    x\t0r', guid="haxor_guid")


    def test_getClientsByName(self):
        clients = self.clients.getClientsByName('joe')
        self.assertEqual(1, len(clients))
        self.assertEqual(1, clients[0].cid)
        
        clients = self.clients.getClientsByName('oe')
        self.assertEqual(1, len(clients))
        self.assertEqual(1, clients[0].cid)
        
        clients = self.clients.getClientsByName('hax')
        self.assertEqual(1, len(clients))
        self.assertEqual(2, clients[0].cid)
        
        clients = self.clients.getClientsByName('qsdfqsdf fqsd fsqd fsd f')
        self.assertEqual([], clients)

    def test_getByDB_when_client_connected(self):
        # GIVEN
        haxor = self.clients[2]
        self.assertIsNotNone(haxor.cid)
        self.assertIsNotNone(haxor.id)
        # WHEN
        clients = self.clients.getByDB('@%s' % haxor.id)
        # THEN
        self.assertEqual(1, len(clients))
        found_client = clients[0]
        self.assertEqual(haxor.id, found_client.id)
        self.assertEqual(2, found_client.cid)
        self.assertEqual(self.console, found_client.console)
        self.assertEqual('H a    x\t0r', found_client.name)
        self.assertEqual(' H a    x\t0r^7', found_client.exactName)

    def test_getByDB_when_client_disconnected(self):
        # GIVEN
        haxor = self.clients[2]
        haxor.disconnect()
        self.assertNotIn(2, self.clients)
        self.assertIsNotNone(haxor.id)
        # WHEN
        clients = self.clients.getByDB('@%s' % haxor.id)
        # THEN
        self.assertEqual(1, len(clients))
        found_client = clients[0]
        self.assertEqual(haxor.id, found_client.id)
        self.assertIsNone(found_client.cid)
        self.assertEqual(self.console, found_client.console)
        self.assertEqual('H a    x\t0r', found_client.name)
        self.assertEqual('H a    x\t0r^7', found_client.exactName)


    @patch.object(b3.events, 'Event')
    def test_disconnect(self, Event_mock):
        joe = self.clients.getByCID(1)
        self.assertIsInstance(joe, Client)
        self.assertTrue(1 in self.clients)
        self.assertEqual(joe, self.clients[1])

        self.assertEqual(2, len(self.clients))
        self.clients.disconnect(joe)
        self.assertEqual(1, len(self.clients))

        # verify that the Client object is removed from Clients
        self.assertFalse(1 in self.clients)
        self.assertIsNone(self.clients.getByCID(1))
        self.assertIsNone(self.clients.getByName('joe'))

        # verify that an proper event was fired
        Event_mock.assert_called_once_with(b3.events.EVT_CLIENT_DISCONNECT, 1, joe, None)
