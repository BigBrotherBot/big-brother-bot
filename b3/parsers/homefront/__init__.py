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
# aaaa/mm/dd - who 
#    blablbalb
#
from b3.parsers.homefront.protocol import MessageType, ChannelType

__author__  = 'xx'
__version__ = '0.0'

import sys
import string
import re
import time
import asyncore
import b3
import b3.parser
from b3.events import Event, EVT_UNKNOWN, EVT_CLIENT_JOIN, EVT_CLIENT_CONNECT, \
EVT_CLIENT_KILL, EVT_CLIENT_SUICIDE, EVT_CLIENT_KILL_TEAM, EVT_CLIENT_SAY, \
EVT_CLIENT_TEAM_SAY, EVT_CLIENT_KICK, EVT_CLIENT_BAN, EVT_CLIENT_BAN_TEMP, \
EVT_GAME_ROUND_END, EVT_GAME_ROUND_START
import rcon
import protocol


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

    _commands = {}
    _commands['message'] = ('say "%(prefix)s [%(name)s] %(message)s"')
    _commands['say'] = ('say "%(prefix)s %(message)s"')
    _commands['saybig'] = ('admin bigsay "%(prefix)s %(message)s"')
    _commands['kick'] = ('admin kick "%(name)s"')
    _commands['ban'] = ('admin kickban "%(name)s"')
    _commands['unban'] = ('admin unban "%(name)s"')
    _commands['tempban'] = ('admin kick "%(name)s"')
    
    _settings = {'line_length': 90, 
                 'min_wrap_length': 100}
    
    prefix = '%s: '
    
    def startup(self):
        self.debug("startup()")
        pass
        # add specific events
        #self.Events.createEvent('EVT_CLIENT_SQUAD_CHANGE', 'Client Squad Change')
                
        ## read game server info and store as much of it in self.game wich
        ## is an instance of the b3.game.Game class
    
    
    def routePacket(self, packet):
        self.console("%s" % packet)
        if packet is None:
            self.warning('cannot route empty packet')
        
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
                    self.queueEvent(Event(EVT_UNKNOWN, packet))
                    
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
                    self.warning('TODO handle packet : %s' % packet)
                    self.queueEvent(Event(EVT_UNKNOWN, packet))
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
                    self.verbose('Connecting to Homefront server ...')
                    self._serverConnection = protocol.Client(self, self._rconIp, self._rconPort, self._rconPassword, keepalive=True)
                    self._serverConnection.add_listener(self.routePacket)
                    self.output.set_homefront_client(self._serverConnection)
                    
                while self.working and not self._paused \
                and (self._serverConnection.connected or not self._serverConnection.authed):
                    #self.verbose2("\t%s" % (time.time() - self._serverConnection.last_pong_time))
                    if time.time() - self._serverConnection.last_pong_time > 6 \
                    and self._serverConnection.last_ping_time < self._serverConnection.last_pong_time:
                        self._serverConnection.ping()
                    asyncore.loop(timeout=3, count=1)
                    
        self.bot('Stop listening.')

        if self.exiting.acquire(1):
            self._serverConnection.close()
            if self.exitcode:
                sys.exit(self.exitcode)



    # ================================================
    # handle Game events.
    #
    # those methods are called by routePacket() and 
    # may return a B3 Event object which would then
    # be queued
    # ================================================
       
    def onServerHello(self, data):
        ## [int: Version]
        self.info("HF server (v %s) says hello to B3" % data)

            
    def onServerAuth(self, data):
        ## [boolean: Result]
        if data == 'true':
            self.info("B3 correctly authenticated on game server")
        else:
            self.warning("B3 failed to authente on game server (%s)" % data)


    def onServerLogin(self, data):
        # [string: Name]
        # (onServerLogin also occurs after a mapchange...)
        return Event(EVT_CLIENT_CONNECT, data, self.getClient(data))

    
    def onServerUid(self, data):
        # [string: Name] <[string: UID]>
        # example : courgette <1100012402D1245>
        match = re.search(r"^(?P<name>.+) <(?P<uid>.*)>$", data)
        if not match:
            self.error("could not get UID in [%s]" % data)
            return None
        client = self.getClient(match.group('name'))
        client.guid = match.group('uid')
        client.auth()
    
    def onServerLogout(self, data):
        ## [string: Name]
        self.debug('%s disconnected' % data)
        # do not call self.getClient() here because we do not want
        # to create a new client
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
        client.team = self.getTeam(match.group('team'))

    def onServerClan_change(self, data):
        # [string: Name] [string: Clan Name]
        match = re.search(r"^(?P<name>.+) (?P<clan>.*)$", data)
        if not match:
            self.error('onServerTeam_change failed match')
            return
        client = self.getClient(match.group('name'))
        client.clan = self.getTeam(match.group('clan'))

    def onServerKill(self, data):
        # [string: Killer Name] [string: DamageType] [string: Victim Name]
        # kill example: courgette EXP_Frag Freelander
        # suicide example#1: Freelander Suicided Freelander (triggers when player leaves the server)
        # suicide example#2: Freelander EXP_Frag Freelander
        ## @TODO: Check the possibility of two players having the exact same name which may lead to a false suicide event.
        match = re.search(r"^(?P<data>(?P<aname>[^;]+)\s+(?P<aweap>[A-z0-9_-]+)\s+(?P<vname>[^;]+))$", data)
        if not match:
            self.error("Can't parse kill line" % data)
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

        event = EVT_CLIENT_KILL

        if weapon == 'Suicided' or attacker == victim:
            event = EVT_CLIENT_SUICIDE
            self.verbose('%s suicided' % attacker.name)
        elif attacker.team != b3.TEAM_UNKNOWN and attacker.team == victim.team:
            event = EVT_CLIENT_KILL_TEAM
            self.verbose('Team kill, attacker: %s, victim: %s' % (attacker.name, victim.name))
        else:
            self.verbose('%s killed %s using %s' % (attacker.name, victim.name, weapon))

        return Event(event, (100, weapon, victim.hitloc), attacker, victim)

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
        return Event(EVT_GAME_ROUND_END, teamid)

    def onServerChange_level(self, data):
        ## [string: Map]
        ## example : fl-harbor
        match = re.search(r"^(?P<level>.*)$", data)
        if not match:
            self.error('onServerChange_level failed match')
            return

        levelname = match.group('level')
        self.verbose('onServerChange_level, levelname: %s' % levelname)
        return Event(EVT_GAME_ROUND_START, levelname)

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
            if type == 'team':
                return Event(EVT_CLIENT_TEAM_SAY, text, client)
            elif type == 'squad':
                raise NotImplementedError, "do squad say event"
            else:
                return Event(EVT_CLIENT_SAY, text, client)
    
    
    
    # =======================================
    # implement parser interface
    # =======================================
        
    def getPlayerList(self):
        """\
        Query the game server for connected players.
        return a dict having players' id for keys and players' data as another dict for values
        """
        ## @todo: getPlayerlist: make this wait for reply packets, stack them, and return full
        # exhaustive list of players
        self.output.write("RETRIEVE PLAYERLIST")

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
        raise NotImplementedError
    
    def say(self, msg):
        """\
        broadcast a message to all players
        """
        msg = self.stripColors(msg)
        for line in self.getWrap(msg, self._settings['line_length'], self._settings['min_wrap_length']):
            self.write(self.getCommand('say',  prefix=self.msgPrefix, message=line))

    def saybig(self, msg):
        """\
        broadcast a message to all players in a way that will catch their attention.
        """
        msg = self.stripColors(msg)
        for line in self.getWrap(msg, self._settings['line_length'], self._settings['min_wrap_length']):
            self.write(self.getCommand('saybig',  prefix=self.msgPrefix, message=line))

    def message(self, client, text):
        """\
        display a message to a given player
        """
        ## @todo: message: change that when the rcon protocol will allow us to
        # actually send private messages
        text = self.stripColors(text)
        for line in self.getWrap(text, self._settings['line_length'], self._settings['min_wrap_length']):
            self.write(self.getCommand('message', name=client.name, prefix=self.msgPrefix, message=line))

    def kick(self, client, reason='', admin=None, silent=False, *kwargs):
        """\
        kick a given players
        """
        self.debug('KICK : client: %s, reason: %s', client.name, reason)
        if admin:
            fullreason = self.getMessage('kicked_by', self.getMessageVariables(client=client, reason=reason, admin=admin))
        else:
            fullreason = self.getMessage('kicked', self.getMessageVariables(client=client, reason=reason))
        fullreason = self.stripColors(fullreason)
        reason = self.stripColors(reason)

        if not silent and fullreason != '':
            self.say(fullreason)

        self.write(self.getCommand('kick', name=client.name))
        self.queueEvent(Event(EVT_CLIENT_KICK, reason, client))
        client.disconnect()

    def ban(self, client, reason='', admin=None, silent=False, *kwargs):
        """\
        ban a given players
        """
        self.debug('BAN : client: %s, reason: %s', client.name, reason)
        if admin:
            fullreason = self.getMessage('banned_by', self.getMessageVariables(client=client, reason=reason, admin=admin))
        else:
            fullreason = self.getMessage('banned', self.getMessageVariables(client=client, reason=reason))
        fullreason = self.stripColors(fullreason)
        reason = self.stripColors(reason)

        if not silent and fullreason != '':
            self.say(fullreason)

        self.write(self.getCommand('ban', name=client.name))
        self.queueEvent(Event(EVT_CLIENT_BAN, reason, client))
        client.disconnect()

    def unban(self, client, reason='', admin=None, silent=False, *kwargs):
        """\
        unban a given players
        """
        self.debug('UNBAN: Name: %s' %client.name)
        response = self.write(self.getCommand('unban', name=client.name))
        ## @todo: unban: need to test response from the server
        self.verbose(response)
        if response:
            self.verbose('UNBAN: Removed name (%s) from banlist' %client.name)
            if admin:
                admin.message('Unbanned: Removed %s from banlist' %client.name)

    def tempban(self, client, reason='', duration=2, admin=None, silent=False, *kwargs):
        """\
        tempban a given players
        """
        self.debug('TEMPBAN : client: %s, reason: %s', client.name, reason)
        if admin:
            fullreason = self.getMessage('temp_banned_by', self.getMessageVariables(client=client, reason=reason, admin=admin, banduration=b3.functions.minutesStr(duration)))
        else:
            fullreason = self.getMessage('temp_banned', self.getMessageVariables(client=client, reason=reason, banduration=b3.functions.minutesStr(duration)))
        fullreason = self.stripColors(fullreason)
        reason = self.stripColors(reason)

        if not silent and fullreason != '':
            self.say(fullreason)

        self.write(self.getCommand('tempban', name=client.name))
        self.queueEvent(Event(EVT_CLIENT_BAN_TEMP, reason, client))
        client.disconnect()

    def getMap(self):
        """\
        return the current map/level name
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
        raise NotImplementedError
        
    def changeMap(self, map):
        """\
        load a given map/level
        return a list of suggested map names in cases it fails to recognize the map that was provided
        """
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

    def getTeam(self, team):
        team = str(team).lower()
        if team == '0':
            result = b3.TEAM_RED
        elif team == '1':
            result = b3.TEAM_BLUE
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
        """return a already connected client (authed or not) by searching the 
        clients name index. If not found, create a new client
        
        This method will always return a client object
        """
        client = self.clients.getByName(name)
        if not client:
            self.debug('client not found by name, creating new client')
            client = self.clients.newClient(name, name=name, state=b3.STATE_UNKNOWN, team=b3.TEAM_UNKNOWN)
        return client

