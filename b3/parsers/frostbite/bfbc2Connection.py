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
# 2010/03/30 - 0.11 - Courgette
# * use console to print messages
# * when listening to event, do not set the socket into blocking mode. This should
#   make the bot recover from a connection loss
# 2010/04/11 - 1.0 - Courgette
# * fix a bug which occurred in the rare case we receive from the server a packet from another sequence
# * make this version 1.0 as it seems to be stable enough now
# 2010/04/18 - 1.1 - Courgette
# * harden readBfbc2Event in cases where a network error occurs while replying OK to an event (Thanks to Merph's report)
# 2010/04/18 - 1.2 - Courgette
# * try to make sure readBfbc2Event does not hang on a dead connection
# 2010/04/20 - 1.2.1 - Courgette
# * harden 1.2
# 2010/10/11 - 1.2.2 - xlr8or
# * Output to log changed: BFBC2 -> Frostbite (cosmetic only!)
#

__author__  = 'Courgette'
__version__ = '1.2.2'

debug = True

import socket
import b3.parsers.frostbite.protocol as protocol
 
    

class Bfbc2Exception(Exception): pass
class Bfbc2NetworkException(Bfbc2Exception): pass
class Bfbc2BadPasswordException(Bfbc2Exception): pass

class Bfbc2CommandFailedError(Exception): pass

