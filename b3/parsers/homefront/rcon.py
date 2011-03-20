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

__author__  = 'xx'
__version__ = '0.0'

"""rcon module for Home Front. This module should focus on sending 
commands to a rcon server presenting a python file like API"""

import thread
from connection import HomefrontConnection, HomefrontConnectionException, HomefrontCommandFailedError

#--------------------------------------------------------------------------------------------------
class Rcon:
    _lock = thread.allocate_lock()
    console = None
    _conn = None
    
    _rconIp = None
    _rconPort = None
    _rconPassword = None
    

    def __init__(self, console, host, password):
        self.console = console
        self._rconIp, self._rconPort = host
        self._rconPassword = password
        
    def _connect(self):
        if self._conn:
            return
        self.console.verbose('RCON: Connecting to HomeFront server ...')
        self._conn = HomefrontConnection(self.console, self._rconIp, self._rconPort, self._rconPassword)

    def writelines(self, lines):
        for line in lines:
            self.write(line)

    def write(self, cmd, maxRetries=1, needConfirmation=False):
        self._lock.acquire()
        try:
            if self._conn is None:
                self._connect()
            tries = 0
            while tries < maxRetries:
                try:
                    tries += 1
                    self.console.verbose('RCON (%s/%s) %s' % (tries, maxRetries, cmd))
                    response = self._conn.sendRequest(cmd)
                    if response[0] != "OK" and response[0] != "NotFound":
                        raise FrostbiteCommandFailedError(response)
                    if needConfirmation:
                        return response[0]
                    else:
                        return response[1:]
                except HomefrontConnectionException, err:
                    self.console.warning('RCON: sending \'%s\', %s' % (cmd, err))
            self.console.error('RCON: failed to send \'%s\'', cmd)
            try:
                # we close the connection to make sure to have a brand new one 
                # on the next write
                self.close()
            except: pass
        finally:
            self._lock.release()

    def flush(self):
        pass

    def close(self):
        self.console.info('RCON: disconnecting from BFBC2 server')
        self._conn.close()

            
            
if __name__ == '__main__':
    """
    To run tests : 
    cd c:\whereever\is\b3
    c:\python26\python.exe b3/parsers/homefront/rcon.py <rcon_ip> <rcon_port> <rcon_password>
    """
    import sys
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
    r.write('command1')  
    
