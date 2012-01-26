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
#   2011/06/05 - 1.27 - xlr8or
#   * implementation of game server encoding/decoding
#   2011/09/12 - 1.26.2 - Courgette
#   * start the admin plugin first as many plugins relie on it (does not affect
#     plugin priority in regard to B3 events dispatching)
#   2011/06/05 - 1.26.1 - Courgette
#   * fix periodic events stats dumping blocking B3 restart/shutdown
#   2011/05/03 - 1.24.8 - Courgette
#   * event queue size can be set in b3.xml in section 'b3/event_queue_size'
#   2011/05/03 - 1.24.7 - Courgette
#   * add periodic events stats dumping to detect slow plugins
#   2011/05/03 - 1.24.6 - Courgette
#   * do not run update sql queries on startup
#   2011/05/03 - 1.24.5 - Courgette
#   * fix bug regarding rcon_ip introduced in 1.24.4
#   2011/04/31 - 1.24.4 - Courgette
#   * add missing b3.timezones import
#   2011/04/30 - 1.24.3 - Courgette
#   * move the B3 start announcement that is broadcasted on the game server after
#     the parser startup() method has been called to give a change to parsers to
#     set up their rcon before it is used.
#   * rcon_ip, rcon_password not mandatory anymore to suport games that have rcon
#     working through files
#   2011/04/27 - 1.24.2 - 82ndab-Bravo17
#   * Auto assign of unique local games_mp log file
#   2011/04/20 - 1.24.1 - Courgette
#   * fix auto detection of locale timezone offset
#   2011/03/30 - 1.24 - Courgette
#   * remove output option log2both and changed the behavior of log2console so
#     that the console log steam is not replacing the stream going to the log file
#   2011/02/03 - 1.23 - Bravo17
#   * allow local log to be appended to instead of overwritten for games with remote logs
#   2010/11/25 - 1.22 - Courgette
#   * at start, can load a plugin in 'disabled' state. Use the 'disabled' as follow :
#         <plugin name="adv" config="@conf/plugin_adv.xml" disabled="Yes"/>
#   2010/11/18 - 1.21 - Courgette
#   * do not resolve eventual domain name found in public_ip
#   2010/11/07 - 1.20.2 - GrosBedo
#   * edited default values of lines_per_second and delay
#   2010/11/07 - 1.20.1 - GrosBedo
#   * added a new dynamical function getMessageVariables to parse messages
#   2010/10/28 - 1.20.0 - Courgette
#   * support an new optional syntax for loading plugins in b3.xml which enable
#     to specify a directory where to find the plugin with the 'path' attribute.
#     This overrides the default and extplugins folders. Example :
#     <plugin name="pluginname" config="@conf/plugin.xml" path="C:\Users\me\myPlugin\"/>
#   2010/10/22 - 1.19.4 - xlr8or
#   * output option log2both writes to logfile AND stderr simultaneously
#   2010/10/06 - 1.19.3 - xlr8or
#   * reintroduced rcontesting on startup, but for q3a based only (rconTest var in parser)
#   2010/09/04 - 1.19.2 - GrosBedo
#   * fixed some typos
#   * moved delay and lines_per_second settings to server category
#   2010/09/04 - 1.19.1 - Grosbedo
#   * added b3/local_game_log option for several remote log reading at once
#   * added http remote log support
#   * delay2 -> lines_per_second
#   2010/09/01 - 1.19 - Grosbedo
#   * reduce disk access costs by reading multiple lines at once from the game log file
#   2010/09/01 - 1.18 - Grosbedo
#   * detect game log file rotation
#   2010/09/01 - 1.17 - Courgette
#   * add beta support for sftp protocol for reading remote game log file
#   2010/08/14 - 1.16.1 - Courgette
#   * fallback on UTC timezone in case the timezone name is not valid
#   2010/04/17 - 1.16 - Courgette
#   * plugin priority is defined by their order in the b3.xml file 
#   * fix bug in getEventName()
#   2010/04/10 - 1.15.1 - Courgette
#   * write the parser version to log file
#   2010/04/10 - 1.15 - Courgette
#   * public_ip and rcon_ip can now be domain names
#   2010/04/10 - 1.14.3 - Bakes
#   * added saybig() to method stubs for inheriting classes.
#   2010/03/23 - 1.14.2 - Bakes
#   * add message_delay for better BFBC2 interoperability.
#   2010/03/22 - 1.14.1 - Courgette
#   * change maprotate() to rotateMap()
#   2010/03/21 - 1.14 - Courgette
#    * create method stubs for inheriting classes to implement
#   10/03/2010 - v1.13 - Courgette
#    * add rconPort for games which have a different rcon port than the game port
#    * server.game_log option is not mandatory anymore. This makes B3 able to work
#      with game servers having no game log file
#    * do not test rcon anymore as the test process differs depending on the game
#   12/12/2009 - v1.12.3 - Courgette
#    * when working in remote mode, does not download the remote log file.
#   06/12/2009 - v1.12.2 - Courgette
#    * write() can specify a custom maxRetries value
#   22/11/2009 - v1.12.1 - Courgette
#    * b3.xml can have option ('server','rcon_timeout') to specify a custom delay
#      (in secondes) to use for the rcon socket
#   17/11/2009 - v1.12.0 - Courgette
#    * b3.xml can now have an optional section named 'devmode'
#    * move 'replay' option to section 'devmode'
#    * move 'delay' option to section 'b3'
#    * add option 'log2console' to section 'devmode'. This will make the bot
#      write to stderr instead of b3.log (useful if using eclipse or such IDE)
#    * fix replay mode when bot detected time reset from game log
#   09/10/2009 - v1.11.2 - xlr8or
#    * Saved original sys.stdout to console.screen to aid communications to b3 screen
#   12/09/2009 - v1.11.1 - xlr8or
#    * Added few functions and prevent spamming b3.log on pause
#   28/08/2009 - v1.11.0 - Bakes
#    * adds Remote B3 thru FTP functionality.
#   19/08/2009 - v1.10.0 - courgette
#    * adds the inflictCustomPenalty() that allows to define game specific penalties.
#      requires admin.py v1.4+
#   10/7/2009 - added code to load publist by default - xlr8or
#   29/4/2009 - fixed ignored exit code (for restarts/shutdowns) - arbscht
#   10/20/2008 - 1.9.1b0 - mindriot
#    * fixed slight typo of b3.events.EVT_UNKOWN to b3.events.EVT_UNKNOWN
#   11/29/2005 - 1.7.0 - ThorN
#    Added atexit handlers
#    Added warning, info, exception, and critical log handlers

