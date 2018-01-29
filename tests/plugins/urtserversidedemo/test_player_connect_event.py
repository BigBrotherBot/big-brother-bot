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
from b3.events import Event
from tests.plugins.urtserversidedemo import PluginTestCase
from b3.fake import FakeClient
from time import sleep


class Test_player_connect_event(PluginTestCase):
    CONF = """\
[commands]
startserverdemo = 20
stopserverdemo = 20
"""
    def setUp(self):
        PluginTestCase.setUp(self)
        self.p.onStartup()

        self.joe = FakeClient(self.console, name="Joe", guid="01230123012301230123", groupBits=1)
        self.joe.clearMessageHistory()

        self.p.start_recording_player = Mock(return_value="startserverdemo: recording ")
        self.p.start_recording_player.reset_mock()

    def test_auto_start_demo_of_connecting_players(self):
        # GIVEN
        self.p._recording_all_players = True

        # WHEN
        self.joe.connects("2")
        self.console.queueEvent(Event(self.console.getEventID('EVT_CLIENT_JOIN'), self.joe, self.joe))

        # THEN
        sleep(.5) # sleep so the thread has time of doing its job
        self.assertTrue(self.p.start_recording_player.called)
        self.p.start_recording_player.assert_called_with(self.joe, None)

    def test_do_not_auto_start_demo_of_connecting_players(self):
        # GIVEN
        self.p._recording_all_players = False

        # WHEN
        self.joe.connects("2")

        # THEN
        sleep(.5) # sleep so the thread has time of doing its job
        self.assertFalse(self.p.start_recording_player.called)

