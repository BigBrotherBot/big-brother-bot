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


from tests.plugins.stats import StatPluginTestCase


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
