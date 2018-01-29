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

__author__ = 'Fenix'
__version__ = '1.0'


import b3.clients
import b3.functions
import b3.parsers.cod4
import re


class Cod4grParser(b3.parsers.cod4.Cod4Parser):

    _guidLength = 10

    # num score ping guid                             name            lastmsg address               qport rate
    # --- ----- ---- -------------------------------- --------------- ------- --------------------- ----- -----
    #    0     0    3 GameRanger-Account-ID_0006400896 Ranger^7           50 103.231.162.141:16000   7068
    _regPlayer = re.compile(r'^\s*(?P<slot>[0-9]+)\s+'
                            r'(?P<score>[0-9-]+)\s+'
                            r'(?P<ping>[0-9]+)\s+'
                            r'GameRanger-Account-ID_(?P<guid>[0-9]+)\s+'
                            r'(?P<name>.*?)\s+'
                            r'(?P<last>[0-9]+?)\s*'
                            r'(?P<ip>(?:(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}'
                            r'(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])):?'
                            r'(?P<port>-?[0-9]{1,5})\s*'
                            r'(?P<qport>-?[0-9]{1,5})\s+'
                            r'(?P<rate>[0-9]+)$', re.IGNORECASE | re.VERBOSE)

    ####################################################################################################################
    #                                                                                                                  #
    #   PARSER INITIALIZATION                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    def __new__(cls, *args, **kwargs):
        b3.parsers.cod4.patch_b3_clients()
        return b3.parsers.cod4.Cod4Parser.__new__(cls)