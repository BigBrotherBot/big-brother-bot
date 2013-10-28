#
# Battlefield 4 Parser for BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2010 Thomas LEVEIL <courgette@bigbrotherbot.net>
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
# versions that only reflect changes to AbstractParser :
# 1.0.1 -> 1.0.3
# 1.1.1 -> 1.1.6
# 1.2.1 -> 1.2.1
# 1.4.1, 1.6, 1.9, 1.10
#
# CHANGELOG
#
# 0.1
#  functional parser implementation based on the BF3 parser
#
from b3.parsers.frostbite2.abstractParser import AbstractParser
from b3.parsers.frostbite2.util import PlayerInfoBlock
import b3
import b3.events
import threading
from time import sleep

__author__ = 'Courgette, ozon'
__version__ = '1.0.0'

BF4_REQUIRED_VERSION = 1149977

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
BASE_GAME_MODES_NAMES = {
    'ConquestLarge0': 'Conquest64',
    'ConquestSmall0': 'Conquest',
    'RushLarge0': 'Rush',
    'SquadDeathMatch0': 'Squad Deathmatch',
    'TeamDeathMatch0': 'Team Deathmatch',
    'Domination0': 'Domination',
    'Elimination0': 'Defuse',
    'Obliteration': 'Obliteration'
}
GAME_MODES_NAMES = BASE_GAME_MODES_NAMES

GAMEMODES_IDS_BY_NAME = dict()
for _id, name in GAME_MODES_NAMES.items():
    GAMEMODES_IDS_BY_NAME[name.lower()] = _id

# Base game maps: dict('Engine name'='Human-readable name')
BASE_MAP_NAME_BY_ID = {
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
}
MAP_NAME_BY_ID = BASE_MAP_NAME_BY_ID

MAP_ID_BY_NAME = dict()
for _id, name in MAP_NAME_BY_ID.items():
    MAP_ID_BY_NAME[name.lower()] = _id

# GAME_MODES_BY_MAP_ID = dict('Map Engine name': tuple('Game mode engine names'))
BASE_GAME_MODES_BY_MAP_ID = dict().fromkeys(BASE_MAP_NAME_BY_ID, tuple(BASE_GAME_MODES_NAMES.keys()))
GAME_MODES_BY_MAP_ID = BASE_GAME_MODES_BY_MAP_ID


