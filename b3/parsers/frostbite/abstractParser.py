#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2005 Michael "ThorN" Thornton
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
#
# CHANGELOG
#
# 2010-10-23 - 1.1   - Courgette - remove bfbc2 names
# 2010-11-07 - 1.1.1 - GrosBedo  - messages now support named $variables instead of %s
# 2010-11-08 - 1.1.2 - GrosBedo  - messages can now be empty (no message broadcasted on kick/tempban/ban/unban)
# 2010-11-02 - 1.2   - Courgette - call get_easy_name() in OnServerLoadinglevel
#                                - fix get_supported_maps()
#                                - OnServerLoadinglevel() now fills game.rounds and game.sv_maxrounds
# 2010-11-21 - 1.3   - Courgette - remove rotate_map and change_map as their implementation differs for MoH
# 2011-05-22 - 1.4   - Courgette - create specific events : EVT_GAME_ROUND_PLAYER_SCORES and EVT_GAME_ROUND_TEAM_SCORES
#                                - handle Frostbite events : OnServerRoundover, OnServerRoundoverplayers and
#                                  OnServerRoundoverteamscores
# 2011-05-24 - 1.4.1 - Courgette - fix get_supported_maps() so it uses the maplist set for the next round
#                                  instead of current
# 2011-05-25 - 1.4.2 - Courgette - fix bug introduced in 1.4.1
# 2011-06-05 - 1.5.0 - Courgette - change data format for EVT_CLIENT_BAN_TEMP and EVT_CLIENT_BAN events
# 2011-11-05 - 1.5.1 - Courgette - make sure to release the self.exiting lock
# 2012-10-06 - 1.6   - Courgette - isolate the patching code in a module function
# 2013-01-20 - 1.6.1 - Courgette - improve punkbuster event parsing
# 2013-02-17 - 1.7   - Courgette - add support for B3 event EVT_CLIENT_SQUAD_SAY
# 2014-05-02 - 1.7.1 - Fenix     - rewrote import statements
#                                - rewrote dictionary creation as literals
#                                - renamed sayqueuelistener() method in sayqueuelistenerworker(): was
#                                  overwriting an attribute
#                                - correctly initialize variables before usage
# 2014-07-18 - 1.7.2 - Fenix     - updated abstract parser to comply with the new get_wrap implementation
# 2014-08-05 - 1.7.3 - Fenix     - make use of self.getEvent when registering events: removes warnings
#                                - added getEasyName method declaration
# 2014-08-27 - 1.8   - Fenix     - syntax cleanup
#                                - major fixes in B3 parser interface methods
# 19/03/2015 - 1.8.1 - Fenix     - raise NotImplementedError instead of NotImplemented
# 16/04/2015 - 1.8.2 - Fenix     - uniform class variables (dict -> variable)
#                                - implement missing abstract class methods
# 30/07/2015 - 1.9   - Fenix     - fixed regression introduced in 1.8.2

__author__  = 'Courgette'
__version__ = '1.9'


import sys
import re
import traceback
import time
import string
import Queue
import threading
import b3.clients
import b3.cron
import b3.parser
import b3.parsers.frostbite.rcon as rcon
import b3.events
import b3.cvar

from b3.functions import soundex
from b3.functions import levenshteinDistance
from b3.functions import prefixText
from b3.parsers.frostbite.connection import FrostbiteConnection
from b3.parsers.frostbite.connection import FrostbiteException
from b3.parsers.frostbite.connection import FrostbiteCommandFailedError
from b3.parsers.frostbite.util import PlayerInfoBlock


