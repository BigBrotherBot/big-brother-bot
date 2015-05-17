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
# 2011-04-04 - 1.1.0 - Courgette - remove inheritence from WopParser
#                                - made changes introduced with Wop 1.5.2 beta
#                                - auth() players at parser startup, making use of the dumpuser command
# 2011-04-07 - 1.2.0 - Courgette - change rcon ban command to 'banaddr'
#                                - remove attacker fixes for special death
#                                - add EVT_CLIENT_PRIVATE_SAY
#                                - ENTITYNUM_WORLD : now a known 'client' in B3
#                                - don't fire teamkills/teamdamage events in gametypes with no teams,
#                                  see TEAM_BASED_GAMETYPES
#                                - add a DEBUG_EVENT flag
#                                - do not provides fake guid for bot, so they won't autheticate and won't
#                                  make it to database
# 2011-04-07 - 1.2.1 - Courgette - fix TEAM_BASED_GAMETYPES
# 2011-04-07 - 1.2.2 - Courgette - fix Tell regexp when cid is -1
#                                - reflect that cid are not converted to int anymore in the clients module
#                                - do not try to fix attacket in on_kill
#                                - fix MOD_SHOTGUN -> MOD_PUMPER
# 2011-04-10 - 1.2.3 - Courgette - fix commands that should use quotation marks
# 2014-01-15 - 1.3   - Fenix     - PEP8 coding standards
#                                - correctly set client bot flag upon new client connection
# 2014-07-17 - 1.4   - Fenix     - updated abstract parser to comply with the new get_wrap implementation
#                                - updated rcon command patterns
# 2014-08-11 - 1.5   - Fenix     - syntax cleanup
# 2015-04-16 - 1.6   - Fenix     - uniform class variables (dict -> variable)
#                                - implement missing abstract class methods

__author__ = 'xlr8or, Courgette'
__version__ = '1.6'

import b3
import b3.events
import b3.parser
import re
import string

from b3.parsers.q3a.abstractParser import AbstractParser

DEBUG_EVENTS = False

MOD_UNKNOWN = '0'
MOD_PUMPER = '1'
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
MOD_FALLING = '20'       # not used in wop
MOD_SUICIDE = '21'
MOD_TARGET_LASER = '22'  # not used in wop
MOD_TRIGGER_HURT = '23'
MOD_GRAPPLE = '24'       # not used in wop

GAMETYPE_FFA = '0'
GAMETYPE_1VS1 = '1'
GAMETYPE_SP = '2'
GAMETYPE_SYC = '3'
GAMETYPE_LPS = '4'
GAMETYPE_TFFA = '5'
GAMETYPE_CTL = '6'
GAMETYPE_TSYC = '7'
GAMETYPE_BB = '8'

TEAM_BASED_GAMETYPES = (GAMETYPE_TFFA, GAMETYPE_CTL, GAMETYPE_TSYC, GAMETYPE_BB)


