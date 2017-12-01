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

import b3

from mock import Mock, patch
from tests.plugins.tk import Tk_functional_test


@patch("threading.Timer")
class Test_tk_detected(Tk_functional_test):
    def test_damage_different_teams(self, timer_patch):
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

    def test_damage(self, timer_patch):
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
