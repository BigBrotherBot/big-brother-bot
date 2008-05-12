#
# World of Padman parser for BigBrotherBot(B3) (www.bigbrotherbot.com)
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


__author__  = 'xlr8or'
__version__ = '1.0.0'

import b3.parsers.q3a
import re, string
import b3
import b3.events

#----------------------------------------------------------------------------------------------------------------------------------------------
class WopParser(b3.parsers.q3a.Q3AParser):
    gameName = 'wop'

    _settings = {}
    _settings['line_length'] = 65
    _settings['min_wrap_length'] = 100

    _commands = {}
    _commands['message'] = '%(prefix)s^7 %(message)s'
    _commands['deadsay'] = '%(prefix)s [DEAD]^7 %(message)s'
    _commands['say'] = 'say %(prefix)s^7 %(message)s'

    _commands['set'] = 'set %(name)s "%(value)s"'
    _commands['kick'] = 'clientkick %(cid)s'
    _commands['ban'] = 'addip %(cid)s'
    _commands['tempban'] = 'clientkick %(cid)s'

    _eventMap = {
        'warmup' : b3.events.EVT_GAME_WARMUP,
        'shutdowngame' : b3.events.EVT_GAME_ROUND_END
    }

    # remove the time off of the line
    _lineClear = re.compile(r'^(?:[0-9:]+\s?)?')
    #0:00 ClientUserinfo: 0:

    _lineFormats = (
        #Generated with : WOP version 1.2
        #ClientConnect: 2 77F303414E4355E0860B483F2A07E4DF 151.16.71.226:27960
        re.compile(r'^(?P<action>[a-z]+):\s(?P<data>(?P<cid>[0-9]+)\s(?P<cl_guid>[0-9A-Z]{32})\s+(?P<ip>[0-9.]+):(?P<port>[0-9]+))$', re.IGNORECASE),
        #Kill: 3 2 8: Beinchen killed linux suse 10.3 by MOD_PLASMA
        re.compile(r'^(?P<action>[a-z]+):\s*(?P<data>(?P<acid>[0-9]+)\s(?P<cid>[0-9]+)\s(?P<aweap>[0-9]+):\s*(?P<text>.*))$', re.IGNORECASE),
        #ClientConnect: 2  151.16.71.226:27960
        re.compile(r'^(?P<action>[a-z]+):\s(?P<data>(?P<cid>[0-9]+)\s+(?P<ip>[0-9.]+):(?P<port>[0-9]+))$', re.IGNORECASE),
        #say: ^3Ghost^2Pirate: Saw red huh?
        re.compile(r'^(?P<action>say):\s*(?P<data>(?P<name>[^:]+):\s*(?P<text>.*))$', re.IGNORECASE),
        #Bot connecting
        #ClientConnect: 0
        re.compile(r'^(?P<action>ClientConnect):\s*(?P<data>(?P<bcid>[0-9]+))$', re.IGNORECASE),
        #Falling thru? Item stuff and so forth... still need some other actions from CTF and other gametypes to compare.  
        #Item: 3 ammo_spray_n
        re.compile(r'^(?P<action>[a-z]+):\s*(?P<data>.*)$', re.IGNORECASE)
    )
    
    #status
    #map: wop_huette
    #num score ping name            lastmsg address               qport rate
    #--- ----- ---- --------------- ------- --------------------- ----- -----
    #  1    34    0 ^1B^2io^1P^2ad^7      100 bot                       0 16384
    #  2    29    0 ^5Pad^1Lilly^7         50 bot                      53 16384
    #  3     5  103 PadPlayer^7             0 77.41.107.169:27960   47612  5000
    #  4   154   50 WARR^7                 50 91.127.64.194:27960   39880 25000
    _regPlayer = re.compile(r'^(?P<slot>[0-9]+)\s+(?P<score>[0-9-]+)\s+(?P<ping>[0-9]+)\s+(?P<name>.*?)\s+(?P<last>[0-9]+)\s+(?P<ip>[0-9.]+):(?P<port>[0-9-]+)\s+(?P<qport>[0-9]+)\s+(?P<rate>[0-9]+)$', re.I)

    PunkBuster = None

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

        if data.has_key('cl_guid') and not data.has_key('pbid'):
            data['pbid'] = data['cl_guid']

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
                #make a new client
                client = self.clients.newClient(bclient['cid'], name=bclient['name'], ip=bclient['ip'], state=b3.STATE_ALIVE, guid=bclient['cl_guid'], data={ 'guid' : bclient['cl_guid'] })

        if id:
            return b3.events.Event(b3.events.EVT_CLIENT_JOIN, None, client)
        else:
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
            self.verbose('Client Found: %s' % client.name)
            return b3.events.Event(b3.events.EVT_CLIENT_SAY, msg[1], client)
        else:
            self.verbose('No Client Found!')
            return None

    # sayteam
    def OnSayteam(self, action, data, match=None):
        #4:06 sayteam: XLR8or: teamchat
        msg = string.split(data, ': ', 1)
        if not len(msg) == 2:
            return None

        client = self.clients.getByExactName(msg[0])

        if client:
            self.verbose('Client Found: %s' % client.name)
            return b3.events.Event(b3.events.EVT_CLIENT_TEAM_SAY, msg[1], client, client.team)
        else:
            self.verbose('No Client Found!')
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

