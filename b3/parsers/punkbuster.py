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

__author__  = 'ThorN'
__version__ = '1.3'

import re


class PunkBuster(object):

    console = None

    # : Player List: [Slot #] [GUID] [Address] [Status] [Power] [Auth Rate] [Recent SS] [O/S] [Name]
    # : 4 27b26543216546163546513465135135(-) 111.11.1.11:28960 OK   1 3.0 0 (W) "ShyRat"
    # : 5 387852749658574858598854913cdf11(-) 222.222.222.222:28960 OK   1 10.0 0 (W) "shatgun"
    # : 6 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5.0 0 (W) "FATTYBMBLATY"
    regPlayer = re.compile(r"""
        ^.*?                                        # a new line start with junk (ungreedy mode)
        (.*?):?\s*                                  # end of PB response prefix (potentially missing one char)
          (?P<slot>[1-9][0-9]??)                    # slot number between 1 and 99 (ungreedy mode)
        (?:\s+|)                                    # blank character(s) or nothing
          (?P<pbid>[a-f0-9]{30,32})                 # PB id (at least 30 char long, max 32)
        [^a-f0-9].*?                                # anything but a pbid char and eventually some junk (ungreedy mode)
          (?P<ip>(?:(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9]))
        .+?                                         # junk
        (?:\)\s*"|\)\s*|\s+")                       # detect start of name
          (?P<name>.*?)"?                           # name
        \s*$                                        # end of line
        """, re.IGNORECASE|re.VERBOSE)


    def __init__(self, console):
        """
        Object constructor.
        :param console: The console instance
        """
        self.console = console

    def send(self, command):
        """
        Send a command to the punkbuster server.
        :param command: The command to be sent
        """
        return self.console.write(command)

    def badName(self, grace, text_filter):
        """
        PB_SV_BadName [grace_seconds] [text_filter]
        Adds a bad name to the list of bad names for the server to disallow in player names
        """
        return self.send('PB_SV_BadName "%s" "%s"' % (grace, text_filter))

    def badNameDel(self, slot):
        """
        PB_SV_BadNameDel [slot #]
        Deletes a bad name from the list of bad names 
        """
        return self.send('PB_SV_BadNameDel "%s"' % slot)

    def ban(self, client, reason='', private=''):
        """
        PB_SV_Ban [name or slot #] [displayed_reason] | [optional_private_reason]
        Removes a player from the game and permanently bans that player from the server based
        on the player's guid (based on the cdkey); the ban is logged and also written to the
        pbbans.dat file in the pb folder 
        """
        if client.cid and client.connected:
            return self.send('PB_SV_Ban "%s" "%s" "%s"' % (int(client.cid) + 1, reason, private))
        else:
            return self.banGUID(client, reason)

    def banGUID(self, client, reason=''):
        """
        PB_SV_BanGuid [guid] [player_name] [IP_Address] [reason]
        Adds a guid directly to PB's permanent ban list; if the player_name or IP_Address
        are not known, we recommend using "???" 
        """
        if not client.pbid:
            return False
        return self.send('PB_SV_BanGuid "%s" "%s" "%s" "%s"' % (client.pbid, client.name, client.ip, reason))

    def kick(self, client, minutes=1, reason='', private=''):
        """
        PB_SV_Kick [name or slot #] [minutes] [displayed_reason] | [optional_private_reason]
        Removes a player from the game and won't let the player rejoin until specified [minutes] 
        has passed or until the server is restarted, whichever comes first - kicks are not written
        to the pbbans.dat file but they are logged and will show up in the output from the pb_sv_banlist command 
        """
        if not client.cid or not client.connected:
            return False
        return self.send('PB_SV_Kick "%s" "%s" "%s" "%s"' % (int(client.cid) + 1, minutes, reason, private))

    def getSs(self, client):
        """
        Sends a request to all applicable connected players asking for a screen shot to be captured and
        sent to the PB Server; to specify a player name or substring (as opposed to slot #), surround the text
        with double-quote marks
        """
        if not client.cid or not client.connected:
            return False
        return self.send('PB_SV_GetSs "%s"' % (int(client.cid) + 1))

    def pList(self):
        """
        PB_SV_PList
        Displays a list of connected players and their current status 
        """
        return self.send('PB_SV_PList')

    def unBan(self, slot):
        """
        PB_SV_UnBan [slot #]
        Unbans a player from the ban list stored in memory; use pb_sv_updbanfile to update the
        permanent ban file after using this command 
        """
        return self.send('PB_SV_UnBan "%s"' % slot)

    def unBanGUID(self, client):
        """
        PB_SV_UnBanGuid [guid]
        Unbans a guid from the ban list stored in memory; use pb_sv_updbanfile to update the
        permanent ban file after using this command 
        """
        if not client.pbid:
            return False

        result = self.send('PB_SV_UnBanGuid "%s"' % client.pbid)
        if result:
            self.send('pb_sv_updbanfile')
            return result

        return False

    def getPlayerList(self):
        """
        Extract cid, pbid, ip for all connected players.
        :return: a dict having slot numbers (minus 1) as keys and an other dict as values.
        This later dict has keys : cid, pbid, guid and ip
        """
        data = self.pList()
        if not data:
            return {}

        players = {}
        lastslot = 0
        for line in data.split('\n'):
            m = re.match(self.regPlayer, line)
            if m:
                d = m.groupdict()
                if int(m.group('slot')) > lastslot:
                    d['guid'] = d['pbid']
                    lastslot = int(m.group('slot'))
                    players[str(lastslot - 1)] = d
                    
                else:
                    self.console.debug('Duplicate or incorrect PB slot number - client ignored %s '
                                       'lastslot %s' % (m.group('slot'), lastslot))
            elif 'Player List:' not in line:
                self.console.verbose2("PB player info cannot be extracted of %r" % line)
        return players

    def __setattr__(self, key, value):
        self.__dict__[key] = value
        if key != 'console':
            self.send('PB_SV_%s %s' % (key.title(), value))

    def __getattr__(self, key):
        try:        
            return self.__dict__[key]
        except:
            return self.send('PB_SV_%s' % key.title())