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
from b3.fake import FakeClient
from b3.plugins.admin import AdminPlugin
from tests.plugins.spamcontrol import SpamcontrolTestCase


class Test_plugin(SpamcontrolTestCase):

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