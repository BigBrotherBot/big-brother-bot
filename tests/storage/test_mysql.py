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
from tests import B3TestCase
from tests.storage.common import StorageAPITest
import b3
import nose
import unittest

"""
    NOTE: to work properly you must be running a MySQL database on localhost
    which must have a user named 'b3test' with password 'test' which has 
    all privileges over a table (already created or not) named 'b3_test'
"""
MYSQL_DB = 'mysql://b3test:test@localhost/b3_test'
MYSQL_HOST = 'localhost'
MYSQL_USER = 'b3test'
MYSQL_PASSWORD = 'test'

#===============================================================================
# 
# Test if we can run the MySQL tests
#
#===============================================================================

is_mysql_ready = True
no_mysql_reason = ''

try:
    import MySQLdb
except ImportError:
    is_mysql_ready = False
    no_mysql_reason = "no MySQLdb module available"

try:
    MySQLdb.connect(host=MYSQL_HOST, user=MYSQL_USER, passwd=MYSQL_PASSWORD)
except MySQLdb.Error, err:
    is_mysql_ready = False
    no_mysql_reason = "%s" % err[1]
except Exception, err:
    is_mysql_ready = False
    no_mysql_reason = "%s" % err


#===============================================================================
# 
# Load the tests
# 
#===============================================================================
@unittest.skipIf(not is_mysql_ready, no_mysql_reason)
class Test_MySQL(B3TestCase, StorageAPITest):

    def setUp(self):
        """this method is called before each test"""
        B3TestCase.setUp(self)
        try:
            db = MySQLdb.connect(host='localhost', user='b3test', passwd='test')
        except MySQLdb.OperationalError, message:
            self.fail("Error %d:\n%s" % (message[0], message[1]))
        db.query("DROP DATABASE IF EXISTS b3_test")
        db.query("CREATE DATABASE b3_test CHARACTER SET utf8;")
        self.storage = b3.console.storage = DatabaseStorage(MYSQL_DB, b3.console)
        self.storage.executeSql("@b3/sql/b3.sql")

    def tearDown(self):
        """this method is called after each test"""
        B3TestCase.tearDown(self)
        self.storage.query("DROP DATABASE b3_test")
        self.storage.shutdown()


if __name__ == '__main__':
    nose.main()
    
    