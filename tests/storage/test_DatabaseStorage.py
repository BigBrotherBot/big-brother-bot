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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
#

import b3
import os
import unittest2 as unittest

from b3.clients import Client
from b3.storage.database import DatabaseStorage
from mock import Mock
from mock import patch
from mock import sentinel
from mockito import when
from mockito import any as ANY

# checks whether we can perform tests on SQL script file parsing
B3_SQL_FILE_AVAILABLE = os.path.exists(b3.getAbsolutePath("@b3/sql/b3.sql"))
B3_DB_SQL_FILE_AVAILABLE = os.path.exists(b3.getAbsolutePath("@b3/sql/b3-db.sql"))
B3_DEFAULT_TABLES = ['aliases' ,'clients', 'data', 'groups', 'ipaliases', 'penalties']

class Test_DatabaseStorage(unittest.TestCase):

    def test_construct(self):
        storage = DatabaseStorage('foo://bar', Mock())
        storage.connect()
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


    def test_getConnection_mysql(self):
        # mock the MySQLdb module so we can test in an environement which does not have this module installed
        mock_MySQLdb = Mock()
        mock_MySQLdb.connect = Mock(return_value=sentinel)
        with patch.dict('sys.modules', {'MySQLdb': mock_MySQLdb}):

            # verify that a correct dsn does work as expected
            mock_MySQLdb.connect.reset_mock()
            storage = DatabaseStorage("mysql://someuser:somepasswd@somehost:someport/somedbname", Mock())
            when(storage).getTables().thenReturn(B3_DEFAULT_TABLES)
            storage.connect()
            assert mock_MySQLdb.connect.called, "expecting MySQLdb.connect to be called"
            self.assertEqual(sentinel, storage.db)

            # verify that B3 creates necessary tables when they are missing
            mock_MySQLdb.connect.reset_mock()
            storage = DatabaseStorage("mysql://someuser:somepasswd@somehost:someport/somedbname", Mock())
            when(storage).getTables().thenReturn([])
            storage.queryFromFile = Mock()
            storage.connect()
            assert storage.queryFromFile.called, "expecting MySQLdb.queryFromFile to be called"
            self.assertEqual(sentinel, storage.db)

            # verify that whenever B3 is not able to create necessary tables, it stops
            mock_MySQLdb.connect.reset_mock()
            console_mock = Mock()
            storage = DatabaseStorage("mysql://someuser:somepasswd@somehost:someport/somedbname", console_mock)
            when(storage).getTables().thenReturn([])
            when(storage).queryFromFile(ANY()).thenRaise(Exception())
            storage.connect()
            assert console_mock.critical.called
            self.assertIn("Missing MySQL database tables", console_mock.critical.call_args[0][0])
            self.assertIsNone(storage.db)

            # verify that an incorrect dsn does fail an stops the bot with a nice error message
            mock_MySQLdb.connect.reset_mock()
            console_mock = Mock()
            storage = DatabaseStorage("mysql://someuser:somepasswd@somehost:3446/", console_mock)
            storage.connect()
            assert console_mock.critical.called
            self.assertIn("Missing MySQL database name", console_mock.critical.call_args[0][0])
            assert not mock_MySQLdb.connect.called, "expecting MySQLdb.connect not to be called"
            self.assertIsNone(storage.db)

            # verify that an incorrect dsn does fail an stops the bot with a nice error message
            mock_MySQLdb.connect.reset_mock()
            console_mock = Mock()
            storage = DatabaseStorage("mysql://someuser:somepasswd@/database", console_mock)
            storage.connect()
            assert console_mock.critical.called
            self.assertIn("Invalid MySQL host", console_mock.critical.call_args[0][0])
            assert not mock_MySQLdb.connect.called, "expecting MySQLdb.connect not to be called"
            self.assertIsNone(storage.db)

    @unittest.skipUnless(B3_SQL_FILE_AVAILABLE, "B3 SQL script not found @ %s" % b3.getAbsolutePath("@b3/sql/b3.sql"))
    def test_b3_sql_file_parsing(self):
        with open(b3.getAbsolutePath("@b3/sql/b3.sql"), 'r') as sql_file:
            statements = DatabaseStorage._parse_statements(sql_file)
            self.assertEqual(27, len(statements))

    @unittest.skipUnless(B3_DB_SQL_FILE_AVAILABLE, "B3 DB SQL script not found @ %s" % b3.getAbsolutePath("@b3/sql/b3-db.sql"))
    def test_b3_db_sql_file_parsing(self):
        with open(b3.getAbsolutePath("@b3/sql/b3-db.sql"), 'r') as sql_file:
            statements = DatabaseStorage._parse_statements(sql_file)
            self.assertEqual(2, len(statements))