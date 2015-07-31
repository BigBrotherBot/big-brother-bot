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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA

__version__ = '1.8'
__author__  = 'Courgette, 82ndab-Bravo17, ozon, Mario'

import re
import ConfigParser
import random
import time
import os
import thread
import b3
import b3.cron
import b3.events

from b3.plugin import Plugin
from b3.functions import getCmd
from b3.functions import soundex
from b3.functions import levenshteinDistance
from ConfigParser import NoOptionError
from b3.parsers.frostbite2.protocol import CommandFailedError
from b3.parsers.frostbite2.util import MapListBlock
from b3.parsers.frostbite2.util import PlayerInfoBlock
from b3.parsers.bf3 import GAME_MODES_NAMES
from b3.parsers.bf3 import GUNMASTER_WEAPONS_PRESET_BY_INDEX


class Scrambler:

    _plugin = None
    _getClients_method = None
    _last_round_scores = PlayerInfoBlock([0,0])

    def __init__(self, plugin):
        self._plugin = plugin
        self._getClients_method = self._getClients_randomly

    def scrambleTeams(self):
        clients = self._getClients_method()
        if not len(clients):
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
        sumofscores = reduce(lambda x, y: x + y, [int(data['score']) for data in self._last_round_scores], 0)
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


class vip_commands_mixin(object):
    
    def cmd_viplist(self, data, client, cmd=None):
        """
        [filter] - display all VIPs or VIP matched by the given filter
        """
        vips = self.getFullreservedSlotsList()
        if not len(vips):
            client.message("VIP list is empty")
        else:

            if data:
                filter_txt = data.lower()
                filtered_vips = filter(lambda x: filter_txt in x.lower(), vips)
                if not len(filtered_vips):
                    client.message("no VIP matching '%s' found over the %s existing VIPs" % (filter_txt, len(vips)))
                    return
                else:
                    vips = filtered_vips

            connected_players = [x.cid for x in self.console.clients.getList()]
            connected_vips = []
            other_vips = []
            for x in vips:
                if x in connected_players:
                    connected_vips.append(x)
                else:
                    other_vips.append(x)
            msg = ''
            if len(connected_vips):
                client.message("Connected VIPs: " + ', '.join(connected_vips))
                msg = 'other '
            msg += "VIPs: " + ', '.join(other_vips[:15])
            if len(other_vips) > 15:
                msg += ' and %s more...' % (len(other_vips) - 15)
            if len(other_vips) > 0:
                client.message(msg)

    def cmd_vips(self, data, client, cmd=None):
        """
        display all online VIPs
        """
        vips = self.getFullreservedSlotsList()
        if not len(vips):
            client.message("No VIP connected")
        else:
            from operator import attrgetter
            connected_players = map(attrgetter('cid'), self.console.clients.getList())
            connected_vips = [x for x in vips if x in connected_players]
            if not len(connected_vips):
                client.message("No VIP connected")
            else:
                client.message("Connected VIPs: " + ', '.join(connected_vips))

    def cmd_vipadd(self, data, client, cmd=None):
        """
        <player> - makes a player a VIP
        """
        if not data:
            client.message("Usage: !vipadd <player>")
        else:
            rv = self.findClientSilent(data)
            if rv is None:
                # a player matching the name was not found online or by its B3 id
                # assume data is the exact player name to be added in the VIP list
                name = data
            elif type(rv) is list:
                # multiple players matches data
                client.message(self.getMessage('players_matched', data, ', '.join(rv)))
                return
            else:
                # we got a match
                name = rv

            try:
                self.console.write(('reservedSlotsList.add', name))
            except CommandFailedError, err:
                client.message('Error: %s' % err.message)
            else:
                client.message('%s is now a VIP' % name)

    def cmd_vipremove(self, data, client, cmd=None):
        """
        <player> - remove VIP privileges to a player
        """
        if not data:
            client.message("Usage: !vipremove <player>")
        else:
            rv = self.findClientSilent(data)
            if rv is None:
                # a player matching the name was not found online or by its B3 id
                # assume the player may be in the VIP list
                if data.lower() in [x.lower() for x in self.getFullreservedSlotsList()]:
                    name = data
                else:
                    client.message("No VIP named '%s' found" % data)
                    return
            elif type(rv) is list:
                client.message(self.getMessage('players_matched', data, ', '.join(rv)))
                return
            else:
                # we got a match
                name = rv

            # try to identify the player to remove
            clients = self.lookupClientByExactName(name)
            if len(clients) == 1:
                sclient = clients[0]
                name = sclient.name
                if sclient.id != client.id and sclient.maxLevel > client.maxLevel:
                    if sclient.maxGroup:
                        client.message(self.getMessage('operation_denied_level', {'name': sclient.name, 'group': sclient.maxGroup.name}))
                    else:
                        client.message(self.getMessage('operation_denied'))
                    return
            try:
                self.console.write(('reservedSlotsList.remove', name))
            except CommandFailedError, err:
                if err.message[0] == 'PlayerNotInList':
                    client.message("There is no VIP named '%s'" % name)
                else:
                    client.message('Error: %s' % err.message[0])
            else:
                client.message('VIP privileges removed for %s' % name)

    def cmd_vipclear(self, data, client, cmd=None):
        """
        clears the VIP list
        """
        try:
            self.console.write(('reservedSlotsList.clear',))
        except CommandFailedError, err:
            client.message('Error: %s' % err.message[0])
        else:
            client.message('VIP list is now empty')

    def cmd_vipload(self, data, client, cmd=None):
        """
        loads the VIP list from disk
        """
        try:
            self.console.write(('reservedSlotsList.load',))
            vips = self.getFullreservedSlotsList()
        except CommandFailedError, err:
            client.message('Error: %s' % err.message[0])
        else:
            client.message('VIP list loaded from disk (%s name%s loaded)' % (len(vips), 's' if len(vips) else ''))

    def cmd_vipsave(self, data, client, cmd=None):
        """
        saves the VIP list to disk
        """
        try:
            vips = self.getFullreservedSlotsList()
            self.console.write(('reservedSlotsList.save',))
        except CommandFailedError, err:
            client.message('Error: %s' % err.message[0])
        else:
            client.message('VIP list saved to disk (%s name%s written)' % (len(vips), 's' if len(vips) else ''))

    def getFullreservedSlotsList(self):
        """query the Frostbite2 game server and return a list containing all vip player names of the current
         reserved slots list.
        """
        names = list()
        offset = 0
        tmp = self.console.write(('reservedSlotsList.list', offset))
        tmp_num_values = len(tmp)
        while tmp_num_values:
            names.extend(tmp)
            tmp = self.console.write(('reservedSlotsList.list', len(names)))
            tmp_num_values = len(tmp)
            # remove duplicates
        seen = set()
        seen_add = seen.add
        return [ x for x in names if x not in seen and not seen_add(x)]


