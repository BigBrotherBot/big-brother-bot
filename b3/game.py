# -*- coding: utf-8 -*-

# ################################################################### #
#                                                                     #
#  BigBrotherBot(B3) (www.bigbrotherbot.net)                          #
#  Copyright (C) 2005 Michael "ThorN" Thornton                        #
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

__author__  = 'ThorN'
__version__ = '1.6'


class Game(object):

    _mapName = None
    _mapTimeStart = None
    _roundTimeStart = None

    captureLimit = None
    fragLimit = None
    timeLimit = None

    gameName = None
    gameType = None
    modName = None

    rounds = 0

    def __init__(self, console, gameName):
        """
        Object constructor.
        :param console: Console class instance
        :param gameName: The current game name
        """
        self.console = console
        self.gameName = gameName
        self.startRound()

    def __getattr__(self, key):
        if key in self.__dict__:
            return self.__dict__[key]
        return None

    def __setitem__(self, key, value):
        self.__dict__[key] = value
        return self.__dict__[key]

    def _get_mapName(self):
        if not self._mapName:
            try:
                # try to get the mapname from the server
                mapname = self.console.getMap()
            except Exception:
                self._mapName = None
            else:
                # set using _set_mapName to generate EVT_GAME_MAP_CHANGE
                self._set_mapName(mapname)
        return self._mapName

    def _set_mapName(self, newmap):
        if self._mapName != newmap:
            # generate EVT_GAME_MAP_CHANGE so plugins can detect that a new game is starting
            event = self.console.getEvent('EVT_GAME_MAP_CHANGE', data={'old': self._mapName, 'new': newmap})
            self.console.queueEvent(event)
        self._mapName = newmap
    
    mapName = property(_get_mapName, _set_mapName)

    def mapTime(self):
        """
        Return the time elapsed since map start.
        """
        if self._mapTimeStart:
            return self.console.time() - self._mapTimeStart
        return None

    def roundTime(self):
        """
        Return the time elapsed since round start
        """
        return self.console.time() - self._roundTimeStart

    def startRound(self):
        """
        Set variables to mark round start.
        """
        if not self._mapTimeStart:
            self.startMap()
        self._roundTimeStart = self.console.time()
        self.rounds += 1

    def startMap(self, mapName=None):
        """
        Set variables to mark map start.
        """
        if mapName:
            self.mapName = mapName
        self._mapTimeStart = self.console.time()

    def mapEnd(self):
        """
        Set variables to mark map end.
        """
        self._mapTimeStart = None