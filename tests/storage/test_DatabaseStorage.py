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
from b3.storage.database import DatabaseStorage
from mock import Mock
import unittest

class Test_DatabaseStorage(unittest.TestCase):

    def test_construct(self):
        storage = DatabaseStorage('foo://bar', Mock())
        self.assertRaises(Exception, storage.getConnection)
        
        
    def test_getClient_connectionfailed(self):
        mock_storage = Mock(spec=DatabaseStorage)
        mock_storage.getClient = DatabaseStorage.getClient
        mock_storage.db = None
        mock_storage.query = Mock(return_value=None)
        mock_storage.console = Mock()
        mock_storage.console.config = Mock()
        mock_storage.console.config.get = Mock(return_value="123,myname,100")
        
        mock_storage.console.config.has_option = Mock(return_value=True)
        c1 = Client()
        c2 = mock_storage.getClient(mock_storage, c1)
        self.assertIs(c2, c1)
        self.assertEqual(123, c1.id)
        self.assertEqual("myname", c1.name)
        self.assertEqual(100, c1._tempLevel)
        
        mock_storage.console.config.has_option = Mock(return_value=False)
        self.assertRaises(KeyError, mock_storage.getClient, mock_storage, Mock())
