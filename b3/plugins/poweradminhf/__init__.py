# PowerAdmin Plugin for BigBrotherBot(B3) (www.bigbrotherbot.com)
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

__version__ = '0.4'
__author__  = 'xlr8or, Courgette'

import b3
import b3.events
import b3.plugin
import threading

from b3.config import NoOptionError
from b3.functions import getCmd


class PoweradminhfPlugin(b3.plugin.Plugin):

    _adminPlugin = None
    _enableTeamBalancer = None
    
    _matchmode = False
    _match_plugin_disable = []
    _matchManager = None
    
    _ignoreBalancingTill = 0
    
    _currentVote = None
    _auto_unban_level = None

    requiresParsers = ['homefront']

    ####################################################################################################################
    #                                                                                                                  #
    #   STARTUP                                                                                                        #
    #                                                                                                                  #
    ####################################################################################################################

    def onStartup(self):
        """
        Initialize plugin settings
        """
        # get the admin plugin so we can register commands
        self._adminPlugin = self.console.getPlugin('admin')
        if not self._adminPlugin:
            raise AttributeError('could not find admin plugin')

        # register our commands
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
        self.registerEvent('EVT_CLIENT_TEAM_CHANGE', self.onClientTeamChange)
        self.registerEvent('EVT_GAME_ROUND_START', self.onRoundStart)
        self.registerEvent('EVT_CLIENT_AUTH', self.onClientAuth)
        self.registerEvent('EVT_CLIENT_VOTE_START', self.onClientVoteStart)
        self.registerEvent('EVT_SERVER_VOTE_END', self.onClientVoteEnd)

        self.debug('plugin started')

    def onLoadConfig(self):
        """
        Load plugin configuration.
        """
        self.LoadTeamBalancer()
        self.LoadMatchMode()
        self.LoadVoteProtector()

    def LoadTeamBalancer(self):
        """
        Load TeamBalancer configuration.
        :return:
        """
        try:
            self._enableTeamBalancer = self.config.getboolean('teambalancer', 'enabled')
        except (NoOptionError, ValueError):
            self._enableTeamBalancer = False
            self.debug('using default value (%s) for teambalancer::enabled', self._enableTeamBalancer)
        self.debug('teambalancer/::enabled : %s' % self._enableTeamBalancer)

    def LoadMatchMode(self):
        """
        Load matchmode configuration.
        """
        try:
            self._match_plugin_disable = [x.strip() for x in self.config.get('settings', 'pamatch_plugins_disable').split(',')]
        except NoOptionError:
            self.debug('can\'t setup pamatch disable plugins because settings::pamatch_plugins_disable is missing')
            self._match_plugin_disable = []

        self.debug('plugins disabled in matchmode: %s' % ', '.join(self._match_plugin_disable))

    def LoadVoteProtector(self):
        """
        Load vote protector configuration.
        """
        try:
            self._auto_unban_level = self.console.getGroupLevel(self.config.get('voteprotector', 'auto_unban_level'))
        except (NoOptionError, ValueError):
            self._auto_unban_level = 20
            self.debug('using default value (%s) for voteprotector::auto_unban_level', self._enableTeamBalancer)
        self.debug('voteprotector/::auto_unban_level : %s' % self._auto_unban_level)

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENTS                                                                                                         #
    #                                                                                                                  #
    ####################################################################################################################

    def onClientTeamChange(self, event):
        """
        Handle EVT_CLIENT_TEAM_CHANGE
        """
        client = event.client
        client.setvar(self, 'teamtime', self.console.time())
        self.verbose('client variable teamtime set to: %s' % client.var(self, 'teamtime').value)

        if self._enableTeamBalancer:

            if self.console.time() < self._ignoreBalancingTill:
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
            if client.name in biggestteam:
                self.debug('%s has contributed to unbalance the teams')
                client.message('do not make teams unbalanced')
                try:
                    self.console.write('admin forceteamswitch "%s"' % client.name)
                except Exception, err:
                    self.warning('error, server replied %s' % err)

    def onClientVoteStart(self, event):
        """
        Handle EVT_CLIENT_VOTE_START.
        """
        self.debug("onVoteStart (%r, %s, %s)" % (event.data, event.client, event.target))
        self._currentVote = event
        if event.data.lower() in ('kick', 'ban') and event.client \
            and event.target and event.target.maxLevel >= self._auto_unban_level \
            and event.target.maxLevel > event.client.maxLevel:
                self._adminPlugin.penalizeClient('warning', event.client, duration="2d", reason="do not call vote against admin")

    def onClientVoteEnd(self, event):
        """
        Handle EVT_CLIENT_VOTE_END.
        """
        self.debug("onVoteEnd (%r, %s, %s)" % (event.data, event.client, event.target))
        if self._currentVote.data.lower() == 'ban' and event.data['voteresult'].lower() == "passed":
            votecaller = self._currentVote.client
            votetarget = self._currentVote.target
            if votecaller and votetarget:
                if votetarget.maxLevel < self._auto_unban_level:
                    self.info("%s (%s) is in a lower group than %s, vote allowed", votetarget, votetarget.maxLevel, self._auto_unban_level)
                elif votecaller.maxLevel > votetarget.maxLevel:
                    self.info("%s (%s) is in a higher group than %s (%s), vote allowed", votecaller, votecaller.maxLevel, votetarget, votetarget.maxLevel)
                else:
                    self.info("%s (%s) cannot vote ban %s (%s), vote cancelled", votecaller, votecaller.maxLevel, votetarget, votetarget.maxLevel)
                    votetarget.unban(reason="stupid vote auto unbanner", silent=True)

    def onClientAuth(self, event):
        """
        Handle EVT_CLIENT_AUTH.
        """
        # store the time of teamjoin for autobalancing purposes
        event.client.setvar(self, 'teamtime', self.console.time())
        
    def onRoundStart(self, _):
        """
        Handle EVT_GAME_ROUND_START.
        """
        self._ignoreBalancingTill = self.console.time() + 60

    ####################################################################################################################
    #                                                                                                                  #
    #   OTHER METHODS                                                                                                  #
    #                                                                                                                  #
    ####################################################################################################################

    def getTeams(self):
        """
        Return two lists containing the names of players from both teams.
        """
        team1players = []
        team2players = []
        clients = self.console.clients.getList()
        for c in clients:
            if c.team == b3.TEAM_RED:
                team1players.append(c.cid)
            elif c.team == b3.TEAM_BLUE:
                team2players.append(c.cid)
        return team1players, team2players

    def teambalance(self):
        """
        Balance current teams.
        """
        # get teams
        team1players, team2players = self.getTeams()

        # if teams are uneven by one or even, then stop here
        gap = abs(len(team1players) - len(team2players))
        if gap <= 1:
            self.verbose('teambalance: teams are balanced, T1: %s, T2: %s (diff: %s)', (len(team1players), len(team2players), gap))
            return

        howManyMustSwitch = int(gap / 2)
        bigTeam = b3.TEAM_RED
        if len(team2players) > len(team1players):
            bigTeam = b3.TEAM_BLUE

        self.verbose('teambalance: teams are NOT balanced, T1: %s, T2: %s (diff: %s)', (len(team1players), len(team2players), gap))
        self.console.saybig('Autobalancing Teams!')

        playerTeamTimes = {}
        clients = self.console.clients.getList()
        for c in clients:
            if c.team == bigTeam:
                playerTeamTimes[c.cid] = c.var(self, 'teamtime', self.console.time()).value

        self.debug('playerTeamTimes: %s', playerTeamTimes)
        sortedPlayersTeamTimes = sorted(playerTeamTimes.iteritems(), key=lambda (k,v):(v,k), reverse=True)
        self.debug('sortedPlayersTeamTimes: %s', sortedPlayersTeamTimes)

        for c, teamtime in sortedPlayersTeamTimes[:howManyMustSwitch]:
            self.debug('forcing %s to the other team',  c)
            self.console.write('admin forceteamswitch "%s"' % c)

    ####################################################################################################################
    #                                                                                                                  #
    #   COMMANDS                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def cmd_paautobalance(self, data, client=None, cmd=None):
        """
        <on/off> - switch autobalancer on or off
        """
        if data and data.lower() in ('on', 'off'):
            self.console.write('admin SetAutoBalance %s' % 'true' if data.lower() == 'on' else 'false')
        else:
            client.message('invalid or missing data, try !help paautobalance')

    def cmd_pateams(self ,data , client, cmd=None):
        """
        - make the teams balanced
        """
        if client:
            team1players, team2players = self.getTeams()
            gap = abs(len(team1players) - len(team2players))
            if gap <= 1:
                client.message('teams are balanced, T1: %s, T2: %s (diff: %s)' % (len(team1players), len(team2players), gap))
            else:
                self.teambalance()

    def cmd_pateambalance(self, data, client=None, cmd=None):
        """
        [<on/off>] - set teambalancer on/off
        Setting teambalancer on will warn players that make teams unbalanced.
        """
        if not data:
            client.message("team balancing is %s" % 'on' if self._enableTeamBalancer else 'off')
        else:
            if data.lower() in ('on', 'off'):
                if data.lower() == 'off':
                    self._enableTeamBalancer = False
                    client.message('teambancer is now disabled')
                elif data.lower() == 'on':
                    self._enableTeamBalancer = True
                    client.message('teambancer is now enabled')
            else:
                client.message('invalid data, try !help pateambalance')

    def cmd_panextmap(self, data, client=None, cmd=None):
        """
        - force server to the Next Map in rotation
        """
        self.console.write('admin NextMap')

    def cmd_payell(self, data, client, cmd=None):
        """
        <msg> - yell message to all players
        """
        if not data:
            client.message('missing parameter, try !help payell')
        else:
            self.console.saybig('%s: %s' % (client.name, data))

    def cmd_paversion(self, data, client, cmd=None):
        """
        - this command identifies PowerAdminHF version and creator.
        """
        cmd.sayLoudOrPM(client, 'I am PowerAdminHF version %s by %s' % (__version__, __author__))

    def cmd_paident(self, data, client, cmd=None):
        """
        [<name>] - show the ip and guid of a player
        (You can safely use the command without the 'pa' at the beginning)
        """
        x = self._adminPlugin.parseUserCmd(data)
        if not x:
            cmd.sayLoudOrPM(client, '%s: %s' % (client.name, client.guid))
        else:
            sclient = self._adminPlugin.findClientPrompt(x[0], client)
            if sclient:
                cmd.sayLoudOrPM(client, '%s: %s' % (sclient.name, sclient.guid))
        
    def cmd_pakill(self, data, client, cmd=None):
        """
        <name> [<reason>] - kill a player
        """
        m = self._adminPlugin.parseUserCmd(data)
        if not m:
            client.message('invalid or missing data, try !help pakill')
        else:
            cid, keyword = m
            reason = self._adminPlugin.getReason(keyword)
            if not reason and client.maxLevel < self._adminPlugin.config.getint('settings', 'noreason_level'):
                client.message('ERROR: you must supply a reason')
            else:
                sclient = self._adminPlugin.findClientPrompt(cid, client)
                if sclient:
                    self.console.saybig('%s was terminated by server admin' % sclient.name)
                    self.console.write(('admin kill "%s"' % sclient.guid))
                    if reason:
                        self.console.say('%s was terminated by server admin for : %s' % (sclient.name, reason))

    def cmd_pachangeteam(self, data, client, cmd=None):
        """
        <name> - change a player to the other team
        """
        x = self._adminPlugin.parseUserCmd(data)
        if not x:
            client.message('invalid or missing data, try !help pachangeteam')
        else:
            sclient = self._adminPlugin.findClientPrompt(x[0], client)
            if sclient:
                self.console.write('admin forceteamswitch "%s"' % sclient.guid)
                cmd.sayLoudOrPM(client, '%s forced to swap teams' % sclient.name)

    def cmd_paspectate(self, data, client, cmd=None):
        """
        <name> - move a player to spectate
        """
        x = self._adminPlugin.parseUserCmd(data)
        if not x:
            client.message('Invalid data, try !help paspectate')
        else:
            sclient = self._adminPlugin.findClientPrompt(x[0], client)
            if sclient:
                self.console.write('admin makespectate "%s"' % sclient.guid )
                cmd.sayLoudOrPM(client, '%s forced to spectate' % sclient.name)
        
    def cmd_pamatch(self, data, client, cmd=None): 
        """
        <on/off> - set server match mode on/off
        (You can safely use the command without the 'pa' at the beginning)
        """
        if not data or str(data).lower() not in ('on','off'):
            client.message('invalid or missing data, try !help pamatch')
        else:
            if data.lower() == 'on':
                self._matchmode = True
                self._enableTeamBalancer = False
                
                for e in self._match_plugin_disable:
                    self.debug('disabling plugin %s' %e)
                    plugin = self.console.getPlugin(e)
                    if plugin:
                        plugin.disable()
                        client.message('plugin %s disabled' % e)
                
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
                    self.debug('enabling plugin %s' %e)
                    plugin = self.console.getPlugin(e)
                    if plugin:
                        plugin.enable()
                        client.message('plugin %s enabled' % e)

                self.console.say('match mode: OFF')


