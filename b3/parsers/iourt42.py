#
# ioUrT 4.2 Parser for BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2012 Thomas LEVEIL <courgette@bigbrotherbot.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
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
# 2012/07/24 - 0.0 - Courgette
#     * parser created
#
from b3.events import Event

__author__  = 'Courgette'
__version__ = '0.0'

import re
from b3.parsers.iourt41 import Iourt41Parser
import b3

#----------------------------------------------------------------------------------------------------------------------------------------------
class Iourt42Parser(Iourt41Parser):
    gameName = 'iourt42'


    _commands = {
        'broadcast': '%(prefix)s^7 %(message)s',
        'message': 'tell %(cid)s %(prefix)s ^3[pm]^7 %(message)s',
        'deadsay': 'tell %(cid)s %(prefix)s [DEAD]^7 %(message)s',
        'say': 'say %(prefix)s %(message)s',
        'saybig': 'bigtext "%(prefix)s %(message)s"',
        'set': 'set %(name)s "%(value)s"',
        'kick': 'clientkick %(cid)s',
        'ban': 'addip %(cid)s',
        'tempban': 'clientkick %(cid)s',
        'banByIp': 'addip %(ip)s',
        'unbanByIp': 'removeip %(ip)s',
        'slap': 'slap %(cid)s',
        'nuke': 'nuke %(cid)s',
        'mute': 'mute %(cid)s %(seconds)s',
        'kill': 'smite %(cid)s',
    }

    _eventMap = {
        #'warmup' : b3.events.EVT_GAME_HOTPOTATO,
        #'shutdowngame' : b3.events.EVT_GAME_ROUND_END
    }

    # remove the time off of the line
    _lineClear = re.compile(r'^(?:[0-9:]+\s?)?')
    #0:00 ClientUserinfo: 0:

    _lineFormats = (
        #Radio: 0 - 7 - 2 - "New Alley" - "I'm going for the flag"
        re.compile(r'''^(?P<action>Radio): (?P<data>(?P<cid>[0-9]+) - (?P<msg_group>[0-9]+) - (?P<msg_id>[0-9]+) - "(?P<location>.+)" - "(?P<text>.*)")$'''),

        #Callvote: 1 - "map dressingroom"
        re.compile(r'''^(?P<action>Callvote): (?P<data>(?P<cid>[0-9]+) - "(?P<vote_string>.*)")$'''),

        #Vote: 0 - 2
        re.compile(r'''^(?P<action>Vote): (?P<data>(?P<cid>[0-9]+) - (?P<value>.*))$'''),

        #Generated with ioUrbanTerror v4.1:
        #Hit: 12 7 1 19: BSTHanzo[FR] hit ercan in the Helmet
        #Hit: 13 10 0 8: Grover hit jacobdk92 in the Head
        re.compile(r'^(?P<action>[a-z]+):\s(?P<data>(?P<cid>[0-9]+)\s(?P<acid>[0-9]+)\s(?P<hitloc>[0-9]+)\s(?P<aweap>[0-9]+):\s+(?P<text>.*))$', re.IGNORECASE),
        #re.compile(r'^(?P<action>[a-z]+):\s(?P<data>(?P<cid>[0-9]+)\s(?P<acid>[0-9]+)\s(?P<hitloc>[0-9]+)\s(?P<aweap>[0-9]+):\s+(?P<text>(?P<aname>[^:])\shit\s(?P<name>[^:])\sin\sthe(?P<locname>.*)))$', re.IGNORECASE),

        #6:37 Kill: 0 1 16: XLR8or killed =lvl1=Cheetah by UT_MOD_SPAS
        #2:56 Kill: 14 4 21: Qst killed Leftovercrack by UT_MOD_PSG1
        re.compile(r'^(?P<action>[a-z]+):\s(?P<data>(?P<acid>[0-9]+)\s(?P<cid>[0-9]+)\s(?P<aweap>[0-9]+):\s+(?P<text>.*))$', re.IGNORECASE),
        #re.compile(r'^(?P<action>[a-z]+):\s(?P<data>(?P<acid>[0-9]+)\s(?P<cid>[0-9]+)\s(?P<aweap>[0-9]+):\s+(?P<text>(?P<aname>[^:])\skilled\s(?P<name>[^:])\sby\s(?P<modname>.*)))$', re.IGNORECASE),

        #Processing chats and tell events...
        #5:39 saytell: 15 16 repelSteeltje: nno
        #5:39 saytell: 15 15 repelSteeltje: nno
        re.compile(r'^(?P<action>[a-z]+):\s(?P<data>(?P<cid>[0-9]+)\s(?P<acid>[0-9]+)\s(?P<name>[^ ]+):\s+(?P<text>.*))$', re.IGNORECASE),

        # We're not using tell in this form so this one is disabled
        #5:39 tell: repelSteeltje to B!K!n1: nno
        #re.compile(r'^(?P<action>[a-z]+):\s+(?P<data>(?P<name>[^:]+)\s+to\s+(?P<aname>[^:]+):\s+(?P<text>.*))$', re.IGNORECASE),

        #3:53 say: 8 denzel: lol
        #15:37 say: 9 .:MS-T:.BstPL: this name is quite a challenge
        #2:28 sayteam: 12 New_UrT_Player_v4.1: woekele
        #16:33 Flag: 2 0: team_CTF_redflag
        #re.compile(r'^(?P<action>[a-z]+):\s(?P<data>(?P<cid>[0-9]+)\s(?P<name>[^ ]+):\s+(?P<text>.*))$', re.IGNORECASE),
        # SGT: fix issue with OnSay when something like this come and the match could'nt find the name group
        # say: 7 -crespino-:
        re.compile(r'^(?P<action>[a-z]+):\s(?P<data>(?P<cid>[0-9]+)\s(?P<name>[^ ]+):\s*(?P<text>.*))$', re.IGNORECASE),

        #15:42 Flag Return: RED
        #15:42 Flag Return: BLUE
        re.compile(r'^(?P<action>Flag Return):\s(?P<data>(?P<color>.+))$', re.IGNORECASE),

        #Bombmode actions:
        #3:06 Bombholder is 2
        re.compile(r'^(?P<action>Bombholder)(?P<data>\sis\s(?P<cid>[0-9]))$', re.IGNORECASE),
        #was planted, was defused, was tossed, has been collected (doh, how gramatically correct!)
        #2:13 Bomb was tossed by 2
        #2:32 Bomb was planted by 2
        #3:01 Bomb was defused by 3!
        #2:17 Bomb has been collected by 2
        re.compile(r'^(?P<action>Bomb)\s(?P<data>(was|has been)\s(?P<subaction>[a-z]+)\sby\s(?P<cid>[0-9]+).*)$', re.IGNORECASE),

        #Falling thru? Item stuff and so forth
        re.compile(r'^(?P<action>[a-z]+):\s(?P<data>.*)$', re.IGNORECASE),
        #Shutdowngame and Warmup... the one word lines
        re.compile(r'^(?P<action>[a-z]+):$', re.IGNORECASE)
    )

    # map: ut4_casa
    # num score ping name            lastmsg address               qport rate
    # --- ----- ---- --------------- ------- --------------------- ----- -----
    #   2     0   19 ^1XLR^78^8^9or^7        0 145.99.135.227:27960  41893  8000  # player with a live ping
    #   4     0 CNCT Dz!k^7                450 83.175.191.27:64459   50308 20000  # connecting player (or inbetween rounds)
    #   9     0 ZMBI ^7                   1900 81.178.80.68:27960    10801  8000  # zombies (need to be disconnected!)
    _regPlayer = re.compile(r'^(?P<slot>[0-9]+)\s+(?P<score>[0-9-]+)\s+(?P<ping>[0-9]+|CNCT|ZMBI)\s+(?P<name>.*?)\s+(?P<last>[0-9]+)\s+(?P<ip>[0-9.]+):(?P<port>[0-9-]+)\s+(?P<qport>[0-9]+)\s+(?P<rate>[0-9]+)$', re.I)
    _reColor = re.compile(r'(\^.)|[\x00-\x20]|[\x7E-\xff]')

    # Map: ut4_algiers
    # Players: 8
    # Scores: R:97 B:98
    # 0:  FREE k:0 d:0 ping:0
    # 4: yene RED k:16 d:8 ping:50 92.104.110.192:63496
    _reTeamScores = re.compile(r'^Scores:\s+R:(?P<RedScore>.+)\s+B:(?P<BlueScore>.+)$', re.I)
    _rePlayerScore = re.compile(r'^(?P<slot>[0-9]+): (?P<name>.*) (?P<team>RED|BLUE|SPECTATOR|FREE) k:(?P<kill>[0-9]+) d:(?P<death>[0-9]+) ping:(?P<ping>[0-9]+|CNCT|ZMBI)( (?P<ip>[0-9.]+):(?P<port>[0-9-]+))?$', re.I) # NOTE: this won't work properly if the server has private slots. see http://forums.urbanterror.net/index.php/topic,9356.0.html


    def startup(self):
        Iourt41Parser.startup(self)

        # add UrT 4.2 specific events
        self.Events.createEvent('EVT_CLIENT_RADIO', 'Event client radio')
        self.Events.createEvent('EVT_GAME_HOTPOTATO', 'Event game hotpotato')
        self._eventMap['hotpotato'] = self.getEventID('EVT_GAME_HOTPOTATO')
        self.Events.createEvent('EVT_CLIENT_CALLVOTE', 'Event client call vote')
        self.Events.createEvent('EVT_CLIENT_VOTE', 'Event client vote')




    ###############################################################################################
    #
    #    Events handlers
    #
    ###############################################################################################

    def OnRadio(self, action, data, match=None):
        cid = match.group('cid')
        msg_group = match.group('msg_group')
        msg_id = match.group('msg_id')
        location = match.group('location')
        text = match.group('text')
        client = self.clients.getByCID(cid)
        if not client:
            self.debug('No client found')
            return None
        return Event(self.getEventID('EVT_CLIENT_RADIO'), client=client, data={
            'msg_group': msg_group,
            'msg_id': msg_id,
            'location': location,
            'text': text
        })

    def OnCallvote(self, action, data, match=None):
        cid = match.group('cid')
        vote_string = match.group('vote_string')
        client = self.clients.getByCID(cid)
        if not client:
            self.debug('No client found')
            return None
        return Event(self.getEventID('EVT_CLIENT_CALLVOTE'), client=client, data=vote_string)

    def OnVote(self, action, data, match=None):
        cid = match.group('cid')
        value = match.group('value')
        client = self.clients.getByCID(cid)
        if not client:
            self.debug('No client found')
            return None
        return Event(self.getEventID('EVT_CLIENT_VOTE'), client=client, data=value)



    ###############################################################################################
    #
    #    B3 Parser interface implementation
    #
    ###############################################################################################


    def inflictCustomPenalty(self, type, client, reason=None, duration=None, admin=None, data=None):
        if type == 'slap' and client:
            cmd = self.getCommand('slap', cid=client.cid)
            self.write(cmd)
            if reason:
                client.message("%s" % reason)
            return True

        elif type == 'nuke' and client:
            cmd = self.getCommand('nuke', cid=client.cid)
            self.write(cmd)
            if reason:
                client.message("%s" % reason)
            return True

        elif type == 'mute' and client:
            if duration is None:
                seconds = 60
            else:
                seconds = round(float(b3.functions.time2minutes(duration) * 60), 0)

            # make sure to unmute first
            cmd = self.getCommand('mute', cid=client.cid, seconds=0)
            self.write(cmd)
            # then mute
            cmd = self.getCommand('mute', cid=client.cid, seconds=seconds)
            self.write(cmd)
            if reason:
                client.message("%s" % reason)
            return True

        elif type == 'kill' and client:
            cmd = self.getCommand('kill', cid=client.cid)
            self.write(cmd)
            if reason:
                client.message("%s" % reason)
            return True


    ###############################################################################################
    #
    #    Other methods
    #
    ###############################################################################################


    # Translate the gameType to a readable format (also for teamkill plugin!)
    def defineGameType(self, gameTypeInt):

        _gameType = str(gameTypeInt)
        #self.debug('gameTypeInt: %s' % gameTypeInt)

        if gameTypeInt == '0':
            _gameType = 'ffa'
        elif gameTypeInt == '1': # Last Man Standing
            _gameType = 'lms'
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
