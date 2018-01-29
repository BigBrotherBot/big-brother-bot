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

from mock import Mock
from tests.plugins.location import LocationTestCase


class Test_events(LocationTestCase):

    def test_event_client_geolocation_success(self):
        # GIVEN
        self.mike.connects('1')
        self.console.say = Mock()
        # WHEN
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_GEOLOCATION_SUCCESS', client=self.mike))
        # THEN
        self.console.say.assert_called_with('^7Mike ^3from ^7Rome ^3(^7Italy^3) connected')