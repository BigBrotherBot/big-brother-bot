#
# ioUrT Parser for BigBrotherBot(B3) (www.bigbrotherbot.com)
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
# v1.0.3 - Courgette added support for banlist.txt
#          xlr8or added parsing Damage (OnHit)
# v1.0.4 - xlr8or added EVT_CLIENT_TEAM_CHANGE in OnKill
# v1.0.5 - xlr8or added hitloc and damageType info to accomodate XLRstats
# v1.0.6 - Fixed a bug where the parser wouldn't parse the shutdowngame and warmup functions.

__author__  = 'xlr8or'
__version__ = '1.0.7'

import b3.parsers.q3a
import re, string, threading, time
import b3
import b3.events

#----------------------------------------------------------------------------------------------------------------------------------------------
class Iourt41Parser(b3.parsers.q3a.Q3AParser):
    gameName = 'iourt41'

    _settings = {}
    _settings['line_length'] = 65
    _settings['min_wrap_length'] = 100

    _commands = {}
    _commands['broadcast'] = '%(prefix)s^7 %(message)s'
    _commands['message'] = 'tell %(cid)s %(prefix)s ^3[pm]^7 %(message)s'
    _commands['deadsay'] = 'tell %(cid)s %(prefix)s [DEAD]^7 %(message)s'
    _commands['say'] = 'say %(prefix)s %(message)s'

    _commands['set'] = 'set %(name)s "%(value)s"'
    _commands['kick'] = 'clientkick %(cid)s'
    _commands['ban'] = 'addip %(cid)s'
    _commands['tempban'] = 'clientkick %(cid)s'
    _commands['banByIp'] = 'addip %(ip)s'
    _commands['unbanByIp'] = 'removeip %(ip)s'

    _eventMap = {
        #'warmup' : b3.events.EVT_GAME_WARMUP,
        #'shutdowngame' : b3.events.EVT_GAME_ROUND_END
    }

    # remove the time off of the line
    _lineClear = re.compile(r'^(?:[0-9:]+\s?)?')
    #0:00 ClientUserinfo: 0:

    _lineFormats = (
        #Generated with ioUrbanTerror v4.1:
        #Hit: 12 7 1 19: BSTHanzo[FR] hit ercan in the Helmet
        #Hit: 13 10 0 8: Grover hit jacobdk92 in the Head
        re.compile(r'^(?P<action>[a-z]+):\s(?P<data>(?P<cid>[0-9]+)\s(?P<acid>[0-9]+)\s(?P<hitloc>[0-9]+)\s(?P<aweap>[0-9]+):\s+(?P<text>.*))$', re.IGNORECASE),

        #6:37 Kill: 0 1 16: XLR8or killed =lvl1=Cheetah by UT_MOD_SPAS
        #2:56 Kill: 14 4 21: Qst killed Leftovercrack by UT_MOD_PSG1
        re.compile(r'^(?P<action>[a-z]+):\s(?P<data>(?P<acid>[0-9]+)\s(?P<cid>[0-9]+)\s(?P<aweap>[0-9]+):\s+(?P<text>.*))$', re.IGNORECASE),


        #Processing chats and tell events...
        #5:39 saytell: 15 16 repelSteeltje: nno
        #5:39 saytell: 15 15 repelSteeltje: nno
        re.compile(r'^(?P<action>[a-z]+):\s(?P<data>(?P<cid>[0-9]+)\s(?P<acid>[0-9]+)\s(?P<name>[^:]+):\s+(?P<text>.*))$', re.IGNORECASE),

        # We're not using tell in this form so this one is disabled
        #5:39 tell: repelSteeltje to B!K!n1: nno
        #re.compile(r'^(?P<action>[a-z]+):\s+(?P<data>(?P<name>[^:]+)\s+to\s+(?P<aname>[^:]+):\s+(?P<text>.*))$', re.IGNORECASE),

        #3:53 say: 8 denzel: lol
        #15:37 say: 9 .:MS-T:.BstPL: this name is quite a challenge
        #2:28 sayteam: 12 New_UrT_Player_v4.1: woekele
        re.compile(r'^(?P<action>[a-z]+):\s(?P<data>(?P<cid>[0-9]+)\s(?P<name>[^:]+):\s+(?P<text>.*))$', re.IGNORECASE),

        #Falling thru? Item stuff and so forth... still need some other actions from CTF and other gametypes to compare.  
        re.compile(r'^(?P<action>[a-z]+):\s(?P<data>.*)$', re.IGNORECASE),
        #Shutdowngame and Warmup... the one word lines
        re.compile(r'^(?P<action>[a-z]+):$', re.IGNORECASE)
    )
    
    # 23:17:32 map: ut4_casa
    # num score ping name            lastmsg address               qport rate
    # --- ----- ---- --------------- ------- --------------------- ----- -----
    #   2     0   19 ^1XLR^78^8^9or^7        0 145.99.135.227:27960  41893  8000  # player with a live ping
    #   4     0 CNCT Dz!k^7                450 83.175.191.27:64459   50308 20000  # connecting player (or inbetween rounds)
    #   9     0 ZMBI ^7                   1900 81.178.80.68:27960    10801  8000  # zombies (need to be disconnected!)
    _regPlayer = re.compile(r'^(?P<slot>[0-9]+)\s+(?P<score>[0-9-]+)\s+(?P<ping>[0-9]+|CNCT|ZMBI)\s+(?P<name>.*?)\s+(?P<last>[0-9]+)\s+(?P<ip>[0-9.]+):(?P<port>[0-9-]+)\s+(?P<qport>[0-9]+)\s+(?P<rate>[0-9]+)$', re.I)
    _reCvarName = re.compile(r'^[a-z0-9_.]+$', re.I)
    _reCvar = (
        #"sv_maxclients" is:"16^7" default:"8^7"
        #latched: "12"
        re.compile(r'^"(?P<cvar>[a-z0-9_.]+)"\s+is:\s*"(?P<value>.*?)(\^7)?"\s+default:\s*"(?P<default>.*?)(\^7)?"$', re.I | re.M),
        #"g_maxGameClients" is:"0^7", the default
        #latched: "1"
        re.compile(r'^"(?P<cvar>[a-z0-9_.]+)"\s+is:\s*"(?P<value>.*?)(\^7)?",\s+the\sdefault$', re.I | re.M),
    )

    PunkBuster = None

    ## kill modes
    MOD_WATER='1'
    MOD_LAVA='3'
    MOD_TELEFRAG='5'
    MOD_FALLING='6'
    MOD_SUICIDE='7'
    MOD_TRIGGER_HURT='9'
    MOD_CHANGE_TEAM='10'
    UT_MOD_KNIFE='12'
    UT_MOD_KNIFE_THROWN='13'
    UT_MOD_BERETTA='14'
    UT_MOD_DEAGLE='15'
    UT_MOD_SPAS='16'
    UT_MOD_UMP45='17'
    UT_MOD_MP5K='18'
    UT_MOD_LR300='19'
    UT_MOD_G36='20'
    UT_MOD_PSG1='21'
    UT_MOD_HK69='22'
    UT_MOD_BLED='23'
    UT_MOD_KICKED='24'
    UT_MOD_HEGRENADE='25'
    UT_MOD_SR8='28'
    UT_MOD_AK103='30'
    UT_MOD_SPLODED='31'
    UT_MOD_SLAPPED='32'
    UT_MOD_BOMBED='33'
    UT_MOD_NUKED='34'
    UT_MOD_NEGEV='35'
    UT_MOD_HK69_HIT='37'
    UT_MOD_M4='38'
    UT_MOD_FLAG='39'
    UT_MOD_GOOMBA='40'
    
    def startup(self):
        # add the world client
        client = self.clients.newClient(-1, guid='WORLD', name='World', hide=True, pbid='WORLD')

        if not self.config.has_option('server', 'punkbuster') or self.config.getboolean('server', 'punkbuster'):
            self.PunkBuster = b3.parsers.punkbuster.PunkBuster(self)

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
            try:
                data = m.group('data').strip()
            except:
                data = None
            return (m, m.group('action').lower(), data, client, target)
        elif '------' not in line:
            self.verbose('line did not match format: %s' % line)

    def parseUserInfo(self, info):
        #2 \ip\145.99.135.227:27960\challenge\-232198920\qport\2781\protocol\68\battleye\1\name\[SNT]^1XLR^78or\rate\8000\cg_predictitems\0\snaps\20\model\sarge\headmodel\sarge\team_model\james\team_headmodel\*james\color1\4\color2\5\handicap\100\sex\male\cl_anonymous\0\teamtask\0\cl_guid\58D4069246865BB5A85F20FB60ED6F65
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

        if data.has_key('cl_guid') and not data.has_key('pbid') and self.PunkBuster:
            data['pbid'] = data['cl_guid']

        return data

    def getCvar(self, cvarName):
        if self._reCvarName.match(cvarName):
            #"g_password" is:"^7" default:"scrim^7"
            val = self.write(cvarName)
            self.debug('Get cvar %s = [%s]', cvarName, val)
            #sv_mapRotation is:gametype sd map mp_brecourt map mp_carentan map mp_dawnville map mp_depot map mp_harbor map mp_hurtgen map mp_neuville map mp_pavlov map mp_powcamp map mp_railyard map mp_rocket map mp_stalingrad^7 default:^7

            for f in self._reCvar:
                m = re.match(f, val)
                if m:
                    #self.debug('line matched %s' % f.pattern)
                    break

            if m:
                #self.debug('m.lastindex %s' % m.lastindex)
                if m.group('cvar').lower() == cvarName.lower() and m.lastindex > 3:
                    return b3.cvar.Cvar(m.group('cvar'), value=m.group('value'), default=m.group('default'))
                elif m.group('cvar').lower() == cvarName.lower():
                    return b3.cvar.Cvar(m.group('cvar'), value=m.group('value'), default=m.group('value'))
            else:
                return None

    def getTeam(self, team):
        if team == 'red': team = 1
        if team == 'blue': team = 2
        team = int(team)
        if team == 1:
            return b3.TEAM_RED
        elif team == 2:
            return b3.TEAM_BLUE
        elif team == 3:
            return b3.TEAM_SPEC
        else:
            return b3.TEAM_UNKNOWN

    # Translate the gameType to a readable format (also for teamkill plugin!)
    def defineGameType(self, gameTypeInt):

        _gameType = ''
        _gameType = str(gameTypeInt)
        #self.debug('gameTypeInt: %s' % gameTypeInt)
        
        if gameTypeInt == '0':
            _gameType = 'dm'
        elif gameTypeInt == '1':   # Dunno what this one is
            _gameType = 'dm'
        elif gameTypeInt == '2':   # Dunno either
            _gameType = 'dm'
        elif gameTypeInt == '3':
            _gameType = 'tdm'
        elif gameTypeInt == '4':
            _gameType = 'ts'
        elif gameTypeInt == '5':
            _gameType = 'ftl'
        elif gameTypeInt == '6':
            _gameType = 'cah'
        elif gameTypeInt == '7':
            _gameType = 'ctf'
        elif gameTypeInt == '8':
            _gameType = 'bm'
        
        #self.debug('_gameType: %s' % _gameType)
        return _gameType

    # self.console.broadcast, a variant on self.console.say in UrT. This will print to upper left, the server message area.
    def broadcast(self, msg):
        lines = []
        for line in self.getWrap(msg, self._settings['line_length'], self._settings['min_wrap_length']):
            lines.append(self.getCommand('broadcast', prefix=self.msgPrefix, message=line))

        if len(lines):        
            self.writelines(lines)

