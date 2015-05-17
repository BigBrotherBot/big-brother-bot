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
# 11/30/2008 - 1.0.1 - xlr8or    - on_kill, kill modes and XLRstats compatibility
# 31/01/2010 - 1.0.2 - Courgette - get_map() is now inherited from q3a
# 09/04/2011 - 1.0.3 - Courgette - reflect that cid are not converted to int anymore in the clients module
# 14/01/2014 - 1.1   - Fenix     - PEP8 coding standards
#                                - correctly set the client bot flag upon new client connection
# 02/05/2014 - 1.2   - Fenix     - correctly initialize variable before referencing
# 30/07/2014 - 1.3   - Fenix     - fixes for the new getWrap implementation
# 11/08/2014 - 1.4   - Fenix     - syntax cleanup
#                                - make use of self.getEvent when producing events
#                                - fixed unresolved reference MOD_CHANGE_TEAM in OnKill()
# 16/04/2015 - 1.5   - Fenix     - uniform class variables (dict -> variable)
#                                - implement missing abstract class methods

__author__ = 'xlr8or'
__version__ = '1.5'

import re
import string
import b3
import b3.events
import b3.parsers.punkbuster

from b3.parsers.q3a.abstractParser import AbstractParser


class WopParser(AbstractParser):

    gameName = 'wop'
    privateMsg = False
    PunkBuster = None

    _clientConnectID = None
    _clientConnectGuid = None
    _clientConnectIp = None

    _line_length = 65
    _line_color_prefix = ''

    _commands = {
        'message': '%(message)s',
        'say': 'say %(message)s',
        'set': 'set %(name)s "%(value)s"',
        'kick': 'clientkick %(cid)s',
        'ban': 'addip %(cid)s',
        'tempban': 'clientkick %(cid)s',
    }

    _eventmap = {
        #'warmup': b3.events.EVT_GAME_WARMUP,
        #'shutdowngame': b3.events.EVT_GAME_ROUND_END
    }

    # remove the time off of the line
    _lineClear = re.compile(r'^(?:[0-9:]+\s?)?')

    _lineFormats = (
        # Generated with : WOP version 1.2
        # ClientConnect: 2 77F303414E4355E0860B483F2A07E4DF 151.16.71.226:27960
        re.compile(r'^(?P<action>[a-z]+):\s'
                   r'(?P<data>'
                   r'(?P<cid>[0-9]+)\s'
                   r'(?P<cl_guid>[0-9A-Z]{32})\s+'
                   r'(?P<ip>[0-9.]+):'
                   r'(?P<port>[0-9]+))$', re.IGNORECASE),

        # Kill: 3 2 8: Beinchen killed linux suse 10.3 by MOD_PLASMA
        re.compile(r'^(?P<action>[a-z]+):\s*'
                   r'(?P<data>'
                   r'(?P<acid>[0-9]+)\s'
                   r'(?P<cid>[0-9]+)\s'
                   r'(?P<aweap>[0-9]+):\s*'
                   r'(?P<text>.*))$', re.IGNORECASE),

        # ClientConnect: 2  151.16.71.226:27960
        re.compile(r'^(?P<action>[a-z]+):\s'
                   r'(?P<data>'
                   r'(?P<cid>[0-9]+)\s+'
                   r'(?P<ip>[0-9.]+):'
                   r'(?P<port>[0-9]+))$', re.IGNORECASE),

        # say: ^3Ghost^2Pirate: Saw red huh?
        re.compile(r'^(?P<action>say):\s*'
                   r'(?P<data>'
                   r'(?P<name>[^:]+):\s*'
                   r'(?P<text>.*))$', re.IGNORECASE),

        # Bot connecting
        # ClientConnect: 0
        re.compile(r'^(?P<action>ClientConnect):\s*'
                   r'(?P<data>(?P<bcid>[0-9]+))$', re.IGNORECASE),

        # Falling thru? Item stuff and so forth... still need some other actions from CTF and other gametypes to compare
        # Item: 3 ammo_spray_n
        re.compile(r'^(?P<action>[a-z]+):\s*(?P<data>.*)$', re.IGNORECASE)
    )
    
    # status
    # map: wop_huette
    # num score ping name            lastmsg address               qport rate
    # --- ----- ---- --------------- ------- --------------------- ----- -----
    #   1    34    0 ^1B^2io^1P^2ad      100 bot                       0 16384
    #   2    29    0 ^5Pad^1Lill y        50 bot                      53 16384
    #   3     5  103 PadPlayer             0 77.41.107.169:27960   47612  5000
    #   4   154   50 WARR                 50 91.127.64.194:27960   39880 25000

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

    MOD_UNKNOWN = '0'
    MOD_SHOTGUN = '1'
    MOD_GAUNTLET = '2'
    MOD_MACHINEGUN = '3'
    MOD_GRENADE = '4'
    MOD_GRENADE_SPLASH = '5'
    MOD_ROCKET = '6'
    MOD_ROCKET_SPLASH = '7'
    MOD_PLASMA = '8'
    MOD_PLASMA_SPLASH = '9'
    MOD_RAILGUN = '10'
    MOD_LIGHTNING = '11'
    MOD_BFG = '12'
    MOD_BFG_SPLASH = '13'
    MOD_KILLERDUCKS = '14'
    MOD_WATER = '15'
    MOD_SLIME = '16'
    MOD_LAVA = '17'
    MOD_CRUSH = '18'
    MOD_TELEFRAG = '19'
    MOD_FALLING = '20'  # not used in wop
    MOD_SUICIDE = '21'
    MOD_TARGET_LASER = '22'  # not used in wop
    MOD_TRIGGER_HURT = '23'
    MOD_GRAPPLE = '24'  # not used in wop

    ####################################################################################################################
    #                                                                                                                  #
    #   PARSER INITIALIZATION                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    def startup(self):
        """
        Called after the parser is created before run().
        """
        self.clients.newClient('-1', guid='WORLD', name='World', hide=True, pbid='WORLD')
        if not self.config.has_option('server', 'punkbuster') or self.config.getboolean('server', 'punkbuster'):
            self.PunkBuster = b3.parsers.punkbuster.PunkBuster(self)

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
        else:
            self.verbose('Line did not match format: %s' % line)

    def parseUserInfo(self, info):
        """
        Parse an infostring.
        :param info: The infostring to be parsed.
        """
        # 3 n\Dr.Schraube\t\0\model\padman/padsoldier_red\hmodel\padman/padsoldier_red\c1\4\c2\1\hc\100\w\0\l\0\tt\...
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

        if 'cl_guid' in data and not 'pbid' in data:
            data['pbid'] = data['cl_guid']

        return data

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENT HANDLERS                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def OnClientconnect(self, action, data, match=None):
        # we get user info in two parts:
        # ClientConnect: 2 77F303414E4355E0860B483F2A07E4DF 151.16.71.226:27960
        # ClientUserinfoChanged: 2 n\^3Ghost^2Pirate\t\0\model\piratpad/ghostpirate_red\hmodel\piratpad...
        # we need to store the ClientConnect ID, the guid and IP for the next call to
        # Clientuserinfochanged only on initial connection

        try:
            # normal client connected
            self._clientConnectID = match.group('cid')
        except IndexError:

            try:
                # game bot identifier
                self._clientConnectID = match.group('bcid')
                self._clientConnectGuid = 'BOT' + str(match.group('bcid'))
                self._clientConnectIp = '0.0.0.0'
                self.bot('Bot connected!')
                return None
            except IndexError:
                self.error('Parser could not connect client')
                return None

        try:
            # if we have no cl_guid we'll use the ip instead.
            self._clientConnectGuid = match.group('cl_guid')
        except IndexError:
            self._clientConnectGuid = match.group('ip')

        self._clientConnectIp = match.group('ip')
        self.verbose('Client connected cid: %s, guid: %s, ip: %s' % (self._clientConnectID,
                                                                     self._clientConnectGuid,
                                                                     self._clientConnectIp))

    def OnClientuserinfochanged(self, action, data, match=None):
        client_id = None
        client = None
        if self._clientConnectID is not None:
            client_id = self._clientConnectID

        self._clientConnectID = None

        bclient = self.parseUserInfo(data)
        self.verbose('Parsed user info %s' % bclient)
        if bclient:
            client = self.clients.getByCID(bclient['cid'])
            if client_id:
                bclient['cl_guid'] = self._clientConnectGuid
                self._clientConnectGuid = None
                bclient['ip'] = self._clientConnectIp
                self._clientConnectIp = None
            
            if client:
                # update existing client
                bclient['cl_guid'] = client.guid 
                bclient['ip'] = client.ip
                for k, v in bclient.iteritems():
                    setattr(client, k, v)
            else:
                # make a new client
                bot = True if bclient['cl_guid'][:3] == 'BOT' else False
                client = self.clients.newClient(bclient['cid'], name=bclient['name'], ip=bclient['ip'],
                                                state=b3.STATE_ALIVE, guid=bclient['cl_guid'], bot=bot,
                                                data={'guid': bclient['cl_guid']})

        if client_id:
            return self.getEvent('EVT_CLIENT_JOIN', client=client)
        return None

    def OnClientdisconnect(self, action, data, match=None):
        client = self.clients.getByCID(data)
        if client: client.disconnect()
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

        self.verbose('current gametype: %s' % self.game.gameType)
        self.game.startRound()
        return self.getEvent('EVT_GAME_ROUND_START', self.game)

    def OnSay(self, action, data, match=None):
        # 3:59 say: XLR8or: general chat
        msg = string.split(data, ': ', 1)
        if not len(msg) == 2:
            return None

        client = self.clients.getByExactName(msg[0])
        if client:
            self.verbose('Client found: %s' % client.name)
            return self.getEvent('EVT_CLIENT_SAY', msg[1], client)
        else:
            self.verbose('No client found!')
            return None

    def OnSayteam(self, action, data, match=None):
        # 4:06 sayteam: XLR8or: teamchat
        msg = string.split(data, ': ', 1)
        if not len(msg) == 2:
            return None

        client = self.clients.getByExactName(msg[0])

        if client:
            self.verbose('Client found: %s' % client.name)
            return self.getEvent('EVT_CLIENT_TEAM_SAY', msg[1], client, client.team)
        else:
            self.verbose('No client found!')
            return None

    def OnKill(self, action, data, match=None):
        """
         0:   MOD_UNKNOWN, Unknown Means od Death, shouldn't occur at all
         1:   MOD_SHOTGUN, Pumper
         2:   MOD_GAUNTLET, Punchy
         3:   MOD_MACHINEGUN, Nipper
         4:   MOD_GRENADE, Balloony
         5:   MOD_GRENADE_SPLASH, Ballony Splashdamage
         6:   MOD_ROCKET, Betty
         7:   MOD_ROCKET_SPLASH, Betty Splashdamage
         8:   MOD_PLASMA, BubbleG
         9:   MOD_PLASMA_SPLASH, BubbleG Splashdamage
        10:   MOD_RAILGUN, Splasher
        11:   MOD_LIGHTNING, Boaster
        12:   MOD_BFG, Imperius
        13:   MOD_BFG_SPLASH, Imperius Splashdamage
        14:   MOD_KILLERDUCKS, Killerducks
        15:   MOD_WATER, Died in Water
        16:   MOD_SLIME, Died in Slime
        17:   MOD_LAVA, Died in Lava
        18:   MOD_CRUSH, Killed by a Mover
        19:   MOD_TELEFRAG, Killed by a Telefrag
        20:   MOD_FALLING, Died due to falling damage, but there is no falling damage in WoP
        21:   MOD_SUICIDE, Commited Suicide
        22:   MOD_TARGET_LASER, Killed by a laser, which don't exist in WoP
        23:   MOD_TRIGGER_HURT, Killed by a trigger_hurt
        24:   MOD_GRAPPLE, Killed by grapple, not used in WoP
        """
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
        if match.group('aweap') in (self.MOD_WATER, self.MOD_LAVA, self.MOD_FALLING, self.MOD_TRIGGER_HURT,):
            # those kills should be considered suicides
            self.debug('OnKill: water/lava/falling/trigger_hurt should be suicides')
            attacker = victim
        else:
            attacker = self.clients.getByCID(match.group('acid'))
        ## end fix attacker
          
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
            #FIXME: MOD_CHANGE_TEAM is undefined in WopParser class
            #if weapon == self.MOD_CHANGE_TEAM:
            #    # Do not pass a teamchange event here. That event is passed
            #    # shortly after the kill.
            #    self.verbose('Team Change Event Caught, exiting')
            #    return None
            #else:
            eventkey = 'EVT_CLIENT_SUICIDE'
        elif attacker.team != b3.TEAM_UNKNOWN and attacker.team == victim.team:
            eventkey = 'EVT_CLIENT_KILL_TEAM'

        # if not logging damage we need a general hitloc (for xlrstats)
        if not hasattr(victim, 'hitloc'):
            victim.hitloc = 'body'
        
        victim.state = b3.STATE_DEAD
        # need to pass some amount of damage for the teamkill plugin - 100 is a kill
        return self.getEvent(eventkey, (100, weapon, victim.hitloc, damagetype), attacker, victim)

    def OnItem(self, action, data, match=None):
        # Item: 5 weapon_betty
        cid, item = string.split(data, ' ', 1)
        client = self.clients.getByCID(cid)
        if client:
            return self.getEvent('EVT_CLIENT_ITEM_PICKUP', item, client)
        return None

    ####################################################################################################################
    #                                                                                                                  #
    #   OTHER METHODS                                                                                                  #
    #                                                                                                                  #
    ####################################################################################################################

    def defineGameType(self, gametype_int):
        """
        Translate the gametype to a readable format.
        """
        gametype = str(gametype_int)

        if gametype_int == '0':
            gametype = 'dm'
        elif gametype_int == '1':
            gametype = 'lvl'
        elif gametype_int == '2':
            gametype = 'sp'
        elif gametype_int == '3':
            gametype = 'syc-ffa'
        elif gametype_int == '4':
            gametype = 'lps'
        elif gametype_int == '5':
            gametype = 'tdm'
        elif gametype_int == '6':
            gametype = 'ctl'
        elif gametype_int == '7':
            gametype = 'syc-tp'
        elif gametype_int == '8':
            gametype = 'bb'

        return gametype

    ####################################################################################################################
    #                                                                                                                  #
    #   B3 PARSER INTERFACE IMPLEMENTATION                                                                             #
    #                                                                                                                  #
    ####################################################################################################################

    def getNextMap(self):
        pass