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

__author__ = 'Fenix'
__version__ = '1.2'

import b3
import b3.cron
import b3.plugin
import b3.plugins.admin
import b3.events
import glob
import os
import re
import sys

from b3 import __version__ as currentVersion
from b3.exceptions import MissingRequirement
from b3.functions import getCmd
from b3.functions import topological_sort
from b3.plugin import PluginData
from b3.update import B3version
from traceback import extract_tb

class PluginmanagerPlugin(b3.plugin.Plugin):

    _adminPlugin = None
    _reSplit = re.compile(r'''\w+''')
    _reParse = re.compile(r'''^(?P<command>\w+)\s*(?P<data>.*)$''')
    _protected = ('admin', 'publist', 'ftpytail', 'sftpytail', 'httpytail', 'cod7http', 'pluginmanager')

    ####################################################################################################################
    #                                                                                                                  #
    #    STARTUP                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def onStartup(self):
        """
        Initialize plugin settings.
        """
        self._adminPlugin = self.console.getPlugin('admin')

        # register our commands
        if 'commands' in self.config.sections():
            for cmd in self.config.options('commands'):
                level = self.config.get('commands', cmd)
                sp = cmd.split('-')
                alias = None
                if len(sp) == 2:
                    cmd, alias = sp

                func = getCmd(self, cmd)
                if func:
                    self._adminPlugin.registerCommand(self, cmd, level, func, alias)

        # notice plugin started
        self.debug('plugin started')

    ####################################################################################################################
    #                                                                                                                  #
    #    AUX METHODS                                                                                                   #
    #                                                                                                                  #
    ####################################################################################################################

    def do_enable(self, client, name=None):
        """
        Enable a plugin
        :param client: The client who launched the command
        :param name: The name of the plugin to enable
        """
        name = name.lower()
        if name in self._protected:
            client.message('^7Plugin ^1%s ^7is protected' % name)
        else:
            plugin = self.console.getPlugin(name)
            if not plugin:
                client.message('^7Plugin ^1%s ^7is not loaded' % name)
            else:
                if plugin.isEnabled():
                    client.message('^7Plugin ^3%s ^7is already enabled' % name)
                else:
                    plugin.enable()
                    client.message('^7Plugin ^3%s ^7is now ^2enabled' % name)

    def do_disable(self, client, name=None):
        """
        Disable a plugin
        :param client: The client who launched the command
        :param name: The name of the plugin to disable
        """
        name = name.lower()
        if name in self._protected:
            client.message('^7Plugin ^1%s ^7is protected' % name)
        else:
            plugin = self.console.getPlugin(name)
            if not plugin:
                client.message('^7Plugin ^1%s ^7is not loaded' % name)
            else:
                if not plugin.isEnabled():
                    client.message('^7Plugin ^3%s ^7is already disabled' % name)
                else:
                    plugin.disable()
                    client.message('^7Plugin ^3%s ^7is now ^1disabled' % name)

    def do_load(self, client, name=None):
        """
        Load a new plugin
        :param client: The client who launched the command
        :param name: The name of the plugin to load
        """
        def _get_plugin_config(p_name, p_clazz):
            """
            Helper that load and return a configuration file for the given Plugin
            :param p_name: The plugin name
            :param p_clazz: The class implementing the plugin
            """
            def _search_config_file(match):
                """
                Helper that returns a list of available configuration file paths for the given plugin.
                :param match: The plugin name
                """
                # first look in the built-in plugins directory
                search = '%s%s*%s*' % (b3.getAbsolutePath('@b3\\conf'), os.path.sep, match)
                self.debug('searching for configuration file(s) matching: %s' % search)
                collection = glob.glob(search)
                if len(collection) > 0:
                    return collection
                # if none is found, then search in the extplugins directory
                extplugins_dir = self.console.config.get_external_plugins_dir()
                search = '%s%s*%s*' % (os.path.join(b3.getAbsolutePath(extplugins_dir), match, 'conf'), os.path.sep, match)
                self.debug('searching for configuration file(s) matching: %s' % search)
                collection = glob.glob(search)
                return collection

            search_path = _search_config_file(p_name)
            if len(search_path) == 0:
                if p_clazz.requiresConfigFile:
                    raise b3.config.ConfigFileNotFound('could not find any configuration file')
                self.debug('no configuration file found for plugin %s: is not required either...' % p_name)
                return None
            if len(search_path) > 1:
                self.warning('multiple configuration files found for plugin %s: %s', p_name, ', '.join(search_path))

            self.debug('using %s as configuration file for plugin %s', search_path[0], p_name)
            self.bot('loading configuration file %s for plugin %s', search_path[0], p_name)
            return b3.config.load(search_path[0])

        name = name.lower()
        if name in self._protected:
            client.message('^7Plugin ^1%s ^7is protected' % name)
            return

        plugin = self.console.getPlugin(name)
        if plugin:
            client.message('^7Plugin ^2%s ^7is already loaded' % name)
            return

        try:
            mod = self.console.pluginImport(name)
            clz = getattr(mod, '%sPlugin' % name.title())
            cfg = _get_plugin_config(p_name=name, p_clazz=clz)
            plugin_data = PluginData(name=name, module=mod, clazz=clz, conf=cfg)
        except ImportError:
            client.message('^7Missing ^1%s ^7plugin python module' % name)
            client.message('^7Please put the plugin module in ^3@b3/extplugins/')
        except AttributeError:
            client.message('^7Plugin ^1%s ^7has an invalid structure: can\'t load' % name)
            client.message('^7Please inspect your b3 log file for more information')
            self.error('could not create plugin %s instance: %s' % (name, extract_tb(sys.exc_info()[2])))
        except b3.config.ConfigFileNotFound:
            client.message('^7Missing ^1%s ^7plugin configuration file' % name)
            client.message('^7Please put the plugin configuration file in ^3@b3/conf ^7or ^3@b3/extplugins/%s/conf' % name)
        except b3.config.ConfigFileNotValid:
            client.message('^7invalid configuration file found for plugin ^1%s' % name)
            client.message('^7Please inspect your b3 log file for more information')
            self.error('plugin %s has an invalid configuration file and can\'t be loaded: %s' % (name, extract_tb(sys.exc_info()[2])))
        else:

            plugin_required = []

            def _get_plugin_data(p_data):
                """
                Return a list of PluginData of plugins needed by the current one
                :param p_data: A PluginData containing plugin information
                :return: list[PluginData] a list of PluginData of plugins needed by the current one
                """
                # check for correct B3 version
                if p_data.clazz.requiresVersion and B3version(p_data.clazz.requiresVersion) > B3version(currentVersion):
                    raise MissingRequirement('plugin %s requires B3 version %s (you have version %s) : please update your '
                                             'B3 if you want to run this plugin' % (p_data.name, p_data.clazz.requiresVersion, currentVersion))

                # check if the current game support this plugin (this may actually exclude more than one plugin
                # in case a plugin is built on top of an incompatible one, due to plugin dependencies)
                if p_data.clazz.requiresParsers and self.console.gameName not in p_data.clazz.requiresParsers:
                    raise MissingRequirement('plugin %s is not compatible with %s parser : supported games are : %s' % (
                                             p_data.name, self.console.gameName, ', '.join(p_data.clazz.requiresParsers)))

                # check if the plugin needs a particular storage protocol to work
                if p_data.clazz.requiresStorage and self.console.storage.protocol not in p_data.clazz.requiresStorage:
                    raise MissingRequirement('plugin %s is not compatible with the storage protocol being used (%s) : '
                                             'supported protocols are : %s' % (p_data.name, self.console.storage.protocol,
                                                                               ', '.join(p_data.clazz.requiresStorage)))

                if p_data.clazz.requiresPlugins:
                    collection = []
                    for r in p_data.requiresPlugins:
                        if r not in self.console._plugins and r not in plugin_required:
                            try:
                                # missing requirement, try to load it
                                self.warning('plugin %s has unmet dependency : %s : trying to load plugin %s...' % (p_data.name, r, r))
                                collection += _get_plugin_data(PluginData(name=r))
                                self.debug('plugin %s dependency satisfied: %s' % r)
                            except Exception, err:
                                raise MissingRequirement('missing required plugin: %s' % r, err)

                    return collection

                # plugin has not been loaded manually nor a previous automatic load attempt has been done
                if p_data.name not in self.console._plugins and p_data.name not in plugin_required:
                    # we are at the bottom step where we load a new requirement by importing the
                    # plugin module, class and configuration file. If the following generate an exception, recursion
                    # will catch it here above and raise it back so we can exclude the first plugin in the list from load
                    self.debug('looking for plugin %s module and configuration file...' % p_data.name)
                    p_data.module = self.console.pluginImport(p_data.name)
                    p_data.clazz = getattr(p_data.module, '%sPlugin' % p_data.name.title())
                    p_data.conf = _get_plugin_config(p_data.name, p_data.clazz)
                    plugin_required.append(p_data.name) # load just once

                return [p_data]

            rollback = []

            try:

                plugin_list = _get_plugin_data(plugin_data)     # generate a list of PluginData (also requirements)
                plugin_dict = {x.name: x for x in plugin_list}  # dict(str, PluginData)
                sorted_list = [y for y in topological_sort([(x.name, set(x.clazz.requiresPlugins)) for x in plugin_list])]

                if len(sorted_list) > 1:
                    client.message('^7Plugin ^3%s ^7relies on other plugins to work: they will be automatically loaded' % name)

                for s in sorted_list:
                    p = plugin_dict[s]
                    self.bot('loading plugin %s [%s]', p.name, '--' if p.conf is None else p.conf.fileName)
                    plugin_instance = p.clazz(self.console, p.conf)
                    plugin_instance.onLoadConfig()
                    plugin_instance.onStartup()
                    self.console._plugins[p.name] = plugin_instance
                    v = getattr(p.module, '__version__', 'unknown')
                    a = getattr(p.module, '__author__', 'unknown')
                    self.bot('plugin %s (%s - %s) loaded', p.name, v, a)
                    client.message('^7Plugin ^2%s ^7(^3%s ^7- ^3%s^7) loaded' % p.name, v, a)
                    # queue an event so other plugins may react on this change (for example if 2 plugins provide the
                    # same functionalities, one of them can be disabled not to do duplicated work)
                    self.console.queueEvent(self.console.getEvent('EVT_PLUGIN_LOADED', data=p.name))
                    # track down all the plugins that we are enabling so we can rollback
                    # changes if a plugin in the dependency tree fails to load/start
                    rollback.append(p.name)

            except b3.exceptions.MissingRequirement:
                # here we do not have to rollback
                client.message('^7Plugin ^1%s can\'t be loaded due to unmet dependencies' % name)
                client.message('^7Please inspect your b3 log file for more information')
            except Exception, e:
                # here we rollback all the plugins loaded which are not needed anymore
                client.message('^7Could not load plugin ^1%s^7: %s' % (name, e))
                client.message('^7Please inspect your b3 log file for more information')
                self.error('plugin %s could not be loaded: %s' % (name, extract_tb(sys.exc_info()[2])))
                if rollback:
                    for name in rollback:
                        self.do_unload(client=client, name=name)

    def do_unload(self, client, name=None):
        """
        Unload a plugin
        :param client: The client who launched the command
        :param name: The name of the plugin to unload
        """
        name = name.lower()
        if name in self._protected:
            client.message('^7Plugin ^1%s ^7is protected' % name)
        else:
            plugin = self.console.getPlugin(name)
            if not plugin:
                client.message('^7Plugin ^1%s ^7is not loaded' % name)
            else:
                if plugin.isEnabled():
                    client.message('^7Plugin ^1%s ^7is currently enabled: disable it first' % name)
                else:
                    unreg = [x for x in self._adminPlugin._commands if self._adminPlugin._commands[x].plugin == plugin]
                    for command in unreg:
                        self._adminPlugin.unregisterCommand(command)

                    # unregister the event handler
                    self.console.unregisterHandler(plugin)

                    # remove all the crontabs bounded to this plugin
                    unreg = [x for x in self.console.cron._tabs
                                if isinstance(self.console.cron._tabs[x], b3.cron.PluginCronTab)
                                    and self.console.cron._tabs[x].plugin == plugin]

                    for tab in unreg:
                        self.console.cron.cancel(tab)

                    del self.console._plugins[name]
                    # queue an event so other plugins may react on this change
                    self.console.queueEvent(self.console.getEvent('EVT_PLUGIN_UNLOADED', data=name))
                    client.message('^7Plugin ^1%s ^7has been unloaded' % name)

    def do_info(self, client, name=None):
        """
        Display info on a specified plugin
        :param client: The client who launched the command
        :param name: The name of the plugin whose info needs to be displayed
        """
        try:
            module = self.console.pluginImport(name.lower())
        except ImportError:
            client.message('^7Plugin ^1%s ^7is not loaded' % name)
        else:
            a = getattr(module, '__author__', 'unknown')
            v = getattr(module, '__version__', 'unknown')
            # cleanup a bit the author so it prints nice
            for r in [re.compile(r'(?:http[s]?://|www.)[^\s]*'),                         # website
                      re.compile(r'[a-zA-Z0-9._%-+]+@[a-zA-Z0-9._%-]+.[a-zA-Z]{2,6}')]:  # email
                a = re.sub(r, '', a)
                a = re.sub(re.compile(r'-|\|'), '', a).strip()
            client.message('^7You are running plugin ^3%s ^7v%s by %s' % (name, v, a))

    ####################################################################################################################
    #                                                                                                                  #
    #    MAIN METHODS                                                                                                  #
    #                                                                                                                  #
    ####################################################################################################################

    def plugin_enable(self, client, data=None):
        """
        Enable a plugin or a set of plugins
        :param client: The client who launched the command
        :param data: A comma/space separated list of plugin to enable
        """
        plugin_list = [x.lower() for x in self._reSplit.findall(data or '')]
        if not plugin_list:
            client.message('^7usage: %splugin enable <name/s>' % self._adminPlugin.cmdPrefix)
        else:
            for plugin in plugin_list:
                self.do_enable(client, plugin)

    def plugin_disable(self, client, data=None):
        """
        Disable a plugin or a set of plugins
        :param client: The client who launched the command
        :param data: A comma/space separated list of plugins to disable
        """
        plugin_list = [x.lower() for x in self._reSplit.findall(data or '')]
        if not plugin_list:
            client.message('^7usage: %splugin disable <name/s>' % self._adminPlugin.cmdPrefix)
        else:
            for plugin in plugin_list:
                self.do_disable(client, plugin)

    def plugin_list(self, client, data=None):
        """
        List loaded plugins
        :param client: The client who launched the command
        """
        plugin_list = self.console._plugins.keys()
        plugin_list.sort()
        plugin_list = ['^2' + x if self.console.getPlugin(x).isEnabled() else '^1' + x for x in plugin_list]
        client.message('^7Loaded plugins: %s' % '^3, ^7'.join(plugin_list))

    def plugin_load(self, client, data=None):
        """
        Load a new plugin or a set of plugins
        :param client: The client who launched the command
        :param data: A comma/space separated list of plugins to load
        """
        plugin_list = [x.lower() for x in self._reSplit.findall(data or '')]
        if not plugin_list:
            client.message('^7usage: %splugin load <name/s>' % self._adminPlugin.cmdPrefix)
        else:
            for plugin in plugin_list:
                self.do_load(client, plugin)

    def plugin_unload(self, client, data=None):
        """
        Unload a plugin or a set of plugins
        :param client: The client who launched the command
        :param data: A comma/space separated list of plugins to load
        """
        plugin_list = [x.lower() for x in self._reSplit.findall(data or '')]
        if not plugin_list:
            client.message('^7usage: %splugin unload <name/s>' % self._adminPlugin.cmdPrefix)
        else:
            for plugin in plugin_list:
                self.do_unload(client, plugin)

    def plugin_info(self, client, data=None):
        """
        Display information on a plugin or a set of plugins
        :param client: The client who launched the command
        :param data: A comma/space separated list of plugins whose info needs to be displayed
        """
        plugin_list = [x.lower() for x in self._reSplit.findall(data or '')]
        if not plugin_list:
            client.message('^7usage: %splugin info <name/s>' % self._adminPlugin.cmdPrefix)
        else:
            for plugin in plugin_list:
                self.do_info(client, plugin)

    ####################################################################################################################
    #                                                                                                                  #
    #    COMMANDS                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def cmd_plugin(self, data, client, cmd=None):
        """
        <action> [<plugin>] - manage plugins
        """
        if not data or not self._reParse.match(data):
            client.message('^7invalid data, try ^3%s^7help plugin' % self._adminPlugin.cmdPrefix)
        else:
            match = self._reParse.match(data)
            command_list = [m[7:] for m in dir(self) if callable(getattr(self, m)) and m.startswith('plugin_')]
            if not match.group('command') in command_list:
                command_list.sort()
                client.message('^7usage: %splugin <%s> [<data>]' % (self._adminPlugin.cmdPrefix, '|'.join(command_list)))
            else:
                try:
                    func = getattr(self, 'plugin_%s' % match.group('command'))
                    func(client=client, data=match.group('data'))
                except Exception, e:
                    client.message('unhandled exception: %s' % e)