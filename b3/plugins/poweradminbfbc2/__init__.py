#
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

__author__  = 'Courgette, SpacepiG, Bakes'
__version__ = '0.6'

import b3
import b3.config
import b3.events
import b3.plugin
import re
import string
import threading
import time

from b3.functions import getCmd
from b3.parsers.frostbite.connection import FrostbiteCommandFailedError


class Poweradminbfbc2Plugin(b3.plugin.Plugin):

    _adminPlugin = None
    _enableTeamBalancer = None
    
    _matchmode = False
    _match_plugin_disable = []
    _matchManager = None
    
    _parseUserCmdRE = re.compile(r'^(?P<cid>[^\s]{2,}|@[0-9]+)\s?(?P<parms>.*)$')
    
    _ignoreBalancingTill = 0

    ####################################################################################################################
    #                                                                                                                  #
    #    STARTUP                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def onLoadConfig(self):
        """
        Load plugin configuration.
        """
        self.LoadTeamBalancer()
        self.LoadMatchMode()

    def LoadTeamBalancer(self):
        """
        Load team balancer configuration.
        """
        try:
            self._enableTeamBalancer = self.config.getboolean('teambalancer', 'enabled')
        except (b3.config.NoOptionError, ValueError):
            self._enableTeamBalancer = False
            self.debug('using default value (%s) for Teambalancer enabled', self._enableTeamBalancer)
      
    def LoadMatchMode(self):
        """
        Load match mode configuration.
        """
        try:
            self._match_plugin_disable = self.config.get('matchmode', 'disabled_plugins').split(', ')
            self.debug('matchmode disabled plugins:: %s' % self._match_plugin_disable)
        except (b3.config.NoOptionError, ValueError):
            self.debug('could not setup pamatch disable plugins because there is no plugins set in config')

    def onStartup(self):
        """
        Initialize plugin settings.
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
        self.registerEvent('EVT_CLIENT_AUTH', self.onClientAuth)
        self.registerEvent('EVT_CLIENT_TEAM_CHANGE', self.onClientTeamChange)
        self.registerEvent('EVT_GAME_ROUND_START', self.onRoundStart)

        self.debug('plugin started')

    ####################################################################################################################
    #                                                                                                                  #
    #    EVENTS                                                                                                        #
    #                                                                                                                  #
    ####################################################################################################################

    def onClientAuth(self, event):
        """
        Handle EVT_CLIENT_AUTH.
        """
        event.client.setvar(self, 'teamtime', self.console.time())

    def onClientTeamChange(self, event):
        """
        Handle EVT_CLIENT_TEAM_CHANGE.
        """
        client= event.client
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
            if client.cid in biggestteam:
                self.debug('%s has contributed to unbalance the teams')
                client.message('do not make teams unbalanced')
                if client.teamId == '1':
                    newteam = '2'
                else:
                    newteam = '1'
                try:
                    self.console.write(('admin.movePlayer', client.cid, newteam, 0, 'true'))
                except FrostbiteCommandFailedError, err:
                    self.warning('could not move player, server replied %s' % err)

    def onRoundStart(self, event):
        """
        Handle EVT_GAME_ROUND_START.
        """
        self._ignoreBalancingTill = self.console.time() + 60

    ####################################################################################################################
    #                                                                                                                  #
    #    OTHER METHODS                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def _changeMode(self, data, client, cmd=None, mode=None):
        """
        Change the current server mode.
        """
        if mode is None:
            self.error('mode cannot be None')
        elif mode not in ('CONQUEST', 'RUSH', 'SQDM', 'SQRUSH'):
            self.error('invalid game mode %s' % mode)
        else:
            try:
                self.console.write(('admin.setPlaylist', mode))
                client.message('Server playlist changed to %s' % mode)
                client.message('Type !map <mapname> to change server mode now')
            except FrostbiteCommandFailedError, err:
                client.message('Failed to change game mode. Server replied with: %s' % err)

    def teambalance(self):
        """
        Balance current teams.
        """
        if self._enableTeamBalancer:
            # get teams
            team1players, team2players = self.getTeams()

            # if teams are uneven by one or even, then stop here
            gap = abs(len(team1players) - len(team2players))
            if gap <= 1:
                self.verbose('teambalance: teams are balanced, T1: %s, T2: %s (diff: %s)' %(len(team1players), len(team2players), gap))
                return

            howManyMustSwitch = int(gap / 2)
            bigTeam = 1
            smallTeam = 2
            if len(team2players) > len(team1players):
                bigTeam = 2
                smallTeam = 1

            self.verbose('teambalance: teams are NOT balanced, T1: %s, T2: %s (diff: %s)' %(len(team1players), len(team2players), gap))
            self.console.saybig('Autobalancing Teams!')

            ## we need to change team for howManyMustSwitch players from bigteam
            playerTeamTimes = {}
            clients = self.console.clients.getList()
            for c in clients:
                if c.teamId == bigTeam:
                    teamTimeVar = c.isvar(self, 'teamtime')
                    if not teamTimeVar:
                        self.debug('client has no variable teamtime')
                        c.setvar(self, 'teamtime', self.console.time())
                        self.verbose('Client variable teamtime set to: %s' % c.var(self, 'teamtime').value)
                    playerTeamTimes[c.cid] = teamTimeVar.value

            self.debug('playerTeamTimes: %s' % str(playerTeamTimes))
            sortedPlayersTeamTimes = sorted(playerTeamTimes.iteritems(), key=lambda (k,v): (v,k))
            self.debug('sortedPlayersTeamTimes: %s' % sortedPlayersTeamTimes)

            for c, teamtime in sortedPlayersTeamTimes[:howManyMustSwitch]:
                try:
                    self.debug('forcing %s to the other team' % c.cid)
                    self.console.write(('admin.movePlayer', c.cid, smallTeam, 0, 'true'))
                except FrostbiteCommandFailedError, err:
                    self.error(err)

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
                team1players.append(name)
        return team1players, team2players

    ####################################################################################################################
    #                                                                                                                  #
    #    COMMANDS                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################
    
    def cmd_pateams(self ,data , client, cmd=None):
        """
        - make the teams balanced
        """
        if client:
            team1players, team2players = self.getTeams()
            # if teams are uneven by one or even, then stop here
            gap = abs(len(team1players) - len(team2players))
            if gap <= 1:
                client.message('Teams are balanced, T1: %s, T2: %s (diff: %s)' % (len(team1players), len(team2players), gap))
            else:
                self.teambalance()

    def cmd_pateambalance(self, data, client=None, cmd=None):
        """
        <on/off> - set teambalancer on/off
        Setting teambalancer on will warn players that make teams unbalanced
        """
        if not data:
            if client:
                if self._enableTeamBalancer:
                    client.message("team balancing is on")
                else:
                    client.message("team balancing is off")
            else:
                self.debug('no data sent to cmd_teambalance')
        else:
            if data.lower() in ('on', 'off'):
                if data.lower() == 'off':
                    self._enableTeamBalancer = False
                    client.message('Teambancer is now disabled')
                elif data.lower() == 'on':
                    self._enableTeamBalancer = True
                    client.message('Teambancer is now enabled')
            else:
                if client:
                    client.message("Invalid data, expecting 'on' or 'off'")
                else:
                    self.debug('invalid data sent to cmd_teambalance : %s' % data)

    def cmd_runscript(self, data, client, cmd=None):
        """
        <configfile.cfg> - execute a server configfile.
        """
        if not data:
            client.message('missing data, try !help runscript')
        else:
            if re.match('^[a-z0-9_.]+.cfg$', data, re.I):
                self.debug('executing configfile = [%s]', data)
                try:
                    self.console.write(('admin.runScript', '%s' % data))
                except FrostbiteCommandFailedError, err:
                    self.warning('could not run script: %s' % err)
                    client.message('ERROR: %s' % str(err))
            else:
                self.error('%s is not a valid configfile', data)

    def cmd_pb_sv_command(self, data, client, cmd=None):
        """
        <punkbuster command> - execute a punkbuster command
        """
        if not data:
            client.message('missing data, try !help pb_sv_command')
        else:
            self.debug('executing punkbuster command = [%s]', data)
            try:
                self.console.write(('punkBuster.pb_sv_command', '%s' % data))
            except FrostbiteCommandFailedError, err:
                self.warning('could not send punkbuster command: %s' % err)
                client.message('ERROR: %s' % str(err))

    def cmd_paserverinfo(self, data, client, cmd=None):
        """
        get server info
        """
        data = self.console.write(('serverInfo',))
        client.message('Server Name: %s' % data[0])
        client.message('Current Players: %s' % data[1])
        client.message('Max Players: %s' % data[2])
        client.message('GameType: %s' % data[3])
        client.message('Map: %s' % self.console.getEasyName(data[4]))

    def cmd_payell(self, data, client, cmd=None):
        """
        <msg> - yell message to all players
        """
        if client:
            if not data:
                client.message('missing data, try !help payell')
            else:
                self.console.saybig('%s: %s' % (client.exactName, data))

    def cmd_payellteam(self, data, client, cmd=None):
        """
        <msg> - yell message to all players of your team
        """ 
        if not data:
            client.message('missing data, try !help payellteam')
        else:
            for c in self.console.clients.getList():
                if c.team == client.team:
                    c.message(data)

    def cmd_payellsquad(self, data, client, cmd=None):
        """
        <msg> - yell message to all players of your squad
        """ 
        if not data:
            client.message('missing data, try !help payellsquad')
        else:
            for c in self.console.clients.getList():
                if c.squad == client.squad and c.team == client.team:
                    c.message(data)

    def cmd_payellenemy(self, data, client, cmd=None):
        """
        <msg> - yell message to all players of the other team
        """
        if not data:
            client.message('missing data, try !help payellenemy')
        else:
            for c in self.console.clients.getList():
                if c.team != client.team:
                    c.message(data)

    def cmd_payellplayer(self, data, client, cmd=None):
        """
        <player> <msg> - yell message to a player
        """
        m = self._adminPlugin.parseUserCmd(data, True)
        if not m:
            client.message('invalid data, try !help payellplayer')
        else:
            cid, message = m
            sclient = self._adminPlugin.findClientPrompt(cid, client)
            if sclient:
                sclient.message(message)

    def cmd_paversion(self, data, client, cmd=None):
        """
        - this command identifies PowerAdminBFBC2 version and creator.
        """
        cmd.sayLoudOrPM(client, 'I am PowerAdminBFBC2 version %s by %s' % (__version__, __author__))
        
    def cmd_pamaplist(self, data, client, cmd=None):
        """
        <maplist.txt> - load a server maplist.
        """
        if not data:
            client.message('missing data, try !help pamaplist')
        else:
            if re.match('^[a-z0-9_.]+.txt$', data, re.I):
                self.debug('loading maplist = [%s]', data)
                self.console.write(('mapList.load %s' % data))
            else:
                self.error('%s is not a valid maplist', data)

    def cmd_pamaprestart(self, data, client, cmd=None):
        """
        Restart the current map.
        """
        self.console.say('restarting map...')
        time.sleep(1)
        self.console.write(('admin.restartMap',))

    def cmd_pamapreload(self, data, client, cmd=None):
        """
        Reload the current map.
        """
        self.console.say('reloading map...')
        time.sleep(1)
        data = self.console.write(('admin.currentLevel',))
        self.console.write(('mapList.clear',))
        self.console.write(('mapList.append', data))
        self.console.write(('admin.runNextLevel',))
        self.console.write(('mapList.load',))
        
    def cmd_paset(self, data, client, cmd=None):
        """
        <var> <value> - set a server var to a certain value.
        """
        if client:
            if not data:
                client.message('missing data, try !help paset')
            else:
                x = data.split(' ',1)
                varName = x[0]
                value = x[1]
                try:
                    self.console.write(('vars.%s' % varName, value))
                    client.message('%s set' % varName)
                except FrostbiteCommandFailedError, err:
                    client.message('ERROR setting %s : %s' % (varName, err))

    def cmd_paget(self, data, client, cmd=None):
        """
        <var> - returns the value of a server var.
        """
        if not data:
            client.message('missing data, try !help paget')
        else:
            # are we still here? Let's write it to console
            var = data.split(' ')
            cvar = self.console.getCvar(var[0])
            client.message('%s' % cvar.value)

    def cmd_pasetnextmap(self, data, client=None, cmd=None):
        """
        <mapname> - set the nextmap (partial map name works)
        """
        if not data:
            client.message('missing data, try !help setnextmap')
        else:
            match = self.console.getMapsSoundingLike(data)
            if len(match) > 1:
                client.message('Do you mean: %s?' % string.join(match,', '))
            elif len(match) == 1:
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
                client.message('No map found matching: %s' % data)

    def cmd_paident(self, data, client, cmd=None):
        """
        [<name>] - show the ip and guid of a player
        """
        x = self._adminPlugin.parseUserCmd(data)
        if not x:
            try:
                cmd.sayLoudOrPM(client, '%s %s %s' % (client.cid, client.ip, client.guid))
            except FrostbiteCommandFailedError, err:
                client.message('Error, server replied %s' % err)
        else:
            try:
                sclient = self._adminPlugin.findClientPrompt(x[0], client)
                if sclient:
                    cmd.sayLoudOrPM(client, '%s %s %s' % (sclient.cid, sclient.ip, sclient.guid))
            except FrostbiteCommandFailedError, err:
                client.message('Error, server replied %s' % err)
        
    def cmd_pakill(self, data, client, cmd=None):
        """
        <name> <reason> - kill a player
        """
        m = self._adminPlugin.parseUserCmd(data)
        if not m:
            client.message('invalid data, try !help pakill')
        else:
            cid, keyword = m
            reason = self._adminPlugin.getReason(keyword)
    
            if not reason and client.maxLevel < self._adminPlugin.config.getint('settings', 'noreason_level'):
                client.message('ERROR: You must supply a reason')
            else:
                sclient = self._adminPlugin.findClientPrompt(cid, client)
                if sclient:
                    self.console.saybig('%s was terminated by server admin' % sclient.name)
                    try:
                        self.console.write(('admin.killPlayer', sclient.cid))
                        if reason:
                            self.console.say('%s was terminated by server admin for : %s' % (sclient.name, reason))
                    except FrostbiteCommandFailedError, err:
                        client.message('Error, server replied %s' % err)

    def cmd_pachangeteam(self, data, client, cmd=None):
        """
        [<name>] - change a player to the other team
        """
        x = self._adminPlugin.parseUserCmd(data)
        if not x:
            client.message('invalid data, try !help pachangeteam')
        else:
            sclient = self._adminPlugin.findClientPrompt(x[0], client)
            if sclient:
                if sclient.teamId == '1':
                    newteam = '2'
                else:
                    newteam = '1' 
                try:
                    self.console.write(('admin.movePlayer', sclient.cid, newteam, 0, 'true'))
                    cmd.sayLoudOrPM(client, '%s forced to the other team' % sclient.cid)
                except FrostbiteCommandFailedError, err:
                    client.message('Error, server replied %s' % err)
        
    def cmd_paspectate(self, data, client, cmd=None):
        """
        [<name>] - move a player to spectate
        """
        x = self._adminPlugin.parseUserCmd(data)
        if not x:
            client.message('invalid data, try !help paspectate')
        else:
            sclient = self._adminPlugin.findClientPrompt(x[0], client)
            if sclient:
                try:
                    self.console.write(('admin.movePlayer', sclient.cid, 0, 0, 'true'))
                    cmd.sayLoudOrPM(client, '%s forced to spectate' % sclient.name)
                except FrostbiteCommandFailedError, err:
                    client.message('Error, server replied %s' % err)
        
    def cmd_pamatch(self, data, client, cmd=None): 
        """
        - set server match mode on/off
        """
        if not data or str(data).lower() not in ('on','off'):
            client.message('invalid or missing data, expecting "on" or "off"')
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

    def cmd_paconquest(self, data, client, cmd=None): 
        """
        change server mode to CONQUEST
        """
        self._changeMode(data, client, cmd, mode='CONQUEST')
        
    def cmd_parush(self, data, client, cmd=None): 
        """
        change server mode to RUSH
        """
        self._changeMode(data, client, cmd, mode='RUSH')
        
    def cmd_pasqdm(self, data, client, cmd=None): 
        """
        change server mode to SQDM
        """
        self._changeMode(data, client, cmd, mode='SQDM')
        
    def cmd_pasqrush(self, data, client, cmd=None): 
        """
        change server mode to SQRUSH
        """
        self._changeMode(data, client, cmd, mode='SQRUSH')


class MatchManager(object):

    _adminPlugin = None

    console = None
    plugin = None
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
        try:
            self.timer.cancel()
        except Exception:
            pass
        self.running = False
        self.unregisterCommandReady()
        
    def initMatch(self):
        """
        Initialize the match mode.
        """
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
        """
        Register the !ready command.
        """
        self._adminPlugin.registerCommand(self.plugin, 'ready', 0, self.cmd_ready)
    
    def unregisterCommandReady(self):
        """
        Unregister the !ready command.
        """
        try:
            cmd = self._adminPlugin._commands['ready']
            if cmd.plugin == self.plugin:
                self.plugin.debug('unregister !ready command')
                del self._adminPlugin._commands['ready']
        except KeyError:
            pass
    
    def yellToClient(self, message, duration, client):
        """
        We need this to bypass the message queue managed by the BFBC2 parser.
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
        except Exception:
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