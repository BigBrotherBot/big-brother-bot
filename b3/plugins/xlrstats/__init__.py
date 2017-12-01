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

__author__ = 'xlr8or & ttlogic'
__version__ = '3.0.0-beta.17'

import b3
import b3.events
import b3.plugin
import b3.cron
import b3.timezones
import datetime
import time
import os
import re
import thread
import threading
import urllib2

from b3.functions import escape
from b3.functions import getCmd
from b3.functions import right_cut
from ConfigParser import NoOptionError

KILLER = "killer"
VICTIM = "victim"
ASSISTER = "assister"

########################################################################################################################
#                                                                                                                      #
#   MAIN PLUGIN XLRSTATS - HANDLES ALL CORE STATISTICS FUNCTIONALITY                                                   #
#                                                                                                                      #
########################################################################################################################

class XlrstatsPlugin(b3.plugin.Plugin):

    _world_clientid = None
    _ffa = ['dm', 'ffa', 'syc-ffa']

    # on damage_able_games we'll only count assists when damage is 50 points or more
    _damage_able_games = ['cod4', 'cod5', 'cod6', 'cod7', 'cod8']
    _damage_ability = False

    hide_bots = True                    # set client.hide to True so bots are hidden from the stats
    exclude_bots = True                 # kills and damage to and from bots do not affect playerskill

    # history management
    _cronTabWeek = None
    _cronTabMonth = None
    _cronTabKillBonus = None

    # webfront variables
    webfront_version = 2                 # maintain backward compatibility
    webfront_url = ''
    webfront_config_nr = 0

    _minKills = 100
    _minRounds = 10
    _maxDays = 14

    # config variables
    defaultskill = 1000
    minlevel = 0
    onemaponly = False

    Kfactor_high = 16
    Kfactor_low = 4
    Kswitch_confrontations = 50

    steepness = 600
    suicide_penalty_percent = 0.05
    tk_penalty_percent = 0.1
    action_bonus = 1.0
    kill_bonus = 1.5
    assist_bonus = 0.5
    assist_timespan = 2                 # on non damage based games: damage before death timespan
    damage_assist_release = 10          # on damage based games: release the assist (will overwrite self.assist_timespan on startup)
    prematch_maxtime = 70
    announce = False                    # announces points gained/lost to players after confrontations
    keep_history = True
    keep_time = True
    min_players = 3                     # minimum number of players to collect stats
    _xlrstats_active = False            # parsing events based on min_players?
    _current_nr_players = 0             # current number of players present
    silent = False                      # Disables the announcement when collecting stats = stealth mode
    provisional_ranking = True          # First Kswitch_confrontations will not alter opponents stats (unless both are under the limit)
    auto_correct = True                 # Auto correct skill points every two hours to maintain a healthy pool
    _auto_correct_ignore_days = 60      # How many days before ignoring a players skill in the auto-correct calculation
    auto_purge = False                  # Purge players and associated data automatically (cannot be undone!)
    _purge_player_days = 365            # Number of days after which players will be auto-purged

    # keep some private map data to detect prematches and restarts
    _last_map = None
    _last_roundtime = None

    # names for various stats tables
    playerstats_table = 'xlr_playerstats'
    weaponstats_table = 'xlr_weaponstats'
    weaponusage_table = 'xlr_weaponusage'
    bodyparts_table = 'xlr_bodyparts'
    playerbody_table = 'xlr_playerbody'
    opponents_table = 'xlr_opponents'
    mapstats_table = 'xlr_mapstats'
    playermaps_table = 'xlr_playermaps'
    actionstats_table = 'xlr_actionstats'
    playeractions_table = 'xlr_playeractions'
    clients_table = 'clients'
    penalties_table = 'penalties'
    # default tablenames for the history subplugin
    history_monthly_table = 'xlr_history_monthly'
    history_weekly_table = 'xlr_history_weekly'
    # default table name for the ctime subplugin
    ctime_table = 'ctime'
    # default tablenames for the Battlestats subplugin
    # battlestats_table = 'xlr_battlestats'
    # playerbattles_table = 'xlr_playerbattles'

    _defaultTableNames = True
    _default_messages = {
        'cmd_xlrstats': '^3XLR Stats: ^7$name ^7: K ^2$kills ^7D ^3$deaths ^7TK ^1$teamkills ^7Ratio ^5$ratio ^7Skill ^3$skill',
        'cmd_xlrtopstats': '^3# $number: ^7$name ^7: Skill ^3$skill ^7Ratio ^5$ratio ^7Kills: ^2$kills',
    }

    ####################################################################################################################
    #                                                                                                                  #
    #    STARTUP                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def __init__(self, console, config=None):
        """
        Object constructor.
        :param console: The console instance
        :param config: The plugin configuration
        """
        self._adminPlugin = None            # admin plugin object reference
        self._xlrstatsHistoryPlugin = None
        self._ctimePlugin = None
        self._xlrstatstables = []           # will contain a list of the xlrstats database tables
        self._cronTabCorrectStats = None
        self.query = None                   # shortcut to the storage.query function
        b3.plugin.Plugin.__init__(self, console, config)

    def onStartup(self):
        """
        Initialize plugin.
        """
        # get the admin plugin so we can register commands
        self._adminPlugin = self.console.getPlugin('admin')

        # build database schema if needed
        self.build_database_schema()

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

        # define a shortcut to the storage.query function
        self.query = self.console.storage.query

        # initialize tablenames
        PlayerStats._table = self.playerstats_table
        WeaponStats._table = self.weaponstats_table
        WeaponUsage._table = self.weaponusage_table
        Bodyparts._table = self.bodyparts_table
        PlayerBody._table = self.playerbody_table
        Opponents._table = self.opponents_table
        MapStats._table = self.mapstats_table
        PlayerMaps._table = self.playermaps_table
        ActionStats._table = self.actionstats_table
        PlayerActions._table = self.playeractions_table

        # register the events we're interested in.
        self.registerEvent('EVT_CLIENT_JOIN', self.onJoin)
        self.registerEvent('EVT_CLIENT_KILL', self.onKill)
        self.registerEvent('EVT_CLIENT_KILL_TEAM', self.onTeamKill)
        self.registerEvent('EVT_CLIENT_SUICIDE', self.onSuicide)
        self.registerEvent('EVT_GAME_ROUND_START', self.onRoundStart)
        self.registerEvent('EVT_CLIENT_ACTION', self.onAction)       # for game-events/actions
        self.registerEvent('EVT_CLIENT_DAMAGE', self.onDamage)       # for assist recognition

        # get the Client.id for the bot itself (guid: WORLD or Server(bfbc2/moh/hf))
        sclient = self.console.clients.getByGUID("WORLD")
        if sclient is None:
            sclient = self.console.clients.getByGUID("Server")

        if sclient is not None:
            self._world_clientid = sclient.id
            self.debug('got client id for B3: %s; %s' % (self._world_clientid, sclient.name))
            # make sure its hidden in the webfront
            player = self.get_PlayerStats(sclient)
            if player:
                player.hide = 1
                self.save_Stat(player)

        # determine the ability to work with damage based assists
        if self.console.gameName in self._damage_able_games:
            self.assist_timespan = self.damage_assist_release
            self._damage_ability = True

        # investigate if we can and want to keep a history
        self._xlrstatstables = [self.playerstats_table, self.weaponstats_table, self.weaponusage_table,
                                self.bodyparts_table, self.playerbody_table, self.opponents_table, self.mapstats_table,
                                self.playermaps_table, self.actionstats_table, self.playeractions_table]

        if self.keep_history:
            self._xlrstatstables = [self.playerstats_table, self.weaponstats_table, self.weaponusage_table,
                                    self.bodyparts_table, self.playerbody_table, self.opponents_table,
                                    self.mapstats_table, self.playermaps_table, self.actionstats_table,
                                    self.playeractions_table, self.history_monthly_table, self.history_weekly_table]

            self.verbose('starting subplugin XLRstats History')
            self._xlrstatsHistoryPlugin = XlrstatshistoryPlugin(self.console, self.history_weekly_table,
                                                                self.history_monthly_table, self.playerstats_table)
            self._xlrstatsHistoryPlugin.onStartup()


        # let's try and get some variables from our webfront installation
        if self.webfront_url and self.webfront_url != '':
            self.debug('webfront set to: %s' % self.webfront_url)
            thread1 = threading.Thread(target=self.getWebsiteVariables)
            thread1.start()
        else:
            self.debug('no webfront url available: using default')

        # Analyze the ELO pool of points
        self.correctStats()
        self._cronTabCorrectStats = b3.cron.PluginCronTab(self, self.correctStats, 0, '0', '*/2')
        self.console.cron + self._cronTabCorrectStats

        self.purgePlayers()

        # set proper kill_bonus and crontab
        self.calculateKillBonus()
        self._cronTabKillBonus = b3.cron.PluginCronTab(self, self.calculateKillBonus, 0, '*/10')
        self.console.cron + self._cronTabKillBonus

        # start the ctime subplugin
        if self.keep_time:
            self._ctimePlugin = CtimePlugin(self.console, self.ctime_table)
            self._ctimePlugin.onStartup()

        #start the xlrstats controller
        #p = XlrstatscontrollerPlugin(self.console, self.min_players, self.silent)
        #p.onStartup()

        # get the map we're in, in case this is a new map and we need to create a db record for it.
        mapstats = self.get_MapStats(self.console.game.mapName)
        if mapstats:
            self.verbose('map %s ready' % mapstats.name)

        # check number of online players (if available)
        self.checkMinPlayers()

        self.console.say('XLRstats v%s by %s started' % (__version__, __author__))
        # end startup sequence

    def onLoadConfig(self):
        """
        Load plugin configuration.
        """
        def validate_server_nr(x):
            """validate the server number and it it's wrong will leave a message in the log file"""
            if x < 0:
                raise ValueError("servernumber cannot be lower than 0")
            return x

        self.provisional_ranking = self.getSetting('settings', 'provisional_ranking', b3.BOOL, self.provisional_ranking)
        self.auto_correct = self.getSetting('settings', 'auto_correct', b3.BOOL, self.auto_correct)
        self.auto_purge = self.getSetting('settings', 'auto_purge', b3.BOOL, self.auto_purge)
        self.silent = self.getSetting('settings', 'silent', b3.BOOL, self.silent)
        self.hide_bots = self.getSetting('settings', 'hide_bots', b3.BOOL, self.hide_bots)
        self.exclude_bots = self.getSetting('settings', 'exclude_bots', b3.BOOL, self.exclude_bots)
        self.min_players = self.getSetting('settings', 'minplayers', b3.INT, self.min_players, lambda x: int(max(x, 0)))
        self.webfront_version = self.getSetting('settings', 'webfrontversion', b3.STR, self.webfront_version)
        self.webfront_url = self.getSetting('settings', 'webfronturl', b3.STR, self.webfront_url)
        self.webfront_config_nr = self.getSetting('settings', 'servernumber', b3.INT, self.webfront_config_nr, validate_server_nr)
        self.keep_history = self.getSetting('settings', 'keep_history', b3.BOOL, self.keep_history)
        self.onemaponly = self.getSetting('settings', 'onemaponly', b3.BOOL, self.onemaponly)
        self.minlevel = self.getSetting('settings', 'minlevel', b3.LEVEL, self.minlevel, lambda x: int(max(x, 0)))
        self.defaultskill = self.getSetting('settings', 'defaultskill', b3.INT, self.defaultskill)
        self.Kfactor_high = self.getSetting('settings', 'Kfactor_high', b3.INT, self.Kfactor_high)
        self.Kfactor_low = self.getSetting('settings', 'Kfactor_low', b3.INT, self.Kfactor_low)
        self.Kswitch_confrontations = self.getSetting('settings', 'Kswitch_confrontations', b3.INT, self.Kswitch_confrontations)
        self.steepness = self.getSetting('settings', 'steepness', b3.INT, self.steepness)
        self.suicide_penalty_percent = self.getSetting('settings', 'suicide_penalty_percent', b3.FLOAT, self.suicide_penalty_percent)
        self.tk_penalty_percent = self.getSetting('settings', 'tk_penalty_percent', b3.FLOAT, self.tk_penalty_percent)
        self.assist_timespan = self.getSetting('settings', 'assist_timespan', b3.INT, self.assist_timespan)
        self.damage_assist_release = self.getSetting('settings', 'damage_assist_release', b3.INT, self.damage_assist_release)
        self.prematch_maxtime = self.getSetting('settings', 'prematch_maxtime', b3.INT, self.prematch_maxtime)
        self.announce = self.getSetting('settings', 'announce', b3.BOOL, self.announce)
        self.keep_time = self.getSetting('settings', 'keep_time', b3.BOOL, self.keep_time)

        # load custom table names
        self.load_config_tables()

    def build_database_schema(self):
        """
        Build the database schema checking if all the needed tables have been properly created.
        If not, it will attempt to create them automatically
        """
        sql_main = os.path.join(b3.getAbsolutePath('@b3/plugins/xlrstats/sql'), self.console.storage.protocol)
        xlr_tables = {x: getattr(self, x) for x in dir(self) if x.endswith('_table')}
        current_tables = self.console.storage.getTables()

        for k, v in xlr_tables.items():
            if v not in current_tables:
                sql_name = right_cut(k, '_table') + '.sql'
                sql_path = os.path.join(sql_main, sql_name)
                if os.path.isfile(sql_path):
                    try:
                        with open(sql_path, 'r') as sql_file:
                            query = self.console.storage.getQueriesFromFile(sql_file)[0]
                        self.console.storage.query(query % v)
                    except Exception, e:
                        self.error("could not create schema for database table '%s': %s", v, e)
                    else:
                        self.info('created database table: %s', v)
                else:
                    self.error("could not create schema for database table '%s': missing SQL script '%s'", v, sql_path)

        # EXECUTE SCHEMA UPDATE
        update_schema = {
            'mysql': {
                'history_monthly-update-3.0.0.sql': self.history_monthly_table,
                'history_weekly-update-3.0.0.sql': self.history_weekly_table,
                'playerstats-update-3.0.0.sql': self.playerstats_table,
            },
            'sqlite': {
                'playerstats-update-3.0.0.sql': self.playerstats_table,
            },
            'postgresql': {
                # NO UPDATE NEEDED FOR THE MOMENT
            }
        }

        for k, v in update_schema[self.console.storage.protocol].items():
            sql_path = os.path.join(sql_main, k)
            if os.path.isfile(sql_path):
                with open(sql_path, 'r') as sql_file:
                    # execute statements separately since we need to substitute the table name
                    for q in self.console.storage.getQueriesFromFile(sql_file):
                        try:
                            self.console.storage.query(q % v)
                        except Exception:
                            # DONT LOG HERE!!! (schema might have already changed so executing the update query will
                            # raise an exception without actually changing the database table structure (which is OK!)
                            pass

    def load_config_tables(self):
        """
        Load config section 'tables'
        """
        def load_conf(property_to_set, setting_option):
            assert hasattr(self, property_to_set)
            try:
                table_name = self.config.get('tables', setting_option)
                if not table_name:
                    raise ValueError("invalid table name for %s: %r" % (setting_option, table_name))
                setattr(self, property_to_set, table_name)
                self._defaultTableNames = False
            except NoOptionError, err:
                self.debug(err)
            except Exception, err:
                self.error(err)
            self.info('using value "%s" for tables::%s' % (property_to_set, setting_option))

        load_conf('playerstats_table', 'playerstats')
        load_conf('actionstats_table', 'actionstats')
        load_conf('weaponstats_table', 'weaponstats')
        load_conf('weaponusage_table', 'weaponusage')
        load_conf('bodyparts_table', 'bodyparts')
        load_conf('playerbody_table', 'playerbody')
        load_conf('opponents_table', 'opponents')
        load_conf('mapstats_table', 'mapstats')
        load_conf('playermaps_table', 'playermaps')
        load_conf('playeractions_table', 'playeractions')
        load_conf('history_monthly_table', 'history_monthly')
        load_conf('history_weekly_table', 'history_weekly')
        load_conf('ctime_table', 'ctime')

    ####################################################################################################################
    #                                                                                                                  #
    #    EVENTS                                                                                                        #
    #                                                                                                                  #
    ####################################################################################################################

    def onJoin(self, event):
        """
        Handle EVT_CLIENT_JOIN
        """
        self.checkMinPlayers()
        self.join(event.client)

    def onKill(self, event):
        """
        Handle EVT_CLIENT_KILL
        """
        if self._xlrstats_active:
            self.kill(event.client, event.target, event.data)

    def onTeamKill(self, event):
        """
        Handle EVT_CLIENT_KILL_TEAM
        """
        if self._xlrstats_active:
            if self.console.game.gameType in self._ffa:
                self.kill(event.client, event.target, event.data)
            else:
                self.teamkill(event.client, event.target, event.data)

    def onDamage(self, event):
        """
        Handle EVT_CLIENT_DAMAGE
        """
        if self._xlrstats_active:
            self.damage(event.client, event.target, event.data)

    def onSuicide(self, event):
        """
        Handle EVT_CLIENT_SUICIDE
        """
        if self._xlrstats_active:
            self.suicide(event.client, event.target, event.data)

    def onRoundStart(self, _):
        """
        Handle EVT_GAME_ROUND_START
        """
        # disable k/d counting if minimum players are not met
        self.checkMinPlayers(_roundstart=True)
        self.roundstart()

    def onAction(self, event):
        """
        Handle EVT_CLIENT_ACTION
        """
        if self._xlrstats_active:
            self.action(event.client, event.data)

    ####################################################################################################################
    #                                                                                                                  #
    #    OTHER METHODS                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def getWebsiteVariables(self):
        """
        Thread that polls for XLRstats webfront variables
        """
        if self.webfront_version == 2:
            req = str(self.webfront_url.rstrip('/')) + '/?config=' + str(self.webfront_config_nr) + '&func=pluginreq'
        else:
            req = str(self.webfront_url.rstrip('/')) + '/' + str(self.webfront_config_nr) + '/pluginreq/index'
        try:
            f = urllib2.urlopen(req)
            res = f.readline().split(',')
            # Our webfront will present us 3 values ie.: 200,20,30 -> minKills,minRounds,maxDays
            if len(res) == 3:
                # Force the collected strings to their final type. If an error occurs they will fail the try statement.
                self._minKills = int(res[0])
                self._minRounds = int(res[1])
                self._maxDays = int(res[2])
                self.debug('successfuly retrieved webfront variables: minkills: %i, minrounds: %i, maxdays: %i' % (
                    self._minKills, self._minRounds, self._maxDays))
        except Exception:
            self.debug('couldn\'t retrieve webfront variables: using defaults')

    def checkMinPlayers(self, _roundstart=False):
        """
        Checks if minimum amount of players are present.
        If minimum amount of players is reached will enable stats collecting
        and if not it disables stats counting on next roundstart
        """
        self._current_nr_players = len(self.console.clients.getList())
        self.debug('checking number of players online: minimum = %s, current = %s', self.min_players, self._current_nr_players)
        if self._current_nr_players < self.min_players and self._xlrstats_active and _roundstart:
            self.info('XLRstats disabled: not enough players online')
            if not self.silent:
                self.console.say('XLRstats disabled: not enough players online!')
            self._xlrstats_active = False
        elif self._current_nr_players >= self.min_players and not self._xlrstats_active:
            self.info('XLRstats enabled: collecting Stats')
            if not self.silent:
                self.console.say('XLRstats enabled: now collecting stats!')
            self._xlrstats_active = True
        else:
            if self._xlrstats_active:
                _status = 'enabled'
            else:
                _status = 'disabled'
            self.debug('nothing to do at the moment: XLRstats is already %s', _status)

    def win_prob(self, player_skill, opponent_skill):
        return 1 / (10 ** ((opponent_skill - player_skill) / self.steepness) + 1)

    def get_PlayerStats(self, client=None):
        """
        Retrieves an existing stats record for given client or makes a new one IFF client's level is high enough
        Otherwise (also on error), it returns None.
        """
        if client is None:
            client_id = self._world_clientid
        else:
            client_id = client.id

        q = """SELECT * from %s WHERE client_id = %s LIMIT 1""" % (self.playerstats_table, client_id)
        cursor = self.query(q)
        if cursor and not cursor.EOF:
            r = cursor.getRow()
            s = PlayerStats()
            s.id = r['id']
            s.client_id = r['client_id']
            s.kills = r['kills']
            if (s.kills + s.deaths) > self.Kswitch_confrontations:
                s.Kfactor = self.Kfactor_low
            else:
                s.Kfactor = self.Kfactor_high
            s.deaths = r['deaths']
            s.teamkills = r['teamkills']
            s.teamdeaths = r['teamdeaths']
            s.suicides = r['suicides']
            s.ratio = r['ratio']
            s.skill = r['skill']
            s.assists = r['assists']
            s.assistskill = r['assistskill']
            s.curstreak = r['curstreak']
            s.winstreak = r['winstreak']
            s.losestreak = r['losestreak']
            s.rounds = r['rounds']
            s.hide = r['hide']
            s.fixed_name = r['fixed_name']
            s.id_token = r['id_token']
            return s
        elif (client is None) or (client.maxLevel >= self.minlevel):
            s = PlayerStats()
            s._new = True
            s.skill = self.defaultskill
            s.Kfactor = self.Kfactor_high
            s.client_id = client_id
            return s
        else:
            return None

    def get_PlayerAnon(self):
        return self.get_PlayerStats(None)

    def get_WeaponStats(self, name):
        s = WeaponStats()
        q = """SELECT * from %s WHERE name = '%s' LIMIT 1""" % (self.weaponstats_table, name)
        cursor = self.query(q)
        if cursor and not cursor.EOF:
            r = cursor.getRow()
            s.id = r['id']
            s.name = r['name']
            s.kills = r['kills']
            s.suicides = r['suicides']
            s.teamkills = r['teamkills']
            return s
        else:
            s._new = True
            s.name = name
            return s

    def get_Bodypart(self, name):
        s = Bodyparts()
        q = """SELECT * from %s WHERE name = '%s' LIMIT 1""" % (self.bodyparts_table, name)
        cursor = self.query(q)
        if cursor and not cursor.EOF:
            r = cursor.getRow()
            s.id = r['id']
            s.name = r['name']
            s.kills = r['kills']
            s.suicides = r['suicides']
            s.teamkills = r['teamkills']
            return s
        else:
            s._new = True
            s.name = name
            return s

    def get_MapStats(self, name):
        assert name is not None
        s = MapStats()
        q = """SELECT * from %s WHERE name = '%s' LIMIT 1""" % (self.mapstats_table, name)
        cursor = self.query(q)
        if cursor and not cursor.EOF:
            r = cursor.getRow()
            s.id = r['id']
            s.name = r['name']
            s.kills = r['kills']
            s.suicides = r['suicides']
            s.teamkills = r['teamkills']
            s.rounds = r['rounds']
            return s
        else:
            s._new = True
            s.name = name
            return s

    def get_WeaponUsage(self, weaponid, playerid):
        s = WeaponUsage()
        q = """SELECT * from %s WHERE weapon_id = %s AND player_id = %s LIMIT 1""" % (self.weaponusage_table, weaponid, playerid)
        cursor = self.query(q)
        if cursor and not cursor.EOF:
            r = cursor.getRow()
            s.id = r['id']
            s.player_id = r['player_id']
            s.weapon_id = r['weapon_id']
            s.kills = r['kills']
            s.deaths = r['deaths']
            s.suicides = r['suicides']
            s.teamkills = r['teamkills']
            s.teamdeaths = r['teamdeaths']
            return s
        else:
            s._new = True
            s.player_id = playerid
            s.weapon_id = weaponid
            return s

    def get_Opponent(self, killerid, targetid):
        s = Opponents()
        q = """SELECT * from %s WHERE killer_id = %s AND target_id = %s LIMIT 1""" % (self.opponents_table, killerid, targetid)
        cursor = self.query(q)
        if cursor and not cursor.EOF:
            r = cursor.getRow()
            s.id = r['id']
            s.killer_id = r['killer_id']
            s.target_id = r['target_id']
            s.kills = r['kills']
            s.retals = r['retals']
            return s
        else:
            s._new = True
            s.killer_id = killerid
            s.target_id = targetid
            return s

    def get_PlayerBody(self, playerid, bodypartid):
        s = PlayerBody()
        q = """SELECT * from %s WHERE bodypart_id = %s AND player_id = %s LIMIT 1""" % (self.playerbody_table, bodypartid, playerid)
        cursor = self.query(q)
        if cursor and not cursor.EOF:
            r = cursor.getRow()
            s.id = r['id']
            s.player_id = r['player_id']
            s.bodypart_id = r['bodypart_id']
            s.kills = r['kills']
            s.deaths = r['deaths']
            s.suicides = r['suicides']
            s.teamkills = r['teamkills']
            s.teamdeaths = r['teamdeaths']
            return s
        else:
            s._new = True
            s.player_id = playerid
            s.bodypart_id = bodypartid
            return s

    def get_PlayerMaps(self, playerid, mapid):
        if not mapid:
            self.info('map not recognized: trying to initialise map...')
            mapstats = self.get_MapStats(self.console.game.mapName)
            if mapstats:
                if hasattr(mapstats, '_new'):
                    self.save_Stat(mapstats)
                self.verbose('map %s successfully initialised', mapstats.name)
                mapid = mapstats.id
                assert mapid is not None, "failed to get mapid from database for %s" % self.console.game.mapName
            else:
                return None

        s = PlayerMaps()
        q = """SELECT * from %s WHERE map_id = %s AND player_id = %s LIMIT 1""" % (self.playermaps_table, mapid, playerid)
        cursor = self.query(q)
        if cursor and not cursor.EOF:
            r = cursor.getRow()
            s.id = r['id']
            s.player_id = r['player_id']
            s.map_id = r['map_id']
            s.kills = r['kills']
            s.deaths = r['deaths']
            s.suicides = r['suicides']
            s.teamkills = r['teamkills']
            s.teamdeaths = r['teamdeaths']
            s.rounds = r['rounds']
            return s
        else:
            s._new = True
            s.player_id = playerid
            s.map_id = mapid
            return s

    def get_ActionStats(self, name):
        s = ActionStats()
        q = """SELECT * from %s WHERE name = '%s' LIMIT 1""" % (self.actionstats_table, name)
        cursor = self.query(q)
        if cursor and not cursor.EOF:
            r = cursor.getRow()
            s.id = r['id']
            s.name = r['name']
            s.count = r['count']
            return s
        else:
            s._new = True
            s.name = name
            return s

    def get_PlayerActions(self, playerid, actionid):
        s = PlayerActions()
        q = """SELECT * from %s WHERE action_id = %s AND player_id = %s LIMIT 1""" % (self.playeractions_table, actionid, playerid)
        cursor = self.query(q)
        if cursor and not cursor.EOF:
            r = cursor.getRow()
            s.id = r['id']
            s.player_id = r['player_id']
            s.action_id = r['action_id']
            s.count = r['count']
            return s
        else:
            s._new = True
            s.player_id = playerid
            s.action_id = actionid
            return s

    def save_Stat(self, stat):
        #self.verbose('*----> XLRstats: saving statistics for %s' % type(stat))
        #self.verbose('*----> Contents: %s' %stat)
        if hasattr(stat, '_new'):
            q = stat._insertquery()
            #self.debug('Inserting using: %r', q)
            cursor = self.query(q)
            if cursor.rowcount > 0:
                stat.id = cursor.lastrowid
                delattr(stat, '_new')
        else:
            q = stat._updatequery()
            #self.debug('Updating using: %r', q)
            self.query(q)

        #print 'save_Stat: q= ', q
        #self.query(q)
        # we could not really do anything with error checking on saving.
        # If it fails, that's just bad luck.
        return

    def check_Assists(self, client, target, data, etype=None):
        # determine eventual assists // an assist only counts if damage was done within # secs. before death
        # it will also punish teammates that have a 'negative' assist!
        _count = 0 # number of assists to return
        _sum = 0   # sum of assistskill returned
        _vsum = 0  # sum of victims skill deduction returned
        self.verbose('----> XLRstats: %s killed %s (%s), checking for assists', client.name, target.name, etype)

        try:
            ainfo = target._attackers
        except:
            target._attackers = {}
            ainfo = target._attackers

        for k, v in ainfo.iteritems():
            if k == client.cid:
                # don't award the killer for the assist aswell
                continue
            elif time.time() - v < self.assist_timespan:
                assister = self.console.clients.getByCID(k)
                self.verbose('----> XLRstats: assister = %s', assister.name)

                anonymous = None

                victimstats = self.get_PlayerStats(target)
                assiststats = self.get_PlayerStats(assister)

                # if both should be anonymous, we have no work to do
                if (assiststats is None) and (victimstats is None):
                    self.verbose('----> XLRstats: check_Assists: %s & %s both anonymous, continuing', assister.name, target.name)
                    continue

                if victimstats is None:
                    anonymous = VICTIM
                    victimstats = self.get_PlayerAnon()
                    if victimstats is None:
                        continue

                if assiststats is None:
                    anonymous = ASSISTER
                    assiststats = self.get_PlayerAnon()
                    if assiststats is None:
                        continue

                # calculate the win probability for the assister and victim
                assist_prob = self.win_prob(assiststats.skill, victimstats.skill)
                # performance patch provided by IzNoGod: ELO states that assist_prob + victim_prob = 1
                #victim_prob = self.win_prob(victimstats.skill, assiststats.skill)
                victim_prob = 1 - assist_prob

                self.verbose('----> XLRstats: win probability for %s: %s', assister.name, assist_prob)
                self.verbose('----> XLRstats: win probability for %s: %s', target.name, victim_prob)

                # get applicable weapon replacement
                actualweapon = data[1]
                for r in data:
                    try:
                        actualweapon = self.config.get('replacements', r)
                    except:
                        pass

                # get applicable weapon multiplier
                try:
                    weapon_factor = self.config.getfloat('weapons', actualweapon)
                except:
                    weapon_factor = 1.0

                # calculate new skill for the assister
                if anonymous != ASSISTER:
                    oldskill = assiststats.skill
                    if ( target.team == assister.team ) and not ( self.console.game.gameType in self._ffa ):
                        #assister is a teammate and needs skill and assists reduced
                        _assistbonus = self.assist_bonus * assiststats.Kfactor * weapon_factor * (0 - assist_prob)
                        assiststats.skill = float(assiststats.skill) + _assistbonus
                        assiststats.assistskill = float(assiststats.assistskill) + _assistbonus
                        assiststats.assists -= 1 # negative assist
                        self.verbose('----> XLRstats: assistpunishment deducted for %s: %s (oldsk: %.3f - '
                                     'newsk: %.3f)', assister.name, assiststats.skill - oldskill, oldskill, assiststats.skill)
                        _count += 1
                        _sum += _assistbonus
                        if self.announce and not assiststats.hide:
                            assister.message('^5XLRstats:^7 Teamdamaged (%s) -> skill: ^1%.3f^7 -> ^2%.1f^7',
                                             target.name, assiststats.skill - oldskill, assiststats.skill)
                    else:
                        # this is a real assist
                        _assistbonus = self.assist_bonus * assiststats.Kfactor * weapon_factor * (1 - assist_prob)
                        assiststats.skill = float(assiststats.skill) + _assistbonus
                        assiststats.assistskill = float(assiststats.assistskill) + _assistbonus
                        assiststats.assists += 1
                        self.verbose('----> XLRstats: assistbonus awarded for %s: %s (oldsk: %.3f - newsk: %.3f)',
                                     assister.name, assiststats.skill - oldskill, oldskill, assiststats.skill)
                        _count += 1
                        _sum += _assistbonus
                        if self.announce and not assiststats.hide:
                            assister.message('^5XLRstats:^7 Assistbonus (%s) -> skill: ^2+%.3f^7 -> ^2%.1f^7',
                                             target.name, assiststats.skill - oldskill, assiststats.skill)
                    self.save_Stat(assiststats)

                    # calculate new skill for the victim
                    oldskill = victimstats.skill
                    if target.team == assister.team and self.console.game.gameType not in self._ffa:
                        # assister was a teammate, this should not affect victims skill.
                        pass
                    else:
                        # this is a real assist
                        _assistdeduction = self.assist_bonus * victimstats.Kfactor * weapon_factor * (0 - victim_prob)
                        victimstats.skill = float(victimstats.skill) + _assistdeduction
                        self.verbose('----> XLRstats: assist skilldeduction for %s: %s (oldsk: %.3f - newsk: %.3f)',
                            target.name, victimstats.skill - oldskill, oldskill, victimstats.skill)
                        _vsum += _assistdeduction
                    self.save_Stat(victimstats)

        # end of assist reward function, return the number of assists
        return _count, _sum, _vsum

    def kill(self, client, target, data):
        """
        Handle situations where client killed target.
        """
        if (client is None) or (client.id == self._world_clientid):
            return
        if target is None:
            return
        if data is None:
            return

        # exclude botkills?
        if (client.bot or target.bot) and self.exclude_bots:
            self.verbose('bot involved: do not process!')
            return

        _assists_count, _assists_sum, _victim_sum = self.check_Assists(client, target, data, 'kill')
        _both_provisional = False

        anonymous = None

        killerstats = self.get_PlayerStats(client)
        victimstats = self.get_PlayerStats(target)

        # if both should be anonymous, we have no work to do
        if (killerstats is None) and (victimstats is None):
            return

        if killerstats is None:
            anonymous = KILLER
            killerstats = self.get_PlayerAnon()
            if killerstats is None:
                return
            killerstats.skill = self.defaultskill

        if victimstats is None:
            anonymous = VICTIM
            victimstats = self.get_PlayerAnon()
            if victimstats is None:
                return

        #_killer_confrontations = killerstats.kills + killerstats.deaths
        #_victom_confrontations = victimstats.kills + victimstats.deaths

        # calculate winning probabilities for both players
        killer_prob = self.win_prob(killerstats.skill, victimstats.skill)
        # performance patch provided by IzNoGod: ELO states that killer_prob + victim_prob = 1
        # victim_prob = self.win_prob(victimstats.skill, killerstats.skill)
        victim_prob = 1 - killer_prob

        # get applicable weapon replacement
        actualweapon = data[1]
        for r in data:
            try:
                actualweapon = self.config.get('replacements', r)
            except:
                pass

        # get applicable weapon multiplier
        try:
            weapon_factor = self.config.getfloat('weapons', actualweapon)
        except:
            weapon_factor = 1.0

        # calculate new stats for the killer
        if anonymous != KILLER:
            oldskill = killerstats.skill
            # pure skilladdition for a 100% kill
            _skilladdition = self.kill_bonus * killerstats.Kfactor * weapon_factor * (1 - killer_prob)
            # deduct the assists from the killers skill, but no more than 50%
            if _assists_sum == 0:
                pass
            elif _assists_sum >= ( _skilladdition / 2 ):
                _skilladdition /= 2
                self.verbose('----> XLRstats: killer: assists > 50perc: %.3f - skilladd: %.3f', _assists_sum, _skilladdition)
            else:
                _skilladdition -= _assists_sum
                self.verbose('----> XLRstats: killer: assists < 50perc: %.3f - skilladd: %.3f', _assists_sum, _skilladdition)

            killerstats.skill = float(killerstats.skill) + _skilladdition
            self.verbose('----> XLRstats: killer: oldsk: %.3f - newsk: %.3f', oldskill, killerstats.skill)
            killerstats.kills = int(killerstats.kills) + 1

            if int(killerstats.deaths) != 0:
                killerstats.ratio = float(killerstats.kills) / float(killerstats.deaths)
            else:
                killerstats.ratio = 0.0

            if int(killerstats.curstreak) > 0:
                killerstats.curstreak = int(killerstats.curstreak) + 1
            else:
                killerstats.curstreak = 1

            if int(killerstats.curstreak) > int(killerstats.winstreak):
                killerstats.winstreak = int(killerstats.curstreak)
            else:
                killerstats.winstreak = int(killerstats.winstreak)

            # first check if both players are in provisional ranking state. If true we need to save both players stats.
            if (victimstats.kills + victimstats.deaths) < self.Kswitch_confrontations and \
                    (killerstats.kills + killerstats.deaths) < self.Kswitch_confrontations and \
                        self.provisional_ranking:
                _both_provisional = True
                self.verbose('----> XLRstats: both players in provisional ranking state!')

            # implementation of provisional ranking 23-2-2014 MWe:
            # we use the first Kswitch_confrontations to determine the victims skill,
            # we don't adjust the killers skill just yet, unless the victim is anonymous (not participating in xlrstats)
            if _both_provisional or (victimstats.kills + victimstats.deaths) > self.Kswitch_confrontations or \
                    not self.provisional_ranking or anonymous == VICTIM:
                if self.announce and not killerstats.hide:
                    client.message('^5XLRstats:^7 Killed %s -> skill: ^2+%.2f^7 -> ^2%.2f^7',
                                   target.name, (killerstats.skill - oldskill), killerstats.skill)
                self.save_Stat(killerstats)

        # calculate new stats for the victim
        if anonymous != VICTIM:
            oldskill = victimstats.skill

            # pure skilldeduction for a 100% kill
            _skilldeduction = victimstats.Kfactor * weapon_factor * (0 - victim_prob)
            # deduct the assists from the victims skill deduction, but no more than 50%
            if _victim_sum == 0:
                pass
            elif _victim_sum <= ( _skilldeduction / 2 ): #carefull, negative numbers here
                _skilldeduction /= 2
                self.verbose('----> XLRstats: victim: assists > 50perc: %.3f - skilldeduct: %.3f', _victim_sum, _skilldeduction)
            else:
                _skilldeduction -= _victim_sum
                self.verbose('----> XLRstats: victim: assists < 50perc: %.3f - skilldeduct: %.3f', _victim_sum, _skilldeduction)

            victimstats.skill = float(victimstats.skill) + _skilldeduction
            self.verbose('----> XLRstats: victim: oldsk: %.3f - newsk: %.3f', oldskill, victimstats.skill)
            victimstats.deaths = int(victimstats.deaths) + 1

            victimstats.ratio = float(victimstats.kills) / float(victimstats.deaths)

            if int(victimstats.curstreak) < 0:
                victimstats.curstreak = int(victimstats.curstreak) - 1
            else:
                victimstats.curstreak = -1

            if victimstats.curstreak < int(victimstats.losestreak):
                victimstats.losestreak = victimstats.curstreak
            else:
                victimstats.losestreak = int(victimstats.losestreak)

            # first check if both players are in provisional ranking state.
            # if true we need to save both players stats.
            if (victimstats.kills + victimstats.deaths) < self.Kswitch_confrontations and \
                (killerstats.kills + killerstats.deaths) < self.Kswitch_confrontations and self.provisional_ranking:
                _both_provisional = True
                self.verbose('----> XLRstats: both players in provisional ranking state!')

            # implementation of provisional ranking 23-2-2014 MWe:
            # we use the first Kswitch_confrontations to determine the victims skill,
            # we don't adjust the victims skill just yet, unless the killer is anonymous (not participating in xlrstats)
            if _both_provisional or (killerstats.kills + killerstats.deaths) > self.Kswitch_confrontations or \
                not self.provisional_ranking or anonymous == KILLER:
                if self.announce and not victimstats.hide:
                    target.message('^5XLRstats:^7 Killed by %s -> skill: ^1%.2f^7 -> ^2%.2f^7',
                                   client.name, (victimstats.skill - oldskill), victimstats.skill)
                self.save_Stat(victimstats)

        # make sure the record for anonymous is really created with an insert once
        if anonymous:
            if (anonymous == KILLER) and (hasattr(killerstats, '_new')):
                self.save_Stat(killerstats)
            elif (anonymous == VICTIM) and (hasattr(victimstats, '_new')):
                self.save_Stat(victimstats)

        # adjust the "opponents" table to register who killed who
        opponent = self.get_Opponent(targetid=victimstats.id, killerid=killerstats.id)
        retal = self.get_Opponent(targetid=killerstats.id, killerid=victimstats.id)
        #the above should always succeed, but you never know...
        if opponent and retal:
            opponent.kills += 1
            retal.retals += 1
            self.save_Stat(opponent)
            self.save_Stat(retal)

        # adjust weapon statistics
        weaponstats = self.get_WeaponStats(name=actualweapon)
        if weaponstats:
            weaponstats.kills += 1
            self.save_Stat(weaponstats)

            w_usage_killer = self.get_WeaponUsage(playerid=killerstats.id, weaponid=weaponstats.id)
            w_usage_victim = self.get_WeaponUsage(playerid=victimstats.id, weaponid=weaponstats.id)
            if w_usage_killer and w_usage_victim:
                w_usage_killer.kills += 1
                w_usage_victim.deaths += 1
                self.save_Stat(w_usage_killer)
                self.save_Stat(w_usage_victim)

        # adjust bodypart statistics
        bodypart = self.get_Bodypart(name=data[2])
        if bodypart:
            bodypart.kills += 1
            self.save_Stat(bodypart)

            bp_killer = self.get_PlayerBody(playerid=killerstats.id, bodypartid=bodypart.id)
            bp_victim = self.get_PlayerBody(playerid=victimstats.id, bodypartid=bodypart.id)
            if bp_killer and bp_victim:
                bp_killer.kills += 1
                bp_victim.deaths += 1
                self.save_Stat(bp_killer)
                self.save_Stat(bp_victim)

        # adjust map statistics
        mapstats = self.get_MapStats(self.console.game.mapName)
        if mapstats:
            mapstats.kills += 1
            self.save_Stat(mapstats)

            map_killer = self.get_PlayerMaps(playerid=killerstats.id, mapid=mapstats.id)
            map_victim = self.get_PlayerMaps(playerid=victimstats.id, mapid=mapstats.id)
            if map_killer and map_victim:
                map_killer.kills += 1
                map_victim.deaths += 1
                self.save_Stat(map_killer)
                self.save_Stat(map_victim)

        # end of kill function
        return

    def damage(self, client, target, data):
        """
        Handle situations where client damaged target.
        """
        if client.id == self._world_clientid:
            self.verbose('----> XLRstats: onDamage: WORLD-damage, moving on...')
            return None
        if client.cid == target.cid:
            self.verbose('----> XLRstats: onDamage: self damage: %s damaged %s, continueing', client.name, target.name)
            return None

        # exclude botdamage?
        if (client.bot or target.bot) and self.exclude_bots:
            self.verbose('bot involved: do not process!')
            return None

        # check if game is _damage_able -> 50 points or more damage will award an assist
        if self._damage_ability and data[0] < 50:
            self.verbose('---> XLRstats: not enough damage done to award an assist')
            return

        try:
            target._attackers[client.cid] = time.time()
        except:
            target._attackers = {client.cid: time.time()}

        self.verbose('----> XLRstats: onDamage: attacker added: %s (%s) damaged %s (%s)',
                     client.name, client.cid, target.name, target.cid)
        self.verbose('----> XLRstats: Assistinfo: %s' % target._attackers)

    def suicide(self, client, target, data):
        """
        Handle situations where a client committed suicide.
        """
        if client is None:
            return
        if target is None:
            return
        if data is None:
            return

        self.check_Assists(client, target, data, 'suicide')

        playerstats = self.get_PlayerStats(client)

        if playerstats is None:
            # anonymous player. We're not interested :)
            return

        playerstats.suicides += 1
        if playerstats.curstreak < 0:
            playerstats.curstreak -= 1
        else:
            playerstats.curstreak = -1
        if playerstats.curstreak < playerstats.losestreak:
            playerstats.losestreak = playerstats.curstreak

        oldskill = playerstats.skill
        playerstats.skill = (1 - (self.suicide_penalty_percent / 100.0) ) * float(playerstats.skill)
        if self.announce and not playerstats.hide:
            client.message('^5XLRstats:^7 Suicide -> skill: ^1%.3f^7 -> ^2%.1f^7',
                           playerstats.skill - oldskill, playerstats.skill)
        self.save_Stat(playerstats)

        # get applicable weapon replacement
        actualweapon = data[1]
        for r in data:
            try:
                actualweapon = self.config.get('replacements', r)
            except:
                pass

        # update weapon stats
        weaponstats = self.get_WeaponStats(name=actualweapon)
        if weaponstats:
            weaponstats.suicides += 1
            self.save_Stat(weaponstats)

            w_usage = self.get_WeaponUsage(playerid=playerstats.id, weaponid=weaponstats.id)
            if w_usage:
                w_usage.suicides += 1
                self.save_Stat(w_usage)

        # update bodypart stats
        bodypart = self.get_Bodypart(name=data[2])
        if bodypart:
            bodypart.suicides += 1
            self.save_Stat(bodypart)

            bp_player = self.get_PlayerBody(playerid=playerstats.id, bodypartid=bodypart.id)
            if bp_player:
                bp_player.suicides = int(bp_player.suicides) + 1
                self.save_Stat(bp_player)

        # adjust map statistics
        mapstats = self.get_MapStats(self.console.game.mapName)
        if mapstats:
            mapstats.suicides += 1
            self.save_Stat(mapstats)

            map_player = self.get_PlayerMaps(playerid=playerstats.id, mapid=mapstats.id)
            if map_player:
                map_player.suicides += 1
                self.save_Stat(map_player)

        # end of function suicide
        return

    def teamkill(self, client, target, data):
        """
        Handle teamkill situations.
        """
        if client is None:
            return
        if target is None:
            return
        if data is None:
            return

        anonymous = None

        self.check_Assists(client, target, data, 'teamkill')

        killerstats = self.get_PlayerStats(client)
        victimstats = self.get_PlayerStats(target)

        # if both should be anonymous, we have no work to do
        if (killerstats is None) and (victimstats is None):
            return

        if killerstats is None:
            anonymous = KILLER
            killerstats = self.get_PlayerAnon()
            if killerstats is None:
                return
            killerstats.skill = self.defaultskill

        if victimstats is None:
            anonymous = VICTIM
            victimstats = self.get_PlayerAnon()
            if victimstats is None:
                return
            victimstats.skill = self.defaultskill

        if anonymous != KILLER:
            # calculate new stats for the killer
            oldskill = killerstats.skill
            killerstats.skill = (1 - (self.tk_penalty_percent / 100.0) ) * float(killerstats.skill)
            killerstats.teamkills += 1
            killerstats.curstreak = 0   # break off current streak as it is now "impure"
            if self.announce and not killerstats.hide:
                client.message('^5XLRstats:^7 Teamkill -> skill: ^1%.3f^7 -> ^2%.1f^7',
                               killerstats.skill - oldskill, killerstats.skill)
            self.save_Stat(killerstats)

        if anonymous != VICTIM:
            # calculate new stats for the victim
            victimstats.teamdeaths += 1
            self.save_Stat(victimstats)

        # do not register a teamkill in the "opponents" table
        # get applicable weapon replacement
        actualweapon = data[1]
        for r in data:
            try:
                actualweapon = self.config.get('replacements', r)
            except:
                pass

        # adjust weapon statistics
        weaponstats = self.get_WeaponStats(name=actualweapon)
        if weaponstats:
            weaponstats.teamkills += 1
            self.save_Stat(weaponstats)

            w_usage_killer = self.get_WeaponUsage(playerid=killerstats.id, weaponid=weaponstats.id)
            w_usage_victim = self.get_WeaponUsage(playerid=victimstats.id, weaponid=weaponstats.id)
            if w_usage_killer and w_usage_victim:
                w_usage_killer.teamkills += 1
                w_usage_victim.teamdeaths += 1
                self.save_Stat(w_usage_killer)
                self.save_Stat(w_usage_victim)

        # adjust bodypart statistics
        bodypart = self.get_Bodypart(name=data[2])
        if bodypart:
            bodypart.teamkills += 1
            self.save_Stat(bodypart)

            bp_killer = self.get_PlayerBody(playerid=killerstats.id, bodypartid=bodypart.id)
            bp_victim = self.get_PlayerBody(playerid=victimstats.id, bodypartid=bodypart.id)
            if bp_killer and bp_victim:
                bp_killer.teamkills += 1
                bp_victim.teamdeaths += 1
                self.save_Stat(bp_killer)
                self.save_Stat(bp_victim)

        # adjust map statistics
        mapstats = self.get_MapStats(self.console.game.mapName)
        if mapstats:
            mapstats.teamkills += 1
            self.save_Stat(mapstats)

            map_killer = self.get_PlayerMaps(playerid=killerstats.id, mapid=mapstats.id)
            map_victim = self.get_PlayerMaps(playerid=victimstats.id, mapid=mapstats.id)
            if map_killer and map_victim:
                map_killer.teamkills += 1
                map_victim.teamdeaths += 1
                self.save_Stat(map_killer)
                self.save_Stat(map_victim)

        # end of function teamkill
        return

    def join(self, client):
        """
        Handle a client joining the game.
        """
        if client is None:
            return

        player = self.get_PlayerStats(client)
        if player:
            player.rounds = int(player.rounds) + 1
            if client.bot:
                if self.hide_bots:
                    self.verbose('hiding bot')
                    player.hide = True
                else:
                    self.verbose('unhiding bot')
                    player.hide = False
            self.save_Stat(player)

            mapstats = self.get_MapStats(self.console.game.mapName)
            if mapstats:
                playermap = self.get_PlayerMaps(player.id, mapstats.id)
                if playermap:
                    playermap.rounds += 1
                    self.save_Stat(playermap)
        return

    def roundstart(self):
        """
        Handle new round start.
        """
        if self._last_map is None:
            self._last_map = self.console.game.mapName
            # self._last_roundtime = self.console.game._roundTimeStart
        else:
            if not self.onemaponly and ( self._last_map == self.console.game.mapName) and  \
                (self.console.game.roundTime() < self.prematch_maxtime):
                # (self.console.game._roundTimeStart - self._last_roundtime < self.prematch_maxtime)):
                return
            else:
                self._last_map = self.console.game.mapName
                #self._last_roundtime = self.console.game._roundTimeStart

        mapstats = self.get_MapStats(self.console.game.mapName)
        if mapstats:
            mapstats.rounds += 1
            self.save_Stat(mapstats)

        return

    def action(self, client, data):
        """
        Handle client actions.
        """
        # self.verbose('----> XLRstats: entering actionfunc')
        if client is None:
            return

        action = self.get_ActionStats(name=data)
        if action:
            action.count += 1
            #self.verbose('----> XLRstats: Actioncount: %s' %action.count)
            #self.verbose('----> XLRstats: Actionname: %s' %action.name)
            #if hasattr(action, '_new'):
            #    self.verbose('----> XLRstats: insertquery: %s' %action._insertquery())
            #else:
            #    self.verbose('----> XLRstats: updatequery: %s' %action._updatequery())
            self.save_Stat(action)

        # is it an anonymous client, stop here
        playerstats = self.get_PlayerStats(client)
        if playerstats is None:
            #self.verbose('----> XLRstats: Anonymous client')
            return

        playeractions = self.get_PlayerActions(playerid=playerstats.id, actionid=action.id)
        if playeractions:
            playeractions.count += 1
            #self.verbose('----> XLRstats: Players Actioncount: %s' %playeractions.count)
            #if hasattr(playeractions, '_new'):
            #    self.verbose('----> XLRstats: insertquery: %s' %playeractions._insertquery())
            #else:
            #    self.verbose('----> XLRstats: updatequery: %s' %playeractions._updatequery())
            self.save_Stat(playeractions)

        # get applicable action bonus
        try:
            _action_bonus = self.config.getfloat('actions', action.name)
            #self.verbose('----> XLRstats: Found a bonus for %s: %s' %(action.name, action_bonus))
        except:
            _action_bonus = self.action_bonus

        if _action_bonus:
            #self.verbose('----> XLRstats: Old Skill: %s.' %playerstats.skill)
            playerstats.skill += _action_bonus
            #self.verbose('----> XLRstats: New Skill: %s.' %playerstats.skill)
            self.save_Stat(playerstats)

        return

    def updateTableColumns(self):
        self.verbose('checking if we need to update tables for version 2.0.0')
        # v2.0.0 additions to the playerstats table:
        self._addTableColumn('assists', PlayerStats._table, 'MEDIUMINT( 8 ) NOT NULL DEFAULT "0" AFTER `skill`')
        self._addTableColumn('assistskill', PlayerStats._table, 'FLOAT NOT NULL DEFAULT "0" AFTER `assists`')
        # alterations to columns in existing tables:
        self._updateTableColumns()
        return None
        # end of update check

    def _addTableColumn(self, c1, t1, specs):
        try:
            self.query("""SELECT %s FROM %s limit 1;""" % (c1, t1))
        except Exception, e:
            if e[0] == 1054:
                self.console.debug('column does not yet exist: %s' % e)
                self.query("""ALTER TABLE %s ADD %s %s ;""" % (t1, c1, specs))
                self.console.info('created new column `%s` on %s' % (c1, t1))
            else:
                self.console.error('query failed - %s: %s' % (type(e), e))

    def _updateTableColumns(self):
        try:
            # need to update the weapon-identifier columns in these tables for cod7.
            # This game knows over 255 weapons/variations
            self.query("""ALTER TABLE %s
                          CHANGE id  id SMALLINT(5) UNSIGNED NOT NULL AUTO_INCREMENT;""" % WeaponStats._table)
            self.query("""ALTER TABLE %s
                          CHANGE weapon_id weapon_id SMALLINT(5) UNSIGNED NOT NULL DEFAULT  "0";""" % WeaponUsage._table)
        except:
            pass

    def showTables(self, xlrstats=False):
        _tables = []
        for table in self.console.storage.getTables():
            if xlrstats and table not in self._xlrstatstables:
                pass
            else:
                _tables.append(table)
        if xlrstats:
            self.console.verbose('available XLRstats tables in this database: %s', _tables)
        else:
            self.console.verbose('available tables in this database: %s', _tables)
        return _tables

    def optimizeTables(self, t=None):
        if not t:
            t = self.showTables()
        if isinstance(t, basestring):
            _tables = str(t)
        else:
            _tables = ', '.join(t)
        self.debug('optimizing table(s): %s', _tables)
        try:
            self.query('OPTIMIZE TABLE %s' % _tables)
            self.debug('optimize success')
        except Exception, msg:
            self.error('optimizing table(s) failed: %s: trying to repair...', msg)
            self.repairTables(t)

    def repairTables(self, t=None):
        if not t:
            t = self.showTables()
        if isinstance(t, basestring):
            _tables = str(t)
        else:
            _tables = ', '.join(t)
        self.debug('repairing table(s): %s' % _tables)
        try:
            self.query('REPAIR TABLE %s' % _tables)
            self.debug('repair success')
        except Exception, msg:
            self.error('repairing table(s) failed: %s' % msg)

    def calculateKillBonus(self):
        self.debug('calculating kill_bonus')
        # make sure _max and _diff are floating numbers (may be redundant)
        _oldkillbonus = self.kill_bonus

        # querymax skill from players active in the last 20 days
        seconds = 20 * 86400
        q = """SELECT %s.time_edit, MAX(%s.skill) AS max_skill FROM %s, %s WHERE %s - %s.time_edit <= %s""" % (
            self.clients_table, self.playerstats_table, self.clients_table, self.playerstats_table, int(time.time()),
            self.clients_table, seconds)
        cursor = self.query(q)
        r = cursor.getRow()
        _max = r['max_skill']
        if _max is None:
            _max = self.defaultskill
        _max = float(_max)
        self.verbose('max skill: %s' % _max)
        _diff = _max - self.defaultskill
        if _diff < 0:
            self.kill_bonus = 2.0
        elif _diff < 400:
            self.kill_bonus = 1.5
        else:
            c = 200.0 / _diff + 1
            self.kill_bonus = round(c, 1)
        self.assist_bonus = self.kill_bonus / 3
        if self.kill_bonus != _oldkillbonus:
            self.debug('kill_bonus changed to: %s', self.kill_bonus)
            self.debug('assist_bonus changed to: %s', self.assist_bonus)
        else:
            self.verbose('kill_bonus: %s' % self.kill_bonus)
            self.verbose('assist_bonus: %s' % self.assist_bonus)

    def correctStats(self):
        self.debug('gathering XLRstats statistics')
        _seconds = self._auto_correct_ignore_days * 86400
        q = """SELECT MAX(%s.skill) AS max_skill, MIN(%s.skill) AS min_skill, SUM(%s.skill) AS sum_skill,
               AVG(%s.skill) AS avg_skill , COUNT(%s.id) AS cnt
               FROM %s, %s
               WHERE %s.id = %s.client_id
               AND %s.client_id <> %s
               AND (%s.kills + %s.deaths) > %s
               AND %s - %s.time_edit <= %s""" \
               % (self.playerstats_table, self.playerstats_table, self.playerstats_table,
                  self.playerstats_table, self.playerstats_table,
                  self.playerstats_table, self.clients_table,
                  self.clients_table, self.playerstats_table,
                  self.playerstats_table, self._world_clientid,
                  self.playerstats_table, self.playerstats_table, self.Kswitch_confrontations,
                  int(time.time()), self.clients_table, _seconds)

        cursor = self.query(q)
        # self.verbose(q)
        r = cursor.getRow()

        if r['cnt'] == 0:
            return None

        _acceptable_average = self.defaultskill + 100
        _factor_decimals = 6
        # self.verbose('%s; %s; %s' % (r['sum_skill'], _acceptable_average, r['cnt']))
        _surplus = r['sum_skill'] - (r['cnt'] * _acceptable_average)
        _correction = _surplus / r['cnt']
        _correction_factor = (r['cnt'] * _acceptable_average) / r['sum_skill']

        self.verbose('------------------------------------------')
        self.verbose('- Active pool parameters:')
        self.verbose('-   Players of last %d days', self._auto_correct_ignore_days)
        self.verbose('-   Players with minimal %d confrontations', self.Kswitch_confrontations)
        self.verbose('------------------------------------------')
        self.verbose('- Total players participating: %d', r['cnt'])
        self.verbose('- Total skill points in pool: %.2f', r['sum_skill'])
        self.verbose('------------------------------------------')
        self.verbose('- Highest skill in pool: %.2f', r['max_skill'])
        self.verbose('- Lowest skill in pool: %.2f', r['min_skill'])
        self.verbose('------------------------------------------')
        self.verbose('- Average skill: %.2f', r['avg_skill'])
        self.verbose('- Acceptable average skill: %.2f', _acceptable_average)
        self.verbose('------------------------------------------')
        self.verbose('- Difference (total) with acceptable pool: %.2f', _surplus)
        self.verbose('- Avg. points deviation p/player: %.3f', _correction)
        self.verbose('- Deviation factor: %s', round(_correction_factor, _factor_decimals))
        self.verbose('------------------------------------------')

        if _correction_factor < 1:
            self.verbose('- !!CORRECTION OF SKILL ADVISED!!')
        else:
            self.verbose('- pool has room for inflation... no action needed')

        self.verbose('------------------------------------------')

        if self.auto_correct and round(_correction_factor, _factor_decimals) < 1:
            self.debug('correcting overall skill with factor %s...' % round(_correction_factor, _factor_decimals))
            self.query("""UPDATE %s SET skill=(SELECT skill * %s ) WHERE %s.client_id <> %s""" % (
                       self.playerstats_table, _correction_factor, self.playerstats_table, self._world_clientid))

    def purgePlayers(self):
        if not self.auto_purge:
            return None

        self.debug('purgin players who haven\'t been online for %s days...', self._purge_player_days)

        # find players who haven't been online for a long time
        _seconds = self._purge_player_days * 86400
        q = """SELECT %s.id, %s.time_edit, %s.client_id, %s.id as player_id FROM %s, %s
               WHERE %s.id = %s.client_id
               AND %s - %s.time_edit > %s""" % (
               self.clients_table, self.clients_table, self.playerstats_table, self.playerstats_table,
               self.clients_table, self.playerstats_table, self.clients_table, self.playerstats_table,
               int(time.time()), self.clients_table, _seconds)

        cursor = self.query(q)
        if cursor and not cursor.EOF:
            while not cursor.EOF:
                r = cursor.getRow()
                self.verbose(r)
                self.purgePlayerStats(r['player_id'])
                self.purgeAssociated(self.playeractions_table, r['player_id'])
                self.purgeAssociated(self.playerbody_table, r['player_id'])
                self.purgeAssociated(self.playermaps_table, r['player_id'])
                self.purgeAssociated(self.weaponusage_table, r['player_id'])
                cursor.moveNext()

    def purgePlayerStats(self, _id):
        self.query("""DELETE FROM %s WHERE id = %s""" % (self.playerstats_table, _id))

    def purgeAssociated(self, _table, _id):
        self.query("""DELETE FROM %s WHERE player_id = %s""" % (_table, _id))

    ####################################################################################################################
    #                                                                                                                  #
    #    COMMANDS                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def cmd_xlrstats(self, data, client, cmd=None):
        """
        [<name>] - list a players XLR stats
        """
        if data:
            sclient = self._adminPlugin.findClientPrompt(data, client)
            if not sclient:
                # a player matchin the name was not found, a list of closest matches will be displayed
                # we can exit here and the user will retry with a more specific player
                return
        else:
            sclient = client

        stats = self.get_PlayerStats(sclient)

        if stats:
            if stats.hide == 1:
                client.message('^3XLR Stats: ^7stats for %s are not available (hidden)' % sclient.exactName)
            else:
                message_vars = {
                    'name': sclient.exactName,
                    'kills': stats.kills,
                    'deaths': stats.deaths,
                    'teamkills': stats.teamkills,
                    'ratio': '%1.02f' % stats.ratio,
                    'skill': '%1.02f' % stats.skill,
                }
                message = self.getMessage('cmd_xlrstats', message_vars)
                cmd.sayLoudOrPM(client, message)
        else:
            client.message('^3XLR Stats: ^7could not find stats for %s' % sclient.exactName)

    def cmd_xlrtopstats(self, data, client, cmd=None, ext=False):
        """
        [<#>] - list the top # players of the last 14 days.
        """
        thread.start_new_thread(self.doTopList, (data, client, cmd, ext))

    def doTopList(self, data, client, cmd=None, ext=False):
        """
        Retrieves the Top # Players.
        """
        limit = 3
        if data:
            if re.match('^[0-9]+$', data, re.I):
                limit = int(data)
                if limit > 10:
                    limit = 10

        q = 'SELECT %s.name, %s.time_edit, %s.id, kills, deaths, ratio, skill, winstreak, losestreak, rounds, fixed_name, ip \
             FROM %s, %s \
                 WHERE (%s.id = %s.client_id) \
                 AND ((%s.kills > %s) \
                 AND (%s.rounds > %s)) \
                 AND (%s.hide = 0) \
                 AND (%s - %s.time_edit  <= %s * 60 * 60 * 24) \
                 AND %s.id NOT IN \
                     ( SELECT distinct(target.id) FROM %s as penalties, %s as target \
                     WHERE (penalties.type = "Ban" \
                     OR penalties.type = "TempBan") \
                     AND inactive = 0 \
                     AND penalties.client_id = target.id \
                     AND ( penalties.time_expire = -1 \
                     OR penalties.time_expire > %s ) ) \
             ORDER BY %s.skill DESC LIMIT %s'\
             % (self.clients_table, self.clients_table, self.playerstats_table, self.clients_table, self.playerstats_table,
                self.clients_table, self.playerstats_table, self.playerstats_table, self._minKills, self.playerstats_table,
                self._minRounds, self.playerstats_table, int(time.time()), self.clients_table, self._maxDays, self.clients_table,
                self.penalties_table, self.clients_table,
                int(time.time()),
                self.playerstats_table, limit)

        cursor = self.query(q)
        if cursor and not cursor.EOF:
            message = '^3XLR Stats Top %s Players:' % limit
            if ext:
                self.console.say(message)
            else:
                cmd.sayLoudOrPM(client, message)
            c = 1
            while not cursor.EOF:
                r = cursor.getRow()
                message = self.getMessage('cmd_xlrtopstats', {'number': c, 'name': r['name'], 'skill': '%1.02f' % r['skill'],
                                                              'ratio': '%1.02f' % r['ratio'], 'kills': r['kills']})
                if ext:
                    self.console.say(message)
                else:
                    cmd.sayLoudOrPM(client, message)

                cursor.moveNext()
                c += 1
                time.sleep(1)
        else:
            self.debug('no players qualified for the toplist yet...')
            message = 'Qualify for the toplist by making at least %i kills and playing %i rounds!' % (
                      self._minKills, self._minRounds)
            if ext:
                self.console.say(message)
            else:
                cmd.sayLoudOrPM(client, message)

    def cmd_xlrhide(self, data, client, cmd=None):
        """
        <player> <on/off> - hide/unhide a player from the stats
        """
        # this will split the player name and the message
        handle = self._adminPlugin.parseUserCmd(data)
        if handle:
            # input[0] is the player id
            sclient = self._adminPlugin.findClientPrompt(handle[0], client)
            if not sclient:
                # a player matchin the name was not found, a list of closest matches will be displayed
                # we can exit here and the user will retry with a more specific player
                return
        else:
            client.message('^7Invalid data, try !help xlrhide')
            return

        if not handle[1]:
            client.message('^7Missing data, try !help xlrhide')
            return

        m = handle[1]
        if m in ('on', '1', 'yes'):
            if client != sclient:
                sclient.message('^3You are invisible in xlrstats!')
            client.message('^3%s INVISIBLE in xlrstats!' % sclient.exactName)
            hide = 1
        elif m in ('off', '0', 'no'):
            if client != sclient:
                sclient.message('^3You are visible in xlrstats!')
            client.message('^3%s VISIBLE in xlrstats!' % sclient.exactName)
            hide = 0
        else:
            client.message('^7Invalid or missing data, try !help xlrhide')
            return

        player = self.get_PlayerStats(sclient)
        if player:
            player.hide = int(hide)
            self.save_Stat(player)

    def cmd_xlrid(self, data, client, cmd=None):
        """
        <player ID Token> - identify yourself to the XLRstats website, get your token in your profile on the xlrstats website (v3)
        """
        handle = self._adminPlugin.parseUserCmd(data)
        if handle:
            # input[0] is the token
            token = handle[0]
        else:
            client.message('^7Invalid/missing data, try !help xlrid')
            return

        player = self.get_PlayerStats(client)
        if player:
            player.id_token = token
            self.verbose('saving identification token %s' % token)
            self.save_Stat(player)
            client.message('^3Token saved!')

    def cmd_xlrstatus(self, data, client, cmd=None):
        """
        - exposes current plugin status and major settings
        """
        if not self._xlrstats_active:
            _neededPlayers = len(self.console.clients.getList()) - self.min_players
            client.message('^3XLRstats disabled: need %s more players' % abs(_neededPlayers))
        else:
            client.message('^3XLRstats enabled: collecting stats')

        if self.provisional_ranking:
            client.message('^3Provisional phase: %s confrontations' % self.Kswitch_confrontations)

        client.message('^3auto_correct: %s, auto_purge: %s, k_b: %s, as_b: %s, ac_b: %s' %
                       (self.auto_correct, self.auto_purge, self.kill_bonus, self.assist_bonus, self.action_bonus))

    def cmd_xlrinit(self, data, client, cmd=None):
        """
        - initialize XLRstats database schema (!!!will remove all the collected stats!!!)
        """
        xlr_tables = [getattr(self, x) for x in dir(self) if x.endswith('_table')]
        current_tables = self.console.storage.getTables()

        # truncate database tables
        for table in xlr_tables:
            if table in current_tables:
                self.info('inizializing table: %s', table)
                self.console.storage.truncateTable(table)

        # eventually rebuild missing tables
        self.build_database_schema()
        client.message('^3XLRstats database schema initialized')

