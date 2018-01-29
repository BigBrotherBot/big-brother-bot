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
import logging

from mockito import when
from b3.plugins.admin import AdminPlugin
from tests import B3TestCase
from b3.plugins.login import LoginPlugin
from b3.config import CfgConfigParser


F00_MD5 = '9f06f2538cdbb40bce9973f60506de09'


class LoginTestCase(B3TestCase):
    """
    Ease testcases that need an working B3 console and need to control the censor plugin config.
    """

    def setUp(self):
        self.log = logging.getLogger('output')
        self.log.propagate = False

        B3TestCase.setUp(self)

        admin_conf = CfgConfigParser()
        admin_conf.load(b3.getAbsolutePath('@b3/conf/plugin_admin.ini'))
        self.adminPlugin = AdminPlugin(self.console, admin_conf)
        when(self.console).getPlugin("admin").thenReturn(self.adminPlugin)
        self.adminPlugin.onLoadConfig()
        self.adminPlugin.onStartup()

        self.console.gameName = "theGame"
        self.console.startup()
        self.log.propagate = True

    def tearDown(self):
        B3TestCase.tearDown(self)

    def init_plugin(self, config_content=None):
        self.conf = CfgConfigParser()
        if config_content:
            self.conf.loadFromString(config_content)
        else:
            self.conf.load(b3.getAbsolutePath('@b3/conf/plugin_login.ini'))
        self.p = LoginPlugin(self.console, self.conf)

        self.log.setLevel(logging.DEBUG)
        self.log.info("============================= Login plugin: loading config ============================")
        self.p.onLoadConfig()
        self.log.info("============================= Login plugin: starting  =================================")
        self.p.onStartup()