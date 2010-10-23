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
# Changelog :
# 2010/03/09 - 0.1 - Courgette
# * alpha, need test server to validate
# 2010/03/09 - 0.2 - courgette
# * tested, seems to work for most cases
# 2010/03/14 - 0.3 - Courgette
# * write() can retry in case of failure
# 2010/03/27 - 0.3.1 - Courgette
# * fix maxRetries limitation 
# * make this class thread safe
# 2010/04/03 - 0.3.2 - courgette
# * fix import FrostbiteException
# 2010/04/11 - 1.0 Courgette
# * just make it v1.0 as it is now part of a public release and works rather good
# 2010/04/15 - 1.0.1 Bakes
# * If the response of the rcon command does not start with 'OK', trigger FrostbiteCommandFailedError
# 2010/07/29 - 1.0.2 xlr8or
# * The response may also be "NotFound" ie. when a guid or ip address is not found in the banslist.
# * Added needConfirmation var to write() so we can use the confirmationtype ("OK", "NotFound") to test on.
# 2010/10/23 - 2.0 - Courgette
# * refactor BFBC2 -> frostbite

 
__author__ = 'Courgette'
__version__ = '2.0'
 
import thread
from b3.parsers.frostbite.connection import FrostbiteConnection, FrostbiteException, FrostbiteCommandFailedError

#--------------------------------------------------------------------------------------------------
class Rcon:
    _lock = thread.allocate_lock()
    console = None
    _frostbiteConnection = None
    
    _rconIp = None
    _rconPort = None
    _rconPassword = None
    

    def __init__(self, console, host, password):
        self.console = console
        self._rconIp, self._rconPort = host
        self._rconPassword = password
        
    def _connect(self):
        if self._frostbiteConnection:
            return
        self.console.verbose('RCON: Connecting to Frostbite server ...')
        self._frostbiteConnection = FrostbiteConnection(self.console, self._rconIp, self._rconPort, self._rconPassword)

    def writelines(self, lines):
        for line in lines:
            self.write(line)

    def write(self, cmd, maxRetries=1, needConfirmation=False):
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
        self.console.info('RCON: disconnecting from BFBC2 server')
        self._frostbiteConnection.close()

            
            
if __name__ == '__main__':
    """
    To run tests : python b3/parsers/bfbc2/rcon.py <rcon_ip> <rcon_port> <rcon_password>
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
    
    import b3.parsers.frostbite.connection as fbConnection
    fbConnection.debug = True


    r = Rcon(fakeConsole, (host, port), pw)   
    r.write(('admin.yell', 'test', 1400, 'player', 'Courgette'))  
    
    
    for cmd in ['version', 'serverInfo', 'help', 'version', 'admin.currentLevel', ('admin.listPlayers', 'all')]:
        fakeConsole.info('Writing %s', cmd)
        data = r.write(cmd)
        fakeConsole.info('Recieved %s', data)
    
    print '----------------------------'
    
    varlist = (
        '3dSpotting',
        'bannerUrl',
        'crossHair',
        'currentPlayerLimit',
        'friendlyFire',
        'gamePassword',
        'hardCore',
        'killCam',
        'maxPlayerLimit',
        'miniMap',
        'miniMapSpotting',
        'playerLimit',
        'punkBuster',
        'rankLimit',
        'ranked',
        'serverDescription',
        'teamBalance',
        'thirdPersonVehicleCameras'
    )
    #for var in varlist:
        #time.sleep(0.5)
        #print r.write('vars.%s' % var)[0]
        
    print '----------------------------'
        
    for c in r.write(('help',)):
        print c
#    import time
#    for var in varlist:
#        time.sleep(0.5)
#        val = r.write('vars.%s' % var)[0]
#        print "------------original %s value : '%s' -------------" % (var, val)
#    
#        if val == 'true':
#            newval = 'false'
#        elif val == 'false':
#            newval = 'true'
#        else:
#            try:
#                int(val)
#                newval = 2
#            except ValueError:
#                newval = 'test qsdf'
#        
#        print "\t > changing to '%s'" % newval
#        time.sleep(0.5)
#        r.write(('vars.%s' % var, newval))
#        
#        time.sleep(0.5)
#        val2 = r.write('vars.%s' % var)[0]
#        print "\t\tnow : '%s'" % val2
#        
#        print "\t > changing back to '%s'" % val
#        time.sleep(0.5)
#        r.write(('vars.%s' % var, val))
#        
#        time.sleep(0.5)
#        val3 = r.write('vars.%s' % var)[0]
#        print "\t\tnow : '%s'" % val3
#        
#        time.sleep(0.5)
#        if val == val2 or val != val3:
#            print "\t FAILED !!!!"
#        else:
#            print "\t PASS"
        