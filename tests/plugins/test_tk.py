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
import unittest

import b3
from b3.plugins.tk import TkPlugin
from b3.config import XmlConfigParser
from b3.fake import fakeConsole, FakeClient

from tests import B3TestCase


default_plugin_file = os.path.normpath(os.path.join(os.path.dirname(__file__), "../../b3/conf/plugin_tk.xml"))

class TkTestCase(B3TestCase):
    """base class for TestCase to apply to the Tk plugin"""

    def setUp(self):
        # Timer needs to be patched to prevent the plugin from scheduling tasks
        self.timer_patcher = patch('threading.Timer')
        self.timer_patcher.start()

        super(TkTestCase, self).setUp()
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
        self.p = TkPlugin(b3.console, self.conf)
        self.p.onLoadConfig()

    def tearDown(self):
        self.timer_patcher.stop()


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


    def test_dammage_within_10s(self, timer_patch):
        Tk_functional_test.p._round_grace = 10
        joe = FakeClient(fakeConsole, name="Joe", exactName="Joe", guid="joeguid", groupBits=1, team=b3.TEAM_RED)
        mike = FakeClient(fakeConsole, name="Mike", exactName="Mike", guid="mikeguid", groupBits=1, team=b3.TEAM_RED)

        joe.warn = Mock()
        joe.connects(0)
        mike.connects(1)

        joe.damages(mike)
        self.assertEqual(1, joe.warn.call_count)


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




@unittest.skipUnless(os.path.exists(default_plugin_file), reason="cannot get default plugin config file at %s" % default_plugin_file)
class Test_Tk_default_config(TkTestCase):

    def setUp(self):
        super(Test_Tk_default_config, self).setUp()
        self.p.config.load(default_plugin_file)
        self.p.onLoadConfig()

    def test(self):
        self.assertEqual("sfire", self.p._issue_warning)
        self.assertEqual(7, self.p._round_grace)
        self.assertEqual(40, self.p._maxLevel)
        self.assertEqual(400, self.p._maxPoints)
        self.assertEqual({
                0: (2.0, 1.0, 2),
                1: (2.0, 1.0, 2),
                2: (1.0, 0.5, 1),
                20: (1.0, 0.5, 0),
                40: (0.75, 0.5, 0)
        }, self.p._levels)
        self.assertTrue(self.p._private_messages)


if __name__ == '__main__':
    unittest.main()