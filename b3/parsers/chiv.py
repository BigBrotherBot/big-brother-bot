# -*- coding: utf-8 -*-

# ################################################################### #
#                                                                     #
#  BigBrotherBot(B3) (www.bigbrotherbot.net)                          #
#  Copyright (C) 2005 Michael "ThorN" Thornton                        #
#                                                                     #
#  This program is free software; you can redistribute it and/or      #
#  modify it under the terms of the GNU General Public License        #
#  as published by the Free Software Foundation; either version 2     #
#  of the License, or (at your option) any later version.             #
#                                                                     #
#  This program is distributed in the hope that it will be useful,    #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of     #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the       #
#  GNU General Public License for more details.                       #
#                                                                     #
#  You should have received a copy of the GNU General Public License  #
#  along with this program; if not, write to the Free Software        #
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA      #
#  02110-1301, USA.                                                   #
#                                                                     #
# ################################################################### #

import b3
import sys
import asyncore
import socket

from b3.parser import Parser
from b3.plugins.admin import AdminPlugin
from struct import pack
from struct import unpack
from hashlib import sha1

__author__ = 'tliszak'
__version__ = '1.8'


class MessageType(object):

    SERVER_CONNECT = 0
    SERVER_CONNECT_SUCCESS = 1
    PASSWORD = 2
    PLAYER_CHAT = 3
    PLAYER_CONNECT = 4
    PLAYER_DISCONNECT = 5
    SAY_ALL = 6
    SAY_ALL_BIG = 7
    SAY = 8
    MAP_CHANGED = 9
    MAP_LIST = 10
    CHANGE_MAP = 11
    ROTATE_MAP = 12
    TEAM_CHANGED = 13
    NAME_CHANGED = 14
    KILL = 15
    SUICIDE = 16
    KICK_PLAYER = 17
    TEMP_BAN_PLAYER = 18
    BAN_PLAYER = 19
    UNBAN_PLAYER = 20
    ROUND_END = 21
    PING = 22


