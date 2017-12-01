# -*- coding: utf-8 -*-

# ################################################################### #
#                                                                     #
#  BigBrotherBot(B3) (www.bigbrotherbot.net)                          #
#  Copyright (C) 2005 Michael "ThorN" Thornton                        #
#                                                                     #
#  This program is free software; you can redistribute it and/or      #
#  modify it under the terms of the GNU General Public License        #
#  as published by the Free Software Foundation; either version 2     #
#  of the License, or (at your option) any later version.             #
#                                                                     #
#  This program is distributed in the hope that it will be useful,    #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of     #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the       #
#  GNU General Public License for more details.                       #
#                                                                     #
#  You should have received a copy of the GNU General Public License  #
#  along with this program; if not, write to the Free Software        #
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA      #
#  02110-1301, USA.                                                   #
#                                                                     #
# ################################################################### #

__author__  = 'ThorN'
__version__ = '0.0.6'

import re
import string
import b3
import b3.clients
import b3.events

from b3.functions import prefixText
from b3.parsers.punkbuster import PunkBuster
from b3.parsers.q3a.abstractParser import AbstractParser

class EtParser(AbstractParser):

    gameName = 'et'
    privateMsg = False
    PunkBuster = None

    _logSync = 2

    _commands = {
        'ban': 'banid %(cid)s %(reason)s',
        'kick': 'clientkick %(cid)s %(reason)s',
        'message': 'qsay %(message)s',
        'say': 'qsay %(message)s',
        'set': 'set %(name)s %(value)s',
        'tempban': 'clientkick %(cid)s %(reason)s'
    }

    _eventMap = {
        #'warmup' : b3.events.EVT_GAME_WARMUP,
        #'restartgame' : b3.events.EVT_GAME_ROUND_END
    }

    # remove the time off of the line
    _lineClear = re.compile(r'^(?:[0-9:.]+\s?)?')

    _lineFormats = (
        # 1579:03ConnectInfo: 0: E24F9B2702B9E4A1223E905BF597FA92: ^w[^2AS^w]^2Lead: 3: 3: 24.153.180.106:2794
        re.compile(r'^(?P<action>[a-z]+):\s*'
                   r'(?P<data>(?P<cid>[0-9]+):\s*'
                   r'(?P<pbid>[0-9A-Z]{32}):\s*'
                   r'(?P<name>[^:]+):\s*'
                   r'(?P<num1>[0-9]+):\s*'
                   r'(?P<num2>[0-9]+):\s*'
                   r'(?P<ip>[0-9.]+):'
                   r'(?P<port>[0-9]+))$', re.IGNORECASE),

        # 1536:17sayc: 0: ^w[^2AS^w]^2Lead:  sorry...
        # 1536:34sayteamc: 17: ^1[^7DP^1]^4Timekiller: ^4ammo ^2here !!!!!
        re.compile(r'^(?P<action>[a-z]+):\s*(?P<data>(?P<cid>[0-9]+):\s*(?P<name>.+):\s+(?P<text>.*))$', re.IGNORECASE),

        # 1536:37Kill: 1 18 9: ^1klaus killed ^1[pura]fox.nl by MOD_MP40
        re.compile(r'^(?P<action>[a-z]+):\s*'
                   r'(?P<data>'
                   r'(?P<cid>[0-9]+)\s'
                   r'(?P<acid>[0-9]+)\s'
                   r'(?P<aweap>[0-9]+):\s*'
                   r'(?P<text>.*))$', re.IGNORECASE),

        re.compile(r'^(?P<action>[a-z]+):\s*(?P<data>(?P<cid>[0-9]+):\s*(?P<text>.*))$', re.IGNORECASE),
        re.compile(r'^(?P<action>[a-z]+):\s*(?P<data>(?P<cid>[0-9]+)\s(?P<text>.*))$', re.IGNORECASE),
        re.compile(r'^(?P<action>[a-z]+):\s*(?P<data>.*)$', re.IGNORECASE)
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
        self.clients.new_client('-1', guid=self.gameName + ':WORLD', name='World', pbid='WORLD', hide=True)
        self.PunkBuster = PunkBuster.PunkBuster(self)
        self._eventMap['warmup'] = self.getEventID('EVT_GAME_WARMUP')
        self._eventMap['restartgame'] = self.getEventID('EVT_GAME_ROUND_END')

        # force g_logsync
        self.debug('Forcing server cvar g_logsync to %s' % self._logSync)
        self.setCvar('g_logsync', self._logSync)

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENT HANDLERS                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def OnConnectinfo(self, action, data, match=None):
        guid = match.group('pbid')
        client = self.clients.getByCID(match.group('cid'))
        if client:
            if client.guid == guid:
                # this is the same player

                if client.exactName != match.group('name'):
                    client.exactName = match.group('name')
                    client.setName(self.stripColors(client.exactName))
                return self.getEvent('EVT_CLIENT_JOIN', client=client)
            else:
                # disconnect the existing client
                self.verbose('disconnect the existing client %s %s => %s %s', match.group('cid'), guid, client.cid, client)
                client.disconnect()

        client = self.clients.newBaseClient()
        client.cid  = match.group('cid')
        client.pbid = client.guid = self.gameName + ':' + guid
        client.ip = match.group('ip')

        client.exactName = match.group('name')
        client.name = self.stripColors(client.exactName)
        self.clients.update(client)

    def OnClientuserinfochangedguid(self, action, data, match=None):
        client = self.clients.getByCID(match.group('cid'))
        cid, pbid, data = string.split(data, ' ', 2)
        bclient = self.parseUserInfo(cid + ' ' + data)
        if bclient:
            self.clients.update(bclient, client)

    def OnGib(self, action, data, match=None):
        victim = self.clients.getByCID(match.group('cid'))
        if not victim:
            self.debug('No victim')
            #self.OnJ(action, data, match)
            return None

        attacker = self.clients.getByCID(match.group('acid'))
        if not attacker:
            self.debug('No attacker')
            return None

        event_key = 'EVT_CLIENT_GIB'
        if attacker.cid == victim.cid:
            event_key = 'EVT_CLIENT_GIB_SELF'
        elif attacker.team != b3.TEAM_UNKNOWN and attacker.team == victim.team:
            event_key = 'EVT_CLIENT_GIB_TEAM'

        return self.getEvent(event_key, (100, match.group('aweap'), ''), attacker, victim)

    def OnKill(self, action, data, match=None):
        victim = self.clients.getByCID(match.group('cid'))
        if not victim:
            self.debug('No victim')
            #self.OnJ(action, data, match)
            return None

        attacker = self.clients.getByCID(match.group('acid'))
        if not attacker:
            self.debug('No attacker')
            return None

        event_key = 'EVT_CLIENT_KILL'
        if attacker.cid == victim.cid:
            event_key = 'EVT_CLIENT_SUICIDE'
        elif attacker.team != b3.TEAM_UNKNOWN and attacker.team == victim.team:
            event_key = 'EVT_CLIENT_KILL_TEAM'

        return self.getEvent(event_key, (100, match.group('aweap'), ''), attacker, victim)

    def OnSayteamc(self, action, data, match=None):
        #1536:34sayteamc: 17: ^1[^7DP^1]^4Timekiller: ^4ammo ^2here !!!!!
        client = self.clients.getByCID(match.group('cid'))
        if not client:
            self.debug('no client - attempt join')
            #self.OnJ(action, data, match)
            #client = self.clients.getByCID(match.group('cid'))
            #if not client:
            return None

        return self.getEvent('EVT_CLIENT_TEAM_SAY', match.group('text'), client)

    def OnSayc(self, action, data, match=None):
        #1536:17sayc: 0: ^w[^2AS^w]^2Lead:  sorry...
        client = self.clients.getByCID(match.group('cid'))
        if not client:
            self.debug('no client - attempt join')
            #self.OnJ(action, data, match)
            #client = self.clients.getByCID(match.group('cid'))
            #if not client:
            return None

        return self.getEvent('EVT_CLIENT_SAY', match.group('text'), client)

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

        if client.cid is None:
            # skip this message
            return

        lines = []
        message = prefixText([self.msgPrefix, self.pmPrefix], text)
        message = message.strip()
        for line in self.getWrap(message):
            lines.append(self.getCommand('message', message=line))
        self.writelines(lines)

    def getNextMap(self):
        pass