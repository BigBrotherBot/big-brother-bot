# # -*- coding: utf-8 -*-
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2005 Michael "ThorN" Thornton
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
# --------------------------------------------------------------------------
#
# CHANGELOG :
# 1.1 - 2010/11/03 - Courgette
#    * add __repr__
#    * fix minor bug in BanlistContent
#    * add automated tests

"""\
This module provides different utilities specific to the Frostbite engine
"""
 
__author__  = 'Courgette'
__version__ = '1.1'



class BanlistContent:
    """
    help extract banlist info from a frostbite banList.list response
    
    usage :
        words = [2, 
            'name', 'Courgette', 'perm', , 'test',  
            'name', 'Courgette', 'seconds', 3600 , 'test2'] 
        bansInfo = BanlistContent(words)
        print "num of bans : %s" % len(bansInfo)
        print "first ban : %s" % bansInfo[0]
        print "second ban : %s" % bansInfo[1]
        print "the first 2 bans : %s" % bansInfo[0:2]
        for b in bansInfo:
            print b
    """
    
    def __init__(self, data):
        """Represent a frostbite banList.list response
        Request: banList.list 
        Response: OK <player ban entries> 
        Response: InvalidArguments 
        Effect: Return list of banned players/IPs/GUIDs. 
        Comment: The list starts with a number telling how many bans the list is holding. 
                 After that, 5 words (Id-type, id, ban-type, time and reason) are received for every ban in the list.
        """
        self.numOfBans = data[0]
        self.bansData = data[1:]
    
    def __len__(self):
        return int(self.numOfBans)
    
    def __getitem__(self, key):
        """Returns the ban data, for provided key (int or slice)"""
        if isinstance(key, slice):
            indices = key.indices(len(self))
            return [self.getData(i) for i in range(*indices) ]
        else:
            return self.getData(key)

    def getData(self, index):
        if index >= self.numOfBans:
            raise IndexError
        tmp = self.bansData[index*5:(index+1)*5]
        return {
            'idType': tmp[0], # name | ip | guid
            'id': tmp[1],
            'banType': tmp[2], # perm | round | seconds
            'time': tmp[3],
            'reason': tmp[4], # 80 chars max
        }

    def __repr__(self):
        txt = "BanlistContent["
        for p in self:
            txt += "%r" % p
        txt += "]"
        return txt        
        
        
        
class PlayerInfoBlock:
    """
    help extract player info from a frostbite Player Info Block which we obtain
    from admin.listPlayers
    
    usage :
        words = [3, 'name', 'guid', 'teamId', 2, 
            'Courgette', 'A32132e', 0, 
            'SpacepiG', '6546545665465', 1]
        playersInfo = PlayerInfoBlock(words)
        print "num of players : %s" % len(playersInfo)
        print "first player : %s" % playersInfo[0]
        print "second player : %s" % playersInfo[1]
        print "the first 2 players : %s" % playersInfo[0:2]
        for p in playersInfo:
            print p
    """
    
    def __init__(self, data):
        """Represent a frostbite Player info block
        The standard set of info for a group of players contains a lot of different 
        fields. To reduce the risk of having to do backwards-incompatible changes to
        the protocol, the player info block includes some formatting information.
            
        The standard set of info for a group of players contains a lot of different 
        fields. To reduce the risk of having to do backwards-incompatible changes to 
        the protocol, the player info block includes some formatting information.
        
            <number of parameters> - number of parameters for each player 
            N x <parameter type: string> - the parameter types that will be sent below 
            <number of players> - number of players following 
            M x N x <parameter value> - all parameter values for player 0, then all parameter values for player 1, etc.

        Current parameters: 
            name string - player name 
            guid string - player�s unique ID 
            teamId Team ID - player�s current team 
            squadId Squad ID - player�s current squad 
            kills integer - number of kills, as shown in the in-game scoreboard 
            deaths integer - number of deaths, as shown in the in-game scoreboard 
            score integer - score, as shown in the in-game scoreboard
        """
        self._num_parameters = int(data[0])
        self._parameter_types = data[1:1+self._num_parameters]
        self._num_players = int(data[1+self._num_parameters])
        self._players_data = data[2+self._num_parameters:]
    
    def __len__(self):
        return self._num_players
    
    def __getitem__(self, key):
        """Returns the player data, for provided key (int or slice)"""
        if isinstance(key, slice):
            indices = key.indices(len(self))
            return [self._getPlayerData(i) for i in range(*indices) ]
        else:
            return self._getPlayerData(key)

    def _getPlayerData(self, index):
        if index >= self._num_players:
            raise IndexError
        data = {}
        playerData = self._players_data[index*self._num_parameters:(index+1)*self._num_parameters]
        for i in range(self._num_parameters):
            data[self._parameter_types[i]] = playerData[i]
        return data 

    def __repr__(self):
        txt = "PlayerInfoBlock["
        for p in self:
            txt += "%r" % p
        txt += "]"
        return txt
    
    