########################################################################################################################
#                                                                                                                      #
#   SUB PLUGIN CONTROLLER - CONTROLS STARTING AND STOPPING OF MAIN XLRSTATS PLUGIN BASED ON PLAYERCOUNT                #
#   OBSOLETE! REMOVED SINCE IT ALSO AFFECTED THE COMMANDS BEING UNAVAILABLE WHEN INACTIVE                              #
#                                                                                                                      #
########################################################################################################################

# class XlrstatscontrollerPlugin(b3.plugin.Plugin):
#     """This is a helper class/plugin that enables and disables the main XLRstats plugin
#     It can not be called directly or separately from the XLRstats plugin!"""
#
#     def __init__(self, console, min_players=3, silent=False):
#         self.console = console
#         self.console.debug('Initializing SubPlugin: XlrstatsControllerPlugin')
#         self.min_players = min_players
#         self.silent = silent
#         # empty message cache
#         self._messages = {}
#         self.registerEvent(b3.events.EVT_STOP)
#         self.registerEvent(b3.events.EVT_EXIT)
#
#     def onStartup(self):
#         self.console.debug('Starting SubPlugin: XlrstatsControllerPlugin')
#         #get a reference to the main Xlrstats plugin
#         self._xlrstatsPlugin = self.console.getPlugin('xlrstats')
#         # register the events we're interested in.
#         self.registerEvent(b3.events.EVT_CLIENT_JOIN)
#         self.registerEvent(b3.events.EVT_GAME_ROUND_START)
#
#     def onEvent(self, event):
#         if event.type == b3.events.EVT_CLIENT_JOIN:
#             self.checkMinPlayers()
#         elif event.type == b3.events.EVT_GAME_ROUND_START:
#             self.checkMinPlayers(_roundstart=True)
#
#     def checkMinPlayers(self, _roundstart=False):
#         """Checks if minimum amount of players are present
#         if minimum amount of players is reached will enable stats collecting
#         and if not it disables stats counting on next roundstart"""
#         self._current_nr_players = len(self.console.clients.getList())
#         self.debug(
#             'Checking number of players online. Minimum = %s, Current = %s' % (self.min_players, self._current_nr_players))
#         if self._current_nr_players < self.min_players and self._xlrstatsPlugin.isEnabled() and _roundstart:
#             self.info('Disabling XLRstats: Not enough players online')
#             if not self.silent:
#                 self.console.say('XLRstats Disabled: Not enough players online!')
#             self._xlrstatsPlugin.disable()
#         elif self._current_nr_players >= self.min_players and not self._xlrstatsPlugin.isEnabled():
#             self.info('Enabling XLRstats: Collecting Stats')
#             if not self.silent:
#                 self.console.say('XLRstats Enabled: Now collecting stats!')
#             self._xlrstatsPlugin.enable()
#         else:
#             if self._xlrstatsPlugin.isEnabled():
#                 _status = 'Enabled'
#             else:
#                 _status = 'Disabled'
#             self.debug('Nothing to do at the moment. XLRstats is already %s' % _status)

