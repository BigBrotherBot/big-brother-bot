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
# 0.1    - functional parser but BF3 admin protocol is not fully implemented on the BF3 side. See TODOs
# 1.0    - update parser for BF3 R20
# 1.1    - reflects changes in AbstractParser and refactor the class by moving some of the code to AbstractParser
# 1.2    - reflects changes in AbstractParser due to BF3 server R21 release
# 1.3    - BF3 server R24 changes
# 1.4    - add available gamemodes by map
#        - check minimum required BF3 server version on startup
#        - fix issue from 1.3 that made impossible to use commands related to Close Quarter maps
# 1.5    - add new maps and gamemode from DLC "Armored Kill"
# 1.7    - add new maps and gamemode from DLC "Aftermath"
# 1.8    - add GUNMASTER_WEAPONS_PRESET_BY_INDEX and GUNMASTER_WEAPONS_PRESET_BY_NAME constants
# 1.8.1  - add new maps and gamemodes from DLC "End Game"
#        - implement get_player_pings
# 1.10.1 - fix the list of gamemodes available for map Talah Market
# 1.10.2 - syntax changes
#        - correctly initialize class attributes
# 1.11   - syntax cleanup
# 1.12   - make use of dict comprehension to generate map/gamemode dictionaries

import b3
import b3.clients
import b3.events
import threading

from time import sleep
from b3.parsers.frostbite2.abstractParser import AbstractParser
from b3.parsers.frostbite2.protocol import CommandFailedError
from b3.parsers.frostbite2.util import PlayerInfoBlock


__author__  = 'Courgette'
__version__ = '1.12'

BF3_REQUIRED_VERSION = 1149977

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
SQUAD_CELESTE  = 32

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

GAME_MODES_NAMES = {
    "ConquestLarge0": "Conquest64",
    "ConquestSmall0": "Conquest",
    "ConquestAssaultLarge0": "Conquest Assault64",
    "ConquestAssaultSmall0": "Conquest Assault",
    "ConquestAssaultSmall1": "Conquest Assault alt.2",
    "RushLarge0": "Rush",
    "SquadRush0": "Squad Rush",
    "SquadDeathMatch0": "Squad Deathmatch",
    "TeamDeathMatch0": "Team Deathmatch",
    "Domination0": "Conquest Domination",
    "GunMaster0": "Gun master",
    "TeamDeathMatchC0": "TDM Close Quarters",
    "TankSuperiority0": "Tank Superiority",
    "Scavenger0": "Scavenger",
    "AirSuperiority0": "Air Superiority",
    "CaptureTheFlag0": "Capture the Flag",
}

GAMEMODES_IDS_BY_NAME = {name.lower(): x for x, name in GAME_MODES_NAMES.items()}

MAP_NAME_BY_ID = {
    'MP_001': 'Grand Bazaar',
    'MP_003': 'Tehran Highway',
    'MP_007': 'Caspian Border',
    'MP_011': 'Seine Crossing',
    'MP_012': 'Operation Firestorm',
    'MP_013': 'Damavand Peak',
    'MP_017': 'Noshahar Canals',
    'MP_018': 'Kharg Island',
    'MP_Subway': 'Operation Metro',
    'XP1_001': 'Strike At Karkand',
    'XP1_002': 'Gulf of Oman',
    'XP1_003': 'Sharqi Peninsula',
    'XP1_004': 'Wake Island',
    "XP2_Factory": "Scrapmetal",
    "XP2_Office": "Operation 925",
    "XP2_Palace": "Donya Fortress",
    "XP2_Skybar": "Ziba Tower",
    "XP3_Desert": "Bandar Desert",
    "XP3_Alborz": "Alborz Mountains",
    "XP3_Shield": "Armored Shield",
    "XP3_Valley": "Death Valley",
    "XP4_Quake": "Epicenter",
    "XP4_FD": "Markaz Monolith",
    "XP4_Parl": "Azadi Palace",
    "XP4_Rubble": "Talah market",
    "XP5_001": "Operation Riverside",
    "XP5_002": "Nebandan Flats",
    "XP5_003": "Kiasar Railroad",
    "XP5_004": "Sabalan Pipeline",
}

