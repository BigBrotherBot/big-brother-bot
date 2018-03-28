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
import configparser
import typing

from .events import Event, EventType
from .functions import rchop
from .parser import Parser


class Plugin(object):
    """B3 base plugin implementation"""

    __metaclass__ = abc.ABCMeta

    # #########################################################################
    # PLUGIN REQUIREMENTS
    # #########################################################################

    required_parsers: typing.Set['Parser'] = {}
    """Set of parsers supported by the plugin (if empty B3 assumes the plugin non-parser dependent)"""

    required_plugins: typing.Set['Plugin'] = {}
    """Set of plugins required to run this very plugin (if one of these is missing, the plugin won't be loaded)"""

    required_version: str = b3.__version__
    """The minimum B3 version necessary to run this plugin (i.e: 2.0): default to current B3 version"""

    def __init__(self, console:Parser, config:configparser.ConfigParser):
        super(Plugin, self).__init__()
        self.config = config
        self.console = console
        self._enabled = True

    # #########################################################################
    # PROPERTIES
    # #########################################################################

    @property
    def name(self):
        """Returns the plugin name"""
        return rchop(self.__class__.__name__.lower(), 'plugin')

    # #########################################################################
    # MISC
    # #########################################################################

    def enable(self):
        """Enable the plugin"""
        self._enabled = True
        self.onEnable()
        self.console.events.post(Event(type=EventType.PLUGIN_ENABLED, data={'name':self.name}))

    def disable(self):
        """Disable the plugin"""
        self._enabled = False
        self.onDisable()
        self.console.events.post(Event(type=EventType.PLUGIN_DISABLED, data={'name': self.name}))

    def isEnabled(self) -> bool:
        """Returns True if the plugin is enabled, False otherwise"""
        return self._enabled

    # #########################################################################
    # HOOKS
    # #########################################################################

    def onDisable(self):
        """Executed when the plugin is disabled"""

    def onEnable(self):
        """Executed when the plugin is enabled"""

    def onEvent(self, event:Event):
        """Executed when an event is received by the plugin"""
        pass

    def onLoadConfig(self, config:configparser.ConfigParser):
        """Executed by the parser to allow plugins to load a configuration file"""
        pass

    def onStartup(self):
        """Executed by the parser the allow plugins to perform startup operations"""
        pass

    # #########################################################################
    # LOGGING
    # #########################################################################

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