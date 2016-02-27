#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2010 Thomas LEVEIL <courgette@bigbrotherbot.net>
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
# 1.1.3 - make use of dict comprehension to generate map/gamemode dictionaries
# 1.1.2 - update to server version R46
#       - add DLC4 (Final Stand) map pack
# 1.1.1 - update to server version R43
#       - new server vars for "player ready" feature
# 1.1   - syntax cleanup
# 1.0.3 - rewrote import statements
# 1.0.2 - forward server event player.onDisconnect to EVT_CLIENT_DISCONNECT_REASON
# 1.0.1 - update to server version R13 that include DLC1 (China Rising) map pack
# 1.0.0 - functional parser implementation based on the BF3 parser
#       - fixed 'filter_client_ids' variable initialization
#       - fixed class attribute initialization

import b3
import b3.clients
import b3.events
import sys
import threading
import traceback

from time import sleep
from b3.parsers.frostbite2.abstractParser import AbstractParser
from b3.parsers.frostbite2.protocol import CommandFailedError
from b3.parsers.frostbite2.util import PlayerInfoBlock

__author__ = 'Courgette, ozon, Dwarfer'
__version__ = '1.1.3'

BF4_REQUIRED_VERSION = 155011

BF4_PLAYER = 0              # normal player
BF4_SPECTATOR = 1           # spectator which is not visible in the game for other player but visible as player for b3
BF4_COMMANDER = 2           # commander which is visible for other player and b3

SQUAD_NOSQUAD = 0
SQUAD_ALPHA = 1
SQUAD_BRAVO = 2
SQUAD_CHARLIE = 3
SQUAD_DELTA = 4
SQUAD_ECHO = 5
SQUAD_FOXTROT = 6
SQUAD_GOLF = 7
SQUAD_HOTEL = 8
SQUAD_INDIA = 9
SQUAD_JULIET = 10
SQUAD_KILO = 11
SQUAD_LIMA = 12
SQUAD_MIKE = 13
SQUAD_NOVEMBER = 14
SQUAD_OSCAR = 15
SQUAD_PAPA = 16
SQUAD_QUEBEC = 17
SQUAD_ROMEO = 18
SQUAD_SIERRA = 19
SQUAD_TANGO = 20
SQUAD_UNIFORM = 21
SQUAD_VICTOR = 22
SQUAD_WHISKEY = 23
SQUAD_XRAY = 24
SQUAD_YANKEE = 25
SQUAD_ZULU = 26
SQUAD_HAGGARD = 27
SQUAD_SWEETWATER = 28
SQUAD_PRESTON = 29
SQUAD_REDFORD = 30
SQUAD_FAITH = 31
SQUAD_CELESTE = 32

SQUAD_NAMES = {
    SQUAD_ALPHA: "Alpha",
    SQUAD_BRAVO: "Bravo",
    SQUAD_CHARLIE: "Charlie",
    SQUAD_DELTA: "Delta",
    SQUAD_ECHO: "Echo",
    SQUAD_FOXTROT: "Foxtrot",
    SQUAD_GOLF: "Golf",
    SQUAD_HOTEL: "Hotel",
    SQUAD_INDIA: "India",
    SQUAD_JULIET: "Juliet",
    SQUAD_KILO: "Kilo",
    SQUAD_LIMA: "Lima",
    SQUAD_MIKE: "Mike",
    SQUAD_NOVEMBER: "November",
    SQUAD_OSCAR: "Oscar",
    SQUAD_PAPA: "Papa",
    SQUAD_QUEBEC: "Quebec",
    SQUAD_ROMEO: "Romeo",
    SQUAD_SIERRA: "Sierra",
    SQUAD_TANGO: "Tango",
    SQUAD_UNIFORM: "Uniform",
    SQUAD_VICTOR: "Victor",
    SQUAD_WHISKEY: "Whiskey",
    SQUAD_XRAY: "Xray",
    SQUAD_YANKEE: "Yankee",
    SQUAD_ZULU: "Zulu",
    SQUAD_HAGGARD: "Haggard",
    SQUAD_SWEETWATER: "Sweetwater",
    SQUAD_PRESTON: "Preston",
    SQUAD_REDFORD: "Redford",
    SQUAD_FAITH: "Faith",
    SQUAD_CELESTE: "Celeste"
}

# Base game modes: dict('Engine name'='Human-readable name')
GAME_MODES_NAMES = {
    'ConquestLarge0': 'Conquest64',
    'ConquestSmall0': 'Conquest',
    'RushLarge0': 'Rush',
    'SquadDeathMatch0': 'Squad Deathmatch',
    'TeamDeathMatch0': 'Team Deathmatch',
    'Domination0': 'Domination',
    'Elimination0': 'Defuse',
    'Obliteration': 'Obliteration',
    'AirSuperiority0': 'Air Superiority',
    'CaptureTheFlag0': 'Capture the Flag',
    'CarrierAssaultSmall0': 'Carrier Assault',
    'CarrierAssaultLarge0': 'Carrier Assault64',
    'Chainlink0': 'Chain Link',
}

GAMEMODES_IDS_BY_NAME = {name.lower(): x for x, name in GAME_MODES_NAMES.items()}