########################################################################################################################
##                                                                                                                    ##
##  SUB PLUGIN HISTORY - SAVES HISTORY SNAPSHOTS, WEEKLY AND/OR MONTHLY                                               ##
##                                                                                                                    ##
########################################################################################################################

class XlrstatshistoryPlugin(b3.plugin.Plugin):
    """
    This is a helper class/plugin that saves history snapshots
    It can not be called directly or separately from the XLRstats plugin!
    """
    requiresConfigFile = False
    _cronTab = None
    _cronTabMonth = None
    _cronTabWeek = None
    _max_months = 12
    _max_weeks = 12
    _hours = 5
    _minutes = 10

    ####################################################################################################################
    #                                                                                                                  #
    #   PLUGIN STARTUP                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def __init__(self, console, weeklyTable, monthlyTable, playerstatsTable):
        """
        Object constructor.
        :param console: The console instance
        :param weeklyTable: The history weekly database table name
        :param monthlyTable: The history monthly database table name
        :param playerstatsTable: The playerstats database table name
        """
        b3.plugin.Plugin.__init__(self, console)
        self.history_weekly_table = weeklyTable
        self.history_monthly_table = monthlyTable
        self.playerstats_table = playerstatsTable
        # empty message cache
        self._messages = {}
        # define a shortcut to the storage.query function
        self.query = self.console.storage.query
        # purge crontab
        tzName = self.console.config.get('b3', 'time_zone').upper()
        tzOffest = b3.timezones.timezones[tzName]
        hoursGMT = (self._hours - tzOffest)%24
        self.debug(u'%02d:%02d %s => %02d:%02d UTC' % (self._hours, self._minutes, tzName, hoursGMT, self._minutes))
        self.info(u'everyday at %2d:%2d %s, history info older than %s months and %s weeks will be deleted' % (
                  self._hours, self._minutes, tzName, self._max_months, self._max_weeks))
        self._cronTab = b3.cron.PluginCronTab(self, self.purge, 0, self._minutes, hoursGMT, '*', '*', '*')
        self.console.cron + self._cronTab

    def onStartup(self):
        """
        Initialize plugin.
        """
        self.debug('starting subplugin...')
        self.verbose('installing history crontabs')

        # remove existing crontabs
        try:
            self.console.cron - self._cronTabMonth
        except:
            pass
        try:
            self.console.cron - self._cronTabWeek
        except:
            pass
        try:
            # install crontabs
            self._cronTabMonth = b3.cron.PluginCronTab(self, self.snapshot_month, 0, 0, 0, 1, '*', '*')
            self.console.cron + self._cronTabMonth
            self._cronTabWeek = b3.cron.PluginCronTab(self, self.snapshot_week, 0, 0, 0, '*', '*', 1)  # day 1 is monday
            self.console.cron + self._cronTabWeek
        except Exception, msg:
            self.error('unable to install history crontabs: %s', msg)

        # purge the tables on startup
        self.purge()

    ####################################################################################################################
    #                                                                                                                  #
    #   CRONJOBS                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def snapshot_month(self):
        """
        Create the monthly snapshot.
        """
        sql = """INSERT INTO %s (client_id, kills, deaths, teamkills, teamdeaths, suicides, ratio,
                 skill, assists, assistskill, winstreak, losestreak, rounds, year, month, week, day)
                 SELECT client_id, kills, deaths, teamkills, teamdeaths, suicides, ratio, skill, assists,
                 assistskill, winstreak, losestreak, rounds, YEAR(NOW()), MONTH(NOW()), WEEK(NOW(),3), DAY(NOW())
                 FROM %s""" % (self.history_monthly_table, self.playerstats_table)
        try:
            self.query(sql)
            self.verbose('monthly XLRstats snapshot created')
        except Exception, msg:
            self.error('creating history snapshot failed: %s' % msg)

    def snapshot_week(self):
        """
        Create the weekly snapshot.
        """
        sql = """INSERT INTO %s (client_id , kills, deaths, teamkills, teamdeaths, suicides, ratio,
                 skill, assists, assistskill, winstreak, losestreak, rounds, year, month, week, day)
                 SELECT client_id, kills, deaths, teamkills, teamdeaths, suicides, ratio, skill, assists,
                 assistskill, winstreak, losestreak, rounds, YEAR(NOW()), MONTH(NOW()), WEEK(NOW(),3), DAY(NOW())
                 FROM %s""" % (self.history_weekly_table, self.playerstats_table)
        try:
            self.query(sql)
            self.verbose('weekly XLRstats snapshot created')
        except Exception, msg:
            self.error('creating history snapshot failed: %s', msg)

    def purge(self):
        """
        Purge history tables.
        """
        # purge the months table
        if not self._max_months or self._max_months == 0:
            self.warning(u'max_months is invalid [%s]' % self._max_months)
            return False
        self.info(u'purge of history entries older than %s months ...' % self._max_months)
        maxMonths = self.console.time() - self._max_months*24*60*60*30
        self.verbose(u'calculated maxMonths: %s' % maxMonths)
        _month = datetime.datetime.fromtimestamp(int(maxMonths)).strftime('%m')
        _year = datetime.datetime.fromtimestamp(int(maxMonths)).strftime('%Y')
        if int(_month) < self._max_months:
            _yearPrev = int(_year)-1
        else:
            _yearPrev = int(_year)
        q = """DELETE FROM %s WHERE (month < %s AND year <= %s) OR year < %s""" % (self.history_monthly_table, _month, _year, _yearPrev)
        self.debug(u'QUERY: %s ' % q)
        self.console.storage.query(q)
        # purge the weeks table
        if not self._max_weeks or self._max_weeks == 0:
            self.warning(u'max_weeks is invalid [%s]' % self._max_weeks)
            return False
        self.info(u'purge of history entries older than %s weeks ...' % self._max_weeks)
        maxWeeks = self.console.time() - self._max_weeks*24*60*60*7
        self.verbose(u'calculated maxWeeks: %s' % maxWeeks)
        _week = datetime.datetime.fromtimestamp(int(maxWeeks)).strftime('%W')
        _year = datetime.datetime.fromtimestamp(int(maxWeeks)).strftime('%Y')
        if int(_week) < self._max_weeks:
            _yearPrev = int(_year)-1
        else:
            _yearPrev = int(_year)
        q = """DELETE FROM %s WHERE (week < %s AND year <= %s) OR year < %s""" % (self.history_weekly_table, _week, _year, _yearPrev)
        self.debug(u'QUERY: %s ' % q)
        self.console.storage.query(q)

