#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2013 Courgette
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
import os

from mock import Mock, patch, call
import unittest2 as unittest
from mockito import when

import b3
from b3.plugins.admin import AdminPlugin
from b3.plugins.welcome import WelcomePlugin, F_FIRST, F_NEWB, F_ANNOUNCE_USER, F_ANNOUNCE_FIRST, F_USER, \
    F_CUSTOM_GREETING
from b3.config import XmlConfigParser
from b3.fake import FakeClient

from tests import B3TestCase, logging_disabled
from b3 import __file__ as b3_module__file__


ADMIN_CONFIG_FILE = os.path.normpath(os.path.join(os.path.dirname(b3_module__file__), "conf/plugin_admin.ini"))
WELCOME_CONFIG_FILE = os.path.normpath(os.path.join(os.path.dirname(b3_module__file__), "conf/plugin_welcome.xml"))


@unittest.skipUnless(os.path.exists(ADMIN_CONFIG_FILE), reason="cannot get default plugin config file at %s" %
                                                               ADMIN_CONFIG_FILE)
class Welcome_functional_test(B3TestCase):

    def setUp(self):
        B3TestCase.setUp(self)

        with logging_disabled():
            self.adminPlugin = AdminPlugin(self.console, ADMIN_CONFIG_FILE)
            when(self.console).getPlugin("admin").thenReturn(self.adminPlugin)
            self.adminPlugin.onLoadConfig()
            self.adminPlugin.onStartup()

            self.conf = XmlConfigParser()
            self.p = WelcomePlugin(self.console, self.conf)

            self.joe = FakeClient(self.console, name="Joe", guid="joeguid", groupBits=1, team=b3.TEAM_RED)
            self.mike = FakeClient(self.console, name="Mike", guid="mikeguid", groupBits=1, team=b3.TEAM_RED)
            self.bill = FakeClient(self.console, name="Bill", guid="billguid", groupBits=1, team=b3.TEAM_RED)
            self.superadmin = FakeClient(self.console, name="SuperAdmin", guid="superadminguid", groupBits=128,
                                         team=b3.TEAM_RED)

    def load_config(self, config_content=None):
        """
        load the given config content, or the default config if config_content is None.
        """
        if config_content is None:
            if not os.path.exists(WELCOME_CONFIG_FILE):
                self.skipTest("cannot get default plugin config file at %s" % WELCOME_CONFIG_FILE)
            else:
                self.conf.load(WELCOME_CONFIG_FILE)
        else:
            self.conf.setXml(config_content)
        self.p.onLoadConfig()
        self.p.onStartup()


@unittest.skipUnless(os.path.exists(WELCOME_CONFIG_FILE), reason="cannot get default plugin config file at %s" %
                                                                 WELCOME_CONFIG_FILE)
