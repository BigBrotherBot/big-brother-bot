#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2012 Thomas LEVEIL <courgette@bigbrotherbot.net>
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
# 24/07/2012 - 0.0    - Courgette - parser created
# 08/08/2012 - 1.0    - Courgette - new authentication system using the Frozen Sand Account if available
# 08/08/2012 - 1.1    - Courgette - fix error when computing Hit damage. Until we got real value, the default value : 15
#                                   is returned for all weapons and all hit locations.
# 09/08/2012 - 1.2    - Courgette - make sure the game is UrT 4.2 or fail to start
# 09/08/2012 - 1.2.1  - Courgette - disabling authentication using the /rcon auth-whois command response
# 12/08/2012 - 1.3    - Courgette - patches the Spamcontrol plugin to make it aware of radio spam
# 14/09/2012 - 1.4    - Courgette - change kick and tempban commands so them give the reason
# 04/10/2012 - 1.5    - Courgette - update for UrT 4.2.002 new auth system with Frozen Sand Account and auth-key
# 04/10/2012 - 1.5.1  - Courgette - fix kick and tempban when used with a reason
# 10/10/2012 - 1.5.2  - Courgette - support names with blank characters
# 24/10/2012 - 1.6    - Courgette - new: settings to ban with the Frozen Sand auth system
# 09/11/2012 - 1.7    - Courgette - new: support new jump game type with code 9
# 15/11/2012 - 1.7.1  - Courgette - fix: banning with the Frozen Sand auth system now works with servers set to auth
#                                   private or notoriety mode
# 26/11/2012 - 1.8    - Courgette - protect some of the Client object property
# 26/11/2012 - 1.9    - Courgette - fix authentication for connecting player Frosen Sand Account is uniquely known
#                                   in the B3 database
# 07/12/2012 - 1.10   - Courgette - add new events : EVT_CLIENT_JUMP_TIMER_START, EVT_CLIENT_JUMP_TIMER_STOP,
#                                   EVT_CLIENT_POS_SAVE, EVT_CLIENT_POS_LOAD and EVT_CLIENT_SURVIVOR_WINNER which can be
#                                   used by plugins
# 08/12/2012 - 1.10.1 - Courgette - fix EVT_CLIENT_JUMP_TIMER_START and EVT_CLIENT_JUMP_TIMER_STOP events when no
#                                   location name is provided
# 22/12/2012 - 1.11   - Courgette - update for UrT 4.2.009 release. adds UT_MOD_SMITED, UT_MOD_GLOCK and fix constants
#                                   values for some of the UT_MOD_* constants
# 08/01/2013 - 1.11.1 - Courgette - fix EVT_SURVIVOR_WIN event
# 08/04/2013 - 1.12   - Courgette - add EVT_BOMB_EXPLODED event
# 05/07/2012 - 1.13   - Fenix     - added support for new UrT 4.2.013 weapons
#                                 - correctly parse ClientJumpRunStarted and ClientJumpRunStopped
#                                 - renamed event EVT_CLIENT_JUMP_TIMER_START into EVT_CLIENT_JUMP_RUN_START and add
#                                   attempt_num and attempt_max info to the event data
#                                 - renamed event EVT_CLIENT_JUMP_TIMER_STOP into EVT_CLIENT_JUMP_RUN_STOP and add
#                                   attempt_num and attempt_max info to the event data
#                                 - added parsing of ClientJumpRunCanceled (generate EVT_CLIENT_JUMP_RUN_CANCEL)
#                                 - fixed Client(Load|Save)Position parsing
# 14/07/2013 - 1.14   - Courgette - add hitlocation constants : HL_HEAD, HL_HELMET and HL_TORSO
# 15/07/2013 - 1.15   - Fenix     - added missing hitlocation constants
#                                 - added damage table
#                                 - restored function _get_damage_points
# 25/07/2013 - 1.16   - Fenix     - fixed means of death ids
#                                 - added hit2kill code translation for UT_MOD_KICKED
# 30/07/2013 - 1.17   - Fenix     - added EVT_CLIENT_GOTO
# 27/09/2013 - 1.18   - Courgette - added EVT_VOTE_PASSED and EVT_VOTE_FAILED
# 09/12/2013 - 1.19   - Fenix     - added EVT_CLIENT_SPAWN and EVT_FLAG_RETURN_TIME
# 11/12/2013 - 1.20   - Courgette - fix: players with ':' in their name can't run commands ('UrT bug spotted' showing
#                                   up in the log)
# 13/01/2014 - 1.21   - Fenix     - PEP8 coding standards
#                                 - correctly set the client bot flag upon new client connection
# 12/01/2014 - 1.22   - Fenix     - updated Radio call regex: allow to parse log lines with missing radio location
#                                 - removed duplicated regular expression (Radio)
#                                 - increase parser version (1.22) and updated changelog
# 22/02/2014 - 1.23   - Courgette - fix issue #162 - 'None' string is written to the database client.pbid column
#                                 - fix auth-whois rcon response not being parsed properly since it has a newline char
# 14/04/2014 - 1.24   - Fenix     - use getEvent_id method to obtain event ids: remove some warnings
#                                 - use integer value while calling tempban method: remove another silly warning
#                                 - rewritten regular expressions on multiline: respect PEP8 line length constraint
#                                 - remove duplicate reference of event ids
# 02/05/2014 - 1.24.1 - Fenix     - correctly initialized spamcontrol_plugin class attribute
# 02/06/2014 - 1.24.2 - Fenix     - fixed reColor regex stripping whitespaces between words
# 03/08/2014 - 1.25   - Fenix     - syntax cleanup
#                                 - reformat changelog
# 14/09/2014 - 1.26   - Fenix     - added FreezeTag events: EVT_CLIENT_FREEZE, EVT_CLIENT_THAWOUT_STARTED,
#                                   EVT_CLIENT_THAWOUT_FINISHED, EVT_CLIENT_MELTED
#                                 - set client.state to b3.STATE_ALIVE on Client Spawn
# 17/09/2014 - 1.26.1 - Fenix     - added missing Freeze Tag gametype declaration (10) in defineGameType()
# 02/10/2014 - 1.27   - Fenix     - fixed regression introduced in 1.25
# 12/12/2014 - 1.28   - Fenix     - increased chat line length to comply with the new HUD setting (4.2.021)
# 25/01/2015 - 1.29   - Fenix     - patch the b3.clients.getByMagic method so it's possible to lookup players using their
#                                   auth login
# 16/04/2015 - 1.30   - Fenix     - uniform class variables (dict -> variable)
# 14/06/2015 - 1.31   - Fenix     - override OnClientuserinfochanged from Iourt1Parser: provide some more verbose logging
#                                   and correctly set racefree client attribute
# 29/06/2015 - 1.32   - Fenix     - fixed onSay regular expression not parsing lines with empty say text
# 30/06/2015 - 1.33   - Fenix     - get client auth login from Clientuserinfo line if available
#                                 - removed notoriety attribute in Iourt42Client: useless in UrT4.2
#                                 - improved logging
# 21/07/2015 - 1.34   - Fenix     - added a patch which deny connection to clients whose nickname is longer than 32
#                                   characters (read more: https://github.com/BigBrotherBot/big-brother-bot/issues/346)
# 26/07/2015 - 1.35   - Fenix     - queue EVT_GAME_ROUND_END when survivor winner is triggered

import b3
import re
import new
import time

from b3.clients import Client
from b3.events import Event
from b3.functions import time2minutes
from b3.parsers.iourt41 import Iourt41Parser
from b3.plugins.spamcontrol import SpamcontrolPlugin


__author__ = 'Courgette, Fenix'
__version__ = '1.35'


