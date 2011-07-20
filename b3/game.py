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
# CHANGELOG:
#
# 26/03/2011 - 1.3 - Courgette
#    * add event EVT_GAME_MAP_CHANGE
# 21/07/2011 - 1.3.1 - Freelander
#    * prevent status plugin errors during map change
#

__author__  = 'ThorN'
__version__ = '1.3.1'

import time
from b3.events import Event, EVT_GAME_MAP_CHANGE

class Game(object):
    _mapName = None
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

    def _get_mapName(self):
        return self._mapName

    def _set_mapName(self, newmap):
        if self._mapName != newmap:
            self.console.queueEvent(Event(EVT_GAME_MAP_CHANGE, {'old': self._mapName, 'new': newmap}))
        self._mapName = newmap
    
    mapName = property(_get_mapName, _set_mapName)

    def mapTime(self):
        if self._mapTimeStart:
            return self.console.time() - self._mapTimeStart
        return None

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
        
        
if __name__ == '__main__':
    from b3.plugin import Plugin
    from b3.fake import fakeConsole
    
    fakeplugin = Plugin(fakeConsole)
    def onEvent(event):
        if event.type == EVT_GAME_MAP_CHANGE:
            fakeConsole.debug("event EVT_GAME_MAP_CHANGE : %r" % event.data)
            fakeConsole.debug("previous map was %s" % event.data['old'])
            fakeConsole.debug("new map is %s" % event.data['new'])
    fakeplugin.onEvent = onEvent
    
    fakeConsole.registerHandler(EVT_GAME_MAP_CHANGE, fakeplugin)
    
    game = Game(fakeConsole, 'fakegamename')
    
    print('setting map name to map1...')
    game.mapName = 'map1'
    assert game.mapName == 'map1'

    time.sleep(2)
    print('setting map name to map2...')
    game.mapName = 'map2'
    assert game.mapName == 'map2'
        
    time.sleep(2)
    print('setting map name to map2...')
    game.mapName = 'map2'
    assert game.mapName == 'map2'
        
    time.sleep(2)
    print('setting map name to map3...')
    game.mapName = 'map3'
    assert game.mapName == 'map3'
    
        
