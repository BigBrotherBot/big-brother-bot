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
#  * parser created
# 2012/08/08 - 1.0 - Courgette
#  * new authentication system using the Frozen Sand Account if available
# 2012/08/08 - 1.1 - Courgette
#  * fix error when computing Hit damage. Until we got real value, the default value : 15 is returned for all
#    weapons and all hit locations.
# 2012/08/09 - 1.2 - Courgette
#  * make sure the game is UrT 4.2 or fail to start
# 2012/08/09 - 1.2.1 - Courgette
#  * disabling authentication using the /rcon auth-whois command response
# 2012/08/12 - 1.3 - Courgette
#  * patches the Spamcontrol plugin to make it aware of radio spam
# 2012/09/14 - 1.4 - Courgette
#  * change kick and tempban commands so them give the reason
# 2012/10/04 - 1.5 - Courgette
#  * update for UrT 4.2.002 new auth system with Frozen Sand Account and auth-key
# 2012/10/04 - 1.5.1 - Courgette
#  * fix kick and tempban when used with a reason
# 2012/10/10 - 1.5.2 - Courgette
#  * support names with blank characters
# 2012/10/24 - 1.6 - Courgette
#  * new: settings to ban with the Frozen Sand auth system
# 2012/11/09 - 1.7 - Courgette
#  * new: support new jump game type with code 9
# 2012/11/15 - 1.7.1 - Courgette
#  * fix: banning with the Frozen Sand auth system now works with servers set to auth private or notoriety mode
# 26/11/2012 - 1.8 - Courgette
#     * protect some of the Client object property
# 26/11/2012 - 1.9 - Courgette
#     * fix authentication for connecting player Frosen Sand Account is uniquely known in the B3 database
# 07/12/2012 - 1.10 - Courgette
#     * add new events : EVT_CLIENT_JUMP_TIMER_START, EVT_CLIENT_JUMP_TIMER_STOP, EVT_CLIENT_POS_SAVE,
#       EVT_CLIENT_POS_LOAD and EVT_CLIENT_SURVIVOR_WINNERwhich can be used by plugins
# 08/12/2012 - 1.10.1 - Courgette
#     * fix EVT_CLIENT_JUMP_TIMER_START and EVT_CLIENT_JUMP_TIMER_STOP events when no location name is provided
# 22/12/2012 - 1.11 - Courgette
#     * update for UrT 4.2.009 release. adds UT_MOD_SMITED, UT_MOD_GLOCK and fix constants values for some of the
#       UT_MOD_* constants.
# 08/01/2013 - 1.11.1 - Courgette
#     * fix EVT_SURVIVOR_WIN event
#
import re, new
import time
from b3.functions import time2minutes
from b3.parsers.iourt41 import Iourt41Parser
import b3
from b3.clients import Client
from b3.events import Event
from b3.plugins.spamcontrol import SpamcontrolPlugin

__author__  = 'Courgette'
__version__ = '1.11.1'

