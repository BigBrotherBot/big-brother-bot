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
import os
import unittest2 as unittest

from b3.clients import Client
from b3.functions import splitDSN
from b3.storage.common import DatabaseStorage
from b3.storage.mysql import MysqlStorage
from mock import Mock
from mock import patch
from mock import sentinel
from mockito import when
from mockito import any as ANY

# checks whether we can perform tests on SQL script file parsing
B3_SQL_FILE_AVAILABLE = os.path.exists(b3.getAbsolutePath("@b3/sql/mysql/b3.sql"))
B3_DB_SQL_FILE_AVAILABLE = os.path.exists(b3.getAbsolutePath("@b3/sql/mysql/b3-db.sql"))
B3_DEFAULT_TABLES = ['aliases' ,'clients', 'data', 'groups', 'ipaliases', 'penalties']

class Test_DatabaseStorage(unittest.TestCase):

    def test_construct(self):
        self.assertRaises(AttributeError, MysqlStorage, 'foo://bar', splitDSN('foo://bar'), Mock())

    def test_getClient_connectionfailed(self):
        mock_storage = Mock(spec=MysqlStorage)
        mock_storage.getClient = MysqlStorage.getClient
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
        # mock the pymysql module so we can test in an environement which does not have this module installed
        dsn = "mysql://someuser:somepasswd@somehost:someport/somedbname"
        mock_pymysql = Mock()
        mock_pymysql.connect = Mock(return_value=sentinel)
        with patch.dict('sys.modules', {'pymysql': mock_pymysql}):

            # verify that a correct dsn does work as expected
            mock_pymysql.connect.reset_mock()
            storage = MysqlStorage(dsn, splitDSN(dsn), Mock())
            when(storage).getTables().thenReturn(B3_DEFAULT_TABLES)
            storage.connect()
            assert mock_pymysql.connect.called, "expecting pymysql.connect to be called"
            self.assertEqual(sentinel, storage.db)

            # verify that B3 creates necessary tables when they are missing
            mock_pymysql.connect.reset_mock()
            storage = MysqlStorage(dsn, splitDSN(dsn), Mock())
            when(storage).getTables().thenReturn([])
            storage.queryFromFile = Mock()
            storage.connect()
            assert storage.queryFromFile.called, "expecting MysqlStorage.queryFromFile to be called"
            self.assertEqual(sentinel, storage.db)

            # verify that whenever B3 is not able to create necessary tables, it stops
            mock_pymysql.connect.reset_mock()
            console_mock = Mock()
            console_mock.critical = Mock()
            storage = MysqlStorage(dsn, splitDSN(dsn), console_mock)
            storage.shutdown = Mock()
            when(storage).getTables().thenReturn([])
            when(storage).queryFromFile(ANY()).thenRaise(Exception())
            storage.connect()
            assert storage.shutdown.called, "expecting MysqlStorage.shutdown to be called"
            assert console_mock.critical.called, "expecting console_mock.critical to be called"
            self.assertIn("Missing MySQL database tables", console_mock.critical.call_args[0][0])

    @unittest.skipUnless(B3_SQL_FILE_AVAILABLE, "B3 SQL script not found @ %s" % b3.getAbsolutePath("@b3/sql/b3.sql"))
    def test_b3_sql_file_parsing(self):
        with open(b3.getAbsolutePath("@b3/sql/mysql/b3.sql"), 'r') as sql_file:
            statements = DatabaseStorage.getQueriesFromFile(sql_file)
            self.assertEqual(14, len(statements))

    @unittest.skipUnless(B3_DB_SQL_FILE_AVAILABLE, "B3 DB SQL script not found @ %s" % b3.getAbsolutePath("@b3/sql/b3-db.sql"))
    def test_b3_db_sql_file_parsing(self):
        with open(b3.getAbsolutePath("@b3/sql/mysql/b3-db.sql"), 'r') as sql_file:
            statements = DatabaseStorage.getQueriesFromFile(sql_file)
            self.assertEqual(2, len(statements))