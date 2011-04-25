#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
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
# CHANGELOG
#
# 2011-03-30 : 0.1
# * first alpha test
# 2011-03-31 : 0.2
# * remove try: catch: around the asyncore loop
# 2011-04-08 : 0.3
# * do not create client without guid as name are not reliable alone
# 2011-04-08 : 0.4
# * refactor getPlayerList() and retrievePlayerList() with cron interval
# 2011-04-08 : 0.5
# * fix the "empty name in database bug" reported by Platanos
# 2011-04-09 : 0.6
# * unban using UID if available
# 2011-04-16 : 0.6.1
# * getPlayerScores do not raise an exception when client has no kills attribute
# 2011-04-17 : 0.7.0
# * implements sync()
# * fix bug with UID '0'
# 2011-04-18 : 0.7.1
# * clear clients list on HF connection loss
# 2011-04-18 : 0.7.2
# * remove color codes before sending each line in say, saybig and message
# 2011-04-25 : 0.8.0
# * read game server info through Source Query Protocol

__author__  = 'Courgette, xlr8or, Freelander, 82ndab-Bravo17'
__version__ = '0.8.0'

from b3.parsers.homefront.protocol import MessageType, ChannelType
import sys
import string
import re
import time
import asyncore
import b3
import b3.parser
import b3.cron
import os
import rcon
import protocol
from ftplib import FTP
import ftplib
from b3 import functions
from b3.lib.SourceLib import SourceQuery


