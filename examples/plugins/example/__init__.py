# # coding=utf-8
#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2015 Daniele Pantaleone <fenix@bigbrotherbot.net>
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

import b3
import b3.functions
import b3.plugin
import b3.config
import b3.cron


class ExamplePlugin(b3.plugin.Plugin):
    """
    This class is meant to ease plugin development.
    Plugin developers who are not familiar with B3 core can copy this plugin module (the whole 'example'
    folder in 'examples/plugins' is the plugin module) over and make their own changes.
    This class illustrates basic interactions with the B3 core: in particular it shows the following:

        - defining new commands
        - reacting on B3 events
        - schedule execution of functions
        - client dynamic variable management (no persistence)

    If you want to see the outcome of this example you can load the plugin in your B3 to test it:

        - move the example folder inside @b3/extplugins
        - add the plugin entry to your main configuration file:

                - b3.ini => example: @b3/extplugins/example/conf/plugin_example.ini
                - b3.xml => <plugin name="example" config="@b3/extplugins/example/conf/plugin_example.ini" />


    From within a plugin you can access the following attributes/methods
    which may be needed in the development of your plugin:

    >>> self.config ## Plugin configuration file (b3.config.CfgConfigParser or b3.config.XmlConfigParser instance)
    >>> self.console ## B3 parser instance (inherits from b3.parser.Parser)
    >>> self.console.clients ## b3.clients.Clients instance (to retrieve client information)
    >>> self.console.cron ## b3.cron.Cron instance (for scheduled execution)
    >>> self.console.storage ## b3.storage.Storage instance (to communicate with the storage layer)
    >>> self.console.config ## b3.config.MainConfig instance (the B3 main configuration file)

    >>> self.bot('message')  ## Log a BOT message
    >>> self.info('message') ## Log a INFO message
    >>> self.debug('message')  ## Log a DEBUG message
    >>> self.warning('message')  ## Log a WARNING message
    >>> self.error('message')  ## Log a ERROR message
    >>> self.critical('message')  ## Log a CRITICAL message (B3 will stop)
    """

    # This flag specifies whether your plugin requires a configuration file or not. By default this
    # is set to true. If this is set to True and a plugin configuration file is not found, then your plugin
    # won't be loaded by B3.
    # If your plugin can make use of a configuration file, but it's not strictly needed (so it's optional), set this
    # to False: the onLoadConfig() method will be executed anyway and you would need to check there is a configuration
    # bounded to the plugin in the onLoadConfig() method (by checking `if self.config is not None:`)
    # If your plugin does not need a configuration file simply set this to False and do not specify a configuration
    # file path in your B3 main configuration file when loading the plugin.
    requiresConfigFile = True

    # Set this to the minimum required version of B3 needed to run your plugin.
    # If you omit this value, your plugin will be loaded no mater the version of the B3 currently running.
    requiresVersion = '1.10'

    # Specify here a list of parsers which are required to run your plugin.
    # Here below the list is empty which means that this plugin is not bounded to a specific game (default setting).
    # If for example you are constructing a plugin which runs only on CoD4 and CoD7, this value would
    # have been: requiresParsers = ['cod4', 'cod7'].
    requiresParsers = []

    # Specify here a list of plugins needed to run your plugin.
    # Here below the list is empty which means that this plugin does not required any other plugin to run.
    # To better understand how this work, think about this example:
    # The Geolocation plugin (in b3.plugins.geolocation) produces 2 new events: EVT_GEOLOCATION_SUCCESS and
    # EVT_GEOLOCATION_FAILURE. If your plugin needs to react on those  events, you need the geolocation plugin
    # to be loaded, and the following line would have been: requiresPlugins = ['geolocation']. B3 will then attempt
    # to load the geolocation plugin (even if the user did not specified such plugin in the B3 main configuration
    # file). If the geolocation plugin can't be loaded, also your plugin won't be loaded since a 'strong' requirement
    # is missing (if instead you need a 'weak' requirement, which means that your plugin may use another one but it's
    # not mandatory, you need to fill the loadAfterPlugins attribute here below.
    requiresPlugins = []

    # Specify here a list of plugins which needs to be loaded before your plugin.
    # All the plugins listed below will be loaded and started (if they are available) before your plugin.
    # You can use this list whenever your plugin can make use of some features (events, commands etc) provided by
    # another plugin but, but it can work also without it. As an example, let's assume that your plugin is declaring
    # a new command !setnextmap: this very command is also provided by many other plugins (for example by the
    # poweradminurt plugin which declares it as !pasetnextmap (and !setnextmap is an alias for this command).
    # If your plugin will be loaded before the poweradminurt plugin, the !setnextmap command will be overridden
    # by the poweradminurt, and your command implementation will never be executed. To make sure that your plugin
    # is loaded after the poweradminurt you need to change the following line to: loadAfterPlugins = ['poweradminurt].
    # When this is specified, you can detect whether the plugin poweradminurt is loaded and unregister the previously
    # registered !setnextmap command like this:
    #
    # >>>   def onStartup(self):
    # >>>       if self.console.getPlugin('poweradminurt'):
    # >>>           self.adminPlugin.unregisterCommand('pasetnextmap')
    #
    # Assiming that the admin plugin instance is in self.adminPlugin, this piece of code unregister the !pasetnextmap
    # command provided by the poweradminurt, so you can later register your own version of the command.
    loadAfterPlugins = []

    # This dictionary holds the default message patterns for your plugin. It usually matches the default [messages]
    # section of the plugin configuration file (but it's not mandatory). It will be used whenever your plugin needs
    # to retrieve a message pattern but the user removed the entry from the configuration file.
    _default_messages = {
        'hello_message': '$client says hello to $target',
        'cookie_message': '$client gives $num cookies to $target',
    }

    ####################################################################################################################
    #                                                                                                                  #
    #    STARTUP                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def __init__(self, console, config=None):
        """
        This is the plugin constructor.
        :param console: the B3 console instance
        :param config: the plugin configuration file instance
        :raise AttributeError: if the admin plugin fails in being loaded
        """
        # Always call b3.plugin.Plugin constructor before doing anything else!!!
        b3.plugin.Plugin.__init__(self, console, config)
        # Here you can initialize your plugin attributes (for example retrieving the Admin plugin so we can
        # later register our commands, initialize some default values which may be later overridden when parsing
        # the plugin configuration file and so on. Not that any uncatched exception raised from within this
        # constructor will sto B3 from loading your plugin, i.e: here below we retrieve the Admin plugin: if this
        # somehow fails, an AttributeError exception is raised which will prevent the plugin to B3 loaded by B3
        # leaving some message in the B3 log file explaining the reason why the plugin is not being loaded.
        self.adminPlugin = self.console.getPlugin('admin')
        if not self.adminPlugin:
            raise AttributeError('could not load admin plugin: this message will be printed in the B3 log file')

        # Initialize default saybig attribute value.
        self.use_saybig = False
        """:type: bool"""

        # Initialize default refill_interval attribute value.
        self.refill_interval = 60
        """:type: int"""

        # Initialize the number of cookies to be given on client connect (no config value for this).
        self.init_cookies = 10
        """:type: int"""

        # This will be set later in onStartup and it's used by the b3.cron.Cron object to schedule function execution.
        self.crontab = None
        """:type: b3.cron.PluginCronTab"""

    def onLoadConfig(self):
        """
        Load the plugin configuration file.
        This is the place where you load your plugin configuration file values and store them locally.
        """
        try:
            # This loads the settings::use_saybig value from the configuration file and store it locally
            # so we can access it later without having to query the configuration file.
            self.use_saybig = self.config.getboolean('settings', 'saybig')
            self.debug('loaded settings::use_saybig : %s' % self.use_saybig)
        except b3.config.NoOptionError:
            # This exception is raised whenever the configuration option is missing.
            self.warning('could not find settings::use_saybig in configuration file : using default (%s)' % self.use_saybig)
        except ValueError, e:
            # This exception is raised whenever the configuration entry is not valid.
            self.error('invalid value specified in settings::use_saybig in configuration file : %s' % e)
            self.debug('using default value for settings::use_saybig : %s' % self.use_saybig)

        try:
            # This loads the settings::refill_interval value from the configuration file and store it locally
            # so we can access it later without having to query the configuration file.
            self.refill_interval = self.config.getint('settings', 'refill_interval')
            self.debug('loaded settings::refill_interval : %s' % self.refill_interval)
        except b3.config.NoOptionError:
            # This exception is raised whenever the configuration option is missing.
            self.warning('could not find settings::refill_interval in configuration file : '
                         'using default (%s)' % self.refill_interval)
        except ValueError, e:
            # This exception is raised whenever the configuration entry is not valid.
            self.error('invalid value specified in settings::refill_interval in configuration file : %s' % e)
            self.debug('using default value for settings::refill_interval : %s' % self.refill_interval)

    def onStartup(self):
        """
        Initialize the plugin.
        This is the place where you perform initialization steps, such as registering new commands and events.
        """
        # in the snippet here below we parse the [commands] section of the plugin configuration file
        # extracting command name, alias and level: the command will then be registered and mapped
        # over the plugin method implementing the command. Note that the method implementing the command must
        # be named accordignly to the command name, i.e: the command !hello, whose name is 'hello' is implemented
        # by the method cmd_hello(self, data, client, cmd=None) defined here below.
        if 'commands' in self.config.sections():
            for cmd in self.config.options('commands'):
                level = self.config.get('commands', cmd)
                sp = cmd.split('-')
                alias = None
                if len(sp) == 2:
                    # this will split the command name and the alias
                    cmd, alias = sp
                # retrieve the method implementing the command
                func = b3.functions.getCmd(self, cmd)
                if func:
                    # register the command is a valid method is found
                    self.adminPlugin.registerCommand(self, cmd, level, func, alias)

        # Here below we register our plugin as event listener for EVT_CLIENT_CONNECT event:
        # when this event is handed over our plugin, the function self.onConnect is executed. You
        # can specify multiple functions as event handlers, i.e:
        #
        #     >>> self.registerEvent('EVT_CLIENT_CONNECT', self.onConnect, self.onConnect2, self.onConnect3)
        #
        # will execute self.onConnect, self.onConnect2, self.onConnect3 in the order they are declared.
        #
        # You can find B3 default events inside b3.events. Some events are bounded to specifid games and they
        # are defined inside parsers (for example the iourt42 parser defines events which belongs only to
        # Urban Terror 4.2 game), so you would need to dig inside parsers code find out which events are provided.
        self.registerEvent('EVT_CLIENT_CONNECT', self.onConnect)

        # create a new plugin crontab and install it into the main cron object (available in self.console.cron)
        self.crontab = b3.cron.PluginCronTab(self, self.scheduled_refill, '*/%s' % self.refill_interval)
        self.console.cron + self.crontab

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENTS                                                                                                         #
    #                                                                                                                  #
    ####################################################################################################################

    def scheduled_refill(self):
        """
        Scheduled execution.
        Will give 1 cookie to every connected client every self.refill_interval seconds.
        """
        for client in self.console.clients.getList():
            client_cookies = client.var(self, 'cookies').value + 1
            client.setvar(self, 'cookies', client_cookies)
            client.message('B3 gifted you 1 cookie: you now have %s cookies' % client_cookies)

    ####################################################################################################################
    #                                                                                                                  #
    #   CRON                                                                                                           #
    #                                                                                                                  #
    ####################################################################################################################

    def onConnect(self, event):
        """
        This is executed whenever an EVT_CLIENT_CONNECT event is handed over the plugin
        :param event: an EVT_CLIENT_CONNECT event
        """
        # Here we give 10 cookies to the client who is connecting to our server: we store
        # them locally inside the client object since we do not need persistence (otherwise we
        # would have need to use self.console.storage module to communicate with the storage layer)
        client = event.client
        self.debug('client connected to the server (%s) : gifting %s cookies to him' % (client.name, self.init_cookies))
        client.setvar(self, 'cookies', self.init_cookies)

    ####################################################################################################################
    #                                                                                                                  #
    #   COMMANDS                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def cmd_hello(self, data, client, cmd=None):
        """
        <client> - the client to who say hello
        :param data: extra data passed over the command method (in this case the client handle)
        :param client: the client who executed the command
        :param cmd: the command instance (see b3.plugins.admin.Command)
        NOTE: this description is shown using !help hello, so you may want to remove it before publishing
        your plugin, and replace with some help text which helps the user with the command usage
        """
        if not data:
            # If not client is specified
            client.message('Missing data, try !help hello')
        else:
            # When searching the target client, pass to the findClientPrompt method of the admin plugin
            # also the the reference of the object of the client who issued the command. In this way if no
            # target is found (or multiple) a list of closest matches is displayed to the user and he can
            # retry using a more specific value.
            target = self.adminPlugin.findClientPrompt(data, client)
            if target:
                # if we have a target we can proceed with the command execution: we retrieve the message from
                # the configuration file (or fallback to default if not provided) and replace tokens with proper
                # values (so here $client is replaced with client.name and $target is replaced with target.name)
                message = self.getMessage('hello_message', {'client': client.name, 'target': target.name})
                if self.use_saybig:
                    # If the user enabled the saybig feature, use it
                    self.console.saybig(message)
                else:
                    # User decided to use normal say command
                    self.console.say(message)

    def cmd_cookie(self, data, client, cmd=None):
        """
        <client> [<amount>] - gives a cookie (or more) to a client
        :param data: extra data passed over the command method (in this case the client handle and the amount of cookies)
        :param client: the client who executed the command
        :param cmd: the command instance (see b3.plugins.admin.Command)
        NOTE: this description is shown using !help cookie, so you may want to remove it before publishing
        your plugin, and replace with some help text which helps the user with the command usage
        """
        if not data:
            # If no parameter is specified
            client.message('Missing data, try !help cookie')
        else:
            m = self.adminPlugin.parseUserCmd(data)
            if not m:
                # If invalid parameters have been specified
                client.message('Invalid data, try !help cookie')
            else:
                # m[0] is the client handle
                # m[1] is the amount of cookies (if specified)
                # When searching the target client, pass to the findClientPrompt method of the admin plugin
                # also the the reference of the object of the client who issued the command. In this way if no
                # target is found (or multiple) a list of closest matches is displayed to the user and he can
                # retry using a more specific value.
                target = self.adminPlugin.findClientPrompt(m[0], client)
                if target:

                    try:
                        # Use the value specified (if any)
                        cookies_to_move = int(m[1])
                    except Exception:
                        # Default to 1 in case of wrong user input or missing value
                        cookies_to_move = 1

                    client_cookies = client.var(self, 'cookies').value
                    if cookies_to_move > client_cookies:
                        # If the user has not enough cookies, inform him
                        client.message('You do not have %s cookies: you have %s cookies left' % (cookies_to_move, client_cookies))
                    else:
                        # The user has the amount of cookies he wants to give, so transfer them.
                        target_cookies = client.var(self, 'cookies').value
                        target_cookies += cookies_to_move
                        client_cookies -= cookies_to_move
                        target.setvar(self, 'cookies', target_cookies)
                        client.setvar(self, 'cookies', client_cookies)

                        # Display a message which informs of the operation being completed
                        message = self.getMessage('cookie_message', {'client': client.name, 'target': target.name, 'num': cookies_to_move})
                        if self.use_saybig:
                            # If the user enabled the saybig feature, use it
                            self.console.saybig(message)
                        else:
                            # User decided to use normal say command
                            self.console.say(message)

                        # Send a personal message to both the clients informing them about their cookie count.
                        client.message('You are left with %s cookies' % client_cookies)
                        target.message('You now have %s cookies' % target_cookies)