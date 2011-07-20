#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2005 Michael "ThorN" Thornton
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
#
# CHANGELOG
#    11/29/2005 - 1.3.0 - ThorN
#    Added warning, info, exception, and critical log handlers
#    14/11/2009 - 1.3.1 - Courgette
#    display a user friendly error message when a plugin config file as broken XML
#    29/11/2009 - 1.4.0 - Courgette
#    constructor now also accepts an instance of Config in place of a config file name
#    29/11/2009 - 1.4.1 - Courgette
#    the onLoadConfig callback is now always called after loadConfig() is called. This
#    aims to make sure onLoadConfig is called after the user use the !reconfig command
#
__author__  = 'ThorN'
__version__ = '1.4.1'

import os
import b3.config
import b3.events

class Plugin:
    _enabled = True
    console = None
    events = []
    config = None
    working = True
    requiresConfigFile = True

    _messages = {}

    def __init__(self, console, config=None):
        self.console = console
        
        if isinstance(config, b3.config.XmlConfigParser) \
            or isinstance(config, b3.config.CfgConfigParser):
            self.config = config
        else:
            try:
                self.loadConfig(config)
            except b3.config.ConfigFileNotValid, e:
                self.critical("The config file XML syntax is broken: %s" %e)
                self.critical("Use a XML editor to modify your config files, it makes easy to spot errors")
                raise 

        self.registerEvent(b3.events.EVT_STOP)
        self.registerEvent(b3.events.EVT_EXIT)

    def enable(self):
        self._enabled = True

    def disable(self):
        self._enabled = False

    def isEnabled(self):
        return self._enabled

    def getMessage(self, msg, *args):
        try:
            msg = self._messages[msg]
        except KeyError:
            self._messages[msg] = self.config.getTextTemplate('messages', msg)
            msg = self._messages[msg]

        if len(args) == 1:
            if type(args[0]) is dict:
                return msg % args[0]
            else:
                return msg % args
        else:
            return msg % args

    def loadConfig(self, fileName=None):
        if fileName:
            self.bot('Loading config %s for %s', fileName, self.__class__.__name__)
            try:
                self.config = b3.config.load(fileName)
            except b3.config.ConfigFileNotFound, e:
                if self.requiresConfigFile:
                    self.critical('Could not find config file %s' % fileName)
                    return False
                else:
                    self.bot('No config file found for %s. (was not required either)'%self.__class__.__name__)
                    return True
        elif self.config:
            self.bot('Loading config %s for %s', self.config.fileName, self.__class__.__name__)
            self.config = b3.config.load(self.config.fileName)
        else:
            if self.requiresConfigFile:
                self.error('Could not load config for %s', self.__class__.__name__)
                return False
            else:
                self.bot('No config file found for %s. (was not required either)'%self.__class__.__name__)
                return True
            
        # empty message cache
        self._messages = {}

        self.onLoadConfig()


    def onLoadConfig(self):
        """\
        This is called after loadConfig(). Any plugin private variables loaded
        from the config need to be reset here.
        """
        return True

    def saveConfig(self):
        self.bot('Saving config %s', self.config.fileName)
        return self.config.save()

    def registerEvent(self, eventName):
        self.events.append(eventName)
        self.console.registerHandler(eventName, self)

    def createEvent(self, key, name):
        self.console.createEvent(key, name)

    def startup(self):
        """\
        Depreciated. Use onStartup().
        """
        pass

    def onStartup(self):
        """\
        Called after the plugin is created before it is started. Overwrite this
        for anything you need to initialize you plugin with.
        """

        # support backwards compatability
        self.startup()

    def start(self):
        """\
        Called after Plugin.startup().
        """
        pass

    def parseEvent(self, event):
        self.onEvent(event)

        if event.type == b3.events.EVT_EXIT or event.type == b3.events.EVT_STOP:
            self.working = False

    def handle(self, event):
        """\
        Depreciated. Use onEvent().
        """
        self.verbose('Warning: No handle func for %s', self.__class__.__name__)

    def onEvent(self, event):
        """\
        Called by B3 when a registered event is encountered. You must overwrite
        this to intercept events.
        """

        # support backwards compatability
        self.handle(event)

    def error(self, msg, *args, **kwargs):
        """\
        Log an error message to the main log.
        """
        self.console.error('%s: %s' % (self.__class__.__name__, msg), *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        """\
        Log a debug message to the main log.
        """
        self.console.debug('%s: %s' % (self.__class__.__name__, msg), *args, **kwargs)

    def bot(self, msg, *args, **kwargs):
        """\
        Log a bot message to the main log.
        """
        self.console.bot('%s: %s' % (self.__class__.__name__, msg), *args, **kwargs)

    def verbose(self, msg, *args, **kwargs):
        """\
        Log a verbose message to the main log. More "chatty" than a debug message.
        """
        self.console.verbose('%s: %s' % (self.__class__.__name__, msg), *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        """\
        Log a warning message to the main log.
        """        
        self.console.warning('%s: %s' % (self.__class__.__name__, msg), *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        """\
        Log an info message to the main log.
        """        
        self.console.info('%s: %s' % (self.__class__.__name__, msg), *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        """\
        Log an exception message to the main log.
        """        
        self.console.exception('%s: %s' % (self.__class__.__name__, msg), *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        """\
        Log a critical message to the main log.
        """
        self.console.critical('%s: %s' % (self.__class__.__name__, msg), *args, **kwargs)