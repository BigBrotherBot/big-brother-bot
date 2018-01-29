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

__author__ = 'ThorN, ttlogic, xlr8or'
__version__ = '1.4.1'

import b3.parsers.cod
import re


class Cod2Parser(b3.parsers.cod.CodParser):

    gameName = 'cod2'
    IpsOnly = False

    _logSync = 1    # value for unbuffered game logging

    def setVersionExceptions(self):
        """
        Set exceptions for this specific version of COD2
        """
        # this shouldn't be inherited by later parsers, so restrict to this game only
        if self.gameName == 'cod2':
            if self.game.shortversion == '1.0' and not self.IpsOnly:
                self.warning('CoD2 version 1.0 has known limitations on authentication! B3 will not work properly!')
            if self.game.shortversion == '1.2':
                # cod2 v1.2 has a bug so PBid's are 31 characters long, instead of 32,
                # override the regexp for testing PBid's
                self.debug('Overriding pbid length for cod2 v1.2 with PB!')
                self._pbRegExp = re.compile(r'^[0-9a-f]{30,32}$', re.IGNORECASE)  # RegExp to match a PunkBuster ID