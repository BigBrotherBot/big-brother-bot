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


from clients import Client
from enum import Enum, unique
from time import time


@unique
class EventType(Enum):
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

class Event(object):

    def __init__(self, type:EventType, data:dict, client:Client=None, target:Client=None):
        """B3 event representation"""
        self.time : float = time()
        self.type : EventType = type
        self.data : dict = data
        self.client : Client = client
        self.target : Client = target

    def __str__(self):
        return 'Event<%s>(%r, %s, %s)' % (self.type.value, self.data, self.client, self.target)
