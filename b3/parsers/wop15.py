#
# World of Padman parser for BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2008 Mark Weirath (xlr8or@xlr8or.com)
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
# 2011-04-04 - 1.1.0 - Courgette
#  * remove inheritence from WopParser
#  * made changes introduced with Wop 1.5.2 beta
# 

__author__  = 'xlr8or, Courgette'
__version__ = '1.1.0'

from b3.parsers.q3a.abstractParser import AbstractParser
import re, string
import b3
import b3.events
from b3.events import EVT_GAME_WARMUP, EVT_GAME_ROUND_END

#----------------------------------------------------------------------------------------------------------------------------------------------
class Wop15Parser(AbstractParser):
    gameName = 'wop15'

    _settings = {}
    _settings['line_length'] = 65
    _settings['min_wrap_length'] = 100

    _commands = {}
    _commands['message'] = 'stell %(cid)s %(prefix)s ^3[pm]^7 %(message)s'
    _commands['deadsay'] = 'stell %(cid)s %(prefix)s [DEAD]^7 %(message)s'
    _commands['say'] = 'ssay %(prefix)s^7 %(message)s'

    _commands['set'] = 'set %(name)s "%(value)s"'
    _commands['kick'] = 'clientkick %(cid)s'
    _commands['ban'] = 'addip %(cid)s'
    _commands['tempban'] = 'clientkick %(cid)s'


    _eventMap = {
        'warmup' : EVT_GAME_WARMUP,
        'shutdowngame' : EVT_GAME_ROUND_END
    }

    # remove the time off of the line
    _lineClear = re.compile(r'^(?:[0-9:]+\s?)?')
    #0:00 ClientUserinfo: 0:

    _lineFormats = (
        #Generated with : WOP version 1.5
        #ClientConnect: 0 014D28A78B194CDA9CED1344D47B903B 84.167.190.158
        re.compile(r'^(?P<action>[a-z]+):\s(?P<data>(?P<cid>[0-9]+)\s(?P<cl_guid>[0-9a-z]{32})\s+(?P<ip>[0-9.]+))$', re.IGNORECASE),
        #ClientConnect: 2  151.16.71.226
        re.compile(r'^(?P<action>[a-z]+):\s(?P<data>(?P<cid>[0-9]+)\s+(?P<ip>[0-9.]+))$', re.IGNORECASE),
        #Bot connecting
        #ClientConnect: 0
        re.compile(r'^(?P<action>ClientConnect):\s*(?P<data>(?P<bcid>[0-9]+))$', re.IGNORECASE),
        #Damage: 2 1022 2 50 7
        re.compile(r'^(?P<action>Damage):\s*(?P<data>(?P<cid>[0-9]+)\s+(?P<aweap>[0-9a-z_]+)\s+(?P<acid>[0-9]+)\s+(?P<damage>\d+)\s+(?P<meansofdeath>\d+))$', re.IGNORECASE),
        #Kill: $attacker-cid $means-of-death $target-cid
        #Kill: 2 MOD_INJECTOR 0
        re.compile(r'^(?P<action>[a-z]+):\s*(?P<data>(?P<acid>[0-9]+)\s(?P<aweap>[0-9a-z_]+)\s(?P<cid>[0-9]+))$', re.IGNORECASE),
        #Say: 0 insta machen?
        #Item: 3 ammo_spray_n
        re.compile(r'^(?P<action>[a-z]+):\s*(?P<data>.*)$', re.IGNORECASE),
    )

    #status
    #map: wop_padcloisterctl
    #num score team ping name            lastmsg address               qport rate
    #--- ----- ---- ---- --------------- ------- --------------------- ----- -----
    #  0     0    2    0 ^0PAD^4MAN^7           50 bot                       0 16384
    #  1     0    3   43 PadPlayer^7           0 2001:41b8:9bf:fe04:f40c:d4ff:fe2b:6af9 45742 90000
    _regPlayer = re.compile(r'^(?P<slot>[0-9]+)\s+(?P<score>[0-9-]+)\s+(?P<team>[0-9]+)\s+(?P<ping>[0-9]+)\s+(?P<name>.*?)\s+(?P<last>[0-9]+)\s+(?P<ip>[0-9.]+)\s+(?P<qport>[0-9]+)\s+(?P<rate>[0-9]+)$', re.I)

    _reColor = re.compile(r'(\^.)|[\x00-\x20]|[\x7E-\xff]')

    PunkBuster = None

    #kill modes
    MOD_UNKNOWN='0'
    MOD_SHOTGUN='1'
    MOD_GAUNTLET='2'
    MOD_MACHINEGUN='3'
    MOD_GRENADE='4'
    MOD_GRENADE_SPLASH='5'
    MOD_ROCKET='6'
    MOD_ROCKET_SPLASH='7'
    MOD_PLASMA='8'
    MOD_PLASMA_SPLASH='9'
    MOD_RAILGUN='10'
    MOD_LIGHTNING='11'
    MOD_BFG='12'
    MOD_BFG_SPLASH='13'
    MOD_KILLERDUCKS='14'
    MOD_WATER='15'
    MOD_SLIME='16'
    MOD_LAVA='17'
    MOD_CRUSH='18'
    MOD_TELEFRAG='19'
    MOD_FALLING='20' # not used in wop
    MOD_SUICIDE='21'
    MOD_TARGET_LASER='22' # not used in wop
    MOD_TRIGGER_HURT='23'
    MOD_GRAPPLE='24' # not used in wop


    def startup(self):
        # add the world client
        self.clients.newClient(-1, guid='WORLD', name='World', hide=True)
        self.clients.newClient(1022, guid='ENTITYNUM_WORLD', name='World', hide=True)

        # get map from the status rcon command
        map = self.getMap()
        if map:
            self.game.mapName = map
            self.info('map is: %s'%self.game.mapName)
        
        # initialize connected clients
        plist = self.getPlayerList()
        for cid, c in plist.iteritems():
            userinfostring = self.queryClientUserInfoByCid(cid)
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
        #3 n\Dr.Schraube\t\0\model\padman/padsoldier_red\hmodel\padman/padsoldier_red\c1\4\c2\1\hc\100\w\0\l\0\tt\0\tl\0\sl\
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

        if data.has_key('cl_guid') and not data.has_key('guid'):
            data['guid'] = data['cl_guid']

        return data

    def OnClientconnect(self, action, data, match=None):
        # we get user info in two parts:
        # ClientConnect: 2 77F303414E4355E0860B483F2A07E4DF 151.16.71.226:27960
        # ClientUserinfoChanged: 2 n\^3Ghost^2Pirate\t\0\model\piratpad/ghostpirate_red\hmodel\piratpad/ghostpirate_red\c1\4\c2\0\hc\70\w\0\l\0\skill\    2.00\tt\0\tl\0\sl\
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
        self.verbose('Client Connected cid: %s, guid: %s, ip: %s' % (self._clientConnectID, self._clientConnectGuid, self._clientConnectIp))

    def OnClientuserinfochanged(self, action, data, match=None):
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
                if 'cl_guid' not in bclient:
                    return
                #make a new client
                if "ip" in bclient:
                    client = self.clients.newClient(bclient['cid'], name=bclient['name'], ip=bclient['ip'], state=b3.STATE_ALIVE, guid=bclient['cl_guid'], data={ 'guid' : bclient['cl_guid'] })
                else:
                    client = self.clients.newClient(bclient['cid'], name=bclient['name'], state=b3.STATE_ALIVE, guid=bclient['cl_guid'], data={ 'guid' : bclient['cl_guid'] })

        if id:
            return self.getEvent("EVT_CLIENT_JOIN", None, client)
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
        
        self.debug('Joining Players')
        self.joinPlayers()

        return self.getEvent('EVT_GAME_ROUND_START', self.game)

    # say
    def OnSay(self, action, data, match=None):
        #3:59 say: 1 general chat
        msg = string.split(data, ' ', 1)
        if not len(msg) == 2:
            return None

        client = self.getByCidOrJoinPlayer(msg[0])

        if client:
            self.verbose('Client Found: %s' % client.name)
            return self.getEvent('EVT_CLIENT_SAY', msg[1], client)
        else:
            self.verbose('No Client Found!')
            return None

    # sayteam
    def OnSayteam(self, action, data, match=None):
        #4:06 sayteam: 1 teamchat
        msg = string.split(data, ' ', 1)
        if not len(msg) == 2:
            return None

        client = self.getByCidOrJoinPlayer(msg[0])

        if client:
            self.verbose('Client Found: %s' % client.name)
            return self.getEvent('EVT_CLIENT_TEAM_SAY', msg[1], client, client.team)
        else:
            self.verbose('No Client Found!')
            return None

    #Damage: 2 1022 2 50 7
    def OnDamage(self, action, data, match=None):
        victim = self.getByCidOrJoinPlayer(match.group('cid'))
        if not victim:
            self.debug('No victim')
            #self.OnClientuserinfo(action, data, match)
            return None

        weapon = match.group('aweap')
        if not weapon:
            self.debug('No weapon')
            return None

        ## Fix attacker
        if match.group('aweap') in (self.MOD_WATER,self.MOD_LAVA,self.MOD_FALLING,self.MOD_TRIGGER_HURT,):
            # those kills should be considered suicides
            self.debug('OnDamage: water/lava/falling/trigger_hurt should be inflicted to self')
            attacker = victim
        else:
            attacker = self.getByCidOrJoinPlayer(match.group('acid'))
        ## end fix attacker
          
        if not attacker:
            self.debug('No attacker')
            return None

        event = 'EVT_CLIENT_DAMAGE'

        # fix event for team change and suicides and tk
        if attacker.cid == victim.cid:
            event = 'EVT_CLIENT_DAMAGE_SELF'
        elif attacker.team != b3.TEAM_UNKNOWN and attacker.team == victim.team:
            event = 'EVT_CLIENT_DAMAGE_TEAM'

        # if not logging damage we need a general hitloc (for xlrstats)
        if not hasattr(victim, 'hitloc'):
            victim.hitloc = 'body'
        
        damagepoints = float(match.group('damage'))
        return self.getEvent(event, (damagepoints, weapon, victim.hitloc), attacker, victim)
    
    # kill
    #kill: acid cid aweap
    def OnKill(self, action, data, match=None):
        # kill modes caracteristics :
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
        self.debug('OnKill: %s (%s)'%(match.group('aweap'),match.group('data')))
        
        victim = self.getByCidOrJoinPlayer(match.group('cid'))
        if not victim:
            self.debug('No victim')
            #self.OnClientuserinfo(action, data, match)
            return None

        weapon = match.group('aweap')
        if not weapon:
            self.debug('No weapon')
            return None

        ## Fix attacker
        if match.group('aweap') in (self.MOD_WATER,self.MOD_LAVA,self.MOD_FALLING,self.MOD_TRIGGER_HURT,):
            # those kills should be considered suicides
            self.debug('OnKill: water/lava/falling/trigger_hurt should be suicides')
            attacker = victim
        else:
            attacker = self.getByCidOrJoinPlayer(match.group('acid'))
        ## end fix attacker
          
        if not attacker:
            self.debug('No attacker')
            return None

        event = 'EVT_CLIENT_KILL'

        # fix event for team change and suicides and tk
        if attacker.cid == victim.cid:
            event = 'EVT_CLIENT_SUICIDE'
        elif attacker.team != b3.TEAM_UNKNOWN and attacker.team == victim.team:
            event = 'EVT_CLIENT_KILL_TEAM'

        # if not logging damage we need a general hitloc (for xlrstats)
        if not hasattr(victim, 'hitloc'):
            victim.hitloc = 'body'
        
        victim.state = b3.STATE_DEAD
        #self.verbose('OnKill Victim: %s, Attacker: %s, Weapon: %s, Hitloc: %s, dType: %s' % (victim.name, attacker.name, weapon, victim.hitloc, dType))
        # need to pass some amount of damage for the teamkill plugin - 100 is a kill
        return self.getEvent(event, (100, weapon, victim.hitloc), attacker, victim)

    # item
    def OnItem(self, action, data, match=None):
        #Item: 5 weapon_betty
        cid, item = string.split(data, ' ', 1)
        client = self.getByCidOrJoinPlayer(cid)
        if client:
            #self.verbose('OnItem: %s picked up %s' % (client.name, item) )
            return self.getEvent('EVT_CLIENT_ITEM_PICKUP', item, client)
        return None

    # Translate the gameType to a readable format
    # //WoP gametypes: 0=FFA / 1=1v1 / 2=SP / 3=SYC-FFA / 4=LPS / 5=TDM / 6=CTL / 7=SYC-TP / 8=BB
    def defineGameType(self, gameTypeInt):

        _gameType = ''
        _gameType = str(gameTypeInt)
        #self.debug('gameTypeInt: %s' % gameTypeInt)
        
        if gameTypeInt == '0':
            _gameType = 'dm'
        elif gameTypeInt == '1':
            _gameType = 'lvl'
        elif gameTypeInt == '2':
            _gameType = 'sp'
        elif gameTypeInt == '3':
            _gameType = 'syc-ffa'
        elif gameTypeInt == '4':
            _gameType = 'lps'
        elif gameTypeInt == '5':
            _gameType = 'tdm'
        elif gameTypeInt == '6':
            _gameType = 'ctl'
        elif gameTypeInt == '7':
            _gameType = 'syc-tp'
        elif gameTypeInt == '8':
            _gameType = 'bb'
        
        #self.debug('_gameType: %s' % _gameType)
        return _gameType

    def joinPlayers(self):
        plist = self.getPlayerList()

        for cid, c in plist.iteritems():
            client = self.clients.getByCID(cid)
            if client:
                self.debug('Joining %s' % client.name)
                self.queueEvent(self.getEvent('EVT_CLIENT_JOIN', None, client))

        return None

    def queryClientUserInfoByCid(self, cid):
        """
        : dumpuser 2
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
        data = self.write('dumpuser %s' % cid)
        if not data:
            return None
        
        if data.split('\n')[0] != "userinfo":
            self.debug("dumpuser %s returned : %s" % (cid, data))
            self.debug('client %s probably disconnected, but its character is still hanging in game...' % cid)
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
        client = self.clients.getByCID(cid)
        if client and client.authed:
            return client
        else:
            userinfostring = self.queryClientUserInfoByCid(cid)
            if userinfostring:
                self.OnClientuserinfo(None, userinfostring)
            return self.clients.getByCID(cid)


    def OnClientuserinfo(self, action, data, match=None):
        bclient = self.parseUserInfo(data)
        self.verbose('Parsed user info %s' % bclient)
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
                client = self.clients.newClient(cid, **bclient)

        return None



"""
game log information provided by GedankenBlitz:

