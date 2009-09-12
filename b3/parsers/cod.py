# BigBrotherBot(B3) (www.bigbrotherbot.com)
# Copyright (C) 2005 Michael "ThorN" Thornton
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
# CHANGELOG
# 7/23/2005 - 1.1.0
#    Added damage type to Damage and Kill event data
# 27/6/2009 - 1.3.1 - xlr8or - Added Action Mechanism (event) for version 1.1.5 
# 28/8/2009 - 1.3.2 - Bakes - added regexp for CoD4 suicides

__author__  = 'ThorN'
__version__ = '1.3.2'



import b3.parsers.q3a
import re, string
import b3
import b3.events
import b3.parsers.punkbuster

class CodParser(b3.parsers.q3a.Q3AParser):
    gameName = 'cod'
    _settings = {}
    _settings['line_length'] = 65
    _settings['min_wrap_length'] = 120

    _commands = {}
    _commands['message'] = 'tell %(cid)s %(prefix)s ^3[pm]^7 %(message)s'
    _commands['deadsay'] = 'tell %(cid)s %(prefix)s [DEAD]^7 %(message)s'
    _commands['say'] = 'say %(prefix)s %(message)s'
    _commands['set'] = 'set %(name)s "%(value)s"'
    _commands['kick'] = 'clientkick %(cid)s'
    _commands['ban'] = 'banid %(cid)s'
    _commands['tempban'] = 'clientkick %(cid)s'

    _eventMap = {
        'warmup' : b3.events.EVT_GAME_WARMUP,
        'restartgame' : b3.events.EVT_GAME_ROUND_END
    }

    # remove the time off of the line
    _lineClear = re.compile(r'^(?:[0-9:]+\s?)?')
    #0:00 InitGame: \g_gametype\dm\gamename\Call of Duty
    _lineFormats = (
        # server events
        re.compile(r'^(?P<action>[a-z]+):\s?(?P<data>.*)$', re.IGNORECASE),
        # world kills
        re.compile(r'^(?P<action>[A-Z]);(?P<data>(?P<guid>[^;]+);(?P<cid>[0-9-]{1,2});(?P<team>[a-z]+);(?P<name>[^;]+);(?P<aguid>[^;]*);(?P<acid>-1);(?P<ateam>world);(?P<aname>[^;]*);(?P<aweap>[a-z0-9_-]+);(?P<damage>[0-9.]+);(?P<dtype>[A-Z_]+);(?P<dlocation>[a-z_]+))$', re.IGNORECASE),
        # player kills/damage
        re.compile(r'^(?P<action>[A-Z]);(?P<data>(?P<guid>[^;]+);(?P<cid>[0-9]{1,2});(?P<team>[a-z]*);(?P<name>[^;]+);(?P<aguid>[^;]+);(?P<acid>[0-9]{1,2});(?P<ateam>[a-z]*);(?P<aname>[^;]+);(?P<aweap>[a-z0-9_-]+);(?P<damage>[0-9.]+);(?P<dtype>[A-Z_]+);(?P<dlocation>[a-z_]+))$', re.IGNORECASE),
        # suicides (cod4)
        re.compile(r'^(?P<action>[A-Z]);(?P<data>(?P<guid>[^;]+);(?P<cid>[0-9]{1,2});(?P<team>[a-z]*);(?P<name>[^;]+);(?P<aguid>[^;]*);(?P<acid>-1);(?P<ateam>[a-z]*);(?P<aname>[^;]+);(?P<aweap>[a-z0-9_-]+);(?P<damage>[0-9.]+);(?P<dtype>[A-Z_]+);(?P<dlocation>[a-z_]+))$', re.IGNORECASE),
        
        #A;168004;7;allies;^4[^9SaW^4] ^9|| ^1IvEl;bomb_plant
        #team actions
        re.compile(r'^(?P<action>[A-Z]);(?P<data>(?P<guid>[^;]+);(?P<cid>[0-9]{1,2});(?P<team>[a-z]+);(?P<name>[^;]+);(?P<type>[a-z_]+))$', re.IGNORECASE),
        
        # tell like events    
        re.compile(r'^(?P<action>[a-z]+);(?P<data>(?P<guid>[^;]+);(?P<cid>[0-9]{1,2});(?P<name>[^;]+);(?P<aguid>[^;]+);(?P<acid>[0-9]{1,2});(?P<aname>[^;]+);(?P<text>.*))$', re.IGNORECASE),
        # say like events
        re.compile(r'^(?P<action>[a-z]+);(?P<data>(?P<guid>[^;]+);(?P<cid>[0-9]{1,2});(?P<name>[^;]+);(?P<text>.*))$', re.IGNORECASE),
        # all other events
        re.compile(r'^(?P<action>[A-Z]);(?P<data>(?P<guid>[^;]+);(?P<cid>[0-9]{1,2});(?P<name>[^;]+))$', re.IGNORECASE)
    )
