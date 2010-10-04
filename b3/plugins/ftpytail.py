#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
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
# 04/10/2010 - 1.5.3 - Courgette
#   * stop thread on FTP permanent error
#   * can activate FTP debug messages with _ftplib_debug_level
#   * display exact error message whenever the ftp connection fails
# 04/09/2010 - 1.5.2 - GrosBedo
#   * b3/delay option now specify the delay between each ftp log fetching
#   * b3/local_game_log option to specify the temporary local log name (permits to manage remotely several servers at once)
# 02/09/2010 - 1.5.1 - Courgette
#    * fix bug in 1.5. Dectect FTP permanent error and give up in such cases
# 02/09/2010 - 1.5 - Courgette
#    * allow to connect on non standard FTP port
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
 
__version__ = '1.5.3'
__author__ = 'Bakes, Courgette'
 
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
    
    _working = True
    _ftplib_debug_level = 0 # 0: no debug, 1: normal debug, 2: extended debug
    
    _ftpdelay = 0.150
    
    def onStartup(self):
        versionsearch = re.search("^((?P<mainversion>[0-9]).(?P<lowerversion>[0-9]+)?)", sys.version)
        version = int(versionsearch.group(3))
        if version < 6:
            self.error('Python Version %s, this is not supported and may lead to hangs. Please update Python to 2.6' % versionsearch.group(1))
            self.console.die()

        if self.console.config.has_option('server', 'delay'):
            self._ftpdelay = self.console.config.getfloat('server', 'delay')
        
        if self.console.config.has_option('server', 'local_game_log'):
            self.lgame_log = self.console.config.getfloat('server', 'local_game_log')
        else:
            self.lgame_log = os.path.normpath(os.path.expanduser('games_mp.log'))

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
        self._working = True
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
        self.file = open(self.lgame_log, 'ab')
        while self.console.working and self._working:
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

            except ftplib.error_perm, e:
                self.critical('FTP permanent error : ' + str(e))
                self.exception(e)
                self._working = False
                continue
            except ftplib.error_temp, e:
                self.debug(str(e))
                self._nbConsecutiveConnFailure += 1
                if self.console._paused is False:
                    self.console.pause()
                self.file.close()
                self.file = open(self.lgame_log, 'w')
                self.file.close()
                self.file = open(self.lgame_log, 'ab')
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
            except ftplib.all_errors, e:
                self.debug(str(e))
                self._nbConsecutiveConnFailure += 1
                if self.console._paused is False:
                    self.console.pause()
                self.file.close()
                self.file = open(self.lgame_log, 'w')
                self.file.close()
                self.file = open(self.lgame_log, 'ab')
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
            time.sleep(self._ftpdelay)
        self.verbose("stopping Ftpytail update thread")
        try:
            ftp.close()
        except:
            pass
        try:
            self.file.close()
        except:
            pass
    
    def ftpconnect(self):
        #self.debug('Python Version %s.%s, so setting timeout of 10 seconds' % (versionsearch.group(2), versionsearch.group(3)))
        self.verbose('Connecting to %s:%s ...' % (self.ftpconfig["host"], self.ftpconfig["port"]))
        try:
            ftp = FTP()
            ftp.set_debuglevel(self._ftplib_debug_level)
            ftp.connect(self.ftpconfig['host'], self.ftpconfig['port'], self._connectionTimeout)
            ftp.login(self.ftpconfig['user'], self.ftpconfig['password'])
            ftp.voidcmd('TYPE I')
            dir = os.path.dirname(self.ftpconfig['path'])
            self.debug('trying to cwd to [%s]' % dir)
            ftp.cwd(dir)
            self.console.clients.sync()
        except ftplib.error_perm, err:
            self.exception(err)
            self.error('Permanent error while trying to connect to FTP server. %s' %err)
        except ftplib.error_temp, err:
            self.exception(err)
            self.error('Temporary error while trying to connect to FTP server. %s' %err)
        except Exception, err:
            self.error('ftp connection has failed. %s' % err)
            self.exception(err)
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
    p.onStartup()

    #p.initThread('ftp://www.somewhere.tld/somepath/somefile.log')
    p.initThread('ftp://thomas@127.0.0.1/DRIVERS/test.txt')
    time.sleep(90)
    fakeConsole.shutdown()
    time.sleep(8)