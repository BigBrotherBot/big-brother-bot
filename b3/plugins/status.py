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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA    02110-1301    USA
#
# CHANGELOG
# 13/08/2010 - 1.4.3 - xlr8or
# * Added running roundtime and maptime
# 08/08/2010 - 1.4.2 - xlr8or
# * Moved 'Game section' before 'Clients section', XLRstats needs gameinfo before it adds clients to the playerlist
# 21/03/2010 - 1.4.1 - Courgette
# * does not fail if there is no player score available
# * make errors more verbose
# 23/11/2009 - 1.4.0 - Courgette
# on bot shutdown, write an empty status.xml document.
# add tests
# 03/11/2009 - 1.3.1 - Bakes
# XML code is now produced through xml.dom.minidocument rather than concatenation. This has a number of advantages.
# 03/11/2009 - 1.3.0 - Bakes
# Combined statusftp and status. Use syntax ftp://user:password@host/path/to/status.xml
# 11/02/2009 - 1.2.7 - xlr8or
# If masked show masked level instead of real level
# 11/02/2009 - 1.2.6 - xlr8or
# Sanitized xml data, cleaning ascii < 32 and > 126 (func is in functions.py)
# 21/11/2008 - 1.2.5 - Anubis
# Added PlayerScores
# 12/03/2008 - 1.2.4 - Courgette
# Properly escape strings to ensure valid xml
# 11/30/2005 - 1.2.3 - ThorN
# Use PluginCronTab instead of CronTab
# 8/29/2005 - 1.2.0 - ThorN
# Converted to use new event handlers

__author__    = 'ThorN'
__version__ = '1.4.3'

import b3, time, os, StringIO
import b3.plugin
import b3.cron
from cgi import escape
from ftplib import FTP
from b3 import functions
from xml.dom.minidom import Document
from b3.functions import sanitizeMe

