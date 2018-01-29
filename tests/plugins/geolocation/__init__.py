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
import logging

from mock import Mock
from mockito import unstub
from b3.fake import FakeClient
from b3.plugins.geolocation import GeolocationPlugin
from tests import B3TestCase


class GeolocationTestCase(B3TestCase):

    def setUp(self):
        self.log = logging.getLogger('output')
        self.log.propagate = False

        B3TestCase.setUp(self)

        self.console.screen = Mock()
        self.console.time = time.time
        self.console.upTime = Mock(return_value=3)

        self.p = GeolocationPlugin(self.console)
        self.p.onLoadConfig()
        self.p.onStartup()

        self.log.propagate = True

        self.mike = FakeClient(console=self.console, name="Mike", guid="MIKEGUID", groupBits=1)

    def tearDown(self):
        B3TestCase.tearDown(self)
        unstub()