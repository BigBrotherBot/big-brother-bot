# Smokin' Guns parser for BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2009 ailmanki
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA    02110-1301    USA
#
# CHANGELOG
# 31/01/2010 - 0.1 - Courgette
# * use the new /cp command to send private messages (requires SmokinGuns v1.1)
# 31/01/2010 - 0.1.1 - Courgette
# * getMap() is now inherited from q3a
# 06/02/2010 - 0.1.2 - Courgette
# * do not use cp/bigtext for private messaging to make this parser compatible with SG pior to v1.1
# * fix the ban command
# 15/09/2010 - 0.1.3 - GrosBedo
# * added !nextmap and !maps support
# 09/04/2011 - 0.1.4 - Courgette
# * reflect that cid are not converted to int anymore in the clients module

__author__  = 'xlr8or, Courgette'
__version__ = '0.1.4'

import re, string, threading
import b3
import b3.events
from b3.parsers.q3a.abstractParser import AbstractParser
import b3.parsers.punkbuster

class SmgParser(AbstractParser):
    gameName = 'smg'
    _counter = {}

    _settings = {}
    _settings['line_length'] = 65
    _settings['min_wrap_length'] = 100

    _empty_name_default = 'EmptyNameDefault'

    _commands = {}
    _commands['message'] = '%(cid)s %(prefix)s ^3[pm]^7 %(message)s'
    _commands['deadsay'] = '%(cid)s %(prefix)s [DEAD]^7 %(message)s'
    _commands['say'] = 'say %(prefix)s %(message)s'
    _commands['set'] = 'set %(name)s "%(value)s"'
    _commands['kick'] = 'clientkick %(cid)s'
    _commands['ban'] = 'banClient %(cid)s'
    _commands['tempban'] = 'clientkick %(cid)s'

    _eventMap = {
        'warmup' : b3.events.EVT_GAME_WARMUP,
        'restartgame' : b3.events.EVT_GAME_ROUND_END
    }

    # remove the time off of the line
    _lineClear = re.compile(r'^(?:[0-9:.]+\s?)?')

    _lineFormats = (
        re.compile(r'^(?P<action>[a-z]+):\s*(?P<data>(?P<cid>[0-9]+):\s*(?P<pbid>[0-9A-Z]{32}):\s*(?P<name>[^:]+):\s*(?P<num1>[0-9]+):\s*(?P<num2>[0-9]+):\s*(?P<ip>[0-9.]+):(?P<port>[0-9]+))$', re.IGNORECASE),
        re.compile(r'^(?P<action>[a-z]+):\s*(?P<data>(?P<cid>[0-9]+):\s*(?P<name>.+):\s+(?P<text>.*))$', re.IGNORECASE),
        #
        #1536:37Kill: 1 18 9: ^1klaus killed ^1[pura]fox.nl by MOD_MP40
        re.compile(r'^(?P<action>[a-z]+):\s*(?P<data>(?P<acid>[0-9]+)\s(?P<cid>[0-9]+)\s(?P<aweap>[0-9]+):\s*(?P<text>.*))$', re.IGNORECASE),
        #
        re.compile(r'^(?P<action>[a-z]+):\s*(?P<data>(?P<cid>[0-9]+):\s*(?P<text>.*))$', re.IGNORECASE),
        re.compile(r'^(?P<action>[a-z]+):\s*(?P<data>(?P<cid>[0-9]+)\s(?P<text>.*))$', re.IGNORECASE),
        #
        # Falling through?
        # 1:05 ClientConnect: 3
        # 1:05 ClientUserinfoChanged: 3 guid\CAB616192CB5652375401264987A23D0\n\xlr8or\t\0\model\wq_male2/red\g_redteam\\g_blueteam\\hc\100\w\0\l\0\tt\0\tl\0
        re.compile(r'^(?P<action>[a-z_]+):\s*(?P<data>.*)$', re.IGNORECASE)
    )

    #map: dm_fort
    #num score ping name            lastmsg address               qport rate
    #--- ----- ---- --------------- ------- --------------------- ----- -----
    #  1     1    0 TheMexican^7          100 bot                       0 16384
    #  2     1    0 Sentenza^7             50 bot                       0 16384
    #  3     3   37 xlr8or^7                0 145.99.135.227:27960   3598 25000
    _regPlayer = re.compile(r'^(?P<slot>[0-9]+)\s+(?P<score>[0-9-]+)\s+(?P<ping>[0-9]+)\s+(?P<name>.*?)\s+(?P<last>[0-9]+)\s+(?P<ip>[0-9.]+):(?P<port>[0-9-]+)\s+(?P<qport>[0-9]+)\s+(?P<rate>[0-9]+)$', re.I)
    #_regPlayer = re.compile(r'^(?P<slot>[0-9]+)\s+(?P<score>[0-9-]+)\s+(?P<ping>[0-9]+)\s+(?P<name>.*?)\s+(?P<last>[0-9]+)\s+(?P<ip>[0-9.:-]+)\s+(?P<qport>[0-9]+)\s+(?P<rate>[0-9]+)$', re.I)
    _reColor = re.compile(r'(\^.)|[\x00-\x20]|[\x7E-\xff]')

    PunkBuster = None

    ## kill mode constants: modNames[meansOfDeath]
    MOD_UNKNOWN='0'
    #melee
    MOD_KNIFE='1'
    #pistols
    MOD_REM58='2'
    MOD_SCHOFIELD='3'
    MOD_PEACEMAKER='4'
    #rifles
    MOD_WINCHESTER66='5'
    MOD_LIGHTNING='6'
    MOD_SHARPS='7'
    #shotguns
    MOD_REMINGTON_GAUGE='8'
    MOD_SAWEDOFF='9'
    MOD_WINCH97='10'
    #automatics
    MOD_GATLING='11'
    #explosives
    MOD_DYNAMITE='12'
    MOD_MOLOTOV='13'
    #misc
    MOD_WATER='14'
    MOD_SLIME='15'
    MOD_LAVA='16'
    MOD_CRUSH='17'
    MOD_TELEFRAG='18'
    MOD_FALLING='19'
    MOD_SUICIDE='20'
    MOD_WORLD_DAMAGE='21'
    MOD_TRIGGER_HURT='22'
    MOD_NAIL='23'
    MOD_CHAINGUN='24'
    MOD_PROXIMITY_MINE='25'
    MOD_BOILER='26'

    ## meansOfDeath to be considered suicides
    Suicides = (
        MOD_WATER,
        MOD_SLIME,
        MOD_LAVA,
        MOD_CRUSH,
        MOD_TELEFRAG,
        MOD_FALLING,
        MOD_SUICIDE,
        MOD_TRIGGER_HURT,
        MOD_NAIL,
        MOD_CHAINGUN,
        MOD_PROXIMITY_MINE,
        MOD_BOILER
    )

