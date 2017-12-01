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

from mock import Mock
from mockito import when
from b3.fake import FakeClient
from b3.plugin import Plugin
from b3.plugins.admin import Command
from tests.plugins.pluginmanager import PluginmanagerTestCase


class Test_commands(PluginmanagerTestCase):

    def test_cmd_plugin_no_parameters(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!plugin")
        # THEN
        self.assertListEqual(['invalid data, try !help plugin'], superadmin.message_history)

    def test_cmd_plugin_with_invalid_command_name(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!plugin fake")
        # THEN
        self.assertListEqual(['usage: !plugin <disable|enable|info|list|load|unload> [<data>]'], superadmin.message_history)

    ####################################################################################################################
    #                                                                                                                  #
    #   PLUGIN LIST                                                                                                    #
    #                                                                                                                  #
    ####################################################################################################################

    def test_cmd_plugin_list(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!plugin list")
        # THEN
        self.assertListEqual(['Loaded plugins: admin, pluginmanager'], superadmin.message_history)

    ####################################################################################################################
    #                                                                                                                  #
    #   PLUGIN ENABLE                                                                                                  #
    #                                                                                                                  #
    ####################################################################################################################

    def test_cmd_plugin_enable_with_no_plugin_name(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!plugin enable")
        # THEN
        self.assertListEqual(['usage: !plugin enable <name/s>'], superadmin.message_history)

    def test_cmd_plugin_enable_protected(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!plugin enable admin")
        # THEN
        self.assertListEqual(['Plugin admin is protected'], superadmin.message_history)

    def test_cmd_plugin_enable_with_invalid_plugin_name(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!plugin enable fake")
        # THEN
        self.assertListEqual(['Plugin fake is not loaded'], superadmin.message_history)

    def test_cmd_plugin_enable_with_already_enabled_plugin(self):
        # GIVEN
        mock_plugin = Mock(spec=Plugin)
        mock_plugin.isEnabled = Mock(return_value=True)
        when(self.console).getPlugin("mock").thenReturn(mock_plugin)
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!plugin enable mock")
        # THEN
        self.assertListEqual(['Plugin mock is already enabled'], superadmin.message_history)

    def test_cmd_plugin_enable_succeed(self):
        # GIVEN
        mock_plugin = Mock(spec=Plugin)
        mock_plugin.isEnabled = Mock(return_value=False)
        when(self.console).getPlugin("mock").thenReturn(mock_plugin)
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!plugin enable mock")
        # THEN
        self.assertListEqual(['Plugin mock is now enabled'], superadmin.message_history)

    def test_cmd_plugin_enable_succeed_multiple(self):
        # GIVEN
        mock_pluginA = Mock(spec=Plugin)
        mock_pluginA.isEnabled = Mock(return_value=False)
        when(self.console).getPlugin("mocka").thenReturn(mock_pluginA)
        mock_pluginB = Mock(spec=Plugin)
        mock_pluginB.isEnabled = Mock(return_value=False)
        when(self.console).getPlugin("mockb").thenReturn(mock_pluginB)
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!plugin enable mocka mockb")
        # THEN
        self.assertListEqual(['Plugin mocka is now enabled', 'Plugin mockb is now enabled'], superadmin.message_history)

    def test_cmd_plugin_enable_mixed_multiple(self):
        # GIVEN
        mock_pluginA = Mock(spec=Plugin)
        mock_pluginA.isEnabled = Mock(return_value=False)
        when(self.console).getPlugin("mock").thenReturn(mock_pluginA)
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!plugin enable mock fake")
        # THEN
        self.assertListEqual(['Plugin mock is now enabled', 'Plugin fake is not loaded'], superadmin.message_history)

    ####################################################################################################################
    #                                                                                                                  #
    #   PLUGIN DISABLE                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def test_cmd_plugin_disable_with_no_plugin_name(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!plugin disable")
        # THEN
        self.assertListEqual(['usage: !plugin disable <name/s>'], superadmin.message_history)

    def test_cmd_plugin_disable_protected(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!plugin disable admin")
        # THEN
        self.assertListEqual(['Plugin admin is protected'], superadmin.message_history)

    def test_cmd_plugin_disable_with_invalid_plugin_name(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!plugin disable fake")
        # THEN
        self.assertListEqual(['Plugin fake is not loaded'], superadmin.message_history)

    def test_cmd_plugin_disable_with_already_disable_plugin(self):
        # GIVEN
        mock_plugin = Mock(spec=Plugin)
        mock_plugin.isEnabled = Mock(return_value=False)
        when(self.console).getPlugin("mock").thenReturn(mock_plugin)
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!plugin disable mock")
        # THEN
        self.assertListEqual(['Plugin mock is already disabled'], superadmin.message_history)

    def test_cmd_plugin_disable_succeed(self):
        # GIVEN
        mock_plugin = Mock(spec=Plugin)
        mock_plugin.isEnabled = Mock(return_value=True)
        when(self.console).getPlugin("mock").thenReturn(mock_plugin)
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!plugin disable mock")
        # THEN
        self.assertListEqual(['Plugin mock is now disabled'], superadmin.message_history)

    def test_cmd_plugin_disable_succeed_multiple(self):
        # GIVEN
        mock_pluginA = Mock(spec=Plugin)
        mock_pluginA.isEnabled = Mock(return_value=True)
        when(self.console).getPlugin("mocka").thenReturn(mock_pluginA)
        mock_pluginB = Mock(spec=Plugin)
        mock_pluginB.isEnabled = Mock(return_value=True)
        when(self.console).getPlugin("mockb").thenReturn(mock_pluginB)
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!plugin disable mocka mockb")
        # THEN
        self.assertListEqual(['Plugin mocka is now disabled', 'Plugin mockb is now disabled'], superadmin.message_history)

    def test_cmd_plugin_disable_mixed_multiple(self):
        # GIVEN
        mock_pluginA = Mock(spec=Plugin)
        mock_pluginA.isEnabled = Mock(return_value=True)
        when(self.console).getPlugin("mock").thenReturn(mock_pluginA)
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!plugin disable mock fake")
        # THEN
        self.assertListEqual(['Plugin mock is now disabled', 'Plugin fake is not loaded'], superadmin.message_history)

    ####################################################################################################################
    #                                                                                                                  #
    #   PLUGIN LOAD                                                                                                    #
    #                                                                                                                  #
    ####################################################################################################################

    def test_cmd_plugin_load_with_no_plugin_name(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!plugin load")
        # THEN
        self.assertListEqual(['usage: !plugin load <name/s>'], superadmin.message_history)

    def test_cmd_plugin_load_protected(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!plugin load admin")
        # THEN
        self.assertListEqual(['Plugin admin is protected'], superadmin.message_history)

    def test_cmd_plugin_load_with_already_loaded_plugin(self):
        # GIVEN
        mock_plugin = Mock(spec=Plugin)
        when(self.console).getPlugin("mock").thenReturn(mock_plugin)
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!plugin load mock")
        # THEN
        self.assertListEqual(['Plugin mock is already loaded'], superadmin.message_history)

    def test_cmd_plugin_load_with_invalid_plugin_name(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!plugin load fake")
        # THEN
        self.assertListEqual(['Missing fake plugin python module', 'Please put the plugin module in @b3/extplugins/'], superadmin.message_history)

    # TODO: add test cases for successful plugin load

    ####################################################################################################################
    #                                                                                                                  #
    #   PLUGIN UNLOAD                                                                                                  #
    #                                                                                                                  #
    ####################################################################################################################

    def test_cmd_plugin_unload_with_no_plugin_name(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!plugin unload")
        # THEN
        self.assertListEqual(['usage: !plugin unload <name/s>'], superadmin.message_history)

    def test_cmd_plugin_unload_protected(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!plugin unload admin")
        # THEN
        self.assertListEqual(['Plugin admin is protected'], superadmin.message_history)

    def test_cmd_plugin_unload_with_invalid_plugin_name(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!plugin unload fake")
        # THEN
        self.assertListEqual(['Plugin fake is not loaded'], superadmin.message_history)

    def test_cmd_plugin_unload_with_enabled_plugin(self):
        # GIVEN
        mock_plugin = Mock(spec=Plugin)
        mock_plugin.isEnabled = Mock(return_value=True)
        when(self.console).getPlugin("mock").thenReturn(mock_plugin)
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!plugin unload mock")
        # THEN
        self.assertListEqual(['Plugin mock is currently enabled: disable it first'], superadmin.message_history)

    def test_cmd_plugin_unload_successful(self):
        # GIVEN

        ###### MOCK PLUGIN
        mock_plugin = Mock(spec=Plugin)
        mock_plugin.console = self.console
        mock_plugin.isEnabled = Mock(return_value=False)
        when(self.console).getPlugin("mock").thenReturn(mock_plugin)
        self.console._plugins['mock'] = mock_plugin
        ###### MOCK COMMAND
        mock_func = Mock()
        mock_func.__name__ = 'cmd_mockfunc'
        self.adminPlugin._commands['mockcommand'] = Command(plugin=mock_plugin, cmd='mockcommand', level=100, func=mock_func)
        ###### MOCK EVENT
        mock_plugin.onSay = Mock()
        mock_plugin.registerEvent('EVT_CLIENT_SAY', mock_plugin.onSay)
        ###### MOCK CRON
        mock_plugin.mockCronjob = Mock()
        mock_plugin.mockCrontab = b3.cron.PluginCronTab(mock_plugin, mock_plugin.mockCronjob, minute='*', second= '*/60')
        self.console.cron.add(mock_plugin.mockCrontab)
        self.assertIn(id(mock_plugin.mockCrontab), self.console.cron._tabs)

        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!plugin unload mock")
        # THEN
        self.assertNotIn('mockcommand', self.adminPlugin._commands)
        self.assertIn(self.console.getEventID('EVT_CLIENT_SAY'), self.console._handlers)
        self.assertNotIn(mock_plugin, self.console._handlers[self.console.getEventID('EVT_CLIENT_SAY')])
        self.assertNotIn(id(mock_plugin.mockCrontab), self.console.cron._tabs)
        self.assertListEqual(['Plugin mock has been unloaded'], superadmin.message_history)

    ####################################################################################################################
    #                                                                                                                  #
    #   PLUGIN INFO                                                                                                    #
    #                                                                                                                  #
    ####################################################################################################################

    def test_cmd_plugin_info_with_no_plugin_name(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!plugin info")
        # THEN
        self.assertListEqual(['usage: !plugin info <name/s>'], superadmin.message_history)

    def test_cmd_plugin_info_with_valid_plugin_name(self):
        # GIVEN
        mock_module = Mock()
        mock_module.__setattr__('__author__', 'Mocker')
        mock_module.__setattr__('__version__', '1.1')
        when(self.console).pluginImport('mock').thenReturn(mock_module)
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!plugin info mock")
        # THEN
        self.assertListEqual(['You are running plugin mock v1.1 by Mocker'], superadmin.message_history)

    def test_cmd_plugin_info_with_valid_plugin_name_and_website_escape(self):
        # GIVEN
        mock_module = Mock()
        mock_module.__setattr__('__author__', 'Mocker - www.mocker.com')
        mock_module.__setattr__('__version__', '1.1')
        when(self.console).pluginImport('mock').thenReturn(mock_module)
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!plugin info mock")
        # THEN
        self.assertListEqual(['You are running plugin mock v1.1 by Mocker'], superadmin.message_history)

    def test_cmd_plugin_info_with_valid_plugin_name_and_email_escape(self):
        # GIVEN
        mock_module = Mock()
        mock_module.__setattr__('__author__', 'Mocker - info@mocker.co.uk')
        mock_module.__setattr__('__version__', '1.1')
        when(self.console).pluginImport('mock').thenReturn(mock_module)
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!plugin info mock")
        # THEN
        self.assertListEqual(['You are running plugin mock v1.1 by Mocker'], superadmin.message_history)