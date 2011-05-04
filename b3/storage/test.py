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
from b3.clients import IpAlias
from b3.storage.database import DatabaseStorage
from mock import Mock
import time
import unittest

__author__  = 'Courgette'
__version__ = '1.0.0'

"""
Requires : mock module from http://www.voidspace.org.uk/python/mock/
"""


class TestMySQLDatabaseStorage(unittest.TestCase):
    """
    NOTE: to work properly you must be running a MySQL database on localhost
    which must have a user named 'b3test' with password 'test' which has 
    all privileges over a table (already created or not) named 'b3_test'
    """

    def setUp(self):
        """this method is called before each test"""
        import MySQLdb
        db = MySQLdb.connect(host='localhost', user='b3test', passwd='test') 
        db.query("DROP DATABASE IF EXISTS b3_test")
        db.query("CREATE DATABASE b3_test CHARACTER SET utf8;")
        self.console = Mock()
        self.console.screen = Mock()
        self.console.time = time.time
        self.storage = self.console.storage = DatabaseStorage('mysql://b3test:test@localhost/b3_test', self.console)
        self.storage.executeSql("@b3/sql/b3.sql")

    def tearDown(self):
        """this method is called after each test"""
        self.storage.query("DROP DATABASE b3_test")

    def test_setClientIpAddresse(self):
        ipalias_id = self.storage.setClientIpAddresse(IpAlias(ip='1.2.3.4', clientId=1))
        self.assertEqual(ipalias_id, 1)
        ipalias_id = self.storage.setClientIpAddresse(IpAlias(ip='127.0.0.1', clientId=1))
        self.assertEqual(ipalias_id, 2)

    def test_getClientIpAddresse(self):
        ipalias = IpAlias(ip='88.44.55.22', timeAdd=12, timeEdit=654, numUsed=7, clientId=54)
        ipalias_id = self.storage.setClientIpAddresse(ipalias)
        ipalias = self.storage.getClientIpAddress(IpAlias(id=ipalias_id))
        self.assertIsInstance(ipalias, IpAlias)
        self.assertEqual(ipalias.ip, '88.44.55.22')
        self.assertEqual(ipalias.timeAdd, 12)
        self.assertEqual(ipalias.timeEdit, 654)
        self.assertEqual(ipalias.numUsed, 7)
        self.assertEqual(ipalias.clientId, 54)

    def test_getClientIpAddress(self):
        client = Mock()
        client.id = 15
        self.storage.setClientIpAddresse(IpAlias(ip='44.44.44.44', clientId=client.id))
        self.storage.setClientIpAddresse(IpAlias(ip='55.55.55.55', clientId=client.id))
        self.storage.setClientIpAddresse(IpAlias(ip='66.66.66.66', clientId=0))
        ipaliases = self.storage.getClientIpAddresses(client)
        self.assertIsInstance(ipaliases, list)
        self.assertEqual(len(ipaliases), 2)
        ips = []
        for i in ipaliases:
            self.assertIsInstance(i, IpAlias)
            self.assertEqual(i.clientId, client.id)
            self.assertNotEqual(i.id, None)
            self.assertNotEqual(i.ip, None)
            self.assertNotEqual(i.timeAdd, None)
            self.assertNotEqual(i.timeEdit, None)
            self.assertNotEqual(i.numUsed, None)
            ips.append(i.ip)
        self.assertIn('44.44.44.44', ips)
        self.assertIn('55.55.55.55', ips)
        self.assertNotIn('66.66.66.66', ips)
        
        


if __name__ == '__main__':
    unittest.main()
    