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
# 2010/11/07 - 0.10 - Courgette
# * add new maps info
# 2010/11/08 - 0.9.2 - GrosBedo
# * messages can now be empty (no message broadcasted on kick/tempban/ban/unban)
# 2010/10/27 - 0.9.1 - GrosBedo
# * messages now support named $variables instead of %s
# 2010/10/27 - 0.9 - Courgette
# * when banning, also kick to take over MoH engine failure to enforce bans. This
#   will need more test to determine how to make the MoH engine enforce temp bans.
# 2010/10/24 - 0.8 - Courgette
# * fix OnServerRoundover and OnServerRoundoverplayers
# 2010/10/24 - 0.7 - Courgette
# * add missing getTeam() method
# 2010/10/24 - 0.6 - Courgette
# * minor fixes
# 2010/10/23 - 0.5 - Courgette
# * create specific events : EVT_GAME_ROUND_PLAYER_SCORES and EVT_GAME_ROUND_TEAM_SCORES
# * now fires native B3 event EVT_GAME_ROUND_END
# * manage team changed event correctly
# 2010/10/23 - 0.4 - Courgette
# * refactor inheriting from frostbite AbstratParser 
# * change available server var list
# 2010/10/10 - 0.3 - Bakes
# * getEasyName is now implemented and working, getHardName is implemented
#   but not working.
# 2010/10/07 - 0.2 - Courgette
# * add gameName property. Fix SAY_LINE_MAX_LENGTH
# 2010/09/25 - 0.1 - Bakes
# * Initial version of MoH parser - hasn't been tested with OnKill events yet
#   but basic commands seem to work.
# 2010-11-21 - 1.0 - Courgette
# * add rotateMap and changeMap to fix !maprotate and !map#
# 2011-02-01 - 1.1 - xlr8or
# * adapted to server R9 version 615937 - fixed onPlayerSpawn and vars.noCrosshairs errors
# 2011-03-05 - 1.2 - xlr8or
# * admin.kickPlayer after ban now in try/except to avoid error msg when player is already gone
# 2011-04-09 - 1.2.1 - Courgette
# * import missing time module
#

__author__  = 'Bakes, Courgette'
__version__ = '1.2.1'

import time
import b3.events
from b3.parsers.frostbite.abstractParser import AbstractParser
from b3.parsers.frostbite.util import PlayerInfoBlock
import b3.functions

SAY_LINE_MAX_LENGTH = 100

