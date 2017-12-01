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

from mock import Mock, patch
from tests.plugins.tk import Tk_functional_test

@patch("threading.Timer")
class Test_commands(Tk_functional_test):
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

