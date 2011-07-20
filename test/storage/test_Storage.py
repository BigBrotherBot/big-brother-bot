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
from b3.storage import Storage
from b3.storage.database import DatabaseStorage
from mock import Mock
from test import B3TestCase
import b3.storage
import unittest

class Test_Storage(B3TestCase):
    storage = None

    def setUp(self):
        self.storage = b3.storage.Storage()

    def test_getCounts(self):
        self.assertRaises(NotImplementedError, self.storage.getCounts)

    def test_getClient(self):
        self.assertRaises(NotImplementedError, self.storage.getClient, Mock())

    def test_getClientsMatching(self):
        self.assertRaises(NotImplementedError, self.storage.getClientsMatching, Mock())

    def test_setClient(self):
        self.assertRaises(NotImplementedError, self.storage.setClient, Mock())

    def test_setClientAlias(self):
        self.assertRaises(NotImplementedError, self.storage.setClientAlias, Mock())

    def test_getClientAlias(self):
        self.assertRaises(NotImplementedError, self.storage.getClientAlias, Mock())

    def test_getClientAliases(self):
        self.assertRaises(NotImplementedError, self.storage.getClientAliases, Mock())

    def test_setClientIpAddresse(self):
        self.assertRaises(NotImplementedError, self.storage.setClientIpAddresse, Mock())

    def test_getClientIpAddress(self):
        self.assertRaises(NotImplementedError, self.storage.getClientIpAddress, Mock())

    def test_getClientIpAddresses(self):
        self.assertRaises(NotImplementedError, self.storage.getClientIpAddresses, Mock())

    def test_setClientPenalty(self):
        self.assertRaises(NotImplementedError, self.storage.setClientPenalty, Mock())

    def test_getClientPenalty(self):
        self.assertRaises(NotImplementedError, self.storage.getClientPenalty, Mock())

    def test_getClientPenalties(self):
        self.assertRaises(NotImplementedError, self.storage.getClientPenalties, Mock())

    def test_getClientLastPenalty(self):
        self.assertRaises(NotImplementedError, self.storage.getClientLastPenalty, Mock())

    def test_getClientFirstPenalty(self):
        self.assertRaises(NotImplementedError, self.storage.getClientFirstPenalty, Mock())

    def test_disableClientPenalties(self):
        self.assertRaises(NotImplementedError, self.storage.disableClientPenalties, Mock())

    def test_numPenalties(self):
        self.assertRaises(NotImplementedError, self.storage.numPenalties, Mock())

    def test_getGroups(self):
        self.assertRaises(NotImplementedError, self.storage.getGroups)

    def test_getGroup(self):
        self.assertRaises(NotImplementedError, self.storage.getGroup, Mock())


class Test_getStorage(unittest.TestCase):
    def test_Database(self):
        DatabaseStorage.__init__ = Mock(return_value=None)
        storage = b3.storage.getStorage('database')
        self.assertIsInstance(storage, DatabaseStorage)

    def test_empty(self):
        Storage.__init__ = Mock(return_value=None)
        storage = b3.storage.getStorage('')
        self.assertIsInstance(storage, Storage)

