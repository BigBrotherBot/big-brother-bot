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

from b3 import functions
import unittest2 as unittest
    
class TestSplitDSN(unittest.TestCase):
    def assertDsnEqual(self, url, expected):
        tmp = functions.splitDSN(url)
        self.assertEqual(tmp, expected)

    def test_sqlite(self):
        self.assertDsnEqual('sqlite://c|/mydatabase/test.db', 
        {'protocol': 'sqlite', 'host': 'c|', 'user': None, 
        'path': '/mydatabase/test.db', 'password': None, 'port': None })

    def test_ftp(self):
        self.assertDsnEqual('ftp://username@domain.com/index.html', 
        {'protocol': 'ftp', 'host': 'domain.com', 'user': 'username', 
         'path': '/index.html', 'password': None, 'port': 21 })
        
    def test_ftp2(self):
        self.assertDsnEqual('ftp://username:password@domain.com/index.html', 
        {'protocol': 'ftp', 'host': 'domain.com', 'user': 'username', 
         'path': '/index.html', 'password': 'password', 'port': 21 })
        
    def test_ftp3(self):
        self.assertDsnEqual('ftp://username@domain.com:password@domain.com/index.html', 
        {'protocol': 'ftp', 'host': 'domain.com', 'user': 'username@domain.com', 
         'path': '/index.html', 'password': 'password', 'port': 21 })
        
    def test_ftp4(self):
        self.assertDsnEqual('ftp://username@domain.com:password@domain.com:2121/index.html', 
        {'protocol': 'ftp', 'host': 'domain.com', 'user': 'username@domain.com', 
         'path': '/index.html', 'password': 'password', 'port': 2121 })
        
    def test_mysql(self):
        self.assertDsnEqual('mysql://b3:password@localhost/b3', 
        {'protocol': 'mysql', 'host': 'localhost', 'user': 'b3', 
         'path': '/b3', 'password': 'password', 'port': 3306} )
        self.assertDsnEqual('mysql://b3:password@localhost:3406/b3',
        {'protocol': 'mysql', 'host': 'localhost', 'user': 'b3',
         'path': '/b3', 'password': 'password', 'port': 3406} )
        self.assertDsnEqual("mysql://someuser:somepasswd@somehost:3326/",
        {'protocol': 'mysql', 'host': 'somehost', 'user': 'someuser',
         'path': '/', 'password': 'somepasswd', 'port': 3326} )

    def test_mysql_empty_password(self):
        self.assertDsnEqual('mysql://b3:@localhost/b3',
                            {'protocol': 'mysql', 'host': 'localhost', 'user': 'b3',
                             'path': '/b3', 'password': '', 'port': 3306})

    def test_mysql_no_password(self):
        self.assertDsnEqual('mysql://b3@localhost:3406/b3',
                            {'protocol': 'mysql', 'host': 'localhost', 'user': 'b3',
                             'path': '/b3', 'password': '', 'port': 3406})

class TestFuzziGuidMatch(unittest.TestCase):
    def test_1(self):
        self.assertTrue(functions.fuzzyGuidMatch( '098f6bcd4621d373cade4e832627b4f6', '098f6bcd4621d373cade4e832627b4f6'))
        self.assertTrue(functions.fuzzyGuidMatch( '098f6bcd4621d373cade4e832627b4f6', '098f6bcd4621d373cade4e832627b4f'))
        self.assertTrue(functions.fuzzyGuidMatch( '098f6bcd4621d373cade4e832627b4f6', '098f6bcd4621d373cde4e832627b4f6'))
        self.assertTrue(functions.fuzzyGuidMatch( '098f6bcd4621d373cade4e832627bf6',  '098f6bcd4621d373cade4e832627b4f6'))
        self.assertFalse(functions.fuzzyGuidMatch('098f6bcd4621d373cade4e832627b4f6', '098f6bcd46d373cade4e832627b4f6'))
        self.assertFalse(functions.fuzzyGuidMatch('098f6bcd4621d373cade4832627b4f6',  '098f6bcd4621d73cade4e832627b4f6'))
    
    def test_caseInsensitive(self):
        self.assertTrue(functions.fuzzyGuidMatch( '098F6BCD4621D373CADE4E832627B4F6', '098f6bcd4621d373cade4e832627b4f6'))
        self.assertTrue(functions.fuzzyGuidMatch( '098F6BCD4621D373CADE4E832627B4F6', '098f6bcd4621d373cade4e832627b4f'))
        self.assertTrue(functions.fuzzyGuidMatch( '098F6BCD4621D373CADE4E832627B4F6', '098f6bcd4621d373cde4e832627b4f6'))
        self.assertFalse(functions.fuzzyGuidMatch('098F6BCD4621D373CADE4E832627B4F6', '098f6bcd46d373cade4e832627b4f6'))
        self.assertTrue(functions.fuzzyGuidMatch( '098F6BCD4621D373CADE4E832627BF6', '098f6bcd4621d373cade4e832627b4f6'))
        self.assertFalse(functions.fuzzyGuidMatch('098F6BCD4621D373CADE4832627B4F6', '098f6bcd4621d73cade4e832627b4f6'))
        
