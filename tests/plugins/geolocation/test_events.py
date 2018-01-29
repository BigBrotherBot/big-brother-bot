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

import sys
import time

from b3.plugins.geolocation.location import Location
from tests.plugins.geolocation import GeolocationTestCase


class Test_events(GeolocationTestCase):

    def test_event_client_geolocation_success(self):
        # GIVEN
        self.mike.ip = '8.8.8.8'
        # WHEN
        self.mike.connects("1")
        time.sleep(6)  # give a chance to the thread to do its job, so retrieve data and create the event
        # THEN
        self.assertEqual(True, hasattr(self.mike, 'location'))
        self.assertIsNotNone(self.mike.location)
        self.assertIsInstance(self.mike.location, Location)
        print >> sys.stderr, "IP: %s : %r" % (self.mike.ip, self.mike.location)

    def test_event_client_geolocation_failure(self):
        # GIVEN
        self.mike.ip = '--'
        # WHEN
        self.mike.connects("1")
        time.sleep(6)  # give a chance to the thread to do its job, so retrieve data and create the event
        # THEN
        self.assertIsNone(self.mike.location)
        print >> sys.stderr, "IP: %s : %r" % (self.mike.ip, self.mike.location)

    def test_event_client_geolocation_success_maxmind(self):
        # GIVEN
        self.p._geolocators.pop(0)
        self.p._geolocators.pop(0)
        self.p._geolocators.pop(0)
        self.mike.ip = '8.8.8.8'
        # WHEN
        self.mike.connects("1")
        time.sleep(2)  # give a chance to the thread to do its job, so retrieve data and create the event
        # THEN
        self.assertGreaterEqual(len(self.p._geolocators), 1)
        self.assertIsNotNone(self.mike.location)
        self.assertIsNone(self.mike.location.isp)
        print >> sys.stderr, "IP: %s : %r" % (self.mike.ip, self.mike.location)

    def test_event_client_geolocation_success_maxmind_using_event_client_update(self):
        # GIVEN
        self.p._geolocators.pop(0)
        self.p._geolocators.pop(0)
        self.p._geolocators.pop(0)
        self.mike.ip = ''
        self.mike.connects("1")
        # WHEN
        self.mike.ip = '8.8.8.8'
        self.mike.save(self.console)
        time.sleep(4)  # give a chance to the thread to do its job, so retrieve data and create the event
        # THEN
        self.assertGreaterEqual(len(self.p._geolocators), 1)
        self.assertEqual(True, hasattr(self.mike, 'location'))
        self.assertIsNotNone(self.mike.location)
        self.assertIsInstance(self.mike.location, Location)
        print >> sys.stderr, "IP: %s : %r" % (self.mike.ip, self.mike.location)
