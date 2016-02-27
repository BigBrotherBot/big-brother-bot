# coding=UTF-8
#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2014 Courgette <courgette@bigbrotherbot.net>
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
# 2014-04-01 - 0.1   - Courgette      - copied from csgo
# 2014-05-02 - 0.2   - Fenix          - rewrote import statements
#                                     - initialize missing class attributes
#                                     - fixed get_player_pings method declaration not matching the method in Parser class
#                                     - fixed client retrieval in kick, ban and tempban function
# 2014-07-16 - 0.3   - Fenix          - added admin key in EVT_CLIENT_KICK data dict when available
# 2014/07/18 - 0.4   - Fenix          - updated abstract parser to comply with the new get_wrap implementation
# 2014/08/29 - 0.5   - 82ndab.Bravo17 - remove color codes from all messages since Insurgency doesn't use them
# 2014/08/30 - 0.6   - Fenix          - syntax cleanup
#                                     - let getcvar() method make use of the Cvar class
# 2014/09/01 - 0.6.1 - 82ndab-Bravo17 - Add color code options for new getWrap method
# 2014/09/02 - 0.7   - 82ndab-Bravo17 - Changed getMaps to get the name and gametypes from the mapcycle file for !maps
#                                     - Get available maps now retrieves the map list from the GAME_MODES_FOR_MAP dict,
#                                       to which non-stock maps can be added in the xml as well as
#                                       the maps * command to provide crash resistant changing to map/gametype pairings
#                                     - Changed map so that it accepts gametype as a required argument, and won't try
#                                       and rotate to an invalid map/gametype combo unless the optional -force parameter
#                                       is used to override the check. Also adds _coop or _hunt to the mapname if it has
#                                       been omitted and is needed.
#                                     - Sourcemod nextmap plugin breaks the default in-game map-voting, which is superior
#                                       to the SM version, so disabled !nextmap unless sm nextmap is loaded
# 2014/10/12 - 0.7.1 - Fenix          - removed unused imports
#                                     - respect PEP8 line length constraints
#                                     - fixed changeMap method declaration so it respect Parser's method inheritence
#                                     - fixed suggestion list not being printed when !map command is not able to select
#                                       a valid mapname through getMapsSoundingLike
# 2014/12/11 - 0.7.2 - 82ndab-Bravo17 - Changed handling of coop and hunt map names to allow for non-standardized ones -
#                                     - eg mapname_coop_v2
#                                     - use suggested map name when only one suggestion is given on map change
#                                     - show map and gametype being changed to for 5 seconds before change
#                                     - don't show BOTs in !list for coop games
# 2014/12/17 - 0.7.3 - 82ndab-Bravo17 - Updated map/gametype list
# 2014/12/23 - 0.8.0 - 82ndab-Bravo17 - Removed map/gametype pair checking, since game no longer seems to lockup if
#                                       invalid.
#                                     - Remove auto adding of _hunt and _coop, since mapmakers are not sticking to this
#                                       format.
# 2015/02/05 - 0.9.0 - Fenix          - correctly initialize Server client
# 2015/02/08 - 0.10  - Thomas LEVEIL  - recognize more log lines + fire events related to rounds
# 2015/02/14 - 0.11  - Thomas LEVEIL  - fix spectator team recognition
#                                     - in the clients manager, identify players by their steamid instead of cid
# 2015/02/19 - 0.12  - Fenix          - fixed EVT_CLIENT_DISCONNECT not being fired
# 2015/02/14 - 0.13  - 82ndab-Bravo17 - check both cid and guid when finding clients to avoid duplicate clients or
#                                     - clients in wrong slots
#                                     - revert to using cid instead of steamid to id players
# 2015/13/01 - 0.14  - 82ndab-Bravo17 - don't authorize Console when it says something in game
#                                     - bots should now stay authed if still on server during sync
# 2015/03/07 - 0.15  - Thomas LEVEIL  - disconnect client after kicking them
# 2015/13/03 - 0.16  - 82ndab-Bravo17 - get map name from host_map cvar since it is no longer returned by status
# 2015-04-16 - 0.17  - Fenix          - uniform class variables (dict -> variable)

import re
import time
import new

from b3 import TEAM_UNKNOWN
from b3 import TEAM_BLUE
from b3 import TEAM_RED
from b3 import TEAM_SPEC
from b3.clients import Client
from b3.clients import Clients
from b3.cvar import Cvar
from b3.decorators import GameEventRouter
from b3.functions import minutesStr
from b3.functions import prefixText
from b3.functions import time2minutes
from b3.functions import getStuffSoundingLike
from b3.parser import Parser
from b3.parsers.source.rcon import Rcon

__author__ = 'Courgette'
__version__ = '0.17'


# GAME SETUP
# ==========
#
# In order to have a consistent name for the game log file, you need to start the game server
# with '-condebug' as a command line parameter. The game server log file can then be found in
# the insurgency folder under the name 'console.log'.
#
# You must have SourceMod installed on the game server. See http://www.sourcemod.net/
# If you want to use the stock map voting system, remove the source mod nextmap plugin.
#
# Make sure to avoid conflict with in-game commands between B3 and SourceMod by choosing different command prefixes.
# See PublicChatTrigger and SilentChatTrigger in addons/sourcemod/configs/core.cfg
#
#
# SourceMod recommended plugins
# -----------------------------
#
# ## B3 Say
# If you have the SourceMod plugin B3 Say installed then the messages sent by B3 will better displayed on screen.
# http://forum.bigbrotherbot.net/counter-strike-global-offensive/sourcemod-plugins-for-b3/

# disable the authorizing timer that comes by default with the b3.clients.Clients class
Clients.authorizeClients = lambda *args, **kwargs: None

# Regular expression recognizing a HalfLife game engine log line as
# described at https://developer.valvesoftware.com/wiki/HL_Log_Standard
RE_HL_LOG_LINE = r'''^L [01]\d/[0-3]\d/\d+ - [0-2]\d:[0-5]\d:[0-5]\d:\s*(?P<data>.*)'''

# Regular expression able to extract properties from HalfLife game engine log line as described at
# https://developer.valvesoftware.com/wiki/HL_Log_Standard#Notes
RE_HL_LOG_PROPERTY = re.compile('''\((?P<key>[^\s\(\)]+)(?P<data>| "(?P<value>[^"]*)")\)''')

# Regular expression to parse cvar queries responses
RE_CVAR = re.compile(r'''^"(?P<cvar>\S+?)" = "(?P<value>.*?)" \( def. "(?P<default>.*?)".*$''', re.MULTILINE)

ger = GameEventRouter()


def parseProperties(properties):
    """
    Parse HL log properties as described at https://developer.valvesoftware.com/wiki/HL_Log_Standard#Notes
    :param properties: string representing HL log properties
    :return: a dict representing all the property key:value parsed
    """
    rv = {}
    if properties:
        for match in re.finditer(RE_HL_LOG_PROPERTY, properties):
            if match.group('data') == '':
                # Parenthised properties with no explicit value indicate a boolean true value
                rv[match.group('key')] = True
            else:
                rv[match.group('key')] = match.group('value')
    return rv


