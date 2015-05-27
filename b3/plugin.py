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
# 29/11/2009 - 1.4.1 - Courgette - the onLoadConfig callback is now always called after loadConfig() is called.
#                                  this aims to make sure on_load_config is called after the user use the !reconfig
#                                  command
# 16/02/2013 - 1.5   - Courgette - add plugin property _default_messages to store default plugin messages
#                                - add user friendly warning and error to the log when a messaged cannot be formatted
# 2013/10/23 - 1.6   - Courgette - on_load_config hook is now called by the parser instead of at plugin instantiation
# 2013/11/30 - 1.7   - Courgette - add two plugin hooks: onEnable and onDisable
# 12/08/2013 - 1.8   - Fenix     - adjust syntax to match PEP8 + fixed some typos
#                                - optionally map a specific event onto a specific plugin method: needs to
#                                  be specified during event registration
# 15/04/2014 - 1.8.1 - Fenix     - use self.console.getEventID to retrieve event ids: remove some warnings
# 21/05/2014 - 1.8.2 - Fenix     - minor syntax cleanup
#                                - moved event mapping function into Parser class
# 02/06/2014 - 1.8.3 - Fenix     - moved back event mapping logic into Plugin class: Parser should be aware only of
#                                  Plugins listening for incoming events and not how to dispatch them: for more info
#                                  see https://github.com/BigBrotherBot/big-brother-bot/pull/193
#                                - added possibility to register multiple event hooks for the same event inside a plugin
# 28/07/2014 - 1.9   - Fenix     - syntax cleanup
#                                - added default event mapping hooks for EVT_EXIT and EVT_STOP
# 08/01/2015 - 1.9.1 - Fenix     - make sure not to load 'None' object as configuration file
# 08/03/2015 - 1.9.2 - Fenix     - added requiresPlugins attribute in Plugin class
#                                - added PluginData class
#                                - produce EVT_PLUGIN_ENABLED ands EVT_PLUGIN_DISABLED
# 17/02/2015 - 1.9.3 - Fenix     - allow plugins to register events using both event key and event id: this allows
#                                  plugin developers to write less code
# 21/03/2015 - 1.9.4 - Fenix     - added requiresParsers attribute in Plugin class: customizable with a list of game
#                                  names the plugin will work on (will reduce the amount of code needed to filter out
#                                  unsupported games inside plugins)
# 25/03/2015 - 1.9.5 - Fenix     - added loadAfterPlugins attribute: specify a list of plugins which needs to be loaded
#                                  before the current one
# 06/04/2015 - 1.9.6 - Fenix     - inherit from object class (new-style-class format to support super() in methods call)
# 21/05/2015 - 1.9.7 - Fenix     - added requiresVersion attribute in plugin class: declares the minimum required
#                                  B3 version needed to run the current plugin (if nothing is specified then the plugin
#                                  will be loaded no matter the version of B3 currently running)
#                                - added Plugin class documentation

__author__ = 'ThorN, Courgette'
__version__ = '1.9.7'

import b3.config
import b3.events
import b3.functions

from b3 import __version__ as b3_version
from ConfigParser import NoOptionError


