# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2012 Thomas LEVEIL <courgette@bigbrotherbot.net>
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

from tests.plugins.adv import AdvTestCase


class Test_config(AdvTestCase):

    def test_default_config(self):
        self.init_plugin()
        self.assertEqual('2', self.p._rate)
        self.assertIsNone(self.p._fileName)
        self.assertEqual("http://forum.bigbrotherbot.net/news-2/?type=rss;action=.xml", self.p._feed)
        self.assertEqual("News: ", self.p._feedpre)
        self.assertEqual(4, self.p._feedmaxitems)
        self.assertEqual('News: ', self.p._feedpre)
        self.assertIsNotNone(self.p._cronTab)
        self.assertTupleEqual((0, range(0, 59, 2), -1, -1, -1, -1),
                              (self.p._cronTab.second, self.p._cronTab.minute, self.p._cronTab.hour,
                               self.p._cronTab.day, self.p._cronTab.month, self.p._cronTab.dow))
        self.assertEqual(10, len(self.p._msg.items))
        self.assertListEqual([
                                 '^2Big Brother Bot is watching you... www.BigBrotherBot.net',
                                 '@feed',
                                 'server watched by @admins',
                                 '^3Rule #1: No racism of any kind',
                                 '@time',
                                 '@admins',
                                 '@feed',
                                 '^2Do you like B3? Consider donating to the project at www.BigBrotherBot.net',
                                 '@nextmap',
                                 '@topstats'
                             ], self.p._msg.items)

    def test_empty(self):
        self.init_plugin("""<configuration plugin="adv" />""")
        self.assertEqual(self.p._rate, '2')
        self.assertIsNone(self.p._fileName)
        self.assertEqual(0, len(self.p._msg.items))
        self.assertEqual("http://forum.bigbrotherbot.net/news-2/?type=rss;action=.xml", self.p._feed)
        self.assertEqual("News: ", self.p._feedpre)
        self.assertEqual(4, self.p._feedmaxitems)   # changed to 4 since plugin configuration loading is not stopped
        self.assertEqual('News: ', self.p._feedpre) # by empty rate anymore, so maxfeed is reduced by 1 unit
        self.assertIsNotNone(self.p._cronTab)

    def test_rate_nominal(self):
        self.init_plugin("""\
<configuration plugin="adv">
    <settings name="settings">
        <set name="rate">1</set>
    </settings>
</configuration>
""")
        self.assertEqual('1', self.p._rate)
        self.assertIsNotNone(self.p._cronTab)
        self.assertTupleEqual((0, range(60), -1, -1, -1, -1),
                              (self.p._cronTab.second, self.p._cronTab.minute, self.p._cronTab.hour,
                               self.p._cronTab.day, self.p._cronTab.month, self.p._cronTab.dow))

    def test_rate_nominal_second(self):
        self.init_plugin("""\
<configuration plugin="adv">
    <settings name="settings">
        <set name="rate">40s</set>
    </settings>
</configuration>
""")
        self.assertEqual('40s', self.p._rate)
        self.assertIsNotNone(self.p._cronTab)
        self.assertTupleEqual(([0, 40], -1, -1, -1, -1, -1),
                              (self.p._cronTab.second, self.p._cronTab.minute, self.p._cronTab.hour,
                               self.p._cronTab.day, self.p._cronTab.month, self.p._cronTab.dow))

    def test_rate_junk(self):
        try:
            self.init_plugin("""\
<configuration plugin="adv">
    <settings name="settings">
        <set name="rate">f00</set>
    </settings>
</configuration>
""")
        except TypeError, err:
            print err
        except Exception:
            raise
        self.assertEqual('f00', self.p._rate)
        self.assertIsNone(self.p._cronTab)
