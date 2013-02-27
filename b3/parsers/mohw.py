#
# Medal of Honor: Warfighter Parser for BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2010 BigBrotherBot(B3)
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
import traceback
import sys
from b3.parsers.frostbite2.abstractParser import AbstractParser
from b3.parsers.frostbite2.util import PlayerInfoBlock, MapListBlockError
import b3
import b3.events
__author__  = 'Freelander'
__version__ = '0.1'

MOHW_REQUIRED_VERSION = 323174

GAME_MODES_NAMES = {
    "CombatMission": "Combat Mission",
    "Sport": "Home Run",
    "SectorControl": "Sector Control",
    "TeamDeathMatch": "Team Death Match",
    "BombSquad": "Hot Spot",
    }

GAMEMODES_IDS_BY_NAME = dict()
for _id, name in GAME_MODES_NAMES.items():
    GAMEMODES_IDS_BY_NAME[name.lower()] = _id

MAP_NAME_BY_ID = {
    'MP_03': 'Somalia Stronghold',
    'MP_05': 'Novi Grad Warzone',
    'MP_10': 'Sarajevo Stadium',
    'MP_12': 'Basilan Aftermath',
    'MP_13': 'Hara Dunes',
    'MP_16': 'Al Fara Cliffside',
    'MP_18': 'Shogore Valley',
    'MP_19': 'Tungunan Jungle',
    'MP_20': 'Darra Gun Market',
    'MP_21': 'Chitrail Compound'
    }

MAP_ID_BY_NAME = dict()
for _id, name in MAP_NAME_BY_ID.items():
    MAP_ID_BY_NAME[name.lower()] = _id

GAME_MODES_BY_MAP_ID = {
    "MP_03": ("CombatMission", "Sport", "SectorControl", "TeamDeathMatch", "BombSquad"),
    "MP_05": ("CombatMission", "SectorControl", "TeamDeathMatch", "BombSquad"),
    "MP_10": ("CombatMission", "Sport", "SectorControl", "TeamDeathMatch", "BombSquad"),
    "MP_12": ("CombatMission", "Sport", "SectorControl", "TeamDeathMatch"),
    "MP_13": ("CombatMission", "SectorControl", "TeamDeathMatch", "BombSquad"),
    "MP_16": ("CombatMission", "Sport", "SectorControl", "TeamDeathMatch", "BombSquad"),
    "MP_18": ("CombatMission", "Sport", "SectorControl", "TeamDeathMatch", "BombSquad"),
    "MP_19": ("CombatMission", "Sport", "SectorControl", "TeamDeathMatch", "BombSquad"),
    "MP_20": ("CombatMission", "Sport", "SectorControl", "TeamDeathMatch", "BombSquad"),
    "MP_21": ("CombatMission", "Sport", "SectorControl", "TeamDeathMatch", "BombSquad")
    }

