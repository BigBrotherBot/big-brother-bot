#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2011 Thomas LEVEIL
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
# 07/28/2012    0.1     Initial release
# 08/31/2012    0.12    Various fixes and cleanups
# 09/01/2012    0.13    Check for non-verified GUIDs in Player List from server
# 09/01/2012    0.14    Allow for non-ascii names by replacing clients.Client.auth method
# 09/05/2012    0.15    change the way events EVT_CLIENT_CONNECT and EVT_CLIENT_AUTH work
#                       fix EVT_CLIENT_DISCONNECT
# 09/10/2012    0.16    Fix UTF-8 encoding issues
# 09/15/2012    0.17
#   - reduce code size by moving some network code to the protocol module
#   - take advantage of new BattleyeServer.command() behaviour which is synchronous since protocol.py v1.1. This makes the parser much easier to write/read
#   - move all UTF-8 encoding/decoding related code to the protocol module. In the B3 parser code, there is no need to worry about those issues.
#   - remove unused or unnecessary code
#   - fix ban (by cid)
#   - add prefix to say/saybig/message methods
#   - implements getPlayerPings()
#   - add method getBanlist()
# 09/20/1012    0.18
#   - Make restart method work correctly when called from a plugin
# 09/25/2012    0.19
#   - Allow clients with un-verified GUIDs to auth if IP's match the one in the batabase
#   - or optionally allow clients to always auth using the nonVerified GUID's

import sys, re, traceback, time, Queue, threading
from logging import Formatter
from b3.output import VERBOSE2, VERBOSE
import b3.parser
from b3.parsers.battleye.rcon import Rcon as BattleyeRcon
from b3.parsers.battleye.protocol import BattleyeServer, CommandFailedError, CommandError, BattleyeError, NetworkError
import b3.events
import b3.cvar
from b3.clients import Clients

__author__  = '82ndab-Bravo17, Courgette'
__version__ = '0.19'


# disable the authorizing timer that come by default with the b3.clients.Clients class
Clients.authorizeClients = lambda *args, **kwargs: None


# how long should the bot try to connect to the Battleye server before giving out (in second)
GAMESERVER_CONNECTION_WAIT_TIMEOUT = 600


