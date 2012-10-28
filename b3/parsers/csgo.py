# coding=UTF-8
#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2012 <courgette@bigbrotherbot.net>
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
#
# 2012-08-28 - 0.4 - Courgette
#   * fix sync()
# 2012-08-28 - 0.5 - Courgette
#   * fix SourceRconError: RCON message too large to send
#   * should fix UnicodeDecodeError in Rcon class when sending a command
#   * refactors the regular expressions for game events to make them easier to read
#   * add method parseProperties which helps extracting extended game log format
#   * add SourceMod SuperLogs CS:S specific events : EVT_SUPERLOGS_WEAPONSTATS and EVT_SUPERLOGS_WEAPONSTATS2
# 2012-08-29 - 0.6 - Courgette
#   * fix Courgette/big-brother-bot#84 - SourceRconError: RCON message too large to send
#   * fix Courgette/big-brother-bot#85 - rcon write() does is missing the maxRetries parameter
#   * fix Courgette/big-brother-bot#86 - UnicodeDecodeError
#   * add kill location as a 5th element to data for events EVT_CLIENT_KILL EVT_CLIENT_SUICIDE EVT_CLIENT_KILL_TEAM
#     if the SourceMod SuperLogs plugin is active and provides kill locations.
#   * fire EVT_CLIENT_ACTION events for game events Got_The_Bomb, Dropped_The_Bomb, Planted_The_Bomb,
#     Begin_Bomb_Defuse_Without_Kit, Defused_The_Bomb, headshot, round_mvp
# 2012-09-11 - 0.7 Courgette
#   * tweak say lines max length
# 2012-09-11 - 0.8 Courgette
#   * full unicode support
# 2012-09-13 - 1.0 Courgette
#   * split long messages into lines and add B3 prefixes to them
# 2012-09-13 - 1.1 Courgette
#   * add support for SourceMod plugin "B3 Say"
# 2012-09-17 - 1.2 Courgette
#   * fix say event when player has no team
#   * fix ban/tempban/unban
#   * add event EVT_SERVER_REQUIRES_RESTART which is triggered when the server requires a restart. This can be useful
#     for a plugin could act upon such event by send an email to admin, restarting the server, ...
#   * implement rotateMap() => the admin plugin !mapcycle command now works
#   * the admin plugin !map command is now able to provide suggestions if map name is incorrect
# 2012-09-19 - 1.3 Courgette
#   * fix issue #88 (https://github.com/courgette/big-brother-bot/issues/88) regarding clan name appearing in some of
#     the game log lines in place of the player team.
# 2012-10-08 - 1.4 Courgette
#   * better detection of EVT_SERVER_REQUIRES_RESTART
#   * now detect client action Begin_Bomb_Defuse_With_Kit
#   * fix #90 - check that SourceMod is installed at startup
# 2012-10-19 - 1.4.1 Courgette
#   * fix ban that was queuing a EVT_CLIENT_BAN_TEMP event instead of EVT_CLIENT_BAN
#
#
import re
import time
from b3.clients import Client, Clients
from b3.functions import minutesStr, time2minutes, getStuffSoundingLike
from b3.parser import Parser
from b3 import TEAM_UNKNOWN, TEAM_BLUE, TEAM_SPEC, TEAM_RED
from b3.game_event_router import Game_event_router
from b3.parsers.source.rcon import Rcon

__author__  = 'Courgette'
__version__ = '1.4.1'


"""
GAME SETUP
==========

In order to have a consistent name for the game log file, you need to start the game server with '-condebug' as a
command line parameter. The game server log file can then be found in the csgo folder under the name 'console.log'.

You must have SourceMod installed on the game server. See http://www.sourcemod.net/

Make sure to avoid conflict with in-game commands between B3 and SourceMod by choosing different command prefixes.
See PublicChatTrigger and SilentChatTrigger in addons/sourcemod/configs/core.cfg


SourceMod recommended plugins
-----------------------------

### B3 Say
If you have the SourceMod plugin B3 Say installed (http://forum.bigbrotherbot.net/counter-strike-global-offensive/sourcemod-plugins-for-b3/)
then the messages sent by B3 will better displayed on screen.

### SuperLogs:CS:S
If you have the SourceMod plugin SuperLogs:CS:S installed (http://forums.alliedmods.net/showthread.php?p=897271) then
kill stats will be more accurate.


"""


"""
TODO
====

# from https://developer.valvesoftware.com/wiki/HL_Log_Standard

- find out if a player can rename himself in-game, and if yes, what kind of event we have in the game log : "Name<uid><wonid><team>" changed name to "Name"
- find out if we can have injury game log line : "Name<uid><wonid><team>" attacked "Name<uid><wonid><team>" with "weapon" (damage "damage")
- find out if we can have Player-Player Actions : "Name<uid><wonid><team>" triggered "action" against "Name<uid><wonid><team>"





"""

# disable the authorizing timer that come by default with the b3.clients.Clients class
Clients.authorizeClients = lambda *args, **kwargs: None

# Regular expression recognizing a HalfLife game engine log line as described at https://developer.valvesoftware.com/wiki/HL_Log_Standard
RE_HL_LOG_LINE = r'''^L [01]\d/[0-3]\d/\d+ - [0-2]\d:[0-5]\d:[0-5]\d:\s*(?P<data>.*)'''

# Regular expression able to extract properties from HalfLife game engine log line as described at
# https://developer.valvesoftware.com/wiki/HL_Log_Standard#Notes
RE_HL_LOG_PROPERTY = re.compile('''\((?P<key>[^\s\(\)]+)(?P<data>| "(?P<value>[^"]*)")\)''')

