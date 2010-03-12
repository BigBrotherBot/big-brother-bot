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
# CHANGELOG
# 2010/03/09 - 0.1 - Courgette
# * parser is able to connect to a distant BFBC2 server through TCP
#   and listens for BFBC2 events.
# * BFBC2 events are routed to create matching B3 events
# 2010/03/12 - 0.2 - Courgette
# * the bot recognize players, commands and can respond
#
#
# TODO :
# * fix the issue regarding messages sent to clients which are sent at
#   a too high frequence. A solution might be to introduce a 'line of text' 
#   queue management at the client level.
# * test commands. at the moment only 'message' and 'say' commands have been tested
#

__author__  = 'Courgette'
__version__ = '0.2'

import sys, time, re, string, traceback
import b3
import b3.events
import b3.parser
from b3.parsers.punkbuster import PunkBuster
import rcon
import b3.cvar

from b3.parsers.bfbc2.bfbc2Connection import *


#----------------------------------------------------------------------------------------------------------------------------------------------
class Bfbc2Parser(b3.parser.Parser):
    gameName = 'bfbc2'
    privateMsg = True
    OutputClass = rcon.Rcon
    
    _bfbc2EventsListener = None
    _bfbc2Connection = None
    _nbConsecutiveConnFailure = 0
    _connectionTimeout = 60

    # BFBC2 does not support color code, so we need this property
    # in order to get stripColors working
    _reColor = re.compile(r'(\^[0-9])') 

    _settings = {}
    _settings['line_length'] = 65
    _settings['min_wrap_length'] = 100

    _commands = {}
    _commands['message'] = ('admin.yell', '%(prefix)s [pm] %(message)s', '%(duration)s', 'player', '%(cid)s')
    _commands['say'] = ('admin.yell', '%(prefix)s %(message)s', '%(duration)s', 'all')
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
        (re.compile(r'^PunkBuster Server: Lost Connection \(slot #(?P<slot>\d+)\) (?P<ip>[^:]+):(?P<port>\d+) (?P<pbuid>[^\s]+)\s(?P<name>.+)$'), 'OnPBLostConnection'),
        (re.compile(r'^PunkBuster Server: Master Query Sent to \((?P<pbmaster>[^\s]+)\) (?P<ip>[^:]+)$'), 'OnPBMasterQuerySent'),
        (re.compile(r'^PunkBuster Server: New Connection \(slot #(?P<slot>\d+)\) (?P<ip>[^:]+):(?P<port>\d+) \[(?P<something>[^\s]+)\]\s"(?P<name>.+)".*$'), 'OnPBNewConnection')
     )

    PunkBuster = None

    def startup(self):
        
        # add specific events
        self.Events.createEvent('EVT_PUNKBUSTER_SCHEDULED_TASK', 'PunkBuster scheduled task')
        self.Events.createEvent('EVT_PUNKBUSTER_CLIENT_CONNECT', 'PunkBuster client connection')
        self.Events.createEvent('EVT_CLIENT_GEAR_CHANGE', 'Client gear change')
        
        try:
            self._connectionTimeout = self.config.getint('server', 'timeout')
        except: 
            self.warning("Error reading timeout from config file. Using default value")
        self.info("BFBC2 connection timeout: %s" % self._connectionTimeout)
        
        if self.config.has_option('server', 'punkbuster') and self.config.getboolean('server', 'punkbuster'):
            self.PunkBuster = PunkBuster(self)
            
        version = self.output.write('version')
        self.info('BFBC2 server version : %s' % version)
        if version[0] != 'BFBC2':
            raise Exception("the bfbc2 parser can only work with BattleField Bad Company 2")
        
        self.info('Server info : %s' % self.output.write('serverInfo'))
        self.info('is PunkBuster enabled on server ? %s' % self.output.write('vars.punkBuster'))
        self.info('PunkBuster version : %s' % self.output.write(('punkBuster.pb_sv_command', 'PB_SV_VER')))
        self.info('PunkBuster PB_SV_PList : %s' % self.output.write(('punkBuster.pb_sv_command', 'PB_SV_PList')))
        
        self.info("available server commands :")
        availableCmd = self.output.write('help')
        for cmd in availableCmd:
            self.debug(cmd)
            
        self.getServerVars()
        
        self.setCvar('serverDescription', 'test description')
        self.debug('new description : %s' % self.getCvar('serverDescription'))
        self.setCvar('serverDescription', '')
        self.debug('new description : %s' % self.getCvar('serverDescription'))
        
        self.info('connecting all players...')
        plist = self.getPlayerList()
        for cid, c in plist.iteritems():
            client = self.getClient(cid)
            if client:
                self.debug('Joining %s' % client.name)
                self.queueEvent(b3.events.Event(b3.events.EVT_CLIENT_JOIN, None, client))
            

    def run(self):
        """Main worker thread for B3"""
        self.bot('Start listening ...')
        self.screen.write('Startup Complete : Let\'s get to work!\n\n')
        self.screen.write('(Please check %s in the B3 root directory for more detailed info)\n' % self.config.getpath('b3', 'logfile'))
        #self.screen.flush()

        self.updateDocumentation()

        while self.working:
            if self._paused:
                if self._pauseNotice == False:
                    self.bot('PAUSED - Not parsing any lines, B3 will be out of sync.')
                    self._pauseNotice = True
            else:
                
                try:
                    if not self._bfbc2Connection:
                        self.verbose('Connecting to BFBC2 server ...')
                        self._bfbc2Connection = Bfbc2Connection(self._rconIp, self._rconPort, self._rconPassword)
                        self._bfbc2Connection.timeout = self._connectionTimeout
                        self._bfbc2Connection.subscribeToBfbc2Events()
                        self.clients.sync()
                        self._nbConsecutiveConnFailure = 0
                        
                    bfbc2packet = self._bfbc2Connection.handle_bfbc2_events()
                    self.console("%s" % bfbc2packet)
                    try:
                        self.routeBfbc2Packet(bfbc2packet)
                    except SystemExit:
                        raise
                    except Exception, msg:
                        self.error('could not route BFBC2 packet %s: %s', msg, traceback.extract_tb(sys.exc_info()[2]))
                except Bfbc2Exception, e:
                    self.debug(str(e))
                    self._nbConsecutiveConnFailure += 1
                    if self._nbConsecutiveConnFailure <= 40:
                        self.debug('sleeping 0.25 sec...')
                        time.sleep(0.25)
                    elif self._nbConsecutiveConnFailure <= 60:
                        self.debug('sleeping 2 sec...')
                        time.sleep(2)
                    else:
                        self.debug('sleeping 10 sec...')
                        time.sleep(10)
                    
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
            self.debug('routing ----> %s' % func)
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

    def getClientByExactNameOrConnect(self, exactName):
        client = self.clients.getByExactName(exactName)
        if client is None:
            self.output.write('')


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
                self.debug('player: %s %s %s %s' % (clantag, name, squadId, teamId))
                players[name] = {'clantag':clantag, 'name':name, 'guid':name, 'squadId':squadId, 'teamId':self.getTeam(teamId)}
        return players

    def getServerVars(self):
        for v in self._gameServerVars:
            self.getCvar(v)

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
            client.disconnect()
        return None

    def OnPlayerJoin(self, action, data):
        #player.onJoin: ['OrasiK']
        name = data[0]
        client = self.getClient(name)
        return b3.events.Event(b3.events.EVT_CLIENT_JOIN, data, client)

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
            slot = match.group('slot')
            ip = match.group('ip')
            port = match.group('port')
            something = match.group('something')
            client.ip = ip
            client.port = port
            self.debug('OnPBNewConnection: client updated with %s' % data)
        else:
            self.warning('OnPBNewConnection: we\'ve been unable to get the client')
        return b3.events.Event(b3.events.EVT_PUNKBUSTER_CLIENT_CONNECT, data, client)

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
            client = b3.clients.Client(console=self, cid=name, guid=name)
        # update client data
        self.debug("saving client PB_ID to database")
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



    def message(self, client, text):
        try:
            if client == None:
                self.say(text)
            elif client.cid == None:
                pass
            else:
                lines = []
                text = self.stripColors(text)
                for line in self.getWrap(text, self._settings['line_length'], self._settings['min_wrap_length']):
                    lines.append(self.getCommand('message', cid=client.cid, prefix=self.stripColors(self.msgPrefix), message=line, duration=2300))

                self.writelines(lines)
        except:
            pass

    def say(self, msg):
        lines = []
        msg = self.stripColors(msg)
        for line in self.getWrap(msg, self._settings['line_length'], self._settings['min_wrap_length']):
            lines.append(self.getCommand('say', prefix=self.stripColors(self.msgPrefix), message=line, duration=2300))

        if len(lines):        
            self.writelines(lines)


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
            self.clients.newClient(name, guid=name, name=name)
            client = self.clients.getByCID(name)
        return client

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
                sp.auth()

    def getCvar(self, cvarName):
        if cvarName not in self._gameServerVars:
            self.warning('cannot get unknown cvar \'%s\'' % cvarName)
            return None
        
        words = self.write(('vars.%s' % cvarName,))
        self.debug('Get cvar %s = [%s]', cvarName, words)
        
        if words and len(words) == 1:
            value = words[0]
            
            val = None
            
            if type(value) == tuple and len(value) == 1:
                if value[0] == 'true':
                    val = True
                elif value[0] == 'false':
                    val = False
                elif value[0] == '':
                    val = ''
                else:
                    try:
                        val = int(value[0])
                    except ValueError:
                        val = value[0]
                
            return b3.cvar.Cvar(cvarName, value=val)
        return None

    def setCvar(self, cvarName, value):
        if cvarName not in self._gameServerVars:
            self.warning('cannot set unknown cvar \'%s\'' % cvarName)
            return
        self.debug('Set cvar %s = \'%s\'', cvarName, value)
        self.write(('vars.%s' % cvarName, value))

    
    def getMaps(self):
        return None

    def sync(self):
        plist = self.getPlayerList()
        mlist = {}

        for name, c in plist.iteritems():
            client = self.clients.getByName(name)
            if client:
                mlist[name] = client
         
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
    
    def write(self, msg, maxRetries=None):
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
            

    def getWrap(self, text, length=80, minWrapLen=150):
        """Returns a sequence of lines for text that fits within the limits
        TODO: simplify this method as in BFBC2, we make sure the text contains
        no Q3 color code before passing it here.
        """
        if not text:
            return []

        length = int(length)
        text = text.replace('//', '/ /')

        if len(text) <= minWrapLen:
            return [text]
        #if len(re.sub(REG, '', text)) <= minWrapLen:
        #    return [text]

        text = re.split(r'\s+', text)

        lines = []
        color = '^7';

        line = text[0]
        for t in text[1:]:
            if len(re.sub(self._reColor, '', line)) + len(re.sub(self._reColor, '', t)) + 2 <= length:
                line = '%s %s' % (line, t)
            else:
                if len(lines) > 0:
                    lines.append('>%s' % line)
                else:
                    lines.append('%s' % line)

                m = re.findall(self._reColor, line)
                if m:
                    color = m[-1]

                line = t

        if len(line):
            if len(lines) > 0:
                lines.append('>%s' % line)
            else:
                lines.append('%s' % line)

        return lines