########################################################################################################################
#                                                                                                                      #
#   SUB PLUGIN CTIME - REGISTERS JOIN AND LEAVE TIMES OF PLAYERS                                                       #
#                                                                                                                      #
########################################################################################################################

class TimeStats(object):
    came = None
    left = None
    client = None


class CtimePlugin(b3.plugin.Plugin):
    """
    This is a helper class/plugin that saves client join and disconnect time info
    It can not be called directly or separately from the XLRstats plugin!
    """
    requiresConfigFile = False
    _clients = {}
    _cronTab = None
    _max_age_in_days = 31
    _hours = 5
    _minutes = 0

    ####################################################################################################################
    #                                                                                                                  #
    #   PLUGIN STARTUP                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def __init__(self, console, cTimeTable):
        """
        Object constructor.
        :param console: The console instance
        :param cTimeTable: The ctime database table name
        """
        b3.plugin.Plugin.__init__(self, console)
        self.ctime_table = cTimeTable
        # define a shortcut to the storage.query function
        self.query = self.console.storage.query
        tzName = self.console.config.get('b3', 'time_zone').upper()
        tzOffest = b3.timezones.timezones[tzName]
        hoursGMT = (self._hours - tzOffest)%24
        self.debug(u'%02d:%02d %s => %02d:%02d UTC' % (self._hours, self._minutes, tzName, hoursGMT, self._minutes))
        self.info(u'everyday at %2d:%2d %s, connection info older than %s days will be deleted' % (self._hours,
                  self._minutes, tzName, self._max_age_in_days))
        self._cronTab = b3.cron.PluginCronTab(self, self.purge, 0, self._minutes, hoursGMT, '*', '*', '*')
        self.console.cron + self._cronTab

    def onStartup(self):
        """
        Initialize plugin.
        """
        self.debug('starting subplugin...')
        self.registerEvent('EVT_CLIENT_AUTH', self.onAuth)
        self.registerEvent('EVT_CLIENT_DISCONNECT', self.onDisconnect)

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENTS                                                                                                         #
    #                                                                                                                  #
    ####################################################################################################################

    def onAuth(self, event):
        """
        Handle EVT_CLIENT_AUTH
        """
        if  not event.client or not event.client.id or event.client.cid is None or \
            not event.client.connected or event.client.hide:
            return
        self.update_time_stats_connected(event.client)

    def onDisconnect(self, event):
        """
        Handle EVT_CLIENT_DISCONNECT
        """
        self.update_time_stats_exit(event.data)

    ####################################################################################################################
    #                                                                                                                  #
    #   OTHER METHODS                                                                                                  #
    #                                                                                                                  #
    ####################################################################################################################

    def purge(self):
        """
        Purge the ctime database table.
        """
        if not self._max_age_in_days or self._max_age_in_days == 0:
            self.warning(u'max_age is invalid [%s]', self._max_age_in_days)
            return False

        self.info(u'purge of connection info older than %s days ...', self._max_age_in_days)
        q = """DELETE FROM %s WHERE came < %i""" % (self.ctime_table, (self.console.time() - (self._max_age_in_days * 24 * 60 * 60)))
        self.debug(u'CTIME QUERY: %s ' % q)
        self.console.storage.query(q)

    def update_time_stats_connected(self, client):
        if client.cid in self._clients:
            self.debug(u'CTIME CONNECTED: client exist! : %s', client.cid)
            tmpts = self._clients[client.cid]
            if tmpts.client.guid == client.guid:
                self.debug(u'CTIME RECONNECTED: player %s connected again, but playing since: %s', client.exactName, tmpts.came)
                return
            else:
                del self._clients[client.cid]

        ts = TimeStats()
        ts.client = client
        ts.came = datetime.datetime.now()
        self._clients[client.cid] = ts
        self.debug(u'CTIME CONNECTED: player %s started playing at: %s', client.exactName, ts.came)

    @staticmethod
    def formatTD(td):
        hours = td // 3600
        minutes = (td % 3600) // 60
        seconds = td % 60
        return '%s:%s:%s' % (hours, minutes, seconds)

    def update_time_stats_exit(self, clientid):
        self.debug(u'CTIME LEFT:')
        if clientid in self._clients:
            ts = self._clients[clientid]
            # Fail: Sometimes PB in cod4 returns 31 character guids, we need to dump them.
            # Lets look ahead and do this for the whole codseries.
            #if(self.console.gameName[:3] == 'cod' and self.console.PunkBuster and len(ts.client.guid) != 32):
            #    pass
            #else:
            ts.left = datetime.datetime.now()
            diff = (int(time.mktime(ts.left.timetuple())) - int(time.mktime(ts.came.timetuple())))

            self.debug(u'CTIME LEFT: player: %s played this time: %s sec', ts.client.exactName, diff)
            self.debug(u'CTIME LEFT: player: %s played this time: %s', ts.client.exactName, self.formatTD(diff))
            #INSERT INTO `ctime` (`guid`, `came`, `left`) VALUES ("6fcc4f6d9d8eb8d8457fd72d38bb1ed2", 1198187868, 1226081506)
            q = """INSERT INTO %s (guid, came, gone, nick) VALUES (\"%s\", \"%s\", \"%s\", \"%s\")""" % (self.ctime_table,
                ts.client.guid, int(time.mktime(ts.came.timetuple())), int(time.mktime(ts.left.timetuple())), ts.client.name)
            self.query(q)

            self._clients[clientid].left = None
            self._clients[clientid].came = None
            self._clients[clientid].client = None
            del self._clients[clientid]

        else:
            self.debug(u'CTIME LEFT: player %s var not set!', clientid)

