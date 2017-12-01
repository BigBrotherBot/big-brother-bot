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

import nose

from b3.functions import splitDSN
from b3.storage.sqlite import SqliteStorage
from tests import B3TestCase
from tests.core.storage.common import StorageAPITest

SQLITE_DB = ":memory:"
#SQLITE_DB = "c:/Users/Thomas/b3.db"

class Test_sqlite(B3TestCase, StorageAPITest):

    def setUp(self):
        """this method is called before each test"""
        B3TestCase.setUp(self)
        self.storage = self.console.storage = SqliteStorage('sqlite://' + SQLITE_DB, splitDSN('sqlite://' + SQLITE_DB), self.console)
        self.storage.connect()
        #self.storage.queryFromFile("@b3/sql/sqlite/b3.sql")

    def tearDown(self):
        """this method is called after each test"""
        B3TestCase.tearDown(self)
        self.storage.shutdown()

    def test_getTables(self):
        self.assertSetEqual(set(
            ['sqlite_sequence',
             'aliases',
             'ipaliases',
             'clients',
             'groups',
             'penalties',
             'data',
            ]), set(self.storage.getTables()))

if __name__ == '__main__':
    nose.main()
    
    