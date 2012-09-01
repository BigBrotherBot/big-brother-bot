# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2010
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
# CHANGELOG
#
# 08/01/2012 - v0.1 - NTAuthority (http://fourdeltaone.net/)



__author__  = 'NTAuthority'
__version__ = '0.1'

import b3.parsers.cod6
import re

class Cod8Parser(b3.parsers.cod6.Cod6Parser):
    gameName = 'cod8'
    _guidLength = 16

    _commands = {}
    _commands['message'] = 'tell %(cid)s %(prefix)s ^3[pm]^7 %(message)s'
    _commands['deadsay'] = 'tell %(cid)s %(prefix)s [DEAD]^7 %(message)s'
    _commands['say'] = 'say %(prefix)s %(message)s'
    _commands['set'] = 'set %(name)s "%(value)s"'
    _commands['kick'] = 'dropclient %(cid)s "%(reason)s"'
    _commands['ban'] = 'banclient %(cid)s'
    _commands['unban'] = 'unban \"%(name)s\"' # remove players from game engine's permanent.ban
    _commands['tempban'] = 'tempbanclient %(cid)s "%(reason)s"'

    _regPlayer = re.compile(r'(?P<slot>[0-9]+)[\s\0]+(?P<score>[0-9-]+)[\s\0]+(?P<ping>[0-9]+)[\s\0]+(?P<guid>[a-z0-9]+)[\s\0]+(?P<name>.*?)[\s\0]+(?P<last>[0-9]+)[\s\0]+(?P<ip>[0-9.]+):(?P<port>[0-9-]+)', re.I)

    def startup(self):
        b3.parsers.cod6.Cod6Parser.startup(self)
        

