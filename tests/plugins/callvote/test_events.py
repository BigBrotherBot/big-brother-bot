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
from tests.plugins.callvote import CallvoteTestCase

class Test_events(CallvoteTestCase):

    def tearDown(self):
        self.mike.disconnects()
        self.bill.disconnects()
        self.mark.disconnects()
        self.sara.disconnects()
        CallvoteTestCase.tearDown(self)

    def test_client_callvote_legit(self):
        # GIVEN
        self.init()
        self.mike.connects("1")
        self.bill.connects("2")
        self.mark.connects("3")
        self.sara.connects("4")
        # WHEN
        self.console.parseLine('''Callvote: 1 - "map ut4_dressingroom"''')
        # THEN
        self.assertIsNotNone(self.p.callvote)
        self.assertEqual(self.mike, self.p.callvote['client'])
        self.assertEqual('map', self.p.callvote['type'])
        self.assertEqual('ut4_dressingroom', self.p.callvote['args'])
        self.assertEqual(1399725576, self.p.callvote['time'])
        self.assertEqual(3, self.p.callvote['max_num'])

    def test_client_callvote_not_enough_level(self):
        # GIVEN
        self.init(dedent(r"""
            [callvoteminlevel]
            clientkick: admin
            clientkickreason: admin
            kick: admin
        """))
        self.mike.connects("1")
        self.bill.connects("2")
        self.mark.connects("3")
        self.sara.connects("4")
        # WHEN
        self.sara.clearMessageHistory()
        self.console.parseLine('''Callvote: 4 - "kick bill"''')
        # THEN
        self.assertIsNone(self.p.callvote)
        self.assertListEqual(["You can't issue this callvote. Required level: Admin"], self.sara.message_history)

    def test_client_callvote_map_not_enough_level(self):
        # GIVEN
        self.init(dedent(r"""
            [callvotespecialmaplist]
            ut4_abbey: admin
            ut4_abbeyctf: superadmin
        """))
        self.mike.connects("1")
        self.bill.connects("2")
        self.mark.connects("3")
        self.sara.connects("4")
        # WHEN
        self.sara.clearMessageHistory()
        self.console.parseLine('''Callvote: 4 - "map ut4_abbey"''')
        # THEN
        self.assertIsNone(self.p.callvote)
        self.assertListEqual(["You can't issue this callvote. Required level: Admin"], self.sara.message_history)

    def test_client_callvote_passed(self):
        # GIVEN
        self.init()
        self.mike.connects("1")
        self.bill.connects("2")
        self.mark.connects("3")
        self.sara.connects("4")
        # WHEN
        self.console.parseLine('''Callvote: 4 - "map ut4_casa"''')
        self.console.parseLine('''VotePassed: 3 - 0 - "map ut4_casa"''')
        # THEN
        self.assertIsNotNone(self.p.callvote)
        self.assertEqual(self.sara, self.p.callvote['client'])
        self.assertEqual('map', self.p.callvote['type'])
        self.assertEqual('ut4_casa', self.p.callvote['args'])
        self.assertEqual(1399725576, self.p.callvote['time'])
        self.assertEqual(4, self.p.callvote['max_num'])
        self.assertEqual(3, self.p.callvote['num_yes'])
        self.assertEqual(0, self.p.callvote['num_no'])

    def test_client_callvote_failed(self):
        # GIVEN
        self.init()
        self.mike.connects("1")
        self.bill.connects("2")
        self.mark.connects("3")
        self.sara.connects("4")
        # WHEN
        self.console.parseLine('''Callvote: 4 - "map ut4_casa"''')
        self.console.parseLine('''VotePassed: 1 - 3 - "map ut4_casa"''')
        # THEN
        self.assertIsNotNone(self.p.callvote)
        self.assertEqual(self.sara, self.p.callvote['client'])
        self.assertEqual('map', self.p.callvote['type'])
        self.assertEqual('ut4_casa', self.p.callvote['args'])
        self.assertEqual(1399725576, self.p.callvote['time'])
        self.assertEqual(4, self.p.callvote['max_num'])
        self.assertEqual(1, self.p.callvote['num_yes'])
        self.assertEqual(3, self.p.callvote['num_no'])

    def test_client_callvote_finish_with_none_callvote_object(self):
        # GIVEN
        self.init()
        self.mike.connects("1")
        self.bill.connects("2")
        self.mark.connects("3")
        self.sara.connects("4")
        # WHEN
        self.console.parseLine('''VotePassed: 3 - 0 - "map ut4_casa"''')
        # THEN
        self.assertIsNone(self.p.callvote)

    def test_client_callvote_finish_with_different_arguments(self):
        # GIVEN
        self.init()
        self.mike.connects("1")
        self.bill.connects("2")
        self.mark.connects("3")
        self.sara.connects("4")
        # WHEN
        self.console.parseLine('''Callvote: 4 - "map ut4_casa"''')
        self.console.parseLine('''VotePassed: 1 - 3 - "reload"''')
        # THEN
        self.assertIsNone(self.p.callvote)