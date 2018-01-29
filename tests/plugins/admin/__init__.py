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

from b3.fake import FakeClient
from b3.plugins.admin import AdminPlugin
from b3.config import CfgConfigParser
from b3 import TEAM_BLUE
from b3 import TEAM_RED
from tests import B3TestCase


class Admin_TestCase(B3TestCase):
    """
    Tests from a class inherithing from Admin_TestCase must call self.init().
    """
    def setUp(self):
        B3TestCase.setUp(self)
        self.conf = CfgConfigParser()
        self.p = AdminPlugin(self.console, self.conf)

    def init(self, config_content=None):
        """
        Optionally specify a config for the plugin. If called with no parameter, then the default config is loaded.
        """
        if config_content is None:
            self.conf.load(b3.getAbsolutePath("@b3/conf/plugin_admin.ini"))
        else:
            self.conf.loadFromString(config_content)
        self.p.onLoadConfig()
        self.p.onStartup()

class Admin_functional_test(B3TestCase):
    """ tests from a class inheriting from Admin_functional_test must call self.init() """
    def setUp(self):
        B3TestCase.setUp(self)
        self.conf = CfgConfigParser()
        self.p = AdminPlugin(self.console, self.conf)

    def init(self, config_content=None):
        """ optionally specify a config for the plugin. If called with no parameter, then the default config is loaded """
        if config_content is None:
            self.conf.load(b3.getAbsolutePath("@b3/conf/plugin_admin.ini"))
        else:
            self.conf.loadFromString(config_content)

        self.p._commands = {}
        self.p.onLoadConfig()
        self.p.onStartup()

        self.joe = FakeClient(self.console, name="Joe", exactName="Joe", guid="joeguid", groupBits=128, team=TEAM_RED)
        self.mike = FakeClient(self.console, name="Mike", exactName="Mike", guid="mikeguid", groupBits=1, team=TEAM_BLUE)