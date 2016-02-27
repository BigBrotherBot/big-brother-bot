#
# PowerAdmin Plugin for BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2008 Mark Weirath (xlr8or@xlr8or.com)
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

__version__ = '1.3'
__author__  = 'Courgette'

import b3
import b3.cron
import b3.events
import b3.plugin
import random
import string
import threading
import time

from b3.functions import getCmd
from b3.parsers.frostbite.connection import FrostbiteCommandFailedError
from b3.parsers.frostbite.util import PlayerInfoBlock

class Scrambler(object):

    _plugin = None
    _getClients_method = None
    _last_round_scores = PlayerInfoBlock([0, 0])
    
    def __init__(self):
        self._getClients_method = self._getClients_randomly

    def scrambleTeams(self):
        clients = self._getClients_method()
        if len(clients) == 0:
            return
        elif len(clients) < 3:
            self.debug("Too few players to scramble")
        else:
            self._scrambleTeams(clients)

    def setStrategy(self, strategy):
        """Set the scrambling strategy"""
        if strategy.lower() == 'random':
            self._getClients_method = self._getClients_randomly
        elif strategy.lower() == 'score':
            self._getClients_method = self._getClients_by_scores
        else: 
            raise ValueError

    def onRoundOverTeamScores(self, playerInfoBlock):
        self._last_round_scores = playerInfoBlock

    def _scrambleTeams(self, listOfPlayers):
        team = 0
        while len(listOfPlayers) > 0:
            self._plugin._movePlayer(listOfPlayers.pop(), team + 1)
            team = (team + 1) % 2

    def _getClients_randomly(self):
        clients = self._plugin.console.clients.getList()
        random.shuffle(clients)
        return clients

    def _getClients_by_scores(self):
        allClients = self._plugin.console.clients.getList()
        self.debug('all clients : %r' % [x.cid for x in allClients])
        sumofscores = reduce(lambda z, y: z + y, [int(data['score']) for data in self._last_round_scores], 0)
        self.debug('sum of scores is %s' % sumofscores)
        if sumofscores == 0:
            self.debug('no score to sort on, using ramdom strategy instead')
            random.shuffle(allClients)
            return allClients
        else:
            sortedScores = sorted(self._last_round_scores, key=lambda z: z['score'])
            self.debug('sorted score : %r' % sortedScores)
            sortedClients = []
            for cid in [x['name'] for x in sortedScores]:
                # find client object for each player score
                clients = [c for c in allClients if c.cid == cid]
                if clients and len(clients) > 0:
                    allClients.remove(clients[0])
                    sortedClients.append(clients[0])
            self.debug('sorted clients A : %r' % map(lambda z: z.cid, sortedClients))
            random.shuffle(allClients)
            for client in allClients:
                # add remaining clients (they had no score ?)
                sortedClients.append(client)
            self.debug('sorted clients B : %r' % map(lambda z: z.cid, sortedClients))
            return sortedClients

    def debug(self, msg):
        self._plugin.debug('scramber:\t %s' % msg)


