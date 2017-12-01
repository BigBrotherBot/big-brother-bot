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

from tests.plugins.location import LocationTestCase


class Test_commands(LocationTestCase):

    def test_cmd_locate_no_arguments(self):
        # GIVEN
        self.mike.connects('1')
        self.bill.connects('2')
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says("!locate")
        # THEN
        self.assertListEqual(['missing data, try !help locate'], self.mike.message_history)

    def test_cmd_locate_failed(self):
        # GIVEN
        self.mike.connects('1')
        self.bill.connects('2')
        self.bill.location = None
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says("!locate bill")
        # THEN
        self.assertListEqual(['Could not locate Bill'], self.mike.message_history)

    def test_cmd_locate(self):
        # GIVEN
        self.mike.connects('1')
        self.bill.connects('2')
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says("!locate bill")
        # THEN
        self.assertListEqual(['Bill is connected from Mountain View (United States)'], self.mike.message_history)

    def test_cmd_distance_no_arguments(self):
        # GIVEN
        self.mike.connects('1')
        self.bill.connects('2')
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says("!distance")
        # THEN
        self.assertListEqual(['missing data, try !help distance'], self.mike.message_history)

    def test_cmd_distance_self(self):
        # GIVEN
        self.mike.connects('1')
        self.bill.connects('2')
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says("!distance mike")
        # THEN
        self.assertListEqual(['Sorry, I\'m not that smart...meh!'], self.mike.message_history)

    def test_cmd_distance_failed(self):
        # GIVEN
        self.mike.connects('1')
        self.bill.connects('2')
        self.bill.location = None
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says("!distance bill")
        # THEN
        self.assertListEqual(['Could not compute distance with Bill'], self.mike.message_history)

    def test_cmd_distance(self):
        # GIVEN
        self.mike.connects('1')
        self.bill.connects('2')
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says("!distance bill")
        # THEN
        self.assertListEqual(['Bill is 10068.18 km away from you'], self.mike.message_history)

    def test_cmd_isp_no_arguments(self):
        # GIVEN
        self.mike.connects('1')
        self.bill.connects('2')
        # WHEN
        self.bill.clearMessageHistory()
        self.bill.says("!isp")
        # THEN
        self.assertListEqual(['missing data, try !help isp'], self.bill.message_history)

    def test_cmd_isp_failed(self):
        # GIVEN
        self.mike.connects('1')
        self.bill.connects('2')
        self.mike.location = None
        # WHEN
        self.bill.clearMessageHistory()
        self.bill.says("!isp mike")
        # THEN
        self.assertListEqual(['Could not determine Mike isp'], self.bill.message_history)

    def test_cmd_isp(self):
        # GIVEN
        self.mike.connects('1')
        self.bill.connects('2')
        # WHEN
        self.bill.clearMessageHistory()
        self.bill.says("!isp mike")
        # THEN
        self.assertListEqual(['Mike is using Fastweb as isp'], self.bill.message_history)