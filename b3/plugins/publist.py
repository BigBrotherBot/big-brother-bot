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
# 23:29 17/07/2008 - 1.1.6- Courgette
#	Add specific user-agent
#	url is now store in a property
#	add info: version, parserversion, database, plugins, os
#	cron job will trigger at a random minute time to avoid jamming
#	22:58 18/07/2008 - 1.1.7 - Courgette
#	add parser version and plugins' versions

__version__ = '1.1.7'
__author__  = 'ThorN'

import urllib
import b3, os, random
import b3.events
import b3.plugin
from b3 import functions

# set up our URLopner so we can specify a custom User-Agent
class PublistURLopener(urllib.FancyURLopener):
		version = "B3 Publist plugin/%s" % __version__
urllib._urlopener = PublistURLopener()


#--------------------------------------------------------------------------------------------------
class PublistPlugin(b3.plugin.Plugin):
	_cronTab = None
	_url='http://www.bigbrotherbot.com/serverping.php'

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
			self.debug("%s"%cvar)
			if cvar:
				break

		self.verbose('Got %s for %s', cvar, cvarName)

		if cvar:
			cvar.value = 'B3 %s' % b3.versionId
			cvar.save(self.console)
			
			rmin = random.randint(0,59)
			rhour = random.randint(0,23)
			self.debug("publist will ping at %s:%s every day" % (rhour,rmin))
			self._cronTab = b3.cron.PluginCronTab(self, self.update, 0, rmin, rhour, '*', '*', '*')
			self.console.cron + self._cronTab
		else:
			self.critical('You MUST have one of the B3 cvars %s set in your config to use the publist plugin. Example: sets .B3 "true"' % str(cvars))
			#self.error('You MUST have one of the B3 cvars (%s) set in your config to use the publist plugin. Example: sets .B3 = "true"' % str(cvars))

	def update(self):
		self.debug('Sending server list update to B3 master')
		
		
		def getModule(name):
			mod = __import__(name)
			components = name.split('.')
			for comp in components[1:]:
				mod = getattr(mod, comp)
			return mod
			
		plugins = []
		for pname in self.console._pluginOrder:
			plugins.append("%s/%s" % (pname, getattr(getModule(self.console.getPlugin(pname).__module__), '__version__', 'Unknown Version')))
			
		info = {
			'ip' : self.console._publicIp,
			'port' : self.console._port,
			'version' : b3.versionId,
			'parser' : self.console.gameName,
			'parserversion' : getattr(getModule(self.console.__module__), '__version__', 'Unknown Version'),
			'database' : functions.splitDSN(self.console.storage.dsn)['protocol'],
			'plugins' : ','.join(plugins),
			'os' : os.name
		}

		f = urllib.urlopen('%s?%s' % (self._url, urllib.urlencode(info)))
		self.debug(f.read())
		f.close()

			