class MohwParser(AbstractParser):
    gameName = 'mohw'

    _commands = {
        'message': ('admin.say', '%(message)s', 'team', '%(teamId)s'),
        'sayTeam': ('admin.say', '%(message)s', 'team', '%(teamId)s'),
        'say': ('admin.say', '%(message)s', 'all'),
        'bigmessage': ('admin.yell', '%(message)s', 'team', '%(teamId)s'),
        'yellTeam': ('admin.yell', '%(message)s', 'team', '%(teamId)s'),
        'yell': ('admin.yell', '%(message)s', 'all'),
        'kick': ('admin.kickPlayer', '%(cid)s', '%(reason)s'),
        'ban': ('banList.add', 'guid', '%(guid)s', 'perm', '%(reason)s'),
        'banByName': ('banList.add', 'name', '%(name)s', 'perm', '%(reason)s'),
        'banByIp': ('banList.add', 'ip', '%(ip)s', 'perm', '%(reason)s'),
        'unban': ('banList.remove', 'guid', '%(guid)s'),
        'unbanByIp': ('banList.remove', 'ip', '%(ip)s'),
        'tempban': ('banList.add', 'guid', '%(guid)s', 'seconds', '%(duration)d', '%(reason)s'),
        'tempbanByName': ('banList.add', 'name', '%(name)s', 'seconds', '%(duration)d', '%(reason)s'),
        }

    _gameServerVars = (
        '3pCam',
        'autoBalance',
        'bannerUrl',
        'buddyOutline',
        'bulletDamage',
        'friendlyFire',
        'gameModeCounter',
        'gamePassword',
        'hardcoreBulletDamageOverride',
        'hudBuddyInfo',
        'hudClassAbility',
        'hudCrosshair',
        'hudEnemyTag',
        'hudExplosiveIcons',
        'hudGameMode',
        'hudHealthAmmo',
        'hudMinimap',
        'hudObiturary',
        'hudPointsTracker',
        'hudUnlocks',
        'idleBanRounds',
        'idleTimeout',
        'killCam',
        'maxPlayers',
        'playerManDownTime',
        'playerRespawnTime',
        'playlist',
        'ranked',
        'regenerateHealth',
        'roundRestartPlayerCount',
        'roundStartPlayerCount',
        'roundsPerMap',
        'serverDescription',
        'serverName',
        'soldierHealth',
        'teamKillCountForKick',
        'teamKillKickForBan',
        'teamKillValueDecreasePerSecond',
        'teamKillValueForKick',
        'teamKillValueIncrease',
        )

    # gamemodes aliases {alias: actual game mode name}
    _gamemode_aliases = {
        'cm': 'Combat Mission',
        'hr': 'Home Run',
        'sc': 'Sector Control',
        'tdm': 'Team Death Match',
        'hs': 'Hot Spot',
        'bomb': 'Hot Spot',
    }

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
            self.warning("Could not get client : %s" % traceback.extract_tb(sys.exc_info()[2]))
            return
        if client.cid == 'Server':
            # ignore chat events for Server
            return
        text = data[1]

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

        return b3.events.Event(b3.events.EVT_CLIENT_SAY, text, client)

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

    def saybig(self, msg):
        """\
        broadcast a message to all players in a way that will catch their attention.
        """
        if msg and len(msg.strip())>0:
            text = self.stripColors(self.msgPrefix + ' ' + msg)
            for line in self.getWrap(text, self._settings['line_length'], self._settings['min_wrap_length']):
                self.write(self.getCommand('yell', message=line))

    def message(self, client, text):
        try:
            if client is None:
                self.say(text)
            elif client.cid is None:
                pass
            else:
                cmd_name = 'bigmessage' if self._settings['big_b3_private_responses'] else 'message'
                self.write(self.getCommand(cmd_name, message=text, teamId=client.teamId))
        except Exception, err:
            self.warning(err)

    ###############################################################################################
    #
    #    Other methods
    #
    ###############################################################################################

    def checkVersion(self):
        version = self.output.write('version')
        self.info('server version : %s' % version)
        if version[0] != 'MOHW':
            raise Exception("the MOHW parser can only work with a Medal of Honor Warfighter server")
        if int(version[1]) < MOHW_REQUIRED_VERSION:
            raise Exception("the MOHW parser can only work with Medal of Honor Warfighter server version %s and above. You are tr"
                            "ying to connect to %s v%s" % (MOHW_REQUIRED_VERSION, version[0], version[1]))

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
        self.game['3pCam'] = getCvarBool('3pCam')
        self.game['autoBalance'] = getCvarBool('autoBalance')
        self.game['bannerUrl'] = getCvar('bannerUrl')
        self.game['buddyOutline'] = getCvarBool('buddyOutline')
        self.game['bulletDamage'] = getCvarInt('bulletDamage')
        self.game['friendlyFire'] = getCvarBool('friendlyFire')
        self.game['gameModeCounter'] = getCvarInt('gameModeCounter')
        self.game['gamePassword'] = getCvar('gamePassword')
        self.game['hardcoreBulletDamageOverride'] = getCvarBool('hardcoreBulletDamageOverride')
        self.game['hudBuddyInfo'] = getCvarBool('hudBuddyInfo')
        self.game['hudClassAbility'] = getCvarBool('hudClassAbility')
        self.game['hudCrosshair'] = getCvarBool('hudCrosshair')
        self.game['hudEnemyTag'] = getCvarBool('hudEnemyTag')
        self.game['hudExplosiveIcons'] = getCvarBool('hudExplosiveIcons')
        self.game['hudGameMode'] = getCvarBool('hudGameMode')
        self.game['hudHealthAmmo'] = getCvarBool('hudHealthAmmo')
        self.game['hudMinimap'] = getCvarBool('hudMinimap')
        self.game['hudObiturary'] = getCvarBool('hudObiturary')
        self.game['hudPointsTracker'] = getCvarBool('hudPointsTracker')
        self.game['hudUnlocks'] = getCvarBool('hudUnlocks')
        self.game['idleBanRounds'] = getCvarInt('idleBanRounds')
        self.game['idleTimeout'] = getCvarInt('idleTimeout')
        self.game['killCam'] = getCvarBool('killCam')
        self.game['maxPlayers'] = getCvarInt('maxPlayers')
        self.game['playerManDownTime'] = getCvarInt('playerManDownTime')
        self.game['playerRespawnTime'] = getCvarInt('playerRespawnTime')
        self.game['playlist'] = getCvar('playlist')
        self.game['ranked'] = getCvarBool('ranked')
        self.game['regenerateHealth'] = getCvarBool('regenerateHealth')
        self.game['roundRestartPlayerCount'] = getCvarInt('roundRestartPlayerCount')
        self.game['roundStartPlayerCount'] = getCvarInt('roundStartPlayerCount')
        self.game['roundsPerMap'] = getCvarInt('roundsPerMap')
        self.game['serverDescription'] = getCvar('serverDescription')
        self.game['serverName'] = getCvar('serverName')
        self.game['soldierHealth'] = getCvarInt('soldierHealth')
        self.game['teamKillCountForKick'] = getCvarInt('teamKillCountForKick')
        self.game['teamKillKickForBan'] = getCvarInt('teamKillKickForBan')
        self.game['teamKillValueDecreasePerSecond'] = getCvarFloat('teamKillValueDecreasePerSecond')
        self.game['teamKillValueForKick'] = getCvarFloat('teamKillValueForKick')
        self.game['teamKillValueIncrease'] = getCvarFloat('teamKillValueIncrease')
        self.game.timeLimit = self.game.gameModeCounter
        self.game.fragLimit = self.game.gameModeCounter
        self.game.captureLimit = self.game.gameModeCounter


    def getServerInfo(self):
        """query server info, update self.game and return query results
        Response: serverName,numPlayers,maxPlayers,gamemode,level,roundsPlayed,roundsTotal,numTeams,team1score,
                  team2score,targetScore,onlineState,isRanked,hasPunkbuster,hasPassword,serverUptime,roundTime,
                  gameIpAndPort,punkBusterVersion,joinQueueEnabled,region,closestPingSite,country
        """
        data = self.write(('serverInfo',))
        data2 = MohwParser.decodeServerinfo(data)
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
        <serverName: string> <numPlayers: integer> <maxPlayers: integer> <gamemode: string>
        <level: string> <roundsPlayed: integer> <roundsTotal: integer> <roundsPlayed: integer>
        <team1score: integer> <team2score: integer> <targetScore: integer> <onlineState: online state>
        <isRanked: boolean> <hasPunkbuster: boolean> <hasPassword: boolean> <serverUptime: seconds>
        <roundTime: seconds> <gameIpAndPort: ip:port> <punkBusterVersion: sting> <joinQueueEnabled: boolean>
        <region: string> <closestPingSite: string> <country: string>

        ['BigBrotherBot #1 MOHW', '0', '20', 'TeamDeathMatch', 'MP_10', '0', '1', '2', '0', '0', '75', '', 'true',
        'true', 'false', '143035', '49895', '', '', '', 'EU', 'i3d-ams', 'GB']
        """

        response = {
            'serverName': data[0],
            'numPlayers': data[1],
            'maxPlayers': data[2],
            'gamemode': data[3],
            'level': data[4],
            'roundsPlayed': data[5],
            'roundsTotal': data[6],
            'numTeams': data[7],
            'team1score': data[8],
            'team2score': data[9],
            'targetScore': data[10],
            'onlineState': data[11],
            'isRanked': data[12],
            'hasPunkbuster': data[13],
            'hasPassword': data[14],
            'serverUptime': data[15],
            'roundTime': data[16],
            'gameIpAndPort': data[17],
            'punkBusterVersion': data[18],
            'joinQueueEnabled': data[19],
            'region': data[20],
            'closestPingSite': data[21],
            'country': data[22],
        }

        return response

    def getFullMapRotationList(self):
        """query the Frostbite2 game server and return a MapListBlock containing all maps of the current
         map rotation list.
        """
        response = NewMapListBlock()
        tmp = self.write(('mapList.list',))
        response.append(tmp)
        return response

class NewMapListBlock(b3.parsers.frostbite2.util.MapListBlock):
    """Alters MapListBlock class since mapList.list raw data includes playlist information in MOHW
    Example raw data for MOHW: [ "2" "CustomPL" "3" "MP_03" "CombatMission" "1" "MP_05" "BombSquad" "1" ]
    """

    def append(self, data):
        """Parses and appends the maps from raw_data.
        data : words as received from the Frostbite2 mapList.list command
        """
        # validation

        if type(data) not in (tuple, list):
            raise MapListBlockError("invalid data. Expecting data as a tuple or as a list. Received '%s' instead" % type(data))

        if len(data) < 3:
            raise MapListBlockError("invalid data. Data should have at least 3 elements. %r", data)

        try:
            num_maps = int(data[0])
        except ValueError, err:
            raise MapListBlockError("invalid data. First element should be a integer, got %r" % data[0], err)

        try:
            num_words = int(data[2])
        except ValueError, err:
            raise MapListBlockError("invalid data. Second element should be a integer, got %r" % data[1], err)

        if len(data) != (3 + (num_maps * num_words)):
            raise MapListBlockError("invalid data. The total number of elements is not coherent with the number of maps declared. %s != (2 + %s * %s)" % (len(data), num_maps, num_words))

        if num_words < 3:
            raise MapListBlockError("invalid data. Expecting at least 3 words of data per map")

        if self._num_words is not None and self._num_words != num_words:
            raise MapListBlockError("cannot append data. nums_words are different from existing data.")

        # parse data
        map_data = []
        for i in range(num_maps):
            base_index = 3 + (i * num_words)
            try:
                num_rounds = int(data[base_index+2])
            except ValueError:
                raise MapListBlockError("invalid data. %sth element should be a integer, got %r" % (base_index + 2, data[base_index + 2]))
            map_data.append({'name': data[base_index+0], 'gamemode': data[base_index+1], 'num_of_rounds': num_rounds})

        # append data
        self._map_data += tuple(map_data)
        self._num_maps = len(self._map_data)
        if self._num_words is None:
            self._num_words = num_words