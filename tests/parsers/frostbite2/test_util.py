#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2011 Courgette
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

import unittest
from b3.parsers.frostbite2.util import BanlistContent, BanlistContentError, PlayerInfoBlock, TeamScoresBlock, MapListBlock, MapListBlockError


class Test_BanlistContent(unittest.TestCase):

    def test_bad(self):
        self.assertRaises(BanlistContentError, BanlistContent, ['x'])
        self.assertRaises(BanlistContentError, BanlistContent, ['a1','a2','a3'])
        self.assertRaises(BanlistContentError, BanlistContent, ['a1','a2','a3','a4','a5'])
        self.assertRaises(BanlistContentError, BanlistContent, ['a1','a2','a3','a4','a5','a6','a7'])
        self.assertRaises(BanlistContentError, BanlistContent, 'foo')

    def test_minimal(self):
        blc = BanlistContent([])
        self.assertEqual(0, len(blc))
        self.assertEqual('BanlistContent[]', repr(blc))
        blc = BanlistContent()
        self.assertEqual(0, len(blc))
        self.assertEqual('BanlistContent[]', repr(blc))
        blc = BanlistContent(['name', 'Averell', 'seconds', '3600', '0', 'reason 2'])
        self.assertEqual(1, len(blc))
        self.assertEqual("BanlistContent[{'idType': 'name', 'seconds_left': '3600', 'reason': 'reason 2', 'banType': 'seconds', 'rounds_left': '0', 'id': 'Averell'}]", repr(blc))

    def test_1(self):
        bloc = BanlistContent([
            'name', 'William', 'perm', '0', '0', 'reason 1',
            'name', 'Averell', 'seconds', '3600', '0', 'reason 2',
        ])
        self.assertEqual(2, len(bloc))
        self.assertEqual("BanlistContent[{'idType': 'name', 'seconds_left': '0', 'reason': 'reason 1', 'banType': 'perm', 'rounds_left': '0', 'id': 'William'}, \
{'idType': 'name', 'seconds_left': '3600', 'reason': 'reason 2', 'banType': 'seconds', 'rounds_left': '0', 'id': 'Averell'}]", repr(bloc))

    def test_slice(self):
        bloc = BanlistContent([
            'name', 'William', 'perm', None , None, 'reason 1',
            'name', 'Averell', 'seconds', 3600, None , 'reason 2',
            'name', 'Jack', 'rounds', None, 2, 'reason 3',
            'name', 'Joe', 'seconds', 120 , None, 'reason 4',
            'guid', 'EA_ababab564ba654ba654ba', 'seconds', 120, None , 'reason 4',
        ])
        self.assertEqual(5, len(bloc))
        self.assertEqual(2, len(bloc[1:3]))
        print bloc[1:3]
        self.assertEqual('name', bloc[1:3][0]['idType'])
        self.assertEqual('Averell', bloc[1:3][0]['id'])
        self.assertEqual('seconds', bloc[1:3][0]['banType'])
        self.assertEqual(3600, bloc[1:3][0]['seconds_left'])
        self.assertEqual(None, bloc[1:3][0]['rounds_left'])
        self.assertEqual('reason 2', bloc[1:3][0]['reason'])

        self.assertEqual('name', bloc[1:3][1]['idType'])
        self.assertEqual('Jack', bloc[1:3][1]['id'])
        self.assertEqual('rounds', bloc[1:3][1]['banType'])
        self.assertEqual(None, bloc[1:3][1]['seconds_left'])
        self.assertEqual(2, bloc[1:3][1]['rounds_left'])
        self.assertEqual('reason 3', bloc[1:3][1]['reason'])


    def test_append(self):
        data1 = ['a1','a2','a3','a4','a5','a6', 'b1','b2','b3','b4','b5','b6']
        data2 = ['c1','c2','c3','c4','c5','a6']
        # check both data lists make valid MapListBlock individually
        blc1 = BanlistContent(data1)
        self.assertEqual(2, len(blc1))
        blc2 = BanlistContent(data2)
        self.assertEqual(1, len(blc2))
        # check both 2nd list can be appended to the 1st one.
        blc3 = BanlistContent(data1)
        blc3.append(data2)
        # check new list length
        blc3_length = len(blc3)
        self.assertEqual(len(blc1) + len(blc2), blc3_length)
        # check appending empty stuff does not affect current length
        blc3.append([])
        self.assertEqual(blc3_length, len(blc3))



