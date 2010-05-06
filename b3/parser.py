#
# BigBrotherBot(B3) (www.bigbrotherbot.com)
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
#
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
__version__ = '1.15.1'

# system modules
import os, sys, re, time, thread, traceback, Queue, imp, atexit, socket

import b3
import b3.storage
import b3.events
import b3.output

import b3.game
import b3.cron
import b3.parsers.q3a_rcon
import b3.clients
import b3.functions
from b3.functions import main_is_frozen, getModule


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

    clients  = None
    delay = 0.001
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

    # Time in seconds of epoch of game log
    logTime = 0

    OutputClass = b3.parsers.q3a_rcon.Rcon

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
            print 'COULD NOT LOAD CONFIG'
            raise SystemExit(220)

        # set up logging
        logfile = self.config.getpath('b3', 'logfile')
        log2console = self.config.has_option('devmode', 'log2console') and self.config.getboolean('devmode', 'log2console')
        self.log = b3.output.getInstance(logfile, self.config.getint('b3', 'log_level'), log2console)

        # save screen output to self.screen
        self.screen = sys.stdout
        print 'Activating log   : %s' % logfile
        sys.stdout = b3.output.stdoutLogger(self.log)
        sys.stderr = b3.output.stderrLogger(self.log)

        # setup ip addresses
        self._publicIp = self.config.get('server', 'public_ip')
        self._port = self.config.getint('server', 'port')
        self._rconPort = self._port # if rcon port is the same as the game port, rcon_port can be ommited
        self._rconIp = self.config.get('server', 'rcon_ip')
        if self.config.has_option('server', 'rcon_port'):
            self._rconPort = self.config.getint('server', 'rcon_port')
        self._rconPassword = self.config.get('server', 'rcon_password')


        if self._publicIp[0:1] == '~' or self._publicIp[0:1] == '/':
            # load ip from a file
            f = file(self.getAbsolutePath(self._publicIp))
            self._publicIp = f.read().strip()
            f.close()

        try:
            # resolve domain names
            self._publicIp = socket.gethostbyname(self._publicIp)
        except:
            pass

        if self._rconIp[0:1] == '~' or self._rconIp[0:1] == '/':
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
        self.bot('Starting %s v%s for server %s:%s', self.__class__.__name__, getattr(getModule(self.__module__), '__version__', ' Unknown'), self._rconIp, self._port)

        # get events
        self.Events = b3.events.eventManager

        self.bot('--------------------------------------------')

        # setup bot
        bot_name = self.config.get('b3', 'bot_name')
        if bot_name:
            self.name = bot_name

        bot_prefix = self.config.get('b3', 'bot_prefix')
        if bot_prefix:
            self.prefix = bot_prefix

        self.msgPrefix = self.prefix

        # delay between log reads
        if self.config.has_option('b3', 'delay'):
            delay = self.config.getfloat('b3', 'delay')
            self.delay = delay

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
            if game_log[0:6] == 'ftp://' :
                self.remoteLog = True
                self.bot('Working in Remote-Log-Mode : %s' % game_log)
                f = os.path.normpath(os.path.expanduser('games_mp.log'))
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
#        res = self.output.write('status')
#        self.output.flush()
#        self.screen.write('Testing RCON     : ')
#        self.screen.flush()
#        if res == 'Bad rconpassword.':
#            self.screen.write('>>> Oops: Bad RCON password\n>>> Hint: This will lead to errors and render B3 without any power to interact!\n')
#            self.screen.flush()
#            time.sleep(2)
#        elif res == '':
#            self.screen.write('>>> Oops: No response\n>>> Could be something wrong with the rcon connection to the server!\n>>> Hint 1: The server is not running or it is changing maps.\n>>> Hint 2: Check your server-ip and port.\n')
#            self.screen.flush()
#            time.sleep(2)
#        else:
#            self.screen.write('OK\n')

        self.loadEvents()
        self.screen.write('Loading Events   : %s events loaded\n' % len(self._events))
        self.clients  = b3.clients.Clients(self)
        self.loadPlugins()
        self.loadArbPlugins()

        self.game = b3.game.Game(self, self.gameName)
        self.queue = Queue.Queue(15)    # event queue

        atexit.register(self.shutdown)

        self.say('%s ^2[ONLINE]' % b3.version)

    def getAbsolutePath(self, path):
        """Return an absolute path name and expand the user prefix (~)"""
        return b3.getAbsolutePath(path)

    def start(self):
        """Start B3"""

        self.onStartup()
        self.startPlugins()
        thread.start_new_thread(self.handleEvents, ())

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
            plugin = p.get('name')
            conf = p.get('config')

            if conf == None:
                conf = '@b3/conf/plugin_%s.xml' % plugin

            plugins[priority] = (plugin, self.getAbsolutePath(conf))
            pluginSort.append(priority)
            priority += 1

        pluginSort.sort()

        self._pluginOrder = []
        for s in pluginSort:

            p, conf = plugins[s]
            self._pluginOrder.append(p)
            self.bot('Loading Plugin #%s %s [%s]', s, p, conf)

            try:
                pluginModule = self.pluginImport(p)
                self._plugins[p] = getattr(pluginModule, '%sPlugin' % p.title())(self, conf)
            except Exception, msg:
                # critical will exit
                self.critical('Error loading plugin: %s', msg)
    
            version = getattr(pluginModule, '__version__', 'Unknown Version')
            author  = getattr(pluginModule, '__author__', 'Unknown Author')
            
            self.bot('Plugin %s (%s - %s) loaded', p, version, author)
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
            #self.debug('ftpytail not found!')
            p = 'ftpytail'
            self.bot('Loading Plugin %s', p)
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
                self.verbose('Error loading plugin: %s', msg)
        if 'admin' not in self._pluginOrder:
            # critical will exit, admin plugin must be loaded!
            self.critical('AdminPlugin is essential and MUST be loaded! Cannot continue without admin plugin.')
        self.screen.write(' (%s)\n' % len(self._pluginOrder))
        self.screen.flush()

    def pluginImport(self, name):
        """Import a single plugin"""
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
        for k in self._pluginOrder:
            p = self._plugins[k]
            self.bot('Starting Plugin %s', k)
            p.onStartup()
            p.start()
            #time.sleep(1)    # give plugin time to crash, er...start
            self.screen.write('.')
            self.screen.flush()
        self.screen.write(' (%s)\n' % len(self._pluginOrder))

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

    def getCommand(self, cmd, **kwargs):
        """Return a reference to a loaded command"""
        try:
            cmd = self._commands[cmd]
        except KeyError:
            return None

        return cmd % kwargs
        
    def formatTime(self, gmttime, tzName=None):
        """Return a time string formated to local time in the b3 config time_format"""

        if tzName:
            tzName = str(tzName).strip().upper()

            try:
                tzOffest = float(tzName)
            except ValueError:
                try:
                    tzOffest = b3.timezones.timezones[tzName]
                except KeyError:
                    pass
        else:
            tzName = self.config.get('b3', 'time_zone').upper()
            tzOffest = b3.timezones.timezones[tzName]

        tzOffest   = tzOffest * 3600
        timeFormat = self.config.get('b3', 'time_format').replace('%Z', tzName).replace('%z', tzName)

        return time.strftime(timeFormat, time.gmtime(gmttime + tzOffest))

    def run(self):
        """Main worker thread for B3"""
        self.bot('Start reading...')
        self.screen.write('Startup Complete : Let\'s get to work!\n\n')
        self.screen.write('(Please check %s in the B3 root directory for more detailed info)\n' % self.config.getpath('b3', 'logfile'))
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
                line = str(self.read()).strip()

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

            time.sleep(self.delay)

        self.bot('Stop reading.')

        if self.exiting.acquire(1):
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

            if self.time() >= expire:    # events can only sit in the queue until expire time
                self.error('**** Event sat in queue too long: %s %s', self.Events.getName(event.type), self.time() - expire)
            else:
                nomore = False
                for hfunc in self._handlers[event.type]:
                    if not hfunc.isEnabled():
                        continue
                    elif nomore:
                        break

                    self.verbose('Parsing Event: %s: %s', self.Events.getName(event.type), hfunc.__class__.__name__)
                    try:
                        hfunc.parseEvent(event)
                        time.sleep(0.001)
                    except b3.events.VetoEvent:
                        # plugin called for event hault, do not continue processing
                        self.bot('Event %s vetoed by %s', self.Events.getName(event.type), str(hfunc))
                        nomore = True
                    except SystemExit, e:
                        self.exitcode = e.code
                    except Exception, msg:
                        self.error('handler %s could not handle event %s: %s: %s %s', hfunc.__class__.__name__, self.Events.getName(event.type), msg.__class__.__name__, msg, traceback.extract_tb(sys.exc_info()[2]))

        self.bot('Shutting down event handler')

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
        """Read date from Rcon/Console"""
        return self.input.readline()

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
        color = '^7';

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
        kick a given players
        """
        raise NotImplementedError

    def ban(self, client, reason='', admin=None, silent=False, *kwargs):
        """\
        ban a given players
        """
        raise NotImplementedError

    def unban(self, client, reason='', admin=None, silent=False, *kwargs):
        """\
        unban a given players
        """
        raise NotImplementedError

    def tempban(self, client, reason='', duration=2, admin=None, silent=False, *kwargs):
        """\
        tempban a given players
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
        
    def inflictCustomPenalty(self, type, **kwargs):
        """
        Called if b3.admin.penalizeClient() does not know a given penalty type. 
        Overwrite this to add customized penalties for your game like 'slap', 'nuke', 
        'mute' or anything you want.
        /!\ This method must return True if the penalty was inflicted.
        """
        pass


if __name__ == '__main__':
    import config
    
    parser = Parser(config.load('conf/b3.xml'))
    print parser
    print parser.start()
