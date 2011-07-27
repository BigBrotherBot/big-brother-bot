#
# Soldier of Fortune 2 parser for BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2011 Mark Weirath (xlr8or@xlr8or.com)
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
#
# CHANGELOG

__author__ = 'xlr8or, ~cGs*Pr3z, ~cGs*AQUARIUS'
__version__ = '1.0.0'

from b3.parsers.q3a.abstractParser import AbstractParser
import re, string
import b3
import b3.events

#----------------------------------------------------------------------------------------------------------------------------------------------
class Sof2Parser(AbstractParser):
    gameName = 'sof2'
    IpsOnly = False
    IpCombi = False
    privateMsg = False
    _empty_name_default = 'EmptyNameDefault'

    _settings = {}
    _settings['line_length'] = 65
    _settings['min_wrap_length'] = 100

    _commands = {}
    _commands['message'] = 'say %(prefix)s [^3%(name)s^7]: %(message)s'
    _commands['deadsay'] = 'say %(prefix)s^7 %(message)s'
    _commands['say'] = 'say %(prefix)s^7 %(message)s'

    _commands['set'] = 'set %(name)s "%(value)s"'
    _commands['kick'] = 'clientkick %(cid)s'
    _commands['ban'] = 'addip %(cid)s'
    _commands['tempban'] = 'clientkick %(cid)s'

    _eventMap = {
        'warmup': b3.events.EVT_GAME_WARMUP,
        'shutdowngame': b3.events.EVT_GAME_ROUND_END
    }

    # remove the time off of the line
    _lineClear = re.compile(r'^(?:[0-9:]+\s?)?')
    #0:00 ClientUserinfo: 0:

    _lineFormats = (
        #Generated with : SoF2 version: SOF2MP GOLD V1.03 win-x86 Nov  5 2002
        #Kill: 0 0 18: xlr8or killed xlr8or by MOD_SMOHG92_GRENADE
        #Kill: <killer> <victim> <meansofdeath>
        re.compile(
            r'^(?P<action>[a-z]+):\s*(?P<data>(?P<acid>[0-9]+)\s(?P<cid>[0-9]+)\s(?P<aweap>[0-9]+):\s*(?P<text>.*))$',
            re.IGNORECASE),

        #hit: 0 0 520 368 0: xlr8or hit xlr8or at location 520 for 368
		#hit: 0 1 8192 80 0: xlr8or hit sh.andrei at location 8192 for 80
        #hit: <acid> <cid> <location> <damage> <meansofdeath>: <aname> hit <name> at location <location> for <damage>
        re.compile(
            r'^(?P<action>[a-z]+):\s(?P<data>(?P<acid>[0-9]+)\s(?P<cid>[0-9]+)\s(?P<hitloc>[0-9]+)\s(?P<damage>[0-9]+)\s(?P<aweap>[0-9]+):\s+(?P<text>.*))$'
            , re.IGNORECASE),

        #say: xlr8or: hello
        re.compile(r'^(?P<action>say):\s*(?P<data>(?P<name>[^:]+):\s*(?P<text>.*))$', re.IGNORECASE),

        #ClientConnect: <cid> - <ip>:<port> [<guid>]
        re.compile(
            r'^(?P<action>[a-z]+):\s(?P<data>(?P<cid>[0-9]+)\s-\s(?P<ip>[0-9.]+):(?P<port>[-0-9]+)\s\[(?P<cl_guid>[0-9A-Z]{32})\])$',
            re.IGNORECASE),

        #Bot connecting
        #ClientConnect: 4 -  []
        re.compile(r'^(?P<action>ClientConnect):\s*(?P<data>(?P<bcid>[0-9]+)\s-\s\s\[\])$', re.IGNORECASE),

        #Falling thru?
        re.compile(r'^(?P<action>[a-z]+):\s*(?P<data>.*)$', re.IGNORECASE)
        )

    #status
    #map: mp_shop
    #num score ping name            lastmsg address               qport rate
    #--- ----- ---- --------------- ------- --------------------- ----- -----
    #  0     0  103 xlr8or               50 145.99.135.000:-2820  64603  9000
    #  1    24  121 ~cGs*Pr3z~      0 178.202.104.000:20100 23805 25000
    #  2    20  108 ~cGs*Jonkie*     50 84.85.84.000:-268      18496 25000
    #  3    18  999 *DS*88  18200 188.157.129.000:20100  29389  9000
    #  4     3    0 Homer~Sexual         50 bot                   54183 16384
    #  7     6    0 Wet~Sponge           50 bot                       0 16384
    #  8     4    0 PaashaasSchaamhaarVerzamelaar     50 bot                       0 16384

    #_regPlayer = re.compile(r'^(?P<slot>[0-9]+)\s+(?P<score>[0-9-]+)\s+(?P<ping>[0-9]+)\s+(?P<name>.*?)\s+(?P<last>[0-9]+)\s+(?P<ip>[0-9.]+):(?P<port>[0-9-]+)\s+(?P<qport>[0-9]+)\s+(?P<rate>[0-9]+)$', re.I)
    _regPlayer = re.compile(
        r'^(?P<slot>[0-9]+)\s+(?P<score>[0-9-]+)\s+(?P<ping>[0-9]+)\s+(?P<name>.*?)\s+(?P<last>[0-9]+)\s+(?P<ip>[0-9.]+):(?P<port>[0-9-]+)\s+(?P<qport>[0-9]+)\s+(?P<rate>[0-9]+)$'
        , re.I)
    _reColor = re.compile(r'(\^.)|[\x00-\x20]|[\x7E-\xff]')

    PunkBuster = None

    #kill modes (aweap, meansofdeath)
    MOD_UNKNOWN = '0'
    MOD_KNIFE = '1'
    MOD_M1911A1_PISTOL = '2'
    MOD_USSOCOM_PISTOL = '3'
    MOD_SILVER_TALON = '4'
    MOD_M590_SHOTGUN = '5'
    MOD_MICRO_UZI_SUBMACHINEGUN = '6'
    MOD_M3A1_SUBMACHINEGUN = '7'
    MOD_MP5 = '8'
    MOD_USAS_12_SHOTGUN = '9'
    MOD_M4_ASSAULT_RIFLE = '10'
    MOD_AK74_ASSAULT_RIFLE = '11'
    MOD_SIG551 = '12'
    MOD_MSG90A1_SNIPER_RIFLE = '13'
    MOD_M60_MACHINEGUN = '14'
    MOD_MM1_GRENADE_LAUNCHER = '15'
    MOD_RPG7_LAUNCHER = '16'
    MOD_M84_GRENADE = '17'
    MOD_SMOHG92_GRENADE = '18'
    MOD_ANM14_GRENADE = '19'
    MOD_M15_GRENADE = '20'
    MOD_WATER = '21'
    MOD_CRUSH = '22'
    MOD_TELEFRAG = '23'
    MOD_FALLING = '24'
    MOD_SUICIDE = '25'
    MOD_TEAMCHANGE = '26'
    MOD_TARGET_LASER = '27'
    MOD_TRIGGER_HURT = '28'
    MOD_TRIGGER_HURT_NOSUICIDE = '29'
    MOD_ADMIN_STRIKE = '30'
    MOD_ADMIN_SLAP = '31'
    MOD_ADMIN_FRY = '32'
    MOD_ADMIN_EXPLODE = '33'
    MOD_ADMIN_TELEFRAG = '34'
    MOD_KNIFE_ALT = '35'
    MOD_M1911A1_PISTOL_ALT = '36'
    MOD_USSOCOM_PISTOL_ALT = '37'
    MOD_SILVER_TALON_ALT = '38'
    MOD_M590_SHOTGUN_ALT = '39'
    MOD_M4_ASSAULT_RIFLE_ALT = '40'
    MOD_AK74_ASSAULT_RIFLE_ALT = '41'
    MOD_M84_GRENADE_ALT = '42'
    MOD_SMOHG92_GRENADE_ALT = '43'
    MOD_ANM14_GRENADE_ALT = '44'
    MOD_M15_GRENADE_ALT = '45'

    def startup(self):
        # add the world client
        client = self.clients.newClient('-1', guid='WORLD', name='World', hide=True, pbid='WORLD')

        if self.privateMsg:
            self.warning('SoF2 will need a mod to enable private messaging!')

        if not self.config.has_option('server', 'punkbuster') or self.config.getboolean('server', 'punkbuster'):
            self.PunkBuster = b3.parsers.punkbuster.PunkBuster(self)

        # get map from the status rcon command
        map = self.getMap()
        if map:
            self.game.mapName = map
            self.info('map is: %s' % self.game.mapName)

        # initialize connected clients
        plist = self.getPlayerList()
        for cid, c in plist.iteritems():
            #self.debug(c)
            userinfostring = self.queryClientUserInfoByName(cid, c['name'])
            if userinfostring:
                self.OnClientuserinfo(None, userinfostring)


    def getLineParts(self, line):
        line = re.sub(self._lineClear, '', line, 1)

        for f in self._lineFormats:
            m = re.match(f, line)
            if m:
                #self.debug('line matched %s' % f.pattern)
                break

        if m:
            client = None
            target = None
            return (m, m.group('action').lower(), m.group('data').strip(), client, target)
        else:
            self.verbose('line did not match format: %s' % line)

    def parseUserInfo(self, info):
        #0 \ip\145.99.135.000:-12553\cl_guid\XXXXD914662572D3649B94B1EA5F921\cl_punkbuster\0\details\5\name\xlr8or\rate\9000\snaps\20\identity\NPC_Sam/sam_gladstone\cl_anonymous\0\cg_predictItems\1\cg_antiLag\1\cg_autoReload\1\cg_smoothClients\0\team_identity\shopguard1\outfitting\GACAA
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

        t = 0
        if data.has_key('team'):
            t = data['team']
        elif data.has_key('t'):
            t = data['t']

        data['team'] = self.getTeam(t)

        if data.has_key('cl_guid') and not data.has_key('pbid'):
            data['pbid'] = data['cl_guid']

        return data

    # Need to override message format. Game does not support PM's
    def message(self, client, text):
        try:
            if client == None:
                self.say(text)
            elif client.cid == None:
                pass
            else:
                lines = []
                for line in self.getWrap(text, self._settings['line_length'], self._settings['min_wrap_length']):
                    lines.append(self.getCommand('message', prefix=self.msgPrefix, name=client.name, message=line))

                self.writelines(lines)
        except:
            pass

    def OnClientconnect(self, action, data, match=None):
        # we get user info in two parts:
        # ClientConnect: 0 - 79.172.5.254:20100 [894E22B3636F8E9198C566C28AD87D0B]
        # ClientUserinfoChanged: 0 n\xlr8or\t\0\identity\NPC_Sam/sam_gladstone
        # we need to store the ClientConnect ID, the guid and IP for the next call to Clientuserinfochanged only on initial connection

        try:
            self._clientConnectID = match.group('cid') # Normal client connected
        except:
            try:
                self._clientConnectID = match.group('bcid') # Game Bot identifier
                self._clientConnectGuid = 'BOT' + str(match.group('bcid'))
                self._clientConnectIp = '0.0.0.0'
                self.bot('Bot Connected')
                return None
            except:
                self.error('Parser could not connect client')
                return None

        try:
            self._clientConnectGuid = match.group('cl_guid') # If we have no cl_guid we'll use the ip instead.
        except:
            self._clientConnectGuid = match.group('ip')

        self._clientConnectIp = match.group('ip')
        self.verbose('Client Connected cid: %s, guid: %s, ip: %s' % (
            self._clientConnectID, self._clientConnectGuid, self._clientConnectIp))

    # Parse Userinfo
    # Only called when bot is starting on a populated server
    def OnClientuserinfo(self, action, data, match=None):
        #0 \ip\145.99.135.000:-12553\cl_guid\XXXXD914662572D3649B94B1EA5F921\cl_punkbuster\0\details\5\name\xlr8or\rate\9000\snaps\20\identity\NPC_Sam/sam_gladstone\cl_anonymous\0\cg_predictItems\1\cg_antiLag\1\cg_autoReload\1\cg_smoothClients\0\team_identity\shopguard1\outfitting\GACAA
        bclient = self.parseUserInfo(data)

        if bclient.has_key('name'):
            # remove spaces from name
            bclient['name'] = bclient['name'].replace(' ','')

        # split port from ip field
        if bclient.has_key('ip'):
            if bclient['ip'] == 'bot':
                #not sure if this one works...
                self.bot('Bot Connected!')
                bclient['ip'] = '0.0.0.0'
                bclient['cl_guid'] = 'BOT' + str(bclient['cid'])
            else:
                ipPortData = string.split(bclient['ip'], ':', 1)
                bclient['ip'] = ipPortData[0]
                if len(ipPortData) > 1:
                    bclient['port'] = ipPortData[1]

        if bclient.has_key('team'):
            bclient['team'] = self.getTeam(bclient['team'])

        if bclient.has_key('cl_guid') and not bclient.has_key('pbid') and self.PunkBuster:
            bclient['pbid'] = bclient['cl_guid']

        self.verbose('Parsed user info %s' % bclient)

        if bclient:
            client = self.clients.getByCID(bclient['cid'])

            if client:
                # update existing client
                for k, v in bclient.iteritems():
                    setattr(client, k, v)
            else:
                #make a new client
                if self.PunkBuster:
                    # we will use punkbuster's guid
                    guid = None
                else:
                    # use io guid
                    if bclient.has_key('cl_guid'):
                        guid = bclient['cl_guid']
                    else:
                        guid = 'unknown'

                if not bclient.has_key('name'):
                    bclient['name'] = self._empty_name_default

                if not bclient.has_key('ip') and guid == 'unknown':
                    # happens when a client is (temp)banned and got kicked so client was destroyed, but
                    # infoline was still waiting to be parsed.
                    self.debug('Client disconnected. Ignoring.')
                    return None

                nguid = ''
                # overide the guid... use ip's only if self.console.IpsOnly is set True.
                if self.IpsOnly:
                    nguid = bclient['ip']
                # replace last part of the guid with two segments of the ip
                elif self.IpCombi:
                    i = bclient['ip'].split('.')
                    d = len(i[0])+len(i[1])
                    nguid = guid[:-d]+i[0]+i[1]
                # Some Quake clients don't have a cl_guid, we'll use ip instead, this is pure fallback!
                elif guid == 'unknown':
                    nguid = bclient['ip']

                if nguid != '':
                    guid = nguid

                client = self.clients.newClient(bclient['cid'], name=bclient['name'], ip=bclient['ip'], state=b3.STATE_ALIVE, guid=guid, data={ 'guid' : guid })

        return None

    def OnClientuserinfochanged(self, action, data, match=None):
        #ClientUserinfoChanged: 0 n\xlr8or\t\0\identity\NPC_Sam/sam_gladstone
        try:
            id = self._clientConnectID
        except:
            id = None # We've already connected before

        self._clientConnectID = None

        bclient = self.parseUserInfo(data)
        self.verbose('Parsed user info %s' % bclient)
        if bclient:
            client = self.clients.getByCID(bclient['cid'])

            if id:
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
                #make a new client
                client = self.clients.newClient(bclient['cid'], name=bclient['name'], ip=bclient['ip'],
                                                state=b3.STATE_ALIVE, guid=bclient['cl_guid'],
                                                data={'guid': bclient['cl_guid']})

        if id:
            return b3.events.Event(b3.events.EVT_CLIENT_JOIN, None, client)
        else:
            return None

    # disconnect
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

        self.verbose('Current gameType: %s' % self.game.gameType)
        self.game.startRound()

        return b3.events.Event(b3.events.EVT_GAME_ROUND_START, self.game)

    # say
    def OnSay(self, action, data, match=None):
        #3:59 say: XLR8or: general chat
        msg = string.split(data, ': ', 1)
        if not len(msg) == 2:
            return None

        client = self.clients.getByExactName(msg[0])

        if client:
            self.verbose('OnSay: Client Found: %s' % client.name)
            return b3.events.Event(b3.events.EVT_CLIENT_SAY, msg[1], client)
        else:
            self.verbose('OnSay: No Client Found!')
            return None

    # sayteam
    def OnSayteam(self, action, data, match=None):
        #4:06 sayteam: XLR8or: teamchat
        msg = string.split(data, ': ', 1)
        if not len(msg) == 2:
            return None

        client = self.clients.getByExactName(msg[0])

        if client:
            self.verbose('OnSayTeam: Client Found: %s' % client.name)
            return b3.events.Event(b3.events.EVT_CLIENT_TEAM_SAY, msg[1], client, client.team)
        else:
            self.verbose('OnSayTeam: No Client Found!')
            return None

    # damage
    #hit: 0 0 520 368 0: xlr8or hit xlr8or at location 520 for 368
    #Hit: cid acid hitloc damage aweap: text
    def OnHit(self, action, data, match=None):
        victim = self.clients.getByCID(match.group('cid'))
        if not victim:
            self.debug('No victim')
            #self.OnClientuserinfo(action, data, match)
            return None

        attacker = self.clients.getByCID(match.group('acid'))
        if not attacker:
            self.debug('No attacker')
            return None

        event = b3.events.EVT_CLIENT_DAMAGE

        if attacker.cid == victim.cid:
            event = b3.events.EVT_CLIENT_DAMAGE_SELF
        elif attacker.team != b3.TEAM_UNKNOWN and attacker.team == victim.team:
            event = b3.events.EVT_CLIENT_DAMAGE_TEAM

        victim.hitloc = match.group('hitloc')
        #victim.state = b3.STATE_ALIVE
        return b3.events.Event(event, (match.group('damage'), match.group('aweap'), victim.hitloc), attacker, victim)

    # kill
    #kill: acid cid aweap: <text>
    def OnKill(self, action, data, match=None):
        # kill modes characteristics :
        """
        0:	MOD_UNKNOWN, UNKNOWN
        1:	MOD_KNIFE, Killed by KNIFE
        2:	MOD_M1911A1_PISTOL, Killed by M1911A1_PISTOL
        3:	MOD_USSOCOM_PISTOL, Killed by USSOCOM_PISTOL
        4:	MOD_SILVER_TALON, Killed by SILVER_TALON
        5:	MOD_M590_SHOTGUN, Killed by M590_SHOTGUN
        6:	MOD_MICRO_UZI_SUBMACHINEGUN, Killed by MICRO_UZI_SUBMACHINEGUN
        7:	MOD_M3A1_SUBMACHINEGUN, Killed by M3A1_SUBMACHINEGUN
        8:	MOD_MP5, Killed by MP5
        9:	MOD_USAS_12_SHOTGUN, Killed by USAS_12_SHOTGUN
        10:	MOD_M4_ASSAULT_RIFLE, Killed by M4_ASSAULT_RIFLE
        11:	MOD_AK74_ASSAULT_RIFLE, Killed by AK74_ASSAULT_RIFLE
        12:	MOD_SIG551, Killed by SIG551
        13:	MOD_MSG90A1_SNIPER_RIFLE, Killed by MSG90A1_SNIPER_RIFLE
        14:	MOD_M60_MACHINEGUN, Killed by M60_MACHINEGUN
        15:	MOD_MM1_GRENADE_LAUNCHER, Killed by MM1_GRENADE_LAUNCHER
        16:	MOD_RPG7_LAUNCHER, Killed by RPG7_LAUNCHER
        17:	MOD_M84_GRENADE, Killed by M84_GRENADE
        18:	MOD_SMOHG92_GRENADE, Killed by SMOHG92_GRENADE
        19:	MOD_ANM14_GRENADE, Killed by ANM14_GRENADE
        20:	MOD_M15_GRENADE, Killed by M15_GRENADE
        21:	MOD_WATER, Killed by WATER
        22:	MOD_CRUSH, Killed by Mover
        23:	MOD_TELEFRAG, Killed by TELEFRAG
        24:	MOD_FALLING, Killed by FALLING
        25:	MOD_SUICIDE, Killed by SUICIDE
        26:	MOD_TEAMCHANGE, Killed by TEAMCHANGE
        27:	MOD_TARGET_LASER, Killed by TARGET_LASER
        28:	MOD_TRIGGER_HURT, Killed by TRIGGER_HURT
        29:	MOD_TRIGGER_HURT_NOSUICIDE, Killed by TRIGGER_HURT_NOSUICIDE
        30:	MOD_ADMIN_STRIKE, Killed by ADMIN_STRIKE
        31:	MOD_ADMIN_SLAP, Killed by ADMIN_SLAP
        32:	MOD_ADMIN_FRY, Killed by ADMIN_FRY
        33:	MOD_ADMIN_EXPLODE, Killed by ADMIN_EXPLODE
        34:	MOD_ADMIN_TELEFRAG, Killed by ADMIN_TELEFRAG
        35:	MOD_KNIFE_ALT, Killed by KNIFE_ALT
        36:	MOD_M1911A1_PISTOL_ALT, Killed by M1911A1_PISTOL_ALT
        37:	MOD_USSOCOM_PISTOL_ALT, Killed by USSOCOM_PISTOL_ALT
        38:	MOD_SILVER_TALON_ALT, Killed by SILVER_TALON_ALT
        39:	MOD_M590_SHOTGUN_ALT, Killed by M590_SHOTGUN_ALT
        40:	MOD_M4_ASSAULT_RIFLE_ALT, Killed by M4_ASSAULT_RIFLE_ALT
        41:	MOD_AK74_ASSAULT_RIFLE, Killed by AK74_ASSAULT_RIFLE
        42:	MOD_M84_GRENADE_ALT, Killed by M84_GRENADE_ALT
        43:	MOD_SMOHG92_GRENADE_ALT, Killed by SMOHG92_GRENADE_ALT
        44:	MOD_ANM14_GRENADE_ALT, Killed by ANM14_GRENADE_ALT
        45:	MOD_M15_GRENADE_ALT, Killed by M15_GRENADE_ALT
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
        if match.group('aweap') in (
            self.MOD_MM1_GRENADE_LAUNCHER, self.MOD_RPG7_LAUNCHER, self.MOD_M84_GRENADE, self.MOD_SMOHG92_GRENADE,
            self.MOD_ANM14_GRENADE, self.MOD_M15_GRENADE, self.MOD_WATER, self.MOD_FALLING, self.MOD_SUICIDE,
            self.MOD_TRIGGER_HURT, self.MOD_M4_ASSAULT_RIFLE_ALT, self.MOD_M84_GRENADE_ALT, self.MOD_SMOHG92_GRENADE_ALT
            , self.MOD_ANM14_GRENADE_ALT, self.MOD_M15_GRENADE_ALT):
            # those kills should be considered suicides
            self.debug(
                'OnKill: mm1_grenade_launcher/rpg7_launcher/m84_grenade/smohg92_grenade/anm14/m15_grenade/water/suicide/trigger_hurt/m4_assault_rifle_alt/m84_grenade_alt/smohg92_grenade_alt/anm14_alt/m15_grenade_alt should be suicides')
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
            if weapon == self.MOD_TEAMCHANGE:
                """
                Do not pass a teamchange event here. That event is passed
                shortly after the kill.
                """
                self.verbose('Team Change Event Caught, exiting')
                return None
            else:
                event = b3.events.EVT_CLIENT_SUICIDE
        elif attacker.team != b3.TEAM_UNKNOWN and attacker.team == victim.team:
            event = b3.events.EVT_CLIENT_KILL_TEAM

        # if not logging damage we need a general hitloc (for xlrstats)
        if not hasattr(victim, 'hitloc'):
            victim.hitloc = 'body'

        victim.state = b3.STATE_DEAD
        #self.verbose('OnKill Victim: %s, Attacker: %s, Weapon: %s, Hitloc: %s, dType: %s' % (victim.name, attacker.name, weapon, victim.hitloc, dType))
        # need to pass some amount of damage for the teamkill plugin - 100 is a kill
        return b3.events.Event(event, (100, weapon, victim.hitloc, dType), attacker, victim)

    # item
    def OnItem(self, action, data, match=None):
        #Item: 5 weapon_betty
        cid, item = string.split(data, ' ', 1)
        client = self.clients.getByCID(cid)
        if client:
            #self.verbose('OnItem: %s picked up %s' % (client.name, item) )
            return b3.events.Event(b3.events.EVT_CLIENT_ITEM_PICKUP, item, client)
        return None

    # Translate the gameType to a readable format
    def defineGameType(self, gameTypeInt):
        _gameType = ''
        _gameType = str(gameTypeInt)
        #self.debug('gameTypeInt: %s' % gameTypeInt)

        if gameTypeInt == '0':
            _gameType = 'ass'
        elif gameTypeInt == '1':
            _gameType = 'cnh'
        elif gameTypeInt == '2':
            _gameType = 'ctb'
        elif gameTypeInt == '3':
            _gameType = 'cctf'
        elif gameTypeInt == '4':
            _gameType = 'ctf'
        elif gameTypeInt == '5':
            _gameType = 'dem'
        elif gameTypeInt == '6':
            _gameType = 'dm'
        elif gameTypeInt == '7':
            _gameType = 'dom'
        elif gameTypeInt == '8':
            _gameType = 'elim'
        elif gameTypeInt == '9':
            _gameType = 'gold'
        elif gameTypeInt == '10':
            _gameType = 'inf'
        elif gameTypeInt == '11':
            _gameType = 'knockback'
        elif gameTypeInt == '12':
            _gameType = 'lms'
        elif gameTypeInt == '13':
            _gameType = 'rctf'
        elif gameTypeInt == '14':
            _gameType = 'stq'
        elif gameTypeInt == '15':
            _gameType = 'tctb'
        elif gameTypeInt == '16':
            _gameType = 'tdm'
        elif gameTypeInt == '17':
            _gameType = 'tstq'

        #self.debug('_gameType: %s' % _gameType)
        return _gameType

    def joinPlayers(self):
        plist = self.getPlayerList()

        for cid, c in plist.iteritems():
            client = self.clients.getByCID(cid)
            if client:
                self.debug('Joining %s' % client.name)
                self.queueEvent(b3.events.Event(b3.events.EVT_CLIENT_JOIN, None, client))

        return None

    def queryClientUserInfoByName(self, cid, name):
        """
        ]\dumpuser xlr8or
        Player xlr8or is not on the server

        ]\dumpuser xlr8or
        userinfo
        --------
        ip                  145.99.135.000:-12892
        cl_guid             XXXXD914662572D3649B94B1EA5F921
        cl_punkbuster       0
        details             5
        name                xlr8or
        rate                9000
        snaps               20
        identity            NPC_Sam/sam_gladstone
        cl_anonymous        0
        cg_predictItems     1
        cg_antiLag          1
        cg_autoReload       1
        cg_smoothClients    0
        team_identity       shopguard1
        outfitting          GACAA

        """
        data = self.write('dumpuser %s' % name)
        if not data:
            return None

        if data.split('\n')[0] != "userinfo":
            self.debug("dumpuser %s returned : %s" % (name, data))
            self.debug('client probably disconnected, but its character is still hanging in game...')
            return None

        datatransformed = "%s " % cid
        for line in data.split('\n'):
            if line.strip() == "userinfo" or line.strip() == "--------":
                continue

            var = line[:20].strip()
            val = line[20:].strip()
            datatransformed += "\\%s\\%s" % (var, val)

        #self.debug(datatransformed)
        return datatransformed

    def getByNameOrJoinPlayer(self, name):
        client = self.clients.getByExactName(name)
        if client:
            return client
        else:
            userinfostring = self.queryClientUserInfoByName(name)
            if userinfostring:
                self.OnClientuserinfo(None, userinfostring)
            return self.clients.getByExactName(name)




#HL_FOOT_RT
#HL_FOOT_LT
#HL_LEG_LOWER_RT
#HL_LEG_LOWER_LT
#HL_LEG_UPPER_RT
#HL_LEG_UPPER_LT
#HL_ARM_RT
#HL_ARM_LT
#HL_HAND_RT
#HL_HAND_LT
#HL_HEAD
#HL_NECK
#HL_WAIST
#HL_BACK
#HL_BACK_RT
#HL_BACK_LT
#HL_CHEST
#HL_CHEST_RT
#HL_CHEST_LT

#INSERT INTO `stats_hitlocations` (`ID`, `BODYPART`) VALUES (256, 'right arm');
#INSERT INTO `stats_hitlocations` (`ID`, `BODYPART`) VALUES (32768, 'right chest');
#INSERT INTO `stats_hitlocations` (`ID`, `BODYPART`) VALUES (0, 'Undetected Hits');
#INSERT INTO `stats_hitlocations` (`ID`, `BODYPART`) VALUES (1024, 'Head');
#INSERT INTO `stats_hitlocations` (`ID`, `BODYPART`) VALUES (4, 'upper right Leg');
#INSERT INTO `stats_hitlocations` (`ID`, `BODYPART`) VALUES (8, 'upper left Leg');
#INSERT INTO `stats_hitlocations` (`ID`, `BODYPART`) VALUES (16, 'lower right Leg');
#INSERT INTO `stats_hitlocations` (`ID`, `BODYPART`) VALUES (32, 'lower left Leg');
#INSERT INTO `stats_hitlocations` (`ID`, `BODYPART`) VALUES (262144, 'Neck');
#INSERT INTO `stats_hitlocations` (`ID`, `BODYPART`) VALUES (1, 'right Foot');
#INSERT INTO `stats_hitlocations` (`ID`, `BODYPART`) VALUES (2, 'left Foot');
#INSERT INTO `stats_hitlocations` (`ID`, `BODYPART`) VALUES (512, 'left lower hand');
#INSERT INTO `stats_hitlocations` (`ID`, `BODYPART`) VALUES (128, 'left hand');
#INSERT INTO `stats_hitlocations` (`ID`, `BODYPART`) VALUES (2048, 'Waist');
#INSERT INTO `stats_hitlocations` (`ID`, `BODYPART`) VALUES (131072, 'Chest');
#INSERT INTO `stats_hitlocations` (`ID`, `BODYPART`) VALUES (64, 'right hand');
#INSERT INTO `stats_hitlocations` (`ID`, `BODYPART`) VALUES (4096, 'back right');
#INSERT INTO `stats_hitlocations` (`ID`, `BODYPART`) VALUES (8192, 'back left');
#INSERT INTO `stats_hitlocations` (`ID`, `BODYPART`) VALUES (16384, 'back');