stell $cid $text
Serverside tell chat.

ssay $text
Serverside say chat.

sprint $cid $text
Print text to a client. Text will be printed to the upper left chat area.

New loglines;
DropItem: $cid $classname
Award: $cid $awardname
AddScore: $cid $score $reason
Vote: failed timeout
Vote: failed
Vote: passed
CvarChange: $cvar-name $cvar-value
AddTeamScore: $teamname $score $reason
Callvote: $cid $vote

Changed loglines;
Kill: $attacker-cid $means-of-death $target-cid
Teamscores: red $score-red blue $score-blue
Score: $cid $score
Say: $cid $text
SayTeam: $cid $text
Tell: $cid $target-cid $text

rcon status currently includes an extra column for the player team;
map: wop_padcloisterctl
num score team ping name            lastmsg address               qport rate
--- ----- ---- ---- --------------- ------- --------------------- ----- -----
  0     0    2    0 ^0PAD^4MAN^7           50 bot                       0 16384
  1     0    3   43 PadPlayer^7           0 2001:41b8:9bf:fe04:f40c:d4ff:fe2b:6af9 45742 90000

Awardnames are;
excellent
gauntlet
cap
impressive
defend
assist
denied
spraygod
spraykiller
unkown

Teamnames are;
FREE
RED
BLUE
SPECTATOR
This order matches the team numbers, which start with index 0.

