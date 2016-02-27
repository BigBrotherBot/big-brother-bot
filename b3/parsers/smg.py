#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2005 Michael "ThorN" Thornton
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
#
# CHANGELOG
#
# 31/01/2010 - 0.1   - Courgette - use the new /cp command to send private messages (requires SmokinGuns v1.1)
# 31/01/2010 - 0.1.1 - Courgette - get_map() is now inherited from q3a
# 06/02/2010 - 0.1.2 - Courgette - do not use cp/bigtext for private messaging to make this parser compatible with
#                                  SG pior to v1.1
#                                - fix the ban command
# 15/09/2010 - 0.1.3 - GrosBedo  - added !nextmap and !maps support
# 09/04/2011 - 0.1.4 - Courgette - reflect that cid are not converted to int anymore in the clients module
# 13/01/2014 - 0.1.5 - Fenix     - PEP8 coding standards
#                                - changed bots guid to match other q3a parsers (BOT<slot>)
#                                - correctly set client bot flag upon new client connection
# 30/07/2014 - 0.1.6 - Fenix     - fixes for the new getWrap implementation
# 11/08/2014 - 0.1.7 - Fenix     - syntax cleanup
#                                - make use of self.getEvent() when producing events
# 16/04/2015 - 0.1.8 - Fenix     - uniform class variables (dict -> variable)

__author__ = 'xlr8or, Courgette'
__version__ = '0.1.8'

import b3
import b3.events
import b3.parsers.punkbuster
import re
import string
import threading

from b3.parsers.q3a.abstractParser import AbstractParser


