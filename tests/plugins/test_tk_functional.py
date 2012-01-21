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

from mock import Mock, patch
import unittest

import b3
from b3.plugins.tk import TkPlugin
from b3.config import XmlConfigParser
from b3.fake import fakeConsole, FakeClient

from tests import B3TestCase


@patch("threading.Timer")
class Tk_functional_test(B3TestCase):

    @classmethod
    def setUpClass(cls):

        cls.conf = XmlConfigParser()
        cls.conf.setXml(r"""
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
        cls.p = TkPlugin(fakeConsole, cls.conf)
        cls.p.onLoadConfig()
        cls.p.onStartup()


    def test_dammage_different_teams(self, timer_patch):
        joe = FakeClient(fakeConsole, name="Joe", exactName="Joe", guid="joeguid", groupBits=1, team=b3.TEAM_RED)
        mike = FakeClient(fakeConsole, name="Mike", exactName="Mike", guid="mikeguid", groupBits=1, team=b3.TEAM_BLUE)

        joe.warn = Mock()
        joe.connects(0)
        mike.connects(1)

        joe.damages(mike)
        self.assertEqual(0, joe.warn.call_count)


    def test_kill_different_teams(self, timer_patch):
        joe = FakeClient(fakeConsole, name="Joe", exactName="Joe", guid="joeguid", groupBits=1, team=b3.TEAM_RED)
        mike = FakeClient(fakeConsole, name="Mike", exactName="Mike", guid="mikeguid", groupBits=1, team=b3.TEAM_BLUE)

        joe.warn = Mock()
        joe.connects(0)
        mike.connects(1)

        joe.kills(mike)
        self.assertEqual(0, joe.warn.call_count)


    def test_kill_within_10s(self, timer_patch):
        Tk_functional_test.p._round_grace = 10
        joe = FakeClient(fakeConsole, name="Joe", exactName="Joe", guid="joeguid", groupBits=1, team=b3.TEAM_RED)
        mike = FakeClient(fakeConsole, name="Mike", exactName="Mike", guid="mikeguid", groupBits=1, team=b3.TEAM_RED)

        joe.warn = Mock()
        joe.connects(0)
        mike.connects(1)

        joe.kills(mike)
        self.assertEqual(1, joe.warn.call_count)

    def test_dammage(self, timer_patch):
        Tk_functional_test.p._round_grace = 0
        joe = FakeClient(fakeConsole, name="Joe", exactName="Joe", guid="joeguid", groupBits=1, team=b3.TEAM_RED)
        mike = FakeClient(fakeConsole, name="Mike", exactName="Mike", guid="mikeguid", groupBits=1, team=b3.TEAM_RED)

        joe.warn = Mock()
        joe.connects(0)
        mike.connects(1)

        joe.damages(mike)
        joe.damages(mike)
        joe.damages(mike)
        joe.damages(mike)
        joe.damages(mike)
        self.assertEqual(0, joe.warn.call_count)


    def test_kill(self, timer_patch):
        Tk_functional_test.p._round_grace = 0
        joe = FakeClient(fakeConsole, name="Joe", exactName="Joe", guid="joeguid", groupBits=1, team=b3.TEAM_RED)
        mike = FakeClient(fakeConsole, name="Mike", exactName="Mike", guid="mikeguid", groupBits=1, team=b3.TEAM_RED)

        joe.warn = Mock()
        joe.connects(0)
        mike.connects(1)

        joe.kills(mike)
        self.assertEqual(1, joe.warn.call_count)
        self.assertIsNotNone(mike.getMessageHistoryLike("^7type ^3!fp ^7 to forgive"))


    def test_multikill(self, timer_patch):
        Tk_functional_test.p._round_grace = 0
        joe = FakeClient(fakeConsole, name="Joe", exactName="Joe", guid="joeguid", groupBits=1, team=b3.TEAM_RED)
        mike = FakeClient(fakeConsole, name="Mike", exactName="Mike", guid="mikeguid", groupBits=1, team=b3.TEAM_RED)

        with patch.object(fakeConsole, "say") as patched_say:
            joe.warn = Mock()
            joe.tempban = Mock()
            joe.connects(0)
            mike.connects(1)

            mike.clearMessageHistory()
            joe.kills(mike)
            self.assertEqual(1, joe.warn.call_count)
            self.assertEquals(1, len(mike.getAllMessageHistoryLike("^7type ^3!fp ^7 to forgive")))

            joe.kills(mike)
            self.assertEqual(1, len([call_args[0][0] for call_args in patched_say.call_args_list if "auto-kick if not forgiven" in call_args[0][0]]))

            joe.kills(mike)
            self.assertEqual(1, joe.tempban.call_count)


    def test_forgiveinfo(self, timer_patch):
        from b3.fake import superadmin
        superadmin.connects(99)

        Tk_functional_test.p._round_grace = 0
        joe = FakeClient(fakeConsole, name="Joe", exactName="Joe", guid="joeguid", groupBits=1, team=b3.TEAM_RED)
        mike = FakeClient(fakeConsole, name="Mike", exactName="Mike", guid="mikeguid", groupBits=1, team=b3.TEAM_RED)
        bill = FakeClient(fakeConsole, name="Bill", exactName="Bill", guid="billguid", groupBits=1, team=b3.TEAM_RED)

        joe.warn = Mock()
        joe.connects(0)
        mike.connects(1)
        bill.connects(2)

        joe.kills(mike)

        superadmin.message_history = []
        superadmin.says("!forgiveinfo joe")
        self.assertIn("Joe has 200 TK points", superadmin.message_history[0])
        self.assertIn("Attacked: Mike (200)", superadmin.message_history[0])
        self.assertNotIn("Attacked By:", superadmin.message_history[0])

        joe.damages(bill, points=6)

        superadmin.message_history = []
        superadmin.says("!forgiveinfo joe")
        self.assertIn("Joe has 206 TK points", superadmin.message_history[0])
        self.assertIn("Attacked: Mike (200), Bill (6)", superadmin.message_history[0])
        self.assertNotIn("Attacked By:", superadmin.message_history[0])


        mike.damages(joe, points=27)

        superadmin.message_history = []
        superadmin.says("!forgiveinfo joe")
        self.assertIn("Joe has 206 TK points", superadmin.message_history[0])
        self.assertIn("Attacked: Mike (200), Bill (6)", superadmin.message_history[0])
        self.assertIn("Attacked By: Mike [27]", superadmin.message_history[0])


    def test_forgive(self, timer_patch):
        from b3.fake import superadmin
        superadmin.connects(99)

        Tk_functional_test.p._round_grace = 0
        joe = FakeClient(fakeConsole, name="Joe", exactName="Joe", guid="joeguid", groupBits=1, team=b3.TEAM_RED)
        mike = FakeClient(fakeConsole, name="Mike", exactName="Mike", guid="mikeguid", groupBits=1, team=b3.TEAM_RED)

        joe.warn = Mock()
        joe.connects(0)
        mike.connects(1)

        joe.kills(mike)

        superadmin.message_history = []
        superadmin.says("!forgiveinfo joe")
        self.assertIn("Joe has 200 TK points", superadmin.message_history[0])

        mike.says("!forgive")

        superadmin.message_history = []
        superadmin.says("!forgiveinfo joe")
        self.assertIn("Joe has 0 TK points", superadmin.message_history[0])


    def test_forgiveclear(self, timer_patch):
        from b3.fake import superadmin
        superadmin.connects(99)

        Tk_functional_test.p._round_grace = 0
        joe = FakeClient(fakeConsole, name="Joe", exactName="Joe", guid="joeguid", groupBits=1, team=b3.TEAM_RED)
        mike = FakeClient(fakeConsole, name="Mike", exactName="Mike", guid="mikeguid", groupBits=1, team=b3.TEAM_RED)

        joe.warn = Mock()
        joe.connects(0)
        mike.connects(1)

        joe.kills(mike)

        superadmin.message_history = []
        superadmin.says("!forgiveinfo joe")
        self.assertIn("Joe has 200 TK points", superadmin.message_history[0])

        superadmin.says("!forgiveclear joe")

        superadmin.message_history = []
        superadmin.says("!forgiveinfo joe")
        self.assertIn("Joe has 0 TK points", superadmin.message_history[0])


    def test_forgivelist(self, timer_patcher):
        Tk_functional_test.p._round_grace = 0
        joe = FakeClient(fakeConsole, name="Joe", exactName="Joe", guid="joeguid", groupBits=1, team=b3.TEAM_RED)
        mike = FakeClient(fakeConsole, name="Mike", exactName="Mike", guid="mikeguid", groupBits=1, team=b3.TEAM_RED)
        bill = FakeClient(fakeConsole, name="Bill", exactName="Bill", guid="billguid", groupBits=1, team=b3.TEAM_RED)

        joe.connects(0)
        mike.connects(1)
        bill.connects(2)

        joe.message_history = []
        joe.says("!forgivelist")
        self.assertEqual("no one to forgive", joe.message_history[0])

        mike.damages(joe, points=14)
        joe.message_history = []
        joe.says("!forgivelist")
        self.assertIn("Mike [14]", joe.message_history[0])


        bill.damages(joe, points=84)
        joe.message_history = []
        joe.says("!forgivelist")
        self.assertIn("Mike [14]", joe.message_history[0])
        self.assertIn("Bill [84]", joe.message_history[0])


    def test_forgiveall(self, timer_patcher):
        Tk_functional_test.p._round_grace = 0
        joe = FakeClient(fakeConsole, name="Joe", exactName="Joe", guid="joeguid", groupBits=1, team=b3.TEAM_RED)
        mike = FakeClient(fakeConsole, name="Mike", exactName="Mike", guid="mikeguid", groupBits=1, team=b3.TEAM_RED)
        bill = FakeClient(fakeConsole, name="Bill", exactName="Bill", guid="billguid", groupBits=1, team=b3.TEAM_RED)

        joe.connects(0)
        mike.connects(1)
        bill.connects(2)

        mike.damages(joe, points=14)
        bill.damages(joe, points=84)

        joe.message_history = []
        joe.says("!forgivelist")
        self.assertIn("Mike [14]", joe.message_history[0])
        self.assertIn("Bill [84]", joe.message_history[0])

        joe.says("!forgiveall")
        joe.message_history = []
        joe.says("!forgivelist")
        self.assertNotIn("Mike", joe.message_history[0])
        self.assertNotIn("Bill", joe.message_history[0])


    def test_forgiveprev(self, timer_patcher):
        Tk_functional_test.p._round_grace = 0
        joe = FakeClient(fakeConsole, name="Joe", exactName="Joe", guid="joeguid", groupBits=1, team=b3.TEAM_RED)
        mike = FakeClient(fakeConsole, name="Mike", exactName="Mike", guid="mikeguid", groupBits=1, team=b3.TEAM_RED)
        bill = FakeClient(fakeConsole, name="Bill", exactName="Bill", guid="billguid", groupBits=1, team=b3.TEAM_RED)

        joe.connects(0)
        mike.connects(1)
        bill.connects(2)

        mike.damages(joe, points=14)
        bill.damages(joe, points=84)

        joe.message_history = []
        joe.says("!forgivelist")
        self.assertIn("Mike [14]", joe.message_history[0])
        self.assertIn("Bill [84]", joe.message_history[0])

        joe.says("!forgiveprev")
        joe.message_history = []
        joe.says("!forgivelist")
        self.assertIn("Mike", joe.message_history[0])
        self.assertNotIn("Bill", joe.message_history[0])


if __name__ == '__main__':
    unittest.main()