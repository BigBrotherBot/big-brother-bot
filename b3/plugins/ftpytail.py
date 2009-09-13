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
from b3.lib.ftplib import FTP
import time
 
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
    ftp = self.ftpconnect()
    self.file = open('games_mp.log', 'ab')
    while True:
        try:
            if ftp == False or ftp == True:
                self.debug('FTP connection set false, reconnecting to FTP!')
                ftp = self.ftpconnect()
                self.clients.sync()
                self.console.unpause()
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
            self.debug('FTP connection set false, sleeping for 10 seconds before retry')
            time.sleep(10)

  def ftpconnect(self):
    ftp=FTP(self.ftpconfig['host'],self.ftpconfig['user'],passwd=self.ftpconfig['password'],timeout=5)
    return ftp