class Iourt42Client(Client):

    def auth_by_guid(self):
        """
        Authorize this client using his GUID.
        """
        self.console.debug("Auth by guid: %r", self.guid)
        try:
            return self.console.storage.getClient(self)
        except KeyError, msg:
            self.console.debug('User not found %s: %s', self.guid, msg)
            return False

    def auth_by_pbid(self):
        """
        Authorize this client using his PBID.
        """
        self.console.debug("Auth by FSA: %r", self.pbid)
        clients_matching_pbid = self.console.storage.getClientsMatching(dict(pbid=self.pbid))
        if len(clients_matching_pbid) > 1:
            self.console.warning("Found %s client having FSA '%s'", len(clients_matching_pbid), self.pbid)
            return self.auth_by_pbid_and_guid()
        elif len(clients_matching_pbid) == 1:
            self.id = clients_matching_pbid[0].id
            # we may have a second client entry in database with current guid.
            # we want to update our current client guid only if it is not the case.
            try:
                client_by_guid = self.console.storage.getClient(Iourt42Client(guid=self.guid))
            except KeyError:
                pass
            else:
                if client_by_guid.id != self.id:
                    # so storage.getClient is able to overwrite the value which will make
                    # it remain unchanged in database when .save() will be called later on
                    self._guid = None
            return self.console.storage.getClient(self)
        else:
            self.console.debug('Frozen Sand account [%s] unknown in database', self.pbid)
            return False

    def auth_by_pbid_and_guid(self):
        """
        Authorize this client using both his PBID and GUID.
        """
        self.console.debug("Auth by both guid and FSA: %r, %r", self.guid, self.pbid)
        clients_matching_pbid = self.console.storage.getClientsMatching({'pbid': self.pbid, 'guid': self.guid})
        if len(clients_matching_pbid):
            self.id = clients_matching_pbid[0].id
            return self.console.storage.getClient(self)
        else:
            self.console.debug("Frozen Sand account [%s] with guid '%s' unknown in database", self.pbid, self.guid)
            return False

    def auth(self):
        """
        The b3.clients.Client.auth method needs to be changed to fit the UrT4.2 authentication scheme.
        In UrT4.2 :
           * all connected players have a cl_guid
           * some have a Frozen Sand account (FSA)
        The FSA is a worldwide identifier while the cl_guid only identify a player on a given game server.
        See http://forum.bigbrotherbot.net/urban-terror-4-2/urt-4-2-discussion/
        """
        if not self.authed and self.guid and not self.authorizing:

            self.authorizing = True

            name = self.name
            pbid = self.pbid
            guid = self.guid
            ip = self.ip

            if not pbid and self.cid:
                fsa_info = self.console.queryClientFrozenSandAccount(self.cid)
                self.pbid = pbid = fsa_info.get('login', None)

            self.console.verbose("Auth with %r", {'name': name, 'ip': ip, 'pbid': pbid, 'guid': guid})

            # FSA will be found in pbid
            if not self.pbid:
                # auth with cl_guid only
                try:
                    in_storage = self.auth_by_guid()
                    # fix up corrupted data due to bug #162
                    if in_storage and in_storage.pbid == 'None':
                        in_storage.pbid = None
                except Exception, e:
                    self.console.error("Auth by guid failed", exc_info=e)
                    self.authorizing = False
                    return False
            else:
                # auth with FSA
                try:
                    in_storage = self.auth_by_pbid()
                except Exception, e:
                    self.console.error("Auth by FSA failed", exc_info=e)
                    self.authorizing = False
                    return False

                if not in_storage:
                    # fallback on auth with cl_guid only
                    try:
                        in_storage = self.auth_by_guid()
                    except Exception, e:
                        self.console.error("Auth by guid failed (when no known FSA)", exc_info=e)
                        self.authorizing = False
                        return False

            if in_storage:
                self.lastVisit = self.timeEdit
                self.console.bot("Client found in the storage @%s: welcome back %s [FSA: '%s']", self.id, self.name, self.pbid)
            else:
                self.console.bot("Client not found in the storage %s [FSA: '%s'], create new", str(self.guid), self.pbid)

            self.connections = int(self.connections) + 1
            self.name = name
            self.ip = ip
            if pbid:
                self.pbid = pbid
            self.save()
            self.authed = True

            self.console.debug("Client authorized: %s [@%s] [GUID: '%s'] [FSA: '%s']", self.name, self.id, self.guid, self.pbid)

            # check for bans
            if self.numBans > 0:
                ban = self.lastBan
                if ban:
                    self.reBan(ban)
                    self.authorizing = False
                    return False

            self.refreshLevel()
            self.console.queueEvent(self.console.getEvent('EVT_CLIENT_AUTH', data=self, client=self))
            self.authorizing = False
            return self.authed
        else:
            return False

    def __str__(self):
        return "Client42<@%s:%s|%s:\"%s\":%s>" % (self.id, self.guid, self.pbid, self.name, self.cid)


