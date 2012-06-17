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
from b3.clients import Client
from mock import Mock
from b3 import TEAM_UNKNOWN
from b3.clients import Alias, IpAlias
from b3.events import EVT_CLIENT_NAME_CHANGE, EVT_CLIENT_TEAM_CHANGE
import unittest2 as unittest
from tests import B3TestCase
 
class Test_Client(B3TestCase):
    
    def setUp(self):
        B3TestCase.setUp(self)
        self.client = Client(console=self.console)
    
    def test_construct(self):
        c = Client(name="Courgette", guid="1234567890")
        self.assertEqual(c.name, "Courgette")
        self.assertEqual(c.exactName, "Courgette^7")
        self.assertEqual(c.guid, "1234567890")
        self.assertEqual(c.team, TEAM_UNKNOWN)
        self.assertTrue(c.connected)
        self.assertFalse(c.hide)
        self.assertEqual(c.ip, '')
        self.assertEqual(c.greeting, '')
        self.assertEqual(c.pbid, '')

    def test_team(self):
        m = Mock()
        self.client.team = m
        self.assertEqual(self.client.team, m)
        
    def test_team_change(self):
        self.console.queueEvent = Mock()
        self.client.team = 24
        self.assertEqual(self.client.team, 24)
        self.console.queueEvent.assert_called()
        args = self.console.queueEvent.call_args
        eventraised = args[0][0]
        self.assertEquals(eventraised.type, EVT_CLIENT_TEAM_CHANGE)
        self.assertEquals(eventraised.data, 24)

    def test_name_change(self):
        self.console.queueEvent = Mock()
        self.client.authed = True
        self.client.name = "cucurb"
        self.assertEqual(self.client.name, "cucurb")
        self.console.queueEvent.assert_called()
        args = self.console.queueEvent.call_args
        eventraised = args[0][0]
        self.assertEquals(eventraised.type, EVT_CLIENT_NAME_CHANGE)
        self.assertEquals(eventraised.data, 'cucurb')

    def test_makeAlias_new(self):
        self.client.id = 123
        self.console.storage.getClientAlias = Mock(side_effect = KeyError())
        self.client.makeAlias("bar")
        self.assertEquals(self.console.storage.getClientAlias.call_count, 1)
        alias = self.console.storage.getClientAlias.call_args[0][0]
        self.assertIsInstance(alias, Alias)
        self.assertEqual(alias.alias, "bar")
        self.assertEqual(alias.numUsed, 1)

    def test_makeAlias_existing(self):
        self.client.id = 123
        aliasFoo = Alias()
        aliasFoo.alias = "foo"
        aliasFoo.clientId = self.client.id
        aliasFoo.numUsed = 48
        self.console.storage.getClientAlias = Mock(side_effect = lambda x: aliasFoo)
        self.client.makeAlias("whatever")
        self.assertEquals(self.console.storage.getClientAlias.call_count, 1)
        self.assertIsInstance(aliasFoo, Alias)
        self.assertEqual(aliasFoo.alias, "foo")
        self.assertEqual(aliasFoo.numUsed, 49)

    def test_guid_readonly(self):
        self.assertFalse(self.client.authed)
        self.client.guid = "foo"
        self.assertEqual(self.client.guid, "foo")
        self.client.auth()
        self.assertTrue(self.client.authed)
        # upon guid change, prevent change and consider client not
        # authed anymore
        self.client.guid = "bar"
        self.assertFalse(self.client.authed)
        self.client.guid = "foo"

    def test_set_ip(self):
        self.client.ip = "1.2.3.4"
        self.assertEqual(self.client._ip, "1.2.3.4")
        self.client.ip = "5.6.7.8:27960"
        self.assertEqual(self.client._ip, "5.6.7.8")
        
    def test_makeIpAlias_new(self):
        self.client.id = 123
        self.console.storage.getClientIpAddress = Mock(side_effect = KeyError())
        self.client.makeIpAlias("1.4.7.8")
        self.assertEquals(self.console.storage.getClientIpAddress.call_count, 1)
        alias = self.console.storage.getClientIpAddress.call_args[0][0]
        self.assertIsInstance(alias, IpAlias)
        self.assertEqual(alias.ip, "1.4.7.8")
        self.assertEqual(alias.numUsed, 1)

    def test_makeIpAlias_existing(self):
        self.client.id = 123
        aliasFoo = IpAlias()
        aliasFoo.ip = "9.5.4.4"
        aliasFoo.clientId = self.client.id
        aliasFoo.numUsed = 8
        self.console.storage.getClientIpAddress = Mock(side_effect = lambda x: aliasFoo)
        self.client.makeIpAlias("whatever")
        self.assertEquals(self.console.storage.getClientIpAddress.call_count, 1)
        self.assertIsInstance(aliasFoo, IpAlias)
        self.assertEqual(aliasFoo.ip, "9.5.4.4")
        self.assertEqual(aliasFoo.numUsed, 9)


if __name__ == '__main__':
    unittest.main()