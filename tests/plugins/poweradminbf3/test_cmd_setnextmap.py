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

import logging
from mockito import when, verify
from b3.config import CfgConfigParser
from b3.plugins.poweradminbf3 import Poweradminbf3Plugin
from tests.plugins.poweradminbf3 import Bf3TestCase


class Test_cmd_setnextmap(Bf3TestCase):
    def setUp(self):
        super(Test_cmd_setnextmap, self).setUp()
        self.conf = CfgConfigParser()
        self.conf.loadFromString("""[commands]
setnextmap-snmap: 20
        """)
        self.p = Poweradminbf3Plugin(self.console, self.conf)
        self.p.onLoadConfig()
        self.p.onStartup()

        logging.getLogger('output').setLevel(logging.DEBUG)
        self.console.game.gameType = 'ConquestSmall0'
        self.console.game.serverinfo = {'roundsTotal': 2}


    def test_no_argument(self):
        self.superadmin.connects('superadmin')
        self.superadmin.message_history = []
        self.superadmin.says('!setnextmap')
        self.assertEqual(['Invalid or missing data, try !help setnextmap'], self.superadmin.message_history)


    def test_my_getMapsSoundingLike_3_suggestions(self):
        when(self.console).getMapsSoundingLike('somemap').thenReturn(['map #1', 'map #2', 'map #3'])
        self.superadmin.connects('superadmin')
        self.superadmin.message_history = []
        self.superadmin.says('!setnextmap somemap')
        self.assertEqual(['do you mean : map #1, map #2, map #3 ?'], self.superadmin.message_history)

    def test_my_getMapsSoundingLike_finds_the_map(self):
        when(self.console).getMapsSoundingLike('somemap').thenReturn('MP_Subway')

        when(self.console).write(('mapList.list',)).thenReturn([5, 3,
                                                                 'MP_001', 'ConquestSmall0', '1',
                                                                 'MP_003', 'RushLarge0', '1',
                                                                 'MP_Subway', 'SquadRush0', '1',
                                                                 'MP_007', 'SquadDeathMatch0', '1',
                                                                 'MP_011', 'TeamDeathMatch0', '1'])
        when(self.console).write(('mapList.getRounds',)).thenReturn([0, 1])
        when(self.console).write(('mapList.getMapIndices',)).thenReturn([0, 1])

        self.superadmin.connects('superadmin')
        self.superadmin.message_history = []
        self.superadmin.says('!setnextmap somemap')
        self.assertEqual(['next map set to Operation Metro (Conquest) 2 rounds'], self.superadmin.message_history)


    def test_empty_list(self):
        when(self.console).getMapsSoundingLike('map1').thenReturn('MP_Subway')
        when(self.console).write(('mapList.list',)).thenReturn([0, 3])
        self.superadmin.connects('superadmin')
        self.superadmin.message_history = []
        self.superadmin.says('!snmap map1')
        verify(self.console).write(('mapList.add', 'MP_Subway', 'ConquestSmall0', 2, 0))
        verify(self.console).write(('mapList.setNextMapIndex', 0))
        self.assertEqual(['next map set to Operation Metro (Conquest) 2 rounds'], self.superadmin.message_history)


    def test_wanted_map_is_not_in_list(self):
        when(self.console).getMapsSoundingLike('map1').thenReturn('MP_Subway')

        when(self.console).write(('mapList.list',)).thenReturn([4, 3,
                                                                 'MP_001', 'ConquestSmall0', '1',
                                                                 'MP_003', 'RushLarge0', '1',
                                                                 'MP_007', 'SquadDeathMatch0', '1',
                                                                 'MP_011', 'TeamDeathMatch0', '1'])
        when(self.console).write(('mapList.getMapIndices',)).thenReturn([4, 1])


        self.superadmin.connects('superadmin')
        self.superadmin.message_history = []
        self.superadmin.says('!snmap map1')
        verify(self.console).write(('mapList.add', 'MP_Subway', 'ConquestSmall0', 2, 5))
        verify(self.console).write(('mapList.setNextMapIndex', 5))
        self.assertEqual(['next map set to Operation Metro (Conquest) 2 rounds'], self.superadmin.message_history)


    def test_wanted_map_is_in_list(self):
        when(self.console).getMapsSoundingLike('map1').thenReturn('MP_Subway')

        when(self.console).write(('mapList.list',)).thenReturn([5, 3,
                                                                 'MP_001', 'ConquestSmall0', '1',
                                                                 'MP_003', 'RushLarge0', '1',
                                                                 'MP_Subway', 'SquadRush0', '1',
                                                                 'MP_007', 'SquadDeathMatch0', '1',
                                                                 'MP_011', 'TeamDeathMatch0', '1'])
        when(self.console).write(('mapList.getMapIndices',)).thenReturn([0, 1])


        self.superadmin.connects('superadmin')
        self.superadmin.message_history = []
        self.superadmin.says('!snmap map1, SquadRush0, 1')
        verify(self.console).write(('mapList.setNextMapIndex', 2))
        self.assertEqual(['next map set to Operation Metro (Squad Rush) 1 round'], self.superadmin.message_history)


    def test_wanted_map_is_already_the_next_map(self):
        when(self.console).getMapsSoundingLike('map1').thenReturn('MP_Subway')

        when(self.console).write(('mapList.list',)).thenReturn([5, 3,
                                                                 'MP_001', 'ConquestSmall0', '1',
                                                                 'MP_003', 'RushLarge0', '1',
                                                                 'MP_Subway', 'SquadRush0', '1',
                                                                 'MP_007', 'SquadDeathMatch0', '1',
                                                                 'MP_011', 'TeamDeathMatch0', '1'])
        when(self.console).write(('mapList.getMapIndices',)).thenReturn([0, 2])

        self.superadmin.connects('superadmin')
        self.superadmin.message_history = []
        self.superadmin.says('!snmap map1, SquadRush0, 1')
        verify(self.console).write(('mapList.setNextMapIndex', 2))
        self.assertEqual(['next map set to Operation Metro (Squad Rush) 1 round'], self.superadmin.message_history)


    def test_wanted_map_is_in_the_list_multiple_times(self):
        when(self.console).getMapsSoundingLike('map1').thenReturn('MP_Subway')

        when(self.console).write(('mapList.list',)).thenReturn([10, 3,
                                                                 'MP_001', 'ConquestSmall0', '1',
                                                                 'MP_003', 'ConquestSmall0', '1',
                                                                 'MP_Subway', 'ConquestSmall0', '1', #2
                                                                 'MP_007', 'ConquestSmall0', '1',
                                                                 'MP_011', 'ConquestSmall0', '1',
                                                                 'MP_012', 'ConquestSmall0', '1',
                                                                 'MP_Subway', 'ConquestSmall0', '1', #6
                                                                 'MP_013', 'ConquestSmall0', '1',
                                                                 'MP_017', 'ConquestSmall0', '1',
                                                                 'MP_018', 'ConquestSmall0', '1',
                                                                 ])
        when(self.console).write(('mapList.getMapIndices',)).thenReturn([0, 1])

        self.superadmin.connects('superadmin')
        self.superadmin.message_history = []
        self.superadmin.says('!snmap map1, ConquestSmall0, 1')
        verify(self.console).write(('mapList.setNextMapIndex', 2))
        self.assertEqual(['next map set to Operation Metro (Conquest) 1 round'], self.superadmin.message_history)


    def test_wanted_map_is_in_the_list_multiple_times_2(self):
        when(self.console).getMapsSoundingLike('map1').thenReturn('MP_Subway')

        when(self.console).write(('mapList.list',)).thenReturn([10, 3,
                                                                 'MP_001', 'ConquestSmall0', '1',
                                                                 'MP_003', 'ConquestSmall0', '1',
                                                                 'MP_Subway', 'ConquestSmall0', '1', #2
                                                                 'MP_007', 'ConquestSmall0', '1',
                                                                 'MP_011', 'ConquestSmall0', '1',
                                                                 'MP_012', 'ConquestSmall0', '1',
                                                                 'MP_Subway', 'ConquestSmall0', '1', #6
                                                                 'MP_013', 'ConquestSmall0', '1',
                                                                 'MP_017', 'ConquestSmall0', '1',
                                                                 'MP_018', 'ConquestSmall0', '1',
                                                                 ])
        when(self.console).write(('mapList.getMapIndices',)).thenReturn([2, 3])

        self.superadmin.connects('superadmin')
        self.superadmin.message_history = []
        self.superadmin.says('!snmap map1, ConquestSmall0, 1')
        verify(self.console).write(('mapList.setNextMapIndex', 6))
        self.assertEqual(['next map set to Operation Metro (Conquest) 1 round'], self.superadmin.message_history)


    def test_wanted_map_is_in_the_list_multiple_times_3(self):
        when(self.console).getMapsSoundingLike('map1').thenReturn('MP_Subway')

        when(self.console).write(('mapList.list',)).thenReturn([10, 3,
                                                                 'MP_001', 'ConquestSmall0', '1',
                                                                 'MP_003', 'ConquestSmall0', '1',
                                                                 'MP_Subway', 'ConquestSmall0', '1', #2
                                                                 'MP_007', 'ConquestSmall0', '1',
                                                                 'MP_011', 'ConquestSmall0', '1',
                                                                 'MP_012', 'ConquestSmall0', '1',
                                                                 'MP_Subway', 'ConquestSmall0', '1', #6
                                                                 'MP_013', 'ConquestSmall0', '1',
                                                                 'MP_017', 'ConquestSmall0', '1',
                                                                 'MP_018', 'ConquestSmall0', '1',
                                                                 ])
        when(self.console).write(('mapList.getMapIndices',)).thenReturn([6, 7])

        self.superadmin.connects('superadmin')
        self.superadmin.message_history = []
        self.superadmin.says('!snmap map1, conquest, 1')
        verify(self.console).write(('mapList.setNextMapIndex', 2))
        self.assertEqual(['next map set to Operation Metro (Conquest) 1 round'], self.superadmin.message_history)

