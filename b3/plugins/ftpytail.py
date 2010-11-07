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
# 29/10/2010 - 1.5.5 - Courgette
#   * Do not stop thread on FTP permanent error (2nd trial)
#   * add 3 new settings in optional config file : short_delay, long_delay, 
#     max_consecutive_failures to tune how aggressive is B3 at retrying to 
#     connect.
#   * update config file example in test section at the bottom of this file
# 29/10/2010 - 1.5.4 - Courgette
#   * Do not stop thread on FTP permanent error
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
 
__version__ = '1.5.5'
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
    _maxConsecutiveConnFailure = 30 # after that amount of consecutive failure, pause the bot for _long_delay seconds
    _short_delay = 1 # time (in sec) to wait before reconnecting after loosing FTP connection (if _nbConsecutiveConnFailure < _maxConsecutiveConnFailure)
    _long_delay = 15 # time (in sec) to wait before reconnecting after loosing FTP connection (if _nbConsecutiveConnFailure > _maxConsecutiveConnFailure)
    _connectionTimeout = 30
    
    requiresConfigFile = False
    ftpconfig = None
    buffer = None
    _remoteFileOffset = None
    _nbConsecutiveConnFailure = 0
    
    
    _ftplib_debug_level = 0 # 0: no debug, 1: normal debug, 2: extended debug
    
    _gamelog_read_delay = 0.150
    
    def onStartup(self):
        versionsearch = re.search("^((?P<mainversion>[0-9]).(?P<lowerversion>[0-9]+)?)", sys.version)
        version = int(versionsearch.group(3))
        if version < 6:
            self.error('Python Version %s, this is not supported and may lead to hangs. Please update Python to 2.6' % versionsearch.group(1))
            self.console.die()

        if self.console.config.has_option('server', 'delay'):
            self._gamelog_read_delay = self.console.config.getfloat('server', 'delay')
        
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

        try:
            self._maxConsecutiveConnFailure = self.config.getint('settings', 'max_consecutive_failures')
        except: 
            self.warning("Error reading max_consecutive_failures from config file. Using default value")
        self.info("max_consecutive_failures: %s" % self._maxConsecutiveConnFailure)

        try:
            self._short_delay = self.config.getfloat('settings', 'short_delay')
        except: 
            self.warning("Error reading short_delay from config file. Using default value")
        self.info("short_delay: %s seconds" % self._short_delay)

        try:
            self._long_delay = self.config.getint('settings', 'long_delay')
        except: 
            self.warning("Error reading maxGapBytes from config file. Using default value")
        self.info("long_delay: %s seconds" % self._long_delay)

        self.info("until %s consecutive errors are met, the bot will wait for \
%s seconds (short_delay), then it will wait for %s seconds (long_delay)" 
            % (self._maxConsecutiveConnFailure, self._short_delay, self._long_delay))


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
        self.file = open(self.lgame_log, 'ab')
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
                
                if self._nbConsecutiveConnFailure <= self._maxConsecutiveConnFailure:
                    time.sleep(self._short_delay)
                else:
                    self.debug('too many failures, sleeping %s sec' % self._long_delay)
                    time.sleep(self._long_delay)
            time.sleep(self._gamelog_read_delay)
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
        ftp = FTP()
        ftp.set_debuglevel(self._ftplib_debug_level)
        ftp.connect(self.ftpconfig['host'], self.ftpconfig['port'], self._connectionTimeout)
        ftp.login(self.ftpconfig['user'], self.ftpconfig['password'])
        ftp.voidcmd('TYPE I')
        dir = os.path.dirname(self.ftpconfig['path'])
        self.debug('trying to cwd to [%s]' % dir)
        ftp.cwd(dir)
        self.console.clients.sync()
        return ftp
    
    
if __name__ == '__main__':
    from b3.fake import fakeConsole
    
    print "------------------------------------"
    config = b3.config.XmlConfigParser()
    config.setXml("""
    <configuration plugin="ftpytail">
        <settings name="settings">
            <!-- timeout to allow when connecting to FTP server -->
            <set name="timeout">5</set>
            <!-- how much bytes to read at most from game log file's tail (this is to avoid downloading megabytes) -->
            <set name="maxGapBytes">1024</set>
            <!-- The 3 settings below defines how aggressive will be B3 at 
            trying to reconnect after loosing the FTP connection.
            Before 'max_consecutive_failures' connections error, the bot will wait
            'short_delay' seconds before retrying. Then it will wait 'long_delay'. -->
            <set name="max_consecutive_failures">10</set>
            <set name="short_delay">2</set>
            <set name="long_delay">15</set>
        </settings>
    </configuration>
    """)
    p = FtpytailPlugin(fakeConsole, config)
    p.onStartup()

    #p.initThread('ftp://www.somewhere.tld/somepath/somefile.log')
    p.initThread('ftp://thomas@127.0.0.1/DRIVERS/test.txt')
    time.sleep(120)
    fakeConsole.shutdown()
    time.sleep(8)