class Poweradminbf3Plugin(Plugin, vip_commands_mixin):

    requiresParsers = ['bf3']

    def __init__(self, console, config=None):
        self._adminPlugin = None
        self._configPath = ''
        self._configManager_configPath = ''
        self.no_level_check_level = 100
        self._configmanager_delay = 5
        self._team_swap_threshold = 3
        self._team_swap_threshold_current = 0
        self._team_swap_threshold_prop = False
        self._autoassign = False
        self._no_autoassign_level = 20
        self._joined_order = []
        self._autobalance = False
        self._run_autobalancer = False
        self._one_round_over = False
        self._autobalance_timer = 60
        self._autobalance_message_interval = 10
        self._cronTab_autobalance = None
        self._scramblingdone = False
        self._scrambling_planned = False
        self._autoscramble_rounds = False
        self._autoscramble_maps = False
        self._autoscramble_gamemode_blacklist = []
        self._scrambler = Scrambler(self)
        self._last_idleTimeout = 300
        self._yell_duration = 10
        self._next_typeandmap = ''
        self._next_gametype = ''
        Plugin.__init__(self, console, config)

    ####################################################################################################################
    #                                                                                                                  #
    #    PLUGIN INTERFACE IMPLEMENTATION                                                                               #
    #                                                                                                                  #
    ####################################################################################################################

    def onLoadConfig(self):
        """
        This is called after loadConfig(). Any plugin private variables loaded
        from the config need to be reset here.
        """
        self._load_messages()
        self._load_config_path()
        self._load_no_level_check_level()
        self._load_autobalance_settings()
        self._load_scrambler()
        self._load_configmanager_config_path()
        self._load_configmanager()
        self._load_yell_duration()

    def onStartup(self):
        """
        Initialize plugin settings
        """
        self._adminPlugin = self.console.getPlugin('admin')

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

        # Register our events
        self.registerEvent('EVT_GAME_ROUND_START', self.onRoundStart)
        self.registerEvent('EVT_GAME_ROUND_END', self.onRoundEnd)
        self.registerEvent('EVT_GAME_ROUND_PLAYER_SCORES', self.onGameRoundPlayerScores)
        self.registerEvent('EVT_CLIENT_AUTH', self.onAuth)
        self.registerEvent('EVT_CLIENT_DISCONNECT', self.onDisconnect)
        self.registerEvent('EVT_CLIENT_TEAM_CHANGE', self.onTeamChange)

    ####################################################################################################################
    #                                                                                                                  #
    #    HANDLE EVENTS                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def onRoundStart(self, event):
        """
        Handle EVT_GAME_ROUND_START
        """
        self.debug('manual scramble planned : '.rjust(30) + str(self._scrambling_planned))
        self.debug('auto scramble rounds : '.rjust(30) + str(self._autoscramble_rounds))
        self.debug('auto scramble maps : '.rjust(30) + str(self._autoscramble_maps))
        self.debug('self.console.game.rounds : '.rjust(30) + repr(self.console.game.rounds))
        if self._scrambling_planned:
            self.debug('manual scramble is planned')
            self._scrambler.scrambleTeams()
            self._scrambling_planned = False
        else:
            if self.console.game.gameType not in self._autoscramble_gamemode_blacklist:
                if self._autoscramble_rounds:
                    self.debug('auto scramble is planned for rounds')
                    self._scrambler.scrambleTeams()
                elif self._autoscramble_maps and self.console.game.rounds == 1:
                    self.debug('auto scramble is planned for maps')
                    self._scrambler.scrambleTeams()
            else:
                self.info(r"ignoring auto scramble as current gamemode '%s' is in the blacklist (see config option"
                    + " 'scrambler\gamemodes_blacklist')" % self._autoscramble_gamemode_blacklist)
        self.debug('Scrambling finished, Autoassign now active')
        self._scramblingdone = True
        self.start_autobalance_cron()

    def onRoundEnd(self, event):
        """
        Handle EVT_GAME_ROUND_END
        """
        self._scramblingdone = False
        self._run_autobalancer = False
        if self._cronTab_autobalance:
            # remove existing crontab
            self.console.cron.cancel(id(self._cronTab_autobalance))
        if not self._one_round_over:
            self._one_round_over = True
            self.debug('One round finished, Autoassign and Autobalance now active')

        if self._configmanager:
            self.config_manager_construct_file_names()
            self.config_manager_check_config()

    def onGameRoundPlayerScores(self, event):
        """
        Handle EVT_GAME_ROUND_PLAYER_SCORES
        """
        self._scrambler.onRoundOverTeamScores(event.data)

    def onAuth(self, event):
        """
        Handle EVT_CLIENT_AUTH
        """
        self.debug(self.console.upTime())
        if self._one_round_over and self._autoassign and self._scramblingdone:
            self.autoassign(event.client)
        self.client_connect(event.client)

    def onDisconnect(self, event):
        """
        Handle EVT_CLIENT_DISCONNECT
        """
        self.client_disconnect(event.client, event.data)

    def onTeamChange(self, event):
        """
        Handle EVT_CLIENT_DISCONNECT
        """
        if self._one_round_over and self._autoassign and self._scramblingdone:
            self.autoassign(event.client)

    ####################################################################################################################
    #                                                                                                                  #
    #    COMMANDS IMPLEMENTATION                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def cmd_roundnext(self, data, client, cmd=None):
        """
        Switch to next round, without ending current
        """
        self.console.say('forcing next round')
        time.sleep(1)
        try:
            self.console.write(('mapList.runNextRound',))
        except CommandFailedError, err:
            client.message('Error: %s' % err.message)

    def cmd_serverreboot(self, data, client, cmd=None):
        """
        Restart the Battlefield 3 Gameserver.
        """
        # @todo: add dialog - Demand that the user wants to restart really
        try:
            self.console.say('Reboot the Gameserver')
            time.sleep(1)
            self.console.write(('admin.shutDown',))
        except CommandFailedError, err:
            client.message('Error: %s' % err.message[0])

    def cmd_endround(self, data, client, cmd=None):
        """
        <team id> - End current round. team id is the winning team
        """
        winnerTeamID = ''
        if not data:
            winnerTeamID = self.current_winningTeamID()
        else:
            args = cmd.parseData(data)
            if args[0].isdigit():
                winnerTeamID = args[0]
            else:
                client.message('Use a number to determine the winning team.')

        if winnerTeamID:
            try:
                self.console.say('End current round')
                time.sleep(1)
                self.console.write(('mapList.endRound', winnerTeamID))
            except CommandFailedError, err:
                client.message('Error: %s' % err.message[0])

    def cmd_roundrestart(self, data, client, cmd=None):
        """
        Restart current round
        """
        self.console.say('Restart current round')
        time.sleep(1)
        try:
            self.console.write(('mapList.restartRound',))
        except CommandFailedError, err:
            client.message('Error: %s' % err.message)

    def cmd_kill(self, data, client, cmd=None):
        """
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
        """
        <name> - change a player to the other team
        """
        if not data:
            client.message('Invalid data, try !help changeteam')
        else:
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
                    original_team = sclient.teamId
                    num_teams = 2 if self.console.game.gameType != 'SquadDeathMatch0' else 4
                    newteam = (sclient.teamId % num_teams) + 1
                    try:
                        self.console.write(('admin.movePlayer', sclient.cid, newteam, 0, 'true'))
                        cmd.sayLoudOrPM(client, '%s forced from team %s to team %s' % (sclient.cid, original_team, newteam))
                    except CommandFailedError, err:
                        client.message('Error, server replied %s' % err)

    def cmd_swap(self, data, client, cmd=None):
        """
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

        if self._autoassign:
            temp_autoassign = True
            self._autoassign = False
        else:
            temp_autoassign = False

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

        self._autoassign = temp_autoassign

    def cmd_punkbuster(self, data, client, cmd=None):
        """
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
        """
        <map> [, gamemode [, num of rounds]] - Set the nextmap (partial map name works)
        """
        if not data:
            client.message('Invalid or missing data, try !help setnextmap')
            return

        parsed_data = self._adminPlugin.parse_map_parameters(data, client)
        if not parsed_data:
            return

        map_id, gamemode_id, num_rounds = parsed_data

        maplist = MapListBlock(self.console.write(('mapList.list',)))
        if not len(maplist):
            # maplist is empty, nextmap will be inserted at index 0
            self.console.write(('mapList.add', map_id, gamemode_id, num_rounds, 0))
            self.console.write(('mapList.setNextMapIndex', 0))
        else:
            current_map_index = int(self.console.write(('mapList.getMapIndices', ))[0])
            matching_maps = maplist.getByNameGamemodeAndRounds(map_id, gamemode_id, num_rounds)
            if not len(matching_maps):
                # then insert wanted map in rotation list
                next_map_index = current_map_index + 1
                self.console.write(('mapList.add', map_id, gamemode_id, num_rounds, next_map_index))
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
            map_info = '%s (%s) %s round%s' % (self.console.getEasyName(map_id), self.console.getGameMode(gamemode_id), num_rounds, 's' if num_rounds>1 else '')
            cmd.sayLoudOrPM(client, 'next map set to %s' % map_info)

    def cmd_loadconfig(self, data, client=None, cmd=None):
        """
        <config name> - Load a server config file
        """
        if not data:
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
        """
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
        """
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
        """
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

    def cmd_vehicles(self, data, client=None, cmd=None):
        """
        <on|off> - Toggle vehicles on or off
        """
        expected_values = ('on', 'off')
        if not data or data.lower() not in expected_values:
            if data.lower() not in expected_values and data != '':
                client.message("unexpected value '%s'. Available modes : %s" % (data, ', '.join(expected_values)))
            try:
                current_mode = self.console.getCvar('vehicleSpawnAllowed').getString()
                self.console.game['vehicleSpawnAllowed'] = current_mode
                if current_mode == 'true':
                    current_mode = 'ON'
                elif current_mode == 'false':
                    current_mode = 'OFF'
            except Exception, err:
                self.error(err)
                current_mode = 'unknown'
            cmd.sayLoudOrPM(client=client, message="Vehicle spawn is [%s]" % current_mode)
        else:
            new_value = 'true' if data.lower() == 'on' else 'false'
            try:
                self.console.setCvar('vehicleSpawnAllowed', new_value)
            except CommandFailedError, err:
                client.message("could not change vehicle spawn mode : %s" % err.message)
            else:
                self.console.game['vehicleSpawnAllowed'] = new_value
                cmd.sayLoudOrPM(client=client, message="vehicle spawn is now [%s]" % data.upper())

    def cmd_idle(self, data, client=None, cmd=None):
        """
        <on|off|minutes> - Toggle idle on / off or the number of minutes you choose
        """
        def current_value():
            try:
                cvar = self.console.getCvar('idleTimeout')
                if cvar is None:
                    return 'unknown'
                current_mode = cvar.getString()
                self.console.game['idleTimeout'] = current_mode
                return current_mode
            except Exception, err:
                self.error(err)
                return 'unknown'

        def human_readable_value(value):
            if value == '0':
                return 'OFF'
            elif value.lower() == 'unknown':
                return 'unknown'
            else:
                v = str(round(float(value)/60,1))
                return "%s min" % v[:-2] if v.endswith('.0') else v

        original_value = current_value()
        if not data:
            if original_value == 'unknown':
                message = "unknown"
            else:
                if original_value == '0':
                    message = "OFF"
                else:
                    message = human_readable_value(original_value)
            cmd.sayLoudOrPM(client=client, message="Idle kick is [%s]" % message)
        else:
            minutes = None
            try:
                minutes = int(data)
            except ValueError:
                pass

            expected_values = ('on', 'off')
            if data.lower() not in expected_values and minutes is None:
                client.message("unexpected value '%s'. Available modes : %s or a number of minutes" % (data, ', '.join(expected_values)))
                return

            new_value = None
            if data.lower() == 'off':
                self._last_idleTimeout = original_value
                new_value = 0
            elif data.lower() == 'on':
                if original_value not in ('0', 'unknown'):
                    client.message("Idle kick is already ON and set to %s" % human_readable_value(original_value))
                    return
                else:
                    new_value = self._last_idleTimeout
            else:
                new_value = minutes * 60

            try:
                self.console.setCvar('idleTimeout', new_value)
            except CommandFailedError, err:
                client.message("could not change idle timeout : %s" % err.message)
            else:
                self.console.game['idleTimeout'] = str(new_value)
                cmd.sayLoudOrPM(client=client, message="Idle kick is now [%s]" % human_readable_value( str(new_value)))

    def cmd_autoassign(self, data, client, cmd=None):
        """
        <off|on> manage the auto assign
        """

        if not data:
            if self._autoassign:
                client.message("Autoassign is currently on, use !autoassign off to turn off")
            else:
                client.message("Autoassign is currently off, use !autoassign on to turn on")
        else:
            if data.lower() == 'off':
                self._autoassign = False
                client.message('Autoassign now disabled')
                if self._autobalance:
                    self._autobalance = False
                    client.message('Autobalance now disabled')
            elif data.lower() == 'on':
                self._autoassign = True
                client.message('Autoassign now enabled')
            else:
                client.message("invalid data. Expecting on or off")

    def cmd_autobalance(self, data, client, cmd=None):
        """
        <off|on|now> manage the auto balance
        """

        if not data:
            if self._autobalance:
                client.message("Autobalance is currently on, use !autobalance off to turn off")
            else:
                client.message("Autobalance is currently off, use !autobalance on to turn on")
        else:
            if data.lower() == 'off':
                self._autobalance = False
                client.message('Autobalance now disabled')
                if self._cronTab_autobalance:
                    # remove existing crontab
                    self.console.cron - self._cronTab_autobalance

            elif data.lower() == 'on':
                if self._autobalance:
                    client.message('Autobalance is already enabled')
                else:
                    self._autobalance = True
                    if self._one_round_over:
                        self.start_autobalance_cron()
                        client.message('Autobalance now enabled')
                    else:
                        client.message('Autobalance will be enabled on next round start')
                    if not self._autoassign:
                        self._autoassign = True
                        client.message('Autoassign now enabled')

            elif data.lower() == 'now':
                self.run_autobalance()
            else:
                client.message("invalid data. Expecting on, off or now")

    def cmd_yell(self, data, client, cmd=None):
        """
        <msg>- Yell message to all players
        """
        if client :
            if not data:
                client.message('missing parameter, try !help yell')
            else:
                self.console.write(self.console.getCommand('yell', message=data, big_msg_duration=self._yell_duration))

    def cmd_yellteam(self, data, client, cmd=None):
        """
        <msg> Yell message to all players of your team
        """
        if not data:
            client.message('missing parameter, try !help yellteam')
        else:
            self.console.write(self.console.getCommand('yellTeam', message=data, teamId=client.teamId, big_msg_duration=self._yell_duration))

    def cmd_yellsquad(self, data, client, cmd=None):
        """
        <msg> Yell message to all players of your squad
        """
        if not data:
            client.message('missing parameter, try !help yellsquad')
        else:
            self.console.write(self.console.getCommand('yellSquad', message=data, teamId=client.teamId, squadId=client.squad, big_msg_duration=self._yell_duration))

    def cmd_yellplayer(self, data, client, cmd=None):
        """
        <player> <msg> - Yell message to a player
        """
        m = self._adminPlugin.parseUserCmd(data)
        if not m:
            client.message('invalid parameters, try !help yellplayer')
            return
        cid, message = m
        sclient = self._adminPlugin.findClientPrompt(cid, client)
        if sclient:
            self.console.write(self.console.getCommand('bigmessage', message=message, cid=sclient.cid, big_msg_duration=self._yell_duration))

    def cmd_nuke(self, data, client, cmd=None):
        """
        <all|ru|us> [reason] - Kill all players (or players from a given team) without scoring effects
        """
        m = self._adminPlugin.parseUserCmd(data)
        if not m:
            client.message('missing parameter, try !help nuke')
            return
        team_name, reason = m
        clean_team_name = team_name.lower()
        if not clean_team_name or clean_team_name not in ('all', 'ru', 'us'):
            client.message("invalid parameter. expecting all, ru or us")
        else:
            self.console.saybig("Incoming nuke warning")

            if clean_team_name == 'all':
                self.console.say("Killing all players")
            elif clean_team_name == 'ru':
                self.console.say("Killing Russian team")
            elif clean_team_name == 'us':
                self.console.say("Killing USA team")

            time.sleep(2.5)

            if reason:
                self.console.say("Nuke reason : %s" % reason)

            def kill(sclient, reason="Nuked by admin"):
                try:
                    self.console.write(('admin.killPlayer', sclient.cid))
                    if reason:
                        sclient.message("Nuke reason: %s" % reason)
                    else:
                        sclient.message("Nuked by admin")
                except CommandFailedError, err:
                    if err.message[0] == "SoldierNotAlive":
                        client.message("%s is already dead" % sclient.name)
                    else:
                        client.message('Error: %s' % err.message)

            players = self.console.clients.getList()
            if clean_team_name == 'all':
                for player in players:
                    kill(player, reason)
            elif clean_team_name == 'us':
                for player in [x for x in players if x.teamId == 1]:
                    kill(player, reason)
            elif clean_team_name == 'ru':
                for player in [x for x in players if x.teamId == 2]:
                    kill(player, reason)

    def cmd_gunmaster(self, data, client, cmd=None):
        """
        <index> - Set Weapon Preset for the next Gunmaster round
        """
        # generate human readable  preset list
        _preset_list = []
        for i in range(len(GUNMASTER_WEAPONS_PRESET_BY_INDEX)):
            _preset_list.append( '%d - %s' % (i, GUNMASTER_WEAPONS_PRESET_BY_INDEX[i][0]))
        # handle command args
        if not data:
            _current_preset = self.console.getCvar('gunMasterWeaponsPreset').getInt()
            client.message('Current Gunmaster Preset: %s' % _preset_list[_current_preset])
        else:
            if data[0].isdigit():
                if int(data[0]) in range(len(GUNMASTER_WEAPONS_PRESET_BY_INDEX)):
                    _new_preset = int(data[0])
                    try:
                        self.console.setCvar('gunMasterWeaponsPreset', int(_new_preset))
                        client.message('Set %s for the next Round.' % _preset_list[_new_preset])
                    except CommandFailedError:
                        pass
                else:
                    client.message('Weapon Preset %s doesn\'t exists' % data[0])
            elif data == 'show':
                client.message('Available Presets: %s' % ', '.join(_preset_list))
            else:
                client.message('wrong parameter, try !help gunmaster')

    ####################################################################################################################
    #                                                                                                                  #
    #    OTHER METHODS                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

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

        re_valid_gamemode = re.compile(r"^[a-z]+\d$", re.IGNORECASE)
        blacklist = []
        try:
            try:
                blacklist_raw = self.config.get('scrambler', 'gamemodes_blacklist')
                gamemodes_list = re.split('\W+', blacklist_raw)
                invalid_gamemodes = []
                for gamemode in gamemodes_list:
                    if not re_valid_gamemode.match(gamemode):
                        invalid_gamemodes.append(gamemode)
                    else:
                        blacklist.append(gamemode)
                if len(invalid_gamemodes):
                    self.warning(r"option 'srambler\gamemodes_blacklist' in your config file has invalid gamemode(s) : %s" % ', '.join(invalid_gamemodes))
            except ConfigParser.NoOptionError:
                self.warning(r"cannot find option 'srambler\gamemodes_blacklist' in your config file")

        except Exception, err:
            self.error(err)
        self._autoscramble_gamemode_blacklist = blacklist
        self.info('auto scrambler will ignore gamemodes : %s' % ', '.join(blacklist) if len(blacklist) else 'auto scrambler will not ignore any gamemodes')

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
        self.no_level_check_level = self.getSetting('preferences', 'no_level_check_level', b3.LEVEL, default=100)
        self.info('no_level_check_level is %s' % self.no_level_check_level)

    def _load_autobalance_settings(self):
        self._no_autoassign_level = self.getSetting('preferences', 'no_autoassign_level', value_type=b3.LEVEL, default=20)
        self.info('no_autoassign_level is %s' % self._no_autoassign_level)

        try:
            self._autoassign = self.config.getboolean('preferences', 'autoassign')
        except NoOptionError:
            self.info('No config option \"preferences\\autoassign\" found. Using default value : %s' % self._autoassign)
        except ValueError, err:
            self.debug(err)
            self.warning('Could not read level value from config option \"preferences\\autoassign\". Using default value \"%s\" instead. (%s)' % (self._autoassign, err))
        except Exception, err:
            self.error(err)
        self.info('autoassign is %s' % self._autoassign)

        try:
            self._autobalance = self.config.getboolean('preferences', 'autobalance')
        except NoOptionError:
            self.info('No config option \"preferences\\autobalance\" found. Using default value : %s' % self._autobalance)
        except ValueError, err:
            self.debug(err)
            self.warning('Could not read level value from config option \"preferences\\autobalance\". Using default value \"%s\" instead. (%s)' % (self._autobalance, err))
        except Exception, err:
            self.error(err)
        self.info('autobalance is %s' % self._autobalance)

        if self._autobalance:
            if not self._autoassign:
                self._autoassign = True
                self.info('Autobalance is ON, so turning Autoassign ON also')

        try:
            self._autobalance_timer = self.config.getint('preferences', 'autobalance_timer')
        except NoOptionError:
            self.info('No config option \"preferences\\autobalance_timer\" found. Using default value : %s' % self._autobalance_timer)
        except ValueError, err:
            self.debug(err)
            self.warning('Could not read level value from config option \"preferences\\autobalance_timer\". Using default value \"%s\" instead. (%s)' % (self._autobalance_timer, err))
        except Exception, err:
            self.error(err)
        if self._autobalance_timer < 30:
            self._autobalance_timer = 30
        self.info('Autobalance timer is %s seconds' % self._autobalance_timer)
        self._autobalance_message_interval = self._autobalance_timer // 6
        if self._autobalance_message_interval > 10:
            self._autobalance_message_interval = 10
        self.info('Autobalance message interval is %s seconds' % self._autobalance_message_interval)

        try:
            self._team_swap_threshold = self.config.getint('preferences', 'team_swap_threshold')
        except NoOptionError:
            self.info(r'No config option "preferences\team_swap_threshold" found. Using default value : %s' % self._team_swap_threshold)
        except ValueError, err:
            self.debug(err)
            self.warning(r'Could not read level value from config option "preferences\team_swap_threshold". Using default value "%s" instead. (%s)' % (self._team_swap_threshold, err))
        except Exception, err:
            self.error(err)
        if self._team_swap_threshold < 2:
            self._team_swap_threshold = 2
        self.info('team swap threshold is %s' % self._team_swap_threshold)

        try:
            self._team_swap_threshold_prop = self.config.getboolean('preferences', 'team_swap_threshold_prop')
        except NoOptionError:
            self.info('No config option \"preferences\\team_swap_threshold_prop\" found. Using default value : %s' % self._team_swap_threshold_prop)
        except ValueError, err:
            self.debug(err)
            self.warning('Could not read level value from config option \"preferences\\team_swap_threshold_prop\". Using default value \"%s\" instead. (%s)' % (self._team_swap_threshold_prop, err))
        except Exception, err:
            self.error(err)
        if self._team_swap_threshold_prop:
            self.info('Team swap threshold will vary according to server population')
        else:
            self.info('Team swap threshold is constant')

    def _load_configmanager(self):
        try:
            self._configmanager = self.config.getboolean('configmanager', 'status')
            self.debug('Configmanager: %s' % self._configmanager)
        except Exception, err:
            self.debug('Unable to load configmanager status from config file, disabling it', exc_info=err)
            self._configmanager = False

    def _load_yell_duration(self):
        try:
            duration = self.config.getint('preferences', 'yell_duration')
            if duration < 1:
                raise ValueError("cannot be lower than a second")
            self._yell_duration = duration
            self.debug('yell_duration: %s' % self._yell_duration)
        except NoOptionError:
            self.info(r'No config option "preferences\yell_duration" found. Using default value : %s' % self._yell_duration)
        except ValueError, err:
            self.debug(err)
            self.warning(r'Could not read value from config option "preferences\yell_duration". Using default value "%s" instead. (%s)' % (self._yell_duration, err))
        except Exception, err:
            self.error(err)

    def _movePlayer(self, client, teamId, squadId=0):
        self.console.write(('admin.movePlayer', client.cid, teamId, squadId, 'true'))
        client.setvar(self, 'movedByBot', True)

    @staticmethod
    def _get_server_config_directory(dir_name=''):
        return b3.getAbsolutePath('@b3/plugins/poweradminbf3/%s' % dir_name)

    def _load_server_config_from_file(self, client, config_name, file_path, threaded=False):
        """
        Loads a preset config file to send to the server
        """
        self.info('Loading %s' % file_path)
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
                    self._sendMessage(client, 'Error "%s" received at line %s when sending "%s" to server' % (err.message, line_index, line))
            else:
                # read cvar
                try:
                    result = self.console.write((m.group('cvar'),))
                    if len(result):
                        self._sendMessage(client, ("%s is \"%s\"" % (m.group('cvar'), result[0])))
                except CommandFailedError, err:
                    self._sendMessage(client, 'Error "%s" received at line %s when sending "%s" to server' % (err.message, line_index, m.group('cvar')))

        if len(map_item_matches):
            self.console.write(('mapList.clear',)) # clear current in-memory map rotation list
            for line_index, line, m in map_item_matches:
                try:
                    self.console.write(('mapList.add', m.group('map_id'), m.group('gamemode'), m.group('num_rounds')))
                except CommandFailedError, err:
                    self._sendMessage(client, "Error adding map \"%s\" on line %s : %s" % (line, line_index, err.message))
            try:
                self.console.write(('mapList.save',)) # write current in-memory map list to server config file so if the server restarts our list is recovered.
                self._sendMessage(client, "New map rotation list written to disk.")
            except CommandFailedError, err:
                self._sendMessage(client, "Error writing map rotation list to disk. %s" % err.message)

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
            matches.sort(key=lambda w: levenshteinDistance(clean_config_name, w))

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
            self.debug('Type and Map Config: %s' % self._next_typeandmap)

            self._next_gametype = 'b3_%s' % c.gameType.lower()
            self.debug('Gametype Config: %s' % self._next_gametype)
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
            self.debug('Type and Map Config for Next Map: %s' % self._next_typeandmap)

            self._next_gametype = 'b3_%s' % next_gameType.lower()
            self.debug('Gametype Config for Next Map: %s' % self._next_gametype)

    def config_manager_check_config(self):
        """
        Check and run the configs
        """
        if os.path.isfile(self._configManager_configPath + os.path.sep + self._next_typeandmap + '.cfg'): # b3_<gametype>_<mapname>.cfg
            _fName = self._configManager_configPath + os.path.sep + self._next_typeandmap + '.cfg'
            self.info('Executing %s.cfg' % self._next_typeandmap)
            self._load_server_config_from_file(client=None, config_name=self._next_typeandmap, file_path=_fName, threaded=True)

        elif os.path.isfile(self._configManager_configPath + os.path.sep + self._next_gametype + '.cfg'): # b3_<gametype>.cfg
            _fName = self._configManager_configPath + os.path.sep + self._next_gametype + '.cfg'
            self.info('Executing %s.cfg' % self._next_gametype)
            self._load_server_config_from_file(client=None, config_name=self._next_gametype, file_path=_fName, threaded=True)

        elif os.path.isfile(self._configManager_configPath + os.path.sep + 'b3_main.cfg'): # b3_main.cfg
            _fName = self._configManager_configPath + os.path.sep + 'b3_main.cfg'
            self.info('Executing b3_main.cfg')
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


    def autoassign(self, client):
        """
        Auto Assign team on joining or changing teams to keep teams balanced
        """
        self.debug('Starting Autoassign for %s' % client.name)
        if client.maxLevel >= self._no_autoassign_level:
            return
        clients = self.console.clients.getList()
        if len(clients) < 3:
            return
        team1, team2 = self.count_teams(clients)
        self.debug('Team1 = %s' % team1)
        self.debug('Team2 = %s' % team2)
        self.debug('New Client team is %s' % client.teamId)
        if team1 - team2 >= self._team_swap_threshold and client.teamId == 1:
            self.debug('Move player to team 2')
            self._movePlayer(client, 2)

        elif team2 - team1 >= self._team_swap_threshold and client.teamId == 2:
            self.debug('Move player to team 1')
            self._movePlayer(client, 1)
        else:
            self.debug('Noone needs moving')

    def run_autobalance(self):
        """
        Perform Auto balance to keep teams balanced
        """
        clients = self.console.clients.getList()
        team1, team2 = self.count_teams(clients)
        self.set_swap_threshold(team1+team2)
        team1more = team1 - team2
        team2more = team2 - team1
        self.debug('Team1 %s vs Team2 %s, threshold %s' % (team1, team2, self._team_swap_threshold_current))
        if team1more >= self._team_swap_threshold_current or team2more >= self._team_swap_threshold_current:
            self._run_autobalancer = True
            self.console.say('Auto balancing teams in %s seconds' % (self._autobalance_message_interval*2))
            i = 0
            while i < self._autobalance_message_interval:
                time.sleep(1)
                i += 1

            self.console.say('Auto balancing teams in %s seconds' % self._autobalance_message_interval)
            i = 0
            while i < self._autobalance_message_interval:
                time.sleep(1)
                i += 1
            self.console.say('Auto balancing teams')
            self.debug('Auto balancing teams')

            clients = self.console.clients.getList()
            team1, team2 = self.count_teams(clients)
            self.set_swap_threshold(team1+team2)
            team1more = team1 - team2
            team2more = team2 - team1
            self.debug('Team1 %s vs Team2 %s, threshold %s' % (team1, team2, self._team_swap_threshold_current))
            if team1more >= self._team_swap_threshold_current or team2more >= self._team_swap_threshold_current:
                if team1more > 0:
                    players_to_move = team1more//2
                    self.auto_move_players( 1, players_to_move)

                else:
                    players_to_move = team2more//2
                    self.auto_move_players( 2, players_to_move)

        self._run_autobalancer = False
        self.start_autobalance_cron()

    def auto_move_players(self, team, players):
        if team == 1:
            newteam = 2
        else:
            newteam = 1

        ind = len(self._joined_order)
        self.debug('Moving %s players from Team %s to %s' % (players, team, newteam))
        while ind > 0 and players > 0:
            ind -= 1
            cl = self._adminPlugin.findClientPrompt(self._joined_order[ind])
            if cl:
                if cl.teamId == team and cl.maxLevel <= self._no_autoassign_level:
                    if self._run_autobalancer:
                        self._movePlayer(cl, newteam)
                        self.console.say('Moving %s to team %s' % (cl.name, newteam))
                        self.debug('Moving %s to team %s' % (cl.name, newteam))
                        players -= 1
            else:
                del self._joined_order[ind]

        if players > 0:
            self.console.say('Not enough players to move')

    def autobalance_time(self):
        s = self._autobalance_timer
        m = int(time.strftime('%M'))
        s += int(time.strftime('%S'))
        while s > 59:
            m += 1
            s -= 60
        if m > 59:
            m -= 60
        return m, s

    def start_autobalance_cron(self):
        if self._cronTab_autobalance:
            # remove existing crontab
            self.debug('Removing autobalance timer')
            self.console.cron - self._cronTab_autobalance
        if self._autobalance:
            self.debug('Restarting autobalance timer')
            #self.console.say('Restarting autobalance timer')
            (m, s) = self.autobalance_time()
            self._cronTab_autobalance = b3.cron.OneTimeCronTab(self.run_autobalance, second=s, minute=m)
            self.console.cron + self._cronTab_autobalance

    @staticmethod
    def count_teams(clients):
        """
        Return the number of players in each team
        """
        team1 = 0
        team2 = 0
        for cl in clients:
            if cl.teamId == 1:
                team1 += 1
            if cl.teamId == 2:
                team2 += 1
        return team1, team2

    def set_swap_threshold(self, count):
        self._team_swap_threshold_current = self._team_swap_threshold
        if self._team_swap_threshold_prop:
            if count > 20:
                self._team_swap_threshold_current +=1
            if count > 40:
                self._team_swap_threshold_current +=1

    def client_connect(self, client):
        """
        Add client to joined order list
        """
        self._joined_order.append(client.name)

    def client_disconnect(self, client, client_name):
        """
        Remove client from joined order list
        """
        self.debug('Trying to remove %s' % client_name)
        self.debug(self._joined_order)
        try:
            self._joined_order.remove(client_name)
        except ValueError, err:
            self.debug(err)
            self.warning('Client %s was not in joined list' % client_name)

    def current_winningTeamID(self):
        """
        Return winning TeamID from current game
        """
        scoretable = {}
        # update values in self.console.game.serverinfo from current game
        self.console.getServerInfo()
        # if we have values in teamXscore, then put they our dict
        if self.console.game.serverinfo['team1score']:
            scoretable['1'] = float(self.console.game.serverinfo['team1score'])
        if self.console.game.serverinfo['team2score']:
            scoretable['2'] = float(self.console.game.serverinfo['team2score'])
        if self.console.game.serverinfo['team3score']:
            scoretable['3'] = float(self.console.game.serverinfo['team3score'])
        if self.console.game.serverinfo['team4score']:
            scoretable['4'] = float(self.console.game.serverinfo['team4score'])

        return max(scoretable, key=scoretable.get)

    def findClientSilent(self, client_id):
        matches = self.console.clients.getByMagic(client_id)
        if matches:
            if len(matches) > 1:
                return [x.name for x in matches]
            else:
                return matches[0].name
        else:
            return None

    def lookupClientByExactName(self, name):
        try:
            sclient = self.console.storage.getClientsMatching({ 'name' : name })
            if not sclient:
                return []
            else:
                clients = []
                for c in sclient:
                    c.clients = self.console.clients
                    c.console = self.console
                    c.exactName = c.name
                    clients.append(c)
                return clients
        except Exception, err:
            self.error(err)
            return []