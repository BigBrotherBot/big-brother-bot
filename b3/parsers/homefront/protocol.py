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
#

__author__  = 'Courgette'
__version__ = '0.1'

"""module implementing the Homefront protocol"""


from struct import *
from hashlib import sha1
import socket

import sys
import string
import threading
import os

        
class Connection(object):
    host = None
    port = None
    password = None

    _socket = None
    _buffer = None
    
    def connect(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print('Connecting to : %s:%d...' % ( self.host, self.port ))
        self._socket.connect((self.host, self.port))
    
    def command(self, text):
        """send command to server"""
        self._send(MessageType.CLIENT_TRANSMISSION, text)
    
    def ping(self):
        """used to keep the connection alive. After 10 seconds of inactivity
        the server will drop the connection"""
        self._send(MessageType.CLIENT_PING, "PING")
    
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
        sha1_pass_bytes = sha1(self.password).hexdigest()
        self.command('PASS: "%s"' % ' '.join(twobytwo(sha1_pass_bytes.upper())))
    
    def shutdown(self):
        self._socket.close()
        del self._socket
    
    def _send(self, messagetype, text):
        packet = Packet()
        packet.message = messagetype
        packet.data = text
        bytes = packet.encode()
        self._socket.send(bytes)
        
    def recv(self):
        """TODO : this is temporary, just for debugging"""
        self._buffer = self._socket.recv(1024)
        return self._buffer

       

class MessageType:
    UNKNOWN = 0
    CONNECT = 'CC'
    CLIENT_TRANSMISSION = 'CT'
    CLIENT_DISCONNECT = 'CD'
    CLIENT_PING = 'CP'
    SERVER_ANNOUNCE = 'SA'
    SERVER_RESPONSE = 'ST'
    SERVER_DISCONNECT = 'SD'
    SERVER_TRANSMISSION = 'SR'
    
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
        str += self.data
        return str
    
    def decode(self, packet):
        ## Message Type
        ## type: 8-bit char[]
        ## byte length : 2
        self.message = packet[0:2]
        ## Message Type
        ## type: 8-bit byte
        ## byte length : 1
        (self.channel,) = unpack('>B', packet[2])
        ## Data
        ## type: 8-bit char[N]
        ## byte length : N
        datalength = unpack('>i', packet[3:7])[0]
        self.data = packet[7:7+datalength]
        
    def __str__(self):
        return "[Message: %s], [Channel: %s], [Data: %s]" % (self.message, ChannelType.type2str(self.channel), self.data)


if __name__ == '__main__':
    from getopt import getopt
    import sys, time

    print "Remote administration event listener for Homefront"

    host = None
    port = None
    pw = None

    opts, args = getopt(sys.argv[1:], 'h:p:e:a:')
    for k, v in opts:
        if k == '-h':
            host = v
        elif k == '-p':
            port = int(v)
        elif k == '-a':
            pw = v
    
    if not host:
        host = raw_input('game server host IP/name: ')
    if not port:
        port = int(raw_input('port: '))
    if not pw:
        pw = raw_input('password: ')

    try:
        conn = Connection()
        conn.host = host
        conn.port = port
        conn.password = pw

        conn.connect()
        p = Packet()
        p.decode(conn.recv())
        print p
        
        conn.login()
        p = Packet()
        p.decode(conn.recv())
        print p
        
        time.sleep(2)
        conn.ping()
        p = Packet()
        p.decode(conn.recv())
        print p
        
        time.sleep(2)
        conn.shutdown()
        
    except socket.error, detail:
        print 'Network error:', detail[1]
        conn.shutdown()
    except EOFError, KeyboardInterrupt:
        conn.shutdown()
    except:
        raise
