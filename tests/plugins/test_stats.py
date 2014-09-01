#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2012 Courgette
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
from textwrap import dedent
from mockito import when
from b3 import TEAM_RED, TEAM_BLUE, TEAM_FREE
from b3.fake import FakeClient
from b3.plugins.admin import AdminPlugin
from tests import B3TestCase, logging_disabled

from b3.plugins.stats import StatsPlugin
from b3.config import CfgConfigParser


class Test_config(B3TestCase):

    def test_empty(self):
        # GIVEN
        conf = CfgConfigParser()
        conf.loadFromString(dedent(r"""
        """))
        self.p = StatsPlugin(self.console, conf)
        # WHEN
        self.p.onLoadConfig()
        # THEN
        self.assertEqual(0, self.p.mapstatslevel)
        self.assertEqual(0, self.p.testscorelevel)
        self.assertEqual(2, self.p.topstatslevel)
        self.assertEqual(2, self.p.topxplevel)
        self.assertEqual(100, self.p.startPoints)
        self.assertFalse(self.p.resetscore)
        self.assertFalse(self.p.resetxp)
        self.assertFalse(self.p.show_awards)
        self.assertFalse(self.p.show_awards_xp)

    def test_nominal(self):
        # GIVEN
        conf = CfgConfigParser()
        conf.loadFromString(dedent(r"""
            [commands]
            mapstats-stats: 2
            testscore-ts: 2
            topstats-top: 20
            topxp: 20

            [settings]
            startPoints: 150
            resetscore: yes
            resetxp: yes
            show_awards: yes
            show_awards_xp: yes
        """))
        self.p = StatsPlugin(self.console, conf)
        # WHEN
        self.p.onLoadConfig()
        # THEN
        self.assertEqual(2, self.p.mapstatslevel)
        self.assertEqual(2, self.p.testscorelevel)
        self.assertEqual(20, self.p.topstatslevel)
        self.assertEqual(20, self.p.topxplevel)
        self.assertEqual(150, self.p.startPoints)
        self.assertTrue(self.p.resetscore)
        self.assertTrue(self.p.resetxp)
        self.assertTrue(self.p.show_awards)
        self.assertTrue(self.p.show_awards_xp)


class StatPluginTestCase(B3TestCase):
    def setUp(self):
        B3TestCase.setUp(self)

        with logging_disabled():
            admin_conf = CfgConfigParser()
            admin_plugin = AdminPlugin(self.console, admin_conf)
            admin_plugin.onLoadConfig()
            admin_plugin.onStartup()
            when(self.console).getPlugin('admin').thenReturn(admin_plugin)

        conf = CfgConfigParser()
        conf.loadFromString(dedent(r"""
            [commands]
            mapstats-stats: 0
            testscore-ts: 0
            topstats-top: 0
            topxp: 0

            [settings]
            startPoints: 100
            resetscore: no
            resetxp: no
            show_awards: no
            show_awards_xp: no
        """))
        self.p = StatsPlugin(self.console, conf)
        self.p.onLoadConfig()
        self.p.onStartup()

        self.joe = FakeClient(self.console, name="Joe", guid="joeguid", groupBits=1, team=TEAM_RED)
        self.mike = FakeClient(self.console, name="Mike", guid="mikeguid", groupBits=1, team=TEAM_RED)
        self.joe.connects(1)
        self.mike.connects(2)


class Test_score(StatPluginTestCase):
    def test_no_points(self):
        # GIVEN
        self.joe.setvar(self.p, 'points', 0)
        self.mike.setvar(self.p, 'points', 0)
        # WHEN
        s = self.p.score(self.joe, self.mike)
        # THEN
        self.assertEqual(12.5, s)

    def test_equal_points(self):
        # GIVEN
        self.joe.setvar(self.p, 'points', 50)
        self.mike.setvar(self.p, 'points', 50)
        # WHEN
        s = self.p.score(self.joe, self.mike)
        # THEN
        self.assertEqual(12.5, s)

    def test_victim_has_more_points(self):
        # GIVEN
        self.joe.setvar(self.p, 'points', 50)
        self.mike.setvar(self.p, 'points', 100)
        # WHEN
        s = self.p.score(self.joe, self.mike)
        # THEN
        self.assertEqual(20.0, s)

    def test_victim_has_less_points(self):
        # GIVEN
        self.joe.setvar(self.p, 'points', 100)
        self.mike.setvar(self.p, 'points', 50)
        # WHEN
        s = self.p.score(self.joe, self.mike)
        # THEN
        self.assertEqual(8.75, s)