class Iourt42Client(Client):

    def auth_by_guid(self):
        try:
            return self.console.storage.getClient(self)
        except KeyError, msg:
            self.console.debug('User not found %s: %s', self.guid, msg)
            return False

    def auth_by_pbid(self):
        clients_matching_pbid = self.console.storage.getClientsMatching({ 'pbid' : self.pbid })
        if len(clients_matching_pbid) > 1:
            self.console.error("DATA ERROR: found %s client having Frozen Sand Account '%s'" % (len(clients_matching_pbid), self.pbid))
            return self.auth_by_pbid_and_guid()
        elif len(clients_matching_pbid) == 1:
            self.id = clients_matching_pbid[0].id
            # we may have a second client entry in database with current guid. We want to update our current
            # client guid only if it is not the case.
            try:
                client_by_guid = self.console.storage.getClient(Client(guid=self.guid))
            except KeyError:
                client_by_guid = None
            if client_by_guid and client_by_guid.id != self.id:
                self._guid = None # so storage.getClient is able to overwrite the value which will make it remain unchanged in database when .save() will be called later on
            return self.console.storage.getClient(self)
        else:
            self.console.debug('Frozen Sand Account [%s] unknown in database', self.pbid)
            return False

    def auth_by_pbid_and_guid(self):
        clients_matching_pbid = self.console.storage.getClientsMatching({ 'pbid': self.pbid, 'guid': self.guid })
        if len(clients_matching_pbid):
            self.id = clients_matching_pbid[0].id
            return self.console.storage.getClient(self)
        else:
            self.console.debug("Frozen Sand Account [%s] with guid '%s' unknown in database" % (self.pbid, self.guid))
            return False

    """
    The b3.clients.Client.auth method needs to be changed to fit the UrT4.2 authentication scheme.
    In UrT4.2 :
     * all connected players have a cl_guid
     * some have a Frozen Sand Account (FSA)

    The FSA is a worldwide identifier while the cl_guid only identify a player on a given game server.

    See http://forum.bigbrotherbot.net/urban-terror-4-2/urt-4-2-discussion/
    """
    def auth(self):
        if not self.authed and self.guid and not self.authorizing:
            self.authorizing = True

            name = self.name
            ip = self.ip
            pbid = self.pbid

            if not pbid and self.cid:
                fsa_info = self.console.queryClientFrozenSandAccount(self.cid)
                self.pbid = pbid = fsa_info.get('login', None)

            # Frozen Sand Account related info
            if not hasattr(self, 'notoriety'):
                self.notoriety = None

            # FSA will be found in pbid
            if not self.pbid:
                # auth with cl_guid only
                try:
                    inStorage = self.auth_by_guid()
                except Exception, e:
                    self.console.error("auth by guid failed", exc_info=e)
                    self.authorizing = False
                    return False
            else:
                # auth with FSA
                try:
                    inStorage = self.auth_by_pbid()
                except Exception, e:
                    self.console.error("auth by FSA failed", exc_info=e)
                    self.authorizing = False
                    return False

                if not inStorage:
                    # fallback on auth with cl_guid only
                    try:
                        inStorage = self.auth_by_guid()
                    except Exception, e:
                        self.console.error("auth by guid failed (when no known FSA)", exc_info=e)
                        self.authorizing = False
                        return False

            #lastVisit = None
            if inStorage:
                self.console.bot('Client found in storage @%s, welcome back %s (FSA: %s)', str(self.id), self.name, self.pbid)
                self.lastVisit = self.timeEdit
            else:
                self.console.bot('Client not found in the storage %s (FSA: %s), create new', str(self.guid), self.pbid)

            self.connections = int(self.connections) + 1
            self.name = name
            self.ip = ip
            if pbid:
                self.pbid = pbid
            self.save()
            self.authed = True

            self.console.debug('Client Authorized: @%s "%s" [%s] (FSA: %s)', self.cid, self.name, self.guid, self.pbid)

            # check for bans
            if self.numBans > 0:
                ban = self.lastBan
                if ban:
                    self.reBan(ban)
                    self.authorizing = False
                    return False

            self.refreshLevel()

            self.console.queueEvent(b3.events.Event(b3.events.EVT_CLIENT_AUTH,
                self,
                self))

            self.authorizing = False

            return self.authed
        else:
            return False

    def __str__(self):
        return "Client42<@%s:%s|%s:\"%s\":%s>" % (self.id, self.guid, self.pbid, self.name, self.cid)

