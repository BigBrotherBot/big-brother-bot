#
# BigBrotherBot(B3) (www.bigbrotherbot.com)
# Copyright (C) 2005 Michael "ThorN" Thornton
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
# CHANGELOG
# 21/11/2008 - 1.2.5 - Anubis
# Added PlayerScores
# 12/03/2008 - 1.2.4 - Courgette
# Properly escape strings to ensure valid xml
#	11/30/2005 - 1.2.3 - ThorN
#	Use PluginCronTab instead of CronTab
#	8/29/2005 - 1.2.0 - ThorN
#	Converted to use new event handlers

__author__  = 'ThorN'
__version__ = '1.2.5'

import b3, time, os
import b3.plugin
import b3.cron
from cgi import escape

#--------------------------------------------------------------------------------------------------
class StatusPlugin(b3.plugin.Plugin):
	_tkPlugin = None
	_cronTab = None

	def onLoadConfig(self):
		self._tkPlugin = self.console.getPlugin('tk')
		self._interval = self.config.getint('settings', 'interval')
		self._outputFile = os.path.expanduser(self.config.get('settings', 'output_file'))

		if self._cronTab:
			# remove existing crontab
			self.console.cron - self._cronTab

		self._cronTab = b3.cron.PluginCronTab(self, self.update, '*/%s' % self._interval)
		self.console.cron + self._cronTab

	def onEvent(self, event):
		pass

	def update(self):
		clients = self.console.clients.getList()  
		
		scoreList = self.console.getPlayerScores() 
         
		self.verbose('Building XML status')
		xml = '<B3Status Time="%s">\n<Clients Total="%s">\n' % (time.asctime(), len(clients))
			  
		for c in clients:
			try:          
				xml += '<Client Name="%s" ColorName="%s" DBID="%s" Connections="%s" CID="%s" Level="%s" GUID="%s" PBID="%s" IP="%s" Team="%s" Joined="%s" Updated="%s" Score="%s" State="%s">\n' % (escape("%s"%c.name), escape("%s"%c.exactName), c.id, c.connections, c.cid, c.maxLevel, c.guid, c.pbid, c.ip, escape("%s"%c.team), time.ctime(c.timeAdd), time.ctime(c.timeEdit) , scoreList[c.cid], c.state )
				for k,v in c.data.iteritems():
					xml += '<Data Name="%s" Value="%s"/>' % (escape("%s"%k), escape("%s"%v)) 
						
				if self._tkPlugin:
					if hasattr(c, 'tkplugin_points'):				
						xml += '<TkPlugin Points="%s">\n' % c.var(self, 'points').toInt()
						if hasattr(c, 'tkplugin_attackers'):
							for acid,points in c.var(self, 'attackers').value.items():
								try:
									xml += '<Attacker Name="%s" CID="%s" Points="%s"/>\n' % (self.console.clients[acid].name, acid, points)
								except:
									pass
								
						xml += '</TkPlugin>\n'

				xml += '</Client>\n'
			except:
				pass

		c = self.console.game
		xml += '</Clients>\n<Game Name="%s" Type="%s" Map="%s" TimeLimit="%s" FragLimit="%s" CaptureLimit="%s" Rounds="%s">\n' % (escape("%s"%c.gameName), escape("%s"%c.gameType), escape("%s"%c.mapName), c.timeLimit, c.fragLimit, c.captureLimit, c.rounds)
		for k,v in self.console.game.__dict__.items():
			xml += '<Data Name="%s" Value="%s"/>\n' % (escape("%s"%k), escape("%s"%v)) 
		xml += '</Game>\n</B3Status>'
				

		self.writeXML(xml)

	def writeXML(self, xml):
		self.debug('Writing XML status to %s', self._outputFile)
		f = file(self._outputFile, 'w')
		f.write(xml)
		f.close()
