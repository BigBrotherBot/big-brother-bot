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
# 2013-01-20 - 0.4.1 - Courgette     - improve punkbuster event parsing
# 2014-05-02 - 0.4.2 - Fenix         - syntax cleanup
# 2014-07-16 - 0.4.3 - Fenix         - added admin key in EVT_CLIENT_KICK data dict when available
# 2014-07-18 - 0.4.4 - Fenix         - updated parser to comply with the new get_wrap implementation
# 2014-08-12 - 0.4.5 - Fenix         - make use of the GameEventRouter decorator
# 2014-08-29 - 0.4.6 - Fenix         - syntax cleanup
# 2015/02/07 - 0.4.7 - Thomas LEVEIL - correctly initialize Server client
# 2015/04/16 - 0.4.8 - Fenix         - uniform class variables (dict -> variable)

import asyncore
import b3
import b3.cron
import b3.events
import protocol
import rcon
import re
import sys
import time

from b3.clients import Client
from b3.decorators import GameEventRouter
from b3.functions import prefixText
from b3.lib.sourcelib import SourceQuery
from b3.parser import Parser
from ConfigParser import NoOptionError

__author__ = 'Courgette'
__version__ = '0.4.8'

ger = GameEventRouter()


class FrontlineParser(b3.parser.Parser):
    """
    The Frontline B3 parser class.
    """
    gameName = "frontline"
    privateMsg = True
    OutputClass = rcon.Rcon
    PunkBuster = None
    prefix = '%s: '

    _async_responses = {}   # dict to hold rcon asynchronous responses
    _serverConnection = None
    _original_connection_handle_close_method = None
    _rconUser = None

    # frontline engine does not support color code, so we
    # need this property in order to get stripColors working
    _reColor = re.compile(r'(\^[0-9])')
    _connectionTimeout = 30
    _playerlistInterval = 3
    _nbConsecutiveConnFailure = 0
    _server_banlist = {}

    _line_length = 200
    _line_color_prefix = ''

    ####################################################################################################################
    #                                                                                                                  #
    #  PARSER INITIALIZATION                                                                                           #
    #                                                                                                                  #
    ####################################################################################################################

    def startup(self):
        """
        Called after the parser is created before run().
        """
        self.debug("startup()")

        # create the server client
        self.clients.newClient('Server', guid='Server', name='Server', hide=True, pbid='Server', team=b3.TEAM_UNKNOWN)

        self.cron.add(b3.cron.CronTab(self.retrievePlayerList, second='*/%s' % self._playerlistInterval))

    def run(self):
        """
        Main worker thread for B3.
        """
        try:
            self._rconUser = self.config.get("server", "rcon_user")
        except NoOptionError, err:
            self.error("Cannot find rcon_user in B3 main config file. %s", err)
            raise SystemExit("incomplete config")

        self.screen.write('Startup complete : B3 is running! Let\'s get to work!\n\n')
        self.screen.write('(If you run into problems, check %s in the B3 root directory for '
                          'detailed log info)\n' % self.config.getpath('b3', 'logfile'))

        self.updateDocumentation()

        self.bot('Start listening...')
        while self.working:
            # While we are working, connect to the Frontline server
            if self._paused:
                if not self._pauseNotice:
                    self.bot('PAUSED - not parsing any lines: B3 will be out of sync')
                    self._pauseNotice = True
            else:
                if self._serverConnection is None:
                    self.bot('connecting to Frontline server %s:%s with user %s...', self._rconIp, self._rconPort,
                             self._rconUser)
                    self._serverConnection = protocol.Client(self, self._rconIp, self._rconPort, self._rconUser,
                                                             self._rconPassword, keepalive=True)

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

        self.bot('Stop listening...')

        with self.exiting:
            self._serverConnection.close()
            if self.exitcode:
                sys.exit(self.exitcode)

    ####################################################################################################################
    #                                                                                                                  #
    #  OTHER METHODS                                                                                                   #
    #                                                                                                                  #
    ####################################################################################################################

    def routePacket(self, packet):
        if packet is None:
            self.warning('Cannot route empty packet')
        else:
            if not packet.startswith('PlayerList:'):
                self.console("%s" % packet.strip())
            hfunc, param_dict = ger.getHandler(packet)
            if hfunc:
                event = hfunc(self, **param_dict)
                if event:
                    self.queueEvent(event)
            else:
                self.warning('TODO: handle packet : %s' % packet)
                self.queueEvent(self.getEvent('EVT_UNKNOWN', packet))

    def _handle_connection_close(self):
        if len(self.clients.getList()):
            self.debug("Clearing player list")
            self.clients.empty()
        self._original_connection_handle_close_method()

    def getClient(self, cid):
        """
        Return a already connected client by searching the clients cid index.
        This method can return None.
        """
        client = self.clients.getByCID(cid)
        if client:
            return client
        return None

    def getClientOrCreate(self, cid, guid, name):
        """
        Return a already connected client by searching the clients guid index or create a new client.
        This method can return None.
        """
        client = self.clients.getByCID(cid)
        if client is None:
            client = self.clients.newClient(cid, guid=guid, name=name, team=b3.TEAM_UNKNOWN)
            client.last_update_time = time.time()
        return client

    def retrievePlayerList(self):
        """
        Send RETRIEVE PLAYERLIST to the server.
        """
        self.write('PLAYERLIST')

    def retrieveBanList(self):
        """
        Send RETRIEVE BANLIST to the server.
        """
        self.write('BanList')

    def getTeam(self, teamId):
        """
        Convert team id to B3 team numbers.
        """
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
            self.verbose2("Unrecognized team id : %r", team)
            result = b3.TEAM_UNKNOWN
        return result

    def queryServerInfo(self):
        # read game server info and store as much of it in self.game wich
        # is an instance of the b3.game.Game class
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

    ####################################################################################################################
    #                                                                                                                  #
    #  GAME EVENTS HANDLERS                                                                                            #
    #                                                                                                                  #
    ####################################################################################################################

    @ger.gameEvent(
        r'^DEBUG: ((Script)?Log|Error|(Perf|Script)Warning|SeamlessTravel): .*',
        r'^DEBUG: (DevOnline|NetComeGo|RendezVous|LoadingScreenLog|Difficulty|LineCheckLog): .*',
        r'^DEBUG: Warning: .*',
        r'^DEBUG: DevNet: .*',
        r'^UnBan failed! Player ProfileID or Hash is not banned: .*',
        r'^Forced transition to next map$',
        r'^.*: Player List: [Slot #] [GUID] [Address] [Status] [Power] [Auth Rate] [Recent SS] [O/S] [Name]$',)
    def ignoreGameEvent(self, *args, **kwargs):
        """
        Do nothing.
        """
        pass

    @ger.gameEvent(r"^WELCOME! Frontlines: Fuel of War \(RCON\) VER=(?P<version>.+) CHALLENGE=(?P<challenge>.*)$")
    def onServerWelcome(self, version, challenge):
        self.info("Connected to Frontline server: RCON version: %s", version)

    @ger.gameEvent(re.compile(r"^PlayerList: (?P<data>.*)$", re.MULTILINE | re.DOTALL | re.IGNORECASE))
    def onServerPlayerlist(self, data):
        """
        PlayerList: Map=CQ-Gnaw Time=739 Players=0/32 Tickets=500,500 Round=2/3
        ID    Name    Ping    Team    Squad    Score    Kills    Deaths    TK    CP
        Time    Idle    Loadout    Role    RoleLvl    Vehicle    Hash    ProfileID
        """
        self.verbose2("Playerlist : %r" % data)
        lines = data.split('\n')
        match = re.match(r"PlayerList: "
                         r"Map=(?P<map>.+) "
                         r"Time=(?P<remaining_time>(-1|\d+)) "
                         r"Players=(?P<players>\d+)/(?P<total_slots>\d+) "
                         r"Tickets=(?P<tickets>,\d+) "
                         r"Round=(?P<current_round>\d+)/(?P<total_rounds>\d+)", lines[0])
        if match:
            self.game.mapName = match.group('map')
            self.game.sv_maxclients = match.group('total_slots')
            self.game.rounds = int(match.group('current_round'))
            self.game.g_maxrounds = int(match.group('total_rounds'))
            self.game.remaining_time = int(match.group('remaining_time'))
            self.game.tickets = int(match.group('tickets'))

        self.sync()

        headers = ("ID", "Name", "Ping", "Team", "Squad", "Score", "Kills", "Deaths",
                   "TK", "CP", "Time", "Idle", "Loadout", "Role", "RoleLvl", "Vehicle", "Hash", "ProfileID")

        for line in lines[2:]:
            if len(line):
                data = line.split('\t')
                pdata = dict(zip(headers, data))
                if 'ProfileID' not in pdata:
                    self.debug("no ProfileID found")
                    continue
                if pdata['ProfileID'] == 0:
                    self.debug("ProfileID is 0")
                    continue
                self.debug("player: %r", pdata)
                client = self.getClientOrCreate(pdata['ID'], pdata['ProfileID'], pdata['Name'])
                if client:
                    client.name = pdata['Name']
                    client.team = self.getTeam(pdata['Team'])
                    client.data = pdata
                    client.last_update_time = time.time()

    @ger.gameEvent(r"^Login SUCCESS! User:(?P<user>.*)$")
    def onServerRconLoginSucess(self, user):
        self.bot("B3 correctly authenticated on game server as user %r", user)
        self.write("CHATLOGGING TRUE")
        self.write("DebugLogging TRUE")
        self.write("Punkbusterlogging TRUE")

    @ger.gameEvent(r"^DEBUG: RendezVous: Update Gathering .*")
    def onServerPlayerLogin(self):
        # DEBUG: RendezVous: Update Gathering 1561500: 7/0
        self.retrievePlayerList()

    @ger.gameEvent(r"^(?P<var>ChatLogging) now (?P<data>.*)$", r"^(?P<var>DebugLogging) now (?P<data>.*)$")
    def onServerVarChange(self, var, data):
        self.info("%s is now: %r", var, data)

    @ger.gameEvent(r'^CHAT: PlayerName="(?P<playerName>[^"]+)" Channel="(?P<channel>[^"]+)" Message="(?P<text>.*)"$')
    def onServerChat(self, playerName, channel, text):
        client = self.clients.getByExactName(playerName)
        if client is None:
            self.debug("could not find client")
            return
        if channel == 'TeamSay':
            return self.getEvent('EVT_CLIENT_TEAM_SAY', text, client)
        elif channel == 'Say':
            return self.getEvent('EVT_CLIENT_SAY', text, client)
        else:
            self.warning("unknown chat channel : %s", channel)

    @ger.gameEvent(r'^.*: Player GUID Computed (?P<pbid>[0-9a-f]+)\(-\) \(slot #(?P<cid>\d+)\) (?P<ip>[0-9.]+):(?P<port>\d+) (?P<name>.+)$')
    def onPunkbusterGUID(self, pbid, cid, ip, port, name):
        client = self.clients.getByCID(cid)
        if client:
            client.pbid(pbid)
            client.ip = ip
            client.save()

    @ger.gameEvent(r'^.*: (?P<cid>\d+)\s+(?P<pbid>[a-z0-9]+)?\(-\) (?P<ip>[0-9.]+):(?P<port>\d+) (\w+)\s+(\d+)\s+([\d.]+)\s+(\d+)\s+\((.)\) "(?P<name>.+)"$')
    def onPunkbusterPlayerList(self, pbid, cid, ip, port, name):
        client = self.clients.getByCID(cid)
        if client:
            if pbid:
                client.pbid(pbid)
            client.ip = ip
            client.save()

    @ger.gameEvent(re.compile(r'^Banned Player: PlayerName="(?P<name>.+)" PlayerID=(?P<cid>(-1|\d+)) ProfileID=(?P<guid>\d+) Hash=(?P<hhash>.*) BanDuration=(?P<duration>-?\d+)( Permanently)?$', re.MULTILINE))
    def onServerBan(self, name, cid, guid, hhash, duration):
        """
        Kicked Player as part of ban: PlayerName="Courgette" PlayerID=1 ProfileID=1561500 Hash= BanDuration=-1
        Banned Player: PlayerName="Courgette" PlayerID=1 ProfileID=1561500 Hash= BanDuration=-1 Permanently
        """
        # we are using storage instead of self.clients because the
        # player might already have been kick
        client = self.storage.getClient(Client(guid=guid))
        if client:
            self.saybig("%s added to server banlist" % client.name)
        else:
            self.error('Cannot find banned client')
        # update banlist
        self.retrieveBanList()

    @ger.gameEvent(re.compile(r'^UnBanned Player: PlayerName="(?P<name>.+)" PlayerID=(-1|\d+) ProfileID=(?P<guid>\d+) Hash=(?P<hhash>.*)$'))
    def onServerUnBan(self, name, guid, hhash):
        """
        UnBanned Player: PlayerName="" PlayerID=-1 ProfileID=1561500 Hash=
        """
        # we are using storage instead of self.clients because the player cannot be connected
        client = self.storage.getClient(Client(guid=guid))
        if client:
            self.saybig("%s removed from server banlist" % client.name)
        else:
            self.error('Cannot find banned client')
        # update banlist
        self.retrieveBanList()

    @ger.gameEvent(r"CurrentMap is: (?P<mapname>.+)")
    def onGetCurrentMapResponse(self, mapname):
        self._async_responses['GetCurrentMap'] = mapname

    @ger.gameEvent(r"NextMap is: (?P<mapname>.+)")
    def onGetNextMapResponse(self, mapname):
        self._async_responses['GetNextMap'] = mapname

    @ger.gameEvent(re.compile(r"^MapList: (?P<data>.+)", re.MULTILINE|re.DOTALL))
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

    @ger.gameEvent(r"^Login SUCCESS! User:(?P<user>.*)$")
    def onTest(self, data):
        self.debug("TEST %r ", data)

    # ------------------------------------- /!\  this one must be the last /!\ --------------------------------------- #

    @ger.gameEvent(r'^(?P<data>.+)$')
    def on_unknown_line(self, data):
        """
        Catch all lines that were not handled.
        """
        self.warning("unhandled log line : %s : please report this on the B3 forums" % data)

    ####################################################################################################################
    #                                                                                                                  #
    #  B3 PARSER INTERFACE IMPLEMENTATION                                                                              #
    #                                                                                                                  #
    ####################################################################################################################

    def getPlayerList(self):
        """
        Returns a list of client objects.
        """
        raise NotImplementedError

    def authorizeClients(self):
        """
        For all connected players, fill the client object with properties allowing to find 
        the user in the database (usualy guid, or punkbuster id, ip) and call the 
        Client.auth() method 
        """
        # in Frontline, there is no synchronous way to obtain a player guid
        # the onServerUid event will be the one calling Client.auth()
        raise NotImplementedError

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
        # we are unable to get the exact list of connected players in a synchronous
        # way. So we use .last_update_time timestamp to detect player we still
        # have in self.clients but that are no longer on the game server
        self.debug("Synchronizing clients")
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
        """
        Broadcast a message to all players.
        :param msg: The message to be broadcasted
        """
        msg = prefixText([self.msgPrefix], self.stripColors(msg))
        for line in self.getWrap(msg):
            self.write('SAY %s' % line)

    def saybig(self, msg):
        """
        Broadcast a message to all players in a way that will catch their attention.
        :param msg: The message to be broadcasted
        """
        msg = prefixText(['#' + self.msgPrefix + '#'], self.stripColors(msg))
        for line in self.getWrap(msg):
            self.write('SAY %s' % line)

    def message(self, client, text):
        """
        Display a message to a given client
        :param client: The client to who send the message
        :param text: The message to be sent
        """
        # actually send private messages
        text = self.stripColors(text)
        for line in self.getWrap(text):
            self.write('PLAYERSAY PlayerID=%(cid)s SayText="%(message)s"' % {'cid': client.cid, 'message': line})

    def kick(self, client, reason='', admin=None, silent=False, *kwargs):
        """
        Kick a given client.
        :param client: The client to kick
        :param reason: The reason for this kick
        :param admin: The admin who performed the kick
        :param silent: Whether or not to announce this kick
        """
        self.debug('KICK : client: %s, reason: %s', client.cid, reason)
        if admin:
            variables = self.getMessageVariables(client=client, reason=reason, admin=admin)
            fullreason = self.getMessage('kicked_by', variables)
        else:
            variables = self.getMessageVariables(client=client, reason=reason)
            fullreason = self.getMessage('kicked', variables)

        fullreason = self.stripColors(fullreason)
        reason = self.stripColors(reason)

        if not silent and fullreason != '':
            self.say(fullreason)

        if len(reason):
            self.write('KICK ProfileID=%s Reason="%s"' % (client.guid, reason))
        else:
            self.write('KICK ProfileID=%s' % client.guid)

        self.queueEvent(b3.events.Event(self.getEventID('EVT_CLIENT_KICK'), {'reason': reason, 'admin': None}, client))
        client.disconnect()

    def ban(self, client, reason='', admin=None, silent=False, *kwargs):
        """
        Ban a given client.
        :param client: The client to ban
        :param reason: The reason for this ban
        :param admin: The admin who performed the ban
        :param silent: Whether or not to announce this ban
        """
        self.debug('BAN : client: %s, reason: %s', client.cid, reason)
        if admin:
            variables = self.getMessageVariables(client=client, reason=reason, admin=admin)
            fullreason = self.getMessage('banned_by', variables)
        else:
            variables = self.getMessageVariables(client=client, reason=reason)
            fullreason = self.getMessage('banned', variables)

        if not silent and fullreason != '':
            self.say(fullreason)

        if len(reason):
            self.write('BAN ProfileID=%s BanTime=0 Reason="%s"' % (client.guid, reason))
        else:
            self.write('BAN ProfileID=%s BanTime=0' % client.guid)

        self.queueEvent(self.getEvent('EVT_CLIENT_BAN', {'reason': reason, 'admin': admin}, client))
        client.disconnect()

    def unban(self, client, reason='', admin=None, silent=False, *kwargs):
        """
        Unban a client.
        :param client: The client to unban
        :param reason: The reason for the unban
        :param admin: The admin who unbanned this client
        :param silent: Whether or not to announce this unban
        """
        self.write('UNBAN ProfileID=%s' % client.guid)
        if admin:
            admin.message('Unbanned: removed %s from banlist' % client.name)
        self.queueEvent(self.getEvent('EVT_CLIENT_UNBAN', reason, client))

    def tempban(self, client, reason='', duration=2, admin=None, silent=False, *kwargs):
        """
        Tempban a client.
        :param client: The client to tempban
        :param reason: The reason for this tempban
        :param duration: The duration of the tempban
        :param admin: The admin who performed the tempban
        :param silent: Whether or not to announce this tempban
        """
        self.debug('TEMPBAN : client: %s, reason: %s', client.cid, reason)
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
                                                              'admin': admin}, client))
        client.disconnect()

    def getMap(self):
        """
        Return the current map/level name.
        """
        self._async_responses['GetCurrentMap'] = None
        self.write('GetCurrentMap')
        count = 0
        while self._async_responses['GetCurrentMap'] is None and count < 30:
            time.sleep(.1)
            count += 1
        return self._async_responses['GetCurrentMap']

    def getNextMap(self):
        """
        Return the name of the next map.
        """
        self._async_responses['GetNextMap'] = None
        self.write('GetNextMap')
        count = 0
        while self._async_responses['GetNextMap'] is None and count < 30:
            time.sleep(.1)
            count += 1
        return self._async_responses['GetNextMap']

    def getMaps(self):
        """
        Return the available maps/levels name
        """
        self._async_responses['MapList'] = None
        self.write('MapList')
        count = 0
        while self._async_responses['MapList'] is None and count < 30:
            time.sleep(.1)
            count += 1
        return self._async_responses['MapList']

    def rotateMap(self):
        """
        Load the next map/level
        """
        self.write('NEXTMAP')

    def changeMap(self, mapname):
        """
        Load a given map/level
        Return a list of suggested map names in cases it fails to recognize the map that was provided
        """
        self.write('ForceMapChange %s' % mapname)

    def getEasyName(self, mapname):
        """
        Change levelname to real name.
        """
        raise NotImplementedError

    def getPlayerPings(self, filter_client_ids=None):
        """
        Returns a dict having players' id for keys and players' ping for values.
        """
        pings = {}
        clients = self.clients.getList()
        if filter_client_ids:
            clients = filter(lambda client: client.cid in filter_client_ids, clients)

        for c in clients:
            try:
                pings[c.cid] = int(c.data['Ping'])
            except AttributeError:
                pass
        return pings

    def getPlayerScores(self):
        """
        Returns a dict having players' id for keys and players' scores for values
        """
        pings = {}
        clients = self.clients.getList()
        for c in clients:
            try:
                pings[c.cid] = int(c.data['Kills'])
            except AttributeError:
                pass
        return pings

    def inflictCustomPenalty(self, penalty_type, client, reason=None, duration=None, admin=None, data=None):
        """
        Called if b3.admin.penalizeClient() does not know a given penalty type. 
        Overwrite this to add customized penalties for your game like 'slap', 'nuke', 
        'mute' or anything you want.
        /!\ This method must return True if the penalty was inflicted.
        """
        pass