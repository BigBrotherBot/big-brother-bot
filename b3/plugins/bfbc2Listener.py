#
# BigBrotherBot(B3) (www.bigbrotherbot.com)
# Copyright (C) 2009 James "Bakes" Baker
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
# CHANGELOG:

 
__version__ = '0.1'
__author__ = 'Courgette'
 
import b3, threading
from b3 import functions
import b3.events
import b3.plugin
import os.path
from b3.parsers.bfbc2.bfbc2Connection import *
import time
import re
import sys
import datetime

#--------------------------------------------------------------------------------------------------
class Bfbc2listenerPlugin(b3.plugin.Plugin):
    _bfbc2Connection = None
    buffer = None
    _nbConsecutiveConnFailure = 0

    ### settings
    requiresConfigFile = False
    _waitBeforeReconnect = 0.001 # time (in sec) to wait before reconnecting after loosing TCP connection : 
    _connectionTimeout = 30
    
    _rconhost = None
    _rconPort = 48888
    _rconPassword = None
    
    
    def onStartup(self):
        try:
            self._rconPort = self.console.config.getint('server', 'rcon_port')
        except: 
            self.warning("Error reading rcon_port from config file. Using default value")
        self.info("rcon_port: %s" % self._bfbc2CommandPort)
    
        self._rconhost = self.console._rconIp
        self._rconPassword = self.console._rconPassword
    
        self.initThread()
    
    def onLoadConfig(self):
        try:
            self._connectionTimeout = self.config.getint('settings', 'timeout')
        except: 
            self.warning("Error reading timeout from config file. Using default value")
        self.info("BFBC2 connection timeout: %s" % self._connectionTimeout)
    
    def initThread(self):
        thread1 = threading.Thread(target=self.update)
        self.info("Starting Bfbc2listener thread")
        thread1.start()
    
    def update(self):
        self._bfbc2Connection = None
        self.file = open('games_mp.log', 'ab')
        while self.console.working:
            try:
                if not self._bfbc2Connection:
                    self._bfbc2Connection = self.bfbc2Connect()
                    self._nbConsecutiveConnFailure = 0
                bfbc2packet = self._bfbc2Connection.waitForEvent()
                d = datetime.datetime.now()
                self.file.write("%s %s: %s\n" % (d.strftime("%Y%m%d-%H%M%S.%f"), bfbc2packet[0], bfbc2packet[1:]))
                self.file.flush()
                if self.console._paused:
                    self.console.unpause()
                    self.debug('Unpausing')
            except Bfbc2Exception, e:
                self.debug(str(e))
                self._nbConsecutiveConnFailure += 1
                self.verbose('Lost connection to server, pausing until updated properly')
                if self.console._paused is False:
                    self.console.pause()
                self.file.close()
                self.file = open('games_mp.log', 'w')
                self.file.close()
                self.file = open('games_mp.log', 'ab')
                try:
                    self._bfbc2Connection.close()
                    self.debug('BFBC2 Connection Closed')
                except:
                    pass
                self._bfbc2Connection = None
                
                if self._nbConsecutiveConnFailure <= 30:
                    time.sleep(1)
                else:
                    self.debug('too many failures, sleeping %s sec' % self._waitBeforeReconnect)
                    time.sleep(self._waitBeforeReconnect)
            time.sleep(0.005)
        self.verbose("B3 is down, stopping Bfbc2listener thread")
        try:
            self._bfbc2Connection.close()
        except:
            pass
        try:
            self.file.close()
        except:
            pass
    
    def bfbc2Connect(self):
        self.verbose('Connecting to BFBC2 server ...')
        self._bfbc2Connection = Bfbc2Connection(self._rconhost, self._rconPort, self._rconPassword)
        self._bfbc2Connection.subscribeToBfbc2Events()
        self.console.clients.sync()
        return self._bfbc2Connection
    
    
if __name__ == '__main__':
    from b3.fake import fakeConsole
    
    print "------------------------------------"
    config = b3.config.XmlConfigParser()
    config.setXml("""
    <configuration plugin="bfbc2listener">
        <settings name="settings">
            <set name="timeout">15</set>
        </settings>
    </configuration>
    """)
    p = Bfbc2listenerPlugin(fakeConsole, config)

    
    print "------------------------------------"
    p = Bfbc2listenerPlugin(fakeConsole)
    p._rconhost = 'xxx.xxx.xxx.xxx'
    p._rconPort = 48888
    p._rconPassword = 'xxxx'
    
    p.initThread()
    time.sleep(3600*5)
    fakeConsole.shutdown()
    time.sleep(8)