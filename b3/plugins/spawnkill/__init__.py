#
# Spawnkill Plugin for BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2013 Daniele Pantaleone <fenix@bigbrotherbot.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
#
# CHANGELOG
#
# 2014-05-09 - 1.2 - Fenix - make use of time.time() instead of self.console.time(): storage methods uses time.time() to
#                            get the timestamp vaue, and using self.console.time() will break data consistency
#                          - added automated tests
# 2015-02-07 - 1.3 - Fenix - changed plugin module structure
#                          - do not let the plugin shutdown B3 when invalid parser is being used (just unload the plugin)
# 2015-03-22 - 1.4 - Fenix - adapted plugin after committing first built-in release


__author__ = 'Fenix'
__version__ = '1.4'

import b3
import b3.plugin
import b3.events
import time

from b3.functions import getCmd
from ConfigParser import NoOptionError


class SpawnkillPlugin(b3.plugin.Plugin):

    adminPlugin = None
    requiresParsers = ['iourt42']

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
        Load plugin configuration
        """
        for index in ('hit', 'kill'):

            try:
                self.settings[index]['maxlevel'] = self.console.getGroupLevel(self.config.get(index, 'maxlevel'))
            except (NoOptionError, KeyError), e:
                self.warning('could not load %s/maxlevel from config file: %s' % (index, e))

            try:
                self.settings[index]['delay'] = self.config.getint(index, 'delay')
            except (NoOptionError, ValueError), e:
                self.warning('could not load %s/delay from config file: %s' % (index, e))

            try:
                if self.config.get(index, 'penalty') not in ('warn', 'kick', 'tempban', 'slap', 'nuke', 'kill'):
                    # specified penalty is not supported by this plugin: fallback to default
                    raise ValueError('invalid penalty specified: %s' % self.config.get(index, 'penalty'))
                self.settings[index]['penalty'] = self.config.get(index, 'penalty')
            except (NoOptionError, ValueError), e:
                self.warning('could not load %s/penalty from config file: %s' % (index, e))

            try:
                self.settings[index]['duration'] = self.config.getDuration(index, 'duration')
            except (NoOptionError, ValueError), e:
                self.warning('could not load %s/duration from config file: %s' % (index, e))

            try:
                self.settings[index]['reason'] = self.config.get(index, 'reason')
            except NoOptionError, e:
                self.warning('could not load %s/reason from config file: %s' % (index, e))

            # print current configuration in the log file for later inspection
            self.debug('setting %s/maxlevel: %s' % (index, self.settings[index]['maxlevel']))
            self.debug('setting %s/delay: %s' % (index, self.settings[index]['delay']))
            self.debug('setting %s/penalty: %s' % (index, self.settings[index]['penalty']))
            self.debug('setting %s/duration: %s' % (index, self.settings[index]['duration']))
            self.debug('setting %s/reason: %s' % (index, self.settings[index]['reason']))

    def onStartup(self):
        """
        Initialize plugin settings
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
        event.client.setvar(self, 'spawntime', time.time())

    def onDamage(self, event):
        """
        Handle EVT_CLIENT_DAMAGE.
        """
        self.onSpawnKill('hit', event.client, event.target)

    def onKill(self, event):
        """
        Handle EVT_CLIENT_KILL.
        """
        self.onSpawnKill('kill', event.client, event.target)

    ####################################################################################################################
    #                                                                                                                  #
    #   OTHER METHODS                                                                                                  #
    #                                                                                                                  #
    ####################################################################################################################

    def onSpawnKill(self, index, client, target):
        """
        Handle possible spawn(hit|kill) events
        """
        # checking for correct client level
        if client.maxLevel >= self.settings[index]['maxlevel']:
            self.verbose('bypassing spawn%s check: client <@%s> is a high group level player' % (index, client.id))
            return

        # checking for spawntime mark in client object
        if not target.isvar(self, 'spawntime'):
            self.verbose('bypassing spawn%s check: client <@%s> has no spawntime marked' % (index, target.id))
            return

        # if we got a spawn(hit|kill) action, applies the configured penalty
        if time.time() - target.var(self, 'spawntime').toInt() < self.settings[index]['delay']:
            func = self.penalties[self.settings[index]['penalty']]
            func(index, client)

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