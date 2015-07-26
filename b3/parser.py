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
# 2015/07/26 - 1.43.6 - Fenix           - fixed loadPlugins crashing B3 owhen it could not load a 3rd party plugin
# 2015/07/19 - 1.43.5 - Fenix           - restored self.critical to raise SystemExit and shutdown B3 (branch rebase lost it???)
# 2015/06/25 - 1.43.4 - Fenix           - correctly handle Plugin attribute requiresVersion (branch rebase lost it???)
# 2015/06/22 - 1.43.3 - Fenix           - added support for the new Plugin attribute: requiresStorage
# 2015/06/17 - 1.43.2 - Fenix           - fixed some absolute path retrieval not decoding non-ascii characters
# 2015/05/26 - 1.43.1 - Fenix           - added StubParser class: can be used when the storage module needs to be
#                                         initilized without a running B3 console (fakes logging and sys.stdout)
#                                       - fixed pluginImport not working correctly when starting B3 using OSX app bundle
# 2015/05/15 - 1.43   - Fenix           - fixed formatTime not converting timestamp according to timezone offset
# 2015/05/04 - 1.42.9 - Fenix           - removed reply mode: it's messing up GUI and it's needed only to debug cod4
#                                       - make sure that the logfile path is actually writable by B3, else it crashes
# 2015/04/28 - 1.42.9 - Fenix           - code cleanup
# 2015/04/22 - 1.42.8 - Fenix           - fixed typo in startPlugins: was causing B3 to crash upon startup
# 2015/04/16 - 1.42.7 - Fenix           - uniform class variables (dict -> variable)
#                                       - print more verbose information in log file when a plugin fails in being loaded
#                                       - simplify exception logging on plugin configuration load and plugin startup
# 2015/03/26 - 1.42.6 - Fenix           - added isFrostbiteGame method: checks if we are running a Frostbite base game
# 2015/03/25 - 1.42.5 - Fenix           - added support for the new plugin attribute 'loadAfterPlugins'
# 2015/03/21 - 1.42.4 - Fenix           - added support for the new plugin attribute 'requiresParsers'
# 2015/03/16 - 1.42.3 - Fenix           - minor fixes to plugin dependency loading
# 2015/03/09 - 1.42.2 - Fenix           - added plugin dependency loading
# 2015/03/01 - 1.42.1 - Fenix           - added unregisterHandler method
# 2015/02/25 - 1.42   - Fenix           - added automatic timezone offset detection
# 2015/02/15 - 1.41.8 - Fenix           - fix broken 1.41.7
# 2015/02/15 - 1.41.7 - Fenix           - make game log reading work properly in osx
# 2015/02/04 - 1.41.6 - Fenix           - optionally specify a log file size: 'logsize' option in 'b3' section of main cfg
# 2015/02/02 - 1.41.5 - 82ndab.Bravo17  - remove color codes at start of getWrap if not valid for game
# 2015/01/29 - 1.41.4 - Fenix           - do not let plugins crash B3 by raising an exception within the constructor
#                                       - fixed KeyError beiung raised in loadPlugins()
# 2015/01/28 - 1.41.3 - Fenix           - fixed external plugins directory retrieval in loadPlugins()
# 2015/01/28 - 1.41.2 - Fenix           - prevent enabling/disabling of cod7http plugin
# 2015/01/28 - 1.41.1 - Fenix           - changed some log messages to be verbose only: debug log file was too messy
#                                       - fixed pluginImport not raising ImportError when B3 is not able to load
#                                         a plugin from a specific path
# 2015/01/27 - 1.41   - Thomas LEVEIL   - allow specifying a custom timeout for `write` (if the rcon implementation
#                                         supports it)
# 2015/01/15 - 1.40.2 - Fenix           - removed redundant code: plugins now are held only by the _plugins OrderedDict()
# 2015/01/15 - 1.40.1 - Fenix           - fixed invalid reference to None object upon plugin loading
# 2015/01/08 - 1.40   - Fenix           - new plugin loading algorithm: check the comments of the following issue for
#                                         details: https://github.com/BigBrotherBot/big-brother-bot/pull/250
# 2015/01/07 - 1.39.2 - Fenix           - updated loadPlugins() to search inside extplugins module directories
#                                       - fixed some invalid references in _get_config_path()
# 2014/12/31 - 1.39.1 - Fenix           - loadArbPlugins: don't bother loading arb plugins if admin plugin is not loaded
#                                       - prevent plugins from crashing B3 if they fails in loading: Admin plugin will
#                                         be still checked in loadArbPlugins since it's strictly needed
# 2014/12/25 - 1.39   - Fenix           - new storage module initialization
# 2014/12/14 - 1.38.2 - Fenix           - correctly set exitcode variable in b3.parser.die() and b3.parser.restart(): B3
#                                         was calling sys.exit(*) in both methods but the main thread was expecting to
#                                         find the exit code in the exitcode (so the main thread was defaulting exit
#                                         code to 0). This fixes auto-restart mode not working.
#                                       - let the parser know if we are running B3 in auto-restart mode or not
# 2014/12/13 - 1.38.1 - Fenix           - moved b3.parser.finalize() call in b3.parser.die() from b3.parser.shutdown()
# 2014/12/11 - 1.38   - Fenix           - added plugin updater loading in loadArbPlugins
#                                       - make use of the newly declared function b3.functions.right_cut instead
# 2014/09/06 - 1.37.4 - Fenix           - updated parser to load configuration from the new .ini format
# 2014/11/30 - 1.37.3 - Fenix           - correctly remove B3 PID file upon parser shutdown (Linux systems only)
# 2014/09/02 - 1.37.2 - Fenix           - moved _first_line_code attribute in _settings['line_color_prefix']
#                                       - allow customization of _settings['line_color_prefix'] from b3.xml:
#                                         setting 'line_color_prefix' in section 'server'
#                                       - slightly changed getWrap method to use a more pythonic approach
#                                       - make sure to have '>' prefix in getWrap method result (also when color codes
#                                         are not being used by the parser) when the result line is not the first of the
#                                         list
# 2014/09/01 - 1.37.1 - 82ndab-Bravo17  - add color code options for new getWrap method
# 2014/07/27 - 1.37   - Fenix           - syntax cleanup
#                                       - reformat changelog
# 2014/07/18 - 1.36   - Fenix           - new getWrap implementation based on the textwrap.TextWrapper class: the
#                                         maximum length of each message can be customized in the _settings dictionary
#                                         (_settings['line_length'] for instance)
# 2014/06/02 - 1.35.3 - Courgette       - prevent the same plugin to register multiple times for the same event
# 2014/06/02 - 1.35.2 - Fenix           - moved back event mapping logic into Plugin class: Parser should be aware only
#                                         of Plugins listening for incoming events and not how to dispatch them: for
#                                         more info see https://github.com/BigBrotherBot/big-brother-bot/pull/193
# 2014/05/21 - 1.35.1 - Fenix           - moved plugin event mapping function into Parser class
# 2014/04/14 - 1.35   - Fenix           - PEP8 coding style guide
# 2014/01/19 - 1.34   - Ozon            - improve plugin config file search
# 2013/10/24 - 1.33   - Courgette       - fix httpytail, ftpytail and sftpytail plugins that would be loaded twice if
#                                         found in the plugins section of the b3.xml file
#                                       - fix on_load_config hook is now called by the parser instead of at plugin
#                                         instantiation
# 2013/10/23 - 1.32   - Courgette       - on_load_config hook is now called by the parser instead of
#                                         at plugin instantiation
# 2013/02/15 - 1.31.1 - Courgette       - fix reload_configs() which would not reload the config for the admin plugin
# 2012/10/19 - 1.31   - Courgette       - add method get_nextmap() to the list of method all B3 parsers should implement
# 2012/09/14 - 1.30.1 - Courgette       - fix variable substitution in default message templates
# 2012/08/27 - 1.30   - Courgette       - better feedback when an error occurs while setting up Rcon
#                                       - add getEventKey method
# 2012/08/12 - 1.29   - Courgette       - gracefully fallback on default message templates if missing from main
#                                         config file
# 2012/08/11 - 1.28   - Courgette       - add two methods: getGroup and getGroupLevel meant to ease the reading of a
#                                         valid group or group level from a config file. Conveniently raises KeyError
#                                         if level or group keyword provided does not match any existing group.
# 2012/07/20 - 1.27.5 - Courgette       - better error message when expected self.input attribute is missing
# 2012/06/17 - 1.27.4 - Courgette       - log traceback when an exception occurs while loading a plugin
#                                         detect missing 'name' attribute in plugin element from the plugins
#                                         section of the config file
# 2012/06/17 - 1.27.3 - Courgette       - more explicit message when failing to load a plugin from a specified path
# 2012/06/17 - 1.27.2 - Courgette       - syntax and code cleanup
# 2012/05/06 - 1.27.1 - Courgette       - increases default b3 event queue size to 50
# 2011/06/05 - 1.27   - xlr8or          - implementation of game server encoding/decoding
# 2011/09/12 - 1.26.2 - Courgette       - start the admin plugin first as many plugins relie on it (does not affect
#                                         plugin priority in regard to B3 events dispatching)
# 2011/06/05 - 1.26.1 - Courgette       - fix periodic events stats dumping blocking B3 restart/shutdown
# 2011/05/03 - 1.24.8 - Courgette       - event queue size can be set in b3.xml in section 'b3/event_queue_size'
# 2011/05/03 - 1.24.7 - Courgette       - add periodic events stats dumping to detect slow plugins
# 2011/05/03 - 1.24.6 - Courgette       - do not run update sql queries on startup
# 2011/05/03 - 1.24.5 - Courgette       - fix bug regarding rcon_ip introduced in 1.24.4
# 2011/04/31 - 1.24.4 - Courgette       - add missing b3.timezones import
# 2011/04/30 - 1.24.3 - Courgette       - move the B3 start announcement that is broadcasted on the game server after
#                                         the parser startup() method has been called to give a change to parsers to
#                                         set up their rcon before it is used.
#                                       - rcon_ip, rcon_password not mandatory anymore to suport games that have rcon
#                                         working through files
# 2011/04/27 - 1.24.2 - 82ndab-Bravo17  - auto assign of unique local games_mp log file
# 2011/04/20 - 1.24.1 - Courgette       - fix auto detection of locale timezone offset
# 2011/03/30 - 1.24   - Courgette       - remove output option log2both and changed the behavior of log2console so
#                                         that the console log steam is not replacing the stream going to the log file
# 2011/02/03 - 1.23   - 82ndab-Bravo17  - allow local log to be appended to instead of overwritten for games with
#                                         remote logs
# 2010/11/25 - 1.22   - Courgette       - at start, can load a plugin in 'disabled' state. Use the 'disabled' as follow:
#                                         <plugin name="adv" config="@conf/plugin_adv.xml" disabled="Yes"/>
# 2010/11/18 - 1.21   - Courgette       - do not resolve eventual domain name found in public_ip
# 2010/11/07 - 1.20.2 - GrosBedo        - edited default values of lines_per_second and delay
# 2010/11/07 - 1.20.1 - GrosBedo        - added a new dynamical function get_message_variables to parse messages
# 2010/10/28 - 1.20.0 - Courgette       - support an new optional syntax for loading plugins in b3.xml which enable
#                                         to specify a directory where to find the plugin with the 'path' attribute.
#                                         this overrides the default and extplugins folders. Example :
#                                         <plugin name="name" config="@conf/plugin.xml" path="C:\Users\me\myPlugin\"/>
# 2010/10/22 - 1.19.4 - xlr8or          - output option log2both writes to logfile AND stderr simultaneously
# 2010/10/06 - 1.19.3 - xlr8or          - reintroduced rcontesting on startup, but for q3a based only
# 2010/09/04 - 1.19.2 - GrosBedo        - fixed some typos
#                                       - moved delay and lines_per_second settings to server category
# 2010/09/04 - 1.19.1 - Grosbedo        - added b3/local_game_log option for several remote log reading at once
#                                       - added http remote log support
#                                       - delay2 -> lines_per_second
# 2010/09/01 - 1.19   - Grosbedo        - reduce disk access costs by reading multiple lines at once from the
#                                         game log file
# 2010/09/01 - 1.18   - Grosbedo        - detect game log file rotation
# 2010/09/01 - 1.17   - Courgette       - add beta support for sftp protocol for reading remote game log file
# 2010/08/14 - 1.16.1 - Courgette       - fallback on UTC timezone in case the timezone name is not valid
# 2010/04/17 - 1.16   - Courgette       - plugin priority is defined by their order in the b3.xml file
#                                       - fix bug in get_event_name()
# 2010/04/10 - 1.15.1 - Courgette       - write the parser version to log file
# 2010/04/10 - 1.15   - Courgette       - public_ip and rcon_ip can now be domain names
# 2010/04/10 - 1.14.3 - Bakes           - added saybig() to method stubs for inheriting classes
# 2010/03/23 - 1.14.2 - Bakes           - add message_delay for better BFBC2 interoperability.
# 2010/03/22 - 1.14.1 - Courgette       - change maprotate() to rotate_map()
# 2010/03/21 - 1.14   - Courgette       - create method stubs for inheriting classes to implement
# 10/03/2010 - 1.13   - Courgette       - add rconPort for games which have a different rcon port than the game port
#                                       - server.game_log option is not mandatory anymore. This makes B3 able to work
#                                         with game servers having no game log file
#                                       - do not test rcon anymore as the test process differs depending on the game
# 12/12/2009 - 1.12.3 - Courgette       - when working in remote mode, does not download the remote log file.
# 06/12/2009 - 1.12.2 - Courgette       - write() can specify a custom max_retries value
# 22/11/2009 - 1.12.1 - Courgette       - b3.xml can have option ('server','rcon_timeout') to specify a custom delay
#                                        (secondes) to use for the rcon socket
# 17/11/2009 - 1.12.0 - Courgette       - b3.xml can now have an optional section named 'devmode'
#                                       - move 'replay' option to section 'devmode'
#                                       - move 'delay' option to section 'b3'
#                                       - add option 'log2console' to section 'devmode'. This will make the bot
#                                         write to stderr instead of b3.log (useful if using eclipse or such IDE)
#                                       - fix replay mode when bot detected time reset from game log
# 09/10/2009 - 1.11.2 - xlr8or          - saved original sys.stdout to console.screen to aid communications to b3 screen
# 12/09/2009 - 1.11.1 - xlr8or          - added few functions and prevent spamming b3.log on pause
# 28/08/2009 - 1.11.0 - Bakes           - adds Remote B3 thru FTP functionality.
# 19/08/2009 - 1.10.0 - Courgette       - adds the inflict_custom_penalty() that allows to define game specific
#                                         penalties: requires admin.py v1.4+
# 10/7/2009  -        - xlr8or          - added code to load publist by default -
# 29/4/2009  -        - xlr8or          - fixed ignored exit code (for restarts/shutdowns)
# 10/20/2008 - 1.9.1b - mindriot        - fixed slight typo of b3.events.EVT_UNKOWN to b3.events.EVT_UNKNOWN
# 11/29/2005 - 1.7.0  - ThorN           - added atexit handlers
#                                       - added warning, info, exception, and critical log handlers

