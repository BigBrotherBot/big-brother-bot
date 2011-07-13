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
#
import asyncore
import md5
import re
import socket
import time
"""
module implementing the Frontline protocol. Provide the Client class which
creates a connection to a Frontline gameserver
"""

__author__  = 'Courgette'
__version__ = '1.1'

RE_CHALLENGE = re.compile(r'WELCOME! Frontlines: Fuel of War \(RCON\) VER=\d+ CHALLENGE=(?P<challenge>.+)')
CMD_TERMINATOR = '\x04'

class FrontlineConnectionError(Exception): pass

class Client(asyncore.dispatcher_with_send):

    def __init__(self, console, host, port, username, password, keepalive=False):
        asyncore.dispatcher_with_send.__init__(self)
        self.console = console
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self.keepalive = keepalive
        self._buffer_in = ''
        self.authed = False
        self._handlers = set()
        self._auth_failures = 0
        self.lastResponseTime = None
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect( (self._host, self._port) )
        
    def handle_connect(self):
        self.console.info('Now connected to Frontline gameserver, waiting for challenge')
        self.authed = False

    def handle_close(self):
        self.console.info('Connection to Frontline gameserver closed')
        self._auth_failures += 1
        self.close()
        self.authed = False
        if self.keepalive:
            if self._auth_failures > 500:
                self.console.error("Too many failures. Could not connect to Frontline server")
                self.keepalive = False
            else:
                self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
                self.connect((self._host, self._port))

    def handle_read(self):
        data = self.recv(1024)
        if len(data):
            #self.console.verbose2('read %s char from Frontline gameserver %r' % (len(data), data))
            self._buffer_in += data
            p = self._readPacket()
            while p is not None:
                for handler_func in self._handlers:
                    try:
                        handler_func(p)
                    except Exception, err:
                        self.console.exception(err)
                p = self._readPacket()

    def add_listener(self, handler_func):
        self._handlers.add(handler_func)
        return self
    
    def remove_listener(self, handler_func):
        try:
            self._handlers.remove(handler_func)
        except:
            raise ValueError("Handler is not handling this event, so cannot unhandle it.")
        return self            
            
    def login(self, challenge):
        """authenticate to the server
        from Frontline documentation : 
        
            Open a TCP/IP streaming socket to the remote console port of the server
            
            All commands sent and received are separated with new line characters '\n' or 0x04
            
            The server will send back a string (without the quotes):
            "WELCOME! Frontlines: Fuel of War (RCON) VER=2 CHALLENGE=38D384D07C"
            
            Note: Challenge string length is not fixed and will vary
            
            To generate a response use the MD5 algorithm to hash an ansi string:
            ResponseString = MD5Hash( ChallengeStringFromServer + Password );
            
            The client will send this string to the server to login:
            "RESPONSE UserNameHere ResponseString"
            
            If the login was successful the client will receive:
            "Login Success!"
            
            If the login failed, the client will be disconnected immediately
            
            Once the client is logged in commands can be sent to be run and responses can come back

        """
        self.console.info("Logging to Frontline server with username %r" % self._username)
        hashed_password = md5.new("%s%s" % (challenge, self._password)).hexdigest()
        try:
            self.send('RESPONSE %s %s' % (self._username, hashed_password))
        except socket.error, e:
            self.console.error(repr(e))

    def ping(self):
        """used to keep the connection alive. After 10 seconds of inactivity
        the server will drop the connection"""
        self.command("ECHONET PING")
    
    def command(self, text):
        """send command to server"""
        if not self.connected:
            return
        if not self.authed:
            self.console.warning("not authenticated, cannot send command")
            return
        #self.console.verbose("sending RCON %s" % text)
        packet = "%s%s" % (text.strip(), CMD_TERMINATOR)
        try:
            self.send(packet)
        except socket.error, e:
            self.console.error(repr(e))
        
    def _readPacket(self):
        if CMD_TERMINATOR in self._buffer_in:
            p = self._buffer_in.split(CMD_TERMINATOR, 1)[0]
            self._buffer_in = self._buffer_in[len(p)+1:]
            self._inspect_packet(p)
            return p

    def _inspect_packet(self, p):
        self.lastResponseTime = time.time()
        if not self.authed:
            if p.startswith('Login SUCCESS!'):
                self.authed = True
                self._auth_failures = 0
                return
            match = RE_CHALLENGE.match(p)
            if match:
                self.login(match.group('challenge'))
            
            
            
###################################################################################
# Example program

if __name__ == '__main__':
    import sys, logging
    from b3.output import OutputHandler
    
#    if len(sys.argv) != 5:
#        host = raw_input('Enter game server host IP/name: ')
#        port = int(raw_input('Enter host port: '))
#        user = raw_input('Enter username: ')
#        pw = raw_input('Enter password: ')
#    else:
#        host = sys.argv[1]
#        port = int(sys.argv[2])
#        user = sys.argv[3]
#        pw = sys.argv[4]
   
    host = '127.0.0.1'
    port = 14507
    user = 'admin'
    pw = 'pass'
    
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(levelname)s\t%(message)s")
    handler.setFormatter(formatter)
    
    myConsole = OutputHandler('console')
    myConsole.addHandler(handler)
    myConsole.setLevel(8)
    
    
    def packetListener(packet):
        myConsole.console(">>> %s" % packet)    
    
    myConsole.info('start client')
    frontlineClient = Client(myConsole, host, port, user, pw, keepalive=True)
    frontlineClient.add_listener(packetListener)
    
    try:
        while frontlineClient.connected or not frontlineClient.authed:
            frontlineClient.command("PLAYERLIST")
            asyncore.loop(timeout=3, count=1)
    except EOFError, KeyboardInterrupt:
        frontlineClient.close()
    
    myConsole.info('end')
    
    
