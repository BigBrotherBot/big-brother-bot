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

import unicodedata

class Location(object):

    def __init__(self, country=None, region=None, city=None, cc=None, rc=None, isp=None, lat=None, lon=None, timezone=None, zipcode=None):
        """
        :param country: The country name
        :param region: The regione name
        :param city: The city name
        :param cc: The country code
        :param rc: The region code
        :param isp: The ISP name
        :param lat: The latitude value
        :param lon: The longitude value
        :param timezone: The timezone value (long string)
        :param zipcode; The zipcode value
        """
        self.country = country or None
        self.region = region or None
        self.city = city or None
        self.cc = cc or None
        self.rc = rc or None
        self.isp = isp or None
        self.lat = lat or None
        self.lon = lon or None
        self.timezone = timezone or None
        self.zipcode = zipcode or None

    def __setattr__(self, key, value):
        """
        Proxy which cleanup attribute value before assignment,
        :param key: The attribute name
        :param value: The attribute value
        """
        if value:
            value = unicodedata.normalize('NFKD', unicode(value)).encode('ascii','ignore').strip()
        self.__dict__[key] = value

    def __repr__(self):
        """
        Object representation,
        :return: string
        """
        v = ['%s=%s' % (x, getattr(self, x)) for x in dir(self) if not x.startswith('__') and not callable(getattr(self, x))]
        return 'Location<%s>' % ', '.join(v)