class Bf4Parser(AbstractParser):
    gameName = 'bf4'

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
        'team1FactionOverride',     # <factionId>  Set the faction for team 1
        'team2FactionOverride',     # <factionId>  Set the faction for team 2
        'team3FactionOverride',     # <factionId>  Set the faction for team 3
        'team4FactionOverride',     # <factionId>  Set the faction for team 4
        'teamKillCountForKick',     # <count>  Set number of teamkills allowed during a round
        'teamKillKickForBan',       # <count>  Set number of team-kill kicks that will lead to permaban
        'teamKillValueDecreasePerSecond',   # <count>  Set kill-value decrease per second
        'teamKillValueForKick',     # <count>  Set max kill-value allowed for a player before he/she is kicked
        'teamKillValueIncrease',    # <count>  Set kill-value increase for a teamkill
        'vehicleSpawnAllowed',      # <bool>  Set whether vehicles should spawn in-game
        'vehicleSpawnDelay',        # <modifier: percent>  Set vehicle spawn delay scale factor
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
    }

    def __new__(cls, *args, **kwargs):
        Bf4Parser.patch_b3_Client_isAlive()
        return AbstractParser.__new__(cls)

    def startup(self):
        AbstractParser.startup(self)

        # create the 'Server' client
        self.clients.newClient('Server', guid='Server', name='Server', hide=True, pbid='Server', team=b3.TEAM_UNKNOWN, squad=None)

        self.verbose('GameType: %s, Map: %s' %(self.game.gameType, self.game.mapName))

    def pluginsStarted(self):
        AbstractParser.pluginsStarted(self)
        self.info('connecting all players...')
        plist = self.getPlayerList()
        for cid, p in plist.iteritems():
            client = self.clients.getByCID(cid)
            if not client:
                #self.clients.newClient(playerdata['cid'], guid=playerdata['guid'], name=playerdata['name'], team=playerdata['team'], squad=playerdata['squad'])
                name = p['name']
                self.debug('client %s found on the server' % cid)
                client = self.clients.newClient(cid, guid=p['name'], name=name, team=p['teamId'], squad=p['squadId'], data=p)
                self.queueEvent(b3.events.Event(b3.events.EVT_CLIENT_JOIN, p, client))

    ###############################################################################################
    #
    #    Frostbite2 events handlers
    #    
    ###############################################################################################

    def OnPlayerTeamchange(self, action, data):
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

    def OnPlayerSquadchange(self, action, data):
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
                return b3.events.Event(b3.events.EVT_CLIENT_SQUAD_CHANGE, data[1:], client)

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
                self.queueEvent(b3.events.Event(b3.events.EVT_GAME_ROUND_START, self.game))

    ###############################################################################################
    #
    #    B3 Parser interface implementation
    #    
    ###############################################################################################

    def getPlayerPings(self, filter_client_ids=None):
        """Ask the server for a given client's pings

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
                self.error("could not get ping info for player %s: %s" % (cid, err), exc_info=err)
        return pings

    ###############################################################################################
    #
    #    Other methods
    #    
    ###############################################################################################

    def checkVersion(self):
        version = self.output.write('version')
        self.info('server version : %s' % version)
        if version[0] != 'BF4':
            raise Exception('the BF4 parser can only work with Battlefield 4')
        if int(version[1]) < BF4_REQUIRED_VERSION:
            raise Exception("the BF4 parser can only work with Battlefield 4 server version %s and above. You are tr"
                            "ying to connect to %s v%s" % (BF4_REQUIRED_VERSION, version[0], version[1]))

    def getClient(self, cid, guid=None):
        """Get a connected client from storage or create it
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
                return self.clients.newClient('Server', guid='Server', name='Server', hide=True, pbid='Server', team=b3.TEAM_UNKNOWN, teamId=None, squadId=None)
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
                    cid = p['name']
                    name = p['name']
                    guid = p['guid']
                    teamId = p['teamId']
                    squadId = p['squadId']
                    client = self.clients.newClient(cid, guid=guid, name=name, team=self.getTeam(teamId), teamId=int(teamId), squad=squadId, data=p)
                    self.queueEvent(b3.events.Event(b3.events.EVT_CLIENT_JOIN, p, client))
        return client

    def getHardName(self, mapname):
        """ Change real name to level name """
        mapname = mapname.lower()
        try:
            return MAP_ID_BY_NAME[mapname]
        except KeyError:
            self.warning('unknown level name \'%s\'. Please make sure you have entered a valid mapname' % mapname)
            return mapname

    def getEasyName(self, mapname):
        """ Change level name to real name """
        try:
            return MAP_NAME_BY_ID[mapname]
        except KeyError:
            self.warning('unknown level name \'%s\'. Please report this on B3 forums' % mapname)
            return mapname

    def getGameMode(self, gamemode_id):
        """ Convert game mode ID into human friendly name """
        if gamemode_id in GAME_MODES_NAMES:
            return GAME_MODES_NAMES[gamemode_id]
        else:
            self.warning('unknown gamemode \"%s\"' % gamemode_id)
            # fallback by sending gamemode id
            return gamemode_id

    def getGameModeId(self, gamemode_name):
        """ Get gamemode id by name """
        name = gamemode_name.lower()
        if name in GAMEMODES_IDS_BY_NAME:
            return GAMEMODES_IDS_BY_NAME[name]
        else:
            self.warning("unknown gamemode name \"%s\"" % gamemode_name)
            # fallback by sending gamemode id
            return gamemode_name

    def getSupportedMapIds(self):
        """return a list of supported levels for the current game mod"""
        # TODO : remove this method once the method on from AbstractParser is working
        return MAP_NAME_BY_ID.keys()

    def getSupportedGameModesByMapId(self, map_id):
        """return a list of supported game modes for the given map id"""
        return GAME_MODES_BY_MAP_ID[map_id]

    def getServerVars(self):
        """Update the game property from server fresh data"""
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
        self.game['alwaysAllowSpectators'] = getCvarBool('alwaysAllowSpectators')
        self.game['autoBalance'] = getCvarBool('autoBalance')
        self.game['bulletDamage'] = getCvarInt('bulletDamage')
        self.game['commander'] = getCvarBool('commander')
        self.game['crossHair'] = getCvarBool('crossHair')
        self.game['forceReloadWholeMags'] = getCvarBool('forceReloadWholeMags')
        self.game['friendlyFire'] = getCvarBool('friendlyFire')
        self.game['gameModeCounter'] = getCvarInt('gameModeCounter')
        self.game['gamePassword'] = getCvar('gamePassword')
        self.game['hitIndicatorsEnabled'] = getCvarBool('hitIndicatorsEnabled')
        self.game['hud'] = getCvarBool('hud')
        self.game['idleBanRounds'] = getCvarInt('idleBanRounds')
        self.game['idleTimeout'] = getCvarInt('idleTimeout')
        self.game['killCam'] = getCvarBool('killCam')
        self.game['maxPlayers'] = getCvarInt('maxPlayers')
        self.game['maxSpectators'] = getCvarInt('maxSpectators')
        self.game['miniMap'] = getCvarBool('miniMap')
        self.game['miniMapSpotting'] = getCvarBool('miniMapSpotting')
        self.game['mpExperience'] = getCvarInt('mpExperience')
        self.game['nameTag'] = getCvarBool('nameTag')
        self.game['onlySquadLeaderSpawn'] = getCvarBool('onlySquadLeaderSpawn')
        self.game['playerRespawnTime'] = getCvarInt('playerRespawnTime')
        self.game['regenerateHealth'] = getCvarBool('regenerateHealth')
        self.game['roundLockdownCountdown'] = getCvarInt('roundLockdownCountdown')
        self.game['roundRestartPlayerCount'] = getCvarInt('roundRestartPlayerCount')
        self.game['roundStartPlayerCount'] = getCvarInt('roundStartPlayerCount')
        self.game['roundTimeLimit'] = getCvarInt('roundTimeLimit')
        self.game['serverDescription'] = getCvar('serverDescription')
        self.game['serverMessage'] = getCvar('serverMessage')
        self.game['serverName'] = getCvar('serverName')
        self.game['serverType'] = getCvar('serverType')
        self.game['soldierHealth'] = getCvarInt('soldierHealth')
        self.game['team1FactionOverride'] = getCvarInt('team1FactionOverride')
        self.game['team2FactionOverride'] = getCvarInt('team2FactionOverride')
        self.game['team3FactionOverride'] = getCvarInt('team3FactionOverride')
        self.game['team4FactionOverride'] = getCvarInt('team4FactionOverride')
        self.game['teamKillCountForKick'] = getCvarInt('teamKillCountForKick')
        self.game['teamKillKickForBan'] = getCvarInt('teamKillKickForBan')
        self.game['teamKillValueDecreasePerSecond'] = getCvarFloat('teamKillValueDecreasePerSecond')
        self.game['teamKillValueForKick'] = getCvarFloat('teamKillValueForKick')
        self.game['teamKillValueIncrease'] = getCvarFloat('teamKillValueIncrease')
        self.game['vehicleSpawnAllowed'] = getCvarBool('vehicleSpawnAllowed')
        self.game['vehicleSpawnDelay'] = getCvarInt('vehicleSpawnDelay')

        self.game.timeLimit = self.game.gameModeCounter
        self.game.fragLimit = self.game.gameModeCounter
        self.game.captureLimit = self.game.gameModeCounter

    def getServerInfo(self):
        """query server info, update self.game and return query results
        Response: OK,serverName,numPlayers,maxPlayers,level,gamemode,[teamscores],isRanked,hasPunkbuster,hasPassword,serverUptime,roundTime
        The first number in the [teamscore] component I listed is numTeams, followed by the score or ticket count for each team (0-4 items), 
        then the targetScore. (e.g. in TDM/SQDM this is the number of kills to win)
        So when you start a Squad Deathmatch round with 50 kills needed to win, it will look like this:
        4,0,0,0,0,50
        
        """
        data = self.write(('serverInfo',))
        data2 = Bf4Parser.decodeServerinfo(data)
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
        """convert team numbers to B3 team numbers"""
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
            'targetScore': data[7+numOfTeams + 1],
            'onlineState': data[7+numOfTeams + 2],
            'isRanked': data[7+numOfTeams + 3],
            'hasPunkbuster': data[7+numOfTeams + 4],
            'hasPassword': data[7+numOfTeams + 5],
            'serverUptime': data[7+numOfTeams + 6],
            'roundTime': data[7+numOfTeams + 7],
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

        new_info = 'gameIpAndPort', 'punkBusterVersion', 'joinQueueEnabled', 'region', 'closestPingSite', 'country'
        start_index = 7 + numOfTeams + 8
        for index, name in zip(range(start_index, start_index + len(new_info)), new_info):
            try:
                response[name] = data[index]
            except IndexError:
                pass

        return response

    @staticmethod
    def patch_b3_Client_isAlive():
        """ add state property to Client """

        def isAlive(self):
            """Returns whether the player is alive or not."""
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
            except Exception, err:
                self.console.error("could not get player state for player %s: %s" % (_player_name, err), exc_info=err)
        b3.clients.Client.isAlive = isAlive

        def getPlayerState(self):
            _state = b3.STATE_UNKNOWN
            _isAlive = self.isAlive()
            if _isAlive:
                _state = b3.STATE_ALIVE
            elif _isAlive == False:
                _state = b3.STATE_DEAD

            return _state

        def setPlayerState(self, v):
            # silently prevents Client.state from being set.
            # The Client.state value is determined by querying the BF4 server through rcon. See getPlayerState
            pass

        b3.clients.Client.state = property(getPlayerState, setPlayerState)

    def _startRound(self):
        # respect var.roundLockdownCountdown
        roundLockdownCountdown = self.getCvar('roundLockdownCountdown').getInt()
        sleep(roundLockdownCountdown)
        self.game.startRound()
