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
from mockito import when
from b3.plugins.admin import AdminPlugin
from b3.plugins.cmdmanager import CmdmanagerPlugin
from b3.config import CfgConfigParser
from tests import B3TestCase


class Cmdmanager_TestCase(B3TestCase):

    def setUp(self):

        B3TestCase.setUp(self)
        self.console.gameName = 'f00'

        self.adminPlugin = AdminPlugin(self.console, '@b3/conf/plugin_admin.ini')
        when(self.console).getPlugin("admin").thenReturn(self.adminPlugin)
        self.adminPlugin.onLoadConfig()
        self.adminPlugin.onStartup()

        self.conf = CfgConfigParser()
        self.conf.loadFromString(dedent(r"""
            [settings]
            update_config_file: no

            [commands]
            cmdlevel: fulladmin
            cmdalias: fulladmin
            cmdgrant: superadmin
            cmdrevoke: superadmin
            cmduse: superadmin
        """))

        self.p = CmdmanagerPlugin(self.console, self.conf)
        self.p.onLoadConfig()
        self.p.onStartup()

    def assert_cmd_groups(self, cmd_name, groups):
        """
        Assert a command has the given authorized groups set correctly.
        :param cmd_name: str name of a command
        :param groups: str minimum group required to run the command or group range
        """
        cmd = self.adminPlugin._commands[cmd_name]
        self.assertIsNotNone(cmd, "could not find command %r" % cmd_name)
        self.assertEqual(groups, self.p.get_command_level_string(cmd))

    def assert_cmd_alias(self, cmd_name, alias_name):
        """
        Assert a command has the given alias.
        :param cmd_name: str command name
        :param alias_name: str expected alias name, or None
        """
        cmd = self.adminPlugin._commands[cmd_name]
        self.assertIsNotNone(cmd, "could not find command %r" % cmd_name)
        self.assertEqual(alias_name if alias_name is not None else '', cmd.alias)