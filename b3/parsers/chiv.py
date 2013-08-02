# encoding: utf-8
#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2013
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
# 1.0 - first working version
# 1.1 - cosmetics and add a few TODO
#
import sys

from b3.parser import Parser
import asyncore
import socket
import b3
from struct import pack, unpack
from hashlib import sha1

__author__  = 'tliszak'
__version__ = '1.1'


class MessageType:
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
    
    ## parser code name to use in b3.xml
    gameName = 'chiv'
    
    _client = None
    _currentMap = None
    _currentMapIndex = None
    _mapList = None
    
    def run(self):
        """Main worker thread for B3"""
        self.screen.write('Startup Complete : B3 is running! Let\'s get to work!\n\n')
        self.screen.write('(If you run into problems, check %s for detailed log info)\n' % self.config.getpath('b3', 'logfile'))
        #self.screen.flush()

        self.updateDocumentation()

        while self.working:
            if self._paused:
                if self._pauseNotice == False:
                    self.bot('PAUSED - Not parsing any lines, B3 will be out of sync.')
                    self._pauseNotice = True
            else:
                if self._client is None:
                    self._client = Client(self, self._rconIp, self._rconPort, self._rconPassword, self.handlePacket)
                
                asyncore.loop(timeout=3, use_poll=True, count=1)

        with self.exiting:
            self._client.close()
            if self.exitcode:
                sys.exit(self.exitcode)
        
    def handlePacket(self, packet):
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
            self._currentMap = packet.getString()
            event = self.getEvent('EVT_GAME_ROUND_START', self._currentMap)
            self.queueEvent(event)
        elif packet.msgType == MessageType.MAP_LIST:
            mapName = packet.getString()
            if self._mapList is None:
                self._mapList = []
            self._mapList.append(mapName)
        elif packet.msgType == MessageType.TEAM_CHANGED:
            playerId = packet.getGUID()
            team = packet.getInt()
            client = self.clients.getByGUID(playerId)
            if client:
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
            eventName = 'EVT_CLIENT_KILL'
            hitloc = 'body'
            
            if attacker.team != b3.TEAM_UNKNOWN and attacker.team == victim.team:
                eventName = 'EVT_CLIENT_KILL_TEAM'
                
            if attacker and victim:
                event = self.getEvent(eventName, (100, weapon, hitloc), attacker, victim)    
                self.queueEvent(event)            
        elif packet.msgType == MessageType.SUICIDE:
            victimId = packet.getGUID()
            victim = self.clients.getByGUID(victimId)
            if victim:
                weapon = None
                hitloc = (0, 0, 0)
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

    def sendPacket(self, packet):
        if self._client and self._client.isAuthed:
            self._client.sendPacket(packet)

    def getPlayerList(self):
        """\
        Query the game server for connected players.
        return a dict having players' id for keys and players' data as another dict for values
        """
        clients = self.clients.getList()  # TODO find a way to query the server for the player list
        return clients

    def authorizeClients(self):
        """\
        For all connected players, fill the client object with properties allowing to find 
        the user in the database (usualy guid, or punkbuster id, ip) and call the 
        Client.auth() method 
        """
        pass  # No need as every rcon packet about a player gives the guid
    
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
        pass
    
    def say(self, msg):
        """\
        broadcast a message to all players
        """
        msg = self.stripColors(msg)
        
        packet = Packet()
        packet.msgType = MessageType.SAY_ALL
        packet.addString(msg)
        self.sendPacket(packet)

    def saybig(self, msg):
        """\
        broadcast a message to all players in a way that will catch their attention.
        """
        msg = self.stripColors(msg)

        packet = Packet()
        packet.msgType = MessageType.SAY_ALL_BIG
        packet.addString(msg)
        self.sendPacket(packet)

    def message(self, client, text):
        """\
        display a message to a given player
        """
        text = self.stripColors(text)

        packet = Packet()
        packet.msgType = MessageType.SAY
        packet.addGUID(client.guid)
        packet.addString(text)
        self.sendPacket(packet)
        
    def kick(self, client, reason='', admin=None, silent=False, *kwargs):
        """\
        kick a given player
        """
        reason = self.stripColors(reason)

        packet = Packet()
        packet.msgType = MessageType.KICK_PLAYER
        packet.addGUID(client.guid)
        packet.addString(reason)
        self.sendPacket(packet)

        self.queueEvent(self.getEvent('EVT_CLIENT_KICK', reason, client))
        
    def ban(self, client, reason='', admin=None, silent=False, *kwargs):
        """\
        ban a given player on the game server and in case of success
        fire the event ('EVT_CLIENT_BAN', data={'reason': reason, 
        'admin': admin}, client=target)
        """
        reason = self.stripColors(reason)

        packet = Packet()
        packet.msgType = MessageType.BAN_PLAYER
        packet.addGUID(client.guid)
        packet.addString(reason)
        self.sendPacket(packet)
        
        self.queueEvent(self.getEvent('EVT_CLIENT_BAN', {'reason': reason, 'admin': admin}, client))

    def unban(self, client, reason='', admin=None, silent=False, *kwargs):
        """\
        unban a given player on the game server
        """
        reason = self.stripColors(reason)

        packet = Packet()
        packet.msgType = MessageType.UNBAN_PLAYER
        packet.addGUID(client.guid)
        self.sendPacket(packet)
        
        self.queueEvent(self.getEvent('EVT_CLIENT_UNBAN', reason, client))

    def tempban(self, client, reason='', duration=2, admin=None, silent=False, *kwargs):
        """\
        tempban a given player on the game server and in case of success
        fire the event ('EVT_CLIENT_BAN_TEMP', data={'reason': reason, 
        'duration': duration, 'admin': admin}, client=target)
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
            client._name = banid  # TODO See if another location than the name column could be better suited for storing the banid
            client.save()
        
        self.queueEvent(self.getEvent('EVT_CLIENT_BAN_TEMP', {'reason': reason, 'duration': duration, 'admin': admin}, client))

    def getMap(self):
        """\
        return the current map/level name
        """
        return self._currentMap  # TODO handle the case where self._currentMap is not set. Can we query the game server ?

    def getNextMap(self):
        """\
        return the next map/level name to be played
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
        """\
        return the available maps/levels name
        """
        return self._mapList  # TODO handle the case where self._mapList is not set. Can we query the game server ?

    def rotateMap(self):
        """\
        load the next map/level
        """
        packet = Packet()
        packet.msgType = MessageType.ROTATE_MAP
        self.sendPacket(packet)
        
    def changeMap(self, map_name):
        """\
        load a given map/level
        return a list of suggested map names in cases it fails to recognize the map that was provided
        """
        packet = Packet()
        packet.msgType = MessageType.CHANGE_MAP
        packet.addString(map_name)
        self.sendPacket(packet)

    def getPlayerPings(self):
        """\
        returns a dict having players' id for keys and players' ping for values
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
        """\
        returns a dict having players' id for keys and players' scores for values
        """
        scores = {}
        clients = self.clients.getList()
        for c in clients:
            try:
                scores[c.name] = int(c.kills)
            except AttributeError:
                pass
        return scores

        
class Packet(object):
    msgType = None
    data = ""
    dataLength = 0
    playerId = None
    message = None
    
    def encode(self):
        str = ""
        str += pack('>H', self.msgType)
        str += pack('>i', len(self.data))
        str += self.data
        return str
        
    def addGUID(self, playerId):
        self.data += pack('>Q', long(playerId))
    
    def addString(self, str):
        encodedData = str.encode('utf-8')
        self.data += pack('>i', len(encodedData))
        self.data += encodedData

    def addInt(self, num):
        self.data += pack('>i', num)
        
    def decode(self, packet):
        self.msgType = unpack('>H', packet[0:2])[0]
        self.dataLength = unpack('>i', packet[2:6])[0]
        self.data = packet[6:6+self.dataLength]
        
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
    
    @staticmethod
    def getHeaderSize():
        return 6
        
    @staticmethod
    def getPacketSize(packet):
        return unpack('>i', packet[2:6])[0] + Packet.getHeaderSize()
    

class Client(asyncore.dispatcher_with_send):

    def __init__(self, console, host, port, password, packetListener):
        asyncore.dispatcher_with_send.__init__(self)
        self._host = host
        self._port = port
        self._password = password
        self._packetListener = packetListener
        self.isAuthed = False
        self.keepalive = True
        self.readBuffer = ""
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((self._host, self._port))

    def handle_connect(self):
        self.isAuthed = False

    def send_password(self, challenge):
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
                packet = Packet()
                packet.decode(self.readBuffer)
                self._packetListener(packet)
                self.readBuffer = self.readBuffer[packetSize:]
       
    def sendPacket(self, packet):
        try:
            self.send(packet.encode())
        except socket.error, e:
            self.console.error(repr(e))