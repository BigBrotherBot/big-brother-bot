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

# CHANGELOG
#    31/01/2010 - 1.2.2 -  xlr8or
#    * Removed commandsdict, inherit from codparser


__author__  = 'ThorN, ttlogic'
__version__ = '1.2.2'

import b3.parsers.cod
import b3.parsers.q3a
import re

class Cod2Parser(b3.parsers.cod.CodParser):
    gameName = 'cod2'
    IpsOnly = False

    # cod2 needs the multiline flag because it adds "Domain is 0 or 1" to the cvar output
    _reCvar = re.compile(b3.parsers.q3a.Q3AParser._reCvar.pattern, re.I | re.M)