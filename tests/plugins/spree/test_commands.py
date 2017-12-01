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

from tests.plugins.spree import SpreeTestCase


class Test_commands(SpreeTestCase):

    def test_cmd_spree_with_no_arguments_and_no_spree(self):
        # GIVEN
        self.init()
        self.bill.connects('1')
        self.mike.connects('2')
        # WHEN
        self.bill.says("!spree")
        self.mike.says("!spree")
        # THEN
        self.assertListEqual(['You are not having a spree right now'], self.bill.message_history)
        self.assertListEqual(['You are not having a spree right now'], self.mike.message_history)

    def test_cmd_spree_with_arguments_and_no_spree(self):
        # GIVEN
        self.init()
        self.bill.connects('1')
        self.mike.connects('2')
        # WHEN
        self.bill.says("!spree mike")
        self.mike.says("!spree bill")
        # THEN
        self.assertListEqual(['Mike is not having a spree right now'], self.bill.message_history)
        self.assertListEqual(['Bill is not having a spree right now'], self.mike.message_history)

    def test_cmd_spree_with_no_arguments_and_spree(self):
        # GIVEN
        self.init()
        self.bill.connects('1')
        self.mike.connects('2')
        # WHEN
        for x in range(5):
            self.console.queueEvent(self.console.getEvent('EVT_CLIENT_KILL', client=self.bill, target=self.mike))
        self.bill.says("!spree")
        self.mike.says("!spree")
        # THEN
        self.assertListEqual(['You have 5 kills in a row'], self.bill.message_history)
        self.assertListEqual(['You have 5 deaths in a row'], self.mike.message_history)

    def test_cmd_spree_with_arguments_and_spree(self):
        # GIVEN
        self.init()
        self.bill.connects('1')
        self.mike.connects('2')
        # WHEN
        for x in range(5):
            self.console.queueEvent(self.console.getEvent('EVT_CLIENT_KILL', client=self.mike, target=self.bill))
        self.bill.says("!spree mike")
        self.mike.says("!spree bill")
        # THEN
        self.assertListEqual(['Mike has 5 kills in a row'], self.bill.message_history)
        self.assertListEqual(['Bill has 5 deaths in a row'], self.mike.message_history)

    def test_cmd_spree_with_invalid_client_handle(self):
        # GIVEN
        self.init()
        self.bill.connects('1')
        self.mike.connects('2')
        # WHEN
        self.bill.says("!spree bob")
        # THEN
        self.assertListEqual(['No players found matching bob'], self.bill.message_history)