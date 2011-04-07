# -*- coding: cp1252 -*-
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
#
# CHANGELOG
#
# 2011/03/23 - Courgette 
#    working so far : packet codec, login(), ping()
#    todo : handle incoming data (split by homefront packet)
# 2011/03/24 - 0.2 - Courgette 
#    can maintain a connection, receive packets, send packets
# 2011/03/31 - 0.3 - Courgette
#    do not crash when send() raises a socket.error
#

"""
module implementing the Homefront protocol. Provide the Client class which
creates a connection to a Homefront gameserver
"""

__author__  = 'Courgette'
__version__ = '0.3'


import asyncore, socket, time
from struct import pack, unpack
from hashlib import sha1



class MessageType:
    CONNECT = 'CC'
    CLIENT_TRANSMISSION = 'CT'
    CLIENT_DISCONNECT = 'CD'
    CLIENT_PING = 'CP'
    SERVER_ANNOUNCE = 'SA'
    SERVER_RESPONSE = 'SR'
    SERVER_DISCONNECT = 'SD'
    SERVER_TRANSMISSION = 'ST'
    
    @staticmethod
    def type2str(type):
        names = {
                 MessageType.CONNECT: "CONNECT",
                 MessageType.CLIENT_TRANSMISSION: "CLIENT_TRANSMISSION",
                 MessageType.CLIENT_DISCONNECT: "CLIENT_DISCONNECT",
                 MessageType.CLIENT_PING: "CLIENT_PING",
                 MessageType.SERVER_ANNOUNCE: "SERVER_ANNOUNCE",
                 MessageType.SERVER_RESPONSE: "SERVER_RESPONSE",
                 MessageType.SERVER_DISCONNECT: "SERVER_DISCONNECT",
                 MessageType.SERVER_TRANSMISSION: "SERVER_TRANSMISSION",
                 }
        try:
            return names[type]
        except KeyError:
            return "unkown(%s)" % type

class ChannelType:
    BROADCAST = 0
    NORMAL = 1
    CHATTER = 2
    GAMEPLAY = 3
    SERVER = 4
    
    @staticmethod
    def type2str(type):
        names = {
                 ChannelType.BROADCAST: "BROADCAST",
                 ChannelType.NORMAL: "NORMAL",
                 ChannelType.CHATTER: "CHATTER",
                 ChannelType.GAMEPLAY: "GAMEPLAY",
                 ChannelType.SERVER: "SERVER",
                 }
        try:
            return names[type]
        except KeyError:
            return "unkown(%s)" % type



class Packet(object):
    message = None
    channel = None
    data = None
    
    def encode(self):
        ## Message Type
        ## type: 8-bit char[]
        ## byte length : 2
        str = self.message[0:2]
        ## Data length
        ## type: 32-bit signed int (big-endian)
        ## byte 4
        str += pack('>i', len(self.data))
        ## Data
        ## type: 8-bit char[N]
        ## byte length : N
        str += self.data.encode('utf-8')
        return str
    
    def decode(self, packet):
        if len(packet) <= 7:
            raise ValueError, "too few data to extract a packet"
        
        ## Message Type
        ## type: 8-bit char[]
        ## byte length : 2
        self.message = packet[0:2]
        ## Message Type
        ## type: 8-bit byte
        ## byte length : 1
        (self.channel,) = unpack('>B', packet[2])
        ## Data length
        ## type: 32-bit signed int (big-endian)
        ## byte 4
        datalength = Packet.decodeIncomingPacketSize(packet)
        ## Data
        ## type: 8-bit char[N]
        ## byte length : N
        str = packet[7:7+datalength]
        self.data = str.decode('utf-8')
        
    @staticmethod
    def decodeIncomingPacketSize(packet):
        ## Data length
        ## type: 32-bit signed int (big-endian)
        ## byte 4
        return unpack('>i', packet[3:7])[0]
    
    def getMessageTypeAsStr(self):
        return MessageType.type2str(self.message)
    
    def getChannelTypeAsStr(self):
        return ChannelType.type2str(self.channel)
    
    def __str__(self):
        return "[Message: %s], [Channel: %s], [Data: %s]" % (self.getMessageTypeAsStr(), self.getChannelTypeAsStr(), self.data)