class MatchManager(object):

    _adminPlugin = None

    plugin = None
    console = None
    playersReady = {}
    countDown = 10
    running = True
    timer = None
    countdownStarted = None
    
    def __init__(self, plugin):
        self.plugin = plugin
        self.console = plugin.console
        self._adminPlugin = self.console.getPlugin('admin')
        if not self._adminPlugin:
            raise AttributeError('could not find admin plugin')
    
    def stop(self):
        try: self.timer.cancel()
        except: pass
        self.running = False
        self.unregisterCommandReady()
        
    def initMatch(self):
        for c in self.console.clients.getList():
            c.setvar(self.plugin, 'ready', False)
        self.countdownStarted = False
        self.registerCommandReady()
        self.console.saybig('MATCH starting soon !!')
        self.console.say('ALL PLAYERS : type !ready when you are ready')
        self.console.saybig('ALL PLAYERS : type !ready when you are ready')
        self.timer = threading.Timer(10.0, self._checkIfEveryoneIsReady)
        self.timer.start()
    
    def registerCommandReady(self):
        self._adminPlugin.registerCommand(self.plugin, 'ready', 0, self.cmd_ready)
    
    def unregisterCommandReady(self):
        try:
            cmd = self._adminPlugin._commands['ready']
            if cmd.plugin == self.plugin:
                self.plugin.debug('unregister !ready command')
                del self._adminPlugin._commands['ready']
        except KeyError:
            pass
    
    def yellToClient(self, message, duration, client):
        """
        We need this to bypass the message queue managed by the HF parser.
        """
        self.console.write(('admin.yell', message, duration, 'player', client.cid))

    def _checkIfEveryoneIsReady(self):
        self.console.debug('checking if all players are ready')
        isAllPlayersReady = True
        waitingForPlayers = []
        for c in self.console.clients.getList():
            isReady = c.var(self.plugin, 'ready', False).value
            self.plugin.debug('is %s ready ? %s' % (c.cid, isReady))
            if isReady is False:
                waitingForPlayers.append(c)
                self.yellToClient('we are waiting for you. type !ready', 10000, c)
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
            self.console.write(('admin.yell', 'MATCH STARTING IN %s' % self.countDown, 900, 'all'))
            self.countDown -= 1
            if self.running:
                self.timer = threading.Timer(1.0, self._countDown)
                self.timer.start()
        else:    
            # make sure to have a brief big text
            self.console.write(('admin.yell', 'FIGHT !!!', 6000, 'all'))
            self.console.say('Match started. GL & HF')
            self.console.write(('admin.restartMap',))
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
                self.yellToClient('You are not ready anymore', 3000, client)
                client.message('You are not ready anymore')
            else:
                client.setvar(self.plugin, 'ready', True)
                self.yellToClient('You are now ready', 3000, client)
                client.message('You are now ready')
            self._checkIfEveryoneIsReady()