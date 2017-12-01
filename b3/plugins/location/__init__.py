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


__author__ = 'Fenix, Courgette'
__version__ = '2.3'


import b3
import b3.plugin
import b3.events
import math

from b3.functions import getCmd
from ConfigParser import NoOptionError


class LocationPlugin(b3.plugin.Plugin):
    
    _adminPlugin = None
    _announce = True

    requiresPlugins = ['geolocation']
    loadAfterPlugins = ['countryfilter', 'proxyfilter']

    ####################################################################################################################
    #                                                                                                                  #
    #   STARTUP                                                                                                        #
    #                                                                                                                  #
    ####################################################################################################################

    def onLoadConfig(self):
        """
        Load plugin configuration.
        """
        self._announce = self.getSetting('settings', 'announce', b3.BOOL, self._announce)

        self._default_messages = {
            'client_connect': '^7$name ^3from ^7$city ^3(^7$country^3) connected',
            'cmd_locate': '^7$name ^3is connected from ^7$city ^3(^7$country^3)',
            'cmd_locate_failed': '^7Could not locate ^1$name',
            'cmd_distance': '^7$name ^3is ^7$distance ^3km away from you',
            'cmd_distance_self': '^7Sorry, I\'m not that smart...meh!',
            'cmd_distance_failed': '^7Could not compute distance with ^1$name',
            'cmd_isp': '^7$name ^3is using ^7$isp ^3as isp',
            'cmd_isp_failed': '^7Could not determine ^1$name ^7isp',
        }

    def onStartup(self):
        """
        Initialize plugin settings.
        """
        # get the admin plugin
        self._adminPlugin = self.console.getPlugin('admin')

        if 'commands' in self.config.sections():
            # parse the commands section looking for valid commands
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
        self.registerEvent(self.console.getEventID('EVT_CLIENT_GEOLOCATION_SUCCESS'), self.onGeolocalization)
        self.registerEvent(self.console.getEventID('EVT_PLUGIN_DISABLED'), self.onPluginDisable)

        # notice plugin started
        self.debug('plugin started')

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENTS                                                                                                         #
    #                                                                                                                  #
    ####################################################################################################################

    def onEnable(self):
        """
        Check that all the required plugins are actually enabled, and if not enable them.
        """
        for req in self.requiresPlugins:
            plugin = self.console.getPlugin(req)
            if not plugin.isEnabled():
                plugin.enable()

    def onGeolocalization(self, event):
        """
        Handle EVT_CLIENT_GEOLOCATION_SUCCESS.
        """
        if self._announce and event.client.location and self.console.upTime() > 300:
            self.console.say(self.getMessage('client_connect', self.getMessageVariables(event.client)))

    def onPluginDisable(self, event):
        """
        Handle EVT_PLUGIN_DISABLED.
        """
        if event.data in self.requiresPlugins:
            self.warning('required plugin (%s) has been disabled: can\'t work without it', event.data)
            self.disable()

    ####################################################################################################################
    #                                                                                                                  #
    #   OTHER METHODS                                                                                                  #
    #                                                                                                                  #
    ####################################################################################################################

    @staticmethod
    def getMessageVariables(client):
        """
        Return a dictionary with message substitution variables
        :param client: The client whose geolocation information we need to display
        :return: dict
        """
        return {
            'id': client.id,
            'name': client.name,
            'connections': client.connections,
            'country': '--' if not client.location or not client.location.country else client.location.country,
            'city': '--' if not client.location or not client.location.city else client.location.city,
            'region': '--' if not client.location or not client.location.region else client.location.region,
            'cc': '--' if not client.location or not client.location.cc else client.location.cc,
            'rc': '--' if not client.location or not client.location.rc else client.location.rc,
            'isp': '--' if not client.location or not client.location.isp else client.location.isp,
        }

    def getLocationDistance(self, client, sclient):
        """
        Return the distance between 2 clients (in Km)
        """
        if not client.location or client.location.lat is None:
            self.debug('could not compute distance: %s has not enough geolocation data', client.name)
            return False
        
        if not sclient.location or sclient.location.lat is None:
            self.debug('could not compute distance: %s has not enough geolocation data', sclient.name)
            return False

        self.verbose('computing distance between %s and %s', client.name, sclient.name)

        lat1 = float(client.location.lat)
        lon1 = float(client.location.lon)
        lat2 = float(sclient.location.lat)
        lon2 = float(sclient.location.lon)
        
        ###
        # Haversine formula
        ###
        
        radius = 6371  # Earth radius in Km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(math.radians(lat1)) \
            * math.cos(math.radians(lat2)) * math.sin(dlon / 2) * math.sin(dlon / 2)
        b = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return round(abs(radius * b), 2)

    ####################################################################################################################
    #                                                                                                                  #
    #   COMMANDS                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def cmd_locate(self, data, client, cmd=None):
        """
        <client> - display geolocation info of the specified client
        """
        if not data: 
            client.message('^7missing data, try ^3!^7help locate')
        else:
            sclient = self._adminPlugin.findClientPrompt(data, client)
            if sclient:
                if not sclient.location:
                    cmd.sayLoudOrPM(client, self.getMessage('cmd_locate_failed', self.getMessageVariables(sclient)))
                else:
                    cmd.sayLoudOrPM(client, self.getMessage('cmd_locate', self.getMessageVariables(sclient)))

    def cmd_distance(self, data, client, cmd=None):
        """
        <client> - display the world distance between you and the given client
        """
        if not data: 
            client.message('^7missing data, try ^3!^7help distance')
        else:
            sclient = self._adminPlugin.findClientPrompt(data, client)
            if sclient:
                if sclient == client:
                    cmd.sayLoudOrPM(client, self.getMessage('cmd_distance_self', self.getMessageVariables(sclient)))
                else:
                    distance = self.getLocationDistance(client, sclient)
                    if not distance:
                        cmd.sayLoudOrPM(client, self.getMessage('cmd_distance_failed', self.getMessageVariables(sclient)))
                    else:
                        variables = self.getMessageVariables(sclient)
                        variables['distance'] = distance
                        cmd.sayLoudOrPM(client, self.getMessage('cmd_distance', variables))

    def cmd_isp(self, data, client, cmd=None):
        """
        <client> - display the isp the specified client is using
        """
        if not data:
            client.message('^7missing data, try ^3!^7help isp')
        else:
            sclient = self._adminPlugin.findClientPrompt(data, client)
            if sclient:
                if not sclient.location:
                    cmd.sayLoudOrPM(client, self.getMessage('cmd_isp_failed', self.getMessageVariables(sclient)))
                else:
                    cmd.sayLoudOrPM(client, self.getMessage('cmd_isp', self.getMessageVariables(sclient)))
