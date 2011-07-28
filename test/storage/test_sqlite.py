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
from b3.storage.database import DatabaseStorage
from test import B3TestCase
from test.storage.common import StorageAPITest
import b3
import nose

SQLITE_DB = ":memory:"
#SQLITE_DB = "c:/Users/Thomas/b3.db"

class Test_sqlite(B3TestCase, StorageAPITest):
    """
    NOTE: to work properly you must be running a MySQL database on localhost
    which must have a user named 'b3test' with password 'test' which has 
    all privileges over a table (already created or not) named 'b3_test'
    """

    def setUp(self):
        """this method is called before each test"""
        B3TestCase.setUp(self)
        self.storage = b3.console.storage = DatabaseStorage('sqlite://'+SQLITE_DB, b3.console)
        self.storage.executeSql("@b3/sql/sqlite/b3.sql")

    def tearDown(self):
        """this method is called after each test"""
        B3TestCase.tearDown(self)
        self.storage.shutdown()


if __name__ == '__main__':
    nose.main()
    
    