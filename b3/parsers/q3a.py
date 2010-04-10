#
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
# $Id: q3a.py 103 2006-04-14 16:23:10Z thorn $
#
# CHANGELOG
#
#    2010/04/10 - 1.4.2 - Bakes
#    * saybig() function can now be used by plugins. Since basic q3 games (such as CoD)
#      cannot print to the centre of the screen, it performs the same function as the scream
#      command.
#    2010/03/22 - 1.4.1 - Courgette
#    * fix conflict between 1.3.4 and 1.4. 
#    2010/03/21 - 1.4 - Courgette
#    * now implements methods maprotate and changeMap
#    21/03/2010 - 1.3.4 - Bakes
#    * rotateMap() function added to make the admin plugin more BFBC2-compatible.
#    31/01/2010 - 1.3.3 -  xlr8or
#    * Fixed a few  typos
#    26/01/2010 - 1.3.2 -  xlr8or
#    * added maxRetries=4 to authorizeClients()
#    * getMap() was moved from iourt to q3a
#    12/06/2009 - 1.3.1 - Courgette
#    * getPlayerList can be called with a custom maxRetries value. This can be
#    useful when a map just changed and the gameserver hangs for a while.
#    11/11/2009 - 1.3.0 - Courgette
#    * New feature: Allow action names to contain spaces. In that case the action
#      method is built following a CamelCase syntax. IE: action "Flag return" will
#      call the method named "OnFlagReturn"
#    2/27/2009 - 1.2.3 - xlr8or
#    Removed error message for getPlayerList(), getPlayerPings() and getPlayerScores()
#    5/6/2008 - 1.2.2 - Anubis
#    Added OnShutdowngame()
#    5/6/2008 - 1.2.1 - xlr8or
#    Modified _reColor to strip Ascii > 127 also
#    12/2/2005 - 1.1.0 - ThorN
#    Fixed getCvar() regular expression
#    11/29/2005 - 1.1.0 - ThorN
#    Added setCvar() and fixed getCvar()
#    7/23/2005 - 1.0.1 - ThorN
#    Added log message for when ban() decides to do a tempban



__author__  = 'ThorN'
__version__ = '1.4.2'

import re, string, time
import b3
import b3.events
from b3.parsers.punkbuster import PunkBuster
import b3.parsers.q3a_rcon
import b3.parser
import b3.cvar

