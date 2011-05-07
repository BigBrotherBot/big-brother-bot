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
from b3.clients import Clients
from test import B3TestCase
import b3
import unittest


class TestClients(B3TestCase):
    clients = None
    joe = None
    
    def setUp(self):
        B3TestCase.setUp(self)
        self.clients = Clients(b3.console)
        self.clients.newClient(1, name='joe')
        self.clients.newClient(2, name=' H a    x\t0r')
        
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


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
