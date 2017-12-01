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
import b3.cron

from textwrap import dedent
from mockito import when
from b3.plugins.admin import AdminPlugin
from b3.plugins.pluginmanager import PluginmanagerPlugin
from b3.config import CfgConfigParser
from tests import B3TestCase


class PluginmanagerTestCase(B3TestCase):

    def setUp(self):

        B3TestCase.setUp(self)
        self.console.gameName = 'f00'

        self.adminPlugin = AdminPlugin(self.console, '@b3/conf/plugin_admin.ini')
        when(self.console).getPlugin("admin").thenReturn(self.adminPlugin)
        self.adminPlugin.onLoadConfig()
        self.adminPlugin.onStartup()

        self.conf = CfgConfigParser()
        self.conf.loadFromString(dedent(r"""
            [commands]
            plugin: superadmin
        """))

        self.p = PluginmanagerPlugin(self.console, self.conf)
        when(self.console).getPlugin("pluginmanager").thenReturn(self.adminPlugin)
        self.p.onLoadConfig()
        self.p.onStartup()

        when(self.console.config).get_external_plugins_dir().thenReturn(b3.getAbsolutePath('@b3\\extplugins'))

        # store them also in the console _plugins dict
        self.console._plugins['admin'] = self.adminPlugin
        self.console._plugins['pluginmanager'] = self.p

    def tearDown(self):
        self.console._plugins.clear()
        B3TestCase.tearDown(self)
