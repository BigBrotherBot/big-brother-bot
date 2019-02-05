# -*- coding: utf-8 -*-

# ################################################################### #
#                                                                     #
#  BigBrotherBot (B3) (www.bigbrotherbot.net)                         #
#  Copyright (C) 2018 Daniele Pantaleone <danielepantaleone@me.com>   #
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


import abc
import b3
import configparser
import re
import threading
import typing

from .clients import Client, ClientManager
from .events import EventManager, EventRouter
from .functions import rchop
from .files import FileManager
from .output import LoggerMixin
from .plugin import PluginManager


router = EventRouter()


class Parser(LoggerMixin, object):
    """B3 base parser implementation"""

    __metaclass__ = abc.ABCMeta

    _reColor = re.compile(r'\^[0-9a-z]')

    def __init__(self, config:configparser.ConfigParser):
        """Initialize the parser"""
        super(Parser, self).__init__()
        self._lock = threading.Lock()
        self._running = False
        self.config = config
        self.clients = ClientManager()
        self.events = EventManager(config)
        self.plugins = PluginManager(self, config)
        self.fs = FileManager()
        self.botname = config.get('b3', 'bot_name', fallback='b3')
        self.botprefix = config.get('b3', 'bot_prefix', fallback='(b3):')

    # -----------------------------------------------------
    # PROPERTIES
    # -----------------------------------------------------

    @property
    def name(self):
        """Returns the parser name"""
        return rchop(self.__class__.__name__.lower(), 'parser')

    # -----------------------------------------------------
    # LIFECYCLE MANAGEMENT
    # -----------------------------------------------------

    def running(self) -> bool:
        """Returns True if the parser is running, False otherwise"""
        with self._lock:
            return self._running

    def shutdown(self):
        """Shutdown the B3 parser and the events manager"""
        if self.running():
            self.debug('Shutting down %s parser')
            self.events.shutdown()
            with self._lock:
                self._running = False

    def start(self):
        """Start the B3 parser together with the events manager and all the plugins"""
        self.info("Starting %s parser", self.name)
        self.startup()
        self.plugins.init_plugins()
        self.plugins.start_plugins()
        self.debug('All plugins started')
        self.plugins_started()
        self.events.start()
        self.say("%s v%s [%s] [ONLINE]", b3.__name__, b3.__version__, b3.__codename__)
        self.run()

    # -----------------------------------------------------
    # MISC (PARSERS MAY OVERRIDE THE FOLLOWING METHODS)
    # -----------------------------------------------------

    def parse(self, data:str):
        """Parse the given data and execute the appropriate handler"""
        if data:
            func, params = router.handler(data)
            if func:
                func(self, **params)

    def sanitize(self, data:str) -> str:
        """Remove color codes from the given message"""
        return re.sub(self._reColor, '', data).strip()

    # -----------------------------------------------------
    # LIFECYCLE
    # -----------------------------------------------------

    def startup(self):
        """Perform operations on parser startup (before plugins are started)"""
        pass

    def plugins_started(self):
        """Executed when all plugins have been started"""
        pass

    def run(self):
        """Main worker from where to parse the game log file and post events on the event manager"""
        pass

    # -----------------------------------------------------
    # INTERFACE (ALL PARSERS MUST IMPLEMENT THE FOLLOWING)
    # -----------------------------------------------------

    @abc.abstractmethod
    def ban(self, client:Client, reason:str='', duration:int=60, admin:Client=None, silent=False, *kwargs):
        """Ban a client from the server"""
        pass

    @abc.abstractmethod
    def cyclemap(self):
        """Load the next map on the server"""
        pass

    @abc.abstractmethod
    def getMap(self) -> str:
        """Returns the name of the map being played"""
        pass

    @abc.abstractmethod
    def getMaps(self) -> typing.List[str]:
        """Returns the list of available maps"""
        pass

    @abc.abstractmethod
    def getNextMap(self) -> str:
        """Returns the name of the nextmap"""
        pass

    @abc.abstractmethod
    def getPlayerPings(self) -> typing.Dict[int, int]:
        """Returns a dict having players' cid(s) for keys and players' ping for values."""
        pass

    @abc.abstractmethod
    def getPlayerScores(self) -> typing.Dict[int, int]:
        """Returns a dict having players' cid(s) for keys and players' score for values"""
        pass

    @abc.abstractmethod
    def kick(self, client:Client, reason:str='', admin:Client=None, silent=False, *kwargs):
        """Kick a client off the server"""
        pass

    @abc.abstractmethod
    def map(self, mapname:str):
        """Load the given map on the server"""
        pass

    @abc.abstractmethod
    def message(self, client:Client, msg:str, *args):
        """Display a message to a given client"""
        pass

    @abc.abstractmethod
    def say(self, msg:str, *args):
        """Broadcast a message to all players"""
        pass

    @abc.abstractmethod
    def saybig(self, msg:str, *args):
        """Broadcast a message to all clients in a way that will catch their attention"""
        pass

    @abc.abstractmethod
    def sync(self):
        """Synchronize game server information"""
        pass

    @abc.abstractmethod
    def unban(self, client:Client, admin=None, silent=False, *kwargs):
        """Unban a client from the server"""
        pass

    @abc.abstractmethod
    def write(self, msg:str, retries:int=2, timeout:int=2):
        """Writes a message to the game server console"""
        pass