class MohParser(AbstractParser):
    gameName = 'moh'
    
    _gameServerVars = (
        'serverName', # vars.serverName [name] Set the server name 
        'gamePassword', # vars.gamePassword [password] Set the game password for the server 
        'punkBuster', # vars.punkBuster [enabled] Set if the server will use PunkBuster or not 
        'hardCore', # vars.hardCore[enabled] Set hardcore mode 
        'ranked', # vars.ranked [enabled] Set ranked or not 
        'skillLimit', # vars.skillLimit [lower, upper] Set the skill limits allowed on to the server 
        'noUnlocks', # vars.noUnlocks [enabled] Set if unlocks should be disabled 
        'noAmmoPickups', # vars.noAmmoPickups [enabled] Set if pickups should be disabled 
        'realisticHealth', # vars.realisticHealth [enabled] Set if health should be realistic 
        'supportAction', # vars.supportAction [enabled] Set if support action should be enabled 
        'preRoundLimit', # vars.preRoundLimit [upper, lower] Set pre round limits. Setting both to zero means the game uses whatever settings are used on the specific levels. On ranked servers, the lowest values allowed are lower = 2 and upper = 4.
        'roundStartTimerPlayersLimit', # vars.roundStartTimerPlayersLimit [limit] Get/Set the number of players that need to spawn on each team for the round start timer to start counting down.
        'roundStartTimerDelay', # vars.roundStartTimerDelay [delay] If set to other than -1, this value overrides the round start delay set on the individual levels.
        'tdmScoreCounterMaxScore', # vars.tdmScoreCounterMaxScore [score] If set to other than -1, this value overrides the score needed to win a round of Team Assault, Sector Control or Hot Zone. 
        'clanTeams', # vars.clanTeams [enabled] Set if clan teams should be used 
        'friendlyFire', # vars.friendlyFire [enabled] Set if the server should allow team damage 
        'currentPlayerLimit', # vars.currentPlayerLimit Retrieve the current maximum number of players 
        'maxPlayerLimit', # vars.maxPlayerLimit Retrieve the server-enforced maximum number of players 
        'playerLimit', # vars.playerLimit [nr of players] Set desired maximum number of players 
        'bannerUrl', # vars.bannerUrl [url] Set banner url 
        'serverDescription', # vars.serverDescription [description] Set server description 
        'noCrosshairs', # vars.noCrosshairs [enabled] Set if crosshairs for all weapons is hidden
        'noSpotting', # vars.noSpotting [enabled] Set if spotted targets are disabled in the 3d-world 
        'teamKillCountForKick', # vars.teamKillCountForKick [count] Set number of teamkills allowed during a round 
        'teamKillValueForKick', # vars.teamKillValueForKick [count] Set max kill-value allowed for a player before he/she is kicked 
        'teamKillValueIncrease', # vars.teamKillValueIncrease [count] Set kill-value increase for a teamkill 
        'teamKillValueDecreasePerSecond', # vars.teamKillValueDecreasePerSecond [count] Set kill-value decrease per second
        'idleTimeout', # vars.idleTimeout [time] Set idle timeout vars.profanityFilter [enabled] Set if profanity filter is enabled
    )
    
    def startup(self):
        AbstractParser.startup(self)
        
        self.Events.createEvent('EVT_GAME_ROUND_PLAYER_SCORES', 'round player scores')
        self.Events.createEvent('EVT_GAME_ROUND_TEAM_SCORES', 'round team scores')
        
        # create the 'Server' client
        self.clients.newClient('Server', guid='Server', name='Server', hide=True, pbid='Server', team=b3.TEAM_UNKNOWN)

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
                
        
        
    def checkVersion(self):
        version = self.output.write('version')
        self.info('server version : %s' % version)
        if version[0] != 'MOH':
            raise Exception("the moh parser can only work with Medal of Honor")

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

    def getHardName(self, mapname):
        """ Change real name to level name """
        mapname = mapname.lower()
        if mapname.startswith('mazar-i-sharif airfield'):
            return 'levels/mp_01'
        
        elif mapname.startswith('bagram hanger'):
            return 'levels/mp_01_elimination'
            
        elif mapname.startswith('shah-i-knot mountains'):
            return 'levels/mp_02'
        
        elif mapname.startswith('hindu kush pass'):
            return 'levels/mp_02_koth'
        
        elif mapname.startswith('khyber caves'):
            return 'levels/mp_03'
            #return 'levels/mp_03_elimination'

        elif mapname.startswith('helmand valley'):
            return 'levels/mp_04'
        
        elif mapname.startswith('helmand river hill'):
            return 'levels/mp_04_koth'

        elif mapname.startswith('kandahar marketplace'):
            return 'levels/mp_05'

        elif mapname.startswith('diwagal camp'):
            return 'levels/mp_06'
            #return 'mp_06_elimination'
        
        elif mapname.startswith('korengal outpost'):
            return 'levels/mp_07_koth'

        elif mapname.startswith('kunar base'):
            return 'levels/mp_08'

        elif mapname.startswith('kabul city ruins'):
            return 'levels/mp_09'
            #return 'levels/mp_09_elimination'

        elif mapname.startswith('garmzir town'):
            return 'levels/mp_10'

        else:
            self.warning('unknown level name \'%s\'. Please make sure you have entered a valid mapname' % mapname)
            return mapname

    def getEasyName(self, mapname):
        """ Change levelname to real name """
        if mapname.startswith('levels/mp_01_elimination'):
            return 'Bagram Hanger'
        
        elif mapname.startswith('levels/mp_01'):
            return 'Mazar-i-Sharif Airfield'
            
        elif mapname.startswith('levels/mp_02_koth'):
            return 'Hindu Kush Pass'
        
        elif mapname.startswith('levels/mp_02'):
            return 'Shah-i-Knot Mountains'

        elif mapname.startswith('levels/mp_03'):
            return 'Khyber Caves'

        elif mapname.startswith('levels/mp_04_koth'):
            return 'Helmand River Hill'

        elif mapname.startswith('levels/mp_04'):
            return 'Helmand Valley'

        elif mapname.startswith('levels/mp_05'):
            return 'Kandahar Marketplace'

        elif mapname.startswith('levels/mp_06'):
            return 'Diwagal Camp'

        elif mapname.startswith('levels/mp_07_koth'):
            return 'Korengal Outpost'

        elif mapname.startswith('levels/mp_08'):
            return 'Kunar Base'

        elif mapname.startswith('levels/mp_09'):
            return 'Kabul City Ruins'

        elif mapname.startswith('levels/mp_10'):
            return 'Garmzir Town'
        
        else:
            self.warning('unknown level name \'%s\'. Please report this on B3 forums' % mapname)
            return mapname

    def getServerVars(self):
        """Update the game property from server fresh data"""
        try: self.game.serverName = self.getCvar('serverName').getBoolean()
        except: pass
        try: self.game.gamePassword = self.getCvar('gamePassword').getBoolean()
        except: pass
        try: self.game.punkBuster = self.getCvar('punkBuster').getBoolean()
        except: pass
        try: self.game.hardCore = self.getCvar('hardCore').getBoolean()
        except: pass
        try: self.game.ranked = self.getCvar('ranked').getBoolean()
        except: pass
        try: self.game.skillLimit = self.getCvar('skillLimit').getBoolean()
        except: pass
        try: self.game.noUnlocks = self.getCvar('noUnlocks').getBoolean()
        except: pass
        try: self.game.noAmmoPickups = self.getCvar('noAmmoPickups').getBoolean()
        except: pass
        try: self.game.realisticHealth = self.getCvar('realisticHealth').getBoolean()
        except: pass
        try: self.game.supportAction = self.getCvar('supportAction').getBoolean()
        except: pass
        try: self.game.preRoundLimit = self.getCvar('preRoundLimit').getBoolean()
        except: pass
        try: self.game.roundStartTimerPlayersLimit = self.getCvar('roundStartTimerPlayersLimit').getBoolean()
        except: pass
        try: self.game.roundStartTimerDelay = self.getCvar('roundStartTimerDelay').getBoolean()
        except: pass
        try: self.game.tdmScoreCounterMaxScore = self.getCvar('tdmScoreCounterMaxScore').getBoolean()
        except: pass
        try: self.game.clanTeams = self.getCvar('clanTeams').getBoolean()
        except: pass
        try: self.game.friendlyFire = self.getCvar('friendlyFire').getBoolean()
        except: pass
        try: self.game.currentPlayerLimit = self.getCvar('currentPlayerLimit').getBoolean()
        except: pass
        try: self.game.maxPlayerLimit = self.getCvar('maxPlayerLimit').getBoolean()
        except: pass
        try: self.game.playerLimit = self.getCvar('playerLimit').getBoolean()
        except: pass
        try: self.game.bannerUrl = self.getCvar('bannerUrl').getBoolean()
        except: pass
        try: self.game.serverDescription = self.getCvar('serverDescription').getBoolean()
        except: pass
        try: self.game.noCrosshair = self.getCvar('noCrosshair').getBoolean()
        except: pass
        try: self.game.noSpotting = self.getCvar('noSpotting').getBoolean()
        except: pass
        try: self.game.teamKillCountForKick = self.getCvar('teamKillCountForKick').getBoolean()
        except: pass
        try: self.game.teamKillValueForKick = self.getCvar('teamKillValueForKick').getBoolean()
        except: pass
        try: self.game.teamKillValueIncrease = self.getCvar('teamKillValueIncrease').getBoolean()
        except: pass
        try: self.game.teamKillValueDecreasePerSecond = self.getCvar('teamKillValueDecreasePerSecond').getBoolean()
        except: pass
        try: self.game.idleTimeout = self.getCvar('idleTimeout').getBoolean()
        except: pass
        
        
    def getTeam(self, team):
        """convert MOH team numbers to B3 team numbers"""
        team = int(team)
        if team == 1:
            return b3.TEAM_RED
        elif team == 2:
            return b3.TEAM_BLUE
        elif team == 3:
            return b3.TEAM_SPEC
        else:
            return b3.TEAM_UNKNOWN
        
        
    def OnPlayerSpawn(self, action, data):
        """
        Request:  player.onSpawn <soldier name: string> <kit: string> <weapon: string> <specializations: 3 x string>
        """
        if len(data) < 2:
            return None

        spawner = self.getClient(data[0])
        kit = data[1]
        weapon = data[2]
        spec1 = data[3]
        spec2 = data[4]
        spec3 = data[5]

        event = b3.events.EVT_CLIENT_SPAWN
        return b3.events.Event(event, (kit, weapon, spec1, spec2, spec3), spawner)


    def OnPlayerTeamchange(self, action, data):
        """
        player.onTeamChange <soldier name: player name> <team: Team ID>
        Effect: Player might have changed team
        """
        #['player.onTeamChange', 'Dalich', '2']
        client = self.getClient(data[0])
        if client:
            client.team = self.getTeam(data[1]) # .team setter will send team change event
            client.teamId = int(data[1])
            
        
    def OnServerRoundover(self, action, data):
        """
        server.onRoundOver <winning team: Team ID>
        
        Effect: The round has just ended, and <winning team> won
        """
        #['server.onRoundOver', '2']
        return b3.events.Event(b3.events.EVT_GAME_ROUND_END, data[0])
        
        
    def OnServerRoundoverplayers(self, action, data):
        """
        server.onRoundOverPlayers <end-of-round soldier info : player info block>
        
        Effect: The round has just ended, and <end-of-round soldier info> is the final detailed player stats
        """
        #['server.onRoundOverPlayers', '8', 'clanTag', 'name', 'guid', 'teamId', 'kills', 'deaths', 'score', 'ping', '17', 'RAID', 'mavzee', 'EA_4444444444444444555555555555C023', '2', '20', '17', '310', '147', 'RAID', 'NUeeE', 'EA_1111111111111555555555555554245A', '2', '30', '18', '445', '146', '', 'Strzaerl', 'EA_88888888888888888888888888869F30', '1', '12', '7', '180', '115', '10tr', 'russsssssssker', 'EA_E123456789461416564796848C26D0CD', '2', '12', '12', '210', '141', '', 'Daezch', 'EA_54567891356479846516496842E17F4D', '1', '25', '14', '1035', '129', '', 'Oldqsdnlesss', 'EA_B78945613465798645134659F3079E5A', '1', '8', '12', '120', '256', '', 'TTETqdfs', 'EA_1321654656546544645798641BB6D563', '1', '11', '16', '180', '209', '', 'bozer', 'EA_E3987979878946546546565465464144', '1', '22', '14', '475', '152', '', 'Asdf 1977', 'EA_C65465413213216656546546546029D6', '2', '13', '16', '180', '212', '', 'adfdasse', 'EA_4F313565464654646446446644664572', '1', '4', '25', '45', '162', 'SG1', 'De56546ess', 'EA_123132165465465465464654C2FC2FBB', '2', '5', '8', '75', '159', 'bsG', 'N06540RZ', 'EA_787897944546565656546546446C9467', '2', '8', '14', '100', '115', '', 'Psfds', 'EA_25654321321321000006546464654B81', '2', '15', '15', '245', '140', '', 'Chezear', 'EA_1FD89876543216548796130EB83E411F', '1', '9', '14', '160', '185', '', 'IxSqsdfOKxI', 'EA_481321313132131313213212313112CE', '1', '21', '12', '625', '236', '', 'Ledfg07', 'EA_1D578987994651615166516516136450', '1', '5', '6', '85', '146', '', '5 56 mm', 'EA_90488E6543216549876543216549877B', '2', '0', '0', '0', '192']
        return b3.events.Event(b3.events.EVT_GAME_ROUND_PLAYER_SCORES, PlayerInfoBlock(data))
        
        
    def OnServerRoundoverteamscores(self, action, data):
        """
        server.onRoundOverTeamScores <end-of-round scores: team scores>
        
        Effect: The round has just ended, and <end-of-round scores> is the final ticket/kill/life count for each team
        """
        #['server.onRoundOverTeamScores', '2', '1180', '1200', '1200']
        return b3.events.Event(b3.events.EVT_GAME_ROUND_TEAM_SCORES, data[1])
        

    def tempban(self, client, reason='', duration=2, admin=None, silent=False, *kwargs):
        duration = b3.functions.time2minutes(duration)

        if isinstance(client, str):
            self.write(self.getCommand('kick', cid=client, reason=reason[:80]))
            return
        elif admin:
            fullreason = self.getMessage('temp_banned_by', self.getMessageVariables(client=client, reason=reason, admin=admin, banduration=b3.functions.minutesStr(duration)))
        else:
            fullreason = self.getMessage('temp_banned', self.getMessageVariables(client=client, reason=reason, banduration=b3.functions.minutesStr(duration)))
        fullreason = self.stripColors(fullreason)
        reason = self.stripColors(reason)

        if self.PunkBuster:
            # punkbuster acts odd if you ban for more than a day
            # tempban for a day here and let b3 re-ban if the player
            # comes back
            if duration > 1440:
                duration = 1440

            self.PunkBuster.kick(client, duration, reason)
        self.write(('banList.list',))
        self.write(self.getCommand('tempban', guid=client.guid, duration=duration*60, reason=reason[:80]))
        self.write(('banList.list',))
        ## also kick as the MoH server seems not to enforce all bans correctly
        self.write(self.getCommand('kick', cid=client.cid, reason=reason[:80]))
        
        if not silent and fullreason != '':
            self.say(fullreason)

        self.queueEvent(b3.events.Event(b3.events.EVT_CLIENT_BAN_TEMP, reason, client))


    def ban(self, client, reason='', admin=None, silent=False, *kwargs):
        """Permanent ban"""
        self.debug('BAN : client: %s, reason: %s', client, reason)
        if isinstance(client, b3.clients.Client):
            self.write(self.getCommand('ban', guid=client.guid, reason=reason[:80]))
            try:
                self.write(self.getCommand('kick', cid=client.cid, reason=reason[:80]))
            except:
                pass
            return

        if admin:
            reason = self.getMessage('banned_by', client.exactName, admin.exactName, reason)
        else:
            reason = self.getMessage('banned', client.exactName, reason)
        reason = self.stripColors(reason)

        if client.cid is None:
            # ban by ip, this happens when we !permban @xx a player that is not connected
            self.debug('EFFECTIVE BAN : %s',self.getCommand('banByIp', ip=client.ip, reason=reason[:80]))
            self.write(self.getCommand('banByIp', ip=client.ip, reason=reason[:80]))
            if admin:
                admin.message('banned: %s (@%s). His last ip (%s) has been added to banlist'%(client.exactName, client.id, client.ip))
        else:
            # ban by cid
            self.debug('EFFECTIVE BAN : %s',self.getCommand('ban', guid=client.guid, reason=reason[:80]))
            self.write(('banList.list',))
            self.write(self.getCommand('ban', cid=client.cid, reason=reason[:80]))
            self.write(('banList.list',))
            self.write(self.getCommand('kick', cid=client.cid, reason=reason[:80]))
            if admin:
                admin.message('banned: %s (@%s) has been added to banlist'%(client.exactName, client.id))

        if self.PunkBuster:
            self.PunkBuster.banGUID(client, reason)
        
        if not silent:
            self.say(reason)
        
        self.queueEvent(b3.events.Event(b3.events.EVT_CLIENT_BAN, reason, client))


    def rotateMap(self):
        """Load the next map (not level). If the current game mod plays each level twice
        to get teams the chance to play both sides, then this rotate a second
        time to really switch to the next map"""
        nextIndex = self.getNextMapIndex()
        if nextIndex == -1:
            # No map in map rotation list, just call admin.runNextLevel
            self.write(('admin.runNextRound',))
        else:
            self.write(('mapList.nextLevelIndex', nextIndex))
            self.write(('admin.runNextRound',))
    
    
    def changeMap(self, map):
        """Change to the given map
        
        1) determine the level name
            If map is of the form 'mp_001' and 'Kaboul' is a supported
            level for the current game mod, then this level is loaded.
            
            In other cases, this method assumes it is given a 'easy map name' (like
            'Port Valdez') and it will do its best to find the level name that seems
            to be for 'Port Valdez' within the supported levels.
        
            If no match is found, then instead of loading the map, this method 
            returns a list of candidate map names
            
        2) if we got a level name
            if the level is not in the current rotation list, then add it to 
            the map list and load it
        """

        supportedMaps = self.getSupportedMaps()
        if 'levels/%s'%map in supportedMaps:
            map = 'levels/%s'%map

        if map not in supportedMaps:
            match = self.getMapsSoundingLike(map)
            if len(match) == 1:
                map = match[0]
            else:
                return match

        if map in supportedMaps:
            levelnames = self.write(('mapList.list',))
            if map not in levelnames:
                # add the map to the map list
                nextIndex = self.getNextMapIndex()
                if nextIndex == -1:
                    self.write(('mapList.append', map))
                    nextIndex = 0
                else:
                    if nextIndex == 0:
                        # case where the map list contains only 1 map
                        nextIndex = 1
                    self.write(('mapList.insert', nextIndex, map))
            else:
                nextIndex = 0
                while nextIndex < len(levelnames) and levelnames[nextIndex] != map:
                    nextIndex += 1
            
            self.say('Changing map to %s' % map)
            time.sleep(1)
            self.write(('mapList.nextLevelIndex', nextIndex))
            self.write(('admin.runNextRound', ))
            
            
