# encoding: utf-8
#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2011 
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
#

__author__  = 'Courgette'
__version__ = '0.1'

import re
from b3.parser import Parser


class AltitudeParser(Parser):
    """B3 parser for the Altitude game. See http://altitudegame.com"""
    
    ## parser code name to use in b3.xml
    gameName = 'altitude'
    
    ## extract the time off a log line
    _lineTime  = re.compile(r'^{"port":[0-9]+, "time":(?P<seconds>[0-9]+),.*')
    
    def startup(self):
        self._initialize_rcon()

    def _initialize_rcon(self):
        """We need a way to send rcon commands to the gale server. In
        Altitude, this is done by writing commands to be run on a new line
        of the command.txt file"""
        
        # check that the command file is provided in the b3.xml config file
        if not self.config.has_option('server', 'command_file'):
            self.critical("The B3 config file for Altitude must provide the location of the command file")
            self.die()
        
        # open the command file
        commandfile_name = self.config.getpath('server', 'command_file')
        self.output = AltitudeRcon(console=self, commandfile=commandfile_name)


    def say(self, msg):
        self.write('serverMessage %s' % self.stripColors(msg))


class AltitudeRcon():
    """Object that opens the Altitude command file and allows B3 to write
    commands in it"""
    def __init__(self, console, commandfile):
        self.console = console
        self._commandfile_name = commandfile
        self._fh = open(commandfile, 'a')
        
    def writelines(self, lines):
        for line in lines:
            self.write(line)

    def write(self, cmd, *args, **kwargs):
        """To send a command to the server, the format to respect is :
        [server port],[command type],[data]
        """
        self.console.verbose(u'RCON :\t %s' % cmd)
        self._fh.write("%s,console,%s\n" % (self.console._port, cmd))
        
    def flush(self):
        self._fh.flush()

    def close(self):
        self._fh.close()
        
    def _get_encoding(self):
        return self._fh.encoding
    encoding = property(_get_encoding)
            