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
# 2014/12/25 - 1.39   - Fenix           - new storage module initialization
# 2014/12/14 - 1.38.2 - Fenix           - correctly set exitcode variable in b3.parser.die() and b3.parser.restart(): B3
#                                         was calling sys.exit(*) in both methods but the main thread was expecting to
#                                         find the exit code in the exitcode (so the main thread was defaulting exit
#                                         code to 0). This fixes auto-restart mode not working.
#                                       - let the parser know if we are running B3 in auto-restart mode or not
# 2014/12/13 - 1.38.1 - Fenix           - moved b3.parser.finalize() call in b3.parser.die() from b3.parser.shutdown()
# 2014/12/11 - 1.38   - Fenix           - added plugin updater loading in loadArbPlugins
#                                       - make use of the newly declared function b3.functions.right_cut instead
# 2014/11/30 - 1.37.3 - Fenix           - correctly remove B3 PID file upon parser shutdown (Linux systems only)
# 2014/09/02 - 1.37.2 - Fenix           - moved _first_line_code attribute in _settings['line_color_prefix']
#                                       - allow customization of _settings['line_color_prefix'] from b3.xml:
#                                         setting 'line_color_prefix' in section 'server'
#                                       - slightly changed getWrap method to use a more pythonic approach
#                                       - make sure to have '>' prefix in getWrap method result (also when color codes
#                                         are not being used by the parser) when the result line is not the first of the
#                                         list
# 2014/09/01 - 1.37.1 - 82ndab-Bravo17  - Add color code options for new getWrap method
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
#                                         <plugin name="pluginname" config="@conf/plugin.xml" \
#                                                                                        path="C:\Users\me\myPlugin\"/>
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
# 10/03/2010 - v1.13  - Courgette       - add rconPort for games which have a different rcon port than the game port
#                                       - server.game_log option is not mandatory anymore. This makes B3 able to work
#                                         with game servers having no game log file
#                                       - do not test rcon anymore as the test process differs depending on the game
# 12/12/2009 - v1.12.3 - Courgette      - when working in remote mode, does not download the remote log file.
# 06/12/2009 - v1.12.2 - Courgette      - write() can specify a custom max_retries value
# 22/11/2009 - v1.12.1 - Courgette      - b3.xml can have option ('server','rcon_timeout') to specify a custom delay
#                                         (secondes) to use for the rcon socket
# 17/11/2009 - v1.12.0 - Courgette      - b3.xml can now have an optional section named 'devmode'
#                                       - move 'replay' option to section 'devmode'
#                                       - move 'delay' option to section 'b3'
#                                       - add option 'log2console' to section 'devmode'. This will make the bot
#                                         write to stderr instead of b3.log (useful if using eclipse or such IDE)
#                                       - fix replay mode when bot detected time reset from game log
# 09/10/2009 - v1.11.2 - xlr8or         - saved original sys.stdout to console.screen to aid communications to b3 screen
# 12/09/2009 - v1.11.1 - xlr8or         - added few functions and prevent spamming b3.log on pause
# 28/08/2009 - v1.11.0 - Bakes          - adds Remote B3 thru FTP functionality.
# 19/08/2009 - v1.10.0 - Courgette      - adds the inflict_custom_penalty() that allows to define game specific
#                                         penalties: requires admin.py v1.4+
# 10/7/2009  -         - xlr8or         - added code to load publist by default -
# 29/4/2009  -         - xlr8or         - fixed ignored exit code (for restarts/shutdowns)
# 10/20/2008 - 1.9.1b0 - mindriot       - fixed slight typo of b3.events.EVT_UNKOWN to b3.events.EVT_UNKNOWN
# 11/29/2005 - 1.7.0   - ThorN          - added atexit handlers
#                                       - added warning, info, exception, and critical log handlers

__author__ = 'ThorN, Courgette, xlr8or, Bakes, Ozon, Fenix'
__version__ = '1.39'

import os
import sys
import re
import time
import thread
import traceback
import Queue
import imp
import atexit
import socket
import glob

