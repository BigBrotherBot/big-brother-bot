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
from mock import patch
from tests import B3TestCase
from b3.plugins.status import StatusPlugin
from b3.config import CfgConfigParser


class Test_config(B3TestCase):

    @patch("b3.cron.PluginCronTab")
    def test_no_svar_table(self, pluginCronTab_mock):
        conf = CfgConfigParser()
        conf.loadFromString(dedent(r"""
            [settings]
            interval: 60
            output_file: ~/status.xml
            enableDBsvarSaving: no
            enableDBclientSaving: no
            """))
        self.p = StatusPlugin(self.console, conf)
        self.p._tables = { 'svars': 'current_svars', 'cvars': 'current_clients' }
        self.p.onLoadConfig()
        self.assertEqual("current_svars", self.p._tables['svars'])

    @patch("b3.cron.PluginCronTab")
    def test_svar_table(self, pluginCronTab_mock):
        conf = CfgConfigParser()
        conf.loadFromString(dedent(r"""
            [settings]
            interval: 60
            output_file: ~/status.xml
            enableDBsvarSaving: yes
            enableDBclientSaving: no
            svar_table: alternate_svar_table
            """))
        self.p = StatusPlugin(self.console, conf)
        self.p._tables = { 'svars': 'current_svars', 'cvars': 'current_clients' }
        self.p.onLoadConfig()
        self.assertEqual("alternate_svar_table", self.p._tables['svars'])

    @patch("b3.cron.PluginCronTab")
    def test_no_client_table(self, pluginCronTab_mock):
        conf = CfgConfigParser()
        conf.loadFromString(dedent(r"""
            [settings]
            interval: 60
            output_file: ~/status.xml
            enableDBsvarSaving: no
            enableDBclientSaving: no
            """))
        self.p = StatusPlugin(self.console, conf)
        self.p._tables = { 'svars': 'current_svars', 'cvars': 'current_clients' }
        self.p.onLoadConfig()
        self.assertEqual("current_clients", self.p._tables['cvars'])

    @patch("b3.cron.PluginCronTab")
    def test_client_table(self, pluginCronTab_mock):
        conf = CfgConfigParser()
        conf.loadFromString(dedent(r"""
            [settings]
            interval: 60
            output_file: ~/status.xml
            enableDBsvarSaving: no
            enableDBclientSaving: yes
            client_table: alternate_client_table
            """))
        self.p = StatusPlugin(self.console, conf)
        self.p._tables = { 'svars': 'current_svars', 'cvars': 'current_clients' }
        self.p.onLoadConfig()
        self.assertEqual("alternate_client_table", self.p._tables['cvars'])