# Regular expression to parse cvar queries responses
RE_CVAR = re.compile(r'''^"(?P<cvar>\S+?)" = "(?P<value>.*?)" \( def. "(?P<default>.*?)".*$''', re.MULTILINE)


ger = Game_event_router()

class CsgoParser(Parser):
    """
    The 'Counter-Strike: Global Offensive' B3 parser class
    """
    gameName = "csgo"
    privateMsg = True
    OutputClass = Rcon
    PunkBuster = None

    # extract the time from game log line
    _lineTime  = re.compile(r"""^L [01]\d/[0-3]\d/\d+ - [0-2]\d:(?P<minutes>[0-5]\d):(?P<seconds>[0-5]\d):\s*""")


    # game engine does not support color code, so we need this property
    # in order to get stripColors working
    _reColor = re.compile(r'(\^[0-9])')


    _settings = {'line_length': 200,
                 'min_wrap_length': 200}


    ###############################################################################################
    #
    #    B3 parser initialisation steps
    #
    ###############################################################################################

    def startup(self):

        if not self.is_sourcemod_installed():
            self.critical("You need to have SourceMod installed on your game server")
            raise SystemExit(220)

        # add game specific events
        self.createEvent("EVT_SUPERLOGS_WEAPONSTATS", "SourceMod SuperLogs weaponstats")
        self.createEvent("EVT_SUPERLOGS_WEAPONSTATS2", "SourceMod SuperLogs weaponstats2")
        self.createEvent("EVT_SERVER_REQUIRES_RESTART", "Source server requires restart")

        # create the 'Server' client
        # todo self.clients.newClient('Server', guid='Server', name='Server', hide=True, pbid='Server', team=b3.TEAM_UNKNOWN)

        self.game.cvar = {}
        self.queryServerInfo()

        # load SM plugins list
        self.sm_plugins = self.get_loaded_sm_plugins()

        # keeps the last properties from a killlocation game event
        self.last_killlocation_properties = None


    def pluginsStarted(self):
        """
        Called once all plugins were started.
        Handy if some of them must be monkey-patched.
        """
        pass



    ###############################################################################################
    #
    #    Game events handlers
    #
    #    Read HL Log Standard documentation at https://developer.valvesoftware.com/wiki/HL_Log_Standard
    #
    ###############################################################################################

    @ger.gameEvent(
        r'''^//''', # comment log line
        r'''^server cvars start''',
        r'''^server cvars end''',
        r'''^\[basechat\.smx\] .*''',
        r'''^\[META\] Loaded \d+ plugins \(\d+ already loaded\)$''',
        r'''^Log file closed.$''',
        r'''^\[META\] Loaded \d+ plugin.$''',
    )
    def ignored_line(self):
        # L 09/24/2001 - 18:44:50: // This is a comment in the log file. It should not be parsed.
        # L 08/26/2012 - 05:29:47: server cvars start
        # L 08/26/2012 - 05:29:47: server cvars end
        # L 08/27/2012 - 23:57:45: [basechat.smx] "Console<0><Console><Console>" triggered sm_say (text "courgette put in group User")
        # L 08/30/2012 - 00:43:10: Log file closed.
        # L 08/30/2012 - 00:45:42: [META] Loaded 1 plugin.
        pass


    @ger.gameEvent(r'''"(?P<a_name>.+)<(?P<a_cid>\d+)><(?P<a_guid>.+)><(?P<a_team>.*)>" killed "(?P<v_name>.+)<(?P<v_cid>\d+)><(?P<v_guid>.+)><(?P<v_team>.*)>" with "(?P<weapon>\S*)"(?P<properties>.*)$''')
    def on_kill(self, a_name, a_cid, a_guid, a_team, v_name, v_cid, v_guid, v_team, weapon, properties):
        # L 08/26/2012 - 03:46:44: "Pheonix<22><BOT><TERRORIST>" killed "Ringo<17><BOT><CT>" with "glock" (headshot)
        # L 08/26/2012 - 03:46:46: "Shark<19><BOT><CT>" killed "Pheonix<22><BOT><TERRORIST>" with "hkp2000"
        # L 08/26/2012 - 03:47:40: "Stone<18><BOT><TERRORIST>" killed "Steel<13><BOT><CT>" with "glock"
        # L 08/26/2012 - 05:08:56: "Kurt<76><BOT><TERRORIST>" killed "courgette<2><STEAM_1:0:1487018><CT>" with "galilar"'
        attacker = self.getClientOrCreate(a_cid, a_guid, a_name, a_team)
        victim = self.getClientOrCreate(v_cid, v_guid, v_name, v_team)
        # victim.state = b3.STATE_DEAD ## do we need that ? is this info used ?

        props = self.parseProperties(properties)
        headshot = props.get('headshot', False)

        event_type = "EVT_CLIENT_KILL"
        if attacker.cid == victim.cid:
            event_type = "EVT_CLIENT_SUICIDE"
        elif attacker.team in (TEAM_BLUE, TEAM_RED) and attacker.team == victim.team:
            event_type = "EVT_CLIENT_KILL_TEAM"

        damage_pct = 100
        damage_type = None
        hit_location = "head" if headshot else "body"
        data = [damage_pct, weapon, hit_location, damage_type]

        if self.last_killlocation_properties:
            data.append(self.parseProperties(self.last_killlocation_properties))
            self.last_killlocation_properties = None

        return self.getEvent(event_type, client=attacker, target=victim, data=tuple(data))


    @ger.gameEvent(r'''^"(?P<name>.+)<(?P<cid>\d+)><(?P<guid>.+)><(?P<team>.*)>" committed suicide with "(?P<weapon>\S*)"$''')
    def on_suicide(self, name, cid, guid, team, weapon):
        # L 08/26/2012 - 03:38:04: "Pheonix<22><BOT><TERRORIST>" committed suicide with "world"
        client = self.getClientOrCreate(cid, guid, name, team)
        # victim.state = b3.STATE_DEAD ## do we need that ? is this info used ?
        damage_pct = 100
        damage_type = None
        return self.getEvent("EVT_CLIENT_SUICIDE", client=client, target=client, data=(damage_pct, weapon, "body", damage_type))


    @ger.gameEvent(
        r'''^"(?P<cvar_name>\S+)" = "(?P<cvar_value>\S*)"$''',
        r'''^server_cvar: "(?P<cvar_name>\S+)" "(?P<cvar_value>\S*)"$'''
    )
    def on_cvar(self, cvar_name, cvar_value):
        # L 08/26/2012 - 03:49:56: "r_JeepViewZHeight" = "10.0"
        # L 08/26/2012 - 03:49:56: "tv_password" = ""
        # L 08/26/2012 - 03:49:56: "sv_specspeed" = "3"
        self.game.cvar[cvar_name] = cvar_value


    @ger.gameEvent(r'''^-------- Mapchange to (?P<new_map>\S+) --------$''')
    def on_map_change(self, new_map):
        # L 08/27/2012 - 23:57:14: -------- Mapchange to de_dust --------
        self.game.mapName = new_map


    @ger.gameEvent(r'''^Loading map "(?P<new_map>\S+)"$''')
    def on_started_map(self, new_map):
        # L 08/26/2012 - 03:49:56: Loading map "de_nuke"
        self.game.mapName = new_map


    @ger.gameEvent(r'''^Started map "(?P<new_map>\S+)" \(CRC "-?\d+"\)$''')
    def on_started_map(self, new_map):
        # L 08/26/2012 - 03:22:35: Started map "de_dust" (CRC "1592693790")
        # L 08/26/2012 - 03:49:58: Started map "de_nuke" (CRC "-568155013")
        self.game.mapName = new_map
        self.game.startMap()


    @ger.gameEvent(r'''^"(?P<name>.+)<(?P<cid>\d+)><(?P<guid>\S*)><(?P<team>\S*)>" STEAM USERID validated$''')
    def on_userid_validated(self, name, cid, guid, team):
        # L 08/26/2012 - 03:22:36: "courgette<2><STEAM_1:0:1111111><>" STEAM USERID validated
        self.getClientOrCreate(cid, guid, name, team)


    @ger.gameEvent(r'''^"(?P<name>.+)<(?P<cid>\d+)><(?P<guid>.+)><(?P<team>.*)>" connected, address "(?P<ip>.+)"$''')
    def on_client_connected(self, name, cid, guid, team, ip):
        # L 08/26/2012 - 03:22:36: "courgette<2><STEAM_1:0:1111111><>" connected, address "11.222.111.222:27005"
        # L 08/26/2012 - 03:22:36: "Moe<3><BOT><>" connected, address "none"
        client = self.getClientOrCreate(cid, guid, name, team)
        client.ip = ip if ip != "none" else ""


    @ger.gameEvent(r'''^"(?P<name>.+)<(?P<cid>\d+)><(?P<guid>.+)><(?P<team>.*)>" disconnected \(reason "(?P<reason>.*)"\)$''')
    def on_client_disconnected(self, name, cid, guid, team, reason):
        # L 08/26/2012 - 04:45:04: "Kyle<63><BOT><CT>" disconnected (reason "Kicked by Console")
        client = self.getClient(cid)
        event = None
        if client:
            if reason == "Kicked by Console":
                event = self.getEvent("EVT_CLIENT_KICK", client=client, data=reason)
            client.disconnect()
        if event:
            return event


    @ger.gameEvent(r'''^"(?P<name>.+)<(?P<cid>\d+)><(?P<guid>.+)><(?P<team>.*)>" entered the game$''')
    def on_client_entered(self, name, cid, guid, team):
        # L 08/26/2012 - 05:29:48: "Rip<93><BOT><>" entered the game
        # L 08/26/2012 - 05:38:36: "GrUmPY<105><STEAM_1:0:22222222><>" entered the game
        # L 08/26/2012 - 05:43:29: "Ein 1337er M!L[H<106><STEAM_1:0:5555555><>" entered the game
        client = self.getClientOrCreate(cid, guid, name, team)
        return self.getEvent("EVT_CLIENT_JOIN", client=client)


    @ger.gameEvent(r'''^"(?P<name>.+)<(?P<cid>\d+)><(?P<guid>.+)><(?P<old_team>\S+)>" joined team "(?P<new_team>\S+)"$''')
    def on_client_join_team(self, name, cid, guid, old_team, new_team):
        # L 08/26/2012 - 03:22:36: "Pheonix<11><BOT><Unassigned>" joined team "TERRORIST"
        # L 08/26/2012 - 03:22:36: "Wolf<12><BOT><Unassigned>" joined team "CT"
        client = self.getClientOrCreate(cid, guid, name, old_team)
        client.team = self.getTeam(new_team)


    @ger.gameEvent(r'''^World triggered "(?P<event_name>\S*)"(?P<properties>.*)$''')
    def on_world_action(self, event_name, properties):
        # L 08/26/2012 - 03:22:36: World triggered "Round_Start"
        # L 08/26/2012 - 03:22:36: World triggered "Game_Commencing"
        # L 08/26/2012 - 03:22:36: World triggered "Round_End"
        # L 08/29/2012 - 22:26:59: World triggered "killlocation" (attacker_position "-282 749 -21") (victim_position "68 528 64")
        if event_name == "Round_Start":
            self.game.startRound()
        elif event_name == "Round_End":
            return self.getEvent("EVT_GAME_ROUND_END")
        elif event_name in ("Game_Commencing"):
            pass
        elif event_name == "killlocation":
            # killlocation log lines are generated by the SourceMod SuperLogs plugin right before a kill event
            # save the properties for the next kill event to use
            self.last_killlocation_properties = properties
        else:
            self.warning("unexpected world event : '%s'. Please report this on the B3 forums" % event_name)


    @ger.gameEvent(r'''^"(?P<name>.+)<(?P<cid>\d+)><(?P<guid>.+)><(?P<team>.*)>" triggered "(?P<event_name>\S+)"(?P<properties>.*)$''')
    def on_player_action(self, name, cid, guid, team, event_name, properties):
        client = self.getClientOrCreate(cid, guid, name, team)
        props = self.parseProperties(properties)
        if event_name in ("Got_The_Bomb", "Dropped_The_Bomb", "Planted_The_Bomb", "Begin_Bomb_Defuse_Without_Kit",
                          "Begin_Bomb_Defuse_With_Kit", "Defused_The_Bomb", "headshot", "round_mvp"):
            # L 08/26/2012 - 03:22:37: "Pheonix<11><BOT><TERRORIST>" triggered "Got_The_Bomb"
            # L 08/26/2012 - 03:46:46: "Pheonix<22><BOT><TERRORIST>" triggered "Dropped_The_Bomb"
            # L 08/26/2012 - 03:51:41: "Gunner<29><BOT><CT>" triggered "Begin_Bomb_Defuse_Without_Kit"
            # L 09/25/2012 - 22:14:09: "Grant<24><BOT><CT>" triggered "Begin_Bomb_Defuse_With_Kit"
            # L 08/26/2012 - 05:04:55: "Steel<80><BOT><TERRORIST>" triggered "Planted_The_Bomb"
            # L 08/29/2012 - 22:27:01: "Zach<5><BOT><CT>" triggered "headshot"
            # L 08/29/2012 - 22:31:50: "Pheonix<4><BOT><TERRORIST>" triggered "round_mvp"
            return self.getEvent("EVT_CLIENT_ACTION", client=client, data=event_name)

        elif event_name == "clantag":
            # L 08/26/2012 - 05:43:31: "Ein 1337er M!L[H<106><STEAM_1:0:5280197><Unassigned>" triggered "clantag" (value "")
            # L 09/18/2012 - 18:26:21: "Spoon<3><STEAM_1:0:11111111><EHD Gaming>" triggered "clantag" (value "EHD")
            client.clantag = props.get("value", "")

        elif event_name == "weaponstats":
            # L 08/28/2012 - 14:58:55: "Gunner<48><BOT><CT>" triggered "weaponstats" (weapon "m4a1") (shots "13") (hits "2") (kills "0") (headshots "0") (tks "0") (damage "42") (deaths "0")
            return self.getEvent("EVT_SUPERLOGS_WEAPONSTATS", client=client, data=props)

        elif event_name == "weaponstats2":
            # L 08/28/2012 - 14:58:55: "Vitaliy<51><BOT><CT>" triggered "weaponstats2" (weapon "famas") (head "0") (chest "0") (stomach "1") (leftarm "0") (rightarm "0") (leftleg "0") (rightleg "0")
            return self.getEvent("EVT_SUPERLOGS_WEAPONSTATS2", client=client, data=props)

        else:
            self.warning("unknown client event : '%s'. Please report this on the B3 forums" % event_name)


    @ger.gameEvent(r'''^Team "(?P<team>\S+)" triggered "(?P<event_name>[^"]+)"(?P<properties>.*)$''')
    def on_team_action(self, team, event_name, properties):
        # L 08/26/2012 - 03:48:09: Team "CT" triggered "SFUI_Notice_Target_Saved" (CT "3") (T "5")
        # L 08/26/2012 - 03:51:50: Team "TERRORIST" triggered "SFUI_Notice_Target_Bombed" (CT "1") (T "1")
        if event_name in ("SFUI_Notice_Target_Saved", "SFUI_Notice_Target_Bombed", "SFUI_Notice_Terrorists_Win",
            "SFUI_Notice_CTs_Win", "SFUI_Notice_Bomb_Defused"):
            pass # TODO should we do anything with that info ?
        else:
            self.warning("unexpected team event : '%s'. Please report this on the B3 forums" % event_name)


    @ger.gameEvent(r'''^Team "(?P<team>\S+)" scored "(?P<points>\d+)" with "(?P<num_players>\d+)" players$''')
    def on_team_score(self, team, points, num_players):
        # L 08/26/2012 - 03:48:09: Team "CT" scored "3" with "5" players
        # L 08/26/2012 - 03:48:09: Team "TERRORIST" scored "5" with "5" players
        pass # TODO should we do anything with that info ?


    @ger.gameEvent(r'''^"(?P<name>.+)<(?P<cid>\d+)><(?P<guid>.+)><(?P<team>.*?)>" say "(?P<text>.*)"$''')
    def on_client_say(self, name, cid, guid, team, text):
        # L 08/26/2012 - 05:09:55: "courgette<2><STEAM_1:0:1487018><CT>" say "!iamgod"
        # L 09/16/2012 - 04:55:17: "Spoon<2><STEAM_1:0:11111111><>" say "!h"
        client = self.getClientOrCreate(cid, guid, name, team)
        return self.getEvent("EVT_CLIENT_SAY", client=client, data=text)


    @ger.gameEvent(r'''^"(?P<name>.+)<(?P<cid>\d+)><(?P<guid>.+)><(?P<team>.*?)>" say_team "(?P<text>.*)"$''')
    def on_client_teamsay(self, name, cid, guid, team, text):
        # L 08/26/2012 - 05:04:44: "courgette<2><STEAM_1:0:1487018><CT>" say_team "team say"
        client = self.getClientOrCreate(cid, guid, name, team)
        return self.getEvent("EVT_CLIENT_TEAM_SAY", client=client, data=text)


    @ger.gameEvent(r'''^rcon from "(?P<ip>.+):(?P<port>\d+)":\sBad Password$''')
    def on_bad_rcon_password(self, ip, port):
        # L 08/26/2012 - 05:21:23: rcon from "78.207.134.100:15073": Bad Password
        self.error("Bad RCON password, check your b3.xml file")


    @ger.gameEvent(r'''^Molotov projectile spawned at (?P<coord>-?[\d.]+ -?[\d.]+ -?[\d.]+), velocity (?P<velocity>-?[\d.]+ -?[\d.]+ -?[\d.]+)$''')
    def on_molotov_spawed(self, coord, velocity):
        # L 08/26/2012 - 05:21:24: Molotov projectile spawned at 132.012238 -2071.752197 -347.858246, velocity 487.665253 106.295044 121.257591
        pass # Do we care ?


    @ger.gameEvent(r'''^rcon from "(?P<ip>.+):(?P<port>\d+)": command "(?P<cmd>.*)"$''')
    def on_rcon(self, ip, port, cmd):
        # L 08/26/2012 - 05:37:56: rcon from "11.222.111.122:15349": command "say test"
        pass


    @ger.gameEvent(r'''^Banid: "(?P<name>.+)<(?P<cid>\d+)><(?P<guid>.+)><(?P<team>.*)>" was banned "for (?P<duration>.+)" by "(?P<admin>.*)"$''')
    def on_banid(self, name, cid, guid, team, duration, admin):
        # L 08/28/2012 - 00:03:01: Banid: "courgette<91><STEAM_1:0:1111111><>" was banned "for 1.00 minutes" by "Console"
        client = self.storage.getClient(Client(guid=guid))
        if client:
            return self.getEvent("EVT_CLIENT_BAN_TEMP", {"duration": duration, "admin": admin, 'reason': None}, client)


    @ger.gameEvent(r'''^\[basecommands.smx\] ".+<\d+><.+><.*>" kicked "(?P<name>.+)<(?P<cid>\d+)><(?P<guid>.+)><(?P<team>.*)>"(?P<properties>.*)$''')
    def on_kicked(self, name, cid, guid, team, properties):
        # L 08/28/2012 - 00:12:07: [basecommands.smx] "Console<0><Console><Console>" kicked "courgette<91><STEAM_1:0:1111111><>" (reason "f00")
        client = self.storage.getClient(Client(guid=guid))
        if client:
            p = self.parseProperties(properties)
            return self.getEvent("EVT_CLIENT_KICK", p.get('reason', ''), client)


    @ger.gameEvent(r'''^server_message: "(?P<msg>.*)"(?P<properties>.*)$''')
    def on_server_message(self, msg, properties):
        # L 08/30/2012 - 00:43:10: server_message: "quit"
        # L 08/30/2012 - 00:43:10: server_message: "restart"
        if msg in ("quit", "restart"):
            pass
        else:
            self.warning("unexpected server_message : '%s'. Please report this on the B3 forums" % msg)


    @ger.gameEvent(r'''^Log file started (?P<properties>.*)$''')
    def on_server_message(self, properties):
        # Log file started (file "logs/L000_000_000_000_0_201208300045_000.log") (game "/home/steam/steamcmd/cs_go/csgo") (version "5038")
        pass


    @ger.gameEvent(
        r'''^(?P<data>Your server needs to be restarted.*)$''',
        r'''^(?P<data>Your server is out of date.*)$'''
    )
    def on_server_restart_request(self, data):
        # L 09/17/2012 - 23:26:45: Your server needs to be restarted in order to receive the latest update.
        # L 09/17/2012 - 23:26:45: Your server is out of date.  Please update and restart.
        return self.getEvent('EVT_SERVER_REQUIRES_RESTART', data)


    # -------------- /!\  this one must be the last /!\ --------------
    @ger.gameEvent(r'''^(?P<data>.+)$''')
    def on_unknown_line(self, data):
        """
        catch all lines that were not handled
        """
        self.warning("unhandled log line : %s. Please report this on the B3 forums" % data)




    ###############################################################################################
    #
    #    B3 Parser interface implementation
    #
    ###############################################################################################

    def getPlayerList(self):
        """\
        Query the game server for connected players.
        return a dict having players' id for keys and players' data as another dict for values
        """
        return self.queryServerInfo()


    def authorizeClients(self):
        """\
        For all connected players, fill the client object with properties allowing to find
        the user in the database (usualy guid, or punkbuster id, ip) and call the
        Client.auth() method
        """
        pass # no need as all game log lines have the client guid


    def sync(self):
        """\
        For all connected players returned by self.getPlayerList(), get the matching Client
        object from self.clients (with self.clients.getByCID(cid) or similar methods) and
        look for inconsistencies. If required call the client.disconnect() method to remove
        a client from self.clients.
        This is mainly useful for games where clients are identified by the slot number they
        occupy. On map change, a player A on slot 1 can leave making room for player B who
        connects on slot 1.
        """
        plist = self.getPlayerList()
        mlist = {}
        for cid, c in plist.iteritems():
            client = self.clients.getByCID(cid)
            if client:
                mlist[cid] = client
        return mlist


    def say(self, msg):
        """\
        broadcast a message to all players
        """
        if msg and len(msg.strip()):
            template = 'sm_say %s'
            if "B3 Say" in self.sm_plugins:
                template = 'b3_say %s'
            else:
                msg = self.msgPrefix + ' ' + msg
            for line in self.getWrap(msg, self._settings['line_length'], self._settings['min_wrap_length']):
                self.output.write(template % line)


    def saybig(self, msg):
        """\
        broadcast a message to all players in a way that will catch their attention.
        """
        if msg and len(msg.strip()):
            template = 'sm_hsay %s'
            if "B3 Say" in self.sm_plugins:
                template = 'b3_hsay %s'
            else:
                msg = self.msgPrefix + ' ' + msg
            for line in self.getWrap(msg, self._settings['line_length'], self._settings['min_wrap_length']):
                self.output.write(template % line)


    def message(self, client, msg):
        """\
        display a message to a given player
        """
        if not client.hide: # do not talk to bots
            if msg and len(msg.strip()):
                template = 'sm_psay #%(guid)s "%(msg)s"'
                if "B3 Say" in self.sm_plugins:
                    template = 'b3_psay #%(guid)s "%(msg)s"'
                else:
                    msg = self.msgPrefix + ' ' + msg
                for line in self.getWrap(msg, self._settings['line_length'], self._settings['min_wrap_length']):
                    self.output.write(template % {'guid': client.guid, 'msg': line})


    def kick(self, client, reason='', admin=None, silent=False, *kwargs):
        """\
        kick a given player
        """

        self.debug('kick reason: [%s]' % reason)
        if isinstance(client, basestring):
            clients = self.clients.getByMagic(client)
            if len(clients) != 1:
                return
            else:
                client = client[0]

        if admin:
            fullreason = self.getMessage('kicked_by', self.getMessageVariables(client=client, reason=reason, admin=admin))
        else:
            fullreason = self.getMessage('kicked', self.getMessageVariables(client=client, reason=reason))
        fullreason = self.stripColors(fullreason)
        reason = self.stripColors(reason)

        self.do_kick(client, reason)

        if not silent and fullreason != '':
            self.say(fullreason)


    def ban(self, client, reason='', admin=None, silent=False, *kwargs):
        """\
        ban a given player on the game server and in case of success
        fire the event ('EVT_CLIENT_BAN', data={'reason': reason,
        'admin': admin}, client=target)
        """
        if client.hide: # exclude bots
            return

        self.debug('BAN : client: %s, reason: %s', client, reason)
        if isinstance(client, basestring):
            clients = self.clients.getByMagic(client)
            if len(clients) != 1:
                return
            else:
                client = client[0]

        if admin:
            fullreason = self.getMessage('banned_by', self.getMessageVariables(client=client, reason=reason, admin=admin))
        else:
            fullreason = self.getMessage('banned', self.getMessageVariables(client=client, reason=reason))
        fullreason = self.stripColors(fullreason)
        reason = self.stripColors(reason)

        self.do_ban(client, reason)
        if admin:
            admin.message('banned: %s (@%s) has been added to banlist' % (client.exactName, client.id))

        if not silent and fullreason != '':
            self.say(fullreason)

        self.queueEvent(self.getEvent("EVT_CLIENT_BAN", {'reason': reason, 'admin': admin}, client))


    def unban(self, client, reason='', admin=None, silent=False, *kwargs):
        """\
        unban a given player on the game server
        """
        if client.hide: # exclude bots
            return

        self.debug('UNBAN: Name: %s, Ip: %s, Guid: %s' % (client.name, client.ip, client.guid))
        if client.ip:
            self.do_unban_by_ip(client)
            self.verbose('UNBAN: Removed ip (%s) from banlist' % client.ip)
            if admin:
                admin.message('Unbanned: %s. His last ip (%s) has been removed from banlist.' % (client.exactName, client.ip))
            if admin:
                fullreason = self.getMessage('unbanned_by', self.getMessageVariables(client=client, reason=reason, admin=admin))
            else:
                fullreason = self.getMessage('unbanned', self.getMessageVariables(client=client, reason=reason))
            if not silent and fullreason != '':
                self.say(fullreason)

        self.do_unban_by_steamid(client)
        self.verbose('UNBAN: Removed guid (%s) from banlist' %client.guid)
        if admin:
            admin.message('Unbanned: Removed %s guid from banlist' % client.exactName)


    def tempban(self, client, reason='', duration=2, admin=None, silent=False, *kwargs):
        """\
        tempban a given player on the game server and in case of success
        fire the event ('EVT_CLIENT_BAN_TEMP', data={'reason': reason,
        'duration': duration, 'admin': admin}, client=target)
        """
        if client.hide: # exclude bots
            return

        self.debug('TEMPBAN : client: %s, duration: %s, reason: %s', client, duration, reason)
        if isinstance(client, basestring):
            clients = self.clients.getByMagic(client)
            if len(clients) != 1:
                return
            else:
                client = client[0]

        if admin:
            fullreason = self.getMessage('temp_banned_by', self.getMessageVariables(client=client, reason=reason, admin=admin, banduration=minutesStr(duration)))
        else:
            fullreason = self.getMessage('temp_banned', self.getMessageVariables(client=client, reason=reason, banduration=minutesStr(duration)))
        fullreason = self.stripColors(fullreason)
        reason = self.stripColors(reason)

        self.do_tempban(client, duration, reason)

        if not silent and fullreason != '':
            self.say(fullreason)

        self.queueEvent(self.getEvent("EVT_CLIENT_BAN_TEMP", {'reason': reason, 'duration': duration, 'admin': admin}, client))


    def getMap(self):
        """\
        return the current map/level name
        """
        self.queryServerInfo()
        return self.game.mapName


    def getMaps(self):
        """\
        return the available maps/levels name
        """
        rv = self.output.write('listmaps')
        if rv:
            return [x for x in rv.split('\n') if x and x != "Map Cycle:" and not x.startswith('L ')]


    def rotateMap(self):
        """\
        load the next map/level
        """
        next_map = self.getNextMap()
        if next_map:
            self.saybig('Changing to next map : %s' % next_map)
            time.sleep(1)
            self.output.write('map %s' % next_map)



    def changeMap(self, map_name):
        """\
        load a given map/level
        return a list of suggested map names in cases it fails to recognize the map that was provided
        """
        rv = self.getMapsSoundingLike(map_name)
        if isinstance(rv, basestring):
            self.output.write('sm_map %s' % map_name)
        else:
            return rv


    def getPlayerPings(self):
        """\
        returns a dict having players' id for keys and players' ping for values
        """
        clients = self.queryServerInfo()
        pings = {}
        for cid, client in clients.iteritems():
            pings[cid] = client.ping
        return pings


    def getPlayerScores(self):
        """\
        returns a dict having players' id for keys and players' scores for values
        """
        # TODO getPlayerScores if doable
        return {}


    def inflictCustomPenalty(self, type, client, reason=None, duration=None, admin=None, data=None):
        """
        Called if b3.admin.penalizeClient() does not know a given penalty type.
        Overwrite this to add customized penalties for your game like 'slap', 'nuke',
        'mute', 'kill' or anything you want.
        /!\ This method must return True if the penalty was inflicted.
        """
        pass
        # TODO inflictCustomPenalty (sm_slap sm_slay sm_votekick sm_voteban sm_voteburn sm_voteslay sm_gag sm_mute sm_silence)


    def getNextMap(self):
        """
        return the next map in the map rotation list
        """
        next_map = self.getCvar("sm_nextmap")
        return next_map


    ###############################################################################################
    #
    #    Other methods
    #
    ###############################################################################################

    def getWrap(self, text, length=80, minWrapLen=150):
        """Returns a sequence of lines for text that fits within the limits"""
        if not text:
            return []

        length = int(length)
        clean_text = self.stripColors(text.strip())


        if len(clean_text) <= minWrapLen:
            return [clean_text]

        text = re.split(r'\s+', clean_text)

        lines = []

        line = text[0]
        for t in text[1:]:
            if len(line) + len(t) + 2 <= length:
                line = '%s %s' % (line, t)
            else:
                if len(lines) > 0:
                    lines.append(u'› %s' % line)
                else:
                    lines.append(line)
                line = t

        if len(line):
            if len(lines) > 0:
                lines.append(u'› %s' % line)
            else:
                lines.append(line)

        return lines


    def parseLine(self, line):
        if line is None:
            return
        if line.startswith("mp\x08 \x08\x08 \x08"):
            line = line[8:]
        m = re.match(RE_HL_LOG_LINE, line.decode('UTF-8', 'replace'))
        if m:
            data = m.group('data')
            if data:
                hfunc, param_dict = ger.getHandler(data)
                if hfunc:
                    self.verbose2("calling %s%r" % (hfunc.func_name, param_dict))
                    event = hfunc(self, **param_dict)
                    if event:
                        self.queueEvent(event)


    def parseProperties(self, properties):
        """
        parse HL log properties as described at https://developer.valvesoftware.com/wiki/HL_Log_Standard#Notes
        :param properties: string representing HL log properties
        :return: a dict representing all the property key:value parsed
        """
        rv = {}
        if properties:
            for match in re.finditer(RE_HL_LOG_PROPERTY, properties):
                if match.group('data') == '':
                    rv[match.group('key')] = True # Parenthised properties with no explicit value indicate a boolean true value
                else:
                    rv[match.group('key')] = match.group('value')
        return rv


    def getClient(self, cid):
        """
        return an already connected client by searching the clients cid index.

        May return None
        """
        client = self.clients.getByCID(cid)
        if client:
            return client
        return None


    def getClientOrCreate(self, cid, guid, name, team=None):
        """
        return an already connected client by searching the clients cid index
        or create a new client.
        
        May return None
        """
        if guid == "BOT":
            guid += "_" + cid
        client = self.clients.getByCID(cid)
        if client is None:
            client = self.clients.newClient(cid, guid=guid, name=name, team=TEAM_UNKNOWN)
            client.last_update_time = time.time()
            if guid.startswith("BOT_"):
                client.hide = True
        else:
            if name:
                client.name = name
        if team:
            parsed_team = self.getTeam(team)
            if parsed_team and parsed_team != TEAM_UNKNOWN:
                client.team = parsed_team
        return client


    def getTeam(self, team):
        """
        convert team CS:GO id to B3 team numbers
        """
        if not team or team == "Unassigned":
            return TEAM_UNKNOWN
        elif team == "TERRORIST":
            return TEAM_BLUE
        elif team == "CT":
            return TEAM_RED
