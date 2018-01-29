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

__author__ = 'ThorN'
__version__ = '1.4'

import b3
import b3.events
import b3.plugin
import b3.cron

from b3.functions import getCmd
from ConfigParser import NoOptionError


class PingwatchPlugin(b3.plugin.Plugin):

    _adminPlugin = None
    _cronTab = None

    _interval = 0
    _maxPing = 0
    _maxPingDuration = 0

    _ignoreTill = 0
    _maxCiPing = 500

    ####################################################################################################################
    #                                                                                                                  #
    #    STARTUP                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def onLoadConfig(self):
        """
        Load plugin configuration.
        """
        try:
            self._interval = self.config.getint('settings', 'interval')
            self.debug('loaded settings/interval: %s' % self._interval)
        except NoOptionError:
            self.warning('could not find settings/interval in config file, using default: %s' % self._interval)
        except ValueError, e:
            self.error('could not load settings/interval config value: %s' % e)
            self.debug('using default value (%s) for settings/interval' % self._interval)

        try:
            self._maxPing = self.config.getint('settings', 'max_ping')
            self.debug('loaded settings/max_ping: %s' % self._maxPing)
        except NoOptionError:
            self.warning('could not find settings/max_ping in config file, using default: %s' % self._maxPing)
        except ValueError, e:
            self.error('could not load settings/max_ping config value: %s' % e)
            self.debug('using default value (%s) for settings/max_ping' % self._maxPing)

        try:
            self._maxPingDuration = self.config.getint('settings', 'max_ping_duration')
            self.debug('loaded settings/max_ping_duration: %s' % self._maxPingDuration)
        except NoOptionError:
            self.warning('could not find settings/max_ping_duration in config file, '
                         'using default: %s' % self._maxPingDuration)
        except ValueError, e:
            self.error('could not load settings/max_ping_duration config value: %s' % e)
            self.debug('using default value (%s) for settings/max_ping_duration' % self._maxPingDuration)

    def onStartup(self):
        """
        Initialize plugin.
        """
        self._adminPlugin = self.console.getPlugin('admin')

        # register events needed
        self.registerEvent('EVT_GAME_EXIT', self.onGameExit)
        self._ignoreTill = self.console.time() + 120  # dont check pings on startup

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
                    self._adminPlugin.registerCommand(self, cmd, level, func, alias)

        # remove existing crontab
        if self._cronTab:
            self.console.cron - self._cronTab

        # setup the new crontab
        self._cronTab = b3.cron.PluginCronTab(self, self.check, '*/%s' % self._interval)
        self.console.cron + self._cronTab

    ####################################################################################################################
    #                                                                                                                  #
    #    EVENTS                                                                                                        #
    #                                                                                                                  #
    ####################################################################################################################

    def onGameExit(self, event):
        """
        Handle EVT_GAME_EXIT
        """
        # ignore ping watching for 2 minutes
        self._ignoreTill = self.console.time() + 120

    ####################################################################################################################
    #                                                                                                                  #
    #    CRONJOB                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def check(self):
        """
        Check for clients with high ping.
        """
        if not self.isEnabled() or self.console.time() <= self._ignoreTill:
            # we are not supposed to check
            return

        for cid, ping in self.console.getPlayerPings().items():
            # loop through all the connected clients
            # self.console.verbose('ping %s = %s', cid, ping)
            if ping <= self._maxPing:
                continue

            client = self.console.clients.getByCID(cid)
            if not client:
                continue

            if not client.isvar(self, 'highping'):
                self.console.verbose('set ping watch %s = %s', cid, ping)
                client.setvar(self, 'highping', self.console.time())
                return

            self.console.verbose('set high ping check %s = %s (%s)', cid, ping, client.var(self, 'highping', 0).value)
            if self.console.time() - client.var(self, 'highping', 0).value > self._maxPingDuration:
                if ping == 999:
                    self.console.say('^7%s ^7ping detected as Connection Interrupted (CI)' % client.name)
                else:
                    self.console.say('^7%s ^7ping detected as too high %s' % (client.name, ping))

    ####################################################################################################################
    #                                                                                                                  #
    #    COMMANDS                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def cmd_ci(self, data, client=None, cmd=None):
        """
        <client> - kick a client that has an interrupted connection
        """
        m = self._adminPlugin.parseUserCmd(data)
        if not m:
            client.message('^7Missing data, try !help ci')
            return False

        sclient = self._adminPlugin.findClientPrompt(m[0], client)
        if not sclient:
            return

        try:
            players = self.console.getPlayerPings()
            ping = players[str(sclient.cid)]
            if ping > self._maxCiPing:
                sclient.kick(self._adminPlugin.getReason('ci'), 'ci', client)
            else:
                client.message('^7%s ^7is not CI' % sclient.exactName)
        except KeyError:
            pass