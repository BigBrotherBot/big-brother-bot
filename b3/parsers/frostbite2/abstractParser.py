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
__author__  = 'Courgette'
__version__ = '0.5'


import sys, re, traceback, time, string, Queue, threading
import b3.parser
from b3.parsers.frostbite2.rcon import Rcon as FrostbiteRcon
from b3.parsers.frostbite2.protocol import FrostbiteServer, CommandFailedError, CommandError, NetworkError
from b3.parsers.frostbite2.util import PlayerInfoBlock, MapListBlock, BanlistContent
import b3.events
import b3.cvar
from b3.functions import soundex, levenshteinDistance

SAY_LINE_MAX_LENGTH = 100

# how long should the bot try to connect to the Frostbite server before giving out (in second)
GAMESERVER_CONNECTION_WAIT_TIMEOUT = 600

class AbstractParser(b3.parser.Parser):
    """
    An abstract base class to help with developing frostbite2 parsers
    """

    gameName = None

    OutputClass = FrostbiteRcon
    _serverConnection = None
    _nbConsecutiveConnFailure = 0

    frostbite_event_queue = Queue.Queue(400)
    sayqueue = Queue.Queue(100)
    sayqueuelistener = None

    # frostbite2 engine does not support color code, so we need this property
    # in order to get stripColors working
    _reColor = re.compile(r'(\^[0-9])')

    _settings = {
        'line_length': 128,
        'min_wrap_length': 128,
        'message_delay': .8,
        }

    _gameServerVars = () # list available cvar

    _commands = {
        'message': ('admin.say', '%(message)s', 'all', '%(cid)s'), # TODO : send private messages when available
        'saySquad': ('admin.say', '%(message)s', 'squad', '%(teamId)s', '%(squadId)s'),
        'sayTeam': ('admin.say', '%(message)s', 'team', '%(teamId)s'),
        'say': ('admin.say', '%(message)s', 'all'),
        'kick': ('admin.kickPlayer', '%(cid)s', '%(reason)s'),
        'ban': ('banList.add', 'guid', '%(guid)s', 'perm', '%(reason)s'),
        'banByIp': ('banList.add', 'ip', '%(ip)s', 'perm', '%(reason)s'),
        'unban': ('banList.remove', 'guid', '%(guid)s'),
        'unbanByIp': ('banList.remove', 'ip', '%(ip)s'),
        'tempban': ('banList.add', 'guid', '%(guid)s', 'seconds', '%(duration)d', '%(reason)s'),
    }

    _eventMap = {
    }

    _punkbusterMessageFormats = (
        (re.compile(r'^(?P<servername>.*): PunkBuster Server for .+ \((?P<version>.+)\)\sEnabl.*$'), 'OnPBVersion'),
        (re.compile(r'^(?P<servername>.*): Running PB Scheduled Task \(slot #(?P<slot>\d+)\)\s+(?P<task>.*)$'), 'OnPBScheduledTask'),
        (re.compile(r'^(?P<servername>.*): Lost Connection \(slot #(?P<slot>\d+)\) (?P<ip>[^:]+):(?P<port>\d+) (?P<pbuid>[^\s]+)\(-\)\s(?P<name>.+)$'), 'OnPBLostConnection'),
        (re.compile(r'^(?P<servername>.*): Master Query Sent to \((?P<pbmaster>[^\s]+)\) (?P<ip>[^:]+)$'), 'OnPBMasterQuerySent'),
        (re.compile(r'^(?P<servername>.*): Player GUID Computed (?P<pbid>[0-9a-fA-F]+)\(-\) \(slot #(?P<slot>\d+)\) (?P<ip>[^:]+):(?P<port>\d+)\s(?P<name>.+)$'), 'OnPBPlayerGuid'),
        (re.compile(r'^(?P<servername>.*): New Connection \(slot #(?P<slot>\d+)\) (?P<ip>[^:]+):(?P<port>\d+) \[(?P<something>[^\s]+)\]\s"(?P<name>.+)".*$'), 'OnPBNewConnection'),
        (re.compile(r'^PunkBuster Server:\s+(?P<index>\d+)\s+(?P<pbid>[0-9a-fA-F]+) {(?P<min_elapsed>\d+)/(?P<duration>\d+)}\s+"(?P<name>[^"]+)"\s+"(?P<ip>[^:]+):(?P<port>\d+)"\s+"?(?P<reason>.*)"\s+"(?P<private_reason>.*)"$'), None), # banlist item
        (re.compile(r'^PunkBuster Server: Guid=(?P<search>.*) Not Found in the Ban List$'), None),
        (re.compile(r'^PunkBuster Server: End of Ban List \(\d+ of \d+ displayed\)$'), None),
        (re.compile(r'^PunkBuster Server: Guid (?P<pbid>[0-9a-fA-F]+) has been Unbanned$'), None),
        (re.compile(r'^PunkBuster Server: PB UCON "(?P<from>.+)"@(?P<ip>[\d.]+):(?P<port>\d+) \[(?P<cmd>.*)\]$'), 'OnPBUCON'),
        (re.compile(r'^PunkBuster Server: Player List: \[Slot #\] \[GUID\] \[Address\] \[Status\] \[Power\] \[Auth Rate\] \[Recent SS\] \[O/S\] \[Name\]$'), None),
        (re.compile(r'^PunkBuster Server: (?P<slot>\d+)\s+(?P<pbid>[0-9a-fA-F]+)\(-\) (?P<ip>[^:]+):(?P<port>\d+) (?P<status>.+)\s+(?P<power>\d+)\s+(?P<authrate>\d+\.\d+)\s+(?P<recentSS>\d+)\s+\((?P<os>.+)\)\s+"(?P<name>.+)".*$'), 'OnPBPlistItem'),
        (re.compile(r'^PunkBuster Server: End of Player List \(\d+ Players\)$'), None),
        (re.compile(r'^PunkBuster Server: Invalid Player Specified: (?P<data>.*)$'), None),
        (re.compile(r'^PunkBuster Server: Received Download File: (?P<file>.*)$'), None),
        (re.compile(r'^PunkBuster Server: Matched: (?P<name>.*) \(slot #(?P<slot>\d+)\)$'), None),
        (re.compile(r'^PunkBuster Server: (?P<num>\d+) Ban Records Updated in (?P<filename>.*)$'), None),
        (re.compile(r'^PunkBuster Server: Ban Added to Ban List$'), None),
        (re.compile(r'^PunkBuster Server: Ban Failed$'), None),
        (re.compile(r'^PunkBuster Server: Received Master Security Information$'), None),
        (re.compile(r'^PunkBuster Server: Auto Screenshot\s+(?P<ssid>\d+)\s+Requested from (?P<slot>\d+) (?P<name>.+)$'), None),
        (re.compile(r'^PunkBuster Server: Screenshot (?P<imgpath>.+)\s+successfully received \(MD5=(?P<md5>[0-9A-F]+)\) from (?P<slot>\d+) (?P<name>.+) \[(?P<pbid>[0-9a-fA-F]+)\(-\) (?P<ip>[^:]+):(?P<port>\d+)\]$'), 'OnPBScreenshotReceived'),
    )

    # if Punkbuster is set, then it will be used to kick/ban/unban
    PunkBuster = None
    # if ban_with_server is True, then the Frostbite server will be used for ban
    ban_with_server = True

    # flag to find out if we need to fire a EVT_GAME_ROUND_START event.
    _waiting_for_round_start = True


    def __new__(cls, *args, **kwargs):
        AbstractParser.patch_b3_Clients_getByMagic()
        return b3.parser.Parser.__new__(cls)

    @staticmethod
    def patch_b3_Clients_getByMagic():
        """
        The b3.clients.Client.getByMagic method does not behave as intended for Frostbive server when id is a string
        composed of digits exclusively. In such case it behave as if id was a slot number as for Quake3 servers.
        This method patches the self.clients object so that it getByMagic method behaves as expected for Frostbite servers.
        """
        def new_clients_getByMagic(self, id):
            id = id.strip()

            if re.match(r'^@([0-9]+)$', id):
                return self.getByDB(id)
            elif id[:1] == '\\':
                c = self.getByName(id[1:])
                if c and not c.hide:
                    return [c]
                else:
                    return []
            else:
                return self.getClientsByName(id)
        b3.clients.Clients.getByMagic = new_clients_getByMagic


    def run(self):
        """Main worker thread for B3"""
        self.bot('Start listening ...')
        self.screen.write('Startup Complete : B3 is running! Let\'s get to work!\n\n')
        self.screen.write('(If you run into problems, check %s for detailed log info)\n' % self.config.getpath('b3', 'logfile'))
        #self.screen.flush()

        self.updateDocumentation()

        ## the block below can activate additional logging for the FrostbiteServer class