#        elif team = "???": # TODO find out what the spec team is
#            return TEAM_SPEC
        else:
            self.debug("unexpected team id : %s" % team)
            return TEAM_UNKNOWN


    def queryServerInfo(self):
        """
        query the server for its status and refresh local data :
         self.game.sv_hostname
         self.game.mapName
        furthermore, discover connected players, refresh their ping and ip info
        finally return a dict of <cid, client>
        """
        rv = self.output.write("status")
        clients = {}
        if rv:
            re_player = re.compile(r'''^#\s*(?P<cid>\d+) (?:\d+) "(?P<name>.+)" (?P<guid>\S+) (?P<duration>\d+:\d+) (?P<ping>\d+) (?P<loss>\S+) (?P<state>\S+) (?P<rate>\d+) (?P<ip>\d+\.\d+\.\d+\.\d+):(?P<port>\d+)$''')
            for line in rv.split('\n'):
                if not line or line.startswith('L '):
                    continue
                if line.startswith('hostname:'):
                    self.game.sv_hostname = line[10:]
                elif line.startswith('map     :'):
                    self.game.mapName = line[10:]
                else:
                    m = re.match(re_player, line)
                    if m:
                        client = self.getClientOrCreate(m.group('cid'), m.group('guid'), m.group('name'))
                        client.ping = m.group('ping')
                        client.ip = m.group('ip')
                        clients[client.cid] = client
            return clients


    def getAvailableMaps(self):
        """
        return the available maps on the server, even if not in the map rotation list
        """
        re_maps = re.compile(r"^PENDING:\s+\(fs\)\s+(?P<map_name>.+)\.bsp$")
        response = []
        for line in self.output.write("maps *").split('\n'):
            m = re.match(re_maps, line)
            if m:
                response.append(m.group('map_name'))
        return response


    def getCvar(self, cvar_name):
        if not cvar_name:
            self.warning('trying to query empty cvar %r' % cvar_name)
            return None
        rv = self.output.write(cvar_name)
        m = re.search(RE_CVAR, rv)
        if m:
            return m.group('value')


    def setCvar(self, cvarName, value):
        """
        set a cvar on the game server
        """
        if re.match('^[a-z0-9_.]+$', cvarName, re.I):
            self.debug('Set cvar %s = [%s]', cvarName, value)
            self.write(self.getCommand('set', name=cvarName, value=value))
        else:
            self.error('%s is not a valid cvar name', cvarName)


    def do_kick(self, client, reason=None):
        if not client.cid:
            self.warning("Trying to kick %s which has no slot id" % client)
        else:
            if reason:
                self.output.write('sm_kick #%s %s' % (client.cid, reason))
            else:
                self.output.write("sm_kick #%s" % client.cid)


    def do_ban(self, client, reason=None):
        # sm_addban <time> <steamid> [reason]
        if reason:
            self.output.write('sm_addban %s "%s" %s' % (0, client.guid, reason))
        else:
            self.output.write('sm_addban %s "%s"' % (0, client.guid))
        self.do_kick(client, reason)


    def do_tempban(self, client, duration=2, reason=None):
        # sm_addban <time> <steamid> [reason]
        if reason:
            self.output.write('sm_addban %s "%s" %s' % (int(time2minutes(duration)), client.guid, reason))
        else:
            self.output.write('sm_addban %s "%s"' % (int(time2minutes(duration)), client.guid))
        self.do_kick(client, reason)


    def do_unban_by_steamid(self, client):
        # sm_unban <steamid|ip>
        self.output.write('sm_unban "%s"' % client.guid)


    def do_unban_by_ip(self, client):
        # sm_unban <steamid|ip>
        self.output.write('sm_unban %s' % client.ip)


    def is_sourcemod_installed(self):
        """
        return a True if Source Mod is installed on the game server
        """
        data = self.output.write("sm version")
        if data:
            if data.startswith("Unknown command"):
                return False
            for m in data.splitlines():
                self.info(m.strip())
            return True
        else:
            return False


    def get_loaded_sm_plugins(self):
        """
        return a dict with SourceMod plugins' name as keys and value is a tuple (index, version, author)
        """
        re_sm_plugin = re.compile(r'''^(?P<index>.+) "(?P<name>.+)" \((?P<version>.+)\) by (?P<author>.+)$''', re.MULTILINE)
        response = {}
        data = self.output.write("sm plugins list")
        if data:
            for m in re.finditer(re_sm_plugin, data):
                response[m.group('name')] = (m.group('index'), m.group('version'), m.group('author'))
        return response


    def getMapsSoundingLike(self, mapname):
        """ return a valid mapname.
        If no exact match is found, then return close candidates as a list
        """
        supportedMaps = [m.lower() for m in self.getAvailableMaps()]
        wanted_map = mapname.lower()
        if wanted_map in supportedMaps:
            return wanted_map

        matches = getStuffSoundingLike(wanted_map, supportedMaps)
        if len(matches) == 1:
            # one match, get the map id
            return matches[0]
        else:
            # multiple matches, provide suggestions
            return matches