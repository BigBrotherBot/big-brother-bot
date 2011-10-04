#
# Battlefield 3 Parser for BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2010 Thomas LEVEIL <courgette@bigbrotherbot.net>
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
# 
#
__author__  = 'Courgette'
__version__ = '0.0'

import time
import b3.events
from b3.parsers.frostbite2.abstractParser import AbstractParser
from b3.parsers.frostbite2.util import PlayerInfoBlock
import b3.functions

SAY_LINE_MAX_LENGTH = 100


class Bf3Parser(AbstractParser):
    gameName = 'bf3'
    
    _gameServerVars = (
        '3dSpotting',
        '3pCam',
        'autoBalance',
        'bannerUrl',
        'bulletDamage',
        'clientSideDamageArbitration',
        'friendlyFire',
        'gameModeCounter',
        'gamePassword',
        'hud',
        'killCam',
        'killRotation',
        'maxPlayerCount',
        'minimap',
        'minimapSpotting',
        'nameTag',
        'noInteractivityRoundBan',
        'noInteractivityThresholdLimit',
        'noInteractivityTimeoutTime',
        'onlySquadLeaderSpawn',
        'playerManDownTime',
        'playerRespawnTime',
        'regenerateHealth',
        'roundRestartPlayerCount',
        'roundStartPlayerCount',
        'roundsPerMap',
        'serverDescription',
        'serverMessage',
        'serverName',
        'soldierHealth',
        'teamKillCountForKick',
        'teamKillKickForBan',
        'teamKillValueDecreasePerSecond',
        'teamKillValueForKick',
        'teamKillValueIncrease',
        'vehicleSpawnAllowed',
        'vehicleSpawnDelay',
    )
    
    def startup(self):
        AbstractParser.startup(self)
        
        # create the 'Server' client
        self.clients.newClient('Server', guid='Server', name='Server', hide=True, pbid='Server', team=b3.TEAM_UNKNOWN, squad=None)

        if self.config.has_option('bf3', 'max_say_line_length'):
            try:
                maxlength = self.config.getint('bf3', 'max_say_line_length')
                if maxlength > SAY_LINE_MAX_LENGTH:
                    self.warning('max_say_line_length cannot be greater than %s' % SAY_LINE_MAX_LENGTH)
                    maxlength = SAY_LINE_MAX_LENGTH
                if maxlength < 20:
                    self.warning('max_say_line_length is way too short. using default')
                    maxlength = self._settings['line_length']
                self._settings['line_length'] = maxlength
                self._settings['min_wrap_length'] = maxlength
            except Exception, err:
                self.error('failed to read max_say_line_length setting "%s" : %s' % (self.config.get('bf3', 'max_say_line_length'), err))
        self.debug('line_length: %s' % self._settings['line_length'])
            
            
        self.verbose('GameType: %s, Map: %s' %(self.game.gameType, self.game.mapName))
        

    def pluginsStarted(self):
        self.info('connecting all players...')
        plist = self.getPlayerList()
        for cid, p in plist.iteritems():
            client = self.clients.getByCID(cid)
            if not client:
                #self.clients.newClient(playerdata['cid'], guid=playerdata['guid'], name=playerdata['name'], team=playerdata['team'], squad=playerdata['squad'])
                name = p['name']
                self.debug('client %s found on the server' % cid)
                client = self.clients.newClient(cid, guid=p['name'], name=name, team=p['teamId'], squad=p['squadId'], data=p)
                self.queueEvent(b3.events.Event(b3.events.EVT_CLIENT_JOIN, p, client))
                



    ###############################################################################################
    #
    #    Frostbite2 events handlers
    #    
    ###############################################################################################

    def OnPlayerSwitchteam(self, action, data):
        """
        player.switchTeam <soldier name: player name> <team: Team ID> <squad: Squad ID>
        Effect: Player might have changed team
        """
        # ['player.switchTeam', 'Cucurbitaceae', '1', '0']
        client = self.getClient(data[0])
        if client:
            client.team = self.getTeam(data[1]) # .team setter will send team change event
            client.teamId = int(data[1])
            client.squad = int(data[2])
            
            
    def TODOOnPlayerSquadchange(self, action, data):
        """
        player.onSquadChange <soldier name: player name> <team: Team ID> <squad: Squad ID>    
        
        Effect: Player might have changed squad
        """
        client = self.getClient(data[0])
        if client:
            client.team = self.getTeam(data[1]) # .team setter will send team change event
            client.teamId = int(data[1])
            if client.squad != data[2]:
                client.squad = int(data[2])
                return b3.events.Event(b3.events.EVT_CLIENT_SQUAD_CHANGE, data[1:], client)


    ###############################################################################################
    #
    #    B3 Parser interface implementation
    #    
    ###############################################################################################



    ###############################################################################################
    #
    #    Other methods
    #    
    ###############################################################################################


    def checkVersion(self):
        version = self.output.write('version')
        self.info('server version : %s' % version)
        if version[0] != 'BF3':
            raise Exception("the bf3 parser can only work with Battlefield 3")

    def getClient(self, cid, _guid=None):
        """Get a connected client from storage or create it
        B3 CID   <--> character name
        B3 GUID  <--> character name (hoping for EA_guid)
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
            if p['name']: # TODO : change this back to 'if p['guid']:' once we have proper guid
                guid = p['name']
            elif _guid:
                guid = _guid
            else:
                # If we still don't have a guid, we cannot create a newclient without the guid!
                self.debug('No guid for %s, waiting for next event.' %name)
                return None

            if 'clanTag' in p and len(p['clanTag']) > 0:
                name = "[" + p['clanTag'] + "] " + p['name']
            client = self.clients.newClient(cid, guid=name, name=name, team=self.getTeam(p['teamId']), teamId=int(p['teamId']), data=p)
            self.queueEvent(b3.events.Event(b3.events.EVT_CLIENT_JOIN, p, client))
        
        return client

    def getHardName(self, mapname):
        """ Change real name to level name """
        mapname = mapname.lower()
        if mapname.startswith('subway'):
            return 'Levels/MP_Subway/MP_Subway'
        else:
            self.warning('unknown level name \'%s\'. Please make sure you have entered a valid mapname' % mapname)
            return mapname

    def getEasyName(self, mapname):
        """ Change levelname to real name """
        if mapname.lower().startswith('levels/mp_subway/'):
            return 'Subway'
        else:
            self.warning('unknown level name \'%s\'. Please report this on B3 forums' % mapname)
            return mapname

    def getServerVars(self):
        """Update the game property from server fresh data"""
        def getCvar(cvar):
            try:
                return self.getCvar(cvar).getString()
            except:
                pass
        def getCvarBool(cvar):
            try:
                return self.getCvar(cvar).getBoolean()
            except:
                pass
        def getCvarInt(cvar):
            try:
                return self.getCvar(cvar).getInt()
            except:
                pass
        def getCvarFloat(cvar):
            try:
                return self.getCvar(cvar).getFloat()
            except:
                pass
        self.game['3dSpotting'] = getCvarBool('3dSpotting')
        self.game['3pCam'] = getCvarBool('3pCam')
        self.game['autoBalance'] = getCvarBool('autoBalance')
        self.game['bannerUrl'] = getCvar('bannerUrl')
        self.game['bulletDamage'] = getCvarInt('bulletDamage')
        self.game['clientSideDamageArbitration'] = getCvarBool('clientSideDamageArbitration')
        self.game['friendlyFire'] = getCvarBool('friendlyFire')
        self.game['gameModeCounter'] = getCvarInt('gameModeCounter')
        self.game['hud'] = getCvarBool('hud')
        self.game['killCam'] = getCvarBool('killCam')
        self.game['killRotation'] = getCvarBool('killRotation')
        self.game['maxPlayerCount'] = getCvarInt('maxPlayerCount')
        self.game['minimap'] = getCvarBool('minimap')
        self.game['minimapSpotting'] = getCvarBool('minimapSpotting')
        self.game['nameTag'] = getCvarBool('nameTag')
        self.game['noInteractivityRoundBan'] = getCvar('noInteractivityRoundBan') # TODO: check cvar type
        self.game['noInteractivityThresholdLimit'] = getCvarFloat('noInteractivityThresholdLimit')
        self.game['noInteractivityTimeoutTime'] = getCvar('noInteractivityTimeoutTime') # TODO: check cvar type
        self.game['onlySquadLeaderSpawn'] = getCvar('onlySquadLeaderSpawn') # TODO: wtf responds 100 ?!?
        self.game['playerManDownTime'] = getCvar('playerManDownTime') # TODO: wtf responds 100 ?!?
        self.game['playerRespawnTime'] = getCvar('playerRespawnTime') # TODO: wtf responds 100 ?!?
        self.game['regenerateHealth'] = getCvarBool('regenerateHealth')
        self.game['roundRestartPlayerCount'] = getCvarInt('roundRestartPlayerCount')
        self.game['roundStartPlayerCount'] = getCvarInt('roundStartPlayerCount')
        self.game['roundsPerMap'] = getCvarInt('roundsPerMap')
        self.game['serverDescription'] = getCvar('serverDescription')
        self.game['serverMessage'] = getCvar('serverMessage')
        self.game['soldierHealth'] = getCvarInt('soldierHealth')
        self.game['teamKillCountForKick'] = getCvarInt('teamKillCountForKick')
        self.game['teamKillKickForBan'] = getCvarInt('teamKillKickForBan') # TODO: check cvar type
        self.game['teamKillValueDecreasePerSecond'] = getCvarFloat('teamKillValueDecreasePerSecond')
        self.game['teamKillValueForKick'] = getCvarFloat('teamKillValueForKick')
        self.game['teamKillValueIncrease'] = getCvarFloat('teamKillValueIncrease')
        self.game['vehicleSpawnAllowed'] = getCvarBool('vehicleSpawnAllowed')
        self.game['vehicleSpawnDelay'] = getCvar('vehicleSpawnDelay') # TODO: check cvar type
        self.game.timeLimit = self.game.gameModeCounter
        self.game.fragLimit = self.game.gameModeCounter
        self.game.captureLimit = self.game.gameModeCounter
        
    
    def getServerInfo(self):
        """query server info, update self.game and return query results
        Response: OK <serverName: string> <current playercount: integer> <max playercount: integer> 
        <current map: string> <current gamemode: string> <roundsPlayed: integer> 
        <roundsTotal: string> <?: boolean> <?: boolean> <?: boolean> <?: integer> <?: integer>
        """
        # TODO : complete getServerInfo
        data = self.write(('serverInfo',))
        self.game.sv_hostname = data[0]
        self.game.sv_maxclients = int(data[2])
        self.game.mapName = data[3]
        self.game.gameType = data[4]
        self.game.rounds = int(data[5])
        self.game.g_maxrounds = int(data[6])
        return data

    def getTeam(self, team):
        """convert BFBC2 team numbers to B3 team numbers"""
        # FIXME: guessed team numbers. Need to check with Frostbite2 protocol documents
        team = int(team)
        if team == 1:
            return b3.TEAM_RED
        elif team == 2:
            return b3.TEAM_BLUE
        elif team == 3:
            return b3.TEAM_SPEC
        else:
            return b3.TEAM_UNKNOWN