class TeamScoresBlock:
    """
    help extract team scores info from frostbite data obtain from game events
    
    usage :
        teamScores = TeamScoresBlock([2, 130, 245, 1000])
        print "num of teams : %s" % len(teamScores)
        print "first team's score : %s" % teamScores[0]
        print "second team's : %s" % teamScores[1]
        print "the first 2 teams' scores : %s" % teamScores[0:2]
        print "target score : %s " % teamScores.get_target_score()
        for p in teamScores:
            print p
    """
    
    def __init__(self, data):
        """Represent a frostbite Team Scores block
            
        This describes the number of tickets, or kills, for each team in the current round.
        
            <number of entries: integer> - number of team scores that follow 
            N x <score: integer> - score for all teams 
            <target score: integer> - when any team reaches this score, the match ends 
        """
        self._num_teams = int(data[0])
        self._scores = tuple([int(x) for x in data[1:1+self._num_teams]])
        self._target_score = int(data[1+self._num_teams])
    
    def __len__(self):
        return self._num_teams
    
    def __getitem__(self, key):
        """Returns the team score data, for provided key (int or slice)"""
        return self._scores[key]
    
    def get_target_score(self):
        return self._target_score

    def __repr__(self):
        txt = "TeamScoresBlock["
        txt += ", ".join([repr(x) for x in self._scores])
        txt += "], target: %s" % self._target_score
        return txt
    
class MapListBlock:
    """
    help extract map list from frostbite data
    
    usage :
        mapList = MapListBlock([2, 3, "MP_001", "ConquestLarge0", 2, "MP_011", "Rush", 3])
        print "num of maps : %s" % len(mapList)
        print "first map name : %s" % mapList[0]['name']
        print "second map gamemode : %s" % mapList[1]['gamemode']
        print "the first 2 maps data : %s" % mapList[0:2]
        print "the first 2 maps num_of_rounds : %s" % [x['num_of_rounds'] for x in mapList[0:2]]
        for p in mapList:
            print p
    """
    
    def __init__(self, data):
        """This describes the set of maps which the server rotates through. 

        Format is as follows: 
            <number of maps: integer> - number of maps that follow 
            <number of words per map: integer> - number of words per map 
            <map name: string> - name of map 
            <gamemode name: string> - name of gamemode 
            <number of rounds: integer> - number of rounds to play on map before switching

        The reason for the <number of words per map> specification is future proofing; 
        in the future, DICE might add extra words per map after the first three. However, 
        the first three words are very likely to remain the same. 
        """
        self._num_maps = int(data[0])
        self._num_words = int(data[1])
        map_data = []
        for i in range(self._num_maps):
            base_index = 2 + (i * self._num_words)
            map_data.append({'name': data[base_index+0], 'gamemode': data[base_index+1], 'num_of_rounds': int(data[base_index+2])})
        self._map_data = tuple(map_data)
    
    def __len__(self):
        return self._num_maps
    
    def __getitem__(self, key):
        """Returns the map data, for provided key (int or slice)"""
        return self._map_data[key]
    
    def __repr__(self):
        txt = "MapListBlock["
        map_info_repr = []
        for p in self:
            map_info_repr.append("%(name)s:%(gamemode)s:%(num_of_rounds)s" % p)
        txt += ", ".join(map_info_repr)
        txt += "]"
        return txt

    def getByName(self, map_name):
        """Returns a dict with map indexes as keys and map info as values for all maps of given name"""
        response = {}
        i = 0
        while i < self._num_maps:
            map_info = self[i]
            if map_info['name'] == map_name:
                response[i] = map_info
            i += 1
        return response

    def getByNameAndGamemode(self, map_name, gamemode):
        """Returns a dict with map indexes as keys and map info as values for all maps of given name and given gamemode"""
        response = {}
        i = 0
        while i < self._num_maps:
            map_info = self[i]
            if map_info['name'] == map_name and map_info['gamemode'] == gamemode:
                response[i] = map_info
            i += 1
        return response


if __name__ == '__main__':
        
    import unittest
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

    class TestTeamScoreBlock(unittest.TestCase):
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
            self.assertEqual("TeamScoresBlock[15, 48], target: 2500", repr(bloc))
            
    class TestMapListBlock(unittest.TestCase):
        def test_no_param(self):
            self.assertRaises(TypeError, MapListBlock, None)
        def test_none(self):
            self.assertRaises(TypeError, MapListBlock, (None,))
        def test_empty_list(self):
            self.assertRaises(TypeError, MapListBlock, ([],))
        def test_bad_list(self):
            self.assertRaises(TypeError, MapListBlock, ([None],))
            self.assertRaises(TypeError, MapListBlock, ([0],))
            self.assertRaises(TypeError, MapListBlock, ([0,1],))
        def test_minimal(self):
            self.assertEqual(0, len(MapListBlock([0,0])))
            self.assertEqual('MapListBlock[]', repr(MapListBlock([0,0])))
            self.assertEqual(0, len(MapListBlock(['0','3'])))
            self.assertEqual(1, len(MapListBlock(['1', '3', 'test','mode', '2'])))
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
    unittest.main()
