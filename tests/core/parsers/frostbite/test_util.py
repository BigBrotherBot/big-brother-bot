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

import unittest2 as unittest
from b3.parsers.frostbite.util import BanlistContent, PlayerInfoBlock



class TestBanlistContent(unittest.TestCase):
    def test_bad(self):
        self.assertRaises(TypeError, BanlistContent, None)
        self.assertRaises(IndexError, BanlistContent, [])
    def test_minimal(self):
        self.assertEqual(0, len(BanlistContent([0])))
        self.assertEqual('BanlistContent[]', repr(BanlistContent([0])))
        self.assertEqual(0, len(BanlistContent(['0'])))
        self.assertEqual('BanlistContent[]', repr(BanlistContent(['0'])))
        self.assertEqual(1, len(BanlistContent(['1','d1','d2','d3','d4','d5'])))
        self.assertEqual("BanlistContent[{'idType': 'd1', 'reason': 'd5', 'banType': 'd3', 'id': 'd2', 'time': 'd4'}]", repr(BanlistContent(['1','d1','d2','d3','d4','d5'])))
    def test_1(self):
        bloc = BanlistContent(['2','d1','d2','d3','d4','d5','p1','p2','p3','p4','p5'])
        self.assertEqual(2, len(bloc))
        self.assertEqual("BanlistContent[{'idType': 'd1', 'reason': 'd5', 'banType': 'd3', 'id': 'd2', 'time': 'd4'}{'idType': 'p1', 'reason': 'p5', 'banType': 'p3', 'id': 'p2', 'time': 'p4'}]", repr(bloc))



class TestPlayerInfoBlock(unittest.TestCase):
    def test_no_param(self):
        self.assertRaises(TypeError, PlayerInfoBlock, None)
    def test_none(self):
        self.assertRaises(TypeError, PlayerInfoBlock, (None,))
    def test_empty_list(self):
        self.assertRaises(TypeError, PlayerInfoBlock, ([],))
    def test_bad_list(self):
        self.assertRaises(TypeError, PlayerInfoBlock, ([None],))
        self.assertRaises(TypeError, PlayerInfoBlock, ([0],))
        self.assertRaises(TypeError, PlayerInfoBlock, ([0,1],))
    def test_minimal(self):
        self.assertEqual(0, len(PlayerInfoBlock([0,0])))
        self.assertEqual('PlayerInfoBlock[]', repr(PlayerInfoBlock([0,0])))
        self.assertEqual(0, len(PlayerInfoBlock(['0','0'])))
        self.assertEqual(0, len(PlayerInfoBlock(['1','test','0'])))
        self.assertEqual('PlayerInfoBlock[]', repr(PlayerInfoBlock(['1','test','0'])))
    def test_1(self):
        bloc = PlayerInfoBlock(['1','param1','1','blabla'])
        self.assertEqual(1, len(bloc))
        self.assertEqual('blabla', bloc[0]['param1'])
        self.assertEqual("PlayerInfoBlock[{'param1': 'blabla'}]", repr(bloc))
    def test_2(self):
        bloc = PlayerInfoBlock(['1','param1','2','bla1', 'bla2'])
        self.assertEqual(2, len(bloc))
        self.assertEqual('bla1', bloc[0]['param1'])
        self.assertEqual('bla2', bloc[1]['param1'])
        self.assertEqual("PlayerInfoBlock[{'param1': 'bla1'}{'param1': 'bla2'}]", repr(bloc))
    def test_3(self):
        bloc = PlayerInfoBlock(['2','param1','param2','2','bla1','bla2','foo1','foo2'])
        self.assertEqual(2, len(bloc))
        self.assertEqual('bla1', bloc[0]['param1'])
        self.assertEqual('bla2', bloc[0]['param2'])
        self.assertEqual('foo1', bloc[1]['param1'])
        self.assertEqual('foo2', bloc[1]['param2'])
        self.assertEqual("PlayerInfoBlock[{'param2': 'bla2', 'param1': 'bla1'}{'param2': 'foo2', 'param1': 'foo1'}]", repr(bloc))
