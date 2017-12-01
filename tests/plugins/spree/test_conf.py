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
from mock import Mock, call

from tests.plugins.spree import SpreeTestCase


class Test_killingspree_messages(SpreeTestCase):

    def setUp(self):
        SpreeTestCase.setUp(self)
        self.p.warning = Mock()

    def test_nominal(self):
        self.init(dedent("""
            [settings]
            reset_spree: yes

            [killingspree_messages]
            # The # character splits the 'start' spree from the 'end' spree.
            5: %player% is on a killing spree (5 kills in a row) # %player% stopped the spree of %victim%

            [loosingspree_messages]
            7: Keep it up %player%, it will come eventually # You're back in business %player%
        """))
        self.assertListEqual([], self.p.warning.mock_calls)

    def test_no_message(self):
        self.init(dedent("""
            [settings]
            reset_spree: yes

            [killingspree_messages]

            [loosingspree_messages]
            7: Keep it up %player%, it will come eventually # You're back in business %player%
        """))
        self.assertListEqual([], self.p.warning.mock_calls)

    def test_missing_dash(self):
        self.init(dedent("""
            [settings]
            reset_spree: yes

            [killingspree_messages]
            # The # character splits the 'start' spree from the 'end' spree.
            5: foo

            [loosingspree_messages]
            7: Keep it up %player%, it will come eventually # You're back in business %player%
        """))
        self.assertListEqual([call("ignoring killingspree message 'foo' due to missing '#'")],
                             self.p.warning.mock_calls)


class Test_loosingspree_messages(SpreeTestCase):

    def setUp(self):
        SpreeTestCase.setUp(self)
        self.p.warning = Mock()

    def test_nominal(self):
        self.init(dedent("""
            [settings]
            reset_spree: yes

            [killingspree_messages]

            [loosingspree_messages]
            # The # character splits the 'start' spree from the 'end' spree.
            7: Keep it up %player%, it will come eventually # You're back in business %player%
        """))
        self.assertListEqual([], self.p.warning.mock_calls)

    def test_no_message(self):
        self.init(dedent("""
            [settings]
            reset_spree: yes

            [killingspree_messages]

            [loosingspree_messages]
        """))
        self.assertListEqual([], self.p.warning.mock_calls)

    def test_missing_dash(self):
        self.init(dedent("""
            [settings]
            reset_spree: yes

            [killingspree_messages]

            [loosingspree_messages]
            # The # character splits the 'start' spree from the 'end' spree.
            7: bar
        """))
        self.assertListEqual([call("ignoring killingspree message 'bar' due to missing '#'")],
                             self.p.warning.mock_calls)
