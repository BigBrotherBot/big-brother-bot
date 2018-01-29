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

from mock import Mock
from tests.plugins.firstkill import FirstKillCase


class Test_events(FirstKillCase):

    ####################################################################################################################
    #                                                                                                                  #
    #   FIRSTKILL                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def test_first_kill(self):
        # GIVEN
        self.p._firsths = False
        self.p._firstkill = True
        self.p._kill = 0
        # WHEN
        self.p.announce_first_kill = Mock()
        self.p.announce_first_kill_by_headshot = Mock()
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_KILL', client=self.mike, target=self.bill, data=(100, self.console.UT_MOD_DEAGLE, self.console.HL_HEAD)))
        # THEN
        self.p.announce_first_kill.assert_called_with(self.mike, self.bill)
        self.assertFalse(self.p.announce_first_kill_by_headshot.called)

    def test_first_kill_already_broadcasted(self):
        # GIVEN
        self.p._firsths = False
        self.p._firstkill = True
        self.p._kill = 1
        # WHEN
        self.p.announce_first_kill = Mock()
        self.p.announce_first_kill_by_headshot = Mock()
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_KILL', client=self.mike, target=self.bill, data=(100, self.console.UT_MOD_DEAGLE, self.console.HL_HEAD)))
        # THEN
        self.assertFalse(self.p.announce_first_kill.called)
        self.assertFalse(self.p.announce_first_kill_by_headshot.called)

    def test_first_kill_disabled(self):
        # GIVEN
        self.p._firsths = False
        self.p._firstkill = False
        self.p._kill = 0
        # WHEN
        self.p.announce_first_kill = Mock()
        self.p.announce_first_kill_by_headshot = Mock()
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_KILL', client=self.mike, target=self.bill, data=(100, self.console.UT_MOD_DEAGLE, self.console.HL_HEAD)))
        # THEN
        self.assertFalse(self.p.announce_first_kill.called)
        self.assertFalse(self.p.announce_first_kill_by_headshot.called)

    ####################################################################################################################
    #                                                                                                                  #
    #   FIRSTKILL BY HEADSHOT                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    def test_first_kill_by_headshot(self):
        # GIVEN
        self.p._firsths = True
        self.p._firstkill = True
        self.p._kill = 0
        # WHEN
        self.p.announce_first_kill = Mock()
        self.p.announce_first_kill_by_headshot = Mock()
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_KILL', client=self.mike, target=self.bill, data=(100, self.console.UT_MOD_DEAGLE, self.console.HL_HEAD)))
        # THEN
        self.p.announce_first_kill_by_headshot.assert_called_with(self.mike, self.bill)
        self.assertFalse(self.p.announce_first_kill.called)

    def test_first_kill_by_headshot_already_broadcasted(self):
        # GIVEN
        self.p._firsths = True
        self.p._firstkill = True
        self.p._kill = 1
        # WHEN
        self.p.announce_first_kill = Mock()
        self.p.announce_first_kill_by_headshot = Mock()
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_KILL', client=self.mike, target=self.bill, data=(100, self.console.UT_MOD_DEAGLE, self.console.HL_HEAD)))
        # THEN
        self.assertFalse(self.p.announce_first_kill.called)
        self.assertFalse(self.p.announce_first_kill_by_headshot.called)

    def test_first_kill_by_headshot_disabled(self):
        # GIVEN
        self.p._firsths = True
        self.p._firstkill = False
        self.p._kill = 0
        # WHEN
        self.p.announce_first_kill = Mock()
        self.p.announce_first_kill_by_headshot = Mock()
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_KILL', client=self.mike, target=self.bill, data=(100, self.console.UT_MOD_DEAGLE, self.console.HL_HEAD)))
        # THEN
        self.assertFalse(self.p.announce_first_kill.called)
        self.assertFalse(self.p.announce_first_kill_by_headshot.called)

    ####################################################################################################################
    #                                                                                                                  #
    #   FIRST TEAMKILL                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def test_first_teamkill(self):
        # GIVEN
        self.p._firsttk = True
        self.p._tk = 0
        # WHEN
        self.p.announce_first_teamkill = Mock()
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_KILL_TEAM', client=self.mike, target=self.mark, data=(100, self.console.UT_MOD_DEAGLE, self.console.HL_HEAD)))
        # THEN
        self.p.announce_first_teamkill.assert_called_with(self.mike, self.mark)

    def test_first_teamkill_already_broadcasted(self):
        # GIVEN
        self.p._firsttk = True
        self.p._tk = 1
        # WHEN
        self.p.announce_first_teamkill = Mock()
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_KILL_TEAM', client=self.mike, target=self.mark, data=(100, self.console.UT_MOD_DEAGLE, self.console.HL_HEAD)))
        # THEN
        self.assertFalse(self.p.announce_first_teamkill.called)

    def test_first_teamkill_disabled(self):
        # GIVEN
        self.p._firsttk = False
        self.p._tk = 0
        # WHEN
        self.p.announce_first_teamkill = Mock()
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_KILL_TEAM', client=self.mike, target=self.mark, data=(100, self.console.UT_MOD_DEAGLE, self.console.HL_HEAD)))
        # THEN
        self.assertFalse(self.p.announce_first_teamkill.called)