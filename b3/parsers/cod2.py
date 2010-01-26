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

__author__  = 'ThorN, ttlogic'
__version__ = '1.2.1'

import b3.parsers.cod
import b3.parsers.q3a
import re

class Cod2Parser(b3.parsers.cod.CodParser):
    gameName = 'cod2'
    IpsOnly = False

    _commands = {}
    _commands['message'] = 'tell %(cid)s %(prefix)s ^3[pm]^7 %(message)s'
    _commands['deadsay'] = 'tell %(cid)s %(prefix)s [DEAD]^7 %(message)s'
    _commands['say'] = 'say %(prefix)s %(message)s'
    _commands['set'] = 'set %(name)s "%(value)s"'
    _commands['kick'] = 'clientkick %(cid)s'
    _commands['ban'] = 'banclient %(cid)s'
    _commands['tempban'] = 'clientkick %(cid)s'


    # cod2 needs the multiline flag because it adds "Domain is 0 or 1" to the cvar output
    _reCvar = re.compile(b3.parsers.q3a.Q3AParser._reCvar.pattern, re.I | re.M)