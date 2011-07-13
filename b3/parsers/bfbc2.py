#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2010 
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
# ====================== CHANGELOG ========================
# 2010/03/09 - 0.1 - Courgette
# * parser is able to connect to a distant BFBC2 server through TCP
#   and listens for BFBC2 events.
# * BFBC2 events are routed to create matching B3 events
# 2010/03/12 - 0.2 - Courgette
# * the bot recognize players, commands and can respond
# 2010/03/14 - 0.3 - Courgette
# * better handling of 'connection reset by peer' issue
# 2010/03/14 - 0.4 - Courgette
# * save clantag as part of the name
# * save Punkbuster ID when client disconnects (when we get notified by PB)
# * save client IP on client connects (when we get notified by PB)
# 2010/03/14 - 0.5 - Courgette
# * add EVT_CLIENT_CONNECT
# * recognize kill/suicide/teamkill
# * add kick, tempban, unban, ban
# 2010/03/14 - 0.5.1 - Courgette
# * fix bug in OnPlayerKill
# 2010/03/14 - 0.5.2 - Courgette
# * remove junk
# 2010/03/14 - 0.5.2 - Courgette
# * fix EVT_CLIENT_SUICIDE parameters
# 2010/03/16 - 0.5.3 - SpacepiG
# * added maps, nextmap, getEasyName for translating map name.
# 2010/03/16 - 0.6 - Courgette
# * set client.team whenever we got the info from the BFBC2 server
# 2010/03/16 - 0.6.1 - Courgette
# * fix getCvar
# 2010/03/21 - 0.7 - Bakes
# * sync each 5 sec. to detect team changes 
# 2010/03/21 - 0.7.1 - Courgette
# * fix bug in getCvar when result is an empty list
# 2010/03/21 - 0.7.2 - Bakes
# * rotateMap() function added for !maprotate functionality.
# 2010/03/21 - 0.7.3 - Bakes
# * message_delay added so that self.say doesn't spew out spam.
# 2010/03/21 - 0.7.4 - Bakes
# * say messages are now queued instead of hanging the bot.
# 2010/03/21 - 0.7.5 - Bakes
# * fixes the 'multiple say event' problem that causes plenty of spam warnings.
# 2010/03/24 - 0.7.6 - Courgette
# * interrupt sayqueuelistener if the bot is paused
# * review all Punkbuster related code
# 2010/03/26 - 0.8 - Courgette
# * refactor the way clients' messages are queued too ensure consecutive
#   messages are displayed at a peaceful rate. Previously this was done
#   in a very similar way in the b3/clients.py file. But it is better
#   to make those changes only for BFBC2 at the moment
# 2010/03/27 - 0.8.1 - Bakes
# * teamkill event fixed - EVT_CLIENT_KILL_TEAM not EVT_CLIENT_TEAMKILL
# 2010/03/27 - 0.8.2 - Courgette
# * getEasyName return the level name is no easyname is found.
# * getEasyName return correct name for maps in SQDM mode
# 2010/03/30 - 0.8.3 - Courgette
# * fix self.Punkbuster
# * add Squad constants
# 2010/04/01 - 0.8.4 - Bakes
# * self.game.* is now updated correctly every 15 seconds.
# 2010/04/05 - 1.0 - Courgette
# * update parser to follow BFBC2 R9 protocol changes
# 2010/04/07 - 1.1 - Courgette
# * fix OnPlayerTeamchange
# * fix OnPlayerSquadchange
# * fix OnServerLoadinglevel
# * fix OnServerLevelstarted
# * introduced a mechanisms that ensure the server loade a target map. This
#   ensure changeMap and mapRotate actually change maps and not just change 
#   map sides (as admin.runNextLevel does natively)
# * make used of the soundex/levenshteinDistance algorithm to get map name from
#   user commands
# 2010/04/08 - 1.2 - Courgette
# * change the way map change was ensured as R9 build 527791 makes things easier
# * ignore chat events when the player who speaks is 'Server'
# * fix client.squad value type
# * on map load, update self.game.<whatever we can> so other plugins can find more data
# * handle gracefully cases where the mapList is empty
# * fix typo in 'africa harbor'
# 2010/04/10 - 1.2.1 - Courgette
# * you can now specify in b3.xml what custom maximum line length you want to 
#   see in the chat zone. 
# * make sure the BFBC2 server is R9 or later
# 2010/04/11 - 1.2.2 - Courgette, Bakes
# * make this module compatible with python 2.4
# * saybig() function is now available for use by plugins.
# 2010/04/11 - 1.2.3 - Bakes
# * fixed arica harbor typo
# 2010/04/11 - 1.2.4 - Bakes
# * client.messagebig() is now available for use by plugins.
# * getHardName is added from poweradminbfbc2, reverse of getEasyname
# 2010/04/12 - 1.2.5 - Courgette
# * make sure client.squad and client.team are of type int. 
# 2010/04/12 - 1.2.6 - Courgette
# Fix client.team inconsistency
# * add client.teamId property which is the exact team id as understood by the BFBC2 
#   (while client.team follow the B3 team numbering scheme : b3.TEAM_BLUE, b3.TEAM_SPEC, etc)
# 2010/05/19 - 1.2.7 - Bakes
# * fixed issue between this and clients.py by overwriting the clients.py method. Will need to
#   be fixed more comprehensively at a later date, this is a quick fix and nothing more!
# 2010/05/21 - 1.2.8 - xlr8or
# * delegated getByCID override to clients.py and fix it there
# 2010/05/22 - 1.2.9 - nicholasperkins (inserted by Bakes)
# * new method for getWrap that doesn't split strings in the middle of words.
# 2010/07/20 - 1.3.0 - xlr8or
# * modified OnPlayerKill to work with R15+
# * fixed infinite loop in a python socket thread in receivePacket() (in protocol.py) on gameserver restart
# * fixed (statusplugin crontab) error when polling for playerscores and -pings while server is unreachable
# 2010/07/26 - 1.3.1 - xlr8or
# * make sure we don't create a new client without a guid and;
# * pass guid to getClient() in OnPlayerAuthenticated() for a better chance on a guid
# 2010/07/28 - 1.3.1 - Durzo
# * merge onPlayerSpawn event with latest xlr8or code base
# 2010/07/29 - 1.3.2 - xlr8or
# * Added EVT_PUNKBUSTER_NEW_CONNECTION when IP address is published by PB
#  (to aid IP and GeoIP based plugins)
# * Removed obsolete code in OnPBLostConection() that generated a consistent error.
# * Fixed unban()
# * Added needConfirmation var to write() so we can test on the confirmationtype ("OK", "NotFound") sent by the server on rcon.
# 2010-07-30 - 1.3.3 - xlr8or
# * Added joinClient() to OnServerLevelstarted() so rounds are counted for playerstats
# 2010-07-30 - 1.3.4 - xlr8or
# * Quick mapretrieval on startup
# 2010-07-30 - 1.3.5 - xlr8or
# * Fixed self.game.rounds
# 2010-08-15 - 1.3.6 - xlr8or
# * Fix PB handling when the PB server was renamed to something else than 'PunkBuster Server'
# * Added OnPBVersion() for testing purposes 
# 2010-09-02 - 1.3.7 - xlr8or
# * Fix memory leak due to never ending threads in messagequeue workers
# 2010-09-02 - 1.3.8 - xlr8or
# * Better thread handling in messagequeue workers
# * Fix bug on exit preventing --restart to function properly
# 2010-09-02 - 1.3.9 - xlr8or
# * Debugged messagequeue workers
# 2010-09-02 - 1.3.10 - xlr8or
# * More debugging messagequeue workers
# 2010-09-25 - 1.4 - Bakes
# * Refactored into Frostbite and Bfbc2 for MoH support.
# 2010-10-23 - 2.0 - Courgette
# * Refactored with inheritence from a frostbite specific abstract parser
# 2010-11-21 - 2.1 - Courgette
# * import rotateMap and changeMap from abstractParser 
# 2010-11-21 - 2.1.1 - Durzo
# * adjust mapnames from mappack 7 and vietnam expansion 
# 2011-06-04 - 2.2 - Courgette
# makes use of the new pluginsStarted parser hook
#
# ===== B3 EVENTS AVAILABLE TO PLUGIN DEVELOPERS USING THIS PARSER ======
# -- standard B3 events  -- 
# EVT_UNKNOWN
# EVT_CLIENT_JOIN
# EVT_CLIENT_KICK
# EVT_CLIENT_SAY
# EVT_CLIENT_TEAM_SAY
# EVT_CLIENT_PRIVATE_SAY
# EVT_CLIENT_CONNECT
# EVT_CLIENT_DISCONNECT
# EVT_CLIENT_SUICIDE
# EVT_CLIENT_KILL_TEAM
# EVT_CLIENT_KILL
# EVT_GAME_WARMUP
# EVT_GAME_ROUND_START
# EVT_CLIENT_BAN_TEMP
# EVT_CLIENT_BAN
#
# -- BFBC2 specific B3 events --
# EVT_CLIENT_SPAWN
# EVT_CLIENT_SQUAD_CHANGE
# EVT_PUNKBUSTER_LOST_PLAYER
# EVT_PUNKBUSTER_SCHEDULED_TASK
# EVT_PUNKBUSTER_NEW_CONNECTION
# 
# -- B3 events triggered natively by B3 core --
# EVT_CLIENT_NAME_CHANGE
# EVT_CLIENT_TEAM_CHANGE
# EVT_CLIENT_AUTH
# EVT_CLIENT_DISCONNECT
#