#---------------------------------------------------------------------------------------------------

    def startup(self):
        # add the world client
        
        client = self.clients.newClient('-1', guid='WORLD', name='World', hide=True, pbid='WORLD')
        #if not self.config.has_option('server', 'punkbuster') or self.config.getboolean('server', 'punkbuster'):
        #    self.PunkBuster = b3.parsers.punkbuster.PunkBuster(self)

        # get map from the status rcon command
        map = self.getMap()
        if map:
            self.game.mapName = map
            self.info('map is: %s'%self.game.mapName)

#---------------------------------------------------------------------------------------------------

    # Added for debugging and identifying/catching log lineparts
    def getLineParts(self, line):
        line = re.sub(self._lineClear, '', line, 1)

        for f in self._lineFormats:
            m = re.match(f, line)
            if m:
                #self.debug('XLR--------> line matched %s' % f.pattern)
                break

        if m:
            client = None
            target = None
            return (m, m.group('action').lower(), m.group('data').strip(), client, target)
        elif '------' not in line:
            self.verbose('XLR--------> line did not match format: %s' % line)

#---------------------------------------------------------------------------------------------------

    def OnClientconnect(self, action, data, match=None):
        self._clientConnectID = data
        client = self.clients.getByCID(data)
        return b3.events.Event(b3.events.EVT_CLIENT_JOIN, None, client)

    # Parse Userinfo
    def OnClientuserinfo(self, action, data, match=None):
        bclient = self.parseUserInfo(data)
        self.verbose('Parsed user info %s' % bclient)
        if bclient:
            cid = bclient['cid']
            client = self.clients.getByCID(cid)

            if client:
                # update existing client
                for k, v in bclient.iteritems():
                    setattr(client, k, v)
            else:
                if not bclient.has_key('name'):
                    bclient['name'] = self._empty_name_default

                if bclient.has_key('guid'):
                    guid = bclient['guid']
                else:
                    #guid = 'BOT-' + str(bclient['name'])
                    guid = 'BOT-' + str(cid)
                    self.verbose('BOT connected!')
                    client = self.clients.newClient(cid, name=bclient['name'], ip='0.0.0.0', state=b3.STATE_ALIVE, guid=guid, data={ 'guid' : guid })
                    return None

                self._counter[cid] = 1
                t = threading.Timer(2, self.newPlayer, (cid, guid, bclient['name']))
                t.start()
                self.debug('%s connected, waiting for Authentication...' %bclient['name'])
                self.debug('Our Authentication queue: %s' % self._counter)

        return None

    # disconnect
    def OnKill(self, action, data, match=None):
        self.debug('OnKill: %s (%s)'%(match.group('aweap'),match.group('text')))
        
        victim = self.clients.getByCID(match.group('cid'))
        if not victim:
            self.debug('No victim')
            #self.OnClientuserinfo(action, data, match)
            return None

        weapon = match.group('aweap')
        if not weapon:
            self.debug('No weapon')
            return None

        ## Fix attacker
        if match.group('aweap') in self.Suicides:
            # those kills should be considered suicides
            self.debug('OnKill: Fixed attacker, suicide detected: %s' %match.group('text'))
            attacker = victim
        else:
            attacker = self.clients.getByCID(match.group('acid'))
        ## end fix attacker
          
        if not attacker:
            self.debug('No attacker')
            return None

        dType = match.group('text').split()[-1:][0]
        if not dType:
            self.debug('No damageType, weapon: %s' % weapon)
            return None

        event = b3.events.EVT_CLIENT_KILL

        # fix event for team change and suicides and tk
        if attacker.cid == victim.cid:
            event = b3.events.EVT_CLIENT_SUICIDE
        elif attacker.team != b3.TEAM_UNKNOWN and attacker.team == victim.team:
            event = b3.events.EVT_CLIENT_KILL_TEAM

        # if not defined we need a general hitloc (for xlrstats)
        if not hasattr(victim, 'hitloc'):
            victim.hitloc = 'body'
        
        victim.state = b3.STATE_DEAD
        #self.verbose('OnKill Victim: %s, Attacker: %s, Weapon: %s, Hitloc: %s, dType: %s' % (victim.name, attacker.name, weapon, victim.hitloc, dType))
        # need to pass some amount of damage for the teamkill plugin - 100 is a kill
        return b3.events.Event(event, (100, weapon, victim.hitloc, dType), attacker, victim)

    def OnClientdisconnect(self, action, data, match=None):
        client = self.clients.getByCID(data)
        if client: client.disconnect()
        return None

    # startgame
    def OnInitgame(self, action, data, match=None):
        options = re.findall(r'\\([^\\]+)\\([^\\]+)', data)

        for o in options:
            if o[0] == 'mapname':
                self.game.mapName = o[1]
            elif o[0] == 'g_gametype':
                self.game.gameType = self.defineGameType(o[1])
            elif o[0] == 'fs_game':
                self.game.modName = o[1]
            else:
                setattr(self.game, o[0], o[1])

        self.verbose('...self.console.game.gameType: %s' % self.game.gameType)
        self.game.startRound()

        self.debug('Synchronizing client info')
        self.clients.sync()

        return b3.events.Event(b3.events.EVT_GAME_ROUND_START, self.game)

    def OnSayteam(self, action, data, match=None):
        # Teaminfo does not exist in the sayteam logline. Parse it as a normal say line
        return self.OnSay(action, data, match)

