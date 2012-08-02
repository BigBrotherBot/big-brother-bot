#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2011 Thomas LEVEIL
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


"""
dummy rcon module for Battleye to satisfy B3 parser. 

Ideally, B3 parser should be changed to allow games to 
not require a separated socket connection for rcon commands

To use that Rcon class, instantiate and use the set_battleye_server() method. 
Then you can expect this class to work like the other Rcon classes
"""
from b3.parsers.battleye.protocol import CommandError, CommandTimeoutError

__author__  = 'Courgette'
__version__ = '1.1'

#--------------------------------------------------------------------------------------------------
class Rcon:
    def __init__(self, console, *args):
        self.console = console
        self.battleye_server = None
        
    def set_battleye_server(self, battleye_server):
        self.battleye_server = battleye_server
    
    def writelines(self, lines):
        for line in lines:
            self.write(line)

    def write(self, cmd, *args, **kwargs):
        if not self.battleye_server or not self.battleye_server.connected:
            return
        self.console.bot(u'RCON > %s' % repr(cmd))
        response = None
        try:
            response = self.battleye_server.command(cmd)
            self.console.bot(u'RCON < %s' % repr(response))
        except CommandTimeoutError, err:
            self.console.error("RCON # %s" % err)
        except CommandError, err:
            self.console.error("RCON ERROR : %s" % err, exc_info=err)
        return response
        
    def flush(self):
        pass

    def close(self):
        pass