class TestMinutes2int(unittest.TestCase):
    def test_NaN(self):
        self.assertEqual(functions.minutes2int('mlkj'), 0)
        self.assertEqual(functions.minutes2int(''), 0)
        self.assertEqual(functions.minutes2int('50,654'), 0)
    def test_int(self):
        self.assertEqual(functions.minutes2int('50'), 50)
        self.assertEqual(functions.minutes2int('50.654'), 50.65)
      
class TestTime2minutes(unittest.TestCase):
    def test_None(self):
        self.assertEqual(functions.time2minutes(None), 0)
    def test_int(self):
        self.assertEqual(functions.time2minutes(0), 0)
        self.assertEqual(functions.time2minutes(1), 1)
        self.assertEqual(functions.time2minutes(154), 154)
    def test_str(self):
        self.assertEqual(functions.time2minutes(''), 0)
    def test_str_h(self):
        self.assertEqual(functions.time2minutes('145h'), 145*60)
        self.assertEqual(functions.time2minutes('0 h'), 0)
        self.assertEqual(functions.time2minutes('0    h'), 0)
        self.assertEqual(functions.time2minutes('5h'), 5*60)
    def test_str_m(self):
        self.assertEqual(functions.time2minutes('145m'), 145)
        self.assertEqual(functions.time2minutes('0 m'), 0)
        self.assertEqual(functions.time2minutes('0    m'), 0)
        self.assertEqual(functions.time2minutes('5m'), 5)
    def test_str_s(self):
        self.assertEqual(functions.time2minutes('0 s'), 0)
        self.assertEqual(functions.time2minutes('0    s'), 0)
        self.assertEqual(functions.time2minutes('60s'), 1)
        self.assertEqual(functions.time2minutes('120s'), 2)
        self.assertEqual(functions.time2minutes('5s'), 5.0/60)
        self.assertEqual(functions.time2minutes('90s'), 1.5)
    def test_str_d(self):
        self.assertEqual(functions.time2minutes('0 d'), 0)
        self.assertEqual(functions.time2minutes('0    d'), 0)
        self.assertEqual(functions.time2minutes('60d'), 60*24*60)
        self.assertEqual(functions.time2minutes('120d'), 120*24*60)
        self.assertEqual(functions.time2minutes('5d'), 5*24*60)
        self.assertEqual(functions.time2minutes('90d'), 90*24*60)
    def test_str_w(self):
        self.assertEqual(functions.time2minutes('0 w'), 0)
        self.assertEqual(functions.time2minutes('0    w'), 0)
        self.assertEqual(functions.time2minutes('60w'), 60*7*24*60)
        self.assertEqual(functions.time2minutes('120w'), 120*7*24*60)
        self.assertEqual(functions.time2minutes('5w'), 5*7*24*60)
        self.assertEqual(functions.time2minutes('90w'), 90*7*24*60)

