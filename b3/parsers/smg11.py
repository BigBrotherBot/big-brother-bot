#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2010 Thomas LEVEIL <courgette@bigbrotherbot.net>
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
# 01/02/2010 - 0.2   - Courgette - fix _regplayer regex for SGv1.1b4
#                                - discover clients at bot start
#                                - make use of dumpuser to get a player's ip
#                                - don't lower() guid
# 06/02/2010 - 0.3   - Courgette - enable private messaging with the new /tell command
#                                - fix ban command
# 06/02/2010 - 0.4   - Courgette - parser recognizes damage lines (when enabled in config with : set g_debugDamage "1")
# 04/03/2010 - 0.5   - Courgette - on_clientuserinfo -> on_clientuserinfochanged
# 06/03/2010 - 0.6   - Courgette - make sure bots are bots on client connection
#                                - auth client by making use of dumpuser whenever needed
#                                - add custom handling of OnItem action
#                                - add the money property to clients that holds the amount of money a player has
# 07/03/2010 - 0.7   - Courgette - when players buy stuff or pickup money, EVT_CLIENT_ITEM_PICKUP events are replaced by
#                                  two SG specific new events : EVT_CLIENT_GAIN_MONEY and EVT_CLIENT_SPEND_MONEY
#                                  Those events help keeping track of money flows and should give plugin developers.
#                                  a lot of freedom
# 07/03/2010 - 0.8   - Courgette - fix bug introduced in 0.6 which messed up clients cid as soon as they are chatting...
# 08/03/2010 - 0.9   - Courgette - should fix the bot's team issue
# 15/09/2010 - 0.9.1 - GrosBedo  - added !nextmap and !maps support
# 13/01/2014 - 0.9.2 - Fenix     - PEP8 coding standards
#                                - changed bots guid syntax to match other q3a parsers (BOT<slot>)
#                                - correctly set client bot flag upon new client connection
# 30/07/2014 - 0.9.3 - Fenix     - fixes for the new getWrap implementation
# 11/08/2014 - 0.9.4 - Fenix     - syntax cleanup
#                                - make use of self.getEvent() when producing events
#                                - fixed current mapname retrieval
# 19/03/2015 - 0.9.5 - Fenix     - removed deprecated usage of dict.has_key (us 'in dict' instead)
# 16/04/2015 - 0.9.6 - Fenix     - uniform class variables (dict -> variable)

__author__ = 'xlr8or, Courgette'
__version__ = '0.9.6'

import re
import string
import b3
import b3.events
import b3.parsers.punkbuster

from b3.parsers.q3a.abstractParser import AbstractParser