class Iourt42Parser(Iourt41Parser):
   
    gameName = 'iourt42'
    spamcontrolPlugin = None

    _logSync = 2

    _permban_with_frozensand = False
    _tempban_with_frozensand = False
    _allow_userinfo_overflow = False

    _commands = {
        'broadcast': '%(message)s',
        'message': 'tell %(cid)s %(message)s',
        'deadsay': 'tell %(cid)s %(message)s',
        'say': 'say %(message)s',
        'saybig': 'bigtext "%(message)s"',
        'set': 'set %(name)s "%(value)s"',
        'kick': 'kick %(cid)s "%(reason)s"',
        'ban': 'addip %(cid)s',
        'tempban': 'kick %(cid)s "%(reason)s"',
        'banByIp': 'addip %(ip)s',
        'unbanByIp': 'removeip %(ip)s',
        'auth-permban': 'auth-ban %(cid)s 0 0 0',
        'auth-tempban': 'auth-ban %(cid)s %(days)s %(hours)s %(minutes)s',
        'slap': 'slap %(cid)s',
        'nuke': 'nuke %(cid)s',
        'mute': 'mute %(cid)s %(seconds)s',
        'kill': 'smite %(cid)s',
    }

    # remove the time off of the line
    _lineClear = re.compile(r'^(?:[0-9:]+\s?)?')
    _line_length = 90

    _lineFormats = (
        # Radio: 0 - 7 - 2 - "New Alley" - "I'm going for the flag"
        re.compile(r'^(?P<action>Radio): '
                   r'(?P<data>(?P<cid>[0-9]+) - '
                   r'(?P<msg_group>[0-9]+) - '
                   r'(?P<msg_id>[0-9]+) - '
                   r'"(?P<location>.*)" - '
                   r'"(?P<text>.*)")$', re.IGNORECASE),

        # Callvote: 1 - "map dressingroom"
        re.compile(r'^(?P<action>Callvote): (?P<data>(?P<cid>[0-9]+) - "(?P<vote_string>.*)")$', re.IGNORECASE),

        # Vote: 0 - 2
        re.compile(r'^(?P<action>Vote): (?P<data>(?P<cid>[0-9]+) - (?P<value>.*))$', re.IGNORECASE),

        # VotePassed: 1 - 0 - "reload"
        re.compile(r'^(?P<action>VotePassed): (?P<data>(?P<yes>[0-9]+) - (?P<no>[0-9]+) - "(?P<what>.*)")$', re.I),

        # VoteFailed: 1 - 1 - "restart"
        re.compile(r'^(?P<action>VoteFailed): (?P<data>(?P<yes>[0-9]+) - (?P<no>[0-9]+) - "(?P<what>.*)")$', re.I),

        # FlagCaptureTime: 0: 1234567890
        # FlagCaptureTime: 1: 1125480101
        re.compile(r'^(?P<action>FlagCaptureTime):\s(?P<cid>[0-9]+):\s(?P<captime>[0-9]+)$', re.IGNORECASE),

        # 13:34 ClientJumpRunStarted: 0 - way: 1
        # 13:34 ClientJumpRunStarted: 0 - way: 1 - attempt: 1 of 5
        re.compile(r'^(?P<action>ClientJumpRunStarted):\s'
                   r'(?P<cid>\d+)\s-\s'
                   r'(?P<data>way:\s'
                   r'(?P<way_id>\d+)'
                   r'(?:\s-\sattempt:\s'
                   r'(?P<attempt_num>\d+)\sof\s'
                   r'(?P<attempt_max>\d+))?)$', re.IGNORECASE),

        # 13:34 ClientJumpRunStopped: 0 - way: 1 - time: 12345
        # 13:34 ClientJumpRunStopped: 0 - way: 1 - time: 12345 - attempt: 1 of 5
        re.compile(r'^(?P<action>ClientJumpRunStopped):\s'
                   r'(?P<cid>\d+)\s-\s'
                   r'(?P<data>way:\s'
                   r'(?P<way_id>\d+)'
                   r'\s-\stime:\s'
                   r'(?P<way_time>\d+)'
                   r'(?:\s-\sattempt:\s'
                   r'(?P<attempt_num>\d+)\sof\s'
                   r'(?P<attempt_max>\d+'
                   r'))?)$', re.IGNORECASE),

        # 13:34 ClientJumpRunCanceled: 0 - way: 1
        # 13:34 ClientJumpRunCanceled: 0 - way: 1 - attempt: 1 of 5
        re.compile(r'^(?P<action>ClientJumpRunCanceled):\s'
                   r'(?P<cid>\d+)\s-\s'
                   r'(?P<data>way:\s'
                   r'(?P<way_id>\d+)'
                   r'(?:\s-\sattempt:\s'
                   r'(?P<attempt_num>\d+)\sof\s'
                   r'(?P<attempt_max>\d+))?)$', re.IGNORECASE),

        # 13:34 ClientSavePosition: 0 - 335.384887 - 67.469154 - -23.875000
        # 13:34 ClientLoadPosition: 0 - 335.384887 - 67.469154 - -23.875000
        re.compile(r'^(?P<action>Client(Save|Load)Position):\s'
                   r'(?P<cid>\d+)\s-\s'
                   r'(?P<data>'
                   r'(?P<x>-?\d+(?:\.\d+)?)\s-\s'
                   r'(?P<y>-?\d+(?:\.\d+)?)\s-\s'
                   r'(?P<z>-?\d+(?:\.\d+)?))$', re.IGNORECASE),

        # 13:34 ClientGoto: 0 - 1 - 335.384887 - 67.469154 - -23.875000
        re.compile(r'^(?P<action>ClientGoto):\s'
                   r'(?P<cid>\d+)\s-\s'
                   r'(?P<tcid>\d+)\s-\s'
                   r'(?P<data>'
                   r'(?P<x>-?\d+(?:\.\d+)?)\s-\s'
                   r'(?P<y>-?\d+(?:\.\d+)?)\s-\s'
                   r'(?P<z>-?\d+(?:\.\d+)?))$', re.IGNORECASE),

        # ClientSpawn: 0
        # ClientMelted: 1
        re.compile(r'^(?P<action>Client(Melted|Spawn)):\s(?P<cid>[0-9]+)$', re.IGNORECASE),

        # Generated with ioUrbanTerror v4.1:
        # Hit: 12 7 1 19: BSTHanzo[FR] hit ercan in the Helmet
        # Hit: 13 10 0 8: Grover hit jacobdk92 in the Head
        re.compile(r'^(?P<action>Hit):\s'
                   r'(?P<data>'
                   r'(?P<cid>[0-9]+)\s'
                   r'(?P<acid>[0-9]+)\s'
                   r'(?P<hitloc>[0-9]+)\s'
                   r'(?P<aweap>[0-9]+):\s+'
                   r'(?P<text>.*))$', re.IGNORECASE),

        # 6:37 Kill: 0 1 16: XLR8or killed =lvl1=Cheetah by UT_MOD_SPAS
        # 2:56 Kill: 14 4 21: Qst killed Leftovercrack by UT_MOD_PSG1
        # 6:37 Freeze: 0 1 16: Fenix froze Biddle by UT_MOD_SPAS
        re.compile(r'^(?P<action>[a-z]+):\s'
                   r'(?P<data>'
                   r'(?P<acid>[0-9]+)\s'
                   r'(?P<cid>[0-9]+)\s'
                   r'(?P<aweap>[0-9]+):\s+'
                   r'(?P<text>.*))$', re.IGNORECASE),

        # ThawOutStarted: 0 1: Fenix started thawing out Biddle
        # ThawOutFinished: 0 1: Fenix thawed out Biddle
        re.compile(r'^(?P<action>ThawOut(Started|Finished)):\s'
                   r'(?P<data>'
                   r'(?P<cid>[0-9]+)\s'
                   r'(?P<tcid>[0-9]+):\s+'
                   r'(?P<text>.*))$', re.IGNORECASE),

        # Processing chats and tell events...
        # 5:39 saytell: 15 16 repelSteeltje: nno
        # 5:39 saytell: 15 15 repelSteeltje: nno
        re.compile(r'^(?P<action>[a-z]+):\s'
                   r'(?P<data>'
                   r'(?P<cid>[0-9]+)\s'
                   r'(?P<acid>[0-9]+)\s'
                   r'(?P<name>.+?):\s+'
                   r'(?P<text>.*))$', re.IGNORECASE),

        # SGT: fix issue with onSay when something like this come and the match could'nt find the name group
        # say: 7 -crespino-:
        # say: 6 ^5Marcel ^2[^6CZARMY^2]: !help
        re.compile(r'^(?P<action>[a-z]+):\s'
                   r'(?P<data>'
                   r'(?P<cid>[0-9]+)\s'
                   r'(?P<name>[^ ]+):\s*'
                   r'(?P<text>.*))$', re.IGNORECASE),

        # 15:42 Flag Return: RED
        # 15:42 Flag Return: BLUE
        re.compile(r'^(?P<action>Flag Return):\s(?P<data>(?P<color>.+))$', re.IGNORECASE),

        # Bombmode actions:
        # 3:06 Bombholder is 2
        re.compile(r'^(?P<action>Bombholder)(?P<data>\sis\s(?P<cid>[0-9]))$', re.IGNORECASE),

        # was planted, was defused, was tossed, has been collected (doh, how gramatically correct!)
        # 2:13 Bomb was tossed by 2
        # 2:32 Bomb was planted by 2
        # 3:01 Bomb was defused by 3!
        # 2:17 Bomb has been collected by 2
        re.compile(r'^(?P<action>Bomb)\s'
                   r'(?P<data>(was|has been)\s'
                   r'(?P<subaction>[a-z]+)\sby\s'
                   r'(?P<cid>[0-9]+).*)$', re.IGNORECASE),

        # 17:24 Pop!
        re.compile(r'^(?P<action>Pop)!$', re.IGNORECASE),

        # Falling thru? Item stuff and so forth
        re.compile(r'^(?P<action>[a-z]+):\s(?P<data>.*)$', re.IGNORECASE),

        # Shutdowngame and Warmup... the one word lines
        re.compile(r'^(?P<action>[a-z]+):$', re.IGNORECASE)
    )

    # map: ut4_casa
    # num score ping name            lastmsg address               qport rate
    # --- ----- ---- --------------- ------- --------------------- ----- -----
    #   2     0   19 ^1XLR^78^8^9or        0 145.99.135.227:27960  41893  8000  # player with a live ping
    #   4     0 CNCT Dz!k^7              450 83.175.191.27:64459   50308 20000  # connecting player
    #   9     0 ZMBI ^7                 1900 81.178.80.68:27960    10801  8000  # zombies (need to be disconnected!)
    _regPlayer = re.compile(r'^(?P<slot>[0-9]+)\s+'
                            r'(?P<score>[0-9-]+)\s+'
                            r'(?P<ping>[0-9]+|CNCT|ZMBI)\s+'
                            r'(?P<name>.*?)\s+'
                            r'(?P<last>[0-9]+)\s+'
                            r'(?P<ip>[0-9.]+):(?P<port>[0-9-]+)\s+'
                            r'(?P<qport>[0-9]+)\s+'
                            r'(?P<rate>[0-9]+)$', re.IGNORECASE)

    _reColor = re.compile(r'(\^\d)')

    # Map: ut4_algiers
    # Players: 8
    # Scores: R:97 B:98
    # 0:  FREE k:0 d:0 ping:0
    # 4: yene RED k:16 d:8 ping:50 92.104.110.192:63496
    _reTeamScores = re.compile(r'^Scores:\s+'
                               r'R:(?P<RedScore>.+)\s+'
                               r'B:(?P<BlueScore>.+)$', re.IGNORECASE)

    _rePlayerScore = re.compile(r'^(?P<slot>[0-9]+): '
                                r'(?P<name>.*) '
                                r'(?P<team>RED|BLUE|SPECTATOR|FREE) '
                                r'k:(?P<kill>[0-9]+) d:(?P<death>[0-9]+) ping:(?P<ping>[0-9]+|CNCT|ZMBI)( '
                                r'(?P<ip>[0-9.]+):(?P<port>[0-9-]+))?$', re.IGNORECASE)

    # /rcon auth-whois replies patterns
    # 'auth: id: 0 - name: ^7Courgette - login: courgette - notoriety: serious - level: -1  \n'
    _re_authwhois = re.compile(r'^auth: id: (?P<cid>\d+) - '
                               r'name: \^7(?P<name>.+?) - '
                               r'login: (?P<login>.*?) - '
                               r'notoriety: (?P<notoriety>.+?) - '
                               r'level: (?P<level>-?\d+?)(?:\s+- (?P<extra>.*))?\s*$', re.MULTILINE)

    ## kill modes
    MOD_WATER = '1'
    MOD_LAVA = '3'
    MOD_TELEFRAG = '5'
    MOD_FALLING = '6'
    MOD_SUICIDE = '7'
    MOD_TRIGGER_HURT = '9'
    MOD_CHANGE_TEAM = '10'
    UT_MOD_KNIFE = '12'
    UT_MOD_KNIFE_THROWN = '13'
    UT_MOD_BERETTA = '14'
    UT_MOD_DEAGLE = '15'
    UT_MOD_SPAS = '16'
    UT_MOD_UMP45 = '17'
    UT_MOD_MP5K = '18'
    UT_MOD_LR300 = '19'
    UT_MOD_G36 = '20'
    UT_MOD_PSG1 = '21'
    UT_MOD_HK69 = '22'
    UT_MOD_BLED = '23'
    UT_MOD_KICKED = '24'
    UT_MOD_HEGRENADE = '25'
    UT_MOD_SR8 = '28'
    UT_MOD_AK103 = '30'
    UT_MOD_SPLODED = '31'
    UT_MOD_SLAPPED = '32'
    UT_MOD_SMITED = '33'
    UT_MOD_BOMBED = '34'
    UT_MOD_NUKED = '35'
    UT_MOD_NEGEV = '36'
    UT_MOD_HK69_HIT = '37'
    UT_MOD_M4 = '38'
    UT_MOD_GLOCK = '39'
    UT_MOD_COLT1911 = '40'
    UT_MOD_MAC11 = '41'
    UT_MOD_FLAG = '42'
    UT_MOD_GOOMBA = '43'

    # HIT LOCATIONS
    HL_HEAD = '1'
    HL_HELMET = '2'
    HL_TORSO = '3'
    HL_VEST = '4'
    HL_ARM_L = '5'
    HL_ARM_R = '6'
    HL_GROIN = '7'
    HL_BUTT = '8'
    HL_LEG_UPPER_L = '9'
    HL_LEG_UPPER_R = '10'
    HL_LEG_LOWER_L = '11'
    HL_LEG_LOWER_R = '12'
    HL_FOOT_L = '13'
    HL_FOOT_R = '14'

    ## weapons id on Hit: lines are different than the one
    ## on the Kill: lines. Here the translation table
    hitweapon2killweapon = {
        1: UT_MOD_KNIFE,
        2: UT_MOD_BERETTA,
        3: UT_MOD_DEAGLE,
        4: UT_MOD_SPAS,
        5: UT_MOD_MP5K,
        6: UT_MOD_UMP45,
        8: UT_MOD_LR300,
        9: UT_MOD_G36,
        10: UT_MOD_PSG1,
        14: UT_MOD_SR8,
        15: UT_MOD_AK103,
        17: UT_MOD_NEGEV,
        19: UT_MOD_M4,
        20: UT_MOD_GLOCK,
        21: UT_MOD_COLT1911,
        22: UT_MOD_MAC11,
        24: UT_MOD_KICKED,
        25: UT_MOD_KNIFE_THROWN,
    }

    ## damage table
    ## Fenix: Hit locations start with index 1 (HL_HEAD).
    ##        Since lists are 0 indexed we'll need to adjust the hit location
    ##        code to match the index number. Instead of adding random values
    ##        in the damage table, the adjustment will be made in _getDamagePoints.
    damage = {
        MOD_TELEFRAG: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        UT_MOD_KNIFE: [100, 60, 44, 35, 20, 20, 40, 37, 20, 20, 18, 18, 15, 15],
        UT_MOD_KNIFE_THROWN: [100, 60, 44, 35, 20, 20, 40, 37, 20, 20, 18, 18, 15, 15],
        UT_MOD_BERETTA: [100, 34, 30, 20, 11, 11, 25, 22, 15, 15, 13, 13, 11, 11],
        UT_MOD_DEAGLE: [100, 66, 57, 38, 22, 22, 45, 41, 28, 28, 22, 22, 18, 18],
        UT_MOD_SPAS: [25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25],
        UT_MOD_UMP45: [100, 51, 44, 29, 17, 17, 36, 32, 21, 21, 17, 17, 14, 14],
        UT_MOD_MP5K: [50, 34, 30, 20, 11, 11, 25, 22, 15, 15, 13, 13, 11, 11],
        UT_MOD_LR300: [100, 51, 44, 29, 17, 17, 37, 33, 20, 20, 17, 17, 14, 14],
        UT_MOD_G36: [100, 51, 44, 29, 17, 17, 37, 33, 20, 20, 17, 17, 14, 14],
        UT_MOD_PSG1: [100, 100, 97, 63, 36, 36, 70, 70, 41, 41, 36, 36, 29, 29],
        UT_MOD_HK69: [50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50],
        UT_MOD_BLED: [15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15],
        UT_MOD_KICKED: [30, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20],
        UT_MOD_HEGRENADE: [50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50],
        UT_MOD_SR8: [100, 100, 100, 100, 50, 50, 80, 70, 60, 60, 50, 50, 40, 40],
        UT_MOD_AK103: [100, 58, 51, 34, 19, 19, 41, 34, 22, 22, 19, 19, 15, 15],
        UT_MOD_NEGEV: [50, 34, 30, 20, 11, 11, 25, 22, 13, 13, 11, 11, 9, 9],
        UT_MOD_HK69_HIT: [20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20],
        UT_MOD_M4: [100, 51, 44, 29, 17, 17, 37, 33, 20, 20, 17, 17, 14, 14],
        UT_MOD_GLOCK: [60, 40, 33, 23, 14, 14, 28, 25, 17, 17, 14, 14, 11, 11],
        UT_MOD_COLT1911: [100, 60, 37, 27, 15, 15, 32, 29, 22, 22, 15, 15, 11, 11],
        UT_MOD_MAC11: [34, 29, 20, 15, 11, 11, 18, 17, 15, 15, 13, 13, 11, 11],
        UT_MOD_GOOMBA: [100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100],
    }   

    ####################################################################################################################
    #                                                                                                                  #
    #   PARSER INITIALIZATION                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    def __new__(cls, *args, **kwargs):
        Iourt42Parser.patch_Clients()
        return Iourt41Parser.__new__(cls)

    def startup(self):
        """
        Called after the parser is created before run().
        """
        try:
            cvar = self.getCvar('gamename')
            gamename = cvar.getString() if cvar else None
            if gamename != 'q3urt42':
                self.error("The iourt42 B3 parser cannot be used with a game server other than Urban Terror 4.2")
                raise SystemExit(220)
        except Exception, e:
            self.warning("Could not query server for gamename.", exc_info=e)

        Iourt41Parser.startup(self)

        # add UrT 4.2 specific events
        self.Events.createEvent('EVT_CLIENT_RADIO', 'Event client radio')
        self.Events.createEvent('EVT_GAME_FLAG_HOTPOTATO', 'Event game hotpotato')
        self.Events.createEvent('EVT_CLIENT_CALLVOTE', 'Event client call vote')
        self.Events.createEvent('EVT_CLIENT_VOTE', 'Event client vote')
        self.Events.createEvent('EVT_VOTE_PASSED', 'Event vote passed')
        self.Events.createEvent('EVT_VOTE_FAILED', 'Event vote failed')
        self.Events.createEvent('EVT_FLAG_CAPTURE_TIME', 'Event flag capture time')
        self.Events.createEvent('EVT_CLIENT_JUMP_RUN_START', 'Event client jump run started')
        self.Events.createEvent('EVT_CLIENT_JUMP_RUN_STOP', 'Event client jump run stopped')
        self.Events.createEvent('EVT_CLIENT_JUMP_RUN_CANCEL', 'Event client jump run canceled')
        self.Events.createEvent('EVT_CLIENT_POS_SAVE', 'Event client position saved')
        self.Events.createEvent('EVT_CLIENT_POS_LOAD', 'Event client position loaded')
        self.Events.createEvent('EVT_CLIENT_GOTO', 'Event client goto')
        self.Events.createEvent('EVT_CLIENT_SPAWN', 'Event client spawn')
        self.Events.createEvent('EVT_CLIENT_SURVIVOR_WINNER', 'Event client survivor winner')
        self.Events.createEvent('EVT_CLIENT_FREEZE', 'Event client freeze')
        self.Events.createEvent('EVT_CLIENT_THAWOUT_STARTED', 'Event client thawout started')
        self.Events.createEvent('EVT_CLIENT_THAWOUT_FINISHED', 'Event client thawout finished')
        self.Events.createEvent('EVT_CLIENT_MELTED', 'Event client melted')

        self._eventMap['hotpotato'] = self.getEventID('EVT_GAME_FLAG_HOTPOTATO')
        self._eventMap['warmup'] = self.getEventID('EVT_GAME_WARMUP')

        self.load_conf_frozensand_ban_settings()
        self.load_conf_userinfo_overflow()

    def pluginsStarted(self):
        """
        Called when all plugins are started.
        """
        self.spamcontrolPlugin = self.getPlugin("spamcontrol")
        if self.spamcontrolPlugin:
            self.patch_spamcontrolPlugin()

    ####################################################################################################################
    #                                                                                                                  #
    #   CONFIG LOADERS                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def load_conf_frozensand_ban_settings(self):
        """
        Load ban settings according to auth system cvars.
        """
        try:
            frozensand_auth_available = self.is_frozensand_auth_available()
        except Exception, e:
            self.warning("Could not query server for cvar auth", exc_info=e)
            frozensand_auth_available = False
        self.info("Frozen Sand auth system enabled : %s" % ('yes' if frozensand_auth_available else 'no'))

        try:
            cvar = self.getCvar('auth_owners')
            if cvar:
                frozensand_auth_owners = cvar.getString()
            else:
                frozensand_auth_owners = None
        except Exception, e:
            self.warning("Could not query server for cvar auth_owners", exc_info=e)
            frozensand_auth_owners = ""

        yn = ('yes - %s' % frozensand_auth_available) if frozensand_auth_owners else 'no'
        self.info("Frozen Sand auth_owners set : %s" % yn)

        if frozensand_auth_available and frozensand_auth_owners:
            self.load_conf_permban_with_frozensand()
            self.load_conf_tempban_with_frozensand()
            if self._permban_with_frozensand or self._tempban_with_frozensand:
                self.info("NOTE: when banning with the Frozen Sand auth system, B3 cannot remove "
                          "the bans on the urbanterror.info website. To unban a player you will "
                          "have to first unban him on B3 and then also unban him on the official Frozen Sand "
                          "website : http://www.urbanterror.info/groups/list/all/?search=%s" % frozensand_auth_owners)
        else:
            self.info("Ignoring settings about banning with Frozen Sand auth system as the "
                      "auth system is not enabled or auth_owners not set")

    def load_conf_permban_with_frozensand(self):
        """
        Load permban configuration from b3.xml.
        """
        self._permban_with_frozensand = False
        if self.config.has_option('server', 'permban_with_frozensand'):
            try:
                self._permban_with_frozensand = self.config.getboolean('server', 'permban_with_frozensand')
            except ValueError, err:
                self.warning(err)

        self.info("Send permbans to Frozen Sand : %s" % ('yes' if self._permban_with_frozensand else 'no'))

    def load_conf_tempban_with_frozensand(self):
        """
        Load tempban configuration from b3.xml.
        """
        self._tempban_with_frozensand = False
        if self.config.has_option('server', 'tempban_with_frozensand'):
            try:
                self._tempban_with_frozensand = self.config.getboolean('server', 'tempban_with_frozensand')
            except ValueError, err:
                self.warning(err)

        self.info("Send temporary bans to Frozen Sand : %s" % ('yes' if self._tempban_with_frozensand else 'no'))

    def load_conf_userinfo_overflow(self):
        """
        Load userinfo overflow configuration settings.
        """
        self._allow_userinfo_overflow = False
        if self.config.has_option('server', 'allow_userinfo_overflow'):
            try:
                self._allow_userinfo_overflow = self.config.getboolean('server', 'allow_userinfo_overflow')
            except ValueError, err:
                self.warning(err)

        self.info("Allow userinfo string overflow : %s" % ('yes' if self._allow_userinfo_overflow else 'no'))

        if self._allow_userinfo_overflow:
            self.info("NOTE: due to a bug in UrT 4.2 gamecode it is possible to exploit the maximum client name length "
                      "and generate a userinfo string longer than the imposed limits: clients connecting with nicknames "
                      "longer than 32 characters will be automatically kicked by B3 in order to prevent any sort of error")
        else:
            self.info("NOTE: due to a bug in UrT 4.2 gamecode it is possible to exploit the maximum client name length "
                      "and generate a userinfo string longer than the imposed limits: B3 will truncate nicknames of clients "
                      "which are longer than 32 characters")

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENT HANDLERS                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################
    
    def OnClientuserinfo(self, action, data, match=None):
        # 2 \ip\145.99.135.227:27960\challenge\-232198920\qport\2781\protocol\68\battleye\1\name\[SNT]^1XLR^78or..
        # 0 \gear\GMIORAA\team\blue\skill\5.000000\characterfile\bots/ut_chicken_c.c\color\4\sex\male\race\2\snaps\20\..
        bclient = self.parseUserInfo(data)
        bot = False
        if not 'cl_guid' in bclient and 'skill' in bclient:
            # must be a bot connecting
            self.bot('Bot connecting!')
            bclient['ip'] = '0.0.0.0'
            bclient['cl_guid'] = 'BOT' + str(bclient['cid'])
            bot = True

        if 'name' in bclient:
            # remove spaces from name
            bclient['name'] = bclient['name'].replace(' ', '')

        # split port from ip field
        if 'ip' in bclient:
            ip_port_data = bclient['ip'].split(':', 1)
            bclient['ip'] = ip_port_data[0]
            if len(ip_port_data) > 1:
                bclient['port'] = ip_port_data[1]

        if 'team' in bclient:
            bclient['team'] = self.getTeam(bclient['team'])

        self.verbose('Parsed user info: %s' % bclient)

        if bclient:

            client = self.clients.getByCID(bclient['cid'])

            if client:
                # update existing client
                for k, v in bclient.iteritems():
                    if hasattr(client, 'gear') and k == 'gear' and client.gear != v:
                        self.queueEvent(b3.events.Event(self.getEventID('EVT_CLIENT_GEAR_CHANGE'), v, client))
                    if not k.startswith('_') and k not in ('login', 'password', 'groupBits', 'maskLevel', 'autoLogin', 'greeting'):
                        setattr(client, k, v)
            else:
                # make a new client
                if 'cl_guid' in bclient:
                    guid = bclient['cl_guid']
                else:
                    guid = 'unknown'

                if 'authl' in bclient:
                    # authl contains FSA since UrT 4.2.022
                    fsa = bclient['authl']
                else:
                    # query FrozenSand Account
                    auth_info = self.queryClientFrozenSandAccount(bclient['cid'])
                    fsa = auth_info.get('login', None)

                # v1.0.17 - mindriot - 02-Nov-2008
                if 'name' not in bclient:
                    bclient['name'] = self._empty_name_default

                # v 1.10.5 => https://github.com/BigBrotherBot/big-brother-bot/issues/346
                if len(bclient['name']) > 32:
                    self.debug("UrT4.2 bug spotted! %s [GUID: '%s'] [FSA: '%s'] has a too long "
                               "nickname (%s characters)", bclient['name'], guid, fsa, len(bclient['name']))
                    if self._allow_userinfo_overflow:
                        x = bclient['name'][0:32]
                        self.debug('Truncating %s (%s) nickname => %s (%s)', bclient['name'], len(bclient['name']), x, len(x))
                        bclient['name'] = x
                    else:
                        self.debug("Connection denied to  %s [GUID: '%s'] [FSA: '%s']", bclient['name'], guid, fsa)
                        self.write(self.getCommand('kick', cid=bclient['cid'], reason='userinfo string overflow protection'))
                        return

                if 'ip' not in bclient:
                    if guid == 'unknown':
                        # happens when a client is (temp)banned and got kicked so client was destroyed,
                        # but infoline was still waiting to be parsed.
                        self.debug('Client disconnected: ignoring...')
                        return None
                    else:
                        try:
                            # see issue xlr8or/big-brother-bot#87 - ip can be missing
                            self.debug("Missing ip: trying to get ip with 'status'")
                            plist = self.getPlayerList()
                            client_data = plist[bclient['cid']]
                            bclient['ip'] = client_data['ip']
                        except Exception, err:
                            bclient['ip'] = ''
                            self.warning("Failed to get client %s ip address" % bclient['cid'], err)

                nguid = ''
                # override the guid... use ip's only if self.console.IpsOnly is set True.
                if self.IpsOnly:
                    nguid = bclient['ip']
                # replace last part of the guid with two segments of the ip
                elif self.IpCombi:
                    i = bclient['ip'].split('.')
                    d = len(i[0]) + len(i[1])
                    nguid = guid[:-d] + i[0] + i[1]
                # Quake clients don't have a cl_guid, we'll use ip instead
                elif guid == 'unknown':
                    nguid = bclient['ip']

                if nguid != '':
                    guid = nguid

                self.clients.newClient(bclient['cid'], name=bclient['name'], ip=bclient['ip'], bot=bot, guid=guid, pbid=fsa)

        return None

    def OnClientuserinfochanged(self, action, data, match=None):
        # 7 n\[SNT]^1XLR^78or\t\3\r\2\tl\0\f0\\f1\\f2\\a0\0\a1\0\a2\0
        parseddata = self.parseUserInfo(data)
        self.verbose('Parsed userinfo: %s' % parseddata)
        if parseddata:
            client = self.clients.getByCID(parseddata['cid'])
            if client:
                # update existing client
                if 'n' in parseddata:
                    setattr(client, 'name', parseddata['n'])

                if 't' in parseddata:
                    team = self.getTeam(parseddata['t'])
                    setattr(client, 'team', team)

                    if 'r' in parseddata:
                        if team == b3.TEAM_BLUE:
                            setattr(client, 'raceblue', parseddata['r'])
                        elif team == b3.TEAM_RED:
                            setattr(client, 'racered', parseddata['r'])
                        elif team == b3.TEAM_FREE:
                            setattr(client, 'racefree', parseddata['r'])

                    if parseddata.get('f0') is not None \
                        and parseddata.get('f1') is not None \
                        and parseddata.get('f2') is not None:

                        data = "%s,%s,%s" % (parseddata['f0'], parseddata['f1'], parseddata['f2'])
                        if team == b3.TEAM_BLUE:
                            setattr(client, 'funblue', data)
                        elif team == b3.TEAM_RED:
                            setattr(client, 'funred', data)

                if 'a0' in parseddata and 'a1' in parseddata and 'a2' in parseddata:
                    setattr(client, 'cg_rgb', "%s %s %s" % (parseddata['a0'], parseddata['a1'], parseddata['a2']))

    def OnRadio(self, action, data, match=None):
        cid = match.group('cid')
        msg_group = match.group('msg_group')
        msg_id = match.group('msg_id')
        location = match.group('location')
        text = match.group('text')
        client = self.getByCidOrJoinPlayer(cid)
        if not client:
            self.debug('No client found')
            return None
        return self.getEvent('EVT_CLIENT_RADIO', client=client, data={'msg_group': msg_group, 'msg_id': msg_id,
                                                                      'location': location, 'text': text})

    def OnCallvote(self, action, data, match=None):
        cid = match.group('cid')
        vote_string = match.group('vote_string')
        client = self.getByCidOrJoinPlayer(cid)
        if not client:
            self.debug('No client found')
            return None
        return self.getEvent('EVT_CLIENT_CALLVOTE', client=client, data=vote_string)

    def OnVote(self, action, data, match=None):
        cid = match.group('cid')
        value = match.group('value')
        client = self.getByCidOrJoinPlayer(cid)
        if not client:
            self.debug('No client found')
            return None
        return self.getEvent('EVT_CLIENT_VOTE', client=client, data=value)

    def OnVotepassed(self, action, data, match=None):
        yes_count = int(match.group('yes'))
        no_count = int(match.group('no'))
        vote_what = match.group('what')
        return self.getEvent('EVT_VOTE_PASSED', data={'yes': yes_count, 'no': no_count, 'what': vote_what})

    def OnVotefailed(self, action, data, match=None):
        yes_count = int(match.group('yes'))
        no_count = int(match.group('no'))
        vote_what = match.group('what')
        return self.getEvent('EVT_VOTE_FAILED', data={'yes': yes_count, 'no': no_count, 'what': vote_what})

    def OnFlagcapturetime(self, action, data, match=None):
        # FlagCaptureTime: 0: 1234567890
        # FlagCaptureTime: 1: 1125480101
        cid = match.group('cid')
        captime = int(match.group('captime'))
        client = self.getByCidOrJoinPlayer(cid)
        if not client:
            self.debug('No client found')
            return None
        return self.getEvent('EVT_FLAG_CAPTURE_TIME', client=client, data=captime)

    def OnClientjumprunstarted(self, action, data, match=None):
        cid = match.group('cid')
        way_id = match.group('way_id')
        attempt_num = match.group('attempt_num')
        attempt_max = match.group('attempt_max')
        client = self.getByCidOrJoinPlayer(cid)
        if not client:
            self.debug('No client found')
            return None
        return self.getEvent('EVT_CLIENT_JUMP_RUN_START', client=client, data={'way_id': way_id,
                                                                               'attempt_num': attempt_num,
                                                                               'attempt_max': attempt_max})

    def OnClientjumprunstopped(self, action, data, match=None):
        cid = match.group('cid')
        way_id = match.group('way_id')
        way_time = match.group('way_time')
        attempt_num = match.group('attempt_num')
        attempt_max = match.group('attempt_max')
        client = self.getByCidOrJoinPlayer(cid)
        if not client:
            self.debug('No client found')
            return None
        return self.getEvent('EVT_CLIENT_JUMP_RUN_STOP', client=client, data={'way_id': way_id,
                                                                              'way_time': way_time,
                                                                              'attempt_num': attempt_num,
                                                                              'attempt_max': attempt_max})
    
    def OnClientjumpruncanceled(self, action, data, match=None):
        cid = match.group('cid')
        way_id = match.group('way_id')
        attempt_num = match.group('attempt_num')
        attempt_max = match.group('attempt_max')
        client = self.getByCidOrJoinPlayer(cid)
        if not client:
            self.debug('No client found')
            return None
        return self.getEvent('EVT_CLIENT_JUMP_RUN_CANCEL', client=client, data={'way_id': way_id,
                                                                                'attempt_num': attempt_num,
                                                                                'attempt_max': attempt_max})
    
    def OnClientsaveposition(self, action, data, match=None):
        cid = match.group('cid')
        position = float(match.group('x')), float(match.group('y')), float(match.group('z'))
        client = self.getByCidOrJoinPlayer(cid)
        if not client:
            self.debug('No client found')
            return None
        return self.getEvent('EVT_CLIENT_POS_SAVE', client=client, data={'position': position})

    def OnClientloadposition(self, action, data, match=None):
        cid = match.group('cid')
        position = float(match.group('x')), float(match.group('y')), float(match.group('z'))
        client = self.getByCidOrJoinPlayer(cid)
        if not client:
            self.debug('No client found')
            return None
        return self.getEvent('EVT_CLIENT_POS_LOAD', client=client, data={'position': position})
    
    def OnClientgoto(self, action, data, match=None):
        cid = match.group('cid')
        tcid = match.group('tcid')
        position = float(match.group('x')), float(match.group('y')), float(match.group('z'))
        client = self.getByCidOrJoinPlayer(cid)
        if not client:
            self.debug('No client found')
            return None
        
        target = self.getByCidOrJoinPlayer(tcid)
        if not target:
            self.debug('No target client found')
            return None
            
        return self.getEvent('EVT_CLIENT_GOTO', client=client, target=target, data={'position': position})

    def OnClientspawn(self, action, data, match=None):
        # ClientSpawn: 0
        cid = match.group('cid')
        client = self.getByCidOrJoinPlayer(cid)
        if not client:
            self.debug('No client found')
            return None

        client.state = b3.STATE_ALIVE
        return self.getEvent('EVT_CLIENT_SPAWN', client=client)

    def OnClientmelted(self, action, data, match=None):
        # ClientMelted: 0
        cid = match.group('cid')
        client = self.getByCidOrJoinPlayer(cid)
        if not client:
            self.debug('No client found')
            return None

        client.state = b3.STATE_ALIVE
        return self.getEvent('EVT_CLIENT_MELTED', client=client)

    def OnSurvivorwinner(self, action, data, match=None):
        # SurvivorWinner: Blue
        # SurvivorWinner: Red
        # SurvivorWinner: 0
        # queue round and in any case (backwards compatibility for plugins)
        self.queueEvent(self.getEvent('EVT_GAME_ROUND_END'))
        if data in ('Blue', 'Red'):
            return self.getEvent('EVT_SURVIVOR_WIN', data=data)
        else:
            client = self.getByCidOrJoinPlayer(data)
            if not client:
                self.debug('No client found')
                return None
            return self.getEvent('EVT_CLIENT_SURVIVOR_WINNER', client=client)

    def OnFreeze(self, action, data, match=None):
        # 6:37 Freeze: 0 1 16: Fenix froze Biddle by UT_MOD_SPAS
        victim = self.getByCidOrJoinPlayer(match.group('cid'))
        if not victim:
            self.debug('No victim')
            return None

        attacker = self.getByCidOrJoinPlayer(match.group('acid'))
        if not attacker:
            self.debug('No attacker')
            return None

        weapon = match.group('aweap')
        if not weapon:
            self.debug('No weapon')
            return None

        victim.state = b3.STATE_DEAD
        return self.getEvent('EVT_CLIENT_FREEZE', data=weapon, client=attacker, target=victim)

    def OnThawoutstarted(self, action, data, match=None):
        # ThawOutStarted: 0 1: Fenix started thawing out Biddle
        client = self.getByCidOrJoinPlayer(match.group('cid'))
        if not client:
            self.debug('No client')
            return None

        target = self.getByCidOrJoinPlayer(match.group('tcid'))
        if not target:
            self.debug('No target')
            return None

        return self.getEvent('EVT_CLIENT_THAWOUT_STARTED', client=client, target=target)

    def OnThawoutfinished(self, action, data, match=None):
        # ThawOutFinished: 0 1: Fenix thawed out Biddle
        client = self.getByCidOrJoinPlayer(match.group('cid'))
        if not client:
            self.debug('No client')
            return None

        target = self.getByCidOrJoinPlayer(match.group('tcid'))
        if not target:
            self.debug('No target')
            return None

        target.state = b3.STATE_ALIVE
        return self.getEvent('EVT_CLIENT_THAWOUT_FINISHED', client=client, target=target)

    ####################################################################################################################
    #                                                                                                                  #
    #   B3 PARSER INTERFACE IMPLEMENTATION                                                                             #
    #                                                                                                                  #
    ####################################################################################################################

    def authorizeClients(self):
        """
        For all connected players, fill the client object with properties allowing to find
        the user in the database (usualy guid, or punkbuster id, ip) and call the
        Client.auth() method.
        """
        pass

    def ban(self, client, reason='', admin=None, silent=False, *kwargs):
        """
        Ban a given client.
        :param client: The client to ban
        :param reason: The reason for this ban
        :param admin: The admin who performed the ban
        :param silent: Whether or not to announce this ban
        """
        self.debug('BAN : client: %s, reason: %s', client, reason)
        if isinstance(client, Client) and not client.guid:
            # client has no guid, kick instead
            return self.kick(client, reason, admin, silent)
        elif isinstance(client, str) and re.match('^[0-9]+$', client):
            self.write(self.getCommand('ban', cid=client, reason=reason))
            return
        elif not client.id:
            # no client id, database must be down, do tempban
            self.error('Q3AParser.ban(): no client id, database must be down, doing tempban')
            return self.tempban(client, reason, 1440, admin, silent)

        if admin:
            variables = self.getMessageVariables(client=client, reason=reason, admin=admin)
            fullreason = self.getMessage('banned_by', variables)
        else:
            variables = self.getMessageVariables(client=client, reason=reason)
            fullreason = self.getMessage('banned', variables)

        if client.cid is None:
            # ban by ip, this happens when we !permban @xx a player that is not connected
            self.debug('EFFECTIVE BAN : %s', self.getCommand('banByIp', ip=client.ip, reason=reason))
            self.write(self.getCommand('banByIp', ip=client.ip, reason=reason))
        else:
            # ban by cid
            self.debug('EFFECTIVE BAN : %s', self.getCommand('ban', cid=client.cid, reason=reason))

            if self._permban_with_frozensand:
                cmd = self.getCommand('auth-permban', cid=client.cid)
                self.info('Sending ban to Frozen Sand : %s' % cmd)
                rv = self.write(cmd)
                if rv:
                    if rv == "Auth services disabled" or rv.startswith("auth: not banlist available."):
                        self.warning(rv)
                    elif rv.startswith("auth: sending ban"):
                        self.info(rv)
                        time.sleep(.250)
                    else:
                        self.warning(rv)
                        time.sleep(.250)

            if client.connected:
                cmd = self.getCommand('ban', cid=client.cid, reason=reason)
                self.info('Sending ban to server : %s' % cmd)
                rv = self.write(cmd)
                if rv:
                    self.info(rv)

        if not silent and fullreason != '':
            self.say(fullreason)

        if admin:
            admin.message('^7Banned^7: ^1%s^7 (^2@%s^7)' % (client.exactName, client.id))
            admin.message('^7His last ip (^1%s^7) has been added to banlist' % client.ip)

        self.queueEvent(self.getEvent('EVT_CLIENT_BAN', data={'reason': reason, 'admin': admin}, client=client))
        client.disconnect()

    def tempban(self, client, reason='', duration=2, admin=None, silent=False, *kwargs):
        """
        Tempban a client.
        :param client: The client to tempban
        :param reason: The reason for this tempban
        :param duration: The duration of the tempban
        :param admin: The admin who performed the tempban
        :param silent: Whether or not to announce this tempban
        """
        duration = time2minutes(duration)
        if isinstance(client, Client) and not client.guid:
            # client has no guid, kick instead
            return self.kick(client, reason, admin, silent)
        elif isinstance(client, str) and re.match('^[0-9]+$', client):
            self.write(self.getCommand('tempban', cid=client, reason=reason))
            return
        elif admin:
            banduration = b3.functions.minutesStr(duration)
            variables = self.getMessageVariables(client=client, reason=reason, admin=admin, banduration=banduration)
            fullreason = self.getMessage('temp_banned_by', variables)
        else:
            banduration = b3.functions.minutesStr(duration)
            variables = self.getMessageVariables(client=client, reason=reason, banduration=banduration)
            fullreason = self.getMessage('temp_banned', variables)

        if self._tempban_with_frozensand:
            minutes = duration
            days = hours = 0
            while minutes >= 60:
                hours += 1
                minutes -= 60
            while hours >= 24:
                days += 1
                hours -= 24

            cmd = self.getCommand('auth-tempban', cid=client.cid, days=days, hours=hours, minutes=int(minutes))
            self.info('Sending ban to Frozen Sand : %s' % cmd)
            rv = self.write(cmd)
            if rv:
                if rv == "Auth services disabled" or rv.startswith("auth: not banlist available."):
                    self.warning(rv)
                elif rv.startswith("auth: sending ban"):
                    self.info(rv)
                    time.sleep(.250)
                else:
                    self.warning(rv)
                    time.sleep(.250)

        if client.connected:
            cmd = self.getCommand('tempban', cid=client.cid, reason=reason)
            self.info('Sending ban to server : %s' % cmd)
            rv = self.write(cmd)
            if rv:
                self.info(rv)

        if not silent and fullreason != '':
            self.say(fullreason)

        self.queueEvent(self.getEvent('EVT_CLIENT_BAN_TEMP', data={'reason': reason,
                                                                   'duration': duration,
                                                                   'admin': admin}, client=client))
        client.disconnect()

    def inflictCustomPenalty(self, penalty_type, client, reason=None, duration=None, admin=None, data=None):
        """
        Urban Terror specific punishments.
        """
        if penalty_type == 'slap' and client:
            cmd = self.getCommand('slap', cid=client.cid)
            self.write(cmd)
            if reason:
                client.message("%s" % reason)
            return True

        elif penalty_type == 'nuke' and client:
            cmd = self.getCommand('nuke', cid=client.cid)
            self.write(cmd)
            if reason:
                client.message("%s" % reason)
            return True

        elif penalty_type == 'mute' and client:
            if duration is None:
                seconds = 60
            else:
                seconds = round(float(time2minutes(duration) * 60), 0)

            # make sure to unmute first
            cmd = self.getCommand('mute', cid=client.cid, seconds=0)
            self.write(cmd)
            # then mute
            cmd = self.getCommand('mute', cid=client.cid, seconds=seconds)
            self.write(cmd)
            if reason:
                client.message("%s" % reason)
            return True

        elif penalty_type == 'kill' and client:
            cmd = self.getCommand('kill', cid=client.cid)
            self.write(cmd)
            if reason:
                client.message("%s" % reason)
            return True

    ####################################################################################################################
    #                                                                                                                  #
    #   OTHER METHODS                                                                                                  #
    #                                                                                                                  #
    ####################################################################################################################

    def queryClientFrozenSandAccount(self, cid):
        """
        : auth-whois 0
        auth: id: 0 - name: ^7laCourge - login:  - notoriety: 0 - level: 0  - ^7no account

        : auth-whois 0
        auth: id: 0 - name: ^7laCourge - login: courgette - notoriety: serious - level: -1

        : auth-whois 3
        Client 3 is not active.
        """
        data = self.write('auth-whois %s' % cid)
        if not data:
            return dict()

        if data == "Client %s is not active." % cid:
            return dict()

        m = self._re_authwhois.match(data)
        if m:
            return m.groupdict()
        else:
            return {}

    def queryAllFrozenSandAccount(self, max_retries=None):
        """
        Query the accounts of all the online clients.
        """
        data = self.write('auth-whois all', maxRetries=max_retries)
        if not data:
            return {}
        players = {}
        for m in re.finditer(self._re_authwhois, data):
            players[m.group('cid')] = m.groupdict()
        return players

    def is_frozensand_auth_available(self):
        """
        Check whether the auth system is available.
        """
        cvar = self.getCvar('auth')
        if cvar:
            auth = cvar.getInt()
            return auth != 0
        else:
            return False

    def defineGameType(self, gametype_int):
        """
        Translate the gametype to a readable format (also for teamkill plugin!)
        """
        gametype = str(gametype_int)

        if gametype_int == '0':
            gametype = 'ffa'
        elif gametype_int == '1':  # Last Man Standing
            gametype = 'lms'
        elif gametype_int == '2':  # Quake 3 Arena single player
            gametype = 'dm'
        elif gametype_int == '3':
            gametype = 'tdm'
        elif gametype_int == '4':
            gametype = 'ts'
        elif gametype_int == '5':
            gametype = 'ftl'
        elif gametype_int == '6':
            gametype = 'cah'
        elif gametype_int == '7':
            gametype = 'ctf'
        elif gametype_int == '8':
            gametype = 'bm'
        elif gametype_int == '9':
            gametype = 'jump'
        elif gametype_int == '10':
            gametype = 'freeze'

        return gametype

    def _getDamagePoints(self, weapon, hitloc):
        """
        Provide the estimated number of damage points inflicted by
        a hit of a given weapon to a given body location.
        """
        try:
            points = self.damage[weapon][int(hitloc) - 1]
            self.debug("_getDamagePoints(%s, %s) -> %d" % (weapon, hitloc, points))
            return points
        except (KeyError, IndexError), err:
            self.warning("_getDamagePoints(%s, %s) cannot find value : %s" % (weapon, hitloc, err))
            return 15

    def patch_spamcontrolPlugin(self):
        """
        This method alters the Spamcontrol plugin after it started to make it aware of RADIO spam.
        """
        self.info("Patching spamcontrol plugin...")

        def onRadio(this, event):
            new_event = Event(type=event.type, client=event.client, target=event.target, data=repr(event.data))
            this.onChat(new_event)

        self.spamcontrolPlugin.onRadio = new.instancemethod(onRadio, self.spamcontrolPlugin, SpamcontrolPlugin)
        self.spamcontrolPlugin.registerEvent('EVT_CLIENT_RADIO', self.spamcontrolPlugin.onRadio)

    @staticmethod
    def patch_Clients():

        def newClient(self, cid, **kwargs):
            """
            Patch the newClient method in the Clients class to handle UrT 4.2 specific client instances.
            """
            client = Iourt42Client(console=self.console, cid=cid, timeAdd=self.console.time(), **kwargs)
            self[client.cid] = client
            self.resetIndex()

            self.console.debug('Urt42 Client Connected: [%s] %s - %s (%s)',  self[client.cid].cid, self[client.cid].name,
                                                                             self[client.cid].guid, self[client.cid].data)

            self.console.queueEvent(self.console.getEvent('EVT_CLIENT_CONNECT', data=client, client=client))

            if client.guid:
                client.auth()
            elif not client.authed:
                self.authorizeClients()
            return client

        def newGetByMagic(self, handle):
            """
            Patch the getByMagic method in the Clients class so it's possible to lookup players using the auth login.
            """
            handle = handle.strip()
            if re.match(r'^[0-9]+$', handle):
                client = self.getByCID(handle)
                if client:
                    return [client]
                return []
            elif re.match(r'^@([0-9]+)$', handle):
                return self.getByDB(handle)
            elif handle[:1] == '\\':
                c = self.getByName(handle[1:])
                if c and not c.hide:
                    return [c]
                return []
            else:
                clients = []
                needle = re.sub(r'\s', '', handle.lower())
                for cid, c in self.items():
                    cleanname = re.sub(r'\s', '', c.name.lower())
                    if not c.hide and (needle in cleanname or needle in c.pbid) and not c in clients:
                        clients.append(c)
                return clients

        b3.clients.Clients.newClient = newClient
        b3.clients.Clients.getByMagic = newGetByMagic