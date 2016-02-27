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
# 05/04/2009 - 0.0.1              - updating so that it works for etpro
# 31/01/2010 - 0.0.2  - Courgette - get_map() is now inherited from q3a
# 09/04/2011 - 0.0.3  - Courgette - reflect that cid are not converted to int anymore in the clients module
# 02/05/2014 - 0.0.4  - Fenix     - rewrote dictionary creation as literal
#                                 - removed some warnings
#                                 - minor syntax changes
#                                 - replaced variable named using python built-in names
# 18/07/2014 - 0.0.5  - Fenix     - updated parser to comply with the new get_wrap implementation
#                                 - removed _settings dict re-declaration: was the same of the AbstractParser
#                                 - updated rcon command patterns
# 30/07/2014 - 0.0.6  - Fenix     - fixes for the new getWrap implementation
# 04/08/2014 - 0.0.7  - Fenix     - make use of self.getEvent when registering events: removes warnings
# 29/08/2014 - 0.0.8  - Fenix     - syntax cleanup
# 14/02/2015 - 0.0.9  - Courgette - display a tip in b3.log at bot start regarding the correct use of b_privatemessages
# 14/02/2015 - 0.0.10 - Courgette - check the value of b_privatemessages at startup
# 19/03/2015 - 0.0.11 - Fenix     - removed deprecated usage of dict.has_key (us 'in dict' instead)
#
# CREDITS
# Based on the version 0.0.1, thanks ThorN.
# Copied alot from wop.py, thanks xlr8or.
# Thanks for B3.
#
# NOTES
# ETPro has not bots.
# ETPro 3.2.6 - no additional LUA or QMM scripts used
#
# ETPRO:
# - qsay (chat window,
# - cpmsay (left popup area) available since 3.0.15+
# - cp (center print)
# - bp (banner print area, top of screen)
# - say (chat window, with "console: " in front)

__author__ = 'xlr8or, ailmanki'
__version__ = '0.0.11'

import re
import string
import b3
import b3.clients
import b3.events
import b3.parsers.punkbuster

from b3.functions import prefixText
from b3.parsers.q3a.abstractParser import AbstractParser