class Iourt42Parser(Iourt41Parser):
    gameName = 'iourt42'


    _commands = {
        'broadcast': '%(prefix)s^7 %(message)s',
        'message': 'tell %(cid)s %(prefix)s ^3[pm]^7 %(message)s',
        'deadsay': 'tell %(cid)s %(prefix)s [DEAD]^7 %(message)s',
        'say': 'say %(prefix)s %(message)s',
        'saybig': 'bigtext "%(prefix)s %(message)s"',
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

        #Radio: 0 - 7 - 2 - "New Alley" - "I'm going for the flag"
        re.compile(r'''^(?P<action>Radio): (?P<data>(?P<cid>[0-9]+) - (?P<msg_group>[0-9]+) - (?P<msg_id>[0-9]+) - "(?P<location>.+)" - "(?P<text>.*)")$'''),

        #Callvote: 1 - "map dressingroom"
        re.compile(r'''^(?P<action>Callvote): (?P<data>(?P<cid>[0-9]+) - "(?P<vote_string>.*)")$'''),

        #Vote: 0 - 2
        re.compile(r'''^(?P<action>Vote): (?P<data>(?P<cid>[0-9]+) - (?P<value>.*))$'''),

        #13:34 ClientJumpTimerStarted: 0 - way: 2 (Easy Way)
        re.compile(r'^(?P<action>ClientJumpTimerStarted):\s(?P<cid>\d+)\s-\s(?P<data>way: (?P<way_id>\d+)(?:\s\((?P<way_label>.+)\))?)$', re.IGNORECASE),
        #13:34 ClientJumpTimerStopped: 0 - 5 seconds - way: 1 (Hard Way)
        re.compile(r'^(?P<action>ClientJumpTimerStopped):\s(?P<cid>\d+)\s-\s(?P<data>(?P<duration>.+)\s-\sway: (?P<way_id>\d+)(?:\s\((?P<way_label>.+)\))?)$', re.IGNORECASE),

        #13:34 ClientSavePosition: 0 - 335.384887 - 67.469154 - -23.875000 - "unknown"
        #13:34 ClientLoadPosition: 0 - 335.384887 - 67.469154 - -23.875000 - "unknown"
        re.compile(r'^(?P<action>Client(Save|Load)Position):\s(?P<cid>\d+)\s-\s(?P<data>(?P<x>-?\d+(?:\.\d+)?)\s-\s(?P<y>-?\d+(?:\.\d+)?)\s-\s(?P<z>-?\d+(?:\.\d+)?)\s-\s"(?P<name>.*)")$', re.IGNORECASE),

        #Generated with ioUrbanTerror v4.1:
        #Hit: 12 7 1 19: BSTHanzo[FR] hit ercan in the Helmet
        #Hit: 13 10 0 8: Grover hit jacobdk92 in the Head
        re.compile(r'^(?P<action>Hit):\s(?P<data>(?P<cid>[0-9]+)\s(?P<acid>[0-9]+)\s(?P<hitloc>[0-9]+)\s(?P<aweap>[0-9]+):\s+(?P<text>.*))$', re.IGNORECASE),
        #re.compile(r'^(?P<action>[a-z]+):\s(?P<data>(?P<cid>[0-9]+)\s(?P<acid>[0-9]+)\s(?P<hitloc>[0-9]+)\s(?P<aweap>[0-9]+):\s+(?P<text>(?P<aname>[^:])\shit\s(?P<name>[^:])\sin\sthe(?P<locname>.*)))$', re.IGNORECASE),

        #6:37 Kill: 0 1 16: XLR8or killed =lvl1=Cheetah by UT_MOD_SPAS
        #2:56 Kill: 14 4 21: Qst killed Leftovercrack by UT_MOD_PSG1
        re.compile(r'^(?P<action>[a-z]+):\s(?P<data>(?P<acid>[0-9]+)\s(?P<cid>[0-9]+)\s(?P<aweap>[0-9]+):\s+(?P<text>.*))$', re.IGNORECASE),
        #re.compile(r'^(?P<action>[a-z]+):\s(?P<data>(?P<acid>[0-9]+)\s(?P<cid>[0-9]+)\s(?P<aweap>[0-9]+):\s+(?P<text>(?P<aname>[^:])\skilled\s(?P<name>[^:])\sby\s(?P<modname>.*)))$', re.IGNORECASE),

        #Processing chats and tell events...
        #5:39 saytell: 15 16 repelSteeltje: nno
        #5:39 saytell: 15 15 repelSteeltje: nno
        re.compile(r'^(?P<action>[a-z]+):\s(?P<data>(?P<cid>[0-9]+)\s(?P<acid>[0-9]+)\s(?P<name>.+?):\s+(?P<text>.*))$', re.IGNORECASE),

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
        # say: 6 ^5Marcel ^2[^6CZARMY^2]: !help
        re.compile(r'^(?P<action>[a-z]+):\s(?P<data>(?P<cid>[0-9]+)\s(?P<name>.+?):\s*(?P<text>.*))$', re.IGNORECASE),

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

    # /rcon auth-whois replies patterns
    _re_authwhois = re.compile(r"""^auth: id: (?P<cid>\d+) - name: \^7(?P<name>.+?) - login: (?P<login>.*?) - notoriety: (?P<notoriety>.+?) - level: (?P<level>-?\d+?)(?:\s+- (?P<extra>.*))?$""", re.MULTILINE)


    _permban_with_frozensand = False
    _tempban_with_frozensand = False

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
    UT_MOD_KICKED='24' # not exising in 4.2 ?
    UT_MOD_HEGRENADE='25'
    UT_MOD_SR8='27'
    UT_MOD_AK103='29'
    UT_MOD_SPLODED='30'
    UT_MOD_SLAPPED='31'
    UT_MOD_SMITED = '32'
    UT_MOD_BOMBED='33'
    UT_MOD_NUKED='34'
    UT_MOD_NEGEV='35'
    UT_MOD_HK69_HIT='36'
    UT_MOD_M4='37'
    UT_MOD_GLOCK='38'
    UT_MOD_FLAG='39'
    UT_MOD_GOOMBA='40'

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
        23: UT_MOD_KNIFE_THROWN,
    }


    def __new__(cls, *args, **kwargs):
        Iourt42Parser.patch_Clients()
        return Iourt41Parser.__new__(cls)


    def startup(self):
        try:
            gamename = self.getCvar('gamename').getString()
            if gamename != 'q3urt42':
                self.error("the iourt42 B3 parser cannot be used with a game server other than Urban Terror 4.2")
                raise SystemExit(220)
        except Exception, e:
            self.warning("Could not query server for gamename.", exc_info=e)

        Iourt41Parser.startup(self)

        # add UrT 4.2 specific events
        self.EVT_CLIENT_RADIO = self.Events.createEvent('EVT_CLIENT_RADIO', 'Event client radio')
        self.EVT_GAME_FLAG_HOTPOTATO = self.Events.createEvent('EVT_GAME_FLAG_HOTPOTATO', 'Event game hotpotato')
        self._eventMap['hotpotato'] = self.EVT_GAME_FLAG_HOTPOTATO
        self.EVT_CLIENT_CALLVOTE = self.Events.createEvent('EVT_CLIENT_CALLVOTE', 'Event client call vote')
        self.EVT_CLIENT_VOTE = self.Events.createEvent('EVT_CLIENT_VOTE', 'Event client vote')
        self.EVT_CLIENT_JUMP_TIMER_START = self.Events.createEvent('EVT_CLIENT_JUMP_TIMER_START', 'Event client jump timer started')
        self.EVT_CLIENT_JUMP_TIMER_STOP = self.Events.createEvent('EVT_CLIENT_JUMP_TIMER_STOP', 'Event client jump timer stopped')
        self.EVT_CLIENT_POS_SAVE = self.Events.createEvent('EVT_CLIENT_POS_SAVE', 'Event client position saved')
        self.EVT_CLIENT_POS_LOAD = self.Events.createEvent('EVT_CLIENT_POS_LOAD', 'Event client position loaded')
        self.EVT_CLIENT_SURVIVOR_WINNER = self.Events.createEvent('EVT_CLIENT_SURVIVOR_WINNER', 'Event client survivor winner')

        self.load_conf_frozensand_ban_settings()


    def pluginsStarted(self):
        """ called when all plugins are started """
        self.spamcontrolPlugin = self.getPlugin("spamcontrol")
        if self.spamcontrolPlugin:
            self.patch_spamcontrolPlugin()



    ###############################################################################################
    #
    #    Config loaders
    #
    ###############################################################################################

    def load_conf_frozensand_ban_settings(self):
        try:
            frozensand_auth_available = self.is_frozensand_auth_available()
        except Exception, e:
            self.warning("Could not query server for cvar auth.", exc_info=e)
            frozensand_auth_available = False
        self.info("Frozen Sand auth system enabled : %s" % ('yes' if frozensand_auth_available else 'no'))

        try:
            frozensand_auth_owners = self.getCvar('auth_owners').getString()
        except Exception, e:
            self.warning("Could not query server for cvar auth_owners.", exc_info=e)
            frozensand_auth_owners = ""
        self.info("Frozen Sand auth_owners set : %s" % (('yes - %s' % frozensand_auth_available) if frozensand_auth_owners else 'no'))

        if frozensand_auth_available and frozensand_auth_owners:
            self.load_conf_permban_with_frozensand()
            self.load_conf_tempban_with_frozensand()
            if self._permban_with_frozensand or self._tempban_with_frozensand:
                self.info("NOTE: when banning with the Frozen Sand auth system, B3 cannot remove the bans on the urbanterror.info website. To unban a player you will have to first unban him on B3 and then also unban him on the official Frozen Sand website : http://www.urbanterror.info/groups/list/all/?search=%s" % frozensand_auth_owners)

        else:
            self.info("ignoring settings about banning with Frozen Sand auth system as the auth system is not enabled or auth_owners not set")



    def load_conf_permban_with_frozensand(self):
        self._permban_with_frozensand = False
        try:
            self._permban_with_frozensand = self.config.getboolean('server', 'permban_with_frozensand')
        except Exception, err:
            self.warning(err)
        self.info("Send permbans to Frozen Sand : %s" % ('yes' if self._permban_with_frozensand else 'no'))


    def load_conf_tempban_with_frozensand(self):
        self._tempban_with_frozensand = False
        try:
            self._tempban_with_frozensand = self.config.getboolean('server', 'tempban_with_frozensand')
        except Exception, err:
            self.warning(err)
        self.info("Send temporary bans to Frozen Sand : %s" % ('yes' if self._tempban_with_frozensand else 'no'))



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
        client = self.getByCidOrJoinPlayer(cid)
        if not client:
            self.debug('No client found')
            return None
        return Event(self.EVT_CLIENT_RADIO, client=client, data={
            'msg_group': msg_group,
            'msg_id': msg_id,
            'location': location,
            'text': text
        })

    def OnCallvote(self, action, data, match=None):
        cid = match.group('cid')
        vote_string = match.group('vote_string')
        client = self.getByCidOrJoinPlayer(cid)
        if not client:
            self.debug('No client found')
            return None
        return Event(self.EVT_CLIENT_CALLVOTE, client=client, data=vote_string)

    def OnVote(self, action, data, match=None):
        cid = match.group('cid')
        value = match.group('value')
        client = self.getByCidOrJoinPlayer(cid)
        if not client:
            self.debug('No client found')
            return None
        return Event(self.EVT_CLIENT_VOTE, client=client, data=value)

    def OnClientjumptimerstarted(self, action, data, match=None):
        cid = match.group('cid')
        way_id = match.group('way_id')
        way_label = match.group('way_label')
        client = self.getByCidOrJoinPlayer(cid)
        if not client:
            self.debug('No client found')
            return None
        return Event(self.EVT_CLIENT_JUMP_TIMER_START, client=client, data={'way_id': way_id, 'way_label': way_label})

    def OnClientjumptimerstopped(self, action, data, match=None):
        cid = match.group('cid')
        way_id = match.group('way_id')
        way_label = match.group('way_label')
        duration = match.group('duration')
        client = self.getByCidOrJoinPlayer(cid)
        if not client:
            self.debug('No client found')
            return None
        return Event(self.EVT_CLIENT_JUMP_TIMER_STOP, client=client, data={'way_id': way_id, 'way_label': way_label, 'duration': duration})

    def OnClientsaveposition(self, action, data, match=None):
        cid = match.group('cid')
        position = float(match.group('x')), float(match.group('y')), float(match.group('z'))
        name = match.group('name')
        client = self.getByCidOrJoinPlayer(cid)
        if not client:
            self.debug('No client found')
            return None
        return Event(self.EVT_CLIENT_POS_SAVE, client=client, data={'position': position, 'name': name})

    def OnClientloadposition(self, action, data, match=None):
        cid = match.group('cid')
        position = float(match.group('x')), float(match.group('y')), float(match.group('z'))
        name = match.group('name')
        client = self.getByCidOrJoinPlayer(cid)
        if not client:
            self.debug('No client found')
            return None
        return Event(self.EVT_CLIENT_POS_LOAD, client=client, data={'position': position, 'name': name})

    def OnSurvivorwinner(self, action, data, match=None):
        #SurvivorWinner: Blue
        #SurvivorWinner: Red
        #SurvivorWinner: 0
        if data in ('Blue', 'Red'):
            return b3.events.Event(b3.events.EVT_SURVIVOR_WIN, data)
        else:
            client = self.getByCidOrJoinPlayer(data)
            if not client:
                self.debug('No client found')
                return None
            return Event(self.EVT_CLIENT_SURVIVOR_WINNER, client=client, data=None)



    ###############################################################################################
    #
    #    B3 Parser interface implementation
    #
    ###############################################################################################

    def authorizeClients(self):
        pass


    def ban(self, client, reason='', admin=None, silent=False, *kwargs):
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
            return self.tempban(client, reason, '1d', admin, silent)

        if admin:
            fullreason = self.getMessage('banned_by', self.getMessageVariables(client=client, reason=reason, admin=admin))
        else:
            fullreason = self.getMessage('banned', self.getMessageVariables(client=client, reason=reason))

        if client.cid is None:
            # ban by ip, this happens when we !permban @xx a player that is not connected
            self.debug('EFFECTIVE BAN : %s',self.getCommand('banByIp', ip=client.ip, reason=reason))
            self.write(self.getCommand('banByIp', ip=client.ip, reason=reason))
        else:
            # ban by cid
            self.debug('EFFECTIVE BAN : %s',self.getCommand('ban', cid=client.cid, reason=reason))

            if self._permban_with_frozensand:
                cmd = self.getCommand('auth-permban', cid=client.cid)
                self.info('sending ban to Frozen Sand : %s' % cmd)
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
                self.info('sending ban to server : %s' % cmd)
                rv = self.write(cmd)
                if rv:
                    self.info(rv)

        if not silent and fullreason != '':
            self.say(fullreason)

        if admin:
            admin.message('^3banned^7: ^1%s^7 (^2@%s^7). His last ip (^1%s^7) has been added to banlist'%(client.exactName, client.id, client.ip))

        self.queueEvent(b3.events.Event(b3.events.EVT_CLIENT_BAN, {'reason': reason, 'admin': admin}, client))
        client.disconnect()



    def tempban(self, client, reason='', duration=2, admin=None, silent=False, *kwargs):
        duration = time2minutes(duration)

        if isinstance(client, Client) and not client.guid:
            # client has no guid, kick instead
            return self.kick(client, reason, admin, silent)
        elif isinstance(client, str) and re.match('^[0-9]+$', client):
            self.write(self.getCommand('tempban', cid=client, reason=reason))
            return
        elif admin:
            fullreason = self.getMessage('temp_banned_by', self.getMessageVariables(client=client, reason=reason, admin=admin, banduration=b3.functions.minutesStr(duration)))
        else:
            fullreason = self.getMessage('temp_banned', self.getMessageVariables(client=client, reason=reason, banduration=b3.functions.minutesStr(duration)))

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
            self.info('sending ban to Frozen Sand : %s' % cmd)
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
            self.info('sending ban to server : %s' % cmd)
            rv = self.write(cmd)
            if rv:
                self.info(rv)

        if not silent and fullreason != '':
            self.say(fullreason)

        self.queueEvent(b3.events.Event(b3.events.EVT_CLIENT_BAN_TEMP, {'reason': reason,
                                                                        'duration': duration,
                                                                        'admin': admin}
            , client))
        client.disconnect()



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
            return {}

        if data == "Client %s is not active." % cid:
            return {}

        m = self._re_authwhois.match(data)
        if m:
            return m.groupdict()
        else:
            return {}


    def queryAllFrozenSandAccount(self, maxRetries=None):
        data = self.write('auth-whois all', maxRetries=maxRetries)
        if not data:
            return {}
        players = {}
        for m in re.finditer(self._re_authwhois, data):
            players[m.group('cid')] = m.groupdict()
        return players


    def is_frozensand_auth_available(self):
        auth = self.getCvar('auth').getInt()
        return auth != 0


    # Parse Userinfo
    def OnClientuserinfo(self, action, data, match=None):
        #2 \ip\145.99.135.227:27960\challenge\-232198920\qport\2781\protocol\68\battleye\1\name\[SNT]^1XLR^78or\rate\8000\cg_predictitems\0\snaps\20\model\sarge\headmodel\sarge\team_model\james\team_headmodel\*james\color1\4\color2\5\handicap\100\sex\male\cl_anonymous\0\teamtask\0\cl_guid\58D4069246865BB5A85F20FB60ED6F65
        #conecting bot:
        #0 \gear\GMIORAA\team\blue\skill\5.000000\characterfile\bots/ut_chicken_c.c\color\4\sex\male\race\2\snaps\20\rate\25000\name\InviteYourFriends!
        bclient = self.parseUserInfo(data)

        if not bclient.has_key('cl_guid') and bclient.has_key('skill'):
            # must be a bot connecting
            self.bot('Bot Connecting!')
            bclient['ip'] = '0.0.0.0'
            bclient['cl_guid'] = 'BOT' + str(bclient['cid'])

        if bclient.has_key('name'):
            # remove spaces from name
            bclient['name'] = bclient['name'].replace(' ','')


        # split port from ip field
        if bclient.has_key('ip'):
            ipPortData = bclient['ip'].split(':', 1)
            bclient['ip'] = ipPortData[0]
            if len(ipPortData) > 1:
                bclient['port'] = ipPortData[1]

        if bclient.has_key('team'):
            bclient['team'] = self.getTeam(bclient['team'])

        self.verbose('Parsed user info %s' % bclient)

        if bclient:
            client = self.clients.getByCID(bclient['cid'])

            if client:
                # update existing client
                for k, v in bclient.iteritems():
                    if hasattr(client, 'gear') and k == 'gear' and client.gear != v:
                        self.queueEvent(b3.events.Event(b3.events.EVT_CLIENT_GEAR_CHANGE, v, client))
                    if not k.startswith('_') and k not in ('login', 'password', 'groupBits', 'maskLevel', 'autoLogin', 'greeting'):
                        setattr(client, k, v)
            else:
                #make a new client
                # use cl_guid
                if bclient.has_key('cl_guid'):
                    guid = bclient['cl_guid']
                else:
                    guid = 'unknown'

                # query FrozenSand Account
                auth_info = self.queryClientFrozenSandAccount(bclient['cid'])
                fsa = auth_info.get('login', None)

                # v1.0.17 - mindriot - 02-Nov-2008
                if not bclient.has_key('name'):
                    bclient['name'] = self._empty_name_default

                if not bclient.has_key('ip'):
                    if guid == 'unknown':
                        # happens when a client is (temp)banned and got kicked so client was destroyed, but
                        # infoline was still waiting to be parsed.
                        self.debug('Client disconnected. Ignoring.')
                        return None
                    else:
                        # see issue xlr8or/big-brother-bot#87 - ip can be missing
                        try:
                            self.debug("missing IP, trying to get ip with 'status'")
                            plist = self.getPlayerList()
                            client_data = plist[bclient['cid']]
                            bclient['ip'] = client_data['ip']
                        except Exception, err:
                            bclient['ip'] = ''
                            self.warning("Failed to get client %s ip address." % bclient['cid'], err)



                nguid = ''
                # overide the guid... use ip's only if self.console.IpsOnly is set True.
                if self.IpsOnly:
                    nguid = bclient['ip']
                # replace last part of the guid with two segments of the ip
                elif self.IpCombi:
                    i = bclient['ip'].split('.')
                    d = len(i[0])+len(i[1])
                    nguid = guid[:-d]+i[0]+i[1]
                # Quake clients don't have a cl_guid, we'll use ip instead
                elif guid == 'unknown':
                    nguid = bclient['ip']

                if nguid != '':
                    guid = nguid

                self.clients.newClient(bclient['cid'], name=bclient['name'], ip=bclient['ip'], state=b3.STATE_ALIVE,
                    guid=guid, pbid=fsa, data=auth_info)

        return None


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
        elif gameTypeInt == '9':
            _gameType = 'jump'

        #self.debug('_gameType: %s' % _gameType)
        return _gameType


    def _getDamagePoints(self, weapon, hitloc):
        """
        provide the estimated number of damage points inflicted by a hit of a given weapon to a given body location.
        """
        '''
        try:
            points = self.damage[weapon][int(hitloc)]
            self.debug("_getDamagePoints(%s, %s) -> %s" % (weapon, hitloc, points))
            return points
        except KeyError, err:
            self.warning("_getDamagePoints(%s, %s) cannot find value : %s" % (weapon, hitloc, err))
            return 15
        '''
        # until we got real values, we return the default value
        return 15


    def patch_spamcontrolPlugin(self):
        """ This method alters the Spamcontrol plugin after it started to make it aware of RADIO spam """
        self.info("Patching Spamcontrol plugin")
        # teach the Spamcontrol plugin how to react on such events
        def onRadio(this, event):
            new_event = Event(type=event.type, client=event.client, target=event.target, data=repr(event.data))
            this.onChat(new_event)
        self.spamcontrolPlugin.onRadio = new.instancemethod(onRadio, self.spamcontrolPlugin, SpamcontrolPlugin)
        self.spamcontrolPlugin.eventHanlders[self.EVT_CLIENT_RADIO] = self.spamcontrolPlugin.onRadio
        self.spamcontrolPlugin.registerEvent(self.EVT_CLIENT_RADIO)



    @staticmethod
    def patch_Clients():
        def newClient(self, cid, **kwargs):
            client = Iourt42Client(console=self.console, cid=cid, timeAdd=self.console.time(), **kwargs)
            self[client.cid] = client
            self.resetIndex()

            self.console.debug('Urt42 Client Connected: [%s] %s - %s (%s)', self[client.cid].cid, self[client.cid].name, self[client.cid].guid, self[client.cid].data)

            self.console.queueEvent(b3.events.Event(b3.events.EVT_CLIENT_CONNECT,
                client,
                client))

            if client.guid:
                client.auth()
            elif not client.authed:
                self.authorizeClients()
            return client
        b3.clients.Clients.newClient = newClient
