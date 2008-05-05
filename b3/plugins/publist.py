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
# $Id: publist.py 43 2005-12-06 02:17:55Z thorn $
#
# CHANGELOG
#	11/30/2005 - 1.0.3 - ThorN
#	Use PluginCronTab instead of CronTab

__version__ = '1.1.5'
__author__  = 'ThorN'

import urllib

import b3
import b3.events
import b3.plugin

#--------------------------------------------------------------------------------------------------
class PublistPlugin(b3.plugin.Plugin):
	_cronTab = None

	def onStartup(self):
		# do instant update
		self.update()

	def onLoadConfig(self):
		if self._cronTab:
			# remove existing crontab
			self.console.cron - self._cronTab


		# set settings so b3 server updater will see
		cvarName = None
		cvar = None
		cvars = ('.B3', '_B3')
		for cvarName in cvars:
			cvar = self.console.getCvar(cvarName)
			if cvar:
				break

		self.verbose('Got %s for %s', cvar, cvarName)

		if cvar:
			cvar.value = 'B3 %s' % b3.versionId
			cvar.save(self.console)
			
			self._cronTab = b3.cron.PluginCronTab(self, self.update, 0, 0, 0, '*', '*', '*')
			self.console.cron + self._cronTab
		else:
			self.critical('You MUST have one of the B3 cvars (%s) set in your config to use the publist plugin. Example: sets .B3 = "true"', str(cvars))

	def update(self):
		self.debug('Sending server list update to B3 master')
		
		info = {
			'ip' : self.console._publicIp,
			'port' : self.console._port,
			'type' : self.console.gameName
		}

		f = urllib.urlopen('http://www.bigbrotherbot.com/serverping.php?%s' % urllib.urlencode(info))
		self.debug(f.read())
		f.close()