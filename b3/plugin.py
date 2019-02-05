# -*- coding: utf-8 -*-

# ################################################################### #
#                                                                     #
#  BigBrotherBot (B3) (www.bigbrotherbot.net)                         #
#  Copyright (C) 2018 Daniele Pantaleone <danielepantaleone@me.com>   #
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


import abc

import b3
import collections
import configparser
import re
import typing
import types

from distutils.version import StrictVersion
from importlib.machinery import SourceFileLoader

from .events import Event, EventType
from .files import FileManager
from .functions import rchop, topological_sort
from .output import LoggerMixin
from .parser import Parser


class Plugin(object):
    """B3 base plugin implementation"""

    __metaclass__ = abc.ABCMeta

    # -----------------------------------------------------
    # PLUGIN REQUIREMENTS
    # -----------------------------------------------------

    required_parsers: typing.Set[str] = {}
    """Set of parsers supported by the plugin (if empty B3 assumes the plugin non-parser dependent)"""

    required_plugins: typing.Set[str] = {}
    """Set of plugins required to run this very plugin (if one of these is missing, the plugin won't be loaded)"""

    required_version: str = b3.__version__
    """The minimum B3 version necessary to run this plugin (i.e: 2.0): default to current B3 version"""

    def __init__(self, console:Parser, config:configparser.ConfigParser):
        super(Plugin, self).__init__()
        self.config = config
        self.console = console
        self._enabled = True

    # -----------------------------------------------------
    # PROPERTIES
    # -----------------------------------------------------

    @property
    def name(self):
        """Returns the plugin name"""
        return rchop(self.__class__.__name__.lower(), 'plugin')

    # -----------------------------------------------------
    # MISC
    # -----------------------------------------------------

    def enable(self):
        """Enable the plugin"""
        self._enabled = True
        self.onEnable() # this very plugin should be notified instantly while other plugins wait for the event
        self.console.events.post(Event(type=EventType.PLUGIN_ENABLED, data={'name':self.name}))

    def disable(self):
        """Disable the plugin"""
        self._enabled = False
        self.onDisable() # this very plugin should be notified instantly while other plugins wait for the event
        self.console.events.post(Event(type=EventType.PLUGIN_DISABLED, data={'name':self.name}))

    def isEnabled(self) -> bool:
        """Returns True if the plugin is enabled, False otherwise"""
        return self._enabled

    # -----------------------------------------------------
    # HOOKS
    # -----------------------------------------------------

    def onDisable(self):
        """Executed when the plugin is disabled"""
        pass

    def onEnable(self):
        """Executed when the plugin is enabled"""
        pass

    def onEvent(self, event:Event):
        """Executed when an event is received by the plugin"""
        pass

    def onStartup(self):
        """Executed by the parser tp allow plugins to perform startup operations"""
        pass

    # -----------------------------------------------------
    # LOGGING
    # -----------------------------------------------------

    def debug(self, msg:str, *args, **kwargs):
        """Log a DEBUG message"""
        self.console.debug('%s: %s' % (self.__class__.__name__, msg), *args, **kwargs)

    def error(self, msg:str, *args, **kwargs):
        """Log a ERROR message"""
        self.console.error('%s: %s' % (self.__class__.__name__, msg), *args, **kwargs)

    def info(self, msg:str, *args, **kwargs):
        """Log a INFO message"""
        self.console.info('%s: %s' % (self.__class__.__name__, msg), *args, **kwargs)

    def verbose(self, msg:str, *args, **kwargs):
        """Log a VERBOSE message"""
        self.console.verbose('%s: %s' % (self.__class__.__name__, msg), *args, **kwargs)

    def warning(self, msg:str, *args, **kwargs):
        """Log a WARNING message"""
        self.console.warning('%s: %s' % (self.__class__.__name__, msg), *args, **kwargs)