class PoweradminmohPlugin(b3.plugin.Plugin):

    requiresParsers = ['moh']

    _adminPlugin = None
    
    _enableTeamBalancer = False
    _ignoreBalancingTill = 0
    _tinterval = 0
    _teamdiff = 1
    _tcronTab = None
    _tmaxlevel = 100
    
    _matchmode = False
    _match_plugin_disable = []
    _matchManager = None
    
    _scrambling_planned = False
    _autoscramble_rounds = False
    _autoscramble_maps = False
    _scrambler = Scrambler()

    ####################################################################################################################
    #                                                                                                                  #
    #    STARTUP                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def onLoadConfig(self):
        """
        Load plugin configuration
        """
        self._scrambler._plugin = self
        self.loadTeamBalancer()
        self.loadMatchMode()
        self.loadScrambler()

    def onStartup(self):
        """
        Initialize plugin settings.
        """
        # get the admin plugin so we can register commands
        self._adminPlugin = self.console.getPlugin('admin')
        if not self._adminPlugin:
            raise AttributeError('could not find admin plugin')

        if 'commands' in self.config.sections():
            for cmd in self.config.options('commands'):
                level = self.config.get('commands', cmd)
                sp = cmd.split('-')
                alias = None
                if len(sp) == 2:
                    cmd, alias = sp
                func = getCmd(self, cmd)
                if func:
                    self._adminPlugin.registerCommand(self, cmd, level, func, alias)
    
        # do not balance on the 1st minute after bot start
        self._ignoreBalancingTill = self.console.time() + 60
        
        # register our events
        self.registerEvent('EVT_CLIENT_TEAM_CHANGE', self.onTeamChange)
        self.registerEvent('EVT_GAME_ROUND_START', self.onRoundStart)
        self.registerEvent('EVT_GAME_ROUND_PLAYER_SCORES', self.onGameRoundPlayerScores)
        self.registerEvent('EVT_CLIENT_AUTH', self.onClientAuth)
        self.registerEvent('EVT_CLIENT_DISCONNECT', self.onClientDisconnect)

    def loadTeamBalancer(self):
        """
        Load teambalancer settings.
        """
        try:
            self._enableTeamBalancer = self.config.getboolean('teambalancer', 'enabled')
        except Exception:
            self._enableTeamBalancer = False
            self.debug('using default value (%s) for Teambalancer enabled', self._enableTeamBalancer)

        try:
            self._tmaxlevel = self.config.getint('teambalancer', 'maxlevel')
        except Exception:
            self._tmaxlevel = 100
            self.debug('using default value (%s) for Teambalancer maxlevel', self._tmaxlevel)

        try:
            self._tinterval = self.config.getint('teambalancer', 'checkInterval')
            # set a max interval for teamchecker
            if self._tinterval > 59:
                self._tinterval = 59
        except Exception:
            self._tinterval = 0
            self.debug('using default value (%s) for Teambalancer Interval', self._tinterval)

        try:
            self._teamdiff = self.config.getint('teambalancer', 'maxDifference')
            # set a minimum/maximum teamdifference
            if self._teamdiff < 1:
                self._teamdiff = 1
            if self._teamdiff > 9:
                self._teamdiff = 9
        except Exception:
            self._teamdiff = 1
            self.debug('using default value (%s) for teamdiff', self._teamdiff)
        
        self.debug('teambalancer enabled: %s' % self._tinterval)
        self.debug('teambalancer maxlevel: %s' % self._tmaxlevel)
        self.debug('teambalancer check interval (in minute): %s' % self._tinterval)
        self.debug('teambalancer max team difference: %s' % self._teamdiff)

        if self._tcronTab:
            # remove existing crontab
            self.console.cron - self._tcronTab
        if self._tinterval > 0:
            self._tcronTab = b3.cron.PluginCronTab(self, self.autobalance, 0, '*/%s' % self._tinterval)
            self.console.cron + self._tcronTab

    def loadMatchMode(self):
        """
        Setup the match mode
        """
        self._match_plugin_disable = self.getSetting('matchmode', 'plugins_disable', b3.LIST, [])

        try:
            # load all the configuration files into a dict
            for key, value in self.config.items('matchmode_configs'):
                self._gameconfig[key] = value
        except (b3.config.NoSectionError, b3.config.NoOptionError, KeyError), e:
            self.warning('could not read matchmode configs: %s' % e)

    def loadScrambler(self):
        """
        Load scrambler configuration.
        """
        try:
            strategy = self.config.get('scrambler', 'strategy')
            self._scrambler.setStrategy(strategy)
            self.debug("scrambling strategy '%s' set" % strategy)
        except Exception:
            self._scrambler.setStrategy('random')
            self.debug('using default value (%s) for scrambling strategy', self._enableTeamBalancer)

        try:
            mode = self.config.get('scrambler', 'mode')
            if mode not in ('off', 'round', 'map'):
                raise ValueError
            if mode == 'off':
                self._autoscramble_rounds = False
                self._autoscramble_maps = False
            elif mode == 'round':
                self._autoscramble_rounds = True
                self._autoscramble_maps = False
            elif mode == 'map':
                self._autoscramble_rounds = False
                self._autoscramble_maps = True
            self.debug('auto scrambler mode is : %s' % mode)
        except Exception:
            self._autoscramble_rounds = False
            self._autoscramble_maps = False
            self.warning('using default value (off) for auto scrambling mode')

    ####################################################################################################################
    #                                                                                                                  #
    #    EVENTS                                                                                                        #
    #                                                                                                                  #
    ####################################################################################################################

    def onClientDisconnect(self, _):
        """
        Handle EVT_CLIENT_DISCONNECT
        """
        # do not balance just after a player disconnected
        self._ignoreBalancingTill = self.console.time() + 10

    def onClientAuth(self, event):
        """
        Handle EVT_CLIENT_AUTH.
        """
        event.client.setvar(self, 'teamtime', self.console.time())

    def onGameRoundPlayerScores(self, event):
        """
        Handle EVT_GAME_ROUND_PLAYER_SCORES.
        """
        self._scrambler.onRoundOverTeamScores(event.data)

    def onRoundStart(self, _):
        """
        Handle EVT_GAME_ROUND_START.
        """
        self.debug('match mode : '.rjust(30) + str(self._matchmode))
        self.debug('manual scramble planned : '.rjust(30) + str(self._scrambling_planned))
        self.debug('auto scramble rounds : '.rjust(30) + str(self._autoscramble_rounds))
        self.debug('auto scramble maps : '.rjust(30) + str(self._autoscramble_maps))
        self.debug('self.console.game.rounds : '.rjust(30) + repr(self.console.game.rounds))
        # do not balance on the 1st minute after bot start
        self._ignoreBalancingTill = self.console.time() + 60
        if self._scrambling_planned:
            self.debug('manual scramble is planned')
            self._scrambler.scrambleTeams()
            self._scrambling_planned = False
        elif self._matchmode:
            self.debug('match mode on, ignoring autosramble')
        else:
            if self._autoscramble_rounds:
                self.debug('auto scramble is planned for rounds')
                self._scrambler.scrambleTeams()
            elif self._autoscramble_maps and self.console.game.rounds == 0:
                self.debug('auto scramble is planned for maps')
                self._scrambler.scrambleTeams()

    def onTeamChange(self, event):
        """
        Handle EVT_CLIENT_TEAM_CHANGE
        """
        client = event.client

        # was this team change make by the player or forced by the bot ?
        wasForcedByBot = client.var(self, 'movedByBot', False).value
        if wasForcedByBot is True:
            self.debug('client was moved over by the bot, don\'t reduce teamtime and don\'t check')
            client.delvar(self, 'movedByBot')
            return
        else:
            #store the time of teamjoin for autobalancing purposes 
            client.setvar(self, 'teamtime', self.console.time())
            self.verbose('client variable teamtime set to: %s' % client.var(self, 'teamtime').value)
        
        if self._enableTeamBalancer:
            if self.console.time() < self._ignoreBalancingTill:
                self.debug('ignoring team balancing right now')
                return
            
            if client.team in (b3.TEAM_SPEC, b3.TEAM_UNKNOWN):
                return
            
            # get teams
            team1players, team2players = self.getTeams()
            
            # if teams are uneven by one or even, then stop here
            if abs(len(team1players) - len(team2players)) <= 1:
                return
            
            biggestteam = team1players
            if len(team2players) > len(team1players):
                biggestteam = team2players
            
            # has the current player gone contributed to making teams uneven ?
            if client.cid in biggestteam:
                self.debug('%s has contributed to unbalance the teams')
                client.message('do not make teams unbalanced')
                if client.teamId == 1:
                    newteam = '2'
                else:
                    newteam = '1' 
                self._movePlayer(client, newteam)
                # do not autobalance right after that
                self._ignoreBalancingTill = self.console.time() + 10

    ####################################################################################################################
    #                                                                                                                  #
    #    COMMANDS                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################
    
    def cmd_pb_sv_command(self, data, client, cmd=None):
        """
        <punkbuster command> - Execute a punkbuster command
        """
        if not data:
            client.message('missing paramter, try !help pb_sv_command')
        else:
            self.debug('Executing punkbuster command = [%s]', data)
            try:
                self.console.write(('punkBuster.pb_sv_command', '%s' % data))
            except FrostbiteCommandFailedError, err:
                self.error(err)
                client.message('Error: %s' % err.message)


    def cmd_runnextround(self, data, client, cmd=None):
        """
        Switch to next round, without ending current
        """
        self.console.say('forcing next round')
        time.sleep(1)
        try:
            self.console.write(('admin.runNextRound',))
        except FrostbiteCommandFailedError, err:
            client.message('Error: %s' % err.message)
        
    def cmd_restartround(self, data, client, cmd=None):
        """
        Restart current round
        """
        self.console.say('Restart current round')
        time.sleep(1)
        try:
            self.console.write(('admin.restartRound',))
        except FrostbiteCommandFailedError, err:
            client.message('Error: %s' % err.message)

    def cmd_kill(self, data, client, cmd=None):
        """
        <player> Kill a player without scoring effects
        """
        # this will split the player name and the message
        x = self._adminPlugin.parseUserCmd(data)
        if x:
            sclient = self._adminPlugin.findClientPrompt(x[0], client)
            if not sclient:
                # a player matchin the name was not found, a list of closest matches will be displayed
                # we can exit here and the user will retry with a more specific player
                return
            else:
                try:
                    self.console.write(('admin.killPlayer', sclient.cid))
                except FrostbiteCommandFailedError, err:
                    client.message('Error: %s' % err.message)

    def cmd_reserveslot(self, data, client, cmd=None):
        """
        <player> add player to the list of players who can use the reserved slots
        """
        # this will split the player name and the message
        x = self._adminPlugin.parseUserCmd(data)
        if x:
            sclient = self._adminPlugin.findClientPrompt(x[0], client)
            if not sclient:
                # a player matchin the name was not found, a list of closest matches will be displayed
                # we can exit here and the user will retry with a more specific player
                return
            else:
                try:
                    self.console.write(('reservedSpectateSlots.load',))
                    self.console.write(('reservedSpectateSlots.addPlayer', sclient.cid))
                    self.console.write(('reservedSpectateSlots.save',))
                    client.message('%s added to reserved slots list' % sclient.cid)
                    sclient.message('You now have access to reserved slots thanks to %s' % client.cid)
                except FrostbiteCommandFailedError, err:
                    if err.message == ['PlayerAlreadyInList']:
                        client.message('%s already has access to reserved slots' % sclient.cid)
                    else:
                        client.message('Error: %s' % err.message)

    def cmd_unreserveslot(self, data, client, cmd=None):
        """
        <player> remove player from the list of players who can use the reserved slots
        """
        # this will split the player name and the message
        x = self._adminPlugin.parseUserCmd(data)
        if x:
            sclient = self._adminPlugin.findClientPrompt(x[0], client)
            if not sclient:
                # a player matchin the name was not found, a list of closest matches will be displayed
                # we can exit here and the user will retry with a more specific player
                return
            else:
                try:
                    self.console.write(('reservedSpectateSlots.load',))
                    self.console.write(('reservedSpectateSlots.removePlayer', sclient.cid))
                    self.console.write(('reservedSpectateSlots.save',))
                    client.message('%s removed from reserved slots list' % sclient.cid)
                    sclient.message('You don\'t have access to reserved slots anymore')
                except FrostbiteCommandFailedError, err:
                    if err.message == ['PlayerNotInList']:
                        client.message('%s has no access to reserved slots' % sclient.cid)
                    else:
                        client.message('Error: %s' % err.message)

    def cmd_spect(self, data, client, cmd=None):
        """
        <player> send a player to spectator mode
        """
        # this will split the player name and the message
        x = self._adminPlugin.parseUserCmd(data)
        if x:
            sclient = self._adminPlugin.findClientPrompt(x[0], client)
            if not sclient:
                # a player matchin the name was not found, a list of closest matches will be displayed
                # we can exit here and the user will retry with a more specific player
                return
            else:
                try:
                    self._movePlayer(sclient, 3)
                except FrostbiteCommandFailedError, err:
                    client.message('Error: %s' % err.message)

    def cmd_changeteam(self, data, client, cmd=None):
        """
        <name> - change a player to the other team
        """
        x = self._adminPlugin.parseUserCmd(data)
        if not x:
            client.message('Invalid data, try !help changeteam')
        else:
            # input[0] is the player id
            sclient = self._adminPlugin.findClientPrompt(x[0], client)
            if sclient:
                if sclient.teamId == 1:
                    newteam = '2'
                else:
                    newteam = '1' 
                self._movePlayer(sclient, newteam)
                cmd.sayLoudOrPM(client, '%s forced to the other team' % sclient.cid)

    def cmd_scramble(self, data, client, cmd=None):
        """
        Toggle on/off the teams scrambling for next round
        """
        if self._scrambling_planned:
            self._scrambling_planned = False
            client.message('Teams scrambling canceled for next round')
        else:
            self._scrambling_planned = True
            client.message('Teams will be scrambled at next round start')

    def cmd_scramblemode(self, data, client, cmd=None):
        """
        <random|score> change the scrambling strategy
        """
        if not data:
            client.message("Invalid data: expecting 'random' or 'score'")
        else:
            if data[0].lower() == 'r':
                self._scrambler.setStrategy('random')
                client.message('Scrambling strategy is now: random')
            elif data[0].lower() == 's':
                self._scrambler.setStrategy('score')
                client.message('Scrambling strategy is now: score')
            else:
                client.message("Invalid data: expecting 'random' or 'score'")

    def cmd_autoscramble(self, data, client, cmd=None):
        """
        <off|round|map> manage the auto scrambler
        """
        if not data:
            client.message("Invalid data: expecting one of [off, round, map]")
        else:
            if data.lower() == 'off':
                self._autoscramble_rounds = False
                self._autoscramble_maps = False
                client.message('Auto scrambler now disabled')
            elif data[0].lower() == 'r':
                self._autoscramble_rounds = True
                self._autoscramble_maps = False
                client.message('Auto scrambler will run at every round start')
            elif data[0].lower() == 'm':
                self._autoscramble_rounds = False
                self._autoscramble_maps = True
                client.message('Auto scrambler will run at every map change')
            else:
                client.message("Invalid data: expecting one of [off, round, map]")

    def cmd_swap(self, data, client, cmd=None):
        """
        <player A> <player B> - swap teams for player A and B if they are in different teams
        """
        x = self._adminPlugin.parseUserCmd(data)
        if not input:
            client.message('Invalid data, try !help swap')
            return

        pA = x[0]

        if len(x) == 1 or x[1] is None:
            client.message('Invalid data, try !help swap')
            return
                
        x = self._adminPlugin.parseUserCmd(x[1])
        if not x:
            client.message('Invalid data, try !help swap')
            return

        pB = x[0]
        
        sclientA = self._adminPlugin.findClientPrompt(pA, client)
        if not sclientA:
            return

        sclientB = self._adminPlugin.findClientPrompt(pB, client)
        if not sclientB:
            return

        if sclientA.teamId not in (1, 2) and sclientB.teamId not in (1, 2):
            client.message('could not determine players teams')
            return

        if sclientA.teamId == sclientB.teamId:
            client.message('both players are in the same team. Cannot swap')
            return

        teamA = sclientA.teamId
        teamB = sclientB.teamId
        teamA, teamB = teamB, teamA
        self._movePlayer(sclientA, teamA)
        self._movePlayer(sclientB, teamB)
        cmd.sayLoudOrPM(client, 'swapped player %s with %s' % (sclientA.cid, sclientB.cid))

    def cmd_teams(self ,data , client, cmd=None):
        """
        Make the teams balanced
        """
        if client:
            team1players, team2players = self.getTeams()
            self.debug('team1players: %s' % team1players)
            self.debug('team2players: %s' % team2players)
            # if teams are uneven by one or even, then stop here
            gap = abs(len(team1players) - len(team2players))
            if gap <= 1:
                client.message('Teams are balanced, %s vs %s (diff: %s)' %(len(team1players), len(team2players), gap))
            else:
                self.teambalance()

    def cmd_teambalance(self, data, client=None, cmd=None):
        """
        <on/off> - Set teambalancer on/off
        Setting teambalancer on will warn players that make teams unbalanced
        """
        if not data:
            if client:
                if self._enableTeamBalancer:
                    client.message("Team balancing is on")
                else:
                    client.message("Team balancing is off")
            else:
                self.debug('No data sent to cmd_teambalance')
        else:
            if data.lower() in ('on', 'off'):
                if data.lower() == 'off':
                    self._enableTeamBalancer = False
                    client.message('Teambalancer is now disabled')
                elif data.lower() == 'on':
                    self._enableTeamBalancer = True
                    client.message('Teambalancer is now enabled')
            else:
                if client:
                    client.message("Invalid data, expecting 'on' or 'off'")
                else:
                    self.debug('Invalid data sent to cmd_teambalance : %s' % data)

    def cmd_match(self, data, client, cmd=None): 
        """
        <on/off> - Set server match mode on/off
        """
        if not data or str(data).lower() not in ('on','off'):
            client.message('Invalid or missing data, expecting "on" or "off"')
        else:

            if data.lower() == 'on':
                
                self._matchmode = True
                self._enableTeamBalancer = False
                
                for e in self._match_plugin_disable:
                    self.debug('Disabling plugin %s' %e)
                    plugin = self.console.getPlugin(e)
                    if plugin:
                        plugin.disable()
                        client.message('Plugin %s disabled' % e)
                
                self.console.say('match mode: ON')
                if self._matchManager:
                    self._matchManager.stop()
                self._matchManager = MatchManager(self)
                self._matchManager.initMatch()

            elif data.lower() == 'off':
                self._matchmode = False
                if self._matchManager:
                    self._matchManager.stop()
                self._matchManager = None
                
                # enable plugins
                for e in self._match_plugin_disable:
                    self.debug('Enabling plugin %s' %e)
                    plugin = self.console.getPlugin(e)
                    if plugin:
                        plugin.enable()
                        client.message('Plugin %s enabled' % e)

                self.console.say('Match mode: OFF')
        
    def cmd_setnextmap(self, data, client=None, cmd=None):
        """
        <mapname> - Set the nextmap (partial map name works)
        """
        if not data:
            client.message('Invalid or missing data, try !help setnextmap')
        else:
            match = self.console.getMapsSoundingLike(data)
            if len(match) > 1:
                client.message('Do you mean: %s ?' % string.join(match,', '))
                return
            if len(match) == 1:
                levelname = match[0]
                
                currentLevelCycle = self.console.write(('mapList.list',))
                try:
                    newIndex = currentLevelCycle.index(levelname)
                    self.console.write(('mapList.nextLevelIndex', newIndex))
                except ValueError:
                    # the wanted map is not in the current cycle
                    # insert the map in the cycle
                    mapindex = self.console.write(('mapList.nextLevelIndex',))
                    self.console.write(('mapList.insert', mapindex, levelname))
                if client:
                    cmd.sayLoudOrPM(client, 'nextmap set to %s' % self.console.getEasyName(levelname))
            else:
                client.message('Do you mean: %s.' % ", ".join(data))
      
    ####################################################################################################################
    #                                                                                                                  #
    #    OTHER METHODS                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def getTeams(self):
        """
        Return two lists containing the names of players from both teams.
        """
        team1players = []
        team2players = []
        for name, clientdata in self.console.getPlayerList().iteritems():
            if str(clientdata['teamId']) == '1':
                team1players.append(name)
            elif str(clientdata['teamId']) == '2':
                team2players.append(name)
        return team1players, team2players

    def autobalance(self):
        """
        Executed from cron.
        """
        if self._enableTeamBalancer is False:
            return
        if self.console.time() < self._ignoreBalancingTill:
            self.debug('ignoring team balancing as the round started less than 1 minute ago')
            return
        self.teambalance()
        
    def teambalance(self):
        """
        Balance teams.
        """
        team1players, team2players = self.getTeams()
        
        # if teams are uneven by one or even, then stop here
        gap = abs(len(team1players) - len(team2players))
        if gap <= self._teamdiff:
            self.verbose('Teambalancer: Teams are balanced, T1: %s, T2: %s '
                         '(diff: %s, tolerance: %s)' % (len(team1players), len(team2players), gap, self._teamdiff))
            return
        
        howManyMustSwitch = int(gap / 2)
        bigTeam = 1
        smallTeam = 2
        if len(team2players) > len(team1players):
            bigTeam = 2
            smallTeam = 1
            
        self.verbose('Teambalance: Teams are NOT balanced, '
                     'T1: %s, T2: %s (diff: %s)' %(len(team1players), len(team2players), gap))

        ## we need to change team for howManyMustSwitch players from bigteam
        playerTeamTimes = {}
        clients = self.console.clients.getList()
        for c in clients:
            if c.teamId == bigTeam:
                playerTeamTimes[c] = c.var(self, 'teamtime', self.console.time()).value
        #self.debug('playerTeamTimes: %s' % playerTeamTimes)
        sortedPlayersTeamTimes = sorted(playerTeamTimes.iteritems(), key=lambda (k,v):(v,k), reverse=True)
        #self.debug('sortedPlayersTeamTimes: %s' % sortedPlayersTeamTimes)


        playersToMove = [c for (c,teamtime) in sortedPlayersTeamTimes if c.maxLevel<self._tmaxlevel][:howManyMustSwitch]
        self.console.say('forcing %s to the other team' % (', '.join([c.name for c in playersToMove])))
        for c in playersToMove:
            self._movePlayer(c, smallTeam)
             
                
    def _movePlayer(self, client, newTeamId):
        """
        Move a player into a different team
        """
        try:
            client.setvar(self, 'movedByBot', True)
            self.console.write(('admin.movePlayer', client.cid, newTeamId, 'true'))
        except FrostbiteCommandFailedError, err:
            self.warning('Error, server replied %s' % err)

