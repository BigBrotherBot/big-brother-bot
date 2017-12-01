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
from time import sleep

EVT_BAD_GUID = eventManager.createEvent('EVT_BAD_GUID', 'Bad guid detected')
EVT_1337_PORT = eventManager.createEvent('EVT_1337_PORT', '1337 port detected')


class HaxbusterurtPlugin():
    """
    dummy HaxbusterurtPlugin
    """
    def __init__(self, console):
        self.working = True


class Test_with_haxbusterurt(PluginTestCase):
    CONF = """\
[commands]
startserverdemo = 20

[haxbusterurt]
demo_duration: 2
"""

    def setUp(self):
        PluginTestCase.setUp(self)

        # create a fake haxbusterurt plugin
        self.haxbusterurt = HaxbusterurtPlugin(self.p.console)
        when(self.console).getPlugin('haxbusterurt').thenReturn(self.haxbusterurt)
        self.console.createEvent('EVT_BAD_GUID', 'Bad guid detected')
        self.console.createEvent('EVT_1337_PORT', '1337 port detected')

        self.p.onLoadConfig()
        self.p.onStartup()

    def tearDown(self):
        PluginTestCase.tearDown(self)

    def test_register_events(self):
        self.assertIn(self.console.getEventID('EVT_BAD_GUID'), self.p.events)
        self.assertIn(self.console.getEventID('EVT_1337_PORT'), self.p.events)

    def test_event_EVT_BAD_GUID(self):
        # GIVEN
        self.p._haxbusterurt_demo_duration = (1.0/60)/8 # will make the auto-stop timer end after 125ms
        self.p.start_recording_player = Mock()
        self.p.stop_recording_player = Mock()
        joe = FakeClient(console=self.console, name="Joe", guid="JOE_GUID")
        joe.connects("2")

        # WHEN the haxbusterurt plugin detects that Joe has a contestable guid
        self.console.queueEvent(Event(self.console.getEventID('EVT_BAD_GUID'), data=joe.guid, client=joe))

        # THEN
        sleep(.5) # sleep so the thread has time of doing its job
        self.p.start_recording_player.assert_called_with(joe, None)

        # THEN
        sleep(.5) # sleep so the thread has time of doing its job
        self.p.stop_recording_player.assert_called_with(joe)

    def test_event_EVT_1337_PORT(self):
        # GIVEN
        self.p._haxbusterurt_demo_duration = (1.0 / 60) / 8 # will make the auto-stop timer end after 125ms
        self.p.start_recording_player = Mock()
        self.p.stop_recording_player = Mock()
        joe = FakeClient(console=self.console, name="Joe", guid="JOE_GUID")
        joe.connects("2")

        # WHEN the haxbusterurt plugin detects that Joe has a contestable guid
        self.console.queueEvent(Event(self.console.getEventID('EVT_1337_PORT'), data=joe.guid, client=joe))

        # THEN
        sleep(.5) # sleep so the thread has time of doing its job
        self.p.start_recording_player.assert_called_with(joe, None)

        # WHEN
        sleep(.5) # sleep so the thread has time of doing its job
        self.p.stop_recording_player.assert_called_with(joe)