#--------------------------------------------------------------------------------------------------
class StatusPlugin(b3.plugin.Plugin):
    _tkPlugin = None
    _cronTab = None
    _ftpstatus = False
    _ftpinfo = None
    
    def onLoadConfig(self):
        if self.config.get('settings','output_file')[0:6] == 'ftp://':
                self._ftpinfo = functions.splitDSN(self.config.get('settings','output_file'))
                self._ftpstatus = True
        else:        
                self._outputFile = os.path.expanduser(self.config.get('settings', 'output_file'))
                
        self._tkPlugin = self.console.getPlugin('tk')
        self._interval = self.config.getint('settings', 'interval')

        if self._cronTab:
            # remove existing crontab
            self.console.cron - self._cronTab

        self._cronTab = b3.cron.PluginCronTab(self, self.update, '*/%s' % self._interval)
        self.console.cron + self._cronTab

    def onEvent(self, event):
        if event.type == b3.events.EVT_STOP:
            self.info('B3 stop/exit.. updating status')
            # create an empty status document
            xml = Document()
            b3status = xml.createElement("B3Status")
            b3status.setAttribute("Time", time.asctime())
            xml.appendChild(b3status)
            self.writeXML(xml.toprettyxml(indent="        "))

    def update(self):
        clients = self.console.clients.getList()
        scoreList = self.console.getPlayerScores() 
                 
        self.verbose('Building XML status')
        xml = Document()
        # --- Main section
        b3status = xml.createElement("B3Status")
        b3status.setAttribute("Time", time.asctime())
        xml.appendChild(b3status)

        # --- Game section
        c = self.console.game
        gamename = ''
        gametype = ''
        mapname = ''
        timelimit = ''
        fraglimit = ''
        capturelimit = ''
        rounds = ''
        roundTime = ''
        mapTime = ''
        if c.gameName:
            gamename = c.gameName
        if c.gameType:
            gametype = c.gameType
        if c.mapName:
            mapname = c.mapName
        if c.timelimit:
            timelimit = c.timelimit
        if c.fraglimit:
            fraglimit = c.fraglimit
        if c.captureLimit:
            capturelimit = c.captureLimit
        if c.rounds:
            rounds = c.rounds
        if c.roundTime:
            roundTime = c.roundTime()
        if c.mapTime:
            mapTime = c.mapTime()
        game = xml.createElement("Game")
        game.setAttribute("Name", str(gamename))
        game.setAttribute("Type", str(gametype))
        game.setAttribute("Map", str(mapname))
        game.setAttribute("TimeLimit", str(timelimit))
        game.setAttribute("FragLimit", str(fraglimit))
        game.setAttribute("CaptureLimit", str(capturelimit))
        game.setAttribute("Rounds", str(rounds))
        game.setAttribute("RoundTime", str(roundTime))
        game.setAttribute("MapTime", str(mapTime))
        b3status.appendChild(game)

        for k,v in self.console.game.__dict__.items():
            data = xml.createElement("Data")
            data.setAttribute("Name", str(k))
            data.setAttribute("Value", str(v))
            game.appendChild(data)
        # --- End Game section        

        # --- Clients section
        b3clients = xml.createElement("Clients")
        b3clients.setAttribute("Total", str(len(clients)))
        b3status.appendChild(b3clients)

        for c in clients:
            if not c.name:
                c.name = "@"+str(c.id)
            if c.exactName == "^7":
                c.exactName = "@"+str(c.id)+"^7"

            if not c.maskedLevel:
                _level = c.maxLevel
            else:
                _level = c.maskedLevel

            try:
                client = xml.createElement("Client")
                client.setAttribute("Name", str(sanitizeMe(c.name)))
                client.setAttribute("ColorName", str(sanitizeMe(c.exactName)))
                client.setAttribute("DBID", str(c.id))
                client.setAttribute("Connections", str(c.connections))
                client.setAttribute("CID", str(c.cid))
                client.setAttribute("Level", str(_level))
                if c.guid:
                    client.setAttribute("GUID", c.guid)
                else:
                    client.setAttribute("GUID", '')
                if c.pbid:
                    client.setAttribute("PBID", c.pbid)
                else:
                    client.setAttribute("PBID", '')
                client.setAttribute("IP", c.ip)
                client.setAttribute("Team", str(c.team))
                client.setAttribute("Joined", str(time.ctime(c.timeAdd)))
                client.setAttribute("Updated", str(time.ctime(c.timeEdit)))
                if scoreList and c.cid in scoreList:
                    client.setAttribute("Score", str(scoreList[c.cid]))
                client.setAttribute("State", str(c.state))
                b3clients.appendChild(client)

                for k,v in c.data.iteritems():
                    data = xml.createElement("Data")
                    data.setAttribute("Name", str(k))
                    data.setAttribute("Value", str(sanitizeMe(v)))
                    client.appendChild(data)
                        
                if self._tkPlugin:
                    if hasattr(c, 'tkplugin_points'):
                        tkplugin = xml.createElement("TkPlugin")
                        tkplugin.setAttribute("Points", str(c.var(self, 'points')))
                        client.appendChild(tkplugin)            
                        if hasattr(c, 'tkplugin_attackers'):
                            for acid,points in c.var(self, 'attackers').value.items():
                                try:
                                    attacker = xml.createElement("Attacker")
                                    attacker.setAttribute("Name", sanitizeMe(self.console.clients[acid].name))
                                    attacker.setAttribute("CID", str(acid))
                                    attacker.setAttribute("Points", str(points))
                                    tkplugin.appendChild(attacker)
                                except:
                                    pass
                                
            except Exception, err:
                self.debug('XML Failed: %r' % err)
                pass
        # --- End Clients section

        self.writeXML(xml.toprettyxml(indent="        "))

    def writeXML(self, xml):
        if self._ftpstatus == True:
            self.debug('Uploading XML status to FTP server')
            ftp=FTP(self._ftpinfo['host'],self._ftpinfo['user'],passwd=self._ftpinfo['password'])
            ftp.cwd(os.path.dirname(self._ftpinfo['path']))
            ftpfile = StringIO.StringIO()
            ftpfile.write(xml)
            ftpfile.seek(0)
            ftp.storbinary('STOR '+os.path.basename(self._ftpinfo['path']), ftpfile)
        else:
            self.debug('Writing XML status to %s', self._outputFile)
            f = file(self._outputFile, 'w')
            f.write(xml)
            f.close()
            
            
if __name__ == '__main__':
    from b3.fake import fakeConsole
    from b3.fake import joe
    from b3.fake import simon
    
    p = StatusPlugin(fakeConsole, "@b3/conf/plugin_status.xml")
    p.onStartup()
    p.update()
    
    while True: pass
    