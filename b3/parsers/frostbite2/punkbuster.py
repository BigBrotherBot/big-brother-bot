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
__author__  = 'Courgette'
__version__ = '1.2'

import b3.parsers.punkbuster

#--------------------------------------------------------------------------------------------------
class PunkBuster(b3.parsers.punkbuster.PunkBuster):

    def send(self, command):
        return self.console.write(('punkBuster.pb_sv_command', command))

    def getPlayerList(self):
        return self.console.getPlayerList()

    def ban(self, client, reason='', private=''):
        # in BF3 we do not have reliable slot id for connected players.
        # fallback on banning by GUID instead
        self.banGUID(client, reason)
        self.send('pb_sv_updbanfile')

    def kick(self, client, minutes=1, reason='', private=''):
        """
        PB_SV_Kick [name or slot #] [minutes] [displayed_reason] | [optional_private_reason]
        Removes a player from the game and won't let the player rejoin until specified [minutes]
        has passed or until the server is restarted, whichever comes first - kicks are not written
        to the pbbans.dat file but they are logged and will show up in the output from the pb_sv_banlist command
        """
        if client and client.connected:
            self.send('PB_SV_Kick "%s" "%s" "%s" "%s"' % (client.cid, minutes, reason, private))
            self.send('pb_sv_updbanfile')

    def banGUID(self, client, reason=''):
        """
        PB_SV_BanGuid [guid] [player_name] [IP_Address] [reason]
        Adds a guid directly to PB's permanent ban list; if the player_name or IP_Address
        are not known, we recommend using "???"
        """
        if client.pbid:
            name = client.name if client.name else '?'
            ip = client.ip if client.ip else '?'
            self.send('PB_SV_BanGuid %s "%s" "%s" "%s"' % (client.pbid, name, ip, reason))

    def unBanGUID(self, client):
        """
        PB_SV_UnBanGuid [guid]
        Unbans a guid from the ban list stored in memory; use pb_sv_updbanfile to update the
        permanent ban file after using this command
        """
        if client.pbid:
            self.send('PB_SV_UnBanGuid %s' % client.pbid)
            self.send('pb_sv_updbanfile')