class Plugin(object):
    """
    This class implements a B3 plugin.
    All the B3 plugins MUST inherit from this one and properly overriding methods and attributes.
    The plugin startup sequence is the following:

        1) call to Plugin.__init__()
        2) call to Plugin.onLoadConfig()
        3) call to Plugin.onStartup()

    If in your plugin you need to initialize some attributes, you can do so by declaring them as class attributes (and
    so all the object instantiated from the plugin class will have them), or (correct way) you can initialize them in
    the plugin constructor, making sure to call the original Plugin constructor before doing anything else (needed
    in case you want to access self.console and self.config from withing the constructor), i.e:

    >>> class MyPlugin(Plugin):
    >>>
    >>>     def __init__(self, console, config=None):
    >>>         Plugin.__init__(self, console, config)
    >>>         # you can get the admin plugin object instance here too
    >>>         self._admin_plugin = self.console.getPlugin('admin')
    >>>         self._my_attribute_1 = 'something'
    >>>         self._my_attribute_2 = 1337
    """
    ################################## PLUGIN DEVELOPERS: CUSTOMIZE THE FOLLOWING ######################################

    # Whether this plugin requires a configuration file to run. When this is set to False,
    # a configuration file can still be loaded if specified in B3 main configuration file.
    requiresConfigFile = True
    """:type: bool"""

    # The minimum B3 version which is needed to run this plugin. By default this is
    # set to the version matching the currently running B3.
    requiresVersion = b3_version
    """:type: str"""

    # List of parsers the current plugin supports: if no parser is specified the plugin will
    # be loaded, if listed in B3 main configuraion file, no matter the parser being used.
    requiresParsers = []
    """:type: list"""

    # List of plugins the current one needs to run: if no plugin is specified then the plugin
    # is dependency free. If one of the listed plugins is not installed in B3, then the current
    # plugin, and eventually all the other dependencies needed by this one, won't be loaded.
    requiresPlugins = []
    """:type: list"""

    # List of plugins which will be loaded before the current one: you can use this when a plugin
    # is not strictly needed by the current one, but this plugin makes use of some data produced by
    # the other one (mostly optional events) and thus needs to be loaded after.
    loadAfterPlugins = []
    """:type: list"""

    # Default messages which can be retrieved using the getMessage method: this dict will be
    # used in place of a missing 'messages' configuration file section.
    _default_messages = {}
    """:type: dict"""

    ################################## PLUGIN DEVELOPERS: END PLUGIN CUSTOMIZATION #####################################

    _enabled = True
    _messages = {}

    config = None
    console = None
    eventmanager = None
    eventmap = None
    events = []

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
        if isinstance(config, b3.config.XmlConfigParser) or isinstance(config, b3.config.CfgConfigParser):
            # this will be used by default from the Parser class since B3 1.10dev
            self.config = config
        else:
            if config is not None:
                # this is mostly used by automated tests which are loading plugins manually
                try:
                    self.loadConfig(config)
                except b3.config.ConfigFileNotValid, e:
                    self.critical("The configuration file syntax is broken: %s" % e)
                    self.critical("TIP: make use of a text editor with syntax highlighting to modify your config "
                                  "files: it makes easy to spot errors")
                    raise e

        self.registerEvent('EVT_STOP', self.onStop)
        self.registerEvent('EVT_EXIT', self.onExit)

    def enable(self):
        """
        Enable the plugin.
        """
        self._enabled = True
        name = b3.functions.right_cut(self.__class__.__name__, 'Plugin').lower()
        self.console.queueEvent(self.console.getEvent('EVT_PLUGIN_ENABLED', data=name))
        self.onEnable()

    def disable(self):
        """
        Disable the plugin.
        """
        self._enabled = False
        name = b3.functions.right_cut(self.__class__.__name__, 'Plugin').lower()
        self.console.queueEvent(self.console.getEvent('EVT_PLUGIN_DISABLED', data=name))
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

    def registerEventHook(self, event_id, hook):
        """
        Register an event hook which will be used to
        dispatch a specific event once it reaches our plugin.
        NOTE: This should be only called internally by registerEvent().
        :param event_id: The event id
        :param hook: The reference to the method that will handle the event
        """
        event_name = self.console.getEventName(event_id)
        if event_id not in self.events:
             # make sure the event we are going to map has been registered already
             raise AssertionError('%s is not an event registered for plugin %s' % (event_name, self.__class__.__name__))

        hook = getattr(self, hook.__name__, None)
        if not callable(hook):
            # make sure the given hook to be a valid method of our plugin
            raise AttributeError('%s is not a valid method of class %s' % (hook.__name__, self.__class__.__name__))

        # if it's the first time we are mapping
        if not event_id in self.eventmap:
            self.eventmap[event_id] = []

        # create the mapping
        if hook not in self.eventmap[event_id]:
            self.eventmap[event_id].append(hook)
        self.debug('created event mapping: <%s:%s>' % (event_name, hook.__name__))

    def registerEvent(self, name, *args):
        """
        Register an event for later processing.
        :param name: The event key or id
        :param args: An optional list of event handlers
        """
        # if we are given the event key, get the event id instead: this will
        # return the event id even if we supplied it as input parameter
        event_id = self.console.getEventID(name)
        event_name = self.console.getEventName(event_id)
        self.events.append(event_id)
        self.console.registerHandler(event_id, self)
        if len(args) > 0:
            for hook in args:
                try:
                    self.registerEventHook(event_id, hook)
                except (AssertionError, AttributeError), e:
                    self.error('could not create mapping for event %s: %s' % (event_name, e))
        else:
            try:
                self.registerEventHook(event_id, self.onEvent)
            except (AssertionError, AttributeError), e:
                self.error('could not create mapping for event %s: %s' % (event_name, e))

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
                self.error('could not parse event %s: %s' % (self.console.getEventName(event.type), e))

        if event.type == self.console.getEventID('EVT_EXIT') or event.type == self.console.getEventID('EVT_STOP'):
            self.working = False

    ####################################################################################################################
    #                                                                                                                  #
    #   LOGGING METHODS                                                                                                #
    #                                                                                                                  #
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
    #                                                                                                                  #
    #   PLUGIN HOOKS                                                                                                   #
    #   INHERITING CLASSES CAN IMPLEMENT THE FOLLOWING METHODS                                                         #
    #                                                                                                                  #
    ####################################################################################################################

    def onLoadConfig(self):
        """
        This is called after loadConfig() and if a user use the !reconfig command.
        Any plugin private variables loaded from the config need to be reset here.
        """
        pass

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
    #                                                                                                                  #
    #   EVENT HANDLERS                                                                                                 #
    #   THOSE ARE DEFAULT EVENT HANDLERS WHICH MAY BE OVERRIDDEN IN PLUGIN CLASSES                                     #
    #                                                                                                                  #
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
    #                                                                                                                  #
    #   DEPRECATED METHODS                                                                                             #
    #                                                                                                                  #
    ####################################################################################################################

    def handle(self, event):
        """
        Deprecated. Use onEvent().
        """
        self.warning('use of deprecated method: handle()')

    def startup(self):
        """
        Deprecated. Use onStartup().
        """
        self.warning('use of deprecated method: startup()')


class PluginData(object):
    """
    Class used to hold plugin data needed for plugin instance initialization.
    """
    def __init__(self, name, module=None, clazz=None, conf=None, disabled=False):
        """
        Inizialize a new PluginData object instance
        :param name: The plugin name as string
        :param module: The reference of the module implementing the plugin
        :param clazz: The class implementing the plugin
        :param conf: The configuration file instance of the plugin (if any)
        :param disabled: Whether this plugin needs to be initialized as disabled
        """
        self.name = name.lower()
        self.module = module
        self.clazz = clazz
        self.conf = conf
        self.disabled = disabled

    def __repr__(self):
        return 'PluginData<%s>' % self.name