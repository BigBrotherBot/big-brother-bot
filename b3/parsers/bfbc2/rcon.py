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
# Changelog :
# 2010/03/09 - 0.1 - Courgette
# * alpha, need test server to validate
#
 
__author__ = 'Courgette'
__version__ = '0.1'
 
from b3.parsers.bfbc2.bfbc2Connection import *

#--------------------------------------------------------------------------------------------------
class Rcon:
    console = None
    _bfbc2Connection = None
    _socket_timeout = 60
    
    _rconIp = None
    _rconPort = None
    _rconPassword = None
    

    def __init__(self, console, host, password):
        self.console = console
        self._rconIp, self._rconPort = host
        self._rconPassword = password
        
    def __set_socket_timeout(self, value):
        if value is not None and value < 0:
            self._socket_timeout = 0
        else:
            self._socket_timeout = value
        if self._socket_timeout is not None:
            self._bfbc2Connection.timeout = self._socket_timeout

    def _connect(self):
        if self._bfbc2Connection:
            self._bfbc2Connection.close()
        self.console.verbose('RCON: Connecting to BFBC2 server ...')
        self._bfbc2Connection = Bfbc2Connection(self._rconIp, self._rconPort, self._rconPassword)
        self._bfbc2Connection.timeout = self._connectionTimeout
        self._bfbc2Connection.subscribeToBfbc2Events()

    def writelines(self, lines):
        for line in lines:
            self.write(line)

    def write(self, cmd):
        #if self._bfbc2Connection is None:
        #    self._connect()
        try:
            response = self._bfbc2Connection.sendRequest(cmd)
        except:
            try:
                self._connect()
                response = self._bfbc2Connection.sendRequest(cmd)
            except Bfbc2Exception, err:
                self.console.error('RCON: sending \'%s\', %s' % (cmd, err))
                return None
        if response[0] == 'OK':
            return response[1:]
        else:
            return None
        

    def flush(self):
        pass

    def close(self):
        pass

            
            
if __name__ == '__main__':
    """
    To run tests : python b3/parsers/bfbc2/rcon.py <rcon_ip> <rcon_port> <rcon_password>
    """
    if len(sys.argv) != 4:
        host = raw_input('Enter game server host IP/name: ')
        port = int(raw_input('Enter host port: '))
        pw = raw_input('Enter password: ')
    else:
        host = sys.argv[1]
        port = int(sys.argv[2])
        pw = sys.argv[3]
    
    from b3.fake import fakeConsole

    r = Rcon(fakeConsole, (host, port), pw)
    
    for cmd in ['version', 'serverInfo', 'quit', 'version', 'help', 'admin.currentLevel']:
        fakeConsole.info('Writing %s', cmd)
        data = r.write(cmd)
        fakeConsole.info('Recieved %s', data)

