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
# 2010/03/16 - 0.6.1 - Courgetet
# * fix getCvar
#
#
# ===== B3 EVENTS AVAILABLE TO PLUGIN DEVELOPPERS USING THIS PARSER ======
# -- standard B3 events  -- 
# EVT_UNKNOWN
# EVT_CLIENT_CONNECT
# EVT_CLIENT_JOIN (only if punkbuter enabled on the server)
# EVT_CLIENT_DISCONNECT
# EVT_CLIENT_SAY
# EVT_CLIENT_KILL
# EVT_CLIENT_TEAMKILL
# EVT_CLIENT_SUICIDE
# EVT_CLIENT_BAN_TEMP
# EVT_CLIENT_BAN
#
# -- BFBC2 specific B3 events --
# EVT_PUNKBUSTER_LOST_PLAYER
# EVT_PUNKBUSTER_SCHEDULED_TASK
# 
# -- B3 events triggered natively by B3 core --
# EVT_CLIENT_NAME_CHANGE
# EVT_CLIENT_TEAM_CHANGE
# EVT_CLIENT_AUTH
#

__author__  = 'Courgette, SpacepiG'
__version__ = '0.6.1'


import sys, time, re, string, traceback
import b3
import b3.events
import b3.parser
from b3.parsers.punkbuster import PunkBuster
import rcon
import b3.cvar

from b3.parsers.bfbc2.bfbc2Connection import *

GAMETYPE_SQDM = 'SQDM' # no team, but up to 4 squad fighting each others
GAMETYPE_CONQUEST = 'CONQUEST'
GAMETYPE_RUSH = 'RUSH'
GAMETYPE_SQRUSH = 'SQRUSH'