class Test_default_config(Welcome_functional_test):

    def setUp(self):
        Welcome_functional_test.setUp(self)
        self.load_config()

    def test_commands_greeting(self):
        self.assertEqual(20, self.p._cmd_greeting_minlevel)

    def test_settings_flags(self):
        self.assertEqual(63, self.p._welcomeFlags)

    def test_settings_newb_connections(self):
        self.assertEqual(15, self.p._newbConnections)

    def test_settings_delay(self):
        self.assertEqual(30, self.p._welcomeDelay)

    def test_settings_min_gap(self):
        self.assertEqual(3600, self.p._min_gap)

    def test_messages_user(self):
        self.assertEqual("^7[^2Authed^7] Welcome back $name ^7[^3@$id^7], last visit ^3$lastVisit^7, you're a ^2$group^7, played $connections times",
                         self.conf.get("messages", 'user'))

    def test_messages_newb(self):
        self.assertEqual('^7[^2Authed^7] Welcome back $name ^7[^3@$id^7], last visit ^3$lastVisit. Type !register in chat to register. Type !help for help',
                         self.conf.get("messages", 'newb'))

    def test_messages_announce_user(self):
        self.assertEqual('^7Everyone welcome back $name^7, player number ^3#$id^7, to the server, played $connections times',
                         self.conf.get("messages", 'announce_user'))

    def test_messages_first(self):
        self.assertEqual('^7Welcome $name^7, this must be your first visit, you are player ^3#$id. Type !help for help',
                         self.conf.get("messages", 'first'))

    def test_messages_announce_first(self):
        self.assertEqual('^7Everyone welcome $name^7, player number ^3#$id^7, to the server',
                         self.conf.get("messages", 'announce_first'))

    def test_messages_greeting(self):
        self.assertEqual('^7$name^7 joined: $greeting',
                         self.conf.get("messages", 'greeting'))

    def test_messages_greeting_empty(self):
        self.assertEqual('^7You have no greeting set',
                         self.conf.get("messages", 'greeting_empty'))

    def test_messages_greeting_yours(self):
        self.assertEqual('^7Your greeting is %s',
                         self.conf.get("messages", 'greeting_yours'))

    def test_messages_greeting_bad(self):
        self.assertEqual('^7Greeting is not formatted properly: %s',
                         self.conf.get("messages", 'greeting_bad'))

    def test_messages_greeting_changed(self):
        self.assertEqual('^7Greeting changed to: %s',
                         self.conf.get("messages", 'greeting_changed'))

    def test_messages_greeting_cleared(self):
        self.assertEqual('^7Greeting cleared',
                         self.conf.get("messages", 'greeting_cleared'))


