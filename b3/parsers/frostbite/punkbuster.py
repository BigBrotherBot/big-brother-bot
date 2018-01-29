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

__author__  = 'Courgette'
__version__ = '1.2'


import b3.parsers.punkbuster


class PunkBuster(b3.parsers.punkbuster.PunkBuster):

    def send(self, command):
        """
        Send a command to the punkbuster server.
        :param command: The command to be sent
        """
        return self.console.write(('punkBuster.pb_sv_command', command))

    def getPlayerList(self):
        """
        Extract cid, pbid, ip for all connected players.
        :return: a dict having slot numbers (minus 1) as keys and an other dict as values.
        """
        return self.console.getPlayerList()

    def ban(self, client, reason='', private=''):
        """
        PB_SV_Ban [name or slot #] [displayed_reason] | [optional_private_reason]
        Removes a player from the game and permanently bans that player from the server based
        on the player's guid (based on the cdkey); the ban is logged and also written to the
        pbbans.dat file in the pb folder.
        """
        # in BFBC2 we do not have reliable slot id for connected players.
        # fallback on banning by GUID instead
        return self.banGUID(client, reason)