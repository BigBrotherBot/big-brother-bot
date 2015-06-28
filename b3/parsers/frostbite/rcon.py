#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2010 Courgette <courgette@bigbrotherbot.net>
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
# 2010/03/09 - 0.1   - Courgette - alpha, need test server to validate
# 2010/03/09 - 0.2   - Courgette - tested, seems to work for most cases
# 2010/03/14 - 0.3   - Courgette - write() can retry in case of failure
# 2010/03/27 - 0.3.1 - Courgette - fix max_retries limitation
#                                - make this class thread safe
# 2010/04/03 - 0.3.2 - Courgette - fix import FrostbiteException
# 2010/04/11 - 1.0   - Courgette - just make it v1.0 as it is now part of a public release and works rather good
# 2010/04/15 - 1.0.1 - Bakes     - if the response of the rcon command does not start with 'OK', trigger
#                                  FrostbiteCommandFailedError
# 2010/07/29 - 1.0.2 - xlr8or    - the response may also be "NotFound" ie. when a guid or ip address is not found in
#                                  the banslist.
#                                - added need_confirmation var to write() so we can use the confirmationtype
#                                  ("OK", "NotFound") to test on.
# 2010/10/23 - 2.0   - Courgette - refactor BFBC2 -> frostbite
# 2014/08/05 - 2.1   - Fenix     - syntax cleanup
#                                - fixed some typos in debug messages
 
__author__ = 'Courgette'
__version__ = '2.1'
 
import thread

from b3.parsers.frostbite.connection import FrostbiteConnection
from b3.parsers.frostbite.connection import FrostbiteException
from b3.parsers.frostbite.connection import FrostbiteCommandFailedError

class Rcon(object):

    console = None

    _lock = thread.allocate_lock()
    _frostbiteConnection = None
    
    _rconIp = None
    _rconPort = None
    _rconPassword = None

    def __init__(self, console, host, password):
        """
        Object constructor.
        :param console: The console implementation
        :param host: The host where to send commands
        :param password: The RCON password
        """
        self.console = console
        self._rconIp, self._rconPort = host
        self._rconPassword = password
        
    def _connect(self):
        """
        Establish a connection with the Frostbite server.
        """
        if self._frostbiteConnection:
            return
        self.console.verbose('RCON: connecting to Frostbite server ...')
        self._frostbiteConnection = FrostbiteConnection(self.console, self._rconIp, self._rconPort, self._rconPassword)

    def writelines(self, lines):
        """
        Send multiple RCON commands to the server.
        """
        for line in lines:
            self.write(line)

    def write(self, cmd, maxRetries=1, needConfirmation=False):
        """
        Send an RCON command to the server.
        """
        self._lock.acquire()
        try:
            if self._frostbiteConnection is None:
                self._connect()
            tries = 0
            while tries < maxRetries:
                try:
                    tries += 1
                    self.console.verbose('RCON (%s/%s) %s' % (tries, maxRetries, cmd))
                    response = self._frostbiteConnection.sendRequest(cmd)
                    if response[0] != "OK" and response[0] != "NotFound":
                        raise FrostbiteCommandFailedError(response)
                    if needConfirmation:
                        return response[0]
                    else:
                        return response[1:]
                except FrostbiteException, err:
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
        """
        Close the connection with the Frostbite server.
        """
        self.console.info('RCON: disconnecting from Frostbite server')
        self._frostbiteConnection.close()
            
########################################################################################################################
# EXAMPLE PROGRAM                                                                                                      #
########################################################################################################################
#
# if __name__ == '__main__':
#     """
#     To run tests : python b3/parsers/bfbc2/rcon.py <rcon_ip> <rcon_port> <rcon_password>
#     """
#     import sys
#     if len(sys.argv) != 4:
#         host = raw_input('Enter game server host IP/name: ')
#         port = int(raw_input('Enter host port: '))
#         pw = raw_input('Enter password: ')
#     else:
#         host = sys.argv[1]
#         port = int(sys.argv[2])
#         pw = sys.argv[3]
#
#     from b3.fake import fakeconsole
#
#     import b3.parsers.frostbite.connection as fbConnection
#     fbConnection.debug = True
#
#
#     r = Rcon(fakeconsole, (host, port), pw)
#     r.write(('admin.yell', 'test', 1400, 'player', 'Courgette'))
#
#
#     for cmd in ['version', 'serverInfo', 'help', 'version', 'admin.currentLevel', ('admin.listPlayers', 'all')]:
#         fakeconsole.info('Writing %s', cmd)
#         data = r.write(cmd)
#         fakeconsole.info('Recieved %s', data)
#
#     print '----------------------------'
#
#     varlist = (
#         '3dSpotting',
#         'bannerUrl',
#         'crossHair',
#         'currentPlayerLimit',
#         'friendlyFire',
#         'gamePassword',
#         'hardCore',
#         'killCam',
#         'maxPlayerLimit',
#         'miniMap',
#         'miniMapSpotting',
#         'playerLimit',
#         'punkBuster',
#         'rankLimit',
#         'ranked',
#         'serverDescription',
#         'teamBalance',
#         'thirdPersonVehicleCameras'
#     )
#     #for var in varlist:
#         #time.sleep(0.5)
#         #print r.write('vars.%s' % var)[0]
#
#     print '----------------------------'
#
#     for c in r.write(('help',)):
#         print c