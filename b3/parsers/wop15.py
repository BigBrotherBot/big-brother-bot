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
#


__author__  = 'xlr8or'
__version__ = '1.0.0'

from b3.parsers.q3a.abstractParser import AbstractParser
import re
import string
import b3.parsers.wop

#----------------------------------------------------------------------------------------------------------------------------------------------
class Wop15Parser(b3.parsers.wop.WopParser):
    gameName = 'wop15'

    _commands = {}
    _commands['message'] = 'stell %(cid)s %(prefix)s ^3[pm]^7 %(message)s'
    _commands['deadsay'] = 'stell %(cid)s %(prefix)s [DEAD]^7 %(message)s'
    _commands['say'] = 'ssay %(prefix)s^7 %(message)s'

    _commands['set'] = 'set %(name)s "%(value)s"'
    _commands['kick'] = 'clientkick %(cid)s'
    _commands['ban'] = 'addip %(cid)s'
    _commands['tempban'] = 'clientkick %(cid)s'

    _lineFormats = (
        #Generated with : WOP version 1.5
        #ClientConnect: 0 014D28A78B194CDA9CED1344D47B903B 84.167.190.158
        re.compile(r'^(?P<action>[a-z]+):\s(?P<data>(?P<cid>[0-9]+)\s(?P<cl_guid>[0-9a-z]{32})\s+(?P<ip>[0-9.]+))$', re.IGNORECASE),
        #ClientConnect: 2  151.16.71.226
        re.compile(r'^(?P<action>[a-z]+):\s(?P<data>(?P<cid>[0-9]+)\s+(?P<ip>[0-9.]+))$', re.IGNORECASE),
        #Bot connecting
        #ClientConnect: 0
        re.compile(r'^(?P<action>ClientConnect):\s*(?P<data>(?P<bcid>[0-9]+))$', re.IGNORECASE),

        #Kill: $attacker-cid $means-of-death $target-cid
        #Kill: 2 MOD_INJECTOR 0
        re.compile(r'^(?P<action>[a-z]+):\s*(?P<data>(?P<acid>[0-9]+)\s(?P<aweap>[0-9a-z_]+)\s(?P<cid>[0-9]+))$', re.IGNORECASE),
        #Say: 0 insta machen?
        #Item: 3 ammo_spray_n
        re.compile(r'^(?P<action>[a-z]+):\s*(?P<data>.*)$', re.IGNORECASE)
    )

    #status
    #map: wop_padcloisterctl
    #num score team ping name            lastmsg address               qport rate
    #--- ----- ---- ---- --------------- ------- --------------------- ----- -----
    #  0     0    2    0 ^0PAD^4MAN^7           50 bot                       0 16384
    #  1     0    3   43 PadPlayer^7           0 2001:41b8:9bf:fe04:f40c:d4ff:fe2b:6af9 45742 90000
    _regPlayer = re.compile(r'^(?P<slot>[0-9]+)\s+(?P<score>[0-9-]+)\s+(?P<team>[0-9]+)\s+(?P<ping>[0-9]+)\s+(?P<name>.*?)\s+(?P<last>[0-9]+)\s+(?P<ip>[0-9.]+):(?P<port>[0-9-]+)\s+(?P<qport>[0-9]+)\s+(?P<rate>[0-9]+)$', re.I)

    # say
    def OnSay(self, action, data, match=None):
        #3:59 say: 1 general chat
        msg = string.split(data, ' ', 1)
        if not len(msg) == 2:
            return None

        client = self.clients.getByCID(msg[0])

        if client:
            self.verbose('Client Found: %s' % client.name)
            return b3.events.Event(b3.events.EVT_CLIENT_SAY, msg[1], client)
        else:
            self.verbose('No Client Found!')
            return None

    # sayteam
    def OnSayteam(self, action, data, match=None):
        #4:06 sayteam: 1 teamchat
        msg = string.split(data, ' ', 1)
        if not len(msg) == 2:
            return None

        client = self.clients.getByCid(msg[0])

        if client:
            self.verbose('Client Found: %s' % client.name)
            return b3.events.Event(b3.events.EVT_CLIENT_TEAM_SAY, msg[1], client, client.team)
        else:
            self.verbose('No Client Found!')
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