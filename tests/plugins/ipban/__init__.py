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

from textwrap import dedent
from mockito import when
from b3.plugins.ipban import IpbanPlugin
from b3.fake import FakeConsole
from b3.config import CfgConfigParser
from b3.config import MainConfig
from b3.plugins.admin import AdminPlugin
from tests import logging_disabled

class IpbanTestCase(unittest2.TestCase):

    def setUp(self):
        self.parser_conf = MainConfig(CfgConfigParser(allow_no_value=True))
        self.parser_conf.loadFromString(dedent(r""""""))
        self.console = FakeConsole(self.parser_conf)
        self.console.gameName = 'f00'
        self.console.startup()

        with logging_disabled():
            self.adminPlugin = AdminPlugin(self.console, '@b3/conf/plugin_admin.ini')
            self.adminPlugin.onLoadConfig()
            self.adminPlugin.onStartup()

        self.evt_queue = []

        # make sure the admin plugin obtained by other plugins is our admin plugin
        when(self.console).getPlugin('admin').thenReturn(self.adminPlugin)

        with logging_disabled():
            from b3.fake import FakeClient

        # prepare a few players
        self.mike = FakeClient(self.console, name="Mike", exactName="Mike", guid="MIKEGUID", groupBits=16, ip='1.1.1.1')
        self.paul = FakeClient(self.console, name="Paul", exactName="Paul", guid="PAULGUID", groupBits=1, ip='2.2.2.2')
        self.john = FakeClient(self.console, name="John", exactName="John", guid="JOHNGUID", groupBits=0, ip='3.3.3.3')
        self.mary = FakeClient(self.console, name="Mary", exactName="Mary", guid="MARYGUID", groupBits=0, ip='4.4.4.4')

        self.conf = CfgConfigParser()
        self.p = IpbanPlugin(self.console, self.conf)

        # return some mock data
        when(self.p).getBanIps().thenReturn(['2.2.2.2', '6.6.6.6', '7.7.7.7'])
        when(self.p).getTempBanIps().thenReturn(['3.3.3.3', '8.8.8.8', '9.9.9.9'])

    def tearDown(self):
        self.console.working = False
        self.mike.disconnects()
        self.paul.disconnects()
        self.john.disconnects()
        self.mary.disconnects()

    def init(self, config_content=None):
        if config_content:
            self.conf.loadFromString(config_content)
        else:
            self.conf.loadFromString(dedent(r"""
                [settings]
                maxlevel: user
            """))
        self.p.onLoadConfig()
        self.p.onStartup()