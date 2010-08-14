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

__author__  = 'ThorN/xlr8or'
__version__ = '1.1.2'

import re
import b3

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
            ('EVT_CLIENT_BAN', 'Client Banned'),
            ('EVT_CLIENT_BAN_TEMP', 'Client Temp Banned'),
            ('EVT_CLIENT_KICK', 'Client Kicked'),
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

#-----------------------------------------------------------------------------------------------------------------------
# raise to cancel event processing
class VetoEvent(Exception):
    pass

eventManager = Events()