########################################################################################################################
#                                                                                                                      #
#   SUB PLUGIN BATTLELOG - REGISTERS LAST PLAYED MATCHES                                                               #
#                                                                                                                      #
########################################################################################################################

class BattlestatsPlugin(b3.plugin.Plugin):
    """
    This is a helper class/plugin that saves last played matches
    It can not be called directly or separately from the XLRstats plugin!
    """
    
    ####################################################################################################################
    #                                                                                                                  #
    #   PLUGIN STARTUP                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################
    
    def __init__(self, console, battlelogGamesTable, battlelogClientsTable):
        """
        Object constructor.
        :param console: The console instance
        :param battlelogGamesTable: The battlelog games table
        :param battlelogClientsTable: The battlelog clients table
        """
        b3.plugin.Plugin.__init__(self, console)
        self.battlelog_games_table = battlelogGamesTable
        self.battlelog_clients_table = battlelogClientsTable
        self.query = self.console.storage.query
        self.gameLog = None
        self.clientsLog = None

    def onStartup(self):
        """
        Initialize plugin.
        """
        self.console.debug('starting subplugin...')
        self.registerEvent('EVT_CLIENT_AUTH', self.onAuth)
        self.registerEvent('EVT_CLIENT_DISCONNECT', self.onDisconnect)
        self.registerEvent('EVT_GAME_ROUND_START', self.onRoundStart)
        self.registerEvent('EVT_GAME_ROUND_END', self.onRoundEnd)

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENTS                                                                                                         #
    #                                                                                                                  #
    ####################################################################################################################

    def onAuth(self, event):
        """
        Handle EVT_CLIENT_AUTH
        """
        pass

    def onDisconnect(self, event):
        """
        Handle EVT_CLIENT_DISCONNECT
        """
        pass

    def onRoundStart(self, event):
        """
        Handle EVT_GAME_ROUND_START
        """
        pass

    def onRoundEnd(self, event):
        """
        Handle EVT_GAME_ROUND_END
        """
        pass

    def clearBattlelog(self):
        self.gameLog = None
        self.clientsLog = None

    def setupBattlelog(self):
        self.gameLog = BattleStats()
        self.clientsLog = {}

