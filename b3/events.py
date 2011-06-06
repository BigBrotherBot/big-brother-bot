#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
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
# 27/6/2009 : xlr8or: added CLIENT_ACTION event
# 11/11/2009 - 1.1.2 - Courgette
#    * minor transparent changes to the code 
# 30/03/2011 - 1.1.3 - SGT
#    * add EVT_CLIENT_UNBAN
# 06/06/2011 - 1.1.4 - Courgette
#    * add EventsStats class
#

__author__  = 'ThorN/xlr8or'
__version__ = '1.1.4'

import re
from collections import deque
import b3
from b3.functions import meanstdv

class Events:
    def __init__(self):
        self._eventNames = {}
        self._events = {}
        self.loadEvents((
            ('EVT_EXIT', 'Program Exit'),
            ('EVT_STOP', 'Stop Process'),
            ('EVT_UNKNOWN', 'Unknown Event'),
            ('EVT_CUSTOM', 'Custom Event'),
            ('EVT_CLIENT_SAY', 'Say'),
            ('EVT_CLIENT_TEAM_SAY', 'Team Say'),
            ('EVT_CLIENT_PRIVATE_SAY', 'Private Message'),
            ('EVT_CLIENT_CONNECT', 'Client Connect'),
            ('EVT_CLIENT_AUTH', 'Client Authenticated'),
            ('EVT_CLIENT_DISCONNECT', 'Client Disconnect'),
            ('EVT_CLIENT_UPDATE', 'Client Update'),
            ('EVT_CLIENT_KILL', 'Client Kill'),
            ('EVT_CLIENT_GIB', 'Client Gib'),
            ('EVT_CLIENT_GIB_TEAM', 'Client Gib Team'),
            ('EVT_CLIENT_GIB_SELF', 'Client Gib Self'),
            ('EVT_CLIENT_SUICIDE', 'Client Suicide'),
            ('EVT_CLIENT_KILL_TEAM', 'Client Team Kill'),
            ('EVT_CLIENT_DAMAGE', 'Client Damage'),
            ('EVT_CLIENT_DAMAGE_SELF', 'Client Damage Self'),
            ('EVT_CLIENT_DAMAGE_TEAM', 'Client Team Damage'),
            ('EVT_CLIENT_JOIN', 'Client Join Team'),
            ('EVT_CLIENT_NAME_CHANGE', 'Client Name Change'),
            ('EVT_CLIENT_TEAM_CHANGE', 'Client Team Change'),
            ('EVT_CLIENT_ITEM_PICKUP', 'Client Item Pickup'),
            ('EVT_CLIENT_ACTION', 'Client Action'),
            ('EVT_CLIENT_KICK', 'Client Kicked'),
            ('EVT_CLIENT_BAN', 'Client Banned'),
            ('EVT_CLIENT_BAN_TEMP', 'Client Temp Banned'),
            ('EVT_CLIENT_UNBAN', 'Client Unbanned'),
            ('EVT_GAME_ROUND_START', 'Game Round Start'),
            ('EVT_GAME_ROUND_END', 'Game Round End'),
            ('EVT_GAME_WARMUP', 'Game Warmup'),
            ('EVT_GAME_EXIT', 'Game Exit')
        ))        

    def createEvent(self, key, name=None):
        g = globals()

        try:
            id = self._events[key] = g[key]
        except:
            id = self._events[key] = len(self._events) + 1

        if name:        
            self._eventNames[id] = name
        else:
            self._eventNames[id] = 'Unnamed (%s)' % key

        g[key] = id

        return id

    def getName(self, key):
        try:
            return self._eventNames[self.getId(key)]
        except:
            return 'Unknown (%s)' % key

    def getId(self, key):
        if re.match('^[0-9]+$', str(key)):
            return int(key)
        else:
            try:
                return self._events[key]
            except:
                return None

    def loadEvents(self, events):
        for k,n in events:
            self.createEvent(k, n)

    def _get_events(self):
        return self._events

    events = property(_get_events)

class Event:
    def __init__(self, type, data, client=None, target=None):
        self.time = b3.console.time()
        self.type = type
        self.data = data
        self.client = client
        self.target = target
    def __str__(self):
        return "Event<%s>(%r, %s, %s)" % (eventManager.getName(self.type), self.data, self.client, self.target)


class EventsStats(object):
    def __init__(self, console, max_samples=100):
        self.console = console
        self._max_samples = max_samples
        self._handling_timers = {}
        self._queue_wait = deque(maxlen=max_samples)
        
    def add_event_handled(self, plugin_name, event_name, milliseconds_elapsed):
        if not self._handling_timers.has_key(plugin_name):
            self._handling_timers[plugin_name] = {}
        if not self._handling_timers[plugin_name].has_key(event_name):
            self._handling_timers[plugin_name][event_name] = deque(maxlen=self._max_samples)
        self._handling_timers[plugin_name][event_name].append(milliseconds_elapsed)
        self.console.verbose2("%s event handled by %s in %0.3f ms", event_name, plugin_name, milliseconds_elapsed)

    def add_event_wait(self,milliseconds_wait):
        self._queue_wait.append(milliseconds_wait)
        
    def dumpStats(self):
        for plugin_name, plugin_timers in self._handling_timers.iteritems():
            for event_name, event_timers in plugin_timers.iteritems():
                mean, stdv = meanstdv(event_timers)
                self.console.verbose("%s %s : (ms) min(%0.1f), max(%0.1f), mean(%0.1f), stddev(%0.1f)", 
                          plugin_name, event_name,  min(event_timers), 
                          max(event_timers), mean, stdv)
        mean, stdv = meanstdv(self._queue_wait)
        self.console.verbose("wait in queue stats : (ms) min(%0.1f), max(%0.1f), mean(%0.1f), stddev(%0.1f)",
                             min(self._queue_wait), max(self._queue_wait), mean, stdv)
    
#-----------------------------------------------------------------------------------------------------------------------
# raise to cancel event processing
class VetoEvent(Exception):
    pass

eventManager = Events()