#----------------------------------------------------------------------------------

    # Connect/Join
    def OnClientconnect(self, action, data, match=None):
        client = self.clients.getByCID(data)
        return b3.events.Event(b3.events.EVT_CLIENT_JOIN, None, client)


    # Parse Userinfo
    def OnClientuserinfo(self, action, data, match=None):
        bclient = self.parseUserInfo(data)
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
                
                if not bclient.has_key('ip') and guid == 'unknown':
                    # happens when a client is (temp)banned and got kicked so client was destroyed, but
                    # infoline was still waiting to be parsed.
                    self.debug('Client disconnected. Ignoring.')
                    return None
                
                # seems Quake clients don't have a cl_guid, we'll use ip instead!
                if guid == 'unknown':
                    guid = bclient['ip']

                client = self.clients.newClient(bclient['cid'], name=bclient['name'], ip=bclient['ip'], state=b3.STATE_ALIVE, guid=guid, data={ 'guid' : guid })

        return None

    # when userinfo changes
    def OnClientuserinfochanged(self, action, data, match=None):
        return self.OnClientuserinfo(action, data, match)

    # damage
    #Hit: 13 10 0 8: Grover hit jacobdk92 in the Head
    #Hit: cid acid hitloc aweap: text
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
        # need to pass some amount of damage for the teamkill plugin - 15 seems okay
        return b3.events.Event(event, (15, match.group('aweap'), victim.hitloc), attacker, victim)

    # kill
    #6:37 Kill: 0 1 16: XLR8or killed =lvl1=Cheetah by UT_MOD_SPAS
    #6:37 Kill: 7 7 10: Mike_PL killed Mike_PL by MOD_CHANGE_TEAM
    #kill: acid cid aweap: <text>
    def OnKill(self, action, data, match=None):
        # kill modes caracteristics :
        """
        1:      MOD_WATER === exclusive attackers : , 1022(<world>), 0(<non-client>)
        3:      MOD_LAVA === exclusive attackers : , 1022(<world>), 0(<non-client>)
        5:      MOD_TELEFRAG --- normal kill line
        6:      MOD_FALLING === exclusive attackers : , 1022(<world>), 0(<non-client>)
        7:      MOD_SUICIDE ===> attacker is always the victim
        9:      MOD_TRIGGER_HURT === exclusive attackers : , 1022(<world>)
        10:     MOD_CHANGE_TEAM ===> attacker is always the victim
        12:     UT_MOD_KNIFE --- normal kill line
        13:     UT_MOD_KNIFE_THROWN --- normal kill line
        14:     UT_MOD_BERETTA --- normal kill line
        15:     UT_MOD_DEAGLE --- normal kill line
        16:     UT_MOD_SPAS --- normal kill line
        17:     UT_MOD_UMP45 --- normal kill line
        18:     UT_MOD_MP5K --- normal kill line
        19:     UT_MOD_LR300 --- normal kill line
        20:     UT_MOD_G36 --- normal kill line
        21:     UT_MOD_PSG1 --- normal kill line
        22:     UT_MOD_HK69 --- normal kill line
        23:     UT_MOD_BLED --- normal kill line
        24:     UT_MOD_KICKED --- normal kill line
        25:     UT_MOD_HEGRENADE --- normal kill line
        28:     UT_MOD_SR8 --- normal kill line
        30:     UT_MOD_AK103 --- normal kill line
        31:     UT_MOD_SPLODED ===> attacker is always the victim
        32:     UT_MOD_SLAPPED ===> attacker is always the victim
        33:     UT_MOD_BOMBED --- normal kill line
        34:     UT_MOD_NUKED --- normal kill line
        35:     UT_MOD_NEGEV --- normal kill line
        37:     UT_MOD_HK69_HIT --- normal kill line
        38:     UT_MOD_M4 --- normal kill line
        39:     UT_MOD_FLAG === exclusive attackers : , 0(<non-client>)
        40:     UT_MOD_GOOMBA --- normal kill line
        """
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
        if match.group('aweap') in (self.UT_MOD_SLAPPED,self.UT_MOD_NUKED):
            self.debug('OnKill: slap/nuke => attacker should be None')
            attacker = None
        elif match.group('aweap') in (self.MOD_WATER,self.MOD_LAVA,self.MOD_FALLING,self.MOD_TRIGGER_HURT,self.UT_MOD_BOMBED,self.UT_MOD_FLAG):
            # those kills should be considered suicides
            self.debug('OnKill: water/lava/falling/trigger_hurt/bombed/flag should be suicides')
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
            if weapon == self.MOD_CHANGE_TEAM:
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

    # disconnect
    def OnClientdisconnect(self, action, data, match=None):
        client = self.clients.getByCID(data)
        if client: client.disconnect()
        return None

    # Action - NOTDONE
    def OnAction(self, action, data, match=None):
        #Need example
        client = self.clients.getByCID(match.group('cid'))
        if not client:
            self.debug('No client found')
            #self.OnClientuserinfo(action, data, match)
            
            client = self.clients.getByCID(match.group('cid'))

            if not client:
                return None

        client.name = match.group('name')
        data = match.group('data')
        self.verbose('OnAction: %s picked up %s' % (client.name, data) )
        return b3.events.Event(b3.events.EVT_CLIENT_ITEM_PICKUP, data, client)

    # say
    def OnSay(self, action, data, match=None):
        #3:53 say: 8 denzel: lol
        client = self.clients.getByCID(match.group('cid'))

        if not client:
            self.verbose('No Client Found!')
            return None

        self.verbose('Client Found: %s' % client.name)
        data = match.group('text')

        #removal of weird characters
        if data and ord(data[:1]) == 21:
            data = data[1:]

        client.name = match.group('name')
        return b3.events.Event(b3.events.EVT_CLIENT_SAY, data, client)


    # sayteam
    def OnSayteam(self, action, data, match=None):
        #2:28 sayteam: 12 New_UrT_Player_v4.1: wokele
        client = self.clients.getByCID(match.group('cid'))

        if not client:
            self.verbose('No Client Found!')
            return None

        self.verbose('Client Found: %s' % client.name)
        data = match.group('text')
        if data and ord(data[:1]) == 21:
            data = data[1:]

        client.name = match.group('name')
        return b3.events.Event(b3.events.EVT_CLIENT_TEAM_SAY, data, client, client.team)


    # saytell
    def OnSaytell(self, action, data, match=None):
        #5:39 saytell: 15 16 repelSteeltje: nno
        #5:39 saytell: 15 15 repelSteeltje: nno

        #data = match.group('text')
        #if not len(data) >= 2 and not (data[:1] == '!' or data[:1] == '@') and match.group('cid') == match.group('acid'):
        #    return None

        client = self.clients.getByCID(match.group('cid'))
        tclient = self.clients.getByCID(match.group('acid'))

        if not client:
            self.verbose('No Client Found')
            return None

        data = match.group('text')
        if data and ord(data[:1]) == 21:
            data = data[1:]

        client.name = match.group('name')
        return b3.events.Event(b3.events.EVT_CLIENT_PRIVATE_SAY, data, client, tclient)


    # tell
    def OnTell(self, action, data, match=None):
        #5:27 tell: woekele to XLR8or: test
        #We'll use saytell instead
        return None
        """-------------------------------------------------------------------------------
        client = self.clients.getByExactName(match.group('name'))
        tclient = self.clients.getByExactName(match.group('aname'))

        if not client:
            self.verbose('No Client Found')
            return None

        data = match.group('text')
        if data and ord(data[:1]) == 21:
            data = data[1:]

        client.name = match.group('name')
        return b3.events.Event(b3.events.EVT_CLIENT_PRIVATE_SAY, data, client, tclient)
        -------------------------------------------------------------------------------"""

    # endmap/shutdown
    def OnShutdowngame(self, action, data=None, match=None):
        self.debug('EVENT: OnShutdowngame')
        self.game.mapEnd()
        self.clients.sync()
        self.debug('Synchronizing client info')
        return b3.events.Event(b3.events.EVT_GAME_EXIT, data)

    # item
    def OnItem(self, action, data, match=None):
        #Item: 3 ut_item_helmet
        cid, item = string.split(data, ' ', 1)
        client = self.clients.getByCID(cid)
        if client:
            #self.verbose('OnItem: %s picked up %s' % (client.name, item) )
            return b3.events.Event(b3.events.EVT_CLIENT_ITEM_PICKUP, item, client)
        return None

    # Startgame
    def OnInitgame(self, action, data, match=None):
        self.debug('EVENT: OnInitgame')
        options = re.findall(r'\\([^\\]+)\\([^\\]+)', data)

        # capturelimit / fraglimit / timelimit
        for o in options:
            if o[0] == 'mapname':
                self.game.mapName = o[1]
            elif o[0] == 'g_gametype':
                self.game.gameType = self.defineGameType(o[1])
            elif o[0] == 'fs_game':
                self.game.modName = o[1]
            elif o[0] == 'capturelimit':
                self.game.captureLimit = o[1]
            elif o[0] == 'fraglimit':
                self.game.fragLimit = o[1]
            elif o[0] == 'timelimit':
                self.game.timeLimit = o[1]
            else:
                setattr(self.game, o[0], o[1])

        self.verbose('Current gameType: %s' % self.game.gameType)
        self.game.startMap()

        self.game.rounds = 0
        return b3.events.Event(b3.events.EVT_GAME_ROUND_START, self.game)


    # Warmup
    def OnWarmup(self, action, data=None, match=None):
        self.debug('EVENT: OnWarmup')
        self.game.rounds = 0
        return b3.events.Event(b3.events.EVT_GAME_WARMUP, data)

    # Start Round
    def OnInitround(self, action, data, match=None):
        self.debug('EVENT: OnInitround')
        options = re.findall(r'\\([^\\]+)\\([^\\]+)', data)

        # capturelimit / fraglimit / timelimit
        for o in options:
            if o[0] == 'mapname':
                self.game.mapName = o[1]
            elif o[0] == 'g_gametype':
                self.game.gameType = self.defineGameType(o[1])
            elif o[0] == 'fs_game':
                self.game.modName = o[1]
            elif o[0] == 'capturelimit':
                self.game.captureLimit = o[1]
            elif o[0] == 'fraglimit':
                self.game.fragLimit = o[1]
            elif o[0] == 'timelimit':
                self.game.timeLimit = o[1]
            else:
                setattr(self.game, o[0], o[1])

        self.verbose('Current gameType: %s' % self.game.gameType)
        self.game.startRound()
        
        self.clients.sync()
        self.debug('Synchronizing client info')

        return b3.events.Event(b3.events.EVT_GAME_ROUND_START, self.game)

        
    def ban(self, client, reason='', admin=None, silent=False, *kwargs):
        self.debug('BAN : client: %s, reason: %s', client, reason)
        if isinstance(client, b3.clients.Client) and not client.guid:
            # client has no guid, kick instead
            return self.kick(client, reason, admin, silent)
        elif isinstance(client, str) and re.match('^[0-9]+$', client):
            self.write(self.getCommand('ban', cid=client, reason=reason))
            return
        elif not client.id:
            # no client id, database must be down, do tempban
            self.error('Q3AParser.ban(): no client id, database must be down, doing tempban')
            return self.tempban(client, reason, '1d', admin, silent)

        if admin:
            reason = self.getMessage('banned_by', client.exactName, admin.exactName, reason)
        else:
            reason = self.getMessage('banned', client.exactName, reason)

        if client.cid is None:
            # ban by ip, this happens when we !permban @xx a player that is not connected
            self.debug('EFFECTIVE BAN : %s',self.getCommand('banByIp', ip=client.ip, reason=reason))
            self.write(self.getCommand('banByIp', ip=client.ip, reason=reason))
        else:
            # ban by cid
            self.debug('EFFECTIVE BAN : %s',self.getCommand('ban', cid=client.cid, reason=reason))
            self.write(self.getCommand('ban', cid=client.cid, reason=reason))

        if not silent:
            self.say(reason)
            
        if admin:
            admin.message('^3banned^7: ^1%s^7 (^2@%s^7). His last ip (^1%s^7) has been added to banlist'%(client.exactName, client.id, client.ip))

        self.queueEvent(b3.events.Event(b3.events.EVT_CLIENT_BAN, reason, client))
        client.disconnect()

    def unban(self, client, reason='', admin=None, silent=False, *kwargs):
        self.debug('EFFECTIVE UNBAN : %s',self.getCommand('unbanByIp', ip=client.ip, reason=reason))
        self.write(self.getCommand('unbanByIp', ip=client.ip, reason=reason))
        if admin:
            admin.message('^3Unbanned^7: ^1%s^7 (^2@%s^7). His last ip (^1%s^7) has been removed from banlist. Trying to remove duplicates...' % (client.exactName, client.id, client.ip))
        t1 = threading.Timer(1, self._unbanmultiple, (client, admin))
        t1.start()

    def _unbanmultiple(self, client, admin=None):
        # UrT adds multiple instances to banlist.txt Make sure we remove up to 4 remaining duplicates in a separate thread
        c = 0
        while c < 4:
            self.write(self.getCommand('unbanByIp', ip=client.ip))
            time.sleep(2)
            c+=1
        if admin:
            admin.message('^3Unbanned^7: ^1%s^7. Up to 4 possible duplicate entries removed from banlist' % client.exactName )

    def sync(self):
        plist = self.getPlayerList()
        mlist = {}

        for cid, c in plist.iteritems():
            client = self.clients.getByCID(cid)
            if client:
                # Disconnect the zombies first
                if c['ping'] == 'ZMBI':
                    self.debug('zombie found: %s - disconnecting', c['ip'])
                    client.disconnect()
                elif client.guid and c.has_key('guid'):
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
