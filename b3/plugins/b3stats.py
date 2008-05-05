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
# $Id: b3stats.py 6 2005-11-18 05:36:17Z thorn $
#
# CHANGELOG
#	8/29/2005 - 1.1.0 - ThorN
#	Converted to use new event handlers

__author__  = 'ThorN'
__version__ = '1.1.0'

import b3, string, re, threading
import b3.events
import b3.plugin

#--------------------------------------------------------------------------------------------------
class TkPlugin(b3.plugin.Plugin):
	_levels = {}
	_adminPlugin = None
	_maxLevel = 0
	_maxPoints = 0

	def onStartup(self):
		self.registerEvent(b3.events.EVT_CLIENT_DAMAGE)
		self.registerEvent(b3.events.EVT_CLIENT_DAMAGE_TEAM)
		self.registerEvent(b3.events.EVT_CLIENT_DAMAGE_SELF)

		self.registerEvent(b3.events.EVT_CLIENT_KILL)
		self.registerEvent(b3.events.EVT_CLIENT_KILL_TEAM)
		self.registerEvent(b3.events.EVT_CLIENT_SUICIDE)

		self.registerEvent(b3.events.EVT_CLIENT_DISCONNECT)
		self.registerEvent(b3.events.EVT_GAME_EXIT)

	def onLoadConfig(self):
		try:
			levels = string.split(self.config.get('settings', 'levels'), ',')

			for lev in levels:
				self._levels[int(lev)] = (self.config.getfloat('level_%s' % lev, 'kill_multiplier'), self.config.getfloat('level_%s' % lev, 'damage_multiplier'), self.config.getint('level_%s' % lev, 'ban_length'))

			self._maxLevel = int(lev)

			self.debug('tk max level is %s', self._maxLevel)

			self._maxPoints = self.config.getint('settings', 'max_points')
		except Exception, msg:
			self.error('There is an error with your TK Plugin config %s' % msg)
			return False

	def onEvent(self, event):
		if event.type == b3.events.EVT_CLIENT_DAMAGE_TEAM:
			if event.client.maxLevel <= self._maxLevel:
				self.clientDamage(event.client, event.target, int(event.data[0]))

		elif event.type == b3.events.EVT_CLIENT_KILL_TEAM:
			if event.client.maxLevel <= self._maxLevel:
				self.clientDamage(event.client, event.target, int(event.data[0]), True)

		elif event.type == b3.events.EVT_CLIENT_DISCONNECT:
			self.forgiveAll(event.data)
			return

		elif event.type == b3.events.EVT_GAME_EXIT:
			self.debug('Map End: cutting all tk points in half')
			for cid,c in self.console.clients.items():
				try:
					tkinfo = self.getClientTkInfo(c)
					for acid,points in tkinfo.attackers.items():
						points = int(round(points / 2))

						if points == 0:
							self.forgive(acid, c, True)
						else:
							try: tkinfo._attackers[acid] = points
							except: pass
				except:
					pass

			return
		else:
			return

		tkinfo = self.getClientTkInfo(event.client)
		points = tkinfo.points
		if points >= self._maxPoints:
			if points >= self._maxPoints + (self._maxPoints / 2):
				self.forgiveAll(event.client.cid)
				event.client.tempban(self.getMessage('ban'), 'tk', self.getMultipliers(event.client)[2])
			elif event.client.var(self, 'checkBan').value:
				pass
			else:			
				msg = ''
				if len(tkinfo.attacked) > 0:
					myvictims = []
					for cid, bol in tkinfo.attacked.items():
						victim = self.console.clients.getByCID(cid)
						if not victim:
							continue
						
						v = self.getClientTkInfo(victim)
						myvictims.append('%s ^7(^1%s^7)' % (victim.name, v.getAttackerPoints(event.client.cid)))
						
					if len(myvictims):
						msg += ', ^1Attacked^7: %s' % ', '.join(myvictims)

				self.console.say(self.getMessage('forgive_warning', { 'name' : event.client.exactName, 'points' : points }) + msg)
				event.client.setvar(self, 'checkBan', True)

				t = threading.Timer(45, self.checkTKBan, (event.client,))
				t.start()



	def clientDamage(self, attacker, victim, points, killed=False):
		if points > 100:
			points = 100

		a = self.getClientTkInfo(attacker)
		v = self.getClientTkInfo(victim)

		if killed:		
			points = int(round(points * self.getMultipliers(attacker)[1]))
		else:
			points = int(round(points * self.getMultipliers(attacker)[0]))

		a.damage(v.cid, points)
		v.damaged(a.cid, points)

		if self._round_grace and self._issue_warning and self.console.game.roundTime() < self._round_grace:
			self._adminPlugin.warnClient(attacker, self._issue_warning, None, False)