class Test_misc(unittest.TestCase):

    def test_minutesStr(self):
        for test_data, expected in {
            '3s': '3 seconds',
            '4m': '4 minutes',
            '41': '41 minutes',
            '2h': '2 hours',
            '2.5h': '2.5 hours',
            '3d': '3 days',
            '5w': '5 weeks',
            0: '0 second',
            0.5: '30 seconds',
            60: '1 hour',
            90: '1.5 hour',
            120: '2 hours',
            122: '2 hours',
            1266: '21.1 hours',
            1440: '1 day',
            3600: '2.5 days',
            10080: '1 week',
            15120: '1.5 week',
            60480: '6 weeks',
            525600: '1 year',
            861984: '1.6 year',
            1051200: '2 years',
            10512000: '20 years',
        }.items():
            result = functions.minutesStr(test_data)
            if expected != result:
                self.fail("%r, expecting '%s' but got '%s'" % (test_data, expected, result))

    def test_vars2printf(self):
        for test_data, expected in {
            '': '',
            'qsdf': 'qsdf',
            'qsdf $azer xcw': 'qsdf %(azer)s xcw',
            'qsdf $wdrf5 xcw': 'qsdf %(wdrf)s5 xcw',
            '$test': '%(test)s',
            '  $test ': '  %(test)s ',
            '  $test $foo $ $bar': '  %(test)s %(foo)s $ %(bar)s',
        }.items():
            result = functions.vars2printf(test_data)
            if expected != result:
                self.fail("%r, expecting '%s' but got '%s'" % (test_data, expected, result))

    def test_meanstdv(self):
        for test_data, expected in {
            (5,): (5.0, 0),
            (10,): (10.0, 0),
            (): (0, 0)
        }.items():
            result = functions.meanstdv(test_data)
            if expected != result:
                self.fail("%r, expecting '%s' but got '%s'" % (test_data, expected, result))

    def test_getBytes(self):
        self.assertEqual(10, functions.getBytes(10))
        self.assertEqual(10, functions.getBytes('10'))
        self.assertEqual(1024, functions.getBytes('1KB'))
        self.assertEqual(1024, functions.getBytes('1k'))
        self.assertEqual(2048, functions.getBytes('2kb'))
        self.assertEqual(2048, functions.getBytes('2K'))
        self.assertEqual(1048576, functions.getBytes('1 m'))
        self.assertEqual(7340032, functions.getBytes('7 MB'))
        self.assertEqual(21474836480, functions.getBytes('20GB'))
        self.assertEqual(2199023255552, functions.getBytes('2T'))

class Test_getStuffSoundingLike(unittest.TestCase):

    def test_empty_expected_stuff(self):
        self.assertListEqual([], functions.getStuffSoundingLike('foO', []))

    def test_exact_match(self):
        self.assertListEqual(['foO'], functions.getStuffSoundingLike('foO', ['foO']))
        self.assertListEqual(['foO'], functions.getStuffSoundingLike('foO', ['bar', 'foO', 'joe', 'jack', 'averell', 'william']))

    def test_substring_match(self):
        self.assertListEqual(['averell'], functions.getStuffSoundingLike('ere', ['bar', 'foO', 'joe', 'jack', 'averell', 'william']))
        self.assertListEqual(['joe', 'jack'], functions.getStuffSoundingLike('j', ['bar', 'foO', 'joe', 'jack', 'averell', 'william']))
        self.assertListEqual(['xxxfoOx1', 'xxxfoOx2', 'xxxfoOx3', 'xxxfoOx4', 'xxxfoOx5', 'xxxfoOx6'],
            functions.getStuffSoundingLike('foO', ['xxxfoOx1', 'xxxfoOx2', 'xxxfoOx3', 'xxxfoOx4', 'xxxfoOx5', 'xxxfoOx6', 'bar']))

    def test_soundex_match(self):
        self.assertListEqual(['jack'], functions.getStuffSoundingLike('jak', ['bar', 'foO', 'joe', 'jack', 'averell', 'william']))

    def test_fallback(self):
        self.assertListEqual(['bar', 'william', 'joe', 'averell', 'foO', 'jack'], functions.getStuffSoundingLike('xxx', ['bar', 'foO', 'joe', 'jack', 'averell', 'william']))


class Test_topologicalSort(unittest.TestCase):

    def test_topological_sort(self):
        dep_list = [('myplugin4', {'myplugin2', 'myplugin1'}),
                    ('myplugin2', {'myplugin1'}),
                    ('myplugin3', {}),
                    ('myplugin1', {}),
                    ('myplugin5', {'myplugin1', 'myplugin3', 'myplugin4'})]
        sorted_list = [x for x in functions.topological_sort(dep_list)]
        self.assertListEqual(sorted_list, ['myplugin3', 'myplugin1', 'myplugin2', 'myplugin4', 'myplugin5'])