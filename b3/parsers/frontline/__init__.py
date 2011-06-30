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
__version__ = '0.1'



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
    _playerlistInterval = 5
    _server_banlist = {}

    #===========================================================================
    # Define below regular expressions that match for event received from the 
    # game server and their handling method name.
    # The groups in the regexp must be named and will be passed as named 
    # parameters to the handling functions. 
    #===========================================================================
    _re_server_events = (
        (re.compile(r"^WELCOME! Frontlines: Fuel of War \(RCON\) VER=(?P<version>.+) CHALLENGE=(?P<challenge>.*)$"), "onServerWelcome"),
        (re.compile(r"^Login SUCCESS! User:(?P<user>.*)$"), "onServerLoginSucess"),
        (re.compile(r"^ChatLogging now (?P<data>.*)$"), "onServerChatLogging"),
        (re.compile(r"^PlayerList: (?P<data>(.|\s)*)$", re.MULTILINE | re.IGNORECASE), "onServerPlayerlist"),
     )

    _commands = {}
    _commands['message'] = ('PLAYERSAY PlayerID=%(cid)s SayText="%(prefix)s [pm] %(message)s"')
    _commands['say'] = ('SAY %(prefix)s %(message)s')
    _commands['saybig'] = ('SAY %(prefix)s %(message)s')
    _commands['kick'] = ('KICK PlayerID=%(cid)s')
    _commands['ban'] = ('KICK PlayerID=%(cid)s')
    _commands['tempban'] = ('KICK PlayerID=%(cid)s')
    _commands['maprotate'] = ('NEXTMAP')
    
    _settings = {'line_length': 90, 
                 'min_wrap_length': 100}
    
    prefix = '%s: '
    
    def startup(self):
        self.debug("startup()")
        
        # create the 'Server' client
        #self.clients.newClient('Server', guid='Server', name='Server', hide=True, pbid='Server', team=b3.TEAM_UNKNOWN)

        # start crontab to trigger playerlist events
        self.cron + b3.cron.CronTab(self.retrievePlayerList, second='*/%s' % self._playerlistInterval)

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

    
    def routePacket(self, packet):
        if packet is None:
            self.warning('cannot route empty packet')
        else:
            self.console("%s" % packet)
            for regex, hfuncName in self._re_server_events:
                try:
                    hfunc = getattr(self, hfuncName)
                except AttributeError, err:
                    self.error(err)
                else:
                    match = regex.match(packet)
                    if match:
                        return hfunc(**match.groupdict())
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
                    self.bot('Connecting to Frontline server ...')
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

    def onServerPass(self, *args, **kwargs):
        """do nothing"""
        pass
    
    def onServerWelcome(self, version, challenge):
        self.info("connected to Frontline server. RCON version %s", version)
       
    def onServerPlayerlist(self, data):
        """PlayerList: Map=CQ-Gnaw Time=739 Players=0/32 Tickets=500,500 Round=2/3
ID    Name    Ping    Team    Squad    Score    Kills    Deaths    TK    CP    Time    Idle    Loadout    Role    RoleLvl    Vehicle    Hash    ProfileID    """
        self.bot("PlayerList : %r" % data)
        for line in data.split('\n')[2:]:
            self.info("player : %r", line.split('\t'))

    def onServerLoginSucess(self, user):
        self.bot("B3 correctly authenticated on game server as user %r.", user)
        self.write("CHATLOGGING TRUE")

    def onServerChatLogging(self, data):
        self.info("chatlogging is now : %r", data)


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
        self.write("PLAYERLIST")
        raise NotImplementedError
        
    
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

    def message(self, client, text):
        """\
        display a message to a given player
        """
        # actually send private messages
        text = self.stripColors(text)
        for line in self.getWrap(text, self._settings['line_length'], self._settings['min_wrap_length']):
            line = self.stripColors(line)
            self.write(self.getCommand('message', cid=client.cid, prefix=self.msgPrefix, message=line))

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

        self.write(self.getCommand('kick', playerid=client.cid))
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
        
        self.write(self.getCommand('ban', cid=client.cid, admin=admin.name.replace('"','\"'), reason=reason))
        self.queueEvent(self.getEvent('EVT_CLIENT_BAN', {'reason': reason, 'admin': admin}, client))
        client.disconnect()

    def unban(self, client, reason='', admin=None, silent=False, *kwargs):
        """\
        unban a given player
        """
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

        self.write(self.getCommand('kick', cid=client.cid))
        self.queueEvent(self.getEvent('EVT_CLIENT_BAN_TEMP', {'reason': reason, 
                                                              'duration': duration, 
                                                              'admin': admin}
                                      , client))
        client.disconnect()

    def getMap(self):
        """\
        return the current map/level name
        """
        raise NotImplementedError


    def getNextMap(self):
        """Return the name of the next map
        """
        raise NotImplementedError

        
    def getMaps(self):
        """\
        return the available maps/levels name
        """
        raise NotImplementedError


    def rotateMap(self):
        """\
        load the next map/level
        """
        self.write(self.getCommand('maprotate'))

        
    def changeMap(self, map):
        """\
        load a given map/level
        return a list of suggested map names in cases it fails to recognize the map that was provided
        """
        raise NotImplementedError

    def getEasyName(self, mapname):
        """ Change levelname to real name """
        raise NotImplementedError

  
    def getPlayerPings(self):
        """\
        returns a dict having players' id for keys and players' ping for values
        """
        raise NotImplementedError

    def getPlayerScores(self):
        """\
        returns a dict having players' id for keys and players' scores for values
        """
        raise NotImplementedError


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

    def getClient(self, name):
        """return a already connected client by searching the 
        clients cid index.

        This method can return None
        """
        client = self.clients.getByCID(name)
        if client:
            return client
        return None
    
    
    def getClientByUidOrCreate(self, uid, name):
        """return a already connected client by searching the 
        clients guid index or create a new client
        
        This method can return None
        """
        client = self.clients.getByGUID(uid)
        if client is None and name:
            client = self.clients.newClient(name, guid=uid, name=name, team=b3.TEAM_UNKNOWN)
            client.last_update_time = time.time()
        return client
    

    def retrievePlayerList(self):
        self.write('PLAYERLIST')