__author__ = 'ThorN, Courgette, xlr8or, Bakes, Ozon, Fenix'
__version__ = '1.43.6'


import os
import sys
import re
import time
import thread
import datetime
import dateutil.tz
import Queue
import imp
import atexit
import socket
import glob

import b3
import b3.config
import b3.storage
import b3.events
import b3.output
import b3.game
import b3.cron
import b3.parsers.q3a.rcon
import b3.timezones

from ConfigParser import NoOptionError
from collections import OrderedDict
from b3 import __version__ as currentVersion
from b3.clients import Clients
from b3.clients import Group
from b3.decorators import Memoize
from b3.exceptions import MissingRequirement
from b3.functions import getModule
from b3.functions import vars2printf
from b3.functions import main_is_frozen
from b3.functions import splitDSN
from b3.functions import right_cut
from b3.functions import topological_sort
from b3.plugin import PluginData
from b3.update import B3version
from textwrap import TextWrapper
from traceback import extract_tb


try:
    from xml.etree import cElementTree as ElementTree
except ImportError:
    from xml.etree import ElementTree


class Parser(object):

    OutputClass = b3.parsers.q3a.rcon.Rcon  # default output class set to the q3a rcon class

    _commands = {}  # will hold RCON commands for the current game
    _cron = None  # cron instance
    _events = {}  # available events (K=>EVENT)
    _eventNames = {}  # available event names (K=>NAME)
    _eventsStats_cronTab = None  # crontab used to log event statistics
    _handlers = {}  # event handlers
    _lineTime = None  # used to track log file time changes
    _lineFormat = re.compile('^([a-z ]+): (.*?)', re.IGNORECASE)
    _line_color_prefix = ''  # a color code prefix to be added to every line resulting from getWrap
    _line_length = 80  # max wrap length
    _messages = {}  # message template cache
    _message_delay = 0  # delay between consequent sent say messages (apply also to private messages)
    _paused = False  # set to True when B3 is paused
    _pauseNotice = False  # whether to notice B3 being paused
    _plugins = OrderedDict()  # plugin instances
    _port = 0  # the port used by the gameserver for clients connection
    _publicIp = ''  # game server public ip address
    _rconIp = ''  # the ip address where to forward RCON commands
    _rconPort = None  # the virtual port where to forward RCON commands
    _rconPassword = ''  # the rcon password set on the server
    _reColor = re.compile(r'\^[0-9a-z]') # regex used to strip out color codes from a given string
    _timeStart = None  # timestamp when B3 has first started
    _use_color_codes = True  # whether the game supports color codes or not

    autorestart = False  # whether B3 has been started in autorestart mode
    clients = None
    config = None  # parser configuration file instance
    delay = 0.33  # time between each game log lines fetching
    delay2 = 0.02  # time between each game log line processing: max number of lines processed in one second
    encoding = 'latin-1'
    game = None
    gameName = None # console name
    log = None  # logger instance
    logTime = 0  # time in seconds of epoch of game log
    name = 'b3'  # bot name
    output = None  # will contain the instance used to send data to the game server (default to b3.parsers.q3a.rcon.Rcon)
    privateMsg = False  # will be set to True if the game supports private messages
    queue = None  # event queue
    rconTest = False  # whether to perform RCON testing or not
    remoteLog = False
    screen = None
    storage = None  # storage module instance
    type = None
    working = True  # whether B3 is running or not
    wrapper = None  # textwrapper instance

    deadPrefix = '[DEAD]^7'  # say dead prefix
    msgPrefix = ''  # say prefix
    pmPrefix = '^8[pm]^7'  # private message prefix
    prefix = '^2%s:^3'  # B3 prefix

    # default messages in case one is missing from config file
    _messages_default = {
        "kicked_by": "$clientname^7 was kicked by $adminname^7 $reason",
        "kicked": "$clientname^7 was kicked $reason",
        "banned_by": "$clientname^7 was banned by $adminname^7 $reason",
        "banned": "$clientname^7 was banned $reason",
        "temp_banned_by": "$clientname^7 was temp banned by $adminname^7 for $banduration^7 $reason",
        "temp_banned": "$clientname^7 was temp banned for $banduration^7 $reason",
        "unbanned_by": "$clientname^7 was un-banned by $adminname^7 $reason",
        "unbanned": "$clientname^7 was un-banned $reason",
    }

    _frostBiteGameNames = ['bfbc2', 'moh', 'bf3', 'bf4']

    # === Exiting ===
    #
    # The parser runs two threads: main and handler.  The main thread is
    # responsible for the main loop parsing and queuing events, and process
    # termination. The handler thread is responsible for processing queued events
    # including raising ``SystemExit'' when a user-requested exit is needed.
    #
    # The ``SystemExit'' exception bubbles up only as far as the top of the handler
    # thread -- the ``handleEvents'' method.  To expose the exit status to the
    # ``run'' method in the main thread, we store the value in ``exitcode''.
    #
    # Since the teardown steps in ``run'' and ``handleEvents'' would occur in
    # parallel, we use a lock (``exiting'') to ensure that ``run'' waits for
    # ``handleEvents'' to finish before proceeding.
    #
    # How exiting works, in detail:
    #
    #   - the parallel loops in run() and handleEvents() are terminated only when working==False.
    #   - die() or restart() invokes shutdown() from the handler thread.
    #   - the exiting lock is acquired by shutdown() in the handler thread before it sets working=False to
    #     end both loops.
    #   - die() or restart() raises SystemExit in the handler thread after shutdown() and a few seconds delay.
    #   - when SystemExit is caught by handleEvents(), its exit status is pushed to the main context via exitcode.
    #   - handleEvents() ensures the exiting lock is released when it finishes.
    #   - run() waits to acquire the lock in the main thread before proceeding with teardown, repeating
    #     sys.exit(exitcode) from the main thread if set.
    #
    #   In the case of an abnormal exception in the handler thread, ``exitcode''
    #   will be None and the ``exiting'' lock will be released when``handleEvents''
    #   finishes so the main thread can still continue.
    #
    #   Exits occurring in the main thread do not need to be synchronised.

    exiting = thread.allocate_lock()
    exitcode = None

    def __new__(cls, *args, **kwargs):
        cls.__read = cls.__read_input
        if sys.platform == 'darwin':
            cls.__read = cls.___read_input_darwin
        return object.__new__(cls)

    def __init__(self, conf, options):
        """
        Object contructor.
        :param conf: The B3 configuration file
        :param options: command line options
        """
        self._timeStart = self.time()

        # store in the parser whether we are running B3 in autorestart mode so
        # plugins can react on this and perform different operations
        self.autorestart = options.autorestart

        if not self.loadConfig(conf):
            print('CRITICAL ERROR : COULD NOT LOAD CONFIG')
            raise SystemExit(220)

        # set game server encoding
        if self.config.has_option('server', 'encoding'):
            self.encoding = self.config.get('server', 'encoding')

        # set up logging
        logfile = self.config.getpath('b3', 'logfile')
        log2console = self.config.has_option('devmode', 'log2console') and \
            self.config.getboolean('devmode', 'log2console')

        # make sure the logfile is writable
        logfile = b3.getWritableFilePath(logfile, True)

        try:
            logsize = b3.functions.getBytes(self.config.get('b3', 'logsize'))
        except (TypeError, NoOptionError):
            logsize = b3.functions.getBytes('10MB')

        # create the main logger instance
        self.log = b3.output.getInstance(logfile, self.config.getint('b3', 'log_level'), logsize, log2console)

        # save screen output to self.screen
        self.screen = sys.stdout
        self.screen.write('Activating log   : %s\n' % b3.getShortPath(os.path.abspath(b3.getAbsolutePath(logfile, True))))
        self.screen.flush()

        sys.stdout = b3.output.STDOutLogger(self.log)
        sys.stderr = b3.output.STDErrLogger(self.log)

        # setup ip addresses
        if self.gameName in 'bf3':
            self._publicIp = ''
            if self.config.has_option('server', 'public_ip'):
                self._publicIp = self.config.get('server', 'public_ip')
            self._port = ''
            if self.config.has_option('server', 'port'):
                self._port = self.config.getint('server', 'port')
        else:
            self._publicIp = self.config.get('server', 'public_ip')
            self._port = self.config.getint('server', 'port')

        self._rconPort = self._port    # if rcon port is the same as the game port, rcon_port can be ommited
        self._rconIp = self._publicIp  # if rcon ip is the same as the game port, rcon_ip can be ommited

        if self.config.has_option('server', 'rcon_ip'):
            self._rconIp = self.config.get('server', 'rcon_ip')
        if self.config.has_option('server', 'rcon_port'):
            self._rconPort = self.config.getint('server', 'rcon_port')
        if self.config.has_option('server', 'rcon_password'):
            self._rconPassword = self.config.get('server', 'rcon_password')

        if self._publicIp and self._publicIp[0:1] in ('~', '/'):
            # load ip from a file
            f = file(b3.getAbsolutePath(self._publicIp, decode=True))
            self._publicIp = f.read().strip()
            f.close()

        if self._rconIp[0:1] in ('~', '/'):
            # load ip from a file
            f = file(b3.getAbsolutePath(self._rconIp, decode=True))
            self._rconIp = f.read().strip()
            f.close()

        try:
            # resolve domain names
            self._rconIp = socket.gethostbyname(self._rconIp)
        except socket.gaierror:
            pass

        self.bot('%s', b3.getB3versionString())
        self.bot('Python: %s', sys.version.replace('\n', ''))
        self.bot('Default encoding: %s', sys.getdefaultencoding())
        self.bot('Starting %s v%s for server %s:%s (autorestart = %s)', self.__class__.__name__,
                                                     getattr(getModule(self.__module__), '__version__', ' Unknown'),
                                                     self._rconIp, self._port, 'ON' if self.autorestart else 'OFF')

        # get events
        self.Events = b3.events.eventManager
        self._eventsStats = b3.events.EventsStats(self)

        self.bot('--------------------------------------------')

        # setup bot
        bot_name = self.config.get('b3', 'bot_name')
        if bot_name:
            self.name = bot_name

        bot_prefix = self.config.get('b3', 'bot_prefix')
        if bot_prefix:
            self.prefix = bot_prefix
        else:
            self.prefix = ''

        self.msgPrefix = self.prefix

        # delay between log reads
        if self.config.has_option('server', 'delay'):
            delay = self.config.getfloat('server', 'delay')
            if self.delay > 0:
                self.delay = delay

        # delay between each log's line processing
        if self.config.has_option('server', 'lines_per_second'):
            delay2 = self.config.getfloat('server', 'lines_per_second')
            if delay2 > 0:
                self.delay2 = 1/delay2

        try:
            # setup storage module
            dsn = self.config.get('b3', 'database')
            self.storage = b3.storage.getStorage(dsn=dsn, dsnDict=splitDSN(dsn), console=self)
        except (AttributeError, ImportError), e:
            # exit if we don't manage to setup the storage module: B3 will stop working upon Admin
            # Plugin loading so it makes no sense to keep going with the console initialization
            self.critical('Could not setup storage module: %s', e)

        # establish a connection with the database
        self.storage.connect()

        if self.config.has_option('server', 'game_log'):
            # open log file
            game_log = self.config.get('server', 'game_log')
            if game_log[0:6] == 'ftp://' or game_log[0:7] == 'sftp://' or game_log[0:7] == 'http://':
                self.remoteLog = True
                self.bot('Working in remote-log mode: %s', game_log)
                
                if self.config.has_option('server', 'local_game_log'):
                    f = self.config.getpath('server', 'local_game_log')
                else:
                    logext = str(self._rconIp.replace('.', '_'))
                    logext = 'games_mp_' + logext + '_' + str(self._port) + '.log'
                    f = os.path.normpath(os.path.expanduser(logext))

                # make sure game log file can be written
                f = b3.getWritableFilePath(f, True)

                if self.config.has_option('server', 'log_append'):
                    if not (self.config.getboolean('server', 'log_append') and os.path.isfile(f)):
                        self.screen.write('Creating gamelog : %s\n' % b3.getShortPath(os.path.abspath(f)))
                        ftptempfile = open(f, "w")
                        ftptempfile.close()
                    else:
                        self.screen.write('Append to gamelog: %s\n' % b3.getShortPath(os.path.abspath(f)))
                else:
                    self.screen.write('Creating gamelog : %s\n' % b3.getShortPath(os.path.abspath(f)))
                    ftptempfile = open(f, "w")
                    ftptempfile.close()
                    
            else:
                self.bot('Game log is: %s', game_log)
                f = self.config.getpath('server', 'game_log')

            self.bot('Starting bot reading file: %s', os.path.abspath(f))
            self.screen.write('Using gamelog    : %s\n' % b3.getShortPath(os.path.abspath(f)))

            if os.path.isfile(f):
                self.input = file(f, 'r')
                if self.config.has_option('server', 'seek'):
                    seek = self.config.getboolean('server', 'seek')
                    if seek:
                        self.input.seek(0, os.SEEK_END)
                else:
                    self.input.seek(0, os.SEEK_END)
            else:
                self.screen.write(">>> Cannot read file: %s\n" % os.path.abspath(f))
                self.screen.flush()
                self.critical("Cannot read file: %s", os.path.abspath(f))

        try:
            # setup rcon
            self.output = self.OutputClass(self, (self._rconIp, self._rconPort), self._rconPassword)
        except Exception, err:
            self.screen.write(">>> Cannot setup RCON: %s\n" % err)
            self.screen.flush()
            self.critical("Cannot setup RCON: %s" % err, exc_info=err)
        
        if self.config.has_option('server', 'rcon_timeout'):
            custom_socket_timeout = self.config.getfloat('server', 'rcon_timeout')
            self.output.socket_timeout = custom_socket_timeout
            self.bot('Setting rcon socket timeout to: %0.3f sec', custom_socket_timeout)

        # allow configurable max line length
        if self.config.has_option('server', 'max_line_length'):
            self._line_length = self.config.getint('server', 'max_line_length')
            self.bot('Setting line_length to: %s', self._line_length)

        # allow configurable line color prefix
        if self.config.has_option('server', 'line_color_prefix'):
            self._line_color_prefix = self.config.get('server', 'line_color_prefix')
            self.bot('Setting line_color_prefix to: "%s"', self._line_color_prefix)

        # testing rcon
        if self.rconTest:
            res = self.output.write('status')
            self.output.flush()
            self.screen.write('Testing RCON     : ')
            self.screen.flush()
            badRconReplies = ['Bad rconpassword.', 'Invalid password.']
            if res in badRconReplies:
                self.screen.write('>>> Oops: Bad RCON password\n'
                                  '>>> Hint: This will lead to errors and render B3 without any power to interact!\n')
                self.screen.flush()
                time.sleep(2)
            elif res == '':
                self.screen.write('>>> Oops: No response\n'
                                  '>>> Could be something wrong with the rcon connection to the server!\n'
                                  '>>> Hint 1: The server is not running or it is changing maps.\n'
                                  '>>> Hint 2: Check your server-ip and port.\n')
                self.screen.flush()
                time.sleep(2)
            else:
                self.screen.write('OK\n')

        self.loadEvents()
        self.screen.write('Loading events   : %s events loaded\n' % len(self._events))
        self.clients = Clients(self)

        self.loadPlugins()
        self.loadArbPlugins()

        self.game = b3.game.Game(self, self.gameName)

        try:
            queuesize = self.config.getint('b3', 'event_queue_size')
        except NoOptionError:
            queuesize = 50
        except ValueError, err:
            queuesize = 50
            self.warning(err)

        self.debug("Creating the event queue with size %s", queuesize)
        self.queue = Queue.Queue(queuesize)

        atexit.register(self.shutdown)

    def getAbsolutePath(self, path, decode=False):
        """
        Return an absolute path name and expand the user prefix (~)
        :param path: the relative path we want to expand
        """
        return b3.getAbsolutePath(path, decode=decode)

    def _dumpEventsStats(self):
        """
        Dump event statistics into the B3 log file.
        """
        self._eventsStats.dumpStats()

    def start(self):
        """
        Start B3
        """
        self.bot("Starting parser..")
        self.startup()
        self.say('%s ^2[ONLINE]' % b3.version)
        self.call_plugins_onLoadConfig()
        self.bot("Starting plugins")
        self.startPlugins()
        self._eventsStats_cronTab = b3.cron.CronTab(self._dumpEventsStats)
        self.cron.add(self._eventsStats_cronTab)
        self.bot("All plugins started")
        self.pluginsStarted()
        self.bot("Starting event dispatching thread")
        thread.start_new_thread(self.handleEvents, ())
        self.bot("Start reading game events")
        self.run()

    def die(self):
        """
        Stop B3 with the die exit status (222)
        """
        self.shutdown()
        self.finalize()
        time.sleep(5)
        self.exitcode = 222

    def restart(self):
        """
        Stop B3 with the restart exit status (221)
        """
        self.shutdown()
        time.sleep(5)
        self.bot('Restarting...')
        self.exitcode = 221

    def upTime(self):
        """
        Amount of time B3 has been running
        """
        return self.time() - self._timeStart

    def loadConfig(self, conf):
        """
        Set the config file to load
        """
        if not conf:
            return False

        self.config = conf
        """:type : MainConfig"""
        return True

    def saveConfig(self):
        """
        Save configration changes
        """
        self.bot('Saving config: %s', self.config.fileName)
        return self.config.save()

    def startup(self):
        """
        Called after the parser is created before run(). Overwrite this
        for anything you need to initialize you parser with.
        """
        pass

    def pluginsStarted(self):
        """
        Called after the parser loaded and started all plugins. 
        Overwrite this in parsers to take actions once plugins are ready
        """
        pass

    def pause(self):
        """
        Pause B3 log parsing
        """
        self.bot('PAUSING')
        self._paused = True

    def unpause(self):
        """
        Unpause B3 log parsing
        """
        self._paused = False
        self._pauseNotice = False
        self.input.seek(0, os.SEEK_END)

    def loadEvents(self):
        """
        Load events from event manager
        """
        self._events = self.Events.events

    def createEvent(self, key, name=None):
        """
        Create a new event
        """
        self.Events.createEvent(key, name)
        self._events = self.Events.events
        return self._events[key]

    def getEventID(self, key):
        """
        Get the numeric ID of an event key
        """
        return self.Events.getId(key)

    def getEvent(self, key, data=None, client=None, target=None):
        """
        Return a new Event object for an event name
        """
        return b3.events.Event(self.Events.getId(key), data, client, target)

    def getEventName(self, key):
        """
        Get the name of an event by its key
        """
        return self.Events.getName(key)

    def getEventKey(self, event_id):
        """
        Get the key of a given event ID
        """
        return self.Events.getKey(event_id)

    def getPlugin(self, plugin):
        """
        Get a reference to a loaded plugin
        """
        try:
            return self._plugins[plugin]
        except KeyError:
            return None

    def reloadConfigs(self):
        """
        Reload all config files
        """
        # reload main config
        self.config.load(self.config.fileName)
        for k in self._plugins:
            self.bot('Reload configuration file for plugin %s', k)
            self._plugins[k].loadConfig()
        self.updateDocumentation()

    def loadPlugins(self):
        """
        Load plugins specified in the config
        """
        self.screen.write('Loading plugins  : ')
        self.screen.flush()

        extplugins_dir = self.config.get_external_plugins_dir()
        self.bot('Loading plugins (external plugin directory: %s)' % extplugins_dir)

        def _get_plugin_config(p_name, p_clazz, p_config_path=None):
            """
            Helper that load and return a configuration file for the given Plugin
            :param p_name: The plugin name
            :param p_clazz: The class implementing the plugin
            :param p_config_path: The plugin configuration file path
            """
            def _search_config_file(match):
                """
                Helper that returns a list of configuration files.
                :param match: The plugin name
                """
                # first look in the built-in plugins directory
                search = '%s%s*%s*' % (b3.getAbsolutePath('@conf\\', decode=True), os.path.sep, match)
                self.debug('Searching for configuration file(s) matching: %s' % search)
                collection = glob.glob(search)
                if len(collection) > 0:
                    return collection
                # if none is found, then search in the extplugins directory
                search = '%s%s*%s*' % (os.path.join(b3.getAbsolutePath(extplugins_dir, decode=True), match, 'conf'), os.path.sep, match)
                self.debug('Searching for configuration file(s) matching: %s' % search)
                collection = glob.glob(search)
                return collection

            if p_config_path is None:
                # no plugin configuration file path specified: we can still load the plugin
                # if there is non need for a configuration file, otherwise we will lookup one
                if not p_clazz.requiresConfigFile:
                    self.debug('No configuration file specified for plugin %s: is not required either' % p_name)
                    return None

                # lookup a configuration file for this plugin
                self.warning('No configuration file specified for plugin %s: searching a valid configuration file...' % p_name)

                search_path = _search_config_file(p_name)
                if len(search_path) == 0:
                    # raise an exception so the plugin will not be loaded (since we miss the needed config file)
                    raise b3.config.ConfigFileNotFound('could not find any configuration file for plugin %s' % p_name)
                if len(search_path) > 1:
                    # log all the configuration files found so users can decide to remove some of them on the next B3 startup
                    self.warning('Multiple configuration files found for plugin %s: %s', p_name, ', '.join(search_path))

                # if the load fails, an exception is raised and the plugin won't be loaded
                self.warning('Using %s as configuration file for plugin %s', search_path[0], p_name)
                self.bot('Loading configuration file %s for plugin %s', search_path[0], p_name)
                return b3.config.load(search_path[0])
            else:
                # configuration file specified: load it if it's found. If we are not able to find the configuration
                # file, then keep loading the plugin if such a plugin doesn't require a configuration file (optional)
                # otherwise stop loading the plugin and loag an error message.
                p_config_absolute_path = b3.getAbsolutePath(p_config_path, decode=True)
                if os.path.exists(p_config_absolute_path):
                    self.bot('Loading configuration file %s for plugin %s', p_config_absolute_path, p_name)
                    return b3.config.load(p_config_absolute_path)

                # notice missing configuration file
                self.warning('Could not find specified configuration file %s for plugin %s', p_config_absolute_path, p_name)

                if p_clazz.requiresConfigFile:
                    # stop loading the plugin
                    raise b3.config.ConfigFileNotFound('plugin %s cannot be loaded without a configuration file' % p_name)

                self.warning('Not loading a configuration file for plugin %s: plugin %s can work also without a configuration file', p_name, p_name)
                self.info('NOTE: plugin %s may behave differently from what expected since no user configuration file has been loaded', p_name)
                return None

        plugin_list = []            # hold an unsorted plugins list used to filter plugins that needs to be excluded
        plugin_required = []        # hold a list of required plugin names which have not been specified in b3.ini
        sorted_plugin_list = []     # hold the list of plugins sorted according requirements
        plugins = OrderedDict()     # no need for OrderedDict anymore but keep for backwards compatibility!

        # here below we will parse the plugins section of b3.ini, looking for plugins to be loaded.
        # we will import needed python classes and generate configuration file instances for plugins.
        for p in self.config.get_plugins():

            if p['name'] in [plugins[i].name for i in plugins if plugins[i].name == p['name']]:
                # do not load a plugin multiple times
                self.warning('Plugin %s already loaded: avoid multiple entries of the same plugin', p['name'])
                continue

            try:
                mod = self.pluginImport(p['name'], p['path'])
                clz = getattr(mod, '%sPlugin' % p['name'].title())
                cfg = _get_plugin_config(p['name'], clz, p['conf'])
                plugins[p['name']] = PluginData(name=p['name'], module=mod, clazz=clz, conf=cfg, disabled=p['disabled'])
            except Exception, err:
                self.error('Could not load plugin %s' % p['name'], exc_info=err)

        # check for AdminPlugin
        if not 'admin' in plugins:
            # critical will exit, admin plugin must be loaded!
            self.critical('Plugin admin is essential and MUST be loaded! Cannot continue without admin plugin')

        # at this point we have an OrderedDict of PluginData of plugins listed in b3.ini and which can be loaded correctly:
        # all the plugins which have not been installed correctly, but are specified in b3.ini, have been already excluded.
        # next we build a list of PluginData instances and then we will sort it according to plugin order importance:
        #   - we'll try to load other plugins required by a listed one
        #   - we'll remove plugin that do not meet requirements

        def _get_plugin_data(p_data):
            """
            Return a list of PluginData of plugins needed by the current one
            :param p_data: A PluginData containing plugin information
            :return: list[PluginData] a list of PluginData of plugins needed by the current one
            """
            if p_data.clazz:

                # check for correct B3 version
                if p_data.clazz.requiresVersion and B3version(p_data.clazz.requiresVersion) > B3version(currentVersion):
                    raise MissingRequirement('plugin %s requires B3 version %s (you have version %s) : please update your '
                                             'B3 if you want to run this plugin' % (p_data.name, p_data.clazz.requiresVersion, currentVersion))

                # check if the current game support this plugin (this may actually exclude more than one plugin
                # in case a plugin is built on top of an incompatible one, due to plugin dependencies)
                if p_data.clazz.requiresParsers and self.gameName not in p_data.clazz.requiresParsers:
                    raise MissingRequirement('plugin %s is not compatible with %s parser : supported games are : %s' % (
                                             p_data.name, self.gameName, ', '.join(p_data.clazz.requiresParsers)))

                # check if the plugin needs a particular storage protocol to work
                if p_data.clazz.requiresStorage and self.storage.protocol not in p_data.clazz.requiresStorage:
                    raise MissingRequirement('plugin %s is not compatible with the storage protocol being used (%s) : '
                                             'supported protocols are : %s' % (p_data.name, self.storage.protocol,
                                                                               ', '.join(p_data.clazz.requiresStorage)))

                # check for plugin dependency
                if p_data.clazz.requiresPlugins:
                    # DFS: look first at the whole requirement tree and try to load from ground up
                    collection = [p_data]
                    for r in p_data.clazz.requiresPlugins:
                        if r not in plugins and r not in plugin_required:
                            try:
                                # missing requirement, try to load it
                                self.debug('Plugin %s has unmet dependency : %s : trying to load plugin %s...' % (p_data.name, r, r))
                                collection += _get_plugin_data(PluginData(name=r))
                                self.debug('Plugin %s dependency satisfied: %s' % (p_data.name, r))
                            except Exception, ex:
                                raise MissingRequirement('missing required plugin: %s : %s' % (r, extract_tb(sys.exc_info()[2])), ex)

                    return collection

            # plugin has not been loaded manually nor a previous automatic load attempt has been done
            if p_data.name not in plugins and p_data.name not in plugin_required:
                # we are at the bottom step where we load a new requirement by importing the
                # plugin module, class and configuration file. If the following generate an exception, recursion
                # will catch it here above and raise it back so we can exclude the first plugin in the list from load
                self.debug('Looking for plugin %s module and configuration file...' % p_data.name)
                p_data.module = self.pluginImport(p_data.name)
                p_data.clazz = getattr(p_data.module, '%sPlugin' % p_data.name.title())
                p_data.conf = _get_plugin_config(p_data.name, p_data.clazz)
                plugin_required.append(p_data.name) # load just once

            return [p_data]

        # construct a list of all the plugins which needs to be loaded
        # here below we will discard all the plugin which have unmet dependency
        for plugin_name, plugin_data in plugins.items():
            try:
                plugin_list += _get_plugin_data(plugin_data)
            except MissingRequirement, err:
                self.error('Could not load plugin %s' % plugin_name, exc_info=err)

        plugin_dict = {x.name: x for x in plugin_list}      # dict(str, PluginData)
        plugin_data = plugin_dict.pop('admin')              # remove admin plugin from dict
        plugin_list.remove(plugin_data)                     # remove admin plugin from unsorted list
        sorted_plugin_list.append(plugin_data)              # put admin plugin as first and discard from the sorting

        # sort remaining plugins according to their inclusion requirements
        self.bot('Sorting plugins according to their dependency tree...')
        sorted_list = [y for y in \
                        topological_sort([(x.name, set(x.clazz.requiresPlugins + [z for z in \
                            x.clazz.loadAfterPlugins if z in plugin_dict])) for x in plugin_list])]

        for plugin_name in sorted_list:
            sorted_plugin_list.append(plugin_dict[plugin_name])

        # make sure that required plugins are enabled (both if loaded in b3.ini or loaded automatically)
        for plugin_data in sorted_plugin_list:
            if plugin_data.disabled:
                if plugin_data.name == 'admin':
                    plugin_data.enabled = True
                else:
                    if plugin_data.clazz.requiresPlugins:
                        for req in plugin_data.clazz.requiresPlugins:
                            plugin_dict = {x.name: x for x in sorted_plugin_list}
                            if req in plugin_dict and plugin_dict[req].enabled:
                                plugin_data.enabled = True

        # notice in log for later inspection
        self.bot('Ready to create plugin instances: %s' % ', '.join([x.name for x in sorted_plugin_list]))

        plugin_num = 1
        self._plugins = OrderedDict()
        for plugin_data in sorted_plugin_list:

            plugin_conf_path = '--' if plugin_data.conf is None else plugin_data.conf.fileName

            try:
                self.bot('Loading plugin #%s : %s [%s]', plugin_num, plugin_data.name, plugin_conf_path)
                self._plugins[plugin_data.name] = plugin_data.clazz(self, plugin_data.conf)
            except Exception, err:
                self.error('Could not load plugin %s' % plugin_data.name, exc_info=err)
                self.screen.write('x')
            else:
                if plugin_data.disabled:
                    self.info("Disabling plugin %s" % plugin_data.name)
                    self._plugins[plugin_data.name].disable()
                plugin_num += 1
                version = getattr(plugin_data.module, '__version__', 'Unknown Version')
                author = getattr(plugin_data.module, '__author__', 'Unknown Author')
                self.bot('Plugin %s (%s - %s) loaded', plugin_data.name, version, author)
                self.screen.write('.')
            finally:
                self.screen.flush()

    def call_plugins_onLoadConfig(self):
        """
        For each loaded plugin, call the onLoadConfig hook.
        """
        for plugin_name in self._plugins:
            p = self._plugins[plugin_name]
            p.onLoadConfig()

    def loadArbPlugins(self):
        """
        Load must have plugins.
        """
        # if we fail to load one of those plugins, B3 will exit
        _mandatory_plugins = ['ftpytail', 'sftpytail', 'httpytail']

        def _load_plugin(console, plugin_name):
            """
            Helper which takes care of loading a single plugin.
            :param console: The current console instance
            :param plugin_name: The name of the plugin to load
            """
            try:
                console.bot('Loading plugin : %s', plugin_name)
                plugin_module = console.pluginImport(plugin_name)
                console._plugins[plugin_name] = getattr(plugin_module, '%sPlugin' % plugin_name.title())(console)
                version = getattr(plugin_module, '__version__', 'Unknown Version')
                author = getattr(plugin_module, '__author__', 'Unknown Author')
            except Exception, e:
                console.screen.write('x')
                if plugin_name in _mandatory_plugins:
                    # critical will stop B3 from running
                    console.screen.write('\n')
                    console.screen.write('>>> CRITICAL: missing mandatory plugin: %s\n' % plugin_name)
                    console.critical('Could not start B3 without %s plugin' % plugin_name, exc_info=e)
                else:
                    console.error('Could not load plugin %s' % plugin_name, exc_info=e)
            else:
                console.screen.write('.')
                console.bot('Plugin %s (%s - %s) loaded', plugin_name, version, author)
            finally:
                console.screen.flush()

        if 'publist' not in self._plugins:
            _load_plugin(self, 'publist')

        if self.config.has_option('server', 'game_log'):
            game_log = self.config.get('server', 'game_log')
            remote_log_plugin = None
            if game_log.startswith('ftp://'):
                remote_log_plugin = 'ftpytail'
            elif game_log.startswith('sftp://'):
                remote_log_plugin = 'sftpytail'
            elif game_log.startswith('http://'):
                remote_log_plugin = 'httpytail'

            if remote_log_plugin and remote_log_plugin not in self._plugins:
                _load_plugin(self, remote_log_plugin)

        self.screen.write(' (%s)\n' % len(self._plugins.keys()))
        self.screen.flush()

    def pluginImport(self, name, path=None):
        """
        Import a single plugin.
        :param name: The plugin name
        """
        if path is not None:
            # import error is being handled in loadPlugins already
            self.info('Loading plugin from specified path: %s', path)
            fp, pathname, description = imp.find_module(name, [path])
            try:
                return imp.load_module(name, fp, pathname, description)
            finally:
                if fp:
                    fp.close()

        fp = None

        try:
            fp, pathname, description = imp.find_module(name, [os.path.join(b3.getB3Path(True), 'plugins')])
            return imp.load_module(name, fp, pathname, description)
        except ImportError, m:
            self.verbose('%s is not a built-in plugin (%s)' % (name.title(), m))
            self.verbose('Trying external plugin directory : %s', self.config.get_external_plugins_dir())
            fp, pathname, description = imp.find_module(name, [self.config.get_external_plugins_dir()])
            return imp.load_module(name, fp, pathname, description)
        finally:
            if fp:
                fp.close()

    def startPlugins(self):
        """
        Start all loaded plugins.
        """
        self.screen.write('Starting plugins : ')
        self.screen.flush()

        def start_plugin(console, p_name):
            """
            Helper which handles the startup of a single plugin
            :param console: the console instance
            :param p_name: the plugin name
            """
            p = console._plugins[p_name]
            p.onStartup()
            p.start()

        plugin_num = 1

        for plugin_name in self._plugins:

            try:
                self.bot('Starting plugin #%s : %s' % (plugin_num, plugin_name))
                start_plugin(self, plugin_name)
            except Exception, err:
                self.error("Could not start plugin %s" % plugin_name, exc_info=err)
                self.screen.write('x')
            else:
                self.screen.write('.')
                plugin_num += 1
            finally:
                self.screen.flush()

        self.screen.write(' (%s)\n' % str(plugin_num - 1))

    def disablePlugins(self):
        """
        Disable all plugins except for 'admin', 'publist', 'ftpytail', 'sftpytail', 'httpytail', 'cod7http'
        """
        for k in self._plugins:
            if k not in ('admin', 'publist', 'ftpytail', 'sftpytail', 'httpytail', 'cod7http'):
                p = self._plugins[k]
                self.bot('Disabling plugin: %s', k)
                p.disable()

    def enablePlugins(self):
        """
        Enable all plugins except for 'admin', 'publist', 'ftpytail', 'sftpytail', 'httpytail', 'cod7http'
        """
        for k in self._plugins:
            if k not in ('admin', 'publist', 'ftpytail', 'sftpytail', 'httpytail', 'cod7http'):
                p = self._plugins[k]
                self.bot('Enabling plugin: %s', k)
                p.enable()

    def getMessage(self, msg, *args):
        """
        Return a message from the config file
        """
        try:
            msg = self._messages[msg]
        except KeyError:
            try:
                msg = self._messages[msg] = self.config.getTextTemplate('messages', msg)
            except Exception, err:
                self.warning("Falling back on default message for '%s': %s" % (msg, err))
                msg = vars2printf(self._messages_default.get(msg, '')).strip()

        if len(args):
            if type(args[0]) == dict:
                return msg % args[0]
            else:
                return msg % args
        else:
            return msg

    @staticmethod
    def getMessageVariables(*args, **kwargs):
        """
        Dynamically generate a dictionary of fields available for messages in config file.
        """
        variables = {}
        for obj in args:
            if obj is None:
                continue
            if type(obj).__name__ in ('str', 'unicode'):
                if obj not in variables:
                    variables[obj] = obj
            else:
                for attr in vars(obj):
                    pattern = re.compile('[\W_]+')
                    cleanattr = pattern.sub('', attr)  # trim any underscore or any non alphanumeric character
                    variables[cleanattr] = getattr(obj, attr)

        for key, obj in kwargs.iteritems():
            #self.debug('Type of kwarg %s: %s' % (key, type(obj).__name__))
            if obj is None:
                continue
            if type(obj).__name__ in ('str', 'unicode'):
                if key not in variables:
                    variables[key] = obj
            #elif type(obj).__name__ == 'instance':
                #self.debug('Classname of object %s: %s' % (key, obj.__class__.__name__))
            else:
                for attr in vars(obj):
                    pattern = re.compile('[\W_]+')
                    cleanattr = pattern.sub('', attr)  # trim any underscore or any non alphanumeric character
                    currkey = ''.join([key, cleanattr])
                    variables[currkey] = getattr(obj, attr)

        return variables

    def getCommand(self, cmd, **kwargs):
        """
        Return a reference to a loaded command
        """
        try:
            cmd = self._commands[cmd]
        except KeyError:
            return None

        return cmd % kwargs

    @Memoize
    def getGroup(self, data):
        """
        Return a valid Group from storage.
        <data> can be either a group keyword or a group level.
        Raises KeyError if group is not found.
        """
        if type(data) is int or isinstance(data, basestring) and data.isdigit():
            g = Group(level=data)
        else:
            g = Group(keyword=data)
        return self.storage.getGroup(g)

    def getGroupLevel(self, data):
        """
        Return a valid Group level.
        <data> can be either a group keyword or a group level.
        Raises KeyError if group is not found.
        """
        group = self.getGroup(data)
        return group.level

    def getTzOffsetFromName(self, tz_name=None):
        """
        Returns the timezone offset given its name.
        :param tz_name: The timezone name
        :return: tuple
        """
        if tz_name:
            if not tz_name in b3.timezones.timezones:
                self.warning("Unknown timezone name [%s]: falling back to auto-detection mode. Valid timezone codes can "
                             "be found on http://wiki.bigbrotherbot.net/doku.php/usage:available_timezones" % tz_name)
            else:
                self.info("Using timezone: %s : %s" % (tz_name, b3.timezones.timezones[tz_name]))
                return b3.timezones.timezones[tz_name], tz_name

        # AUTO-DETECT TZ NAME/OFFSET
        self.debug("Auto detecting timezone information...")

        # this will compute the timezone offset from from UTC
        tz_local = dateutil.tz.tzlocal()
        tz_info = tz_local.utcoffset(datetime.datetime.now(tz_local)).total_seconds() / 3600, \
                  tz_local.tzname(datetime.datetime.now(tz_local))

        self.info("Using timezone: %s : %s" % (tz_info[1], tz_info[0]))
        return tz_info

    def formatTime(self, gmttime, tz_name=None):
        """
        Return a time string formatted to local time in the b3 config time_format
        :param gmttime: The current GMT time
        :param tz_name: The timezone name to be used for time formatting
        """
        if tz_name:
            # if a timezone name has been specified try to use it to format the given gmttime
            tz_name = str(tz_name).strip().upper()
            try:
                # used when the user manually specifies the offset (i.e: !time +4)
                tz_offset = float(tz_name) * 3600
            except ValueError:
                # treat it as a timezone name (can potentially fallback to autodetection mode)
                tz_offset, tz_name = self.getTzOffsetFromName(tz_name)
        else:
            # use the timezone name specified in b3 main configuration file (if specified),
            # or make use of the timezone offset autodetection implemented in getTzOffsetFromName
            tz_name = None
            if self.config.has_option('b3', 'time_zone'):
                tz_name = self.config.get('b3', 'time_zone').strip().upper()
                tz_name = tz_name if tz_name and tz_name != 'AUTO' else None
            tz_offset, tz_name = self.getTzOffsetFromName(tz_name)

        time_format = self.config.get('b3', 'time_format').replace('%Z', tz_name).replace('%z', tz_name)
        self.debug('Formatting time with timezone [%s], tzOffset : %s' % (tz_name, tz_offset))
        return time.strftime(time_format, time.gmtime(gmttime + int(tz_offset * 3600)))

    def run(self):
        """
        Main worker thread for B3
        """
        self.screen.write('Startup complete : B3 is running! Let\'s get to work!\n\n')
        self.screen.write('If you run into problems check your B3 log file for more information\n')
        self.screen.flush()
        self.updateDocumentation()

        log_time_start = None
        log_time_last = 0
        while self.working:
            if self._paused:
                if not self._pauseNotice:
                    self.bot('PAUSED - not parsing any lines: B3 will be out of sync')
                    self._pauseNotice = True
            else:
                lines = self.read()
                if lines:
                    for line in lines:
                        line = str(line).strip()
                        if line and self._lineTime is not None:
                            # Track the log file time changes. This is mostly for
                            # parsing old log files for testing and to have time increase
                            # predictably
                            m = self._lineTime.match(line)
                            if m:
                                log_time_current = (int(m.group('minutes')) * 60) + int(m.group('seconds'))
                                if log_time_start and log_time_current - log_time_start < log_time_last:
                                    # Time in log has reset
                                    log_time_start = log_time_current
                                    log_time_last = 0
                                    self.debug('log time reset %d' % log_time_current)
                                elif not log_time_start:
                                    log_time_start = log_time_current

                                # Remove starting offset, we want the first line to be at 0 seconds
                                log_time_current -= log_time_start
                                self.logTime += log_time_current - log_time_last
                                log_time_last = log_time_current

                            self.console(line)

                            try:
                                self.parseLine(line)
                            except SystemExit:
                                raise
                            except Exception, msg:
                                self.error('Could not parse line %s: %s', msg, extract_tb(sys.exc_info()[2]))
                            
                            time.sleep(self.delay2)

            time.sleep(self.delay)

        self.bot('Stop reading')

        with self.exiting:
            self.input.close()
            self.output.close()

            if self.exitcode:
                sys.exit(self.exitcode)

    def parseLine(self, line):
        """
        Parse a single line from the log file
        """
        m = re.match(self._lineFormat, line)
        if m:
            self.queueEvent(b3.events.Event(self.getEventID('EVT_UNKNOWN'), m.group(2)[:1]))

    def registerHandler(self, event_name, event_handler):
        """
        Register an event handler.
        """
        self.debug('%s: register event <%s>', event_handler.__class__.__name__, self.getEventName(event_name))
        if not event_name in self._handlers:
            self._handlers[event_name] = []
        if event_handler not in self._handlers[event_name]:
            self._handlers[event_name].append(event_handler)

    def unregisterHandler(self, event_handler):
        """
        Unregister an event handler.
        """
        for event_name in self._handlers:
            if event_handler in self._handlers[event_name]:
                self.debug('%s: unregister event <%s>', event_handler.__class__.__name__, self.getEventName(event_name))
                self._handlers[event_name].remove(event_handler)

    def queueEvent(self, event, expire=10):
        """
        QueEvents.gevent for processing.
        """
        if not hasattr(event, 'type'):
            return False
        elif event.type in self._handlers:  # queue only if there are handlers to listen for this event
            self.verbose('Queueing event %s : %s', self.getEventName(event.type), event.data)
            try:
                time.sleep(0.001)  # wait a bit so event doesnt get jumbled
                self.queue.put((self.time(), self.time() + expire, event), True, 2)
                return True
            except Queue.Full:
                self.error('**** Event queue was full (%s)', self.queue.qsize())
                return False

        return False

    def handleEvents(self):
        """
        Event handler thread.
        """
        while self.working:
            added, expire, event = self.queue.get(True)
            if event.type == self.getEventID('EVT_EXIT') or event.type == self.getEventID('EVT_STOP'):
                self.working = False

            event_name = self.getEventName(event.type)
            self._eventsStats.add_event_wait((self.time() - added)*1000)
            if self.time() >= expire:  # events can only sit in the queue until expire time
                self.error('**** Event sat in queue too long: %s %s', event_name, self.time() - expire)
            else:
                nomore = False
                for hfunc in self._handlers[event.type]:
                    if not hfunc.isEnabled():
                        continue
                    elif nomore:
                        break

                    self.verbose('Parsing event: %s: %s', event_name, hfunc.__class__.__name__)
                    timer_plugin_begin = time.clock()
                    try:
                        hfunc.parseEvent(event)
                        time.sleep(0.001)
                    except b3.events.VetoEvent:
                        # plugin called for event hault, do not continue processing
                        self.bot('Event %s vetoed by %s', event_name, str(hfunc))
                        nomore = True
                    except SystemExit, e:
                        self.exitcode = e.code
                    except Exception, msg:
                        self.error('Handler %s could not handle event %s: %s: %s %s', hfunc.__class__.__name__,
                                   event_name, msg.__class__.__name__, msg, extract_tb(sys.exc_info()[2]))
                    finally:
                        elapsed = time.clock() - timer_plugin_begin
                        self._eventsStats.add_event_handled(hfunc.__class__.__name__, event_name, elapsed * 1000)
                    
        self.bot('Shutting down event handler')

        # releasing lock if it was set by self.shutdown() for instance
        if self.exiting.locked():
            self.exiting.release()

    def write(self, msg, maxRetries=None, socketTimeout=None):
        """
        Write a message to Rcon/Console
        """
        if self.output:
            res = self.output.write(msg, maxRetries=maxRetries, socketTimeout=socketTimeout)
            self.output.flush()
            return res

    def writelines(self, msg):
        """
        Write a sequence of messages to Rcon/Console. Optimized for speed.
        :param msg: The message to be sent to Rcon/Console.
        """
        if self.output and msg:
            res = self.output.writelines(msg)
            self.output.flush()
            return res

    def __read_input(self, game_log):
        """
        Read lines from the log file
        :param game_log: The gamelog file pointer
        """
        return game_log.readlines()

    def ___read_input_darwin(self, game_log):
        """
        Read lines from the log file (darwin version)
        :param game_log: The gamelog file pointer
        """
        return [game_log.readline()]

    def read(self):
        """
        Read from game server log file
        """
        if not hasattr(self, 'input'):
            self.critical("Cannot read game log file: check that you have a correct "
                          "value for the 'game_log' setting in your main config file")

        # Getting the stats of the game log (we are looking for the size)
        filestats = os.fstat(self.input.fileno())
        # Compare the current cursor position against the current file size,
        # if the cursor is at a number higher than the game log size, then
        # there's a problem
        if self.input.tell() > filestats.st_size:   
            self.debug('Parser: game log is suddenly smaller than it was before (%s bytes, now %s), '
                       'the log was probably either rotated or emptied. B3 will now re-adjust to the new '
                       'size of the log' % (str(self.input.tell()), str(filestats.st_size)))
            self.input.seek(0, os.SEEK_END)
        # NOTE: __read is defined at runtime in __new__
        return self.__read(self.input)

    def shutdown(self):
        """
        Shutdown B3.
        """
        try:
            if self.working and self.exiting.acquire():
                self.bot('Shutting down...')
                self.working = False
                for k, plugin in self._plugins.items():
                    plugin.parseEvent(b3.events.Event(self.getEventID('EVT_STOP'), ''))
                if self._cron:
                    self.bot('Stopping cron')
                    self._cron.stop()
                if self.storage:
                    self.bot('Shutting down database connection')
                    self.storage.shutdown()
        except Exception, e:
            self.error(e)

    def finalize(self):
        """
        Commons operation to be done on B3 shutdown.
        Called internally by b3.parser.die()
        """
        if b3.getPlatform() in ('linux', 'darwin'):
            # check for PID file if B3 has been started using the provided BASH initialization scripts.
            b3_name = os.path.basename(self.config.fileName)
            for x in ('.xml', '.ini'):
                b3_name = right_cut(b3_name, x)

            pidpath = os.path.join(b3.getAbsolutePath('@b3/', decode=True), '..', 'scripts', 'pid', '%s.pid' % b3_name)
            if os.path.isfile(pidpath):
                self.bot('Found PID file : %s : attempt to remove it' % pidpath)
                try:
                    os.unlink(pidpath)
                except Exception, e:
                    self.error('Could not remove PID file (%s) : %s' % (pidpath, e))
                else:
                    self.bot('PID file removed (%s)' % pidpath)

    def getWrap(self, text):
        """
        Returns a sequence of lines for text that fits within the limits.
        :param text: The text that needs to be splitted.
        """
        if not text:
            return []

        # remove all color codes if not needed
        if not self._use_color_codes:
            text = self.stripColors(text)

        if not self.wrapper:
            # initialize the text wrapper if not already instantiated
            self.wrapper = TextWrapper(width=self._line_length, drop_whitespace=True,
                                       break_long_words=True, break_on_hyphens=False)

        wrapped_text = self.wrapper.wrap(text)
        if self._use_color_codes:
            lines = []
            color = self._line_color_prefix
            for line in wrapped_text:
                if not lines:
                    lines.append('%s%s' % (color, line))
                else:
                    lines.append('^3>%s%s' % (color, line))
                match = re.findall(self._reColor, line)
                if match:
                    color = match[-1]
            return lines
        else:
            # we still need to add the > prefix w/o color codes
            # to all the lines except the first one
            lines = [wrapped_text[0]]
            if len(wrapped_text) > 1:
                for line in wrapped_text[1:]:
                    lines.append('>%s' % line)
            return lines

    def error(self, msg, *args, **kwargs):
        """
        Log an ERROR message.
        """
        self.log.error(msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        """
        Log a DEBUG message.
        """
        self.log.debug(msg, *args, **kwargs)

    def bot(self, msg, *args, **kwargs):
        """
        Log a BOT message.
        """
        self.log.bot(msg, *args, **kwargs)

    def verbose(self, msg, *args, **kwargs):
        """
        Log a VERBOSE message.
        """
        self.log.verbose(msg, *args, **kwargs)

    def verbose2(self, msg, *args, **kwargs):
        """
        Log an EXTRA VERBOSE message.
        """
        self.log.verbose2(msg, *args, **kwargs)

    def console(self, msg, *args, **kwargs):
        """
        Log a CONSOLE message.
        """
        self.log.console(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        """
        Log a WARNING message.
        """
        self.log.warning(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        """
        Log an INFO message.
        """
        self.log.info(msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        """
        Log an EXCEPTION message.
        """
        self.log.exception(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        """
        Log a CRITICAL message and shutdown B3.
        """
        self.log.critical(msg, *args, **kwargs)
        self.shutdown()
        self.finalize()
        time.sleep(2)
        self.exitcode = 220
        raise SystemExit(self.exitcode)

    @staticmethod
    def time():
        """
        Return the current time in GMT/UTC.
        """
        return int(time.time())

    def _get_cron(self):
        """
        Instantiate the main Cron object.
        """
        if not self._cron:
            self._cron = b3.cron.Cron(self)
            self._cron.start()
        return self._cron

    cron = property(_get_cron)

    def stripColors(self, text):
        """
        Remove color codes from the given text.
        :param text: the text to clean from color codes.
        :return: str
        """
        return re.sub(self._reColor, '', text).strip()

    def isFrostbiteGame(self, gamename=None):
        """
        Tells whether we are running a Frostbite based game.
        :return: True if we are running a Frostbite game, False otherwise
        """
        if not gamename:
            gamename = self.gameName
        return gamename in self._frostBiteGameNames

    def updateDocumentation(self):
        """
        Create a documentation for all available commands.
        """
        if self.config.has_section('autodoc'):
            try:
                from b3.tools.documentationBuilder import DocBuilder
                docbuilder = DocBuilder(self)
                docbuilder.save()
            except Exception, err:
                self.error("Failed to generate user documentation")
                self.exception(err)
        else:
            self.info('No user documentation generated: to enable update your configuration file')

    ####################################################################################################################
    #                                                                                                                  #
    #   INHERITING CLASSES MUST IMPLEMENTS THE FOLLOWING METHODS                                                       #
    #   PLUGINS THAT ARE GAME INDEPENDANT ASSUME THOSE METHODS EXIST                                                   #
    #                                                                                                                  #
    ####################################################################################################################

    def getPlayerList(self):
        """
        Query the game server for connected players.
        return a dict having players' id for keys and players' data as another dict for values
        """
        raise NotImplementedError

    def authorizeClients(self):
        """
        For all connected players, fill the client object with properties allowing to find 
        the user in the database (usualy guid, or punkbuster id, ip) and call the 
        Client.auth() method 
        """
        raise NotImplementedError
    
    def sync(self):
        """
        For all connected players returned by self.getPlayerList(), get the matching Client
        object from self.clients (with self.clients.getByCID(cid) or similar methods) and
        look for inconsistencies. If required call the client.disconnect() method to remove
        a client from self.clients.
        This is mainly useful for games where clients are identified by the slot number they
        occupy. On map change, a player A on slot 1 can leave making room for player B who
        connects on slot 1.
        """
        raise NotImplementedError
    
    def say(self, msg, *args):
        """
        Broadcast a message to all players
        """
        raise NotImplementedError

    def saybig(self, msg, *args):
        """
        Broadcast a message to all players in a way that will catch their attention.
        """
        raise NotImplementedError

    def message(self, client, text, *args):
        """
        Display a message to a given player
        """
        raise NotImplementedError

    def kick(self, client, reason='', admin=None, silent=False, *kwargs):
        """
        Kick a given player
        """
        raise NotImplementedError

    def ban(self, client, reason='', admin=None, silent=False, *kwargs):
        """
        Ban a given player on the game server and in case of success
        fire the event ('EVT_CLIENT_BAN', data={'reason': reason, 
        'admin': admin}, client=target)
        """
        raise NotImplementedError

    def unban(self, client, reason='', admin=None, silent=False, *kwargs):
        """
        Unban a given player on the game server
        """
        raise NotImplementedError

    def tempban(self, client, reason='', duration=2, admin=None, silent=False, *kwargs):
        """
        Tempban a given player on the game server and in case of success
        fire the event ('EVT_CLIENT_BAN_TEMP', data={'reason': reason, 
        'duration': duration, 'admin': admin}, client=target)
        """
        raise NotImplementedError

    def getMap(self):
        """
        Return the current map/level name
        """
        raise NotImplementedError

    def getNextMap(self):
        """
        Return the next map/level name to be played
        """
        raise NotImplementedError

    def getMaps(self):
        """
        Return the available maps/levels name
        """
        raise NotImplementedError

    def rotateMap(self):
        """
        Load the next map/level
        """
        raise NotImplementedError
        
    def changeMap(self, map_name):
        """
        Load a given map/level
        Return a list of suggested map names in cases it fails to recognize the map that was provided
        """
        raise NotImplementedError

    def getPlayerPings(self, filter_client_ids=None):
        """
        Returns a dict having players' id for keys and players' ping for values
        :param filter_client_ids: If filter_client_id is an iterable, only return values for the given client ids.
        """
        raise NotImplementedError

    def getPlayerScores(self):
        """
        Returns a dict having players' id for keys and players' scores for values
        """
        raise NotImplementedError
        
    def inflictCustomPenalty(self, penalty_type, client, reason=None, duration=None, admin=None, data=None):
        """
        Called if b3.admin.penalizeClient() does not know a given penalty type. 
        Overwrite this to add customized penalties for your game like 'slap', 'nuke', 
        'mute', 'kill' or anything you want.
        /!\ This method must return True if the penalty was inflicted.
        """
        pass


class StubParser(object):
    """
    Parser implementation used when dealing with the Storage module while updating B3 database.
    """

    screen = sys.stdout

    def __init__(self):

        class StubSTDOut(object):
            def write(self, *args, **kwargs):
                pass

        if not main_is_frozen():
            self.screen = StubSTDOut()

    def bot(self, msg, *args, **kwargs):
        pass

    def info(self, msg, *args, **kwargs):
        pass

    def debug(self, msg, *args, **kwargs):
        pass

    def error(self, msg, *args, **kwargs):
        pass

    def warning(self, msg, *args, **kwargs):
        pass

    def verbose(self, msg, *args, **kwargs):
        pass

    def verbose2(self, msg, *args, **kwargs):
        pass

    def critical(self, msg, *args, **kwargs):
        pass