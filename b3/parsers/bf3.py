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
from b3.parsers.frostbite.abstractParser import AbstractParser
from b3.parsers.frostbite.util import PlayerInfoBlock
import b3.functions

SAY_LINE_MAX_LENGTH = 100

class Bf3Parser(AbstractParser):
    gameName = 'bf3'
    
    _gameServerVars = (
        'serverName', # vars.serverName [name] Set the server name 
        'gamePassword', # vars.gamePassword [password] Set the game password for the server 
        #'punkBuster', # vars.punkBuster [enabled] Set if the server will use PunkBuster or not 
        #'hardCore', # vars.hardCore [enabled] Set hardcore mode 
        #'ranked', # vars.ranked [enabled] Set ranked or not 
        #'skillLimit', # vars.skillLimit [lower, upper] Set the skill limits allowed on to the server 
        #'noUnlocks', # vars.noUnlocks [enabled] Set if unlocks should be disabled 
        #'noAmmoPickups', # vars.noAmmoPickups [enabled] Set if pickups should be disabled 
        #'realisticHealth', # vars.realisticHealth [enabled] Set if health should be realistic 
        #'supportAction', # vars.supportAction [enabled] Set if support action should be enabled 
        #'preRoundLimit', # vars.preRoundLimit [upper, lower] Set pre round limits. Setting both to zero means the game uses whatever settings are used on the specific levels. On ranked servers, the lowest values allowed are lower = 2 and upper = 4.
        #'roundStartTimerPlayersLimit', # vars.roundStartTimerPlayersLimit [limit] Get/Set the number of players that need to spawn on each team for the round start timer to start counting down.
        #'roundStartTimerDelay', # vars.roundStartTimerDelay [delay] If set to other than -1, this value overrides the round start delay set on the individual levels.
        #'tdmScoreCounterMaxScore', # vars.tdmScoreCounterMaxScore [score] If set to other than -1, this value overrides the score needed to win a round of Team Assault, Sector Control or Hot Zone. 
        #'clanTeams', # vars.clanTeams [enabled] Set if clan teams should be used 
        'friendlyFire', # vars.friendlyFire [enabled] Set if the server should allow team damage 
        #'currentPlayerLimit', # vars.currentPlayerLimit Retrieve the current maximum number of players 
        #'maxPlayerLimit', # vars.maxPlayerLimit Retrieve the server-enforced maximum number of players 
        #'playerLimit', # vars.playerLimit [nr of players] Set desired maximum number of players 
        #'bannerUrl', # vars.bannerUrl [url] Set banner url 
        'serverDescription', # vars.serverDescription [description] Set server description 
        #'noCrosshair', # vars.noCrosshair [enabled] Set if crosshairs for all weapons is hidden
        #'noSpotting', # vars.noSpotting [enabled] Set if spotted targets are disabled in the 3d-world 
        'teamKillCountForKick', # vars.teamKillCountForKick [count] Set number of teamkills allowed during a round 
        'teamKillValueForKick', # vars.teamKillValueForKick [count] Set max kill-value allowed for a player before he/she is kicked 
        'teamKillValueIncrease', # vars.teamKillValueIncrease [count] Set kill-value increase for a teamkill 
        'teamKillValueDecreasePerSecond', # vars.teamKillValueDecreasePerSecond [count] Set kill-value decrease per second
        #'idleTimeout', # vars.idleTimeout [time] Set idle timeout vars.profanityFilter [enabled] Set if profanity filter is enabled
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
                client = self.clients.newClient(cid, guid=p['guid'], name=name, team=p['teamId'], squad=p['squadId'], data=p)
                self.queueEvent(b3.events.Event(b3.events.EVT_CLIENT_JOIN, p, client))
                
        
        
    def checkVersion(self):
        version = self.output.write('version')
        self.info('server version : %s' % version)
        if version[0] != 'BF':
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
        try: self.game.serverName = self.getCvar('serverName').getBoolean()
        except: pass
        try: self.game.gamePassword = self.getCvar('gamePassword').getBoolean()
        except: pass
#        try: self.game.punkBuster = self.getCvar('punkBuster').getBoolean()
#        except: pass
#        try: self.game.hardCore = self.getCvar('hardCore').getBoolean()
#        except: pass
#        try: self.game.ranked = self.getCvar('ranked').getBoolean()
#        except: pass
#        try: self.game.skillLimit = self.getCvar('skillLimit').getBoolean()
#        except: pass
#        try: self.game.noUnlocks = self.getCvar('noUnlocks').getBoolean()
#        except: pass
#        try: self.game.noAmmoPickups = self.getCvar('noAmmoPickups').getBoolean()
#        except: pass
#        try: self.game.realisticHealth = self.getCvar('realisticHealth').getBoolean()
#        except: pass
#        try: self.game.supportAction = self.getCvar('supportAction').getBoolean()
#        except: pass
#        try: self.game.preRoundLimit = self.getCvar('preRoundLimit').getBoolean()
#        except: pass
#        try: self.game.roundStartTimerPlayersLimit = self.getCvar('roundStartTimerPlayersLimit').getBoolean()
#        except: pass
#        try: self.game.roundStartTimerDelay = self.getCvar('roundStartTimerDelay').getBoolean()
#        except: pass
#        try: self.game.tdmScoreCounterMaxScore = self.getCvar('tdmScoreCounterMaxScore').getBoolean()
#        except: pass
#        try: self.game.clanTeams = self.getCvar('clanTeams').getBoolean()
#        except: pass
        try: self.game.friendlyFire = self.getCvar('friendlyFire').getBoolean()
        except: pass
#        try: self.game.currentPlayerLimit = self.getCvar('currentPlayerLimit').getBoolean()
#        except: pass
#        try: self.game.maxPlayerLimit = self.getCvar('maxPlayerLimit').getBoolean()
#        except: pass
#        try: self.game.playerLimit = self.getCvar('playerLimit').getBoolean()
#        except: pass
#        try: self.game.bannerUrl = self.getCvar('bannerUrl').getBoolean()
#        except: pass
        try: self.game.serverDescription = self.getCvar('serverDescription').getBoolean()
        except: pass
#        try: self.game.noCrosshair = self.getCvar('noCrosshair').getBoolean()
#        except: pass
#        try: self.game.noSpotting = self.getCvar('noSpotting').getBoolean()
#        except: pass
        try: self.game.teamKillCountForKick = self.getCvar('teamKillCountForKick').getBoolean()
        except: pass
        try: self.game.teamKillValueForKick = self.getCvar('teamKillValueForKick').getBoolean()
        except: pass
        try: self.game.teamKillValueIncrease = self.getCvar('teamKillValueIncrease').getBoolean()
        except: pass
        try: self.game.teamKillValueDecreasePerSecond = self.getCvar('teamKillValueDecreasePerSecond').getBoolean()
        except: pass
#        try: self.game.idleTimeout = self.getCvar('idleTimeout').getBoolean()
#        except: pass
        
    
    def getServerInfo(self):
        """query server info, update self.game and return query results
        Response: OK <serverName: string> <current playercount: integer> <current map: string> <private: bool> <uptime: integer>
        """
        data = self.write(('serverInfo',))
        self.game.sv_hostname = data[0]
        self.game.mapName = data[2]
        self.game.private = data[3] == "true"
        self.game.uptime = int(data[4])
        return data

