# -*- encoding: utf-8 -*-
#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2011 Thomas "Courgette" LÉVEIL <courgette@bigbrotherbot.net>
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
from b3 import update
import urllib2
import unittest

class TestGetDefaultChannel(unittest.TestCase):
    def test_rotten_input(self):
        self.assertEqual(update.UPDATE_CHANNEL_STABLE, update.getDefaultChannel(None))
        self.assertEqual(update.UPDATE_CHANNEL_STABLE, update.getDefaultChannel(""))
        self.assertEqual(update.UPDATE_CHANNEL_STABLE, update.getDefaultChannel(" "))
        self.assertEqual(update.UPDATE_CHANNEL_STABLE, update.getDefaultChannel(" qsdf sf qsd"))
        self.assertEqual(update.UPDATE_CHANNEL_STABLE, update.getDefaultChannel("1.4.5.6"))
        self.assertEqual(update.UPDATE_CHANNEL_STABLE, update.getDefaultChannel("1.4beta"))

    def test_stable(self):
        self.assertEqual(update.UPDATE_CHANNEL_STABLE, update.getDefaultChannel("1.0"))
        self.assertEqual(update.UPDATE_CHANNEL_STABLE, update.getDefaultChannel("1.0.1"))
        self.assertEqual(update.UPDATE_CHANNEL_STABLE, update.getDefaultChannel("1.2"))

    def test_beta(self):
        self.assertEqual(update.UPDATE_CHANNEL_BETA, update.getDefaultChannel("1.0b"))
        self.assertEqual(update.UPDATE_CHANNEL_BETA, update.getDefaultChannel("1.0.1b2"))
        self.assertEqual(update.UPDATE_CHANNEL_BETA, update.getDefaultChannel("1.2b5"))

    def test_dev(self):
        self.assertEqual(update.UPDATE_CHANNEL_DEV, update.getDefaultChannel("1.0a"))
        self.assertEqual(update.UPDATE_CHANNEL_DEV, update.getDefaultChannel("1.0.1a2"))
        self.assertEqual(update.UPDATE_CHANNEL_DEV, update.getDefaultChannel("1.2a5"))
        self.assertEqual(update.UPDATE_CHANNEL_DEV, update.getDefaultChannel("1.0dev"))
        self.assertEqual(update.UPDATE_CHANNEL_DEV, update.getDefaultChannel("1.0.1dev2"))
        self.assertEqual(update.UPDATE_CHANNEL_DEV, update.getDefaultChannel("1.2dev5"))


