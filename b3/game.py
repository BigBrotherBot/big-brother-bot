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

__author__  = 'ThorN'
__version__ = '1.2.0'

import time

class Game(object):
    mapName = None
    timeLimit = None
    fragLimit = None
    captureLimit = None
    gameType = None
    _roundTimeStart = None
    _mapTimeStart = None
    rounds = 0
    gameName = None
    modName = None

    def __init__(self, console, gameName):
        self.console = console
        self.gameName = gameName
        self.startRound()

    def __getattr__(self, key):
        if self.__dict__.has_key(key):
            return self.__dict__[key]

        return None

    def __setitem__(self, key, value):
        self.__dict__[key] = value
        return self.__dict__[key]

    def mapTime(self):
        return self.console.time()  - self._mapTimeStart

    def roundTime(self):
        return self.console.time() - self._roundTimeStart

    def startRound(self):
        if not self._mapTimeStart:
            self.startMap()

        self._roundTimeStart = self.console.time()
        self.rounds = self.rounds + 1

    def startMap(self, mapName=None):
        if mapName:
            self.mapName = mapName

        self._mapTimeStart = self.console.time()

    def mapEnd(self):
        self._mapTimeStart = None
        