#        import logging
#        frostbiteServerLogger = logging.getLogger("FrostbiteServer")
#        for handler in logging.getLogger('output').handlers:
#            frostbiteServerLogger.addHandler(handler)
#        frostbiteServerLogger.setLevel(logging.getLogger('output').level)

        while self.working:
            if not self._serverConnection or not self._serverConnection.connected:
                try:
                    self.setup_frostbite_connection()
                except CommandError, err:
                    if err.message[0] == 'InvalidPasswordHash':
                        self.error("your rcon password is incorrect. Check setting 'rcon_password' in your main config file.")
                        self.exitcode = 220
                        break
                    else:
                        self.error(err.message)
                except IOError, err:
                    self.error("IOError %s"% err)
                except Exception, err:
                    self.error(err)
                    self.exitcode = 220
                    break

            try:
                added, expire, packet = self.frostbite_event_queue.get(timeout=5)
                self.routeFrostbitePacket(packet)
            except Queue.Empty:
                self.verbose2("no game server event to treat in the last 5s")
            except CommandError, err:
                # it does not matter from the parser perspective if Frostbite command failed
                # (timeout or bad reply)
                self.warning(err)
            except NetworkError, e:
                # the connection to the frostbite server is lost
                self.warning(e)
                self.close_frostbite_connection()
            except Exception, e:
                self.error("unexpected error, please report this on the B3 forums")
                self.error(e)
                # unexpected exception, better close the frostbite connection
                self.close_frostbite_connection()


        self.info("Stop listening for Frostbite2 events")
        # exiting B3
        with self.exiting:
            # If !die or !restart was called, then  we have the lock only after parser.handleevent Thread releases it
            # and set self.working = False and this is one way to get this code is executed.
            # Else there was an unhandled exception above and we end up here. We get the lock instantly.

            self.output.frostbite_server = None

            # The Frostbite connection is running its own thread to communicate with the game server. We need to tell
            # this thread to stop.
            self.close_frostbite_connection()

            # If !die was called, exitcode have been set to 222
            # If !restart was called, exitcode have been set to 221
            # In both cases, the SystemExit exception that triggered exitcode to be filled with an exit value was
            # caught. Now that we are sure that everything was gracefully stopped, we can re-raise the SystemExit
            # exception.
            if self.exitcode:
                sys.exit(self.exitcode)

    def setup_frostbite_connection(self):
        self.info('Connecting to frostbite2 server ...')
        if self._serverConnection:
            self.close_frostbite_connection()
        self._serverConnection = FrostbiteServer(self._rconIp, self._rconPort, self._rconPassword)

        timeout = GAMESERVER_CONNECTION_WAIT_TIMEOUT + time.time()
        while time.time() < timeout and not self._serverConnection.connected:
            self.info("retrying to connect to game server...")
            time.sleep(2)
            self.close_frostbite_connection()
            self._serverConnection = FrostbiteServer(self._rconIp, self._rconPort, self._rconPassword)

        if self._serverConnection is None or not self._serverConnection.connected:
            self.error("Could not connect to Frostbite2 server")
            self.close_frostbite_connection()
            self.shutdown()
            raise SystemExit()

        # listen for incoming game server events
        self._serverConnection.subscribe(self.OnFrosbiteEvent)

        self._serverConnection.auth()
        self._serverConnection.command('admin.eventsEnabled', 'true')

        # setup Rcon
        self.output.set_frostbite_server(self._serverConnection)

        self.checkVersion()
        self.say('%s ^2[ONLINE]' % b3.version)
        self.getServerInfo()
        self.getServerVars()
        self.clients.sync()

        # checkout punkbuster support
        try:
            result = self._serverConnection.command('punkBuster.isActive')
        except CommandError, e:
            self.error("could not get punkbuster status : %r" % e)
            self.PunkBuster = None
            self.ban_with_server = True
        else:
            if result and result[0] == 'true':
                self.write(('punkBuster.pb_sv_command', 'pb_sv_plist')) # will make punkbuster send IP address of currently connected players
            elif not self.ban_with_server:
                self.ban_with_server = True
                self.warning("Forcing ban agent to 'server' as we failed to verify that punkbuster is active on the server")

    def close_frostbite_connection(self):
        try:
            self._serverConnection.stop()
        except Exception:
            pass
        self._serverConnection = None

    def OnFrosbiteEvent(self, packet):
        if not self.working:
            self.verbose("dropping Frostbite event %r" % packet)
        self.console(repr(packet))
        try:
            self.frostbite_event_queue.put((self.time(), self.time() + 10, packet), timeout=2)
        except Queue.Full:
            self.error("Frostbite event queue full, dropping event %r" % packet)

    def routeFrostbitePacket(self, packet):
        if packet is None:
            self.warning('cannot route empty packet : %s' % traceback.extract_tb(sys.exc_info()[2]))
        eventType = packet[0]
        eventData = packet[1:]
        
        match = re.search(r"^(?P<actor>[^.]+)\.(on)?(?P<event>.+)$", eventType)
        func = None
        if match:
            func = 'On%s%s' % (string.capitalize(match.group('actor')), \
                               string.capitalize(match.group('event')))
            self.verbose2("looking for event handling method called : " + func)
            
        if match and hasattr(self, func):
            #self.verbose2('routing ----> %s(%r)' % (func,eventData))
            func = getattr(self, func)
            event = func(eventType, eventData)
            #self.debug('event : %s' % event)
            if event:
                self.queueEvent(event)
            
        elif eventType in self._eventMap:
            self.queueEvent(b3.events.Event(
                    self._eventMap[eventType],
                    eventData))
        else:
            data = ''
            if func:
                data = func + ' '
            data += str(eventType) + ': ' + str(eventData)
            self.warning('TODO : handle \'%r\' frostbite2 events' % packet)
            self.queueEvent(b3.events.Event(b3.events.EVT_UNKNOWN, data))


    def startup(self):
       
        # add specific events
        self.Events.createEvent('EVT_CLIENT_SQUAD_CHANGE', 'Client Squad Change')
        self.Events.createEvent('EVT_CLIENT_SPAWN', 'Client Spawn')
        self.Events.createEvent('EVT_GAME_ROUND_PLAYER_SCORES', 'round player scores')
        self.Events.createEvent('EVT_GAME_ROUND_TEAM_SCORES', 'round team scores')
        self.Events.createEvent('EVT_PUNKBUSTER_UNKNOWN', 'PunkBuster unknown')
        self.Events.createEvent('EVT_PUNKBUSTER_MISC', 'PunkBuster misc')
        self.Events.createEvent('EVT_PUNKBUSTER_SCHEDULED_TASK', 'PunkBuster scheduled task')
        self.Events.createEvent('EVT_PUNKBUSTER_LOST_PLAYER', 'PunkBuster client connection lost')
        self.Events.createEvent('EVT_PUNKBUSTER_NEW_CONNECTION', 'PunkBuster client received IP')
        self.Events.createEvent('EVT_PUNKBUSTER_UCON', 'PunkBuster UCON')
        self.Events.createEvent('EVT_PUNKBUSTER_SCREENSHOT_RECEIVED', 'PunkBuster Screenshot received')

        # setting up ban agent
        self.PunkBuster = None
        self.ban_with_server = True
        if self.config.has_option('server', 'ban_agent'):
            ban_agent = self.config.get('server', 'ban_agent')
            if ban_agent.lower() not in ('server', 'punkbuster', 'both'):
                self.warning("unexpected value '%s' for ban_agent config option. Expecting one of 'server', 'punkbuster', 'both'." % ban_agent)
            else:
                if ban_agent.lower() == 'server':
                    self.PunkBuster = None
                    self.ban_with_server = True
                    self.info("ban_agent is 'server' -> B3 will ban using the game server banlist")
                elif ban_agent.lower() == 'punkbuster':
                    from b3.parsers.frostbite2.punkbuster import PunkBuster
                    self.PunkBuster = PunkBuster(console=self)
                    self.ban_with_server = False
                    self.info("ban_agent is 'punkbuster' -> B3 will ban using the punkbuster banlist")
                elif ban_agent.lower() == 'both':
                    from b3.parsers.frostbite2.punkbuster import PunkBuster
                    self.PunkBuster = PunkBuster(console=self)
                    self.ban_with_server = True
                    self.info("ban_agent is 'both' -> B3 will ban using both the game server banlist and punkbuster")
                else:
                    self.error("unexpected value '%s' for ban_agent" % ban_agent)
        self.info("ban agent 'server' : %s" % ('activated' if self.ban_with_server else 'deactivated'))
        self.info("ban agent 'punkbuster' : %s" % ('activated' if self.PunkBuster else 'deactivated'))
        
        self.sayqueuelistener = threading.Thread(target=self.sayqueuelistener)
        self.sayqueuelistener.setDaemon(True)
        self.sayqueuelistener.start()

        # start crontab to trigger playerlist events
        self.cron + b3.cron.CronTab(self.clients.sync, minute='*/5')
    
    def sayqueuelistener(self):
        self.info("sayqueuelistener job started")
        while self.working:
            try:
                msg = self.sayqueue.get(timeout=40)
                for line in self.getWrap(self.stripColors(self.msgPrefix + ' ' + msg), self._settings['line_length'], self._settings['min_wrap_length']):
                    self.write(self.getCommand('say', message=line))
                    time.sleep(self._settings['message_delay'])
            except Queue.Empty:
                self.verbose2("sayqueuelistener: had nothing to do in the last 40 sec")
            except Exception, err:
                self.error(err)
        self.info("sayqueuelistener job ended")

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

    
    ###############################################################################################
    #
    #    Frostbite2 events handlers
    #    
    ###############################################################################################

    
    def OnPlayerChat(self, action, data):
        """
        player.onChat <source soldier name: string> <text: string>
        
        Effect: Player with name <source soldier name> (or the server, or the 
            server admin) has sent chat message <text> to some people
        
        Comment: If <source soldier name> is "Server", then the message was sent 
            from the server rather than from an actual player
        """
        client = self.getClient(data[0])
        if client is None:
            self.warning("Could not get client :( %s" % traceback.extract_tb(sys.exc_info()[2]))
            return
        if client.cid == 'Server':
            # ignore chat events for Server
            return
        return b3.events.Event(b3.events.EVT_CLIENT_SAY, data[1].lstrip('/'), client)
        

    def OnPlayerLeave(self, action, data):
        #player.onLeave: ['GunnDawg']
        client = self.getClient(data[0])
        if client: 
            client.endMessageThreads = True
            client.disconnect() # this triggers the EVT_CLIENT_DISCONNECT event
        return None

    def OnPlayerJoin(self, action, data):
        """
        player.onJoin <soldier name: string> <id : EAID>
        """
        # we receive this event very early and even before the game client starts to connect to the game server.
        # In some occasions, the game client fails to properly connect and the game server then fails to send
        # us a player.onLeave event resulting in B3 thinking the player is connected while it is not.
        # The fix is to ignore this event. If the game client successfully connect, then we'll receive other
        # events like player.onTeamChange or even a event from punkbuster which will create the Client object.
        pass

    def OnPlayerAuthenticated(self, action, data):
        """
        player.authenticated <soldier name: string> <EA_GUID: string>
        
        Effect: Player with name <soldier name> has been authenticated
        """
        try:
            _guid = data[1]
        except IndexError:
            _guid = None
        self.getClient(data[0], guid=_guid)


    def OnPlayerSpawn(self, action, data):
        """
        Request: player.onSpawn <spawning soldier name: string> <team: int>
        """
        if len(data) < 2:
            return None
        spawner = self.getClient(data[0])
        spawner.team = self.getTeam(data[1])

        self._OnServerLevelstarted(action=None, data=None)

        return b3.events.Event(b3.events.EVT_CLIENT_SPAWN, (), spawner)


    def OnPlayerKill(self, action, data):
        """
        Request: player.onKill <killing soldier name: string> 
            <killed soldier name: string> <weapon: string> <headshot: boolean>

        Effect: Player with name <killing soldier name> has killed 
            <killed soldier name> Suicide indication is unknown at this moment. 
            If the server kills the player (through admin.killPlayer), the result is unknown. 
        """
        # example suicide : ['Cucurbitaceae', 'Cucurbitaceae', 'M67', 'false']
        # example killed by fire : ['', 'Cucurbitaceae', 'DamageArea', 'false']
        if data[0] == '':
            data[0] = 'Server'
        attacker = self.getClient(data[0])
        if not attacker:
            self.debug('No attacker')
            return None

        victim = self.getClient(data[1])
        if not victim:
            self.debug('No victim')
            return None
        
        weapon = data[2]

        if data[3] == 'true':
            hitloc = 'head'
        else:
            hitloc = 'torso'

        event = b3.events.EVT_CLIENT_KILL
        if victim == attacker:
            event = b3.events.EVT_CLIENT_SUICIDE
        elif attacker.team == victim.team and attacker.team != b3.TEAM_UNKNOWN and attacker.team != b3.TEAM_SPEC:
            event = b3.events.EVT_CLIENT_KILL_TEAM
        return b3.events.Event(event, (100, weapon, hitloc), attacker, victim)


    def OnPlayerKicked(self, action, data):
        """
        Request: player.onKicked <soldier name: string> <reason: string>
        Effect: Player with name <soldier name> has been kicked
        """
        if len(data) < 2:
            return None
        client = self.getClient(data[0])
        reason = data[1]
        return b3.events.Event(b3.events.EVT_CLIENT_KICK, data=reason, client=client)


    def OnServerLevelloaded(self, action, data):
        """
        server.onLevelLoaded <level name: string> <gamemode: string> <roundsPlayed: int> <roundsTotal: int>

        Effect: Level has completed loading, and will start in a bit

        example: ['server.onLevelLoaded', 'MP_001', 'ConquestLarge0', '1', '2']
        """
        self.debug("OnServerLevelLoaded: %s" % data)
        if not self.game.mapName:
            self.game.mapName = data[0]
        if self.game.mapName != data[0]:
            # map change detected
            self.game.startMap()
        self.game.mapName = data[0]
        self.game.gameType = data[1]
        self.game.rounds = int(data[2]) + 1 # round index starts at 0
        self.game.g_maxrounds = int(data[3])
        self.getServerInfo()
        # to debug getEasyName()
        self.info('Loading %s [%s]'  % (self.getEasyName(self.game.mapName), self.game.gameType))
        self._waiting_for_round_start = True

        return b3.events.Event(b3.events.EVT_GAME_WARMUP, data[0])

    def _OnServerLevelstarted(self, action, data):
        """
        Event server.onLevelStarted was used to be sent in Frostbite1. Unfortunately it does not exists anymore
        in Frostbite2.
        Instead we call this method from OnPlayerSpawn and maintain a flag which tells if we need to fire the
        EVT_GAME_ROUND_START event
        """
        if self._waiting_for_round_start:
            self._waiting_for_round_start = False

            # as the game server provides us the exact round number in OnServerLoadinglevel()
            # hence we need to deduct one to compensate?
            # we'll still leave the call here since it provides us self.game.roundTime()
            # next function call will increase roundcount by one, this is not wanted
            self.game.startRound()
            self.queueEvent(b3.events.Event(b3.events.EVT_GAME_ROUND_START, self.game))

        
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

    def OnPunkbusterMessage(self, action, data):
        """handles all punkbuster related events and 
        route them to the appropriate method depending
        on the type of PB message.
        
        Request: punkBuster.onMessage <message: string>
        Effect: PunkBuster server has output a message
        Comment: The entire message is sent as a raw string. It may contain newlines and whatnot.
        """
        #self.debug("PB> %s" % data)
        if data and data[0]:
            for regexp, funcName in self._punkbusterMessageFormats:
                match = re.match(regexp, str(data[0]).strip())
                if match:
                    break
            if match:
                if funcName is None:
                    return b3.events.Event(b3.events.EVT_PUNKBUSTER_MISC, match)
                if hasattr(self, funcName):
                    func = getattr(self, funcName)
                    return func(match, data[0])
                else:
                    self.warning("func %s not found, defaulting to EVT_PUNKBUSTER_UNKNOWN" % funcName)
                    return b3.events.Event(b3.events.EVT_PUNKBUSTER_UNKNOWN, data)
            else:
                self.debug("no pattern matching \"%s\", defaulting to EVT_PUNKBUSTER_UNKNOWN" % str(data[0]).strip())
                return b3.events.Event(b3.events.EVT_PUNKBUSTER_UNKNOWN, data)
                
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
        """PB notifies us it lost track of a player.
        This event is triggered after the OnPlayerLeave, so normaly the client
        is not connected. Anyway our task here is to raise an event not to
        connect/disconnect the client.
        """
        name = match.group('name')
        dict = {
            'slot': match.group('slot'),
            'ip': match.group('ip'),
            'port': match.group('port'),
            'pbuid': match.group('pbuid'),
            'name': name
        }
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
        if client:
            client.ip = ip
            client.pbid = pbid
            if not client.guid:
                # a bug in the BF3 server can make admin.listPlayers response reply with players having an
                # empty string as guid. What we can do here is to try to get the guid from the pbid in the
                # B3 database.
                try:
                    matching_clients = self.console.storage.getClientsMatching({'pbid': pbid})
                    if len(matching_clients) == 0:
                        self.debug("no client found by pbid")
                    elif len(matching_clients) > 1:
                        self.debug("too many clients found by pbid")
                    else:
                        client.guid = matching_clients[0].guid
                        client.auth()
                except Exception, err:
                    self.warning("failed to try to auth %s by pbid. %r" % (name, err))
            client.save()

    def OnPBPlistItem(self, match, data):
        """we received one of the line containing details about one player"""
        self.OnPBPlayerGuid(match, data)

    def OnPBUCON(self, match, data):
        """We get notified of a UCON command
        match groups : from, ip, port, cmd
        """
        return b3.events.Event(b3.events.EVT_PUNKBUSTER_UCON, match.groupdict())

    def OnPBScreenshotReceived(self, match, data):
        """We get notified that a screenshot was successfully received by the server"""
        return b3.events.Event(b3.events.EVT_PUNKBUSTER_SCREENSHOT_RECEIVED, match.groupdict())


    ###############################################################################################
    #
    #    B3 Parser interface implementation
    #    
    ###############################################################################################

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


    def say(self, msg):
        self.sayqueue.put(msg)

    def saybig(self, msg):
        """\
        broadcast a message to all players in a way that will catch their attention.
        """
        raise NotImplementedError


    def kick(self, client, reason='', admin=None, silent=False, *kwargs):
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

        if self.PunkBuster:
            self.PunkBuster.kick(client, 0.5, reason)

        self.write(self.getCommand('kick', cid=client.cid, reason=reason[:80]))

        if not silent and fullreason != '':
            self.say(fullreason)


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


    def ban(self, client, reason='', admin=None, silent=False, *kwargs):
        """Permanent ban"""
        self.debug('BAN : client: %s, reason: %s', client, reason)
        if isinstance(client, str):
            traceback.print_stack() # TODO: remove this stack trace when we figured out when tempban is called with a str as client
            self.write(self.getCommand('ban', guid=client, reason=reason[:80]))
            return

        if admin:
            fullreason = self.getMessage('banned_by', self.getMessageVariables(client=client, reason=reason, admin=admin))
        else:
            fullreason = self.getMessage('banned', self.getMessageVariables(client=client, reason=reason))
        fullreason = self.stripColors(fullreason)
        reason = self.stripColors(reason)

        if self.ban_with_server:
            if client.cid is None:
                # ban by ip, this happens when we !permban @xx a player that is not connected
                self.debug('EFFECTIVE BAN : %s',self.getCommand('banByIp', ip=client.ip, reason=reason[:80]))
                try:
                    self.write(self.getCommand('banByIp', ip=client.ip, reason=reason[:80]))
                    self.write(('banList.save',))
                    if admin:
                        admin.message('banned: %s (@%s). His last ip (%s) has been added to banlist'%(client.exactName, client.id, client.ip))
                except CommandFailedError, err:
                    self.error(err)
            else:
                # ban by guid
                self.debug('EFFECTIVE BAN : %s',self.getCommand('ban', guid=client.guid, reason=reason[:80]))
                try:
                    self.write(self.getCommand('ban', guid=client.guid, reason=reason[:80]))
                    self.write(('banList.save',))
                    if admin:
                        admin.message('banned: %s (@%s) has been added to banlist'%(client.exactName, client.id))
                except CommandFailedError, err:
                    self.error(err)

        if self.PunkBuster:
            self.PunkBuster.banGUID(client, reason)
            # Also issue a server kick in case we do not ban with the server and punkbuster fails
            if client.cid: # only if client is currently connected
                self.write(self.getCommand('kick', cid=client.cid, reason=reason[:80]))
        
        if not silent and fullreason != '':
            self.say(fullreason)
        
        self.queueEvent(b3.events.Event(b3.events.EVT_CLIENT_BAN, {'reason': reason, 'admin': admin}, client))


    def unban(self, client, reason='', admin=None, silent=False, *kwargs):
        self.debug('UNBAN: Name: %s, Ip: %s, Guid: %s' %(client.name, client.ip, client.guid))
        if client.ip:
            try:
                response = self.write(self.getCommand('unbanByIp', ip=client.ip, reason=reason), needConfirmation=True)
                self.write(('banList.save',))
                #self.verbose(response)
                self.verbose('UNBAN: Removed ip (%s) from banlist' %client.ip)
                if admin:
                    admin.message('Unbanned: %s. His last ip (%s) has been removed from banlist.' % (client.exactName, client.ip))
                if admin:
                    fullreason = self.getMessage('unbanned_by', self.getMessageVariables(client=client, reason=reason, admin=admin))
                else:
                    fullreason = self.getMessage('unbanned', self.getMessageVariables(client=client, reason=reason))
                if not silent and fullreason != '':
                    self.say(fullreason)
            except CommandFailedError, err:
                if "NotInList" in err.message:
                    pass
                else:
                    raise

        try:
            response = self.write(self.getCommand('unban', guid=client.guid, reason=reason), needConfirmation=True)
            self.write(('banList.save',))
            #self.verbose(response)
            self.verbose('UNBAN: Removed guid (%s) from banlist' %client.guid)
            if admin:
                admin.message('Unbanned: Removed %s guid from banlist' % (client.exactName))
        except CommandFailedError, err:
            if "NotInList" in err.message:
                pass
            else:
                raise

        if self.PunkBuster:
            self.PunkBuster.unBanGUID(client)


    def tempban(self, client, reason='', duration=2, admin=None, silent=False, *kwargs):
        duration = b3.functions.time2minutes(duration)

        if isinstance(client, str):
            traceback.print_stack() # TODO: remove this stack trace when we figured out when tempban is called with a str as client
            self.write(self.getCommand('tempban', guid=client.guid, duration=duration*60, reason=reason[:80]))
            return
        
        if admin:
            fullreason = self.getMessage('temp_banned_by', self.getMessageVariables(client=client, reason=reason, admin=admin, banduration=b3.functions.minutesStr(duration)))
        else:
            fullreason = self.getMessage('temp_banned', self.getMessageVariables(client=client, reason=reason, banduration=b3.functions.minutesStr(duration)))
        fullreason = self.stripColors(fullreason)
        reason = self.stripColors(reason)

        if self.PunkBuster:
            if client.cid is not None: # only if player is currently on the server
                # punkbuster acts odd if you ban for more than a day
                # tempban for a day here and let b3 re-ban if the player
                # comes back
                if duration > 1440:
                    duration = 1440
                self.PunkBuster.kick(client, duration, reason)
                # Also issue a server kick in case we do not ban with the server and punkbuster fails
                self.write(self.getCommand('kick', cid=client.cid, reason=reason[:80]))

        if self.ban_with_server:
            try:
                self.write(self.getCommand('tempban', guid=client.guid, duration=duration*60, reason=reason[:80]))
                self.write(('banList.save',))
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
        self.getServerInfo()
        return self.game.mapName


    def getMaps(self):
        """Return the map list for the current rotation. (as easy map names)
        This does not return all available maps
        """
        response = []
        for map_list in self.getFullMapRotationList():
            response.append('%s (%s)' % (self.getEasyName(map_list['name']), self.getGameMode(map_list['gamemode'])))
        return response


    def rotateMap(self):
        """\
        load the next map/level
        """
        maplist = self.getFullMapRotationList()
        if not len(maplist):
            # maplist is empty, fix this situation by loading save mapList from disk
            try:
                self.write(('mapList.load',))
            except Exception, err:
                self.warning(err)
            maplist = self.getFullMapRotationList()
            if not len(maplist):
                # maplist is still empty, fix this situation by adding current map to map list
                current_max_rounds = self.write(('mapList.getRounds',))[1]
                self.write(('mapList.add', self.game.mapName, self.game.gameType, current_max_rounds, 0))
        mapIndices = self.write(('mapList.getMapIndices', ))
        self.write(('mapList.setNextMapIndex', mapIndices[1]))
        self.write(('mapList.runNextRound',))
        # we create a EVT_GAME_ROUND_END event as the game server won't make one.
        # https://github.com/courgette/big-brother-bot/issues/52
        self.queueEvent(b3.events.Event(b3.events.EVT_GAME_ROUND_END, data=None))


    def changeMap(self, map):
        """\
        load a given map/level
        return a list of suggested map names in cases it fails to recognize the map that was provided
        
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
        supportedMaps = self.getSupportedMapIds()
        if map not in supportedMaps:
            match = self.getMapsSoundingLike(map)
            if len(match) == 1:
                map = match[0]
            else:
                return match
            
        if map in supportedMaps:
            mapList = self.getFullMapRotationList()

            # we want to find the next index to set for mapList
            nextMapListIndex = None

            # simple case : mapList is empty. Then just add our map at index 0 and load it
            if not len(mapList):
                nextMapListIndex = 0
                self.write(('mapList.add', map, self.game.gameType, 2, nextMapListIndex))
            else:
                # the wanted map could already be in the rotation list (for the current gamemode)
                maps_for_current_gamemode = mapList.getByNameAndGamemode(map, self.game.gameType)
                if len(maps_for_current_gamemode):
                    nextMapListIndex = maps_for_current_gamemode.keys()[0]

                # or it could be in map rotation list for another gamemode
                if nextMapListIndex is None:
                    filtered_mapList = mapList.getByName(map)
                    if len(filtered_mapList):
                        nextMapListIndex = filtered_mapList.keys()[0]

                # or map is not found in mapList and we need to insert it after the index of the current map
                current_index = self.write(('mapList.getMapIndices',))[0]
                nextMapListIndex = int(current_index) + 1
                self.write(('mapList.add', map, self.game.gameType, 2, nextMapListIndex))

            # now we have a nextMapListIndex correctly set to the wanted map
            self.write(('mapList.setNextMapIndex', nextMapListIndex))
            self.say('Changing map to %s (%s)' % (self.getEasyName(map), self.getGameMode(self.game.gameType)))
            time.sleep(1)
            self.write(('mapList.runNextRound',))

        
    def getPlayerPings(self):
        """Ask the server for a given client's pings
        """
        raise NotImplementedError # TODO : implement getPlayerPings when BF3 allows this
        pings = {}
        try:
            pib = PlayerInfoBlock(self.write(('admin.listPlayers', 'all')))
            for p in pib:
                pings[p['name']] = int(p['ping'])
        except Exception, e:
            self.debug('Unable to retrieve pings from playerlist (%r)' % e)
        return pings


    def getPlayerScores(self):
        """Ask the server for a given client's team
        """
        scores = {}
        try:
            pib = PlayerInfoBlock(self.write(('admin.listPlayers', 'all')))
            for p in pib:
                scores[p['name']] = int(p['score'])
        except Exception, e:
            self.debug('Unable to retrieve scores from playerlist (%r)' % e)
        return scores


    ###############################################################################################
    #
    #    Other methods
    #    
    ###############################################################################################

    def getFullMapRotationList(self):
        """query the Frostbite2 game server and return a MapListBlock containing all maps of the current
         map rotation list.
        """
        response = MapListBlock()
        offset = 0
        tmp = self.write(('mapList.list', offset))
        tmp_num_maps = len(MapListBlock(tmp))
        while tmp_num_maps:
            response.append(tmp)
            tmp = self.write(('mapList.list', len(response)))
            tmp_num_maps = len(MapListBlock(tmp))
        return response

    def getFullBanList(self):
        """query the Frostbite2 game server and return a BanlistContent object containing all bans stored on the game
        server memory.
        """
        response = BanlistContent()
        offset = 0
        tmp = self.write(('banList.list', offset))
        tmp_num_bans = len(BanlistContent(tmp))
        while tmp_num_bans:
            response.append(tmp)
            tmp = self.write(('banList.list', len(response)))
            tmp_num_bans = len(BanlistContent(tmp))
        return response

    def getHardName(self, mapname):
        """ Change human map name to map id """
        raise NotImplementedError('getHardName must be implemented in concrete classes')

    def getEasyName(self, mapname):
        """ Change map id to map human name """
        raise NotImplementedError('getEasyName must be implemented in concrete classes')

    def getGameMode(self, gamemode):
        """ Get game mode in real name """
        raise NotImplementedError('getGameMode must be implemented in concrete classes')

    def getCvar(self, cvarName):
        """Read a server var"""
        if cvarName not in self._gameServerVars:
            self.warning('unknown cvar \'%s\'' % cvarName)
            return None
        
        try:
            words = self.write(('vars.%s' % cvarName,))
        except CommandFailedError, err:
            self.warning(err)
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
        except CommandFailedError, err:
            self.warning(err)

    def checkVersion(self):
        raise NotImplementedError('checkVersion must be implemented in concrete classes')
        
    def getServerVars(self):
        raise NotImplementedError('getServerVars must be implemented in concrete classes')

    def getClient(self, cid, guid=None):
        """Get a connected client from storage or create it
        B3 CID   <--> ingame character name
        B3 GUID  <--> EA_guid
        """
        raise NotImplementedError('getClient must be implemented in concrete classes')
    
    def getTeam(self, team):
        """convert frostbite team numbers to B3 team numbers"""
        raise NotImplementedError('getTeam must be implemented in concrete classes')
        
    def getServerInfo(self):
        """query server info, update self.game and return query results
        """
        raise NotImplementedError('getServerInfo must be implemented in concrete classes')

        
    def getNextMap(self):
        """Return the name of the next map and gamemode"""
        maps = self.getFullMapRotationList()
        if len(maps) == 0:
            next_map_name = self.game.mapName
            next_map_gamemode = self.game.gameType
        else:
            mapIndices = self.write(('mapList.getMapIndices', ))
            next_map_info = maps[int(mapIndices[1])]
            next_map_name = next_map_info['name']
            next_map_gamemode = next_map_info['gamemode']
        return '%s (%s)' % (self.getEasyName(next_map_name), self.getGameMode(next_map_gamemode))

    def getSupportedMapIds(self):
        """return a list of supported levels for the current game mod"""
        # TODO : test this once the command work in BF3
        # TODO : to test this latter, remove getSupportedMapIds from bf3.py
        return self.write(('mapList.availableMaps',))

    def getMapsSoundingLike(self, mapname):
        """found matching level names for the given mapname (which can either
        be a level name or map name)
        If no exact match is found, then return close candidates using soundex
        and then LevenshteinDistance algorithms
        """
        supportedMaps = self.getSupportedMapIds()
        supportedEasyNames = {}
        for m in supportedMaps:
            supportedEasyNames[self.getEasyName(m).lower()] = m
            
        clean_map_name = mapname.strip().lower()
        soundex1 = soundex(mapname)
        #self.debug('soundex %s : %s' % (data, soundex1))

        match = []
        # given mapname could be the exact map id
        if clean_map_name in supportedMaps:
            match = [clean_map_name]
        else:
            # or we assume it is not a map id but a map name
            if clean_map_name in supportedEasyNames:
                # we are lucky to have an exact match
                match = [supportedEasyNames[clean_map_name]]
            else:
                # compute a list of map id for which we can find clean_map_name in their map name
                maps_matching_subset = [(map_id, map_name) for map_name, map_id in supportedEasyNames.items() if map_name.lower().find(clean_map_name) >= 0]
                if len(maps_matching_subset) == 1:
                    match = [maps_matching_subset[0][0]]
                elif len(maps_matching_subset) > 1:
                    match = [map_name for map_id, map_name in maps_matching_subset]
                else:
                    # no luck with subset lookup, fallback on soundex magic
                    for m in supportedEasyNames:
                        s = soundex(m)
                        #self.debug('soundex %s : %s' % (m, s))
                        if s == soundex1:
                            #self.debug('probable map : %s', m)
                            match.append(supportedEasyNames[m])


        if not len(match):
            # suggest closest spellings
            shortmaplist = []
            for m in supportedEasyNames:
                if m.find(clean_map_name) != -1:
                    shortmaplist.append(m)
            if len(shortmaplist) > 0:
                shortmaplist.sort(key=lambda _map: levenshteinDistance(clean_map_name, string.replace(_map.strip())))
                self.debug("shortmaplist sorted by distance : %s" % shortmaplist)
                match = shortmaplist[:3]
            else:
                easyNames = supportedEasyNames.keys()
                easyNames.sort(key=lambda _map: levenshteinDistance(clean_map_name, _map.strip()))
                self.debug("maplist sorted by distance : %s" % easyNames)
                match = easyNames[:3]
        return match



#############################################################
# Below is the code that change a bit the b3.clients.Client
# class at runtime. What the point of coding in python if we
# cannot play with its dynamic nature ;)
#
# why ?
# because doing so make sure we're not broking any other 
# working and long tested parser. The changes we make here
# are only applied when the frostbite parser is loaded.
#############################################################
  
## add a new method to the Client class
def frostbiteClientMessageQueueWorker(self):
    """
    This take a line off the queue and displays it
    then pause for 'message_delay' seconds
    """
    while not self.messagequeue.empty():
        msg = self.messagequeue.get()
        if msg:
            self.console.message(self, msg)
            time.sleep(int(self.console._settings['message_delay']))
b3.clients.Client.messagequeueworker = frostbiteClientMessageQueueWorker

## override the Client.message() method at runtime
def frostbiteClientMessageMethod(self, msg):
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
b3.clients.Client.message = frostbiteClientMessageMethod
