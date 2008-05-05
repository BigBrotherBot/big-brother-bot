#
# BigBrotherBot(B3) (www.bigbrotherbot.com)
# Copyright (C) 2005 Michael "ThorN" Thornton
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
# $Id: parser.py 102 2006-04-14 06:46:03Z thorn $
#
# CHANGELOG
#	11/29/2005 - 1.7.0 - ThorN
#	Added atexit handlers
#	Added warning, info, exception, and critical log handlers

__author__  = 'ThorN'
__version__ = '1.8.2'

# system modules
import os, sys, re, time, thread, traceback, Queue, imp, atexit

import b3
import b3.storage
import b3.events
import b3.output

import b3.game
import b3.cron
import b3.parsers.q3a_rcon
import b3.clients
import b3.functions

class Parser(object):
	_lineFormat = re.compile('^([a-z ]+): (.*?)', re.IGNORECASE)

	_handlers = {}
	_plugins  = {}
	_pluginOrder = []
	_paused = False
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

	OutputClass = b3.parsers.q3a_rcon.Rcon

	_settings = {}
	_settings['line_length'] = 65
	_settings['min_wrap_length'] = 100

	_reColor = re.compile(r'\^[0-9a-z]')
	_cron = None

	name = 'b3'
	prefix = '^2%s:^3'
	msgPrefix = ''

	_publicIp = ''
	_rconIp = ''
	_port = 0

	info = None

	def __init__(self, config):
		self._timeStart = self.time()

		if not self.loadConfig(config):
			print 'COULD NOT LOAD CONFIG'
			raise SystemExit(220)

		# set up logging
		logfile = self.config.getpath('b3', 'logfile')
		self.log = b3.output.getInstance(logfile, self.config.getint('b3', 'log_level'))

		print 'Redirect all output to %s' % logfile
		sys.stdout = b3.output.stdoutLogger(self.log)
		sys.stderr = b3.output.stderrLogger(self.log)

		# setup ip addresses
		self._publicIp = self.config.get('server', 'public_ip')
		self._rconIp   = self.config.get('server', 'rcon_ip')
		self._port	 = self.config.getint('server', 'port')

		if self._publicIp[0:1] == '~' or self._publicIp[0:1] == '/':
			# load ip from a file
			f = file(self.getAbsolutePath(self._publicIp))
			self._publicIp = f.read().strip()
			f.close()
	
		if self._rconIp[0:1] == '~' or self._rconIp[0:1] == '/':
			# load ip from a file
			f = file(self.getAbsolutePath(self._rconIp))
			self._rconIp = f.read().strip()
			f.close()

		self.bot('Starting %s server for %s:%s', self.__class__.__name__, self._rconIp, self._port)

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
		if self.config.has_option('server', 'delay'):
			delay = self.config.getfloat('server', 'delay')
			self.delay = delay

		self.storage = b3.storage.getStorage('database', self.config.get('b3', 'database'), self)

		# open log file
		self.bot('Game log %s', self.config.getpath('server', 'game_log'))
		f = self.config.getpath('server', 'game_log')
		self.bot('Starting bot reading file %s', f)

		if os.path.isfile(f):
			self.output = None
			self.input  = file(f, 'r')

			# seek to point in log file?
			if self.config.has_option('server', 'seek'):
				seek = self.config.getboolean('server', 'seek')
				if seek:
					self.input.seek(0, 2)
			else:
				self.input.seek(0, 2)
		else:
			self.error('Error reading file %s', f)
			raise SystemExit('Error reading file %s\n' % f)

		# setup rcon
		self.output = self.OutputClass(self, (self._rconIp, self._port), self.config.get('server', 'rcon_password'))

		self.loadEvents()
		self.clients  = b3.clients.Clients(self)
		self.loadPlugins()
		self.game = b3.game.Game(self.gameName)
		self.queue = Queue.Queue(15)	# event queue

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
		return self.Events.getName(key)

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

	def loadPlugins(self):
		"""Load plugins specified in the config"""
		plugins = {}
		pluginSort = []

		for p in self.config.get('plugins/plugin'):
			priority = int(p.get('priority'))
			plugin = p.get('name')
			conf = p.get('config')

			if conf == None:
				conf = '@b3/conf/plugin_%s.xml' % name

			plugins[priority] = (plugin, self.getAbsolutePath(conf))
			pluginSort.append(priority)

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
			self.info('Could not find built in plugin %s, trying external plugin directories.\n%s', name, m)
			fp, pathname, description = imp.find_module(name, [self.config.getpath('plugins', 'external_dir')])

			try:
				return imp.load_module(name, fp, pathname, description)
			finally:
				if fp:
					fp.close()

	def startPlugins(self):
		"""Start all loaded plugins"""
		for k in self._pluginOrder:
			p = self._plugins[k]
			self.bot('Starting Plugin %s', k)
			p.onStartup()
			p.start()
			#time.sleep(1)	# give plugin time to crash, er...start

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

		while self.working:
			if self._paused:
				self.bot('PAUSED')
			else:
				line = str(self.read()).strip()

				if line:
					self.console(line)

					try:
						self.parseLine(line)
					except SystemExit:
						raise
					except Exception, msg:
						self.error('could not parse line %s: %s', msg, traceback.extract_tb(sys.exc_info()[2]))

			time.sleep(self.delay)

		self.bot('Stop reading.')
		self.input.close()
		self.output.close()

	def parseLine(self, line):
		"""Parse a single line from the log file"""
		m = re.match(self._lineFormat, line)
		if m:
			self.queueEvent(b3.events.Event(
					b3.events.EVT_UNKOWN,
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
		elif self._handlers.has_key(event.type):	# queue only if there are handlers to listen for this event
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

			if self.time() >= expire:	# events can only sit in the queue until expire time
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
					except SystemExit:
						raise
					except Exception, msg:
						self.error('handler %s could not handle event %s: %s: %s %s', hfunc.__class__.__name__, self.Events.getName(event.type), msg.__class__.__name__, msg, traceback.extract_tb(sys.exc_info()[2]))

		self.bot('Shutting down event handler')

	def write(self, msg):
		"""Write a message to Rcon/Console"""
		if self.output == None:
			pass
		else:
			res = self.output.write(msg)
			self.output.flush()
			return res

	def writelines(self, msg):
		"""Write a sequence of messages to Rcon/Console. Optimized for speed"""
		if self.output == None:
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
		if self.working:
			self.bot('Shutting down...')
			self.working = False
			for k,plugin in self._plugins.items():
				plugin.parseEvent(b3.events.Event(b3.events.EVT_STOP, ''))
			if self._cron:
				self._cron.stop()

			self.bot('Shutting down database connections...')
			self.storage.shutdown()

	def getWrap(self, text, length=80, minWrapLen=150):
		"""Returns a sequence of lines for text that fits within the limits"""
		if not text:
			return []

		length = int(length)
		text = text.replace('//', '/ /')

		if len(text) <= minWrapLen:
			return [text]
		#if len(re.sub(REG, '', text)) <= minWrapLen:
		#	return [text]

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
		return int(time.time())

	def _get_cron(self):
		"""Instantiate the main Cron object"""
		if not self._cron:
			self._cron = b3.cron.Cron(self)
			self._cron.start()
		return self._cron

	cron = property(_get_cron)


if __name__ == '__main__':
	import config
	
	parser = Parser(config.load('conf/b3.xml'))
	print parser
	print parser.start()
