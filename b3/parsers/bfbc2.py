# -*- coding: utf-8 -*-

# ################################################################### #
#                                                                     #
#  BigBrotherBot(B3) (www.bigbrotherbot.net)                          #
#  Copyright (C) 2005 Michael "ThorN" Thornton                        #
#                                                                     #
#  This program is free software; you can redistribute it and/or      #
#  modify it under the terms of the GNU General Public License        #
#  as published by the Free Software Foundation; either version 2     #
#  of the License, or (at your option) any later version.             #
#                                                                     #
#  This program is distributed in the hope that it will be useful,    #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of     #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the       #
#  GNU General Public License for more details.                       #
#                                                                     #
#  You should have received a copy of the GNU General Public License  #
#  along with this program; if not, write to the Free Software        #
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA      #
#  02110-1301, USA.                                                   #
#                                                                     #
# ################################################################### #

# ============================ B3 EVENTS AVAILABLE TO PLUGIN DEVELOPERS USING THIS PARSER =============================
#
# -- standard B3 events  --
# EVT_UNKNOWN
# EVT_CLIENT_JOIN
# EVT_CLIENT_KICK
# EVT_CLIENT_SAY
# EVT_CLIENT_TEAM_SAY
# EVT_CLIENT_PRIVATE_SAY
# EVT_CLIENT_CONNECT
# EVT_CLIENT_DISCONNECT
# EVT_CLIENT_SUICIDE
# EVT_CLIENT_KILL_TEAM
# EVT_CLIENT_KILL
# EVT_GAME_WARMUP
# EVT_GAME_ROUND_START
# EVT_CLIENT_BAN_TEMP
# EVT_CLIENT_BAN
#
# -- BFBC2 specific B3 events --
# EVT_CLIENT_SPAWN
# EVT_CLIENT_SQUAD_CHANGE
# EVT_PUNKBUSTER_LOST_PLAYER
# EVT_PUNKBUSTER_SCHEDULED_TASK
# EVT_PUNKBUSTER_NEW_CONNECTION
#
# -- B3 events triggered natively by B3 core --
# EVT_CLIENT_NAME_CHANGE
# EVT_CLIENT_TEAM_CHANGE
# EVT_CLIENT_AUTH
# EVT_CLIENT_DISCONNECT

__author__  = 'Courgette, SpacepiG, Bakes'
__version__ = '2.8.1'

import time
import threading
import Queue
import b3.clients
import b3.events

from b3.functions import prefixText
from b3.parsers.frostbite.abstractParser import AbstractParser
from b3.parsers.frostbite.util import PlayerInfoBlock

SAY_LINE_MAX_LENGTH = 100

GAMETYPE_SQDM = 'SQDM'          # Squad Deathmatch. no team, but up to 4 squad fighting each others
GAMETYPE_CONQUEST = 'CONQUEST'
GAMETYPE_RUSH = 'RUSH'
GAMETYPE_SQRUSH = 'SQRUSH'      # Squad Rush

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

BUILD_NUMBER_R9 = 527791
BUILD_NUMBER_R16 = 556157
BUILD_NUMBER_R17 = 560541