class ChivParser(Parser):
    
    ## parser code name to use in b3.ini
    gameName = 'chiv'
    
    _client = None
    _currentMap = None
    _currentMapIndex = None
    _mapList = None

    ####################################################################################################################
    #                                                                                                                  #
    #   PARSER INITIALIZATION                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    def __new__(cls, *args, **kwargs):
        ChivParser.patch_admin_plugin_doList()
        ChivParser.patch_admin_plugin_cmd_find()
        return Parser.__new__(cls)

    def run(self):
        """
        Main worker thread for B3.
        """
        self.screen.write('Startup complete : B3 is running! Let\'s get to work!\n\n')
        self.screen.write('If you run into problems check your B3 log file for more information\n')
        self.screen.flush()
        self.updateDocumentation()

        while self.working:
            if self._paused:
                if self._pauseNotice is False:
                    self.bot('PAUSED - not parsing any lines: B3 will be out of sync')
                    self._pauseNotice = True
            else:
                if self._client is None:
                    self._client = Client(self, self._rconIp, self._rconPort, self._rconPassword, self.handlePacket)
                
                asyncore.loop(timeout=3, use_poll=True, count=1)

        with self.exiting:
            self._client.close()
            if self.exitcode:
                sys.exit(self.exitcode)

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENT HANDLERS                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def handlePacket(self, packet):
        """
        Handle a received packet.
        :param packet: The received packet
        """
        if packet.msgType == MessageType.SERVER_CONNECT:
            challenge = packet.getString()
            self._client.send_password(challenge)
        elif packet.msgType == MessageType.SERVER_CONNECT_SUCCESS:
            self._mapList = None
            self._client.isAuthed = True
            
        if not self._client.isAuthed:
            return
            
        if packet.msgType == MessageType.PLAYER_CHAT:
            playerId = packet.getGUID()
            message = packet.getString()
            team = packet.getInt()
            message = message.strip()
            client = self.clients.getByGUID(playerId)
            if client:
                if client.team == team:
                    event = self.getEvent('EVT_CLIENT_TEAM_SAY', message, client)
                else:
                    event = self.getEvent('EVT_CLIENT_SAY', message, client)
                self.queueEvent(event)

        elif packet.msgType == MessageType.PLAYER_CONNECT:
            playerId = packet.getGUID()
            name = packet.getString()
            client = self.clients.getByGUID(playerId)
            if not client:
                client = self.clients.newClient(name, guid=playerId, name=name, team=b3.TEAM_UNKNOWN)
                self.queueEvent(self.getEvent('EVT_CLIENT_JOIN', None, client))

        elif packet.msgType == MessageType.PLAYER_DISCONNECT:
            playerId = packet.getGUID()
            client = self.clients.getByGUID(playerId)
            if client:
                client.disconnect()

        elif packet.msgType == MessageType.MAP_CHANGED:
            self._currentMapIndex = packet.getInt()
            currentMap = packet.getString()
            self.game.mapName = currentMap
            event = self.getEvent('EVT_GAME_ROUND_START', currentMap)
            self.queueEvent(event)

        elif packet.msgType == MessageType.MAP_LIST:
            mapName = packet.getString().split('?', 1)[0]
            if self._mapList is None:
                self._mapList = []
            self._mapList.append(mapName)

        elif packet.msgType == MessageType.TEAM_CHANGED:
            playerId = packet.getGUID()
            team = packet.getInt()
            client = self.clients.getByGUID(playerId)
            if client:
                # TODO: map to B3 team ids TEAM_BLUE, TEAM_RED, etc
                client.team = team

        elif packet.msgType == MessageType.NAME_CHANGED:
            playerId = packet.getGUID()
            name = packet.getString()
            client = self.clients.getByGUID(playerId)
            if client:
                client.name = name            

        elif packet.msgType == MessageType.KILL:
            attackerId = packet.getGUID()
            victimId = packet.getGUID()
            weapon = packet.getString()
            attacker = self.clients.getByGUID(attackerId)
            victim = self.clients.getByGUID(victimId)
            eventkey = 'EVT_CLIENT_KILL'
            hitloc = 'body'

            if not attacker:
                self.debug("Attacker not found: %s, packet: %r" % (attackerId, packet))
                return

            if not victim:
                self.debug("Victim not found: %s, packet: %r" % (victimId, packet))
                return

            if attacker.team != b3.TEAM_UNKNOWN and attacker.team == victim.team:
                eventkey = 'EVT_CLIENT_KILL_TEAM'
                
            if attacker and victim:
                event = self.getEvent(eventkey, (100, weapon, hitloc), attacker, victim)
                self.queueEvent(event)            

        elif packet.msgType == MessageType.SUICIDE:
            victimId = packet.getGUID()
            victim = self.clients.getByGUID(victimId)
            if victim:
                weapon = None
                hitloc = None
                event = self.getEvent('EVT_CLIENT_SUICIDE', (100, weapon, hitloc), victim, victim)    
                self.queueEvent(event)

        elif packet.msgType == MessageType.ROUND_END:
            winningTeam = packet.getInt()
            event = self.getEvent('EVT_GAME_ROUND_END', winningTeam)
            self.queueEvent(event)

        elif packet.msgType == MessageType.PING:
            playerId = packet.getGUID()
            ping = packet.getInt()
            client = self.clients.getByGUID(playerId)
            if client:
                client.ping = ping
        else:
            self.warning("unkown RCON message type: %s. REPORT THIS TO THE B3 FORUMS. %r" % (packet.msgType, packet))

    ####################################################################################################################
    #                                                                                                                  #
    #   OTHER METHODS                                                                                                  #
    #                                                                                                                  #
    ####################################################################################################################

    def sendPacket(self, packet):
        if self._client and self._client.isAuthed:
            self._client.sendPacket(packet)

    ####################################################################################################################
    #                                                                                                                  #
    #   B3 PARSER INTERFACE IMPLEMENTATION                                                                             #
    #                                                                                                                  #
    ####################################################################################################################

    def getPlayerList(self):
        """
        Query the game server for connected players.
        return a dict having players' id for keys and players' data as another dict for values
        """
        # TODO find a way to query the server for the player list
        clients = self.clients.getList()
        return clients

    def authorizeClients(self):
        """
        For all connected players, fill the client object with properties allowing to find 
        the user in the database (usualy guid, or punkbuster id, ip) and call the 
        Client.auth() method 
        """
        pass  # No need as every rcon packet about a player gives the guid
    
    def sync(self):
        """
        For all connected players returned by self.getPlayerList(), get the matching Client
        object from self.clients (with self.clients.getByCID(cid) or similar methods) and
        look for inconsistencies. If required call the client.disconnect() method to remove
        a client from self.clients.
        """
        pass
    
    def say(self, msg, *args):
        """
        Broadcast a message to all players.
        :param msg: The message to be broadcasted
        """
        msg = self.stripColors(msg % args)
        packet = Packet()
        packet.msgType = MessageType.SAY_ALL
        packet.addString(msg)
        self.sendPacket(packet)

    def saybig(self, msg, *args):
        """
        Broadcast a message to all players in a way that will catch their attention.
        :param msg: The message to be broadcasted
        """
        msg = self.stripColors(msg % args)
        packet = Packet()
        packet.msgType = MessageType.SAY_ALL_BIG
        packet.addString(msg)
        self.sendPacket(packet)

    def message(self, client, text, *args):
        """
        Display a message to a given client
        :param client: The client to who send the message
        :param text: The message to be sent
        """
        text = self.stripColors(text % args)
        packet = Packet()
        packet.msgType = MessageType.SAY
        packet.addGUID(client.guid)
        packet.addString(text)
        self.sendPacket(packet)
        
    def kick(self, client, reason='', admin=None, silent=False, *kwargs):
        """
        Kick a given client.
        :param client: The client to kick
        :param reason: The reason for this kick
        :param admin: The admin who performed the kick
        :param silent: Whether or not to announce this kick
        """
        reason = self.stripColors(reason)
        packet = Packet()
        packet.msgType = MessageType.KICK_PLAYER
        packet.addGUID(client.guid)
        packet.addString(reason)
        self.sendPacket(packet)
        self.queueEvent(self.getEvent(self.getEventID('EVT_CLIENT_KICK'), {'reason': reason, 'admin': admin}, client))
        
    def ban(self, client, reason='', admin=None, silent=False, *kwargs):
        """
        Ban a given client.
        :param client: The client to ban
        :param reason: The reason for this ban
        :param admin: The admin who performed the ban
        :param silent: Whether or not to announce this ban
        """
        reason = self.stripColors(reason)
        packet = Packet()
        packet.msgType = MessageType.BAN_PLAYER
        packet.addGUID(client.guid)
        packet.addString(reason)
        self.sendPacket(packet)
        self.queueEvent(self.getEvent('EVT_CLIENT_BAN', {'reason': reason, 'admin': admin}, client))

    def unban(self, client, reason='', admin=None, silent=False, *kwargs):
        """
        Unban a client.
        :param client: The client to unban
        :param reason: The reason for the unban
        :param admin: The admin who unbanned this client
        :param silent: Whether or not to announce this unban
        """
        reason = self.stripColors(reason)
        packet = Packet()
        packet.msgType = MessageType.UNBAN_PLAYER
        packet.addGUID(client.guid)
        self.sendPacket(packet)
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
        reason = self.stripColors(reason)
        packet = Packet()
        packet.msgType = MessageType.TEMP_BAN_PLAYER
        packet.addGUID(client.guid)
        packet.addString(reason)
        packet.addInt(duration * 60)
        self.sendPacket(packet)
        
        banid = client.guid
        if banid is None:
            banid = client.cid
            self.debug('using name to ban : %s' % banid)
            # saving banid in the name column in database
            # so we can unban a unconnected player using name
            # TODO See if another location than the name column could be better suited for storing the banid
            client._name = banid
            client.save()
        
        self.queueEvent(self.getEvent('EVT_CLIENT_BAN_TEMP', {'reason': reason,
                                                              'duration': duration,
                                                              'admin': admin}, client))

    def getMap(self):
        """
        Return the current map/level name
        """
        # TODO handle the case where self._currentMap is not set. Can we query the game server ?
        return self.game.mapName

    def getNextMap(self):
        """
        Return the next map/level name to be played.
        """
        numMaps = len(self._mapList)
        currentmap = self.getMap()
        if self._currentMapIndex is not None:
            if self._currentMapIndex < numMaps-1:
                nextmap = self._mapList[self._currentMapIndex+1]
            else:
                nextmap = self._mapList[0]
        elif self._mapList.count(currentmap) == 1:
            i = self._mapList.index(currentmap)
            if i < numMaps-1:
                nextmap = self._mapList[i+1]
            else:
                nextmap = self._mapList[0]
        else:
            nextmap = "Unknown"
        
        return nextmap

    def getMaps(self):
        """
        Return the available maps/levels name.
        """
        # TODO handle the case where self._mapList is not set. Can we query the game server ?
        return self._mapList

    def rotateMap(self):
        """
        Load the next map/level.
        """
        packet = Packet()
        packet.msgType = MessageType.ROTATE_MAP
        self.sendPacket(packet)
        
    def changeMap(self, map_name):
        """
        Load a given map/level
        Return a list of suggested map names in cases it fails to recognize the map that was provided.
        """
        packet = Packet()
        packet.msgType = MessageType.CHANGE_MAP
        packet.addString(map_name)
        self.sendPacket(packet)

    def getPlayerPings(self, filter_client_ids=None):
        """
        Returns a dict having players' id for keys and players' ping for values.
        """
        pings = {}
        clients = self.clients.getList()
        for c in clients:
            try:
                pings[c.name] = int(c.ping)
            except AttributeError:
                pass
        return pings

    def getPlayerScores(self):
        """
        Returns a dict having players' id for keys and players' scores for values.
        """
        scores = {}
        clients = self.clients.getList()
        for c in clients:
            try:
                scores[c.name] = int(c.kills)
            except AttributeError:
                pass
        return scores

    ####################################################################################################################
    #                                                                                                                  #
    #   APPLY PATCHES                                                                                                  #
    #                                                                                                                  #
    ####################################################################################################################

    @staticmethod
    def patch_admin_plugin_doList():
        """
        Patch the admin plugin doList method enforcing a custom player_id pattern.
        Unreal Engine 3 doesn't support the player slot number as RCON command parameter, so it's useless displaying it
        (is uses the client GUID instead which can be retrieved also using the player database id).
        Check: http://forum.bigbrotherbot.net/general-discussion/!list-command/
        """
        def doList(self, client, cmd):
            names = []
            for c in self.console.clients.getClientsByLevel():
                names.append('^7%s [^2@%s^7]' % (c.name, c.id))
            cmd.sayLoudOrPM(client, ', '.join(names))
            return True

        AdminPlugin.doList = doList

    @staticmethod
    def patch_admin_plugin_cmd_find():
        """
        Patch the admin plugin !find command displaying the client database id instead of the slot number.
        """
        def cmd_find(self, data, client=None, cmd=None):
            m = self.parseUserCmd(data)
            if not m:
                client.message(self.getMessage('invalid_parameters'))
                return

            cid = m[0]
            sclient = self.findClientPrompt(cid, client)
            if sclient:
                cmd.sayLoudOrPM(client, '^7Found player matching %s [^2@%s^7] %s' % (cid, sclient.id, sclient.exactName))

        AdminPlugin.cmd_find = cmd_find