class Test_config_flags(Welcome_functional_test):

    def test_flags_nominal(self):
        self.load_config("""<configuration>
            <settings name="settings">
                <set name="flags">34</set>
            </settings>
        </configuration>""")
        self.assertEqual(34, self.p._welcomeFlags)

    def test_flags_empty(self):
        self.load_config("""<configuration>
            <settings name="settings">
                <set name="flags"></set>
            </settings>
        </configuration>""")
        self.assertEqual(63, self.p._welcomeFlags)

    def test_flags_junk(self):
        self.load_config("""<configuration>
            <settings name="settings">
                <set name="flags">f00</set>
            </settings>
        </configuration>""")
        self.assertEqual(63, self.p._welcomeFlags)

    def test_settings_no_flags(self):
        self.load_config("""<configuration>
            <settings name="settings">
            </settings>
        </configuration>""")
        self.assertEqual(63, self.p._welcomeFlags)

    def test_welcome_first(self):
        self.p._welcomeFlags = 0
        self.load_config("""<configuration>
            <settings name="settings">
                <set name="welcome_first">yes</set>
            </settings>
        </configuration>""")
        self.assertTrue(F_FIRST & self.p._welcomeFlags)
        self.load_config("""<configuration>
            <settings name="settings">
                <set name="welcome_first">no</set>
            </settings>
        </configuration>""")
        self.assertFalse(F_FIRST & self.p._welcomeFlags)

    def test_welcome_newb(self):
        self.p._welcomeFlags = 0
        self.load_config("""<configuration>
            <settings name="settings">
                <set name="welcome_newb">yes</set>
            </settings>
        </configuration>""")
        self.assertTrue(F_NEWB & self.p._welcomeFlags)
        self.load_config("""<configuration>
            <settings name="settings">
                <set name="welcome_newb">no</set>
            </settings>
        </configuration>""")
        self.assertFalse(F_NEWB & self.p._welcomeFlags)

    def test_welcome_user(self):
        self.p._welcomeFlags = 0
        self.load_config("""<configuration>
            <settings name="settings">
                <set name="welcome_user">yes</set>
            </settings>
        </configuration>""")
        self.assertTrue(F_USER & self.p._welcomeFlags)
        self.load_config("""<configuration>
            <settings name="settings">
                <set name="welcome_user">no</set>
            </settings>
        </configuration>""")
        self.assertFalse(F_USER & self.p._welcomeFlags)

    def test_announce_first(self):
        self.p._welcomeFlags = 0
        self.load_config("""<configuration>
            <settings name="settings">
                <set name="announce_first">yes</set>
            </settings>
        </configuration>""")
        self.assertTrue(F_ANNOUNCE_FIRST & self.p._welcomeFlags)
        self.load_config("""<configuration>
            <settings name="settings">
                <set name="announce_first">no</set>
            </settings>
        </configuration>""")
        self.assertFalse(F_ANNOUNCE_FIRST & self.p._welcomeFlags)

    def test_announce_user(self):
        self.p._welcomeFlags = 0
        self.load_config("""<configuration>
            <settings name="settings">
                <set name="announce_user">yes</set>
            </settings>
        </configuration>""")
        self.assertTrue(F_ANNOUNCE_USER & self.p._welcomeFlags)
        self.load_config("""<configuration>
            <settings name="settings">
                <set name="announce_user">no</set>
            </settings>
        </configuration>""")
        self.assertFalse(F_ANNOUNCE_USER & self.p._welcomeFlags)

    def test_show_user_greeting(self):
        self.p._welcomeFlags = 0
        self.load_config("""<configuration>
            <settings name="settings">
                <set name="show_user_greeting">yes</set>
            </settings>
        </configuration>""")
        self.assertTrue(F_CUSTOM_GREETING & self.p._welcomeFlags)
        self.load_config("""<configuration>
            <settings name="settings">
                <set name="show_user_greeting">no</set>
            </settings>
        </configuration>""")
        self.assertFalse(F_CUSTOM_GREETING & self.p._welcomeFlags)

    def test_nonce_set(self):
        self.p._welcomeFlags = 0
        self.load_config("""<configuration>
            <settings name="settings">
                <set name="welcome_first">no</set>
                <set name="welcome_newb">no</set>
                <set name="welcome_user">no</set>
                <set name="announce_first">no</set>
                <set name="announce_user">no</set>
                <set name="show_user_greeting">no</set>
            </settings>
        </configuration>""")
        self.assertEqual(0, self.p._welcomeFlags)

    def test_all_set(self):
        self.p._welcomeFlags = 0
        self.load_config("""<configuration>
            <settings name="settings">
                <set name="welcome_first">yes</set>
                <set name="welcome_newb">yes</set>
                <set name="welcome_user">yes</set>
                <set name="announce_first">yes</set>
                <set name="announce_user">yes</set>
                <set name="show_user_greeting">yes</set>
            </settings>
        </configuration>""")
        self.assertEqual(F_FIRST | F_NEWB | F_USER | F_ANNOUNCE_FIRST | F_ANNOUNCE_USER | F_CUSTOM_GREETING,
                         self.p._welcomeFlags)

    def test_partly_set(self):
        self.p._welcomeFlags = 0
        self.load_config("""<configuration>
            <settings name="settings">
                <set name="welcome_first">yes</set>
                <set name="welcome_newb">no</set>
                <set name="welcome_user">yes</set>
                <set name="announce_first">yes</set>
                <set name="announce_user">no</set>
                <set name="show_user_greeting">yes</set>
            </settings>
        </configuration>""")
        self.assertEqual(F_FIRST | F_USER | F_ANNOUNCE_FIRST | F_CUSTOM_GREETING,
                         self.p._welcomeFlags)

    def test_mix_old_style_and_new_style(self):
        """
        Old style config uses settings/flags.
        New style uses welcome_first, welcome_newb, etc.
        When both styles are found, ignore old style.
        Also a missing new style option is assumed to be 'yes'
        """
        self.p._welcomeFlags = 0
        self.load_config("""<configuration>
            <settings name="settings">
                <set name="flags">54</set>
                <!-- <set name="welcome_first">no</set> -->
                <set name="welcome_newb">no</set>
                <set name="welcome_user">no</set>
                <set name="announce_first">no</set>
                <set name="announce_user">yes</set>
                <set name="show_user_greeting">no</set>
            </settings>
        </configuration>""")
        self.assertEqual(F_FIRST | F_ANNOUNCE_USER, self.p._welcomeFlags)


