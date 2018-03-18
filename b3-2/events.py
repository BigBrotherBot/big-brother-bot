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


import aenum
import configparser
import queue
import threading
import time
import traceback
import typing

from .clients import Client
from .output import LoggerMixin
from .plugin import Plugin


@aenum.unique
class EventType(aenum.Enum):
    """B3 parser indipendent event type definitions"""
    EXIT = 'Program exit'
    CLIENT_AUTH = 'Client authentication'
    CLIENT_BAN = 'Client ban'
    CLIENT_CONNECT = 'Client connect'
    CLIENT_DISCONNECT = 'Client disconnect'
    CLIENT_DAMAGE = 'Client damage'
    CLIENT_DAMAGE_TEAM = 'Client team damage'
    CLIENT_DAMAGE_SELF = 'Client self damage'
    CLIENT_KICK = 'Client kick'
    CLIENT_KILL = 'Client kill'
    CLIENT_KILL_TEAM = 'Client team kill'
    CLIENT_KILL_SELF = 'Client suicide'
    CLIENT_NAME_CHANGE = 'Client name change'
    CLIENT_NOTICE = 'Client notice'
    CLIENT_SAY = 'Client say'
    CLIENT_SAY_TEAM = 'Client say team'
    CLIENT_SAY_PRIVATE = 'Client private message'
    CLIENT_TEAM_CHANGE = 'Client team change'
    CLIENT_TEAM_JOIN = 'Client team join'
    CLIENT_WARNING = 'Client warning'
    GAME_EXIT = 'Game exit'
    GAME_MAP_CHANGE = 'Game map change'
    GAME_ROUND_START = 'Game round start'
    GAME_ROUND_END = 'Game round end'
    GAME_WARMUP = 'Game warmup'
    PLUGIN_DISABLED = 'Plugin disabled'
    PLUGIN_ENABLED = 'Plugin enabled'

    @classmethod
    def extend(cls, name:str, description:str):
        """Dynamically create a new event type"""
        aenum.extend_enum(cls, name, description)


class Event(object):
    """B3 event representation"""

    def __init__(self, type:EventType, data:dict, client:Client=None, target:Client=None):
        super(Event, self).__init__()
        self.type = type
        self.data = data
        self.client = client
        self.target = target
        self.expire = 0
        self.time = 0

    def __str__(self):
        return 'Event<%s>(%r, %s, %s)' % (self.type.value, self.data, self.client, self.target)


class EventManager(LoggerMixin, object):
    """B3 event manager implementation"""

    def __init__(self, config:configparser.ConfigParser):
        super(EventManager, self).__init__()
        self._running = True
        self._event_queue_size = config.getint('b3', 'event_queue_size', fallback=50)
        self._event_queue_expire_time = config.getint('b3', 'event_queue_expire_time', fallback=10)
        self._handlers:typing.Dict[EventType, typing.List[Plugin]] = {}
        self._lock = threading.RLock()
        self.debug("Creating the event queue with size %s", self._event_queue_size)
        self.queue = queue.Queue(self._event_queue_size)

    # #########################################################################
    # EVENT MANAGEMENT
    # #########################################################################

    def post(self, event:Event, expire:int=None) -> bool:
        """Enqueue the given event for later processing"""
        if event.type in self._handlers:
            if expire is None:
                expire = self._event_queue_expire_time
            event.time = time.time()
            event.expire = event.time + expire
            try:
                time.sleep(0.001)  # wait a bit so event doesnt get jumbled
                self.verbose('Queuing event %s', event)
                self.queue.put(event, True, 2)
                return True
            except queue.Full:
                self.error('Event queue is full (%d)', self.queue.qsize())
                return False
        return False

    def subscribe(self, handler:Plugin, event:EventType):
        """Register an handler for the given event type"""
        self.debug('%s: register event <%s>', handler.__class__.__name__, event.value)
        if event not in self._handlers:
            self._handlers[event] = []
        if handler not in self._handlers[event]:
            self._handlers[event].append(handler)

    def unsubscribe(self, handler:Plugin, event:EventType=None):
        """Unregister an event handler"""
        for e in self._handlers:
            if event is None or e is event:
                if handler in self._handlers[e]:
                    self.debug('%s: unregister event <%s>', handler.__class__.__name__, e.value)
                    self._handlers[e].remove(handler)

    # #########################################################################
    # MAIN
    # #########################################################################

    def running(self) -> bool:
        """Returns True if the event manager is running, False otherwise"""
        with self._lock:
            return self._running

    def shutdown(self):
        """Shutdown the event manager preving further event processing"""
        with self._lock:
            self._running = False

    def start(self):
        """Main event loop"""
        self.debug('Event manager started processing events')
        while self.running():
            event = self.queue.get(True)
            if event.type == EventType.EXIT:
                self.shutdown()
            if time.time() >= event.expire: # Events can only sit in the queue until expire time.
                self.error('Event <%s> sat in queue too long: %s %fms', event.value, (time.time() - event.expire) * 1000)
            else:
                # We need to check again for the event manager to be alive because
                # queue.get blocks until an event is available for processing and another
                # thread may have forced the event manager to shutdown.
                if self.running():
                    nomore = False
                    for handler in self._handlers[event.type]:
                        if not handler.isEnabled():
                            continue
                        if nomore:
                            break
                        self.verbose('%s: processing event <%s>', handler.__class__.__name__, event.value)
                        start = time.process_time()
                        try:
                            handler.onEvent(event)
                        except VetoEvent:
                            self.verbose('Event <%s> vetoed by %s', event.value, handler.__class__.__name__)
                            nomore = True
                        except Exception as e:
                            self.error('%s: could not process event <%s> : %s',
                                       handler.__class__.__name__, event.value,
                                       ''.join(traceback.format_exception(type(e), e, e.__traceback__)))
                        else:
                            elapsed = (time.process_time() - start) * 1000
                            self.verbose('Event <%s> processed by %s in %fms',
                                         event.value, handler.__class__.__name__, elapsed)
        self.debug('Event manager stopped processing events')


class VetoEvent(Exception):
    """Raised to cancel event processing"""
    pass