class Test_PlayerInfoBlock(unittest.TestCase):

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

    def test_slice(self):
        bloc = PlayerInfoBlock(['2','param1','param2','4','player0-p1','player0-p2','player1-p1','player1-p2', 'player2-p1','player2-p2','player3-p1','player3-p2' ])
        self.assertEqual(4, len(bloc))
        self.assertEqual(2, len(bloc[1:3]))
        self.assertEqual('player1-p1', bloc[1:3][0]['param1'])
        self.assertEqual('player1-p2', bloc[1:3][0]['param2'])
        self.assertEqual('player2-p1', bloc[1:3][1]['param1'])
        self.assertEqual('player2-p2', bloc[1:3][1]['param2'])
        self.assertEqual("[{'param2': 'player1-p2', 'param1': 'player1-p1'}, {'param2': 'player2-p2', 'param1': 'player2-p1'}]", repr(bloc[1:3]))


class Test_TeamScoreBlock(unittest.TestCase):

    def test_no_param(self):
        self.assertRaises(TypeError, TeamScoresBlock, None)

    def test_none(self):
        self.assertRaises(TypeError, TeamScoresBlock, (None,))

    def test_empty_list(self):
        self.assertRaises(TypeError, TeamScoresBlock, ([],))

    def test_bad_list(self):
        self.assertRaises(TypeError, TeamScoresBlock, ([None],))
        self.assertRaises(TypeError, TeamScoresBlock, ([0],))
        self.assertRaises(TypeError, TeamScoresBlock, ([0,1],))

    def test_minimal(self):
        self.assertEqual(0, len(TeamScoresBlock([0,1000])))
        self.assertEqual('TeamScoresBlock[], target: 100', repr(TeamScoresBlock([0,100])))
        self.assertEqual(0, len(TeamScoresBlock(['0','0'])))
        self.assertEqual(1, len(TeamScoresBlock(['1','10','5000'])))
        self.assertEqual('TeamScoresBlock[10], target: 5000', repr(TeamScoresBlock(['1','10','5000'])))

    def test_1(self):
        bloc = TeamScoresBlock(['2','15','48','2500'])
        self.assertEqual(2, len(bloc))
        self.assertEqual(15, bloc[0])
        self.assertEqual(48, bloc[1])
        self.assertEqual(2500, bloc.get_target_score())
        self.assertEqual("TeamScoresBlock[15, 48], target: 2500", repr(bloc))



