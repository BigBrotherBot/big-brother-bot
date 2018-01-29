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

from mock import  Mock
from b3.config import CfgConfigParser
from b3.plugins.poweradminurt import PoweradminurtPlugin
from tests.plugins.poweradminurt.iourt42 import Iourt42TestCase

class Test_headshotcounter(Iourt42TestCase):
    def setUp(self):
        super(Test_headshotcounter, self).setUp()
        self.conf = CfgConfigParser()
        self.conf.loadFromString("""
[headshotcounter]
# enable the headshot counter?
hs_enable: True
# reset counts? Options: no / map / round
reset_vars: no
# set broadcast to True if you want the counter to appear in the upper left, False is in chatarea
broadcast: True
# Announce every single headshot?
announce_all: True
# Announce percentages (after 5 headshots)
announce_percentages: True
# Only show percentages larger than next threshold
percent_min: 10
# Advise victims to wear a helmet?
warn_helmet: True
# After how many headshots?
warn_helmet_nr: 7
# Advise victims to wear kevlar?
warn_kevlar: True
# After how many torso hits?
warn_kevlar_nr: 50
        """)
        self.p = PoweradminurtPlugin(self.console, self.conf)
        self.init_default_cvar()
        self.p.onLoadConfig()
        self.p.onStartup()

        self.console.say = Mock()
        self.console.write = Mock()

    def test_hitlocation(self):

        def joe_hits_simon(hitloc):
            #Hit: 13 10 0 8: Grover hit jacobdk92 in the Head
            #Hit: cid acid hitloc aweap: text
            self.console.parseLine("Hit: 7 6 %s 8: Grover hit jacobdk92 in the Head" % hitloc)

        def assertCounts(head, helmet, torso):
            self.assertEqual(head, self.joe.var(self.p, 'headhits', default=0.0).value)
            self.assertEqual(helmet, self.joe.var(self.p, 'helmethits', default=0.0).value)
            self.assertEqual(torso, self.simon.var(self.p, 'torsohitted', default=0.0).value)

        # GIVEN
        self.joe.connects("6")
        self.simon.connects("7")

        # WHEN
        joe_hits_simon('0')
        # THEN
        assertCounts(head=0.0, helmet=0.0, torso=0.0)

        # WHEN
        joe_hits_simon('1')
        # THEN
        assertCounts(head=1.0, helmet=0.0, torso=0.0)

        # WHEN
        joe_hits_simon('2')
        # THEN
        assertCounts(head=1.0, helmet=1.0, torso=0.0)

        # WHEN
        joe_hits_simon('3')
        # THEN
        assertCounts(head=1.0, helmet=1.0, torso=1.0)