__author__  = 'ThorN, Courgette, xlr8or, Bakes'
__version__ = '1.27'

# system modules
import os, sys, re, time, thread, traceback, Queue, imp, atexit, socket, threading

import b3
import b3.storage
import b3.events
import b3.output

import b3.game
import b3.cron
import b3.parsers.q3a.rcon
import b3.clients
import b3.functions
import b3.timezones
from ConfigParser import NoOptionError
from b3.functions import main_is_frozen, getModule, executeSql


class Parser(object):
    _lineFormat = re.compile('^([a-z ]+): (.*?)', re.IGNORECASE)

    _handlers = {}
    _plugins  = {}
    _pluginOrder = []
    _paused = False
    _pauseNotice = False
    _events = {}
    _eventNames = {}
    _commands = {}
    _messages = {}
    _timeStart = None

    encoding = 'latin-1'
    clients  = None
    delay = 0.33 # to apply between each game log lines fetching (max time before a command is detected by the bot + (delay2*nb_of_lines) )
    delay2 = 0.02 # to apply between each game log line processing (max number of lines processed in one second)
    game = None
    gameName = None
    type = None
    working = True
    queue = None
    config = None
    storage = None
    _debug = True
    output = None
    log = None
    replay = False
    remoteLog = False
    screen = None
    rconTest = False

    # Time in seconds of epoch of game log
    logTime = 0

    # Default outputclass set to the q3a rcon class
    OutputClass = b3.parsers.q3a.rcon.Rcon

    _settings = {}
    _settings['line_length'] = 65
    _settings['min_wrap_length'] = 100
    _settings['message_delay'] = 0

    _reColor = re.compile(r'\^[0-9a-z]')
    _cron = None

    name = 'b3'
    prefix = '^2%s:^3'
    msgPrefix = ''

    _publicIp = ''
    _rconIp = ''
    _rconPort = None
    _port = 0
    _rconPassword = ''

    info = None

    """\
    === Exiting ===

    The parser runs two threads: main and handler.  The main thread is
    responsible for the main loop parsing and queuing events, and process
    termination. The handler thread is responsible for processing queued events
    including raising ``SystemExit'' when a user-requested exit is needed.

    The ``SystemExit'' exception bubbles up only as far as the top of the handler
    thread -- the ``handleEvents'' method.  To expose the exit status to the
    ``run'' method in the main thread, we store the value in ``exitcode''.

    Since the teardown steps in ``run'' and ``handleEvents'' would occur in
    parallel, we use a lock (``exiting'') to ensure that ``run'' waits for
    ``handleEvents'' to finish before proceeding.

    How exiting works, in detail:

      - the parallel loops in run() and handleEvents() are terminated only when
          working==False.

      - die() or restart() invokes shutdown() from the handler thread.

      - the exiting lock is acquired by shutdown() in the handler thread before
          it sets working=False to end both loops.

      - die() or restart() raises SystemExit in the handler thread after
          shutdown() and a few seconds delay.

      - when SystemExit is caught by handleEvents(), its exit status is pushed to
          the main context via exitcode.

      - handleEvents() ensures the exiting lock is released when it finishes.

      - run() waits to acquire the lock in the main thread before proceeding
          with teardown, repeating sys.exit(exitcode) from the main thread if set.

      In the case of an abnormal exception in the handler thread, ``exitcode''
      will be None and the ``exiting'' lock will be released when``handleEvents''
      finishes so the main thread can still continue.

      Exits occurring in the main thread do not need to be synchronised.

    """
    exiting = thread.allocate_lock()
    exitcode = None

    def __init__(self, config):
        self._timeStart = self.time()

        if not self.loadConfig(config):
            print('CRITICAL ERROR : COULD NOT LOAD CONFIG')
            raise SystemExit(220)

        # set game server encoding
        if self.config.has_option('server', 'encoding'):
            self.encoding = self.config.get('server', 'encoding')

        # set up logging
        logfile = self.config.getpath('b3', 'logfile')
        log2console = self.config.has_option('devmode', 'log2console') and self.config.getboolean('devmode', 'log2console')
        self.log = b3.output.getInstance(logfile, self.config.getint('b3', 'log_level'), log2console)

        # save screen output to self.screen
        self.screen = sys.stdout
        print('Activating log   : %s' % logfile)
        sys.stdout = b3.output.stdoutLogger(self.log)
        sys.stderr = b3.output.stderrLogger(self.log)

        # setup ip addresses
        if self.gameName in ('bf3'):
            # for some games we do not need any game ip:port
            self._publicIp = self.config.get('server', 'public_ip') if self.config.has_option('server', 'public_ip') else ''
            self._port = self.config.getint('server', 'port') if self.config.has_option('server', 'port') else ''
        else:
            self._publicIp = self.config.get('server', 'public_ip')
            self._port = self.config.getint('server', 'port')
        self._rconPort = self._port # if rcon port is the same as the game port, rcon_port can be ommited
        self._rconIp = self._publicIp # if rcon ip is the same as the game port, rcon_ip can be ommited
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
        except:
            pass

        self.bot('%s', b3.getB3versionString())
        self.bot('Python: %s', sys.version)
        self.bot('Default encoding: %s', sys.getdefaultencoding())
        self.bot('Starting %s v%s for server %s:%s', self.__class__.__name__, getattr(getModule(self.__module__), '__version__', ' Unknown'), self._rconIp, self._port)

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

        self.storage = b3.storage.getStorage('database', self.config.get('b3', 'database'), self)

        if self.config.has_option('server','game_log'):
            # open log file
            game_log = self.config.get('server','game_log')
            if game_log[0:6] == 'ftp://' or game_log[0:7] == 'sftp://' or game_log[0:7] == 'http://':
                self.remoteLog = True
                self.bot('Working in Remote-Log-Mode : %s' % game_log)
                
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
            self.bot('Starting bot reading file %s', f)
            self.screen.write('Using Gamelog    : %s\n' % f)

            if os.path.isfile(f):
                self.input  = file(f, 'r')
    
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
                self.error('Error reading file %s', f)
                raise SystemExit('Error reading file %s\n' % f)

        # setup rcon
        self.output = self.OutputClass(self, (self._rconIp, self._rconPort), self._rconPassword)
        
        if self.config.has_option('server','rcon_timeout'):
            custom_socket_timeout = self.config.getfloat('server','rcon_timeout')
            self.output.socket_timeout = custom_socket_timeout
            self.bot('Setting Rcon socket timeout to %0.3f sec' % custom_socket_timeout)
        
        # testing rcon
        if self.rconTest:
            res = self.output.write('status')
            self.output.flush()
            self.screen.write('Testing RCON     : ')
            self.screen.flush()
            _badRconReplies = ['Bad rconpassword.', 'Invalid password.']
            if res in _badRconReplies:
                self.screen.write('>>> Oops: Bad RCON password\n>>> Hint: This will lead to errors and render B3 without any power to interact!\n')
                self.screen.flush()
                time.sleep(2)
            elif res == '':
                self.screen.write('>>> Oops: No response\n>>> Could be something wrong with the rcon connection to the server!\n>>> Hint 1: The server is not running or it is changing maps.\n>>> Hint 2: Check your server-ip and port.\n')
                self.screen.flush()
                time.sleep(2)
            else:
                self.screen.write('OK\n')

        self.loadEvents()
        self.screen.write('Loading Events   : %s events loaded\n' % len(self._events))
        self.clients  = b3.clients.Clients(self)
        self.loadPlugins()
        self.loadArbPlugins()

        self.game = b3.game.Game(self, self.gameName)
        
        try:
            queuesize = self.config.getint('b3', 'event_queue_size')
        except NoOptionError:
            queuesize = 15
        except Exception, err:
            self.warning(err)
            queuesize = 15
        self.debug("creating the event queue with size %s", queuesize)
        self.queue = Queue.Queue(queuesize)    # event queue

        atexit.register(self.shutdown)



    def getAbsolutePath(self, path):
        """Return an absolute path name and expand the user prefix (~)"""
        return b3.getAbsolutePath(path)

    def _dumpEventsStats(self):
        self._eventsStats.dumpStats()

    def start(self):
        """Start B3"""
        self.bot("Starting parser")
        self.startup()
        self.say('%s ^2[ONLINE]' % b3.version)
        self.bot("Starting plugins")
        self.startPlugins()
        self.bot("all plugins started")
        self.pluginsStarted()
        self.bot("starting event dispatching thread")
        thread.start_new_thread(self.handleEvents, ())
        self.bot("start reading game events")
        self.run()

    def die(self):
        """Stop B3 with the die exit status (222)"""
        self.shutdown()

        time.sleep(5)

        sys.exit(222)

    def restart(self):
        """Stop B3 with the restart exit statis (221)"""
        self.shutdown()

        time.sleep(5)

        self.bot('Restarting...')
        sys.exit(221)

    def upTime(self):
        """Amount of time B3 has been running"""
        return self.time() - self._timeStart

    def loadConfig(self, config):
        """Set the config file to load"""

        if not config:
            return False

        self.config = config

        return True

    def saveConfig(self):
        """Save configration changes"""
        self.bot('Saving config %s', self.config.fileName)
        return self.config.save()

    def startup(self):
        """\
        Called after the parser is created before run(). Overwrite this
        for anything you need to initialize you parser with.
        """
        pass

    def pluginsStarted(self):
        """\
        Called after the parser loaded and started all plugins. 
        Overwrite this in parsers to take actions once plugins are ready
        """
        pass

    def pause(self):
        """Pause B3 log parsing"""
        self.bot('PAUSING')
        self._paused = True

    def unpause(self):
        """Unpause B3 log parsing"""
        self._paused = False
        self._pauseNotice = False
        self.input.seek(0, os.SEEK_END)

    def loadEvents(self):
        """Load events from event manager"""
        self._events = self.Events.events

    def createEvent(self, key, name=None):
        """Create a new event"""
        self.Events.createEvent(key, name)
        self._events = self.Events.events
        return self._events[key]

    def getEventID(self, key):
        """Get the numeric ID of an event name"""
        return self.Events.getId(key)

    def getEvent(self, key, data, client=None, target=None):
        """Return a new Event object for an event name"""
        return b3.events.Event(self.Events.getId(key), data, client, target)

    def getEventName(self, id):
        """Get the name of an event by numeric ID"""
        return self.Events.getName(id)

    def getPlugin(self, plugin):
        """Get a reference to a loaded plugin"""
        try:
            return self._plugins[plugin]
        except KeyError:
            return None

    def reloadConfigs(self):
        """Reload all config files"""
        # reload main config
        self.config.load(self.config.fileName)

        for k in self._pluginOrder:
            p = self._plugins[k]
            self.bot('Reload plugin config for %s', k)
            p.loadConfig()
            
        self.updateDocumentation()

    def loadPlugins(self):
        """Load plugins specified in the config"""
        self.screen.write('Loading Plugins  : ')
        self.screen.flush()
        
        extplugins_dir = self.config.getpath('plugins', 'external_dir');
        self.bot('Loading Plugins (external plugin directory: %s)' % extplugins_dir)
        
        plugins = {}
        pluginSort = []

        priority = 1
        for p in self.config.get('plugins/plugin'):
            name = p.get('name')
            conf = p.get('config')
            if conf == None:
                conf = '@b3/conf/plugin_%s.xml' % name
            disabledconf = p.get('disabled')
            plugins[priority] = {'name': name, \
                                 'conf': self.getAbsolutePath(conf), \
                                 'path': p.get('path'), \
                                 'disabled': disabledconf is not None and disabledconf.lower() in ('yes', '1', 'on', 'true')}
            pluginSort.append(priority)
            priority += 1

        pluginSort.sort()

        self._pluginOrder = []
        for s in pluginSort:

            self._pluginOrder.append(plugins[s]['name'])
            self.bot('Loading Plugin #%s %s [%s]', s, plugins[s]['name'], plugins[s]['conf'])

            try:
                pluginModule = self.pluginImport(plugins[s]['name'], plugins[s]['path'])
                self._plugins[plugins[s]['name']] = getattr(pluginModule, '%sPlugin' % plugins[s]['name'].title())(self, plugins[s]['conf'])
                if plugins[s]['disabled']:
                    self.info("disabling plugin %s" % plugins[s]['name'])
                    self._plugins[plugins[s]['name']].disable()
            except Exception, msg:
                # critical will exit
                self.critical('Error loading plugin: %s', msg)
    
            version = getattr(pluginModule, '__version__', 'Unknown Version')
            author  = getattr(pluginModule, '__author__', 'Unknown Author')
            
            self.bot('Plugin %s (%s - %s) loaded', plugins[s]['name'], version, author)
            self.screen.write('.')
            self.screen.flush()

    def loadArbPlugins(self):
        """Load must have plugins and check for admin plugin"""

        if 'publist' not in self._pluginOrder:
            #self.debug('publist not found!')
            p = 'publist'
            self.bot('Loading Plugin %s', p)
            try:
                pluginModule = self.pluginImport(p)
                self._plugins[p] = getattr(pluginModule, '%sPlugin' % p.title())(self)
                self._pluginOrder.append(p)
                version = getattr(pluginModule, '__version__', 'Unknown Version')
                author  = getattr(pluginModule, '__author__', 'Unknown Author')
                self.bot('Plugin %s (%s - %s) loaded', p, version, author)
                self.screen.write('.')
                self.screen.flush()
            except Exception, msg:
                self.verbose('Error loading plugin: %s', msg)
        if self.config.has_option('server','game_log') \
            and self.config.get('server','game_log')[0:6] == 'ftp://' :
            p = 'ftpytail'
            self.bot('Loading %s', p)
            try:
                pluginModule = self.pluginImport(p)
                self._plugins[p] = getattr(pluginModule, '%sPlugin' % p.title()) (self)
                self._pluginOrder.append(p)
                version = getattr(pluginModule, '__version__', 'Unknown Version')
                author  = getattr(pluginModule, '__author__', 'Unknown Author')
                self.bot('Plugin %s (%s - %s) loaded', p, version, author)
                self.screen.write('.')
                self.screen.flush()
            except Exception, msg:
                self.critical('Error loading plugin: %s', msg)
                raise SystemExit('error while loading %s' % p)
        if self.config.has_option('server','game_log') \
            and self.config.get('server','game_log')[0:7] == 'sftp://' :
            p = 'sftpytail'
            self.bot('Loading %s', p)
            try:
                pluginModule = self.pluginImport(p)
                self._plugins[p] = getattr(pluginModule, '%sPlugin' % p.title()) (self)
                self._pluginOrder.append(p)
                version = getattr(pluginModule, '__version__', 'Unknown Version')
                author  = getattr(pluginModule, '__author__', 'Unknown Author')
                self.bot('Plugin %s (%s - %s) loaded', p, version, author)
                self.screen.write('.')
                self.screen.flush()
            except Exception, msg:
                self.critical('Error loading plugin: %s', msg)
                raise SystemExit('error while loading %s' % p)
        if self.config.has_option('server','game_log') \
            and self.config.get('server','game_log')[0:7] == 'http://' :
            p = 'httpytail'
            self.bot('Loading %s', p)
            try:
                pluginModule = self.pluginImport(p)
                self._plugins[p] = getattr(pluginModule, '%sPlugin' % p.title()) (self)
                self._pluginOrder.append(p)
                version = getattr(pluginModule, '__version__', 'Unknown Version')
                author  = getattr(pluginModule, '__author__', 'Unknown Author')
                self.bot('Plugin %s (%s - %s) loaded', p, version, author)
                self.screen.write('.')
                self.screen.flush()
            except Exception, msg:
                self.critical('Error loading plugin: %s', msg)
                raise SystemExit('error while loading %s' % p)
        if 'admin' not in self._pluginOrder:
            # critical will exit, admin plugin must be loaded!
            self.critical('AdminPlugin is essential and MUST be loaded! Cannot continue without admin plugin.')
        self.screen.write(' (%s)\n' % len(self._pluginOrder))
        self.screen.flush()

    def pluginImport(self, name, path=None):
        """Import a single plugin"""
        if path is not None:
            try:
                self.info('loading plugin from specified path : %s', path)
                fp, pathname, description = imp.find_module(name, [path])
                try:
                    return imp.load_module(name, fp, pathname, description)
                finally:
                    if fp:
                        fp.close()
            except ImportError:
                pass
        try:
            module = 'b3.plugins.%s' % name
            mod = __import__(module)
            components = module.split('.')
            for comp in components[1:]:
                mod = getattr(mod, comp)
            return mod
        except ImportError, m:
            self.info('Could not load built in plugin %s (%s)', name, m)
            self.info('trying external plugin directory : %s', self.config.getpath('plugins', 'external_dir'))
            fp, pathname, description = imp.find_module(name, [self.config.getpath('plugins', 'external_dir')])
            try:
                return imp.load_module(name, fp, pathname, description)
            finally:
                if fp:
                    fp.close()

    def startPlugins(self):
        """Start all loaded plugins"""
        self.screen.write('Starting Plugins : ')
        self.screen.flush()

        _plugins = self._pluginOrder
        def start_plugin(plugin_name):
            p = self._plugins[plugin_name]
            self.bot('Starting Plugin %s', plugin_name)
            p.onStartup()
            p.start()
            #time.sleep(1)    # give plugin time to crash, er...start
            self.screen.write('.')
            self.screen.flush()

        # handle admin plugin first as many plugins relie on it
        if 'admin' in _plugins:
            start_plugin('admin')
            _plugins.remove('admin')

        # start other plugins
        for plugin_name in _plugins:
            start_plugin(plugin_name)

        self.screen.write(' (%s)\n' % (len(_plugins)+1))

    def disablePlugins(self):
        """Disable all plugins except for publist, ftpytail and admin"""
        for k in self._pluginOrder:
            if k not in ('admin', 'publist', 'ftpytail'):
                p = self._plugins[k]
                self.bot('Disabling Plugin %s', k)
                p.disable()

    def enablePlugins(self):
        """Enable all plugins except for publist, ftpytail and admin"""
        for k in self._pluginOrder:
            if k not in ('admin', 'publist', 'ftpytail'):
                p = self._plugins[k]
                self.bot('Enabling Plugin %s', k)
                p.enable()

    def getMessage(self, msg, *args):
        """Return a message from the config file"""
        try:
            msg = self._messages[msg]
        except KeyError:
            try:
                self._messages[msg] = self.config.getTextTemplate('messages', msg)
                msg = self._messages[msg]
            except KeyError:
                msg = ''

        if len(args):
            if type(args[0]) == dict:
                return msg % args[0]
            else:
                return msg % args
        else:
            return msg

    def getMessageVariables(self, *args, **kwargs):
        """Dynamically generate a dictionnary of fields available for messages in config file"""
        variables = {}
        for obj in args:
            if obj is None:
                continue
            if type(obj).__name__ in ('str','unicode'):
                if variables.has_key(obj) is False:
                    variables[obj] = obj
            else:
                for attr in vars(obj):
                    pattern = re.compile('[\W_]+')
                    cleanattr = pattern.sub('', attr) # trim any underscore or any non alphanumeric character
                    variables[cleanattr] = getattr(obj,attr)
        for key, obj in kwargs.iteritems():
            #self.debug('Type of kwarg %s: %s' % (key, type(obj).__name__))
            if obj is None:
                continue
            if type(obj).__name__ in ('str','unicode'):
                if variables.has_key(key) is False:
                    variables[key] = obj
            #elif type(obj).__name__ == 'instance':
                #self.debug('Classname of object %s: %s' % (key, obj.__class__.__name__))
            else:
                for attr in vars(obj):
                    pattern = re.compile('[\W_]+')
                    cleanattr = pattern.sub('', attr) # trim any underscore or any non alphanumeric character
                    currkey = ''.join([key,cleanattr])
                    variables[currkey] = getattr(obj,attr)
        ''' For debug purposes, uncomment to see in the log a list of the available fields
        allkeys = variables.keys()
        allkeys.sort()
        for key in allkeys:
            self.debug('%s has value %s' % (key, variables[key]))
        '''
        return variables

    def getCommand(self, cmd, **kwargs):
        """Return a reference to a loaded command"""
        try:
            cmd = self._commands[cmd]
        except KeyError:
            return None

        return cmd % kwargs
        
    def getTzOffsetFromName(self, tzName):
        try:
            tzOffset = b3.timezones.timezones[tzName] * 3600
        except KeyError:
            try:
                self.warning("Unknown timezone name [%s]. Valid timezone codes can be found on http://wiki.bigbrotherbot.net/doku.php/usage:available_timezones" % tzName)
                tzOffset = time.timezone
                if tzOffset < 0:
                    tzName = 'UTC%s' % (tzOffset/3600)
                else:
                    tzName = 'UTC+%s' % (tzOffset/3600)
                self.info("using system offset [%s]", tzOffset)
            except KeyError:
                self.error("Unknown timezone name [%s]. Valid timezone codes can be found on http://wiki.bigbrotherbot.net/doku.php/usage:available_timezones" % tzName)
                tzName = 'UTC'
                tzOffset = 0
        return (tzOffset, tzName)

    def formatTime(self, gmttime, tzName=None):
        """Return a time string formated to local time in the b3 config time_format"""
        if tzName:
            tzName = str(tzName).strip().upper()
            try:
                tzOffset = float(tzName) * 3600
            except ValueError:
                tzOffset, tzName = self.getTzOffsetFromName(tzName)
        else:
            tzName = self.config.get('b3', 'time_zone').upper()
            tzOffset, tzName = self.getTzOffsetFromName(tzName)

        timeFormat = self.config.get('b3', 'time_format').replace('%Z', tzName).replace('%z', tzName)
        self.debug('formatting time with timezone [%s], tzOffset : %s' % (tzName, tzOffset))
        return time.strftime(timeFormat, time.gmtime(gmttime + tzOffset))

    def run(self):
        """Main worker thread for B3"""
        self.screen.write('Startup Complete : B3 is running! Let\'s get to work!\n\n')
        self.screen.write('(If you run into problems, check %s in the B3 root directory for detailed log info)\n' % self.config.getpath('b3', 'logfile'))
        #self.screen.flush()

        self.updateDocumentation()

        logTimeStart = None
        logTimeLast = 0
        while self.working:
            if self._paused:
                if self._pauseNotice == False:
                    self.bot('PAUSED - Not parsing any lines, B3 will be out of sync.')
                    self._pauseNotice = True
            else:
                lines = self.read()

                if lines:
                    for line in lines:
                        line = str(line).strip()
                        if line:
                            # Track the log file time changes. This is mostly for
                            # parsing old log files for testing and to have time increase
                            # predictably
                            m = self._lineTime.match(line)
                            if m:
                                logTimeCurrent = (int(m.group('minutes')) * 60) + int(m.group('seconds'))
                                if logTimeStart and logTimeCurrent - logTimeStart < logTimeLast:
                                    # Time in log has reset
                                    logTimeStart = logTimeCurrent
                                    logTimeLast = 0
                                    self.debug('Log time reset %d' % logTimeCurrent)
                                elif not logTimeStart:
                                    logTimeStart = logTimeCurrent

                                # Remove starting offset, we want the first line to be at 0 seconds
                                logTimeCurrent = logTimeCurrent - logTimeStart
                                self.logTime += logTimeCurrent - logTimeLast
                                logTimeLast = logTimeCurrent

                            if self.replay:                    
                                self.debug('Log time %d' % self.logTime)

                            self.console(line)

                            try:
                                self.parseLine(line)
                            except SystemExit:
                                raise
                            except Exception, msg:
                                self.error('could not parse line %s: %s', msg, traceback.extract_tb(sys.exc_info()[2]))
                            
                            time.sleep(self.delay2)

            time.sleep(self.delay)

        self.bot('Stop reading.')

        with self.exiting:
            self.input.close()
            self.output.close()

            if self.exitcode:
                sys.exit(self.exitcode)


    def parseLine(self, line):
        """Parse a single line from the log file"""
        m = re.match(self._lineFormat, line)
        if m:
            self.queueEvent(b3.events.Event(
                    b3.events.EVT_UNKNOWN,
                    m.group(2)[:1]
                ))

    def registerHandler(self, eventName, eventHandler):
        """Register an event handler"""
        self.debug('Register Event: %s: %s', self.Events.getName(eventName), eventHandler.__class__.__name__)

        if not self._handlers.has_key(eventName):
            self._handlers[eventName] = []
        self._handlers[eventName].append(eventHandler)

    def queueEvent(self, event, expire=10):
        """Queue an event for processing"""
        if not hasattr(event, 'type'):
            return False
        elif self._handlers.has_key(event.type):    # queue only if there are handlers to listen for this event
            self.verbose('Queueing event %s %s', self.Events.getName(event.type), event.data)
            try:
                time.sleep(0.001) # wait a bit so event doesnt get jumbled
                self.queue.put((self.time(), self.time() + expire, event), True, 2)
                return True
            except Queue.Full, msg:
                self.error('**** Event queue was full (%s)', self.queue.qsize())
                return False

        return False

    def handleEvents(self):
        """Event handler thread"""
        while self.working:
            added, expire, event = self.queue.get(True)
            if event.type == b3.events.EVT_EXIT or event.type == b3.events.EVT_STOP:
                self.working = False

            eventName = self.Events.getName(event.type)
            self._eventsStats.add_event_wait((self.time() - added)*1000)
            if self.time() >= expire:    # events can only sit in the queue until expire time
                self.error('**** Event sat in queue too long: %s %s', eventName, self.time() - expire)
            else:
                nomore = False
                for hfunc in self._handlers[event.type]:
                    if not hfunc.isEnabled():
                        continue
                    elif nomore:
                        break

                    self.verbose('Parsing Event: %s: %s', eventName, hfunc.__class__.__name__)
                    timer_plugin_begin = time.clock()
                    try:
                        hfunc.parseEvent(event)
                        time.sleep(0.001)
                    except b3.events.VetoEvent:
                        # plugin called for event hault, do not continue processing
                        self.bot('Event %s vetoed by %s', eventName, str(hfunc))
                        nomore = True
                    except SystemExit, e:
                        self.exitcode = e.code
                    except Exception, msg:
                        self.error('handler %s could not handle event %s: %s: %s %s', hfunc.__class__.__name__, eventName, msg.__class__.__name__, msg, traceback.extract_tb(sys.exc_info()[2]))
                    finally:
                        elapsed = time.clock() - timer_plugin_begin
                        self._eventsStats.add_event_handled(hfunc.__class__.__name__, eventName, elapsed*1000)
                    
        self.bot('Shutting down event handler')

        # releasing lock if it was set by self.shutdown() for instance
        if self.exiting.locked():
            self.exiting.release()

    def write(self, msg, maxRetries=None):
        """Write a message to Rcon/Console"""
        if self.replay:
            self.bot('Sent rcon message: %s' % msg)
        elif self.output == None:
            pass
        else:
            res = self.output.write(msg, maxRetries=maxRetries)
            self.output.flush()
            return res

    def writelines(self, msg):
        """Write a sequence of messages to Rcon/Console. Optimized for speed"""
        if self.replay:
            self.bot('Sent rcon message: %s' % msg)
        elif self.output == None:
            pass
        else:
            res = self.output.writelines(msg)
            self.output.flush()
            return res

    def read(self):
        """read from game server log file"""
        # Getting the stats of the game log (we are looking for the size)
        filestats = os.fstat(self.input.fileno())
        # Compare the current cursor position against the current file size,
        # if the cursor is at a number higher than the game log size, then
        # there's a problem
        if self.input.tell() > filestats.st_size:   
            self.debug('Parser: Game log is suddenly smaller than it was before (%s bytes, now %s), the log was probably either rotated or emptied. B3 will now re-adjust to the new size of the log.' % (str(self.input.tell()), str(filestats.st_size)) )  
            self.input.seek(0, os.SEEK_END)  
        return self.input.readlines() 

    def shutdown(self):
        """Shutdown B3"""
        try:
            if self.working and self.exiting.acquire():
                self.bot('Shutting down...')
                self.working = False
                for k,plugin in self._plugins.items():
                    plugin.parseEvent(b3.events.Event(b3.events.EVT_STOP, ''))
                if self._cron:
                    self._cron.stop()

                self.bot('Shutting down database connections...')
                self.storage.shutdown()
        except Exception, e:
            self.error(e)

    def getWrap(self, text, length=80, minWrapLen=150):
        """Returns a sequence of lines for text that fits within the limits"""
        if not text:
            return []

        length = int(length)
        text = text.replace('//', '/ /')

        if len(text) <= minWrapLen:
            return [text]
        #if len(re.sub(REG, '', text)) <= minWrapLen:
        #    return [text]

        text = re.split(r'\s+', text)

        lines = []
        color = '^7'

        line = text[0]
        for t in text[1:]:
            if len(re.sub(self._reColor, '', line)) + len(re.sub(self._reColor, '', t)) + 2 <= length:
                line = '%s %s' % (line, t)
            else:
                if len(lines) > 0:
                    lines.append('^3>%s%s' % (color, line))
                else:
                    lines.append('%s%s' % (color, line))

                m = re.findall(self._reColor, line)
                if m:
                    color = m[-1]

                line = t

        if len(line):
            if len(lines) > 0:
                lines.append('^3>%s%s' % (color, line))
            else:
                lines.append('%s%s' % (color, line))

        return lines

    def error(self, msg, *args, **kwargs):
        """Log an error"""
        self.log.error(msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        """Log a debug message"""
        self.log.debug(msg, *args, **kwargs)

    def bot(self, msg, *args, **kwargs):
        """Log a bot message"""
        self.log.bot(msg, *args, **kwargs)

    def verbose(self, msg, *args, **kwargs):
        """Log a verbose message"""
        self.log.verbose(msg, *args, **kwargs)

    def verbose2(self, msg, *args, **kwargs):
        """Log an extra verbose message"""
        self.log.verbose2(msg, *args, **kwargs)

    def console(self, msg, *args, **kwargs):
        """Log a message from the console"""
        self.log.console(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        """Log a message from the console"""
        self.log.warning(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        """Log a message from the console"""
        self.log.info(msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        """Log a message from the console"""
        self.log.exception(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        """Log a message from the console"""
        self.log.critical(msg, *args, **kwargs)

    def time(self):
        """Return the current time in GMT/UTC"""
        if self.replay:
            return self.logTime

        return int(time.time())

    def _get_cron(self):
        """Instantiate the main Cron object"""
        if not self._cron:
            self._cron = b3.cron.Cron(self)
            self._cron.start()
        return self._cron

    cron = property(_get_cron)


    def stripColors(self, text):
        return re.sub(self._reColor, '', text).strip()

    def updateDocumentation(self):
        """Create a documentation for all available commands"""
        try: 
            from b3.tools.documentationBuilder import DocBuilder
            docbuilder = DocBuilder(self)
            docbuilder.save()
        except Exception, err:
            self.error("Failed to generate user documentation")
            self.exception(err)


    ###############################################################################
    ##                                                                           ##
    ##     Inheriting classes must implements the following methods.             ##
    ##     Plugins that are game independant assume those methods exist          ##
    ##                                                                           ##
    ###############################################################################

    def getPlayerList(self):
        """\
        Query the game server for connected players.
        return a dict having players' id for keys and players' data as another dict for values
        """
        raise NotImplementedError

    def authorizeClients(self):
        """\
        For all connected players, fill the client object with properties allowing to find 
        the user in the database (usualy guid, or punkbuster id, ip) and call the 
        Client.auth() method 
        """
        raise NotImplementedError
    
    def sync(self):
        """\
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
        """\
        broadcast a message to all players
        """
        raise NotImplementedError

    def saybig(self, msg):
        """\
        broadcast a message to all players in a way that will catch their attention.
        """
        raise NotImplementedError

    def message(self, client, text):
        """\
        display a message to a given player
        """
        raise NotImplementedError

    def kick(self, client, reason='', admin=None, silent=False, *kwargs):
        """\
        kick a given player
        """
        raise NotImplementedError

    def ban(self, client, reason='', admin=None, silent=False, *kwargs):
        """\
        ban a given player on the game server and in case of success
        fire the event ('EVT_CLIENT_BAN', data={'reason': reason, 
        'admin': admin}, client=target)
        """
        raise NotImplementedError

    def unban(self, client, reason='', admin=None, silent=False, *kwargs):
        """\
        unban a given player on the game server
        """
        raise NotImplementedError

    def tempban(self, client, reason='', duration=2, admin=None, silent=False, *kwargs):
        """\
        tempban a given player on the game server and in case of success
        fire the event ('EVT_CLIENT_BAN_TEMP', data={'reason': reason, 
        'duration': duration, 'admin': admin}, client=target)
        """
        raise NotImplementedError

    def getMap(self):
        """\
        return the current map/level name
        """
        raise NotImplementedError

    def getMaps(self):
        """\
        return the available maps/levels name
        """
        raise NotImplementedError

    def rotateMap(self):
        """\
        load the next map/level
        """
        raise NotImplementedError
        
    def changeMap(self, map):
        """\
        load a given map/level
        return a list of suggested map names in cases it fails to recognize the map that was provided
        """
        raise NotImplementedError

    def getPlayerPings(self):
        """\
        returns a dict having players' id for keys and players' ping for values
        """
        raise NotImplementedError

    def getPlayerScores(self):
        """\
        returns a dict having players' id for keys and players' scores for values
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
