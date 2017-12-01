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

import b3
import b3.clients
import re
import os
import os.path
import requests

from .exceptions import GeolocalizationError
from .lib.geoip import GeoIP
from .location import Location


class Geolocator(object):

    _timeout = 5

    def __init__(self, *args, **kwargs):
        """
        Object constructor.
        """
        pass

    @staticmethod
    def _getIp(data):
        """
        Extract ip information from the given data
        :param data: The data from where to extract the ip address
        :raise TypeError: if we receive an invalid input data
        :return: string
        """
        if isinstance(data, basestring):
            if not re.match(r'''^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}''', str(data)):
                raise GeolocalizationError('invalid ip address string supplied: %s' % data)
        elif isinstance(data, b3.clients.Client):
            client = data
            if not client.ip:
                raise GeolocalizationError('b3.clients.Client object instance has not ip attribute set')
            elif not re.match(r'''^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}''', client.ip):
                raise GeolocalizationError('b3.clients.Client object instance has an invalid ip address string: %s' % client.ip)
        else:
            raise GeolocalizationError('invalid argument supplied: %s' % type(data).__name__)


        return data if isinstance(data, basestring) else data.ip

    def getLocation(self, data):
        """
        Retrieve location data
        :param data: A B3 client object or an IP string
        :raise RequestException: When we are not able to retrieve location information
        :return: A Location object initialized with location data
        """
        raise NotImplementedError


class IpApiGeolocator(Geolocator):

    _url = 'http://ip-api.com/json/%s'

    def getLocation(self, data):
        """
        Retrieve location data
        :param data: A B3 client object or an IP string
        :raise GeolocalizationError: When we are not able to retrieve location information
        :return: A Location object initialized with location data
        """
        ip = self._getIp(data)
        rt = requests.get(self._url % ip, timeout=self._timeout).json()

        if rt['status'] == 'fail':
            raise GeolocalizationError('invalid data returned by the api: %r' % rt)

        return Location(country=rt.get('country', None), region=rt.get('regionName', None), city=rt.get('city', None),
                        cc=rt.get('countryCode', None), rc=rt.get('regionCode', None), isp=rt.get('isp', None),
                        lat=rt.get('lat', None), lon=rt.get('lon', None), timezone=rt.get('timezone', None),
                        zipcode=rt.get('zip', None))


class TelizeGeolocator(Geolocator):

    _url = 'http://www.telize.com/geoip/%s'

    def getLocation(self, data):
        """
        Retrieve location data
        :param data: A B3 client object or an IP string
        :raise GeolocalizationError: When we are not able to retrieve location information
        :return: A Location object initialized with location data
        """
        ip = self._getIp(data)
        rt = requests.get(self._url % ip, timeout=self._timeout).json()
        if 'code' in rt and int(rt['code']) == 401:
            raise GeolocalizationError('input string is not a valid ip address: %s' % ip)
        if 'country' not in rt:
            raise GeolocalizationError('could not establish in which country is ip %s' % ip)

        return Location(country=rt.get('country', None), region=rt.get('region', None), city=rt.get('city', None),
                        cc=rt.get('country_code', None), rc=rt.get('region_code', None), isp=rt.get('isp', None),
                        lat=rt.get('latitude', None), lon=rt.get('longitude', None), timezone=rt.get('timezone', None),
                        zipcode=rt.get('postal_code', None))


class FreeGeoIpGeolocator(Geolocator):

    _url = 'https://freegeoip.net/json/%s'

    def getLocation(self, data):
        """
        Retrieve location data
        :param data: A B3 client object or an IP string
        :raise GeolocalizationError: When we are not able to retrieve location information
        :return: A Location object initialized with location data
        """
        ip = self._getIp(data)
        rq = requests.get(self._url % ip, timeout=self._timeout)
        if rq.text.strip() == '404 page not found':
            raise GeolocalizationError('input string is not a valid ip address: %s' % ip)

        rt = rq.json()

        if rt['status'] == 'fail':
            raise GeolocalizationError('invalid data returned by the api: %r' % rt)

        return Location(country=rt.get('country_name', None), region=rt.get('region_name', None), city=rt.get('city', None),
                        cc=rt.get('country_code', None), rc=rt.get('region_code', None), lat=rt.get('latitude', None),
                        lon=rt.get('longitude', None), timezone=rt.get('time_zone', None),
                        zipcode=rt.get('zip_code', None))


class MaxMindGeolocator(Geolocator):

    _path = None
    _geoip = None

    def __init__(self, *args, **kwargs):
        """
        Object constructor.
        :raise IOError: if the database is not available
        """
        super(MaxMindGeolocator, self).__init__(*args, **kwargs)
        # prefer plugin relative path
        self._path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib', 'geoip', 'db', 'GeoIP.dat')
        if not os.path.isfile(self._path):
            # search system wide (using system path according to installation
            # instructions: http://dev.maxmind.com/geoip/legacy/install/country/
            if not os.path.isfile('/usr/local/share/GeoIP/GeoIP.dat'):
                raise IOError('no MaxMind GeoIP.dat database available: put the database file in %s' % self._path)
            self._path = '/usr/local/share/GeoIP/GeoIP.dat'
        self.geoip = GeoIP.open(self._path, GeoIP.GEOIP_STANDARD)

    def getLocation(self, data):
        """
        Retrieve location data
        :param data: A B3 client object or an IP string
        :raise GeolocalizationError: When we are not able to retrieve location information
        :return: A Location object initialized with location data
        """
        country_id = self.geoip.id_by_addr(self._getIp(data))
        return Location(country=GeoIP.id_to_country_name(country_id), cc=GeoIP.id_to_country_code(country_id))