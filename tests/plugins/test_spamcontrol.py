#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2012 Courgette
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
import logging
import new
import os
from mockito import when
from mock import Mock, call, patch
import unittest2 as unittest
from b3.events import Event
from b3.fake import FakeClient
from b3.plugins.spamcontrol import SpamcontrolPlugin
from tests import B3TestCase

from b3 import __file__ as b3_module__file__
from b3.config import XmlConfigParser


SPAMCONTROM_CONFIG_FILE = os.path.normpath(os.path.join(os.path.dirname(b3_module__file__), "conf/plugin_spamcontrol.xml"))

class SpamcontrolTestCase(B3TestCase):
    """ Ease testcases that need an working B3 console and need to control the Spamcontrol plugin config """

    def setUp(self):
        self.timer_patcher = patch('threading.Timer')
        self.timer_patcher.start()

        self.log = logging.getLogger('output')
        self.log.propagate = False

        B3TestCase.setUp(self)
        self.console.startup()
        self.log.propagate = True

    def tearDown(self):
        B3TestCase.tearDown(self)
        self.timer_patcher.stop()

    def init_plugin(self, config_content):
        self.conf = XmlConfigParser()
        self.conf.setXml(config_content)
        self.p = SpamcontrolPlugin(self.console, self.conf)

        self.log.setLevel(logging.DEBUG)
        self.log.info("============================= Spamcontrol plugin: loading config ============================")
        self.p.onLoadConfig()
        self.log.info("============================= Spamcontrol plugin: starting  =================================")
        self.p.onStartup()



class Test_config(SpamcontrolTestCase):
    """ test different config are correctly loaded """
    default_max_spamins = 10
    default_mod_level = 20
    default_falloff_rate = 6.5

    @unittest.skipUnless(os.path.exists(SPAMCONTROM_CONFIG_FILE), reason="cannot get default plugin config file at %s" % SPAMCONTROM_CONFIG_FILE)
    def test_default_conf(self):
        with open(SPAMCONTROM_CONFIG_FILE) as default_conf:
            self.init_plugin(default_conf.read())
        self.assertEqual(self.default_max_spamins, self.p._maxSpamins)
        self.assertEqual(self.default_mod_level, self.p._modLevel)
        self.assertEqual(self.default_falloff_rate, self.p._falloffRate)


    def test_emtpy_conf(self):
        self.init_plugin(r"""<configuration plugin="spamcontrol"/>""")
        self.assertEqual(self.default_max_spamins, self.p._maxSpamins)
        self.assertEqual(self.default_mod_level, self.p._modLevel)
        self.assertEqual(self.default_falloff_rate, self.p._falloffRate)


    def test_max_spamins_empty(self):
        self.init_plugin(r"""
            <configuration plugin="spamcontrol">
                <settings name="settings">
                    <set name="max_spamins"></set>
                </settings>
            </configuration>
        """)
        self.assertEqual(self.default_max_spamins, self.p._maxSpamins)

    def test_max_spamins_NaN(self):
        self.init_plugin(r"""
            <configuration plugin="spamcontrol">
                <settings name="settings">
		            <set name="max_spamins">fo0</set>
                </settings>
            </configuration>
        """)
        self.assertEqual(self.default_max_spamins, self.p._maxSpamins)

    def test_max_spamins_negative(self):
        self.init_plugin(r"""
            <configuration plugin="spamcontrol">
                <settings name="settings">
		            <set name="max_spamins">-15</set>
                </settings>
            </configuration>
        """)
        self.assertEqual(0, self.p._maxSpamins)


    def test_mod_level_empty(self):
        self.init_plugin(r"""
            <configuration plugin="spamcontrol">
                <settings name="settings">
                    <set name="mod_level"></set>
                </settings>
            </configuration>
        """)
        self.assertEqual(self.default_mod_level, self.p._modLevel)

    def test_mod_level_NaN(self):
        self.init_plugin(r"""
            <configuration plugin="spamcontrol">
                <settings name="settings">
                    <set name="mod_level">fo0</set>
                </settings>
            </configuration>
        """)
        self.assertEqual(self.default_mod_level, self.p._modLevel)

    def test_mod_level_nominal(self):
        self.init_plugin(r"""
            <configuration plugin="spamcontrol">
                <settings name="settings">
                    <set name="mod_level">60</set>
                </settings>
            </configuration>
        """)
        self.assertEqual(60, self.p._modLevel)

    def test_mod_level_by_group_keyword(self):
        self.init_plugin(r"""
            <configuration plugin="spamcontrol">
                <settings name="settings">
                    <set name="mod_level">senioradmin</set>
                </settings>
            </configuration>
        """)
        self.assertEqual(80, self.p._modLevel)



