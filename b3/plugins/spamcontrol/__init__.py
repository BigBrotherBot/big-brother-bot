# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2009 James "Bakes" Baker
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

import b3
import b3.events
import b3.plugin
import re

from b3.functions import getCmd
from ConfigParser import NoOptionError

__author__ = 'ThorN, Courgette'
__version__ = '1.4.3'


class SpamcontrolPlugin(b3.plugin.Plugin):

    _adminPlugin = None

    _maxSpamins = 10
    _modLevel = 20
    _falloffRate = 6.5

    ####################################################################################################################
    #                                                                                                                  #
    #    STARTUP                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def onLoadConfig(self):
        """
        Load plugin configuration
        """
        try:
            self._maxSpamins = self.config.getint('settings', 'max_spamins')
            if self._maxSpamins < 0:
                self._maxSpamins = 0
            self.debug('loaded settings/max_spamins: %s' % self._maxSpamins)
        except NoOptionError:
            self.warning('could not find settings/max_spamins in config file, using default: %s' % self._maxSpamins)
        except ValueError, e:
            self.error('could not load settings/max_spamins config value: %s' % e)
            self.debug('using default value (%s) for settings/max_spamins' % self._maxSpamins)

        try:
            self._modLevel = self.console.getGroupLevel(self.config.get('settings', 'mod_level'))
            self.debug('loaded settings/mod_level: %s' % self._modLevel)
        except NoOptionError:
            self.warning('could not find settings/mod_level in config file, using default: %s' % self._modLevel)
        except KeyError, e:
            self.error('could not load settings/mod_level config value: %s' % e)
            self.debug('using default value (%s) for settings/mod_level' % self._modLevel)

        try:
            self._falloffRate = self.config.getfloat('settings', 'falloff_rate')
            self.debug('loaded settings/falloff_rate: %s' % self._falloffRate)
        except NoOptionError:
            self.warning('could not find settings/falloff_rate in config file, using default: %s' % self._falloffRate)
        except ValueError, e:
            self.error('could not load settings/falloff_rate config value: %s' % e)
            self.debug('using default value (%s) for settings/falloff_rate' % self._falloffRate)

    def onStartup(self):
        """
        Initialize the plugin.
        """
        # register the events needed
        self.registerEvent('EVT_CLIENT_SAY', self.onChat)
        self.registerEvent('EVT_CLIENT_TEAM_SAY', self.onChat)
        self.registerEvent('EVT_CLIENT_PRIVATE_SAY', self.onChat)

        self._adminPlugin = self.console.getPlugin('admin')

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

    ####################################################################################################################
    #                                                                                                                  #
    #    OTHER METHODS                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def getTime(self):
        """
        Just to ease automated tests.
        """
        return self.console.time()

    def add_spam_points(self, client, points, text):
        """
        Add spam points to the given client.
        """
        now = self.getTime()
        if client.var(self, 'ignore_till', now).value > now:
            # ignore the user
            raise b3.events.VetoEvent

        last_message_time = client.var(self, 'last_message_time', now).value
        gap = now - last_message_time

        if gap < 2:
            points += 1

        spamins = client.var(self, 'spamins', 0).value + points

        # apply natural points decrease due to time
        spamins -= int(gap / self._falloffRate)

        if spamins < 1:
            spamins = 0

        # set new values
        client.setvar(self, 'spamins', spamins)
        client.setvar(self, 'last_message_time', now)
        client.setvar(self, 'last_message', text)

        # should we warn ?
        if spamins >= self._maxSpamins:
            client.setvar(self, 'ignore_till', now + 2)
            self._adminPlugin.warnClient(client, 'spam')
            spamins = int(spamins / 1.5)
            client.setvar(self, 'spamins', spamins)
            raise b3.events.VetoEvent

    ####################################################################################################################
    #                                                                                                                  #
    #    EVENTS                                                                                                        #
    #                                                                                                                  #
    ####################################################################################################################

    def onChat(self, event):
        """
        Handle EVT_CLIENT_SAY and EVT_CLIENT_TEAM_SAY and EVT_CLIENT_PRIVATE_SAY
        """
        if not event.client or event.client.maxLevel >= self._modLevel:
            return

        points = 0
        client = event.client
        text = event.data
        last_message = client.var(self, 'last_message').value
        color = re.match(r'\^[0-9]', event.data)
        if color and text == last_message:
            points += 5
        elif text == last_message:
            points += 3
        elif color:
            points += 2
        elif text.startswith('QUICKMESSAGE_'):
            points += 2
        else:
            points += 1

        if text[:1] == '!':
            points += 1

        self.add_spam_points(client, points, text)

    ####################################################################################################################
    #                                                                                                                  #
    #    COMMANDS                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def cmd_spamins(self, data, client, cmd=None):
        """
        [<name>] - display a spamins level
        """
        if data:
            sclient = self._adminPlugin.findClientPrompt(data, client)
            if not sclient:
                return
        else:
            sclient = client

        if sclient.maxLevel >= self._modLevel:
            cmd.sayLoudOrPM(client, '%s ^7is too cool to spam' % sclient.exactName)
        else:
            now = self.getTime()
            last_message_time = sclient.var(self, 'last_message_time', now).value
            gap = now - last_message_time

            msmin = smin = sclient.var(self, 'spamins', 0).value
            smin -= int(gap / self._falloffRate)

            if smin < 1:
                smin = 0

            cmd.sayLoudOrPM(client, '%s ^7currently has %s spamins, peak was %s' % (sclient.exactName, smin, msmin))