########################################################################################################################
#                                                                                                                      #
#   ABSTRACT CLASSES TO AID XLRSTATS PLUGIN CLASS                                                                      #
#                                                                                                                      #
########################################################################################################################


class StatObject(object):

    _table = None

    def _insertquery(self):
        return None

    def _updatequery(self):
        return None


class PlayerStats(StatObject):

    # default name of the table for this data object
    _table = 'playerstats'

    # fields of the table
    id = None
    client_id = 0

    Kfactor = 1

    kills = 0
    deaths = 0
    teamkills = 0
    teamdeaths = 0
    suicides = 0

    ratio = 0
    skill = 0
    assists = 0
    assistskill = 0
    curstreak = 0
    winstreak = 0
    losestreak = 0
    rounds = 0
    hide = 0

    # the following fields are used only by the PHP presentation code
    fixed_name = ""
    id_token = ""    # player identification token for webfront v3

    def _insertquery(self):
        q = """INSERT INTO %s (client_id, kills, deaths, teamkills, teamdeaths, suicides, ratio, skill, assists,
               assistskill, curstreak, winstreak, losestreak, rounds, hide, fixed_name, id_token) VALUES (%s, %s, %s,
               %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, '%s', '%s')""" % (self._table, self.client_id, self.kills,
               self.deaths, self.teamkills, self.teamdeaths, self.suicides, self.ratio, self.skill, self.assists,
               self.assistskill, self.curstreak, self.winstreak, self.losestreak, self.rounds, self.hide,
               escape(self.fixed_name, "'"), self.id_token)
        return q

    def _updatequery(self):
        q = """UPDATE %s SET client_id=%s, kills=%s, deaths=%s, teamkills=%s, teamdeaths=%s, suicides=%s, ratio=%s,
               skill=%s, assists=%s, assistskill=%s, curstreak=%s, winstreak=%s, losestreak=%s, rounds=%s, hide=%s,
               fixed_name='%s', id_token='%s' WHERE id= %s""" % (self._table, self.client_id, self.kills, self.deaths,
               self.teamkills, self.teamdeaths, self.suicides, self.ratio, self.skill, self.assists, self.assistskill,
               self.curstreak, self.winstreak, self.losestreak, self.rounds, self.hide, escape(self.fixed_name, "'"),
               self.id_token, self.id)
        return q


