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
#

__author__  = 'Courgette'
__version__ = '0.0'


import sys, re, traceback, time, string, Queue, threading
import b3.parser
import b3.parsers.frostbite2.rcon as rcon
from b3.parsers.frostbite2.connection import FrostbiteConnection, FrostbiteException, FrostbiteCommandFailedError
from b3.parsers.frostbite2.util import PlayerInfoBlock
import b3.events
#from b3.parsers.frostbite.punkbuster import PunkBuster as Bfbc2PunkBuster
import b3.cvar
from b3.functions import soundex, levenshteinDistance

SAY_LINE_MAX_LENGTH = 100

class AbstractParser(b3.parser.Parser):
    '''
    An abstract base class to help with developing frostbite2 parsers 
    '''
    gameName = None
    OutputClass = rcon.Rcon
    _serverConnection = None
    _nbConsecutiveConnFailure = 0
    
    sayqueue = Queue.Queue()
    sayqueuelistener = None

    # frostbite2 engine does not support color code, so we need this property
    # in order to get stripColors working
    _reColor = re.compile(r'(\^[0-9])') 
    
    _settings = {}
    _settings['line_length'] = 65
    _settings['min_wrap_length'] = 65
    _settings['message_delay'] = 2

    _gameServerVars = () # list available cvar

    _commands = {}
    _commands['message'] = ('admin.say', '%(message)s', 'player', '%(cid)s')
    _commands['say'] = ('admin.say', '%(message)s', 'all')
    _commands['kick'] = ('admin.kickPlayer', '%(cid)s', '%(reason)s')
    _commands['ban'] = ('banList.add', 'guid', '%(guid)s', 'perm', '%(reason)s')
    _commands['banByIp'] = ('banList.add', 'ip', '%(ip)s', 'perm', '%(reason)s')
    _commands['unban'] = ('banList.remove', 'guid', '%(guid)s')
    _commands['unbanByIp'] = ('banList.remove', 'ip', '%(ip)s')
    _commands['tempban'] = ('banList.add', 'guid', '%(guid)s', 'seconds', '%(duration)d', '%(reason)s')

    _eventMap = {
        'player.kicked': b3.events.EVT_CLIENT_KICK, # TODO: test this event
    }
    
    _punkbusterMessageFormats = (
        (re.compile(r'^(?P<servername>.*): PunkBuster Server for .+ \((?P<version>.+)\)\sEnabl.*$'), 'OnPBVersion'),
        (re.compile(r'^(?P<servername>.*): Running PB Scheduled Task \(slot #(?P<slot>\d+)\)\s+(?P<task>.*)$'), 'OnPBScheduledTask'),
        (re.compile(r'^(?P<servername>.*): Lost Connection \(slot #(?P<slot>\d+)\) (?P<ip>[^:]+):(?P<port>\d+) (?P<pbuid>[^\s]+)\(-\)\s(?P<name>.+)$'), 'OnPBLostConnection'),
        (re.compile(r'^(?P<servername>.*): Master Query Sent to \((?P<pbmaster>[^\s]+)\) (?P<ip>[^:]+)$'), 'OnPBMasterQuerySent'),
        (re.compile(r'^(?P<servername>.*): Player GUID Computed (?P<pbid>[0-9a-fA-F]+)\(-\) \(slot #(?P<slot>\d+)\) (?P<ip>[^:]+):(?P<port>\d+)\s(?P<name>.+)$'), 'OnPBPlayerGuid'),
        (re.compile(r'^(?P<servername>.*): New Connection \(slot #(?P<slot>\d+)\) (?P<ip>[^:]+):(?P<port>\d+) \[(?P<something>[^\s]+)\]\s"(?P<name>.+)".*$'), 'OnPBNewConnection')
     )

    PunkBuster = None
           
           
           
    def run(self):
        """Main worker thread for B3"""
        self.bot('Start listening ...')
        self.screen.write('Startup Complete : B3 is running! Let\'s get to work!\n\n')
        self.screen.write('(If you run into problems, check %s for detailed log info)\n' % self.config.getpath('b3', 'logfile'))
        #self.screen.flush()

        self.updateDocumentation()

        while self.working:
            """
            While we are working, connect to the frostbite2 server
            """
            if self._paused:
                if self._pauseNotice == False:
                    self.bot('PAUSED - Not parsing any lines, B3 will be out of sync.')
                    self._pauseNotice = True
            else:
                
                try:                
                    if self._serverConnection is None:
                        self.verbose('Connecting to frostbite2 server ...')
                        self._serverConnection = FrostbiteConnection(self, self._rconIp, self._rconPort, self._rconPassword, "event connection")

                    self._serverConnection.subscribeToEvents()
                    self.clients.sync()
                    self._nbConsecutiveConnFailure = 0
                        
                    nbConsecutiveReadFailure = 0
                    while self.working:
                        """
                        While we are working and connected, read a packet
                        """
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
                                #self.debug(e)
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
                    
        self.bot('Stop listening.')

        if self.exiting.acquire(1):
            #self.input.close()
            self.output.close()

            if self.exitcode:
                sys.exit(self.exitcode)


    def routeFrostbitePacket(self, packet):
        if packet is None:
            self.warning('cannot route empty packet : %s' % traceback.extract_tb(sys.exc_info()[2]))
        
        eventType = packet[0]
        eventData = packet[1:]
        
        match = re.search(r"^(?P<actor>[^.]+)\.(?P<event>.+)$", eventType)
        func = None
        if match:
            func = 'On%s%s' % (string.capitalize(match.group('actor')), \
                               string.capitalize(match.group('event')))
            self.debug("looking for event handling method called : " + func)
            
        if match and hasattr(self, func):
            self.debug('routing ----> %s(%r)' % (func,eventData))
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
        self.checkVersion()
        
        # add specific events
        self.Events.createEvent('EVT_CLIENT_SQUAD_CHANGE', 'Client Squad Change')
        self.Events.createEvent('EVT_PUNKBUSTER_SCHEDULED_TASK', 'PunkBuster scheduled task')
        self.Events.createEvent('EVT_PUNKBUSTER_LOST_PLAYER', 'PunkBuster client connection lost')
        self.Events.createEvent('EVT_PUNKBUSTER_NEW_CONNECTION', 'PunkBuster client received IP')
        self.Events.createEvent('EVT_GAME_ROUND_PLAYER_SCORES', 'round player scores')
        self.Events.createEvent('EVT_GAME_ROUND_TEAM_SCORES', 'round team scores')
                
        self.getServerVars()
        self.getServerInfo()
        
        if self.config.has_option('server', 'punkbuster') and self.config.getboolean('server', 'punkbuster'):
            self.info('kick/ban by punkbuster is unsupported')
            #self.debug('punkbuster enabled in config')
            #self.PunkBuster = Bfbc2PunkBuster(self)
        
        self.sayqueuelistener = threading.Thread(target=self.sayqueuelistener)
        self.sayqueuelistener.setDaemon(True)
        self.sayqueuelistener.start()

    
    def sayqueuelistener(self):
        while self.working:
            msg = self.sayqueue.get()
            for line in self.getWrap(self.stripColors(self.msgPrefix + ' ' + msg), self._settings['line_length'], self._settings['min_wrap_length']):
                self.write(self.getCommand('say', message=line))
                time.sleep(self._settings['message_delay'])


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

    
    def TODOOnPlayerChat(self, action, data):
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
        

    def OnPlayerLeft(self, action, data):
        #player.onLeave: ['GunnDawg']
        client = self.getClient(data[0])
        if client: 
            client.endMessageThreads = True
            client.disconnect() # this triggers the EVT_CLIENT_DISCONNECT event
        return None

    def TODOOnPlayerJoin(self, action, data):
        """
        we don't have guid at this point. Wait for player.onAuthenticated
        """
        pass
        

    def OnPlayerAuthenticated(self, action, data):
        """
        player.authenticated <soldier name: string>
        
        Effect: Player with name <soldier name> has been authenticated
        """
        self.getClient(data[0])


    def OnPlayerSpawn(self, action, data):
        """
        Request: player.onSpawn <spawning soldier name: string> <team: int>
        TODO: confirm team parameter
        """
        if len(data) < 2:
            return None

        spawner = self.getClient(data[0])
        spawner.team = self.getTeam(data[1])

        event = b3.events.EVT_CLIENT_JOIN
        return b3.events.Event(event, (), spawner)


    def OnPlayerKilled(self, action, data):
        """
        Request: player.killed' <killing soldier name: string> <killed soldier name: string> <weapon: string> <headshot: boolean>

        Effect: Player with name <killing soldier name> has killed <killed soldier name> Suicide is indicated with the same soldier name for killer and victim. If the server kills the player (through admin.killPlayer), it is indicated by showing the killing soldier name as Server. 
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



    def TODOOnServerLoadinglevel(self, action, data):
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
        return b3.events.Event(b3.events.EVT_GAME_WARMUP, data[0])

    def TODOOnServerLevelstarted(self, action, data):
        """
        server.onLevelStarted
        
        Effect: Level is started"""
        # next function call will increase roundcount by one, this is not wanted
        # as the game server provides us the exact round number in OnServerLoadinglevel()
        # hence we need to deduct one to compensate?
        # we'll still leave the call here since it provides us self.game.roundTime()
        self.game.startRound()
        self.game.rounds -= 1
        
        return b3.events.Event(b3.events.EVT_GAME_ROUND_START, self.game)
            
        
    def TODOOnServerRoundover(self, action, data):
        """
        server.onRoundOver <winning team: Team ID>
        
        Effect: The round has just ended, and <winning team> won
        """
        #['server.onRoundOver', '2']
        return b3.events.Event(b3.events.EVT_GAME_ROUND_END, data[0])
        
        
    def TODOOnServerRoundoverplayers(self, action, data):
        """
        server.onRoundOverPlayers <end-of-round soldier info : player info block>
        
        Effect: The round has just ended, and <end-of-round soldier info> is the final detailed player stats
        """
        #['server.onRoundOverPlayers', '8', 'clanTag', 'name', 'guid', 'teamId', 'kills', 'deaths', 'score', 'ping', '17', 'RAID', 'mavzee', 'EA_4444444444444444555555555555C023', '2', '20', '17', '310', '147', 'RAID', 'NUeeE', 'EA_1111111111111555555555555554245A', '2', '30', '18', '445', '146', '', 'Strzaerl', 'EA_88888888888888888888888888869F30', '1', '12', '7', '180', '115', '10tr', 'russsssssssker', 'EA_E123456789461416564796848C26D0CD', '2', '12', '12', '210', '141', '', 'Daezch', 'EA_54567891356479846516496842E17F4D', '1', '25', '14', '1035', '129', '', 'Oldqsdnlesss', 'EA_B78945613465798645134659F3079E5A', '1', '8', '12', '120', '256', '', 'TTETqdfs', 'EA_1321654656546544645798641BB6D563', '1', '11', '16', '180', '209', '', 'bozer', 'EA_E3987979878946546546565465464144', '1', '22', '14', '475', '152', '', 'Asdf 1977', 'EA_C65465413213216656546546546029D6', '2', '13', '16', '180', '212', '', 'adfdasse', 'EA_4F313565464654646446446644664572', '1', '4', '25', '45', '162', 'SG1', 'De56546ess', 'EA_123132165465465465464654C2FC2FBB', '2', '5', '8', '75', '159', 'bsG', 'N06540RZ', 'EA_787897944546565656546546446C9467', '2', '8', '14', '100', '115', '', 'Psfds', 'EA_25654321321321000006546464654B81', '2', '15', '15', '245', '140', '', 'Chezear', 'EA_1FD89876543216548796130EB83E411F', '1', '9', '14', '160', '185', '', 'IxSqsdfOKxI', 'EA_481321313132131313213212313112CE', '1', '21', '12', '625', '236', '', 'Ledfg07', 'EA_1D578987994651615166516516136450', '1', '5', '6', '85', '146', '', '5 56 mm', 'EA_90488E6543216549876543216549877B', '2', '0', '0', '0', '192']
        return b3.events.Event(b3.events.EVT_GAME_ROUND_PLAYER_SCORES, PlayerInfoBlock(data))
        
        
    def TODOOnServerRoundoverteamscores(self, action, data):
        """
        server.onRoundOverTeamScores <end-of-round scores: team scores>
        
        Effect: The round has just ended, and <end-of-round scores> is the final ticket/kill/life count for each team
        """
        #['server.onRoundOverTeamScores', '2', '1180', '1200', '1200']
        return b3.events.Event(b3.events.EVT_GAME_ROUND_TEAM_SCORES, data[1])

    def TODOOnPunkbusterMessage(self, action, data):
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
                
    def TODOOnPBVersion(self, match,data):
        """PB notifies us of the version numbers
        version = match.group('version')"""
        #self.debug('PunkBuster server named: %s' % match.group('servername') )
        #self.debug('PunkBuster Server version: %s' %( match.group('version') ) )
        pass

    def TODOOnPBNewConnection(self, match, data):
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

    def TODOOnPBLostConnection(self, match, data):
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

    def TODOOnPBScheduledTask(self, match, data):
        """We get notified the server ran a PB scheduled task
        Nothing much to do but it can be interresting to have
        this information logged
        """
        slot = match.group('slot')
        task = match.group('task')
        return b3.events.Event(b3.events.EVT_PUNKBUSTER_SCHEDULED_TASK, {'slot': slot, 'task': task})

    def TODOOnPBMasterQuerySent(self, match, data):
        """We get notified that the server sent a ping to the PB masters"""
        #pbmaster = match.group('pbmaster')
        #ip = match.group('ip')
        pass

    def TODOOnPBPlayerGuid(self, match, data):
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
            self.write(self.getCommand('kick', cid=client.cid, reason=reason[:80]))
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
        if isinstance(client, b3.clients.Client):
            self.write(self.getCommand('ban', guid=client.guid, reason=reason[:80]))
            return

        if admin:
            fullreason = self.getMessage('banned_by', self.getMessageVariables(client=client, reason=reason, admin=admin))
        else:
            fullreason = self.getMessage('banned', self.getMessageVariables(client=client, reason=reason))
        fullreason = self.stripColors(fullreason)
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
        
        if not silent and fullreason != '':
            self.say(fullreason)
        
        self.queueEvent(b3.events.Event(b3.events.EVT_CLIENT_BAN, {'reason': reason, 'admin': admin}, client))


    def unban(self, client, reason='', admin=None, silent=False, *kwargs):
        self.debug('UNBAN: Name: %s, Ip: %s, Guid: %s' %(client.name, client.ip, client.guid))
        if client.ip:
            response = self.write(self.getCommand('unbanByIp', ip=client.ip, reason=reason), needConfirmation=True)
            #self.verbose(response)
            if response == "OK":
                self.verbose('UNBAN: Removed ip (%s) from banlist' %client.ip)
                if admin:
                    admin.message('Unbanned: %s. His last ip (%s) has been removed from banlist.' % (client.exactName, client.ip))
                if admin:
                    fullreason = self.getMessage('unbanned_by', self.getMessageVariables(client=client, reason=reason, admin=admin))
                else:
                    fullreason = self.getMessage('unbanned', self.getMessageVariables(client=client, reason=reason))
                if not silent and fullreason != '':
                    self.say(fullreason)
        
        response = self.write(self.getCommand('unban', guid=client.guid, reason=reason), needConfirmation=True)
        #self.verbose(response)
        if response == "OK":
            self.verbose('UNBAN: Removed guid (%s) from banlist' %client.guid)
            if admin:
                admin.message('Unbanned: Removed %s guid from banlist' % (client.exactName))
        
        if self.PunkBuster:
            self.PunkBuster.unBanGUID(client)


    def tempban(self, client, reason='', duration=2, admin=None, silent=False, *kwargs):
        duration = b3.functions.time2minutes(duration)

        if isinstance(client, str):
            self.write(self.getCommand('tempban', guid=client.guid, duration=duration*60, reason=reason[:80]))
            return
        
        if admin:
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
        
        self.write(self.getCommand('tempban', guid=client.guid, duration=duration*60, reason=reason[:80]))
        
        
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
        levelnames = self.write(('mapSequencer.list',))
        mapList = []
        for l in levelnames:
            mapList.append(self.getEasyName(l))
        return mapList


    def rotateMap(self):
        """\
        load the next map/level
        """
        self.write(('mapSequencer.runNextMap'))


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
            self.write(('mapSequencer.setNextMap', map))
            self.say('Changing map to %s' % map)
            time.sleep(1)
            self.write(('mapSequencer.runNextMap'))

        
    def getPlayerPings(self):
        """Ask the server for a given client's pings
        """
        raise NotImplemented
        pings = {}
        try:
            pib = PlayerInfoBlock(self.write(('admin.listPlayers', 'all')))
            for p in pib:
                pings[p['name']] = int(p['ping'])
        except:
            self.debug('Unable to retrieve pings from playerlist')
        return pings


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


    ###############################################################################################
    #
    #    Other methods
    #    
    ###############################################################################################

    def getHardName(self, mapname):
        """ Change human map name to map id """
        raise NotImplemented('getHardName must be implemented in concrete classes')

    def getEasyName(self, mapname):
        """ Change map id to map human name """
        raise NotImplemented('getEasyName must be implemented in concrete classes')

    def getCvar(self, cvarName):
        """Read a server var"""
        if cvarName not in self._gameServerVars:
            self.warning('unknown cvar \'%s\'' % cvarName)
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
        """Set a server var"""
        if cvarName not in self._gameServerVars:
            self.warning('cannot set unknown cvar \'%s\'' % cvarName)
            return
        self.debug('Set cvar %s = \'%s\'', cvarName, value)
        try:
            self.write(('vars.%s' % cvarName, value))
        except FrostbiteCommandFailedError, err:
            self.error(err)

    def checkVersion(self):
        raise NotImplemented('checkVersion must be implemented in concrete classes')
        
    def getServerVars(self):
        raise NotImplemented('getServerVars must be implemented in concrete classes')

    def getClient(self, cid, _guid=None):
        """Get a connected client from storage or create it
        B3 CID   <--> ingame character name
        B3 GUID  <--> EA_guid
        """
        raise NotImplemented('getClient must be implemented in concrete classes')
    
    def getTeam(self, team):
        """convert frostbite team numbers to B3 team numbers"""
        raise NotImplemented('getTeam must be implemented in concrete classes')
        
    def getServerInfo(self):
        """query server info, update self.game and return query results
        """
        raise NotImplemented('getServerInfo must be implemented in concrete classes')

        
    def getNextMap(self):
        """Return the name of the next map
        """
        levelnames = self.write(('mapSequencer.list',))
        self.getServerInfo()
        currentName = self.game.mapName
        if len(levelnames) == 0:
            return self.getEasyName(currentName)
        elif len(levelnames) == 1:
            return self.getEasyName(levelnames[0])
        elif currentName not in levelnames:
            return self.getEasyName(levelnames[0])
        else:
            nextmap = levelnames[(levelnames.index(currentName) + 1) % len(levelnames)]
            return self.getEasyName(nextmap)
        

    def getSupportedMapIds(self):
        """return a list of supported levels for the current game mod"""
        return self.write(('mapSequencer.availableMaps'))

    def getMapsSoundingLike(self, mapname):
        """found matching level names for the given mapname (which can either
        be a level name or map name)
        If no exact match is found, then return close candidates using soundex
        and then LevenshteinDistance algoritms
        """
        supportedMaps = self.getSupportedMapIds()
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



#############################################################
# Below is the code that change a bit the b3.clients.Client
# class at runtime. What the point of coding in python if we
# cannot play with its dynamic nature ;)
#
# why ?
# because doing so make sure we're not broking any other 
# working and long tested parser. The change we make here
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
