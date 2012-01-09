# -*- coding: utf-8 -*-
#
# PowerAdmin BF3 Plugin for BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2011 Thomas LÉVEIL (courgette@bigbrotherbot.net)
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
#
# 0.1 - add command !kill
# 0.2 - add commands !roundrestart and !roundnext
# 0.3 - add commands !changeteam and !swap
# 0.4 - commands !kill, !changeteam, !swap won't act on an admin of higher level
# 0.5 - add commands !punkbuster and !setnextmap. Fix bug in 0.4
# 0.6 - add command !loadconfig
# 0.7 - add the swap_no_level_check config variable to allow one to !swap players without any level restriction
# 0.8
#   renamed 'swap_no_level_check' to 'no_level_check_level' and this option now also applies to the !changeteam command
#   add commands !scramble, !scramblemode, !autoscramble
# 0.8.1 - fix crash with 0.8
# 0.8.2 - fix issue #17 with !loadconfig
# 0.9   - add command !listconfig, !loadconfig can understand mis-spelt names and suggest config names
# 0.10  - ported xlr8or's configmanager plugin for cod series. Automagically loads server config files based on maps/gamemodes
# 0.11  - fix issue with configmanager examples' filenames
# 0.12  - add command !unlockmode
# 0.13  - fixes #22 : !swap reports everything went fine even when failing
import re
from b3.functions import soundex, levenshteinDistance

__version__ = '0.13'
__author__  = 'Courgette'

import random
import time
import os
import thread
import b3
import b3.events
from b3.plugin import Plugin
from ConfigParser import NoOptionError
from b3.parsers.frostbite2.protocol import CommandFailedError
from b3.parsers.frostbite2.util import MapListBlock, PlayerInfoBlock
from b3.parsers.bf3 import GAME_MODES_NAMES


class Scrambler:
    _plugin = None
    _getClients_method = None
    _last_round_scores = PlayerInfoBlock([0,0])

    def __init__(self, plugin):
        self._plugin = plugin
        self._getClients_method = self._getClients_randomly

    def scrambleTeams(self):
        clients = self._getClients_method()
        if len(clients)==0:
            return
        elif len(clients)<3:
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
        while len(listOfPlayers)>0:
            self._plugin._movePlayer(listOfPlayers.pop(), team + 1)
            team = (team + 1)%2

    def _getClients_randomly(self):
        clients = self._plugin.console.clients.getList()
        random.shuffle(clients)
        return clients

    def _getClients_by_scores(self):
        allClients = self._plugin.console.clients.getList()
        self.debug('all clients : %r' % [x.cid for x in allClients])
        sumofscores = reduce(lambda x, y: x+y, [int(data['score']) for data in self._last_round_scores], 0)
        self.debug('sum of scores is %s' % sumofscores)
        if sumofscores == 0:
            self.debug('no score to sort on, using ramdom strategy instead')
            random.shuffle(allClients)
            return allClients
        else:
            sortedScores = sorted(self._last_round_scores, key=lambda x:x['score'])
            self.debug('sorted score : %r' % sortedScores)
            sortedClients = []
            for cid in [x['name'] for x in sortedScores]:
                # find client object for each player score
                clients = [c for c in allClients if c.cid == cid]
                if clients and len(clients)>0:
                    allClients.remove(clients[0])
                    sortedClients.append(clients[0])
            self.debug('sorted clients A : %r' % map(lambda x:x.cid, sortedClients))
            random.shuffle(allClients)
            for client in allClients:
                # add remaining clients (they had no score ?)
                sortedClients.append(client)
            self.debug('sorted clients B : %r' % map(lambda x:x.cid, sortedClients))
            return sortedClients

    def debug(self, msg):
        self._plugin.debug('scramber:\t %s' % msg)




class Poweradminbf3Plugin(Plugin):

    def __init__(self, console, config=None):
        self._adminPlugin = None
        self._configPath = ''
        self._configManager_configPath = ''
        self.no_level_check_level = 100
        self._configmanager_delay = 5
        self._scrambling_planned = False
        self._autoscramble_rounds = False
        self._autoscramble_maps = False
        self._scrambler = Scrambler(self)
        Plugin.__init__(self, console, config)