class Test_config(Welcome_functional_test):

    def test_commands_greeting(self):
        # nominal
        self.load_config("""<configuration>
            <settings name="commands">
                <set name="greeting">60</set>
            </settings>
        </configuration>""")
        self.assertEqual(60, self.p._cmd_greeting_minlevel)
        # empty
        self.load_config("""<configuration>
            <settings name="commands">
                <set name="greeting"></set>
            </settings>
        </configuration>""")
        self.assertEqual(20, self.p._cmd_greeting_minlevel)
        # junk
        self.load_config("""<configuration>
            <settings name="commands">
                <set name="greeting">f00</set>
            </settings>
        </configuration>""")
        self.assertEqual(20, self.p._cmd_greeting_minlevel)
    def test_settings_newb_connections(self):
        # nominal
        self.load_config("""<configuration>
            <settings name="settings">
                <set name="newb_connections">27</set>
            </settings>
        </configuration>""")
        self.assertEqual(27, self.p._newbConnections)
        # empty
        self.load_config("""<configuration>
            <settings name="settings">
                <set name="newb_connections"></set>
            </settings>
        </configuration>""")
        self.assertEqual(15, self.p._newbConnections)
        # junk
        self.load_config("""<configuration>
            <settings name="settings">
                <set name="newb_connections">f00</set>
            </settings>
        </configuration>""")
        self.assertEqual(15, self.p._newbConnections)

    def test_settings_delay(self):
        # nominal
        self.load_config("""<configuration>
            <settings name="settings">
                <set name="delay">15</set>
            </settings>
        </configuration>""")
        self.assertEqual(15, self.p._welcomeDelay)
        # empty
        self.load_config("""<configuration>
            <settings name="settings">
                <set name="delay"></set>
            </settings>
        </configuration>""")
        self.assertEqual(30, self.p._welcomeDelay)
        # junk
        self.load_config("""<configuration>
            <settings name="settings">
                <set name="delay">f00</set>
            </settings>
        </configuration>""")
        self.assertEqual(30, self.p._welcomeDelay)
        # too low
        self.load_config("""<configuration>
            <settings name="settings">
                <set name="delay">5</set>
            </settings>
        </configuration>""")
        self.assertEqual(30, self.p._welcomeDelay)
        # too high
        self.load_config("""<configuration>
            <settings name="settings">
                <set name="delay">500</set>
            </settings>
        </configuration>""")
        self.assertEqual(30, self.p._welcomeDelay)

    def test_settings_min_gap(self):
        # nominal
        self.load_config("""<configuration>
            <settings name="settings">
                <set name="min_gap">540</set>
            </settings>
        </configuration>""")
        self.assertEqual(540, self.p._min_gap)
        # empty
        self.load_config("""<configuration>
            <settings name="settings">
                <set name="min_gap"></set>
            </settings>
        </configuration>""")
        self.assertEqual(3600, self.p._min_gap)
        # junk
        self.load_config("""<configuration>
            <settings name="settings">
                <set name="min_gap">f00</set>
            </settings>
        </configuration>""")
        self.assertEqual(3600, self.p._min_gap)
        # too low
        self.load_config("""<configuration>
            <settings name="settings">
                <set name="min_gap">-15</set>
            </settings>
        </configuration>""")
        self.assertEqual(0, self.p._min_gap)