class Packet(object):

    def __init__(self):
        self.raw_packet = None
        self.msgType = None
        self.data = ""
        self.dataLength = 0
        self.playerId = None
        self.message = None

    def encode(self):
        s = ""
        s += pack('>H', self.msgType)
        s += pack('>i', len(self.data))
        s += self.data
        return s
        
    def addGUID(self, playerId):
        self.data += pack('>Q', long(playerId))
    
    def addString(self, s):
        encodedData = s.encode('utf-8')
        self.data += pack('>i', len(encodedData))
        self.data += encodedData

    def addInt(self, num):
        self.data += pack('>i', num)

    def getGUID(self):
        playerId = unpack('>Q', self.data[0:8])[0]
        playerId = str(playerId)
        self.data = self.data[8:]
        return playerId
    
    def getInt(self):
        num = unpack('>i', self.data[0:4])[0]
        self.data = self.data[4:]
        return num
    
    def getString(self):
        length = self.getInt()
        data = self.data[0:length]
        self.data = self.data[length:]
        return data.decode('utf-8')

    def __repr__(self):
        if self.raw_packet is not None:
            return "Packet.decode(%r)  # {'msgType': %r, 'dataLength': %r, 'data': %r}" % (self.raw_packet,
                                                                                           self.msgType,
                                                                                           self.dataLength,
                                                                                           self.data)
        return "Packet(%r)" % self.__dict__
    
    @staticmethod
    def getHeaderSize():
        return 6
        
    @staticmethod
    def getPacketSize(packet):
        return unpack('>i', packet[2:6])[0] + Packet.getHeaderSize()

    @staticmethod
    def decode(raw_packet):
        p = Packet()
        p.msgType = unpack('>H', raw_packet[0:2])[0]
        p.dataLength = unpack('>i', raw_packet[2:6])[0]
        p.data = raw_packet[6:6+p.dataLength]
        p.raw_packet = raw_packet[0:6+p.dataLength]
        return p

