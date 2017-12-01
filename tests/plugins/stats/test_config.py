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

from textwrap import dedent
from tests import B3TestCase
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