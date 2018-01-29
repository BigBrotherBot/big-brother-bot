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
import new

from mock import Mock
from mockito import when
from b3.events import Event
from b3.fake import FakeClient
from b3.plugins.spamcontrol import SpamcontrolPlugin
from tests.plugins.spamcontrol import SpamcontrolTestCase

class Test_game_specific_spam(SpamcontrolTestCase):

    def setUp(self):
        SpamcontrolTestCase.setUp(self)

        with open(b3.getAbsolutePath('@b3/conf/plugin_spamcontrol.ini')) as default_conf:
            self.init_plugin(default_conf.read())

        self.joe = FakeClient(self.console, name="Joe", exactName="Joe", guid="zaerezarezar", groupBits=1)
        self.joe.connects("1")

        # let's say our game has a new event : EVT_CLIENT_RADIO
        EVT_CLIENT_RADIO = self.console.Events.createEvent('EVT_CLIENT_RADIO', 'Event client radio')

        # teach the Spamcontrol plugin how to react on such events
        def onRadio(this, event):
            new_event = Event(type=event.type, client=event.client, target=event.target, data=event.data['text'])
            this.onChat(new_event)

        self.p.onRadio = new.instancemethod(onRadio, self.p, SpamcontrolPlugin)
        self.p.registerEvent('EVT_CLIENT_RADIO', self.p.onRadio)

        # patch joe to make him able to send radio messages
        def radios(me, text):
            me.console.queueEvent(Event(type=EVT_CLIENT_RADIO, client=me, data={'text': text}))
        self.joe.radios = new.instancemethod(radios, self.joe, FakeClient)

    def test_radio_spam(self):
        when(self.p).getTime().thenReturn(0)
        self.joe.warn = Mock()
        self.joe.says("doh 1")
        self.joe.radios("doh 2")
        self.joe.says("doh 3")
        self.joe.radios("doh 4")
        self.joe.says("doh 5")
        self.assertEqual(1, self.joe.warn.call_count)