class HomefrontParser(b3.parser.Parser):
    '''
    The HomeFront B3 parser class
    '''
    gameName = "homefront"
    OutputClass = rcon.Rcon
    PunkBuster = None 
    _serverConnection = None

    # homefront engine does not support color code, so we need this property
    # in order to get stripColors working
    _reColor = re.compile(r'(\^[0-9])')
    # Map related
    _currentmap = None
    _ini_file = None
    _currentmap = None
    _mapline = re.compile(r'^(?P<start>Map=)(?P<mapname>[^\?]+)\?(?P<sep>GameMode=)(?P<gamemode>.*)$', re.IGNORECASE)
    ftpconfig = None
    _ftplib_debug_level = 0 # 0: no debug, 1: normal debug, 2: extended debug
    _connectionTimeout = 30
    maplist = None
    mapgamelist = None
    _playerlistInterval = 15
    _server_banlist = {}

    _commands = {}
    _commands['message'] = ('say %(prefix)s [%(name)s] %(message)s')
    _commands['say'] = ('say %(prefix)s %(message)s')
    _commands['saybig'] = ('admin bigsay %(prefix)s %(message)s')
    _commands['kick'] = ('admin kick "%(name)s"')
    _commands['ban'] = ('admin kickban "%(name)s" "%(admin)s" "[B3] %(reason)s"')
    _commands['unban'] = ('admin unban "%(name)s"')
    _commands['tempban'] = ('admin kick "%(name)s"')
    _commands['maprotate'] = ('admin nextmap')
    
    _settings = {'line_length': 90, 
                 'min_wrap_length': 100}
    
    prefix = '%s: '
    
    def startup(self):
        self.debug("startup()")
        
        # create the 'Server' client
        self.clients.newClient('Server', guid='Server', name='Server', hide=True, pbid='Server', team=b3.TEAM_UNKNOWN)

        if self.config.has_option('server','inifile'):
            # open ini file
            ini_file = self.config.get('server','inifile')
            if ini_file[0:6] == 'ftp://':
                    self.ftpconfig = functions.splitDSN(ini_file)
                    self._ini_file = 'ftp'
                    self.bot('ftp supported')
            elif ini_file[0:7] == 'sftp://':
                self.bot('sftp currently not supported')
            else:
                self.bot('Getting configs from %s', ini_file)
                f = self.config.getpath('server', 'inifile')
                if os.path.isfile(f):
                    self.input  = file(f, 'r')
                    self._ini_file = f

        if not self._ini_file:
            self.debug('Incorrect ini file or no ini file specified, map commands other than nextmap not available')
            
        # start crontab to trigger playerlist events
        self.cron + b3.cron.CronTab(self.retrievePlayerList, second='*/%s' % self._playerlistInterval)

        # add specific events
        self.Events.createEvent('EVT_CLIENT_SQUAD_SAY', 'Squad Say')
        self.Events.createEvent('EVT_SERVER_SAY', 'Server Chatter')
        self.Events.createEvent('EVT_CLIENT_CLAN_CHANGE', 'Client Clan Change')
        #self.Events.createEvent('EVT_CLIENT_SQUAD_CHANGE', 'Client Squad Change')
                
        ## read game server info and store as much of it in self.game wich
        ## is an instance of the b3.game.Game class
        sq = SourceQuery.SourceQuery(self._publicIp, self._port, timeout=10)
        try:
            serverinfo = sq.info()
            self.debug("server info : %r", serverinfo)
            if 'map' in serverinfo:
                self.game.mapName = serverinfo['map'].lower()
            if 'steamid' in serverinfo:
                self.game.steamid = serverinfo['steamid']
            if 'hostname' in serverinfo:
                self.game.sv_hostname = serverinfo['hostname']
            if 'maxplayers' in serverinfo:
                self.game.sv_maxclients = serverinfo['maxplayers']
        except Exception, err:
            self.exception(err)


    
    
    def routePacket(self, packet):
        if packet is None:
            self.warning('cannot route empty packet')
        if packet.message == MessageType.SERVER_TRANSMISSION \
            and packet.data == "PONG":
            self.verbose2("%s" % packet)
        else:
            self.console("%s" % packet)
        
        if packet.message == MessageType.SERVER_TRANSMISSION:
            if packet.channel == ChannelType.SERVER:
                if packet.data == "PONG":
                    return
                match = re.search(r"^(?P<event>[A-Z ]+): (?P<data>.*)$", packet.data)
                if match:
                    func = 'onServer%s' % (string.capitalize(match.group('event').replace(' ','_')))
                    data = match.group('data')
                    #self.debug("-==== FUNC!!: " + func)
                    
                    if hasattr(self, func):
                        #self.debug('routing ----> %s' % func)
                        func = getattr(self, func)
                        event = func(data)
                        if event:
                            self.queueEvent(event)
                    else:
                        self.warning('TODO handle: %s(%s)' % (func, data))
                else:
                    self.warning('TODO handle packet : %s' % packet)
                    self.queueEvent(self.getEvent('EVT_UNKNOWN', packet))
                    
            elif packet.channel == ChannelType.CHATTER:
                if packet.data.startswith('BROADCAST:'):
                    data = packet.data[10:]
                    func = 'onChatterBroadcast'
                    if hasattr(self, func):
                        #self.debug('routing ----> %s' % func)
                        func = getattr(self, func)
                        event = func(data)
                        if event:
                            self.queueEvent(event)
                    else:
                        self.warning('TODO handle: %s(%s)' % (func, data))
                else:
                    data = packet.data
                    func = 'onChatter'
                    if hasattr(self, func):
                        #self.debug('routing ----> %s' % func)
                        func = getattr(self, func)
                        event = func(data)
                        if event:
                            self.queueEvent(event)
                    else:
                        self.warning('TODO handle: %s(%s)' % (func, data))
            else:
                self.warning("Unhandled channel type : %s" % packet.getChannelTypeAsStr())
        else:
            self.warning("Unhandled message type : %s" % packet.getMessageTypeAsStr())
        
           
    def run(self):
        """Main worker thread for B3"""
        self.bot('Start listening ...')
        self.screen.write('Startup Complete : B3 is running! Let\'s get to work!\n\n')
        self.screen.write('(If you run into problems, check %s for detailed log info)\n' % self.config.getpath('b3', 'logfile'))
        #self.screen.flush()

        self.updateDocumentation()

        while self.working:
            """
            While we are working, connect to the Homefront server
            """
            if self._paused:
                if self._pauseNotice == False:
                    self.bot('PAUSED - Not parsing any lines, B3 will be out of sync.')
                    self._pauseNotice = True
            else:
                if self._serverConnection is None:
                    self.bot('Connecting to Homefront server ...')
                    self._serverConnection = protocol.Client(self, self._rconIp, self._rconPort, self._rconPassword, keepalive=True)
                    
                    # hook on handle_close to protocol.Client
                    self._original_connection_handle_close_method = self._serverConnection.handle_close
                    self._serverConnection.handle_close = self._handle_connection_close
                    
                    # listen for incoming HF packets
                    self._serverConnection.add_listener(self.routePacket)
                    
                    # setup Rcon
                    self.output.set_homefront_client(self._serverConnection)
                
                self._nbConsecutiveConnFailure = 0
                
                while self.working and not self._paused \
                and (self._serverConnection.connected or not self._serverConnection.authed):
                    #self.verbose2("\t%s" % (time.time() - self._serverConnection.last_pong_time))
                    if time.time() - self._serverConnection.last_pong_time > 6 \
                    and self._serverConnection.last_ping_time < self._serverConnection.last_pong_time:
                        self._serverConnection.ping()
                    asyncore.loop(timeout=3, use_poll=True, count=1)
        self.bot('Stop listening.')

        if self.exiting.acquire(1):
            self._serverConnection.close()
            if self.exitcode:
                sys.exit(self.exitcode)


    def _handle_connection_close(self):
        if len(self.clients.getList()): 
            self.debug("clearing player list")
            self.clients.empty()
        self._original_connection_handle_close_method()


    # ================================================
    # handle Game events.
    #
    # those methods are called by routePacket() and 
    # may return a B3 Event object which would then
    # be queued
    # ================================================
       
    def onServerHello(self, data):
        ## [int: Version]
        self.bot("HF server (v %s) says hello to B3" % data)

            
    def onServerAuth(self, data):
        ## [boolean: Result]
        if data == 'true':
            self.bot("B3 correctly authenticated on game server")
            self.clients.sync()
            self.retrieveBanList()
        else:
            self.warning("B3 failed to authenticate on game server (%s)" % data)


    def onServerLogin(self, data):
        # [string: Name]
        # (onServerLogin also occurs after a mapchange...)
        # we need this event for xlrstats (counting playerrounds)
        client = self.getClient(data)
        if client:
            self.queueEvent(self.getEvent('EVT_CLIENT_JOIN', None, client))

    
    def onServerUid(self, data):
        # [string: Name] [string: UID]
        # example : courgette 1100012402D1245
        match = re.search(r"^(?P<name>.+) (?P<uid>.*)$", data)
        if not match:
            self.error("could not get UID in [%s]" % data)
            return None
        if match.group('uid') == '00':
            self.info("banned player connecting")
            return
        client = self.clients.getByGUID(match.group('uid'))
        if client is None:
            name = match.group('name')
            client = self.clients.newClient(name, guid=match.group('uid'), name=name, team=b3.TEAM_UNKNOWN)
            client.last_update_time = time.time()
    
    def onServerLogout(self, data):
        ## [string: Name]
        self.debug('%s disconnected' % data)
        client = self.clients.getByCID(data)
        if client:
            client.disconnect()
    
    def onServerTeam_change(self, data):
        # [string: Name] [int: Team ID]
        self.debug('onServerTeam_change: %s' % data)
        match = re.search(r"^(?P<name>.+) (?P<team>.*)$", data)
        if not match:
            self.error('onServerTeam_change failed match')
            return
        client = self.getClient(match.group('name'))
        if client is None:
            self.debug("Could not find client")
            return
        #This next line will also raise the EVT_CLIENT_TEAM_CHANGE event
        client.team = self.getTeam(match.group('team'))

    def onServerClan_change(self, data):
        # [string: Name] [string: Clan Name]
        match = re.search(r"^(?P<name>.+) (?P<clan>.*)$", data)
        if not match:
            self.error('onServerTeam_change failed match')
            return
        client = self.getClient(match.group('name'))
        if client is None:
            self.debug("Could not find client")
            return
        client.clan = match.group('clan')
        return self.getEvent('EVT_CLIENT_CLAN_CHANGE', client.clan, client)

    def onServerKill(self, data):
        # [string: Killer Name] [string: DamageType] [string: Victim Name]
        # kill example: courgette EXP_Frag Freelander
        # suicide example#1: Freelander Suicided Freelander (triggers when player leaves the server)
        # suicide example#2: Freelander EXP_Frag Freelander
        match = re.search(r"^(?P<data>(?P<aname>[^;]+)\s+(?P<aweap>[A-z0-9_-]+)\s+(?P<vname>[^;]+))$", data)
        if not match:
            self.error("Can't parse kill line: %s" % data)
            return
        else:
            attacker = self.getClient(match.group('aname'))
            if not attacker:
                self.debug('No attacker!')
                return

            victim = self.getClient(match.group('vname'))
            if not victim:
                self.debug('No victim!')
                return

            weapon = match.group('aweap')
            if not weapon:
                self.debug('No weapon')
                return

            if not hasattr(victim, 'hitloc'):
                victim.hitloc = 'body'

        event = 'EVT_CLIENT_KILL'

        if weapon == 'Suicided' or attacker == victim:
            event = 'EVT_CLIENT_SUICIDE'
            self.verbose('%s suicided' % attacker.name)
        elif attacker.team != b3.TEAM_UNKNOWN and attacker.team == victim.team:
            event = 'EVT_CLIENT_KILL_TEAM'
            self.verbose('Team kill, attacker: %s, victim: %s' % (attacker.name, victim.name))
        else:
            self.verbose('%s killed %s using %s' % (attacker.name, victim.name, weapon))

        return self.getEvent(event, (100, weapon, victim.hitloc), attacker, victim)

    def onServerRound_over(self, data):
        ## [int: Team ID]
        match = re.search(r"^(?P<team>.*)$", data)
        if not match:
            self.error('onServerRound_over failed match')
            return

        # teamid = The ID of the winning team
        # 0 = KPA
        # 1 = USA
        # 2 = TIE
        teamid = match.group('team')

        self.verbose('onServerRound_over: %s, winning team id: %s' % (data, teamid)) 
        return self.getEvent('EVT_GAME_ROUND_END', teamid)

    def onServerChange_level(self, data):
        ## [string: Map]
        ## example : fl-harbor
        match = re.search(r"^(?P<level>.*)$", data)
        if not match:
            self.error('onServerChange_level failed match')
            return
        
        # resync players to get rid of eventual 'phantom' players
        self.clients.sync()

        levelname = match.group('level')
        self.verbose('onServerChange_level, levelname: %s' % levelname)
        self._currentmap = levelname.lower()
        self.game.mapName = levelname.lower()
        return self.getEvent('EVT_GAME_ROUND_START', levelname)

    def onChatterBroadcast(self, data):
        # [string: Name] [string: Context]: [string: Text]
        # example : courgette says: !register
        match = re.search(r"^(?P<name>.+) (\((?P<type>team|squad)\))?says: (?P<text>.*)$", data)
        if not match:
            self.error("could not understand broadcast format [%s]" % data)
            raise 
        else:
            type = match.group('type')
            name = match.group('name')
            text = match.group('text')
            client = self.getClient(name)
            if client is None:
                self.debug("Could not find client")
                return
            if type == 'team':
                return self.getEvent('EVT_CLIENT_TEAM_SAY', text, client)
            elif type == 'squad':
                return self.getEvent('EVT_CLIENT_SQUAD_SAY', text, client)
            else:
                return self.getEvent('EVT_CLIENT_SAY', text, client)
    
    def onChatter(self, data):
        """\
        Everything that is said by the server or a player is sent over this channel.
        All onChatterBroadcast messages also reappear here.
        """
        # [string: Text]
        self.verbose2('Recieved Chatter: %s' % data )
        return self.getEvent('EVT_SERVER_SAY', data)

    def onServerBan_remove(self, data):
        self.write(self.getCommand('saybig',  prefix='', message="%s unbanned" % data))
        # update banlist
        self.retrieveBanList()
    
    def onServerBan_added(self, data):
        self.write(self.getCommand('saybig',  prefix='', message="%s banned" % data))
        # update banlist
        self.retrieveBanList()

    def onServerPlayer(self, data):
        # [int: Team] [string: Clan] [string: Name] [int: Kills] [int: Deaths]
        match = re.search(r"^(?P<data>(?P<uid>[0-9]+) (?P<team>[0-9]) (?P<clan>.*) (?P<name>[^ ]+) (?P<kills>[0-9]+) (?P<deaths>[0-9]+))$", data)
        if not match:
            self.error("onServerPlayer failed match")
            return
        
        uid = match.group('uid')
        
        if uid == '0':
            # connecting player with no UID resolved yet --> ignore
            return
        
        if len(uid) != 17:
            self.warning(u"weird UID : [%s]" % uid)
        
        # try to get the client by guid
        client = self.clients.getByGUID(uid)
        if not client:
            client = self.clients.newClient(match.group('name'), guid=uid, name=match.group('name'), team=b3.TEAM_UNKNOWN)
        # update client data
        client.name = match.group('name')
        client.team = self.getTeam(match.group('team'))
        client.clan = match.group('clan')
        client.kills = match.group('kills')
        client.deaths = match.group('deaths')
        client.last_update_time = time.time() ## save the timestamp so sync() can use that info
        self.verbose2('onServerPlayer: name: %s, clan: %s, team: %s, kills: %s, deaths: %s' %( client.name, client.clan, client.team, client.kills, client.deaths ))

    def onServerBan_item(self, data):
        # [string: Name] [string: Uid]
        match = re.match(r"^(?P<data>(?P<name>[^ ]+) (?P<uid>[0-9]+))$", data)
        if not match:
            self.error('onServerBan_item failed match')
            return

        name = match.group('name')
        guid = match.group('uid')

        self._server_banlist[guid] = name

    # =======================================
    # implement parser interface
    # =======================================

    def getPlayerList(self):
        """\
        Returns a list of client objects
        """
        clients = self.clients.getList()
        return clients

    def authorizeClients(self):
        """\
        For all connected players, fill the client object with properties allowing to find 
        the user in the database (usualy guid, or punkbuster id, ip) and call the 
        Client.auth() method 
        """
        ## in Homefront, there is no synchronous way to obtain a player guid
        ## the onServerUid event will be the one calling Client.auth()
        pass
    
    def sync(self):
        """\
        For all connected players returned by self.getPlayerList(), get the matching Client
        object from self.clients (with self.clients.getByCID(cid) or similar methods) and
        look for inconsistencies. If required call the client.disconnect() method to remove
        a client from self.clients.
        This is mainly useful for games where clients are identified by the slot number they
        occupy. On map change, a player A on slot 1 can leave making room for player B who
        connects on slot 1.
        """
        ## we are unable to get the exact list of connected players in a synchronous
        ## way. So we use .last_update_time timestamp to detect player we still
        ## have in self.clients but that are no longer on the game server
        self.debug("synchronizing clients")
        mlist = {}
        now = time.time()
        for client in self.clients.getList():
            howlongago = now - client.last_update_time
            self.debug(u"%s last seen %d seconds ago" % (client, howlongago))
            if howlongago < (self._playerlistInterval * 2):
                mlist[client.cid] = client
            else:
                self.info(u"%s last update is too old" % client)
                client.disconnect()
        return mlist
        
    
    def say(self, msg):
        """\
        broadcast a message to all players
        """
        msg = self.stripColors(msg)
        for line in self.getWrap(msg, self._settings['line_length'], self._settings['min_wrap_length']):
            line = self.stripColors(line)
            self.write(self.getCommand('say',  prefix=self.msgPrefix, message=line))

    def saybig(self, msg):
        """\
        broadcast a message to all players in a way that will catch their attention.
        """
        msg = self.stripColors(msg)
        for line in self.getWrap(msg, self._settings['line_length'], self._settings['min_wrap_length']):
            line = self.stripColors(line)
            self.write(self.getCommand('saybig',  prefix=self.msgPrefix, message=line))

    ## @todo Change private messages when the rcon protocol will allow us to
    def message(self, client, text):
        """\
        display a message to a given player
        """
        # actually send private messages
        text = self.stripColors(text)
        for line in self.getWrap(text, self._settings['line_length'], self._settings['min_wrap_length']):
            line = self.stripColors(line)
            self.write(self.getCommand('message', name=client.name, prefix=self.msgPrefix, message=line))

    def kick(self, client, reason='', admin=None, silent=False, *kwargs):
        """\
        kick a given players
        """
        self.debug('KICK : client: %s, reason: %s', client.cid, reason)
        if admin:
            fullreason = self.getMessage('kicked_by', self.getMessageVariables(client=client, reason=reason, admin=admin))
        else:
            fullreason = self.getMessage('kicked', self.getMessageVariables(client=client, reason=reason))
        fullreason = self.stripColors(fullreason)
        reason = self.stripColors(reason)

        if not silent and fullreason != '':
            self.say(fullreason)

        if client.guid:
            self.write(self.getCommand('kick', name=client.guid))
        else:
            self.write(self.getCommand('kick', name=client.cid))
        self.queueEvent(self.getEvent('EVT_CLIENT_KICK', reason, client))
        client.disconnect()

    def ban(self, client, reason='', admin=None, silent=False, *kwargs):
        """\
        ban a given players
        """
        self.debug('BAN : client: %s, reason: %s', client.cid, reason)
        if admin:
            fullreason = self.getMessage('banned_by', self.getMessageVariables(client=client, reason=reason, admin=admin))
        else:
            fullreason = self.getMessage('banned', self.getMessageVariables(client=client, reason=reason))
        fullreason = self.stripColors(fullreason)
        reason = self.stripColors(reason)

        if not silent and fullreason != '':
            self.say(fullreason)
        
        banid = client.cid
        if banid is None and client.name:
            banid = client.name
            self.debug('using name to ban : %s' % banid)
        self.write(self.getCommand('ban', name=banid, admin=admin, reason=reason))
        # saving banid in the name column in database
        # so we can unban a unconnected player using name
        client._name = banid
        client.save()
        self.queueEvent(self.getEvent('EVT_CLIENT_BAN', reason, client))
        client.disconnect()

    ## @todo Need to test response from the server
    def unban(self, client, reason='', admin=None, silent=False, *kwargs):
        """\
        unban a given players
        """
        if client.guid in self._server_banlist.keys():
            self.debug('using guid to unban')
            banid = self._server_banlist[client.guid]
        else:
            self.debug('using name to unban')
            banid = client.name
        self.debug('UNBAN: %s' % banid)
        response = self.write(self.getCommand('unban', name=banid))
        self.verbose(response)
        if response:
            self.verbose('UNBAN: Removed name (%s) from banlist' %client.name)
            if admin:
                admin.message('Unbanned: Removed %s from banlist' %client.name)
        self.queueEvent(self.getEvent('EVT_CLIENT_UNBAN', reason, client))

    def tempban(self, client, reason='', duration=2, admin=None, silent=False, *kwargs):
        """\
        tempban a given players
        """
        self.debug('TEMPBAN : client: %s, reason: %s', client.cid, reason)
        if admin:
            fullreason = self.getMessage('temp_banned_by', self.getMessageVariables(client=client, reason=reason, admin=admin, banduration=b3.functions.minutesStr(duration)))
        else:
            fullreason = self.getMessage('temp_banned', self.getMessageVariables(client=client, reason=reason, banduration=b3.functions.minutesStr(duration)))
        fullreason = self.stripColors(fullreason)
        reason = self.stripColors(reason)

        if not silent and fullreason != '':
            self.say(fullreason)

        self.write(self.getCommand('tempban', name=client.cid))
        self.queueEvent(self.getEvent('EVT_CLIENT_BAN_TEMP', reason, client))
        client.disconnect()

    def getMap(self):
        """\
        return the current map/level name
        """
        if self._currentmap is None:
            return "Unknown"
        else:
            return self._currentmap

    def getNextMap(self):
        """Return the name of the next map
        """
        nextmap=''
        self.getMaps()
        no_maps = len(self.maplist)
        currentmap = self.getMap()
        if self.maplist.count(currentmap) == 1:
            i = self.maplist.index(currentmap)
            if i < no_maps-1:
                nextmap = self.mapgamelist[i+1]
            else:
                nextmap =self.mapgamelist[0]
                
        else:
            nextmap = 'Unknown'
        
        return nextmap
        
    def getMaps(self):
        """\
        return the available maps/levels name
        """
        self.maplist = []
        self.mapgamelist = []
        if self._ini_file:
            if self._ini_file == 'ftp':
                self.getftpini()
            else:
                input = open(self._ini_file, 'r')
                for line in input:
                    mapline = self.checkMapline(line)
                    if mapline:
                        if mapline[1] == 'FL':
                            mapline[1] = 'GC'
                        if mapline[1] == 'FL,BC':
                            mapline[1] = 'GC,BC'
                        self.maplist.append(mapline[0])
                        self.mapgamelist.append(self.getEasyName(mapline[0]) + ' [' + mapline[1] + ']')
                
                input.close()
            return self.mapgamelist

    def checkMapline(self, line):
        map = re.match( self._mapline, line)
        if map:
            d = map.groupdict()
            d2 = [d['mapname'], d['gamemode']]
            return d2
        else:
            return None

    def rotateMap(self):
        """\
        load the next map/level
        """
        #CT admin NextMap
        self.write(self.getCommand('maprotate'))
        
    def changeMap(self, map):
        """\
        load a given map/level
        return a list of suggested map names in cases it fails to recognize the map that was provided
        """
        raise NotImplementedError

    def getEasyName(self, mapname):
        """ Change levelname to real name """
        if mapname == 'fl-angelisland':
            return 'Angel Island'
            
        elif mapname == 'fl-crossroads':
            return 'Crossroads'

        elif mapname == 'fl-culdesac':
            return 'Cul-de-Sac'

        elif mapname == 'fl-farm':
            return 'Farm'

        elif mapname == 'fl-harbor':
            return 'Green Zone'

        elif mapname == 'fl-lowlands':
            return 'Lowlands'

        elif mapname == 'fl-borderlands':
            return 'Borderlands'
        else:
            self.warning('unknown level name \'%s\'. Please report this on B3 forums' % mapname)
            return mapname
  
    def getPlayerPings(self):
        """\
        returns a dict having players' id for keys and players' ping for values
        """
        return {}

    def getPlayerScores(self):
        """\
        returns a dict having players' id for keys and players' scores for values
        """
        # trigger a 'retrieve playerlist' command
        #self.retrievePlayerList()

        scores = {}
        clients = self.clients.getList()
        for c in clients:
            try:
                scores[c.name] = int(c.kills)
            except AttributeError:
                pass
        return scores

    def getTeam(self, team):
        team = str(team).lower()
        if team == '0':
            result = b3.TEAM_RED
        elif team == '1':
            result = b3.TEAM_BLUE
        elif team == '2':
            result = b3.TEAM_SPEC
        elif team == '3':
            result = b3.TEAM_UNKNOWN
        else:
            result = b3.TEAM_UNKNOWN
        return result

    def inflictCustomPenalty(self, type, **kwargs):
        """
        Called if b3.admin.penalizeClient() does not know a given penalty type. 
        Overwrite this to add customized penalties for your game like 'slap', 'nuke', 
        'mute' or anything you want.
        /!\ This method must return True if the penalty was inflicted.
        """
        pass

    
    # =======================================
    # convenience methods
    # =======================================

    def getClient(self, name):
        """return a already connected client by searching the 
        clients cid index.

        This method can return None
        """
        client = self.clients.getByCID(name)
        if client:
            return client
        return None

    def getftpini(self):
        def handleDownload(line):
            #self.debug('received %s bytes' % len(block))
            line = line + '\n'
            mapline = self.checkMapline(line)
            if mapline:
                self.maplist.append(mapline[0])
                self.mapgamelist.append(self.getEasyName(mapline[0]) + ' [' + mapline[1] + ']')

        ftp = None
        try:
            ftp = self.ftpconnect()
            self._nbConsecutiveConnFailure = 0
            remoteSize = ftp.size(os.path.basename(self.ftpconfig['path']))
            self.verbose("Connection successful. Remote file size is %s" % remoteSize)
            ftp.retrlines('RETR ' + os.path.basename(self.ftpconfig['path']), handleDownload)          

        except ftplib.all_errors, e:
            self.debug(str(e))
            try:
                ftp.close()
                self.debug('FTP Connection Closed')
            except:
                pass
            ftp = None

        try:
            ftp.close()
        except:
            pass


    def ftpconnect(self):
        #self.debug('Python Version %s.%s, so setting timeout of 10 seconds' % (versionsearch.group(2), versionsearch.group(3)))
        self.verbose('Connecting to %s:%s ...' % (self.ftpconfig["host"], self.ftpconfig["port"]))
        ftp = FTP()
        ftp.set_debuglevel(self._ftplib_debug_level)
        ftp.connect(self.ftpconfig['host'], self.ftpconfig['port'], self._connectionTimeout)
        ftp.login(self.ftpconfig['user'], self.ftpconfig['password'])
        ftp.voidcmd('TYPE I')
        dir = os.path.dirname(self.ftpconfig['path'])
        self.debug('trying to cwd to [%s]' % dir)
        ftp.cwd(dir)
        return ftp
    

    def retrieveBanList(self):
        """\
        Send RETRIEVE BANLIST to the server
        """
        self.verbose2('Retrieving Banlist')
        self.write('RETRIEVE BANLIST')


    def retrievePlayerList(self):
        """\
        Send RETRIEVE PLAYERLIST to the server to trigger onServerPlayer return events
        """
        self.verbose2('Retrieving Playerlist')
        self.write('RETRIEVE PLAYERLIST')