################################################################################################################
#
#    Plugin interface implementation
#
################################################################################################################

    def onLoadConfig(self):
        """\
        This is called after loadConfig(). Any plugin private variables loaded
        from the config need to be reset here.
        """
        self._load_messages()
        self._load_config_path()
        self._load_no_level_check_level()
        self._load_scrambler()
        self._load_configmanager_config_path()
        self._load_configmanager()

    def startup(self):
        """\
        Initialize plugin settings
        """
        # get the admin plugin so we can register commands
        self._adminPlugin = self.console.getPlugin('admin')
        if not self._adminPlugin:
            # something is wrong, can't start without admin plugin
            self.error('Could not find admin plugin')
            return False
        self._registerCommands()

        # Register our events
        self.registerEvent(b3.events.EVT_GAME_ROUND_START)
        self.registerEvent(b3.events.EVT_GAME_ROUND_END)
        self.registerEvent(b3.events.EVT_GAME_ROUND_PLAYER_SCORES)
        self.registerEvent(b3.events.EVT_CLIENT_AUTH)
        self.registerEvent(b3.events.EVT_CLIENT_DISCONNECT)


    def onEvent(self, event):
        """\
        Handle intercepted events
        """
        if event.type == b3.events.EVT_GAME_ROUND_PLAYER_SCORES:
            self._scrambler.onRoundOverTeamScores(event.data)
        elif event.type == b3.events.EVT_GAME_ROUND_START:
            self.debug('manual scramble planned : '.rjust(30) + str(self._scrambling_planned))
            self.debug('auto scramble rounds : '.rjust(30) + str(self._autoscramble_rounds))
            self.debug('auto scramble maps : '.rjust(30) + str(self._autoscramble_maps))
            self.debug('self.console.game.rounds : '.rjust(30) + repr(self.console.game.rounds))
            if self._scrambling_planned:
                self.debug('manual scramble is planned')
                self._scrambler.scrambleTeams()
                self._scrambling_planned = False
            else:
                if self._autoscramble_rounds:
                    self.debug('auto scramble is planned for rounds')
                    self._scrambler.scrambleTeams()
                elif self._autoscramble_maps and self.console.game.rounds == 0:
                    self.debug('auto scramble is planned for maps')
                    self._scrambler.scrambleTeams()
        elif event.type == b3.events.EVT_GAME_ROUND_END:
            if self._configmanager:
                self.config_manager_construct_file_names()
                self.config_manager_check_config()