# game maps: dict('Engine name'='Human-readable name')
MAP_NAME_BY_ID = {
    'MP_Abandoned': 'Zavod 311',
    'MP_Damage': 'Lancang Dam',
    'MP_Flooded': 'Flood Zone',
    'MP_Journey': 'Golmud Railway',
    'MP_Naval': 'Paracel Storm',
    'MP_Prison': 'Operation Locker',
    'MP_Resort': 'Hainan Resort',
    'MP_Siege': 'Siege of Shanghai',
    'MP_TheDish': 'Rogue Transmission',
    'MP_Tremors': 'Dawnbreaker',
    'XP0_Caspian': 'Caspian Border 2014',
    'XP0_Firestorm': 'Firestorm 2014',
    'XP0_Oman': 'Gulf Of Oman 2014',
    'XP0_Metro': 'Operation Metro 2014',
    'XP1_001': 'Silk Road',
    'XP1_002': 'Altai Range',
    'XP1_003': 'Guilin Peaks',
    'XP1_004': 'Dragon Pass',
    'XP2_001': 'Lost Islands',
    'XP2_002': 'Nansha Strike',
    'XP2_003': 'Wave Breaker',
    'XP2_004': 'Operation Mortar',
    'XP3_MarketPl': 'Pearl Market',
    'XP3_Prpganda': 'Propaganda',
    'XP3_UrbanGdn': 'Lumphini Garden',
    'XP3_WtrFront': 'Sunken Dragon',
    'XP4_Arctic': 'Operation Whiteout',
    'XP4_SubBase': 'Hammerhead',
    'XP4_Titan': 'Hangar 21',
    'XP4_WlkrFtry': 'Giants Of Karelia',
}

MAP_ID_BY_NAME = {name.lower(): x for x, name in MAP_NAME_BY_ID.items()}