class Bfbc2Connection(object):
    
    console = None
    _serverSocket = None
    _receiveBuffer = None
    _host = None
    _port = None
    _password = None

    def __init__(self, console, host, port, password):
        self.console = console
        self._host = host
        self._port = port
        self._password = password
        
        try:
            self._connect()
            self._auth()
        except socket.error, detail:
            raise Bfbc2NetworkException('Cannot create FrostbiteConnection: %s'% detail)
   
    def __del__(self):
        self.close()
   
    def _connect(self):
        try:
            self.console.debug('opening FrostbiteConnection socket')
            self._receiveBuffer = ''
            self._serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._serverSocket.connect( ( self._host, self._port ) )
        except Exception, err:
            raise Bfbc2Exception(err)
    
    def close(self):
        if self._serverSocket is not None:
            self.console.debug('closing FrostbiteConnection socket')
            try:
                self.sendRequest('quit')
            except: pass
            self._serverSocket.close()
            self._serverSocket = None

    def sendRequest(self, *command):
        if command is None:
            return None
        if self._serverSocket is None:
            self.console.info("sendRequest: reconnecting...")
            self._connect()
            self._auth()
            
        if len(command) == 1 and type(command[0]) == tuple:
            words = command[0]
        else:
            words = command
        request = protocol.EncodeClientRequest(words)
        self.printPacket(protocol.DecodePacket(request))
        try:
            self._serverSocket.sendall(request)
            [response, self._receiveBuffer] = protocol.receivePacket(self._serverSocket, self._receiveBuffer)
        except socket.error, detail:
            raise Bfbc2NetworkException(detail)
        
        if response is None:
            return None
        decodedResponse = protocol.DecodePacket(response)
        self.printPacket(decodedResponse)
        #[isFromServer, isResponse, sequence, words] = decodedResponse
        return decodedResponse[3]
        
    def _auth(self):
        self.console.debug('authing to Frostbite server')
        if self._serverSocket is None:
            raise Bfbc2Connection("cannot auth, need to be connected")
            
        # Retrieve this connection's 'salt' (magic value used when encoding password) from server
        words = self.sendRequest("login.hashed")

        # if the server doesn't understand "login.hashed" command, abort
        if words[0] != "OK":
            raise Bfbc2Exception("Could not retrieve salt")

        # Given the salt and the password, combine them and compute hash value
        salt = words[1].decode("hex")
        passwordHash = protocol.generatePasswordHash(salt, self._password)
        passwordHashHexString = protocol.string.upper(passwordHash.encode("hex"))

        # Send password hash to server
        loginResponse = self.sendRequest("login.hashed", passwordHashHexString)

        # if the server didn't like our password, abort
        if loginResponse[0] != "OK":
            raise Bfbc2BadPasswordException("The Frostbite server refused our password")

            
    def subscribeToBfbc2Events(self):
        """
        tell the bfbc2 server to send us events
        """
        self.console.debug('subscribing to Frostbite events')
        response = self.sendRequest("eventsEnabled", "true")

        # if the server didn't know about the command, abort
        if response[0] != "OK":
            raise Bfbc2CommandFailedError(response)

        
    def readBfbc2Event(self):
        # Wait for event from server
        packet = None
        timeout_counter = 0
        while packet is None:
            try:
                if self._serverSocket is None:
                    self.console.info("readBfbc2Event: reconnecting...")
                    self._connect()
                    self._auth()
                    self.subscribeToBfbc2Events()
                [tmppacket, self._receiveBuffer] = protocol.receivePacket(self._serverSocket, self._receiveBuffer)
                [isFromServer, isResponse, sequence, words] = protocol.DecodePacket(tmppacket)
                if isFromServer and not isResponse:
                    packet = tmppacket
                else:
                    self.console.verbose2('received a packet which is not an event: %s' % [isFromServer, isResponse, sequence, words,])
            except socket.timeout:
                timeout_counter += 1
                self.console.verbose2('timeout %s' % timeout_counter)
                if timeout_counter >= 5:
                    self.console.verbose2('checking connection...')
                    request = protocol.EncodeClientRequest(['eventsEnabled','true'])
                    self.printPacket(protocol.DecodePacket(request))
                    self._serverSocket.sendall(request)
                    timeout_counter = 0
            except socket.error, detail:
                raise Bfbc2NetworkException('readBfbc2Event: %r'% detail)

        try:
            [isFromServer, isResponse, sequence, words] = protocol.DecodePacket(packet)
            self.printPacket(protocol.DecodePacket(packet))
        except:
            raise Bfbc2Exception('readBfbc2Event: failed to decodePacket {%s}' % packet)
        
        # If this was a command from the server, we should respond to it
        # For now, we always respond with an "OK"
        if isResponse:
            self.console.debug('Received an unexpected response packet from server, ignoring: %r' % packet)
            return self.readBfbc2Event()
        else:
            response = protocol.EncodePacket(True, True, sequence, ["OK"])
            self.printPacket(protocol.DecodePacket(response))
            
            try:
                self._serverSocket.sendall(response)
            except socket.error, detail:
                self.console.warning("in readBfbc2Event while sending response OK to server : %s" % detail)
                
            return words
            
    def printPacket(self, packet):
        """Display contents of packet in user-friendly format, useful for debugging purposes"""
        if debug:
            isFromServer = packet[0]
            isResponse = packet[1]
            msg = ""
            if isFromServer and isResponse:
                msg += "<-R-"
            elif isFromServer and not isResponse:
                msg += "-Q->"
            elif not isFromServer and isResponse:
                msg += "-R->"
            elif not isFromServer and not isResponse:
                msg += "<-Q-"
        
            msg += " (%s)" %  packet[2]
        
            if packet[3]:
                msg += " :"
                for word in packet[3]:
                    msg += " \"" + word + "\""
        
            self.console.verbose2(msg)
        

        

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
    
    class MyConsole:
        def debug(self, msg):
            print "   DEBUG: " + msg
        def info(self, msg):
            print "    INFO: " + msg
        def verbose2(self, msg):
            print "VERBOSE2: " + msg
        def warning(self, msg):
            print "WARNING : " + msg
    myConsole = MyConsole()
    
    bc2server = Bfbc2Connection(myConsole, host, port, pw)
    print "connected"
    
    reponse = bc2server.sendRequest(('version',))
    print reponse[1]
    
    reponse = bc2server.sendRequest(('help',))
    for command in reponse[1:]:
        print '\t' + command
    
    bc2server.close()
    print "closed"
    
    bc2server.readBfbc2Event()
    
    
    