MAP_ID_BY_NAME = {name.lower(): x for x, name in MAP_NAME_BY_ID.items()}

GAME_MODES_BY_MAP_ID = {
    "MP_001": (
        "ConquestLarge0",
        "ConquestSmall0",
        "RushLarge0",
        "SquadRush0",
        "SquadDeathMatch0",
        "TeamDeathMatch0"),
    "MP_003": (
        "ConquestLarge0",
        "ConquestSmall0",
        "RushLarge0",
        "SquadRush0",
        "SquadDeathMatch0",
        "TeamDeathMatch0"),
    "MP_007": (
        "ConquestLarge0",
        "ConquestSmall0",
        "RushLarge0",
        "SquadRush0",
        "SquadDeathMatch0",
        "TeamDeathMatch0"),
    "MP_011": (
        "ConquestLarge0",
        "ConquestSmall0",
        "RushLarge0",
        "SquadRush0",
        "SquadDeathMatch0",
        "TeamDeathMatch0"),
    "MP_012": (
        "ConquestLarge0",
        "ConquestSmall0",
        "RushLarge0",
        "SquadRush0",
        "SquadDeathMatch0",
        "TeamDeathMatch0"),
    "MP_013": (
        "ConquestLarge0",
        "ConquestSmall0",
        "RushLarge0",
        "SquadRush0",
        "SquadDeathMatch0",
        "TeamDeathMatch0"),
    "MP_017": (
        "ConquestLarge0",
        "ConquestSmall0",
        "RushLarge0",
        "SquadRush0",
        "SquadDeathMatch0",
        "TeamDeathMatch0"),
    "MP_018": (
        "ConquestLarge0",
        "ConquestSmall0",
        "RushLarge0",
        "SquadRush0",
        "SquadDeathMatch0",
        "TeamDeathMatch0"),
    "MP_Subway": (
        "ConquestLarge0",
        "ConquestSmall0",
        "RushLarge0",
        "SquadRush0",
        "SquadDeathMatch0",
        "TeamDeathMatch0"),
    "XP1_001": (
        "ConquestAssaultLarge0",
        "ConquestAssaultSmall0",
        "ConquestAssaultSmall1",
        "RushLarge0",
        "SquadRush0",
        "SquadDeathMatch0",
        "TeamDeathMatch0"),
    "XP1_002": (
        "ConquestLarge0",
        "ConquestSmall0",
        "ConquestAssaultSmall0",
        "RushLarge0",
        "SquadRush0",
        "SquadDeathMatch0",
        "TeamDeathMatch0"),
    "XP1_003": (
        "ConquestAssaultLarge0",
        "ConquestAssaultSmall0",
        "ConquestAssaultSmall1",
        "RushLarge0",
        "SquadRush0",
        "SquadDeathMatch0",
        "TeamDeathMatch0"),
    "XP1_004": (
        "ConquestAssaultLarge0",
        "ConquestAssaultSmall0",
        "ConquestAssaultSmall1",
        "RushLarge0",
        "SquadRush0",
        "SquadDeathMatch0",
        "TeamDeathMatch0"),
    "XP2_Factory": (
        "TeamDeathMatchC0",
        "GunMaster0",
        "Domination0",
        "SquadDeathMatch0"),
    "XP2_Office": (
        "TeamDeathMatchC0",
        "GunMaster0",
        "Domination0",
        "SquadDeathMatch0"),
    "XP2_Palace": (
        "TeamDeathMatchC0",
        "GunMaster0",
        "Domination0",
        "SquadDeathMatch0"),
    "XP2_Skybar": (
        "TeamDeathMatchC0",
        "GunMaster0",
        "Domination0",
        "SquadDeathMatch0"),
    "XP3_Desert": (
        "ConquestLarge0",
        "ConquestSmall0",
        "RushLarge0",
        "SquadRush0",
        "SquadDeathMatch0",
        "TeamDeathMatch0",
        "TankSuperiority0"),
    "XP3_Alborz": (
        "ConquestLarge0",
        "ConquestSmall0",
        "RushLarge0",
        "SquadRush0",
        "SquadDeathMatch0",
        "TeamDeathMatch0",
        "TankSuperiority0"),
    "XP3_Shield": (
        "ConquestLarge0",
        "ConquestSmall0",
        "RushLarge0",
        "SquadRush0",
        "SquadDeathMatch0",
        "TeamDeathMatch0",
        "TankSuperiority0"),
    "XP3_Valley": (
        "ConquestLarge0",
        "ConquestSmall0",
        "RushLarge0",
        "SquadRush0",
        "SquadDeathMatch0",
        "TeamDeathMatch0",
        "TankSuperiority0"),
    "XP4_Quake": (
        "ConquestLarge0",
        "ConquestSmall0",
        "RushLarge0",
        "SquadRush0",
        "SquadDeathMatch0",
        "TeamDeathMatch0",
        "GunMaster0",
        "Scavenger0"),
    "XP4_FD": (
        "ConquestLarge0",
        "ConquestSmall0",
        "RushLarge0",
        "SquadRush0",
        "SquadDeathMatch0",
        "TeamDeathMatch0",
        "GunMaster0",
        "Scavenger0"),
    "XP4_Parl": (
        "ConquestLarge0",
        "ConquestSmall0",
        "RushLarge0",
        "SquadRush0",
        "SquadDeathMatch0",
        "TeamDeathMatch0",
        "GunMaster0",
        "Scavenger0"),
    "XP4_Rubble": (
        "ConquestAssaultLarge0",
        "ConquestAssaultSmall0",
        "RushLarge0",
        "SquadRush0",
        "SquadDeathMatch0",
        "TeamDeathMatch0",
        "GunMaster0",
        "Scavenger0"),
    "XP5_001": (
        "CaptureTheFlag0",
        "AirSuperiority0",
        "ConquestLarge0",
        "ConquestAssaultLarge0",
        "ConquestSmall0",
        "ConquestAssaultSmall0",
        "RushLarge0",
        "SquadRush0",
        "SquadDeathMatch0",
        "TeamDeathMatch0"),
    "XP5_002": (
        "CaptureTheFlag0",
        "AirSuperiority0",
        "ConquestLarge0",
        "ConquestAssaultLarge0",
        "ConquestSmall0",
        "ConquestAssaultSmall0",
        "RushLarge0",
        "SquadRush0",
        "SquadDeathMatch0",
        "TeamDeathMatch0"),
    "XP5_003": (
        "CaptureTheFlag0",
        "AirSuperiority0",
        "ConquestLarge0",
        "ConquestAssaultLarge0",
        "ConquestSmall0",
        "ConquestAssaultSmall0",
        "RushLarge0",
        "SquadRush0",
        "SquadDeathMatch0",
        "TeamDeathMatch0"),
    "XP5_004": (
        "CaptureTheFlag0",
        "AirSuperiority0",
        "ConquestLarge0",
        "ConquestAssaultLarge0",
        "ConquestSmall0",
        "ConquestAssaultSmall0",
        "RushLarge0",
        "SquadRush0",
        "SquadDeathMatch0",
        "TeamDeathMatch0"),
}

