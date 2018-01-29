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

from textwrap import dedent
from b3.plugins.welcome import F_FIRST, F_NEWB, F_ANNOUNCE_USER, F_ANNOUNCE_FIRST, F_USER, F_CUSTOM_GREETING
from tests.plugins.welcome import Welcome_functional_test

class Test_default_config(Welcome_functional_test):

    def setUp(self):
        Welcome_functional_test.setUp(self)
        self.load_config()

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
        self.load_config(dedent("""
            [settings]
            flags: 34
        """))
        self.assertEqual(34, self.p._welcomeFlags)

    def test_flags_empty(self):
        self.load_config(dedent("""
            [settings]
            flags: 
        """))
        self.assertEqual(63, self.p._welcomeFlags)

    def test_flags_junk(self):
        self.load_config(dedent("""
            [settings]
            flags: f00
        """))
        self.assertEqual(63, self.p._welcomeFlags)

    def test_settings_no_flags(self):
        self.load_config(dedent("""
            [settings]
        """))
        self.assertEqual(63, self.p._welcomeFlags)

    def test_welcome_first(self):
        self.p._welcomeFlags = 0
        self.load_config(dedent("""
            [settings]
            welcome_first: yes
        """))
        self.assertTrue(F_FIRST & self.p._welcomeFlags)
        self.load_config(dedent("""
            [settings]
            welcome_first: no
        """))
        self.assertFalse(F_FIRST & self.p._welcomeFlags)

    def test_welcome_newb(self):
        self.p._welcomeFlags = 0
        self.load_config(dedent("""
            [settings]
            welcome_newb: yes
        """))
        self.assertTrue(F_NEWB & self.p._welcomeFlags)
        self.load_config(dedent("""
            [settings]
            welcome_newb: no
        """))
        self.assertFalse(F_NEWB & self.p._welcomeFlags)

    def test_welcome_user(self):
        self.p._welcomeFlags = 0
        self.load_config(dedent("""
            [settings]
            welcome_user: yes
        """))
        self.assertTrue(F_USER & self.p._welcomeFlags)
        self.load_config(dedent("""
            [settings]
            welcome_user: no
        """))
        self.assertFalse(F_USER & self.p._welcomeFlags)

    def test_announce_first(self):
        self.p._welcomeFlags = 0
        self.load_config(dedent("""
            [settings]
            announce_first: yes
        """))
        self.assertTrue(F_ANNOUNCE_FIRST & self.p._welcomeFlags)
        self.load_config(dedent("""
            [settings]
            announce_first: no
        """))
        self.assertFalse(F_ANNOUNCE_FIRST & self.p._welcomeFlags)

    def test_announce_user(self):
        self.p._welcomeFlags = 0
        self.load_config(dedent("""
            [settings]
            announce_user: yes
        """))
        self.assertTrue(F_ANNOUNCE_USER & self.p._welcomeFlags)
        self.load_config(dedent("""
            [settings]
            announce_user: no
        """))
        self.assertFalse(F_ANNOUNCE_USER & self.p._welcomeFlags)

    def test_show_user_greeting(self):
        self.p._welcomeFlags = 0
        self.load_config(dedent("""
            [settings]
            show_user_greeting: yes
        """))
        self.assertTrue(F_CUSTOM_GREETING & self.p._welcomeFlags)
        self.load_config(dedent("""
            [settings]
            show_user_greeting: no
        """))
        self.assertFalse(F_CUSTOM_GREETING & self.p._welcomeFlags)

    def test_nonce_set(self):
        self.p._welcomeFlags = 0
        self.load_config(dedent("""
            [settings]
            welcome_first: no
            welcome_newb: no
            welcome_user: no
            announce_first: no
            announce_user: no
            show_user_greeting: no
        """))
        self.assertEqual(0, self.p._welcomeFlags)

    def test_all_set(self):
        self.p._welcomeFlags = 0
        self.load_config(dedent("""
            [settings]
            welcome_first: yes
            welcome_newb: yes
            welcome_user: yes
            announce_first: yes
            announce_user: yes
            show_user_greeting: yes
        """))
        self.assertEqual(F_FIRST | F_NEWB | F_USER | F_ANNOUNCE_FIRST | F_ANNOUNCE_USER | F_CUSTOM_GREETING,
                         self.p._welcomeFlags)

    def test_partly_set(self):
        self.p._welcomeFlags = 0
        self.load_config(dedent("""
            [settings]
            welcome_first: yes
            welcome_newb: no
            welcome_user: yes
            announce_first: yes
            announce_user: no
            show_user_greeting: yes
        """))
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
        self.load_config(dedent("""
            [settings]
            flags: 54
            ; welcome_first: no
            welcome_newb: no
            welcome_user: no
            announce_first: no
            announce_user: yes
            show_user_greeting: no
        """))
        self.assertEqual(F_FIRST | F_ANNOUNCE_USER, self.p._welcomeFlags)


class Test_config(Welcome_functional_test):

    def test_settings_newb_connections(self):
        # nominal
        self.load_config(dedent("""
            [settings]
            newb_connections: 27
        """))
        self.assertEqual(27, self.p._newbConnections)
        # empty
        self.load_config(dedent("""
            [settings]
            newb_connections: 
        """))
        self.assertEqual(15, self.p._newbConnections)
        # junk
        self.load_config(dedent("""
            [settings]
            newb_connections: f00
        """))
        self.assertEqual(15, self.p._newbConnections)

    def test_settings_delay(self):
        # nominal
        self.load_config(dedent("""
            [settings]
            delay: 15
        """))
        self.assertEqual(15, self.p._welcomeDelay)
        # empty
        self.load_config(dedent("""
            [settings]
            delay: 
        """))
        self.assertEqual(30, self.p._welcomeDelay)
        # junk
        self.load_config(dedent("""
            [settings]
            delay: f00
        """))
        self.assertEqual(30, self.p._welcomeDelay)
        # too low
        self.load_config(dedent("""
            [settings]
            delay: 5
        """))
        self.assertEqual(30, self.p._welcomeDelay)
        # too high
        self.load_config(dedent("""
            [settings]
            delay: 500
        """))
        self.assertEqual(30, self.p._welcomeDelay)

    def test_settings_min_gap(self):
        # nominal
        self.load_config(dedent("""
            [settings]
            min_gap: 540
        """))
        self.assertEqual(540, self.p._min_gap)
        # empty
        self.load_config(dedent("""
            [settings]
            min_gap: 
        """))
        self.assertEqual(3600, self.p._min_gap)
        # junk
        self.load_config(dedent("""
            [settings]
            min_gap: f00
        """))
        self.assertEqual(3600, self.p._min_gap)
        # too low
        self.load_config(dedent("""
            [settings]
            min_gap: -15
        """))
        self.assertEqual(0, self.p._min_gap)