GAME_MODES_BY_MAP_ID = {
    'MP_Abandoned': (
        'ConquestLarge0',
        'ConquestSmall0',
        'Elimination0',
        'Obliteration',
        'RushLarge0',
        'TeamDeathMatch0',
        'SquadDeathMatch0',
        'Domination0'),
    'MP_Damage': (
        'ConquestLarge0',
        'ConquestSmall0',
        'Elimination0',
        'Obliteration',
        'RushLarge0',
        'TeamDeathMatch0',
        'SquadDeathMatch0',
        'Domination0'),
    'MP_Flooded': (
        'ConquestLarge0',
        'ConquestSmall0',
        'Elimination0',
        'Obliteration',
        'RushLarge0',
        'TeamDeathMatch0',
        'SquadDeathMatch0',
        'Domination0'),
    'MP_Journey': (
        'ConquestLarge0',
        'ConquestSmall0',
        'Elimination0',
        'Obliteration',
        'RushLarge0',
        'TeamDeathMatch0',
        'SquadDeathMatch0',
        'Domination0'),
    'MP_Naval': (
        'ConquestLarge0',
        'ConquestSmall0',
        'Elimination0',
        'Obliteration',
        'RushLarge0',
        'TeamDeathMatch0',
        'SquadDeathMatch0',
        'Domination0'),
    'MP_Prison': (
        'ConquestLarge0',
        'ConquestSmall0',
        'Elimination0',
        'Obliteration',
        'RushLarge0',
        'TeamDeathMatch0',
        'SquadDeathMatch0',
        'Domination0'),
    'MP_Resort': (
        'ConquestLarge0',
        'ConquestSmall0',
        'Elimination0',
        'Obliteration',
        'RushLarge0',
        'TeamDeathMatch0',
        'SquadDeathMatch0',
        'Domination0'),
    'MP_Siege': (
        'ConquestLarge0',
        'ConquestSmall0',
        'Elimination0',
        'Obliteration',
        'RushLarge0',
        'TeamDeathMatch0',
        'SquadDeathMatch0',
        'Domination0'),
    'MP_TheDish': (
        'ConquestLarge0',
        'ConquestSmall0',
        'Elimination0',
        'Obliteration',
        'RushLarge0',
        'TeamDeathMatch0',
        'SquadDeathMatch0',
        'Domination0'),
    'MP_Tremors': (
        'ConquestLarge0',
        'ConquestSmall0',
        'Elimination0',
        'Obliteration',
        'RushLarge0',
        'TeamDeathMatch0',
        'SquadDeathMatch0',
        'Domination0'),
    'XP0_Caspian': (
        'ConquestLarge0',
        'ConquestSmall0',
        'Elimination0',
        'Obliteration',
        'RushLarge0',
        'TeamDeathMatch0',
        'SquadDeathMatch0',
        'Domination0',
        'CaptureTheFlag0'),
    'XP0_Firestorm': (
        'ConquestLarge0',
        'ConquestSmall0',
        'Elimination0',
        'Obliteration',
        'RushLarge0',
        'TeamDeathMatch0',
        'SquadDeathMatch0',
        'Domination0',
        'CaptureTheFlag0'),
    'XP0_Oman': (
        'ConquestLarge0',
        'ConquestSmall0',
        'Elimination0',
        'Obliteration',
        'RushLarge0',
        'TeamDeathMatch0',
        'SquadDeathMatch0',
        'Domination0',
        'CaptureTheFlag0'),
    'XP0_Metro': (
        'ConquestLarge0',
        'ConquestSmall0',
        'Elimination0',
        'Obliteration',
        'RushLarge0',
        'TeamDeathMatch0',
        'SquadDeathMatch0',
        'Domination0',
        'CaptureTheFlag0'),
    'XP1_001': (
        'ConquestLarge0',
        'ConquestSmall0',
        'Elimination0',
        'Obliteration',
        'RushLarge0',
        'TeamDeathMatch0',
        'SquadDeathMatch0',
        'Domination0',
        'AirSuperiority0'),
    'XP1_002': (
        'ConquestLarge0',
        'ConquestSmall0',
        'Elimination0',
        'Obliteration',
        'RushLarge0',
        'TeamDeathMatch0',
        'SquadDeathMatch0',
        'Domination0',
        'AirSuperiority0'),
    'XP1_003': (
        'ConquestLarge0',
        'ConquestSmall0',
        'Elimination0',
        'Obliteration',
        'RushLarge0',
        'TeamDeathMatch0',
        'SquadDeathMatch0',
        'Domination0',
        'AirSuperiority0'),
    'XP1_004': (
        'ConquestLarge0',
        'ConquestSmall0',
        'Elimination0',
        'Obliteration',
        'RushLarge0',
        'TeamDeathMatch0',
        'SquadDeathMatch0',
        'Domination0',
        'AirSuperiority0'),
    'XP2_001': (
        'ConquestLarge0',
        'ConquestSmall0',
        'Elimination0',
        'Obliteration',
        'RushLarge0',
        'TeamDeathMatch0',
        'SquadDeathMatch0',
        'Domination0',
        'CaptureTheFlag0',
        'CarrierAssaultSmall0',
        'CarrierAssaultLarge0'),
    'XP2_002': (
        'ConquestLarge0',
        'ConquestSmall0',
        'Elimination0',
        'Obliteration',
        'RushLarge0',
        'TeamDeathMatch0',
        'SquadDeathMatch0',
        'Domination0',
        'CaptureTheFlag0',
        'CarrierAssaultSmall0',
        'CarrierAssaultLarge0'),
    'XP2_003': (
        'ConquestLarge0',
        'ConquestSmall0',
        'Elimination0',
        'Obliteration',
        'RushLarge0',
        'TeamDeathMatch0',
        'SquadDeathMatch0',
        'Domination0',
        'CaptureTheFlag0',
        'CarrierAssaultSmall0',
        'CarrierAssaultLarge0'),
    'XP2_004': (
        'ConquestLarge0',
        'ConquestSmall0',
        'Elimination0',
        'Obliteration',
        'RushLarge0',
        'TeamDeathMatch0',
        'SquadDeathMatch0',
        'Domination0',
        'CaptureTheFlag0',
        'CarrierAssaultSmall0',
        'CarrierAssaultLarge0'),
    'XP3_MarketPl': (
        'ConquestLarge0',
        'ConquestSmall0',
        'Elimination0',
        'Obliteration',
        'RushLarge0',
        'TeamDeathMatch0',
        'SquadDeathMatch0',
        'Domination0',
        'CaptureTheFlag0',
        'Chainlink0'),
    'XP3_Prpganda': (
        'ConquestLarge0',
        'ConquestSmall0',
        'Elimination0',
        'Obliteration',
        'RushLarge0',
        'TeamDeathMatch0',
        'SquadDeathMatch0',
        'Domination0',
        'CaptureTheFlag0',
        'Chainlink0'),
    'XP3_UrbanGdn': (
        'ConquestLarge0',
        'ConquestSmall0',
        'Elimination0',
        'Obliteration',
        'RushLarge0',
        'TeamDeathMatch0',
        'SquadDeathMatch0',
        'Domination0',
        'CaptureTheFlag0',
        'Chainlink0'),
    'XP3_WtrFront': (
        'ConquestLarge0',
        'ConquestSmall0',
        'Elimination0',
        'Obliteration',
        'RushLarge0',
        'TeamDeathMatch0',
        'SquadDeathMatch0',
        'Domination0',
        'CaptureTheFlag0',
        'Chainlink0'),
    'XP4_Arctic': (
        'ConquestLarge0',
        'ConquestSmall0',
        'Elimination0',
        'Obliteration',
        'RushLarge0',
        'TeamDeathMatch0',
        'SquadDeathMatch0',
        'Domination0',
        'CaptureTheFlag0'),
    'XP4_SubBase': (
        'ConquestLarge0',
        'ConquestSmall0',
        'Elimination0',
        'Obliteration',
        'RushLarge0',
        'TeamDeathMatch0',
        'SquadDeathMatch0',
        'Domination0',
        'CaptureTheFlag0'),
    'XP4_Titan': (
        'ConquestLarge0',
        'ConquestSmall0',
        'Elimination0',
        'Obliteration',
        'RushLarge0',
        'TeamDeathMatch0',
        'SquadDeathMatch0',
        'Domination0',
        'CaptureTheFlag0'),
    'XP4_WlkrFtry': (
        'ConquestLarge0',
        'ConquestSmall0',
        'Elimination0',
        'Obliteration',
        'RushLarge0',
        'TeamDeathMatch0',
        'SquadDeathMatch0',
        'Domination0',
        'CaptureTheFlag0'),
}

COMROSE_CHAT_NAME_BY_ID = {
    'ID_CHAT_ATTACK/DEFEND': 'ATTACK/DEFEND',
    'ID_CHAT_AFFIRMATIVE': 'AFFIRMATIVE',
    'ID_CHAT_NEGATIVE': 'NEGATIVE',
    'ID_CHAT_THANKS': 'THANK YOU',
    'ID_CHAT_GOGOGO': 'GO GO GO',
    'ID_CHAT_GET_IN': 'GET IN',
    'ID_CHAT_GET_OUT': 'GET OUT',
    'ID_CHAT_REQUEST_MEDIC': 'NEED MEDIC',
    'ID_CHAT_REQUEST_AMMO': 'NEED AMMO',
    'ID_CHAT_REQUEST_RIDE': 'NEED A RIDE',
    'ID_CHAT_REQUEST_REPAIRS': 'NEED REPAIRS',
    'ID_CHAT_REQUEST_ORDER': 'REQUEST ORDER',
    'ID_CHAT_SORRY': 'SORRY',
}


