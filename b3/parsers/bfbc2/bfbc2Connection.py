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
# 2010/03/09 - 0.5 - Courgette
# * open a TCP connection to a BFBC2 server, auth with provided password
# * can either be used to send commands or enter the listening mode (which
#   waits for BFBC2 events)
# 2010/03/14 - 0.6 - Courgette
# * raise a Bfbc2NetworkException whenever something goes wrong on the 
#   network while using sendRequest()
# 2010/03/16 - 0.7 - Courgette
# * Bfbc2CommandFailedError now also contains the BFBC2 response
# 2010/03/19 - 0.8 - Courgette
# * fix bug listening to event when we have an incomplete packet
# 2010/03/23 - 0.9 - Courgette
# * bugfix: when start listening and only a partial packet is available
# 2010/03/25 - 0.10 - Courgette
# * updated to use latest protocol.py
# * sendRequest and readBfbc2Event now detect a lost connection and reconnect in such cases
# 2010/03/25 - 0.10.1 - Courgette
# * Exception message more explicit
# * fix the socket time out message when listening to events
#

__author__  = 'Courgette'
__version__ = '0.10.1'

debug = True

import time
import socket
from b3.parsers.bfbc2.protocol import *
 
    

class Bfbc2Exception(Exception): pass
class Bfbc2NetworkException(Bfbc2Exception): pass
class Bfbc2BadPasswordException(Bfbc2Exception): pass

class Bfbc2CommandFailedError(Exception): pass

class Bfbc2Connection(object):
    
    _serverSocket = None
    _receiveBuffer = None
    _host = None
    _port = None
    _password = None

    def __init__(self, host, port, password):
        self._host = host
        self._port = port
        self._password = password
        
        try:
            self._connect()
            self._auth()
        except socket.error, detail:
            raise Bfbc2NetworkException('Cannot create Bfbc2Connection: %s'% detail)
   
    def __del__(self):
        self.close()
   
    def _connect(self):
        try:
            self._receiveBuffer = ''
            self._serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._serverSocket.connect( ( self._host, self._port ) )
        except Exception, err:
            raise Bfbc2Exception(err)
    
    def close(self):
        if self._serverSocket is not None:
            try:
                self.sendRequest('quit')
            except: pass
            self._serverSocket.close()
            self._serverSocket = None

    def sendRequest(self, *command):
        if command is None:
            return None
        if self._serverSocket is None:
            print "reconnecting..."
            self._connect()
            self._auth()
            
        if len(command) == 1 and type(command[0]) == tuple:
            words = command[0]
        else:
            words = command
        request = EncodeClientRequest(words)
        printPacket(DecodePacket(request))
        try:
            self._serverSocket.sendall(request)
            [response, self._receiveBuffer] = receivePacket(self._serverSocket, self._receiveBuffer)
        except socket.error, detail:
            raise Bfbc2NetworkException(detail)
        
        if response is None:
            return None
        decodedResponse = DecodePacket(response)
        printPacket(decodedResponse)
        #[isFromServer, isResponse, sequence, words] = decodedResponse
        return decodedResponse[3]
        
    def _auth(self):
        if self._serverSocket is None:
            raise Bfbc2Connection("cannot auth, need to be connected")
            
        # Retrieve this connection's 'salt' (magic value used when encoding password) from server
        words = self.sendRequest("login.hashed")

        # if the server doesn't understand "login.hashed" command, abort
        if words[0] != "OK":
            raise Bfbc2Exception("Could not retrieve salt")

        # Given the salt and the password, combine them and compute hash value
        salt = words[1].decode("hex")
        passwordHash = generatePasswordHash(salt, self._password)
        passwordHashHexString = string.upper(passwordHash.encode("hex"))

        # Send password hash to server
        loginResponse = self.sendRequest("login.hashed", passwordHashHexString)

        # if the server didn't like our password, abort
        if loginResponse[0] != "OK":
            raise Bfbc2BadPasswordException("The BFBC2 server refused our password")

            
    def subscribeToBfbc2Events(self):
        """
        tell the bfbc2 server to send us events
        """
        self._serverSocket.setblocking(1)
        response = self.sendRequest("eventsEnabled", "true")

        # if the server didn't know about the command, abort
        if response[0] != "OK":
            raise Bfbc2CommandFailedError(response)

        
    def readBfbc2Event(self):
        # Wait for packet from server
        try:
            if self._serverSocket is None:
                print "reconnecting..."
                self._connect()
                self._auth()
                self.subscribeToBfbc2Events()
            [packet, self._receiveBuffer] = receivePacket(self._serverSocket, self._receiveBuffer)
        except socket.error, detail:
            raise Bfbc2NetworkException('readBfbc2Event: %r'% detail)
        try:
            [isFromServer, isResponse, sequence, words] = DecodePacket(packet)
            printPacket(DecodePacket(packet))
        except:
            raise Bfbc2Exception('failed to decodePacket {%s}' % packet)
        
        # If this was a command from the server, we should respond to it
        # For now, we always respond with an "OK"
        if isResponse:
            print 'Received an unexpected response packet from server, ignoring: %r' % packet
            return self.handle_bfbc2_events()
        else:
            response = EncodePacket(True, True, sequence, ["OK"])
            printPacket(DecodePacket(response))
            self._serverSocket.sendall(response)
            return words
            

        


###################################################################################
# Display contents of packet in user-friendly format, useful for debugging purposes
def printPacket(packet):
    if debug:
        erf = sys.__stderr__
        isFromServer = packet[0]
        isResponse = packet[1]
        if isFromServer and isResponse:
            print>>erf, "<-R-",
        elif isFromServer and not isResponse:
            print>>erf, "-Q->",
        elif not isFromServer and isResponse:
            print>>erf, "-R->",
        elif not isFromServer and not isResponse:
            print>>erf, "<-Q-",
    
        print>>erf, "(%s)" %  packet[2],
    
        if packet[3]:
            print>>erf, " :",
            for word in packet[3]:
                print>>erf, "\"" + word + "\"",
    
        print>>erf, ""
    
###################################################################################
# Example program

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) != 4:
        host = raw_input('Enter game server host IP/name: ')
        port = int(raw_input('Enter host port: '))
        pw = raw_input('Enter password: ')
    else:
        host = sys.argv[1]
        port = int(sys.argv[2])
        pw = sys.argv[3]
        
    bc2server = Bfbc2Connection(host, port, pw)
    print "connected"
    
    reponse = bc2server.sendRequest(('version',))
    print reponse[1]
    
    reponse = bc2server.sendRequest(('help',))
    for command in reponse[1:]:
        print '\t' + command
    
    bc2server.close()
    print "closed"
    
    
    