class TestCheckUpdateUrl(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_url = update.URL_B3_LATEST_VERSION

    def setUp(self):
        self._time_start = 0
        self._time_start = time.time()

    def tearDown(self):
        # make sure to restore update url between tests
        update.URL_B3_LATEST_VERSION = self.__class__.original_url
        ms = ((time.time() - self._time_start)*1000)
        self.assertTrue(ms < 4000, "Test exceeded timeout")

    def test_official_url(self):
        result = update.checkUpdate('1.2', singleLine=False, showErrormsg=True)
        self.assertIsNotNone(result)
        self.assertNotIn('Could not check updates', result)

    def test_not_existing_url(self):
        update.URL_B3_LATEST_VERSION = 'http://no.where.local/'
        result = update.checkUpdate('1.2', singleLine=True, showErrormsg=True, timeout=1)
        self.assertIn('Could not check updates', result)


class TestCheckUpdate (unittest.TestCase):

    def setUp(self):
        self.expected_stable = u'*** NOTICE: B3 1.4.3 is available. See http://www.url.stable.fake ! ***'
        self.expected_beta = u'*** NOTICE: B3 1.5.3b3 is available. See http://www.url.beta.fake ! ***'
        self.expected_dev = u'*** NOTICE: B3 1.6dev5 is available. See http://www.url.dev.fake ! ***'

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
                                "url": "http://www.url.beta.fake",
                                "latest-version": "1.5.3b3"
                            },
                            "dev": {
                                "url": "http://www.url.dev.fake",
                                "latest-version": "1.6dev5"
                            }
                        }
                    }
                }
            """)
        self.original_urlopen = urllib2.urlopen
        urllib2.urlopen = urlopen

    def tearDown(self):
        urllib2.urlopen = self.original_urlopen

    def test_default_channel(self):
        for v in ('1.0', '1.1.1', '1.4', '1.4.2'):
            self.assertEqual(self.expected_stable, update.checkUpdate(v))
        for v in ('1.4.3', '1.4.4', '1.5', '1.5.2', '1.5.3', '1.5.4', '1.6', '1.6.1'):
            self.assertEqual(None, update.checkUpdate(v))

        for v in ('1.0b', '1.1.1b', '1.1.1b2', '1.4.3b', '1.4.3b1', '1.4.4b', '1.5.3b', '1.5.3b1', '1.5.3b2'):
            self.assertEqual(self.expected_beta, update.checkUpdate(v))
        for v in ('1.5.3b3', '1.5.3b4', '1.5.4b', '1.6b', '1.6b1'):
            self.assertEqual(None, update.checkUpdate(v))

        for v in ('1.0dev15', '1.1.1dev7', '1.4.3dev', '1.4.3dev1', '1.4.4dev', '1.5.3dev', '1.5.3dev1', '1.5.4dev', '1.6dev', '1.6dev4'):
            self.assertEqual(self.expected_dev, update.checkUpdate(v))
        for v in ('1.6dev5', '1.6dev6', '1.7dev'):
            self.assertEqual(None, update.checkUpdate(v))


    def test_stable_channel(self):
        for v in ('1.0dev15','1.0b', '1.0', '1.1.1', '1.1.1b', '1.1.1b2', '1.1.1dev7', '1.4', '1.4.2', '1.4.3dev',
                  '1.4.3dev1', '1.4.3b', '1.4.3b1'):
            self.assertEqual(self.expected_stable, update.checkUpdate(v, channel=update.UPDATE_CHANNEL_STABLE))
        for v in ('1.4.3', '1.4.3', '1.4.4dev', '1.4.4b', '1.4.4', '1.5', '1.5.2', '1.5.3dev', '1.5.3dev1',
                  '1.5.3b', '1.5.3b1', '1.5.3b2', '1.5.3b3', '1.5.3b4', '1.5.3', '1.5.4dev', '1.5.4b', '1.5.4',
                  '1.6dev', '1.6dev4', '1.6dev5', '1.6dev6', '1.6b', '1.6b1', '1.6', '1.6.1'):
            self.assertEqual(None, update.checkUpdate(v, channel=update.UPDATE_CHANNEL_STABLE))

    def test_beta_channel(self):
        for v in ('1.0dev15','1.0b', '1.0', '1.1.1', '1.1.1b', '1.1.1b2', '1.1.1dev7', '1.4', '1.4.2', '1.4.3dev',
                  '1.4.3dev1', '1.4.3b', '1.4.3b1', '1.4.3', '1.4.3', '1.4.4dev', '1.4.4b', '1.4.4', '1.5',
                  '1.5.2', '1.5.3dev', '1.5.3dev1', '1.5.3b', '1.5.3b1', '1.5.3b2'):
            self.assertEqual(self.expected_beta, update.checkUpdate(v, channel=update.UPDATE_CHANNEL_BETA))
        for v in ('1.5.3b3', '1.5.3b4', '1.5.3', '1.5.4dev', '1.5.4b', '1.5.4', '1.6dev', '1.6dev4', '1.6dev5',
                  '1.6dev6', '1.6b', '1.6b1', '1.6', '1.6.1'):
            self.assertEqual(None, update.checkUpdate(v, channel=update.UPDATE_CHANNEL_BETA))

    def test_dev_channel(self):
        for v in ('1.0dev15','1.0b', '1.0', '1.1.1', '1.1.1b', '1.1.1b2', '1.1.1dev7', '1.4', '1.4.2', '1.4.3dev',
                  '1.4.3dev1', '1.4.3b', '1.4.3b1', '1.4.3', '1.4.3', '1.4.4dev', '1.4.4b', '1.4.4', '1.5',
                  '1.5.2', '1.5.3dev', '1.5.3dev1', '1.5.3b', '1.5.3b1', '1.5.3b2', '1.5.3b3', '1.5.3b4', '1.5.3',
                  '1.5.4dev', '1.5.4b', '1.5.4', '1.6dev', '1.6dev4'):
            self.assertEqual(self.expected_dev, update.checkUpdate(v, channel=update.UPDATE_CHANNEL_DEV))
        for v in ('1.6dev5',
                  '1.6dev6', '1.6b', '1.6b1', '1.6', '1.6.1'):
            self.assertEqual(None, update.checkUpdate(v, channel=update.UPDATE_CHANNEL_DEV))

    def test_unknown_channel(self):
        self.assertIn("unknown channel 'foo'", update.checkUpdate('1.0', channel="foo", showErrormsg=True))

    @unittest.expectedFailure
    def test_bad_version(self):
        update.checkUpdate('one.two', showErrormsg=True)

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
        self.assertIn("Could not check updates", update.checkUpdate('1.0', showErrormsg=True))


if __name__ == '__main__':
    unittest.main()