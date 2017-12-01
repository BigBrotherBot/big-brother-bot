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

__version__ = '1.3.1'
__author__  = 'SGT'

import time
import threading

from b3.functions import getCmd
from b3.plugins.welcome import WelcomePlugin
from b3.plugins.welcome import F_FIRST
from b3.plugins.welcome import F_NEWB
from b3.plugins.welcome import F_USER
from b3.plugins.welcome import F_ANNOUNCE_FIRST
from b3.plugins.welcome import F_ANNOUNCE_USER
from b3.plugins.welcome import F_CUSTOM_GREETING


class GeowelcomePlugin(WelcomePlugin):

    requiresPlugins = ['geolocation']
    loadAfterPlugins = ['countryfilter', 'welcome']

    _default_messages = {
        'first': '^7Welcome $name^7, this must be your first visit, you are player ^3#$id. Type !help for help',
        'newb': '^7[^2Authed^7] Welcome back $name ^7[^3@$id^7], last visit ^3$lastVisit. '
                'Type !register in chat to register. Type !help for help',
        'user': '^7[^2Authed^7] Welcome back $name ^7[^3@$id^7], last visit ^3$lastVisit^7, '
                'you\'re a ^2$group^7, played $connections times',
        'announce_first': '^7Everyone welcome $name^7, player number ^3#$id^7, to the server',
        'announce_user': '^7Everyone welcome back $name^7, player number ^3#$id^7, to the server, '
                         'played $connections times',
        'greeting': '^7$name^7 joined: $greeting',
        'greeting_empty': '^7You have no greeting set',
        'greeting_yours': '^7Your greeting is %s',
        'greeting_bad': '^7Greeting is not formatted properly: %s',
        'greeting_changed': '^7Greeting changed to: %s',
        'greeting_cleared': '^7Greeting cleared',
        'announce_user_geo': '^7Everyone welcome back $name^7, from ^3$country^7. Player number ^3#$id^7, '
                             'played $connections times',
        'announce_first_geo': '^7Everyone welcome $name^7, from ^3$country^7. Player number ^3#$id^7'
    }

    ####################################################################################################################
    #                                                                                                                  #
    #    STARTUP                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def onStartup(self):
        """
        Initialize the plugin
        """
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

        # register events needed
        self.registerEvent('EVT_CLIENT_GEOLOCATION_SUCCESS', self.onGeolocationSuccess)
        self.registerEvent('EVT_CLIENT_GEOLOCATION_FAILURE', self.onGeolocationFailure)

        welcomePlugin = self.console.getPlugin('welcome')
        if welcomePlugin:
            self.info('NOTE: to run this plugin you don\'t need to load also the Welcome plugin: disabling Welcome plugin')
            welcomePlugin.disable()

    ####################################################################################################################
    #                                                                                                                  #
    #    EVENTS                                                                                                        #
    #                                                                                                                  #
    ####################################################################################################################

    def onGeolocationSuccess(self, event):
        """
        Handle EVT_CLIENT_GEOLOCATION_SUCCESS
        """
        if self.must_welcome(event.client):
            t = threading.Timer(self._welcomeDelay, self.geowelcome, (event.client,))
            t.start()

    def onGeolocationFailure(self, event):
        """
        Handle EVT_CLIENT_GEOLOCATION_FAILURE
        """
        if self.must_welcome(event.client):
            t = threading.Timer(self._welcomeDelay, self.welcome, (event.client,))
            t.start()

    ####################################################################################################################
    #                                                                                                                  #
    #    OTHER METHODS                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def must_welcome(self, client):
        """
        Checks whether we have to show a welcome message or not.
        :return: True if we need to welcome the player, False otherwise
        """
        if self._welcomeFlags <= 0 or not client or client.id is None or \
           client.cid is None or not client.connected or client.pbid == 'WORLD':
            return False
        if self.console.upTime() < 300:
            self.debug('not welcoming player because the bot started less than 5 min ago')
            return False
        return True

    def geowelcome(self, client):
        """
        Geo Welcome a player
        """
        if client.lastVisit:
            self.debug('lastVisit: %s' % self.console.formatTime(client.lastVisit))
            _timeDiff = time.time() - client.lastVisit
        else:
            self.debug('lastVisit not available: must be the first time')
            _timeDiff = 1000000  # big enough so it will welcome new players

        # don't need to welcome people who got kicked or where already
        # welcomed in before _min_gap s ago
        if client.connected and _timeDiff > self._min_gap:
            info = self.get_client_info(client)
            if client.connections >= 2:
                if client.maskedLevel > 0:
                    if self._welcomeFlags & F_USER:
                        client.message(self.getMessage('user', info))
                elif self._welcomeFlags & F_NEWB:
                    client.message(self.getMessage('newb', info))

                if self._welcomeFlags & F_ANNOUNCE_USER and client.connections < self._newbConnections:
                    self.console.say(self.getMessage('announce_user_geo', info))
            else:
                if self._welcomeFlags & F_FIRST:
                    client.message(self.getMessage('first', info))
                if self._welcomeFlags & F_ANNOUNCE_FIRST:
                    self.console.say(self.getMessage('announce_first_geo', info))

            if self._welcomeFlags & F_CUSTOM_GREETING and client.greeting:
                _info = {'greeting': client.greeting % info}
                _info.update(info)
                self.console.say(self.getMessage('greeting', _info))
        else:
            if _timeDiff <= self._min_gap:
                self.debug('client already welcomed in the past %s seconds' % self._min_gap)

    def get_client_info(self, client):
        """
        Get client information for message substitution
        """
        info = super(GeowelcomePlugin, self).get_client_info(client)
        if client.location and client.location.country:
            info['country'] = client.location.country
        return info