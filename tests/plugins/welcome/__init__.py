# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2013 Thomas LEVEIL <courgette@bigbrotherbot.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA

import b3

from mockito import when
from b3.plugins.admin import AdminPlugin
from b3.plugins.welcome import WelcomePlugin
from b3.config import CfgConfigParser
from b3.fake import FakeClient
from tests import B3TestCase, logging_disabled


class Welcome_functional_test(B3TestCase):

    def setUp(self):

        B3TestCase.setUp(self)

        with logging_disabled():
            self.adminPlugin = AdminPlugin(self.console, '@b3/conf/plugin_admin.ini')
            when(self.console).getPlugin("admin").thenReturn(self.adminPlugin)
            self.adminPlugin.onLoadConfig()
            self.adminPlugin.onStartup()

            self.conf = CfgConfigParser()
            self.p = WelcomePlugin(self.console, self.conf)

            self.joe = FakeClient(self.console, name="Joe", guid="joeguid", groupBits=1, team=b3.TEAM_RED)
            self.mike = FakeClient(self.console, name="Mike", guid="mikeguid", groupBits=1, team=b3.TEAM_RED)
            self.bill = FakeClient(self.console, name="Bill", guid="billguid", groupBits=1, team=b3.TEAM_RED)
            self.superadmin = FakeClient(self.console, name="SuperAdmin", guid="superadminguid", groupBits=128, team=b3.TEAM_RED)

    def load_config(self, config_content=None):
        """
        load the given config content, or the default config if config_content is None.
        """
        if config_content is None:
            self.conf.load(b3.getAbsolutePath('@b3/conf/plugin_welcome.ini'))
        else:
            self.conf.loadFromString(config_content)
        self.p.onLoadConfig()
        self.p.onStartup()