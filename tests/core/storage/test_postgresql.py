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

import os

import nose
import unittest2 as unittest

from b3.functions import splitDSN
from b3.storage.postgresql import PostgresqlStorage
from tests import B3TestCase
from tests.core.storage.common import StorageAPITest

"""
    NOTE: you can customize the PostgreSQL host, database and credential using the following
    environment variables :
        POSTGRESQL_TEST_HOST
        POSTGRESQL_TEST_USER
        POSTGRESQL_TEST_PASSWORD
        POSTGRESQL_TEST_DB

    Make sure to execute this query (with adjusted parameters) before running tests:
        >>> CREATE ROLE b3test WITH PASSWORD 'test' LOGIN CREATEDB;
"""

POSTGRESQL_TEST_HOST = os.environ.get('POSTGRESQL_TEST_HOST', 'localhost')
POSTGRESQL_TEST_USER = os.environ.get('POSTGRESQL_TEST_USER', 'b3test')
POSTGRESQL_TEST_PASSWORD = os.environ.get('POSTGRESQL_TEST_PASSWORD', 'test')
POSTGRESQL_TEST_DB = os.environ.get('POSTGRESQL_TEST_DB', 'b3_test')

#===============================================================================
#
# Test if we can run the PostgreSQL tests
#
#===============================================================================

is_postgresql_ready = True
no_postgresql_reason = ''

try:
    import psycopg2
except ImportError:
    psycopg2 = None
    is_postgresql_ready = False
    no_postgresql_reason = "no psycopg2 module available"
else:
    try:
        psycopg2.connect(host=POSTGRESQL_TEST_HOST,
                         user=POSTGRESQL_TEST_USER,
                         password=POSTGRESQL_TEST_PASSWORD,
                         database='postgres')
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

@unittest.skipIf(not is_postgresql_ready, no_postgresql_reason)
class Test_PostgreSQL(B3TestCase, StorageAPITest):

    def setUp(self):
        """this method is called before each test"""
        B3TestCase.setUp(self)

        try:
            dsn = "postgresql://%s:%s@%s/%s" % (POSTGRESQL_TEST_USER, POSTGRESQL_TEST_PASSWORD, POSTGRESQL_TEST_HOST, POSTGRESQL_TEST_DB)
            self.storage = self.console.storage = PostgresqlStorage(dsn, splitDSN(dsn), self.console)
            self.storage.connect()

            tables = self.storage.getTables()
            if tables:
                # dont remove the groups table since we would need it in next tests
                tables.remove('groups')
                self.storage.truncateTable(tables)
        except Exception, e:
            self.fail("Error: %s" % e)

    def tearDown(self):
        """this method is called after each test"""
        B3TestCase.tearDown(self)
        self.storage.shutdown()

if __name__ == '__main__':
    nose.main()

