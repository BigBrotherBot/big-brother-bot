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


"""
 TIPS FOR CONTRIBUTORS :
 =======================

  * In your main config file, set log level down to 8 to see log message of
    type VERBOS2.  <set name="log_level">8</set>

  * You can add the section below in your b3.xml in order to display the log
    file on your console :
        <settings name="devmode">
            <set name="log2console">true</set>
        </settings>

"""

import re
import json

import b3
from b3.parser import Parser
from b3.events import EVT_CUSTOM

class AltitudeParser(Parser):
    """B3 parser for the Altitude game. See http://altitudegame.com"""
    
    ## parser code name to use in b3.xml
    gameName = 'altitude'
    
    ## extract the time off a log line
    _lineTime  = re.compile(r'^{"port":[0-9]+, "time":(?P<seconds>[0-9]+),.*')
    
    ## Direct event mapping between Altitude events type and B3 event types.
    ## B3 event will be created with their data parameter set to the full
    ## altitude event object
    _eventMap = {
        'consoleCommandExecute' : EVT_CUSTOM,
    }


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
        ## capitalized name prefixed by 'OnAltitude'.
        ## I.E.: type 'clientAdd' would route to 'OnAltitudeClientAdd' method
        type = altitude_event['type']
        method_name = "OnAltitude%s%s" % (type[:1].upper(), type[1:])
        event = None
        if not hasattr(self, method_name):
            if type in self._eventMap:
                event = b3.events.Event(self._eventMap[type], data=altitude_event)
            else:
                # no handling method for such event :(
                # we fallback on creating a B3 event of type EVT_UNKNOWN
                self.verbose2("create method %s to handle event %r", method_name, altitude_event)
                event = self.getEvent('EVT_UNKNOWN', data=altitude_event)
        else:
            func = getattr(self, method_name)
            event = func(altitude_event)
        
        # if we came up with a B3 event, then queue it up so it can be dispatched
        # to the listening plugins
        if event:
            self.verbose2("event created for this log line : %s", event)
            self.queueEvent(event)



    # ================================================
    # handle Game events.
    #
    # those methods are called by parseLine() and 
    # may return a B3 Event object
    # ================================================

    def OnAltitudeClientAdd(self, altitude_event):
        """ handle log lines of type clientAdd
        example :
        {"port":27276,"demo":false,"time":12108767,"level":9,"player":2,"nickname":"Courgette","aceRank":0,"vaporId":"a8654321-123a-414e-c71a-123123123131","type":"clientAdd","ip":"192.168.10.1:27272"}
        """
        ## self.clients is B3 currently connected player store. We tell the client store we got a new one.
        self.clients.newClient(altitude_event['player'], guid=altitude_event['vaporId'], name=altitude_event['nickname'], team=b3.TEAM_UNKNOWN)


    def OnAltitudeClientRemove(self, altitude_event):
        """ handle log lines of type clientRemove
        example :
        {"port":27276,"message":"left","time":17317434,"player":2,"reason":"Client left.","nickname":"Courgette","vaporId":"a8654321-123a-414e-c71a-123123123131","type":"clientRemove","ip":"192.168.10.1:27272"}'
        """
        c = self.clients.getByCID(altitude_event['player'])
        if c:
            c.disconnect()


    def OnAltitudeChat(self, altitude_event):
        """ handle log lines of type clientRemove
        example :
        {"port":27276,"message":"test","time":326172,"player":2,"server":false,"type":"chat"}

        Unfortunately, there is no distinction between a normal chat and team chat
        {"port":27276,"message":"test team chat","time":1167491,"player":3,"server":false,"type":"chat"}
        """
        c = self.clients.getByCID(altitude_event['player'])
        if c:
            if altitude_event['server'] == False:
                return self.getEvent('EVT_CLIENT_SAY', data=altitude_event['message'], client=c)
            else:
                return self.getEvent('EVT_CUSTOM', data=altitude_event, client=c)

    # =======================================
    # implement parser interface
    # =======================================

    def say(self, msg):
        """\
        broadcast a message to all players
        """
        self.write('serverMessage %s' % self.stripColors(msg))


    def message(self, client, msg):
        """\
        display a message to a given player
        """
        self.write('serverWhisper %s %s' % (client.name, self.stripColors(msg)))


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
            