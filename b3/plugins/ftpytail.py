#
# BigBrotherBot(B3) (www.bigbrotherbot.com)
# Copyright (C) 2009 James "Bakes" Baker
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
# 28/08/2009 - 1.1 - Bakes
# Connects with parser.py to provide real remote b3.
# 17/06/2009 - 1.0 - Bakes
# Initial Plugin, basic functionality.
 
__version__ = '1.1'
__author__ = 'Bakes'
 
import b3, threading, time, re
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
  requiresConfigFile = False
  ftpconfig = None
  tempfile = None
  
  def onStartup(self):
    if self.console.config.get('server','game_log')[0:6] == 'ftp://' :
        gamelog = self.console.config.get('server', 'game_log')
        self.ftpconfig = functions.splitDSN(gamelog)
        thread1 = threading.Thread( target=self.update)
        thread1.start()

  def update(self):
    def handleDownload(block):
        if self.tempfile == None:
            self.tempfile = block
        else:
            self.tempfile = self.tempfile + block
    ftp = None
    self.file = open('games_mp.log', 'ab')
    while True:
        try:
            if not ftp:
                self.debug('FTP connection not active, attempting to (re)connect')
                ftp = self.ftpconnect()
                self.debug('FTP = %s' % str(ftp))
            size=os.path.getsize('games_mp.log')
            ftp.retrbinary('RETR ' + os.path.basename(self.ftpconfig['path']), handleDownload, rest=size)          
            if self.tempfile:
                self.file.write(self.tempfile)
                self.tempfile = None
                self.file.flush()
            if self.console._paused:
                self.console.unpause()
                self.debug('Unpausing')
        except ftplib.all_errors, e:
            self.debug(str(e))
            self.debug('Lost connection to server, pausing until updated properly, Sleeping 10 seconds')
            self.console.pause()
            self.file.close()
            self.file = open('games_mp.log', 'w')
            self.file.close()
            self.file = open('games_mp.log', 'ab')
            self.debug('Lost Connection, redownloading entire logfile')
            try:
                ftp.close()
                self.debug('FTP Connection Closed')
            except:
                self.debug('FTP does not appear to be open, so not closed')
            ftp = None
            time.sleep(10)

  def ftpconnect(self):
    versionsearch = re.search("^((?P<mainversion>[0-9]).(?P<lowerversion>[0-9]+)?)", sys.version)
    version = int(versionsearch.group(3))
    if version < 6:
        self.debug('Python Version %s.%s, this is not supported and may lead to hangs. Please update Python to 2.6 if you want B3 to autorestart properly.' % (versionsearch.group(2), versionsearch.group(3)))
        self.console.die('Python version is not new enough for FTPyTail, this will almost certainly lead to bot hangs. Please update your Python.')
    else:
        self.debug('Python Version %s.%s, so setting timeout of 10 seconds' % (versionsearch.group(2), versionsearch.group(3)))
        ftp=FTP(self.ftpconfig['host'],self.ftpconfig['user'],passwd=self.ftpconfig['password'],timeout=10)
    try:
        ftp.cwd(os.path.dirname(self.ftpconfig['path']))
    except:
        self.error('Cannot CWD to the correct directory, ftp connection has failed')
    self.console.clients.sync()
    return ftp