class WeaponStats(StatObject):

    # default name of the table for this data object
    _table = 'weaponstats'

    # fields of the table
    id = None
    name = ''
    kills = 0
    suicides = 0
    teamkills = 0

    def _insertquery(self):
        q = """INSERT INTO %s (name, kills, suicides, teamkills) VALUES ('%s', %s, %s, %s)""" % (
            self._table, escape(self.name, "'"), self.kills, self.suicides, self.teamkills)
        return q

    def _updatequery(self):
        q = """UPDATE %s SET name='%s', kills=%s, suicides=%s, teamkills=%s WHERE id=%s""" % (
            self._table, escape(self.name, "'"), self.kills, self.suicides, self.teamkills, self.id)
        return q


class WeaponUsage(StatObject):

    # default name of the table for this data object
    _table = 'weaponusage'

    # fields of the table
    id = None
    player_id = 0
    weapon_id = 0
    kills = 0
    deaths = 0
    suicides = 0
    teamkills = 0
    teamdeaths = 0

    def _insertquery(self):
        q = """INSERT INTO %s (player_id, weapon_id, kills, deaths, suicides, teamkills, teamdeaths)
            VALUES (%s, %s, %s, %s, %s, %s, %s)""" % (self._table, self.player_id, self.weapon_id, self.kills,
            self.deaths, self.suicides, self.teamkills, self.teamdeaths)
        return q

    def _updatequery(self):
        q = """UPDATE %s SET player_id=%s, weapon_id=%s, kills=%s, deaths=%s, suicides=%s, teamkills=%s,
            teamdeaths=%s WHERE id=%s""" % (self._table, self.player_id, self.weapon_id, self.kills, self.deaths,
            self.suicides, self.teamkills, self.teamdeaths, self.id)
        return q


