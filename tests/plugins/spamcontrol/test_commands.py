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

from mockito import when
from mock import Mock
from b3.fake import FakeClient
from b3.plugins.admin import AdminPlugin
from tests.plugins.spamcontrol import SpamcontrolTestCase


class Test_commands(SpamcontrolTestCase):

    def setUp(self):
        SpamcontrolTestCase.setUp(self)

        self.adminPlugin = AdminPlugin(self.console, '@b3/conf/plugin_admin.ini')
        when(self.console).getPlugin("admin").thenReturn(self.adminPlugin)
        self.adminPlugin.onLoadConfig()
        self.adminPlugin.onStartup()

        with open(b3.getAbsolutePath('@b3/conf/plugin_spamcontrol.ini')) as default_conf:
            self.init_plugin(default_conf.read())

        self.joe = FakeClient(self.console, name="Joe", guid="zaerezarezar", groupBits=1)
        self.joe.connects("1")

        self.superadmin = FakeClient(self.console, name="Superadmin", guid="superadmin_guid", groupBits=128)
        self.superadmin.connects("2")

    def test_cmd_spamins(self):
        # GIVEN
        when(self.p).getTime().thenReturn(0).thenReturn(3).thenReturn(4).thenReturn(4).thenReturn(500)
        self.joe.says("doh") # 0s
        self.joe.says("doh") # 3s
        self.joe.says("doh") # 4s
        # WHEN
        self.superadmin.clearMessageHistory()
        self.superadmin.says("!spamins joe")
        # THEN
        self.assertListEqual(['Joe currently has 9 spamins, peak was 9'], self.superadmin.message_history) # 4s
        # WHEN
        self.superadmin.clearMessageHistory()
        self.superadmin.says("!spamins joe")
        self.assertListEqual(['Joe currently has 0 spamins, peak was 9'], self.superadmin.message_history) # 500s

    def test_cmd_spamins_lowercase(self):
        # GIVEN
        mike = FakeClient(self.console, name="Mike")
        mike.connects("3")
        # WHEN
        self.superadmin.clearMessageHistory()
        self.superadmin.says("!spamins mike")
        # THEN
        self.assertListEqual(['Mike currently has 0 spamins, peak was 0'], self.superadmin.message_history)

    def test_cmd_spamins_uppercase(self):
        # GIVEN
        mike = FakeClient(self.console, name="Mike")
        mike.connects("3")
        # WHEN
        self.superadmin.clearMessageHistory()
        self.superadmin.says("!spamins MIKE")
        # THEN
        self.assertListEqual(['Mike currently has 0 spamins, peak was 0'], self.superadmin.message_history)

    def test_cmd_spamins_unknown_player(self):
        # WHEN
        self.superadmin.clearMessageHistory()
        self.superadmin.says("!spamins nobody")
        # THEN
        self.assertListEqual(['No players found matching nobody'], self.superadmin.message_history)

    def test_cmd_spamins_no_argument(self):
        # GIVEN
        self.console.getPlugin('admin')._warn_command_abusers = True
        # WHEN
        self.joe.clearMessageHistory()
        self.joe.says("!spamins")
        # THEN
        self.assertListEqual(['You need to be in group Moderator to use !spamins'], self.joe.message_history)
        # WHEN
        self.superadmin.says("!putgroup joe mod")
        self.joe.clearMessageHistory()
        self.joe.says("!spamins")
        # THEN
        self.assertListEqual(['Joe is too cool to spam'], self.joe.message_history)

    def test_joe_gets_warned(self):
        # GIVEN
        when(self.p).getTime().thenReturn(0)
        self.joe.warn = Mock()

        # WHEN
        self.joe.says("doh 1")
        self.joe.says("doh 2")
        self.joe.says("doh 3")
        self.joe.says("doh 4")
        self.joe.says("doh 5")

        # THEN
        self.assertEqual(1, self.joe.warn.call_count)
