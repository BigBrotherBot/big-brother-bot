# -*- coding: utf-8 -*-

# ################################################################### #
#                                                                     #
#  BigBrotherBot(B3) (www.bigbrotherbot.net)                          #
#  Copyright (C) 2005 Michael "ThorN" Thornton                        #
#                                                                     #
#  This program is free software; you can redistribute it and/or      #
#  modify it under the terms of the GNU General Public License        #
#  as published by the Free Software Foundation; either version 2     #
#  of the License, or (at your option) any later version.             #
#                                                                     #
#  This program is distributed in the hope that it will be useful,    #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of     #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the       #
#  GNU General Public License for more details.                       #
#                                                                     #
#  You should have received a copy of the GNU General Public License  #
#  along with this program; if not, write to the Free Software        #
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA      #
#  02110-1301, USA.                                                   #
#                                                                     #
# ################################################################### #

__author__ = 'Fenix'
__version__ = '1.5.1'

import b3
import b3.plugin
import b3.events

from b3.functions import getCmd


class SpawnkillPlugin(b3.plugin.Plugin):

    adminPlugin = None
    requiresParsers = ['iourt42','iourt43']

    penalties = {}

    settings = {
        'hit': {
            'maxlevel': 40,
            'delay': 2,
            'penalty': 'warn',
            'duration': 3,
            'reason': 'do not shoot to spawning players!'
        },
        'kill': {
            'maxlevel': 40,
            'delay': 3,
            'penalty': 'warn',
            'duration': 5,
            'reason': 'spawnkilling is not allowed on this server!'
        }
    }

    ####################################################################################################################
    #                                                                                                                  #
    #   STARTUP                                                                                                        #
    #                                                                                                                  #
    ####################################################################################################################

    def onLoadConfig(self):
        """
        Load plugin configuration.
        """
        def validate(x):
            """helper used to validate the penalty value"""
            acceptable = ('warn', 'kick', 'tempban', 'slap', 'nuke', 'kill')
            if x not in acceptable:
                raise ValueError('value must be one of [%s]' % ', '.join(acceptable))
            return x

        for index in ('hit', 'kill'):
            self.settings[index]['maxlevel'] = self.getSetting(index, 'maxlevel', b3.LEVEL, self.settings[index]['maxlevel'])
            self.settings[index]['delay'] = self.getSetting(index, 'delay', b3.INT, self.settings[index]['delay'])
            self.settings[index]['duration'] = self.getSetting(index, 'duration', b3.DURATION, self.settings[index]['duration'])
            self.settings[index]['reason'] = self.getSetting(index, 'reason', b3.STR, self.settings[index]['reason'])
            self.settings[index]['penalty'] = self.getSetting(index, 'penalty', b3.STR, self.settings[index]['penalty'], validate)

    def onStartup(self):
        """
        Initialize plugin settings.
        """
        # get the admin plugin
        self.adminPlugin = self.console.getPlugin('admin')

        # register our commands
        if 'commands' in self.config.sections():
            for cmd in self.config.options('commands'):
                level = self.config.get('commands', cmd)
                sp = cmd.split('-')
                alias = None
                if len(sp) == 2:
                    cmd, alias = sp

                func = getCmd(self, cmd)
                if func:
                    self.adminPlugin.registerCommand(self, cmd, level, func, alias)

        # register the events needed
        self.registerEvent('EVT_CLIENT_SPAWN', self.onSpawn)
        self.registerEvent('EVT_CLIENT_DAMAGE', self.onDamage)
        self.registerEvent('EVT_CLIENT_KILL', self.onKill)
        self.registerEvent('EVT_CLIENT_KILL_TEAM', self.onKillTeam)

        # create out custom events
        self.console.createEvent('EVT_CLIENT_SPAWNKILL', 'Event client spawnkill')
        self.console.createEvent('EVT_CLIENT_SPAWNKILL_TEAM', 'Event client spawnkill team')

        # register penalty handlers
        self.penalties['warn'] = self.warn_client
        self.penalties['kick'] = self.kick_client
        self.penalties['tempban'] = self.tempban_client
        self.penalties['slap'] = self.slap_client
        self.penalties['nuke'] = self.nuke_client
        self.penalties['kill'] = self.kill_client

        # notice plugin startup
        self.debug('plugin started')

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENTS                                                                                                         #
    #                                                                                                                  #
    ####################################################################################################################

    def onSpawn(self, event):
        """
        Handle EVT_CLIENT_SPAWN.
        """
        event.client.setvar(self, 'spawntime', self.console.time())

    def onDamage(self, event):
        """
        Handle EVT_CLIENT_DAMAGE.
        """
        client = event.client
        target = event.target
        
        if client.maxLevel >= self.settings['hit']['maxlevel']:
            self.verbose('bypassing spawnhit check: %s <@%s> is a high group level player', client.name, client.id)
            return
        
        if not target.isvar(self, 'spawntime'):
            self.verbose('bypassing spawnhit check: %s <@%s> has no spawntime marked', target.name, target.id)
            return
        
        if self.console.time() - target.var(self, 'spawntime').toInt() < self.settings['hit']['delay']:
            func = self.penalties[self.settings['hit']['penalty']]
            func('hit', client)

    def onKill(self, event):
        """
        Handle EVT_CLIENT_KILL.
        """
        client = event.client
        target = event.target
        
        if client.maxLevel >= self.settings['kill']['maxlevel']:
            self.verbose('bypassing spawnkill check: %s <@%s> is a high group level player', client.name, client.id)
            return
        
        if not target.isvar(self, 'spawntime'):
            self.verbose('bypassing spawnkill check: %s <@%s> has no spawntime marked', target.name, target.id)
            return
        
        if self.console.time() - target.var(self, 'spawntime').toInt() < self.settings['kill']['delay']:
            func = self.penalties[self.settings['kill']['penalty']]
            func('kill', client)
            ## EVENT: produce an event so other plugins can perform other actions
            self.console.queueEvent(self.console.getEvent('EVT_CLIENT_SPAWNKILL', client=client, target=target))

    def onKillTeam(self, event):
        """
        Handle EVT_CLIENT_KILL_TEAM.
        """
        client = event.client
        target = event.target

        if client.maxLevel < self.settings['kill']['maxlevel'] and target.isvar(self, 'spawntime'):
            ## EVENT: produce an event so other plugins can perform other actions
            self.console.queueEvent(self.console.getEvent('EVT_CLIENT_SPAWNKILL_TEAM', client=client, target=target))

    ####################################################################################################################
    #                                                                                                                  #
    #   APPLY PENALTIES                                                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    def warn_client(self, index, client):
        """
        Warn a client for spawnkilling
        """
        self.debug('applying warn penalty on client <@%s>: spawn%s detected!' % (client.id, index))
        self.adminPlugin.warnClient(client, self.settings[index]['reason'], admin=None,
                                    timer=False, newDuration=self.settings[index]['duration'])

    def kick_client(self, index, client):
        """
        Kick a client for spawnkilling
        """
        self.debug('applying kick penalty on client <@%s>: spawn%s detected!' % (client.id, index))
        client.kick(self.settings[index]['reason'])

    def tempban_client(self, index, client):
        """
        Ban a client for spawnkilling
        """
        self.debug('applying tempban penalty on client <@%s>: spawn%s detected!' % (client.id, index))
        client.tempban(reason=self.settings[index]['reason'], duration=self.settings[index]['duration'])

    def slap_client(self, index, client):
        """
        Slap a client for spawnkilling
        """
        self.debug('applying slap penalty on client <@%s>: spawn%s detected!' % (client.id, index))
        self.console.inflictCustomPenalty('slap', client, self.settings[index]['reason'])

    def nuke_client(self, index, client):
        """
        Slap a client for spawnkilling
        """
        self.debug('applying nuke penalty on client <@%s>: spawn%s detected!' % (client.id, index))
        self.console.inflictCustomPenalty('nuke', client, self.settings[index]['reason'])

    def kill_client(self, index, client):
        """
        Slap a client for spawnkilling
        """
        self.debug('applying kill penalty on client <@%s>: spawn%s detected!' % (client.id, index))
        self.console.inflictCustomPenalty('kill', client, self.settings[index]['reason'])