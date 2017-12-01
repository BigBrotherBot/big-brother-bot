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

import time
import unittest2

from mock import Mock
from mockito import when, unstub
from b3.config import MainConfig
from b3.config import CfgConfigParser
from b3.plugins.admin import AdminPlugin
from b3.plugins.location import LocationPlugin
from textwrap import dedent
from tests import logging_disabled


LOCATION_MIKE = Mock()
LOCATION_MIKE.country = 'Italy'
LOCATION_MIKE.region = 'Lazio'
LOCATION_MIKE.city = 'Rome'
LOCATION_MIKE.cc = 'IT'
LOCATION_MIKE.rc = '07'
LOCATION_MIKE.isp = 'Fastweb'
LOCATION_MIKE.timezone = 'Europe/Rome'
LOCATION_MIKE.lat = 41.9
LOCATION_MIKE.lon = 12.4833
LOCATION_MIKE.zipcode = 00100

LOCATION_BILL = Mock()
LOCATION_BILL.country = 'United States'
LOCATION_BILL.region = 'California'
LOCATION_BILL.city = 'Mountain View'
LOCATION_BILL.cc = 'US'
LOCATION_BILL.rc = 'CA'
LOCATION_BILL.isp = 'Google Inc.'
LOCATION_BILL.timezone = 'America/Los_Angeles'
LOCATION_BILL.lat = 37.386
LOCATION_BILL.lon = -122.0838
LOCATION_BILL.zipcode = 94035


class LocationTestCase(unittest2.TestCase):

    def setUp(self):
        # create a FakeConsole parser
        parser_ini_conf = CfgConfigParser()
        parser_ini_conf.loadFromString(r'''''')
        self.parser_main_conf = MainConfig(parser_ini_conf)

        with logging_disabled():
            from b3.fake import FakeConsole
            self.console = FakeConsole(self.parser_main_conf)

        with logging_disabled():
            self.adminPlugin = AdminPlugin(self.console, '@b3/conf/plugin_admin.ini')
            self.adminPlugin._commands = {}
            self.adminPlugin.onStartup()

        # make sure the admin plugin obtained by other plugins is our admin plugin
        when(self.console).getPlugin('admin').thenReturn(self.adminPlugin)

        # simulate geolocation plugin registering events
        self.console.createEvent('EVT_CLIENT_GEOLOCATION_SUCCESS', 'Event client geolocation success')

        self.console.screen = Mock()
        self.console.time = time.time
        self.console.upTime = Mock(return_value=1000)
        self.console.cron.stop()


        self.conf = CfgConfigParser()
        self.conf.loadFromString(dedent(r"""
            [settings]
            announce: yes

            [messages]
            client_connect: ^7$name ^3from ^7$city ^3(^7$country^3) connected
            cmd_locate: ^7$name ^3is connected from ^7$city ^3(^7$country^3)
            cmd_locate_failed: ^7Could not locate ^1$name
            cmd_distance: ^7$name ^3is ^7$distance ^3km away from you
            cmd_distance_self: ^7Sorry, I'm not that smart...meh!
            cmd_distance_failed: ^7Could not compute distance with ^1$name
            cmd_isp: ^7$name ^3is using ^7$isp ^3as isp
            cmd_isp_failed: ^7Could not determine ^1$name ^7isp

            [commands]
            locate: user
            distance: user
            isp: mod
        """))

        self.p = LocationPlugin(self.console, self.conf)
        self.p.onLoadConfig()
        self.p.onStartup()

        with logging_disabled():
            from b3.fake import FakeClient

        self.mike = FakeClient(console=self.console, name="Mike", guid="MIKEGUID", groupBits=1)
        self.bill = FakeClient(console=self.console, name="Bill", guid="BILLGUID", groupBits=16)
        self.mike.location = LOCATION_MIKE
        self.bill.location = LOCATION_BILL

    def tearDown(self):
        unstub()