class AbstractParser(b3.parser.Parser):
    """
    An abstract base class to help with developing frostbite parsers 
    """
    gameName = None
    privateMsg = True
    OutputClass = rcon.Rcon
    PunkBuster = None

    _serverConnection = None
    _nbConsecutiveConnFailure = 0
    
    sayqueue = Queue.Queue()
    sayqueuelistener = None

    # frostbite engine does not support color code, so we need this property
    # in order to get stripColors working
    _reColor = re.compile(r'(\^[0-9])') 
    
    _line_length = 100
    _message_delay = 2
    _line_color_prefix = ''

    _gameServerVars = () # list available cvars

    _commands = {
        'message': ('admin.say', '%(message)s', 'player', '%(cid)s'),
        'say': ('admin.say', '%(message)s', 'all'),
        'kick': ('admin.kickPlayer', '%(cid)s', '%(reason)s'),
        'ban': ('banList.add', 'guid', '%(guid)s', 'perm', '%(reason)s'),
        'banByIp': ('banList.add', 'ip', '%(ip)s', 'perm', '%(reason)s'),
        'unban': ('banList.remove', 'guid', '%(guid)s'),
        'unbanByIp': ('banList.remove', 'ip', '%(ip)s'),
        'tempban': ('banList.add', 'guid', '%(guid)s', 'seconds', '%(duration)d', '%(reason)s')
    }

    _eventMap = {
        #'player.onKicked': b3.events.EVT_CLIENT_KICK,
    }
    
    _punkbusterMessageFormats = (
        (re.compile(r'^.*: PunkBuster Server for BC2 \((?P<version>.+)\)\sEnabl.*$'), 'OnPBVersion'),
        (re.compile(r'^.*: Running PB Scheduled Task \(slot #(?P<slot>\d+)\)\s+(?P<task>.*)$'), 'OnPBScheduledTask'),
        (re.compile(r'^.*: Lost Connection \(slot #(?P<slot>\d+)\) (?P<ip>[^:]+):(?P<port>\d+) (?P<pbuid>[^\s]+)\(-\)\s(?P<name>.+)$'), 'OnPBLostConnection'),
        (re.compile(r'^.*: Master Query Sent to \((?P<pbmaster>[^\s]+)\) (?P<ip>[^:]+)$'), 'OnPBMasterQuerySent'),
        (re.compile(r'^.*: Player GUID Computed (?P<pbid>[0-9a-fA-F]+)\(-\) \(slot #(?P<slot>\d+)\) (?P<ip>[^:]+):(?P<port>\d+)\s(?P<name>.+)$'), 'OnPBPlayerGuid'),
        (re.compile(r'^.*: New Connection \(slot #(?P<slot>\d+)\) (?P<ip>[^:]+):(?P<port>\d+) \[(?P<something>[^\s]+)\]\s"(?P<name>.+)".*$'), 'OnPBNewConnection')
    )

    ####################################################################################################################
    #                                                                                                                  #
    #   PARSER INITIALIZATION                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    def __new__(cls, *args, **kwargs):
        patch_b3_clients()
        return b3.parser.Parser.__new__(cls)
           
    def startup(self):
        """
        Called after the parser is created before run().
        """
        self.checkVersion()

        # add specific events
        self.Events.createEvent('EVT_CLIENT_SQUAD_CHANGE', 'Client Squad Change')
        self.Events.createEvent('EVT_PUNKBUSTER_SCHEDULED_TASK', 'PunkBuster scheduled task')
        self.Events.createEvent('EVT_PUNKBUSTER_LOST_PLAYER', 'PunkBuster client connection lost')
        self.Events.createEvent('EVT_PUNKBUSTER_NEW_CONNECTION', 'PunkBuster client received IP')
        self.Events.createEvent('EVT_CLIENT_SPAWN', 'Client Spawn')
        self.Events.createEvent('EVT_GAME_ROUND_PLAYER_SCORES', 'round player scores')
        self.Events.createEvent('EVT_GAME_ROUND_TEAM_SCORES', 'round team scores')

        self._eventMap['player.onKicked'] = self.getEventID('EVT_CLIENT_KICK')

        self.getServerVars()
        self.getServerInfo()

        if self.config.has_option('server', 'punkbuster') and self.config.getboolean('server', 'punkbuster'):
            self.info('kick/ban by punkbuster is unsupported yet')
            #self.debug('punkbuster enabled in config')
            #self.PunkBuster = Bfbc2PunkBuster(self)

        self.sayqueuelistener = threading.Thread(target=self.sayqueuelistenerworker)
        self.sayqueuelistener.setDaemon(True)
        self.sayqueuelistener.start()

    def run(self):
        """
        Main worker thread for B3.
        """
        self.bot('Start listening ...')
        self.screen.write('Startup complete : B3 is running! Let\'s get to work!\n\n')
        self.screen.write('(If you run into problems, check %s in the B3 root directory for '
                          'detailed log info)\n' % self.config.getpath('b3', 'logfile'))

        self.updateDocumentation()

        while self.working:
            # while we are working, connect to the frostbite server
            if self._paused:
                if self._pauseNotice is False:
                    self.bot('PAUSED - not parsing any lines: B3 will be out of sync')
                    self._pauseNotice = True
            else:
                
                try:                
                    if self._serverConnection is None:
                        self.verbose('Connecting to frostbite server...')
                        self._serverConnection = FrostbiteConnection(self, self._rconIp, self._rconPort, self._rconPassword)

                    self._serverConnection.subscribeToEvents()
                    self.clients.sync()
                    self._nbConsecutiveConnFailure = 0
                        
                    nbConsecutiveReadFailure = 0
                    while self.working:
                        # while we are working and connected, read a packet
                        if not self._paused:
                            try:
                                packet = self._serverConnection.readEvent()
                                self.console("%s" % packet)
                                try:
                                    self.routeFrostbitePacket(packet)
                                except SystemExit:
                                    raise
                                except Exception, msg:
                                    self.error('%s: %s', msg, traceback.extract_tb(sys.exc_info()[2]))
                            except FrostbiteException, e:
                                nbConsecutiveReadFailure += 1
                                if nbConsecutiveReadFailure > 5:
                                    raise e
                except FrostbiteException, e:
                    self.debug(e)
                    self._nbConsecutiveConnFailure += 1
                    self._serverConnection.close()
                    if self._nbConsecutiveConnFailure <= 20:
                        self.debug('sleeping 0.5 sec...')
                        time.sleep(0.5)
                    elif self._nbConsecutiveConnFailure <= 60:
                        self.debug('sleeping 2 sec...')
                        time.sleep(2)
                    else:
                        self.debug('sleeping 30 sec...')
                        time.sleep(30)
                    
        self.bot('Stop listening...')

        with self.exiting:
            #self.input.close()
            self.output.close()

            if self.exitcode:
                sys.exit(self.exitcode)

    ####################################################################################################################
    #                                                                                                                  #
    #   OTHER METHODS                                                                                                  #
    #                                                                                                                  #
    ####################################################################################################################

    def routeFrostbitePacket(self, packet):
        """
        Route a Frostbite packet.
        """
        if packet is None:
            self.warning('Cannot route empty packet : %s' % traceback.extract_tb(sys.exc_info()[2]))
        
        eventType = packet[0]
        eventData = packet[1:]

        data = ''
        func = ''
        match = re.search(r"^(?P<actor>[^.]+)\.on(?P<event>.+)$", eventType)
        if match:
            func = 'On%s%s' % (string.capitalize(match.group('actor')), string.capitalize(match.group('event')))
            #self.debug("-==== FUNC!!: " + func)
            
        if match and hasattr(self, func):
            func = getattr(self, func)
            event = func(eventType, eventData)
            if event:
                self.queueEvent(event)
            
        elif eventType in self._eventMap:
            self.queueEvent(b3.events.Event(self._eventMap[eventType], eventData))
        else:
            if func:
                data = func + ' '

            data += str(eventType) + ': ' + str(eventData)
            self.debug('TODO: %r' % packet)
            self.queueEvent(self.getEvent('EVT_UNKNOWN', data))
    
    def sayqueuelistenerworker(self):
        while self.working:
            message = self.sayqueue.get()
            message = self.stripColors(prefixText([self.msgPrefix], message)).strip()
            for line in self.getWrap(message):
                self.write(self.getCommand('say', message=line))
                time.sleep(self._message_delay)

    def joinPlayers(self):
        self.info('Joining players...')
        plist = self.getPlayerList()
        for cid, p in plist.iteritems():
            client = self.clients.getByCID(cid)
            if client:
                self.debug(' - joining %s' % cid)
                self.queueEvent(self.getEvent('EVT_CLIENT_JOIN', p, client))
        return None

    def getCommand(self, cmd, **kwargs):
        """
        Return a reference to a loaded command.
        """
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
        """
        Write a message to Rcon/Console.
        Unfortunaltely this has been abused all over B3 and B3 plugins to broadcast text :(
        """
        if type(msg) == str:
            # console abuse to broadcast text
            self.say(msg)
        else:
            # then we got a command
            if self.output:
                res = self.output.write(msg, maxRetries=maxRetries, needConfirmation=needConfirmation)
                self.output.flush()
                return res

    def checkVersion(self):
        raise NotImplementedError('checkVersion must be implemented in concrete classes')
        
    def getServerVars(self):
        raise NotImplementedError('getServerVars must be implemented in concrete classes')

    def getServerInfo(self):
        """
        Query server info, update self.game and return query results
        Response: OK <pb prefix: string> <current playercount: integer> <max playercount: integer>
        <current gamemode: string> <current map: string> <roundsPlayed: integer>
        <roundsTotal: string> <scores: team scores> <onlineState: online state>
        """
        data = self.write(('serverInfo',))
        self.game.sv_hostname = data[0]
        self.game.sv_maxclients = int(data[2])
        self.game.gameType = data[3]
        if not self.game.mapName:
            self.game.mapName = data[4]
        self.game.rounds = int(data[5])
        self.game.g_maxrounds = int(data[6])
        return data

    def getClient(self, cid, _guid=None):
        """
        Get a connected client from storage or create it
        B3 CID   <--> ingame character name
        B3 GUID  <--> EA_guid
        """
        raise NotImplementedError('getClient must be implemented in concrete classes')
    
    def getTeam(self, team):
        """
        Convert frostbite team numbers to B3 team numbers.
        """
        raise NotImplementedError('getTeam must be implemented in concrete classes')

    def getEasyName(self, mapname):
        """
        Change levelname to real name.
        """
        raise NotImplementedError('get_easy_name must be implemented in concrete classes')

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENT HANDLERS                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################
    
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
            self.warning("Could not get client: %s" % traceback.extract_tb(sys.exc_info()[2]))
            return
        if client.cid == 'Server':
            # ignore chat events for Server
            return
        if data[2] == 'all':
            return self.getEvent('EVT_CLIENT_SAY', data[1].lstrip('/'), client, 'all')
        elif data[2] == 'team':
            return self.getEvent('EVT_CLIENT_TEAM_SAY', data[1].lstrip('/'), client, data[2] + ' ' + data[3])
        elif 'squad' in data[2]:
            return self.getEvent('EVT_CLIENT_SQUAD_SAY', data[1].lstrip('/'), client, data[2] + ' ' + data[3])
        elif data[2] == 'player':
            target = self.getClient(data[3])
            return self.getEvent('EVT_CLIENT_PRIVATE_SAY', data[1].lstrip('/'), client, target)

    def OnPlayerLeave(self, action, data):
        # player.onLeave: ['GunnDawg']
        client = self.getClient(data[0])
        if client: 
            client.endMessageThreads = True
            client.disconnect() # this triggers the EVT_CLIENT_DISCONNECT event
        return None

    def OnPlayerJoin(self, action, data):
        """
        We don't have guid at this point.
        Wait for player.onAuthenticated.
        """
        pass

    def OnPlayerAuthenticated(self, action, data):
        """
        player.onAuthenticated <soldier name: string> <player GUID: guid>
        Effect: Player with name <soldier name> has been authenticated, and has the given GUID
        """
        # player.onJoin: ['OrasiK']
        client = self.getClient(data[0], data[1])
        # No need to queue a client join event, that is done by clients.newClient() already
        # return b3.events.Event(b3.events.EVT_CLIENT_CONNECT, data, client)

    def OnPlayerSpawn(self, action, data):
        """
        Request: player.onSpawn <spawning soldier name: string> <kit type: string> <gadget: string> <pistol: string>
               <primary weapon: string> <specialization 1: string> <specialization 2: string> <specialization 3: string>
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

        return self.getEvent('EVT_CLIENT_SPAWN', (kit, gadget, pistol, weapon, spec1, spec2, spec3), spawner)

    def OnPlayerKill(self, action, data):
        """
        Request: player.onKill <killing soldier name: string> <killed soldier name: string> <weapon: string>
                               <headshot: boolean> <killer location: 3 x integer> <killed location: 3 x integes>

        Effect: Player with name <killing soldier name> has killed <killed soldier name> Suicide is indicated with
        the same soldier name for killer and victim. If the server kills the player (through admin.killPlayer),
        it is indicated by showing the killing soldier name as Server. The locations of the killer and the
        killed have a random error of up to 10 meters in each direction.
        """
        # R15: player.onKill: ['Brou88', 'kubulina', 'S20K', 'true', '-77', '68', '-195', '-76', '62', '-209']
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

        event_key = 'EVT_CLIENT_KILL'
        if victim == attacker:
            event_key = 'EVT_CLIENT_SUICIDE'
        elif attacker.team == victim.team and attacker.team != b3.TEAM_UNKNOWN and attacker.team != b3.TEAM_SPEC:
            event_key = 'EVT_CLIENT_KILL_TEAM'
        return self.getEvent(event_key, (100, weapon, hitloc, attackerloc, victimloc), attacker, victim)

    def OnServerLoadinglevel(self, action, data):
        """
        server.onLoadingLevel <level name: string> <roundsPlayed: int> <roundsTotal: int>
        Effect: Level is loading
        """
        #['server.onLoadingLevel', 'levels/mp_04', '0', '2']
        self.debug("OnServerLoadinglevel: %s" % data)
        if not self.game.mapName:
            self.game.mapName = data[0]
        if self.game.mapName != data[0]:
            # map change detected
            self.game.startMap()
        self.game.mapName = data[0]
        self.game.rounds = int(data[1])
        self.game.g_maxrounds = int(data[2])
        self.getServerInfo()
        # to debug getEasyName()
        self.info('Loading %s [%s]'  % (self.getEasyName(self.game.mapName), self.game.gameType))
        return self.getEvent('EVT_GAME_WARMUP', data[0])

    def OnServerLevelstarted(self, action, data):
        # next function call will increase roundcount by one, this is not wanted
        # as the game server provides us the exact round number in OnServerLoadinglevel()
        # hence we need to deduct one to compensate?
        # we'll still leave the call here since it provides us self.game.roundTime()
        self.game.startRound()
        self.game.rounds -= 1
        
        # players need to be joined (EVT_CLIENT_JOIN) for stats to count rounds
        self.joinPlayers()
        return self.getEvent('EVT_GAME_ROUND_START', self.game)

    def OnServerRoundover(self, action, data):
        """
        server.onRoundOver <winning team: Team ID>
        Effect: The round has just ended, and <winning team> won
        """
        #['server.onRoundOver', '2']
        return self.getEvent('EVT_GAME_ROUND_END', data[0])

    def OnServerRoundoverplayers(self, action, data):
        """
        server.onRoundOverPlayers <end-of-round soldier info : player info block>
        Effect: The round has just ended, and <end-of-round soldier info> is the final detailed player stats
        """
        #['server.onRoundOverPlayers', '8', 'clanTag', 'name', 'guid', 'teamId', 'kills', 'deaths', 'score', 'ping',
        # '17', 'RAID', 'mavzee', 'EA_4444444444444444555555555555C023', '2', '20', '17', '310', '147', 'RAID', 'NUeeE',
        # 'EA_1111111111111555555555555554245A', '2', '30', '18', '445', '146', '', 'Strzaerl',
        # 'EA_88888888888888888888888888869F30', '1', '12', '7', '180', '115', '10tr', 'russsssssssker',
        # 'EA_E123456789461416564796848C26D0CD', '2', '12', '12', '210', '141', '', 'Daezch',
        # 'EA_54567891356479846516496842E17F4D', '1', '25', '14', '1035', '129', '', 'Oldqsdnlesss',
        # 'EA_B78945613465798645134659F3079E5A', '1', '8', '12', '120', '256', '', 'TTETqdfs',
        # 'EA_1321654656546544645798641BB6D563', '1', '11', '16', '180', '209', '', 'bozer',
        # 'EA_E3987979878946546546565465464144', '1', '22', '14', '475', '152', '', 'Asdf 1977',
        # 'EA_C65465413213216656546546546029D6', '2', '13', '16', '180', '212', '', 'adfdasse',
        # 'EA_4F313565464654646446446644664572', '1', '4', '25', '45', '162', 'SG1', 'De56546ess',
        # 'EA_123132165465465465464654C2FC2FBB', '2', '5', '8', '75', '159', 'bsG', 'N06540RZ',
        # 'EA_787897944546565656546546446C9467', '2', '8', '14', '100', '115', '', 'Psfds',
        # 'EA_25654321321321000006546464654B81', '2', '15', '15', '245', '140', '', 'Chezear',
        # 'EA_1FD89876543216548796130EB83E411F', '1', '9', '14', '160', '185', '', 'IxSqsdfOKxI',
        # 'EA_481321313132131313213212313112CE', '1', '21', '12', '625', '236', '', 'Ledfg07',
        # 'EA_1D578987994651615166516516136450', '1', '5', '6', '85', '146', '', '5 56 mm',
        # 'EA_90488E6543216549876543216549877B', '2', '0', '0', '0', '192']
        return self.getEvent('EVT_GAME_ROUND_PLAYER_SCORES', PlayerInfoBlock(data))

    def OnServerRoundoverteamscores(self, action, data):
        """
        server.onRoundOverTeamScores <end-of-round scores: team scores>
        Effect: The round has just ended, and <end-of-round scores> is the final ticket/kill/life count for each team
        """
        #['server.onRoundOverTeamScores', '2', '1180', '1200', '1200']
        return self.getEvent('EVT_GAME_ROUND_TEAM_SCORES', data[1])

    def OnPunkbusterMessage(self, action, data):
        """
        Handles all punkbuster related events and route them to the appropriate
        method depending on the type of PB message.
        """
        #self.debug("PB> %s" % data)
        match = None
        funcName = None
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
                return self.getEvent('EVT_UNKNOWN', data)
                
    def OnPBVersion(self, match,data):
        """
        PB notifies us of the version numbers version = match.group('version').
        """
        #self.debug('PunkBuster Server version: %s' %( match.group('version') ) )
        pass

    def OnPBNewConnection(self, match, data):
        """
        PunkBuster tells us a new player identified. The player is normally already connected and authenticated
        by B3 by ea_guid. This is our first moment where we receive the clients IP address so we also fire the custom
        event EVT_PUNKBUSTER_NEW_CONNECTION here.
        """
        name = match.group('name')
        client = self.getClient(name)
        if client:
            # slot = match.group('slot')
            ip = match.group('ip')
            port = match.group('port')
            # something = match.group('something')
            client.ip = ip
            client.port = port
            client.save()
            self.debug('OnPBNewConnection: client updated with %s' % data)
            # This is our first moment where we get a clients IP.
            # Fire this event to accomodate geoIP based plugins like Countryfilter.
            return self.getEvent('EVT_PUNKBUSTER_NEW_CONNECTION', data, client)
        else:
            self.warning('OnPBNewConnection: we\'ve been unable to get the client')

    def OnPBLostConnection(self, match, data):
        """
        PB notifies us it lost track of a player. This is the only change
        we have to save the ip of clients.
        This event is triggered after the OnPlayerLeave, so normaly the client
        is not connected. Anyway our task here is to save data into db not to 
        connect/disconnect the client.
        Part of this code is obsolete since R15, IP is saved to DB on OnPBNewConnection()
        """
        name = match.group('name')
        data = {
            'slot': match.group('slot'),
            'ip': match.group('ip'),
            'port': match.group('port'),
            'pbuid': match.group('pbuid'),
            'name': name
        }
        # Code Obsolete since R15:
        # client = self.clients.getByCID(dict['name'])
        # if not client:
        #     matchingClients = self.storage.getClientsMatching( {'pbid': match.group('pbuid')} )
        #     if matchingClients and len(matchingClients) == 0:
        #         client = matchingClients[0]
        # if not client:
        #     self.error('unable to find client %s. weird' %name )
        # else:
        #     # update client data with PB id and IP
        #    client.pbid = dict['pbuid']
        #     client.ip = dict['ip']
        #     client.save()
        self.verbose('PB lost connection: %s' % data)
        return self.getEvent('EVT_PUNKBUSTER_LOST_PLAYER', data)

    def OnPBScheduledTask(self, match, data):
        """
        We get notified the server ran a PB scheduled task
        Nothing much to do but it can be interresting to have
        this information logged
        """
        slot = match.group('slot')
        task = match.group('task')
        return self.getEvent('EVT_PUNKBUSTER_SCHEDULED_TASK', {'slot': slot, 'task': task})

    def OnPBMasterQuerySent(self, match, data):
        """
        We get notified that the server sent a ping to the PB masters.
        """
        #pbmaster = match.group('pbmaster')
        #ip = match.group('ip')
        pass

    def OnPBPlayerGuid(self, match, data):
        """
        We get notified of a player punkbuster GUID.
        """
        pbid = match.group('pbid')
        #slot = match.group('slot')
        ip = match.group('ip')
        #port = match.group('port')
        name = match.group('name')
        client = self.getClient(name)
        client.ip = ip
        client.pbid = pbid
        client.save()
        
    ####################################################################################################################
    #                                                                                                                  #
    #   B3 PARSER INTERFACE IMPLEMENTATION                                                                             #
    #                                                                                                                  #
    ####################################################################################################################

    def message(self, client, text):
        """
        Display a message to a given client
        :param client: The client to who send the message
        :param text: The message to be sent
        """
        try:
            if client is None:
                self.say(text)
            elif client.cid is None:
                pass
            else:
                self.write(self.getCommand('message', message=text, cid=client.cid))
        except:
            pass

    def say(self, msg):
        """
        Broadcast a message to all players.
        :param msg: The message to be broadcasted
        """
        self.sayqueue.put(msg)

    def kick(self, client, reason='', admin=None, silent=False, *kwargs):
        """
        Kick a given client.
        :param client: The client to kick
        :param reason: The reason for this kick
        :param admin: The admin who performed the kick
        :param silent: Whether or not to announce this kick
        """
        self.debug('Kick reason: [%s]' % reason)
        if isinstance(client, str):
            self.write(self.getCommand('kick', cid=client, reason=reason[:80]))
            return
        
        if admin:
            variables = self.getMessageVariables(client=client, reason=reason, admin=admin)
            fullreason = self.getMessage('kicked_by', variables)
        else:
            variables = self.getMessageVariables(client=client, reason=reason)
            fullreason = self.getMessage('kicked', variables)

        fullreason = self.stripColors(fullreason)
        reason = self.stripColors(reason)

        if self.PunkBuster:
            self.PunkBuster.kick(client, 0.5, reason)
        
        self.write(self.getCommand('kick', cid=client.cid, reason=reason[:80]))

        if not silent and fullreason != '':
            self.say(fullreason)
            
    def tempban(self, client, reason='', duration=2, admin=None, silent=False, *kwargs):
        """
        Tempban a client.
        :param client: The client to tempban
        :param reason: The reason for this tempban
        :param duration: The duration of the tempban
        :param admin: The admin who performed the tempban
        :param silent: Whether or not to announce this tempban
        """
        duration = b3.functions.time2minutes(duration)
        if isinstance(client, str):
            self.write(self.getCommand('tempban', guid=client, duration=duration*60, reason=reason[:80]))
            return
        
        if admin:
            banduration = b3.functions.minutesStr(duration)
            variables = self.getMessageVariables(client=client, reason=reason, admin=admin, banduration=banduration)
            fullreason = self.getMessage('temp_banned_by', variables)
        else:
            banduration = b3.functions.minutesStr(duration)
            variables = self.getMessageVariables(client=client, reason=reason, banduration=banduration)
            fullreason = self.getMessage('temp_banned', variables)
            
        fullreason = self.stripColors(fullreason)
        reason = self.stripColors(reason)

        if self.PunkBuster:
            # punkbuster acts odd if you ban for more than a day
            # tempban for a day here and let b3 re-ban if the player
            # comes back
            if duration > 1440:
                duration = 1440

            self.PunkBuster.kick(client, duration, reason)
        
        self.write(self.getCommand('tempban', guid=client.guid, duration=duration*60, reason=reason[:80]))
        
        if not silent and fullreason != '':
            self.say(fullreason)

        data = {'reason': reason, 'duration': duration, 'admin': admin}
        self.queueEvent(self.getEvent('EVT_CLIENT_BAN_TEMP', data=data, client=client))
        client.disconnect()


    def unban(self, client, reason='', admin=None, silent=False, *kwargs):
        """
        Unban a client.
        :param client: The client to unban
        :param reason: The reason for the unban
        :param admin: The admin who unbanned this client
        :param silent: Whether or not to announce this unban
        """
        self.debug('UNBAN: Name: %s, Ip: %s, Guid: %s' %(client.name, client.ip, client.guid))
        if client.ip:
            response = self.write(self.getCommand('unbanByIp', ip=client.ip, reason=reason), needConfirmation=True)
            if response == "OK":
                self.verbose('UNBAN: removed ip (%s) from banlist' %client.ip)
                if admin:
                    admin.message('Unbanned: %s. '
                                  'His last ip (%s) has been removed from banlist.' % (client.exactName, client.ip))
                if admin:
                    variables = self.getMessageVariables(client=client, reason=reason, admin=admin)
                    fullreason = self.getMessage('unbanned_by', variables)
                else:
                    variables = self.getMessageVariables(client=client, reason=reason)
                    fullreason = self.getMessage('unbanned', variables)
                
                if not silent and fullreason != '':
                    self.say(fullreason)
        
        response = self.write(self.getCommand('unban', guid=client.guid, reason=reason), needConfirmation=True)

        if response == "OK":
            self.verbose('UNBAN: removed guid (%s) from banlist' %client.guid)
            if admin:
                admin.message('Unbanned: removed %s guid from banlist' % client.exactName)
        
        if self.PunkBuster:
            self.PunkBuster.unBanGUID(client)

    def ban(self, client, reason='', admin=None, silent=False, *kwargs):
        """
        Ban a given client.
        :param client: The client to ban
        :param reason: The reason for this ban
        :param admin: The admin who performed the ban
        :param silent: Whether or not to announce this ban
        """
        self.debug('BAN : client: %s, reason: %s', client, reason)
        if isinstance(client, b3.clients.Client):
            self.write(self.getCommand('ban', guid=client.guid, reason=reason[:80]))
            return

        if admin:
            variables = self.getMessageVariables(client=client, reason=reason, admin=admin)
            fullreason = self.getMessage('banned_by', variables)
        else:
            variables = self.getMessageVariables(client=client, reason=reason)
            fullreason = self.getMessage('banned', variables)
            
        fullreason = self.stripColors(fullreason)
        reason = self.stripColors(reason)

        if client.cid is None:
            # ban by ip, this happens when we !permban @xx a player that is not connected
            self.debug('EFFECTIVE BAN : %s',self.getCommand('banByIp', ip=client.ip, reason=reason[:80]))
            self.write(self.getCommand('banByIp', ip=client.ip, reason=reason[:80]))
            if admin:
                admin.message('Banned: %s (@%s). '
                              'His last ip (%s) has been added to banlist' % (client.exactName, client.id, client.ip))
        else:
            # ban by cid
            self.debug('EFFECTIVE BAN : %s',self.getCommand('ban', guid=client.guid, reason=reason[:80]))
            self.write(self.getCommand('ban', cid=client.cid, reason=reason[:80]))
            if admin:
                admin.message('Banned: %s (@%s) has been added to banlist' % (client.exactName, client.id))

        if self.PunkBuster:
            self.PunkBuster.banGUID(client, reason)
        
        if not silent and fullreason != '':
            self.say(fullreason)
        
        self.queueEvent(self.getEvent('EVT_CLIENT_BAN', {'reason': reason, 'admin': admin}, client))

    def sync(self):
        """
        For all connected players returned by self.getPlayerList(), get the matching Client
        object from self.clients (with self.clients.getByCID(cid) or similar methods) and
        look for inconsistencies. If required call the client.disconnect() method to remove
        a client from self.clients.
        This is mainly useful for games where clients are identified by the slot number they
        occupy. On map change, a player A on slot 1 can leave making room for player B who
        connects on slot 1.
        """
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

    def authorizeClients(self):
        """
        For all connected players, fill the client object with properties allowing to find
        the user in the database (usualy guid, or punkbuster id, ip) and call the
        Client.auth() method.
        """
        players = self.getPlayerList()
        self.verbose('authorizeClients() = %s' % players)
        for cid, p in players.iteritems():
            sp = self.clients.getByCID(cid)
            if sp:
                # only set provided data,
                # otherwise use the currently set data
                sp.ip = p.get('ip', sp.ip)
                sp.pbid = p.get('pbid', sp.pbid)
                sp.guid = p.get('guid', sp.guid)
                sp.data = p
                newTeam = p.get('teamId', None)
                if newTeam is not None:
                    sp.team = self.getTeam(newTeam)
                sp.teamId = int(newTeam)
                sp.auth()

    def getPlayerList(self, maxRetries=None):
        """
        Return a dict which keys are cid and values a dict of player properties
        as returned by admin.listPlayers. Does not return client objects.
        """
        data = self.write(('admin.listPlayers', 'all'))
        if not data:
            return {}
        players = {}
        pib = PlayerInfoBlock(data)
        for p in pib:
            players[p['name']] = p
        return players

    def getPlayerScores(self):
        """Ask the server for a given client's team
        """
        scores = {}
        try:
            pib = PlayerInfoBlock(self.write(('admin.listPlayers', 'all')))
            for p in pib:
                scores[p['name']] = int(p['score'])
        except:
            self.debug('Unable to retrieve scores from playerlist')
        return scores

    def getPlayerPings(self, filter_client_ids=None):
        """
        Ask the server for a given client's team.
        """
        pings = {}
        try:
            pib = PlayerInfoBlock(self.write(('admin.listPlayers', 'all')))
            for p in pib:
                pings[p['name']] = int(p['ping'])
        except:
            self.debug('Unable to retrieve pings from playerlist')
        return pings

    def getNextMap(self):
        """
        Return the name of the next map
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

    def saybig(self, msg):
        pass

    def rotateMap(self):
        pass

    def changeMap(self, map_name):
        pass

    def getMaps(self):
        """
        Return the map list for the current rotation. (as easy map names)
        This does not return all available maps.
        """
        levelnames = self.write(('mapList.list',))
        mapList = []
        for l in levelnames:
            mapList.append(self.getEasyName(l))
        return mapList

    def getMap(self):
        """
        Return the current level name (not easy map name).
        """
        self.getServerInfo()
        return self.game.mapName

    def getSupportedMaps(self):
        """
        Return a list of supported levels for the current game mod.
        """
        [currentMode] = self.write(('admin.getPlaylist',))
        supportedMaps = self.write(('admin.supportedMaps', currentMode))
        return supportedMaps

    def getMapsSoundingLike(self, mapname):
        """
        Found matching level names for the given mapname (which can either be a level name or map name).
        If no exact match is found, then return close candidates using soundex and then LevenshteinDistance algoritms.
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
                shortmaplist.sort(key=lambda mn: levenshteinDistance(data, mn.strip()))
                self.debug("Shortmaplist sorted by distance : %s" % shortmaplist)
                match = shortmaplist[:3]
            else:
                easyNames = supportedEasyNames.keys()
                easyNames.sort(key=lambda mn: levenshteinDistance(data, mn.strip()))
                self.debug("Maplist sorted by distance : %s" % easyNames)
                match = easyNames[:3]
        return match

    def getCvar(self, cvarName):
        """
        Return a CVAR from the server.
        :param cvarName: The CVAR name.
        """
        if cvarName not in self._gameServerVars:
            self.warning('Unknown cvar: %s' % cvarName)
            return None
        
        try:
            words = self.write(('vars.%s' % cvarName,))
        except FrostbiteCommandFailedError, err:
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
        """
        Set a CVAR on the server.
        :param cvarName: The CVAR name
        :param value: The CVAR value
        """
        if cvarName not in self._gameServerVars:
            self.warning('Cannot set unknown cvar: %s' % cvarName)
            return
        self.debug('Set cvar %s = \'%s\'', cvarName, value)
        try:
            self.write(('vars.%s' % cvarName, value))
        except FrostbiteCommandFailedError, err:
            self.error(err)

########################################################################################################################
##                                                                                                                    ##
##  APPLY SPECIFIC PARSER PATCHES TO B3 CORE MODULES                                                                  ##
##                                                                                                                    ##
########################################################################################################################

def patch_b3_clients():

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
                time.sleep(float(self.console._message_delay))

    ## override the Client.message() method at runtime
    def frostbiteClientMessageMethod(self, msg):
        if msg and len(msg.strip())>0:
            # do we have a queue?
            if not hasattr(self, 'messagequeue'):
                self.messagequeue = Queue.Queue()
            # fill the queue
            text = self.console.stripColors(self.console.msgPrefix + ' [pm] ' + msg)
            for line in self.console.getWrap(text):
                self.messagequeue.put(line)
            # create a thread that executes the worker and pushes out the queue
            if not hasattr(self, 'messagehandler') or not self.messagehandler.isAlive():
                self.messagehandler = threading.Thread(target=self.messagequeueworker)
                self.messagehandler.setDaemon(True)
                self.messagehandler.start()
            else:
                self.console.verbose('messagehandler for %s isAlive' %self.name)

    b3.clients.Client.messagequeueworker = frostbiteClientMessageQueueWorker
    b3.clients.Client.message = frostbiteClientMessageMethod