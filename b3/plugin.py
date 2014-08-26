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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
#
# CHANGELOG
#
# 11/29/2005 - 1.3.0 - ThorN     - added warning, info, exception, and critical log handlers
# 14/11/2009 - 1.3.1 - Courgette - display a user friendly error message when a plugin config file as broken XML
# 29/11/2009 - 1.4.0 - Courgette - constructor now also accepts an instance of Config in place of a config file name
# 29/11/2009 - 1.4.1 - Courgette - the on_load_config callback is now always called after load_config() is called.
#                                  this aims to make sure on_load_config is called after the user use the !reconfig
#                                  command
# 16/02/2013 - 1.5   - Courgette - add plugin property _default_messages to store default plugin messages
#                                - add user friendly warning and error to the log when a messaged cannot be formatted
# 2013/10/23 - 1.6   - Courgette - on_load_config hook is now called by the parser instead of at plugin instantiation
# 2013/11/30 - 1.7   - Courgette - add two plugin hooks: on_enable and on_disable
# 12/08/2013 - 1.8   - Fenix     - adjust syntax to match PEP8 + fixed some typos
#                                - optionally map a specific event onto a specific plugin method: needs to
#                                  be specified during event registration
# 15/04/2014 - 1.8.1 - Fenix     - use self.console.get_event_id to retrieve event ids: remove some warnings
# 21/05/2014 - 1.8.2 - Fenix     - minor syntax cleanup
#                                - moved event mapping function into Parser class
# 02/06/2014 - 1.8.3 - Fenix     - moved back event mapping logic into Plugin class: Parser should be aware only of
#                                  Plugins listening for incoming events and not how to dispatch them: for more info
#                                  see https://github.com/BigBrotherBot/big-brother-bot/pull/193
#                                - added possibility to register multiple event hooks for the same event inside a plugin
# 28/07/2014 - 1.9   - Fenix     - syntax cleanup
#                                - added default event mapping hooks for EVT_EXIT and EVT_STOP

__author__ = 'ThorN, Courgette'
__version__ = '1.9'

import b3.config
import b3.events
import b3.functions

from b3.decorators import deprecated
from ConfigParser import NoOptionError