GUNMASTER_WEAPONS_PRESET_BY_INDEX = [
    ["Standard Weapon list",
        ["MP443", "M93", "T44", "PP-19", "P90", "SPAS-12", "MK3A1 Flechette", "ACW-R",
         "MTAR", "AUG", "SCAR-L", "LSAT", "L86", "M417", "JNG-90", "M320 LVG", "Knife"]],
    ["Standard Weapon list REVERSED",
        ["JNG-90", "M417", "L86", "LSAT", "SCAR-L", "AUG", "MTAR", "ACW-R", "MK3A1 Flechette",
         "SPAS-12", "P90", "PP-19", "T44", "M93", "MP443", "M320 LVG, Knife"]],
    ["Light Weight",
        ["M9", "Glock17", "M93", "870", "Saiga12", "Spas-12", "Dao-12", "M1014", "PP2000",
         "M5K", "P90", "MP7", "ASVal", "PP-19", "UMP45", "M320 GL", "Knife"]],
    ["Heavy Gear",
        ["MP412Rex", "T44", "SPAS-12 Slugs", "MK3A3 slugs", "AK47M", "F2000", "G3A3", "FAMAS",
         "SCAR-L", "SteyrAug", "M249", "M60", "QBB-95", "MG36", "LSAT, C4, Knife"]],
    ["Pistol run!",
        ["M9", "MP443", "G17c", "M9 Suppressed", "G17 Suppressed", "M1911", "Glock18", "M93",
         "MP12rex", "Taurus44", "Knife"]],
    ["Snipers Heaven",
        ["M9 Suppressor", "Glock17 Suppressor", "M1911 Suppressor", "SVD", "SKS", "MK11",
         "QBU-88", "M417", "M40A5", "SV98", "L96", "JNG90", "M98B", "Crossbow Bolt, Knife"]],
    ["US arms race",
        ["M9", "M1911", "M870", "PDW-R", "M4A1", "M16", "M249", "M240", "MK11", "M40A5",
         "SMAW", "Knife"]],
    ["RU arms race",
        ["MP443", ".412 rex", "Saiga 12k", "PP-2000", "PP-19", "AS Val", "AKS-74u",
         "AK74M", "RPK-74", "SVD", "RPG-7", "Knife"]],
    ["EU arms race",
        ["G17", "M93R", "SPAS-12", "MP7", "UMP", "G36", "M416", "L85", "MG36", "M417",
         "M320 GL", "Knife"]],
]