class MatchManager(object):

    _adminPlugin = None

    console = None
    countDown = 10
    plugin = None
    playersReady = {}
    running = True
    timer = None
    countdownStarted = None
    
    def __init__(self, plugin):
        self.plugin = plugin
        self.console = plugin.console
        self._adminPlugin = self.console.getPlugin('admin')
        if not self._adminPlugin:
            # something is wrong, can't start without admin plugin
            raise AttributeError('could not find admin plugin')
    
    def stop(self):
        try:
            self.timer.cancel()
        except:
            pass
        self.running = False
        self.unregisterCommandReady()
        
    def initMatch(self):
        for c in self.console.clients.getList():
            c.setvar(self.plugin, 'ready', False)
        self.countdownStarted = False
        self.registerCommandReady()
        self.console.say('MATCH starting soon !!')
        self.console.say('ALL PLAYERS : type !ready when you are ready')
        self.timer = threading.Timer(10.0, self._checkIfEveryoneIsReady)
        self.timer.start()
    
    def registerCommandReady(self):
        self._adminPlugin.registerCommand(self.plugin, 'ready', 0, self.cmd_ready)
    
    def unregisterCommandReady(self):
        # unregister the !ready command
        try:
            cmd = self._adminPlugin._commands['ready']
            if cmd.plugin == self.plugin:
                self.plugin.debug('unregister !ready command')
                del self._adminPlugin._commands['ready']
        except KeyError:
            pass
    
    def sayToClient(self, message, client):
        """
        We need this to bypass the message queue managed by the frostbite parser.
        """
        self.console.write(('admin.say', message, 'player', client.cid))

    def _checkIfEveryoneIsReady(self):
        self.console.debug('checking if all players are ready')
        isAllPlayersReady = True
        waitingForPlayers = []
        for c in self.console.clients.getList():
            isReady = c.var(self.plugin, 'ready', False).value
            self.plugin.debug('is %s ready ? %s' % (c.cid, isReady))
            if isReady is False:
                waitingForPlayers.append(c)
                self.sayToClient('we are waiting for you. type !ready', c)
                isAllPlayersReady = False
    
        if 0 < len(waitingForPlayers) <= 6:
            self.console.say('waiting for %s' % ', '.join([c.cid for c in waitingForPlayers]))
        
        try:
            self.timer.cancel()
        except:
            pass
        
        if isAllPlayersReady is True:
            self.console.say('All players are ready, starting count down')
            self.countDown = 10
            self.countdownStarted = True
            self.timer = threading.Timer(0.9, self._countDown)
        else:
            self.timer = threading.Timer(10.0, self._checkIfEveryoneIsReady)
            
        if self.running:
            self.timer.start()

    def _countDown(self):
        self.plugin.debug('countdown: %s' % self.countDown)
        if self.countDown > 0:
            self.console.write(('admin.say', 'MATCH STARTING IN %s' % self.countDown, 'all'))
            self.countDown -= 1
            if self.running:
                self.timer = threading.Timer(1.0, self._countDown)
                self.timer.start()
        else:    
            # make sure to have a brief big text
            self.console.write(('admin.say', 'FIGHT !!!', 'all'))
            self.console.say('Match started. GL & HF')
            self.console.write(('admin.restartRound',))
            self.stop()

    def cmd_ready(self, data, client, cmd=None): 
        """
        Notify other teams you are ready to start the match
        """
        self.plugin.debug('MatchManager::ready(%s)' % client.cid)
        if self.countdownStarted:
            client.message('Count down already started. You cannot change your ready state')
        else:
            wasReady = client.var(self.plugin, 'ready', False).value
            if wasReady:
                client.setvar(self.plugin, 'ready', False)
                self.sayToClient('You are not ready anymore', client)
                client.message('You are not ready anymore')
            else:
                client.setvar(self.plugin, 'ready', True)
                self.sayToClient('You are now ready', client)
                client.message('You are now ready')
            self._checkIfEveryoneIsReady()