class InsurgencyParser(Parser):
    """
    The Insurgency B3 parser class
    """
    gameName = "insurgency"
    privateMsg = True
    OutputClass = Rcon
    PunkBuster = None
    sm_plugins = None
    last_killlocation_properties = None
    map_cycles = {}
    map_cycle_no = 0

    # extract the time from game log line
    _lineTime = re.compile(r"""^L [01]\d/[0-3]\d/\d+ - [0-2]\d:(?P<minutes>[0-5]\d):(?P<seconds>[0-5]\d):\s*""")

    # game engine does not support color code, so we need this property
    # in order to get stripColors working
    _reColor = re.compile(r'(\^[0-9])')

    _line_length = 120
    _line_color_prefix = ''
    _use_color_codes = False

    ####################################################################################################################
    #                                                                                                                  #
    #  PARSER INITIALIZATION                                                                                           #
    #                                                                                                                  #
    ####################################################################################################################

    def __new__(cls, *args, **kwargs):
        return Parser.__new__(cls)

    def patch_b3_admin_plugin(self):
        """
        Monkey patches the admin plugin
        """
        def parse_map_parameters(this, data, client):
            """
            Method that parses a command parameters to extract map and gamemode.
            Expecting one or two parameters separated by a space.
            <map> <gamemode>
            """
            parts = data.split()
            if len(parts) < 2:
                gamemode_data = ''
            else:
                gamemode_data = parts[1]
            map_data = parts[0]

            return map_data, gamemode_data

        # Monkey patch the cmd_map method of the loaded AdminPlugin instance
        # to require 2nd parameter which is the game mode
        def new_cmd_map(this, data, client, cmd=None):
            """
            <map> <gamemode> - switch current map. Specify a gamemode by separating
            them from the map name with a space
            """
            if not data:
                allavailablemaps = this.console.getAllAvailableMaps()
                maplist = ''
                for m in allavailablemaps:
                    maplist = maplist + ', ' + m
                client.message("Full list of maps on the server" + maplist)
                client.message("PVP Gametypes are: ambush, firefight, flashpoint, infiltrate, occupy, push, skirmish, "
                               "strike")
                client.message("Coop Gametypes are: checkpoint, outpost, hunt, survival")
                client.message('For more help, type !help map')
                return

            parsed_data = this.parse_map_parameters(data, client)
            map_id, gamemode_id = parsed_data

            suggestions = this.console.changeMap(map_id, gamemode_id)
            if type(suggestions) == list:
                client.message('do you mean : %s ?' % ', '.join(suggestions))

        adminPlugin = self.getPlugin('admin')
        adminPlugin.parse_map_parameters = new.instancemethod(parse_map_parameters, adminPlugin)
        command = adminPlugin._commands['map']
        command.func = new.instancemethod(new_cmd_map, adminPlugin)
        command.help = new_cmd_map.__doc__.strip()

    def startup(self):
        """
        Called after the parser is created before run().
        """
        self.bot("TIP: In order to have a consistent name for the game log file, you need to start the game server "
                 "with '-condebug' as a command line parameter. The game server log file can then be found in the "
                 "insurgency folder under the name 'console.log'.")
        self.bot("TIP: Make sure to avoid conflicts with in-game commands between B3 and SourceMod by choosing "
                 "different command prefixes. See PublicChatTrigger and SilentChatTrigger in "
                 "addons/sourcemod/configs/core.cfg")
        self.bot("TIP: If you have the SourceMod plugin `B3 Say` installed then the messages sent by B3 will better "
                 "displayed on screen. "
                 "http://forum.bigbrotherbot.net/counter-strike-global-offensive/sourcemod-plugins-for-b3/")

        if not self.is_sourcemod_installed():
            self.critical("You need to have SourceMod installed on your game server")
            raise SystemExit(220)

        # add game specific events
        self.createEvent("EVT_SUPERLOGS_WEAPONSTATS", "SourceMod SuperLogs weaponstats")
        self.createEvent("EVT_SUPERLOGS_WEAPONSTATS2", "SourceMod SuperLogs weaponstats2")
        self.createEvent("EVT_SERVER_REQUIRES_RESTART", "Source server requires restart")

        # create the server client
        self.clients.newClient('Server', guid='Server', name='Server', hide=True, pbid='Server', team=TEAM_UNKNOWN)

        self.game.cvar = {}
        self.queryServerInfo()
        self.game.mapName = self.getMap()
        if self.game.mapName == None:
            self.game.mapName = ''
        self.verbose2('Current map name is %s' % self.game.mapName)

        # load SM plugins list
        self.sm_plugins = self.get_loaded_sm_plugins()

        # keeps the last properties from a killlocation game event
        self.last_killlocation_properties = None

    def pluginsStarted(self):
        """
        Called once all plugins were started.
        Handy if some of them must be monkey-patched.
        """
        self.patch_b3_admin_plugin()
        self.info('Admin plugin patched')

    ####################################################################################################################
    #                                                                                                                  #
    #  GAME EVENTS HANDLERS                                                                                            #
    #  READ HL LOG STANDARD DOCUMENTATION AT: https://developer.valvesoftware.com/wiki/HL_Log_Standard                 #
    #                                                                                                                  #
    ####################################################################################################################

    @ger.gameEvent(
        r'''^//''',  # comment log line
        r'''^server cvars start''',
        r'''^server cvars end''',
        r'''^\[basechat\.smx\] .*''',
        r'''^\[META\] Loaded \d+ plugins \(\d+ already loaded\)$''',
        r'''^\[META\] Loaded \d+ plugin.$''',
        r'^Log file started.*$',
        r'^Log file closed.*$',
        r'^\s*path_goal .*',
        r'^Vote succeeded.*',
        r'^".+" STEAM USERID validated$',
        r'^Dropped .+ from server (Disconnected\.)$'
    )
    def ignored_line(self):
        # L 09/24/2001 - 18:44:50: // This is a comment in the log file. It should not be parsed.
        # L 08/26/2012 - 05:29:47: server cvars start
        # L 08/26/2012 - 05:29:47: server cvars end
        # L 02/07/2015 - 15:15:24: Log file started (file "logs\\L023_081_154_166_23274_201502071515_001.log") (game "C:\\servers\\insurgency") (version "5885")
        # L 02/07/2015 - 15:15:22: Log file closed
        print "ignored"
        pass

    @ger.gameEvent(r'^"(?P<a_name>.+)<(?P<a_cid>\d+)><(?P<a_guid>.+)><(?P<a_team>.*)>" killed "(?P<v_name>.+)<(?P<v_cid>\d+)><(?P<v_guid>.+)><(?P<v_team>.*)>" with "(?P<weapon>\S*)"(?P<properties>.*)$',
                   r'^"(?P<a_name>.+)<(?P<a_cid>\d+)><(?P<a_guid>.+)><(?P<a_team>.*)>" \[-?\d+ -?\d+ -?\d+\] killed "(?P<v_name>.+)<(?P<v_cid>\d+)><(?P<v_guid>.+)><(?P<v_team>.*)>" \[-?\d+ -?\d+ -?\d+\] with "(?P<weapon>\S*)"(?P<properties>.*)$')
    def on_kill(self, a_name, a_cid, a_guid, a_team, v_name, v_cid, v_guid, v_team, weapon, properties):
        # L 08/26/2012 - 03:46:44: "Pheonix<22><BOT><TERRORIST>" killed "Ringo<17><BOT><CT>" with "glock" (headshot)
        # L 08/26/2012 - 03:46:46: "Shark<19><BOT><CT>" killed "Pheonix<22><BOT><TERRORIST>" with "hkp2000"
        # L 08/26/2012 - 03:47:40: "Stone<18><BOT><TERRORIST>" killed "Steel<13><BOT><CT>" with "glock"
        attacker = self.getClientOrCreate(a_cid, a_guid, a_name, a_team)
        victim = self.getClientOrCreate(v_cid, v_guid, v_name, v_team)
        # victim.state = b3.STATE_DEAD ## do we need that ? is this info used ?
        props = parseProperties(properties)
        headshot = props.get('headshot', False)

        eventkey = "EVT_CLIENT_KILL"
        if attacker.cid == victim.cid:
            eventkey = "EVT_CLIENT_SUICIDE"
        elif attacker.team in (TEAM_BLUE, TEAM_RED) and attacker.team == victim.team:
            eventkey = "EVT_CLIENT_KILL_TEAM"

        damage_pct = 100
        damage_type = None
        hit_location = "head" if headshot else "body"
        data = [damage_pct, weapon, hit_location, damage_type]

        if self.last_killlocation_properties:
            data.append(parseProperties(self.last_killlocation_properties))
            self.last_killlocation_properties = None

        return self.getEvent(eventkey, client=attacker, target=victim, data=tuple(data))

    @ger.gameEvent(r'^"(?P<a_name>.+)<(?P<a_cid>\d+)><(?P<a_guid>.+)><(?P<a_team>.*)>" assisted killing "(?P<v_name>.+)<(?P<v_cid>\d+)><(?P<v_guid>.+)><(?P<v_team>.*)>"(?P<properties>.*)$')
    def on_assisted_killing(self, a_name, a_cid, a_guid, a_team, v_name, v_cid, v_guid, v_team, properties):
        # L 08/26/2012 - 03:46:44: "Greg<3946><BOT><CT>" assisted killing "Dennis<3948><BOT><TERRORIST>"
        attacker = self.getClientOrCreate(a_cid, a_guid, a_name, a_team)
        victim = self.getClientOrCreate(v_cid, v_guid, v_name, v_team)
        #props = parseProperties(properties)
        return self.getEvent("EVT_CLIENT_ACTION", client=attacker, target=victim, data="assisted killing")

    @ger.gameEvent(r'^"(?P<name>.+)<(?P<cid>\d+)><(?P<guid>.+)><(?P<team>.*)>"(?: \[-?\d+ -?\d+ -?\d+\])? committed suicide with "(?P<weapon>\S*)"$')
    def on_suicide(self, name, cid, guid, team, weapon):
        # L 08/26/2012 - 03:38:04: "Pheonix<22><BOT><TERRORIST>" committed suicide with "world"
        client = self.getClientOrCreate(cid, guid, name, team)
        # victim.state = b3.STATE_DEAD ## do we need that ? is this info used ?
        damage_pct = 100
        damage_type = None
        return self.getEvent("EVT_CLIENT_SUICIDE", client=client, target=client, data=(damage_pct, weapon, "body",
                                                                                       damage_type))

    @ger.gameEvent(r'^"(?P<cvar_name>\S+)" = "(?P<cvar_value>.*)"$',
                   r'^server_cvar: "(?P<cvar_name>\S+)" "(?P<cvar_value>.*)"$')
    def on_cvar(self, cvar_name, cvar_value):
        # L 08/26/2012 - 03:49:56: "r_JeepViewZHeight" = "10.0"
        # L 08/26/2012 - 03:49:56: "tv_password" = ""
        # L 08/26/2012 - 03:49:56: "sv_specspeed" = "3"
        # L 02/07/2015 - 14:48:24: "nextlevel" = "heights_coop checkpoint"
        self.game.cvar[cvar_name] = cvar_value

    @ger.gameEvent(r'^-------- Mapchange to (?P<new_map>\S+) --------$')
    def on_map_change(self, new_map):
        # L 08/27/2012 - 23:57:14: -------- Mapchange to de_dust --------
        self.game.mapName = new_map

    @ger.gameEvent(r'^Loading map "(?P<new_map>\S+)"$')
    def on_started_map(self, new_map):
        # L 08/26/2012 - 03:49:56: Loading map "de_nuke"
        self.game.mapName = new_map

    @ger.gameEvent(r'^Started map "(?P<new_map>\S+)" \(CRC "-?\d+"\)$')
    def on_started_map(self, new_map):
        # L 08/26/2012 - 03:22:35: Started map "de_dust" (CRC "1592693790")
        # L 08/26/2012 - 03:49:58: Started map "de_nuke" (CRC "-568155013")
        self.game.mapName = new_map
        self.game.startMap()

    @ger.gameEvent(r'^"(?P<name>.+)<(?P<cid>\d+)><(?P<guid>\S*)><(?P<team>\S*)>" STEAM USERID validated$')
    def on_userid_validated(self, name, cid, guid, team):
        # L 08/26/2012 - 03:22:36: "courgette<2><STEAM_1:0:1111111><>" STEAM USERID validated
        self.getClientOrCreate(cid, guid, name, team)

    @ger.gameEvent(r'^"(?P<name>.+)<(?P<cid>\d+)><(?P<guid>.+)><(?P<team>.*)>" connected, address "(?P<ip>.+)"$')
    def on_client_connected(self, name, cid, guid, team, ip):
        # L 08/26/2012 - 03:22:36: "courgette<2><STEAM_1:0:1111111><>" connected, address "11.222.111.222:27005"
        # L 08/26/2012 - 03:22:36: "Moe<3><BOT><>" connected, address "none"
        client = self.getClientOrCreate(cid, guid, name, team)
        if ip != "none" and client.ip != ip:
            client.ip = ip
            client.save()

    @ger.gameEvent(r'^"(?P<name>.+)<(?P<cid>\d+)><(?P<guid>.+)><(?P<team>.*)>" disconnected \(reason "(?P<reason>.*)"\)$')
    def on_client_disconnected(self, name, cid, guid, team, reason):
        # L 08/26/2012 - 04:45:04: "Kyle<63><BOT><CT>" disconnected (reason "Kicked by Console")
        # L 02/13/2015 - 18:08:14: "JACKASS NINJA<479><STEAM_1:0:87123453><#Team_Security>" disconnected (reason "to make room for a clan member")
        # L 02/13/2015 - 18:18:38: "[CiD] Toki<21><STEAM_1:0:27763712><#Team_Security>" disconnected (reason "Disconnected.")
        client = self.getClient(cid, guid)
        event = None
        if client:
            if reason == "Kicked by Console":
                event = self.getEvent("EVT_CLIENT_KICK", client=client, data={'reason': reason, 'admin': None})
            client.disconnect()
        if event:
            return event

    @ger.gameEvent(r'^"(?P<name>.+)<(?P<cid>\d+)><(?P<guid>.+)><(?P<team>.*)>" entered the game$')
    def on_client_entered(self, name, cid, guid, team):
        # L 08/26/2012 - 05:29:48: "Rip<93><BOT><>" entered the game
        # L 08/26/2012 - 05:38:36: "GrUmPY<105><STEAM_1:0:22222222><>" entered the game
        # L 08/26/2012 - 05:43:29: "Ein 1337er M!L[H<106><STEAM_1:0:5555555><>" entered the game
        client = self.getClientOrCreate(cid, guid, name, team)
        return self.getEvent("EVT_CLIENT_JOIN", client=client)

    @ger.gameEvent(r'^"(?P<old_name>.+)<(?P<cid>\d+)><(?P<guid>.+)><(?P<team>.*)>" changed name to "(?P<new_name>.+)"$')
    def on_client_changed_name(self, old_name, cid, guid, team, new_name):
        # L 02/07/2015 - 19:36:25: "Jono<252><BOT><#Team_Insurgent>" changed name to "(1)Jono"
        client = self.getClientOrCreate(cid, guid, old_name, team)
        client.name = new_name  # Client.name setter will fire EVT_CLIENT_NAME_CHANGE is needed

    @ger.gameEvent(r'^"(?P<name>.+)<(?P<cid>\d+)><(?P<guid>.+)><(?P<old_team>\S+)>" joined team "(?P<new_team>\S+)"$',
                   r'^"(?P<name>.+)<(?P<cid>\d+)><(?P<guid>.+)>" switched from team <(?P<old_team>\S+)> to <(?P<new_team>\S+)>$')
    def on_client_join_team(self, name, cid, guid, old_team, new_team):
        #L 08/26/2012 - 03:22:36: "Pheonix<11><BOT><Unassigned>" joined team "TERRORIST"
        #L 08/26/2012 - 03:22:36: "Wolf<12><BOT><Unassigned>" joined team "CT"
        #L 07/19/2013 - 17:18:44: "courgette<194><STEAM_1:0:1111111><CT>" switched from team <TERRORIST> to <Unassigned>
        if new_team == 'Unassigned':
            # The player might have just left the game server, so we must make sure not to recreate the Client object
            client = self.getClient(cid, guid)
        else:
            client = self.getClientOrCreate(cid, guid, name, old_team)
        if client:
            client.team = self.getTeam(new_team)


    @ger.gameEvent(r"""^Gamerules: entering state '(?P<gamerule_state>.+)'""")
    def on_gamerule_state(self, gamerule_state):
        # "Gamerules: entering state 'GR_STATE_PREGAME'"
        # "Gamerules: entering state 'GR_STATE_STARTGAME'"
        # "Gamerules: entering state 'GR_STATE_PREROUND'"
        # "Gamerules: entering state 'GR_STATE_RND_RUNNING'"
        # "Gamerules: entering state 'GR_STATE_POSTROUND'"
        # "Gamerules: entering state 'GR_STATE_PREROUND'"
        # "Gamerules: entering state 'GR_STATE_RND_RUNNING'"
        # "Gamerules: entering state 'GR_STATE_POSTROUND'"
        # "Gamerules: entering state 'GR_STATE_PREROUND'"
        # "Gamerules: entering state 'GR_STATE_RND_RUNNING'"
        # "Gamerules: entering state 'GR_STATE_POSTROUND'"
        # "Gamerules: entering state 'GR_STATE_PREROUND'"
        # "Gamerules: entering state 'GR_STATE_RND_RUNNING'"
        # "Gamerules: entering state 'GR_STATE_POSTROUND'"
        # "Gamerules: entering state 'GR_STATE_GAME_OVER'"
        if gamerule_state == 'GR_STATE_PREGAME':
            return self.getEvent("EVT_GAME_WARMUP")
        elif gamerule_state == 'GR_STATE_STARTGAME':
            self.game.startRound()
            self.sync()
            clients = self.getPlayerList()
            for cid in clients:
                client = self.clients.getByCID(cid)
                return self.getEvent("EVT_CLIENT_JOIN", client=client)
        elif gamerule_state == 'GR_STATE_RND_RUNNING':
            self.game.startRound()
            return self.getEvent('EVT_GAME_ROUND_START', data=self.game)
        elif gamerule_state == 'GR_STATE_POSTROUND':
            return self.getEvent("EVT_GAME_ROUND_END")
        elif gamerule_state == 'GR_STATE_GAME_OVER':
            self.game.mapEnd()
            return self.getEvent("EVT_GAME_EXIT")
        elif gamerule_state in ( 'GR_STATE_PREROUND'):
            pass
        else:
            self.warning("unexpected GameRule state : '%s' : please report this on the B3 forums" % gamerule_state)

    @ger.gameEvent(r'^"(?P<name>.+)<(?P<cid>\d+)><(?P<guid>.+)><(?P<team>.*)>" triggered "(?P<event_name>\S+)"(?P<properties>.*)$')
    def on_player_action(self, name, cid, guid, team, event_name, properties):
        client = self.getClientOrCreate(cid, guid, name, team)
        props = parseProperties(properties)
        if event_name in ("Got_The_Bomb", "Dropped_The_Bomb", "Planted_The_Bomb", "Begin_Bomb_Defuse_Without_Kit",
                          "Begin_Bomb_Defuse_With_Kit", "Defused_The_Bomb", "headshot", "round_mvp", "obj_captured",
                          "obj_destroyed"):
            # L 08/26/2012 - 03:22:37: "Pheonix<11><BOT><TERRORIST>" triggered "Got_The_Bomb"
            # L 08/26/2012 - 03:46:46: "Pheonix<22><BOT><TERRORIST>" triggered "Dropped_The_Bomb"
            # L 08/26/2012 - 03:51:41: "Gunner<29><BOT><CT>" triggered "Begin_Bomb_Defuse_Without_Kit"
            # L 09/25/2012 - 22:14:09: "Grant<24><BOT><CT>" triggered "Begin_Bomb_Defuse_With_Kit"
            # L 08/26/2012 - 05:04:55: "Steel<80><BOT><TERRORIST>" triggered "Planted_The_Bomb"
            # L 08/29/2012 - 22:27:01: "Zach<5><BOT><CT>" triggered "headshot"
            # L 08/29/2012 - 22:31:50: "Pheonix<4><BOT><TERRORIST>" triggered "round_mvp"
            return self.getEvent("EVT_CLIENT_ACTION", client=client, data=event_name)

        elif event_name == "clantag":
            client.clantag = props.get("value", "")

        elif event_name == "weaponstats":
            return self.getEvent("EVT_SUPERLOGS_WEAPONSTATS", client=client, data=props)

        elif event_name == "weaponstats2":
            return self.getEvent("EVT_SUPERLOGS_WEAPONSTATS2", client=client, data=props)

        else:
            self.warning("unknown client event : '%s' : please report this on the B3 forums" % event_name)

    @ger.gameEvent(r'^Team "(?P<team>\S+)" triggered "(?P<event_name>[^"]+)"(?P<properties>.*)$')
    def on_team_action(self, team, event_name, properties):
        # L 08/26/2012 - 03:48:09: Team "CT" triggered "SFUI_Notice_Target_Saved" (CT "3") (T "5")
        # L 08/26/2012 - 03:51:50: Team "TERRORIST" triggered "SFUI_Notice_Target_Bombed" (CT "1") (T "1")
        if event_name in ("SFUI_Notice_Target_Saved",
                          "SFUI_Notice_Target_Bombed",
                          "SFUI_Notice_Terrorists_Win",
                          "SFUI_Notice_CTs_Win",
                          "SFUI_Notice_Bomb_Defused",
                          "obj_captured",
                          "obj_destroyed",
                          "Round_Win"):
            return self.getEvent('EVT_GAME_ROUND_END', data={"team": self.getTeam(team),
                                                             "event_name": event_name,
                                                             "properties": properties})
        else:
            self.warning("unexpected team event : '%s' : please report this on the B3 forums" % event_name)

    @ger.gameEvent(r'^Team "(?P<team>\S+)" scored "(?P<points>\d+)" with "(?P<num_players>\d+)" players$')
    def on_team_score(self, team, points, num_players):
        # L 08/26/2012 - 03:48:09: Team "CT" scored "3" with "5" players
        # L 08/26/2012 - 03:48:09: Team "TERRORIST" scored "5" with "5" players
        pass  # TODO should we do anything with that info ?

    @ger.gameEvent(r'^"(?P<name>.+)<(?P<cid>\d+)><(?P<guid>.+)><(?P<team>.*?)>" say "(?P<text>.*)"$')
    def on_client_say(self, name, cid, guid, team, text):
        # L 08/26/2012 - 05:09:55: "courgette<2><STEAM_1:0:1487018><CT>" say "!iamgod"
        # L 09/16/2012 - 04:55:17: "Spoon<2><STEAM_1:0:11111111><>" say "!h"
        if guid == 'Console':
            pass
        else:
            client = self.getClientOrCreate(cid, guid, name, team)
            return self.getEvent("EVT_CLIENT_SAY", client=client, data=text)

    @ger.gameEvent(r'^"(?P<name>.+)<(?P<cid>\d+)><(?P<guid>.+)><(?P<team>.*?)>" say_team "(?P<text>.*)"$')
    def on_client_teamsay(self, name, cid, guid, team, text):
        # L 08/26/2012 - 05:04:44: "courgette<2><STEAM_1:0:1487018><CT>" say_team "team say"
        client = self.getClientOrCreate(cid, guid, name, team)
        return self.getEvent("EVT_CLIENT_TEAM_SAY", client=client, data=text)

    @ger.gameEvent(r'^"(?P<name>.+)<(?P<cid>\d+)><(?P<guid>.+)><(?P<team>\S+)>" purchased "(?P<item>\S+)"$')
    def on_player_purchased(self, name, cid, guid, team, item):
        client = self.getClientOrCreate(cid, guid, name, team)
        # L 08/26/2012 - 03:22:37: "Calvin<3942><BOT><CT>" purchased "p90"
        # L 08/26/2012 - 03:22:37: "courgette<2><STEAM_1:0:1487018><CT>" purchased "hegrenade"
        return self.getEvent("EVT_CLIENT_ACTION", client=client, data='purchased "%s"' % item)

    @ger.gameEvent(r'^"(?P<name>.+)<(?P<cid>\d+)><(?P<guid>.+)><(?P<team>\S+)>" threw (?P<item>.+?)( \[-?\d+ -?\d+ -?\d+\])?$')
    def on_player_threw(self, name, cid, guid, team, item):
        client = self.getClientOrCreate(cid, guid, name, team)
        # L 08/26/2012 - 03:22:37: "courgette<2><STEAM_1:0:1111111><CT>" threw molotov [59 386 -225]
        return self.getEvent("EVT_CLIENT_ACTION", client=client, data='threw "%s"' % item)

    @ger.gameEvent(r'^rcon from "(?P<ip>.+):(?P<port>\d+)":\sBad Password$')
    def on_bad_rcon_password(self, ip, port):
        # L 08/26/2012 - 05:21:23: rcon from "78.207.134.100:15073": Bad Password
        self.error("Bad RCON password, check your b3.xml file")

    @ger.gameEvent(r'^Molotov projectile spawned at (?P<coord>-?[\d.]+ -?[\d.]+ -?[\d.]+), velocity (?P<velocity>-?[\d.]+ -?[\d.]+ -?[\d.]+)$')
    def on_molotov_spawed(self, coord, velocity):
        pass # Do we care ?

    @ger.gameEvent(r'^rcon from "(?P<ip>.+):(?P<port>\d+)": command "(?P<cmd>.*)"$')
    def on_rcon(self, ip, port, cmd):
        # L 08/26/2012 - 05:37:56: rcon from "11.222.111.122:15349": command "say test"
        pass

    @ger.gameEvent(r'^Banid: "(?P<name>.+)<(?P<cid>\d+)><(?P<guid>.+)><(?P<team>.*)>" was banned "for (?P<duration>.+)" by "(?P<admin>.*)"$')
    def on_banid(self, name, cid, guid, team, duration, admin):
        # L 08/28/2012 - 00:03:01: Banid: "courgette<91><STEAM_1:0:1111111><>" was banned "for 1.00 minutes" by "Console"
        client = self.storage.getClient(Client(guid=guid))
        if client:
            return self.getEvent("EVT_CLIENT_BAN_TEMP", {"duration": duration, "admin": admin, 'reason': None}, client)

    @ger.gameEvent(r'^\[basecommands.smx\] ".+<\d+><.+><.*>" kicked "(?P<name>.+)<(?P<cid>\d+)><(?P<guid>.+)><(?P<team>.*)>"(?P<properties>.*)$')
    def on_kicked(self, name, cid, guid, team, properties):
        client = self.storage.getClient(Client(guid=guid))
        if client:
            p = parseProperties(properties)
            return self.getEvent("EVT_CLIENT_KICK", {'reason': p.get('reason', ''), 'admin': None}, client)

    @ger.gameEvent(r'^server_message: "(?P<msg>.*)"(?P<properties>.*)$')
    def on_server_message(self, msg, properties):
        # L 08/30/2012 - 00:43:10: server_message: "quit"
        # L 08/30/2012 - 00:43:10: server_message: "restart"
        if msg in ("quit", "restart"):
            pass
        else:
            self.warning("unexpected server_message : '%s' : please report this on the B3 forums" % msg)

    @ger.gameEvent(r'^(?P<data>Your server needs to be restarted.*)$',
                   r'^(?P<data>Your server is out of date.*)$')
    def on_server_restart_request(self, data):
        # L 09/17/2012 - 23:26:45: Your server needs to be restarted in order to receive the latest update.
        # L 09/17/2012 - 23:26:45: Your server is out of date.  Please update and restart.
        return self.getEvent('EVT_SERVER_REQUIRES_RESTART', data)

    @ger.gameEvent(r'''(?x)
        ^
            "(?P<name>.+)<(?P<cid>\d+)><(?P<guid>.+)><(?P<team>\S+)>"
            \ stuck
            \ \(position\ "(?P<position>.+?)"\)
            \ \(duration\ "(?P<duration>.+?)"\)
            (
                \s+L\ .+path_goal
                \ \(\s*"(?P<path_goal>.*?)"\s*\)
            )?
        $''')
    def on_bot_stuck(self, name, cid, guid, team, position, duration, path_goal=None):
        # "Ted<368><BOT><3>" stuck (position "4700.29 -2847.70 150.76") (duration "3.47") L 02/07/2015 - 12:28:49:    path_goal ( "4693.44 -2975.00 151.53" )
        pass

    # ------------------------------------- /!\  this one must be the last /!\ --------------------------------------- #

    @ger.gameEvent(r'''^(?P<data>.+)$''')
    def on_unknown_line(self, data):
        """
        Catch all lines that were not handled.
        """
        self.warning("unhandled log line : %s : please report this on the B3 forums" % data)

    ####################################################################################################################
    #                                                                                                                  #
    #  B3 PARSER INTERFACE IMPLEMENTATION                                                                              #
    #                                                                                                                  #
    ####################################################################################################################

    def getPlayerList(self):
        """
        Query the game server for connected players.
        return a dict having players' id for keys and players' data as another dict for values
        """
        return self.queryServerInfo()

    def authorizeClients(self):
        """
        For all connected players, fill the client object with properties allowing to find
        the user in the database (usualy guid, or punkbuster id, ip) and call the
        Client.auth() method
        """
        pass  # no need as all game log lines have the client guid

    def sync(self):
        """
        For all connected players returned by self.getPlayerList(), get the matching Client
        object from self.clients (with self.clients.getByCID(cid) or similar methods) and
        look for inconsistencies. If required call the client.disconnect() method to remove
        a client from self.clients.
        This is mainly useful for games where clients are identified by the slot number they
        occupy. On map change, a player A on slot 1 can leave making room for player B who
        connects on slot 1.
        """
        plist = self.getPlayerList()

        for cid, c in plist.iteritems():
            client = self.clients.getByCID(cid)
            if client:
                if client.guid == c.guid:
                    # player matches
                    self.debug('in-sync %s == %s', client.guid, c.guid)
                else:
                    self.debug('no-sync, disconnect client %s <> %s', client.guid, c.guid)
                    client.disconnect()
                    self.getClientOrCreate(c.cid, c.guid, c.name)
            else:
                self.getClientOrCreate(c.cid, c.guid, c.name)

        # now we need to remove any players that have left
        if self.clients:
            client_cid_list = []

            for cl in plist.values():
                client_cid_list.append(cl.cid)

            #Use clients.items so we get all clients, including bots
            client_list = self.clients.items()
            for cid, client in client_list:
                self.verbose2('Client in Client list %s' % client.name)
                if client.cid not in client_cid_list:
                    self.debug('Removing %s from list - left server' % client.name)
                    client.disconnect()
        return

    def say(self, msg, *args):
        """
        Broadcast a message to all players.
        :param msg: The message to be broadcasted
        """
        msg = self.stripColors(msg % args)
        if msg and len(msg.strip()):
            template = 'sm_say %s'
            if "B3 Say" in self.sm_plugins:
                template = 'b3_say %s'
            else:
                msg = prefixText([self.msgPrefix], msg)
            for line in self.getWrap(msg):
                self.output.write(template % line)

    def saybig(self, msg, *args):
        """
        Broadcast a message to all players in a way that will catch their attention.
        :param msg: The message to be broadcasted
        """
        msg = self.stripColors(msg % args)
        if msg and len(msg.strip()):
            template = 'sm_hsay %s'
            if "B3 Say" in self.sm_plugins:
                template = 'b3_hsay %s'
            else:
                msg = prefixText([self.msgPrefix], msg)
            for line in self.getWrap(msg):
                self.output.write(template % line)

    def message(self, client, msg, *args):
        """
        Display a message to a given client
        :param client: The client to who send the message
        :param msg: The message to be sent
        """
        msg = self.stripColors(msg % args)
        if not client.bot:  # do not talk to bots
            if msg and len(msg.strip()):
                template = 'sm_psay #%(guid)s "%(msg)s"'
                if "B3 Say" in self.sm_plugins:
                    template = 'b3_psay #%(guid)s "%(msg)s"'
                else:
                    msg = prefixText([self.msgPrefix], msg)
                for line in self.getWrap(msg):
                    self.output.write(template % {'guid': client.guid, 'msg': line})

    def kick(self, client, reason='', admin=None, silent=False, *kwargs):
        """
        Kick a given client.
        :param client: The client to kick
        :param reason: The reason for this kick
        :param admin: The admin who performed the kick
        :param silent: Whether or not to announce this kick
        """
        self.debug('kick reason: [%s]' % reason)
        if isinstance(client, basestring):
            clients = self.clients.getByMagic(client)
            if len(clients) != 1:
                return
            else:
                client = clients[0]

        if admin:
            variables = self.getMessageVariables(client=client, reason=reason, admin=admin)
            fullreason = self.getMessage('kicked_by', variables)
        else:
            variables = self.getMessageVariables(client=client, reason=reason)
            fullreason = self.getMessage('kicked', variables)

        fullreason = self.stripColors(fullreason)
        reason = self.stripColors(reason)

        self.do_kick(client, reason)

        if not silent and fullreason != '':
            self.say(fullreason)

    def ban(self, client, reason='', admin=None, silent=False, *kwargs):
        """
        Ban a given client.
        :param client: The client to ban
        :param reason: The reason for this ban
        :param admin: The admin who performed the ban
        :param silent: Whether or not to announce this ban
        """
        if client.bot:  # exclude bots
            return

        self.debug('BAN : client: %s, reason: %s', client, reason)
        if isinstance(client, basestring):
            clients = self.clients.getByMagic(client)
            if len(clients) != 1:
                return
            else:
                client = clients[0]

        if admin:
            variables = self.getMessageVariables(client=client, reason=reason, admin=admin)
            fullreason = self.getMessage('banned_by', variables)
        else:
            variables = self.getMessageVariables(client=client, reason=reason)
            fullreason = self.getMessage('banned', variables)

        fullreason = self.stripColors(fullreason)
        reason = self.stripColors(reason)

        self.do_ban(client, reason)
        if admin:
            admin.message('Banned: %s (@%s) has been added to banlist' % (client.exactName, client.id))

        if not silent and fullreason != '':
            self.say(fullreason)

        self.queueEvent(self.getEvent("EVT_CLIENT_BAN", {'reason': reason, 'admin': admin}, client))

    def unban(self, client, reason='', admin=None, silent=False, *kwargs):
        """
        Unban a client.
        :param client: The client to unban
        :param reason: The reason for the unban
        :param admin: The admin who unbanned this client
        :param silent: Whether or not to announce this unban
        """
        if client.bot:  # exclude bots
            return

        self.debug('UNBAN: name: %s - ip: %s - guid: %s' % (client.name, client.ip, client.guid))
        if client.ip:
            self.do_unban_by_ip(client)
            self.verbose('UNBAN: removed ip (%s) from banlist' % client.ip)
            if admin:
                admin.message('Unbanned: %s. '
                              'His last ip (%s) has been removed from banlist' % (client.exactName, client.ip))
            if admin:
                variables = self.getMessageVariables(client=client, reason=reason, admin=admin)
                fullreason = self.getMessage('unbanned_by', variables)
            else:
                variables = self.getMessageVariables(client=client, reason=reason)
                fullreason = self.getMessage('unbanned', variables)

            if not silent and fullreason != '':
                self.say(fullreason)

        self.do_unban_by_steamid(client)
        self.verbose('UNBAN: removed guid (%s) from banlist' % client.guid)
        if admin:
            admin.message('Unbanned: removed %s guid from banlist' % client.exactName)

    def tempban(self, client, reason='', duration=2, admin=None, silent=False, *kwargs):
        """
        Tempban a client.
        :param client: The client to tempban
        :param reason: The reason for this tempban
        :param duration: The duration of the tempban
        :param admin: The admin who performed the tempban
        :param silent: Whether or not to announce this tempban
        """
        if client.bot:  # exclude bots
            return

        self.debug('TEMPBAN : client: %s - duration: %s - reason: %s', client, duration, reason)
        if isinstance(client, basestring):
            clients = self.clients.getByMagic(client)
            if len(clients) != 1:
                return
            else:
                client = clients[0]

        if admin:
            banduration = minutesStr(duration)
            variables = self.getMessageVariables(client=client, reason=reason, admin=admin, banduration=banduration)
            fullreason = self.getMessage('temp_banned_by', variables)
        else:
            banduration = minutesStr(duration)
            variables = self.getMessageVariables(client=client, reason=reason, banduration=banduration)
            fullreason = self.getMessage('temp_banned', variables)

        fullreason = self.stripColors(fullreason)
        reason = self.stripColors(reason)

        self.do_tempban(client, duration, reason)

        if not silent and fullreason != '':
            self.say(fullreason)

        data = {'reason': reason, 'duration': duration, 'admin': admin}
        self.queueEvent(self.getEvent("EVT_CLIENT_BAN_TEMP", data=data, client=client))

    def getMap(self):
        """
        Return the current map/level name.
        """
        return self.getCvar("host_map")['value'][0:-4]

    def getMaps(self):
        """
        Return the available maps/levels name.
        """
        mapfile = Cvar.getString(self.getCvar('mapcyclefile'))
        game_log = self.config.getpath('server', 'game_log')
        folder = game_log.rpartition('console.log')
        mapcyclefile = folder[0] + mapfile
        map_rotation = []
        self.map_cycles = {}
        self.map_cycle_no = 0
        f = open(mapcyclefile, 'r')
        for line in f:
            if len(line):
                map_rotation.append(line)
        f.close()
        return map_rotation

    def rotateMap(self):
        """
        Load the next map/level
        """
        next_map = self.getNextMap()
        if next_map:
            self.saybig('Changing to next map : %s' % next_map)
            time.sleep(1)
            self.output.write('map %s' % next_map)

    def changeMap(self, map_name, gamemode_name=''):
        """
        Load a given map/level
        Return a list of suggested map names in cases it fails to recognize the map that was provided.
        """
        map_name = self.getMapsSoundingLike(map_name)
        if not isinstance(map_name, basestring):
            return map_name
        else:
            self.saybig('Changing map to: %s - %s' % (map_name, gamemode_name))
            time.sleep(5)
            self.output.write('changelevel %s %s' % (map_name, gamemode_name))

    def checkGameMode(self, map_name, gamemode_name):
        if gamemode_name in ('hunt',):
            if map_name.find ('_hunt') == -1:
                map_name += '_hunt'
        elif gamemode_name in ('checkpoint', 'outpost'):
            if map_name.find ('_coop') == -1:
                map_name += '_coop'
        return map_name

    def getPlayerPings(self, filter_client_ids=None):
        """
        Returns a dict having players' id for keys and players' ping for values.
        """
        clients = self.queryServerInfo()
        pings = {}
        for cid, client in clients.iteritems():
            pings[cid] = client.ping
        return pings

    def getPlayerScores(self):
        """
        Returns a dict having players' id for keys and players' scores for values.
        """
        # TODO getPlayerScores if doable
        return dict()

    def inflictCustomPenalty(self, penalty_type, client, reason=None, duration=None, admin=None, data=None):
        """
        Called if b3.admin.penalizeClient() does not know a given penalty type.
        Overwrite this to add customized penalties for your game like 'slap', 'nuke',
        'mute', 'kill' or anything you want.
        /!\ This method must return True if the penalty was inflicted.
        """
        pass
        # TODO
        # inflictCustomPenalty(sm_slap sm_slay sm_votekick sm_voteban sm_voteburn sm_voteslay sm_gag sm_mute sm_silence)

    def getNextMap(self):
        """
        Return the next map in the map rotation list
        """
        if "nextmap" in self.sm_plugins:
            next_map = self.getCvar("sm_nextmap")
            return next_map
        else:
            return 'Not available, Source Mod "nextmap" plugin not loaded'

    ####################################################################################################################
    #                                                                                                                  #
    #  PARSING                                                                                                         #
    #                                                                                                                  #
    ####################################################################################################################

    def parseLine(self, line):
        """
        Parse a single line from the log file.
        """
        if line is None:
            return
        if line.startswith("mp\x08 \x08\x08 \x08"):
            line = line[8:]
        text = line.decode('UTF-8', 'replace')
        data = None

        m = re.match(RE_HL_LOG_LINE, text)
        if m:
            data = m.group('data')
        elif text.startswith("Gamerules: entering state "):
            data = text

        if data is not None:
            hfunc, param_dict = ger.getHandler(data)
            if hfunc:
                self.verbose2("calling %s%r" % (hfunc.func_name, param_dict))
                event = hfunc(self, **param_dict)
                if event:
                    self.queueEvent(event)

    ####################################################################################################################
    #                                                                                                                  #
    #  OTHER METHODS                                                                                                   #
    #                                                                                                                  #
    ####################################################################################################################

    def getClient(self, cid, guid):
        """
        Return an already connected client by searching the clients cid index.
        May return None
        """
        if guid == 'BOT':
            guid = self.botGUID(cid, guid)
        client = self.clients.getByCID(cid)
        if client:
            if client.guid != guid:
                client.disconnect()
                self.sync()
                return None
            else:
                return client
        return None

    def getClientOrCreate(self, cid, guid, name, team=None):
        """
        Return an already connected client by searching the clients cid index or create a new client.
        May return None
        """
        bot = False
        hide = False
        if guid == 'BOT':
            guid = self.botGUID(cid, guid)
            bot = True
            hide = True

        client = self.clients.getByGUID(guid)
        if client and client.cid != cid:
            self.sync()

        client = self.clients.getByCID(cid)
        if client and client.guid != guid:
            self.sync()

        client = self.clients.getByCID(cid)

        if client is None:
            client = self.clients.newClient(cid, guid=guid, name=name, bot=bot, hide=hide, team=TEAM_UNKNOWN)
            client.last_update_time = time.time()
        else:
            if name:
                client.name = name
        if team:
            parsed_team = self.getTeam(team)
            if parsed_team is not None:
                client.team = parsed_team
        return client

    def getTeam(self, team):
        """
        Convert Insurgency team id to B3 team numbers
        """
        if not team:
            return None
        elif team == "#Team_Unassigned":
            return TEAM_UNKNOWN
        elif team == "#Team_Insurgent":
            return TEAM_BLUE
        elif team == "#Team_Security":
            return TEAM_RED
        elif team == "Spectator":
            return TEAM_SPEC
        # elif team = "???": TODO: find out if there is a special team for game modes with no team like Free For All
        #     return TEAM_FREE
        else:
            self.warning("unexpected team id: %r. Please report this on the B3 forums" % team)
            return None

    def queryServerInfo(self):
        """
        Query the server for its status and refresh local data :
          self.game.sv_hostname
          self.game.mapName
        furthermore, discover connected players, refresh their ping and ip info
        finally return a dict of <cid, client>
        """
        current_clients = dict()
        rv = self.output.write("status")
        self.verbose2('Querying Server Status')
        if rv:
            self.verbose2('Status: %s' % rv)
            re_player = re.compile(r'^#\s*(?P<cid>\d+) (?:\d+) "(?P<name>.+)" (?P<guid>\S+) '
                                   r'(?P<duration>\d+:\d+) (?P<ping>\d+) (?P<loss>\S+) (?P<state>\S+) '
                                   r'(?P<rate>\d+) (?P<ip>\d+\.\d+\.\d+\.\d+):(?P<port>\d+)$')
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
                        current_clients[client.cid] = client
            self.verbose2('Current Client List: %s' % current_clients)
            return current_clients

    def getAllAvailableMaps(self):
        """
        Return the available maps for the server, even if not in the map rotation list
        This returns ALL maps on the server
        """
        re_maps = re.compile(r"^PENDING:\s+\(fs\)\s+(?P<map_name>.+)\.bsp$")
        response = []
        for line in self.output.write("maps *").split('\n'):
            m = re.match(re_maps, line)
            if m:
                response.append(m.group('map_name'))
        return response

    def getCvar(self, cvarName):
        """
        Return a CVAR from the game server.
        :param cvarName: The CVAR name
        """
        if not cvarName:
            self.warning('trying to query empty cvar %r' % cvarName)
            return None
        rv = self.output.write(cvarName)
        m = re.search(RE_CVAR, rv)
        if m:
            return Cvar(cvarName, value=m.group('value'), default=m.group('default'))
        else:
            return None

    def setCvar(self, cvarName, value):
        """
        Set a CVAR on the game server.
        :param cvarName: The CVAR name
        :param value: The CVAR value
        """
        if re.match('^[a-z0-9_.]+$', cvarName, re.I):
            self.debug('Set cvar %s = [%s]', cvarName, value)
            self.write(self.getCommand('set', name=cvarName, value=value))
        else:
            self.error('%s is not a valid cvar name', cvarName)

    def do_kick(self, client, reason=None):
        """
        Kick a client.
        :param client: The client to kick
        :param reason: The reason for the kick
        """
        if not client.cid:
            self.warning("trying to kick %s which has no slot id" % client)
        else:
            if reason:
                self.output.write('sm_kick #%s %s' % (client.cid, reason))
            else:
                self.output.write("sm_kick #%s" % client.cid)
            client.disconnect()

    def do_ban(self, client, reason=None):
        """
        Ban a client.
        :param client: The client to ban
        :param reason: The reason for the ban
        """
        # sm_addban <time> <steamid> [reason]
        if reason:
            self.output.write('sm_addban %s "%s" %s' % (0, client.guid, reason))
        else:
            self.output.write('sm_addban %s "%s"' % (0, client.guid))
        self.do_kick(client, reason)

    def do_tempban(self, client, duration=2, reason=None):
        """
        Tempban a client.
        :param client: The client to tempban
        :param duration: The tempban duration
        :param reason: The reason for the tempban
        """
        # sm_addban <time> <steamid> [reason]
        if reason:
            self.output.write('sm_addban %s "%s" %s' % (int(time2minutes(duration)), client.guid, reason))
        else:
            self.output.write('sm_addban %s "%s"' % (int(time2minutes(duration)), client.guid))
        self.do_kick(client, reason)

    def do_unban_by_steamid(self, client):
        """
        Unban a client using his GUID.
        :param client: The client to unban
        """
        # sm_unban <steamid|ip>
        self.output.write('sm_unban "%s"' % client.guid)

    def do_unban_by_ip(self, client):
        """
        Unban a client using his IP address.
        :param client: The client to unban
        """
        # sm_unban <steamid|ip>
        self.output.write('sm_unban %s' % client.ip)

    def is_sourcemod_installed(self):
        """
        Return a True if Source Mod is installed on the game server
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
        Return a dict with SourceMod plugins' name as keys and value is a tuple (index, version, author)
        """
        re_sm_plugin = re.compile(r'^(?P<index>.+) "(?P<name>.+)" \((?P<version>.+)\) by (?P<author>.+)$', re.MULTILINE)

        response = dict()
        data = self.output.write("sm plugins list")
        if data:
            for m in re.finditer(re_sm_plugin, data):
                response[m.group('name')] = (m.group('index'), m.group('version'), m.group('author'))
        return response

    def getMapsSoundingLike(self, mapname):
        """
        Return a valid mapname.
        If no exact match is found, then return close candidates as a list
        """
        supported_maps = [m.lower() for m in self.getAllAvailableMaps()]
        wanted_map = mapname.lower()
        if wanted_map in supported_maps:
            return wanted_map

        matches = getStuffSoundingLike(wanted_map, supported_maps)
        if len(matches) == 1:
            # one match, get the map id
            return matches[0]
        else:
            # multiple matches, provide suggestions
            return matches

    def botGUID(self, cid, guid):
        """
        Return a unique guid for a bot
        Otherwise all bots g=have guid = BOT
        """
        botguid = guid + str(cid)
        self.verbose2('BOT guid is %s' % botguid)
        return botguid