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
from mockito import when
from time import sleep
from b3.fake import FakeClient
from tests.plugins.urtserversidedemo import PluginTestCase
from b3.events import eventManager, Event


EVT_FOLLOW_CONNECTED = eventManager.createEvent('EVT_FOLLOW_CONNECTED', 'EVT_FOLLOW_CONNECTED')


class FollowPlugin():
    """
    dummy FollowPlugin
    """
    def __init__(self, console):
        self.working = True


class Test_with_follow(PluginTestCase):
    CONF = """\
[commands]
startserverdemo = 20

[follow]
demo_duration: 2
"""

    def setUp(self):
        PluginTestCase.setUp(self)
        # create a fake follow plugin
        self.follow = FollowPlugin(self.p.console)
        when(self.console).getPlugin('follow').thenReturn(self.follow)
        self.p.onLoadConfig()
        self.p.onStartup()

    def tearDown(self):
        PluginTestCase.tearDown(self)

    def test_register_events(self):
        self.assertIn(EVT_FOLLOW_CONNECTED, self.p.events)

    def test_event_EVT_FOLLOW_CONNECTED(self):
        # GIVEN
        self.p._follow_demo_duration = (1.0/60)/8 # will make the auto-stop timer end after 125ms
        self.p.start_recording_player = Mock()
        self.p.stop_recording_player = Mock()
        joe = FakeClient(console=self.console, name="Joe", guid="JOE_GUID")
        joe.connects("2")

        self.console.queueEvent(Event(EVT_FOLLOW_CONNECTED, data=None, client=joe))

        # THEN
        self.p.start_recording_player.assert_called_with(joe, None)

        # WHEN
        sleep(.2)
        # THEN
        self.p.stop_recording_player.assert_called_with(joe)

