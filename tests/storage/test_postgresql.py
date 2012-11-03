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
import nose
import unittest2 as unittest

"""
    NOTE: to work properly you must be running a PostgreSQL database on localhost
    which must have a user named 'b3test' with password 'test' which has 
    all privileges over a table (already created or not) named 'b3_test'
"""
POSTGRESQL_DB = 'postgresql://b3test:test@localhost/b3_test'
POSTGRESQL_HOST = 'localhost'
POSTGRESQL_USER = 'b3test'
POSTGRESQL_PASSWORD = 'test'

#===============================================================================
# 
# Test if we can run the MySQL tests
#
#===============================================================================

is_postgresql_ready = True
no_postgresql_reason = ''

try:
    import psycopg2
except ImportError:
    is_postgresql_ready = False
    no_postgresql_reason = "no psycopg2 module available"
else:
    try:
        psycopg2.connect(host=POSTGRESQL_HOST, user=POSTGRESQL_USER, password=POSTGRESQL_PASSWORD, database='postgres')
    except psycopg2.Error, err:
        is_postgresql_ready = False
        no_postgresql_reason = "%r" % err
    except Exception, err:
        is_postgresql_ready = False
        no_postgresql_reason = "%r" % err


#===============================================================================
# 
# Load the tests
# 
#===============================================================================
@unittest.skip('work in progress')
@unittest.skipIf(not is_postgresql_ready, no_postgresql_reason)
class Test_PostgreSQL(B3TestCase, StorageAPITest):

    def setUp(self):
        """this method is called before each test"""
        B3TestCase.setUp(self)
        try:
            conn = psycopg2.connect(host='localhost', user='b3test', password='test', database='postgres')
        except psycopg2.OperationalError, message:
            self.fail("Error %d:\n%s" % (message[0], message[1]))
        conn.set_isolation_level(0)
        cursor = conn.cursor()
        cursor.execute("DROP DATABASE IF EXISTS b3_test;")
        cursor.execute("CREATE DATABASE b3_test WITH OWNER = b3test ENCODING = 'UTF8';")
        self.storage = self.console.storage = DatabaseStorage(POSTGRESQL_DB, self.console)
        self.storage.executeSql("@b3/sql/postgresql/b3.sql")

    def tearDown(self):
        """this method is called after each test"""
        B3TestCase.tearDown(self)
        self.storage.query("DROP DATABASE b3_test")
        self.storage.shutdown()


if __name__ == '__main__':
    nose.main()
    
    