class AbstractParser(b3.parser.Parser):
    """
    An base class to help with developing battleye parsers
    """

    gameName = None

    # hard limit for rcon command admin.say
    SAY_LINE_MAX_LENGTH = 128

    OutputClass = BattleyeRcon
    _serverConnection = None
    _nbConsecutiveConnFailure = 0

    battleye_event_queue = Queue.Queue(400)
    sayqueue = Queue.Queue(100)
    sayqueuelistener = None

    # battleye engine does not support color code, so we need this property
    # in order to get stripColors working
    _reColor = re.compile(r'(\^[0-9])')
    _reSafename = re.compile(r"('|\\)")

    _settings = {
        'line_length': 128,
        'min_wrap_length': 128,
        'message_delay': .8,
        }

    _gameServerVars = () # list available cvar

    _commands = {
        'message': ('say', '%(cid)s', '%(message)s'),
        'say': ('say -1' , '%(message)s'),
        'kick': ('kick', '%(cid)s', '%(reason)s'),
        'ban': ('ban', '%(cid)s', '0', '%(reason)s'),
        'banByGUID': ('addBan', '%(guid)s', '0', '%(reason)s'),
        'unban': ('removeBan', '%(ban_no)s'),
        'tempban': ('ban', '%(cid)s', '%(duration)d', '%(reason)s'),
        'tempbanByGUID': ('addBan', '%(guid)s', '%(duration)d', '%(reason)s'),
        'shutdown': ('#shutdown', ),
        }

    _eventMap = {
    }

    _regPlayer = re.compile(r'^(?P<cid>[0-9]+)\s+(?P<ip>[0-9.]+):(?P<port>[0-9]+)\s+(?P<ping>[0-9-]+)\s+(?P<guid>[0-9a-f]+)\((?P<verified>[A-Z\?]+)\)\s+(?P<name>.*?)$', re.I)
    _regPlayer_lobby = re.compile(r'^(?P<cid>[0-9]+)\s+(?P<ip>[0-9.]+):(?P<port>[0-9]+)\s+(?P<ping>[0-9-]+)\s+(?P<guid>[0-9a-f]+)\((?P<verified>[A-Z\?]+)\)\s+(?P<name>.*?)\s+(?P<lobby>\(Lobby\))$', re.I)
    re_playerlist = re.compile(r'''^\s*(?P<cid>[0-9]+)\s+(?P<ip>[0-9.]+):(?P<port>[0-9]+)\s+(?P<ping>[0-9-]+)\s+(?P<guid>[0-9a-f]+)\((?P<verified>[A-Z\?]+)\)\s+(?P<name>.*?)(?:\s+(?P<lobby>\(Lobby\)))?$''', re.I|re.MULTILINE)
    _useunverifiedguid = False


    # flag to find out if we need to fire a EVT_GAME_ROUND_START event.
    _waiting_for_round_start = True

    def run(self):
        """Main worker thread for B3"""
        self.bot('Start listening ...')
        self.screen.write('Startup Complete : B3 is running! Let\'s get to work!\n\n')
        self.screen.write('(If you run into problems, check %s for detailed log info)\n' % self.config.getpath('b3', 'logfile'))
        #self.screen.flush()

        self.updateDocumentation()

        try:
            b3_log_level = self.config.getint('b3', 'log_level')
        except:
            b3_log_level = VERBOSE

        server_logging = self.load_protocol_logging()

        formatter = Formatter('"%(asctime)s %(name)-15s [%(thread)-6d] %(threadName)-20s %(levelname)-8s %(message)r"')
        ## the block below can activate additional logging for the BattleyeServer class
        if server_logging or b3_log_level == VERBOSE2:
            import logging
            battleyeServerLogger = logging.getLogger("BattleyeServer")
            for handler in logging.getLogger('output').handlers:
                handler.setFormatter(formatter)
                battleyeServerLogger.addHandler(handler)
            battleyeServerLogger.setLevel(logging.INFO)

            if server_logging:
                ## This block will send the logging info to a separate file

                hdlr = logging.FileHandler(server_logging)
                hdlr.setFormatter(formatter)
                battleyeServerLogger.addHandler(hdlr)
                battleyeServerLogger.setLevel(logging.DEBUG)

        while self.working:
            if not self._serverConnection or not self._serverConnection.connected:
                try:
                    self.setup_battleye_connection()
                except CommandError, err:
                    self.error(err.message)
                except IOError, err:
                    self.error("IOError %s"% err)
                except Exception, err:
                    self.error(err)
                    self.exitcode = 220
                    break

            try:
                added, expire, event = self.battleye_event_queue.get(timeout=5)
                self.routeBattleyeEvent(event)
            except Queue.Empty:
                self.verbose2("no game server event to treat in the last 5s")
            except CommandError, err:
                # it does not matter from the parser perspective if Battleye command failed
                # (timeout or bad reply)
                self.warning(err)
            except BattleyeError, e:
                # the connection to the battleye server is lost
                self.warning(e)
                self.close_battleye_connection()
            except Exception, e:
                self.error("unexpected error, please report this on the B3 forums")
                self.error(e)
                # unexpected exception, better close the battleye connection
                self.close_battleye_connection()

        # The Battleye connection is running its own thread to communicate with the game server. We need to tell
        # this thread to stop.
        self.close_battleye_connection()
        self.info("Stop listening for Battleye events")
        self.output.battleye_server = None
        
        # exiting B3
        with self.exiting:
            # If !die or !restart was called, then  we have the lock only after parser.handleevent Thread releases it
            # and set self.working = False and this is one way to get this code is executed.
            # Else there was an unhandled exception above and we end up here. We get the lock instantly.


            # If !die was called, exitcode have been set to 222
            # If !restart was called, exitcode have been set to 221
            # In both cases, the SystemExit exception that triggered exitcode to be filled with an exit value was
            # caught. Now that we are sure that everything was gracefully stopped, we can re-raise the SystemExit
            # exception.
            self.debug('Exiting with exitcode of %s' % self.exitcode)
            time.sleep(5)
            if self.exitcode:
                sys.exit(self.exitcode)


    def setup_battleye_connection(self):
        """
        Setup the Connection to the Battleye server
        """
        self.info('Connecting to battleye server  on %s:%s...' % (self._rconIp, self._rconPort))
        if self._serverConnection:
            self.close_battleye_connection()

        self._serverConnection = BattleyeServer(self._rconIp, self._rconPort, self._rconPassword)
        self.info("Server Connection is %s" % repr(self._serverConnection))
        timeout = GAMESERVER_CONNECTION_WAIT_TIMEOUT + time.time()
        while time.time() < timeout and not self._serverConnection.connected:
            self.info("retrying to connect to game server...")
            time.sleep(2)
            self.close_battleye_connection()
            self._serverConnection = BattleyeServer(self._rconIp, self._rconPort, self._rconPassword)

        if self._serverConnection is None or not self._serverConnection.connected:
            self.error("Could not connect to Battleye server")
            self.close_battleye_connection()
            self.shutdown()
            raise SystemExit()

        # listen for incoming game server events
        self._serverConnection.subscribe(self.OnBattleyeEvent)

        # setup Rcon
        self.output.set_battleye_server(self._serverConnection)

        self.queueEvent(b3.events.Event(b3.events.EVT_GAMESERVER_CONNECT, None))

        self.say('%s ^2[ONLINE]' % b3.version)
        #self.getServerInfo()
        #self.getServerVars()
        self.clients.sync()


    def close_battleye_connection(self):
        try:
            self._serverConnection.stop()
        except Exception:
            pass
        self._serverConnection = None


    def OnBattleyeEvent(self, event):
        if not self.working:
            try:
                self.verbose("dropping Battleye event %r" % event)
            except:
                pass
        self.console(repr(event))
        try:
            self.battleye_event_queue.put((self.time(), self.time() + 10, event), timeout=2)
            self.info('Battleye Event Queue: %s' % repr(self.battleye_event_queue))
        except Queue.Full:
            self.error("Battleye event queue full, dropping event %r" % event)

            