class PluginManager(LoggerMixin, object):
    """B3 plugin manager implementation"""

    def __init__(self, console:Parser, config:configparser.ConfigParser):
        super(PluginManager, self).__init__()
        self._plugins = collections.OrderedDict()
        self.fs = FileManager()
        self.console = console
        self.config = config

    def init_plugins(self):
        """Load all the plugins and load their configuration file"""
        plugins_found:typing.Dict[str, tuple] = {} # unsorted dict of available plugins
        plugins_ok:typing.Dict[str, tuple] = {} # unsorted dict of plugins that meets dependencies
        plugins_sorted:typing.List[str] = [] # list of plugin names sorted according to their requirements

        def find_plugin_module(name:str) -> typing.Tuple[types.ModuleType, str]:
            root = self.fs.join('@plugins', name, name)
            for extension in ('.pyc', '.pyo', '.py'):
                path = '{0}{1}'.format(root, extension)
                if self.fs.isFile(path):
                    self.verbose('Found plugin %s module at %s', name, path)
                    break
            else:
                raise IOError('no module named {0} at {1}.py[c|o]'.format(name, root))
            module = SourceFileLoader(name, path).load_module()
            return module, path

        def find_plugin_class(module:types.ModuleType, path:str, name:str) -> typing.Type['Plugin']:
            imp = '{0}Plugin'.format(''.join(x.title() for x in list(filter(None, re.split("[_\-]+", name)))))
            if not hasattr(module, imp):
                raise AttributeError('no class named {0} found in module {1}'.format(imp, path))
            return getattr(module, imp)

        def find_plugin_config(name:str):
            path = self.fs.expand(self.config.get('plugins', plugin_name))
            if not self.fs.isFile(path):
                raise IOError('missing configuration file {0} for plugin {1}'.format(path, name))
            self.verbose('Found plugin %s configuration at %s', name, path)
            return path

        # --- SEARCHING PLUGINS ---------------------------

        if self.config.has_section('plugins'):

            options = self.config.options('plugins')
            self.debug('Searching %d plugins: %s', len(options), ', '.join(options))
            for plugin_name in options:
                try:
                    plugin_module, plugin_path = find_plugin_module(plugin_name)
                    plugin_imp = find_plugin_class(plugin_module, plugin_path, plugin_name)
                    plugin_config = find_plugin_config(plugin_name)
                except Exception:
                    self.exception('Could not load plugin %s', plugin_name)
                else:
                    plugins_found[plugin_name] = (plugin_module, plugin_imp, plugin_config)

            self.debug('Found %d plugins: %s', len(plugins_found), ', '.join(x for x in plugins_found))

        # --- CHECK REQUIREMENTS --------------------------

        if 'admin' not in plugins_found:
            self.critical('Missing admin plugin: cannot continue without admin plugin!')

        for plugin_name in plugins_found:

            try:
                plugin_imp = plugins_found[plugin_name][1]
                if plugin_imp.required_version and StrictVersion(plugin_imp.required_version) > StrictVersion(b3.__version__):
                    raise RuntimeError('minimum B3 required version is {0}'.format(plugin_imp.required_version))
                if plugin_imp.required_parsers and self.console.name not in plugin_imp.required_parsers:
                    raise RuntimeError('supported games are <{0}>'.format(','.join(plugin_imp.required_parsers)))
                if plugin_imp.required_plugins:
                    for plugin in plugin_imp.required_plugins:
                        if plugin not in plugins_found:
                            raise RuntimeError('additional required plugins are <{0}>'.format(','.join(plugin_imp.required_plugins)))
            except Exception:
                self.exception('Missing requirement in %s plugin', plugin_name)
            else:
                plugins_ok[plugin_name] = plugins_found[plugin_name]

        # --- SORT ACCORDING TO THEIR REQUIREMENTS --------

        for plugin_name in [y for y in \
            topological_sort([(plugin_name, set(plugins_ok[plugin_name][1].required_plugins)) \
                for plugin_name in plugins_ok])]:
            plugins_sorted.append(plugin_name)
        plugins_sorted.remove('admin')
        plugins_sorted.insert(0, 'admin')

        # --- CREATE INSTANCES ----------------------------

        i = 1
        for plugin_name in plugins_sorted:
            try:
                plugin_module = plugins_ok[plugin_name][0]
                plugin_imp = plugins_ok[plugin_name][1]
                plugin_config = plugins_ok[plugin_name][2]
                self.debug('Loading plugin #%s : %s [%s]', i, plugin_name, plugin_config)
                config = configparser.ConfigParser()
                config.read(plugin_config)
                plugin = plugin_imp(console=self.console, config=config)
            except Exception:
                self.exception('Could not create %s plugin instance', plugin_name)
            else:
                i += 1
                self._plugins[plugin_name] = plugin
                version = getattr(plugin_module, '__version__', '<unknown>')
                author = getattr(plugin_module, '__author__', '<unknown>')
                self.debug('Loaded plugin %s version %s by %s)', plugin_name, version, author)

    def start_plugins(self):
        """Start all the loaded plugins"""
        i = 1
        for plugin_name in self._plugins:
            try:
                self.debug('Starting plugin #%s: %s', i, plugin_name)
                plugin = self._plugins[plugin_name]
                plugin.onStartup()
            except Exception:
                self.exception('Could not start %s plugin', plugin_name)
            else:
                i += 1