################################################################################################################
#
#   Commands implementations
#
################################################################################################################

    def cmd_roundnext(self, data, client, cmd=None):
        """\
        Switch to next round, without ending current
        """
        self.console.say('forcing next round')
        time.sleep(1)
        try:
            self.console.write(('mapList.runNextRound',))
        except CommandFailedError, err:
            client.message('Error: %s' % err.message)


    def cmd_roundrestart(self, data, client, cmd=None):
        """\
        Restart current round
        """
        self.console.say('Restart current round')
        time.sleep(1)
        try:
            self.console.write(('mapList.restartRound',))
        except CommandFailedError, err:
            client.message('Error: %s' % err.message)

    def cmd_kill(self, data, client, cmd=None):
        """\
        <player> [reason] - Kill a player without scoring effects
        """
        # this will split the player name and the message
        name, reason = self._adminPlugin.parseUserCmd(data)
        if name:
            sclient = self._adminPlugin.findClientPrompt(name, client)
            if not sclient:
                # a player matching the name was not found, a list of closest matches will be displayed
                # we can exit here and the user will retry with a more specific player
                return
            elif sclient.maxLevel >= client.maxLevel:
                if sclient.maxGroup:
                    client.message(self.getMessage('operation_denied_level', {'name': sclient.name, 'group': sclient.maxGroup.name}))
                else:
                    client.message(self.getMessage('operation_denied'))
            else:
                try:
                    self.console.write(('admin.killPlayer', sclient.cid))
                    if reason:
                        sclient.message("Kill reason: %s" % reason)
                    else:
                        sclient.message("Killed by admin")
                except CommandFailedError, err:
                    if err.message[0] == "SoldierNotAlive":
                        client.message("%s is already dead" % sclient.name)
                    else:
                        client.message('Error: %s' % err.message)

    def cmd_changeteam(self, data, client, cmd=None):
        """\
        <name> - change a player to the other team
        """
        name, reason = self._adminPlugin.parseUserCmd(data)
        if not name:
            client.message('Invalid data, try !help changeteam')
        else:
            sclient = self._adminPlugin.findClientPrompt(name, client)
            if not sclient:
                # a player matching the name was not found, a list of closest matches will be displayed
                # we can exit here and the user will retry with a more specific player
                return
            elif sclient.maxLevel > client.maxLevel and self.no_level_check_level > client.maxLevel:
                if sclient.maxGroup:
                    client.message(self.getMessage('operation_denied_level', {'name': sclient.name, 'group': sclient.maxGroup.name}))
                else:
                    client.message(self.getMessage('operation_denied'))
            else:
                newteam = '2' if sclient.teamId == 1 else '1'
                try:
                    self.console.write(('admin.movePlayer', sclient.cid, newteam, 0, 'true'))
                    cmd.sayLoudOrPM(client, '%s forced from team %s to team %s' % (sclient.cid, sclient.teamId, newteam))
                except CommandFailedError, err:
                    client.message('Error, server replied %s' % err)


    def cmd_swap(self, data, client, cmd=None):
        """\
        <player A> [<player B>] - swap teams for player A and B if they are in different teams or squads
        """
        # player A's name
        pA, otherparams = self._adminPlugin.parseUserCmd(data)
        if not pA:
            client.message('Invalid data, try !help swap')
            return

        if len(pA)==1 or otherparams is None:
            # assumes pB is the player that use the command
            otherparams = client.name

        # player B's name
        pB, otherparams2 = self._adminPlugin.parseUserCmd(otherparams)
        if not pB:
            client.message('Invalid data, try !help swap')
            return

        # get client object for player A and B
        sclientA = self._adminPlugin.findClientPrompt(pA, client)
        if not sclientA:
            return
        sclientB = self._adminPlugin.findClientPrompt(pB, client)
        if not sclientB:
            return

        if client.maxLevel < self.no_level_check_level:
            # check if client A and client B are in lower or equal groups
            if client.maxLevel < sclientA.maxLevel:
                if sclientA.maxGroup:
                    client.message(self.getMessage('operation_denied_level', {'name': sclientA.name, 'group': sclientA.maxGroup.name}))
                else:
                    client.message(self.getMessage('operation_denied'))
                return
            if client.maxLevel < sclientB.maxLevel:
                if sclientB.maxGroup:
                    client.message(self.getMessage('operation_denied_level', {'name': sclientB.name, 'group': sclientB.maxGroup.name}))
                else:
                    client.message(self.getMessage('operation_denied'))
                return


        if sclientA.teamId not in (1, 2) and sclientB.teamId not in (1, 2):
            client.message('could not determine players teams')
            return
        if sclientA.teamId == sclientB.teamId and sclientA.squad == sclientB.squad:
            client.message('both players are in the same team and squad. Cannot swap')
            return

        teamA, teamB = sclientA.teamId, sclientB.teamId
        squadA, squadB = sclientA.squad, sclientB.squad

        try:
            # move player A to teamB/NO_SQUAD
            self._movePlayer(sclientA, teamB)

            # move player B to teamA/squadA
            self._movePlayer(sclientB, teamA, squadA)

            # move player A to teamB/squadB if squadB != 0
            if squadB:
                self._movePlayer(sclientA, teamB, squadB)

            cmd.sayLoudOrPM(client, 'swapped player %s with %s' % (sclientA.cid, sclientB.cid))
        except CommandFailedError, e:
            client.message("Error while trying to swap %s with %s. (%s)" % (sclientA.cid, sclientB.cid, e.message[0]))


    def cmd_punkbuster(self, data, client, cmd=None):
        """\
        <punkbuster command> - Execute a punkbuster command
        """
        if not data:
            client.message('missing paramter, try !help punkbuster')
        else:
            try:
                isPbActive = self.console.write(('punkBuster.isActive',))
                if isPbActive and len(isPbActive) and isPbActive[0] == 'false':
                    client.message('Punkbuster is not active')
                    return
            except CommandFailedError, err:
                self.error(err)

            self.debug('Executing punkbuster command = [%s]', data)
            try:
                self.console.write(('punkBuster.pb_sv_command', '%s' % data))
            except CommandFailedError, err:
                self.error(err)
                client.message('Error: %s' % err.message)


    def cmd_setnextmap(self, data, client=None, cmd=None):
        """\
        <mapname> - Set the nextmap (partial map name works)
        """
        if not data:
            client.message('Invalid or missing data, try !help setnextmap')
        else:
            match = self.console.getMapsSoundingLike(data)
            if len(match) > 1:
                client.message('do you mean : %s ?' % ', '.join(match))
                return
            if len(match) == 1:
                map_id = match[0]

                maplist = MapListBlock(self.console.write(('mapList.list',)))
                if not len(maplist):
                    # maplist is empty, fix this situation by loading save mapList from disk
                    try:
                        self.console.write(('mapList.load',))
                    except Exception, err:
                        self.warning(err)
                    maplist = MapListBlock(self.console.write(('mapList.list',)))

                current_max_rounds = self.console.write(('mapList.getRounds',))[1]
                if not len(maplist):
                    # maplist is still empty, nextmap will be inserted at index 0
                    self.console.write(('mapList.add', map_id, self.console.game.gameType, current_max_rounds, 0))
                    self.console.write(('mapList.setNextMapIndex', 0))
                else:
                    current_map_index = int(self.console.write(('mapList.getMapIndices', ))[0])
                    matching_maps = maplist.getByName(map_id)
                    if not len(matching_maps):
                        # then insert wanted map in rotation list
                        next_map_index = current_map_index + 1
                        self.console.write(('mapList.add', map_id, self.console.game.gameType, current_max_rounds, next_map_index))
                        self.console.write(('mapList.setNextMapIndex', next_map_index))
                    elif len(matching_maps) == 1:
                        # easy case, just set the nextLevelIndex to the index found
                        self.console.write(('mapList.setNextMapIndex', matching_maps.keys()[0]))
                    else:
                        # multiple matches :s
                        matching_indices = matching_maps.keys()
                        # try to find the next indice after the index of the current map
                        indices_after_current = [x for x in matching_indices if x > current_map_index]
                        if len(indices_after_current):
                            next_map_index = indices_after_current[0]
                        else:
                            next_map_index = matching_indices[0]
                        self.console.write(('mapList.setNextMapIndex', next_map_index))
                if client:
                    cmd.sayLoudOrPM(client, 'next map set to %s' % self.console.getEasyName(map_id))

    def cmd_loadconfig(self, data, client=None, cmd=None):
        """\
        <config name> - Load a server config file
        """
        if self._configPath is None:
            client.message("The directory containing the config files is unknown, check the plugin configuration file")
        elif not data:
            client.message('Invalid or missing data, try !help loadconfig')
        elif '/' in data or '../' in data:
            client.message('Invalid data, try !help loadconfig')
        else:
            found_names = self._getConfigSoundingLike(data)
            if not len(found_names):
                client.message("Cannot find any config file named %s.cfg" % data)
            elif len(found_names) > 1:
                client.message("Do you mean : %s ?" % ", ".join(found_names[:5]))
            else:
                _fName = self._configPath + os.path.sep + found_names[0] + '.cfg'
                self.verbose(_fName)
                client.message("Loading config %s ..." % data)
                try:
                    self._load_server_config_from_file(client, config_name=found_names[0], file_path=_fName, threaded=True)
                except Exception, msg:
                    self.error('Error loading config: %s' % msg)
                    client.message("Error while loading config")

    def cmd_listconfig(self, data, client=None, cmd=None):
        """\
        List available config files that can be loaded with the !loadconfig command
        """
        if self._configPath is None:
            client.message("The directory containing the config files is unknown, check the plugin configuration file")
        else:
            config_files = self._list_available_server_config_files()
            if not config_files:
                client.message('No server config files found')
            else:
                client.message('^3Available config files:^7 %s' % ', '.join(config_files))

    def cmd_scramble(self, data, client, cmd=None):
        """\
        Toggle on/off the teams scrambling for next round
        """
        if self._scrambling_planned:
            self._scrambling_planned = False
            client.message('Teams scrambling canceled for next round')
        else:
            self._scrambling_planned = True
            client.message('Teams will be scrambled at next round start')

    def cmd_scramblemode(self, data, client, cmd=None):
        """\
        <random|score> change the scrambling strategy
        """
        if not data:
            client.message("invalid data. Expecting 'random' or 'score'")
        else:
            if data[0].lower() == 'r':
                self._scrambler.setStrategy('random')
                client.message('Scrambling strategy is now: random')
            elif data[0].lower() == 's':
                self._scrambler.setStrategy('score')
                client.message('Scrambling strategy is now: score')
            else:
                client.message("invalid data. Expecting 'random' or 'score'")

    def cmd_autoscramble(self, data, client, cmd=None):
        """\
        <off|round|map> manage the auto scrambler
        """
        if not data:
            client.message("invalid data. Expecting one of [off, round, map]")
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
                client.message("invalid data. Expecting one of [off, round, map]")


    def cmd_unlockmode(self, data, client, cmd=None):
        """\
        <all|common|stats|none> set the weapons unlocks mode
        """
        expected_values = ('all', 'common', 'stats', 'none')
        if not data or data.lower() not in expected_values:
            if data.lower() not in expected_values and data != '':
                client.message("unexpected value '%s'. Available modes : %s" % (data, ', '.join(expected_values)))
            try:
                current_mode = self.console.getCvar('unlockMode').getString()
                self.console.game['unlockMode'] = current_mode
            except Exception:
                current_mode = 'unknown'
            cmd.sayLoudOrPM(client=client, message="Current unlock mode is [%s]" % current_mode)
        else:
            wanted_mode = data.lower()
            self.console.setCvar('unlockMode', wanted_mode)
            self.console.game['unlockMode'] = wanted_mode
            cmd.sayLoudOrPM(client=client, message="Unlock mode set to %s" % wanted_mode)