GUNMASTER_WEAPONS_PRESET_BY_NAME = {x[0]: x[1] for x in GUNMASTER_WEAPONS_PRESET_BY_INDEX}


class Bf3Parser(AbstractParser):

    gameName = 'bf3'

    _gameServerVars = (
        '3dSpotting',
        '3pCam',
        'autoBalance',
        'bannerUrl',
        'bulletDamage',
        'friendlyFire',
        'gameModeCounter',
        'gamePassword',
        'hud',
        'idleBanRounds',
        'idleTimeout',
        'killCam',
        'killRotation',
        'maxPlayers',
        'minimap',
        'minimapSpotting',
        'nameTag',
        'onlySquadLeaderSpawn',
        'playerManDownTime',
        'playerRespawnTime',
        'ranked',
        'regenerateHealth',
        'roundLockdownCountdown',
        'roundRestartPlayerCount',
        'roundStartPlayerCount',
        'roundsPerMap',
        'serverDescription',
        'serverMessage',
        'serverName',
        'soldierHealth',
        'teamKillCountForKick',
        'teamKillKickForBan',
        'teamKillValueDecreasePerSecond',
        'teamKillValueForKick',
        'teamKillValueIncrease',
        'unlockMode',
        'vehicleSpawnAllowed',
        'vehicleSpawnDelay',
        'premiumStatus',
        'gunMasterWeaponsPreset'
    )

    # gamemodes aliases {alias: actual game mode name}
    _gamemode_aliases = {
        'cq': 'conquest',
        'cq64': 'conquest64',
        'tdm': 'team deathmatch',
        'sqdm': 'squad deathmatch',
        'ctf': 'capture the flag'
    }

    _gamePort = None

    ####################################################################################################################
    #                                                                                                                  #
    #   PARSER INITIALIZATION                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    def __new__(cls, *args, **kwargs):
        Bf3Parser.patch_b3_Client_isAlive()
        return AbstractParser.__new__(cls)

    def startup(self):
        """
        Called after the parser is created before run().
        """
        AbstractParser.startup(self)

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
            client = self.clients.getByCID(cid)
            if not client:
                self.debug('Client %s found on the server' % cid)
                client = self.clients.newClient(cid, guid=p['name'], name=p['name'], team=p['teamId'], squad=p['squadId'], data=p)
                self.queueEvent(self.getEvent('EVT_CLIENT_JOIN', data=p, client=client))

    ####################################################################################################################
    #                                                                                                                  #
    #   FROSTBITE2 EVENTS HANDLERS                                                                                     #
    #                                                                                                                  #
    ####################################################################################################################

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
                return self.getEvent('EVT_CLIENT_SQUAD_CHANGE', data=data[1:], client=client)

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

    def _OnServerLevelstarted(self, action, data):
        """
        Event server.onLevelStarted was used to be sent in Frostbite1.
        Unfortunately it does not exists anymore in Frostbite2.
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
                self.queueEvent(self.getEvent('EVT_GAME_ROUND_START', data=self.game))

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
        if not filter_client_ids:
            filter_client_ids = [client.cid for client in self.clients.getList()]

        for cid in filter_client_ids:
            try:
                words = self.write(("player.ping", cid))
                pings[cid] = int(words[0])
            except ValueError:
                pass
            except Exception, err:
                self.error("Could not get ping info for player %s: %s" % (cid, err), exc_info=err)
        return pings

    ####################################################################################################################
    #                                                                                                                  #
    #   OTHER METHODS                                                                                                  #
    #                                                                                                                  #
    ####################################################################################################################

    def checkVersion(self):
        version = self.output.write('version')
        self.info('server version : %s' % version)
        if version[0] != 'BF3':
            raise Exception("the BF3 parser can only work with Battlefield 3")
        if int(version[1]) < BF3_REQUIRED_VERSION:
            raise Exception("the BF3 parser can only work with Battlefield 3 server version %s and above. "
                            "You are trying to connect to %s v%s" % (BF3_REQUIRED_VERSION, version[0], version[1]))

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
                words = self.write(('admin.listPlayers', 'player', cid))
                pib = PlayerInfoBlock(words)
                if not len(pib):
                    self.debug('No such client found')
                    return None
                p = pib[0]
                if 'guid' in p:
                    client = self.clients.newClient(p['name'], guid=p['guid'], name=p['name'],
                                                    team=self.getTeam(p['teamId']), teamId=int(p['teamId']),
                                                    squad=p['squadId'], data=p)

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
        Change levelname to real name.
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
            self.warning("unknown gamemode: %s" % gamemode_id)
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
        def getCvar(cvar):
            try:
                return self.getCvar(cvar).getString()
            except Exception:
                pass
        def getCvarBool(cvar):
            try:
                return self.getCvar(cvar).getBoolean()
            except Exception:
                pass
        def getCvarInt(cvar):
            try:
                return self.getCvar(cvar).getInt()
            except Exception:
                pass
        def getCvarFloat(cvar):
            try:
                return self.getCvar(cvar).getFloat()
            except Exception:
                pass
        self.game['3dSpotting'] = getCvarBool('3dSpotting')
        self.game['3pCam'] = getCvarBool('3pCam')
        self.game['autoBalance'] = getCvarBool('autoBalance')
        self.game['bannerUrl'] = getCvar('bannerUrl')
        self.game['bulletDamage'] = getCvarInt('bulletDamage')
        self.game['friendlyFire'] = getCvarBool('friendlyFire')
        self.game['gameModeCounter'] = getCvarInt('gameModeCounter')
        self.game['gamePassword'] = getCvar('gamePassword')
        self.game['hud'] = getCvarBool('hud')
        self.game['idleBanRounds'] = getCvarInt('idleBanRounds')
        self.game['idleTimeout'] = getCvarInt('idleTimeout')
        self.game['killCam'] = getCvarBool('killCam')
        self.game['killRotation'] = getCvarBool('killRotation')
        self.game['maxPlayers'] = getCvarInt('maxPlayers')
        self.game['minimap'] = getCvarBool('minimap')
        self.game['minimapSpotting'] = getCvarBool('minimapSpotting')
        self.game['nameTag'] = getCvarBool('nameTag')
        self.game['onlySquadLeaderSpawn'] = getCvarBool('onlySquadLeaderSpawn')
        self.game['playerManDownTime'] = getCvarInt('playerManDownTime')
        self.game['playerRespawnTime'] = getCvarInt('playerRespawnTime')
        self.game['ranked'] = getCvarBool('ranked')
        self.game['regenerateHealth'] = getCvarBool('regenerateHealth')
        self.game['roundLockdownCountdown'] = getCvarInt('roundLockdownCountdown')
        self.game['roundRestartPlayerCount'] = getCvarInt('roundRestartPlayerCount')
        self.game['roundStartPlayerCount'] = getCvarInt('roundStartPlayerCount')
        self.game['roundsPerMap'] = getCvarInt('roundsPerMap')
        self.game['serverDescription'] = getCvar('serverDescription')
        self.game['serverMessage'] = getCvar('serverMessage')
        self.game['serverName'] = getCvar('serverName')
        self.game['soldierHealth'] = getCvarInt('soldierHealth')
        self.game['teamKillCountForKick'] = getCvarInt('teamKillCountForKick')
        self.game['teamKillKickForBan'] = getCvarInt('teamKillKickForBan')
        self.game['teamKillValueDecreasePerSecond'] = getCvarFloat('teamKillValueDecreasePerSecond')
        self.game['teamKillValueForKick'] = getCvarFloat('teamKillValueForKick')
        self.game['teamKillValueIncrease'] = getCvarFloat('teamKillValueIncrease')
        self.game['unlockMode'] = getCvar('unlockMode')
        self.game['vehicleSpawnAllowed'] = getCvarBool('vehicleSpawnAllowed')
        self.game['vehicleSpawnDelay'] = getCvarInt('vehicleSpawnDelay')
        self.game['premiumStatus'] = getCvarBool('premiumStatus')
        self.game['gunMasterWeaponsPreset'] = getCvarInt('gunMasterWeaponsPreset')
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
        data2 = Bf3Parser.decodeServerinfo(data)
        self.debug("decoded server info : %r" % data2)
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

    def getTeam(self, team):
        """
        Convert team numbers to B3 team numbers.
        """
        team = int(team)
        if team == 1:
            return b3.TEAM_RED
        elif team == 2:
            return b3.TEAM_BLUE
        elif team == 3:
            return b3.TEAM_SPEC
        else:
            return b3.TEAM_UNKNOWN

    @staticmethod
    def decodeServerinfo(data):
        """
        <serverName: string> <current playercount: integer> <max playercount: integer> <current gamemode: string>
        <current map: string> <roundsPlayed: integer> <roundsTotal: string> <scores: team scores>
        <onlineState: online state> <ranked: boolean> <punkBuster: boolean> <hasGamePassword: boolean>
        <serverUpTime: seconds> <roundTime: seconds>
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
        }
        if numOfTeams >= 1:
            response['team1score'] = data[8]
        if numOfTeams >= 2:
            response['team2score'] = data[9]
        if numOfTeams >= 3:
            response['team3score'] = data[10]
        if numOfTeams == 4:
            response['team4score'] = data[11]

        # since BF3 R9
        new_info = 'gameIpAndPort', 'punkBusterVersion', 'joinQueueEnabled', 'region', 'closestPingSite', 'country'
        start_index = 7 + numOfTeams + 8
        for i, n in zip(range(start_index, start_index + len(new_info)), new_info):
            try:
                response[n] = data[i]
            except IndexError:
                pass

        return response

    @staticmethod
    def patch_b3_Client_isAlive():
        """
        Add state property to Client
        """
        def isAlive(self):
            """
            Returns whether the player is alive or not.
            """
            # True: player is alive/spawned
            # False: player is death or not spawned
            # None: BF3 server responded with an error or unexpected value
            _player_name = self.name
            try:
                _response = self.console.write(('player.isAlive', _player_name))
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
            # The Client.state value is determined by querying the BF3 server through rcon. See getPlayerState
            pass

        b3.clients.Client.isAlive = isAlive
        b3.clients.Client.state = property(getPlayerState, setPlayerState)

    def _startRound(self):
        # respect var.roundLockdownCountdown
        roundLockdownCountdown = self.getCvar('roundLockdownCountdown').getInt()
        sleep(roundLockdownCountdown)
        self.game.startRound()