class SmgParser(AbstractParser):

    gameName = 'smg'
    PunkBuster = None

    _counter = {}
    _empty_name_default = 'EmptyNameDefault'
    _logSync = 1
    _maplist = None

    _clientConnectID = None
    _clientConnectGuid = None
    _clientConnectIp = None

    _line_length = 65
    _line_color_prefix = ''

    _commands = {
        'message': '%(cid)s %(message)s',
        'say': 'say %(message)s',
        'set': 'set %(name)s "%(value)s"',
        'kick': 'clientkick %(cid)s',
        'ban': 'banClient %(cid)s',
        'tempban': 'clientkick %(cid)s',
    }

    _eventMap = {
        #'warmup': b3.events.EVT_GAME_WARMUP,
        #'restartgame': b3.events.EVT_GAME_ROUND_END
    }

    # remove the time off of the line
    _lineClear = re.compile(r'^(?:[0-9:.]+\s?)?')

    _lineFormats = (
        re.compile(r'^(?P<action>[a-z]+):\s*'
                   r'(?P<data>'
                   r'(?P<cid>[0-9]+):\s*'
                   r'(?P<pbid>[0-9A-Z]{32}):\s*'
                   r'(?P<name>[^:]+):\s*'
                   r'(?P<num1>[0-9]+):\s*'
                   r'(?P<num2>[0-9]+):\s*'
                   r'(?P<ip>[0-9.]+):'
                   r'(?P<port>[0-9]+))$', re.IGNORECASE),

        re.compile(r'^(?P<action>[a-z]+):\s*'
                   r'(?P<data>'
                   r'(?P<cid>[0-9]+):\s*'
                   r'(?P<name>.+):\s+'
                   r'(?P<text>.*))$', re.IGNORECASE),

        # 1536:37Kill: 1 18 9: ^1klaus killed ^1[pura]fox.nl by MOD_MP40
        re.compile(r'^(?P<action>[a-z]+):\s*'
                   r'(?P<data>'
                   r'(?P<acid>[0-9]+)\s'
                   r'(?P<cid>[0-9]+)\s'
                   r'(?P<aweap>[0-9]+):\s*'
                   r'(?P<text>.*))$', re.IGNORECASE),

        re.compile(r'^(?P<action>[a-z]+):\s*'
                   r'(?P<data>'
                   r'(?P<cid>[0-9]+):\s*'
                   r'(?P<text>.*))$', re.IGNORECASE),

        re.compile(r'^(?P<action>[a-z]+):\s*'
                   r'(?P<data>'
                   r'(?P<cid>[0-9]+)\s'
                   r'(?P<text>.*))$', re.IGNORECASE),

        # Falling through?
        # 1:05 ClientConnect: 3
        # 1:05 ClientUserinfoChanged: 3 guid\CAB616192CB5652375401264987A23D0\n\xlr8or\t\0\model\wq_male2/red...
        re.compile(r'^(?P<action>[a-z_]+):\s*(?P<data>.*)$', re.IGNORECASE)
    )

    # map: dm_fort
    # num score ping name            lastmsg address               qport rate
    # --- ----- ---- --------------- ------- --------------------- ----- -----
    #   1     1    0 TheMexican^7        100 bot                       0 16384
    #   2     1    0 Sentenza^7           50 bot                       0 16384
    #   3     3   37 xlr8or^7              0 145.99.135.227:27960   3598 25000
    _regPlayer = re.compile(r'^(?P<slot>[0-9]+)\s+'
                            r'(?P<score>[0-9-]+)\s+'
                            r'(?P<ping>[0-9]+)\s+'
                            r'(?P<name>.*?)\s+'
                            r'(?P<last>[0-9]+)\s+'
                            r'(?P<ip>[0-9.]+):'
                            r'(?P<port>[0-9-]+)\s+'
                            r'(?P<qport>[0-9]+)\s+'
                            r'(?P<rate>[0-9]+)$', re.IGNORECASE)
    
    _reColor = re.compile(r'(\^.)|[\x00-\x20]|[\x7E-\xff]')



    ## kill mode constants: modNames[meansOfDeath]
    MOD_UNKNOWN = '0'
    #melee
    MOD_KNIFE = '1'
    #pistols
    MOD_REM58 = '2'
    MOD_SCHOFIELD = '3'
    MOD_PEACEMAKER = '4'
    #rifles
    MOD_WINCHESTER66 = '5'
    MOD_LIGHTNING = '6'
    MOD_SHARPS = '7'
    #shotguns
    MOD_REMINGTON_GAUGE = '8'
    MOD_SAWEDOFF = '9'
    MOD_WINCH97 = '10'
    #automatics
    MOD_GATLING = '11'
    #explosives
    MOD_DYNAMITE = '12'
    MOD_MOLOTOV = '13'
    #misc
    MOD_WATER = '14'
    MOD_SLIME = '15'
    MOD_LAVA = '16'
    MOD_CRUSH = '17'
    MOD_TELEFRAG = '18'
    MOD_FALLING = '19'
    MOD_SUICIDE = '20'
    MOD_WORLD_DAMAGE = '21'
    MOD_TRIGGER_HURT = '22'
    MOD_NAIL = '23'
    MOD_CHAINGUN = '24'
    MOD_PROXIMITY_MINE = '25'
    MOD_BOILER = '26'

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

    ####################################################################################################################
    #                                                                                                                  #
    #   PARSER INITIALIZATION                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    def startup(self):
        """
        Called after the parser is created before run().
        """
        # add the world client
        self.clients.newClient('-1', guid='WORLD', name='World', hide=True, pbid='WORLD')

        self._eventMap['warmup'] = self.getEventID('EVT_GAME_WARMUP')
        self._eventMap['restartgame'] = self.getEventID('EVT_GAME_ROUND_END')

        # force g_logsync
        self.debug('Forcing server cvar g_logsync to %s' % self._logSync)
        self.setCvar('g_logsync', self._logSync)

        # get map from the status rcon command
        mapname = self.getMap()
        if mapname:
            self.game.mapName = mapname
            self.info('map is: %s' % self.game.mapName)

    ####################################################################################################################
    #                                                                                                                  #
    #   PARSING                                                                                                        #
    #                                                                                                                  #
    ####################################################################################################################

    def getLineParts(self, line):
        """
        Parse a log line returning extracted tokens.
        :param line: The line to be parsed
        """
        line = re.sub(self._lineClear, '', line, 1)
        m = None
        for f in self._lineFormats:
            m = re.match(f, line)
            if m:
                break
        if m:
            client = None
            target = None
            return m, m.group('action').lower(), m.group('data').strip(), client, target
        elif '------' not in line:
            self.verbose('XLR--------> line did not match format: %s' % line)

    def parseUserInfo(self, info):
        """
        Parse an infostring.
        :param info: The infostring to be parsed.
        """
        player_id, info = string.split(info, ' ', 1)
        if info[:1] != '\\':
            info += '\\'

        options = re.findall(r'\\([^\\]+)\\([^\\]+)', info)

        data = dict()
        for o in options:
            data[o[0]] = o[1]

        data['cid'] = player_id

        if 'n' in data:
            data['name'] = data['n']

        # split port from ip field
        if 'ip' in data:
            tip = string.split(data['ip'], ':', 1)
            data['ip'] = tip[0]
            data['port'] = tip[1]

        t = 0
        if 'team' in data:
            t = data['team']
        elif 't' in data:
            t = data['t']

        data['team'] = self.getTeam(t)
        if 'cl_guid' in data:
            data['cl_guid'] = data['cl_guid'].lower()

        if 'pbid' in data:
            data['pbid'] = data['pbid'].lower()

        if 'cl_guid' in data and not 'pbid' in data:
            data['pbid'] = data['cl_guid']

        return data

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENT HANDLERS                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def OnClientconnect(self, action, data, match=None):
        self._clientConnectID = data
        client = self.clients.getByCID(data)
        return self.getEvent('EVT_CLIENT_JOIN', client=client)

    def OnClientuserinfo(self, action, data, match=None):
        bclient = self.parseUserInfo(data)
        self.verbose('Parsed user info: %s' % bclient)
        if bclient:
            cid = bclient['cid']
            client = self.clients.getByCID(cid)

            if client:
                # update existing client
                for k, v in bclient.iteritems():
                    setattr(client, k, v)
            else:
                if not 'name' in bclient:
                    bclient['name'] = self._empty_name_default

                if 'guid' in bclient:
                    guid = bclient['guid']
                else:
                    guid = 'BOT' + str(cid)
                    self.verbose('bot connected!')
                    self.clients.newClient(cid, name=bclient['name'], ip='0.0.0.0',
                                           state=b3.STATE_ALIVE, guid=guid, bot=True,
                                           data={'guid': guid})
                    return None

                self._counter[cid] = 1
                t = threading.Timer(2, self.newPlayer, (cid, guid, bclient['name']))
                t.start()
                self.debug('%s connected, waiting for authentication...' % bclient['name'])
                self.debug('our authentication queue: %s' % str(self._counter))

        return None

    def OnKill(self, action, data, match=None):
        self.debug('OnKill: %s (%s)' % (match.group('aweap'), match.group('text')))
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
            self.debug('OnKill: fixed attacker, suicide detected: %s' % match.group('text'))
            attacker = victim
        else:
            attacker = self.clients.getByCID(match.group('acid'))
        ## end fix attacker
          
        if not attacker:
            self.debug('No attacker')
            return None

        damagetype = match.group('text').split()[-1:][0]
        if not damagetype:
            self.debug('no damage type, weapon: %s' % weapon)
            return None

        eventkey = 'EVT_CLIENT_KILL'
        # fix event for team change and suicides and tk
        if attacker.cid == victim.cid:
            eventkey = 'EVT_CLIENT_SUICIDE'
        elif attacker.team != b3.TEAM_UNKNOWN and attacker.team == victim.team:
            eventkey = 'EVT_CLIENT_KILL_TEAM'

        # if not defined we need a general hitloc (for xlrstats)
        if not hasattr(victim, 'hitloc'):
            victim.hitloc = 'body'
        
        victim.state = b3.STATE_DEAD
        # need to pass some amount of damage for the teamkill plugin - 100 is a kill
        return self.getEvent(eventkey, (100, weapon, victim.hitloc, damagetype), attacker, victim)

    def OnClientdisconnect(self, action, data, match=None):
        client = self.clients.getByCID(data)
        if client:
            client.disconnect()
        return None

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
        self.debug('synchronizing client info')
        self.clients.sync()

        return self.getEvent('EVT_GAME_ROUND_START', self.game)

    def OnSayteam(self, action, data, match=None):
        # teaminfo does not exist in the sayteam logline.
        # parse it as a normal say line
        return self.OnSay(action, data, match)

    ####################################################################################################################
    #                                                                                                                  #
    #   OTHER METHODS                                                                                                  #
    #                                                                                                                  #
    ####################################################################################################################

    def getTeam(self, team):
        """
        Return a B3 team given the team value.
        :param team: The team value
        """
        if team == 'red':
            team = 1
        if team == 'blue':
            team = 2

        team = int(team)
        if team == 1:
            return b3.TEAM_RED
        elif team == 2:
            return b3.TEAM_BLUE
        elif team == 3:
            return b3.TEAM_SPEC
        else:
            return b3.TEAM_UNKNOWN

    def defineGameType(self, gametype_int):
        """
        Translate the gametype to a readable format (also for teamkill plugin!).
        """
        gametype = str(gametype_int)

        if gametype_int == '0':
            gametype = 'dm'        # Deathmatch
        elif gametype_int == '1':
            gametype = 'du'        # Duel
        elif gametype_int == '3':
            gametype = 'tdm'       # Team Death Match
        elif gametype_int == '4':
            gametype = 'ts'        # Team Survivor (Round TDM)
        elif gametype_int == '5':
            gametype = 'br'        # Bank Robbery

        return gametype

    def findNextMap(self, data):
        # "nextmap" is: "vstr next4; echo test; vstr aupo3; map oasago2"
        # the last command in the line is the one that decides what is the next map
        # in a case like : map oasago2; echo test; vstr nextmap6; vstr nextmap3
        # the parser will recursively look each last vstr var, and if it can't find a map,
        # fallback to the last map command
        self.debug('extracting nextmap name from: %s' % data)
        nextmapregex = re.compile(r'.*("|;)\s*('
                                  r'(?P<vstr>vstr (?P<vstrnextmap>[a-z0-9_]+))|'
                                  r'(?P<map>map (?P<mapnextmap>[a-z0-9_]+)))', re.IGNORECASE)
        m = re.match(nextmapregex, data)
        if m:
            if m.group('map'):
                self.debug('found nextmap: %s' % (m.group('mapnextmap')))
                return m.group('mapnextmap')
            elif m.group('vstr'):
                self.debug('nextmap is redirecting to var: %s' % (m.group('vstrnextmap')))
                data = self.write(m.group('vstrnextmap'))
                result = self.findNextMap(data)  # recursively dig into the vstr vars to find the last map called
                if result:
                    # if a result was found in a deeper level, then we return it to the upper level,
                    # until we get back to the root level
                    return result
                else:
                    # if none could be found, then try to find a map command in the current string
                    nextmapregex = re.compile(r'.*("|;)\s*(?P<map>map (?P<mapnextmap>[a-z0-9_]+))"', re.IGNORECASE)
                    m = re.match(nextmapregex, data)
                    if m.group('map'):
                        self.debug('found nextmap: %s' % (m.group('mapnextmap')))
                        return m.group('mapnextmap')
                    else:
                        # if none could be found, we go up a level by returning None (remember this is done recursively)
                        self.debug('no nextmap found in this string')
                        return None
        else:
            self.debug('no nextmap found in this string')
            return None

    ####################################################################################################################
    #                                                                                                                  #
    #   B3 PARSER INTERFACE IMPLEMENTATION                                                                             #
    #                                                                                                                  #
    ####################################################################################################################

    def getMaps(self):
        """
        Return the available maps/levels name
        """
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
        """
        Return the next map/level name to be played.
        """
        data = self.write('nextmap')
        nextmap = self.findNextMap(data)
        if nextmap:
            return nextmap
        else:
            return 'no nextmap set or it is in an unrecognized format !'

    def sync(self):
        """
        For all connected players returned by self.get_player_list(), get the matching Client
        object from self.clients (with self.clients.get_by_cid(cid) or similar methods) and
        look for inconsistencies. If required call the client.disconnect() method to remove
        a client from self.clients.
        """
        plist = self.getPlayerList()
        mlist = dict()
        for cid, c in plist.iteritems():
            client = self.clients.getByCID(cid)
            if client:
                if client.guid and 'guid' in c:
                    if client.guid == c['guid']:
                        # player matches
                        self.debug('in-sync %s == %s', client.guid, c['guid'])
                        mlist[str(cid)] = client
                    else:
                        self.debug('no-sync %s <> %s', client.guid, c['guid'])
                        client.disconnect()
                elif client.ip and 'ip' in c:
                    if client.ip == c['ip']:
                        # player matches
                        self.debug('in-sync %s == %s', client.ip, c['ip'])
                        mlist[str(cid)] = client
                    else:
                        self.debug('no-sync %s <> %s', client.ip, c['ip'])
                        client.disconnect()
                else:
                    self.debug('no-sync: no guid or ip found')
        
        return mlist

    def connectClient(self, ccid):
        s = 'status'
        if self.PunkBuster:
            s = 'punkbuster'

        self.debug('getting the (%s) playerlist' % s)
        players = self.getPlayerList()
        self.verbose('connectClient() = %s' % players)

        for cid, p in players.iteritems():
            if int(cid) == int(ccid):
                self.debug('client found in status/playerList')
                return p

    def newPlayer(self, cid, guid, name):
        if not self._counter.get(cid):
            self.verbose('newPlayer thread no longer needed: key no longer available')
            return None
        if self._counter.get(cid) == 'Disconnected':
            self.debug('%s disconnected: removing from authentication queue' % name)
            self._counter.pop(cid)
            return None

        self.debug('newPlayer: %s, %s, %s' % (cid, guid, name))
        sp = self.connectClient(cid)

        if sp:
            ip = sp['ip']
            self.verbose('ip = %s' % ip)
            self._counter.pop(cid)
        elif self._counter[cid] > 10:
            self.debug('couldn not auth %s: giving up...' % name)
            self._counter.pop(cid)
            return None

        else:
            self.debug('%s not yet fully connected: retrying...#:%s' % (name, self._counter[cid]))
            self._counter[cid] += 1
            t = threading.Timer(4, self.newPlayer, (cid, guid, name))
            t.start()
            return None
            
        self.clients.newClient(cid, name=name, ip=ip, state=b3.STATE_ALIVE, guid=guid, bot=False, data={'guid': guid})

# ---- Documentation ---------------------------------------------------------------------------------------------------
# //infos clienuserinfochanged
# //0 = player_ID
# //n = name
# //t = team
# //c = class
# //r = rank
# //m = medals
# //s = skills
# //dn = disguised name
# //dr = disguised rank
# //w = weapon
# //lw = weapon last used
# //sw = 2nd weapon (not sure)
# //mu = muted
# //ref = referee
# //lw = latched weapon (weapon on next spawn)
# //sw = latched secondary weapon (secondary weapon on next spawn)
# //p = privilege level (peon = 0, referee (vote), referee (password), semiadmin, rconauth) (etpro only)
# //ss = stats restored by stat saver (etpro only)
# //sc = shoutcaster status (etpro only)
# //tv = ETTV slave (etpro only)