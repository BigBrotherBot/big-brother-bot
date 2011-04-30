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
import json
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

    def parseLine(self, line):
        """method call for each line of the game log file that must return
        a B3 event"""
        ## conveniently, Altitude log lines are encoded in JSON
        ''' Examples of log lines :
{"port":27276,"time":103197,"name":"Courgette test Server","type":"serverInit","maxPlayerCount":14}
{"port":27276,"time":103344,"map":"ball_cave","type":"mapLoading"}
{"port":27276,"time":103682,"type":"serverStart"}
{"port":27276,"demo":false,"time":103691,"level":1,"player":0,"nickname":"Bot 1","aceRank":0,"vaporId":"00000000-0000-0000-0000-000000000000","type":"clientAdd","ip":"0.0.0.0:100001"}
{"port":27276,"demo":false,"time":12108767,"level":9,"player":2,"nickname":"Courgette","aceRank":0,"vaporId":"d8123456-18a4-124e-a45b-155641685161","type":"clientAdd","ip":"192.168.10.1:27272"}
{"port":27276,"time":12110927,"type":"pingSummary","pingByPlayer":{"2":0}}
{"port":27276,"time":12123445,"player":2,"team":2,"type":"teamChange"}
{"port":27276,"time":12124957,"plane":"Loopy","player":1,"perkRed":"Tracker","perkGreen":"Rubberized Hull","team":4,"type":"spawn","perkBlue":"Turbocharger","skin":"Flame Skin"}
{"port":27276,"time":15048305,"streak":0,"source":"turret","player":-1,"victim":1,"multi":0,"xp":10,"type":"kill"}
        '''
        altitude_event = json.loads(line)
        
        ## we will route the handling of that altitude_event to a method dedicated 
        ## to an alititude event type. The method will be name after the event type
        ## capitalized name prefixed by 'OnAltitude'
        method_name = "OnAltitude%s" % altitude_event['type'].capitalize()
        
        event = None
        if not hasattr(self, method_name):
            # no handling method for such event :(
            # we fallback on creating a B3 event of type EVT_UNKNOWN
            self.verbose("un-handled altitude event : %r", altitude_event)
            event = self.getEvent('EVT_UNKNOWN', data=altitude_event)
        else:
            func = getattr(self, method_name)
            event = func(altitude_event)
        
        # if we came up with a B3 event, then queue it up so it can be dispatched
        # to the listening plugins
        if event:
            self.queueEvent(event)



    # ================================================
    # handle Game events.
    #
    # those methods are called by parseLine() and 
    # may return a B3 Event object
    # ================================================
       
    


    # =======================================
    # implement parser interface
    # =======================================

    def say(self, msg):
        self.write('serverMessage %s' % self.stripColors(msg))

    
    # =======================================
    # other methods
    # =======================================




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
            