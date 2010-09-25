#
# BigBrotherBot(B3) (www.bigbrotherbot.com)
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
__version__ = '1.3.10'


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
class Bfbc2Parser(b3.parser.Parser):
    gameName = 'bfbc2'
    OutputClass = rcon.Rcon
    sayqueue = Queue.Queue()
    sayqueuelistener = None
    saybigqueue = Queue.Queue()
    saybigqueuelistener = None
    
    _bfbc2EventsListener = None
    _bfbc2Connection = None
    _nbConsecutiveConnFailure = 0
    

    # BFBC2 does not support color code, so we need this property
    # in order to get stripColors working
    _reColor = re.compile(r'(\^[0-9])') 
    
    _settings = {}
    _settings['line_length'] = 65
    _settings['min_wrap_length'] = 65
    _settings['message_delay'] = 2

    _commands = {}
    _commands['message'] = ('admin.say', '%(message)s', 'player', '%(cid)s')
    _commands['messagebig'] = ('admin.yell', '%(message)s', '%(duration)s', 'player', '%(cid)s')
    _commands['say'] = ('admin.say', '%(message)s', 'all')
    _commands['saybig'] = ('admin.yell', '%(message)s', '%(duration)s', 'all')
    _commands['kick'] = ('admin.kickPlayer', '%(cid)s', '%(reason)s')
    _commands['ban'] = ('banList.add', 'guid', '%(guid)s', 'perm', '%(reason)s')
    _commands['banByIp'] = ('banList.add', 'ip', '%(ip)s', 'perm', '%(reason)s')
    _commands['unban'] = ('banList.remove', 'guid', '%(guid)s')
    _commands['unbanByIp'] = ('banList.remove', 'ip', '%(ip)s')
    _commands['tempban'] = ('banList.add', 'guid', '%(guid)s', 'seconds', '%(duration)d', '%(reason)s')

    
    _eventMap = {
        'player.onKicked': b3.events.EVT_CLIENT_KICK,
    }

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

    _punkbusterMessageFormats = (
        (re.compile(r'^(?P<servername>.*): PunkBuster Server for BC2 \((?P<version>.+)\)\sEnabl.*$'), 'OnPBVersion'),
        (re.compile(r'^(?P<servername>.*): Running PB Scheduled Task \(slot #(?P<slot>\d+)\)\s+(?P<task>.*)$'), 'OnPBScheduledTask'),
        (re.compile(r'^(?P<servername>.*): Lost Connection \(slot #(?P<slot>\d+)\) (?P<ip>[^:]+):(?P<port>\d+) (?P<pbuid>[^\s]+)\(-\)\s(?P<name>.+)$'), 'OnPBLostConnection'),
        (re.compile(r'^(?P<servername>.*): Master Query Sent to \((?P<pbmaster>[^\s]+)\) (?P<ip>[^:]+)$'), 'OnPBMasterQuerySent'),
        (re.compile(r'^(?P<servername>.*): Player GUID Computed (?P<pbid>[0-9a-fA-F]+)\(-\) \(slot #(?P<slot>\d+)\) (?P<ip>[^:]+):(?P<port>\d+)\s(?P<name>.+)$'), 'OnPBPlayerGuid'),
        (re.compile(r'^(?P<servername>.*): New Connection \(slot #(?P<slot>\d+)\) (?P<ip>[^:]+):(?P<port>\d+) \[(?P<something>[^\s]+)\]\s"(?P<name>.+)".*$'), 'OnPBNewConnection')
     )

    PunkBuster = None

    def startup(self):
        
        # add specific events
        self.Events.createEvent('EVT_CLIENT_SQUAD_CHANGE', 'Client Squad Change')
        self.Events.createEvent('EVT_PUNKBUSTER_SCHEDULED_TASK', 'PunkBuster scheduled task')
        self.Events.createEvent('EVT_PUNKBUSTER_LOST_PLAYER', 'PunkBuster client connection lost')
        self.Events.createEvent('EVT_PUNKBUSTER_NEW_CONNECTION', 'PunkBuster client received IP')
        self.Events.createEvent('EVT_CLIENT_SPAWN', 'Client Spawn')
                
        # create the 'Server' client
        self.clients.newClient('Server', guid='Server', name='Server', hide=True, pbid='Server', team=b3.TEAM_UNKNOWN, squad=SQUAD_NEUTRAL)
        
        if self.config.has_option('server', 'punkbuster') and self.config.getboolean('server', 'punkbuster'):
            self.info('kick/ban by punkbuster is unsupported yet')
            #self.debug('punkbuster enabled in config')
            #self.PunkBuster = Bfbc2PunkBuster(self)
        
        
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
            
        version = self.output.write('version')
        self.info('BFBC2 server version : %s' % version)
        if version[0] != 'BFBC2':
            raise Exception("the bfbc2 parser can only work with BattleField Bad Company 2")
        if int(version[1]) < BUILD_NUMBER_R9:
            raise SystemExit("this bfbc2 parser requires a BFBC2 server R9 or later")
        
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
                client = self.clients.newClient(cid, guid=p['guid'], name=name, team=p['teamId'], squad=p['squadId'], data=p)
                self.queueEvent(b3.events.Event(b3.events.EVT_CLIENT_JOIN, p, client))
                
        
        self.sayqueuelistener = threading.Thread(target=self.sayqueuelistener)
        self.sayqueuelistener.setDaemon(True)
        self.sayqueuelistener.start()
        
        self.saybigqueuelistener = threading.Thread(target=self.saybigqueuelistener)
        self.saybigqueuelistener.setDaemon(True)
        self.saybigqueuelistener.start()
        
        
    def sayqueuelistener(self):
        while self.working:
            msg = self.sayqueue.get()
            for line in self.getWrap(self.stripColors(self.msgPrefix + ' ' + msg), self._settings['line_length'], self._settings['min_wrap_length']):
                self.write(self.getCommand('say', message=line))
                time.sleep(self._settings['message_delay'])
                
    def saybigqueuelistener(self):
        while self.working:
            msg = self.saybigqueue.get()
            for line in self.getWrap(self.stripColors(self.msgPrefix + ' ' + msg), self._settings['line_length'], self._settings['min_wrap_length']):
                self.write(self.getCommand('saybig', message=line, duration=2400))
                time.sleep(self._settings['message_delay'])
           
    def run(self):
        """Main worker thread for B3"""
        self.bot('Start listening ...')
        self.screen.write('Startup Complete : B3 is running! Let\'s get to work!\n\n')
        self.screen.write('(If you run into problems, check %s in the B3 root directory for detailed log info)\n' % self.config.getpath('b3', 'logfile'))
        #self.screen.flush()

        self.updateDocumentation()

        while self.working:
            """
            While we are working, connect to the BFBC2 server
            """
            if self._paused:
                if self._pauseNotice == False:
                    self.bot('PAUSED - Not parsing any lines, B3 will be out of sync.')
                    self._pauseNotice = True
            else:
                
                try:                
                    if self._bfbc2Connection is None:
                        self.verbose('Connecting to BFBC2 server ...')
                        self._bfbc2Connection = Bfbc2Connection(self, self._rconIp, self._rconPort, self._rconPassword)

                    self._bfbc2Connection.subscribeToBfbc2Events()
                    self.clients.sync()
                    self._nbConsecutiveConnFailure = 0
                        
                    nbConsecutiveReadFailure = 0
                    while self.working:
                        """
                        While we are working and connected, read a packet
                        """
                        if not self._paused:
                            try:
                                bfbc2packet = self._bfbc2Connection.readBfbc2Event()
                                self.console("%s" % bfbc2packet)
                                try:
                                    self.routeBfbc2Packet(bfbc2packet)
                                except SystemExit:
                                    raise
                                except Exception, msg:
                                    self.error('%s: %s', msg, traceback.extract_tb(sys.exc_info()[2]))
                            except Bfbc2Exception, e:
                                #self.debug(e)
                                nbConsecutiveReadFailure += 1
                                if nbConsecutiveReadFailure > 5:
                                    raise e
                except Bfbc2Exception, e:
                    self.debug(e)
                    self._nbConsecutiveConnFailure += 1
                    self._bfbc2Connection.close()
                    if self._nbConsecutiveConnFailure <= 20:
                        self.debug('sleeping 0.5 sec...')
                        time.sleep(0.5)
                    elif self._nbConsecutiveConnFailure <= 60:
                        self.debug('sleeping 2 sec...')
                        time.sleep(2)
                    else:
                        self.debug('sleeping 30 sec...')
                        time.sleep(30)
                    
        self.bot('Stop listening.')

        if self.exiting.acquire(1):
            #self.input.close()
            self.output.close()

            if self.exitcode:
                sys.exit(self.exitcode)

    def routeBfbc2Packet(self, packet):
        if packet is None:
            self.warning('cannot route empty packet : %s' % traceback.extract_tb(sys.exc_info()[2]))
        
        bfbc2EventType = packet[0]
        bfbc2EventData = packet[1:]
        
        match = re.search(r"^(?P<actor>[^.]+)\.on(?P<event>.+)$", bfbc2EventType)
        if match:
            func = 'On%s%s' % (string.capitalize(match.group('actor')), \
                               string.capitalize(match.group('event')))
            #self.debug("-==== FUNC!!: " + func)
            
        if match and hasattr(self, func):
            #self.debug('routing ----> %s' % func)
            func = getattr(self, func)
            event = func(bfbc2EventType, bfbc2EventData)
            #self.debug('event : %s' % event)
            if event:
                self.queueEvent(event)
            
        elif bfbc2EventType in self._eventMap:
            self.queueEvent(b3.events.Event(
                    self._eventMap[bfbc2EventType],
                    bfbc2EventData))
        else:
            if func:
                data = func + ' '
            data += str(bfbc2EventType) + ': ' + str(bfbc2EventData)
            self.debug('TODO: %r' % packet)
            self.queueEvent(b3.events.Event(b3.events.EVT_UNKNOWN, data))


    #----------------------------------
    

    def OnPlayerChat(self, action, data):
        """
        player.onChat <source soldier name: string> <text: string> <target group: player subset>
        
        Effect: Player with name <source soldier name> (or the server, or the 
        server admin) has sent chat message <text> to some people
        
        Comment: The chat text is as represented before the profanity filtering 
        If <source soldier name> is 'Server', then the message was sent from the 
        server rather than from an actual player If sending to a specific player, 
        and the player doesn't exist, then the target group will be 'player' ''
        """
        #['envex', 'gg', 'team', 1]
        #['envex', 'gg', 'all']
        #['envex', 'gg', 'squad' 2]
        #['envex', 'gg', 'player', 'Courgette']
        client = self.getClient(data[0])
        if client is None:
            self.warning("Could not get client :( %s" % traceback.extract_tb(sys.exc_info()[2]))
            return
        if client.cid == 'Server':
            # ignore chat events for Server
            return
        if data[2] == 'all':
            return b3.events.Event(b3.events.EVT_CLIENT_SAY, data[1].lstrip('/'), client, 'all')
        elif data[2] == 'team' or data[2] == 'squad':
            return b3.events.Event(b3.events.EVT_CLIENT_TEAM_SAY, data[1].lstrip('/'), client, data[2] + ' ' + data[3])
        elif data[2] == 'player':
            target = self.getClient(data[3])
            return b3.events.Event(b3.events.EVT_CLIENT_PRIVATE_SAY, data[1].lstrip('/'), client, target)
        

    def OnPlayerLeave(self, action, data):
        #player.onLeave: ['GunnDawg']
        client = self.getClient(data[0])
        if client: 
            client.endMessageThreads = True
            client.disconnect() # this triggers the EVT_CLIENT_DISCONNECT event
        return None

    def OnPlayerJoin(self, action, data):
        """
        we don't have guid at this point. Wait for player.onAuthenticated
        """
        pass
        

    def OnPlayerAuthenticated(self, action, data):
        """
        player.onAuthenticated <soldier name: string> <player GUID: guid>
        
        Effect: Player with name <soldier name> has been authenticated, and has the given GUID
        """
        #player.onJoin: ['OrasiK']
        client = self.getClient(data[0], data[1])
        # No need to queue a client join event, that is done by clients.newClient() already
        # return b3.events.Event(b3.events.EVT_CLIENT_CONNECT, data, client)


    def OnPlayerSpawn(self, action, data):
        """
        Request: player.onSpawn <spawning soldier name: string> <kit type: string> <gadget: string> <pistol: string> <primary weapon: string> <specialization 1: string> <specialization 2: string> <specialization 3: string>
        """
        if len(data) < 2:
            return None

        spawner = self.getClient(data[0])
        kit = data[1]
        gadget = data[2]
        pistol = data[3]
        weapon = data[4]
        spec1 = data[5]
        spec2 = data[6]
        spec3 = data[7]

        event = b3.events.EVT_CLIENT_SPAWN
        return b3.events.Event(event, (kit, gadget, pistol, weapon, spec1, spec2, spec3), spawner)


    def OnPlayerKill(self, action, data):
        """
        Request: player.onKill <killing soldier name: string> <killed soldier name: string> <weapon: string> <headshot: boolean> <killer location: 3 x integer> <killed location: 3 x integes>

        Effect: Player with name <killing soldier name> has killed <killed soldier name> Suicide is indicated with the same soldier name for killer and victim. If the server kills the player (through admin.killPlayer), it is indicated by showing the killing soldier name as Server. The locations of the killer and the killed have a random error of up to 10 meters in each direction.
        """
        #R15: player.onKill: ['Brou88', 'kubulina', 'S20K', 'true', '-77', '68', '-195', '-76', '62', '-209']
        if len(data) < 2:
            return None

        attacker = self.getClient(data[0])
        if not attacker:
            self.debug('No attacker')
            return None

        victim = self.getClient(data[1])
        if not victim:
            self.debug('No victim')
            return None
        
        if data[2]:
            weapon = data[2]
        else:
            # to accomodate pre R15 servers
            weapon = None

        if data[3]:
            if data[3] == 'true':
                hitloc = 'head'
            else:
                hitloc = 'torso'
        else:
            # to accomodate pre R15 servers
            hitloc = None

        attackerloc = []
        victimloc = []
        if data[4] and data[9]:
            attackerloc.append(data[4])
            attackerloc.append(data[5])
            attackerloc.append(data[6])
            victimloc.append(data[7])
            victimloc.append(data[8])
            victimloc.append(data[9])
        else:
            # to accomodate pre R15 servers
            attackerloc.append('None')
            victimloc.append('None')

        event = b3.events.EVT_CLIENT_KILL
        if victim == attacker:
            event = b3.events.EVT_CLIENT_SUICIDE
        elif attacker.team == victim.team and attacker.team != b3.TEAM_UNKNOWN and attacker.team != b3.TEAM_SPEC:
            event = b3.events.EVT_CLIENT_KILL_TEAM
        return b3.events.Event(event, (100, weapon, hitloc, attackerloc, victimloc), attacker, victim)

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


    def OnServerLoadinglevel(self, action, data):
        """
        server.onLoadingLevel <level name: string>
        
        Effect: Level is loading
        """
        self.debug("OnServerLoadinglevel: %s" % data)
        if not self.game.mapName:
            self.game.mapName = data[0]
        if self.game.mapName != data[0]:
            # map change detected
            self.game.startMap()
        self.game.mapName = data[0]
        self.getServerInfo()
        return b3.events.Event(b3.events.EVT_GAME_WARMUP, data[0])

    def OnServerLevelstarted(self, action, data):
        """
        server.onLevelStarted
        
        Effect: Level is started"""
        # next function call will increase roundcount by one, this is not correct, need to deduct one to compensate
        # we'll still leave the call here since it provides us self.game.roundTime()
        self.game.startRound()
        self.game.rounds -= 1
        
        #Players need to be joined (EVT_CLIENT_JOIN) for stats to count rounds
        self.joinPlayers()
        return b3.events.Event(b3.events.EVT_GAME_ROUND_START, self.game)
            

    def OnPunkbusterMessage(self, action, data):
        """handles all punkbuster related events and 
        route them to the appropriate method depending
        on the type of PB message.
        """
        #self.debug("PB> %s" % data)
        if data and data[0]:
            for regexp, funcName in self._punkbusterMessageFormats:
                match = re.match(regexp, str(data[0]).strip())
                if match:
                    break
            if match and hasattr(self, funcName):
                func = getattr(self, funcName)
                event = func(match, data[0])
                if event:
                    self.queueEvent(event)     
            else:
                return b3.events.Event(b3.events.EVT_UNKNOWN, data)
                
    def OnPBVersion(self, match,data):
        """PB notifies us of the version numbers
        version = match.group('version')"""
        #self.debug('PunkBuster server named: %s' % match.group('servername') )
        #self.debug('PunkBuster Server version: %s' %( match.group('version') ) )
        pass

    def OnPBNewConnection(self, match, data):
        """PunkBuster tells us a new player identified. The player is
        normally already connected and authenticated by B3 by ea_guid
        
        This is our first moment where we receive the clients IP address
        so we also fire the custom event EVT_PUNKBUSTER_NEW_CONNECTION here"""
        name = match.group('name')
        client = self.getClient(name)
        if client:
            #slot = match.group('slot')
            ip = match.group('ip')
            port = match.group('port')
            #something = match.group('something')
            client.ip = ip
            client.port = port
            client.save()
            self.debug('OnPBNewConnection: client updated with %s' % data)
            # This is our first moment where we get a clients IP. Fire this event to accomodate geoIP based plugins like Countryfilter.
            return b3.events.Event(b3.events.EVT_PUNKBUSTER_NEW_CONNECTION, data, client)
        else:
            self.warning('OnPBNewConnection: we\'ve been unable to get the client')

    def OnPBLostConnection(self, match, data):
        """PB notifies us it lost track of a player. This is the only change
        we have to save the ip of clients.
        This event is triggered after the OnPlayerLeave, so normaly the client
        is not connected. Anyway our task here is to save data into db not to 
        connect/disconnect the client.
        
        Part of this code is obsolete since R15, IP is saved to DB on OnPBNewConnection()
        """
        name = match.group('name')
        dict = {
            'slot': match.group('slot'),
            'ip': match.group('ip'),
            'port': match.group('port'),
            'pbuid': match.group('pbuid'),
            'name': name
        }
        """ Code Obsolete since R15:
        client = self.clients.getByCID(dict['name'])
        if not client:
            matchingClients = self.storage.getClientsMatching( {'pbid': match.group('pbuid')} )
            if matchingClients and len(matchingClients) == 0:
                client = matchingClients[0]
        if not client:
            self.error('unable to find client %s. weird' %name )
        else:
            # update client data with PB id and IP
            client.pbid = dict['pbuid']
            client.ip = dict['ip']
            client.save()
        """
        self.verbose('PB lost connection: %s' %dict)
        return b3.events.Event(b3.events.EVT_PUNKBUSTER_LOST_PLAYER, dict)

    def OnPBScheduledTask(self, match, data):
        """We get notified the server ran a PB scheduled task
        Nothing much to do but it can be interresting to have
        this information logged
        """
        slot = match.group('slot')
        task = match.group('task')
        return b3.events.Event(b3.events.EVT_PUNKBUSTER_SCHEDULED_TASK, {'slot': slot, 'task': task})

    def OnPBMasterQuerySent(self, match, data):
        """We get notified that the server sent a ping to the PB masters"""
        #pbmaster = match.group('pbmaster')
        #ip = match.group('ip')
        pass

    def OnPBPlayerGuid(self, match, data):
        """We get notified of a player punkbuster GUID"""
        pbid = match.group('pbid')
        #slot = match.group('slot')
        ip = match.group('ip')
        #port = match.group('port')
        name = match.group('name')
        client = self.getClient(name)
        client.ip = ip
        client.pbid = pbid
        client.save()
        

    def message(self, client, text):
        try:
            if client == None:
                self.say(text)
            elif client.cid == None:
                pass
            else:
                self.write(self.getCommand('message', message=text, cid=client.cid))
        except:
            pass
            
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

    def say(self, msg):
        self.sayqueue.put(msg)
        
    def saybig(self, msg):
        self.saybigqueue.put(msg)


    def kick(self, client, reason='', admin=None, silent=False, *kwargs):
        self.debug('kick reason: [%s]' % reason)
        if isinstance(client, str):
            self.write(self.getCommand('kick', cid=client.cid, reason=reason[:80]))
            return
        elif admin:
            reason = self.getMessage('kicked_by', client.exactName, admin.exactName, reason)
        else:
            reason = self.getMessage('kicked', client.exactName, reason)
        reason = self.stripColors(reason)

        if self.PunkBuster:
            self.PunkBuster.kick(client, 0.5, reason)
        
        self.write(self.getCommand('kick', cid=client.cid, reason=reason[:80]))

        if not silent:
            self.say(reason)
            
            
    def tempban(self, client, reason='', duration=2, admin=None, silent=False, *kwargs):
        duration = b3.functions.time2minutes(duration)

        if isinstance(client, str):
            self.write(self.getCommand('tempban', guid=client.guid, duration=duration*60, reason=reason[:80]))
            return
        elif admin:
            reason = self.getMessage('temp_banned_by', client.exactName, admin.exactName, b3.functions.minutesStr(duration), reason)
        else:
            reason = self.getMessage('temp_banned', client.exactName, b3.functions.minutesStr(duration), reason)
        reason = self.stripColors(reason)

        if self.PunkBuster:
            # punkbuster acts odd if you ban for more than a day
            # tempban for a day here and let b3 re-ban if the player
            # comes back
            if duration > 1440:
                duration = 1440

            self.PunkBuster.kick(client, duration, reason)
        
        self.write(self.getCommand('tempban', guid=client.guid, duration=duration*60, reason=reason[:80]))
        
        
        if not silent:
            self.say(reason)

        self.queueEvent(b3.events.Event(b3.events.EVT_CLIENT_BAN_TEMP, reason, client))

    def unban(self, client, reason='', admin=None, silent=False, *kwargs):
        self.debug('UNBAN: Name: %s, Ip: %s, Guid: %s' %(client.name, client.ip, client.guid))
        if client.ip:
            response = self.write(self.getCommand('unbanByIp', ip=client.ip, reason=reason), needConfirmation=True)
            #self.verbose(response)
            if response == "OK":
                self.verbose('UNBAN: Removed ip (%s) from banlist' %client.ip)
                if admin:
                    admin.message('Unbanned: %s. His last ip (%s) has been removed from banlist.' % (client.exactName, client.ip))    
        
        response = self.write(self.getCommand('unban', guid=client.guid, reason=reason), needConfirmation=True)
        #self.verbose(response)
        if response == "OK":
            self.verbose('UNBAN: Removed guid (%s) from banlist' %client.guid)
            if admin:
                admin.message('Unbanned: Removed %s guid from banlist' % (client.exactName))
        
        if self.PunkBuster:
            self.PunkBuster.unBanGUID(client)
        

    def ban(self, client, reason='', admin=None, silent=False, *kwargs):
        """Permanent ban"""
        self.debug('BAN : client: %s, reason: %s', client, reason)
        if isinstance(client, b3.clients.Client):
            self.write(self.getCommand('ban', guid=client.guid, reason=reason[:80]))
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
            self.write(self.getCommand('ban', cid=client.cid, reason=reason[:80]))
            if admin:
                admin.message('banned: %s (@%s) has been added to banlist'%(client.exactName, client.id))

        if self.PunkBuster:
            self.PunkBuster.banGUID(client, reason)
        
        if not silent:
            self.say(reason)
        
        self.queueEvent(b3.events.Event(b3.events.EVT_CLIENT_BAN, reason, client))
        
        
    def getNextMap(self):
        """Return the name of the next map
        """
        nextLevelIndex = self.getNextMapIndex()
        if nextLevelIndex == -1:
            return 'none'
        levelnames = self.write(('mapList.list',))
        return self.getEasyName(levelnames[nextLevelIndex])
    
    def getNextMapIndex(self):
        [nextLevelIndex] = self.write(('mapList.nextLevelIndex',))
        nextLevelIndex = int(nextLevelIndex)
        if nextLevelIndex == -1:
            return -1
        levelnames = self.write(('mapList.list',))
        if levelnames[nextLevelIndex] == self.getMap():
            nextLevelIndex = (nextLevelIndex+1)%len(levelnames)
        return nextLevelIndex
    
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
        
        else:
            self.warning('unknown level name \'%s\'. Please make sure you have entered a valid mapname' % mapname)
            return mapname
    
    def getMaps(self):
        """Return the map list for the current rotation. (as easy map names)
        This does not return all available maps
        """
        levelnames = self.write(('mapList.list',))
        mapList = []
        for l in levelnames:
            mapList.append(self.getEasyName(l))
        return mapList

    def getMap(self):
        """Return the current level name (not easy map name)"""
        data = self.write(('admin.currentLevel',))
        if not data:
            return None
        return data[0]

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
            

    def getSupportedMaps(self):
        """return a list of supported levels for the current game mod"""
        [currentPlaylist] = self.write(('admin.getPlaylist',))
        supportedMaps = self.write(('admin.supportedMaps', currentPlaylist))
        return supportedMaps

    def getMapsSoundingLike(self, mapname):
        """found matching level names for the given mapname (which can either
        be a level name or map name)
        If no exact match is found, then return close candidates using soundex
        and then LevenshteinDistance algoritms
        """
        supportedMaps = self.getSupportedMaps()
        supportedEasyNames = {}
        for m in supportedMaps:
            supportedEasyNames[self.getEasyName(m)] = m
            
        data = mapname.strip()
        soundex1 = soundex(data)
        #self.debug('soundex %s : %s' % (data, soundex1))
        
        match = []
        if data in supportedMaps:
            match = [data]
        elif data in supportedEasyNames:
            match = [supportedEasyNames[data]]
        else:
            for m in supportedEasyNames:
                s = soundex(m)
                #self.debug('soundex %s : %s' % (m, s))
                if s == soundex1:
                    #self.debug('probable map : %s', m)
                    match.append(supportedEasyNames[m])
        
        if len(match) == 0:
            # suggest closest spellings
            shortmaplist = []
            for m in supportedEasyNames:
                if m.find(data) != -1:
                    shortmaplist.append(m)
            if len(shortmaplist) > 0:
                shortmaplist.sort(key=lambda map: levenshteinDistance(data, string.replace(map.strip())))
                self.debug("shortmaplist sorted by distance : %s" % shortmaplist)
                match = shortmaplist[:3]
            else:
                easyNames = supportedEasyNames.keys()
                easyNames.sort(key=lambda map: levenshteinDistance(data, map.strip()))
                self.debug("maplist sorted by distance : %s" % easyNames)
                match = easyNames[:3]
        return match


        
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
        B3 CID   <--> BFBC2 character name
        B3 GUID  <--> BFBC2 EA_guid
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


    def getPlayerList(self, maxRetries=None):
        """return a dict which keys are cid and values a dict of player properties
        as returned by admin.listPlayers.
        Does not return client objects"""
        data = self.write(('admin.listPlayers', 'all'))
        if not data:
            return {}
        players = {}
        pib = PlayerInfoBlock(data)
        for p in pib:
            players[p['name']] = p
        return players


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
        
        
    def getPlayerScores(self):
        """Ask the BFBC2 for a given client's team
        """
        scores = {}
        try:
            pib = PlayerInfoBlock(self.write(('admin.listPlayers', 'all')))
            for p in pib:
                scores[p['name']] = int(p['score'])
        except:
            self.debug('Unable to retrieve scores from playerlist')
        return scores
    
    def getPlayerPings(self):
        """Ask the BFBC2 for a given client's team
        """
        pings = {}
        try:
            pib = PlayerInfoBlock(self.write(('admin.listPlayers', 'all')))
            for p in pib:
                pings[p['name']] = int(p['ping'])
        except:
            self.debug('Unable to retrieve pings from playerlist')
        return pings
    
    def getServerInfo(self):
        """query server info, update self.game and return query results"""
        data = self.write(('serverInfo',))
        self.game.sv_hostname = data[0]
        self.game.sv_maxclients = int(data[2])
        self.game.gameType = data[3]
        if not self.game.mapName:
            self.game.mapName = data[4]
        self.game.rounds = int(data[5])
        self.game.g_maxrounds = int(data[6])
        return data

    def authorizeClients(self):
        players = self.getPlayerList()
        self.verbose('authorizeClients() = %s' % players)

        for cid, p in players.iteritems():
            sp = self.clients.getByCID(cid)
            if sp:
                # Only set provided data, otherwise use the currently set data
                sp.ip   = p.get('ip', sp.ip)
                sp.pbid = p.get('pbid', sp.pbid)
                sp.guid = p.get('guid', sp.guid)
                sp.data = p
                newTeam = p.get('teamId', None)
                if newTeam is not None:
                    sp.team = self.getTeam(newTeam)
                sp.teamId = int(newTeam)
                sp.auth()

    def getCvar(self, cvarName):
        """Read a server var"""
        if cvarName not in self._gameServerVars:
            self.warning('unknown cvar \'%s\'' % cvarName)
            return None
        
        try:
            words = self.write(('vars.%s' % cvarName,))
        except Bfbc2CommandFailedError, err:
            self.error(err)
            return
        self.debug('Get cvar %s = %s', cvarName, words)
        
        if words:
            if len(words) == 0:
                return b3.cvar.Cvar(cvarName, value=None)
            else:
                return b3.cvar.Cvar(cvarName, value=words[0])
        return None

    def setCvar(self, cvarName, value):
        """Set a server var"""
        if cvarName not in self._gameServerVars:
            self.warning('cannot set unknown cvar \'%s\'' % cvarName)
            return
        self.debug('Set cvar %s = \'%s\'', cvarName, value)
        try:
            self.write(('vars.%s' % cvarName, value))
        except Bfbc2CommandFailedError, err:
            self.error(err)

    def joinPlayers(self):
        self.info('Joining players...')
        plist = self.getPlayerList()
        for cid, p in plist.iteritems():
            client = self.clients.getByCID(cid)
            if client:
                self.debug(' - Joining %s' % cid)
                self.queueEvent(b3.events.Event(b3.events.EVT_CLIENT_JOIN, p, client))
        return None
    
    def sync(self):
        plist = self.getPlayerList()
        mlist = {}

        for cid, c in plist.iteritems():
            client = self.clients.getByCID(cid)
            if client:
                mlist[cid] = client
                newTeam = c.get('teamId', None)
                if newTeam is not None:
                    client.team = self.getTeam(newTeam)
                client.teamId = int(newTeam)
        return mlist

    def getCommand(self, cmd, **kwargs):
        """Return a reference to a loaded command"""
        try:
            cmd = self._commands[cmd]
        except KeyError:
            return None

        preparedcmd = []
        for a in cmd:
            try:
                preparedcmd.append(a % kwargs)
            except KeyError:
                pass
        
        result = tuple(preparedcmd)
        self.debug('getCommand: %s', result)
        return result
    
    def write(self, msg, maxRetries=1, needConfirmation=False):
        """Write a message to Rcon/Console
        Unfortunaltely this has been abused all over B3 
        and B3 plugins to broadcast text :(
        """
        if type(msg) == str:
            # console abuse to broadcast text
            self.say(msg)
        else:
            # Then we got a command
            if self.replay:
                self.bot('Sent rcon message: %s' % msg)
            elif self.output == None:
                pass
            else:
                res = self.output.write(msg, maxRetries=maxRetries, needConfirmation=needConfirmation)
                self.output.flush()
                return res
            
    def getWrap(self, text, length=SAY_LINE_MAX_LENGTH, minWrapLen=SAY_LINE_MAX_LENGTH):
        """Returns a sequence of lines for text that fits within the limits
        """
        if not text:
            return []
    
        maxLength = int(length)
        
        if len(text) <= maxLength:
            return [text]
        else:
            wrappoint = text[:maxLength].rfind(" ")
            if wrappoint == 0:
                wrappoint = maxLength
            lines = [text[:wrappoint]]
            remaining = text[wrappoint:]
            while len(remaining) > 0:
                if len(remaining) <= maxLength:
                    lines.append(remaining)
                    remaining = ""
                else:
                    wrappoint = remaining[:maxLength].rfind(" ")
                    if wrappoint == 0:
                        wrappoint = maxLength
                    lines.append(remaining[0:wrappoint])
                    remaining = remaining[wrappoint:]
            return lines
        

