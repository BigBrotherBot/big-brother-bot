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
# 1.2 - 2012/01/21 - Courgette
#    * add a append() method to BanlistContent and MapListBlock classes
#

"""\
This module provides different utilities specific to the Frostbite engine
"""

__author__  = 'Courgette'
__version__ = '1.2'


class BanlistContentError(Exception):
    pass

class BanlistContent(object):
    """
    help extract banlist info from a frostbite banList.list response
    
    usage :
        words = [
            'name', 'Courgette', 'perm',         , 'test',
            'name', 'Courgette', 'seconds', 3600 , 'test2'] 
        bansInfo = BanlistContent(words)
        print "num of bans : %s" % len(bansInfo)
        print "first ban : %s" % bansInfo[0]
        print "second ban : %s" % bansInfo[1]
        print "the first 2 bans : %s" % bansInfo[0:2]
        for b in bansInfo:
            print b
    """

    def __init__(self, data=None):
        """Represent a frostbite banList.list response
        Request: banList.list 
        Response: OK <player ban entries> 
        Response: InvalidArguments 
        Effect: Return list of banned players/IPs/GUIDs. 
        Comment: 6 words (Id-type, id, ban-type, seconds left, rounds left, and reason) are received for every ban in
        the list.
        If no startOffset is supplied, it is assumed to be 0.
        At most 100 entries will be returned by the command. To retrieve the full list, perform several banList.list
        calls with increasing offset until the server returns 0 entries.
        (There is an unsolved synchronization problem hidden there: if a ban expires during this process, then one other
        entry will be skipped during retrieval. There is no known workaround for this.)
        """
        self.numOfBans = 0
        self.bansData = []
        if data is not None:
            self.append(data)


    def append(self, data):
        """Parses and appends the maps from raw_data.
        data : words as received from the Frostbite2 mapList.list command
        """
        # validation
        if type(data) not in (tuple, list):
            raise BanlistContentError("invalid data. Expecting data as a tuple or as a list. Received '%s' instead" % type(data))

        if len(data) == 0:
            # banList.list returns nothing when the banlist contains no ban.
            return

        if len(data) % 6 != 0:
            raise BanlistContentError("invalid data. The total number of elements is not divisible by 6 (%s)" % len(data))

        # append data
        self.bansData += data
        self.numOfBans += len(data) / 6


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
        tmp = self.bansData[index*6:(index+1)*6]
        return {
            'idType': tmp[0], # name | ip | guid
            'id': tmp[1],
            'banType': tmp[2], # perm | round | seconds
            'seconds_left': tmp[3],
            'rounds_left': tmp[4],
            'reason': tmp[5], # 80 chars max
        }

    def __repr__(self):
        return "BanlistContent[%s]" % ', '.join([repr(x) for x in self])



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


class MapListBlockError(Exception):
    pass

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

    def __init__(self, data=None):
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
        self._num_maps = 0
        self._num_words = None
        self._map_data = tuple()
        if data is not None:
            self.append(data)

    def append(self, data):
        """Parses and appends the maps from raw_data.
        data : words as received from the Frostbite2 mapList.list command
        """
        # validation
        if type(data) not in (tuple, list):
            raise MapListBlockError("invalid data. Expecting data as a tuple or as a list. Received '%s' instead" % type(data))

        if len(data) < 2:
            raise MapListBlockError("invalid data. Data should have at least 2 elements. %r", data)

        try:
            num_maps = int(data[0])
        except ValueError, err:
            raise MapListBlockError("invalid data. First element should be a integer, got %r" % data[0], err)

        try:
            num_words = int(data[1])
        except ValueError, err:
            raise MapListBlockError("invalid data. Second element should be a integer, got %r" % data[1], err)

        if len(data) != (2 + (num_maps * num_words)):
            raise MapListBlockError("invalid data. The total number of elements is not coherent with the number of maps declared. %s != (2 + %s * %s)" % (len(data), num_maps, num_words))

        if num_words < 3:
            raise MapListBlockError("invalid data. Expecting at least 3 words of data per map")

        if self._num_words is not None and self._num_words != num_words:
            raise MapListBlockError("cannot append data. nums_words are different from existing data.")

        # parse data
        map_data = []
        for i in range(num_maps):
            base_index = 2 + (i * num_words)
            try:
                num_rounds = int(data[base_index+2])
            except ValueError:
                raise MapListBlockError("invalid data. %sth element should be a integer, got %r" % (base_index + 2, data[base_index + 2]))
            map_data.append({'name': data[base_index+0], 'gamemode': data[base_index+1], 'num_of_rounds': num_rounds})

        # append data
        self._map_data += tuple(map_data)
        self._num_maps = len(self._map_data)
        if self._num_words is None:
            self._num_words = num_words

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
