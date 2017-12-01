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

from mock import Mock, call
from tests.plugins.spree import SpreeTestCase


class Test_events(SpreeTestCase):

    def test_killing_spree_start_with_5_kills(self):
        # GIVEN
        self.init()
        self.console.say = Mock()
        self.bill.connects('1')
        self.mike.connects('2')
        # WHEN
        for x in range(5):
            self.console.queueEvent(self.console.getEvent('EVT_CLIENT_KILL', client=self.bill, target=self.mike))
        # THEN
        self.console.say.assert_called_with('Bill is on a killing spree (5 kills in a row)')

    def test_killing_spree_end_with_5_kills(self):
        # GIVEN
        self.init()
        self.console.say = Mock()
        self.bill.connects('1')
        self.mike.connects('2')
        # WHEN
        for x in range(5):
            self.console.queueEvent(self.console.getEvent('EVT_CLIENT_KILL', client=self.bill, target=self.mike))
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_KILL', client=self.mike, target=self.bill))
        # THEN
        self.console.say.assert_has_calls([call('Bill is on a killing spree (5 kills in a row)'),
                                           call('Mike stopped the spree of Bill')])

    def test_killing_spree_start_with_10_kills(self):
        # GIVEN
        self.init()
        self.console.say = Mock()
        self.bill.connects('1')
        self.mike.connects('2')
        # WHEN
        for x in range(10):
            self.console.queueEvent(self.console.getEvent('EVT_CLIENT_KILL', client=self.bill, target=self.mike))
        # THEN
        self.console.say.assert_called_with('Bill is on fire! (10 kills in a row)')

    def test_killing_spree_end_with_10_kills(self):
        # GIVEN
        self.init()
        self.console.say = Mock()
        self.bill.connects('1')
        self.mike.connects('2')
        # WHEN
        for x in range(10):
            self.console.queueEvent(self.console.getEvent('EVT_CLIENT_KILL', client=self.bill, target=self.mike))
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_KILL', client=self.mike, target=self.bill))
        # THEN
        self.console.say.assert_has_calls([call('Bill is on fire! (10 kills in a row)'),
                                           call('Mike iced Bill')])

    def test_losing_spree_start_with_12_kills(self):
        # GIVEN
        self.init()
        self.console.say = Mock()
        self.bill.connects('1')
        self.mike.connects('2')
        # WHEN
        for x in range(12):
            self.console.queueEvent(self.console.getEvent('EVT_CLIENT_KILL', client=self.bill, target=self.mike))
        # THEN
        self.console.say.assert_has_calls([call('Bill is on fire! (10 kills in a row)'),
                                           call('Keep it up Mike, it will come eventually')])

    def test_losing_spree_end_with_12_kills(self):
        # GIVEN
        self.init()
        self.console.say = Mock()
        self.bill.connects('1')
        self.mike.connects('2')
        # WHEN
        for x in range(12):
            self.console.queueEvent(self.console.getEvent('EVT_CLIENT_KILL', client=self.bill, target=self.mike))
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_KILL', client=self.mike, target=self.bill))
        # THEN
        self.console.say.assert_has_calls([call('Bill is on fire! (10 kills in a row)'),
                                           call('Keep it up Mike, it will come eventually'),
                                           call("You're back in business Mike"),
                                           call('Mike iced Bill')])