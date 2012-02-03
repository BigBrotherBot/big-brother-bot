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
# CHANGELOG
# 0.1
#  functionnal parser but BF3 admin protocol is not fully implemented on the BF3 side. See TODOs
#
from b3.parsers.frostbite2.abstractParser import AbstractParser
from b3.parsers.frostbite2.util import PlayerInfoBlock
import b3
import b3.events
__author__  = 'Courgette'
__version__ = '0.1'


SAY_LINE_MAX_LENGTH = 128

SQUAD_NOSQUAD = 0
SQUAD_ALPHA = 1
SQUAD_BRAVO = 2
SQUAD_CHARLIE = 3
SQUAD_DELTA = 4
SQUAD_ECHO = 5
SQUAD_FOXTROT = 6
SQUAD_GOLF = 7
SQUAD_HOTEL = 8
SQUAD_NEUTRAL = 24

GAME_MODES_NAMES = {
    "ConquestLarge0": "Conquest64",
    "ConquestSmall0": "Conquest",
    "ConquestSmall1": "Conquest Assault",
    "RushLarge0": "Rush",
    "SquadRush0": "Squad Rush",
    "SquadDeathMatch0": "Squad Deathmatch",
    "TeamDeathMatch0": "Team Deathmatch",
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
    )


    def startup(self):
        AbstractParser.startup(self)
        
        # create the 'Server' client
        self.clients.newClient('Server', guid='Server', name='Server', hide=True, pbid='Server', team=b3.TEAM_UNKNOWN, squad=None)

        self.load_conf_max_say_line_length()
        self.load_config_message_delay()

        self.verbose('GameType: %s, Map: %s' %(self.game.gameType, self.game.mapName))
        

    def pluginsStarted(self):
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

    def saybig(self, msg):
        """\
        broadcast a message to all players in a way that will catch their attention.
        """
        return self.say(msg)

    def message(self, client, text):
        try:
            if client is None:
                self.say(text)
            elif client.cid is None:
                pass
            else:
                #self.write(self.getCommand('message', message=text, cid=client.cid)) # TODO: uncomment this once private chat is working
                if client.teamId is not None and client.squad is not None:
                # until private chat works, we try to send the message to the squad only
                    self.write(self.getCommand('saySquad', message=text, teamId=client.teamId, squadId=client.squad))
                elif client.teamId:
                    # or the team only
                    self.write(self.getCommand('sayTeam', message=text, teamId=client.teamId))
                else:
                    # or fallback on all players
                    self.say(text)
        except Exception, err:
            self.warning(err)
        
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



    def load_config_message_delay(self):
        if self.config.has_option('bf3', 'message_delay'):
            try:
                delay_sec = self.config.getfloat('bf3', 'message_delay')
                if delay_sec > 3:
                    self.warning('message_delay cannot be greater than 3')
                    delay_sec = 3
                if delay_sec < .5:
                    self.warning('message_delay cannot be less than 0.5 second.')
                    delay_sec = .5
                self._settings['message_delay'] = delay_sec
            except Exception, err:
                self.error(
                    'failed to read message_delay setting "%s" : %s' % (self.config.get('bf3', 'message_delay'), err))
        self.debug('message_delay: %s' % self._settings['message_delay'])


    def load_conf_max_say_line_length(self):
        if self.config.has_option('bf3', 'max_say_line_length'):
            try:
                maxlength = self.config.getint('bf3', 'max_say_line_length')
                if maxlength > SAY_LINE_MAX_LENGTH:
                    self.warning('max_say_line_length cannot be greater than %s' % SAY_LINE_MAX_LENGTH)
                    maxlength = SAY_LINE_MAX_LENGTH
                if maxlength < 20:
                    self.warning('max_say_line_length is way too short. using minimum value 20')
                    maxlength = 20
                self._settings['line_length'] = maxlength
                self._settings['min_wrap_length'] = maxlength
            except Exception, err:
                self.error('failed to read max_say_line_length setting "%s" : %s' % (
                    self.config.get('bf3', 'max_say_line_length'), err))
        self.debug('line_length: %s' % self._settings['line_length'])


    def checkVersion(self):
        version = self.output.write('version')
        self.info('server version : %s' % version)
        if version[0] != 'BF3':
            raise Exception("the bf3 parser can only work with Battlefield 3")

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
        if mapname == 'grand bazaar':
            return 'MP_001'
        elif mapname == 'tehran highway':
            return 'MP_003'
        elif mapname == 'caspian border':
            return 'MP_007'
        elif mapname == 'seine crossing':
            return 'MP_011'
        elif mapname == 'operation firestorm':
            return 'MP_012'
        elif mapname == 'damavand peak':
            return 'MP_013'
        elif mapname == 'noshahar canals':
            return 'MP_017'
        elif mapname == 'kharg island':
            return 'MP_018'
        elif mapname == 'operation metro':
            return 'MP_Subway'
        elif mapname == 'strike at karkand':
            return 'XP1_001'
        elif mapname == 'gulf of oman':
            return 'XP1_002'
        elif mapname == 'sharqi peninsula':
            return 'XP1_003'
        elif mapname == 'wake island':
            return 'XP1_004'
        else:
            self.warning('unknown level name \'%s\'. Please make sure you have entered a valid mapname' % mapname)
            return mapname

    def getEasyName(self, mapname):
        """ Change levelname to real name """
        if mapname == 'MP_001':
            return 'Grand Bazaar'
        elif mapname == 'MP_003':
            return 'Tehran Highway'
        elif mapname == 'MP_007':
            return 'Caspian Border'
        elif mapname == 'MP_011':
            return 'Seine Crossing'
        elif mapname == 'MP_012':
            return 'Operation Firestorm'
        elif mapname == 'MP_013':
            return 'Damavand Peak'
        elif mapname == 'MP_017':
            return 'Noshahar Canals'
        elif mapname == 'MP_018':
            return 'Kharg Island'
        elif mapname == 'MP_Subway':
            return 'Operation Metro'
        elif mapname == 'XP1_001':
            return 'Strike At Karkand'
        elif mapname == 'XP1_002':
            return 'Gulf of Oman'
        elif mapname == 'XP1_003':
            return 'Sharqi Peninsula'
        elif mapname == 'XP1_004':
            return 'Wake Island'
        else:
            self.warning('unknown level name \'%s\'. Please report this on B3 forums' % mapname)
            return mapname

    def getGameMode(self, gamemode_id):
        """ Get game mode in real name """
        if gamemode_id in GAME_MODES_NAMES:
            return GAME_MODES_NAMES[gamemode_id]
        else:
            self.warning("unknown gamemode \"%s\"" % gamemode_id)
            # fallback by sending gamemode id
            return gamemode_id

    def getSupportedMapIds(self):
        """return a list of supported levels for the current game mod"""
        # TODO : remove this method once the method on from AbstractParser is working
        return ["MP_001", "MP_003", "MP_007", "MP_011", "MP_012", "MP_013", "MP_017", "MP_018", "MP_Subway", "XP1_001", "XP1_002", "XP1_003", "XP1_004"]

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

