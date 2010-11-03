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

# CHANGELOG
# 31/01/2010 - 1.2.2 - xlr8or - Removed commandsdict, inherit from codparser
# 18/04/2010 - 1.2.3 - xlr8or - Forcing g_logsync to make server write unbuffered gamelogs
# 30/05/2010 - 1.2.4 - xlr8or - Setting exception for 31 char PBid in shortversion v1.2
# 17/10/2010 - 1.2.5 - xlr8or - Don't let version exceptions be inherited by later parsers


__author__  = 'ThorN, ttlogic, xlr8or'
__version__ = '1.2.5'

import b3.parsers.cod
import re

class Cod2Parser(b3.parsers.cod.CodParser):
    gameName = 'cod2'
    IpsOnly = False
    _logSync = 1 # Value for unbuffered game logging

    # cod2 needs the multiline flag because it adds "Domain is 0 or 1" to the cvar output
    _reCvar = re.compile(b3.parsers.q3a.abstractParser.AbstractParser._reCvar.pattern, re.I | re.M)

    # set exceptions for this specific version of cod2
    def setVersionExceptions(self):
        # this shouldn't be inherited by later parsers, so restrict to this game only
        if self.gameName == 'cod2':
            if self.game.shortversion == '1.0' and not self.IpsOnly:
                self.warning('CoD2 version 1.0 has known limitations on Authentication! B3 will not work properly!')
            if self.game.shortversion == '1.2':
                # cod2 v1.2 has a bug so PBid's are 31 characters long, instead of 32, override the regexp for testing PBid's
                self.debug('Overriding pbid length for cod2 v1.2 with PB!')
                self._pbRegExp = re.compile(r'^[0-9a-f]{30,32}$', re.IGNORECASE) # RegExp to match a PunkBuster ID
            else:
                pass
        else:
            pass