class Smg11Parser(AbstractParser):

    gameName = 'smg'
    PunkBuster = None

    _empty_name_default = 'EmptyNameDefault'
    _connectingSlots = []
    _logSync = 1
    _maplist = None
    
    _line_length = 65
    _line_color_prefix = ''

    _commands = {
        'message': 'tell %(cid)s %(message)s',
        'say': 'say %(message)s',
        'set': 'set %(name)s "%(value)s"',
        'kick': 'clientkick %(cid)s',
        'ban': 'banClient %(cid)s',
        'tempban': 'clientkick %(cid)s',
    }

    _eventmap = {
        #'warmup': b3.events.EVT_GAME_WARMUP,
        #'restartgame': b3.events.EVT_GAME_ROUND_END
    }

    # remove the time off of the line
    _lineClear = re.compile(r'^(?:[0-9:.]+\s?)?')

    _lineFormats = (
        # 468950: client:0 health:90 damage:21.6 where:arm from:MOD_SCHOFIELD by:2
        re.compile(r'^\d+:\s+'
                   r'(?P<data>client:'
                   r'(?P<cid>\d+)\s+health:'
                   r'(?P<health>\d+)\s+damage:'
                   r'(?P<damage>[.\d]+)\s+where:'
                   r'(?P<hitloc>[^\s]+)\s+from:'
                   r'(?P<aweap>[^\s]+)\s+by:'
                   r'(?P<acid>\d+))$', re.IGNORECASE),

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

        re.compile(r'^(?P<action>[a-z]+):\s*(?P<data>(?P<cid>[0-9]+):\s*(?P<text>.*))$', re.IGNORECASE),
        re.compile(r'^(?P<action>[a-z]+):\s*(?P<data>(?P<cid>[0-9]+)\s(?P<text>.*))$', re.IGNORECASE),

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
                            r'(?P<ip>[0-9.]+)\s+'
                            r'(?P<qport>[0-9]+)\s+'
                            r'(?P<rate>[0-9]+)$', re.IGNORECASE)

    _reColor = re.compile(r'(\^.)|[\x00-\x20]|[\x7E-\xff]')

    ## kill mode constants: modNames[meansOfDeath]
    MOD_UNKNOWN = '0'
    # melee
    MOD_KNIFE = '1'
    # pistols
    MOD_REM58 = '2'
    MOD_SCHOFIELD = '3'
    MOD_PEACEMAKER = '4'
    # rifles
    MOD_WINCHESTER66 = '5'
    MOD_LIGHTNING = '6'
    MOD_SHARPS = '7'
    # shotguns
    MOD_REMINGTON_GAUGE = '8'
    MOD_SAWEDOFF = '9'
    MOD_WINCH97 = '10'
    # automatics
    MOD_GATLING = '11'
    # explosives
    MOD_DYNAMITE = '12'
    MOD_MOLOTOV = '13'
    # misc
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
        # add SG specific events
        self.Events.createEvent('EVT_CLIENT_GAIN_MONEY', 'Client gain money')
        self.Events.createEvent('EVT_CLIENT_SPEND_MONEY', 'Client spend money')

        # add the world client
        self.clients.newClient('1022', guid='WORLD', name='World', hide=True, pbid='WORLD')

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

        # initialize connected clients
        self.info('Discover connected clients')
        plist = self.getPlayerList()
        for cid, c in plist.iteritems():
            userinfostring = self.queryClientUserInfoByCid(cid)
            if userinfostring:
                self.OnClientuserinfochanged(None, userinfostring)

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
                #self.debug('XLR--------> line matched %s' % f.pattern)
                break
        if m:
            client = None
            target = None
            
            try:
                action = m.group('action').lower()
            except IndexError:
                # special case for damage lines where no action group can be set
                action = 'damage'
            
            return m, action, m.group('data').strip(), client, target

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

        t = 0
        if 'team' in data:
            t = data['team']
        elif 't' in data:
            t = data['t']

        data['team'] = self.getTeam(t)

        if 'cl_guid' in data:
            data['guid'] = data['cl_guid']

        if 'guid' in data:
            data['guid'] = data['guid']

        return data

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENT HANDLERS                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def OnClientconnect(self, action, data, match=None):
        #self._clientConnectID = data
        client = self.clients.getByCID(data)
        self.debug('OnClientConnect: %s, %s' % (data, client))
        return self.getEvent('EVT_CLIENT_JOIN', client=client)

    def OnClientuserinfochanged(self, action, data, match=None):
        bclient = self.parseUserInfo(data)
        self.verbose('Parsed user info: %s' % bclient)
        if bclient:
            cid = bclient['cid']
            if cid in self._connectingSlots:
                self.debug('Client on slot %s is already being connected' % cid)
                return
            
            self._connectingSlots.append(cid)
            client = self.clients.getByCID(cid)

            if client:
                # update existing client
                for k, v in bclient.iteritems():
                    setattr(client, k, v)
            else:
                if 'name' not in bclient:
                    bclient['name'] = self._empty_name_default

                if 'team' not in bclient:
                    bclient['team'] = self.getTeam(bclient['team'])

                if 'guid' in bclient:
                    guid = bclient['guid']
                else:
                    if 'skill' in bclient:
                        guid = 'BOT' + str(cid)
                        self.verbose('Bot connected!')
                        self.clients.newClient(cid, name=bclient['name'], ip='0.0.0.0', state=b3.STATE_ALIVE,
                                               guid=guid, data={'guid': guid}, bot=True, money=20)
                    else:
                        self.warning('Cannot connect player because he has no guid and is not a bot either')

                    self._connectingSlots.remove(cid)
                    return None
                
                if 'ip' not in bclient:
                    infoclient = self.parseUserInfo(self.queryClientUserInfoByCid(cid))
                    if 'ip' in infoclient:
                        bclient['ip'] = infoclient['ip']
                    else:
                        self.warning('Failed to get client ip')
                
                if 'ip' in bclient:
                    self.clients.newClient(cid, name=bclient['name'], ip=bclient['ip'],
                                           state=b3.STATE_ALIVE, guid=guid, data={'guid': guid},
                                           bot=False, money=20)
                else:
                    self.warning('Failed to get connect client')
                    
            self._connectingSlots.remove(cid)
                
        return None

    def OnKill(self, action, data, match=None):
        self.debug('OnKill: %s (%s)' % (match.group('aweap'), match.group('text')))
        victim = self.getByCidOrJoinPlayer(match.group('cid'))
        if not victim:
            self.debug('No victim')
            #self.OnClientuserinfochanged(action, data, match)
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
            attacker = self.getByCidOrJoinPlayer(match.group('acid'))
        ## End fix attacker
          
        if not attacker:
            self.debug('No attacker')
            return None

        damagetype = match.group('text').split()[-1:][0]
        if not damagetype:
            self.debug('No damage type, weapon: %s' % weapon)
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
        self.debug('OnInitgame: %s' % data)
        options = re.findall(r'\\([^\\]+)\\([^\\]+)', data)
        for o in options:
            if o[0] == 'mapname':
                self.game.mapName = o[1]
            elif o[0] == 'g_gametype':
                self.game.gameType = self.defineGameType(o[1])
            elif o[0] == 'fs_game':
                self.game.modName = o[1]
            else:
                #self.debug('%s = %s' % (o[0],o[1]))
                setattr(self.game, o[0], o[1])

        self.verbose('...self.console.game.gameType: %s' % self.game.gameType)
        self.game.startRound()
        self.debug('Synchronizing client info')
        self.clients.sync()

        return self.getEvent('EVT_GAME_ROUND_START', self.game)

    def OnSayteam(self, action, data, match=None):
        # teaminfo does not exist in the sayteam logline.
        # parse it as a normal say line
        return self.OnSay(action, data, match)

    def OnItem(self, action, data, match=None):
        # Item: 0 pickup_money (5) picked up ($25)
        # Item: 0 weapon_schofield bought ($18/$20)
        # Item: 0 weapon_remington58 (7) picked up
        cid, item = string.split(data, ' ', 1)
        client = self.getByCidOrJoinPlayer(cid)
        if client:
            if 'pickup_money' in item:
                re_pickup_money = re.compile(r"^pickup_money \((?P<amount>\d+)\) picked up \(\$(?P<totalmoney>\d+)\)$")
                m = re_pickup_money.search(item)
                if m is not None:
                    amount = m.group('amount')
                    totalmoney = m.group('totalmoney')
                    setattr(client, 'money', int(totalmoney))
                    self.verbose('%s has now $%s' % (client.name, client.money))
                    return self.getEvent('EVT_CLIENT_GAIN_MONEY', {'amount': amount, 'totalmoney': totalmoney}, client)

            if 'bought' in item:
                re_bought = re.compile(r"^(?P<item>.+) bought \(\$(?P<cost>\d+)/\$(?P<totalmoney>\d+)\)$")
                m = re_bought.search(item)
                if m is not None:
                    what = m.group('item')
                    cost = m.group('cost')
                    totalmoney = m.group('totalmoney')
                    if cost is not None and totalmoney is not None:
                        setattr(client, 'money', int(totalmoney) - int(cost))
                        self.verbose('%s has now $%s' % (client.name, client.money))
                        return self.getEvent('EVT_CLIENT_SPEND_MONEY', {'item': what,
                                                                         'cost': cost,
                                                                         'totalmoney': client.money}, client)

            return self.getEvent('EVT_CLIENT_ITEM_PICKUP', item, client)

        return None

    def OnDamage(self, action, data, match=None):
        victim = self.clients.getByCID(match.group('cid'))
        if not victim:
            self.debug('No victim')
            return None

        attacker = self.clients.getByCID(match.group('acid'))
        if not attacker:
            self.debug('No attacker')
            return None

        eventkey = 'EVT_CLIENT_DAMAGE'
        if attacker.cid == victim.cid:
            eventkey = 'EVT_CLIENT_DAMAGE_SELF'
        elif attacker.team != b3.TEAM_UNKNOWN and attacker.team == victim.team:
            eventkey = 'EVT_CLIENT_DAMAGE_TEAM'

        victim.hitloc = match.group('hitloc')
        damagepoints = round(float(match.group('damage')), 1)
        return self.getEvent(eventkey, (damagepoints, match.group('aweap'), victim.hitloc), attacker, victim)

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
        self.debug('Extracting nextmap name from: %s' % data)
        nextmapregex = re.compile(r'.*("|;)\s*('
                                  r'(?P<vstr>vstr (?P<vstrnextmap>[a-z0-9_]+))|'
                                  r'(?P<map>map (?P<mapnextmap>[a-z0-9_]+)))', re.IGNORECASE)
        m = re.match(nextmapregex, data)
        if m:
            if m.group('map'):
                self.debug('Found nextmap: %s' % (m.group('mapnextmap')))
                return m.group('mapnextmap')
            elif m.group('vstr'):
                self.debug('Nextmap is redirecting to var: %s' % (m.group('vstrnextmap')))
                data = self.write(m.group('vstrnextmap'))
                result = self.findNextMap(data)  # recursively dig into the vstr vars to find the last map called
                if result:
                    # if a result was found in a deeper level,
                    # then we return it to the upper level,
                    # until we get back to the root level
                    return result
                else:
                    # if none could be found, then try to find a map command in the current string
                    nextmapregex = re.compile(r'.*("|;)\s*(?P<map>map (?P<mapnextmap>[a-z0-9_]+))"', re.IGNORECASE)
                    m = re.match(nextmapregex, data)
                    if m.group('map'):
                        self.debug('Found nextmap: %s' % (m.group('mapnextmap')))
                        return m.group('mapnextmap')
                    else:
                    # if none could be found, we go up a level by returning None (remember this is done recursively)
                        self.debug('No nextmap found in this string')
                        return None
        else:
            self.debug('No nextmap found in this string')
            return None

    def connectClient(self, ccid):
        s = 'status'
        if self.PunkBuster:
            s = 'punkbuster'

        self.debug('Getting the (%s) playerlist' % s)
        players = self.getPlayerList()
        self.verbose('connectClient() = %s' % players)

        for cid, p in players.iteritems():
            #self.debug('cid: %s, ccid: %s, p: %s' %(cid, ccid, p))
            if int(cid) == int(ccid):
                self.debug('Client found in status/playerList')
                return p

    def getByCidOrJoinPlayer(self, cid):
        client = self.clients.getByCID(cid)
        if client:
            return client
        else:
            userinfostring = self.queryClientUserInfoByCid(cid)
            if userinfostring:
                self.OnClientuserinfochanged(None, userinfostring)
            return self.clients.getByCID(cid)

    def queryClientUserInfoByCid(self, cid):
        """
        : dumpuser 5
        Player 5 is not on the server

        : dumpuser 0
        userinfo
        --------
        name                Courgette
        ip                  11.222.111.33
        rate                25000
        snaps               20
        model               wq_male3/red
        handicap            100
        sex                 male
        cg_predictItems     1
        team_model          wq_male1
        cl_voip             1
        cg_cmdTimeNudge     0
        cg_delag            1
        g_blueTeam          Outlaws
        g_redTeam           Lawmen
        team_headmodel      *james
        headmodel           sarge
        teamtask            0
        cl_version          1.1b4 20100116
        cl_md5              9F1646464ADFA64A654A6546546465E9
        sa_engine_check1    7B135FE5ACACACACAAC4656546546543
        cl_guid             0F4E000FFF0FFC00000ACCDE0000FF8A
        ui_singlePlayerActive0
        sa_engine_in_use    1
        teamoverlay         1
        cg_debugDelag       0
        cg_latentSnaps      0
        cg_latentCmds       0
        cg_plOut            0
        """
        data = self.write('dumpuser %s' % cid)
        if not data:
            return None

        if data.split('\n')[0] != "userinfo":
            self.debug("Dumpuser %s returned : %s" % (cid, data))
            return None

        datatransformed = "%s " % cid
        for line in data.split('\n'):
            if line.strip() == "userinfo" or line.strip() == "--------":
                continue

            var = line[:20].strip()
            val = line[20:].strip()
            datatransformed += "\\%s\\%s" % (var, val)

        return datatransformed

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
            client = self.getByCidOrJoinPlayer(cid)
            if client:
                if client.guid and 'guid' in c():
                    if client.guid == c['guid']:
                        # player matches
                        self.debug('in-sync %s == %s', client.guid, c['guid'])
                        mlist[str(cid)] = client
                    else:
                        self.debug('no-sync %s <> %s', client.guid, c['guid'])
                        client.disconnect()
                elif client.ip and 'ip' in c():
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