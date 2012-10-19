#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2012 Courgette
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
#
import re


"""
This module helps defining handlers functions to be called when a game event is received by providing :

  - a decorator for associating a regular expression to a handling function : @ger.gameEvent(<regular expression>, ...)
  - a method getHandler(<text>) that return a tuple <func, dict> where *func* is the first handler function defined
    with the gameEvent decorator that matches the given *text* and *dict* is a dict of all matched groups from the
    regular expression that was associated to *func* with the decorator.


Usage :
-------

This tool is meant to be used by B3 game parsers which need to parse game event (in the form of a string) and call
a function that takes action for this type of game event.

To make a B3 parser take advantage of the GameEventRouter, the B3 parser needs to redefine the *parseLine* method
as follow :

from b3.game_event_router import Game_event_router

ger = Game_event_router()

def parseLine(self, line):
    if line is None:
        return
    hfunc, param_dict = ger.getHandler(line)
    if hfunc:
        self.verbose2("calling %s%r" % (hfunc.func_name, param_dict))
        event = hfunc(self, **param_dict)
        if event:
            self.queueEvent(event)


Let say you need to print "Robin joined team BLUE" when parsing a game event which is "join: Robin, BLUE" then you would
have the following method in your B3 game parser :

@ger.gameEvent("^join: (?P<name>.+), (?P<team>.+)$")
def on_connect(self, name, team):
    print "%s joined team %s" % (name, team)


Note that the handler function must have parameters that matches the regular expression groups.

The @ger.gameEvent decorator accepts multiple parameters if you need to have one handling function for multiple kind of
game events. Note that those regular expressions should all define the same groups.

"""


class Game_event_router(object):

    def __init__(self):
        # will hold mapping between regular expressions and handler functions
        self._gameevents_mapping = list()


    def gameEvent(self, *decorator_param):
        """
        python decorator to easily map a handler function to a regular expression mathching a game event
        """
        def wrapper(func):
            for param in decorator_param:
                if isinstance(param, type(re.compile(''))):
                    self._gameevents_mapping.append((param, func))
                elif isinstance(param, basestring):
                    self._gameevents_mapping.append((re.compile(param), func))
            return func
        return wrapper



    def getHandler(self, gameEvent):
        """
        for a given game event, return the corresponding handler function and a dict of the matched regular expression groups
        """
        for regex, hfunc in self._gameevents_mapping:
            match = regex.match(gameEvent)
            if match:
                return hfunc, match.groupdict()
        return None, {}