class Client(asyncore.dispatcher_with_send):

    def __init__(self, console, host, port, password, packetListener):
        asyncore.dispatcher_with_send.__init__(self)
        self.console = console
        self._host = host
        self._port = port
        self._password = password
        self._packetListener = packetListener
        self.isAuthed = False
        self.keepalive = True
        self.readBuffer = ""
        self.console.info("Starting RCON for game server %s:%s" % (host, port))
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((self._host, self._port))

    def handle_connect(self):
        self.isAuthed = False
        self.console.info("RCON connection established")

    def send_password(self, challenge):
        self.console.info("RCON authenticating...")
        password = self._password
        password += challenge
        sha1_pass_bytes = sha1(password).hexdigest().upper()
        packet = Packet()
        packet.msgType = MessageType.PASSWORD
        packet.addString(sha1_pass_bytes)
        self.sendPacket(packet)

    def handle_close(self):
        self.close()
        self.isAuthed = False
        self.readBuffer = ""
        if self.keepalive:
            self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connect((self._host, self._port))

    def handle_read(self):
        self.readBuffer += self.recv(8192)
        while len(self.readBuffer) >= Packet.getHeaderSize():
            packetSize = Packet.getPacketSize(self.readBuffer)
            if len(self.readBuffer) >= packetSize:
                packet = Packet.decode(self.readBuffer)
                if packet.msgType != MessageType.PING:
                    self.console.verbose2("RCON> %r" % packet)
                try:
                    self._packetListener(packet)
                except Exception as e:
                    self.error("Failed to handle game server %r" % packet, exc_info=e)
                self.readBuffer = self.readBuffer[packetSize:]
       
    def sendPacket(self, packet):
        try:
            self.console.verbose2("RCON< %r" % packet)
            self.send(packet.encode())
        except socket.error, e:
            self.console.error(repr(e))