class Test_cmd_greeting(Welcome_functional_test):

    def setUp(self):
        Welcome_functional_test.setUp(self)
        self.load_config()
        # disabled event handling (spawns threads and is of no use for that test)
        self.p.onEvent = lambda *args, **kwargs: None
        self.superadmin.connects("0")
        self.superadmin._connections = 3

    def test_no_parameter(self):
        # GIVEN
        self.superadmin.greeting = ''
        self.superadmin.clearMessageHistory()
        # WHEN
        self.superadmin.says('!greeting')
        # THEN
        self.assertListEqual(['You have no greeting set'], self.superadmin.message_history)

        # GIVEN
        self.superadmin.greeting = 'hi f00'
        self.superadmin.clearMessageHistory()
        # WHEN
        self.superadmin.says('!greeting')
        # THEN
        self.assertListEqual(['Your greeting is hi f00'], self.superadmin.message_history)

    def test_set_new_greeting_none(self):
        # GIVEN
        self.superadmin.greeting = 'f00'
        # WHEN
        self.superadmin.says('!greeting none')
        # THEN
        self.assertListEqual(['Greeting cleared'], self.superadmin.message_history)
        self.assertEqual('', self.superadmin.greeting)

    def test_set_new_greeting_nominal(self):
        # GIVEN
        self.superadmin.greeting = ''
        # WHEN
        self.superadmin.says('!greeting f00')
        # THEN
        self.assertListEqual(['Greeting Test: f00', 'Greeting changed to: f00'], self.superadmin.message_history)
        self.assertEqual('f00', self.superadmin.greeting)

    def test_set_new_greeting_too_long(self):
        # GIVEN
        self.superadmin.greeting = 'f00'
        # WHEN
        self.superadmin.says('!greeting %s' % ('x' * 256))
        # THEN
        self.assertListEqual(['Your greeting is too long'], self.superadmin.message_history)
        self.assertEqual('f00', self.superadmin.greeting)

    def test_set_new_greeting_with_placeholder_name(self):
        # GIVEN
        self.superadmin.greeting = 'f00'
        # WHEN
        self.superadmin.says('!greeting |$name|')
        # THEN
        self.assertListEqual(['Greeting Test: |SuperAdmin|', 'Greeting changed to: |$name|'],
                             self.superadmin.message_history)
        self.assertEqual('|%(name)s|', self.superadmin.greeting)

    def test_set_new_greeting_with_placeholder_greeting(self):
        """
        make sure that '$greeting' cannot be taken as a placeholder or we would allow recursive greeting.
        """
        # GIVEN
        self.superadmin.greeting = 'f00'
        # WHEN
        self.superadmin.says('!greeting |$greeting|')
        # THEN
        self.assertListEqual(['Greeting Test: |$greeting|', 'Greeting changed to: |$greeting|'],
                             self.superadmin.message_history)
        self.assertEqual('|$greeting|', self.superadmin.greeting)

    def test_set_new_greeting_with_placeholder_maxLevel(self):
        # GIVEN
        self.superadmin.greeting = 'f00'
        # WHEN
        self.superadmin.says('!greeting |$maxLevel|')
        # THEN
        self.assertListEqual(['Greeting Test: |100|', 'Greeting changed to: |$maxLevel|'],
                             self.superadmin.message_history)
        self.assertEqual('|%(maxLevel)s|', self.superadmin.greeting)

    def test_set_new_greeting_with_placeholder_group(self):
        # GIVEN
        self.superadmin.greeting = 'f00'
        # WHEN
        self.superadmin.says('!greeting |$group|')
        # THEN
        self.assertListEqual(['Greeting Test: |Super Admin|', 'Greeting changed to: |$group|'],
                             self.superadmin.message_history)
        self.assertEqual('|%(group)s|', self.superadmin.greeting)

    def test_set_new_greeting_with_placeholder_connections(self):
        # GIVEN
        self.superadmin.greeting = 'f00'
        # WHEN
        self.superadmin.says('!greeting |$connections|')
        # THEN
        self.assertListEqual(['Greeting Test: |3|', 'Greeting changed to: |$connections|'],
                             self.superadmin.message_history)
        self.assertEqual('|%(connections)s|', self.superadmin.greeting)


