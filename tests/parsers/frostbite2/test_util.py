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
from b3.parsers.frostbite2.util import BanlistContent, PlayerInfoBlock, TeamScoresBlock, MapListBlock, MapListBlockError


class Test_BanlistContent(unittest.TestCase):

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

    def test_slice(self):
        bloc = BanlistContent([5,
            'name', 'William', 'perm', None , 'reason 1',
            'name', 'Averell', 'seconds', 3600 , 'reason 2',
            'name', 'Jack', 'seconds', 60 , 'reason 3',
            'name', 'Joe', 'seconds', 120 , 'reason 4',
            'guid', 'EA_ababab564ba654ba654ba', 'seconds', 120 , 'reason 4',
        ])
        self.assertEqual(5, len(bloc))
        self.assertEqual(2, len(bloc[1:3]))
        print bloc[1:3]
        self.assertEqual('name', bloc[1:3][0]['idType'])
        self.assertEqual('Averell', bloc[1:3][0]['id'])
        self.assertEqual('seconds', bloc[1:3][0]['banType'])
        self.assertEqual(3600, bloc[1:3][0]['time'])
        self.assertEqual('reason 2', bloc[1:3][0]['reason'])

        self.assertEqual('name', bloc[1:3][1]['idType'])
        self.assertEqual('Jack', bloc[1:3][1]['id'])
        self.assertEqual('seconds', bloc[1:3][1]['banType'])
        self.assertEqual(60, bloc[1:3][1]['time'])
        self.assertEqual('reason 3', bloc[1:3][1]['reason'])



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

    def _assertRaiseMapListBlockError(self, data):
        try:
            MapListBlock(data)
        except MapListBlockError, err:
            return err
        except Exception, err:
            self.fail("expecting MapListBlockError but got %r instead" % err)
        else:
            self.fail("expecting MapListBlockError")

    def test_no_param(self):
        self.assertEqual(0, len(MapListBlock()))

    def test_none(self):
        self.assertRaises(MapListBlockError, MapListBlock, (None,))

    def test_empty_list(self):
        self.assertRaises(MapListBlockError, MapListBlock, ([],))

    def test_bad_list(self):
        self._assertRaiseMapListBlockError([None])
        self._assertRaiseMapListBlockError([0])
        self._assertRaiseMapListBlockError([0,1])
        self._assertRaiseMapListBlockError(['a','b','c','d'])
        self._assertRaiseMapListBlockError(['1','3', 'a1','b1','1', 'a2'])
        self._assertRaiseMapListBlockError(['1','3', 'a1','b1','xxx'])

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