#D;364484;25;axis;^2(AS) ^6Frank ^1The ^3Tank;;-1;world;;none;3;MOD_FALLING;none
#D;441615;14;axis;^4dnb^1[malcontent];;-1;world;;none;6;MOD_FALLING;none
#D;248102;19;allies;sgtglen;248102;10;axis;=^1J^7=^1K^9ismet;mp44_mp;27;MOD_PISTOL_BULLET;right_foot
#K;465030;4;axis;<-(^3AS^7)-ThorN->;578287;0;axis;^9Xx.^7R^1yga^7R^9.xX;kar98k_mp;180;MOD_HEAD_SHOT;head

    #num score ping guid   name            lastmsg address               qport rate
    #--- ----- ---- ------ --------------- ------- --------------------- ----- -----
    #2     0   29 465030 <-{^4AS^7}-^3ThorN^7->^7       50 68.63.6.62:-32085      6597  5000
    _regPlayer = re.compile(r'^(?P<slot>[0-9]+)\s+(?P<score>[0-9-]+)\s+(?P<ping>[0-9]+)\s+(?P<guid>[0-9]+)\s+(?P<name>.*?)\s+(?P<last>[0-9]+)\s+(?P<ip>[0-9.]+):(?P<port>[0-9-]+)\s+(?P<qport>[0-9]+)\s+(?P<rate>[0-9]+)$', re.I)

    PunkBuster = None

    def startup(self):
        # add the world client
        client = self.clients.newClient(-1, guid='WORLD', name='World', hide=True, pbid='WORLD')

        if not self.config.has_option('server', 'punkbuster') or self.config.getboolean('server', 'punkbuster'):
            self.PunkBuster = b3.parsers.punkbuster.PunkBuster(self)

    # kill
    def OnK(self, action, data, match=None):
        victim = self.getClient(victim=match)
        if not victim:
            self.debug('No victim')
            self.OnJ(action, data, match)
            return None

        attacker = self.getClient(attacker=match)
        if not attacker:
            self.debug('No attacker')
            return None

        attacker.team = self.getTeam(match.group('ateam'))
        attacker.name = match.group('aname')
        victim.team = self.getTeam(match.group('team'))
        victim.name = match.group('name')

        event = b3.events.EVT_CLIENT_KILL

        if attacker.cid == victim.cid:
            event = b3.events.EVT_CLIENT_SUICIDE
        elif attacker.team != b3.TEAM_UNKNOWN and attacker.team == victim.team:
            event = b3.events.EVT_CLIENT_KILL_TEAM

        victim.state = b3.STATE_DEAD
        return b3.events.Event(event, (float(match.group('damage')), match.group('aweap'), match.group('dlocation'), match.group('dtype')), attacker, victim)

    # damage
    def OnD(self, action, data, match=None):
        victim = self.getClient(victim=match)
        if not victim:
            self.debug('No victim - attempt join')
            self.OnJ(action, data, match)
            return None

        attacker = self.getClient(attacker=match)
        if not attacker:
            self.debug('No attacker')
            return None

        attacker.team = self.getTeam(match.group('ateam'))
        attacker.name = match.group('aname')
        victim.team = self.getTeam(match.group('team'))
        victim.name = match.group('name')

        event = b3.events.EVT_CLIENT_DAMAGE
        if attacker.cid == victim.cid:
            event = b3.events.EVT_CLIENT_DAMAGE_SELF
        elif attacker.team != b3.TEAM_UNKNOWN and attacker.team == victim.team:
            event = b3.events.EVT_CLIENT_DAMAGE_TEAM

        return b3.events.Event(event, (float(match.group('damage')), match.group('aweap'), match.group('dlocation'), match.group('dtype')), attacker, victim)

    # disconnect
    def OnQ(self, action, data, match=None):
        client = self.getClient(match)
        if client: client.disconnect()
        return None

    # join
    def OnJ(self, action, data, match=None):
        codguid = match.group('guid')
        if len(codguid) <= 5:
            # invalid guid
            codguid = None

        client = self.getClient(match)

        if client:
            # update existing client
            client.state = b3.STATE_ALIVE
            # possible name changed
            client.name = match.group('name')
        else:
            # make a new client
            if self.PunkBuster:        
                # we will use punkbuster's guid
                guid = None
            else:
                # use cod guid
                guid = codguid 

            client = self.clients.newClient(match.group('cid'), name=match.group('name'), state=b3.STATE_ALIVE, guid=guid, data={ 'codguid' : codguid })

        return b3.events.Event(b3.events.EVT_CLIENT_JOIN, None, client)

    # action
    def OnA(self, action, data, match=None):
        #A;136528;6;allies;{^6AS^7}^6Honey;re_pickup
        client = self.getClient(match)
        if not client:
            self.debug('No client - attempt join')
            self.OnJ(action, data, match)
            
            client = self.getClient(match)

            if not client:
                return None

        client.name = match.group('name')
        actiontype = match.group('type')
        self.verbose('OnAction: %s: %s' % (client.name, actiontype) )
        return b3.events.Event(b3.events.EVT_CLIENT_ACTION, actiontype, client)

    def OnSay(self, action, data, match=None):
        #3:12 say: <-{AS}-ThorN->: sfs
        client = self.getClient(match)
        if not client:
            self.debug('No client - attempt join')
            self.OnJ(action, data, match)
            
            client = self.getClient(match)

            if not client:
                return None

        data = match.group('text')
        if data and ord(data[:1]) == 21:
            data = data[1:]

        client.name = match.group('name')
        return b3.events.Event(b3.events.EVT_CLIENT_SAY, data, client)

    def OnSayteam(self, action, data, match=None):
        #3:12 sayteam: <-{AS}-ThorN->: sfs
        client = self.getClient(match)
        if not client:
            self.debug('No client - attempt join')
            self.OnJ(action, data, match)
            
            client = self.getClient(match)

            if not client:
                return None

        data = match.group('text')
        # sometimes there is a weird character in the message
        # remove if it is there
        if data and ord(data[:1]) == 21:
            data = data[1:]

        client.name = match.group('name')
        return b3.events.Event(b3.events.EVT_CLIENT_TEAM_SAY, data, client)

    def OnTell(self, action, data, match=None):
        #4197:48tell;465030;2;ThorN;465030;2;ThorN;testing
        client = self.getClient(match)
        tclient = self.getClient(attacker=match)

        if not client:
            self.debug('No client - attempt join')
            self.OnJ(action, data, match)
            
            client = self.getClient(match)

            if not client:
                return None

        data = match.group('text')
        if data and ord(data[:1]) == 21:
            data = data[1:]

        client.name = match.group('name')
        return b3.events.Event(b3.events.EVT_CLIENT_PRIVATE_SAY, data, client, tclient)

    def OnExitlevel(self, action, data, match=None):
        self.clients.sync()
        return b3.events.Event(b3.events.EVT_GAME_EXIT, data)

    def OnItem(self, action, data, match=None):
        guid, cid, name, item = string.split(data, ';', 3)
        client = self.clients.getByCID(cid)
        if client:
            return b3.events.Event(b3.events.EVT_CLIENT_ITEM_PICKUP, item, client)
        return None

    def getTeam(self, team):
        if team == 'allies':
            return b3.TEAM_BLUE
        elif team == 'axis':
            return b3.TEAM_RED
        else:
            return b3.TEAM_UNKNOWN

    _reMap = re.compile(r'map ([a-z0-9_-]+)', re.I)
    def getMaps(self):
        maps = self.getCvar('sv_mapRotation')

        nmaps = []
        if maps:
            maps = re.findall(self._reMap, maps[0])

            for m in maps:
                if m[:3] == 'mp_':
                    m = m[3:]

                nmaps.append(m.title())

        return nmaps

    def getNextMap(self):
        if not self.game.mapName: return None
        
        maps = self.getCvar('sv_mapRotation')

        if maps:
            maps = re.findall(self._reMap, maps[0])

            gmap = self.game.mapName.strip().lower()

            found = False
            for nmap in maps:
                nmap = nmap.strip().lower()
                if found:
                    found = nmap
                    break
                elif nmap == gmap:
                    # current map, break on next map
                    found = True

            if found == True:
                # map is first map in rotation
                nmap = maps[0].strip().lower()

            if found:
                if nmap[:3] == 'mp_': nmap = nmap[3:]
                return nmap.title()

            return None
        else:
            return None