################################################################################################################
#
#    Other methods
#
################################################################################################################

    def _load_scrambler(self):
        try:
            strategy = self.config.get('scrambler', 'strategy')
            self._scrambler.setStrategy(strategy)
            self.debug("scrambling strategy '%s' set" % strategy)
        except Exception, err:
            self.debug(err)
            self._scrambler.setStrategy('random')
            self.debug('Using default value (random) for scrambling strategy')

        try:
            mode = self.config.get('scrambler', 'mode').lower()
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
        except Exception, err:
            self.debug(err)
            self._autoscramble_rounds = False
            self._autoscramble_maps = False
            self.warning('Using default value (off) for auto scrambling mode')

    def _load_messages(self):
        """Loads the messages section from the plugin config file"""
        try:
            self.getMessage('operation_denied_level', {'name': '', 'group': ''})
        except NoOptionError:
            self._messages['operation_denied_level'] = "Operation denied because %(name)s is in the %(group)s group"

        try:
            self.getMessage('operation_denied')
        except NoOptionError:
            self._messages['operation_denied'] = "Operation denied"

    def _load_config_path(self):
        try:
            tmp_path = self.config.getpath('preferences', 'config_path')
            if os.path.isdir(tmp_path):
                self._configPath = tmp_path
            else:
                self._configPath = self._get_server_config_directory(tmp_path)
        except NoOptionError:
            self._configPath = self._get_server_config_directory('serverconfigs')
        if self._configPath is None:
            self.error('Could not find the server config files directory. Update your config file with an existing directory name in option "config_path" of section "preferences".')
        else:
            self.info("Server config files directory : %s" % self._configPath)

    def _load_configmanager_config_path(self):
        self._configManager_configPath = self._get_server_config_directory('configmanager')
        if self._configManager_configPath is None:
            self.error('Could not find the configmanager directory. Create a directory named \'configmanager\' next to your plugin config file')
        else:
            self.info("ConfigManager directory : %s" % self._configManager_configPath)

    def _load_no_level_check_level(self):
        try:
            self.no_level_check_level = self.config.getint('preferences', 'no_level_check_level')
        except NoOptionError:
            self.info('No config option \"preferences\\no_level_check_level\" found. Using default value : %s' % self.no_level_check_level)
        except ValueError, err:
            self.debug(err)
            self.warning('Could not read level value from config option \"preferences\\no_level_check_level\". Using default value \"%s\" instead. (%s)' % (self.no_level_check_level, err))
        except Exception, err:
            self.error(err)
        self.info('no_level_check_level is %s' % self.no_level_check_level)

    def _load_configmanager(self):
        try:
            self._configmanager = self.config.getboolean('configmanager', 'status')
            self.debug('Configmanager: %s' % self._configmanager)
        except:
            self.debug('Unable to load configmanager status from config file, disabling it')
            self._configmanager = False

    def _getCmd(self, cmd):
        cmd = 'cmd_%s' % cmd
        if hasattr(self, cmd):
            func = getattr(self, cmd)
            return func
        return None

    def _registerCommands(self):
        # register our commands
        if 'commands' in self.config.sections():
            for cmd in self.config.options('commands'):
                level = self.config.get('commands', cmd)
                sp = cmd.split('-')
                alias = None
                if len(sp) == 2:
                    cmd, alias = sp
                func = self._getCmd(cmd)
                if func:
                    self._adminPlugin.registerCommand(self, cmd, level, func, alias)

    def _movePlayer(self, client, teamId, squadId=0):
        self.console.write(('admin.movePlayer', client.cid, teamId, squadId, 'true'))
        client.setvar(self, 'movedByBot', True)

    def _get_server_config_directory(self, dir_name=''):
        """returns an existing absolute directory path supposed to contain some game server config files.
        Actual directory if found by checking the existence of :
            dir_name
            <plugin config folder>/dir_name
            <B3 config directory>/dir_name
        If no directory found, returns None
        """
        if os.path.isdir(dir_name):
            return os.path.normpath(dir_name)
        if hasattr(self.config, 'fileName') and self.config.fileName:
            # the plugin config was loaded from a file
            plugin_config_directory = os.path.dirname(self.config.fileName)
            tmp_dir = os.path.join(plugin_config_directory, dir_name)
            if os.path.isdir(tmp_dir):
                return os.path.normpath(tmp_dir)
        if hasattr(self.console.config, 'fileName') and self.console.config.fileName:
            # the B3 config was loaded from a file
            b3_config_directory = os.path.dirname(self.console.config.fileName)
            tmp_dir = os.path.join(b3_config_directory, dir_name)
            if os.path.isdir(tmp_dir):
                return os.path.normpath(tmp_dir)
        return None

    def _load_server_config_from_file(self, client, config_name, file_path, threaded=False):
        """
        Loads a preset config file to send to the server
        """
        self.info('Loading %s' % file_path)

        lines = []
        with file(file_path, 'r') as f:
            lines = f.readlines()
        #self.verbose(repr(lines))
        if threaded:
            #delegate communication with the server to a new thread
            thread.start_new_thread(self.load_server_config, (client, config_name, lines))
        else:
            self.load_server_config(client, config_name, lines)

    def load_server_config(self, client, config_name, items=None):
        """
        Clean up the lines in the config and send them to the server
        """
        if items is None:
            return

        re_cvar = re.compile(r'^\s*(?P<cvar>vars\.[^\s]+)(\s+(?P<value>.*))?$')
        re_maplist_item = re.compile(r'^\s*(?P<map_id>\w+)\s+(?P<gamemode>\w+)\s+(?P<num_rounds>\d+)\s*$')

        cvars_matches = []
        map_item_matches = []

        line_index = 0
        for line in items:
            line_index += 1
            match = re_cvar.search(line.strip())
            if match:
                cvars_matches.append((line_index, line, match))
                continue
            match = re_maplist_item.search(line.strip())
            if match:
                map_item_matches.append((line_index, line, match))

        for line_index, line, m in cvars_matches:
            if m.group('value'):
                # set cvar
                try:
                    self.console.write((m.group('cvar'), m.group('value')))
                except CommandFailedError, err:
                    self._sendMessage(client, ('Error "%s" received at line %s when sending "%s" to server' % (err.message, line_index, line)))
            else:
                # read cvar
                try:
                    result = self.console.write((m.group('cvar'),))
                    if len(result):
                        self._sendMessage(client, ("%s is \"%s\"" % (m.group('cvar'), result[0])))
                except CommandFailedError, err:
                    self._sendMessage(client, ('Error "%s" received at line %s when sending "%s" to server' % (err.message, line_index, m.group('cvar'))))

        if len(map_item_matches):
            self.console.write(('mapList.clear',)) # clear current in-memory map rotation list
            for line_index, line, m in map_item_matches:
                try:
                    self.console.write(('mapList.add', m.group('map_id'), m.group('gamemode'), m.group('num_rounds')))
                except CommandFailedError, err:
                    self._sendMessage(client, ("Error adding map \"%s\" on line %s : %s" % (line, line_index, err.message)))
            try:
                self.console.write(('mapList.save',)) # write current in-memory map list to server config file so if the server restarts our list is recovered.
                self._sendMessage(client, ("New map rotation list written to disk."))
            except CommandFailedError, err:
                self._sendMessage(client, ("Error writing map rotation list to disk. %s" % err.message))

        self._sendMessage(client, ("config \"%s\" loaded" % config_name))

    def _list_available_server_config_files(self):
        self.info("looking for config files in directory : %s" % self._configPath)
        config_files = []
        filenames = os.listdir(self._configPath)
        for filename in filenames:
            if filename.endswith('.cfg'):
                filename = filename.split('.')
                config_files.append('.'.join(filename[:-1]))
        return config_files

    def _getConfigSoundingLike(self, config_name):
        """return a list of existing server config names sounding like config_name"""
        available_configs = self._list_available_server_config_files()

        clean_config_name = config_name.strip().lower()

        # exact match
        if clean_config_name in available_configs:
            return [clean_config_name]

        # substring match
        matching_subset = [x for x in available_configs if clean_config_name in x.lower()]
        if len(matching_subset) == 1:
            matches = [matching_subset[0]]
        elif len(matching_subset) > 1:
            matches = matching_subset
        else:
            # no luck with subset search, fallback on soundex magic
            soundex_query = soundex(clean_config_name)
            matches = [name for name in available_configs if soundex(name) == soundex_query]

        # got nothing ? suggest available config names
        if not len(matches):
            matches = available_configs

        # order what we came up with by levenshtein distance
        if len(matches):
            matches.sort(key=lambda name: levenshteinDistance(clean_config_name, name))

        return matches

    def config_manager_construct_file_names(self):
        """
        Construct file names based on next level name and next game mode for configmanager feature
        """
        #check if we have more rounds to play
        _rounds_left = self._get_rounds_left()
        if _rounds_left > 0:
            self.debug('%s more round(s) to go' % _rounds_left)
            #get current map and gametype
            c = self.console.game

            self._next_typeandmap = 'b3_%s_%s' % (c.gameType.lower(), c.mapName.lower())
            self.debug('Type and Map Config: %s' %(self._next_typeandmap))

            self._next_gametype = 'b3_%s' % (c.gameType.lower())
            self.debug('Gametype Config: %s' %(self._next_gametype))
        else:
            #get next map and gametype
            next_map_gametype = self.console.getNextMap()
            p = next_map_gametype.split('(')
            next_mapName = p[0].strip()
            next_mapName = self.console.getHardName(next_mapName)

            game_modes_names_inverse = dict((GAME_MODES_NAMES[k], k) for k in GAME_MODES_NAMES)
            next_gameType = p[1][:-1].strip()
            next_gameType = game_modes_names_inverse[next_gameType]

            self._next_typeandmap = 'b3_%s_%s' % (next_gameType.lower(), next_mapName.lower())
            self.debug('Type and Map Config for Next Map: %s' %(self._next_typeandmap))

            self._next_gametype = 'b3_%s' % (next_gameType.lower())
            self.debug('Gametype Config for Next Map: %s' %(self._next_gametype))

    def config_manager_check_config(self):
        """
        Check and run the configs
        """
        if os.path.isfile(self._configManager_configPath + os.path.sep + self._next_typeandmap + '.cfg'): # b3_<gametype>_<mapname>.cfg
            _fName = self._configManager_configPath + os.path.sep + self._next_typeandmap + '.cfg'
            self.debug('Executing %s.cfg' %(self._next_typeandmap))
            self._load_server_config_from_file(client=None, config_name=self._next_typeandmap, file_path=_fName, threaded=True)

        elif os.path.isfile(self._configManager_configPath + os.path.sep + self._next_gametype + '.cfg'): # b3_<gametype>.cfg
            _fName = self._configManager_configPath + os.path.sep + self._next_gametype + '.cfg'
            self.debug('Executing %s.cfg' %(self._next_gametype))
            self._load_server_config_from_file(client=None, config_name=self._next_gametype, file_path=_fName, threaded=True)

        elif os.path.isfile(self._configManager_configPath + os.path.sep + 'b3_main.cfg'): # b3_main.cfg
            _fName = self._configManager_configPath + os.path.sep + 'b3_main.cfg'
            self.debug('Executing b3_main.cfg')
            self._load_server_config_from_file(client=None, config_name='b3_main.cfg', file_path=_fName, threaded=True)

        else:
            self.debug('No matching configs found.')

    def _sendMessage(self, client, msg):
        """
        send message to console when client is None
        """
        if client:
            client.message(msg)
        else:
            self.debug(msg)

    def _get_rounds_left(self):
        """
        check and return rounds left
        """
        rounds = self.console.write(('mapList.getRounds',))
        current_round = int(rounds[0]) + 1
        total_rounds = int(rounds[1])
        rounds_left = total_rounds - current_round
        return rounds_left
