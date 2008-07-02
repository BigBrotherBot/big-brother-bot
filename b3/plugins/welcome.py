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

__version__ = '1.0.2'
__author__  = 'ThorN'

import b3, threading
import b3.events
import b3.plugin

#--------------------------------------------------------------------------------------------------
class WelcomePlugin(b3.plugin.Plugin):
	_newbConnections = 0
	_welcomeFlags = 0

	def onStartup(self):
		self.registerEvent(b3.events.EVT_CLIENT_AUTH)

	def onLoadConfig(self):
		self._welcomeFlags = self.config.getint('settings', 'flags')
		self._newbConnections = self.config.getint('settings', 'newb_connections')

	def onEvent(self, event):
		if event.type == b3.events.EVT_CLIENT_AUTH:
			if 	self._welcomeFlags < 1 or \
				not event.client or \
				not event.client.id or \
				event.client.cid == None or \
				not event.client.connected or \
				event.client.pbid == 'WORLD' or \
				self.console.upTime() < 300:
				return

			t = threading.Timer(30, self.welcome, (event.client,))
			t.start()

	def welcome(self, client):
		# don't need to welcome people who got kicked
		if client.connected:
			info = {
				'name'	: client.exactName,
				'id'	: str(client.id),
				'connections' : str(client.connections)
			}

			if client.maskedGroup:
				info['group'] = client.maskedGroup.name
				info['level'] = str(client.maskedGroup.level)
			else:
				info['group'] = 'None'
				info['level'] = '0'

			if client.connections >= 2:
				info['lastVisit'] = self.console.formatTime(client.timeEdit)
			else:
				info['lastVisit'] = 'Unknown'

			if client.connections >= 2:
				if client.maskedGroup:
					if self._welcomeFlags & 16:
						client.message(self.getMessage('user', info))
				elif self._welcomeFlags & 1:
						client.message(self.getMessage('newb', info))

				if self._welcomeFlags & 2 and client.connections < self._newbConnections:
					self.console.say(self.getMessage('announce_user', info))
			else:
				if self._welcomeFlags & 4:
					client.message(self.getMessage('first', info))
				if self._welcomeFlags & 8:
					self.console.say(self.getMessage('announce_first', info))

			if self._welcomeFlags & 32 and client.greeting:
				info['greeting'] = client.greeting % info
				self.console.say(self.getMessage('greeting', info))