@unittest.skipUnless(os.path.exists(SPAMCONTROM_CONFIG_FILE), reason="cannot get default plugin config file at %s" % SPAMCONTROM_CONFIG_FILE)
class Test_plugin(SpamcontrolTestCase):

    def setUp(self):
        SpamcontrolTestCase.setUp(self)

        with open(SPAMCONTROM_CONFIG_FILE) as default_conf:
            self.init_plugin(default_conf.read())

        self.joe = FakeClient(self.console, name="Joe", exactName="Joe", guid="zaerezarezar", groupBits=1)
        self.joe.connects("1")

        self.original_admin_plugin = self.p._adminPlugin

    def assertSpaminsPoints(self, client, points):
        actual = client.var(self.p, 'spamins', 0).value
        self.assertEqual(points, actual, "expecting %s to have %s spamins points" % (client.name, points))


    def test_say(self):
        when(self.p).getTime().thenReturn(0).thenReturn(1).thenReturn(20).thenReturn(120)

        self.assertSpaminsPoints(self.joe, 0)

        self.joe.says("doh") # 0s
        self.assertSpaminsPoints(self.joe, 2)

        self.joe.says("foo") # 1s
        self.assertSpaminsPoints(self.joe, 4)

        self.joe.says("bar") # 20s
        self.assertSpaminsPoints(self.joe, 3)

        self.joe.says("hi") # 120s
        self.assertSpaminsPoints(self.joe, 0)


    def test_cmd_spamins(self):
        when(self.p._adminPlugin).findClientPrompt("joe", self.joe).thenReturn(self.joe)
        when(self.p).getTime().thenReturn(0).thenReturn(3).thenReturn(4).thenReturn(4).thenReturn(500)
        self.joe.says("doh") # 0s
        self.joe.says("doh") # 3s
        self.joe.says("doh") # 4s

        cmd_mock = Mock()
        self.p.cmd_spamins(data="joe", client=self.joe, cmd=cmd_mock)
        cmd_mock.sayLoudOrPM.assert_has_calls([call(self.joe, 'Joe^7 ^7currently has 9 spamins, peak was 9')]) # 10s

        cmd_mock = Mock()
        self.p.cmd_spamins(data="joe", client=self.joe, cmd=cmd_mock)
        cmd_mock.sayLoudOrPM.assert_has_calls([call(self.joe, 'Joe^7 ^7currently has 0 spamins, peak was 9')]) # 10s


    def test_cmd_spamins_lowercase(self):
        # GIVEN
        mike = FakeClient(self.console, name="Mike")
        mike.connects("3")
        cmd_mock = Mock()

        # WHEN
        when(self.p._adminPlugin).findClientPrompt("mike", self.joe).thenReturn(mike)
        self.p.cmd_spamins(data="mike", client=self.joe, cmd=cmd_mock)

        # THEN
        cmd_mock.sayLoudOrPM.assert_has_calls([call(self.joe, 'Mike^7 ^7currently has 0 spamins, peak was 0')])


    def test_cmd_spamins_uppercase(self):
        # GIVEN
        mike = FakeClient(self.console, name="Mike")
        mike.connects("3")
        cmd_mock = Mock()

        # WHEN
        when(self.p._adminPlugin).findClientPrompt("MIKE", self.joe).thenReturn(mike)
        self.p.cmd_spamins(data="MIKE", client=self.joe, cmd=cmd_mock)

        # THEN
        cmd_mock.sayLoudOrPM.assert_has_calls([call(self.joe, 'Mike^7 ^7currently has 0 spamins, peak was 0')])


    def test_cmd_spamins_unknown_player(self):
        # GIVEN
        cmd_mock = Mock()

        # WHEN
        when(self.p._adminPlugin).findClientPrompt("mike", self.joe).thenReturn(None)
        self.p.cmd_spamins(data="mike", client=self.joe, cmd=cmd_mock)

        # THEN
        cmd_mock.sayLoudOrPM.assert_has_calls([])


    def test_cmd_spamins_no_argument(self):
        # GIVEN
        cmd_mock = Mock()

        # WHEN
        self.p.cmd_spamins(data=None, client=self.joe, cmd=cmd_mock)

        # THEN
        cmd_mock.sayLoudOrPM.assert_has_calls([call(self.joe, 'Joe^7 ^7currently has 0 spamins, peak was 0')])



    def test_joe_gets_warned(self):
        when(self.p).getTime().thenReturn(0)
        self.joe.warn = Mock()
        self.joe.says("doh 1")
        self.joe.says("doh 2")
        self.joe.says("doh 3")
        self.joe.says("doh 4")
        self.joe.says("doh 5")
        self.assertEqual(1, self.joe.warn.call_count)




class Test_game_specific_spam(SpamcontrolTestCase):

    def setUp(self):
        SpamcontrolTestCase.setUp(self)

        with open(SPAMCONTROM_CONFIG_FILE) as default_conf:
            self.init_plugin(default_conf.read())

        self.joe = FakeClient(self.console, name="Joe", exactName="Joe", guid="zaerezarezar", groupBits=1)
        self.joe.connects("1")

        # let's say our game has a new event : EVT_CLIENT_RADIO
        EVT_CLIENT_RADIO = self.console.Events.createEvent('EVT_CLIENT_RADIO', 'Event client radio')

        # teach the Spamcontrol plugin how to react on such events
        def onRadio(event):
            new_event = Event(type=event.type, client=event.client, target=event.target, data=event.data['text'])
            self.p.onChat(new_event)
        self.p.eventHanlders[EVT_CLIENT_RADIO] = onRadio
        self.p.registerEvent(EVT_CLIENT_RADIO)

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