class Plugin:

    _default_messages = {}      # plugin developers : customize this
    _enabled = True
    _messages = {}

    config = None
    console = None
    eventmanager = None
    eventmap = None
    events = []
    requiresConfigFile = True   # plugin developers : customize this
    working = True

    def __init__(self, console, config=None):
        """
        Object constructor.
        :param console: The console implementation
        :param config: The plugin configuration file
        """
        self.console = console
        self.eventmanager = b3.events.eventManager
        self.eventmap = dict()
        if isinstance(config, b3.config.XmlConfigParser) \
           or isinstance(config, b3.config.CfgConfigParser):
            self.config = config
        else:
            try:
                self.loadConfig(config)
            except b3.config.ConfigFileNotValid, e:
                self.critical("The config file XML syntax is broken: %s" % e)
                self.critical("Use a XML editor to modify your config files: it makes easy to spot errors")
                raise 

        self.registerEvent(self.console.getEventID('EVT_STOP'), self.onStop)
        self.registerEvent(self.console.getEventID('EVT_EXIT'), self.onExit)

    def enable(self):
        """
        Enable the plugin.
        """
        self._enabled = True
        self.onEnable()

    def disable(self):
        """
        Disable the plugin.
        """
        self._enabled = False
        self.onDisable()

    def isEnabled(self):
        """
        Check whether this plugin is enabled.
        :return True if the plugin is enabled, False otherwise
        """
        return self._enabled

    def getMessage(self, msg, *args):
        """
        Return a message from the config file.
        :param msg: The message name
        :param args: The message variables
        """
        try:
            _msg = self._messages[msg]
        except KeyError:
            try:
                self._messages[msg] = self.config.getTextTemplate('messages', msg)
            except NoOptionError:
                self.warning("config file is missing %r in section 'messages'" % msg)
                if msg in self._default_messages:
                    self._messages[msg] = b3.functions.vars2printf(self._default_messages[msg]).strip()
                else:
                    raise
            _msg = self._messages[msg]

        if len(args) == 1 and type(args[0]) is dict:
            try:
                return _msg % args[0]
            except KeyError, err:
                self.error("failed to format message %r (%r) with parameters %r: "
                           "missing value for %s", msg, _msg, args, err)
                raise
        else:
            try:
                return _msg % args
            except TypeError, err:
                self.error("failed to format message %r (%r) with parameters %r: %s", msg, _msg, args, err)
                raise

    def loadConfig(self, filename=None):
        """
        Load the plugin configuration file.
        :param filename: The plugin configuration file name
        """
        if filename:
            self.bot('loading config %s for %s', filename, self.__class__.__name__)
            try:
                self.config = b3.config.load(filename)
            except b3.config.ConfigFileNotFound:
                if self.requiresConfigFile:
                    self.critical('could not find config file %s' % filename)
                    return False
                else:
                    self.bot('no config file found for %s: was not required either' % self.__class__.__name__)
                    return True
        elif self.config:
            self.bot('loading config %s for %s', self.config.fileName, self.__class__.__name__)
            self.config = b3.config.load(self.config.fileName)
        else:
            if self.requiresConfigFile:
                self.error('could not load config for %s', self.__class__.__name__)
                return False
            else:
                self.bot('no config file found for %s: was not required either' % self.__class__.__name__)
                return True
            
        # empty message cache
        self._messages = {}

    def saveConfig(self):
        """
        Save the plugin configuration file.
        """
        self.bot('saving config %s', self.config.fileName)
        return self.config.save()

    def registerEventHook(self, name, hook):
        """
        Register an event hook which will be used to
        dispatch a specific event once it reaches our plugin.
        NOTE: This should be only called internally by registerEvent().
        :param name: The event name
        :param hook: The event hook
        """
        readable_name = self.eventmanager.getName(name)
        if name not in self.events:
             # make sure the event we are going to map has been registered already
             raise AssertionError('%s is not an event registered for plugin %s' % (readable_name, self.__class__.__name__))

        hook = getattr(self, hook.__name__, None)
        if not callable(hook):
            # make sure the given hook to be a valid method of our plugin
            raise AttributeError('%s is not a valid method of class %s' % (hook.__name__, self.__class__.__name__))

        # if it's the first time we are mapping
        if not name in self.eventmap.keys():
            self.eventmap[name] = []

        # create the mapping
        if hook not in self.eventmap[name]:
            self.eventmap[name].append(hook)
        self.debug('created event mapping: %s:%s' % (readable_name, hook.__name__))

    def registerEvent(self, name, *args):
        """
        Register an event for later processing.
        :param name: The event name
        :param args: An optional list of event handlers
        """
        self.events.append(name)
        self.console.registerHandler(name, self)
        if len(args) > 0:
            for hook in args:
                try:
                    self.registerEventHook(name, hook)
                except (AssertionError, AttributeError), e:
                    self.error('could not register event hook: %s' % e)
        else:
            try:
                self.registerEventHook(name, self.onEvent)
            except (AssertionError, AttributeError), e:
                self.error('could not register event hook: %s' % e)

    def createEvent(self, key, name):
        """
        Create a new event.
        :param key: The event key.
        :param name: The event name.
        """
        self.console.createEvent(key, name)

    def start(self):
        """
        Called after Plugin.startup().
        """
        pass

    def parseEvent(self, event):
        """
        Dispatch an Event.
        :param event: The event to be dispatched
        """
        collection = self.eventmap[event.type]
        for func in collection:
            try:
                func(event)
            except TypeError, e:
                self.error('could not parse event %s: %s' % (event.type, e))

        if event.type == self.console.getEventID('EVT_EXIT') or \
            event.type == self.console.getEventID('EVT_STOP'):
            self.working = False

    ####################################################################################################################
    ##                                                                                                                ##
    ##  LOGGING METHODS                                                                                               ##
    ##                                                                                                                ##
    ####################################################################################################################

    def error(self, msg, *args, **kwargs):
        """
        Log an ERROR message to the main log.
        """
        self.console.error('%s: %s' % (self.__class__.__name__, msg), *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        """
        Log a DEBUG message to the main log.
        """
        self.console.debug('%s: %s' % (self.__class__.__name__, msg), *args, **kwargs)

    def bot(self, msg, *args, **kwargs):
        """
        Log a BOT message to the main log.
        """
        self.console.bot('%s: %s' % (self.__class__.__name__, msg), *args, **kwargs)

    def verbose(self, msg, *args, **kwargs):
        """
        Log a VERBOSE message to the main log. More "chatty" than a debug message.
        """
        self.console.verbose('%s: %s' % (self.__class__.__name__, msg), *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        """
        Log a WARNING message to the main log.
        """        
        self.console.warning('%s: %s' % (self.__class__.__name__, msg), *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        """
        Log an INFO message to the main log.
        """        
        self.console.info('%s: %s' % (self.__class__.__name__, msg), *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        """
        Log an EXCEPTION message to the main log.
        """        
        self.console.exception('%s: %s' % (self.__class__.__name__, msg), *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        """
        Log a CRITICAL message to the main log.
        """
        self.console.critical('%s: %s' % (self.__class__.__name__, msg), *args, **kwargs)

    ####################################################################################################################
    ##                                                                                                                ##
    ##  PLUGIN HOOKS                                                                                                  ##
    ##  INHERITING CLASSES CAN IMPLEMENT THE FOLLOWING METHODS                                                        ##
    ##                                                                                                                ##
    ####################################################################################################################

    def onLoadConfig(self):
        """
        This is called after loadConfig() and if a user use the !reconfig command.
        Any plugin private variables loaded from the config need to be reset here.
        """
        return True

    def onStartup(self):
        """
        Called after the plugin is created before it is started. Overwrite this
        for anything you need to initialize you plugin with.
        """
        self.startup()  # support backwards compatibility

    def onEvent(self, event):
        """
        Called when a registered event is received.
        """
        self.handle(event)  # support backwards compatibility

    def onEnable(self):
        """
        Called when the plugin is enabled.
        """
        pass

    def onDisable(self):
        """
        Called when the plugin is disabled.
        """
        pass

    ####################################################################################################################
    ##                                                                                                                ##
    ##  EVENT HANDLERS                                                                                                ##
    ##  THOSE ARE DEFAULT EVENT HANDLERS WHICH MAY BE OVERRIDDEN IN PLUGIN CLASSES                                    ##
    ##                                                                                                                ##
    ####################################################################################################################

    def onExit(self, event):
        """
        Perform operations when EVT_EXIT is received.
        :param event: The event to be handled
        """
        pass

    def onStop(self, event):
        """
        Perform operations when EVT_STOP is received.
        :param event: The event to be handled
        """
        pass

    ####################################################################################################################
    ##                                                                                                                ##
    ##  DEPRECATED METHODS                                                                                            ##
    ##                                                                                                                ##
    ####################################################################################################################

    @deprecated
    def handle(self, event):
        """
        Deprecated. Use onEvent().
        """
        pass

    @deprecated
    def startup(self):
        """
        Deprecated. Use onStartup().
        """
        pass