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
import time
import sys
from b3 import functions
import unittest
    
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


class TestCheckUpdateUrl(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_url = functions.URL_B3_LATEST_VERSION
    def setUp(self):
        self._time_start = 0
        self._time_start = time.time()
    def tearDown(self):
        # make sure to restore update url between tests
        functions.URL_B3_LATEST_VERSION = self.__class__.original_url
        ms = ((time.time() - self._time_start)*1000)
        self.assertTrue(ms < 4000, "Test exceeded timeout")
    def test_official_url(self):
        result = functions.checkUpdate('1.2', singleLine=False, showErrormsg=True)
        self.assertIsNotNone(result)
        self.assertNotIn('Could not check updates', result)
    def test_not_existing_url(self):
        functions.URL_B3_LATEST_VERSION = 'http://no.where.local/'
        result = functions.checkUpdate('1.2', singleLine=True, showErrormsg=True)
        self.assertIn('Could not check updates', result)


class TestCheckUpdate (unittest.TestCase):
    def setUp(self):
        def urlopen(*args, **kwargs):
            """
            will fake urllib2.urlopen
            """
            import StringIO
            return StringIO.StringIO("""
                {
                    "B3": {
                        "channels": {
                            "stable": {
                                "url": "http://www.url.stable.fake",
                                "latest-version": "1.4.3"
                            },
                            "beta": {
                                "url": "http:///www.url.beta.fake",
                                "latest-version": "1.5.3b3"
                            },
                            "dev": {
                                "url": "http:///www.url.dev.fake",
                                "latest-version": "1.6dev5"
                            }
                        }
                    }
                }
            """)
        import urllib2
        urllib2.urlopen = urlopen

    def test_stable_channel(self):
        expected_when_update = u'*** NOTICE: B3 1.4.3 is available. See http://www.url.stable.fake ! ***'
        for v in ('1.0dev15','1.0b', '1.0', '1.1.1', '1.1.1b', '1.1.1b2', '1.1.1dev7', '1.4', '1.4.2', '1.4.3dev',
                  '1.4.3dev1', '1.4.3b', '1.4.3b1'):
            self.assertEqual(expected_when_update, functions.checkUpdate(v))
        for v in ('1.4.3', '1.4.3', '1.4.4dev', '1.4.4b', '1.4.4', '1.5', '1.5.2', '1.5.3dev', '1.5.3dev1',
                  '1.5.3b', '1.5.3b1', '1.5.3b2', '1.5.3b3', '1.5.3b4', '1.5.3', '1.5.4dev', '1.5.4b', '1.5.4',
                  '1.6dev', '1.6dev4', '1.6dev5', '1.6dev6', '1.6b', '1.6b1', '1.6', '1.6.1'):
            self.assertEqual(None, functions.checkUpdate(v))
    def test_beta_channel(self):
        expected_when_update = u'*** NOTICE: B3 1.5.3b3 is available. See http:///www.url.beta.fake ! ***'
        for v in ('1.0dev15','1.0b', '1.0', '1.1.1', '1.1.1b', '1.1.1b2', '1.1.1dev7', '1.4', '1.4.2', '1.4.3dev',
                  '1.4.3dev1', '1.4.3b', '1.4.3b1', '1.4.3', '1.4.3', '1.4.4dev', '1.4.4b', '1.4.4', '1.5',
                  '1.5.2', '1.5.3dev', '1.5.3dev1', '1.5.3b', '1.5.3b1', '1.5.3b2'):
            self.assertEqual(expected_when_update, functions.checkUpdate(v, channel=functions.UPDATE_CHANNEL_BETA))
        for v in ('1.5.3b3', '1.5.3b4', '1.5.3', '1.5.4dev', '1.5.4b', '1.5.4', '1.6dev', '1.6dev4', '1.6dev5',
                  '1.6dev6', '1.6b', '1.6b1', '1.6', '1.6.1'):
            self.assertEqual(None, functions.checkUpdate(v, channel=functions.UPDATE_CHANNEL_BETA))
    def test_dev_channel(self):
        expected_when_update = u'*** NOTICE: B3 1.6dev5 is available. See http:///www.url.dev.fake ! ***'
        for v in ('1.0dev15','1.0b', '1.0', '1.1.1', '1.1.1b', '1.1.1b2', '1.1.1dev7', '1.4', '1.4.2', '1.4.3dev',
                  '1.4.3dev1', '1.4.3b', '1.4.3b1', '1.4.3', '1.4.3', '1.4.4dev', '1.4.4b', '1.4.4', '1.5',
                  '1.5.2', '1.5.3dev', '1.5.3dev1', '1.5.3b', '1.5.3b1', '1.5.3b2', '1.5.3b3', '1.5.3b4', '1.5.3',
                  '1.5.4dev', '1.5.4b', '1.5.4', '1.6dev', '1.6dev4'):
            self.assertEqual(expected_when_update, functions.checkUpdate(v, channel=functions.UPDATE_CHANNEL_DEV))
        for v in ('1.6dev5',
                  '1.6dev6', '1.6b', '1.6b1', '1.6', '1.6.1'):
            self.assertEqual(None, functions.checkUpdate(v, channel=functions.UPDATE_CHANNEL_DEV))
    def test_unknown_channel(self):
        self.assertIn("unknown channel 'foo'", functions.checkUpdate('1.0', channel="foo", showErrormsg=True))
    @unittest.expectedFailure
    def test_bad_version(self):
        functions.checkUpdate('one.two', showErrormsg=True)
    def test_broken_json(self):
        def urlopen2(*args, **kwargs):
            """
            will fake urllib2.urlopen
            """
            import StringIO
            return StringIO.StringIO("""
                {
                    "B3": {
                        "channels": {
                            "stable": {
                                "url": "http://www.url.stable.fake",
                                "latest-version": "1.4.3"
                            },
                            "be
            """)
        import urllib2
        urllib2.urlopen = urlopen2
        self.assertIn("Could not check updates", functions.checkUpdate('1.0', showErrormsg=True))

if __name__ == '__main__':
    unittest.main()