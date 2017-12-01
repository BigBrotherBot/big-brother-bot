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

from tests.plugins.callvote import CallvoteTestCase

class Test_commands(CallvoteTestCase):

    def test_cmd_veto(self):
        # GIVEN
        self.init()
        self.mike.connects("1")
        self.bill.connects("2")
        self.mark.connects("3")
        self.sara.connects("4")
        # WHEN
        self.console.parseLine('''Callvote: 4 - "map ut4_dressingroom"''')
        self.mike.says('!veto')
        # THEN
        self.assertIsNone(self.p.callvote)

    def test_cmd_lastvote_legit(self):
        # GIVEN
        self.init()
        self.mike.connects("1")
        self.bill.connects("2")
        self.mark.connects("3")
        self.sara.connects("4")
        # WHEN
        self.console.parseLine('''Callvote: 4 - "map ut4_casa"''')
        self.p.callvote['time'] = self.p.getTime() - 10  # fake timestamp
        self.console.parseLine('''VotePassed: 3 - 0 - "map ut4_casa"''')
        self.mike.clearMessageHistory()
        self.mike.says('!lastvote')
        # THEN
        self.assertIsNotNone(self.p.callvote)
        self.assertListEqual(["Last vote issued by Sara 10 seconds ago",
                              "Type: map - Data: ut4_casa",
                              "Result: 3:0 on 4 clients"], self.mike.message_history)