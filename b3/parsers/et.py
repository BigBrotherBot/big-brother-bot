# BigBrotherBot(B3) (www.bigbrotherbot.net)
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

__author__  = 'ThorN'
__version__ = '0.0.1'

import re, string
import b3
from b3.parsers.q3a.abstractParser import AbstractParser
import PunkBuster

class EtParser(AbstractParser):
    gameName = 'et'
    privateMsg = False
    _settings = {}
    _settings['line_length'] = 65
    _settings['min_wrap_length'] = 90

    _commands = {}
    _commands['message'] = 'qsay %s %s ^8[pm]^7 %s'
    _commands['say'] = 'qsay %s %s'
    _commands['set'] = 'set %s %s'
    _commands['kick'] = 'clientkick %s %s'
    _commands['ban'] = 'banid %s %s'
    _commands['tempban'] = 'clientkick %s %s'

    _eventMap = {
        'warmup' : b3.events.EVT_GAME_WARMUP,
        'restartgame' : b3.events.EVT_GAME_ROUND_END
    }

    # remove the time off of the line
    _lineClear = re.compile(r'^(?:[0-9:.]+\s?)?')

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

    PunkBuster = None

    def startup(self):
        # add the world client
        client = self.clients.newBaseClient()
        client.name = 'World'
        client.cid  = -1
        client.guid = self.gameName + ':WORLD'
        client.maxLevel = -1
        client.hide = True

        self.clients.update(client)

        self.PunkBuster = PunkBuster.PunkBuster(self)

    def message(self, client, text):
        try:
            if client == None:
                self.say(text)
            elif client.cid == None:
                pass
            else:
                lines = []
                for line in self.getWrap(text, self._settings['line_length'], self._settings['min_wrap_length']):
                    lines.append('qsay %s ^8[%s^8]^7 %s' % (self.msgPrefix, client.exactName, line))

                self.writelines(lines)
        except:
            pass

    # join
    #1579:03ConnectInfo: 0: E24F9B2702B9E4A1223E905BF597FA92: ^w[^2AS^w]^2Lead: 3: 3: 24.153.180.106:2794
    def OnConnectinfo(self, action, data, match=None):
        guid = match.group('pbid')
        client = self.clients.getByCID(match.group('cid'))

        if client:
            if client.guid == guid:
                # this is the same player

                if client.exactName != match.group('name'):
                    client.exactName = match.group('name')
                    client.setName(self.stripColors(client.exactName))
                return b3.events.Event(b3.events.EVT_CLIENT_JOIN, None, client)
            else:
                # disconnect the existing client
                self.verbose('disconnect the existing client %s %s => %s %s', match.group('cid'), guid, client.cid, client)
                client.disconnect()

        client = self.clients.newBaseClient()
        client.cid  = match.group('cid')

        #if match.group('guid') == '0':
        #    client.guid = None
        #else:
        client.pbid = client.guid = self.gameName + ':' + guid
        client.ip = match.group('ip')

        client.exactName = match.group('name')
        client.name = self.stripColors(client.exactName)
        self.clients.update(client)

    #1579:03ClientUserinfoChangedGUID: 0 E24F9B2702B9E4A1223E905BF597FA92 n\^w[^2AS^w]^2Lead\t\3\c\3\r\0\m\0000000\s\0000000\dn\\dr\0\w\3\lw\3\sw\7\mu\0\ref\0
    def OnClientuserinfochangedguid(self, action, data, match=None):
        client = self.clients.getByCID(match.group('cid'))
        cid, pbid, data = string.split(data, ' ', 2)
        bclient = self.parseUserInfo(cid + ' ' + data)
        if bclient:
            self.clients.update(bclient, client)

    def OnGib(self, action, data, match=None):
        #1538:42Gib: 5 10 1: ^0Apache Death gibbed ^,^t^9^8that ^2guy by MOD_MACHINEGUN
        victim = self.clients.getByCID(match.group('cid'))
        if not victim:
            self.debug('No victim')
            #self.OnJ(action, data, match)
            return None

        attacker = self.clients.getByCID(match.group('acid'))
        if not attacker:
            self.debug('No attacker')
            return None

        event = b3.events.EVT_CLIENT_GIB

        if attacker.cid == victim.cid:
            event = b3.events.EVT_CLIENT_GIB_SELF
        elif attacker.team != b3.TEAM_UNKNOWN and attacker.team == victim.team:
            event = b3.events.EVT_CLIENT_GIB_TEAM

        return b3.events.Event(event, (100, match.group('aweap'), ''), attacker, victim)

    def OnKill(self, action, data, match=None):
        #1536:37Kill: 1 18 9: ^1klaus killed ^1[pura]fox.nl by MOD_MP40
        victim = self.clients.getByCID(match.group('cid'))
        if not victim:
            self.debug('No victim')
            #self.OnJ(action, data, match)
            return None

        attacker = self.clients.getByCID(match.group('acid'))
        if not attacker:
            self.debug('No attacker')
            return None

        event = b3.events.EVT_CLIENT_KILL

        if attacker.cid == victim.cid:
            event = b3.events.EVT_CLIENT_SUICIDE
        elif attacker.team != b3.TEAM_UNKNOWN and attacker.team == victim.team:
            event = b3.events.EVT_CLIENT_KILL_TEAM

        return b3.events.Event(event, (100, match.group('aweap'), ''), attacker, victim)

    def OnSayteamc(self, action, data, match=None):
        #1536:34sayteamc: 17: ^1[^7DP^1]^4Timekiller: ^4ammo ^2here !!!!!
        client = self.clients.getByCID(match.group('cid'))
        if not client:
            self.debug('No client - attempt join')
            #self.OnJ(action, data, match)
            #client = self.clients.getByCID(match.group('cid'))
            #if not client:
            return None

        return b3.events.Event(b3.events.EVT_CLIENT_TEAM_SAY, match.group('text'), client)

    def OnSayc(self, action, data, match=None):
        #1536:17sayc: 0: ^w[^2AS^w]^2Lead:  sorry...
        client = self.clients.getByCID(match.group('cid'))
        if not client:
            self.debug('No client - attempt join')
            #self.OnJ(action, data, match)
            #client = self.clients.getByCID(match.group('cid'))
            #if not client:
            return None

        return b3.events.Event(b3.events.EVT_CLIENT_SAY, match.group('text'), client)