class Bf4Parser(AbstractParser):

    gameName = 'bf4'

    _gamePort = None

    _gameServerVars = (
        '3dSpotting',               # <bool>  Set if spotted targets are visible in the 3d-world
        '3pCam',                    # <bool>  Set if allowing to toggle to third person vehicle cameras
        'alwaysAllowSpectators',    # <bool>  Set whether spectators need to be in the spectator list before joining
        'autoBalance',              # <bool>  Set if the server should autobalance
        'bulletDamage',             # <modifier: percent>  Set bullet damage scale factor
        'commander',                # <bool>  Set if commander is allowed or not on the game server
        'crossHair',                # <bool>  Set if crosshair for all weapons is enabled
        'forceReloadWholeMags',     # <bool>  Set hardcore reload on or off
        'friendlyFire',             # <bool>  Set if the server should allow team damage
        'gameModeCounter',          # <modifier: integer> Set scale factor for number of tickets to end round
        'gamePassword',             # <password>  Set the game password for the server
        'hitIndicatorsEnabled',     # <bool>  Set if hit indicators are enabled or not
        'hud',                      # <bool>  Set if HUD is enabled
        'idleBanRounds',            # <bool>  Set how many rounds idle timeout should ban (if at all)
        'idleTimeout',              # <time>  Set idle timeout
        'killCam',                  # <bool>  Set if killcam is enabled
        'maxPlayers',               # <numPlayers>  Set desired maximum number of players
        'maxSpectators',            # <numSpectators>  Set desired maximum number of spectators
        'miniMap',                  # <bool>  Set if minimap is enabled
        'miniMapSpotting',          # <bool>  Set if spotted targets are visible on the minimap
        'mpExperience',             # <experience>  Set the MP Experience of the game server
        'nameTag',                  # <bool>  Set if nametags should be displayed
        'onlySquadLeaderSpawn',     # <bool>  Set if players can only spawn on their squad leader
        'playerRespawnTime',        # <modifier: percent>  Set player respawn time scale factor
        'regenerateHealth',         # <bool>  Set if health regeneration should be active
        'roundLockdownCountdown',   # <time>  Set the duration of pre-round
        'roundRestartPlayerCount',  # <numPlayers> Set minimum numbers of players to go from in-round to warm-up
        'roundStartPlayerCount',    # <numPlayers>  Set minimum numbers of players to go from warm-up to pre-/inround
        'roundTimeLimit',           # <modifier: percent>  Set percentage of the default time limit value
        'serverDescription',        # <description>  Set server description
        'serverMessage',            # <message>  Set the server welcome message
        'serverName',               # <name>  Set the server name
        'serverType',               # <type>  Set the server type: Official, Ranked, Unranked or Private
        'soldierHealth',            # <modifier: percent>  Set soldier max health scale factor
        'teamFactionOverride',      # Overwrites team factions
        'teamKillCountForKick',     # <count>  Set number of teamkills allowed during a round
        'teamKillKickForBan',       # <count>  Set number of team-kill kicks that will lead to permaban
        'teamKillValueDecreasePerSecond',   # <count>  Set kill-value decrease per second
        'teamKillValueForKick',     # <count>  Set max kill-value allowed for a player before he/she is kicked
        'teamKillValueIncrease',    # <count>  Set kill-value increase for a teamkill
        'vehicleSpawnAllowed',      # <bool>  Set whether vehicles should spawn in-game
        'vehicleSpawnDelay',        # <modifier: percent>  Set vehicle spawn delay scale factor
        'preset',                   # allows you to set the server to either normal, hardcore infantry or custom
        'unlockMode'                # which set of unlocks is available on an unranked server (all/common/stats/none)
        'ticketBleedRate'           # controls the rate of tickets drop
        'roundPlayersReadyBypassTimer'  # <time> amount of seconds after which the ready screen is bypassed
        'roundPlayersReadyMinCount'     # <count> minimum number of players per team which have to confirm ready state
        'roundPlayersReadyPercent'  # <modifier:percent>
    )

    # gamemodes aliases {alias: actual game mode name}
    _gamemode_aliases = {
        'cq': 'conquest',
        'cq64': 'conquest64',
        'tdm': 'team deathmatch',
        'sqdm': 'squad deathmatch',
        'dom': 'domination',
        'elm': 'defuse',
        'obl': 'obliteration',
        'rush': 'rush',
        'ctf': 'capture the flag',
        'ca': 'carrier assault',
        'ca64': 'carrier assault64',
        'cl': 'chain link',
    }

    ####################################################################################################################
    #                                                                                                                  #
    #   PARSER INITIALIZATION                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    def __new__(cls, *args, **kwargs):
        Bf4Parser.patch_b3_Client_properties()
        return AbstractParser.__new__(cls)

    def startup(self):
        """
        Called after the parser is created before run().
        """
        AbstractParser.startup(self)

        # create event for comrose actions
        self.Events.createEvent('EVT_CLIENT_COMROSE', 'Client Comrose')
        self.Events.createEvent('EVT_CLIENT_DISCONNECT_REASON', 'Client disconnected')

        # create the 'Server' client
        self.clients.newClient('Server', guid='Server', name='Server', hide=True,
                               pbid='Server', team=b3.TEAM_UNKNOWN, squad=None)

        self.verbose('Gametype: %s, Map: %s' %(self.game.gameType, self.game.mapName))

    def pluginsStarted(self):
        """
        Called after the parser loaded and started all plugins.
        """
        AbstractParser.pluginsStarted(self)
        self.info('Connecting all players...')
        plist = self.getPlayerList()
        for cid, p in plist.iteritems():
            self.getClient(cid)

    ####################################################################################################################
    #                                                                                                                  #
    #   FROSTBITE2 EVENTS HANDLERS                                                                                     #
    #                                                                                                                  #
    ####################################################################################################################

    def OnPlayerChat(self, action, data):
        """
        player.onChat <source soldier name: string> <text: string> <target players: player subset>

        Effect: Player with name <source soldier name> (or the server, or the
            server admin) has sent chat message <text> to <target players>

        Comment: If <source soldier name> is "Server", then the message was sent
            from the server rather than from an actual player
        """
        client = self.getClient(data[0])
        if client is None:
            self.warning("Could not get client: %s" % traceback.extract_tb(sys.exc_info()[2]))
            return
        if client.cid == 'Server':
            # ignore chat events for Server
            return
        text = data[1]

        if text in COMROSE_CHAT_NAME_BY_ID:
            return self.getEvent('EVT_CLIENT_COMROSE', text, client, data[2] + ' ' + data[3])

        # existing commands can be prefixed with a '/' instead of usual prefixes
        cmdPrefix = '!'
        cmd_prefixes = (cmdPrefix, '@', '&')
        admin_plugin = self.getPlugin('admin')
        if admin_plugin:
            cmdPrefix = admin_plugin.cmdPrefix
            cmd_prefixes = (cmdPrefix, admin_plugin.cmdPrefixLoud, admin_plugin.cmdPrefixBig)

        cmd_name = text[1:].split(' ', 1)[0].lower()
        if len(text) >= 2 and text[0] == '/':
            if text[1] in cmd_prefixes:
                text = text[1:]
            elif cmd_name in admin_plugin._commands:
                text = cmdPrefix + text[1:]

        if 'team' in data[2]:
            eventkey = 'EVT_CLIENT_TEAM_SAY'
        elif 'squad' in data[2]:
            eventkey = 'EVT_CLIENT_SQUAD_SAY'
        else:
            eventkey = 'EVT_CLIENT_SAY'

        return self.getEvent(eventkey, text, client)

    def OnPlayerTeamchange(self, _, data):
        """
        player.onTeamChange <soldier name: player name> <team: Team ID> <squad: Squad ID>
        Effect: Player might have changed team
        """
        # ['player.switchTeam', 'Cucurbitaceae', '1', '0']
        client = self.getClient(data[0])
        if client:
            client.squad = int(data[2])
            client.teamId = int(data[1])
            client.team = self.getTeam(data[1]) # .team setter will send team change event

    def OnPlayerSquadchange(self, _, data):
        """
        player.onSquadChange <soldier name: player name> <team: Team ID> <squad: Squad ID>    
        
        Effect: Player might have changed squad
        NOTE: this event also happens after a player left the game
        """
        client = self.clients.getByCID(data[0])
        if client:
            previous_squad = client.squad
            client.squad = int(data[2])
            client.teamId = int(data[1])
            client.team = self.getTeam(data[1]) # .team setter will send team change event
            if client.squad != previous_squad:
                return self.getEvent('EVT_CLIENT_SQUAD_CHANGE', data[1:], client)

    def OnPlayerJoin(self, action, data):
        """
        player.onJoin <soldier name: string> <id : EAID>
        """
        # we receive this event very early and even before the game client starts to connect to the game server.
        # In some occasions, the game client fails to properly connect and the game server then fails to send
        # us a player.onLeave event resulting in B3 thinking the player is connected while it is not.
        # The fix is to ignore this event. If the game client successfully connect, then we'll receive other
        # events like player.onTeamChange or even a event from punkbuster which will create the Client object.
        if self._waiting_for_round_start:
            self._OnServerLevelstarted(action=None, data=None)

    def OnPlayerDisconnect(self, _, data):
        """
        player.onDisconnect <soldier name: string> <reason: string>
        """
        # We receive this event if a player disconnects from the game. If a player lave the game, the reason is empty.
        # The "reason" may contain an error id or a kick/ban reason.
        # Example from server:['player.onDisconnect', 'O2ON', 'PLAYER_CONN_LOST']
        client = self.getClient(data[0])
        self.queueEvent(self.getEvent('EVT_CLIENT_DISCONNECT_REASON', data=data[1], client=client))

    def _OnServerLevelstarted(self, action, data):
        """
        Event server.onLevelStarted was used to be sent in Frostbite1. Unfortunately it does not exists anymore
        in Frostbite2.
        Instead we call this method from OnPlayerSpawn and maintain a flag which tells if we need to fire the
        EVT_GAME_ROUND_START event
        """
        if self._waiting_for_round_start:
            # prevents that EVT_GAME_ROUND_START is fired if the minimum player count is  not yet reached.
            if len(self.getPlayerList()) >= self.getCvar('roundStartPlayerCount').getInt():
                self._waiting_for_round_start = False
                # as the game server provides us the exact round number in OnServerLoadinglevel()
                # hence we need to deduct one to compensate?
                # we'll still leave the call here since it provides us self.game.roundTime()
                # next function call will increase roundcount by one, this is not wanted
                correct_rounds_value = self.game.rounds
                threading.Thread(target=self._startRound).start()
                self.game.rounds = correct_rounds_value
                self.queueEvent(self.getEvent('EVT_GAME_ROUND_START', self.game))

    ####################################################################################################################
    #                                                                                                                  #
    #   B3 PARSER INTERFACE IMPLEMENTATION                                                                             #
    #                                                                                                                  #
    ####################################################################################################################

    def getPlayerPings(self, filter_client_ids=None):
        """
        Ask the server for a given client's pings
        :param filter_client_ids: If filter_client_id is an iterable, only return values for the given client ids.
        """
        pings = {}
        if filter_client_ids is None:
            filter_client_ids = []

        try:
            player_info_block = PlayerInfoBlock(self.write(('admin.listPlayers', 'all')))
            for player in player_info_block:
                if player['name'] in filter_client_ids or len(filter_client_ids) == 0:
                    pings[player['name']] = int(player['ping'])
        except (ValueError, TypeError):
            pass  # continue if the ping value is empty
        except Exception, err:
            self.error('Unable to retrieve pings from player list', exc_info=err)
        return pings

    ####################################################################################################################
    #                                                                                                                  #
    #   OTHER METHODS                                                                                                  #
    #                                                                                                                  #
    ####################################################################################################################

    def checkVersion(self):
        version = self.output.write('version')
        self.info('Server version : %s' % version)
        if version[0] != 'BF4':
            raise Exception('the BF4 parser can only work with Battlefield 4')
        if int(version[1]) < BF4_REQUIRED_VERSION:
            raise Exception("the BF4 parser can only work with Battlefield 4 server version %s and above. "
                            "You are trying to connect to %s v%s" % (BF4_REQUIRED_VERSION, version[0], version[1]))

    def getClient(self, cid, guid=None):
        """
        Get a connected client from storage or create it
        B3 CID   <--> character name
        B3 GUID  <--> EA_guid
        """
        client = None
        if guid:
            # try to get the client from the storage of already authed clients by guid
            client = self.clients.getByGUID(guid)
        if not client:
            # try to get the client from the storage of already authed clients by name
            client = self.clients.getByCID(cid)
        if not client:
            if cid == 'Server':
                return self.clients.newClient('Server', guid='Server', name='Server', hide=True,
                                              pbid='Server', team=b3.TEAM_UNKNOWN, teamId=None, squadId=None)
            if guid:
                client = self.clients.newClient(cid, guid=guid, name=cid, team=b3.TEAM_UNKNOWN, teamId=None, squad=None)
            else:
                # must be the first time we see this client
                # query client info
                words = self.write(('admin.listPlayers', 'player', cid))
                pib = PlayerInfoBlock(words)
                if not len(pib):
                    self.debug('no such client found')
                    return None
                p = pib[0]
                if 'guid' in p:
                    client = self.clients.newClient(p['name'], guid=p['guid'], name=p['name'],
                                                    team=self.getTeam(p['teamId'], p.get('type')),
                                                    teamId=int(p['teamId']), squad=p['squadId'], data=p)

                    self.queueEvent(self.getEvent('EVT_CLIENT_JOIN', data=p, client=client))

        return client

    def getHardName(self, mapname):
        """
        Change real name to level name.
        """
        mapname = mapname.lower()
        try:
            return MAP_ID_BY_NAME[mapname]
        except KeyError:
            self.warning('unknown level name \'%s\': please make sure you have entered a valid mapname' % mapname)
            return mapname

    def getEasyName(self, mapname):
        """
        Change level name to real name.
        """
        try:
            return MAP_NAME_BY_ID[mapname]
        except KeyError:
            self.warning('unknown level name \'%s\': please report this on B3 forums' % mapname)
            return mapname

    def getGameMode(self, gamemode_id):
        """
        Convert game mode ID into human friendly name.
        """
        if gamemode_id in GAME_MODES_NAMES:
            return GAME_MODES_NAMES[gamemode_id]
        else:
            self.warning('unknown gamemode \"%s\"' % gamemode_id)
            # fallback by sending gamemode id
            return gamemode_id

    def getGameModeId(self, gamemode_name):
        """
        Get gamemode id by name.
        """
        n = gamemode_name.lower()
        if n in GAMEMODES_IDS_BY_NAME:
            return GAMEMODES_IDS_BY_NAME[n]
        else:
            self.warning("unknown gamemode name: %s" % gamemode_name)
            # fallback by sending gamemode id
            return gamemode_name

    def getSupportedMapIds(self):
        """
        Return a list of supported levels for the current game mod.
        """
        # TODO : remove this method once the method on from AbstractParser is working
        return MAP_NAME_BY_ID.keys()

    def getSupportedGameModesByMapId(self, map_id):
        """
        Return a list of supported game modes for the given map id.
        """
        return GAME_MODES_BY_MAP_ID[map_id]

    def getServerVars(self):
        """
        Update the game property from server fresh data.
        """
        def get_cvar(cvar, cvar_type='string'):
            """
            Helper function to query cvar from the server.
            """
            _cvar = self.getCvar(cvar)
            if _cvar:
                if cvar_type == 'string':
                    return _cvar.getString()
                elif cvar_type == 'bool':
                    return _cvar.getBoolean()
                elif cvar_type == 'int':
                    return _cvar.getInt()
                elif cvar_type == 'float':
                    return _cvar.getFloat()

        self.game['3dSpotting'] = get_cvar('3dSpotting', 'bool')
        self.game['3pCam'] = get_cvar('3pCam', 'bool')
        self.game['alwaysAllowSpectators'] = get_cvar('alwaysAllowSpectators', 'bool')
        self.game['autoBalance'] = get_cvar('autoBalance', 'bool')
        self.game['bulletDamage'] = get_cvar('bulletDamage', 'int')
        self.game['commander'] = get_cvar('commander', 'bool')
        self.game['crossHair'] = get_cvar('crossHair', 'bool')
        self.game['forceReloadWholeMags'] = get_cvar('forceReloadWholeMags', 'bool')
        self.game['friendlyFire'] = get_cvar('friendlyFire', 'bool')
        self.game['gameModeCounter'] = get_cvar('gameModeCounter', 'int')
        self.game['gamePassword'] = get_cvar('gamePassword')
        self.game['hitIndicatorsEnabled'] = get_cvar('hitIndicatorsEnabled', 'bool')
        self.game['hud'] = get_cvar('hud', 'bool')
        self.game['idleBanRounds'] = get_cvar('idleBanRounds', 'int')
        self.game['idleTimeout'] = get_cvar('idleTimeout', 'int')
        self.game['killCam'] = get_cvar('killCam', 'bool')
        self.game['maxPlayers'] = get_cvar('maxPlayers', 'int')
        self.game['maxSpectators'] = get_cvar('maxSpectators', 'int')
        self.game['miniMap'] = get_cvar('miniMap', 'bool')
        self.game['miniMapSpotting'] = get_cvar('miniMapSpotting', 'bool')
        self.game['mpExperience'] = get_cvar('mpExperience')
        self.game['nameTag'] = get_cvar('nameTag', 'bool')
        self.game['onlySquadLeaderSpawn'] = get_cvar('onlySquadLeaderSpawn', 'bool')
        self.game['playerRespawnTime'] = get_cvar('playerRespawnTime', 'int')
        self.game['regenerateHealth'] = get_cvar('regenerateHealth', 'bool')
        self.game['roundLockdownCountdown'] = get_cvar('roundLockdownCountdown', 'int')
        self.game['roundRestartPlayerCount'] = get_cvar('roundRestartPlayerCount', 'int')
        self.game['roundStartPlayerCount'] = get_cvar('roundStartPlayerCount', 'int')
        self.game['roundTimeLimit'] = get_cvar('roundTimeLimit', 'int')
        self.game['serverDescription'] = get_cvar('serverDescription')
        self.game['serverMessage'] = get_cvar('serverMessage')
        self.game['serverName'] = get_cvar('serverName')
        self.game['serverType'] = get_cvar('serverType')
        self.game['soldierHealth'] = get_cvar('soldierHealth', 'int')
        self.game['teamFactionOverride'] = get_cvar('teamFactionOverride', 'string')
        self.game['teamKillCountForKick'] = get_cvar('teamKillCountForKick', 'int')
        self.game['teamKillKickForBan'] = get_cvar('teamKillKickForBan', 'int')
        self.game['teamKillValueDecreasePerSecond'] = get_cvar('teamKillValueDecreasePerSecond', 'float')
        self.game['teamKillValueForKick'] = get_cvar('teamKillValueForKick', 'float')
        self.game['teamKillValueIncrease'] = get_cvar('teamKillValueIncrease', 'float')
        self.game['vehicleSpawnAllowed'] = get_cvar('vehicleSpawnAllowed', 'bool')
        self.game['vehicleSpawnDelay'] = get_cvar('vehicleSpawnDelay', 'int')
        self.game['preset'] = get_cvar('preset')
        self.game['unlockMode'] = get_cvar('unlockMode')
        self.game['ticketBleedRate'] = get_cvar('ticketBleedRate', 'int')

        self.game.timeLimit = self.game.gameModeCounter
        self.game.fragLimit = self.game.gameModeCounter
        self.game.captureLimit = self.game.gameModeCounter

    def getServerInfo(self):
        """
        Query server info, update self.game and return query results
        Response: OK,serverName,numPlayers,maxPlayers,level,gamemode,[teamscores],isRanked,hasPunkbuster,hasPassword,serverUptime,roundTime
        The first number in the [teamscore] component I listed is numTeams, followed by the score or ticket count for each team (0-4 items), 
        then the targetScore. (e.g. in TDM/SQDM this is the number of kills to win)
        So when you start a Squad Deathmatch round with 50 kills needed to win, it will look like this:
        4,0,0,0,0,50
        """
        data = self.write(('serverInfo',))
        data2 = Bf4Parser.decodeServerinfo(data)
        self.debug("Decoded server info : %r" % data2)
        self.game.sv_hostname = data2['serverName']
        self.game.sv_maxclients = int(data2['maxPlayers'])
        self.game.mapName = data2['level']
        self.game.gameType = data2['gamemode']
        if 'gameIpAndPort' in data2 and data2['gameIpAndPort']:
            try:
                self._publicIp, self._gamePort = data2['gameIpAndPort'].split(':')
            except ValueError:
                pass
        self.game.serverinfo = data2
        return data

    def getTeam(self, team, type_id=None):
        """
        Convert team numbers to B3 team numbers
        :param team the team number as sent by the BF4 server
        :param type_id the type number as sent by the BF4 server - Commander / player / spectator
        """
        team = int(team)
        if type_id and int(type_id) == BF4_SPECTATOR:
            return b3.TEAM_SPEC
        elif team == 1:
            return b3.TEAM_RED
        elif team == 2:
            return b3.TEAM_BLUE
        elif team == 0:
            return b3.TEAM_SPEC
        else:
            return b3.TEAM_UNKNOWN

    def getMap(self):
        """
        Return the current level name (not easy map name).
        """
        # First, we try to get the map name from the server.
        # If this fails, we use the old method and get the map name from the server vars.
        try:
            return self.write(('currentLevel',))[0]
        except CommandFailedError, err:
            self.warning(err)
            self.getServerInfo()
            return self.game.mapName

    @staticmethod
    def decodeServerinfo(data):
        """
        <serverName: string>
        <current playercount: integer>
        <effective max playercount: integer>
        <current gamemode: string>
        <current map: string>
        <roundsPlayed: integer>
        <roundsTotal: string>
        <scores: team scores>
        <onlineState: online state>
        <ranked: boolean>
        <punkBuster: boolean>
        <hasGamePassword: boolean>
        <serverUpTime: seconds>
        <roundTime: seconds>
        <gameIpAndPort: IpPortPair>
        <punkBusterVersion: string>
        <joinQueueEnabled: boolean>
        <region: string>
        <closestPingSite: string>
        <country: string>
        <matchMakingEnabled: boolean>
        <blazePlayerCount: integer>
        <blazeGameState: string>
        ['BigBrotherBot #2', '0', '16', 'ConquestLarge0', 'MP_012', '0', '2', '2', '300', '300', '0', '', 'true', 'true', 'false', '5148', '455']
        """
        numOfTeams = 0
        if data[7] != '':
            numOfTeams = int(data[7])

        response = {
            'serverName': data[0],
            'numPlayers': data[1],
            'maxPlayers': data[2],
            'gamemode': data[3],
            'level': data[4],
            'roundsPlayed': data[5],
            'roundsTotal': data[6],
            'numTeams': data[7],
            # depending on numTeams, there might be between 0 and 4 team scores here
            'team1score': None,
            'team2score': None,
            'team3score': None,
            'team4score': None,
            'targetScore': data[7 + numOfTeams + 1],
            'onlineState': data[7 + numOfTeams + 2],
            'isRanked': data[7 + numOfTeams + 3],
            'hasPunkbuster': data[7 + numOfTeams + 4],
            'hasPassword': data[7 + numOfTeams + 5],
            'serverUptime': data[7 + numOfTeams + 6],
            'roundTime': data[7 + numOfTeams + 7],
            'gameIpAndPort': None,
            'punkBusterVersion': None,
            'joinQueueEnabled': None,
            'region': None,
            'closestPingSite': None,
            'country': None,
            #'matchMakingEnabled': None,
            'blazePlayerCount': None,
            'blazeGameState': None,
        }

        if numOfTeams >= 1:
            response['team1score'] = data[8]
        if numOfTeams >= 2:
            response['team2score'] = data[9]
        if numOfTeams >= 3:
            response['team3score'] = data[10]
        if numOfTeams == 4:
            response['team4score'] = data[11]

        new_info = ('gameIpAndPort', 'punkBusterVersion', 'joinQueueEnabled', 'region',
                    'closestPingSite', 'country', 'blazePlayerCount', 'blazeGameState')

        start_index = 7 + numOfTeams + 8
        for i, n in zip(range(start_index, start_index + len(new_info)), new_info):
            try:
                response[n] = data[i]
            except IndexError:
                pass

        return response

    @staticmethod
    def patch_b3_Client_properties():
        """
        Add some properties to the Client Object.
        """
        def isAlive(self):
            """
            Returns whether the player is alive or not.
            """
            # True: player is alive/spawned
            # False: player is death or not spawned
            # None: BF$ server responded with an error or unexpected value
            _player_name = self.name
            try:
                _response = self.console.write(('player.isAlive', _player_name))
                if _response:
                    if _response[0] == 'true':
                        return True
                    elif _response[0] == 'false':
                        return False
            except IndexError:
                pass
            except CommandFailedError, err:
                if err.message[0] == 'InvalidPlayerName':
                    pass
                else:
                    raise Exception(err)
            except Exception, err:
                self.console.error("Could not get player state for player %s: %s" % (_player_name, err), exc_info=err)

        def getPlayerState(self):
            _state = b3.STATE_UNKNOWN
            _isAlive = self.isAlive()
            if _isAlive:
                _state = b3.STATE_ALIVE
            elif _isAlive is False:
                _state = b3.STATE_DEAD
            return _state

        def setPlayerState(self, v):
            # silently prevents Client.state from being set.
            # The Client.state value is determined by querying the BF4 server through rcon. See getPlayerState
            pass

        def _get_player_type(self):
            """
            Queries the type of player from the server.
            """
            _player_name = self.name
            try:
                _player_info_block = PlayerInfoBlock(self.console.write(('admin.listPlayers', 'player', _player_name)))
                return int(_player_info_block[0]['type'])
            except Exception, err:
                self.console.error("Could not get player_type for player %s: %s" % (self.name, err), exc_info=err)

        def get_player_type(self):
            return self._get_player_type()

        def set_player_type(self, ptype):
            pass

        def get_commander_state(self):
            return self.player_type == BF4_COMMANDER

        def set_commander_state(self):
            # silently prevents Client.is_commander from being set.
            # The Client.is_commander value is determined from Client.type
            pass

        b3.clients.Client.isAlive = isAlive
        b3.clients.Client.state = property(getPlayerState, setPlayerState)
        b3.clients.Client._get_player_type = _get_player_type
        b3.clients.Client.player_type = property(get_player_type, set_player_type)
        b3.clients.Client.is_commander = property(get_commander_state, set_commander_state)

    def _startRound(self):
        # respect var.roundLockdownCountdown
        roundLockdownCountdown = self.getCvar('roundLockdownCountdown').getInt()
        sleep(roundLockdownCountdown)
        self.game.startRound()