class Test_welcome(Welcome_functional_test):

    def setUp(self):
        Welcome_functional_test.setUp(self)
        self.load_config()
        # disabled event handling (spawns threads and is of no use for that test)
        self.p.onEvent = lambda *args, **kwargs: None

        self.client = FakeClient(console=self.console, name="Jack", guid="JackGUID")
        self.client._connections = 0
        self.client.greeting = 'hi everyone :)'
        self.client.connects("0")
        self.superadmin.connects("1")

        self.say_patcher = patch.object(self.console, "say")
        self.say_mock = self.say_patcher.start()

    def tearDown(self):
        Welcome_functional_test.tearDown(self)
        self.say_patcher.stop()

    def Test_get_client_info(self):
        self.parser_conf._settings["b3"] = {"time_zone": "CET", "time_format": "%I:%M%p %Z %m/%d/%y"}
        self.assertDictEqual({'connections': '1',
                              'group': 'Super Admin',
                              'id': '2',
                              'lastVisit': 'Unknown',
                              'level': '100',
                              'name': u'SuperAdmin^7'}, self.p.get_client_info(self.superadmin))
        # WHEN
        self.superadmin.lastVisit = 1364821993
        self.superadmin._connections = 2
        # THEN
        self.assertDictEqual({'connections': '2',
                              'group': u'Super Admin',
                              'id': '2',
                              'lastVisit': '02:13PM CET 04/01/13',
                              'level': '100',
                              'name': 'SuperAdmin^7'}, self.p.get_client_info(self.superadmin))
        # WHEN
        self.superadmin.says("!mask mod")
        # THEN
        self.assertDictEqual({'connections': '2',
                              'group': u'Moderator',
                              'id': '2',
                              'lastVisit': '02:13PM CET 04/01/13',
                              'level': '20',
                              'name': 'SuperAdmin^7'}, self.p.get_client_info(self.superadmin))

    def test_0(self):
        # GIVEN
        self.p._welcomeFlags = 0
        # WHEN
        self.p.welcome(self.superadmin)
        # THEN
        self.assertListEqual([], self.say_mock.mock_calls)
        self.assertListEqual([], self.superadmin.message_history)

    def test_first(self):
        # GIVEN
        self.client._connections = 0
        self.p._welcomeFlags = F_FIRST
        # WHEN
        self.p.welcome(self.client)
        # THEN
        self.assertListEqual([], self.say_mock.mock_calls)
        self.assertListEqual(['Welcome Jack, this must be your first visit, you are player #1. Type !help for '
                              'help'], self.client.message_history)

    def test_newb(self):
        # GIVEN
        self.client._connections = 2
        self.p._welcomeFlags = F_NEWB
        # WHEN
        self.p.welcome(self.client)
        # THEN
        self.assertListEqual([], self.say_mock.mock_calls)
        self.assertListEqual(['[Authed] Welcome back Jack [@1], last visit Unknown. Type !register in chat to register.'
                              ' Type !help for help'], self.client.message_history)

    def test_user(self):
        # GIVEN
        self.client._connections = 2
        self.p._welcomeFlags = F_USER
        self.client.says("!register")
        self.client.clearMessageHistory()
        # WHEN
        self.p.welcome(self.client)
        # THEN
        self.assertListEqual([call(u'^7Jack^7 ^7put in group User')], self.say_mock.mock_calls)
        self.assertListEqual(["[Authed] Welcome back Jack [@1], last visit Unknown, you're a User, played 2 times"],
                             self.client.message_history)

    def test_announce_first(self):
        # GIVEN
        self.client._connections = 0
        self.p._welcomeFlags = F_ANNOUNCE_FIRST
        # WHEN
        self.p.welcome(self.client)
        # THEN
        self.assertListEqual([call('^7Everyone welcome Jack^7^7, player number ^3#1^7, to the server')],
                             self.say_mock.mock_calls)
        self.assertListEqual([], self.client.message_history)

    def test_announce_user(self):
        # GIVEN
        self.client._connections = 2
        self.p._welcomeFlags = F_ANNOUNCE_USER
        self.client.says("!register")
        self.client.clearMessageHistory()
        # WHEN
        self.p.welcome(self.client)
        # THEN
        self.assertListEqual([call(u'^7Jack^7 ^7put in group User'),
                              call('^7Everyone welcome back Jack^7^7, player number ^3#1^7, to the server, played 2 '
                                   'times')], self.say_mock.mock_calls)
        self.assertListEqual([], self.client.message_history)

    def test_custom_greeting(self):
        # GIVEN
        self.client._connections = 2
        self.p._welcomeFlags = F_CUSTOM_GREETING
        self.client.says("!register")
        self.client.clearMessageHistory()
        # WHEN
        self.p.welcome(self.client)
        # THEN
        self.assertListEqual([call(u'^7Jack^7 ^7put in group User'), call('^7Jack^7^7 joined: hi everyone :)')],
                             self.say_mock.mock_calls)
        self.assertListEqual([], self.client.message_history)