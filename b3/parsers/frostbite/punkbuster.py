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
# CHANGELOG
# 2010/03/24 - 1.1 - Courgette
#   * make sure to fallback on the parsers' getPlayerList() method as in the BFBC2 
#     the PB_SV_PList command is asynchronous and cannot be used as expected
#     with other B3 parsers
#   * make sure not to ban with slot id as this is not reliable
#
#

__author__  = 'Courgette'
__version__ = '1.1'

import re
import b3.parsers.punkbuster

#--------------------------------------------------------------------------------------------------
class PunkBuster(b3.parsers.punkbuster.PunkBuster):

    def send(self, command):
        return self.console.write(('punkBuster.pb_sv_command', command))

    def getPlayerList(self):
        return self.console.getPlayerList()

    def ban(self, client, reason='', private=''):
        # in BFBC2 we do not have reliable slot id for connected players.
        # fallback on banning by GUID instead
        return self.banGUID(client, reason)
            