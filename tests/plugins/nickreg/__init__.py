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

import unittest2

from mockito import when
from b3.config import XmlConfigParser
from b3.plugins.admin import AdminPlugin
from tests import logging_disabled
from b3.config import CfgConfigParser
from b3.plugins.nickreg import NickregPlugin
from textwrap import dedent


class NickregTestCase(unittest2.TestCase):

    def setUp(self):
        # create a FakeConsole parser
        self.parser_conf = XmlConfigParser()
        self.parser_conf.loadFromString(r"""<configuration/>""")
        with logging_disabled():
            from b3.fake import FakeConsole
            self.console = FakeConsole(self.parser_conf)

        with logging_disabled():
            self.adminPlugin = AdminPlugin(self.console, '@b3/conf/plugin_admin.ini')
            self.adminPlugin._commands = {}
            self.adminPlugin.onStartup()

        # make sure the admin plugin obtained by other plugins is our admin plugin
        when(self.console).getPlugin('admin').thenReturn(self.adminPlugin)

        self.conf = CfgConfigParser()
        self.conf.loadFromString(dedent("""
            [settings]
            min_level: mod
            min_level_global_manage: admin
            max_nicks: 3
            interval: 30
        """))

        self.p = NickregPlugin(self.console, self.conf)
        self.p.onLoadConfig()
        self.p.onStartup()

        with logging_disabled():
            from b3.fake import FakeClient
            self.senioradmin = FakeClient(console=self.console, name="SeniorAdmin", guid="SENIORADMIN", groupBits=64)
            self.admin = FakeClient(console=self.console, name="Admin", guid="ADMIN", groupBits=16)
            self.guest = FakeClient(console=self.console, name="Guest", guid="GUEST", groupBits=0)

        self.admin.connects("1")
        self.guest.connects("2")
        self.senioradmin.connects("3")

    def tearDown(self):
        pass