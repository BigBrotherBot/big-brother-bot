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
import os

from mock import Mock, patch
import unittest2 as unittest
from mockito import when

import b3
from b3.plugins.admin import AdminPlugin
from b3.plugins.tk import TkPlugin
from b3.config import XmlConfigParser
from b3.fake import FakeClient

from tests import B3TestCase

from b3 import __file__ as b3_module__file__


ADMIN_CONFIG_FILE = os.path.normpath(os.path.join(os.path.dirname(b3_module__file__), "conf/plugin_admin.xml"))

@unittest.skipUnless(os.path.exists(ADMIN_CONFIG_FILE), reason="cannot get default plugin config file at %s" % ADMIN_CONFIG_FILE)
@patch("threading.Timer")
class Tk_functional_test(B3TestCase):


    def setUp(self):
        B3TestCase.setUp(self)

        self.console.gameName = 'f00'

        self.adminPlugin = AdminPlugin(self.console, ADMIN_CONFIG_FILE)
        when(self.console).getPlugin("admin").thenReturn(self.adminPlugin)
        self.adminPlugin.onLoadConfig()
        self.adminPlugin.onStartup()

        self.conf = XmlConfigParser()
        self.conf.setXml(r"""
        <configuration plugin="tk">
            <settings name="settings">
                <set name="max_points">400</set>
                <set name="levels">0,1,2,20,40</set>
                <set name="round_grace">7</set>
                <set name="issue_warning">sfire</set>
                <set name="grudge_enable">True</set>
                <set name="private_messages">True</set>
            </settings>
            <settings name="messages">
                <set name="ban">^7team damage over limit</set>
                <set name="forgive">^7$vname^7 has forgiven $aname [^3$points^7]</set>
                <set name="grudged">^7$vname^7 has a ^1grudge ^7against $aname [^3$points^7]</set>
                <set name="forgive_many">^7$vname^7 has forgiven $attackers</set>
                <set name="forgive_warning">^1ALERT^7: $name^7 auto-kick if not forgiven. Type ^3!forgive $cid ^7to forgive. [^3damage: $points^7]</set>
                <set name="no_forgive">^7no one to forgive</set>
                <set name="no_punish">^7no one to punish</set>
                <set name="players">^7Forgive who? %s</set>
                <set name="forgive_info">^7$name^7 has ^3$points^7 TK points</set>
                <set name="grudge_info">^7$name^7 is ^1grudged ^3$points^7 TK points</set>
                <set name="forgive_clear">^7$name^7 cleared of ^3$points^7 TK points</set>
            </settings>
            <settings name="level_0">
                <set name="kill_multiplier">2</set>
                <set name="damage_multiplier">1</set>
                <set name="ban_length">2</set>
            </settings>
            <settings name="level_1">
                <set name="kill_multiplier">2</set>
                <set name="damage_multiplier">1</set>
                <set name="ban_length">2</set>
            </settings>
            <settings name="level_2">
                <set name="kill_multiplier">1</set>
                <set name="damage_multiplier">0.5</set>
                <set name="ban_length">1</set>
            </settings>
            <settings name="level_20">
                <set name="kill_multiplier">1</set>
                <set name="damage_multiplier">0.5</set>
                <set name="ban_length">0</set>
            </settings>
            <settings name="level_40">
                <set name="kill_multiplier">0.75</set>
                <set name="damage_multiplier">0.5</set>
                <set name="ban_length">0</set>
            </settings>
        </configuration>
        """)
        self.p = TkPlugin(self.console, self.conf)
        self.p.onLoadConfig()
        self.p.onStartup()

        self.joe = FakeClient(self.console, name="Joe", guid="joeguid", groupBits=1, team=b3.TEAM_RED)
        self.mike = FakeClient(self.console, name="Mike", guid="mikeguid", groupBits=1, team=b3.TEAM_RED)
        self.bill = FakeClient(self.console, name="Bill", guid="billguid", groupBits=1, team=b3.TEAM_RED)
        self.superadmin = FakeClient(self.console, name="superadmin",guid="superadminguid", groupBits=128, team=b3.TEAM_RED)


    def test_dammage_different_teams(self, timer_patch):
        self.joe.warn = Mock()
        self.joe.connects(0)
        self.mike.connects(1)
        self.mike.team = b3.TEAM_BLUE
        self.joe.damages(self.mike)
        self.assertEqual(0, self.joe.warn.call_count)


    def test_kill_different_teams(self, timer_patch):
        self.joe.warn = Mock()
        self.joe.connects(0)
        self.mike.connects(1)
        self.mike.team = b3.TEAM_BLUE
        self.joe.kills(self.mike)
        self.assertEqual(0, self.joe.warn.call_count)


    def test_kill_within_10s(self, timer_patch):
        self.p._round_grace = 10

        self.joe.warn = Mock()
        self.joe.connects(0)
        self.mike.connects(1)

        self.joe.kills(self.mike)
        self.assertEqual(1, self.joe.warn.call_count)

    def test_dammage(self, timer_patch):
        self.p._round_grace = 0

        self.joe.warn = Mock()
        self.joe.connects(0)
        self.mike.connects(1)

        self.joe.damages(self.mike)
        self.joe.damages(self.mike)
        self.joe.damages(self.mike)
        self.joe.damages(self.mike)
        self.joe.damages(self.mike)
        self.assertEqual(0, self.joe.warn.call_count)


    def test_kill(self, timer_patch):
        self.p._round_grace = 0

        self.joe.warn = Mock()
        self.joe.connects(0)
        self.mike.connects(1)

        self.joe.kills(self.mike)
        self.assertEqual(1, self.joe.warn.call_count)
        self.assertIsNotNone(self.mike.getMessageHistoryLike("^7type ^3!fp ^7 to forgive"))


    def test_multikill(self, timer_patch):
        self.p._round_grace = 0

        with patch.object(self.console, "say") as patched_say:
            self.joe.warn = Mock()
            self.joe.tempban = Mock()
            self.joe.connects(0)
            self.mike.connects(1)

            self.mike.clearMessageHistory()
            self.joe.kills(self.mike)
            self.assertEqual(1, self.joe.warn.call_count)
            self.assertEquals(1, len(self.mike.getAllMessageHistoryLike("^7type ^3!fp ^7 to forgive")))

            self.joe.kills(self.mike)
            self.assertEqual(1, len([call_args[0][0] for call_args in patched_say.call_args_list if "auto-kick if not forgiven" in call_args[0][0]]))

            self.joe.kills(self.mike)
            self.assertEqual(1, self.joe.tempban.call_count)


    def test_forgiveinfo(self, timer_patch):
        self.superadmin.connects(99)

        self.p._round_grace = 0

        self.joe.warn = Mock()
        self.joe.connects(0)
        self.mike.connects(1)
        self.bill.connects(2)

        self.joe.kills(self.mike)

        self.superadmin.clearMessageHistory()
        self.superadmin.says("!forgiveinfo joe")
        self.assertEqual(['Joe has 200 TK points, Attacked: Mike (200)'], self.superadmin.message_history)

        self.joe.damages(self.bill, points=6)

        self.superadmin.clearMessageHistory()
        self.superadmin.says("!forgiveinfo joe")
        self.assertEqual(['Joe has 206 TK points, Attacked: Mike (200), Bill (6)'], self.superadmin.message_history)

        self.mike.damages(self.joe, points=27)

        self.superadmin.clearMessageHistory()
        self.superadmin.says("!forgiveinfo joe")
        self.assertEqual(['Joe has 206 TK points, Attacked: Mike (200), Bill (6), Attacked By: Mike [27]'], self.superadmin.message_history)


    def test_forgive(self, timer_patch):
        self.superadmin.connects(99)
        self.p._round_grace = 0

        self.joe.warn = Mock()
        self.joe.connects(0)
        self.mike.connects(1)

        self.joe.kills(self.mike)

        self.superadmin.clearMessageHistory()
        self.superadmin.says("!forgiveinfo joe")
        self.assertEqual(['Joe has 200 TK points, Attacked: Mike (200)'], self.superadmin.message_history)

        self.mike.says("!forgive")

        self.superadmin.clearMessageHistory()
        self.superadmin.says("!forgiveinfo joe")
        self.assertEqual(["Joe has 0 TK points"], self.superadmin.message_history)


    def test_forgiveclear(self, timer_patch):
        self.superadmin.connects(99)

        self.p._round_grace = 0

        self.joe.warn = Mock()
        self.joe.connects(0)
        self.mike.connects(1)

        self.joe.kills(self.mike)

        self.superadmin.clearMessageHistory()
        self.superadmin.says("!forgiveinfo joe")
        self.assertEqual(['Joe has 200 TK points, Attacked: Mike (200)'], self.superadmin.message_history)

        self.superadmin.says("!forgiveclear joe")

        self.superadmin.clearMessageHistory()
        self.superadmin.says("!forgiveinfo joe")
        self.assertEqual(["Joe has 0 TK points"], self.superadmin.message_history)


    def test_forgivelist(self, timer_patcher):
        self.p._round_grace = 0

        self.joe.connects(0)
        self.mike.connects(1)
        self.bill.connects(2)

        self.joe.clearMessageHistory()
        self.joe.says("!forgivelist")
        self.assertEqual(["no one to forgive"], self.joe.message_history)

        self.mike.damages(self.joe, points=14)
        self.joe.clearMessageHistory()
        self.joe.says("!forgivelist")
        self.assertEqual(['Forgive who? [1] Mike [14]'], self.joe.message_history)


        self.bill.damages(self.joe, points=84)
        self.joe.clearMessageHistory()
        self.joe.says("!forgivelist")
        self.assertEqual(['Forgive who? [1] Mike [14], [2] Bill [84]'], self.joe.message_history)


    def test_forgiveall(self, timer_patcher):
        self.p._round_grace = 0

        self.joe.connects(0)
        self.mike.connects(1)
        self.bill.connects(2)

        self.mike.damages(self.joe, points=14)
        self.bill.damages(self.joe, points=84)

        self.joe.clearMessageHistory()
        self.joe.says("!forgivelist")
        self.assertEqual(['Forgive who? [1] Mike [14], [2] Bill [84]'], self.joe.message_history)

        self.joe.says("!forgiveall")
        self.joe.clearMessageHistory()
        self.joe.says("!forgivelist")
        self.assertNotIn("Mike", self.joe.message_history[0])
        self.assertNotIn("Bill", self.joe.message_history[0])


    def test_forgiveprev(self, timer_patcher):
        self.p._round_grace = 0

        self.joe.connects(0)
        self.mike.connects(1)
        self.bill.connects(2)

        self.mike.damages(self.joe, points=14)
        self.bill.damages(self.joe, points=84)

        self.joe.clearMessageHistory()
        self.joe.says("!forgivelist")
        self.assertEqual(['Forgive who? [1] Mike [14], [2] Bill [84]'], self.joe.message_history)

        self.joe.says("!forgiveprev")
        self.joe.clearMessageHistory()
        self.joe.says("!forgivelist")
        self.assertEqual(['Forgive who? [1] Mike [14]'], self.joe.message_history)

