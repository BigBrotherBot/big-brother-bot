#
# Medal of Honor Parser for BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2010 James 'Bakes' Baker (bakes@bigbrotherbot.net)
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
#
# CHANGELOG
# 2010/10/10 - 0.3 - Bakes
# * getEasyName is now implemented and working, getHardName is implemented
#   but not working.
# 2010/10/07 - 0.2 - Courgette
# * add gameName property. Fix SAY_LINE_MAX_LENGTH
# 2010/09/25 - 0.1 - Bakes
# * Initial version of MoH parser - hasn't been tested with OnKill events yet
#   but basic commands seem to work.
# 

__author__  = 'Bakes'
__version__ = '0.2'

import b3.parsers.bfbc2
import sys, time, re, string, traceback
import b3
import b3.events
import b3.parser
from b3.parsers.frostbite.punkbuster import PunkBuster as Bfbc2PunkBuster
import threading
import Queue
import b3.parsers.frostbite.rcon as rcon
import b3.cvar
from b3.functions import soundex, levenshteinDistance
from b3.parsers.frostbite.bfbc2Connection import *

SAY_LINE_MAX_LENGTH = 100

class MohParser(b3.parsers.bfbc2.Bfbc2Parser):
    gameName = 'moh'
    def startup(self):
        
        # add specific events
        self.Events.createEvent('EVT_CLIENT_SQUAD_CHANGE', 'Client Squad Change')
        self.Events.createEvent('EVT_PUNKBUSTER_SCHEDULED_TASK', 'PunkBuster scheduled task')
        self.Events.createEvent('EVT_PUNKBUSTER_LOST_PLAYER', 'PunkBuster client connection lost')
        self.Events.createEvent('EVT_PUNKBUSTER_NEW_CONNECTION', 'PunkBuster client received IP')
        self.Events.createEvent('EVT_CLIENT_SPAWN', 'Client Spawn')
                
        # create the 'Server' client
        self.clients.newClient('Server', guid='Server', name='Server', hide=True, pbid='Server', team=b3.TEAM_UNKNOWN)
        
        if self.config.has_option('server', 'punkbuster') and self.config.getboolean('server', 'punkbuster'):
            self.info('kick/ban by punkbuster is unsupported yet')
            #self.debug('punkbuster enabled in config')
            #self.PunkBuster = Bfbc2PunkBuster(self)
        
        
        if self.config.has_option('moh', 'max_say_line_length'):
            try:
                maxlength = self.config.getint('moh', 'max_say_line_length')
                if maxlength > SAY_LINE_MAX_LENGTH:
                    self.warning('max_say_line_length cannot be greater than %s' % SAY_LINE_MAX_LENGTH)
                    maxlength = SAY_LINE_MAX_LENGTH
                if maxlength < 20:
                    self.warning('max_say_line_length is way too short. using default')
                    maxlength = self._settings['line_length']
                self._settings['line_length'] = maxlength
                self._settings['min_wrap_length'] = maxlength
            except Exception, err:
                self.error('failed to read max_say_line_length setting "%s" : %s' % (self.config.get('moh', 'max_say_line_length'), err))
        self.debug('line_length: %s' % self._settings['line_length'])
            
        version = self.output.write('version')
        self.info('MoH server version : %s' % version)
        if version[0] != 'MOH':
            raise Exception("the moh parser can only work with Medal of Honor")
        
        self.getServerVars()
        self.getServerInfo()
        self.verbose('GameType: %s, Map: %s' %(self.game.gameType, self.game.mapName))
        
        self.info('connecting all players...')
        plist = self.getPlayerList()
        for cid, p in plist.iteritems():
            client = self.clients.getByCID(cid)
            if not client:
                #self.clients.newClient(playerdata['cid'], guid=playerdata['guid'], name=playerdata['name'], team=playerdata['team'], squad=playerdata['squad'])
                name = p['name']
                if 'clanTag' in p and len(p['clanTag']) > 0:
                    name = "[" + p['clanTag'] + "] " + p['name']
                self.debug('client %s found on the server' % cid)
                client = self.clients.newClient(cid, guid=p['guid'], name=name, team=p['teamId'], data=p)
                self.queueEvent(b3.events.Event(b3.events.EVT_CLIENT_JOIN, p, client))
                
        
        self.sayqueuelistener = threading.Thread(target=self.sayqueuelistener)
        self.sayqueuelistener.setDaemon(True)
        self.sayqueuelistener.start()
        
        self.saybigqueuelistener = threading.Thread(target=self.saybigqueuelistener)
        self.saybigqueuelistener.setDaemon(True)
        self.saybigqueuelistener.start()

    def getClient(self, cid, _guid=None):
        """Get a connected client from storage or create it
        B3 CID   <--> MoH character name
        B3 GUID  <--> MoH EA_guid
        """
        
        # try to get the client from the storage of already authed clients
        client = self.clients.getByCID(cid)
        if not client:
            if cid == 'Server':
                return self.clients.newClient('Server', guid='Server', name='Server', hide=True, pbid='Server', team=b3.TEAM_UNKNOWN)
            # must be the first time we see this client
            words = self.write(('admin.listPlayers', 'player', cid))
            pib = PlayerInfoBlock(words)
            if len(pib) == 0:
                self.debug('no such client found')
                return None
            p = pib[0]
            cid = p['name']
            name = p['name']

            # Let's see if we have a guid, either from the PlayerInfoBlock, or passed to us by OnPlayerAuthenticated()
            if p['guid']:
                guid = p['guid']
            elif _guid:
                guid = _guid
            else:
                # If we still don't have a guid, we cannot create a newclient without the guid!
                self.debug('No guid for %s, waiting for next event.' %name)
                return None

            if 'clanTag' in p and len(p['clanTag']) > 0:
                name = "[" + p['clanTag'] + "] " + p['name']
            client = self.clients.newClient(cid, guid=guid, name=name, team=self.getTeam(p['teamId']), teamId=int(p['teamId']), data=p)
            self.queueEvent(b3.events.Event(b3.events.EVT_CLIENT_JOIN, p, client))
        
        return client
    def rotateMap(self):
        """Load the next map (not level). If the current game mod plays each level twice
        to get teams the chance to play both sides, then this rotate a second
        time to really switch to the next map"""
        #nextIndex = self.getNextMapIndex()
        self.write(('admin.runNextRound',))

    def getMap(self):
        """Return the current level name (not easy map name)"""
        data = self.write(('serverInfo',))
        if not data:
            return None
        return data[4]
		
		
    def getHardName(self, mapname):
        """ Change real name to level name """
        mapname = mapname.lower()
        if mapname.startswith('mazar-i-sharif airfield'):
            return 'levels/mp_01'
            
        elif mapname.startswith('shah-i-knot mountains'):
            return 'levels/mp_02'

        elif mapname.startswith('helmand valley'):
            return 'levels/mp_04'

        elif mapname.startswith('kandahar marketplace'):
            return 'levels/mp_05'

        elif mapname.startswith('diwagal camp'):
            return 'levels/mp_06'

        elif mapname.startswith('kunar base'):
            return 'levels/mp_08'

        elif mapname.startswith('kabul city ruins'):
            return 'levels/mp_09'

        elif mapname.startswith('garmzir town'):
            return 'levels/mp_10'
			
        else:
            self.warning('unknown level name \'%s\'. Please make sure you have entered a valid mapname' % mapname)
            return mapname
			
    def getEasyName(self, mapname):
        """ Change levelname to real name """
        if mapname.startswith('levels/mp_01'):
            return 'Mazar-i-Sharif Airfield'
            
        elif mapname.startswith('levels/mp_02'):
            return 'Shah-i-Knot Mountains'

        elif mapname.startswith('levels/mp_04'):
            return 'Helmand Valley'

        elif mapname.startswith('levels/mp_05'):
            return 'Kandahar Marketplace'

        elif mapname.startswith('levels/mp_06'):
            return 'Diwagal Camp'

        elif mapname.startswith('levels/mp_08'):
            return 'Kunar Base'

        elif mapname.startswith('levels/mp_09'):
            return 'Kabul City Ruins'

        elif mapname.startswith('levels/mp_10'):
            return 'Garmzir Town'
        
        else:
            self.warning('unknown level name \'%s\'. Please report this on B3 forums' % mapname)
            return mapname

class PlayerInfoBlock:
    """
    help extract player info from a MoH Player Info Block which we obtain
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
        """Represent a MoH Player info block
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