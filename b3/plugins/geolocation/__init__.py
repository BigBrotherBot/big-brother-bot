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
__version__ = '1.5'

import b3
import b3.clients
import b3.plugin
import b3.events
import threading

from .exceptions import GeolocalizationError
from .geolocators import FreeGeoIpGeolocator
from .geolocators import IpApiGeolocator
from .geolocators import MaxMindGeolocator
from .geolocators import TelizeGeolocator


class GeolocationPlugin(b3.plugin.Plugin):

    requiresConfigFile = False

    def __init__(self, console, config=None):
        """
        Build the plugin object.
        """
        b3.plugin.Plugin.__init__(self, console, config)
        # create geolocators instances
        self.info('creating geolocators object instances...')
        self._geolocators = [IpApiGeolocator(), TelizeGeolocator(), FreeGeoIpGeolocator()]
        try:
            # append this one separately since db may be missing
            self._geolocators.append(MaxMindGeolocator())
        except IOError, e:
            self.debug('MaxMind geolocation not available: %s' % e)

    def onStartup(self):
        """
        Initialize plugin.
        """
        # register events needed
        if self.console.isFrostbiteGame():
            self.registerEvent('EVT_PUNKBUSTER_NEW_CONNECTION', self.geolocate)
        else:
            self.registerEvent('EVT_CLIENT_AUTH', self.geolocate)

        self.registerEvent('EVT_CLIENT_UPDATE', self.geolocate)

        # create our custom events so other plugins can react when clients are geolocated
        self.console.createEvent('EVT_CLIENT_GEOLOCATION_SUCCESS', 'Event client geolocation success')
        self.console.createEvent('EVT_CLIENT_GEOLOCATION_FAILURE', 'Event client geolocation failure')

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENTS                                                                                                         #
    #                                                                                                                  #
    ####################################################################################################################

    def geolocate(self, event):
        """
        Handle EVT_CLIENT_AUTH and EVT_CLIENT_UPDATE.
        """
        def _threaded_geolocate(client):

            client.location = None

            for geotool in self._geolocators:

                try:
                    self.debug('retrieving geolocation data for %s <@%s>...', client.name, client.id)
                    client.location = geotool.getLocation(client)
                    self.debug('retrieved geolocation data for %s <@%s>: %r', client.name, client.id, client.location)
                    break # stop iterating if we collect valid data
                except GeolocalizationError, e:
                    self.warning('could not retrieve geolocation data %s <@%s>: %s', client.name, client.id, e)
                except Exception, e:
                    self.error('client %s <@%s> geolocation terminated unexpectedtly when using %s service: %s',
                               client.name, client.id, geotool.__class__.__name__, e)

            if client.location is not None:
                self.console.queueEvent(self.console.getEvent('EVT_CLIENT_GEOLOCATION_SUCCESS', client=client))
            else:
                self.console.queueEvent(self.console.getEvent('EVT_CLIENT_GEOLOCATION_FAILURE', client=client))

        # do not use hasattr or try except here: we'd better try to get geodata also when a previous attempt failed
        # and we ended up with NoneType object in client.location (so we have an attribute but it's not useful).
        # also make sure to launch geolocation only if we have a valid ip address.
        if not getattr(event.client, 'location', None) and event.client.ip:
            t = threading.Thread(target=_threaded_geolocate, args=(event.client,))
            t.daemon = True  # won't prevent B3 from exiting
            t.start()