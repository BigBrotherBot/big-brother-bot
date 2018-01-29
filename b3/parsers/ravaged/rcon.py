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

"""
Dummy rcon module for Ravaged to satisfy B3 parser API.

Ideally, B3 parser should be changed to allow games to
not require a separated socket connection for rcon commands

To use that Rcon class, instantiate and use the set_server_connection() method.
Then you can expect this class to work like the other Rcon classes
"""

__author__ = 'Courgette'
__version__ = '1.1'


class Rcon(object):

    def __init__(self, console, *args):
        self.console = console
        self.server_conn = None

    def set_server_connection(self, server_conn):
        self.server_conn = server_conn

    def writelines(self, lines):
        for line in lines:
            self.write(line)

    def write(self, cmd, *args, **kwargs):
        if not self.server_conn:
            return
        self.console.verbose(u'RCON :\t %s' % repr(cmd))
        response = self.server_conn.command(cmd)
        self.console.verbose(u'RCON response:\t %s' % repr(response))
        return response

    def flush(self):
        pass

    def close(self):
        pass