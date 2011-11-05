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
#
from b3 import functions
from b3.clients import Client
from b3.lib.sourcelib import SourceQuery
from b3.parser import Parser
import asyncore
import b3
import b3.cron
import ftplib
import os
import protocol
import rcon
import re
import string
import sys
import time
from ConfigParser import NoOptionError


__author__  = 'Courgette'
__version__ = '0.4'

_gameevents_mapping = list()
def gameEvent(*decorator_param):
    def wrapper(func):
        for param in decorator_param:
            if isinstance(param, type(re.compile(''))):
                _gameevents_mapping.append((param, func))
            elif isinstance(param, basestring):
                _gameevents_mapping.append((re.compile(param), func))
        return func
    return wrapper

def getGameEventHandler(line):
    for regex, hfunc in _gameevents_mapping:
        match = regex.match(line)
        if match:
            return hfunc, match.groupdict()
    return None, {}

class FrontlineParser(b3.parser.Parser):
    '''
    The Frontline B3 parser class
    '''
    gameName = "frontline"
    OutputClass = rcon.Rcon
    PunkBuster = None 
    _serverConnection = None
    _rconUser = None

    # frontline engine does not support color code, so we need this property
    # in order to get stripColors working
    _reColor = re.compile(r'(\^[0-9])')
    _connectionTimeout = 30
    _playerlistInterval = 3
    _server_banlist = {}

    _settings = {'line_length': 200, 
                 'min_wrap_length': 200}
    
    # dict to hold rcon asynchronous responses
    _async_responses = {}
    
    prefix = '%s: '
    
    def startup(self):
        self.debug("startup()")
            
        for regexp, func in _gameevents_mapping:
            self.debug("%s maps to %s", regexp, func)

        # create the 'Server' client
        #self.clients.newClient('Server', guid='Server', name='Server', hide=True, pbid='Server', team=b3.TEAM_UNKNOWN)

        # start crontab to trigger playerlist events
        self.cron + b3.cron.CronTab(self.retrievePlayerList, second='*/%s' % self._playerlistInterval)

        #self.queryServerInfo()
    
    def routePacket(self, packet):
        if packet is None:
            self.warning('cannot route empty packet')
        else:
            if not packet.startswith('PlayerList:'):
                self.console("%s" % packet.strip())
            hfunc, param_dict = getGameEventHandler(packet)
            if hfunc:
                event = hfunc(self, **param_dict)
                if event:
                    self.queueEvent(event)
            else:
                self.warning('TODO handle packet : %s' % packet)
                self.queueEvent(self.getEvent('EVT_UNKNOWN', packet))


    def run(self):
        """Main worker thread for B3"""
        try:
            self._rconUser = self.config.get("server", "rcon_user")
        except NoOptionError, err:
            self.error("cannot find rcon_user in B3 main config file. %s", err)
            raise SystemExit("incomplete config")
        
        self.screen.write('Startup Complete : B3 is running! Let\'s get to work!\n\n')
        self.screen.write('(If you run into problems, check %s for detailed log info)\n' % self.config.getpath('b3', 'logfile'))
        #self.screen.flush()

        self.updateDocumentation()

        self.bot('Start listening ...')
        while self.working:
            """
            While we are working, connect to the Frontline server
            """
            if self._paused:
                if self._pauseNotice == False:
                    self.bot('PAUSED - Not parsing any lines, B3 will be out of sync.')
                    self._pauseNotice = True
            else:
                if self._serverConnection is None:
                    self.bot('Connecting to Frontline server %s:%s with user %s ...', self._rconIp, self._rconPort, self._rconUser)
                    self._serverConnection = protocol.Client(self, self._rconIp, self._rconPort, self._rconUser, self._rconPassword, keepalive=True)
                    
                    # hook on handle_close to protocol.Client
                    self._original_connection_handle_close_method = self._serverConnection.handle_close
                    self._serverConnection.handle_close = self._handle_connection_close
                    
                    # listen for incoming HF packets
                    self._serverConnection.add_listener(self.routePacket)
                    
                    # setup Rcon
                    self.output.set_frontline_client(self._serverConnection)
                
                self._nbConsecutiveConnFailure = 0
                
                while self.working and not self._paused \
                and (self._serverConnection.connected or not self._serverConnection.authed):
                    asyncore.loop(timeout=3, use_poll=True, count=1)
        self.bot('Stop listening.')

        with self.exiting:
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

    @gameEvent(r'^DEBUG: ((Script)?Log|Error|(Perf|Script)Warning|SeamlessTravel): .*',
               r'^DEBUG: (DevOnline|NetComeGo|RendezVous|LoadingScreenLog|Difficulty|LineCheckLog): .*',
               r'^DEBUG: Warning: .*',
               r'^DEBUG: DevNet: .*',
               r'^UnBan failed! Player ProfileID or Hash is not banned: .*',
               r'^Forced transition to next map$',
               r'^\^5PunkBuster Server: Player List: [Slot #] [GUID] [Address] [Status] [Power] [Auth Rate] [Recent SS] [O/S] [Name]$',
               )
    def ignoreGameEvent(self, *args, **kwargs):
        """do nothing"""
        pass
    
    @gameEvent(r"^WELCOME! Frontlines: Fuel of War \(RCON\) VER=(?P<version>.+) CHALLENGE=(?P<challenge>.*)$")
    def onServerWelcome(self, version, challenge):
        self.info("connected to Frontline server. RCON version %s", version)
       
    @gameEvent(re.compile(r"^PlayerList: (?P<data>.*)$", re.MULTILINE|re.DOTALL|re.IGNORECASE))
    def onServerPlayerlist(self, data):
        """PlayerList: Map=CQ-Gnaw Time=739 Players=0/32 Tickets=500,500 Round=2/3
ID    Name    Ping    Team    Squad    Score    Kills    Deaths    TK    CP    Time    Idle    Loadout    Role    RoleLvl    Vehicle    Hash    ProfileID    """
        self.verbose2("PlayerList : %r" % data)
        lines = data.split('\n')
        match = re.match(r"PlayerList: Map=(?P<map>.+) Time=(?P<remaining_time>(-1|\d+)) Players=(?P<players>\d+)/(?P<total_slots>\d+) Tickets=(?P<tickets>,\d+) Round=(?P<current_round>\d+)/(?P<total_rounds>\d+)", lines[0])
        if match:
            self.game.mapName = match.group('map')
            self.game.sv_maxclients = match.group('total_slots')
            #self.game.gameType = 
            self.game.rounds = int(match.group('current_round'))
            self.game.g_maxrounds = int(match.group('total_rounds'))
            self.game.remaining_time = int(match.group('remaining_time'))
            self.game.tickets = int(match.group('tickets'))
        self.sync()
        headers = ("ID", "Name", "Ping", "Team", "Squad", "Score", "Kills", "Deaths", 
                   "TK", "CP", "Time", "Idle", "Loadout", "Role", "RoleLvl", "Vehicle", 
                   "Hash", "ProfileID")
        for line in lines[2:]:
            if len(line):
                data = line.split('\t')
                pdata = dict(zip(headers, data))
                if 'ProfileID' not in pdata:
                    self.debug("no ProfileID found")
                    continue
                if pdata['ProfileID'] == 0:
                    self.debug("Profile id is 0")
                    continue
                self.debug("player : %r", pdata)
                client = self.getClientOrCreate(pdata['ID'], pdata['ProfileID'], pdata['Name'])
                if client:
                    client.name = pdata['Name']
                    client.team = self.getTeam(pdata['Team'])
                    client.data = pdata
                    client.last_update_time = time.time()

    @gameEvent(r"^Login SUCCESS! User:(?P<user>.*)$")
    def onServerRconLoginSucess(self, user):
        self.bot("B3 correctly authenticated on game server as user %r.", user)
        self.write("CHATLOGGING TRUE")
        self.write("DebugLogging TRUE")
        self.write("Punkbusterlogging TRUE")

    @gameEvent(r"^DEBUG: RendezVous: Update Gathering .*")
    def onServerPlayerLogin(self):
        # DEBUG: RendezVous: Update Gathering 1561500: 7/0
        self.retrievePlayerList()
        
    @gameEvent(r"^(?P<var>ChatLogging) now (?P<data>.*)$", r"^(?P<var>DebugLogging) now (?P<data>.*)$")
    def onServerVarChange(self, var, data):
        self.info("%s is now : %r", var, data)
        
    @gameEvent(r'^CHAT: PlayerName="(?P<playerName>[^"]+)" Channel="(?P<channel>[^"]+)" Message="(?P<text>.*)"$')
    def onServerChat(self, playerName, channel, text):
        client = self.clients.getByExactName(playerName)
        if client is None:
            self.debug("Could not find client")
            return
        if channel == 'TeamSay':
            return self.getEvent('EVT_CLIENT_TEAM_SAY', text, client)
        elif channel == 'Say':
            return self.getEvent('EVT_CLIENT_SAY', text, client)
        else:
            self.warning("unknown Chat channel : %s", channel)

    @gameEvent(r"""^\^5PunkBuster Server: Player GUID Computed (?P<pbid>[0-9a-f]+)\(-\) \(slot #(?P<cid>\d+)\) (?P<ip>[0-9.]+):(?P<port>\d+) (?P<name>.+)$""")
    def onPunkbusterGUID(self, pbid, cid, ip, port, name):
        client = self.clients.getByCID(cid)
        if client:
            client.pbid(pbid)
            client.ip = ip
            client.save()


    @gameEvent(r"""^\^5PunkBuster Server: (?P<cid>\d+)\s+(?P<pbid>[a-z0-9]+)?\(-\) (?P<ip>[0-9.]+):(?P<port>\d+) (\w+)\s+(\d+)\s+([\d.]+)\s+(\d+)\s+\((.)\) "(?P<name>.+)"$""")
    def onPunkbusterPlayerList(self, pbid, cid, ip, port, name):
        client = self.clients.getByCID(cid)
        if client:
            if pbid:
                client.pbid(pbid)
            client.ip = ip
            client.save()

    @gameEvent(re.compile(r"""^Banned Player: PlayerName="(?P<name>.+)" PlayerID=(?P<cid>(-1|\d+)) ProfileID=(?P<guid>\d+) Hash=(?P<hash>.*) BanDuration=(?P<duration>-?\d+)( Permanently)?$""", re.MULTILINE))
    def onServerBan(self, name, cid, guid, hash, duration):
        """ Kicked Player as part of ban: PlayerName="Courgette" PlayerID=1 ProfileID=1561500 Hash= BanDuration=-1
Banned Player: PlayerName="Courgette" PlayerID=1 ProfileID=1561500 Hash= BanDuration=-1 Permanently
"""
        # we are using storage instead of self.clients because the player might already
        # have been kick
        client = self.storage.getClient(Client(guid=guid))
        if client:
            self.saybig("%s added to server banlist" % client.name)
        else:
            self.error('Cannot find banned client')
        # update banlist
        self.retrieveBanList()
        
    @gameEvent(re.compile(r"""^UnBanned Player: PlayerName="(?P<name>.+)" PlayerID=(-1|\d+) ProfileID=(?P<guid>\d+) Hash=(?P<hash>.*)$"""))
    def onServerUnBan(self, name, guid, hash):
        """UnBanned Player: PlayerName="" PlayerID=-1 ProfileID=1561500 Hash="""
        # we are using storage instead of self.clients because the player cannot be connected
        client = self.storage.getClient(Client(guid=guid))
        if client:
            self.saybig("%s removed from server banlist" % client.name)
        else:
            self.error('Cannot find banned client')
        # update banlist
        self.retrieveBanList()
        
    @gameEvent(r"CurrentMap is: (?P<map>.+)")
    def onGetCurrentMapResponse(self, map):
        self._async_responses['GetCurrentMap'] = map
        
    @gameEvent(r"NextMap is: (?P<map>.+)")
    def onGetNextMapResponse(self, map):
        self._async_responses['GetNextMap'] = map
        
    @gameEvent(re.compile(r"^MapList: (?P<data>.+)", re.MULTILINE|re.DOTALL))
    def onMapListResponse(self, data):
        lines = data.split('\n')
        self.debug("lines: %r", lines)
        maps = list()
        for line in lines[2:]:
            if len(line):
                mapName = line.split('\t')[1]
                self.debug("mapName : %s", mapName)
                if mapName.startswith('FL-'):
                    maps.append(mapName)
        self._async_responses['MapList'] = maps

    @gameEvent(r"^Login SUCCESS! User:(?P<user>.*)$")
    def onTest(self, data):
        self.debug("TEST %r ", data)



    # =======================================
    # implement parser interface
    # =======================================

    def getPlayerList(self):
        """\
        Returns a list of client objects
        """
        raise NotImplementedError

    def authorizeClients(self):
        """\
        For all connected players, fill the client object with properties allowing to find 
        the user in the database (usualy guid, or punkbuster id, ip) and call the 
        Client.auth() method 
        """
        ## in Frontline, there is no synchronous way to obtain a player guid
        ## the onServerUid event will be the one calling Client.auth()
        raise NotImplementedError
    
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
        # disconnect clients that have left
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
            self.write('SAY %s %s' % (self.msgPrefix, line))

    def saybig(self, msg):
        """\
        broadcast a message to all players in a way that will catch their attention.
        """
        msg = self.stripColors(msg)
        for line in self.getWrap(msg, self._settings['line_length'], self._settings['min_wrap_length']):
            line = self.stripColors(line)
            self.write('SAY #%s# %s' % (self.msgPrefix, line))

    def message(self, client, text):
        """\
        display a message to a given player
        """
        # actually send private messages
        text = self.stripColors(text)
        for line in self.getWrap(text, self._settings['line_length'], self._settings['min_wrap_length']):
            line = self.stripColors(line)
            self.write('PLAYERSAY PlayerID=%(cid)s SayText="%(message)s"' % {'cid':client.cid, 'message':line})

    def kick(self, client, reason='', admin=None, silent=False, *kwargs):
        """\
        kick a given player
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

        if len(reason):
            self.write('KICK ProfileID=%s Reason="%s"' % (client.guid, reason))
        else:
            self.write('KICK ProfileID=%s' % client.guid)
        
        self.queueEvent(self.getEvent('EVT_CLIENT_KICK', reason, client))
        client.disconnect()

    def ban(self, client, reason='', admin=None, silent=False, *kwargs):
        """\
        ban a given player
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
        
        if len(reason):
            self.write('BAN ProfileID=%s BanTime=0 Reason="%s"' % (client.guid, reason))
        else:
            self.write('BAN ProfileID=%s BanTime=0' % client.guid)
        self.queueEvent(self.getEvent('EVT_CLIENT_BAN', {'reason': reason, 'admin': admin}, client))
        client.disconnect()

    def unban(self, client, reason='', admin=None, silent=False, *kwargs):
        """\
        unban a given player
        """
        self.write('UNBAN ProfileID=%s' % client.guid)
        if admin:
            admin.message('Unbanned: Removed %s from banlist' %client.name)
        self.queueEvent(self.getEvent('EVT_CLIENT_UNBAN', reason, client))


    def tempban(self, client, reason='', duration=2, admin=None, silent=False, *kwargs):
        """\
        tempban a given player
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
        
        if duration < 1:
            if len(reason):
                self.write('KICK ProfileID=%s Reason="%s"' % (client.guid, reason))
            else:
                self.write('KICK ProfileID=%s' % client.guid)
        else:
            if len(reason):
                self.write('BAN ProfileID=%s BanTime=%s Reason="%s"' % (client.guid, int(duration), reason))
            else:
                self.write('BAN ProfileID=%s BanTime=%s' % (client.guid, int(duration)))
        self.queueEvent(self.getEvent('EVT_CLIENT_BAN_TEMP', {'reason': reason, 
                                                              'duration': duration, 
                                                              'admin': admin}
                                      , client))
        client.disconnect()

    def getMap(self):
        """\
        return the current map/level name
        """
        self._async_responses['GetCurrentMap'] = None
        self.write('GetCurrentMap')
        count = 0
        while self._async_responses['GetCurrentMap'] is None and count < 30: 
            time.sleep(.1)
            count += 1
        return self._async_responses['GetCurrentMap']


    def getNextMap(self):
        """Return the name of the next map
        """
        self._async_responses['GetNextMap'] = None
        self.write('GetNextMap')
        count = 0
        while self._async_responses['GetNextMap'] is None and count < 30: 
            time.sleep(.1)
            count += 1
        return self._async_responses['GetNextMap']

        
    def getMaps(self):
        """\
        return the available maps/levels name
        """
        self._async_responses['MapList'] = None
        self.write('MapList')
        count = 0
        while self._async_responses['MapList'] is None and count < 30: 
            time.sleep(.1)
            count += 1
        return self._async_responses['MapList']


    def rotateMap(self):
        """\
        load the next map/level
        """
        self.write('NEXTMAP')

        
    def changeMap(self, map):
        """\
        load a given map/level
        return a list of suggested map names in cases it fails to recognize the map that was provided
        """
        self.write('ForceMapChange %s' % map)


    def getEasyName(self, mapname):
        """ Change levelname to real name """
        raise NotImplementedError

  
    def getPlayerPings(self):
        """\
        returns a dict having players' id for keys and players' ping for values
        """
        pings = {}
        clients = self.clients.getList()
        for c in clients:
            try:
                pings[c.cid] = int(c.data['Ping'])
            except AttributeError:
                pass
        return pings

    def getPlayerScores(self):
        """\
        returns a dict having players' id for keys and players' scores for values
        """
        pings = {}
        clients = self.clients.getList()
        for c in clients:
            try:
                pings[c.cid] = int(c.data['Kills'])
            except AttributeError:
                pass
        return pings


    def inflictCustomPenalty(self, type, client, reason=None, duration=None, admin=None, data=None):
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

    def getClient(self, cid):
        """return a already connected client by searching the 
        clients cid index.

        This method can return None
        """
        client = self.clients.getByCID(cid)
        if client:
            return client
        return None
    
    
    def getClientOrCreate(self, cid, guid, name):
        """return a already connected client by searching the 
        clients guid index or create a new client
        
        This method can return None
        """
        client = self.clients.getByCID(cid)
        if client is None:
            client = self.clients.newClient(cid, guid=guid, name=name, team=b3.TEAM_UNKNOWN)
            client.last_update_time = time.time()
        return client
    

    def retrievePlayerList(self):
        self.write('PLAYERLIST')


    def retrieveBanList(self):
        """\
        Send RETRIEVE BANLIST to the server
        """
        self.write('BanList')


    def getTeam(self, teamId):
        team = str(teamId).lower()
        if team == '0':
            result = b3.TEAM_RED
        elif team == '1':
            result = b3.TEAM_BLUE
        elif team == '2':
            result = b3.TEAM_SPEC
        elif team == '255':
            result = b3.TEAM_UNKNOWN
        else:
            self.verbose2("unrecognized team id : %r", team)
            result = b3.TEAM_UNKNOWN
        return result


    def queryServerInfo(self):
        ## read game server info and store as much of it in self.game wich
        ## is an instance of the b3.game.Game class
        sq = SourceQuery.SourceQuery(self._publicIp, self._port, timeout=10)
        try:
            serverinfo = sq.info()
            self.debug("server info : %r", serverinfo)
            if 'map' in serverinfo:
                self.game.mapName = serverinfo['map'].lower()
            if 'hostname' in serverinfo:
                self.game.sv_hostname = serverinfo['hostname']
            if 'maxplayers' in serverinfo:
                self.game.sv_maxclients = serverinfo['maxplayers']
        except Exception, err:
            self.exception(err)

