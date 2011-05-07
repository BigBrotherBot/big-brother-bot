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
import b3
import unittest
from test import B3TestCase
 
class Test_Client(B3TestCase):
    
    def test_construct(self):
        c = Client(name="Courgette", guid="1234567890")
        self.assertEqual(c.name, "Courgette")
        self.assertEqual(c.exactName, "Courgette^7")
        self.assertEqual(c.guid, "1234567890")
        self.assertEqual(c.team, b3.TEAM_UNKNOWN)
        self.assertTrue(c.connected)
        self.assertFalse(c.hide)
        self.assertEqual(c.ip, '')
        self.assertEqual(c.greeting, '')
        self.assertEqual(c.pbid, '')

    def test_team(self):
        m = Mock()
        c = Client(team=m)
        self.assertEqual(c.team, m)
        
    def test_team_change(self):
        b3.console = Mock()
        c = Client(console=b3.console)
        c.team = 24
        self.assertEqual(c.team, 24)
        b3.console.queueEvent.assert_called()
        args = b3.console.queueEvent.call_args
        eventraised = args[0][0]
        self.assertEquals(eventraised.type, b3.events.EVT_CLIENT_TEAM_CHANGE)
        self.assertEquals(eventraised.data, 24)

    def test_name_change(self):
        c = Client(console=b3.console, authed=True)
        c.name = "cucurb"
        self.assertEqual(c.name, "cucurb")
        b3.console.queueEvent.assert_called()
        args = b3.console.queueEvent.call_args
        eventraised = args[0][0]
        self.assertEquals(eventraised.type, b3.events.EVT_CLIENT_NAME_CHANGE)
        self.assertEquals(eventraised.data, 'cucurb')

    def test_makeAlias_new(self):
        c = Client(console=b3.console)
        c.id = 123
        c.name = "foo"
        b3.console.storage.getClientAlias.side_effect = KeyError()
        c.makeAlias("bar")
        self.assertEquals(b3.console.storage.getClientAlias.call_count, 1)
        alias = b3.console.storage.getClientAlias.call_args[0][0]
        self.assertIsInstance(alias, b3.clients.Alias)
        self.assertEqual(alias.alias, "bar")
        self.assertEqual(alias.numUsed, 1)

    def test_makeAlias_existing(self):
        c = Client(console=b3.console)
        c.id = 123
        c.name = "foo"
        aliasFoo = b3.clients.Alias()
        aliasFoo.alias = "foo"
        aliasFoo.clientId = c.id
        aliasFoo.numUsed = 48
        b3.console.storage.getClientAlias.side_effect = lambda x: aliasFoo
        c.makeAlias("whatever")
        self.assertEquals(b3.console.storage.getClientAlias.call_count, 1)
        self.assertIsInstance(aliasFoo, b3.clients.Alias)
        self.assertEqual(aliasFoo.alias, "foo")
        self.assertEqual(aliasFoo.numUsed, 49)


    def test_guid_readonly(self):
        c = Client(console=b3.console)
        self.assertFalse(c.authed)
        c.guid = "foo"
        self.assertEqual(c.guid, "foo")
        c.auth()
        self.assertTrue(c.authed)
        # upon guid change, prevent change and consider client not
        # authed anymore
        c.guid = "bar"
        self.assertFalse(c.authed)
        c.guid = "foo"


if __name__ == '__main__':
    unittest.main()