Inbuilt score reasons include;
suicide
teamkill
kill
survive
spray
spray_wrongwall
target_score
frag_carrier
carrier_protect
defense
recovery
capture
capture_team
assist_return
assist_frag_carrier
flag
spraykiller
spraygod

Means of death have changed to
MOD_UNKNOWN = 0
MOD_PUMPER
MOD_PUNCHY
MOD_NIPPER
MOD_BALLOONY
MOD_BALLOONY_SPLASH
MOD_BETTY
MOD_BETTY_SPLASH
MOD_BUBBLEG
MOD_BUBBLEG_SPLASH // should be unused
MOD_SPLASHER
MOD_BOASTER
MOD_IMPERIUS
MOD_IMPERIUS_SPLASH
MOD_INJECTOR // new
MOD_KILLERDUCKS
MOD_WATER
MOD_SLIME
MOD_LAVA
MOD_CRUSH
MOD_TELEFRAG
MOD_FALLING   // should be unused
MOD_SUICIDE
MOD_TARGET_LASER
MOD_TRIGGER_HURT
MOD_GRAPPLE   // should be unused
MOD_BAMBAM // new
MOD_BOOMIES // new

Votes depend on the vote of course, an example is;
map wop_dinerbb; set nextmap "wop_padcrashctl"
"""