class Bfbc2Parser(AbstractParser):

    gameName = 'bfbc2'
    saybigqueue = Queue.Queue()
    saybigqueuelistener = None

    _gameServerVars = (
        '3dSpotting',
        'adminPassword',
        'bannerUrl',
        'crossHair',
        'currentPlayerLimit',
        'friendlyFire',
        'gamePassword',
        'hardCore',
        'killCam',
        'maxPlayerLimit',
        'miniMap',
        'miniMapSpotting',
        'playerLimit',
        'punkBuster',
        'rankLimit',
        'ranked',
        'serverDescription',
        'teamBalance',
        'thirdPersonVehicleCameras'
    )

    ####################################################################################################################
    #                                                                                                                  #
    #   PARSER INITIALIZATION                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    def startup(self):
        """
        Called after the parser is created before run().
        """
        AbstractParser.startup(self)

        self.saybigqueuelistener = threading.Thread(target=self.saybigqueuelistenerworker)
        self.saybigqueuelistener.setDaemon(True)
        self.saybigqueuelistener.start()

        # add BFBC2 specific commands
        self._commands['messagebig'] = ('admin.yell', '%(message)s', '%(duration)s', 'player', '%(cid)s')
        self._commands['saybig'] = ('admin.yell', '%(message)s', '%(duration)s', 'all')

        # create the 'Server' client
        self.clients.newClient('Server', guid='Server', name='Server', hide=True,
                               pbid='Server', team=b3.TEAM_UNKNOWN, squad=SQUAD_NEUTRAL)

        self.verbose('gametype: %s, map: %s' %(self.game.gameType, self.game.mapName))

    def pluginsStarted(self):
        """
        Called after the parser loaded and started all plugins.
        """
        self.info('connecting all players...')
        plist = self.getPlayerList()
        for cid, p in plist.iteritems():
            client = self.clients.getByCID(cid)
            if not client:
                name = p['name']
                if 'clanTag' in p and len(p['clanTag']) > 0:
                    name = "[" + p['clanTag'] + "] " + p['name']
                self.debug('Client %s found on the server' % cid)
                client = self.clients.newClient(cid, guid=p['guid'], name=name,
                                                team=self.getTeam(p['teamId']),
                                                squad=p['squadId'], data=p)

                self.queueEvent(self.getEvent('EVT_CLIENT_JOIN', p, client))

    ####################################################################################################################
    #                                                                                                                  #
    #   OTHER METHODS                                                                                                  #
    #                                                                                                                  #
    ####################################################################################################################

    def saybigqueuelistenerworker(self):
        while self.working:
            msg = self.saybigqueue.get()
            for line in self.getWrap(self.stripColors(prefixText([self.msgPrefix], msg))):
                self.write(self.getCommand('saybig', message=line, duration=2400))
                time.sleep(self._message_delay)

    def checkVersion(self):
        version = self.output.write('version')
        self.info('server version : %s' % version)
        if version[0] != 'BFBC2':
            raise Exception("the bfbc2 parser can only work with BattleField Bad Company 2")
        if int(version[1]) < BUILD_NUMBER_R9:
            raise SystemExit("this bfbc2 parser requires a BFBC2 server R9 or later") 

    def getEasyName(self, mapname):
        """
        Change levelname to real name.
        """
        if mapname.startswith('Levels/MP_001'):
            return 'Panama Canal'
        elif mapname.startswith('Levels/MP_002'):
            return 'Valparaiso'
        elif mapname.startswith('Levels/MP_003'):
            return 'Laguna Alta'
        elif mapname.startswith('Levels/MP_004'):
            return 'Isla Inocentes'
        elif mapname.startswith('Levels/MP_005'):
            return 'Atacama Desert'
        elif mapname.startswith('Levels/MP_006'):
            return 'Arica Harbor'
        elif mapname.startswith('Levels/MP_007'):
            return 'White Pass'
        elif mapname.startswith('Levels/MP_008'):
            return 'Nelson Bay'
        elif mapname.startswith('Levels/MP_009'):
            return 'Laguna Preza'
        elif mapname.startswith('Levels/MP_012'):
            return 'Port Valdez'
        elif mapname.startswith('Levels/BC1_Oasis'):
            return 'Oasis'
        elif mapname.startswith('Levels/BC1_Harvest_Day'):
            return 'Harvest Day'
        elif mapname.startswith('Levels/MP_SP_002'):
            return 'Cold War'
        elif mapname.startswith('Levels/MP_SP_005'):
            return 'Heavy Metal'
        elif mapname.startswith('Levels/nam_mp_002'):
            return 'Vantage Point'
        elif mapname.startswith('Levels/nam_mp_003'):
            return 'Hill 137'
        elif mapname.startswith('Levels/nam_mp_005'):
            return 'Cao Son Temple'
        elif mapname.startswith('Levels/nam_mp_006'):
            return 'Phu Bai Valley'
        else:
            self.warning('unknown level name \'%s\': please report this on B3 forums' % mapname)
            return mapname

    def getHardName(self, mapname):
        """
        Change real name to level name.
        """
        mapname = mapname.lower()
        if mapname.startswith('panama canal'):
            return 'Levels/MP_001'
        elif mapname.startswith('val paraiso'):
            return 'Levels/MP_002'
        elif mapname.startswith('laguna alta'):
            return 'Levels/MP_003'
        elif mapname.startswith('isla inocentes'):
            return 'Levels/MP_004'
        elif mapname.startswith('atacama desert'):
            return 'Levels/MP_005'
        elif mapname.startswith('arica harbor'):
            return 'Levels/MP_006'
        elif mapname.startswith('white pass'):
            return 'Levels/MP_007'
        elif mapname.startswith('nelson bay'):
            return 'Levels/MP_008'
        elif mapname.startswith('laguna preza'):
            return 'Levels/MP_009'
        elif mapname.startswith('port valdez'):
            return 'Levels/MP_012'
        elif mapname.startswith('oasis'):
            return 'Levels/BC1_Oasis'
        elif mapname.startswith('harvest day'):
            return 'Levels/BC1_Harvest_Day'
        elif mapname.startswith('cold war'):
            return 'Levels/MP_SP_002'
        elif mapname.startswith('heavy metal'):
            return 'Levels/MP_SP_005'
        elif mapname.startswith('vantage point'):
            return 'levels/nam_mp_002'
        elif mapname.startswith('hill 137'):
            return 'levels/nam_mp_003'
        elif mapname.startswith('cao son temple'):
            return 'levels/nam_mp_005'
        elif mapname.startswith('phu bai valley'):
            return 'levels/nam_mp_006'
        else:
            self.warning('unknown level name \'%s\': please make sure you have entered a valid mapname' % mapname)
            return mapname

    def getTeam(self, team):
        """
        Convert BFBC2 team numbers to B3 team numbers.
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

    def getClient(self, cid, _guid=None):
        """
        Get a connected client from storage or create it
        B3 CID   <--> ingame character name
        B3 GUID  <--> EA_guid
        """
        # try to get the client from the storage of already authed clients
        client = self.clients.getByCID(cid)
        if not client:
            if cid == 'Server':
                return self.clients.newClient('Server', guid='Server', name='Server', hide=True,
                                              pbid='Server', team=b3.TEAM_UNKNOWN, squad=SQUAD_NEUTRAL)
            # must be the first time we see this client
            words = self.write(('admin.listPlayers', 'player', cid))
            pib = PlayerInfoBlock(words)
            if len(pib) == 0:
                self.debug('No such client found')
                return None
            p = pib[0]
            cid = p['name']
            name = p['name']

            # Let's see if we have a guid, either from the PlayerInfoBlock,
            # or passed to us by OnPlayerAuthenticated()
            if p['guid']:
                guid = p['guid']
            elif _guid:
                guid = _guid
            else:
                # If we still don't have a guid, we cannot create a newclient without the guid!
                self.debug('No guid for %s, waiting for next event' %name)
                return None

            if 'clanTag' in p and len(p['clanTag']) > 0:
                name = "[" + p['clanTag'] + "] " + p['name']
            client = self.clients.newClient(cid, guid=guid, name=name, team=self.getTeam(p['teamId']),
                                            teamId=int(p['teamId']), squad=p['squadId'], data=p)

            self.queueEvent(self.getEvent('EVT_CLIENT_JOIN', p, client))

        return client

    def getServerVars(self):
        """
        Update the game property from server fresh data.
        """
        try:
            self.game.is3dSpotting = self.getCvar('3dSpotting').getBoolean()
        except:
            pass
        try:
            self.game.bannerUrl = self.getCvar('bannerUrl').getString()
        except:
            pass
        try:
            self.game.crossHair = self.getCvar('crossHair').getBoolean()
        except:
            pass
        try:
            self.game.currentPlayerLimit = self.getCvar('currentPlayerLimit').getInt()
        except:
            pass
        try:
            self.game.friendlyFire = self.getCvar('friendlyFire').getBoolean()
        except:
            pass
        try:
            self.game.hardCore = self.getCvar('hardCore').getBoolean()
        except:
            pass
        try:
            self.game.killCam = self.getCvar('killCam').getBoolean()
        except:
            pass
        try:
            self.game.maxPlayerLimit = self.getCvar('maxPlayerLimit').getInt()
        except:
            pass
        try:
            self.game.miniMap = self.getCvar('miniMap').getBoolean()
        except:
            pass
        try:
            self.game.miniMapSpotting = self.getCvar('miniMapSpotting').getBoolean()
        except:
            pass
        try:
            self.game.playerLimit = self.getCvar('playerLimit').getInt()
        except:
            pass
        try:
            self.game.punkBuster = self.getCvar('punkBuster').getBoolean()
        except:
            pass
        try:
            self.game.rankLimit = self.getCvar('rankLimit').getInt()
        except:
            pass
        try:
            self.game.ranked = self.getCvar('ranked').getBoolean()
        except:
            pass
        try:
            self.game.serverDescription = self.getCvar('serverDescription').getString()
        except:
            pass
        try:
            self.game.teamBalance = self.getCvar('teamBalance').getBoolean()
        except:
            pass
        try:
            self.game.thirdPersonVehicleCameras = self.getCvar('thirdPersonVehicleCameras').getBoolean()
        except:
            pass

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENT HANDLERS                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def OnPlayerTeamchange(self, action, data):
        """
        player.onTeamChange <soldier name: player name> <team: Team ID> <squad: Squad ID>
        Effect: Player might have changed team
        """
        client = self.getClient(data[0])
        if client:
            client.teamId = int(data[1])
            client.squad = int(data[2])
            client.team = self.getTeam(data[1]) # .team setter will send team change event

    def OnPlayerSquadchange(self, action, data):
        """
        player.onSquadChange <soldier name: player name> <team: Team ID> <squad: Squad ID>
        Effect: Player might have changed squad
        """
        client = self.getClient(data[0])
        if client:
            previous_squad = client.squad
            client.squad = int(data[2])
            client.teamId = int(data[1])
            client.team = self.getTeam(data[1]) # .team setter will send team change event
            if client.squad != previous_squad:
                return self.getEvent('EVT_CLIENT_SQUAD_CHANGE', data[1:], client)

    ####################################################################################################################
    #                                                                                                                  #
    #   B3 PARSER INTERFACE IMPLEMENTATION                                                                             #
    #                                                                                                                  #
    ####################################################################################################################

    def messagebig(self, client, text):
        """
        Write a big message to a client.
        :param client: The client to who send the message
        :param text: The text to send
        """
        try:
            if client is None:
                self.saybig(text)
            elif client.cid is None:
                pass
            else:
                self.write(self.getCommand('messagebig', message=text, cid=client.cid, duration=2400))
        except:
            pass

    def saybig(self, msg):
        """
        Broadcast a message to all players in a way that will catch their attention.
        :param msg: The message to be broadcasted
        """
        self.saybigqueue.put(msg)

    def rotateMap(self):
        """
        Load the next map (not level). If the current game mod plays each level twice
        to get teams the chance to play both sides, then this rotate a second
        time to really switch to the next map.
        """
        nextIndex = self.getNextMapIndex()
        if nextIndex == -1:
            # No map in map rotation list, just call admin.runNextLevel
            self.write(('admin.runNextLevel',))
        else:
            self.write(('mapList.nextLevelIndex', nextIndex))
            self.write(('admin.runNextLevel',))

    def changeMap(self, mapname):
        """
        Change to the given map
        
        1) determine the level name
            If map is of the form 'Levels/MP_001' and 'Levels/MP_001' is a supported
            level for the current game mod, then this level is loaded.
            
            In other cases, this method assumes it is given a 'easy map name' (like
            'Port Valdez') and it will do its best to find the level name that seems
            to be for 'Port Valdez' within the supported levels.
        
            If no match is found, then instead of loading the map, this method 
            returns a list of candidate map names
            
        2) if we got a level name
            if the level is not in the current rotation list, then add it to 
            the map list and load it
        """        
        supportedMaps = self.getSupportedMaps()
        if mapname not in supportedMaps:
            match = self.getMapsSoundingLike(mapname)
            if len(match) == 1:
                mapname = match[0]
            else:
                return match
            
        if mapname in supportedMaps:
            levelnames = self.write(('mapList.list',))
            if mapname not in levelnames:
                # add the map to the map list
                nextIndex = self.getNextMapIndex()
                if nextIndex == -1:
                    self.write(('mapList.append', mapname))
                    nextIndex = 0
                else:
                    if nextIndex == 0:
                        # case where the map list contains only 1 map
                        nextIndex = 1
                    self.write(('mapList.insert', nextIndex, mapname))
            else:
                nextIndex = 0
                while nextIndex < len(levelnames) and levelnames[nextIndex] != mapname:
                    nextIndex += 1
            
            self.say('Changing map to %s' % mapname)
            time.sleep(1)
            self.write(('mapList.nextLevelIndex', nextIndex))
            self.write(('admin.runNextLevel', ))

########################################################################################################################
#                                                                                                                      #
#   APPLY SPECIFIC PARSER PATCHES TO B3 CORE MODULES                                                                   #
#                                                                                                                      #
########################################################################################################################

## add a new method to the Client class
def frostbiteClientMessageBigQueueWorker(self):
    """
    This takes a line off the queue and displays it
    in the middle of the screen then pause for
    'message_delay' seconds
    """
    while not self.messagebigqueue.empty():
        msg = self.messagebigqueue.get()
        if msg:
            self.console.messagebig(self, msg)
            time.sleep(float(self.console._message_delay))

## add the Client.messagebig() method at runtime
def frostbiteClientMessageBigMethod(self, msg):
    if msg and len(msg.strip())>0:
        # do we have a queue?
        if not hasattr(self, 'messagebigqueue'):
            self.messagebigqueue = Queue.Queue()
        # fill the queue
        text = self.console.stripColors(self.console.msgPrefix + ' [pm] ' + msg)
        for line in self.console.getWrap(text):
            self.messagebigqueue.put(line)
        # create a thread that executes the worker and pushes out the queue
        if not hasattr(self, 'messagebighandler') or not self.messagebighandler.isAlive():
            self.messagebighandler = threading.Thread(target=self.messagebigqueueworker)
            self.messagebighandler.setDaemon(True)
            self.messagebighandler.start()
        else:
            self.console.verbose('messagebighandler for %s isAlive' %self.name)

b3.clients.Client.messagebigqueueworker = frostbiteClientMessageBigQueueWorker
b3.clients.Client.messagebig = frostbiteClientMessageBigMethod