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
from b3.events import EVT_UNKNOWN
from b3.parser import Parser
from b3.parsers.q3a.rcon import Rcon as Q3Rcon
import b3.events
import re
import select
import string
__author__  = 'Courgette'
__version__ = '0.0'



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



class BrinkRcon(Q3Rcon):
    rconsendstring = '\xff\xffrcon\xff%s\xff%s\xff'
    rconreplystring = '\xff\xffprint\x00'
    qserversendstring = '\xff\xff%s\xff'

    def readSocket(self, sock, size=4048, socketTimeout=None):
        if socketTimeout is None:
            socketTimeout = self.socket_timeout
        data = ''
        readables, writeables, errors = select.select([sock], [], [sock], socketTimeout)
        if not len(readables):
            raise Exception('No readable socket')
        d = str(sock.recv(size))
        if d:
            # remove rcon header
            data += d[12:]
            if len(d)==size:
                readables, writeables, errors = select.select([sock], [], [sock], socketTimeout)
                while len(readables):
                    self.console.verbose('RCON: More data to read in socket')
                    d = str(sock.recv(size))
                    if d:
                        data += d
                    readables, writeables, errors = select.select([sock], [], [sock], socketTimeout)
        return data.rstrip('\x00').strip()



class BrinkParser(Parser):
    gameName = 'brink'
    OutputClass = BrinkRcon

    # remove the time off of the line
    _lineTime  = re.compile(r'^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:(?P<minutes>[0-9]+):(?P<seconds>[0-9]+).*')
    _lineClear = re.compile(r'^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]+:[0-9]+ : ')

    _lineFormats = (
        # OnClientConnect: Clearing abilities for client 15
        ("OnClientConnect", re.compile(r'^OnClientConnect: Clearing abilities for client (?P<cid>[0-9]+)$')),
        ("OnClientDisconnect", re.compile(r'^client (?P<cid>[0-9]+) disconnected.$')),
    )

    def startup(self):
        pass

    def getLineParts(self, line):
        line = re.sub(self._lineClear, '', line, 1)
        for f in self._lineFormats:
            m = re.match(f[1], line)
            if m:
                self.debug('line matched %s' % f[1].pattern)
                break
        if m:
            return (f[0], m)

    def parseLine(self, line):           
        result = self.getLineParts(line)
        if not result:
            return False
        action, match = result
        if hasattr(self, action):
            func = getattr(self, action)
            event = func(line, match)
            if event:
                self.queueEvent(event)
        else:
            self.verbose2("Implement method : def %s(self, line, match):", action)
            self.queueEvent(b3.events.Event(EVT_UNKNOWN, "%s: %s" % (action, line)))




    # ================================================
    # handle Game events.
    #
    # those methods are called by parseLine() and 
    # may return a B3 Event object
    # ================================================
    
    def OnClientConnect(self, line, match):
        cid = match.group('cid')
        if cid:
            self.clients.newClient(cid)
            
    def OnClientDisconnect(self, line, match):
        cid = match.group('cid')
        if cid:
            client = self.clients.getByCID(cid)
            if client:
                client.disconnect()
        

    # =======================================
    # implement parser interface
    # =======================================
    
    def getPlayerList(self):
        """\
        Query the game server for connected players.
        return a dict having players' id for keys and players' data as another dict for values
        """
        raise NotImplementedError

    def authorizeClients(self):
        """\
        For all connected players, fill the client object with properties allowing to find 
        the user in the database (usualy guid, or punkbuster id, ip) and call the 
        Client.auth() method 
        """
        ## todo : find a way to obtain guid
        pass
    
    def sync(self):
        """\
        For all connected players returned by self.getPlayerList(), get the matching Client
        object from self.clients (with self.clients.getByCID(cid) or similar methods) and
        look for inconsistencies. If required call the client.disconnect() method to remove
        a client from self.clients.
        This is mainly useful for games where clients are identified by the slot number they
        occupy. On map change, a player A on slot 1 can leave making room for player B who
        connects on slot 1.
        """
        raise NotImplementedError
    
    def say(self, msg):
        """\
        broadcast a message to all players
        """
        self.write("say %s" % msg)

    def saybig(self, msg):
        """\
        broadcast a message to all players in a way that will catch their attention.
        """
        raise NotImplementedError

    def message(self, client, text):
        """\
        display a message to a given player
        """
        raise NotImplementedError

    def kick(self, client, reason='', admin=None, silent=False, *kwargs):
        """\
        kick a given player
        """
        raise NotImplementedError

    def ban(self, client, reason='', admin=None, silent=False, *kwargs):
        """\
        ban a given player
        """
        raise NotImplementedError

    def unban(self, client, reason='', admin=None, silent=False, *kwargs):
        """\
        unban a given player
        """
        raise NotImplementedError

    def tempban(self, client, reason='', duration=2, admin=None, silent=False, *kwargs):
        """\
        tempban a given player
        """
        raise NotImplementedError

    def getMap(self):
        """\
        return the current map/level name
        """
        raise NotImplementedError

    def getMaps(self):
        """\
        return the available maps/levels name
        """
        raise NotImplementedError

    def rotateMap(self):
        """\
        load the next map/level
        """
        raise NotImplementedError
        
    def changeMap(self, map):
        """\
        load a given map/level
        return a list of suggested map names in cases it fails to recognize the map that was provided
        """
        raise NotImplementedError

    def getPlayerPings(self):
        """\
        returns a dict having players' id for keys and players' ping for values
        """
        raise NotImplementedError

    def getPlayerScores(self):
        """\
        returns a dict having players' id for keys and players' scores for values
        """
        raise NotImplementedError
        
    def inflictCustomPenalty(self, type, client, reason=None, duration=None, admin=None, data=None):
        """
        Called if b3.admin.penalizeClient() does not know a given penalty type. 
        Overwrite this to add customized penalties for your game like 'slap', 'nuke', 
        'mute', 'kill' or anything you want.
        /!\ This method must return True if the penalty was inflicted.
        """
        pass



if __name__ == '__main__':
    from b3.fake import fakeConsole

    def test_rcon():
        server = BrinkRcon(fakeConsole, ('127.0.0.1', 27025), 'pass')

        data = server.sendRcon("serverinfo")

        for line in data.splitlines():
            if line == '\x00':
                print("-"*10)
            else:
                print(line)

        print("%r" % server.sendRcon("sys_cpuSpeed"))
        print('-'*20)


    test_rcon()