class Test_MapListBlock(unittest.TestCase):

    def test_no_param(self):
        self.assertEqual(0, len(MapListBlock()))

    def test_none(self):
        self.assertRaises(MapListBlockError, MapListBlock, (None,))

    def test_empty_list(self):
        self.assertRaises(MapListBlockError, MapListBlock, ([],))

    def test_bad_list(self):
        self.assertRaises(MapListBlockError, MapListBlock, ('foo',))
        self.assertRaises(MapListBlockError, MapListBlock, (['x'],))
        self.assertRaises(MapListBlockError, MapListBlock, ([None],))
        self.assertRaises(MapListBlockError, MapListBlock, ([0],))
        self.assertRaises(MapListBlockError, MapListBlock, ([0,1],))
        self.assertRaises(MapListBlockError, MapListBlock, ([0,'x'],))
        self.assertRaises(MapListBlockError, MapListBlock, (['a','b','c','d'],))
        self.assertRaises(MapListBlockError, MapListBlock, (['1','3', 'a1','b1','1', 'a2'],))
        self.assertRaises(MapListBlockError, MapListBlock, (['1','3', 'a1','b1','xxx'],))

    def test_minimal(self):
        self.assertEqual(0, len(MapListBlock([0,3])))
        self.assertEqual('MapListBlock[]', repr(MapListBlock([0,3])))
        self.assertEqual(0, len(MapListBlock(['0','3'])))
        tmp = MapListBlock(['1', '3', 'test','mode', '2'])
        self.assertEqual(1, len(tmp), repr(tmp))
        self.assertEqual('MapListBlock[]', repr(MapListBlock(['0','3'])))
        self.assertEqual(0, len(MapListBlock(['0','3']).getByName('MP_003')))

    def test_1(self):
        bloc = MapListBlock(['1', '3', 'test','mode', '2'])
        self.assertEqual(1, len(bloc))
        self.assertEqual('test', bloc[0]['name'])
        self.assertEqual('mode', bloc[0]['gamemode'])
        self.assertEqual(2, bloc[0]['num_of_rounds'])
        self.assertEqual("MapListBlock[test:mode:2]", repr(bloc))
        self.assertEqual(0, len(bloc.getByName('MP_003')))
        self.assertEqual(1, len(bloc.getByName('test')))

    def test_2(self):
        bloc = MapListBlock(['2','3','map1','mode1', '1', 'map2', 'mode2', '2'])
        self.assertEqual(2, len(bloc))
        self.assertEqual('map1', bloc[0]['name'])
        self.assertEqual('mode1', bloc[0]['gamemode'])
        self.assertEqual(1, bloc[0]['num_of_rounds'])
        self.assertEqual('map2', bloc[1]['name'])
        self.assertEqual('mode2', bloc[1]['gamemode'])
        self.assertEqual(2, bloc[1]['num_of_rounds'])
        self.assertEqual("MapListBlock[map1:mode1:1, map2:mode2:2]", repr(bloc))
        self.assertEqual(0, len(bloc.getByName('MP_003')))
        self.assertEqual(1, len(bloc.getByName('map1')))
        self.assertEqual(1, len(bloc.getByName('map2')))
        self.assertIn(0, bloc.getByName('map1'))
        self.assertIn(1, bloc.getByName('map2'))
        self.assertTrue(bloc.getByName('map1')[0]['gamemode'] == 'mode1')
        self.assertTrue(bloc.getByName('map2')[1]['gamemode'] == 'mode2')
        self.assertEqual(0, len(bloc.getByNameAndGamemode('map1', 'mode?')))
        self.assertEqual(1, len(bloc.getByNameAndGamemode('map1', 'mode1')))
        self.assertEqual(0, len(bloc.getByNameAndGamemode('map2', 'mode?')))
        self.assertEqual(1, len(bloc.getByNameAndGamemode('map2', 'mode2')))
        self.assertIn(0, bloc.getByNameAndGamemode('map1', 'mode1'))
        self.assertIn(1, bloc.getByNameAndGamemode('map2', 'mode2'))


    def test_3(self):
        bloc = MapListBlock(['3','3', 'map1','mode1','1', 'map2','mode2','2', 'map1','mode2','2'])
        self.assertEqual(3, len(bloc))
        self.assertEqual('map1', bloc[2]['name'])
        self.assertEqual('mode2', bloc[2]['gamemode'])
        self.assertEqual(0, len(bloc.getByName('MP_003')))
        self.assertEqual(2, len(bloc.getByName('map1')))
        self.assertEqual(1, len(bloc.getByName('map2')))
        self.assertEqual("MapListBlock[map1:mode1:1, map2:mode2:2, map1:mode2:2]", repr(bloc))
        self.assertIn(0, bloc.getByName('map1'))
        self.assertIn(1, bloc.getByName('map2'))
        self.assertIn(2, bloc.getByName('map1'))
        self.assertTrue(bloc.getByName('map1')[0]['gamemode'] == 'mode1')
        self.assertTrue(bloc.getByName('map1')[2]['gamemode'] == 'mode2')
        self.assertTrue(bloc.getByName('map2')[1]['gamemode'] == 'mode2')
        self.assertEqual(0, len(bloc.getByNameAndGamemode('map1', 'mode?')))
        self.assertEqual(1, len(bloc.getByNameAndGamemode('map1', 'mode1')))
        self.assertEqual(1, len(bloc.getByNameAndGamemode('map1', 'mode2')))
        self.assertEqual(0, len(bloc.getByNameAndGamemode('map2', 'mode?')))
        self.assertEqual(0, len(bloc.getByNameAndGamemode('map2', 'mode1')))
        self.assertEqual(1, len(bloc.getByNameAndGamemode('map2', 'mode2')))
        self.assertIn(0, bloc.getByNameAndGamemode('map1', 'mode1'))
        self.assertIn(1, bloc.getByNameAndGamemode('map2', 'mode2'))
        self.assertIn(2, bloc.getByNameAndGamemode('map1', 'mode2'))


class Test_MapListBlock_append(unittest.TestCase):

    def test_append_list_with_different_num_words(self):
        data1 = [1, 3, 'a1','a2',1]
        data2 = [1, 4, 'b1','b2',1,'b4']
        # check both data lists make valid MapListBlock individually
        self.assertEqual(1, len(MapListBlock(data1)))
        self.assertEqual(1, len(MapListBlock(data2)))
        # check both 2nd list cannot be appended to the 1st one.
        mlb1 = MapListBlock(data1)
        self.assertEqual(3, mlb1._num_words)
        try:
            mlb1.append(data2)
        except MapListBlockError, err:
            self.assertIn('cannot append data', err.message, "expecting error message to contain 'cannot append data' but got %r instead" % err)
        except Exception, err:
            self.fail("expecting MapListBlockError but got %r instead" % err)
        else:
            self.fail("expecting MapListBlockError")


    def test_append_list_with_same_num_words(self):
        data1 = [1, 3, 'a1','a2',1]
        data2 = [1, 3, 'b1','b2',2]
        # check both data lists make valid MapListBlock individually
        mlb1 = MapListBlock(data1)
        self.assertEqual(1, len(mlb1))
        mlb2 = MapListBlock(data2)
        self.assertEqual(1, len(mlb2))
        # check both 2nd list can be appended to the 1st one.
        mlb3 = MapListBlock(data1)
        mlb3.append(data2)
        # check new list length
        self.assertEqual(len(mlb1) + len(mlb2), len(mlb3))


if __name__ == '__main__':
    unittest.main()