class Bodyparts(StatObject):

    # default name of the table for this data object
    _table = 'bodyparts'

    # fields of the table
    id = None
    name = ''
    kills = 0
    suicides = 0
    teamkills = 0

    def _insertquery(self):
        q = """INSERT INTO %s (name, kills, suicides, teamkills) VALUES ('%s', %s, %s, %s)""" % (
            self._table, escape(self.name, "'"), self.kills, self.suicides, self.teamkills)
        return q

    def _updatequery(self):
        q = """UPDATE %s SET name='%s', kills=%s, suicides=%s, teamkills=%s WHERE id=%s""" % (
            self._table, escape(self.name, "'"), self.kills, self.suicides, self.teamkills, self.id)
        return q


class MapStats(StatObject):

    # default name of the table for this data object
    _table = 'mapstats'

    # fields of the table
    id = None
    name = ''
    kills = 0
    suicides = 0
    teamkills = 0
    rounds = 0

    def _insertquery(self):
        q = """INSERT INTO %s (name, kills, suicides, teamkills, rounds) VALUES ('%s', %s, %s, %s, %s)""" % (
            self._table, escape(self.name, "'"), self.kills, self.suicides, self.teamkills, self.rounds)
        return q

    def _updatequery(self):
        q = """UPDATE %s SET name='%s', kills=%s, suicides=%s, teamkills=%s, rounds=%s WHERE id=%s""" % (
            self._table, escape(self.name, "'"), self.kills, self.suicides, self.teamkills, self.rounds, self.id)
        return q


class PlayerBody(StatObject):

    # default name of the table for this data object
    _table = 'playerbody'

    # fields of the table
    id = None
    player_id = 0
    bodypart_id = 0
    kills = 0
    deaths = 0
    suicides = 0
    teamkills = 0
    teamdeaths = 0

    def _insertquery(self):
        q = """INSERT INTO %s (player_id, bodypart_id, kills, deaths, suicides, teamkills, teamdeaths)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""" % (self._table, self.player_id, self.bodypart_id, self.kills,
               self.deaths, self.suicides, self.teamkills, self.teamdeaths)
        return q

    def _updatequery(self):
        q = """UPDATE %s SET player_id=%s, bodypart_id=%s, kills=%s, deaths=%s, suicides=%s, teamkills=%s, teamdeaths=%s
            WHERE id=%s""" % (self._table, self.player_id, self.bodypart_id, self.kills, self.deaths, self.suicides, self.teamkills,
            self.teamdeaths, self.id)
        return q


class PlayerMaps(StatObject):

    # default name of the table for this data object
    _table = 'playermaps'

    # fields of the table
    id = 0
    player_id = 0
    map_id = 0
    kills = 0
    deaths = 0
    suicides = 0
    teamkills = 0
    teamdeaths = 0
    rounds = 0

    def _insertquery(self):
        q = """INSERT INTO %s (player_id, map_id, kills, deaths, suicides, teamkills, teamdeaths, rounds)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""" % (self._table, self.player_id, self.map_id, self.kills,
            self.deaths, self.suicides, self.teamkills, self.teamdeaths, self.rounds)
        return q

    def _updatequery(self):
        q = """UPDATE %s SET player_id=%s, map_id=%s, kills=%s, deaths=%s, suicides=%s, teamkills=%s,
            teamdeaths=%s, rounds=%s WHERE id=%s""" % (self._table, self.player_id, self.map_id, self.kills,
            self.deaths, self.suicides, self.teamkills, self.teamdeaths, self.rounds, self.id)
        return q


class Opponents(StatObject):

    # default name of the table for this data object
    _table = 'opponents'

    # fields of the table
    id = None
    killer_id = 0
    target_id = 0
    kills = 0
    retals = 0

    def _insertquery(self):
        q = """INSERT INTO %s (killer_id, target_id, kills, retals) VALUES (%s, %s, %s, %s)""" % (
            self._table, self.killer_id, self.target_id, self.kills, self.retals)
        return q

    def _updatequery(self):
        q = """UPDATE %s SET killer_id=%s, target_id=%s, kills=%s, retals=%s WHERE id=%s""" % (
            self._table, self.killer_id, self.target_id, self.kills, self.retals, self.id)
        return q


class ActionStats(StatObject):

    # default name of the table for this data object
    _table = 'actionstats'

    # fields of the table
    id = None
    name = ''
    count = 0

    def _insertquery(self):
        q = """INSERT INTO %s (name, count) VALUES ('%s', %s)""" % (self._table, escape(self.name, "'"), self.count)
        return q

    def _updatequery(self):
        q = """UPDATE %s SET name='%s', count=%s WHERE id=%s""" % (self._table, escape(self.name, "'"), self.count, self.id)
        return q


class PlayerActions(StatObject):

    # default name of the table for this data object
    _table = 'playeractions'

    # fields of the table
    id = None
    player_id = 0
    action_id = 0
    count = 0

    def _insertquery(self):
        q = """INSERT INTO %s (player_id, action_id, count) VALUES (%s, %s, %s)""" % (
            self._table, self.player_id, self.action_id, self.count)
        return q

    def _updatequery(self):
        q = """UPDATE %s SET player_id=%s, action_id=%s, count=%s WHERE id=%s""" % (
            self._table, self.player_id, self.action_id, self.count, self.id)
        return q


class BattleStats(StatObject):

    # default name of the table for this data object
    _table = 'battlestats'

    id = 0
    map_id = 0
    game_type = ''
    total_players = 0
    start_time = time.time()
    end_time = 0
    scores = {}

    def _insertquery(self):
        q = """INSERT INTO %s (map_id, game_type, total_players, start_time, end_time, scores)
               VALUES ('%s', %s, %s, %s, %s, '%s')""" % (self._table, self.map_id, self.game_type, self.total_players,
               self.start_time, self.end_time, self.scores)
        return q

    def _updatequery(self):
        q = """UPDATE %s SET map_id=%s, game_type='%s', total_players=%s, start_time=%s, end_time=%s,
            scores='%s' """ % (self._table, self.map_id, self.game_type, self.total_players, self.start_time,
            self.end_time, self.scores)
        return q


class PlayerBattles(StatObject):

    # default name of the table for this data object
    _table = 'playerbattles'

    battlestats_id = 0
    start_skill = 0
    end_skill = 0
    kills = 0
    teamKills = 0
    deaths = 0
    assists = 0
    actions = 0
    weapon_kills = {}
    favorite_weapon_id = 0


if __name__ == '__main__':
    print '\nThis is version ' + __version__ + ' by ' + __author__ + ' for BigBrotherBot.\n'

"""
Crontab:
*  *  *  *  *  command to be executed
-  -  -  -  -
|  |  |  |  |
|  |  |  |  +----- day of week (0 - 6) (Sunday=0)
|  |  |  +------- month (1 - 12)
|  |  +--------- day of month (1 - 31)
|  +----------- hour (0 - 23)
+------------- min (0 - 59)

Query:
INSERT INTO xlr_history_weekly (`client_id` , `kills` , `deaths` , `teamkills` , `teamdeaths` , `suicides` , `ratio` , `skill` , `winstreak` , `losestreak` , `rounds`, `year`, `month`, `week`, `day`) 
  SELECT `client_id` , `kills` , `deaths` , `teamkills` , `teamdeaths` , `suicides` , `ratio` , `skill` , `winstreak` , `losestreak` , `rounds`, YEAR(NOW()), MONTH(NOW()), WEEK(NOW(),3), DAY(NOW()) 
  FROM `xlr_playerstats`
"""