#----------------------------------------------------------------------------------------------------------------------------------------------
class Bfbc2Parser(b3.parser.Parser):
    gameName = 'bfbc2'
    privateMsg = True
    OutputClass = rcon.Rcon
    
    _bfbc2EventsListener = None
    _bfbc2Connection = None
    _nbConsecutiveConnFailure = 0

    # BFBC2 does not support color code, so we need this property
    # in order to get stripColors working
    _reColor = re.compile(r'(\^[0-9])') 
    
    _reServerInfo = re.compile(r'^"(?P<sv_hostname>[^"]+)" "(?P<numplayers>\d+)" "(?P<sv_maxclients>\d+)" "(?P<gametype>[^"]+)" "(?P<currentmap>.+)"$')

    _settings = {}
    _settings['line_length'] = 99
    _settings['min_wrap_length'] = 99

    _commands = {}
    _commands['message'] = ('admin.yell', '%(message)s', '%(duration)s', 'player', '%(cid)s')
    _commands['say'] = ('admin.yell', '%(message)s', '%(duration)s', 'all')
    _commands['kick'] = ('admin.kickPlayer', '%(cid)s')
    _commands['ban'] = ('admin.banPlayer', '%(cid)s', 'perm')
    _commands['unban'] = ('admin.unbanPlayer', '%(cid)s')
    _commands['tempban'] = ('admin.banPlayer', '%(cid)s', 'seconds', '%(duration)d')
    _commands['banByIp'] = ('admin.banIP', '%(ip)s', 'perm')
    _commands['unbanByIp'] = ('admin.unbanIP', '%(ip)s')

    
    _eventMap = {
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
        (re.compile(r'^PunkBuster Server: Running PB Scheduled Task \(slot #(?P<slot>\d+)\)\s+(?P<task>.*)$'), 'OnPBScheduledTask'),
        (re.compile(r'^PunkBuster Server: Lost Connection \(slot #(?P<slot>\d+)\) (?P<ip>[^:]+):(?P<port>\d+) (?P<pbuid>[^\s]+)\(-\)\s(?P<name>.+)$'), 'OnPBLostConnection'),
        (re.compile(r'^PunkBuster Server: Master Query Sent to \((?P<pbmaster>[^\s]+)\) (?P<ip>[^:]+)$'), 'OnPBMasterQuerySent'),
        (re.compile(r'^PunkBuster Server: Player GUID Computed (?P<pbid>[0-9a-fA-F]+)\(-\) \(slot #(?P<slot>\d+)\) (?P<ip>[^:]+):(?P<port>\d+)\s(?P<name>.+)$'), 'OnPBPlayerGuid'),
        (re.compile(r'^PunkBuster Server: New Connection \(slot #(?P<slot>\d+)\) (?P<ip>[^:]+):(?P<port>\d+) \[(?P<something>[^\s]+)\]\s"(?P<name>.+)".*$'), 'OnPBNewConnection')
     )

    PunkBuster = None

    def startup(self):
        
        # add specific events
        self.Events.createEvent('EVT_PUNKBUSTER_SCHEDULED_TASK', 'PunkBuster scheduled task')
        self.Events.createEvent('EVT_PUNKBUSTER_LOST_PLAYER', 'PunkBuster client connection lost')
        
        if self.config.has_option('server', 'punkbuster') and self.config.getboolean('server', 'punkbuster'):
            self.PunkBuster = PunkBuster(self)
            
        version = self.output.write('version')
        self.info('BFBC2 server version : %s' % version)
        if version[0] != 'BFBC2':
            raise Exception("the bfbc2 parser can only work with BattleField Bad Company 2")
        
        self.getServerVars()
        
        self.info('connecting all players...')
        plist = self.getPlayerList()
        for cid, c in plist.iteritems():
            client = self.getClient(cid)
            if client:
                self.debug('Joining %s' % client.name)
                self.queueEvent(b3.events.Event(b3.events.EVT_CLIENT_JOIN, None, client))
        
        # request pbid of connected players
        self.write(('punkBuster.pb_sv_command', 'pb_sv_list'))
        updatethread = threading.Thread(target=self.updatePlayers)
        updatethread.start()
           
    def updatePlayers(self):
        """Update player list to detect team changes"""
        while self.working:
            self.debug('Updating Player List')
            self.sync()
            time.sleep(5)
        self.debug('End Updating Player List')

    def run(self):
        """Main worker thread for B3"""
        self.bot('Start listening ...')
        self.screen.write('Startup Complete : Let\'s get to work!\n\n')
        self.screen.write('(Please check %s in the B3 root directory for more detailed info)\n' % self.config.getpath('b3', 'logfile'))
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
                        self._bfbc2Connection = Bfbc2Connection(self._rconIp, self._rconPort, self._rconPassword)

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
                                self.debug(e)
                                nbConsecutiveReadFailure += 1
                                if nbConsecutiveReadFailure > 5:
                                    raise e
                except Bfbc2Exception, e:
                    self.debug(e)
                    self._nbConsecutiveConnFailure += 1
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
            self.input.close()
            self.output.close()

            if self.exitcode:
                sys.exit(self.exitcode)

    def routeBfbc2Packet(self, packet):
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
            self.queueEvent(b3.events.Event(b3.events.EVT_UNKNOWN, data))



    def getPlayerList(self, maxRetries=None):
        if self.PunkBuster:
            return self.PunkBuster.getPlayerList()
        else:
            data = self.write(('admin.listPlayers', 'all'))
            if not data:
                return {}

            players = {}
            def group(s, n): return [s[i:i+n] for i in xrange(0, len(s), n)]
            for clantag, name, squadId, teamId  in group(data,4):
                #self.debug('player: %s %s %s %s' % (clantag, name, squadId, teamId))
                players[name] = {'clantag':clantag, 'name':"%s%s"% (clantag, name), 'guid':name, 'squadId':squadId, 'teamId':self.getTeam(teamId)}
        return players

    def getServerVars(self):
        """Update the game property from server fresh data"""
        
        self.game.is3dSpotting = self.getCvar('3dSpotting').getBoolean()
        self.game.bannerUrl = self.getCvar('bannerUrl').getString()
        self.game.crossHair = self.getCvar('crossHair').getBoolean()
        self.game.currentPlayerLimit = self.getCvar('currentPlayerLimit').getInt()
        self.game.friendlyFire = self.getCvar('friendlyFire').getBoolean()
        self.game.hardCore = self.getCvar('hardCore').getBoolean()
        self.game.killCam = self.getCvar('killCam').getBoolean()
        self.game.maxPlayerLimit = self.getCvar('maxPlayerLimit').getInt()
        self.game.miniMap = self.getCvar('miniMap').getBoolean()
        self.game.miniMapSpotting = self.getCvar('miniMapSpotting').getBoolean()
        self.game.playerLimit = self.getCvar('playerLimit').getInt()
        self.game.punkBuster = self.getCvar('punkBuster').getBoolean()
        self.game.rankLimit = self.getCvar('rankLimit').getInt()
        self.game.ranked = self.getCvar('ranked').getBoolean()
        self.game.serverDescription = self.getCvar('serverDescription').getString()
        self.game.teamBalance = self.getCvar('teamBalance').getBoolean()
        self.game.thirdPersonVehicleCameras = self.getCvar('thirdPersonVehicleCameras').getBoolean()
        

    def getMap(self):
        data = self.write(('serverInfo',))
        if not data:
            return None
        return data[4]
    


    #----------------------------------
    

    def OnPlayerChat(self, action, data):
        #['envex', 'gg']
        if not len(data) == 2:
            return None
        client = self.getClient(data[0])
        return b3.events.Event(b3.events.EVT_CLIENT_SAY, data[1], client)

    def OnPlayerLeave(self, action, data):
        #player.onLeave: ['GunnDawg']
        client = self.getClient(data[0])
        if client: 
            client.disconnect() # this triggers the EVT_CLIENT_DISCONNECT event
        return None

    def OnPlayerJoin(self, action, data):
        #player.onJoin: ['OrasiK']
        name = data[0]
        client = self.getClient(name)
        return b3.events.Event(b3.events.EVT_CLIENT_CONNECT, data, client)

    def OnPlayerKill(self, action, data):
        #player.onKill: ['Juxta', '6blBaJlblu']
        if not len(data) == 2:
            return None
        attacker = self.getClient(data[0])
        if not attacker:
            self.debug('No attacker')
            return None

        victim = self.getClient(data[1])
        if not victim:
            self.debug('No victim')
            return None
        
        attackerteam = self.getPlayerTeam(attacker.name)
        attacker.team = attackerteam

        if attacker != victim:
            victimteam = self.getPlayerTeam(victim.name)
            victim.team = victimteam
        
        if victim == attacker:
            return b3.events.Event(b3.events.EVT_CLIENT_SUICIDE, (100, 1, 1), attacker, victim)
        elif attacker.team == victim.team and attacker.team != b3.TEAM_UNKNOWN and attacker.team != b3.TEAM_SPEC:
            return b3.events.Event(b3.events.EVT_CLIENT_TEAMKILL, (100, None, None), attacker, victim)
        else:
            return b3.events.Event(b3.events.EVT_CLIENT_KILL, (100, None, None), attacker, victim)
        

    def OnPunkbusterMessage(self, action, data):
        """handes all punkbuster related events and 
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
                
    def OnPBNewConnection(self, match, data):
        """PunkBuster tells us a new player identified. The player is
        normally already connected"""
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
        else:
            self.warning('OnPBNewConnection: we\'ve been unable to get the client')
        return b3.events.Event(b3.events.EVT_CLIENT_JOIN, data, client)

    def OnPBLostConnection(self, match, data):
        """PB notifies us it lost track of a player. This is the only change
        we have to save the PunkBuster id of clients.
        This event is triggered after the OnPlayerLeave, so normaly the client
        is not connected. Anyway our task here is to save PBid not to 
        connect/disconnect the client
        """
        name = match.group('name')
        dict = {
            'slot': match.group('slot'),
            'ip': match.group('ip'),
            'port': match.group('port'),
            'pbuid': match.group('pbuid'),
            'name': name
        }
        client = self.clients.getByCID(dict['name'])
        if not client:
            tmpclient = b3.clients.Client(console=self, id=-1, guid=name)
            client = self.storage.getClient(tmpclient)
        if not client:
            self.error('unable to find client %s. weird')
        else:
            # update client data with PB id and IP
            client.pbid = dict['pbuid']
            client.ip = dict['ip']
            client.save()
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
                lines = []
                text = self.stripColors(self.msgPrefix + ' [pm] ' + text)
                for line in self.getWrap(text, self._settings['line_length'], self._settings['min_wrap_length']):
                    lines.append(self.getCommand('message', cid=client.cid, message=line, duration=2300))

                self.writelines(lines)
        except:
            pass

    def say(self, msg):
        lines = []
        msg = self.stripColors(self.msgPrefix + ' ' + msg)
        for line in self.getWrap(msg, self._settings['line_length'], self._settings['min_wrap_length']):
            lines.append(self.getCommand('say', message=line, duration=2300))

        if len(lines):        
            self.writelines(lines)

    def kick(self, client, reason='', admin=None, silent=False, *kwargs):
        if isinstance(client, str):
            self.write(self.getCommand('kick', cid=client, reason=reason))
            return
        elif admin:
            reason = self.getMessage('kicked_by', client.exactName, admin.exactName, reason)
        else:
            reason = self.getMessage('kicked', client.exactName, reason)

        if self.PunkBuster:
            self.PunkBuster.kick(client, 0.5, reason)
        else:
            self.write(self.getCommand('kick', cid=client.cid, reason=reason))

        if not silent:
            self.say(reason)
            
            
    def tempban(self, client, reason='', duration=2, admin=None, silent=False, *kwargs):
        duration = b3.functions.time2minutes(duration)

        if isinstance(client, str):
            self.write(self.getCommand('tempban', cid=client, duration=duration*60, reason=reason))
            return
        elif admin:
            reason = self.getMessage('temp_banned_by', client.exactName, admin.exactName, b3.functions.minutesStr(duration), reason)
        else:
            reason = self.getMessage('temp_banned', client.exactName, b3.functions.minutesStr(duration), reason)

        if self.PunkBuster:
            # punkbuster acts odd if you ban for more than a day
            # tempban for a day here and let b3 re-ban if the player
            # comes back
            if duration > 1440:
                duration = 1440

            self.PunkBuster.kick(client, duration, reason)
        else:
            self.write(self.getCommand('tempban', cid=client.cid, duration=duration*60, reason=reason))

        if not silent:
            self.say(reason)

        self.queueEvent(b3.events.Event(b3.events.EVT_CLIENT_BAN_TEMP, reason, client))

    def unban(self, client, reason='', admin=None, silent=False, *kwargs):
        if client.ip is not None:
            self.write(self.getCommand('unbanByIp', ip=client.ip, reason=reason))
            if admin:
                admin.message('Unbanned: %s. His last ip (^1%s^7) has been removed from banlist.' % (client.exactName, client.ip))    
        
        self.write(self.getCommand('unban', cid=client.guid, reason=reason))
        if admin:
            admin.message('Unbanned: %s' % (client.exactName))
        

    def ban(self, client, reason='', admin=None, silent=False, *kwargs):
        """Permanent ban"""
        self.debug('BAN : client: %s, reason: %s', client, reason)
        if isinstance(client, b3.clients.Client):
            self.write(self.getCommand('ban', cid=client.guid, reason=reason))
            return

        if admin:
            reason = self.getMessage('banned_by', client.exactName, admin.exactName, reason)
        else:
            reason = self.getMessage('banned', client.exactName, reason)

        if client.cid is None:
            # ban by ip, this happens when we !permban @xx a player that is not connected
            self.debug('EFFECTIVE BAN : %s',self.getCommand('banByIp', ip=client.ip, reason=reason))
            self.write(self.getCommand('banByIp', ip=client.ip, reason=reason))
            if admin:
                admin.message('banned: %s (@%s). His last ip (%s) has been added to banlist'%(client.exactName, client.id, client.ip))
        else:
            # ban by cid
            self.debug('EFFECTIVE BAN : %s',self.getCommand('ban', cid=client.guid, reason=reason))
            self.write(self.getCommand('ban', cid=client.guid, reason=reason))
            if admin:
                admin.message('banned: %s (@%s) has been added to banlist'%(client.exactName, client.id))

        if not silent:
            self.say(reason)
        
        self.queueEvent(b3.events.Event(b3.events.EVT_CLIENT_BAN, reason, client))
        
        
    def getNextMap(self):
        """Return the name of the next map
        """
        currentMap = self.write(('admin.currentLevel',))
        data = self.write(('mapList.list',))
        for index in range(0,len(data)): 
            if data[index] == currentMap[0]:
                index = ((index +1) % len(data))
                nextMap = self.getEasyName(data[index])
                self.debug('currentmap: %s ' % (nextMap)) 
                return nextMap  
        return None 
    
    def getEasyName(self, mapname):
        """ Change levelname to real name """
        if mapname == 'Levels/MP_001':
            return ('Panama Canal')
            
        elif mapname == 'Levels/MP_002':
            return ('Valparaiso')

        elif mapname == 'Levels/MP_003':
            return ('Laguna Alta')

        elif mapname == 'Levels/MP_004':
            return ('Isla Inocentes')

        elif mapname == 'Levels/MP_005':
            return ('Atacama Desert')

        elif mapname == 'Levels/MP_006':
            return ('Arica Harbor')

        elif mapname == 'Levels/MP_007':
            return ('White Pass')

        elif mapname == 'Levels/MP_008':
            return ('Nelson Bay')

        elif mapname == 'Levels/MP_009':
            return ('Laguna Preza')

        elif mapname == 'Levels/MP_012':
            return ('Port Valdez')

        return None
    
    def getMaps(self):
        """Return the map list
        TODO"""
        data = self.write(('mapList.list',))
        mapList = []
        for index in range(0,len(data)):
            mapList[index] = self.getEasyName(data[index])
        return mapList 
    
        
    def getTeam(self, team):
        team = int(team)
        if team == 1:
            return b3.TEAM_RED
        elif team == 2:
            return b3.TEAM_BLUE
        elif team == 3:
            return b3.TEAM_SPEC
        else:
            return b3.TEAM_UNKNOWN
        
        
    def getClient(self, name):
        """Get a connected client from storage or create it
        In BFBC2, clients are identified by their name, so we
        have to trick B3 giving the name for CID and GUID fields
        """
        client = self.clients.getByCID(name)
        if not client:
            clantag = ''
            squadId = -1
            teamId = b3.TEAM_UNKNOWN
            data = self.write(('admin.listPlayers', 'player', name))
            if data and len(data) == 4:
                clantag, name, squadId, teamId = data
                self.debug('player: %s %s %s %s' % (clantag, name, squadId, teamId))
                if clantag is not None and len(clantag.strip()) > 0:
                    clantag += ' '
                self.clients.newClient(name, guid=name, name="%s%s" % (clantag, name), team=self.getTeam(teamId))
        client = self.clients.getByCID(name)
        return client

        
    def getPlayerTeam(self, name):
        """Ask the BFBC2 for a given client's team
        """
        teamId = b3.TEAM_UNKNOWN
        if name:
            data = self.write(('admin.listPlayers', 'player', name))
            if data and len(data) == 4:
                teamId = self.getTeam(data[3])
        return teamId
        
    def getPlayerScores(self):
        """I don't know what we could put here...
        maybe we could send the number of kills if the mstat plugin is enabled"""
        return None

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
                sp.team = p.get('teamId', sp.team)
                sp.auth()

    def getCvar(self, cvarName):
        if cvarName not in self._gameServerVars:
            self.warning('unknown cvar \'%s\'' % cvarName)
            return None
        
        try:
            words = self.write(('vars.%s' % cvarName,))
        except Bfbc2CommandFailedError, err:
            self.error(err)
            return
        self.debug('Get cvar %s = %s', cvarName, words)
        
        if words and len(words) == 1:
            return b3.cvar.Cvar(cvarName, value=words[0])
        return None

    def setCvar(self, cvarName, value):
        if cvarName not in self._gameServerVars:
            self.warning('cannot set unknown cvar \'%s\'' % cvarName)
            return
        self.debug('Set cvar %s = \'%s\'', cvarName, value)
        try:
            self.write(('vars.%s' % cvarName, value))
        except Bfbc2CommandFailedError, err:
            self.error(err)

    
    def sync(self):
        plist = self.getPlayerList()
        mlist = {}

        for name, c in plist.iteritems():
            client = self.clients.getByName(name)
            if client:
                mlist[name] = client
                client.team = c.get('teamId', client.team)
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
    
    def write(self, msg, maxRetries=1):
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
                res = self.output.write(msg, maxRetries=maxRetries)
                self.output.flush()
                return res
            
    def getWrap(self, text, length=100, minWrapLen=100):
        """Returns a sequence of lines for text that fits within the limits
        """
        if not text:
            return []
    
        length = int(length)
        
        if len(text) <= minWrapLen:
            return [text]
        else:
            lines = [text[0:length]]
            remaining = text[length:]
            while len(remaining) > 0:
                lines.append(">%s" % remaining[0:length-1])
                remaining = remaining[length-1:]
            return lines
        