#---------------------------------------------------------------------------------------------------

    def parseUserInfo(self, info):
        #2 n\peyote\t\3\c\0\r\0\m\0000000\s\0000000\dn\\dr\0\w\0\lw\0\sw\0\mu\0\ref\0\p\0\ss\0\sc\0\tv\0\lc\0
        #0 \g_password\none\cl_guid\0A337702493AF67BB0B0F8565CE8BC6C\cl_wwwDownload\1\name\thorn\rate\25000\snaps\20\cl_anonymous\0\cl_punkbuster\1\password\test\protocol\83\qport\16735\challenge\-79719899\ip\69.85.205.66:27960
        playerID, info = string.split(info, ' ', 1)

        if info[:1] != '\\':
            info = '\\' + info

        options = re.findall(r'\\([^\\]+)\\([^\\]+)', info)

        data = {}
        for o in options:
            data[o[0]] = o[1]

        data['cid'] = playerID

        if data.has_key('n'):
            data['name'] = data['n']

        # split port from ip field
        if data.has_key('ip'):
            tip = string.split(data['ip'], ':', 1)
            data['ip'] = tip[0]
            data['port'] = tip[1]

        t = 0
        if data.has_key('team'):
            t = data['team']
        elif data.has_key('t'):
            t = data['t']

        data['team'] = self.getTeam(t)
        if data.has_key('cl_guid'):
            data['cl_guid'] = data['cl_guid'].lower()

        if data.has_key('pbid'):
            data['pbid'] = data['pbid'].lower()

        if data.has_key('cl_guid') and not data.has_key('pbid'):
            data['pbid'] = data['cl_guid']
        
        return data


    def getTeam(self, team):
        if team == 'red': team = 1
        if team == 'blue': team = 2
        team = int(team)
        if team == 1:
            #self.verbose('Team is Red')
            return b3.TEAM_RED
        elif team == 2:
            #self.verbose('Team is Blue')
            return b3.TEAM_BLUE
        elif team == 3:
            #self.verbose('Team is Spec')
            return b3.TEAM_SPEC
        else:
            return b3.TEAM_UNKNOWN

    # Translate the gameType to a readable format (also for teamkill plugin!)
    def defineGameType(self, gameTypeInt):

        _gameType = ''
        _gameType = str(gameTypeInt)
        #self.debug('gameTypeInt: %s' % gameTypeInt)
        
        if gameTypeInt == '0':
            _gameType = 'dm'        # Deathmatch
        elif gameTypeInt == '1':
            _gameType = 'du'        # Duel
        elif gameTypeInt == '3':
            _gameType = 'tdm'       # Team Death Match
        elif gameTypeInt == '4':
            _gameType = 'ts'        # Team Survivor (Round TDM)
        elif gameTypeInt == '5':
            _gameType = 'br'        # Bank Robbery
        
        #self.debug('_gameType: %s' % _gameType)
        return _gameType

    def getMaps(self):
        if self._maplist is not None:
            return self._maplist

        data = self.write('fdir *.bsp')
        if not data:
            return []

        mapregex = re.compile(r'^maps/(?P<map>.+)\.bsp$', re.I)
        maps = []
        for line in data.split('\n'):
            m = re.match(mapregex, line.strip())
            if m:
                if m.group('map'):
                    maps.append(m.group('map'))

        return maps

    def getNextMap(self):
        data = self.write('nextmap')
        nextmap = self.findNextMap(data)
        if nextmap:
            return nextmap
        else:
            return 'no nextmap set or it is in an unrecognized format !'

    def findNextMap(self, data):
        # "nextmap" is: "vstr next4; echo test; vstr aupo3; map oasago2"
        # the last command in the line is the one that decides what is the next map
        # in a case like : map oasago2; echo test; vstr nextmap6; vstr nextmap3
        # the parser will recursively look each last vstr var, and if it can't find a map, fallback to the last map command
        self.debug('Extracting nextmap name from: %s' % (data))
        nextmapregex = re.compile(r'.*("|;)\s*((?P<vstr>vstr (?P<vstrnextmap>[a-z0-9_]+))|(?P<map>map (?P<mapnextmap>[a-z0-9_]+)))', re.IGNORECASE)
        m = re.match(nextmapregex, data)
        if m:
            if m.group('map'):
                self.debug('Found nextmap: %s' % (m.group('mapnextmap')))
                return m.group('mapnextmap')
            elif m.group('vstr'):
                self.debug('Nextmap is redirecting to var: %s' % (m.group('vstrnextmap')))
                data = self.write(m.group('vstrnextmap'))
                result = self.findNextMap(data) # recursively dig into the vstr vars to find the last map called
                if result: # if a result was found in a deeper level, then we return it to the upper level, until we get back to the root level
                    return result
                else: # if none could be found, then try to find a map command in the current string
                    nextmapregex = re.compile(r'.*("|;)\s*(?P<map>map (?P<mapnextmap>[a-z0-9_]+))"', re.IGNORECASE)
                    m = re.match(nextmapregex, data)
                    if m.group('map'):
                        self.debug('Found nextmap: %s' % (m.group('mapnextmap')))
                        return m.group('mapnextmap')
                    else: # if none could be found, we go up a level by returning None (remember this is done recursively)
                        self.debug('No nextmap found in this string !')
                        return None
        else:
            self.debug('No nextmap found in this string !')
            return None

    def sync(self):
        plist = self.getPlayerList()
        mlist = {}

        for cid, c in plist.iteritems():
            client = self.clients.getByCID(cid)
            if client:
                if client.guid and c.has_key('guid'):
                    if client.guid == c['guid']:
                        # player matches
                        self.debug('in-sync %s == %s', client.guid, c['guid'])
                        mlist[str(cid)] = client
                    else:
                        self.debug('no-sync %s <> %s', client.guid, c['guid'])
                        client.disconnect()
                elif client.ip and c.has_key('ip'):
                    if client.ip == c['ip']:
                        # player matches
                        self.debug('in-sync %s == %s', client.ip, c['ip'])
                        mlist[str(cid)] = client
                    else:
                        self.debug('no-sync %s <> %s', client.ip, c['ip'])
                        client.disconnect()
                else:
                    self.debug('no-sync: no guid or ip found.')
        
        return mlist

    def connectClient(self, ccid):
        if self.PunkBuster:
            self.debug('Getting the (PunkBuster) Playerlist')
        else:
            self.debug('Getting the (status) Playerlist')
        players = self.getPlayerList()
        self.verbose('connectClient() = %s' % players)

        for cid, p in players.iteritems():
            #self.debug('cid: %s, ccid: %s, p: %s' %(cid, ccid, p))
            if int(cid) == int(ccid):
                self.debug('Client found in status/playerList')
                return p

    def newPlayer(self, cid, guid, name):
        if not self._counter.get(cid):
            self.verbose('newPlayer thread no longer needed, Key no longer available')
            return None
        if self._counter.get(cid) == 'Disconnected':
            self.debug('%s disconnected, removing from authentication queue' %name)
            self._counter.pop(cid)
            return None

        self.debug('newClient: %s, %s, %s' %(cid, guid, name))
        sp = self.connectClient(cid)

        if sp:
            ip = sp['ip']
            self.verbose('ip = %s' %ip)
            self._counter.pop(cid)
        elif self._counter[cid] > 10:
            self.debug('Couldn\'t Auth %s, giving up...' % name)
            self._counter.pop(cid)
            return None
        # Player is not in the status response (yet), retry
        else:
            self.debug('%s not yet fully connected, retrying...#:%s' %(name, self._counter[cid]))
            self._counter[cid] +=1
            t = threading.Timer(4, self.newPlayer, (cid, guid, name))
            t.start()
            return None
            
        client = self.clients.newClient(cid, name=name, ip=ip, state=b3.STATE_ALIVE, guid=guid, data={ 'guid' : guid })

#---- Documentation --------------------------------------------------------------------------------
"""

//infos clienuserinfochanged
//0 = player_ID
//n = name
//t = team
//c = class
//r = rank
//m = medals
//s = skills
//dn = disguised name
//dr = disguised rank
//w = weapon
//lw = weapon last used
//sw = 2nd weapon (not sure)
//mu = muted
//ref = referee
//lw = latched weapon (weapon on next spawn)
//sw = latched secondary weapon (secondary weapon on next spawn)
//p = privilege level (peon = 0, referee (vote), referee (password), semiadmin, rconauth) (etpro only)
//ss = stats restored by stat saver (etpro only)
//sc = shoutcaster status (etpro only)
//tv = ETTV slave (etpro only)

"""