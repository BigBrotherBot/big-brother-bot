#
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
    numOfBans = None
    bansData = []
    
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
        words = [3, 'name', 'guid', 'ping', 2, 
            'Courgette', 'A32132e', 130, 
            'SpacepiG', '6546545665465', 120,
            'Bakes', '6ae54ae54ae5', 50]
        playersInfo = PlayerInfoBlock(words)
        print "num of players : %s" % len(playersInfo)
        print "first player : %s" % playersInfo[0]
        print "second player : %s" % playersInfo[1]
        print "the first 2 players : %s" % playersInfo[0:2]
        for p in playersInfo:
            print p
    """
    playersData = []
    numOfParameters= 0
    numOfPlayers = 0
    parameterTypes = []
    
    def __init__(self, data):
        """Represent a frostbite Player info block
        The standard set of info for a group of players contains a lot of different 
        fields. To reduce the risk of having to do backwards-incompatible changes to
        the protocol, the player info block includes some formatting information.
            
        <number of parameters>       - number of parameters for each player 
        N x <parameter type: string> - the parameter types that will be sent below 
        <number of players>          - number of players following 
        M x N x <parameter value>    - all parameter values for player 0, then all 
                                    parameter values for player 1, etc
                                    
        Current parameters:
          name     string     - player name 
          guid     GUID       - player GUID, or '' if GUID is not yet known 
          teamId   Team ID    - player's current team 
          squadId  Squad ID   - player's current squad 
          kills    integer    - number of kills, as shown in the in-game scoreboard
          deaths   integer    - number of deaths, as shown in the in-game scoreboard
          score    integer    - score, as shown in the in-game scoreboard 
          ping     integer    - ping (ms), as shown in the in-game scoreboard
        """
        self.numOfParameters = int(data[0])
        self.parameterTypes = data[1:1+self.numOfParameters]
        self.numOfPlayers = int(data[1+self.numOfParameters])
        self.playersData = data[1+self.numOfParameters+1:]
    
    def __len__(self):
        return self.numOfPlayers
    
    def __getitem__(self, key):
        """Returns the player data, for provided key (int or slice)"""
        if isinstance(key, slice):
            indices = key.indices(len(self))
            return [self.getPlayerData(i) for i in range(*indices) ]
        else:
            return self.getPlayerData(key)

    def getPlayerData(self, index):
        if index >= self.numOfPlayers:
            raise IndexError
        data = {}
        playerData = self.playersData[index*self.numOfParameters:(index+1)*self.numOfParameters]
        for i in range(self.numOfParameters):
            data[self.parameterTypes[i]] = playerData[i]
        return data 

    def __repr__(self):
        txt = "PlayerInfoBlock["
        for p in self:
            txt += "%r" % p
        txt += "]"
        return txt
    