class Test_cmd_mapstats(StatPluginTestCase):

    def test_no_activity(self):
        # WHEN
        self.joe.says('!mapstats')
        # THEN
        self.assertListEqual(['Stats [ Joe ] K 0 D 0 TK 0 Dmg 0 Skill 100.00 XP 0.0'], self.joe.message_history)

    def test_tk(self):
        # GIVEN
        self.joe.kills(self.mike)
        # WHEN
        self.joe.says('!mapstats')
        # THEN
        self.assertListEqual(['Stats [ Joe ] K 0 D 0 TK 1 Dmg 0 Skill 87.50 XP 0.0'], self.joe.message_history)
        # WHEN
        self.mike.says('!mapstats')
        # THEN
        self.assertListEqual(['Stats [ Mike ] K 0 D 0 TK 0 Dmg 0 Skill 100.00 XP 0.0'], self.mike.message_history)

    def test_kill(self):
        # GIVEN
        self.joe.team = TEAM_BLUE
        self.mike.team = TEAM_RED
        self.joe.kills(self.mike)
        # WHEN
        self.joe.says('!mapstats')
        # THEN
        self.assertListEqual(['Stats [ Joe ] K 1 D 0 TK 0 Dmg 100 Skill 112.50 XP 12.5'], self.joe.message_history)
        # WHEN
        self.mike.says('!mapstats')
        # THEN
        self.assertListEqual(['Stats [ Mike ] K 0 D 1 TK 0 Dmg 0 Skill 87.50 XP 0.0'], self.mike.message_history)


class Test_cmd_testscore(StatPluginTestCase):

    def test_no_data(self):
        # WHEN
        self.joe.says('!testscore')
        # THEN
        self.assertListEqual(['You must supply a player name to test'], self.joe.message_history)

    def test_self(self):
        # WHEN
        self.joe.says('!testscore joe')
        # THEN
        self.assertListEqual(["You don't get points for killing yourself"], self.joe.message_history)

    def test_teammate(self):
        # GIVEN
        assert self.joe.team == self.mike.team
        # WHEN
        self.joe.says('!testscore mike')
        # THEN
        self.assertListEqual(["You don't get points for killing a team mate"], self.joe.message_history)

    def test_no_team(self):
        # GIVEN
        self.joe.team = TEAM_FREE
        self.mike.team = TEAM_FREE
        assert self.joe.team == self.mike.team
        # WHEN
        self.joe.says('!testscore mike')
        # THEN
        self.assertListEqual(['Stats: Joe will get 12.5 skill points for killing Mike'], self.joe.message_history)

    def test_enemy(self):
        # GIVEN
        self.joe.team = TEAM_BLUE
        assert self.joe.team != self.mike.team
        # WHEN
        self.joe.says('!testscore mike')
        # THEN
        self.assertListEqual(['Stats: Joe will get 12.5 skill points for killing Mike'], self.joe.message_history)


class Test_cmd_topstats(StatPluginTestCase):

    def test_no_data(self):
        # WHEN
        self.joe.says('!topstats')
        # THEN
        self.assertListEqual(['Stats: No top players'], self.joe.message_history)

    def test_teammate(self):
        # GIVEN
        assert self.joe.team == self.mike.team
        self.joe.kills(self.mike)
        # WHEN
        self.joe.says('!topstats')
        # THEN
        self.assertListEqual(['Top Stats: #1 Mike [100.0], #2 Joe [87.5]'], self.joe.message_history)

    def test_no_team(self):
        # GIVEN
        self.joe.team = TEAM_FREE
        self.mike.team = TEAM_FREE
        assert self.joe.team == self.mike.team
        self.joe.kills(self.mike)
        # WHEN
        self.joe.says('!topstats')
        # THEN
        self.assertListEqual(['Top Stats: #1 Mike [100.0], #2 Joe [87.5]'], self.joe.message_history)

    def test_enemy(self):
        # GIVEN
        self.joe.team = TEAM_BLUE
        assert self.joe.team != self.mike.team
        self.joe.kills(self.mike)
        # WHEN
        self.joe.says('!topstats')
        # THEN
        self.assertListEqual(['Top Stats: #1 Joe [112.5], #2 Mike [87.5]'], self.joe.message_history)


class Test_cmd_topxp(StatPluginTestCase):

    def test_no_data(self):
        # WHEN
        self.joe.says('!topxp')
        # THEN
        self.assertListEqual(['Stats: No top experienced players'], self.joe.message_history)

    def test_teammate(self):
        # GIVEN
        assert self.joe.team == self.mike.team
        self.joe.kills(self.mike)
        # WHEN
        self.joe.says('!topxp')
        # THEN
        self.assertListEqual(['Top Experienced Players: #1 Mike [0.0], #2 Joe [-0.0]'], self.joe.message_history)

    def test_no_team(self):
        # GIVEN
        self.joe.team = TEAM_FREE
        self.mike.team = TEAM_FREE
        assert self.joe.team == self.mike.team
        self.joe.kills(self.mike)
        # WHEN
        self.joe.says('!topxp')
        # THEN
        self.assertListEqual(['Top Experienced Players: #1 Mike [0.0], #2 Joe [-0.0]'], self.joe.message_history)

    def test_enemy(self):
        # GIVEN
        self.joe.team = TEAM_BLUE
        assert self.joe.team != self.mike.team
        self.joe.kills(self.mike)
        # WHEN
        self.joe.says('!topxp')
        # THEN
        self.assertListEqual(['Top Experienced Players: #1 Joe [12.5], #2 Mike [-0.0]'], self.joe.message_history)