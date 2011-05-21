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
from b3.cvar import Cvar
from b3.lib.sourcelib import SourceQuery
from b3.parser import Parser
from b3.parsers.q3a.rcon import Rcon as Q3Rcon
import b3
import re
import select
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

    _reCvarName = re.compile(r'^[a-z0-9_.]+$', re.I)
    _reCvar = re.compile(r'^"(?P<cvar>[a-z0-9_.]+)" is:"(?P<value>.*?)"\^7 default:"(?P<default>.*?)".*', re.I)

    # remove the time off of the line
    _lineTime  = re.compile(r'^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:(?P<minutes>[0-9]+):(?P<seconds>[0-9]+).*')
    _lineClear = re.compile(r'^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]+:[0-9]+ : ')

    _lineFormats = (
        # OnClientConnect: Clearing abilities for client 15
        ("OnClientConnect", re.compile(r'^client (?P<cid>[0-9]+) connected.$')),
        ("OnClientDisconnect", re.compile(r'^client (?P<cid>[0-9]+) disconnected.$')),
        ("OnClientDisconnectByName", re.compile(r'^(?P<name>.+) disconnected.$')),
        ("OnClientTeamChange", re.compile(r'^(?P<name>.+) joined the (?P<team>.+)$')),
        ("OnInitFromNewMap", re.compile(r"^InitFromNewMap: 'maps/mp/(?P<map>.+).entities'$")),
        ("OnClientClassChange", re.compile(r"^(?P<cid>[0-9]+) given player class '(?P<class>.+)' \(clients desired player class\)$")),
    )
    
    queryPort = None
    sourceQueryClient = None

    def startup(self):
        self.setCvar('logTimeStamps', "1")
        self.setCvar('logFileFilter', "WARNING:")
        self.setCvar('logFile', "2")
        
        self.queryPort = self.getCvar("net_serverPortMaster").getInt()
        self.info("query port is : %s", self.queryPort)
        self.sourceQueryClient = SourceQuery.SourceQuery(self._rconIp, self.queryPort, timeout=5)
        
        self.queryGameInfo()
        self.info("connected players : %r" % self.getPlayerList())


    def getLineParts(self, line):
        line = re.sub(self._lineClear, '', line, 1)
        f = None
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
                self.verbose2("queuing event %r ", event)
                self.queueEvent(event)
        else:
            self.verbose2("Implement method : def %s(self, line, match):", action)
            self.queueEvent(self.getEvent('EVT_UNKNOWN', data="%s: %s" % (action, line)))

    def getCvar(self, cvarName):
        if self._reCvarName.match(cvarName):
            #"g_password" is:"^7" default:"scrim^7"
            val = self.write(cvarName)
            self.debug('Get cvar %s = [%s]', cvarName, val)
            #sv_mapRotation is:gametype sd map mp_brecourt map mp_carentan map mp_dawnville map mp_depot map mp_harbor map mp_hurtgen map mp_neuville map mp_pavlov map mp_powcamp map mp_railyard map mp_rocket map mp_stalingrad^7 default:^7
            m = self._reCvar.match(val)
            if m and m.group('cvar').lower() == cvarName.lower():
                return Cvar(m.group('cvar'), value=m.group('value'), default=m.group('default'))

    def setCvar(self, cvarName, value):
        if re.match('^[a-z0-9_.]+$', cvarName, re.I):
            self.debug('Set cvar %s = [%s]', cvarName, value)
            self.write('set %s %s' % (cvarName, value))
        else:
            self.error('%s is not a valid cvar name', cvarName)


    # ================================================
    # handle Game events.
    #
    # those methods are called by parseLine() and 
    # may return a B3 Event object
    # ================================================
    
    def OnClientConnect(self, line, match):
        """
        example: client 4 connected.
        """
        cid = match.group('cid')
        if cid:
            # find out its name
            players = self.getPlayerList()
            if cid in players:
                data = players[cid]
                client = self.clients.newClient(cid, name=data['name'], data=data)
                self.debug("created client %r " % client)
            
    def OnClientDisconnect(self, line, match):
        """
        example: client 4 Disconnected.
        """
        cid = match.group('cid')
        if cid:
            client = self.clients.getByCID(cid)
            if client:
                client.disconnect()
            
    def OnClientDisconnectByName(self, line, match):
        """
        example: medvidek Disconnected.
        """
        name = match.group('name')
        if name:
            client = self.clients.getByExactName(name)
            if client:
                client.disconnect()
        
    def OnClientTeamChange(self, line, match):
        name = match.group('name')
        team = match.group('team')
        if name and team:
            client = self.clients.getByExactName(name)
            if client:
                client.team = self.getTeam(team)
            return self.getEvent('EVT_CLIENT_JOIN', data=team, client=client)
        
    def OnInitFromNewMap(self, line, match):
        """
        example: InitFromNewMap: 'maps/mp/reactor.entities'
        """
        map = match.group('map')
        if map:
            self.game.mapName = map
            self.game.startMap()
        
    def OnClientClassChange(self, line, match):
        """
        example: 10 given player class 'soldier' (clients desired player class)
        """
        cid = match.group('cid')
        playerclass = match.group('class')
        if cid and playerclass:
            client = self.clients.getByCID(cid)
            if client:
                client.data = {'class': playerclass}
                self.debug("updated %s class to %s ", client, playerclass)




    # =======================================
    # implement parser interface
    # =======================================
    
    def getPlayerList(self):
        """\
        Query the game server for connected players.
        return a dict having players' id for keys and players' data as another dict for values
        """
        data = self.sourceQueryClient.player()
        if not data:
            return {}
        self.debug(data)
        players = {}
        for pdata in data:
            players[pdata['index']] = pdata
        return players

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


    #===============================================================================
    # 
    # convenience methods
    # 
    #===============================================================================

    def getTeam(self, id):
        """convert a Brink team identifier into a B3 team id"""
        if id == 'Resistance':
            return b3.TEAM_BLUE
        elif id == 'Security':
            return b3.TEAM_RED
        elif id == 'Spectators':
            return b3.TEAM_SPEC
        else:
            return b3.TEAM_UNKNOWN
        
    def queryGameInfo(self):
        """use the Source Query Protocol to get game info
        
        {'steamid': 90083332288439317L, 'map': 'mp/aquarium', 'dedicated': 'd', 
        'gamedir': 'Brink', 'secure': 1, 'numbots': 0, 'gamedesc': 'Brink', 
        'hostname': 'Cucurb B3 test server', 'numplayers': 1, 'maxplayers': 16, 
        'version': '0.0.0.0', 'appid': 22350, 'edf': 177, 'passworded': 0, 
        'tag': 'apv=2621477,mr=sdGameRulesObjective,pm=2,q=social,dlc=0,ded=1,hij=0,pwd=0,t1=15,t2=0,pnr=1,pl=0,bd=0,sr=2', 
        'os': 'w', 'port': 27025}
        """
        data = self.sourceQueryClient.info()
        if data:
            self.game.mapName = data.pop('map')
            datatags = data.pop('tag')
            tags = {}
            for t in datatags.split(','):
                if not t: continue
                k,v = t.split('=')
                tags[k] = v
            self.game.gameType = tags['mr']
            for k,v in data.iteritems():
                self.game[k] = v
        self.debug("game : %r" % self.game)
        

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