class Wop15Parser(AbstractParser):

    gameName = 'wop15'

    _line_length = 65
    _line_color_prefix = ''

    _commands = {
        'message': 'stell %(cid)s "%(message)s"',
        'say': 'ssay "%(message)s"',
        'saybig': 'scp -1 "%(message)s"',
        'set': 'set %(name)s "%(value)s"',
        'kick': 'clientkick %(cid)s',
        'ban': 'banAddr %(cid)s',
        'tempban': 'clientkick %(cid)s',
    }

    _eventMap = {
        #'warmup': EVT_GAME_WARMUP,
        #'shutdowngame': EVT_GAME_ROUND_END
    }

    # remove the time off of the line
    _lineClear = re.compile(r'^(?:[0-9:]+\s?)?')

    _lineFormats = (
        # Generated with : WOP version 1.5
        # ClientConnect: 0 014D28A78B194CDA9CED1344D47B903B 84.167.190.158
        re.compile(r'^(?P<action>[a-z]+):\s'
                   r'(?P<data>'
                   r'(?P<cid>[0-9]+)\s'
                   r'(?P<cl_guid>[0-9a-z]{32})\s+'
                   r'(?P<ip>[0-9.]+))$', re.IGNORECASE),

        # ClientConnect: 2  151.16.71.226
        re.compile(r'^(?P<action>[a-z]+):\s'
                   r'(?P<data>'
                   r'(?P<cid>[0-9]+)\s+'
                   r'(?P<ip>[0-9.]+))$', re.IGNORECASE),

        # Tell: $cid $target-cid $text"
        # Tell: -1 $target-cid $text"
        re.compile(r'^(?P<action>Tell):\s*'
                   r'(?P<data>'
                   r'(?P<cid>[-]?[0-9]+)\s+'
                   r'(?P<tcid>[0-9]+)\s+'
                   r'(?P<text>.+))$', re.IGNORECASE),

        # Award: 2 gauntlet
        ## disabled because no cid
        #re.compile(r'^(?P<action>Award):\s*(?P<data>.+))$', re.IGNORECASE),

        # ClientConnect: 0
        # re.compile(r'^(?P<action>ClientConnect):\s*(?P<data>(?P<bcid>[0-9]+))$', re.IGNORECASE),

        # Damage: 2 1022 2 50 7
        re.compile(r'^(?P<action>Damage):\s*'
                   r'(?P<data>'
                   r'(?P<cid>[0-9]+)\s+'
                   r'(?P<aweap>[0-9a-z_]+)\s+'
                   r'(?P<acid>[0-9]+)\s+'
                   r'(?P<damage>\d+)\s+'
                   r'(?P<meansofdeath>\d+))$', re.IGNORECASE),

        # Kill: $attacker-cid $means-of-death $target-cid
        # Kill: 2 MOD_INJECTOR 0
        re.compile(r'^(?P<action>[a-z]+):\s*'
                   r'(?P<data>'
                   r'(?P<acid>[0-9]+)\s'
                   r'(?P<aweap>[0-9a-z_]+)\s'
                   r'(?P<cid>[0-9]+))$', re.IGNORECASE),

        # Say: 0 insta machen?
        # Item: 3 ammo_spray_n
        re.compile(r'^(?P<action>[a-z]+):\s*(?P<data>.*)$', re.IGNORECASE),
    )

    # status
    # map: wop_padcloisterctl
    # num score team ping name            lastmsg address               qport rate
    # --- ----- ---- ---- --------------- ------- --------------------- ----- -----
    #   0     0    2    0 ^0PAD^4MAN^7         50 bot                       0 16384
    #   1     0    3   43 PadPlayer^7           0 2001:41b8:9bf:fe04:f40c:d4ff:fe2b:6af9 45742 90000
    _regPlayer = re.compile(r'^(?P<slot>[0-9]+)\s+'
                            r'(?P<score>[0-9-]+)\s+'
                            r'(?P<team>[0-9]+)\s+'
                            r'(?P<ping>[0-9]+)\s+'
                            r'(?P<name>.*?)\s+'
                            r'(?P<last>[0-9]+)\s+'
                            r'(?P<ip>[0-9.]+)\s+'
                            r'(?P<qport>[0-9]+)\s+'
                            r'(?P<rate>[0-9]+)$', re.IGNORECASE)

    _reColor = re.compile(r'(\^.)|[\x00-\x20]|[\x7E-\xff]')

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
        self.clients.newClient('-1', guid='WORLD', name='World', hide=True)
        self.clients.newClient('1022', guid='ENTITYNUM_WORLD', name='World', hide=True)

        # force g_logsync
        self.debug('Forcing server cvar g_logsync to %s' % self._logSync)
        self.setCvar('g_logsync', self._logSync)

        # get map from the status rcon command
        mapname = self.getMap()
        if mapname:
            self.game.mapName = mapname
            self.info('map is: %s' % self.game.mapName)
        
        # initialize connected clients
        plist = self.getPlayerList()
        for cid, c in plist.iteritems():
            userinfostring = self.queryClientUserInfoByCid(cid)
            if userinfostring:
                self.OnClientuserinfo(None, userinfostring)

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENT HANDLERS                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def OnClientconnect(self, action, data, match=None):
        # ClientConnect: 2 77F303414E4355E0860B483F2A07E4DF 151.16.71.226:27960
        # ClientConnect: 2  151.16.71.226
        # ClientConnect: 0
        try:
            cid = match.group('cid')  # Normal client connected
            self.verbose('Client connected cid: %s' % cid)
        except IndexError:
            pass

    def OnClientuserinfochanged(self, action, data, match=None):
        bclient = self.parseUserInfo(data)
        self.verbose('Parsed user info: %s' % bclient)
        if bclient:
            client = self.clients.getByCID(bclient['cid'])
            if client:
                # update existing client
                bclient['ip'] = client.ip
                for k, v in bclient.iteritems():
                    setattr(client, k, v)

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

        self.verbose('Current gametype: %s' % self.game.gameType)
        self.game.startRound()
        self.debug('Joining players')
        self.joinPlayers()

        return self.getEvent('EVT_GAME_ROUND_START', self.game)

    def OnSay(self, action, data, match=None):
        # 3:59 say: 1 general chat
        msg = string.split(data, ' ', 1)
        if not len(msg) == 2:
            return None

        if msg[0] == '-1':
            # server talking -> ignore
            return

        client = self.getByCidOrJoinPlayer(msg[0])

        if client:
            self.verbose('Client found: %s' % client.name)
            return self.getEvent('EVT_CLIENT_SAY', msg[1], client)
        else:
            self.verbose('No client found')
            return None

    def OnSayteam(self, action, data, match=None):
        # 4:06 sayteam: 1 teamchat
        msg = string.split(data, ' ', 1)
        if not len(msg) == 2:
            return None

        client = self.getByCidOrJoinPlayer(msg[0])

        if client:
            self.verbose('Client found: %s' % client.name)
            return self.getEvent('EVT_CLIENT_TEAM_SAY', msg[1], client, client.team)
        else:
            self.verbose('No client found')
            return None

    def OnTell(self, action, data, match=None):
        # Tell: $cid $target-cid $text
        if match is None:
            return
        cid = match.group('cid')
        client = self.getByCidOrJoinPlayer(cid)
        target = self.getByCidOrJoinPlayer(match.group('tcid'))
        if client and cid != '-1':
            return self.getEvent('EVT_CLIENT_PRIVATE_SAY', match.group('text'), client, target)

    def OnDamage(self, action, data, match=None):
        # note : do not use getByCidOrJoinPlayer because cid in 
        # damage line is sometimes bugged (numbers over 64)
        cid = match.group('cid')
        if not -1 < int(cid) < 64:
            cid = '1022'
        victim = self.clients.getByCID(cid)
        if not victim:
            self.debug('No victim')
            return None

        acid = match.group('acid')
        if not -1 < int(acid) < 64:
            acid = '1022'
        attacker = self.clients.getByCID(acid)
        if not attacker:
            self.debug('No attacker')
            return None

        # ignore kills involving no player (world killing world)
        if attacker.cid == victim.cid == '1022':
            self.debug("world damaging world -> ignoring")
            return

        weapon = match.group('aweap')
        if not weapon:
            self.debug('No weapon')
            return None

        eventkey = 'EVT_CLIENT_DAMAGE'
        # fix event for team change and suicides and tk
        if attacker.cid == victim.cid:
            eventkey = 'EVT_CLIENT_DAMAGE_SELF'
        elif attacker.team != b3.TEAM_UNKNOWN and attacker.team == victim.team and \
                self.game.gameType in TEAM_BASED_GAMETYPES:
            eventkey = 'EVT_CLIENT_DAMAGE_TEAM'

        # if not logging damage we need a general hitloc (for xlrstats)
        if not hasattr(victim, 'hitloc'):
            victim.hitloc = 'body'
        
        damagepoints = float(match.group('damage'))
        return self.getEvent(eventkey, (damagepoints, weapon, victim.hitloc), attacker, victim)

    def OnKill(self, action, data, match=None):
        """
         0:   MOD_UNKNOWN, Unknown Means od Death, shouldn't occur at all
         1:   MOD_PUMPER, Pumper
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
        self.debug('OnKill: %s (%s)' % (match.group('aweap'), match.group('data')))
        cid = match.group('cid')
        if not -1 < int(cid) < 64:
            cid = '1022'
        victim = self.clients.getByCID(cid)
        if not victim:
            self.debug('No victim')
            #self.OnClientuserinfo(action, data, match)
            return None

        acid = match.group('acid')
        if not -1 < int(acid) < 64:
            acid = '1022'
        attacker = self.clients.getByCID(acid)
        if not attacker:
            self.debug('No attacker')
            return None

        # ignore kills involving no player (world killing world)
        if attacker.cid == victim.cid == '1022':
            self.debug("World damaging world -> ignoring")
            return

        weapon = match.group('aweap')
        if not weapon:
            self.debug('No weapon')
            return None
        
        eventkey = 'EVT_CLIENT_KILL'
        # fix event for team change and suicides and tk
        if attacker.cid == victim.cid:
            eventkey = 'EVT_CLIENT_SUICIDE'
        elif attacker.team != b3.TEAM_UNKNOWN and attacker.team == victim.team and \
                self.game.gameType in TEAM_BASED_GAMETYPES:
            eventkey = 'EVT_CLIENT_KILL_TEAM'

        # if not logging damage we need a general hitloc (for xlrstats)
        if not hasattr(victim, 'hitloc'):
            victim.hitloc = 'body'
        
        victim.state = b3.STATE_DEAD
        #self.verbose('OnKill Victim: %s, Attacker: %s, Weapon: %s, Hitloc: %s, dType: %s' % (
        # victim.name, attacker.name, weapon, victim.hitloc, dType))
        # need to pass some amount of damage for the teamkill plugin - 100 is a kill
        return self.getEvent(eventkey, (100, weapon, victim.hitloc), attacker, victim)

    def OnItem(self, action, data, match=None):
        # Item: 5 weapon_betty
        cid, item = string.split(data, ' ', 1)
        client = self.getByCidOrJoinPlayer(cid)
        if client:
            return self.getEvent('EVT_CLIENT_ITEM_PICKUP', item, client)
        return None

    def OnClientuserinfo(self, action, data, match=None):
        bot = False
        bclient = self.parseUserInfo(data)
        self.verbose('Parsed user info: %s' % bclient)
        if not 'cl_guid' in bclient and 'skill' in bclient:
            # must be a bot connecting
            self.bot('Bot connecting')
            bclient['ip'] = '0.0.0.0'
            bot = True
            
        if 'cl_guid' in bclient:
            bclient['guid'] = bclient['cl_guid']
        if bclient:
            client = self.clients.getByCID(bclient['cid'])
            if client:
                # update existing client
                for k, v in bclient.iteritems():
                    setattr(client, k, v)
            else:
                cid = bclient['cid']
                del bclient['cid']
                client = self.clients.newClient(cid, state=b3.STATE_ALIVE, bot=bot, **bclient)
                
            self.debug("Client is now: %s" % client)

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
        # 3 n\Dr.Schraube\t\0\model\padman/padsoldier_red\hmodel\padman/padsoldier_red\c1\4\c2\1\hc\100\w\0\l\0...
        player_id, info = string.split(info, ' ', 1)

        if info[:1] != '\\':
            info = '\\' + info

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

        if 'cl_guid' in data and not 'guid' in data:
            data['guid'] = data['cl_guid']

        return data

    ####################################################################################################################
    #                                                                                                                  #
    #   OTHER METHODS                                                                                                  #
    #                                                                                                                  #
    ####################################################################################################################

    def defineGameType(self, gametype_int):
        """
        Translate the gametype to a readable format.
        """
        gametype = ''

        if gametype_int == GAMETYPE_FFA:
            gametype = 'FFA'
        elif gametype_int == GAMETYPE_1VS1:
            gametype = 'lVSl'
        elif gametype_int == GAMETYPE_SP:
            gametype = 'SP'
        elif gametype_int == GAMETYPE_SYC:
            gametype = 'SYC'
        elif gametype_int == GAMETYPE_LPS:
            gametype = 'LPS'
        elif gametype_int == GAMETYPE_TFFA:
            gametype = 'TFFA'
        elif gametype_int == GAMETYPE_CTL:
            gametype = 'CTL'
        elif gametype_int == GAMETYPE_TSYC:
            gametype = 'TSYC'
        elif gametype_int == GAMETYPE_BB:
            gametype = 'BB'

        return gametype

    def joinPlayers(self):
        """
        Join all the connected clients.
        """
        plist = self.getPlayerList()
        for cid, c in plist.iteritems():
            client = self.clients.getByCID(cid)
            if client:
                self.debug('Joining client: %s' % client.name)
                self.queueEvent(self.getEvent('EVT_CLIENT_JOIN', None, client))

        return None

    def queryClientUserInfoByCid(self, cid):
        """
        userinfo 2
        --------
        ip                   192.168.10.1
        syc_color            0
        cl_voip              1
        cg_predictItems      1
        sex                  male
        handicap             100
        team_headmodel       padman
        team_model           padman
        headmodel            padman
        model                padman
        snaps                40
        rate                 25000
        name                 PadPlayer
        cl_guid              98E40E6546546546546546546543D572
        teamoverlay          1
        cg_smoothClients     0
        
        : dumpuser 4
        Player 4 is not on the server
        """
        if not -1 < int(cid) < 64:
            return None
        data = self.write('dumpuser %s' % cid)
        if not data:
            return None
        
        if data.split('\n')[0] != "userinfo":
            self.debug("Dumpuser %s returned : %s" % (cid, data))
            self.debug('Client %s probably disconnected but its character is still hanging in game...' % cid)
            return None

        datatransformed = "%s " % cid
        for line in data.split('\n'):
            if line.strip() == "userinfo" or line.strip() == "--------":
                continue

            var = line[:20].strip()
            val = line[20:].strip()
            datatransformed += "\\%s\\%s" % (var, val)

        return datatransformed

    def getByCidOrJoinPlayer(self, cid):
        if int(cid) > 63:
            self.debug("A client cid cannot be over 63 ! received : %s" % cid)
            return None
        client = self.clients.getByCID(cid)
        if client is None:
            self.debug('Cannot find client by cid %r' % cid)
            self.debug(repr(self.clients))
            userinfostring = self.queryClientUserInfoByCid(cid)
            if userinfostring:
                self.OnClientuserinfo(None, userinfostring)
            client = self.clients.getByCID(cid)
        return client

    def queueEvent(self, event, expire=10):
        """
        Queue an event for processing.
        :param event: The event to be enqueued
        :param expire: The amount of seconds after which the event will be discarded
        """
        try:
            if DEBUG_EVENTS:
                self.verbose2(event)
        finally:
            return b3.parser.Parser.queueEvent(self, event, expire)

    ####################################################################################################################
    #                                                                                                                  #
    #   B3 PARSER INTERFACE IMPLEMENTATION                                                                             #
    #                                                                                                                  #
    ####################################################################################################################

    def getNextMap(self):
        pass

# ------ Documentation -------------------------------------------------------------------------------------------------
#
# game log information provided by GedankenBlitz:
#
# stell $cid $text
# Serverside tell chat.
#
# ssay $text
# Serverside say chat.
#
# sprint $cid $text
# Print text to a client. Text will be printed to the upper left chat area.
#
# New loglines;
# DropItem: $cid $classname
# Award: $cid $awardname
# AddScore: $cid $score $reason
# Vote: failed timeout
# Vote: failed
# Vote: passed
# CvarChange: $cvar-name $cvar-value
# AddTeamScore: $teamname $score $reason
# Callvote: $cid $vote
#
# Changed loglines;
# Kill: $attacker-cid $means-of-death $target-cid
# Teamscores: red $score-red blue $score-blue
# Score: $cid $score
# Say: $cid $text
# SayTeam: $cid $text
# Tell: $cid $target-cid $text
#
# rcon status currently includes an extra column for the player team;
# map: wop_padcloisterctl
# num score team ping name            lastmsg address               qport rate
# --- ----- ---- ---- --------------- ------- --------------------- ----- -----
#   0     0    2    0 ^0PAD^4MAN^7         50 bot                       0 16384
#   1     0    3   43 PadPlayer^7           0 2001:41b8:9bf:fe04:f40c:d4ff:fe2b:6af9 45742 90000
#
# Awardnames are;
# excellent
# gauntlet
# cap
# impressive
# defend
# assist
# denied
# spraygod
# spraykiller
# unkown
#
# Teamnames are;
# FREE
# RED
# BLUE
# SPECTATOR
# This order matches the team numbers, which start with index 0.
#
# Inbuilt score reasons include;
# suicide
# teamkill
# kill
# survive
# spray
# spray_wrongwall
# target_score
# frag_carrier
# carrier_protect
# defense
# recovery
# capture
# capture_team
# assist_return
# assist_frag_carrier
# flag
# spraykiller
# spraygod
#
# Means of death have changed to
# MOD_UNKNOWN = 0
# MOD_PUMPER
# MOD_PUNCHY
# MOD_NIPPER
# MOD_BALLOONY
# MOD_BALLOONY_SPLASH
# MOD_BETTY
# MOD_BETTY_SPLASH
# MOD_BUBBLEG
# MOD_BUBBLEG_SPLASH // should be unused
# MOD_SPLASHER
# MOD_BOASTER
# MOD_IMPERIUS
# MOD_IMPERIUS_SPLASH
# MOD_INJECTOR // new
# MOD_KILLERDUCKS
# MOD_WATER
# MOD_SLIME
# MOD_LAVA
# MOD_CRUSH
# MOD_TELEFRAG
# MOD_FALLING   // should be unused
# MOD_SUICIDE
# MOD_TARGET_LASER
# MOD_TRIGGER_HURT
# MOD_GRAPPLE   // should be unused
# MOD_BAMBAM // new
# MOD_BOOMIES // new
#
# Votes depend on the vote of course, an example is;
# map wop_dinerbb; set nextmap "wop_padcrashctl"