#----------------------------------------------------------------------------------------------------------------------------------------------
class Q3AParser(b3.parser.Parser):
    gameName = 'q3a'
    privateMsg = True
    OutputClass = b3.parsers.q3a_rcon.Rcon

    _settings = {}
    _settings['line_length'] = 65
    _settings['min_wrap_length'] = 100

    _commands = {}
    _commands['message'] = 'tell %s %s ^8[pm]^7 %s'
    _commands['deadsay'] = 'tell %s %s [DEAD]^7 %s'
    _commands['say'] = 'say %s %s'
    _commands['set'] = 'set %s %s'
    _commands['kick'] = 'clientkick %s %s'
    _commands['ban'] = 'banid %s %s'
    _commands['tempban'] = 'clientkick %s %s'

    _eventMap = {
        'warmup' : b3.events.EVT_GAME_WARMUP,
        'shutdowngame' : b3.events.EVT_GAME_ROUND_END
    }

    # remove the time off of the line
    _lineClear = re.compile(r'^(?:[0-9:]+\s?)?')
    _lineTime  = re.compile(r'^(?P<minutes>[0-9]+):(?P<seconds>[0-9]+).*')

    _lineFormats = (
        #1579:03ConnectInfo: 0: E24F9B2702B9E4A1223E905BF597FA92: ^w[^2AS^w]^2Lead: 3: 3: 24.153.180.106:2794
        re.compile(r'^(?P<action>[a-z]+):\s*(?P<data>(?P<cid>[0-9]+):\s*(?P<pbid>[0-9A-Z]{32}):\s*(?P<name>[^:]+):\s*(?P<num1>[0-9]+):\s*(?P<num2>[0-9]+):\s*(?P<ip>[0-9.]+):(?P<port>[0-9]+))$', re.IGNORECASE),
        #1536:17sayc: 0: ^w[^2AS^w]^2Lead:  sorry...
        #1536:34sayteamc: 17: ^1[^7DP^1]^4Timekiller: ^4ammo ^2here !!!!!
        re.compile(r'^(?P<action>[a-z]+):\s*(?P<data>(?P<cid>[0-9]+):\s*(?P<name>.+):\s+(?P<text>.*))$', re.IGNORECASE),
        #1536:37Kill: 1 18 9: ^1klaus killed ^1[pura]fox.nl by MOD_MP40
        re.compile(r'^(?P<action>[a-z]+):\s*(?P<data>(?P<cid>[0-9]+)\s(?P<acid>[0-9]+)\s(?P<aweap>[0-9]+):\s*(?P<text>.*))$', re.IGNORECASE),
        re.compile(r'^(?P<action>[a-z]+):\s*(?P<data>(?P<cid>[0-9]+):\s*(?P<text>.*))$', re.IGNORECASE),
        re.compile(r'^(?P<action>[a-z]+):\s*(?P<data>(?P<cid>[0-9]+)\s(?P<text>.*))$', re.IGNORECASE),
        re.compile(r'^(?P<action>[a-z]+):\s*(?P<data>.*)$', re.IGNORECASE)
    )
    
    #num score ping guid   name            lastmsg address               qport rate
    #--- ----- ---- ------ --------------- ------- --------------------- ----- -----
    #2     0   29 465030 <-{^4AS^7}-^3ThorN^7->^7       50 68.63.6.62:-32085      6597  5000
    #_regPlayer = re.compile(r'^(?P<slot>[0-9]+)\s+(?P<score>[0-9-]+)\s+(?P<ping>[0-9]+)\s+(?P<guid>[0-9]+)\s+(?P<name>.*?)\s+(?P<last>[0-9]+)\s+(?P<ip>[0-9.]+):(?P<port>[0-9-]+)\s+(?P<qport>[0-9]+)\s+(?P<rate>[0-9]+)$', re.I)
    _regPlayer = re.compile(r'^(?P<slot>[0-9]+)\s+(?P<score>[0-9-]+)\s+(?P<ping>[0-9]+)\s+(?P<guid>[0-9a-zA-Z]+)\s+(?P<name>.*?)\s+(?P<last>[0-9]+)\s+(?P<ip>[0-9.]+):(?P<port>[0-9-]+)\s+(?P<qport>[0-9]+)\s+(?P<rate>[0-9]+)$', re.I)

    _regPlayerShort = re.compile(r'\s+(?P<slot>[0-9]+)\s+(?P<score>[0-9]+)\s+(?P<ping>[0-9]+)\s+(?P<name>.*)\^7\s+', re.I)
    _reColor = re.compile(r'(\^[0-9a-z])|[\x80-\xff]')
    _reCvarName = re.compile(r'^[a-z0-9_.]+$', re.I)
    _reCvar = re.compile(r'^"(?P<cvar>[a-z0-9_.]+)"\s+is:\s*"(?P<value>.*?)(\^7)?"\s+default:\s*"(?P<default>.*?)(\^7)?"$', re.I)
    _reMapNameFromStatus = re.compile(r'^map:\s+(?P<map>.+)$', re.I)

    PunkBuster = None

    def startup(self):
        # add the world client
        client = self.clients.newClient(1022, guid='WORLD', name='World', hide=True, pbid='WORLD')

        if self.config.has_option('server', 'punkbuster') and self.config.getboolean('server', 'punkbuster'):
            self.PunkBuster = PunkBuster(self)

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
        elif '------' not in line:
            self.verbose('line did not match format: %s' % line)

    def parseLine(self, line):           
        m = self.getLineParts(line)
        if not m:
            return False

        match, action, data, client, target = m

        func = 'On%s' % string.capwords(action).replace(' ','')
        
        #self.debug("-==== FUNC!!: " + func)
        
        if hasattr(self, func):
            func = getattr(self, func)
            event = func(action, data, match)

            if event:
                self.queueEvent(event)
        elif action in self._eventMap:
            self.queueEvent(b3.events.Event(
                    self._eventMap[action],
                    data,
                    client,
                    target
                ))
        else:
            self.queueEvent(b3.events.Event(
                    b3.events.EVT_UNKNOWN,
                    str(action) + ': ' + str(data),
                    client,
                    target
                ))

    def getClient(self, match=None, attacker=None, victim=None):
        """Get a client object using the best availible data"""
        if attacker:
            return self.clients.getByCID(attacker.group('acid'))
        elif victim:
            return self.clients.getByCID(victim.group('cid'))
        elif match:
            return self.clients.getByCID(match.group('cid'))

    #----------------------------------
    def OnSay(self, action, data, match=None):
        """\
        if self.type == b3.COMMAND:
            # we really need the second line
            text = self.read()
            if text:
                msg = string.split(text[:-1], '^7: ', 1)
                if not len(msg) == 2:
                    return None
        else:
        """
        msg = string.split(data, ': ', 1)
        if not len(msg) == 2:
            return None

        client = self.clients.getByExactName(msg[0])

        return b3.events.Event(b3.events.EVT_CLIENT_SAY, msg[1], client)

    def OnShutdowngame(self, action, data, match=None):
        #self.game.mapEnd()
        #self.clients.sync()
        return b3.events.Event(b3.events.EVT_GAME_ROUND_END, data)

    def OnClientdisconnect(self, action, data, match=None):
        client = self.getClient(match)
        if client: client.disconnect()
        return None

    def OnSayteam(self, action, data, match=None):
        msg = string.split(data, ': ', 1)
        if not len(msg) == 2:
            return None

        client = self.clients.getByName(msg[0])

        if client:
            return b3.events.Event(b3.events.EVT_CLIENT_TEAM_SAY, msg[1], client, client.team)
        else:
            return None

    def OnExit(self, action, data, match=None):
        self.game.mapEnd()
        return b3.events.Event(b3.events.EVT_GAME_EXIT, None)

    def OnItem(self, action, data, match=None):
        client = self.getClient(match)
        if client:
            return b3.events.Event(b3.events.EVT_CLIENT_ITEM_PICKUP, match.group('text'), client)
        return None

    def OnClientbegin(self, action, data, match=None):
        # we get user info in two parts:
        # 19:42.36 ClientBegin: 4
        # 19:42.36 Userinfo: \cg_etVersion\ET Pro, ET 2.56\cg_u
        # we need to store the ClientConnect ID for the next call to userinfo

        self._clientConnectID = data

        return None

    def OnClientconnect(self, action, data, match=None):
        # we get user info in two parts:
        # 19:42.36 ClientConnect: 4
        # 19:42.36 Userinfo: \cg_etVersion\ET Pro, ET 2.56\cg_u
        # we need to store the ClientConnect ID for the next call to userinfo

        self._clientConnectID = data

        return None

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
                client = self.clients.newClient(bclient['cid'], **bclient)

        return None

    def OnClientuserinfochanged(self, action, data, match=None):
        return self.OnClientuserinfo(action, data, match)

    def OnUserinfo(self, action, data, match=None):
        #f = re.findall(r'\\name\\([^\\]+)', data)

        #if f:
        #    client = self.clients.getByExactName(f[0])
        #    if client:

        try:
            id = self._clientConnectID
        except:
            id = None

        self._clientConnectID = None

        if not id:
            self.error('OnUserinfo called without a ClientConnect ID')
            return None

        return self.OnClientuserinfo(action, '%s %s' % (id, data), match)

    def OnKill(self, action, data, match=None):
        #Kill: 1022 0 6: <world> killed <-NoX-ThorN-> by MOD_FALLING
        #20:26.59 Kill: 3 2 9: ^9n^2@^9ps killed [^0BsD^7:^0Und^7erKo^0ver^7] by MOD_MP40
        #m = re.match(r'^([0-9]+)\s([0-9]+)\s([0-9]+): (.*?) killed (.*?) by ([A-Z_]+)$', data)

        attacker = self.getClient(attacker=match)
        if not attacker:
            self.bot('No attacker')
            return None

        victim = self.getClient(victim=match)
        if not victim:
            self.bot('No victim')
            return None

        return b3.events.Event(b3.events.EVT_CLIENT_KILL, (100, match.group('aweap'), None), attacker, victim)

    def OnInitgame(self, action, data, match=None):
        options = re.findall(r'\\([^\\]+)\\([^\\]+)', data)

        for o in options:
            if o[0] == 'mapname':
                self.game.mapName = o[1]
            elif o[0] == 'g_gametype':
                self.game.gameType = o[1]
            elif o[0] == 'fs_game':
                self.game.modName = o[1]
            else:
                setattr(self.game, o[0], o[1])

        self.game.startRound()

        return b3.events.Event(b3.events.EVT_GAME_ROUND_START, self.game)

    #----------------------------------
    def parseUserInfo(self, info):
        #0 \g_password\none\cl_guid\0A337702493AF67BB0B0F8565CE8BC6C\cl_wwwDownload\1\name\thorn\rate\25000\snaps\20\cl_anonymous\0\cl_punkbuster\1\password\test\protocol\83\qport\16735\challenge\-79719899\ip\69.85.205.66:27960
        playerID, info = string.split(info, ' ', 1)

        if info[:1] != '\\':
            info = '\\' + info

        options = re.findall(r'\\([^\\]+)\\([^\\]+)', info)

        data = {}
        for o in options:
            data[o[0]] = o[1]

        if data.has_key('n'):
            data['name'] = data['n']

        t = None
        if data.has_key('team'):
            t = data['team']
        elif data.has_key('t'):
            t = data['t']

        data['team'] = self.getTeam(t)

        if data.has_key('cl_guid') and not data.has_key('pbid'):
            data['pbid'] = data['cl_guid']

        return data

    def getTeam(self, team):
        team = int(team)
        if team == 1:
            return b3.TEAM_RED
        elif team == 2:
            return b3.TEAM_BLUE
        elif team == 3:
            return b3.TEAM_SPEC
        else:
            return b3.TEAM_UNKNOWN


    def message(self, client, text):
        try:
            if client == None:
                self.say(text)
            elif client.cid == None:
                pass
            else:
                lines = []
                for line in self.getWrap(text, self._settings['line_length'], self._settings['min_wrap_length']):
                    lines.append(self.getCommand('message', cid=client.cid, prefix=self.msgPrefix, message=line))

                self.writelines(lines)
        except:
            pass

    def say(self, msg):
        lines = []
        for line in self.getWrap(msg, self._settings['line_length'], self._settings['min_wrap_length']):
            lines.append(self.getCommand('say', prefix=self.msgPrefix, message=line))

        if len(lines):        
            self.writelines(lines)
    
    def saybig(self, msg):
        for c in range(1,6):
            self.say('^%i%s' % (c, msg))
            time.sleep(delay)


    def smartSay(self, client, msg):
        if client and (client.state == b3.STATE_DEAD or client.team == b3.TEAM_SPEC):
            self.verbose('say dead state: %s, team %s', client.state, client.team)
            self.sayDead(msg)
        else:
            self.verbose('say all')
            self.say(msg)

    def sayDead(self, msg):
        wrapped = self.getWrap(msg, self._settings['line_length'], self._settings['min_wrap_length'])
        lines = []
        for client in self.clients.getClientsByState(b3.STATE_DEAD):
            if client.cid:                
                for line in wrapped:
                    lines.append(self.getCommand('deadsay', cid=client.cid, prefix=self.msgPrefix, message=line))

        if len(lines):        
            self.writelines(lines)

    def kick(self, client, reason='', admin=None, silent=False, *kwargs):
        if isinstance(client, str) and re.match('^[0-9]+$', client):
            self.write(self.getCommand('kick', cid=client, reason=reason))
            return
        elif admin:
            reason = self.getMessage('kicked_by', client.exactName, admin.exactName, reason)
        else:
            reason = self.getMessage('kicked', client.exactName, reason)

        if self.PunkBuster:
            self.PunkBuster.kick(client, 0.5, reason)
        else:
            self.write(self.getCommand('kick', cid=client.cid, reason=reason))

        if not silent:
            self.say(reason)

        self.queueEvent(b3.events.Event(b3.events.EVT_CLIENT_KICK, reason, client))
        client.disconnect()

    def ban(self, client, reason='', admin=None, silent=False, *kwargs):
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

        if self.PunkBuster:
            self.PunkBuster.ban(client, reason)
            # bans will only last 7 days, this is a failsafe incase a ban cant
            # be removed from punkbuster
            #self.PunkBuster.kick(client, 1440 * 7, reason)
        else:
            self.write(self.getCommand('ban', cid=client.cid, reason=reason))

        if not silent:
            self.say(reason)

        self.queueEvent(b3.events.Event(b3.events.EVT_CLIENT_BAN, reason, client))
        client.disconnect()

    def unban(self, client, reason='', admin=None, silent=False, *kwargs):
        if self.PunkBuster:
            if client.pbid:
                result = self.PunkBuster.unBanGUID(client)

                if result:                    
                    admin.message('^3Unbanned^7: %s^7: %s' % (client.exactName, result))

                if not silent:
                    if admin:
                        self.say(self.getMessage('unbanned_by', client.exactName, admin.exactName, reason))
                    else:
                        self.say(self.getMessage('unbanned', client.exactName, reason))
            elif admin:
                admin.message('%s^7 unbanned but has no punkbuster id' % client.exactName)
        elif admin:
            admin.message('^3Unbanned^7: %s^7. You may need to manually remove the user from the game\'s ban file.' % client.exactName)

    def tempban(self, client, reason='', duration=2, admin=None, silent=False, *kwargs):
        duration = b3.functions.time2minutes(duration)

        if isinstance(client, b3.clients.Client) and not client.guid:
            # client has no guid, kick instead
            return self.kick(client, reason, admin, silent)
        elif isinstance(client, str) and re.match('^[0-9]+$', client):
            self.write(self.getCommand('tempban', cid=client, reason=reason))
            return
        elif admin:
            reason = self.getMessage('temp_banned_by', client.exactName, admin.exactName, b3.functions.minutesStr(duration), reason)
        else:
            reason = self.getMessage('temp_banned', client.exactName, b3.functions.minutesStr(duration), reason)

        if self.PunkBuster:
            # punkbuster acts odd if you ban for more than a day
            # tempban for a day here and let b3 re-ban if the player
            # comes back
            if duration > 1440:
                duration = 1440

            self.PunkBuster.kick(client, duration, reason)
        else:
            self.write(self.getCommand('tempban', cid=client.cid, reason=reason))

        if not silent:
            self.say(reason)

        self.queueEvent(b3.events.Event(b3.events.EVT_CLIENT_BAN_TEMP, reason, client))
        client.disconnect()

    def rotateMap(self):
        self.say('^7Changing map to next map')
        time.sleep(1)
        self.write('map_rotate 0')
        
    def changeMap(self, map):
        self.say('^7Changing map to %s' % map)
        time.sleep(1)
        self.write('map %s' % map)

    def getPlayerPings(self):
        data = self.write('status')
        if not data:
            return {}

        players = {}
        for line in data.split('\n'):
            #self.debug('Line: ' + line + "-")
            m = re.match(self._regPlayerShort, line)
            if not m:
                m = re.match(self._regPlayer, line.strip())
            
            if m:
                players[str(m.group('slot'))] = int(m.group('ping'))
            #elif '------' not in line and 'map: ' not in line and 'num score ping' not in line:
                #self.verbose('getPlayerScores() = Line did not match format: %s' % line)
        
        return players
        
    def getPlayerScores(self):
        data = self.write('status')
        if not data:
            return {}

        players = {}
        for line in data.split('\n'):
            #self.debug('Line: ' + line + "-")
            m = re.match(self._regPlayerShort, line)
            if not m:
                m = re.match(self._regPlayer, line.strip())
            
            if m:  
                players[str(m.group('slot'))] = int(m.group('score'))
            #elif '------' not in line and 'map: ' not in line and 'num score ping' not in line:
                #self.verbose('getPlayerScores() = Line did not match format: %s' % line)
        
        return players
        
    def getPlayerScoressssss(self):
        plist = self.getPlayerListRcon()
        scorelist = {}

        for cid, c in plist.iteritems():
            client = self.clients.getByCID(cid)
            if client:
                scorelist[str(cid)] = c['score']
        return scorelist
        
    def getPlayerList(self, maxRetries=None):
        if self.PunkBuster:
            return self.PunkBuster.getPlayerList()
        else:
            data = self.write('status', maxRetries=maxRetries)
            if not data:
                return {}

            players = {}
            for line in data.split('\n')[3:]:
                m = re.match(self._regPlayer, line.strip())
                if m:
                    d = m.groupdict()
                    d['pbid'] = None
                    players[str(m.group('slot'))] = d
                #elif '------' not in line and 'map: ' not in line and 'num score ping' not in line:
                    #self.verbose('getPlayerList() = Line did not match format: %s' % line)

        return players

    def getCvar(self, cvarName):
        if self._reCvarName.match(cvarName):
            #"g_password" is:"^7" default:"scrim^7"
            val = self.write(cvarName)
            self.debug('Get cvar %s = [%s]', cvarName, val)
            #sv_mapRotation is:gametype sd map mp_brecourt map mp_carentan map mp_dawnville map mp_depot map mp_harbor map mp_hurtgen map mp_neuville map mp_pavlov map mp_powcamp map mp_railyard map mp_rocket map mp_stalingrad^7 default:^7

            m = self._reCvar.match(val)
            if m and m.group('cvar').lower() == cvarName.lower():
                return b3.cvar.Cvar(m.group('cvar'), value=m.group('value'), default=m.group('default'))

        return None

    def set(self, cvarName, value):
        self.warning('Parser.set() is depreciated, use Parser.setCvar() instead')
        self.setCvar(cvarName, value)

    def setCvar(self, cvarName, value):
        if re.match('^[a-z0-9_.]+$', cvarName, re.I):
            self.debug('Set cvar %s = [%s]', cvarName, value)
            self.write(self.getCommand('set', name=cvarName, value=value))
        else:
            self.error('%s is not a valid cvar name', cvarName)

    def getMap(self):
        data = self.write('status')
        if not data:
            return None

        line = data.split('\n')[0]
        #self.debug('[%s]'%line.strip())

        m = re.match(self._reMapNameFromStatus, line.strip())
        if m:
            return str(m.group('map'))

        return None

    def getMaps(self):
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

    def authorizeClients(self):
        players = self.getPlayerList(maxRetries=4)
        self.verbose('authorizeClients() = %s' % players)

        for cid, p in players.iteritems():
            sp = self.clients.getByCID(cid)
            if sp:
                # Only set provided data, otherwise use the currently set data
                sp.ip   = p.get('ip', sp.ip)
                sp.pbid = p.get('pbid', sp.pbid)
                sp.guid = p.get('guid', sp.guid)
                sp.data = p
                sp.auth()