import b3
import b3.storage
import b3.events
import b3.output
import b3.game
import b3.cron
import b3.parsers.q3a.rcon
import b3.timezones

from ConfigParser import NoOptionError
from ConfigParser import NoSectionError
from b3.clients import Clients
from b3.clients import Group
from b3.decorators import memoize
from b3.functions import getModule
from b3.functions import vars2printf
from b3.functions import main_is_frozen
from b3.functions import splitDSN
from b3.functions import right_cut
from textwrap import TextWrapper

try:
    from xml.etree import cElementTree as ElementTree
except ImportError:
    from xml.etree import ElementTree


class Parser(object):

    _lineFormat = re.compile('^([a-z ]+): (.*?)', re.IGNORECASE)

    _handlers = {}
    _plugins = {}
    _pluginOrder = []
    _debug = True
    _paused = False
    _pauseNotice = False
    _events = {}
    _eventNames = {}
    _commands = {}

    _messages = {}  # message template cache

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

    _lineTime = None
    _timeStart = None

    encoding = 'latin-1'
    clients = None

    game = None
    gameName = None
    type = None
    working = True
    wrapper = None
    queue = None
    config = None
    storage = None
    output = None
    log = None
    replay = False
    remoteLog = False
    autorestart = False
    screen = None
    rconTest = False
    privateMsg = False

    # to apply between each game log lines fetching:
    # max time beforeva command is detected by the bot + (delay2 * nb_of_lines)
    delay = 0.33

    # to apply between each game log line processing:
    # max number of lines processed in one second
    delay2 = 0.02

    # time in seconds of epoch of game log
    logTime = 0

    # default outputclass set to the q3a rcon class
    OutputClass = b3.parsers.q3a.rcon.Rcon

    _use_color_codes = True

    _settings = {
        'line_length': 80,
        'line_color_prefix': '',
        'message_delay': 0
    }
    
    _eventsStats_cronTab = None
    _reColor = re.compile(r'\^[0-9a-z]')
    _cron = None

    name = 'b3'
    prefix = '^2%s:^3'
    pmPrefix = '^8[pm]^7'
    msgPrefix = ''
    deadPrefix = '[DEAD]^7'

    _publicIp = ''
    _rconIp = ''
    _rconPort = None
    _port = 0
    _rconPassword = ''

    # === Exiting ===
    #
    # The parser runs two threads: main and handler.  The main thread is
    # responsible for the main loop parsing and queuing events, and process
    # termination. The handler thread is responsible for processing queued events
    # including raising ``SystemExit'' when a user-requested exit is needed.
    #
    # The ``SystemExit'' exception bubbles up only as far as the top of the handler
    # thread -- the ``handle_events'' method.  To expose the exit status to the
    # ``run'' method in the main thread, we store the value in ``exitcode''.
    #
    # Since the teardown steps in ``run'' and ``handle_events'' would occur in
    # parallel, we use a lock (``exiting'') to ensure that ``run'' waits for
    # ``handle_events'' to finish before proceeding.
    #
    # How exiting works, in detail:
    #
    #   - the parallel loops in run() and handle_events() are terminated only when working==False.
    #   - die() or restart() invokes shutdown() from the handler thread.
    #   - the exiting lock is acquired by shutdown() in the handler thread before it sets working=False to
    #     end both loops.
    #   - die() or restart() raises SystemExit in the handler thread after shutdown() and a few seconds delay.
    #   - when SystemExit is caught by handle_events(), its exit status is pushed to the main context via exitcode.
    #   - handle_events() ensures the exiting lock is released when it finishes.
    #   - run() waits to acquire the lock in the main thread before proceeding with teardown, repeating
    #     sys.exit(exitcode) from the main thread if set.
    #
    #   In the case of an abnormal exception in the handler thread, ``exitcode''
    #   will be None and the ``exiting'' lock will be released when``handle_events''
    #   finishes so the main thread can still continue.
    #
    #   Exits occurring in the main thread do not need to be synchronised.

    exiting = thread.allocate_lock()
    exitcode = None

    def __init__(self, conf, autorestart=False):
        """
        Object contructor.
        :param conf: The B3 configuration file
        :param autorestart: Whether B3 is running in autorestart mode or not
        """
        self._timeStart = self.time()

        # store in the parser whether we are running B3 in autorestart mode so
        # plugins can react on this and perform different operations
        self.autorestart = autorestart

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

        self.log = b3.output.getInstance(logfile, self.config.getint('b3', 'log_level'), log2console)

        # save screen output to self.screen
        self.screen = sys.stdout
        print('Activating log   : %s' % logfile)
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
            f = file(self.getAbsolutePath(self._publicIp))
            self._publicIp = f.read().strip()
            f.close()

        if self._rconIp[0:1] in ('~', '/'):
            # load ip from a file
            f = file(self.getAbsolutePath(self._rconIp))
            self._rconIp = f.read().strip()
            f.close()

        try:
            # resolve domain names
            self._rconIp = socket.gethostbyname(self._rconIp)
        except socket.gaierror:
            pass

        self.bot('%s', b3.getB3versionString())
        self.bot('Python: %s', sys.version)
        self.bot('Default encoding: %s', sys.getdefaultencoding())
        self.bot('Starting %s v%s for server %s:%s', self.__class__.__name__,
                                                     getattr(getModule(self.__module__), '__version__', ' Unknown'),
                                                     self._rconIp, self._port)

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

        # demo mode: use log time
        if self.config.has_option('devmode', 'replay'):
            self.replay = self.config.getboolean('devmode', 'replay')
            if self.replay:
                self._timeStart = 0
                self.bot('Replay mode enabled')

        try:
            # setup storage module
            dsn = self.config.get('b3', 'database')
            self.storage = b3.storage.getStorage(dsn=dsn, dsnDict=splitDSN(dsn), console=self)
        except (AttributeError, ImportError), e:
            # exit if we don't manage to setup the storage module: B3 will stop working upon Admin
            # Plugin loading so it makes no sense to keep going with the console initialization
            self.critical('Could not setup storage module: %s' % e)

        # establish a connection with the database
        self.storage.connect()

        if self.config.has_option('server', 'game_log'):
            # open log file
            game_log = self.config.get('server', 'game_log')
            if game_log[0:6] == 'ftp://' or game_log[0:7] == 'sftp://' or game_log[0:7] == 'http://':
                self.remoteLog = True
                self.bot('Working in remote-log mode : %s' % game_log)
                
                if self.config.has_option('server', 'local_game_log'):
                    f = self.config.getpath('server', 'local_game_log')
                else:
                    logext = str(self._rconIp.replace('.', '_'))
                    logext = 'games_mp_' + logext + '_' + str(self._port) + '.log'
                    f = os.path.normpath(os.path.expanduser(logext))

                if self.config.has_option('server', 'log_append'):
                    if not (self.config.getboolean('server', 'log_append') and os.path.isfile(f)):
                        self.screen.write('Creating Gamelog : %s\n' % f)
                        ftptempfile = open(f, "w")
                        ftptempfile.close()
                    else:
                        self.screen.write('Append to Gamelog: %s\n' % f)
                else:
                    self.screen.write('Creating Gamelog : %s\n' % f)
                    ftptempfile = open(f, "w")
                    ftptempfile.close()
                    
            else:
                self.bot('Game log %s', game_log)
                f = self.config.getpath('server', 'game_log')

            self.bot('Starting bot reading file: %s', f)
            self.screen.write('Using Gamelog    : %s\n' % f)

            if os.path.isfile(f):
                self.input = file(f, 'r')
    
                # seek to point in log file?
                if self.replay:
                    pass
                elif self.config.has_option('server', 'seek'):
                    seek = self.config.getboolean('server', 'seek')
                    if seek:
                        self.input.seek(0, os.SEEK_END)
                else:
                    self.input.seek(0, os.SEEK_END)
            else:
                self.error('Error reading file: %s', f)
                raise SystemExit('ERROR reading file %s\n' % f)

        # setup rcon
        try:
            self.output = self.OutputClass(self, (self._rconIp, self._rconPort), self._rconPassword)
        except Exception, err:
            self.screen.write(">>> Cannot setup RCON. %s" % err)
            self.screen.flush()
            self.critical("Cannot setup RCON: %s" % err, exc_info=err)
        
        if self.config.has_option('server', 'rcon_timeout'):
            custom_socket_timeout = self.config.getfloat('server', 'rcon_timeout')
            self.output.socket_timeout = custom_socket_timeout
            self.bot('Setting Rcon socket timeout to: %0.3f sec' % custom_socket_timeout)
        
        # testing rcon
        if self.rconTest:
            res = self.output.write('status')
            self.output.flush()
            self.screen.write('Testing RCON     : ')
            self.screen.flush()
            _badRconReplies = ['Bad rconpassword.', 'Invalid password.']
            if res in _badRconReplies:
                self.screen.write('>>> Oops: Bad RCON password\n>>> Hint: This will lead to errors and '
                                  'render B3 without any power to interact!\n')
                self.screen.flush()
                time.sleep(2)
            elif res == '':
                self.screen.write('>>> Oops: No response\n>>> Could be something wrong with the rcon '
                                  'connection to the server!\n>>> Hint 1: The server is not running or it '
                                  'is changing maps.\n>>> Hint 2: Check your server-ip and port.\n')
                self.screen.flush()
                time.sleep(2)
            else:
                self.screen.write('OK\n')

        self.loadEvents()
        self.screen.write('Loading Events   : %s events loaded\n' % len(self._events))
        self.clients = Clients(self)
        self.loadPlugins()
        self.loadArbPlugins()

        # allow configurable max line length
        if self.config.has_option('server', 'max_line_length'):
            self._settings['line_length'] = self.config.getint('server', 'max_line_length')

        # allow configurable line color prefix
        if self.config.has_option('server', 'line_color_prefix'):
            self._settings['line_color_prefix'] = self.config.get('server', 'line_color_prefix')

        self.bot('Setting line_length to: %s' % self._settings['line_length'])
        self.bot('Setting line_color_prefix to: "%s"' % self._settings['line_color_prefix'])

        self.game = b3.game.Game(self, self.gameName)
        
        try:
            queuesize = self.config.getint('b3', 'event_queue_size')
        except NoOptionError:
            queuesize = 50
        except Exception, err:
            self.warning(err)
            queuesize = 50
        self.debug("Creating the event queue with size %s", queuesize)
        self.queue = Queue.Queue(queuesize)    # event queue

        atexit.register(self.shutdown)

    def getAbsolutePath(self, path):
        """
        Return an absolute path name and expand the user prefix (~)
        """
        return b3.getAbsolutePath(path)

    def _dumpEventsStats(self):
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
            p = self._plugins[k]
            self.bot('Reload plugin config for %s', k)
            p.loadConfig()

        self.updateDocumentation()

    def loadPlugins(self):
        """
        Load plugins specified in the config
        """
        self.screen.write('Loading Plugins  : ')
        self.screen.flush()
        
        extplugins_dir = self.config.getpath('plugins', 'external_dir')
        self.bot('Loading plugins (external plugin directory: %s)' % extplugins_dir)

        def _get_config_path(_plugin):
            """
            Helper that return a config path for the given Plugin
            """
            # read config path from b3 configuration
            cfg = _plugin.get('config')
            # check if the configuration file exists - if not, attempts to find the configuration file
            if cfg is not None and os.path.exists(self.getAbsolutePath(cfg)):
                return self.getAbsolutePath(cfg)
            else:
                # warn the users
                if cfg is None:
                    self.warning('No configuration file specified for plugin %s' % p.get('name'))
                else:
                    self.warning('The specified configuration file %s for the plugin %s does not exist'
                                 % (cfg, p.get('name')))

                # try to find a config file
                _cfg_path = glob.glob(self.getAbsolutePath('@b3\\conf\\') + '*%s*' % p.get('name'))
                if len(_cfg_path) == 0:
                    _cfg_path = glob.glob(self.getAbsolutePath(extplugins_dir) + '\\conf\\' + '*%s*' % p.get('name'))

                if len(_cfg_path) != 1 or _cfg_path[0] in [c.get('conf', '') for c in plugins.values()]:
                    # return none if no file found or file already loaded
                    return cfg
                else:
                    self.warning('Using %s as configuration file for %s' % (_cfg_path[0], p.get('name')))
                    return _cfg_path[0]

        plugins = {}
        plugin_sort = []

        priority = 1
        for p in self.config.get('plugins/plugin'):
            name = p.get('name')
            if not name:
                self.critical("Config error in the plugins section: "
                              "no plugin name found in [%s]" % ElementTree.tostring(p).strip())
                raise SystemExit(220)
            if name in [plugins[i]['name'] for i in plugins if plugins[i]['name'] == name]:
                self.warning('Plugin %s already loaded: avoid multiple entries of the same plugin' % name)
            else:
                conf = _get_config_path(p)
                #if conf is None:
                #    conf = '@b3/conf/plugin_%s.xml' % name
                disabledconf = p.get('disabled')
                disabled = disabledconf is not None and disabledconf.lower() in ('yes', '1', 'on', 'true')
                plugins[priority] = {'name': name,
                                     'conf': conf,
                                     'path': p.get('path'),
                                     'disabled': disabled}

                plugin_sort.append(priority)
                priority += 1

        plugin_sort.sort()

        self._pluginOrder = []
        for s in plugin_sort:
            plugin_name = plugins[s]['name']
            plugin_conf = plugins[s]['conf']
            self._pluginOrder.append(plugin_name)
            self.bot('Loading plugin #%s %s [%s]', s, plugin_name, plugin_conf)
            try:
                plugin_module = self.pluginImport(plugin_name, plugins[s]['path'])
                self._plugins[plugin_name] = getattr(plugin_module, '%sPlugin' % plugin_name.title())(self, plugin_conf)
                if plugins[s]['disabled']:
                    self.info("Disabling plugin %s" % plugin_name)
                    self._plugins[plugin_name].disable()
            except Exception, err:
                self.error('Error loading plugin %s' % plugin_name, exc_info=err)
            else:
                version = getattr(plugin_module, '__version__', 'Unknown Version')
                author = getattr(plugin_module, '__author__', 'Unknown Author')
                self.bot('Plugin %s (%s - %s) loaded', plugin_name, version, author)
                self.screen.write('.')
                self.screen.flush()

    def call_plugins_onLoadConfig(self):
        """
        For each loaded plugin, call the onLoadConfig hook
        """
        for plugin_name in self._pluginOrder:
            p = self._plugins[plugin_name]
            p.onLoadConfig()

    def loadArbPlugins(self):
        """
        Load must have plugins and check for admin plugin
        """
        def loadPlugin(parser_mod, plugin_id):
            parser_mod.bot('Loading plugin %s', plugin_id)
            plugin_module = parser_mod.pluginImport(plugin_id)
            parser_mod._plugins[plugin_id] = getattr(plugin_module, '%sPlugin' % plugin_id.title())(parser_mod)
            parser_mod._pluginOrder.append(plugin_id)
            version = getattr(plugin_module, '__version__', 'Unknown Version')
            author = getattr(plugin_module, '__author__', 'Unknown Author')
            parser_mod.bot('Plugin %s (%s - %s) loaded', plugin_id, version, author)
            parser_mod.screen.write('.')
            parser_mod.screen.flush()

        if 'publist' not in self._pluginOrder:
            try:
                loadPlugin(self, 'publist')
            except Exception, err:
                self.error('Could not load plugin publist', exc_info=err)

        if not main_is_frozen():
            # load the updater plugin if we are running B3 from sources
            if 'updater' not in self._pluginOrder:
                try:
                    update_channel = self.config.get('update', 'channel')
                    if update_channel == 'skip':
                        self.debug('Not loading plugin updater: update channel not specified in B3 configuration file')
                    else:
                        try:
                            loadPlugin(self, 'updater')
                        except Exception, err:
                            self.error('Could not load plugin updater', exc_info=err)
                except (NoSectionError, NoOptionError):
                    self.debug('Not loading plugin updater: update section missing in B3 main configuration file')

        if self.config.has_option('server', 'game_log'):
            game_log = self.config.get('server', 'game_log')
            remote_log_plugin = None
            if game_log.startswith('ftp://'):
                remote_log_plugin = 'ftpytail'
            elif game_log.startswith('sftp://'):
                remote_log_plugin = 'sftpytail'
            elif game_log.startswith('http://'):
                remote_log_plugin = 'httpytail'

            if remote_log_plugin and remote_log_plugin not in self._pluginOrder:
                try:
                    loadPlugin(self, remote_log_plugin)
                except Exception, err:
                    self.critical('Error loading plugin %s' % remote_log_plugin, exc_info=err)
                    raise SystemExit('ERROR while loading %s' % remote_log_plugin)

        if 'admin' not in self._pluginOrder:
            # critical will exit, admin plugin must be loaded!
            self.critical('AdminPlugin is essential and MUST be loaded! Cannot continue without admin plugin')

        self.screen.write(' (%s)\n' % len(self._pluginOrder))
        self.screen.flush()

    def pluginImport(self, name, path=None):
        """
        Import a single plugin
        """
        if path is not None:
            try:
                self.info('Loading plugin from specified path: %s', path)
                fp, pathname, description = imp.find_module(name, [path])
                try:
                    return imp.load_module(name, fp, pathname, description)
                finally:
                    if fp:
                        fp.close()
            except ImportError, err:
                self.error(err)
        try:
            module = 'b3.plugins.%s' % name
            mod = __import__(module)
            components = module.split('.')
            for comp in components[1:]:
                mod = getattr(mod, comp)
            return mod
        except ImportError, m:
            self.info('%s is not a built-in plugin (%s)', name, m)
            self.info('Trying external plugin directory : %s', self.config.getpath('plugins', 'external_dir'))
            fp, pathname, description = imp.find_module(name, [self.config.getpath('plugins', 'external_dir')])
            try:
                return imp.load_module(name, fp, pathname, description)
            finally:
                if fp:
                    fp.close()

    def startPlugins(self):
        """
        Start all loaded plugins.
        """
        self.screen.write('Starting Plugins : ')
        self.screen.flush()

        def start_plugin(p_name):
            p = self._plugins[p_name]
            self.bot('Starting plugin %s', p_name)
            p.onStartup()
            p.start()
            #time.sleep(1)    # give plugin time to crash, er...start
            self.screen.write('.')
            self.screen.flush()

        # handle admin plugin first as many plugins rely on it
        if 'admin' in self._pluginOrder:
            start_plugin('admin')
            self._pluginOrder.remove('admin')

        # start other plugins
        for plugin_name in self._pluginOrder:
            if plugin_name not in self._plugins:
                self.warning("Not starting plugin %s as it was not loaded" % plugin_name)
            else:
                try:
                    start_plugin(plugin_name)
                except Exception, err:
                    self.error("Could not start plugin %s" % plugin_name, exc_info=err)

        self.screen.write(' (%s)\n' % (len(self._pluginOrder)+1))

    def disablePlugins(self):
        """
        Disable all plugins except for publist, ftpytail and admin
        """
        for k in self._pluginOrder:
            if k not in ('admin', 'publist', 'ftpytail'):
                p = self._plugins[k]
                self.bot('Disabling plugin: %s', k)
                p.disable()

    def enablePlugins(self):
        """
        Enable all plugins except for publist, ftpytail and admin
        """
        for k in self._pluginOrder:
            if k not in ('admin', 'publist', 'ftpytail'):
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

    def getMessageVariables(self, *args, **kwargs):
        """
        Dynamically generate a dictionary of fields available for messages in config file.
        """
        variables = {}
        for obj in args:
            if obj is None:
                continue
            if type(obj).__name__ in ('str', 'unicode'):
                if obj not in variables.keys():
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
                if key not in variables.keys():
                    variables[key] = obj
            #elif type(obj).__name__ == 'instance':
                #self.debug('Classname of object %s: %s' % (key, obj.__class__.__name__))
            else:
                for attr in vars(obj):
                    pattern = re.compile('[\W_]+')
                    cleanattr = pattern.sub('', attr)  # trim any underscore or any non alphanumeric character
                    currkey = ''.join([key, cleanattr])
                    variables[currkey] = getattr(obj, attr)

        # For debug purposes, uncomment to see in the log a list of the available fields
        # allkeys = variables.keys()
        # allkeys.sort()
        # for key in allkeys:
        #     self.debug('%s has value %s' % (key, variables[key]))
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

    @memoize
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

    def getTzOffsetFromName(self, tz_name):
        try:
            tz_offset = b3.timezones.timezones[tz_name] * 3600
        except KeyError:
            try:
                self.warning("Unknown timezone name [%s]: valid timezone codes can be found on "
                             "http://wiki.bigbrotherbot.net/doku.php/usage:available_timezones" % tz_name)
                tz_offset = time.timezone
                if tz_offset < 0:
                    tz_name = 'UTC%s' % (tz_offset/3600)
                else:
                    tz_name = 'UTC+%s' % (tz_offset/3600)
                self.info("Using system offset [%s]", tz_offset)
            except KeyError:
                self.error("Unknown timezone name [%s]: valid timezone codes can be found on "
                           "http://wiki.bigbrotherbot.net/doku.php/usage:available_timezones" % tz_name)
                tz_name = 'UTC'
                tz_offset = 0
        return tz_offset, tz_name

    def formatTime(self, gmttime, tz_name=None):
        """
        Return a time string formated to local time in the b3 config time_format
        """
        if tz_name:
            tz_name = str(tz_name).strip().upper()
            try:
                tz_offset = float(tz_name) * 3600
            except ValueError:
                tz_offset, tz_name = self.getTzOffsetFromName(tz_name)
        else:
            tz_name = self.config.get('b3', 'time_zone').upper()
            tz_offset, tz_name = self.getTzOffsetFromName(tz_name)

        time_format = self.config.get('b3', 'time_format').replace('%Z', tz_name).replace('%z', tz_name)
        self.debug('Formatting time with timezone [%s], tzOffset : %s' % (tz_name, tz_offset))
        return time.strftime(time_format, time.gmtime(gmttime + tz_offset))

    def run(self):
        """
        Main worker thread for B3
        """
        self.screen.write('Startup Complete : B3 is running! Let\'s get to work!\n\n')
        self.screen.write('(If you run into problems, check %s in the B3 root directory for '
                          'detailed log info)\n' % self.config.getpath('b3', 'logfile'))
        
        #self.screen.flush()
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

                            if self.replay:                    
                                self.debug('log time %d' % self.logTime)

                            self.console(line)

                            try:
                                self.parseLine(line)
                            except SystemExit:
                                raise
                            except Exception, msg:
                                self.error('Could not parse line %s: %s', msg, traceback.extract_tb(sys.exc_info()[2]))
                            
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
        self.debug('%s: register event <%s>', event_handler.__class__.__name__, self.Events.getName(event_name))
        if not event_name in self._handlers.keys():
            self._handlers[event_name] = []
        if event_handler not in self._handlers[event_name]:
            self._handlers[event_name].append(event_handler)

    def queueEvent(self, event, expire=10):
        """
        Queue an event for processing.
        """
        if not hasattr(event, 'type'):
            return False
        elif event.type in self._handlers.keys():  # queue only if there are handlers to listen for this event
            self.verbose('Queueing event %s %s', self.Events.getName(event.type), event.data)
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

            event_name = self.Events.getName(event.type)
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
                                   event_name, msg.__class__.__name__, msg, traceback.extract_tb(sys.exc_info()[2]))
                    finally:
                        elapsed = time.clock() - timer_plugin_begin
                        self._eventsStats.add_event_handled(hfunc.__class__.__name__, event_name, elapsed*1000)
                    
        self.bot('Shutting down event handler')

        # releasing lock if it was set by self.shutdown() for instance
        if self.exiting.locked():
            self.exiting.release()

    def write(self, msg, maxRetries=None):
        """
        Write a message to Rcon/Console
        """
        if self.replay:
            self.bot('Sent rcon message: %s' % msg)
        elif self.output is None:
            pass
        else:
            res = self.output.write(msg, maxRetries=maxRetries)
            self.output.flush()
            return res

    def writelines(self, msg):
        """
        Write a sequence of messages to Rcon/Console. Optimized for speed.
        :param msg: The message to be sent to Rcon/Console.
        """
        if self.replay:
            self.bot('Sent rcon message: %s' % msg)
        elif self.output is None:
            pass
        elif not msg:
            pass
        else:
            res = self.output.writelines(msg)
            self.output.flush()
            return res

    def read(self):
        """
        Read from game server log file
        """
        if not hasattr(self, 'input'):
            self.critical("Cannot read game log file: check that you have a correct "
                          "value for the 'game_log' setting in your main config file.")
            raise SystemExit(220)

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
        return self.input.readlines() 

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
                    self._cron.stop()

                self.bot('Shutting down database connections...')
                self.storage.shutdown()
        except Exception, e:
            self.error(e)

    def finalize(self):
        """
        Commons operation to be done on B3 shutdown.
        Called internally by b3.parser.die()
        """
        if os.name == 'posix':

            b3_name = os.path.basename(self.config.fileName)
            for val in ('.xml', '.ini'):
                b3_name = right_cut(b3_name, val)

            pid_path = os.path.join(right_cut(sys.path[0], '/b3'), 'scripts', 'pid', '%s.pid' % b3_name)
            self.bot('Looking for PID file: %s ...' % pid_path)
            if os.path.isfile(pid_path):
                try:
                    self.bot('Removing PID file: %s ...' % pid_path)
                    os.unlink(pid_path)
                except Exception, e:
                    self.error('Could not remove PID file: %s' % e)
            else:
                self.bot('PID file not found')

    def getWrap(self, text):
        """
        Returns a sequence of lines for text that fits within the limits.
        :param text: The text that needs to be splitted.
        """
        if not text:
            return []

        if not self.wrapper:
            # initialize the text wrapper if not already instantiated
            self.wrapper = TextWrapper(width=self._settings['line_length'], drop_whitespace=True,
                                       break_long_words=True, break_on_hyphens=False)

        wrapped_text = self.wrapper.wrap(text)
        if self._use_color_codes:
            lines = []
            color = self._settings['line_color_prefix']
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
        Log a CRITICAL message.
        """
        self.log.critical(msg, *args, **kwargs)

    def time(self):
        """
        Return the current time in GMT/UTC.
        """
        if self.replay:
            return self.logTime
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
        return re.sub(self._reColor, '', text).strip()

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
    ##                                                                                                                ##
    ##     INHERITING CLASSES MUST IMPLEMENTS THE FOLLOWING METHODS                                                   ##
    ##     PLUGINS THAT ARE GAME INDEPENDANT ASSUME THOSE METHODS EXIST                                               ##
    ##                                                                                                                ##
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
    
    def say(self, msg):
        """
        Broadcast a message to all players
        """
        raise NotImplementedError

    def saybig(self, msg):
        """
        Broadcast a message to all players in a way that will catch their attention.
        """
        raise NotImplementedError

    def message(self, client, text):
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
        
    def inflictCustomPenalty(self, type, client, reason=None, duration=None, admin=None, data=None):
        """
        Called if b3.admin.penalizeClient() does not know a given penalty type. 
        Overwrite this to add customized penalties for your game like 'slap', 'nuke', 
        'mute', 'kill' or anything you want.
        /!\ This method must return True if the penalty was inflicted.
        """
        pass

if __name__ == '__main__':
    import config
    parser = Parser(config.load('conf/b3.xml'))
    print parser
    print parser.start()