class EtproParser(AbstractParser):

    gameName = 'etpro'
    PunkBuster = None
    IpsOnly = False  # Setting True will use ip's only for identification.
    IpCombi = False  # Setting True will replace last part of the guid with 2 segments of the ip.

    _empty_name_default = 'EmptyNameDefault'

    _logSync = 2

    _commands = {
        'message': 'm %(name)s %(message)s',
        'say': 'cpmsay %(message)s',
        'set': 'set %(name)s "%(value)s"',
        'kick': 'clientkick %(cid)s',
        'ban': 'banid %(cid)s',
        'tempban': 'clientkick %(cid)s'}

    _eventMap = {
        #'warmup' : b3.events.EVT_GAME_WARMUP,
        #'restartgame' : b3.events.EVT_GAME_ROUND_END
    }

    # remove the time off of the line
    _lineClear = re.compile(r'^(?:[0-9:.]+\s?)?')

    _lineFormats = (
        # 1579:03 ConnectInfo: 0: E24F9B2702B9E4A1223E905BF597FA92: ^w[^2AS^w]^2Lead: 3: 3: 24.153.180.106:2794
        re.compile(r'^(?P<action>[a-z]+):\s*'
                   r'(?P<data>'
                   r'(?P<cid>[0-9]+):\s*'
                   r'(?P<pbid>[0-9A-Z]{32}):\s*'
                   r'(?P<name>[^:]+):\s*'
                   r'(?P<num1>[0-9]+):\s*'
                   r'(?P<num2>[0-9]+):\s*'
                   r'(?P<ip>[0-9.]+):'
                   r'(?P<port>[0-9]+))$', re.IGNORECASE),

        re.compile(r'^(?P<action>[a-z]+):\s*(?P<data>(?P<cid>[0-9]+):\s*(?P<name>.+):\s+(?P<text>.*))$', re.IGNORECASE),

        # 1536:37Kill: 1 18 9: ^1klaus killed ^1[pura]fox.nl by MOD_MP40
        re.compile(r'^(?P<action>[a-z]+):\s*'
                   r'(?P<data>'
                   r'(?P<acid>[0-9]+)\s'
                   r'(?P<cid>[0-9]+)\s'
                   r'(?P<aweap>[0-9]+):\s*'
                   r'(?P<text>.*))$', re.IGNORECASE),

        re.compile(r'^(?P<action>[a-z]+):\s*(?P<data>(?P<cid>[0-9]+):\s*(?P<text>.*))$', re.IGNORECASE),
        re.compile(r'^(?P<action>[a-z]+):\s*(?P<data>(?P<cid>[0-9]+)\s(?P<text>.*))$', re.IGNORECASE),

        # 5:41 Medic_Revive: 3 8
        re.compile(r'^(?P<action>[a-z_]+):\s*(?P<data>(?P<acid>[0-9]+)\s(?P<cid>.*))$', re.IGNORECASE),

        # 5:41 Dynamite_Plant: 3
        re.compile(r'^(?P<action>[a-z_]+):\s*(?P<data>(?P<cid>[0-9]+))$', re.IGNORECASE),

        # Falling through?
        re.compile(r'^(?P<action>[a-z_]+):\s*(?P<data>.*)$', re.IGNORECASE),

        #------ Addon / Mod Lines ------------------------------------------------------------------

        #[QMM] Successfully hooked g_log file
        re.compile(r'^\[(?P<action>[a-z]+)]\s(?P<data>.*)$', re.IGNORECASE),

        # 16:33.29 etpro privmsg: xlr8or[*] to xlr8or: hi
        re.compile(r'^(?P<action>[a-z]+)\s'
                   r'(?P<data>'
                   r'(?P<command>[a-z]+):\s'
                   r'(?P<origin>.*)\sto\s'
                   r'(?P<target>.*):\s'
                   r'(?P<text>.*))$', re.IGNORECASE),

        re.compile(r'^(?P<action>[a-z]+)\s'
                   r'(?P<data>'
                   r'(?P<command>[a-z]+):\s'
                   r'(?P<origin>.*)\sto\s'
                   r'(?P<target>.*):)$', re.IGNORECASE),  # in case there is no privmsg text entered

        re.compile(r'^(?P<action>[a-z]+)\s(?P<data>(?P<command>[a-z]+):\s(?P<text>.*))$', re.IGNORECASE)
    )

    # 15:11:15 map: goldrush
    # num score ping name            lastmsg address               qport rate
    # --- ----- ---- --------------- ------- --------------------- ----- -----
    #   2     0   45 xlr8or[*]             0 145.99.135.227:27960  39678 25000
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
    MOD_MACHINEGUN = '1'
    MOD_BROWNING = '2'
    MOD_MG42 = '3'
    MOD_GRENADE = '4'
    MOD_ROCKET = '5'
    MOD_KNIFE = '6'
    MOD_LUGER = '7'
    MOD_COLT = '8'
    MOD_MP40 = '9'
    MOD_THOMPSON = '10'
    MOD_STEN = '11'
    MOD_GARAND = '12'
    MOD_SNOOPERSCOPE = '13'
    MOD_SILENCER = '14'
    MOD_FG42 = '15'
    MOD_FG42SCOPE = '16'
    MOD_PANZERFAUST = '17'
    MOD_GRENADE_LAUNCHER = '18'
    MOD_FLAMETHROWER = '19'
    MOD_GRENADE_PINEAPPLE = '20'
    MOD_CROSS = '21'
    MOD_MAPMORTAR = '22'
    MOD_MAPMORTAR_SPLASH = '23'
    MOD_KICKED = '24'
    MOD_GRABBER = '25'
    MOD_DYNAMITE = '26'
    MOD_AIRSTRIKE = '27'
    MOD_SYRINGE = '28'
    MOD_AMMO = '29'
    MOD_ARTY = '30'
    MOD_WATER = '31'
    MOD_SLIME = '32'
    MOD_LAVA = '33'
    MOD_CRUSH = '34'
    MOD_TELEFRAG = '35'
    MOD_FALLING = '36'
    MOD_SUICIDE = '37'
    MOD_TARGET_LASER = '38'
    MOD_TRIGGER_HURT = '39'
    MOD_EXPLOSIVE = '40'
    MOD_CARBINE = '41'
    MOD_KAR98 = '42'
    MOD_GPG40 = '43'
    MOD_M7 = '44'
    MOD_LANDMINE = '45'
    MOD_SATCHEL = '46'
    MOD_TRIPMINE = '47'
    MOD_SMOKEBOMB = '48'
    MOD_MOBILE_MG42 = '49'
    MOD_SILENCED_COLT = '50'
    MOD_GARAND_SCOPE = '51'
    MOD_CRUSH_CONSTRUCTION = '52'
    MOD_CRUSH_CONSTRUCTIONDEATH = '53'
    MOD_CRUSH_CONSTRUCTIONDEATH_NOATTACKER = '54'
    MOD_K43 = '55'
    MOD_K43_SCOPE = '56'
    MOD_MORTAR = '57'
    MOD_AKIMBO_COLT = '58'
    MOD_AKIMBO_LUGER = '59'
    MOD_AKIMBO_SILENCEDCOLT = '60'
    MOD_AKIMBO_SILENCEDLUGER = '61'
    MOD_SMOKEGRENADE = '62'
    MOD_SWAP_PLACES = '63'
    MOD_SWITCHTEAM = '64'

    ## meansOfDeath to be considered suicides
    Suicides = (
        MOD_WATER,
        MOD_SLIME,
        MOD_LAVA,
        MOD_CRUSH,
        MOD_TELEFRAG,
        MOD_FALLING,
        MOD_SUICIDE,
        MOD_TARGET_LASER,
        MOD_TRIGGER_HURT,
        MOD_LANDMINE,
        MOD_TRIPMINE
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
        self.bot("TIP: Make sure b_privatemessages isn't set to `0` in your game server config file or B3 won't be able"
                 " to send private messages to players.")
        b_privatemessages = self.getCvar('b_privatemessages').getString()
        if b_privatemessages == "0":
            self.warning("Current b_privatemessages value: %s" % b_privatemessages)
        else:
            self.info("Current b_privatemessages value: %s" % b_privatemessages)
        self.clients.newClient('-1', guid='WORLD', name='World', hide=True, pbid='WORLD')

        # get map from the status rcon command
        mapname = self.getMap()
        if mapname:
            self.game.mapName = mapname
            self.info('map is: %s' % self.game.mapName)

        # force g_logsync
        self.debug('Forcing server cvar g_logsync to %s' % self._logSync)
        self.setCvar('g_logsync', self._logSync)

        self._eventMap['warmup'] = self.getEventID('EVT_GAME_WARMUP')
        self._eventMap['restartgame'] = self.getEventID('EVT_GAME_ROUND_END')

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
        m = None
        line = re.sub(self._lineClear, '', line, 1)
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

        data = {}
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
            client = self.clients.getByCID(bclient['cid'])
            if client:
                # update existing client
                for k, v in bclient.iteritems():
                    setattr(client, k, v)
            else:
                # make a new client
                if 'cl_guid' in bclient:
                    guid = bclient['cl_guid']
                else:
                    guid = 'unknown'

                if not 'name' in bclient:
                    bclient['name'] = self._empty_name_default

                if not 'ip' in bclient and guid == 'unknown':
                    # happens when a client is (temp)banned and got kicked so client was destroyed, but
                    # infoline was still waiting to be parsed.
                    self.debug('Client disconnected: ignoring...')
                    return None

                nguid = ''
                # overide the guid... use ip's only if self.console.IpsOnly is set True.
                if self.IpsOnly:
                    nguid = bclient['ip']
                # replace last part of the guid with two segments of the ip
                elif self.IpCombi:
                    i = bclient['ip'].split('.')
                    d = len(i[0]) + len(i[1])
                    nguid = guid[:-d] + i[0] + i[1]
                # fallback for clients that don't have a cl_guid, we'll use ip instead
                elif guid == 'unknown':
                    nguid = bclient['ip']

                if nguid != '':
                    guid = nguid

                self.clients.newClient(bclient['cid'], name=bclient['name'], ip=bclient['ip'],
                                       state=b3.STATE_ALIVE, guid=guid, data={'guid': guid})

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
            if weapon == self.MOD_SWITCHTEAM:
                # Do not pass a teamchange event here. That event is passed
                # shortly after the kill (in clients.py by adjusting the client object).
                self.verbose('Team change event caught: exiting')
                return None
            else:
                eventkey = 'EVT_CLIENT_SUICIDE'
        elif attacker.team != b3.TEAM_UNKNOWN and attacker.team == victim.team:
            eventkey = 'EVT_CLIENT_KILL_TEAM'

        # if not defined we need a general hitloc (for xlrstats)
        if not hasattr(victim, 'hitloc'):
            victim.hitloc = 'body'

        victim.state = b3.STATE_DEAD
        return self.getEvent(eventkey, (100, weapon, victim.hitloc, damagetype), attacker, victim)

    def OnClientbegin(self, action, data, match=None):
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

        self.verbose('...self.console.game.gameType: %s' % self.game.gameType)
        self.game.startRound()
        self.debug('Synchronizing client info')
        self.clients.sync()

        return self.getEvent('EVT_GAME_ROUND_START', self.game)

    def OnQmm(self, action, data, match=None):
        #self.verbose('OnQmm: data: %s' %data)
        return None

    def OnEtpro(self, action, data, match=None):
        #self.verbose('OnEtpro: data: %s' %data)
        #self.verbose('OnEtpro: command = %s' %(match.group('command')))
        try:
            command = match.group('command')
        except:
            self.debug('Etpro info line: %s' % match.group('data'))
            return None

        if command == 'privmsg':
            try:
                text = match.group('text')
            except:
                self.verbose('No message entered in privmsg!')
                return None
            self.OnPrivMsg(match.group('origin'), match.group('target'), text)
        # an example on how to catch other etpro events:
        elif command == 'event':
            self.verbose('event: %s' % (match.group('text')))
        else:
            self.verbose('%s: %s' % (command, match.group('text')))

        return None

    def OnPrivMsg(self, origin, target, text):
        client = self.clients.getByExactName(origin)
        tclient = self.clients.getClientLikeName(target)
        if not client:
            #self.verbose('No Client Found')
            return None

        if not tclient:
            client.message('Please be more specific providing the target, can\'t find it with given input!')
            return None

        if text and ord(text[:1]) == 21:
            text = text[1:]

        #client.name = match.group('name')
        self.verbose(
            'text: %s, client: %s - %s, tclient: %s - %s' % (text, client.name, client.id, tclient.name, tclient.id))
        self.queueEvent(self.getEvent('EVT_CLIENT_PRIVATE_SAY', text, client, tclient))

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
        Translate the gametype to a readable format (also for teamkill plugin!)
        """
        gametype = str(gametype_int)
        if gametype_int == '0':
            gametype = 'sp'  # Single Player
        elif gametype_int == '1':
            gametype = 'cp'  # Co-Op
        elif gametype_int == '2':
            gametype = 'smo'  # Single Map Objective
        elif gametype_int == '3':
            gametype = 'sw'  # Stopwatch
        elif gametype_int == '4':
            gametype = 'ca'  # Campaign
        elif gametype_int == '5':
            gametype = 'lms'  # Last Man Standing

        return gametype

    ####################################################################################################################
    #                                                                                                                  #
    #   B3 PARSER INTERFACE IMPLEMENTATION                                                                             #
    #                                                                                                                  #
    ####################################################################################################################

    def message(self, client, text):
        """
        Send a private message to a client.
        :param client: The client to who send the message.
        :param text: The message to be sent.
        """
        if client is None:
            # do a normal say
            self.say(text)
            return

        lines = []
        message = prefixText([self.msgPrefix, self.pmPrefix], text)
        message = message.strip()
        for line in self.getWrap(message):
            lines.append(self.getCommand('message', name=client.name, message=line))
        self.writelines(lines)

    def sayDead(self, text):
        """
        Send a private message to all the dead clients.
        :param text: The message to be sent.
        """
        lines = []
        message = prefixText([self.msgPrefix, self.deadPrefix], text)
        message = message.strip()
        wrapped = self.getWrap(message)
        for client in self.clients.getClientsByState(b3.STATE_DEAD):
            if client.cid:
                for line in wrapped:
                    lines.append(self.getCommand('message', name=client.name, message=line))
        self.writelines(lines)

    def getMaps(self):
        return ['Command not supported!']

    def getNextMap(self):
        return 'Command not supported!'

    def sync(self):
        """
        For all connected players returned by self.get_player_list(), get the matching Client
        object from self.clients (with self.clients.get_by_cid(cid) or similar methods) and
        look for inconsistencies. If required call the client.disconnect() method to remove
        a client from self.clients.
        """
        plist = self.getPlayerList()
        mlist = {}
        for cid, c in plist.iteritems():
            client = self.clients.getByCID(cid)
            if client:
                if client.guid and 'guid' in c:
                    if client.guid == c['guid']:
                        # player matches
                        self.debug('in-sync %s == %s (cid: %s - slotid: %s)', client.guid, c['guid'], client.cid,
                                   c['cid'])
                        mlist[str(cid)] = client
                    else:
                        self.debug('no-sync %s <> %s (disconnecting %s from slot %s)', client.guid, c['guid'],
                                   client.name, client.cid)
                        client.disconnect()
                elif client.ip and 'ip' in c:
                    if client.ip == c['ip']:
                        # player matches
                        self.debug('in-sync %s == %s (cid: %s == slotid: %s)', client.ip, c['ip'], client.cid, c['cid'])
                        mlist[str(cid)] = client
                    else:
                        self.debug('no-sync %s <> %s (disconnecting %s from slot %s)', client.ip, c['ip'], client.name,
                                   client.cid)
                        client.disconnect()
                else:
                    self.debug('no-sync: no guid or ip found')

        return mlist

        # ---- Documentation --------------------------------------------------------------------------------
        #
        #//infos clienuserinfochanged
        #//0 = player_ID
        #//n = name
        #//t = team
        #//c = class
        #//r = rank
        #//m = medals
        #//s = skills
        #//dn = disguised name
        #//dr = disguised rank
        #//w = weapon
        #//lw = weapon last used
        #//sw = 2nd weapon (not sure)
        #//mu = muted
        #//ref = referee
        #//lw = latched weapon (weapon on next spawn)
        #//sw = latched secondary weapon (secondary weapon on next spawn)
        #//p = privilege level (peon = 0, referee (vote), referee (password), semiadmin, rconauth) (etpro only)
        #//ss = stats restored by stat saver (etpro only)
        #//sc = shoutcaster status (etpro only)
        #//tv = ETTV slave (etpro only)