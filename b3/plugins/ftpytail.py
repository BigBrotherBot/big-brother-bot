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
 
#--------------------------------------------------------------------------------------------------
class FtpytailPlugin(b3.plugin.Plugin):
  requiresConfigFile = False
  ftpconfig = None
  
  def onStartup(self):
    if self.console.config.get('server','game_log')[0:6] == 'ftp://' :
        gamelog = self.console.config.get('server', 'game_log')
        self.ftpconfig = functions.splitFTPDSN(gamelog)
        thread1 = threading.Thread( target=self.update)
        thread1.start()

  def update(self):
    def handleDownload(block):
	  self.file.write(block)
	  self.file.flush()
    while True:
        ftp=FTP(self.ftpconfig['host'], self.ftpconfig['user'], self.ftpconfig['password'])
        ftp.cwd(self.ftpconfig['path'])
        self.file = open('games_mp.log', 'ab')
        while True:
          size=os.path.getsize(self.ftpconfig['filename'])
          ftp.retrbinary('RETR ' + self.ftpconfig['filename'], handleDownload, rest=size)          


              
