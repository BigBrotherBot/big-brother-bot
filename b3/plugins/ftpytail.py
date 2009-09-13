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
 
__version__ = '1.0'
__author__ = 'Bakes'
 
import b3, threading, time, re
from b3 import functions
import b3.events
import b3.plugin
import os.path
from ftplib import FTP
import time
import re
import sys
#--------------------------------------------------------------------------------------------------
class FtpytailPlugin(b3.plugin.Plugin):
  requiresConfigFile = False
  ftpconfig = None
  
  def onStartup(self):
    if self.console.config.get('server','game_log')[0:6] == 'ftp://' :
        gamelog = self.console.config.get('server', 'game_log')
        self.ftpconfig = functions.splitDSN(gamelog)
        thread1 = threading.Thread( target=self.update)
        thread1.start()

  def update(self):
    def handleDownload(block):
	  self.file.write(block)
	  self.file.flush()
    ftp = False
    self.file = open('games_mp.log', 'ab')
    while True:
        try:
            if ftp == False:
                ftp = self.ftpconnect()
                ftp.cwd(os.path.dirname(self.ftpconfig['path']))
            size=os.path.getsize('games_mp.log')
            ftp.retrbinary('RETR ' + os.path.basename(self.ftpconfig['path']), handleDownload, rest=size)          
        except:
            self.debug('Lost connection to server, pausing until updated properly, Sleeping 10 seconds')
            self.console.pause()
            try:
                ftp.close()
                self.debug('FTP Connection Closed')
            except:
                self.debug('FTP does not appear to be open, so not closed')
            ftp = False
            time.sleep(10)

  def ftpconnect(self):
    versionsearch = re.search("^((?P<mainversion>[0-9]).(?P<lowerversion>[0-9]+)?)", sys.version)
    version = int(versionsearch.group(3))
    if version < 6:
        self.debug('Python Version %s.%s, so not setting timeout, update to 2.6 if you want B3 to autorestart quicker.' % (versionsearch.group(2), versionsearch.group(3)))
        ftp=FTP(self.ftpconfig['host'],self.ftpconfig['user'],passwd=self.ftpconfig['password'])
    else:
        self.debug('Python Version %s.%s, so setting timeout of 5 seconds' % (versionsearch.group(2), versionsearch.group(3)))
        ftp=FTP(self.ftpconfig['host'],self.ftpconfig['user'],passwd=self.ftpconfig['password'],timeout=5)
    self.console.clients.sync()
    self.console.unpause()
    return ftp