class PlayerInfoBlock:
    """
    help extract player info from a BFBC2 Player Info Block which we obtain
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
        """Represent a BFBC2 Player info block
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


class BanlistContent:
    """
    help extract banlist info from a BFBC2 banList.list response
    
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
    bansData = []
    numOfBans = 0
    
    def __init__(self, data):
        """Represent a BFBC2 banList.list response
        Request: banList.list 
        Response: OK <player ban entries> 
        Response: InvalidArguments 
        Effect: Return list of banned players/IPs/GUIDs. 
        Comment: The list starts with a number telling how many bans the list is holding. 
                 After that, 5 words (Id-type, id, ban-type, time and reason) are received for every ban in the list.
        """
        self.bansData = data[1:]
        self.numOfBans = data[0]
    
    def __len__(self):
        return self.numOfBans
    
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
def bfbc2ClientMessageQueueWorker(self):
    """
    This take a line off the queue and displays it
    then pause for 'message_delay' seconds
    """
    while not self.messagequeue.empty():
        msg = self.messagequeue.get()
        if msg:
            self.console.message(self, msg)
            time.sleep(int(self.console._settings['message_delay']))
b3.clients.Client.messagequeueworker = bfbc2ClientMessageQueueWorker

## override the Client.message() method at runtime
def bfbc2ClientMessageMethod(self, msg):
    if msg and len(msg.strip())>0:
        # do we have a queue?
        if not hasattr(self, 'messagequeue'):
            self.messagequeue = Queue.Queue()
        # fill the queue
        text = self.console.stripColors(self.console.msgPrefix + ' [pm] ' + msg)
        for line in self.console.getWrap(text, self.console._settings['line_length'], self.console._settings['min_wrap_length']):
            self.messagequeue.put(line)
        # create a thread that executes the worker and pushes out the queue
        if not hasattr(self, 'messagehandler') or not self.messagehandler.isAlive():
            self.messagehandler = threading.Thread(target=self.messagequeueworker)
            self.messagehandler.setDaemon(True)
            self.messagehandler.start()
        else:
            self.console.verbose('messagehandler for %s isAlive' %self.name)
b3.clients.Client.message = bfbc2ClientMessageMethod

## add a new method to the Client class
def bfbc2ClientMessageBigQueueWorker(self):
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
b3.clients.Client.messagebigqueueworker = bfbc2ClientMessageBigQueueWorker

## add the Client.messagebig() method at runtime
def bfbc2ClientMessageBigMethod(self, msg):
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
b3.clients.Client.messagebig = bfbc2ClientMessageBigMethod