class Client(asyncore.dispatcher_with_send):

    def __init__(self, console, host, port, password, keepalive=False):
        asyncore.dispatcher_with_send.__init__(self)
        self.console = console
        self._host = host
        self._port = port
        self._password = password
        self.keepalive = keepalive
        self._buffer_in = ''
        self.authed = False
        self.server_version = None
        self.last_pong_time = self.last_ping_time = time.time()
        self._handlers = set()
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect( (self._host, self._port) )
        
    def handle_connect(self):
        self.console.verbose('Now connected to Homefront gameserver')
        self.login()
        self.ping()
        pass

    def handle_close(self):
        self.console.verbose('Connection to Homefront gameserver closed')
        self.close()
        self.authed = False
        if self.keepalive:
            self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connect((self._host, self._port))

    def handle_read(self):
        data = self.recv(8192)
        self.console.verbose2('read %s char from Homefront gameserver' % len(data))
        self._buffer_in += data
        p = self._readPacket()
        while p is not None:
            for handler in self._handlers:
                try:
                    handler(p)
                except Exception, err:
                    self.console.exception(err)
            p = self._readPacket()

    def add_listener(self, handler):
        self._handlers.add(handler)
        return self
    
    def remove_listener(self, handler):
        try:
            self._handlers.remove(handler)
        except:
            raise ValueError("Handler is not handling this event, so cannot unhandle it.")
        return self            
            
    def login(self):
        """authenticate to the server
        
        Message Type: ClientTransmission
        Format : PASS: "[string: SHA1Hash]"
        SHA1Hash: A 60 byte ASCII string with a 40-bit SHA1 Hash converted to 
            uppercase hexadecimal text and spaces inserted between each pair.
        """
        def twobytwo(str):
            i = 0
            while i < len(str):
                yield str[i:i+2]
                i+=2
        sha1_pass_bytes = sha1(self._password).hexdigest()
        self.command('PASS: "%s"' % ' '.join(twobytwo(sha1_pass_bytes.upper())))

    def ping(self):
        """used to keep the connection alive. After 10 seconds of inactivity
        the server will drop the connection"""
        packet = Packet()
        packet.message = MessageType.CLIENT_PING
        packet.data = "PING"
        try:
            self.send(packet.encode())
            self.last_ping_time = time.time()
        except socket.error, e:
            self.console.error(repr(e))
    
    def command(self, text):
        """send command to server"""
        packet = Packet()
        packet.message = MessageType.CLIENT_TRANSMISSION
        packet.data = text
        try:
            self.send(packet.encode())
        except socket.error, e:
            self.console.error(repr(e))
        
    def _readPacket(self):
        if len(self._buffer_in) > 7:
            packetlength = Packet.decodeIncomingPacketSize(self._buffer_in)
            if len(self._buffer_in) >= 7 + packetlength:
                p = Packet()
                p.decode(self._buffer_in)
                self._buffer_in = self._buffer_in[7 + packetlength:]
                self._inspect_packet(p)
                return p

    def _inspect_packet(self, p):
        if p.data == "PONG":
            self.last_pong_time = time.time()
        elif p.channel == ChannelType.SERVER and p.data == "AUTH: true":
            self.authed = True
        elif p.channel == ChannelType.SERVER and p.data.startswith("HELLO: "):
            self.server_version = p.data[7:]
            
            
            
###################################################################################
# Example program

if __name__ == '__main__':
    import sys, logging
    from b3.output import OutputHandler
    
    if len(sys.argv) != 4:
        host = raw_input('Enter game server host IP/name: ')
        port = int(raw_input('Enter host port: '))
        pw = raw_input('Enter password: ')
    else:
        host = sys.argv[1]
        port = int(sys.argv[2])
        pw = sys.argv[3]
    
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(levelname)s\t%(message)s")
    handler.setFormatter(formatter)
    
    myConsole = OutputHandler('console')
    myConsole.addHandler(handler)
    myConsole.setLevel(logging.NOTSET)
    
    
    def packetListener(packet):
        myConsole.console(">>> %s" % packet)    
    
    myConsole.info('start client')
    hfclient = Client(myConsole, host, port, pw, keepalive=True)
    hfclient.add_listener(packetListener)
    
    try:
        while hfclient.connected or not hfclient.authed:
            #print("\t%s" % (time.time() - hfclient.last_pong_time))
            if time.time() - hfclient.last_pong_time > 6 and hfclient.last_ping_time < hfclient.last_pong_time:
                hfclient.ping()
                hfclient.command("RETRIEVE PLAYERLIST")
            asyncore.loop(timeout=3, count=1)
    except EOFError, KeyboardInterrupt:
        hfclient.close()
    
    myConsole.info('end')
    
    
