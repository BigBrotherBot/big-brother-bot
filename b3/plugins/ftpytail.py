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
# 06/02/2010 - 1.4 - Courgette
#    * force FTP binary mode
# 13/12/2009 - 1.3 - Courgette
#    * default timeout is 30 secondes (as I had a user reporting the FTP server he uses 
#      lags 15 sec before accepting connections).
#    * Can optionnaly read a config file to customize timeout and max allowed gap between
#      remote and local gamelog
#    * add a test to validate config reading
# 12/12/2009 - 1.2 - Courgette
#     does not download huge amount of log in case local file is too far behind remote file (prevents memory errors)
#     In case of connection failure, try to reconnect every second for the first 30 seconds
# 12/12/2009 - 1.1.1 - Courgette
#     Gracefully stop thread when B3 is shutting down
#     Add tests
# 28/08/2009 - 1.1 - Bakes
#     Connects with parser.py to provide real remote b3.
# 17/06/2009 - 1.0 - Bakes
#     Initial Plugin, basic functionality.
 
__version__ = '1.4'
__author__ = 'Bakes'
 
import b3, threading
from b3 import functions
import b3.events
import b3.plugin
import os.path
from ftplib import FTP
import ftplib
import time
import re
import sys
#--------------------------------------------------------------------------------------------------
class FtpytailPlugin(b3.plugin.Plugin):
    ### settings
    _maxGap = 20480 # max gap in bytes between remote file and local file
    _waitBeforeReconnect = 15 # time (in sec) to wait before reconnecting after loosing FTP connection : 
    _connectionTimeout = 30
    
    requiresConfigFile = False
    ftpconfig = None
    buffer = None
    _remoteFileOffset = None
    _nbConsecutiveConnFailure = 0
    
    def onStartup(self):
        if self.console.config.get('server','game_log')[0:6] == 'ftp://' :
            self.initThread(self.console.config.get('server','game_log'))
    
    def onLoadConfig(self):
        try:
            self._connectionTimeout = self.config.getint('settings', 'timeout')
        except: 
            self.warning("Error reading timeout from config file. Using default value")
        self.info("FTP connection timeout: %s" % self._connectionTimeout)

        try:
            self._maxGap = self.config.getint('settings', 'maxGapBytes')
        except: 
            self.warning("Error reading maxGapBytes from config file. Using default value")
        self.info("Maximum gap allowed between remote and local gamelog: %s bytes" % self._maxGap)
    
    def initThread(self, ftpfileDSN):
        self.ftpconfig = functions.splitDSN(ftpfileDSN)
        thread1 = threading.Thread(target=self.update)
        self.info("Starting ftpytail thread")
        thread1.start()
    
    def update(self):
        def handleDownload(block):
            #self.debug('received %s bytes' % len(block))
            self._remoteFileOffset += len(block)
            if self.buffer == None:
                self.buffer = block
            else:
                self.buffer = self.buffer + block
        ftp = None
        self.file = open('games_mp.log', 'ab')
        while self.console.working:
            try:
                if not ftp:
                    ftp = self.ftpconnect()
                    self._nbConsecutiveConnFailure = 0
                    remoteSize = ftp.size(os.path.basename(self.ftpconfig['path']))
                    self.verbose("Connection successful. Remote file size is %s" % remoteSize)
                    if self._remoteFileOffset is None:
                        self._remoteFileOffset = remoteSize
                remoteSize = ftp.size(os.path.basename(self.ftpconfig['path']))
                if remoteSize < self._remoteFileOffset:
                    self.debug("remote file rotation detected")
                    self._remoteFileOffset = 0
                if remoteSize > self._remoteFileOffset:
                    if  (remoteSize - self._remoteFileOffset) > self._maxGap:
                        self.debug('gap between local and remote file too large (%s bytes)', (remoteSize - self._remoteFileOffset))
                        self.debug('downloading only the last %s bytes' % self._maxGap)
                        self._remoteFileOffset = remoteSize - self._maxGap
                    #self.debug('RETR from remote offset %s. (expecting to read at least %s bytes)' % (self._remoteFileOffset, remoteSize - self._remoteFileOffset))
                    ftp.retrbinary('RETR ' + os.path.basename(self.ftpconfig['path']), handleDownload, rest=self._remoteFileOffset)          
                    if self.buffer:
                        self.file.write(self.buffer)
                        self.buffer = None
                        self.file.flush()
                    if self.console._paused:
                        self.console.unpause()
                        self.debug('Unpausing')
            except ftplib.all_errors, e:
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
                    ftp.close()
                    self.debug('FTP Connection Closed')
                except:
                    pass
                ftp = None
                
                if self._nbConsecutiveConnFailure <= 30:
                    time.sleep(1)
                else:
                    self.debug('too many failures, sleeping %s sec' % self._waitBeforeReconnect)
                    time.sleep(self._waitBeforeReconnect)
            time.sleep(0.150)
        self.verbose("B3 is down, stopping Ftpytail thread")
        try:
            ftp.close()
        except:
            pass
        try:
            self.file.close()
        except:
            pass
    
    def ftpconnect(self):
        versionsearch = re.search("^((?P<mainversion>[0-9]).(?P<lowerversion>[0-9]+)?)", sys.version)
        version = int(versionsearch.group(3))
        if version < 6:
            self.debug('Python Version %s.%s, this is not supported and may lead to hangs. Please update Python to 2.6 if you want B3 to autorestart properly.' % (versionsearch.group(2), versionsearch.group(3)))
            self.console.die('Python version is not new enough for FTPyTail, this will almost certainly lead to bot hangs. Please update your Python.')
        else:
            #self.debug('Python Version %s.%s, so setting timeout of 10 seconds' % (versionsearch.group(2), versionsearch.group(3)))
            self.verbose('Connecting to %s ...', self.ftpconfig["host"])
            ftp=FTP(self.ftpconfig['host'],self.ftpconfig['user'],passwd=self.ftpconfig['password'],timeout=self._connectionTimeout)
            ftp.voidcmd('TYPE I')
        try:
            ftp.cwd(os.path.dirname(self.ftpconfig['path']))
        except:
            self.error('Cannot CWD to the correct directory, ftp connection has failed')
        self.console.clients.sync()
        return ftp
    
    
if __name__ == '__main__':
    from b3.fake import fakeConsole
    
    print "------------------------------------"
    config = b3.config.XmlConfigParser()
    config.setXml("""
    <configuration plugin="ftpytail">
        <settings name="settings">
            <set name="timeout">15</set>
            <set name="maxGapBytes">1024</set>
        </settings>
    </configuration>
    """)
    p = FtpytailPlugin(fakeConsole, config)

    
    print "------------------------------------"
    p = FtpytailPlugin(fakeConsole)

    p.initThread('ftp://www.somewhere.tld/somepath/somefile.log')
    time.sleep(30)
    fakeConsole.shutdown()
    time.sleep(8)