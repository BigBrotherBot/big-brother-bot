#
# Battlefield 3 Parser for BigBrotherBot(B3) (www.bigbrotherbot.net)
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
#
# CHANGELOG
#
# 0.1
#  functional parser but BF3 admin protocol is not fully implemented on the BF3 side. See TODOs
# 1.0
#  update parser for BF3 R20
# 1.1
#  reflects changes in AbstractParser and refactor the class by moving some of the code to AbstractParser
# 1.2
#  reflects changes in AbstractParser due to BF3 server R21 release
# 1.3
#  BF3 server R24 changes
# 1.4
#  add available gamemodes by map
#  check minimum required BF3 server version on startup
#  fix issue from 1.3 that made impossible to use commands related to Close Quarter maps
#
from b3.parsers.frostbite2.abstractParser import AbstractParser
from b3.parsers.frostbite2.util import PlayerInfoBlock
import b3
import b3.events
__author__  = 'Courgette'
__version__ = '1.4'

BF3_REQUIRED_VERSION = 964189

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
    }

GAMEMODES_IDS_BY_NAME = dict()
for _id, name in GAME_MODES_NAMES.items():
    GAMEMODES_IDS_BY_NAME[name.lower()] = _id

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
    }

MAP_ID_BY_NAME = dict()
for _id, name in MAP_NAME_BY_ID.items():
    MAP_ID_BY_NAME[name.lower()] = _id

GAME_MODES_BY_MAP_ID = {
    "MP_001": ("ConquestLarge0", "ConquestSmall0", "RushLarge0", "SquadRush0", "SquadDeathMatch0", "TeamDeathMatch0"),
    "MP_003": ("ConquestLarge0", "ConquestSmall0", "RushLarge0", "SquadRush0", "SquadDeathMatch0", "TeamDeathMatch0"),
    "MP_007": ("ConquestLarge0", "ConquestSmall0", "RushLarge0", "SquadRush0", "SquadDeathMatch0", "TeamDeathMatch0"),
    "MP_011": ("ConquestLarge0", "ConquestSmall0", "RushLarge0", "SquadRush0", "SquadDeathMatch0", "TeamDeathMatch0"),
    "MP_012": ("ConquestLarge0", "ConquestSmall0", "RushLarge0", "SquadRush0", "SquadDeathMatch0", "TeamDeathMatch0"),
    "MP_013": ("ConquestLarge0", "ConquestSmall0", "RushLarge0", "SquadRush0", "SquadDeathMatch0", "TeamDeathMatch0"),
    "MP_017": ("ConquestLarge0", "ConquestSmall0", "RushLarge0", "SquadRush0", "SquadDeathMatch0", "TeamDeathMatch0"),
    "MP_018": ("ConquestLarge0", "ConquestSmall0", "RushLarge0", "SquadRush0", "SquadDeathMatch0", "TeamDeathMatch0"),
    "MP_Subway": ("ConquestLarge0", "ConquestSmall0", "RushLarge0", "SquadRush0", "SquadDeathMatch0", "TeamDeathMatch0"),
    "XP1_001": ("ConquestAssaultLarge0", "ConquestAssaultSmall0", "ConquestAssaultSmall1", "RushLarge0", "SquadRush0", "SquadDeathMatch0", "TeamDeathMatch0"),
    "XP1_002": ("ConquestLarge0", "ConquestSmall0", "ConquestAssaultSmall0", "RushLarge0", "SquadRush0", "SquadDeathMatch0", "TeamDeathMatch0"),
    "XP1_003": ("ConquestAssaultLarge0", "ConquestAssaultSmall0", "ConquestAssaultSmall1", "RushLarge0", "SquadRush0", "SquadDeathMatch0", "TeamDeathMatch0"),
    "XP1_004": ("ConquestAssaultLarge0", "ConquestAssaultSmall0", "ConquestAssaultSmall1", "RushLarge0", "SquadRush0", "SquadDeathMatch0", "TeamDeathMatch0"),
    "XP2_Factory": ("TeamDeathMatchC0", "GunMaster0", "Domination0", "SquadDeathMatch0"),
    "XP2_Office": ("TeamDeathMatchC0", "GunMaster0", "Domination0", "SquadDeathMatch0"),
    "XP2_Palace": ("TeamDeathMatchC0", "GunMaster0", "Domination0", "SquadDeathMatch0"),
    "XP2_Skybar": ("TeamDeathMatchC0", "GunMaster0", "Domination0", "SquadDeathMatch0"),
}


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
        )


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


    ###############################################################################################
    #
    #    B3 Parser interface implementation
    #    
    ###############################################################################################
        
    def getPlayerPings(self):
        """Ask the server for a given client's pings
        """
        # TODO: implements getPlayerPings when pings available on admin.listPlayers
        return {}

    ###############################################################################################
    #
    #    Other methods
    #    
    ###############################################################################################

    def checkVersion(self):
        version = self.output.write('version')
        self.info('server version : %s' % version)
        if version[0] != 'BF3':
            raise Exception("the BF3 parser can only work with Battlefield 3")
        if int(version[1]) < BF3_REQUIRED_VERSION:
            raise Exception("the BF3 parser can only work with Battlefield 3 server version %s and above. You are tr"
                            "ying to connect to %s v%s" % (BF3_REQUIRED_VERSION, version[0], version[1]))

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
        """ Change levelname to real name """
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
            self.warning("unknown gamemode \"%s\"" % gamemode_id)
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

        # since BF3 R9
        new_info = 'gameIpAndPort', 'punkBusterVersion', 'joinQueueEnabled', 'region', 'closestPingSite', 'country'
        start_index = 7 + numOfTeams + 8
        for index, name in zip(range(start_index, start_index + len(new_info)), new_info):
            try:
                response[name] = data[index]
            except IndexError:
                pass

        return response

