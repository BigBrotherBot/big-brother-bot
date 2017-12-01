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

__author__ = 'ThorN, Courgette'
__version__ = '1.13'


import re
import b3.clients
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

    # List of storage protocols supported by your plugin ('mysql', 'sqlite', 'postgresql'): if no value is specified
    # B3 will load the plugin no matter the type of storage module being used (so it will assume that your plugin will
    # not use the storage layer at all, or that your plugin is capable of handling all of them).
    # NOTE: B3 will not generate the database schema: you would have to handle this yourself in plugin onStartup()
    requiresStorage = []
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
                    self.critical("TIP: make use of a text editor with syntax highlighting to "
                                  "modify your config files: it makes easy to spot errors")
                    raise e

        self.registerEvent('EVT_STOP', self.onStop)
        self.registerEvent('EVT_EXIT', self.onExit)

    def start(self):
        """
        Called after Plugin.startup().
        """
        pass

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

    ####################################################################################################################
    #                                                                                                                  #
    #   CONFIG RELATED METHODS                                                                                         #
    #                                                                                                                  #
    ####################################################################################################################

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
                    self.critical('could not find config file %s', filename)
                    return False
                else:
                    self.bot('no config file found for %s: was not required either', self.__class__.__name__)
                    return True
        elif self.config:
            self.bot('loading config %s for %s', self.config.fileName, self.__class__.__name__)
            self.config = b3.config.load(self.config.fileName)
        else:
            if self.requiresConfigFile:
                self.error('could not load config for %s', self.__class__.__name__)
                return False
            else:
                self.bot('no config file found for %s: was not required either', self.__class__.__name__)
                return True

        # empty message cache
        self._messages = {}

    def saveConfig(self):
        """
        Save the plugin configuration file.
        """
        self.bot('saving config %s', self.config.fileName)
        return self.config.save()

    def isSetting(self, section, option):
        """
        Tests whether the given section/option combination is valid.
        This is a shortcut to config.has_option method
        :param section: the configuration file section
        :param option: the configuration file option
        :return: True if the section/option matches a an entry, False otherwise
        """
        return self.config.has_option(section, option)

    def getSetting(self, section, option, value_type=b3.STRING, default=None, validate=None):
        """
        Safely return a setting value from the configuration file.
        Will print in the log file information about the value being loaded
        :param section: the configuration file section
        :param option: the configuration file option
        :param value_type: the value type used to cast the retrieved value
        :param default: the default value to be returned when an error occurs
        :param validate: a reference to a function which has the job of validating the given value: the function
                         should return the valid itself (or modified if it can be done) or raise ValueError if the value
                          is not acceptable.
        """
        def _get_string(value):
            """convert the given value to str"""
            self.verbose('trying to convert value to string : %s', value)
            return str(value)

        def _get_integer(value):
            """convert the given value to int"""
            self.verbose('trying to convert value to integer : %s', value)
            return int(str(value))

        def _get_boolean(value):
            """convert the given value to bool"""
            self.verbose('trying to convert value to boolean : %s', value)
            x = str(value).lower()
            if x in ('yes', '1', 'on', 'true'):
                return True
            elif x in ('no', '0', 'off', 'false'):
                return False
            else:
                raise ValueError('%s is not a boolean value' % x)

        def _get_float(value):
            """convert the given value to float"""
            self.verbose('trying to convert value to float : %s', value)
            return float(str(value))

        def _get_level(value):
            """convert the given value to a b3 group level"""
            self.verbose('trying to convert value to b3 group level : %s', value)
            return self.console.getGroupLevel(str(value).lower().strip())

        def _get_duration(value):
            """convert the given value using b3.functions.time2minutes"""
            self.verbose('trying to convert value to time duration : %s', value)
            return b3.functions.time2minutes(str(value).strip())

        def _get_path(value):
            """convert the given path using b3.getAbsolutePath"""
            self.verbose('trying to convert value to absolute path : %s', value)
            return b3.getAbsolutePath(str(value), decode=True)

        def _get_template(value):
            """process the given value using b3.functions.vars2printf"""
            return b3.functions.vars2printf(value).strip()

        def _get_list(value):
            """process the given value by extracting tokens"""
            return [x for x in re.split('\W+', value) if x]

        handlers = {
            b3.STRING: _get_string,
            b3.INTEGER: _get_integer,
            b3.BOOLEAN: _get_boolean,
            b3.FLOAT: _get_float,
            b3.LEVEL: _get_level,
            b3.DURATION: _get_duration,
            b3.PATH: _get_path,
            b3.TEMPLATE: _get_template,
            b3.LIST: _get_list,
        }

        if not self.config:
            self.warning('could not find %s::%s : no configuration file loaded, using default : %s', section, option, default)
            return default

        try:
            val = self.config.get(section, option, value_type == b3.TEMPLATE)
        except b3.config.NoOptionError:
            self.warning('could not find %s::%s in configuration file, using default : %s', section, option, default)
            val = default
        else:
            try:
                func = handlers[value_type]
            except KeyError:
                val = default
                self.warning('could not convert %s::%s : invalid value type specified (%s) : expecting one of (%s), '
                             'using default : %s', section, option , value_type, ', '.join(map(str, handlers.keys())), default)
            else:
                try:
                    val = func(val)
                except (ValueError, KeyError), e:
                    self.warning('could not convert %s::%s (%s) : %s, using default : %s', section, option , val, e, default)
                    val = default

        if validate:
            try:
                val = validate(val)
            except ValueError, e:
                self.warning('invalid value specified for %s::%s (%s) : %s,  using default : %s', section, option, val, e, default)
                val = default

        self.debug('loaded value from configuration file : %s::%s = %s', section, option, val)
        return val

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

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENTS RELATED METHODS                                                                                         #
    #                                                                                                                  #
    ####################################################################################################################

    def registerEventHook(self, event_id, hook):
        """
        Register an event hook which will be used to dispatch a specific event once it reaches our plugin.
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

    def handle(self, _):
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