__author__  = 'Courgette, SpacepiG, Bakes'
__version__ = '2.2'

import time, threading, Queue
import b3.events
from b3.parsers.frostbite.abstractParser import AbstractParser
from b3.parsers.frostbite.util import PlayerInfoBlock

SAY_LINE_MAX_LENGTH = 100

GAMETYPE_SQDM = 'SQDM' # Squad Deathmatch. no team, but up to 4 squad fighting each others
GAMETYPE_CONQUEST = 'CONQUEST'
GAMETYPE_RUSH = 'RUSH'
GAMETYPE_SQRUSH = 'SQRUSH' # Squad Rush

SQUAD_NOSQUAD = 0
SQUAD_ALPHA = 1
SQUAD_BRAVO = 2
SQUAD_CHARLIE = 3
SQUAD_DELTA = 4
SQUAD_ECHO = 5
SQUAD_FOXTROT = 6
SQUAD_GOLF = 7
SQUAD_HOTEL = 8
SQUAD_NEUTRAL = 24

BUILD_NUMBER_R9 = 527791
BUILD_NUMBER_R16 = 556157
BUILD_NUMBER_R17 = 560541

#----------------------------------------------------------------------------------------------------------------------------------------------
class Bfbc2Parser(AbstractParser):
    gameName = 'bfbc2'

    _gameServerVars = (
        '3dSpotting',
        'adminPassword',
        'bannerUrl',
        'crossHair',
        'currentPlayerLimit',
        'friendlyFire',
        'gamePassword',
        'hardCore',
        'killCam',
        'maxPlayerLimit',
        'miniMap',
        'miniMapSpotting',
        'playerLimit',
        'punkBuster',
        'rankLimit',
        'ranked',
        'serverDescription',
        'teamBalance',
        'thirdPersonVehicleCameras'
    )

    saybigqueue = Queue.Queue()
    saybigqueuelistener = None


    def startup(self):
        AbstractParser.startup(self)

        self.saybigqueuelistener = threading.Thread(target=self.saybigqueuelistener)
        self.saybigqueuelistener.setDaemon(True)
        self.saybigqueuelistener.start()

        # add BFBC2 specific commands
        self._commands['messagebig'] = ('admin.yell', '%(message)s', '%(duration)s', 'player', '%(cid)s')
        self._commands['saybig'] = ('admin.yell', '%(message)s', '%(duration)s', 'all')


        # create the 'Server' client
        self.clients.newClient('Server', guid='Server', name='Server', hide=True, pbid='Server', team=b3.TEAM_UNKNOWN, squad=SQUAD_NEUTRAL)
        

        if self.config.has_option('bfbc2', 'max_say_line_length'):
            try:
                maxlength = self.config.getint('bfbc2', 'max_say_line_length')
                if maxlength > SAY_LINE_MAX_LENGTH:
                    self.warning('max_say_line_length cannot be greater than %s' % SAY_LINE_MAX_LENGTH)
                    maxlength = SAY_LINE_MAX_LENGTH
                if maxlength < 20:
                    self.warning('max_say_line_length is way too short. using default')
                    maxlength = self._settings['line_length']
                self._settings['line_length'] = maxlength
                self._settings['min_wrap_length'] = maxlength
            except Exception, err:
                self.error('failed to read max_say_line_length setting "%s" : %s' % (self.config.get('bfbc2', 'max_say_line_length'), err))
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
                if 'clanTag' in p and len(p['clanTag']) > 0:
                    name = "[" + p['clanTag'] + "] " + p['name']
                self.debug('client %s found on the server' % cid)
                client = self.clients.newClient(cid, guid=p['guid'], name=name, team=p['teamId'], squad=p['squadId'], data=p)
                self.queueEvent(b3.events.Event(b3.events.EVT_CLIENT_JOIN, p, client))


    def saybigqueuelistener(self):
        while self.working:
            msg = self.saybigqueue.get()
            for line in self.getWrap(self.stripColors(self.msgPrefix + ' ' + msg), self._settings['line_length'], self._settings['min_wrap_length']):
                self.write(self.getCommand('saybig', message=line, duration=2400))
                time.sleep(self._settings['message_delay'])
 
 
    def checkVersion(self):
        version = self.output.write('version')
        self.info('server version : %s' % version)
        if version[0] != 'BFBC2':
            raise Exception("the bfbc2 parser can only work with BattleField Bad Company 2")
        if int(version[1]) < BUILD_NUMBER_R9:
            raise SystemExit("this bfbc2 parser requires a BFBC2 server R9 or later") 

    #----------------------------------
    

    def OnPlayerTeamchange(self, action, data):
        """
        player.onTeamChange <soldier name: player name> <team: Team ID> <squad: Squad ID>
        Effect: Player might have changed team
        """
        client = self.getClient(data[0])
        if client:
            client.team = self.getTeam(data[1]) # .team setter will send team change event
            client.teamId = int(data[1])
            client.squad = int(data[2])
            
            
    def OnPlayerSquadchange(self, action, data):
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


    def getEasyName(self, mapname):
        """ Change levelname to real name """
        if mapname.startswith('Levels/MP_001'):
            return 'Panama Canal'
            
        elif mapname.startswith('Levels/MP_002'):
            return 'Valparaiso'

        elif mapname.startswith('Levels/MP_003'):
            return 'Laguna Alta'

        elif mapname.startswith('Levels/MP_004'):
            return 'Isla Inocentes'

        elif mapname.startswith('Levels/MP_005'):
            return 'Atacama Desert'

        elif mapname.startswith('Levels/MP_006'):
            return 'Arica Harbor'

        elif mapname.startswith('Levels/MP_007'):
            return 'White Pass'

        elif mapname.startswith('Levels/MP_008'):
            return 'Nelson Bay'

        elif mapname.startswith('Levels/MP_009'):
            return 'Laguna Preza'

        elif mapname.startswith('Levels/MP_012'):
            return 'Port Valdez'

        elif mapname.startswith('Levels/BC1_Oasis'):
            return 'Oasis'

        elif mapname.startswith('Levels/BC1_Harvest_Day'):
            return 'Harvest Day'

        elif mapname.startswith('Levels/MP_SP_002'):
            return 'Cold War'

        elif mapname.startswith('Levels/MP_SP_005'):
            return 'Heavy Metal'

        elif mapname.startswith('Levels/nam_mp_002'):
            return 'Vantage Point'

        elif mapname.startswith('Levels/nam_mp_003'):
            return 'Hill 137'

        elif mapname.startswith('Levels/nam_mp_005'):
            return 'Cao Son Temple'

        elif mapname.startswith('Levels/nam_mp_006'):
            return 'Phu Bai Valley'

        else:
            self.warning('unknown level name \'%s\'. Please report this on B3 forums' % mapname)
            return mapname
            
            
    def getHardName(self, mapname):
        """ Change real name to level name """
        mapname = mapname.lower()
        if mapname.startswith('panama canal'):
            return 'Levels/MP_001'
            
        elif mapname.startswith('val paraiso'):
            return 'Levels/MP_002'

        elif mapname.startswith('laguna alta'):
            return 'Levels/MP_003'

        elif mapname.startswith('isla inocentes'):
            return 'Levels/MP_004'

        elif mapname.startswith('atacama desert'):
            return 'Levels/MP_005'

        elif mapname.startswith('arica harbor'):
            return 'Levels/MP_006'

        elif mapname.startswith('white pass'):
            return 'Levels/MP_007'

        elif mapname.startswith('nelson bay'):
            return 'Levels/MP_008'

        elif mapname.startswith('laguna preza'):
            return 'Levels/MP_009'

        elif mapname.startswith('port valdez'):
            return 'Levels/MP_012'

        elif mapname.startswith('oasis'):
            return 'Levels/BC1_Oasis'

        elif mapname.startswith('harvest day'):
            return 'Levels/BC1_Harvest_Day'

        elif mapname.startswith('cold war'):
            return 'Levels/MP_SP_002'

        elif mapname.startswith('heavy metal'):
            return 'Levels/MP_SP_005'

        elif mapname.startswith('vantage point'):
            return 'levels/nam_mp_002'

        elif mapname.startswith('hill 137'):
            return 'levels/nam_mp_003'

        elif mapname.startswith('cao son temple'):
            return 'levels/nam_mp_005'

        elif mapname.startswith('phu bai valley'):
            return 'levels/nam_mp_006'        

        else:
            self.warning('unknown level name \'%s\'. Please make sure you have entered a valid mapname' % mapname)
            return mapname

        
    def getTeam(self, team):
        """convert BFBC2 team numbers to B3 team numbers"""
        team = int(team)
        if team == 1:
            return b3.TEAM_RED
        elif team == 2:
            return b3.TEAM_BLUE
        elif team == 3:
            return b3.TEAM_SPEC
        else:
            return b3.TEAM_UNKNOWN
        
        
    def getClient(self, cid, _guid=None):
        """Get a connected client from storage or create it
        B3 CID   <--> ingame character name
        B3 GUID  <--> EA_guid
        """
        
        # try to get the client from the storage of already authed clients
        client = self.clients.getByCID(cid)
        if not client:
            if cid == 'Server':
                return self.clients.newClient('Server', guid='Server', name='Server', hide=True, pbid='Server', team=b3.TEAM_UNKNOWN, squad=SQUAD_NEUTRAL)
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
            client = self.clients.newClient(cid, guid=guid, name=name, team=self.getTeam(p['teamId']), teamId=int(p['teamId']), squad=p['squadId'], data=p)
            self.queueEvent(b3.events.Event(b3.events.EVT_CLIENT_JOIN, p, client))
        
        return client


    def getServerVars(self):
        """Update the game property from server fresh data"""
        try: self.game.is3dSpotting = self.getCvar('3dSpotting').getBoolean()
        except: pass
        try: self.game.bannerUrl = self.getCvar('bannerUrl').getString()
        except: pass
        try: self.game.crossHair = self.getCvar('crossHair').getBoolean()
        except: pass
        try: self.game.currentPlayerLimit = self.getCvar('currentPlayerLimit').getInt()
        except: pass
        try: self.game.friendlyFire = self.getCvar('friendlyFire').getBoolean()
        except: pass
        try: self.game.hardCore = self.getCvar('hardCore').getBoolean()
        except: pass
        try: self.game.killCam = self.getCvar('killCam').getBoolean()
        except: pass
        try: self.game.maxPlayerLimit = self.getCvar('maxPlayerLimit').getInt()
        except: pass
        try: self.game.miniMap = self.getCvar('miniMap').getBoolean()
        except: pass
        try: self.game.miniMapSpotting = self.getCvar('miniMapSpotting').getBoolean()
        except: pass
        try: self.game.playerLimit = self.getCvar('playerLimit').getInt()
        except: pass
        try: self.game.punkBuster = self.getCvar('punkBuster').getBoolean()
        except: pass
        try: self.game.rankLimit = self.getCvar('rankLimit').getInt()
        except: pass
        try: self.game.ranked = self.getCvar('ranked').getBoolean()
        except: pass
        try: self.game.serverDescription = self.getCvar('serverDescription').getString()
        except: pass
        try: self.game.teamBalance = self.getCvar('teamBalance').getBoolean()
        except: pass
        try: self.game.thirdPersonVehicleCameras = self.getCvar('thirdPersonVehicleCameras').getBoolean()
        except: pass


    def messagebig(self, client, text):
        try:
            if client == None:
                self.saybig(text)
            elif client.cid == None:
                pass
            else:
                self.write(self.getCommand('messagebig', message=text, cid=client.cid, duration=2400))
        except:
            pass
        
        
    def saybig(self, msg):
        self.saybigqueue.put(msg)


    def rotateMap(self):
        """Load the next map (not level). If the current game mod plays each level twice
        to get teams the chance to play both sides, then this rotate a second
        time to really switch to the next map"""
        nextIndex = self.getNextMapIndex()
        if nextIndex == -1:
            # No map in map rotation list, just call admin.runNextLevel
            self.write(('admin.runNextLevel',))
        else:
            self.write(('mapList.nextLevelIndex', nextIndex))
            self.write(('admin.runNextLevel',))
    
    
    def changeMap(self, map):
        """Change to the given map
        
        1) determine the level name
            If map is of the form 'Levels/MP_001' and 'Levels/MP_001' is a supported
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
            self.write(('admin.runNextLevel', ))



#############################################################
# Below is the code that change a bit the b3.clients.Client
# class at runtime. What the point of coding in python if we
# cannot play with its dynamic nature ;)
#
# why ?
# because doing so make sure we're not broking any other 
# working and long tested parser. The change we make here
# are only applied when the Bfbc2 parser is loaded.
#############################################################

## add a new method to the Client class
def frostbiteClientMessageBigQueueWorker(self):
    """
    This takes a line off the queue and displays it
    in the middle of the screen then pause for
    'message_delay' seconds
    """
    while not self.messagebigqueue.empty():
        msg = self.messagebigqueue.get()
        if msg:
            self.console.messagebig(self, msg)
            time.sleep(int(self.console._settings['message_delay']))
b3.clients.Client.messagebigqueueworker = frostbiteClientMessageBigQueueWorker

## add the Client.messagebig() method at runtime
def frostbiteClientMessageBigMethod(self, msg):
    if msg and len(msg.strip())>0:
        # do we have a queue?
        if not hasattr(self, 'messagebigqueue'):
            self.messagebigqueue = Queue.Queue()
        # fill the queue
        text = self.console.stripColors(self.console.msgPrefix + ' [pm] ' + msg)
        for line in self.console.getWrap(text):
            self.messagebigqueue.put(line)
        # create a thread that executes the worker and pushes out the queue
        if not hasattr(self, 'messagebighandler') or not self.messagebighandler.isAlive():
            self.messagebighandler = threading.Thread(target=self.messagebigqueueworker)
            self.messagebighandler.setDaemon(True)
            self.messagebighandler.start()
        else:
            self.console.verbose('messagebighandler for %s isAlive' %self.name)
b3.clients.Client.messagebig = frostbiteClientMessageBigMethod