#'RCon admin #0 (76.108.91.78:62382) logged in'
#'Player #0 Bravo17 (76.108.91.78:2304) connected'
#'Player #0 Bravo17 - GUID: 80a5885ebe2420bab5e158a310fcbc7d (unverified)'
#'Verified GUID (80a5885ebe2420bab5e158a310fcbc7d) of player #0 Bravo17'
#'Player #2 NZ (04b81a0bd914e7ba610ef3c0ffd66a1a) has been kicked by BattlEye: Script Restriction #107'
#'Player #4 Kauldron disconnected'
#(Lobby) Bravo17: hello b3'
#(Global) Bravo17: global channel
#Players on server:\n
#[#] [IP Address]:[Port] [Ping] [GUID] [Name]\n
#--------------------------------------------------\n
#0   76.108.91.78:2304     63   80a5885ebe2420bab5e158a310fcbc7d(OK) Bravo17\n
#(1 players in total)'

    
#Players on server:\n
#[#] [IP Address]:[Port] [Ping] [GUID] [Name]\n--------------------------------------------------\n
#0   76.108.91.78:2304     63   80a5885ebe2420bab5e158a310fcbc7d(OK) Bravo17\n
#(1 players in total)'
    


    def routeBattleyeEvent(self, message):
        """
        Decide what to do with the event received from the BattlEye server
        """

        if message is None:
            self.warning('cannot route empty event')

        self.info('Server Message is %s' % message)

        if message.startswith('RCon admin #'):
            func = self.OnServerMessage
            eventData = message[12:]
        elif message.startswith('Player #'):
            if message.endswith(' disconnected'):
                func = self.OnPlayerLeave
                eventData = message[8:len(message)-13]
            elif message.endswith(' connected'):
                func = self.OnPlayerConnected
                eventData = message[8:len(message)-10]
            elif message.endswith('(unverified)'):
                func = self.OnUnverifiedGUID
                eventData = message[8:len(message)-13]
            elif message.find(' has been kicked by BattlEye: '):
                func = self.OnBattleyeKick
                eventData = message[8:]
            else:
                self.debug('Unhandled server message %s' % message)
                eventData = None
                func = self.OnUnknownEvent
        elif message.startswith('Verified GUID'):
            func = self.OnVerifiedGUID
            eventData = message[15:]
        elif message.startswith('(Lobby)'):
            func = self.OnPlayerChat
            eventData = message[8:] + ' (Lobby)'
        elif message.startswith('(Global)'):
            func = self.OnPlayerChat
            eventData = message[9:] + ' (Global)'
        elif message.startswith('(Direct)'):
            func = self.OnPlayerChat
            eventData = message[9:] + ' (Direct)'
        elif message.startswith('(Vehicle)'):
            func = self.OnPlayerChat
            eventData = message[10:] + ' (Vehicle)'
        elif message.startswith('(Group)'):
            func = self.OnPlayerChat
            eventData = message[8:] + ' (Group)'
        elif message.startswith('(Side)'):
            func = self.OnPlayerChat
            eventData = message[7:] + ' (Side)'
        elif message.startswith('(Command)'):
            func = self.OnPlayerChat
            eventData = message[10:] + ' (Command)'

        else:
            self.debug('Unhandled server message %s' % message)
            eventData = None
            func = self.OnUnknownEvent

        event = func(eventData)
        #self.debug('event : %s' % event)
        if event:
            self.queueEvent(event)


    def startup(self):

        # add specific events
        self.Events.createEvent('EVT_GAMESERVER_CONNECT', 'connected to game server')
        self.Events.createEvent('EVT_CLIENT_SPAWN', 'Client Spawn')
        self.Events.createEvent('EVT_PLAYER_SYNC_COMPLETED', 'Players syncing finished')

        self.load_conf_max_say_line_length()
        self.load_config_message_delay()
        self.load_use_unverified_guid()

        self.start_sayqueue_worker()
        # start crontab to trigger playerlist events
        self.cron + b3.cron.CronTab(self.clients.sync, minute='*/1')
        self.clients.newClient('Server', guid='Server', name='Server', hide=True, pbid='Server', team=b3.TEAM_UNKNOWN, squad=None)


    def pluginsStarted(self):
        # self.patch_b3_admin_plugin()
        return


    def sayqueuelistener_worker(self):
        self.info("sayqueuelistener job started")
        while self.working:
            try:
                self._say(self.sayqueue.get(timeout=40))
            except Queue.Empty:
                self.verbose2("sayqueuelistener: had nothing to do in the last 40 sec")
            except Exception, err:
                self.info("sayqueuelistener Error", exc_info=err)
        self.info("sayqueuelistener job ended")


    def _say(self, msg):
        for line in self.getWrap(self.stripColors(self.msgPrefix + ' ' + msg), self._settings['line_length'], self._settings['min_wrap_length']):
            self.write(self.getCommand('say', message=line))
            time.sleep(self._settings['message_delay'])


    def start_sayqueue_worker(self):
        self.sayqueuelistener = threading.Thread(target=self.sayqueuelistener_worker)
        self.sayqueuelistener.setDaemon(True)
        self.sayqueuelistener.start()


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


    def write(self, msg, *args, **kwargs):
        """Write a message to Rcon/Console
        Unfortunately this has been abused all over B3
        and B3 plugins to broadcast text :(
        """
        if isinstance(msg, basestring):
            # console abuse to broadcast text
            self.say(msg)
        else:
            # Then we got a command, so unpack it
            cmd = ' '.join(msg).strip()
            if self.replay:
                self.bot('Sent rcon message: %s' % cmd)
            elif self.output:
                return self.output.write(cmd)


    
    ###############################################################################################
    #
    #    Battleye events handlers
    #    
    ###############################################################################################

    
    def OnPlayerChat(self, data):
        """
        #(Lobby) Bravo17: hello b3'
        #(Global) Bravo17: global channel

        Player has sent a message to other players
        """
        name, sep, message = data.partition(': ')
        self.debug('Name = %s, Message = %s Name length = %s' % (name, message, len(name)))
        
        self.debug('Looking for client [%s]' % name)
        client = self.getClient(name.lower(), auth=False)

        if client is None:
            self.warning("Could not get client :( %s" % traceback.extract_tb(sys.exc_info()[2]))
            return
        if client.cid == 'Server':
            # ignore chat events for Server
            return
        text = message

        # existing commands can be prefixed with a '/' instead of usual prefixes
        cmdPrefix = '!'
        cmd_prefixes = (cmdPrefix, '@', '&')
        admin_plugin = self.getPlugin('admin')
        if admin_plugin:
            cmdPrefix = admin_plugin.cmdPrefix
            cmd_prefixes = (cmdPrefix, admin_plugin.cmdPrefixLoud, admin_plugin.cmdPrefixBig)
        cmd_name = text[1:].split(' ', 1)[0].lower()
        if len(text) >= 2 and text[0] == '/':
            if text[1] in cmd_prefixes:
                text = text[1:]
            elif cmd_name in admin_plugin._commands:
                text = cmdPrefix + text[1:]
            
        if len(text) >= 2:
            cmd_name = text[1:].split(' ', 1)[0]
            if cmd_name in admin_plugin._commands:
                # Remove chat source from end of line
                text = text.rpartition(' ')[0]

        event_type = b3.events.EVT_CLIENT_SAY
        return b3.events.Event(event_type, text, client)
        

    def OnPlayerLeave(self, data):
        """
        #Player #4 Kauldron disconnected
        Player has left the server
        """
        parts = data.split(' ', 1)
        name = parts[1]
        client = self.getClient(name=name, cid=parts[0])
        if client: 
            client.disconnect() # this triggers the EVT_CLIENT_DISCONNECT event
        return None


    def OnPlayerConnected(self, data):
        """
        # Player #0 Bravo17 (76.108.91.78:2304)
        Initial player connect message received
        """

        data = data.rpartition(')')[0]
        data, sep, ip = data.rpartition('(')
        ip = ip.partition(':')[0]
        cid, sep, name = data.partition(' ')
        self.getClient(cid=cid, name=name, ip=ip) # fires EVT_CLIENT_CONNECTED


    def OnUnverifiedGUID(self, data):
        """
        #Player #0 Bravo17 - GUID: 80a5885ebe2420bab5e158a310fcbc7d (unverified)
        Players GUID has been found but not verified, no action to take
        """

        if not self._useunverifiedguid:
            return
        cid, sep, data = data.partition(' ')
        name, sep, guid = data.rpartition(' - GUID: ')
        name = name.strip()
        self.debug('CID: %s Name %s Guid %s' % (cid, name, guid))

        client = self.getClient(name=name, cid=cid, guid=guid)
        if client:
            # update client data
            client.guid = guid
            client.name = name
            client.cid = cid
            # make sure client is now authenticated as we know its guid
            client.auth()
        else:
            self.warning("could not create client")
        

    def OnVerifiedGUID(self, data):
        """
        #Verified GUID  (80a5885ebe2420bab5e158a310fcbc7d) of player #0 Bravo17
        Players GUID has been verified, auth player
        """
        if self._useunverifiedguid:
            return
        guid = data.partition(')')[0]
        data = data .partition('#')[2]
        cid, sep, name = data.partition(' ')

        client = self.getClient(name=name, cid=cid, guid=guid)
        if client:
            # update client data
            client.guid = guid
            client.name = name
            client.cid = cid
            # make sure client is now authenticated as we know its guid
            client.auth()
        else:
            self.warning("could not create client")


    def OnServerMessage(self, data):
        """
        Request: Message from Server
        Effect: None, no messages from server are relevant
        """
        self.debug("Server Message")
        event_type = b3.events.EVT_CLIENT_SAY
        evt = b3.events.Event(event_type, None, None)
        #pass
        return
        

    def OnBattleyeKick(self, data):
        """
        #Player #2 NZ (04b81a0bd914e7ba610ef3c0ffd66a1a) has been kicked by BattlEye: Script Restriction #107'
        Player has been kicked by Battleye
        """

        player, msg, reason = data.partition(') has been kicked by BattlEye: ')
        cid = player.partition(' ')[0]
        guid = player.rpartition('(')[2]
        name = data[len(cid)+1:-len(guid)-len(reason)-33]
        self.debug('Looking for client %s with GUID %s' % (name, guid))
        client = self.getClient(name, guid=guid, auth=False)
        if client: 
            client.disconnect() # this triggers the EVT_CLIENT_DISCONNECT event


    def OnUnknownEvent(self, data):
        return False


    ###############################################################################################
    #
    #    B3 Parser interface implementation
    #    
    ###############################################################################################


    def getClient(self, name, guid=None, cid=None, ip='', auth=True):
        """Get a connected client from storage or create it
        B3 CID   <--> cid
        B3 GUID  <--> guid
        """
        client = None
        if guid:
            # try to get the client from the storage of already authed clients by guid
            client = self.clients.getByGUID(guid)
        if not client:
            # try to get the client from the storage of already authed clients by name
            client = self.clients.getByName(name)
        if auth and not client and cid and name:
            if cid == 'Server':
                return self.clients.newClient('Server', guid='Server', name='Server', hide=True)
            client = self.clients.newClient(cid, guid=guid, name=name, ip=ip)
        return client
    

    
    
    def getPlayerList(self, maxRetries=None):
        """return a dict which keys are cid and values a dict of player properties
        as returned by admin.listPlayers.
        Does not return client objects"""
        #Players on server:\n
        #[#] [IP Address]:[Port] [Ping] [GUID] [Name]\n--------------------------------------------------\n
        #0   76.108.91.78:2304     63   80a5885ebe2420bab5e158a310fcbc7d(OK) Bravo17\n
        #0   192.168.0.100:2316    0    80a5885ebe2420bab5e158a310fcbc7d(OK) Bravo17 (Lobby)\n
        #(1 players in total)'
        player_list = self.output.write("players").splitlines()
        self.debug('Playerlist is %s' % player_list)
        self.debug('Playerlist is %s long' % (len(player_list)-4))
        players = {}
        for i in range(3, len(player_list)-1):
            p = re.match(self._regPlayer_lobby, player_list[i])
            if p:
                pl = p.groupdict()
                if pl['verified'] =='OK':
                    self.debug('Player: %s' % pl)
                    pl['lobby'] = True
                    players[pl['cid']] = pl
                elif pl['verified'] =='?':
                        self.debug('Player in Lobby GUID not yet verified: %s' % pl)
                        pl['lobby'] = True
                        players[pl['cid']] = pl
                else:
                        self.debug('Player in Lobby GUID status unknown: %s' % pl)
            else:
                p = re.match(self._regPlayer, player_list[i])
                if p:
                    pl = p.groupdict()
                    if pl['verified'] =='OK':
                        self.debug('Player: %s' % pl)
                        pl['lobby'] = False
                        players[pl['cid']] = pl
                    elif pl['verified'] =='?':
                        self.debug('Player GUID not yet verified: %s' % pl)
                        pl['lobby'] = False
                        players[pl['cid']] = pl
                    else:
                        self.debug('Player GUID status unknown: %s' % pl)
                else:
                    self.debug('Not Matched: %s ' % player_list[i])

        self.debug('Players on server: %s' % players)
        return players


    def authorizeClients(self):
        """
        Authorise clients from player list
        """
        pass # no need in this game as we always know player guid and verified status


    def sync(self):
        """
        Sync clients with player list
        """
        plist = self.getPlayerList()
        mlist = {}

        for cid, c in plist.iteritems():
            client = self.clients.getByCID(cid)
            c_guid = c.get('guid', None)
            if client:
                if c_guid == client.guid:
                    self.debug('Client found on server %s' % client.name)
                    mlist[cid] = client
                    self.debug ('Lobby is %s ' % c['lobby'])
                    if c['lobby'] and client.team != self.getTeam('lobby'):
                        self.debug('Putting in Lobby')
                        client.team = self.getTeam('lobby')
                    elif client.team == self.getTeam('lobby') and not c['lobby']:
                        self.debug('Removing from Lobby')
                        client.team = self.getTeam('unknown')
                else:
                    # Wrong client in slot
                    self.debug('Removing %s from list' % client.name)
                    client.disconnect()
            else:
                self.debug('Look for client in storage')
                cl = None
                if c_guid:
                    c_verified = c.get('verified', None)
                    c_ip = c.get('ip', None)
                    if c_verified == 'OK' or self._useunverifiedguid:
                        cl = self.getClient(c['name'], guid=c_guid, cid=c['cid'], ip=c_ip)
                    elif c_ip:
                        # case where guid is not verified but as we have an IP we can try to verify it ourselve
                        client_matches = self.storage.getClientsMatching({'guid': c_guid, 'ip': c_ip})
                        if len(client_matches) == 1:
                            # assume that guid is OK as it matches a known client entry in database with that same IP
                            cl = self.getClient(c['name'], guid=c_guid, cid=c['cid'], ip=c_ip)
                        else:
                            cl = self.getClient(c['name'], guid=None, cid=c['cid'], ip=c_ip)
                    else:
                        cl = self.getClient(c['name'], guid=None, cid=c['cid'], ip=c_ip)
                if cl:
                    mlist[cid] = cl
                    
        # Now we need to remove any players that have left
        if self.clients:
            client_cid_list = []

            for cl in plist.values():
                client_cid_list.append(cl['cid'])

            for client in self.clients.getList():

                if client.cid not in client_cid_list:
                    self.debug('Removing %s from list' % client.name)
                    client.disconnect()
        self.queueEvent(b3.events.Event(b3.events.EVT_PLAYER_SYNC_COMPLETED, None, None))
        
        return mlist


    def say(self, msg):
        self.sayqueue.put(msg)


    def saybig(self, msg):
        """\
        broadcast a message to all players in a way that will catch their attention.
        """
        self.say(msg)


    def kick(self, client, reason='', admin=None, silent=False, *kwargs):
        #'kick': ('kick ', '%(cid)s', '%(reason)s'),

        self.debug('kick reason: [%s]' % reason)
        if isinstance(client, str):
            self.write(self.getCommand('kick', cid=client, reason=reason[:80]))
            return
        
        if admin:
            fullreason = self.getMessage('kicked_by', self.getMessageVariables(client=client, reason=reason, admin=admin))
        else:
            fullreason = self.getMessage('kicked', self.getMessageVariables(client=client, reason=reason))
        fullreason = self.stripColors(fullreason)
        reason = self.stripColors(reason)

        self.write(self.getCommand('kick', cid=client.cid, reason=reason[:80]))

        if not silent and fullreason != '':
            self.say(fullreason)


    def message(self, client, text):
        if client:
            for line in self.getWrap(self.stripColors(self.msgPrefix + ' ' + text), self._settings['line_length'], self._settings['min_wrap_length']):
                self.write(self.getCommand('message', cid=client.cid, message=line))


    def ban(self, client, reason='', admin=None, silent=False, *kwargs):
        """Permanent ban"""
        #'ban': ('ban ', '%(cid)s', '0', '%(reason)s'),
        #'banByGUID': ('ban ', '%(guid)s', '0', '%(reason)s'),

        self.debug('BAN : client: %s, reason: %s', client, reason)

        if admin:
            fullreason = self.getMessage('banned_by', self.getMessageVariables(client=client, reason=reason, admin=admin))
        else:
            fullreason = self.getMessage('banned', self.getMessageVariables(client=client, reason=reason))
        fullreason = self.stripColors(fullreason)
        reason = self.stripColors(reason)

        if client.cid is None:
            # ban by guid, this happens when we !permban @xx a player that is not connected
            self.debug('EFFECTIVE BAN : %s',self.getCommand('banByGUID', guid=client.guid, reason=reason[:80]))
            try:
                self.write(self.getCommand('banByGUID', guid=client.guid, reason=reason[:80]))
                self.write(('writeBans',))
                if admin:
                    admin.message('banned: %s (@%s) has been added to banlist' % (client.exactName, client.id))
            except CommandFailedError, err:
                self.error(err)
        else:
            # ban by cid
            self.debug('EFFECTIVE BAN : %s',self.getCommand('ban', cid=client.cid, reason=reason[:80]))
            try:
                self.write(self.getCommand('ban', cid=client.cid, reason=reason[:80]))
                self.write(('writeBans',))
                if admin:
                    admin.message('banned: %s (@%s) has been added to banlist' % (client.exactName, client.id))
            except CommandFailedError, err:
                self.error(err)

        
        if not silent and fullreason != '':
            self.say(fullreason)
        
        self.queueEvent(b3.events.Event(b3.events.EVT_CLIENT_BAN, {'reason': reason, 'admin': admin}, client))


    def unban(self, client, reason='', admin=None, silent=False, *kwargs):
        if not client or not client.guid:
            return
        bans = self.getBanlist()
        if not client.guid in bans:
            if admin:
                admin.message("%s guid not found in banlist" % client.guid)
            return

        ban_entry = bans[client.guid]
        self.debug('UNBAN: ban index: %s, Name: %s, Guid: %s' %(ban_entry['ban_index'], client.name, client.guid))
        try:
            self.write(self.getCommand('unban', ban_no=ban_entry['ban_index'], reason=reason))
            self.write(('writeBans',))
            #self.verbose(response)
            self.verbose('UNBAN: Removed ban (%s) guid from banlist' % ban_entry['ban_index'])
            if admin:
                admin.message('Unbanned: Removed %s guid from banlist' % client.exactName)
        except CommandFailedError, err:
            if "NotInList" in err.message:
                if admin:
                    admin.message("ban not found in banlist")
            else:
                raise


    def tempban(self, client, reason='', duration=2, admin=None, silent=False, *kwargs):
        #'tempban': ('ban ', '%(cid)s', '%(duration)d', '%(reason)s'),
        #'tempbanByGUID': ('ban ', '%(guid)s', '%(duration)d', '%(reason)s'),
        duration = b3.functions.time2minutes(duration)
        if duration < 1:
            # Ban with length of zero will permban a player with Battleye, so do not activate the ban
            return

        if admin:
            fullreason = self.getMessage('temp_banned_by', self.getMessageVariables(client=client, reason=reason, admin=admin, banduration=b3.functions.minutesStr(duration)))
        else:
            fullreason = self.getMessage('temp_banned', self.getMessageVariables(client=client, reason=reason, banduration=b3.functions.minutesStr(duration)))
        fullreason = self.stripColors(fullreason)
        reason = self.stripColors(reason)

        if client.cid is None:
            # ban by guid, this happens when we !tempban @xx a player that is not connected
            try:
                self.write(self.getCommand('tempbanByGUID', guid=client.guid, duration=duration, reason=reason[:80]))
                self.write(('writeBans',))
            except CommandFailedError, err:
                if admin:
                    admin.message("server replied with error %s" % err.message[0])
                else:
                    self.error(err)
        else:
            try:
                self.write(self.getCommand('tempban', cid=client.cid, duration=duration, reason=reason[:80]))
                self.write(('writeBans',))
            except CommandFailedError, err:
                if admin:
                    admin.message("server replied with error %s" % err.message[0])
                else:
                    self.error(err)

        if not silent and fullreason != '':
            self.say(fullreason)

        self.queueEvent(b3.events.Event(b3.events.EVT_CLIENT_BAN_TEMP, {'reason': reason, 
                                                              'duration': duration, 
                                                              'admin': admin}
                                        , client))

 
    def getMap(self):
        """Return the current level name (not easy map name)"""
        pass


    def getMaps(self):
        """Return the map list for the current rotation. (as easy map names)
        This does not return all available maps
        """
        pass


    def rotateMap(self):
        """\
        load the next map/level
        """
        pass

    def changeMap(self, map_name, gamemode_id=None):
        """\
        load a given map/level
        return a list of suggested map names in cases it fails to recognize the map that was provided
        """
        pass

        
    def getPlayerPings(self):
        """Ask the server for all clients' pings"""
        #Players on server:
        #[#] [IP Address]:[Port] [Ping] [GUID] [Name]\n--------------------------------------------------
        #0   76.108.91.78:2304     63   80a5885ebe2420bab5e158a310fcbc7d(OK) Bravo17
        #0   192.168.0.100:2316    0    80a5885ebe2420bab5e158a310fcbc7d(OK) Bravo17 (Lobby)
        #(1 players in total)
        pings = {}
        player_list = self.output.write("players")
        for m in re.finditer(self.re_playerlist, player_list):
            if not m.group('lobby'):
                try:
                    pings[m.group('cid')] = int(m.group('ping'))
                except ValueError:
                    pass
        return pings


    def getPlayerScores(self):
        """Ask the server for a given client's team
        """
        scores = {}
        pass

    def getTeam(self, team):
        if team == '0':
            result = b3.TEAM_RED
        elif team == '1':
            result = b3.TEAM_BLUE
        elif team == 'lobby':
            result = b3.TEAM_SPEC
        elif team == 'unknown':
            result = b3.TEAM_UNKNOWN
        else:
            result = b3.TEAM_UNKNOWN
        return result
        

    ###############################################################################################
    #
    #    Other methods
    #    
    ###############################################################################################

    def getBanlist(self):
        #GUID Bans:
        #[#] [GUID] [Minutes left] [Reason]
        #----------------------------------------
        #0  b57cb4973da76f4588936416aae2de05 perm Script Detection: Gerk
        #1  8ac69e7189ecd2ff4235142feff0bd26 perm Script Detection: setVehicleInit DoThis;
        bans = {}
        raw_bans = self.output.write("bans")
        for m in re.finditer(r'''^\s*(?P<ban_index>\d+)\s+(?P<guid>[a-fA-F0-9]+)\s+(?P<min_left>\S+)\s+(?P<reason>.*)$''', raw_bans, re.MULTILINE):
            bans[m.group('guid')] = m.groupdict()
        return bans



    def load_conf_max_say_line_length(self):
        if self.config.has_option(self.gameName, 'max_say_line_length'):
            try:
                maxlength = self.config.getint(self.gameName, 'max_say_line_length')
                if maxlength > self.SAY_LINE_MAX_LENGTH:
                    self.warning('max_say_line_length cannot be greater than %s' % self.SAY_LINE_MAX_LENGTH)
                    maxlength = self.SAY_LINE_MAX_LENGTH
                if maxlength < 20:
                    self.warning('max_say_line_length is way too short. using minimum value 20')
                    maxlength = 20
                self._settings['line_length'] = maxlength
                self._settings['min_wrap_length'] = maxlength
            except Exception, err:
                self.error('failed to read max_say_line_length setting "%s" : %s' % (
                    self.config.get(self.gameName, 'max_say_line_length'), err))
        self.debug('line_length: %s' % self._settings['line_length'])


    def load_config_message_delay(self):
        if self.config.has_option(self.gameName, 'message_delay'):
            try:
                delay_sec = self.config.getfloat(self.gameName, 'message_delay')
                if delay_sec > 3:
                    self.warning('message_delay cannot be greater than 3')
                    delay_sec = 3
                if delay_sec < .5:
                    self.warning('message_delay cannot be less than 0.5 second.')
                    delay_sec = .5
                self._settings['message_delay'] = delay_sec
            except Exception, err:
                self.error(
                    'failed to read message_delay setting "%s" : %s' % (self.config.get(self.gameName, 'message_delay'), err))
        self.debug('message_delay: %s' % self._settings['message_delay'])
        
        
    def load_protocol_logging(self):
        """
        Allow extra logging from protocol.py to be activaed
        """
        if self.config.has_option('b3', 'protocol_log'):
            logfile = self.config.getpath('b3', 'protocol_log')
            return logfile
        else:
            return None
        
    def load_use_unverified_guid(self):
        if self.config.has_option('b3', 'use_unverified_guid'):
            self._useunverifiedguid = self.config.getboolean('b3', 'use_unverified_guid')

        self.debug('Use unverified GUID %s' % self._useunverifiedguid)
        
    def shutdown(self):
        """Shutdown B3"""
        try:
            if self.working and self.exiting.acquire():
                self.bot('Shutting down...')
                self.queueEvent(b3.events.Event(b3.events.EVT_STOP, None))
                for k,plugin in self._plugins.items():
                    self.debug('Stop event running for plugin %s' % plugin)
                    plugin.parseEvent(b3.events.Event(b3.events.EVT_STOP, ''))
                self.bot('Stopping any cron jobs still running....')
                if self._cron:
                    self._cron.stop()

                self.bot('Shutting down database connections...')
                self.storage.shutdown()
        except Exception, e:
            self.error(e)

            
    def restart(self):
        """Stop B3 with the restart exit status (221)"""
        # Need to set this so that if restart is called from within a plugin, and there is no event, exitcode is correctly set
        self.exitcode = 221
        self.shutdown()

        time.sleep(5)

        self.bot('Restarting...')

        sys.exit(221)

    def getWrap(self, text, length=None, minWrapLen=None):
        """Returns a sequence of lines for text that fits within the limits
        """
        if not text:
            return []

        if length is None:
            length = self._settings['line_length']

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




