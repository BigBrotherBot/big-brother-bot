##################################################################
#
# XLRstats
# statistics-generating plugin for B3 (www.bigbrotherbot.net)
# (c) 2004, 2005 Tim ter Laak (ttlogic@xlr8or.com)
# (c) 2005 - 2013 Mark Weirath (xlr8or@xlr8or.com)
#
# This program is free software and licensed under the terms of
# the GNU General Public License (GPL), version 2.
#
##################################################################
# CHANGELOG
# See xlrstats-v2-changelog.txt for version 1 and 2 history and credits.
#
# 22-11-2012 - 3.0.0b1 - Mark Weirath
#   preparations for version 3.0 of XLRstats

# This section is DoxuGen information. More information on how to comment your code
# is available at http://wiki.bigbrotherbot.net/doku.php/customize:doxygen_rules
## @file
# XLRstats Real Time playerstats plugin

__author__ = 'Tim ter Laak / Mark Weirath'
__version__ = '3.0.0'

# Version = major.minor.patches

import datetime
import time
import re
import thread
import threading
import urllib2
from ConfigParser import NoOptionError
import b3
import b3.events
import b3.plugin
import b3.cron

KILLER = "killer"
VICTIM = "victim"
ASSISTER = "assister"


class XlrstatsPlugin(b3.plugin.Plugin):
    requiresConfigFile = True

    _world_clientid = None
    _ffa = ['dm', 'ffa', 'syc-ffa']
    _damage_able_games = ['cod'] # will only count assists when damage is 50 points or more.
    _damage_ability = False
    hide_bots = True # set client.hide to True so bots are hidden from the stats
    exclude_bots = True # kills and damage to and from bots do not affect playerskill

    # history management
    _cronTabWeek = None
    _cronTabMonth = None
    _cronTabKillBonus = None

    # webfront variables
    webfrontUrl = ''
    webfrontConfigNr = 0
    _minKills = 500
    _minRounds = 50
    _maxDays = 14

    # config variables
    defaultskill = 1000
    minlevel = 1
    onemaponly = False

    Kfactor_high = 16
    Kfactor_low = 4
    Kswitch_kills = 100

    steepness = 600
    suicide_penalty_percent = 0.05
    tk_penalty_percent = 0.1
    kill_bonus = 1.5
    assist_bonus = 0.5
    assist_timespan = 2 # on non damage based games: damage before death timespan
    damage_assist_release = 10 # on damage based games: release the assist (wil overwrite self.assist_timespan on startup)
    prematch_maxtime = 70
    announce = False
    keep_history = True
    keep_time = True
    minPlayers = 3 # minimum number of players to collect stats
    _currentNrPlayers = 0 # current number of players present
    silent = False # Disables the announcement when collecting stats = stealth mode

    # keep some private map data to detect prematches and restarts
    last_map = None
    last_roundtime = None

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
    #
    _defaultTableNames = True


    def startup(self):
        # get the admin plugin so we can register commands
        self._adminPlugin = self.console.getPlugin('admin')
        if not self._adminPlugin:
            # something is wrong, can't start without admin plugin
            self.error('Could not find admin plugin')
            return False

        # register our commands
        if 'commands' in self.config.sections():
            for cmd in self.config.options('commands'):
                level = self.config.get('commands', cmd)
                sp = cmd.split('-')
                alias = None
                if len(sp) == 2:
                    cmd, alias = sp

                func = self.getCmd(cmd)
                if func:
                    self._adminPlugin.registerCommand(self, cmd, level, func, alias)

        #define a shortcut to the storage.query function
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

        #--OBSOLETE
        # create tables if necessary
        # This needs to be done here, because table names were loaded from config
        #PlayerStats.createTable(ifNotExists=True)
        #WeaponStats.createTable(ifNotExists=True)
        #WeaponUsage.createTable(ifNotExists=True)
        #Bodyparts.createTable(ifNotExists=True)
        #PlayerBody.createTable(ifNotExists=True)
        #Opponents.createTable(ifNotExists=True)
        #MapStats.createTable(ifNotExists=True)
        #PlayerMaps.createTable(ifNotExists=True)
        #--end OBS

        # create default tables if not present
        # removed to avoid MySQL 5.5 issues locking the db
        #if self._defaultTableNames:
        #    self.console.storage.queryFromFile("@b3/sql/xlrstats.sql", silent=True)

        # register the events we're interested in.
        self.registerEvent(b3.events.EVT_CLIENT_JOIN)
        self.registerEvent(b3.events.EVT_CLIENT_KILL)
        self.registerEvent(b3.events.EVT_CLIENT_KILL_TEAM)
        self.registerEvent(b3.events.EVT_CLIENT_SUICIDE)
        self.registerEvent(b3.events.EVT_GAME_ROUND_START)
        self.registerEvent(b3.events.EVT_CLIENT_ACTION) #for game-events/actions
        self.registerEvent(b3.events.EVT_CLIENT_DAMAGE) #for assist recognition

        # get the Client.id for the bot itself (guid: WORLD or Server(bfbc2/moh/hf))
        sclient = self.console.clients.getByGUID("WORLD")
        if sclient is None:
            sclient = self.console.clients.getByGUID("Server")
        if sclient is not None:
            self._world_clientid = sclient.id
            self.debug('Got client id for B3: %s; %s' % (self._world_clientid, sclient.name))
            #make sure its hidden in the webfront
            player = self.get_PlayerStats(sclient)
            if player:
                player.hide = 1
                self.save_Stat(player)


        #determine the ability to work with damage based assists
        if self.console.gameName[:3] in self._damage_able_games:
            self._damage_ability = True
            self.assist_timespan = self.damage_assist_release

        #investigate if we can and want to keep a history
        self._xlrstatstables = [self.playerstats_table, self.weaponstats_table, self.weaponusage_table,
                                self.bodyparts_table, self.playerbody_table, self.opponents_table, self.mapstats_table,
                                self.playermaps_table, self.actionstats_table, self.playeractions_table]
        if self.keep_history:
            self._xlrstatstables = [self.playerstats_table, self.weaponstats_table, self.weaponusage_table,
                                    self.bodyparts_table, self.playerbody_table, self.opponents_table,
                                    self.mapstats_table, self.playermaps_table, self.actionstats_table,
                                    self.playeractions_table, self.history_monthly_table, self.history_weekly_table]
            _tables = self.showTables(xlrstats=True)
            if (self.history_monthly_table in _tables) and (self.history_monthly_table in _tables):
                self.verbose('History tables are present! Starting Subplugin XLRstatsHistory.')
                #start the xlrstats history plugin
                p = XlrstatshistoryPlugin(self.console, self.history_weekly_table, self.history_monthly_table,
                                          self.playerstats_table)
                p.startup()
            else:
                self.keep_history = False
                self._xlrstatstables = [self.playerstats_table, self.weaponstats_table, self.weaponusage_table,
                                        self.bodyparts_table, self.playerbody_table, self.opponents_table,
                                        self.mapstats_table, self.playermaps_table, self.actionstats_table,
                                        self.playeractions_table]
                self.error(
                    'History Tables are NOT present! Please run b3/docs/xlrstats.sql on your database to install missing tables!')

        #check and update columns in existing tables // This is not working with MySQL server 5.5!
        #self.updateTableColumns()
        #optimize xlrstats tables
        #self.optimizeTables(self._xlrstatstables)

        #let's try and get some variables from our webfront installation
        if self.webfrontUrl and self.webfrontUrl != '':
            thread1 = threading.Thread(target=self.getWebsiteVariables)
            thread1.start()
        else:
            self.debug('No Webfront Url available, using defaults')

        #set proper kill_bonus and crontab
        self.calculateKillBonus()
        if self._cronTabKillBonus:
            self.console.cron - self._cronTabKillBonus
        self._cronTabKillBonus = b3.cron.PluginCronTab(self, self.calculateKillBonus, 0, '*/10')
        self.console.cron + self._cronTabKillBonus

        #start the ctime subplugin
        if self.keep_time:
            p = CtimePlugin(self.console, self.ctime_table)
            p.startup()

        #start the xlrstats controller
        p = XlrstatscontrollerPlugin(self.console, self.minPlayers, self.silent)
        p.startup()

        #get the map we're in, in case this is a new map and we need to create a db record for it.
        map = self.get_MapStats(self.console.game.mapName)
        if map:
            self.verbose('Map %s ready' % map.name)

        msg = 'XLRstats v. %s by %s started.' % (__version__, __author__)
        self.console.say(msg)
        #end startup sequence


    def onLoadConfig(self):
        self.load_config_settings()
        self.load_config_tables()


    def load_config_settings(self):
        try:
            self.silent = self.config.getboolean('settings', 'silent')
        except:
            self.debug('Using default value (%s) for settings::silent', self.silent)

        try:
            self.hide_bots = self.config.getboolean('settings', 'hide_bots')
        except:
            self.debug('Using default value (%s) for settings::hide_bots', self.hide_bots)

        try:
            self.exclude_bots = self.config.getboolean('settings', 'exclude_bots')
        except:
            self.debug('Using default value (%s) for settings::exclude_bots', self.exclude_bots)

        try:
            min_players = self.config.getint('settings', 'minplayers')
            if min_players < 0:
                raise ValueError("minplayers cannot be lower than 0")
            self.minPlayers = min_players
        except:
            self.debug('Using default value (%s) for settings::minplayers', self.minPlayers)

        try:
            self.webfrontUrl = self.config.get('settings', 'webfronturl')
        except:
            self.debug('Using default value (%s) for settings::webfronturl', self.webfrontUrl)

        try:
            server_number = self.config.getint('settings', 'servernumber')
            if server_number < 0:
                raise ValueError("servernumber cannot be lower than 0")
            self.webfrontConfigNr = server_number
        except:
            self.debug('Using default value (%i) for settings::servernumber', self.webfrontConfigNr)

        try:
            self.keep_history = self.config.getboolean('settings', 'keep_history')
        except:
            self.debug('Using default value (%i) for settings::keep_history', self.keep_history)

        try:
            self.onemaponly = self.config.getboolean('settings', 'onemaponly')
        except:
            self.debug('Using default value (%i) for settings::onemaponly', self.onemaponly)

        try:
            min_level = self.config.getint('settings', 'minlevel')
            if min_level < 0:
                raise ValueError("minlevel cannot be lower than 0")
            self.minlevel = min_level
        except:
            self.debug('Using default value (%i) for settings::minlevel', self.minlevel)

        try:
            self.defaultskill = self.config.getint('settings', 'defaultskill')
        except:
            self.debug('Using default value (%i) for settings::defaultskill', self.defaultskill)

        try:
            self.Kfactor_high = self.config.getint('settings', 'Kfactor_high')
        except:
            self.debug('Using default value (%i) for settings::Kfactor_high', self.Kfactor_high)

        try:
            self.Kfactor_low = self.config.getint('settings', 'Kfactor_low')
        except:
            self.debug('Using default value (%i) for settings::Kfactor_low', self.Kfactor_low)

        try:
            self.Kswitch_kills = self.config.getint('settings', 'Kswitch_kills')
        except:
            self.debug('Using default value (%i) for settings::Kswitch_kills', self.Kswitch_kills)

        try:
            self.steepness = self.config.getint('settings', 'steepness')
        except:
            self.debug('Using default value (%i) for settings::steepness', self.steepness)

        try:
            self.suicide_penalty_percent = self.config.getfloat('settings', 'suicide_penalty_percent')
        except:
            self.debug('Using default value (%f) for settings::suicide_penalty_percent', self.suicide_penalty_percent)

        try:
            self.tk_penalty_percent = self.config.getfloat('settings', 'tk_penalty_percent')
        except:
            self.debug('Using default value (%f) for settings::tk_penalty_percent', self.tk_penalty_percent)

        #--OBSOLETE
        #try:
        #    self.kill_bonus = self.config.getfloat('settings', 'kill_bonus')
        #except:
        #    self.kill_bonus = 1.2
        #    self.debug('Using default value (%f) for settings::kill_bonus', self.kill_bonus)

        #try:
        #    self.assist_bonus = self.config.getfloat('settings', 'assist_bonus')
        #    #cap off the assistbonus, so it will not be better rewarded than a kill
        #    if self.assist_bonus > 0.9:
        #        self.assist_bonus = 0.9
        #except:
        #    self.debug('Using default value (%f) for settings::assist_bonus', self.assist_bonus)
        #--end OBS

        try:
            self.assist_timespan = self.config.getint('settings', 'assist_timespan')
        except:
            self.debug('Using default value (%d) for settings::assist_timespan', self.assist_timespan)

        try:
            self.damage_assist_release = self.config.getint('settings', 'damage_assist_release')
        except:
            self.debug('Using default value (%d) for settings::damage_assist_release', self.damage_assist_release)

        try:
            self.prematch_maxtime = self.config.getint('settings', 'prematch_maxtime')
        except:
            self.debug('Using default value (%d) for settings::prematch_maxtime', self.prematch_maxtime)

        try:
            self.announce = self.config.getboolean('settings', 'announce')
        except:
            self.debug('Using default value (%d) for settings::announce', self.announce)

        try:
            self.keep_time = self.config.getboolean('settings', 'keep_time')
        except:
            self.debug('Using default value (%d) for settings::keep_time', self.keep_time)


    def load_config_tables(self):
        """
        load config section 'tables'
        """

        def load_conf(property_to_set, setting_option):
            assert hasattr(self, property_to_set)
            try:
                table_name = self.config.get('tables', setting_option)
                if not table_name:
                    raise ValueError("invalid table name for %s : %r" % (setting_option, table_name))
                setattr(self, property_to_set, table_name)
                self._defaultTableNames = False
            except NoOptionError, err:
                self.debug(err)
            except Exception, err:
                self.error(err)
            self.info('Using value "%s" for tables::%s' % (property_to_set, setting_option))

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


    def getCmd(self, cmd):
        cmd = 'cmd_%s' % cmd
        if hasattr(self, cmd):
            func = getattr(self, cmd)
            return func

        return None


    def onEvent(self, event):
        if event.type == b3.events.EVT_CLIENT_JOIN:
            self.join(event.client)
        elif event.type == b3.events.EVT_CLIENT_KILL:
            self.kill(event.client, event.target, event.data)
        elif event.type == b3.events.EVT_CLIENT_KILL_TEAM:
            if self.console.game.gameType in self._ffa:
                self.kill(event.client, event.target, event.data)
            else:
                self.teamkill(event.client, event.target, event.data)
        elif event.type == b3.events.EVT_CLIENT_DAMAGE:
            self.damage(event.client, event.target, event.data)
        elif event.type == b3.events.EVT_CLIENT_SUICIDE:
            self.suicide(event.client, event.target, event.data)
        elif event.type == b3.events.EVT_GAME_ROUND_START:
            self.roundstart()
        elif event.type == b3.events.EVT_CLIENT_ACTION:
            self.action(event.client, event.data)
        else:
            self.dumpEvent(event)


    def dumpEvent(self, event):
        self.debug('xlrstats.dumpEvent -- Type %s, Client %s, Target %s, Data %s',
                   event.type, event.client, event.target, event.data)


    def getWebsiteVariables(self):
        """
        Thread that polls for XLRstats webfront variables
        """
        _request = str(self.webfrontUrl.rstrip('/')) + '/?config=' + str(self.webfrontConfigNr) + '&func=pluginreq'
        try:
            f = urllib2.urlopen(_request)
            _result = f.readline().split(',')
            # Our webfront will present us 3 values ie.: 200,20,30
            if len(_result) == 3:
                # Force the collected strings to their final type. If an error occurs they will fail the try statement.
                self._minKills = int(_result[0])
                self._minRounds = int(_result[1])
                self._maxDays = int(_result[2])
                self.debug('Successfuly retrieved webfront variables: minkills: %i, minrounds: %i, maxdays: %i' % (
                    self._minKills, self._minRounds, self._maxDays))
        except Exception:
            self.debug('Couldn\'t retrieve webfront variables, using defaults')


    def win_prob(self, player_skill, opponent_skill):
        return 1 / ( 10 ** ( (opponent_skill - player_skill) / self.steepness ) + 1 )


    # Retrieves an existing stats record for given client,
    # or makes a new one IFF client's level is high enough
    # Otherwise (also on error), it returns None.
    def get_PlayerStats(self, client=None):
        if client is None:
            id = self._world_clientid
        else:
            id = client.id
        q = 'SELECT * from %s WHERE client_id = %s LIMIT 1' % (self.playerstats_table, id)
        cursor = self.query(q)
        if cursor and not cursor.EOF:
            r = cursor.getRow()
            s = PlayerStats()
            s.id = r['id']
            s.client_id = r['client_id']
            s.kills = r['kills']
            if s.kills > self.Kswitch_kills:
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
            s.client_id = id
            return s
        else:
            return None

    def get_PlayerAnon(self):
        return self.get_PlayerStats(None)

    def get_WeaponStats(self, name):
        s = WeaponStats()
        q = 'SELECT * from %s WHERE name = "%s" LIMIT 1' % (self.weaponstats_table, name)
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
        q = 'SELECT * from %s WHERE name = "%s" LIMIT 1' % (self.bodyparts_table, name)
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
        s = MapStats()
        q = 'SELECT * from %s WHERE name = "%s" LIMIT 1' % (self.mapstats_table, name)
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
        q = 'SELECT * from %s WHERE weapon_id = %s AND player_id = %s LIMIT 1' % (
            self.weaponusage_table, weaponid, playerid)
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
        q = 'SELECT * from %s WHERE killer_id = %s AND target_id = %s LIMIT 1' % (
            self.opponents_table, killerid, targetid)
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
        q = 'SELECT * from %s WHERE bodypart_id = %s AND player_id = %s LIMIT 1' % (
            self.playerbody_table, bodypartid, playerid)
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
            self.error('Map not recognized, trying to initialise map...')
            map = self.get_MapStats(self.console.game.mapName)
            if map:
                self.verbose('Map %s successfully initialised.' % map.name)
                mapid = map.id
            else:
                return None

        s = PlayerMaps()
        q = 'SELECT * from %s WHERE map_id = %s AND player_id = %s LIMIT 1' % (self.playermaps_table, mapid, playerid)
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
        q = 'SELECT * from %s WHERE name = "%s" LIMIT 1' % (self.actionstats_table, name)
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
        q = 'SELECT * from %s WHERE action_id = %s AND player_id = %s LIMIT 1' % (
            self.playeractions_table, actionid, playerid)
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
        #self.verbose('*----> XLRstats: Saving statistics for %s' %type(stat))
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
        #determine eventual assists // an assist only counts if damage was done within # secs. before death
        #it will also punish teammates that have a 'negative' assist!
        _count = 0 # number of assists to return
        _sum = 0   # sum of assistskill returned
        _vsum = 0  # sum of victims skill deduction returned
        self.verbose('----> XLRstats: %s Killed %s (%s), checking for assists' % (client.name, target.name, etype))

        try:
            ainfo = target._attackers
        except:
            target._attackers = {}
            ainfo = target._attackers

        for k, v in ainfo.iteritems():
            if k == client.cid:
                #don't award the killer for the assist aswell
                continue
            elif time.time() - v < self.assist_timespan:
                assister = self.console.clients.getByCID(k)
                self.verbose('----> XLRstats: assister = %s' % assister.name)

                anonymous = None

                victimstats = self.get_PlayerStats(target)
                assiststats = self.get_PlayerStats(assister)

                # if both should be anonymous, we have no work to do
                if (assiststats is None) and (victimstats is None):
                    self.verbose('----> XLRstats: check_Assists: %s & %s both anonymous, continueing' % (
                        assister.name, target.name))
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

                #calculate the win probability for the assister and victim
                assist_prob = self.win_prob(assiststats.skill, victimstats.skill)
                #performance patch provided by IzNoGod: ELO states that assist_prob + victim_prob = 1
                #victim_prob = self.win_prob(victimstats.skill, assiststats.skill)
                victim_prob = 1 - assist_prob

                self.verbose('----> XLRstats: win probability for %s: %s' % (assister.name, assist_prob))
                self.verbose('----> XLRstats: win probability for %s: %s' % (target.name, victim_prob))

                #get applicable weapon replacement
                actualweapon = data[1]
                for r in data:
                    try:
                        actualweapon = self.config.get('replacements', r)
                    except:
                        pass

                #get applicable weapon multiplier
                try:
                    weapon_factor = self.config.getfloat('weapons', actualweapon)
                except:
                    weapon_factor = 1.0

                #calculate new skill for the assister
                if anonymous != ASSISTER:
                    oldskill = assiststats.skill
                    if ( target.team == assister.team ) and not ( self.console.game.gameType in self._ffa ):
                        #assister is a teammate and needs skill and assists reduced
                        _assistbonus = self.assist_bonus * assiststats.Kfactor * weapon_factor * (0 - assist_prob)
                        assiststats.skill = float(assiststats.skill) + _assistbonus
                        assiststats.assistskill = float(assiststats.assistskill) + _assistbonus
                        assiststats.assists -= 1 #negative assist
                        self.verbose(
                            '----> XLRstats: Assistpunishment deducted for %s: %s (oldsk: %.3f - newsk: %.3f)' % (
                                assister.name, assiststats.skill - oldskill, oldskill, assiststats.skill))
                        _count += 1
                        _sum += _assistbonus
                        if self.announce and not assiststats.hide:
                            assister.message('^5XLRstats:^7 Teamdamaged (%s) -> skill: ^1%.3f^7 -> ^2%.1f^7' % (
                                target.name, assiststats.skill - oldskill, assiststats.skill))
                    else:
                        #this is a real assist
                        _assistbonus = self.assist_bonus * assiststats.Kfactor * weapon_factor * (1 - assist_prob)
                        assiststats.skill = float(assiststats.skill) + _assistbonus
                        assiststats.assistskill = float(assiststats.assistskill) + _assistbonus
                        assiststats.assists += 1
                        self.verbose('----> XLRstats: Assistbonus awarded for %s: %s (oldsk: %.3f - newsk: %.3f)' % (
                            assister.name, assiststats.skill - oldskill, oldskill, assiststats.skill))
                        _count += 1
                        _sum += _assistbonus
                        if self.announce and not assiststats.hide:
                            assister.message('^5XLRstats:^7 Assistbonus (%s) -> skill: ^2+%.3f^7 -> ^2%.1f^7' % (
                                target.name, assiststats.skill - oldskill, assiststats.skill))
                    self.save_Stat(assiststats)

                #calculate new skill for the victim
                    oldskill = victimstats.skill
                    if ( target.team == assister.team ) and not ( self.console.game.gameType in self._ffa ):
                        #assister was a teammate, this should not affect victims skill.
                        pass
                    else:
                        #this is a real assist
                        _assistdeduction = self.assist_bonus * victimstats.Kfactor * weapon_factor * (0 - victim_prob)
                        victimstats.skill = float(victimstats.skill) + _assistdeduction
                        self.verbose('----> XLRstats: Assist skilldeduction for %s: %s (oldsk: %.3f - newsk: %.3f)' % (
                            target.name, victimstats.skill - oldskill, oldskill, victimstats.skill))
                        _vsum += _assistdeduction
                    self.save_Stat(victimstats)

        #end of assist reward function, return the number of assists 
        return _count, _sum, _vsum

    def kill(self, client, target, data):
        if (client is None) or (client.id == self._world_clientid):
            return
        if target is None:
            return
        if data is None:
            return

        # exclude botkills?
        if (client.bot or target.bot) and self.exclude_bots:
            self.verbose('Bot involved, do not process!')
            return

        _assists_count, _assists_sum, _victim_sum = self.check_Assists(client, target, data, 'kill')

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

        #calculate winning probabilities for both players
        killer_prob = self.win_prob(killerstats.skill, victimstats.skill)
        #performance patch provided by IzNoGod: ELO states that killer_prob + victim_prob = 1
        #victim_prob = self.win_prob(victimstats.skill, killerstats.skill)
        victim_prob = 1 - killer_prob

        #get applicable weapon replacement
        actualweapon = data[1]
        for r in data:
            try:
                actualweapon = self.config.get('replacements', r)
            except:
                pass

        #get applicable weapon multiplier
        try:
            weapon_factor = self.config.getfloat('weapons', actualweapon)
        except:
            weapon_factor = 1.0

        #calculate new stats for the killer
        if anonymous != KILLER:
            oldskill = killerstats.skill
            #pure skilladdition for a 100% kill
            _skilladdition = self.kill_bonus * killerstats.Kfactor * weapon_factor * (1 - killer_prob)
            #deduct the assists from the killers skill, but no more than 50%
            if _assists_sum == 0:
                pass
            elif _assists_sum >= ( _skilladdition / 2 ):
                _skilladdition /= 2
                self.verbose(
                    '----> XLRstats: Killer: assists > 50perc: %.3f - skilladd: %.3f' % (_assists_sum, _skilladdition))
            else:
                _skilladdition -= _assists_sum
                self.verbose(
                    '----> XLRstats: Killer: assists < 50perc: %.3f - skilladd: %.3f' % (_assists_sum, _skilladdition))

            killerstats.skill = float(killerstats.skill) + _skilladdition
            self.verbose('----> XLRstats: Killer: oldsk: %.3f - newsk: %.3f' % (oldskill, killerstats.skill))
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

            if self.announce and not killerstats.hide:
                client.message('^5XLRstats:^7 Killed %s -> skill: ^2+%.3f^7 -> ^2%.1f^7' % (
                    target.name, (killerstats.skill - oldskill), killerstats.skill))
            self.save_Stat(killerstats)

        #calculate new stats for the victim
        if anonymous != VICTIM:
            oldskill = victimstats.skill

            #pure skilldeduction for a 100% kill
            _skilldeduction = victimstats.Kfactor * weapon_factor * (0 - victim_prob)
            #deduct the assists from the victims skill deduction, but no more than 50%
            if _victim_sum == 0:
                pass
            elif _victim_sum <= ( _skilldeduction / 2 ): #carefull, negative numbers here
                _skilldeduction /= 2
                self.verbose('----> XLRstats: Victim: assists > 50perc: %.3f - skilldeduct: %.3f' % (
                    _victim_sum, _skilldeduction))
            else:
                _skilldeduction -= _victim_sum
                self.verbose('----> XLRstats: Victim: assists < 50perc: %.3f - skilldeduct: %.3f' % (
                    _victim_sum, _skilldeduction))

            victimstats.skill = float(victimstats.skill) + _skilldeduction
            self.verbose('----> XLRstats: Victim: oldsk: %.3f - newsk: %.3f' % (oldskill, victimstats.skill))
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

            if self.announce and not victimstats.hide:
                target.message('^5XLRstats:^7 Killed by %s -> skill: ^1%.3f^7 -> ^2%.1f^7' % (
                    client.name, (victimstats.skill - oldskill), victimstats.skill))
            self.save_Stat(victimstats)

        #make sure the record for anonymous is really created with an insert once
        if anonymous:
            if (anonymous == KILLER) and (hasattr(killerstats, '_new')):
                self.save_Stat(killerstats)
            elif (anonymous == VICTIM) and (hasattr(victimstats, '_new')):
                self.save_Stat(victimstats)

                #adjust the "opponents" table to register who killed who
        opponent = self.get_Opponent(targetid=victimstats.id, killerid=killerstats.id)
        retal = self.get_Opponent(targetid=killerstats.id, killerid=victimstats.id)
        #the above should always succeed, but you never know...
        if opponent and retal:
            opponent.kills += 1
            retal.retals += 1
            self.save_Stat(opponent)
            self.save_Stat(retal)

        #adjust weapon statistics
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

        #adjust bodypart statistics
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

        #adjust map statistics
        map = self.get_MapStats(self.console.game.mapName)
        if map:
            map.kills += 1
            self.save_Stat(map)

            map_killer = self.get_PlayerMaps(playerid=killerstats.id, mapid=map.id)
            map_victim = self.get_PlayerMaps(playerid=victimstats.id, mapid=map.id)
            if map_killer and map_victim:
                map_killer.kills += 1
                map_victim.deaths += 1
                self.save_Stat(map_killer)
                self.save_Stat(map_victim)

        #end of kill function
        return

    def damage(self, client, target, data):
        if client.id == self._world_clientid:
            self.verbose('----> XLRstats: onDamage: WORLD-damage, moving on...')
            return None
        if client.cid == target.cid:
            self.verbose(
                '----> XLRstats: onDamage: self damage: %s damaged %s, continueing' % (client.name, target.name))
            return None
            # exclude botdamage?
        if (client.bot or target.bot) and self.exclude_bots:
            self.verbose('Bot involved, do not process!')
            return None

        #check if game is _damage_able -> 50 points or more damage will award an assist
        if self._damage_ability and data[0] < 50:
            self.verbose('---> XLRstats: Not enough damage done to award an assist')
            return

        try:
            target._attackers[client.cid] = time.time()
        except:
            target._attackers = {}
            target._attackers[client.cid] = time.time()
        self.verbose('----> XLRstats: onDamage: attacker added: %s (%s) damaged %s (%s)' % (
            client.name, client.cid, target.name, target.cid))
        self.verbose('----> XLRstats: Assistinfo: %s' % target._attackers)

    def suicide(self, client, target, data):
        if client is None:
            return
        if target is None:
            return
        if data is None:
            return

        self.check_Assists(client, target, data, 'suicide')

        playerstats = self.get_PlayerStats(client)

        if playerstats is None:
            #anonymous player. We're not interested :)
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
            client.message('^5XLRstats:^7 Suicide -> skill: ^1%.3f^7 -> ^2%.1f^7' % (
                playerstats.skill - oldskill, playerstats.skill))
        self.save_Stat(playerstats)

        #get applicable weapon replacement
        actualweapon = data[1]
        for r in data:
            try:
                actualweapon = self.config.get('replacements', r)
            except:
                pass

        #update weapon stats
        weaponstats = self.get_WeaponStats(name=actualweapon)
        if weaponstats:
            weaponstats.suicides += 1
            self.save_Stat(weaponstats)

            w_usage = self.get_WeaponUsage(playerid=playerstats.id, weaponid=weaponstats.id)
            if w_usage:
                w_usage.suicides += 1
                self.save_Stat(w_usage)

        #update bodypart stats
        bodypart = self.get_Bodypart(name=data[2])
        if bodypart:
            bodypart.suicides += 1
            self.save_Stat(bodypart)

            bp_player = self.get_PlayerBody(playerid=playerstats.id, bodypartid=bodypart.id)
            if bp_player:
                bp_player.suicides = int(bp_player.suicides) + 1
                self.save_Stat(bp_player)

        #adjust map statistics
        map = self.get_MapStats(self.console.game.mapName)
        if map:
            map.suicides += 1
            self.save_Stat(map)

            map_player = self.get_PlayerMaps(playerid=playerstats.id, mapid=map.id)
            if map_player:
                map_player.suicides += 1
                self.save_Stat(map_player)

        #end of function suicide
        return

    def teamkill(self, client, target, data):
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
            #Calculate new stats for the killer
            oldskill = killerstats.skill
            killerstats.skill = (1 - (self.tk_penalty_percent / 100.0) ) * float(killerstats.skill)
            killerstats.teamkills += 1
            killerstats.curstreak = 0   # break off current streak as it is now "impure"
            if self.announce and not killerstats.hide:
                client.message('^5XLRstats:^7 Teamkill -> skill: ^1%.3f^7 -> ^2%.1f^7' % (
                    killerstats.skill - oldskill, killerstats.skill))
            self.save_Stat(killerstats)

        if anonymous != VICTIM:
            #Calculate new stats for the victim
            victimstats.teamdeaths += 1
            self.save_Stat(victimstats)

        # do not register a teamkill in the "opponents" table

        #get applicable weapon replacement
        actualweapon = data[1]
        for r in data:
            try:
                actualweapon = self.config.get('replacements', r)
            except:
                pass

        #adjust weapon statistics
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

        #adjust bodypart statistics
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

        #adjust map statistics
        map = self.get_MapStats(self.console.game.mapName)
        if map:
            map.teamkills += 1
            self.save_Stat(map)

            map_killer = self.get_PlayerMaps(playerid=killerstats.id, mapid=map.id)
            map_victim = self.get_PlayerMaps(playerid=victimstats.id, mapid=map.id)
            if map_killer and map_victim:
                map_killer.teamkills += 1
                map_victim.teamdeaths += 1
                self.save_Stat(map_killer)
                self.save_Stat(map_victim)

        #end of function teamkill
        return


    def join(self, client):
        if client is None:
            return

        # test if it is a bot and flag it
        if client.guid[:3] == 'BOT':
            self.verbose('Bot found!')
            client.bot = True

        player = self.get_PlayerStats(client)
        if player:
            player.rounds = int(player.rounds) + 1
            if client.bot:
                if self.hide_bots:
                    self.verbose('Hiding Bot!')
                    player.hide = True
                else:
                    self.verbose('Unhiding Bot!')
                    player.hide = False
            self.save_Stat(player)

            map = self.get_MapStats(self.console.game.mapName)
            if map:
                playermap = self.get_PlayerMaps(player.id, map.id)
                if playermap:
                    playermap.rounds += 1
                    self.save_Stat(playermap)
        return

    def roundstart(self):
        #disable k/d counting if minimum players are not met

        if self.last_map is None:
            self.last_map = self.console.game.mapName
            #self.last_roundtime = self.console.game._roundTimeStart
        else:
            if not self.onemaponly and ( self.last_map == self.console.game.mapName) and  (
                self.console.game.roundTime() < self.prematch_maxtime):
                #( self.console.game._roundTimeStart - self.last_roundtime < self.prematch_maxtime) ):
                return
            else:
                self.last_map = self.console.game.mapName
                #self.last_roundtime = self.console.game._roundTimeStart

        map = self.get_MapStats(self.console.game.mapName)
        if map:
            map.rounds += 1
            self.save_Stat(map)

        return

    def action(self, client, data):
        #self.verbose('----> XLRstats: Entering actionfunc.')
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

        #is it an anonymous client, stop here
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

        #get applicable action bonus
        try:
            action_bonus = self.config.getfloat('actions', action.name)
            #self.verbose('----> XLRstats: Found a bonus for %s: %s' %(action.name, action_bonus))
        except:
            action_bonus = 3

        if action_bonus:
            #self.verbose('----> XLRstats: Old Skill: %s.' %playerstats.skill)
            playerstats.skill += action_bonus
            #self.verbose('----> XLRstats: New Skill: %s.' %playerstats.skill)
            self.save_Stat(playerstats)

        return

    def cmd_xlrstats(self, data, client, cmd=None):
        """\
        [<name>] - list a players XLR stats
        """
        if data:
            sclient = self._adminPlugin.findClientPrompt(data, client)
            if not sclient: return
        else:
            sclient = client

        stats = self.get_PlayerStats(sclient)

        if stats:
            if stats.hide == 1:
                client.message('^3XLR Stats: ^7Stats for %s are not available (hidden).' % sclient.exactName)
                return None
            else:
                message = '^3XLR Stats: ^7%s ^7: K ^2%s ^7D ^3%s ^7TK ^1%s ^7Ratio ^5%1.02f ^7Skill ^3%1.02f' % (
                    sclient.exactName, stats.kills, stats.deaths, stats.teamkills, stats.ratio, stats.skill)
                cmd.sayLoudOrPM(client, message)
        else:
            client.message('^3XLR Stats: ^7Could not find stats for %s' % sclient.exactName)

        return

    # Start a thread to get the top players
    def cmd_xlrtopstats(self, data, client, cmd=None, ext=False):
        """\
        [<#>] - list the top # players of the last 14 days.
        """
        thread.start_new_thread(self.doTopList, (data, client, cmd, ext))

        return

    # Retrieves the Top # Players
    def doTopList(self, data, client, cmd=None, ext=False):
        if data:
            if re.match('^[0-9]+$', data, re.I):
                limit = int(data)
                if limit > 10:
                    limit = 10
        else:
            limit = 3


        q = 'SELECT `%s`.name, `%s`.time_edit, `%s`.id, kills, deaths, ratio, skill, winstreak, losestreak, rounds, fixed_name, ip \
        FROM `%s`, `%s` \
            WHERE (`%s`.id = `%s`.client_id) \
            AND ((`%s`.kills > %s) \
            OR (`%s`.rounds > %s)) \
            AND (`%s`.hide = 0) \
            AND (%s - `%s`.time_edit  <= %s*60*60*24) \
            AND `%s`.id NOT IN \
                ( SELECT distinct(target.id) FROM `%s` as penalties, `%s` as target \
                WHERE (penalties.type = "Ban" \
                OR penalties.type = "TempBan") \
                AND inactive = 0 \
                AND penalties.client_id = target.id \
                AND ( penalties.time_expire = -1 \
                OR penalties.time_expire > %s ) ) \
        ORDER BY `%s`.`skill` DESC LIMIT %s'\
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
                message = '^3# %s: ^7%s ^7: Skill ^3%1.02f ^7Ratio ^5%1.02f ^7Kills: ^2%s' % (
                    c, r['name'], r['skill'], r['ratio'], r['kills'])
                if ext:
                    self.console.say(message)
                else:
                    cmd.sayLoudOrPM(client, message)
                cursor.moveNext()
                c += 1
                time.sleep(1)
        else:
            self.debug('No players qualified for the toplist yet...')
            message = 'Qualify for the toplist by making %i kills, or playing %i rounds!' % (
                self._minKills, self._minRounds)
            if ext:
                self.console.say(message)
            else:
                cmd.sayLoudOrPM(client, message)
            return None

        return

    def cmd_xlrhide(self, data, client, cmd=None):
        """\
        <player> <on/off> - Hide/unhide a player from the stats
        """
        # this will split the player name and the message
        input = self._adminPlugin.parseUserCmd(data)
        if input:
            # input[0] is the player id
            sclient = self._adminPlugin.findClientPrompt(input[0], client)
            if not sclient:
                # a player matchin the name was not found, a list of closest matches will be displayed
                # we can exit here and the user will retry with a more specific player
                return False
        else:
            client.message('^7Invalid data, try !help xlrhide')
            return False

        if not input[1]:
            client.message('^7Missing data, try !help xlrhide')
            return False

        m = input[1]
        if m in ('on', '1'):
            if client != sclient:
                sclient.message('^3You are invisible in xlrstats!')
            client.message('^3%s INVISIBLE in xlrstats!' % sclient.exactName)
            hide = 1
        elif m in ('off', '0'):
            if client != sclient:
                sclient.message('^3You are visible in xlrstats!')
            client.message('^3%s VISIBLE in xlrstats!' % sclient.exactName)
            hide = 0
        else:
            client.message('^7Invalid or missing data, try !help xlrhide')

        player = self.get_PlayerStats(sclient)
        if player:
            player.hide = int(hide)
            self.save_Stat(player)

        return

    def cmd_xlrid(self, data, client, cmd=None):
        """\
        <player ID Token> - Identify yourself to the XLRstats website, get your token in your profile on the xlrstats website (v3)
        """
        input = self._adminPlugin.parseUserCmd(data)
        if input:
            # input[0] is the token
            token = input[0]
        else:
            client.message('^7Invalid/missing data, try !help xlrid')
            return False

        player = self.get_PlayerStats(client)
        if player:
            player.id_token = token
            self.verbose('Saving identification token %s' % token)
            self.save_Stat(player)

        return

    ## @todo: add mysql condition
    def updateTableColumns(self):
        self.verbose('Checking if we need to update tables for version 2.0.0')
        #v2.0.0 additions to the playerstats table:
        self._addTableColumn('assists', PlayerStats._table, 'MEDIUMINT( 8 ) NOT NULL DEFAULT "0" AFTER `skill`')
        self._addTableColumn('assistskill', PlayerStats._table, 'FLOAT NOT NULL DEFAULT "0" AFTER `assists`')
        #alterations to columns in existing tables:
        self._updateTableColumns()
        return None
        #end of update check

    def _addTableColumn(self, c1, t1, specs):
        try:
            self.query('SELECT `%s` FROM %s limit 1;' % (c1, t1))
        except Exception, e:
            if e[0] == 1054:
                self.console.debug('Column does not yet exist: %s' % e)
                self.query('ALTER TABLE %s ADD `%s` %s ;' % (t1, c1, specs))
                self.console.info('Created new column `%s` on %s' % (c1, t1))
            else:
                self.console.error('Query failed - %s: %s' % (type(e), e))

    def _updateTableColumns(self):
        try:
            #need to update the weapon-identifier columns in these tables for cod7. This game knows over 255 weapons/variations
            self.query(
                'ALTER TABLE  `%s` CHANGE  `id`  `id` SMALLINT( 5 ) UNSIGNED NOT NULL AUTO_INCREMENT;' % WeaponStats._table)
            self.query(
                'ALTER TABLE  `%s` CHANGE  `weapon_id`  `weapon_id` SMALLINT( 5 ) UNSIGNED NOT NULL DEFAULT  "0";' % WeaponUsage._table)
        except:
            pass

    def showTables(self, xlrstats=False):
        _tables = []
        q = 'SHOW TABLES'
        cursor = self.query(q)
        if cursor and (cursor.rowcount > 0):
            while not cursor.EOF:
                r = cursor.getRow()
                n = str(r.values()[0])
                if xlrstats and not n in self._xlrstatstables:
                    pass
                else:
                    _tables.append(r.values()[0])
                cursor.moveNext()
        if xlrstats:
            self.console.verbose('Available XLRstats tables in this database: %s' % _tables)
        else:
            self.console.verbose('Available tables in this database: %s' % _tables)
        return _tables

    def optimizeTables(self, t=None):
        if not t:
            t = self.showTables()
        if type(t) == type(''):
            _tables = str(t)
        else:
            _tables = ', '.join(t)
        self.debug('Optimizing Table(s): %s' % _tables)
        try:
            self.query('OPTIMIZE TABLE %s' % _tables)
            self.debug('Optimize Success')
        except Exception, msg:
            self.error('Optimizing Table(s) Failed: %s, trying to repair...' % msg)
            self.repairTables(t)

    def repairTables(self, t=None):
        if not t:
            t = self.showTables()
        if type(t) == type(''):
            _tables = str(t)
        else:
            _tables = ', '.join(t)
        self.debug('Repairing Table(s): %s' % _tables)
        try:
            self.query('REPAIR TABLE %s' % _tables)
            self.debug('Repair Success')
        except Exception, msg:
            self.error('Repairing Table(s) Failed: %s' % msg)

    def calculateKillBonus(self):
        self.debug('Calculating kill_bonus')
        # make sure max and diff are floating numbers (may be redundant)
        max = 0.0
        diff = 0.0
        _oldkillbonus = self.kill_bonus

        q = 'SELECT MAX(skill) AS max_skill FROM %s' % self.playerstats_table
        cursor = self.query(q)
        r = cursor.getRow()
        max = r['max_skill']
        if max is None:
            max = self.defaultskill
        diff = max - self.defaultskill
        if diff < 0:
            self.kill_bonus = 2.0
        elif diff < 400:
            self.kill_bonus = 1.5
        else:
            c = 200.0 / diff + 1
            self.kill_bonus = round(c, 1)
        self.assist_bonus = self.kill_bonus / 3
        if self.kill_bonus != _oldkillbonus:
            self.debug('kill_bonus set to: %s' % self.kill_bonus)
            self.debug('assist_bonus set to: %s' % self.assist_bonus)


class XlrstatscontrollerPlugin(b3.plugin.Plugin):
    """This is a helper class/plugin that enables and disables the main XLRstats plugin
    It can not be called directly or separately from the XLRstats plugin!"""

    def __init__(self, console, minPlayers=3, silent=False):
        self.console = console
        self.minPlayers = minPlayers
        self.silent = silent
        # empty message cache
        self._messages = {}
        self.registerEvent(b3.events.EVT_STOP)
        self.registerEvent(b3.events.EVT_EXIT)

    def startup(self):
        self.console.debug('Starting SubPlugin: XlrstatsControllerPlugin')
        #get a reference to the main Xlrstats plugin
        self._xlrstatsPlugin = self.console.getPlugin('xlrstats')
        # register the events we're interested in.
        self.registerEvent(b3.events.EVT_CLIENT_JOIN)
        self.registerEvent(b3.events.EVT_GAME_ROUND_START)

    def onEvent(self, event):
        if event.type == b3.events.EVT_CLIENT_JOIN:
            self.checkMinPlayers()
        elif event.type == b3.events.EVT_GAME_ROUND_START:
            self.checkMinPlayers(_roundstart=True)

    def checkMinPlayers(self, _roundstart=False):
        """Checks if minimum amount of players are present
        if minimum amount of players is reached will enable stats collecting
        and if not it disables stats counting on next roundstart"""
        self._currentNrPlayers = len(self.console.clients.getList())
        self.debug(
            'Checking number of players online. Minimum = %s, Current = %s' % (self.minPlayers, self._currentNrPlayers))
        if self._currentNrPlayers < self.minPlayers and self._xlrstatsPlugin.isEnabled() and _roundstart:
            self.info('Disabling XLRstats: Not enough players online')
            if not self.silent:
                self.console.say('XLRstats Disabled: Not enough players online!')
            self._xlrstatsPlugin.disable()
        elif self._currentNrPlayers >= self.minPlayers and not self._xlrstatsPlugin.isEnabled():
            self.info('Enabling XLRstats: Collecting Stats')
            if not self.silent:
                self.console.say('XLRstats Enabled: Now collecting stats!')
            self._xlrstatsPlugin.enable()
        else:
            if self._xlrstatsPlugin.isEnabled():
                _status = 'Enabled'
            else:
                _status = 'Disabled'
            self.debug('Nothing to do at the moment. XLRstats is already %s' % _status)


class XlrstatshistoryPlugin(b3.plugin.Plugin):
    """This is a helper class/plugin that saves history snapshots
    It can not be called directly or separately from the XLRstats plugin!"""

    def __init__(self, console, weeklyTable, monthlyTable, playerstatsTable):
        self.console = console
        self.history_weekly_table = weeklyTable
        self.history_monthly_table = monthlyTable
        self.playerstats_table = playerstatsTable
        # empty message cache
        self._messages = {}
        self.registerEvent(b3.events.EVT_STOP)
        self.registerEvent(b3.events.EVT_EXIT)

    def startup(self):
        self.console.debug('Starting SubPlugin: XlrstatsHistoryPlugin')
        #define a shortcut to the storage.query function
        self.query = self.console.storage.query

        self.console.verbose('XlrstatshistoryPlugin: Installing history Crontabs:')
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
            self._cronTabWeek = b3.cron.PluginCronTab(self, self.snapshot_week, 0, 0, 0, '*', '*', 1) # day 1 is monday
            self.console.cron + self._cronTabWeek
        except Exception, msg:
            self.console.error('XlrstatshistoryPlugin: Unable to install History Crontabs: %s' % msg)


    def snapshot_month(self):
        sql = (
            'INSERT INTO ' + self.history_monthly_table + ' (`client_id` , `kills` , `deaths` , `teamkills` , `teamdeaths` , `suicides` ' +
            ', `ratio` , `skill` , `assists` , `assistskill` , `winstreak` , `losestreak` , `rounds`, `year`, `month`, `week`, `day`)' +
            '  SELECT `client_id` , `kills`, `deaths` , `teamkills` , `teamdeaths` , `suicides` , `ratio` , `skill` , `assists` , `assistskill` , `winstreak` ' +
            ', `losestreak` , `rounds`, YEAR(NOW()), MONTH(NOW()), WEEK(NOW(),3), DAY(NOW())' +
            '  FROM `' + self.playerstats_table + '`' )
        try:
            self.query(sql)
            self.verbose('Monthly XLRstats snapshot created')
        except Exception, msg:
            self.error('Creating history snapshot failed: %s' % msg)


    def snapshot_week(self):
        sql = (
            'INSERT INTO ' + self.history_weekly_table + ' (`client_id` , `kills` , `deaths` , `teamkills` , `teamdeaths` , `suicides` ' +
            ', `ratio` , `skill` , `assists` , `assistskill` , `winstreak` , `losestreak` , `rounds`, `year`, `month`, `week`, `day`)' +
            '  SELECT `client_id` , `kills`, `deaths` , `teamkills` , `teamdeaths` , `suicides` , `ratio` , `skill` , `assists` , `assistskill` , `winstreak` ' +
            ', `losestreak` , `rounds`, YEAR(NOW()), MONTH(NOW()), WEEK(NOW(),3), DAY(NOW())' +
            '  FROM `' + self.playerstats_table + '`' )
        try:
            self.query(sql)
            self.verbose('Weekly XLRstats snapshot created')
        except Exception, msg:
            self.error('Creating history snapshot failed: %s' % msg)

class TimeStats:
    came = None
    left = None
    client = None

class CtimePlugin(b3.plugin.Plugin):
    """This is a helper class/plugin that saves client join and disconnect time info
    It can not be called directly or separately from the XLRstats plugin!"""

    _clients = {}
    _cronTab = None
    _max_age_in_days = 31
    _hours = 5
    _minutes = 0

    def __init__(self, console, cTimeTable):
        self.console = console
        self.ctime_table = cTimeTable
        self.registerEvent(b3.events.EVT_CLIENT_AUTH)
        self.registerEvent(b3.events.EVT_CLIENT_DISCONNECT)
        self.query = self.console.storage.query
        tzName = self.console.config.get('b3', 'time_zone').upper()
        tzOffest = b3.timezones.timezones[tzName]
        hoursGMT = (self._hours - tzOffest)%24
        self.debug(u'%02d:%02d %s => %02d:%02d UTC' % (self._hours, self._minutes, tzName, hoursGMT, self._minutes))
        self.info(u'everyday at %2d:%2d %s, connection info older than %s days will be deleted' % (self._hours, self._minutes, tzName, self._max_age_in_days))
        self._cronTab = b3.cron.PluginCronTab(self, self.purge, 0, self._minutes, hoursGMT, '*', '*', '*')
        self.console.cron + self._cronTab

    def purge(self):
        if not self._max_age_in_days or self._max_age_in_days == 0:
            self.warning(u'max_age is invalid [%s]' % self._max_age_in_days)
            return False

        self.info(u'purge of connection info older than %s days ...' % self._max_age_in_days)
        q = "DELETE FROM %s WHERE came < %i" % (self.ctime_table, (self.console.time() - (self._max_age_in_days*24*60*60)))
        self.debug(u'CTIME QUERY: %s ' % q)
        cursor = self.console.storage.query(q)

    def onEvent(self, event):
        if event.type == b3.events.EVT_CLIENT_AUTH:
            if  not event.client or\
                not event.client.id or\
                event.client.cid == None or\
                not event.client.connected or\
                event.client.hide:
                return

            self.update_time_stats_connected(event.client)

        elif event.type == b3.events.EVT_CLIENT_DISCONNECT:
            self.update_time_stats_exit(event.data)

    def update_time_stats_connected(self, client):
        if self._clients.has_key(client.cid):
            self.debug(u'CTIME CONNECTED: Client exist! : %s' % client.cid)
            tmpts = self._clients[client.cid]
            if tmpts.client.guid == client.guid:
                self.debug(u'CTIME RECONNECTED: Player %s connected again, but playing since: %s' %  (client.exactName, tmpts.came))
                return
            else:
                del self._clients[client.cid]

        ts = TimeStats()
        ts.client = client
        ts.came = datetime.datetime.now()
        self._clients[client.cid] = ts
        self.debug(u'CTIME CONNECTED: Player %s started playing at: %s' % (client.exactName, ts.came))

    def formatTD(self, td):
        hours = td // 3600
        minutes = (td % 3600) // 60
        seconds = td % 60
        return '%s:%s:%s' % (hours, minutes, seconds)

    def update_time_stats_exit(self, clientid):
        self.debug(u'CTIME LEFT:')
        if self._clients.has_key(clientid):
            ts = self._clients[clientid]
            # Fail: Sometimes PB in cod4 returns 31 character guids, we need to dump them. Lets look ahead and do this for the whole codseries.
            #if(self.console.gameName[:3] == 'cod' and self.console.PunkBuster and len(ts.client.guid) != 32):
            #    pass
            #else:
            ts.left = datetime.datetime.now()
            diff = (int(time.mktime(ts.left.timetuple())) - int(time.mktime(ts.came.timetuple())))

            self.debug(u'CTIME LEFT: Player: %s played this time: %s sec' % (ts.client.exactName, diff))
            self.debug(u'CTIME LEFT: Player: %s played this time: %s' % (ts.client.exactName, self.formatTD(diff)))
            #INSERT INTO `ctime` (`guid`, `came`, `left`) VALUES ("6fcc4f6d9d8eb8d8457fd72d38bb1ed2", 1198187868, 1226081506)
            q = 'INSERT INTO %s (guid, came, gone, nick) VALUES (\"%s\", \"%s\", \"%s\", \"%s\")' % (self.ctime_table, ts.client.guid, int(time.mktime(ts.came.timetuple())), int(time.mktime(ts.left.timetuple())), ts.client.name)
            self.query(q)

            self._clients[clientid].left = None
            self._clients[clientid].came = None
            self._clients[clientid].client = None

            del self._clients[clientid]

        else:
            self.debug(u'CTIME LEFT: Player %s var not set!' % clientid)

#-----------------------------------------------------------------------------------------------------------------------
# This is an abstract class. Do not call directly.
class StatObject(object):
    _table = None

    def _insertquery(self):
        return None

    def _updatequery(self):
        return None


class PlayerStats(StatObject):
    #default name of the table for this data object
    _table = 'playerstats'

    #fields of the table
    id = None
    client_id = 0

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
        q = 'INSERT INTO %s ( client_id, kills, deaths, teamkills, teamdeaths, suicides, ratio, skill, assists, assistskill, curstreak, winstreak, losestreak, rounds, hide, fixed_name, id_token ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, "%s", "%s")' % (
            self._table, self.client_id, self.kills, self.deaths, self.teamkills, self.teamdeaths, self.suicides, self.ratio,
            self.skill, self.assists, self.assistskill, self.curstreak, self.winstreak, self.losestreak, self.rounds,
            self.hide, self.fixed_name, self.id_token)
        return q

    def _updatequery(self):
        q = 'UPDATE %s SET client_id=%s, kills=%s, deaths=%s, teamkills=%s, teamdeaths=%s, suicides=%s, ratio=%s, skill=%s, assists=%s, assistskill=%s, curstreak=%s, winstreak=%s, losestreak=%s, rounds=%s, hide=%s, fixed_name="%s", id_token="%s" WHERE id=%s' % (
            self._table, self.client_id, self.kills, self.deaths, self.teamkills, self.teamdeaths, self.suicides, self.ratio, 
            self.skill, self.assists, self.assistskill, self.curstreak, self.winstreak, self.losestreak, self.rounds,
            self.hide, self.fixed_name, self.id_token, self.id)
        return q


class WeaponStats(StatObject):
    #default name of the table for this data object
    _table = 'weaponstats'

    #fields of the table
    id = None
    name = ''
    kills = 0
    suicides = 0
    teamkills = 0

    def _insertquery(self):
        q = 'INSERT INTO %s ( name, kills, suicides, teamkills ) VALUES ("%s", %s, %s, %s)' % (
            self._table, self.name, self.kills, self.suicides, self.teamkills)
        return q

    def _updatequery(self):
        q = 'UPDATE %s SET name="%s", kills=%s, suicides=%s, teamkills=%s WHERE id=%s' % (
            self._table, self.name, self.kills, self.suicides, self.teamkills, self.id)
        return q


class WeaponUsage(StatObject):
    #default name of the table for this data object
    _table = 'weaponusage'

    #fields of the table
    id = None
    player_id = 0
    weapon_id = 0
    kills = 0
    deaths = 0
    suicides = 0
    teamkills = 0
    teamdeaths = 0

    def _insertquery(self):
        q = 'INSERT INTO %s ( player_id, weapon_id, kills, deaths, suicides, teamkills, teamdeaths ) VALUES (%s, %s, %s, %s, %s, %s, %s)' % (
            self._table, self.player_id, self.weapon_id, self.kills, self.deaths, self.suicides, self.teamkills,
            self.teamdeaths)
        return q

    def _updatequery(self):
        q = 'UPDATE %s SET player_id=%s, weapon_id=%s, kills=%s, deaths=%s, suicides=%s, teamkills=%s, teamdeaths=%s WHERE id=%s' % (
            self._table, self.player_id, self.weapon_id, self.kills, self.deaths, self.suicides, self.teamkills,
            self.teamdeaths, self.id)
        return q


class Bodyparts(StatObject):
    #default name of the table for this data object
    _table = 'bodyparts'

    #fields of the table
    id = None
    name = ''
    kills = 0
    suicides = 0
    teamkills = 0

    def _insertquery(self):
        q = 'INSERT INTO %s ( name, kills, suicides, teamkills ) VALUES ("%s", %s, %s, %s)' % (
            self._table, self.name, self.kills, self.suicides, self.teamkills)
        return q

    def _updatequery(self):
        q = 'UPDATE %s SET name="%s", kills=%s, suicides=%s, teamkills=%s WHERE id=%s' % (
            self._table, self.name, self.kills, self.suicides, self.teamkills, self.id)
        return q


class MapStats(StatObject):
    #default name of the table for this data object
    _table = 'mapstats'

    #fields of the table
    id = None
    name = ''
    kills = 0
    suicides = 0
    teamkills = 0
    rounds = 0

    def _insertquery(self):
        q = 'INSERT INTO %s ( name, kills, suicides, teamkills, rounds ) VALUES ("%s", %s, %s, %s, %s)' % (
            self._table, self.name, self.kills, self.suicides, self.teamkills, self.rounds)
        return q

    def _updatequery(self):
        q = 'UPDATE %s SET name="%s", kills=%s, suicides=%s, teamkills=%s, rounds=%s WHERE id=%s' % (
            self._table, self.name, self.kills, self.suicides, self.teamkills, self.rounds, self.id)
        return q


class PlayerBody(StatObject):
    #default name of the table for this data object
    _table = 'playerbody'

    #fields of the table
    id = None
    player_id = 0
    bodypart_id = 0
    kills = 0
    deaths = 0
    suicides = 0
    teamkills = 0
    teamdeaths = 0

    def _insertquery(self):
        q = 'INSERT INTO %s ( player_id, bodypart_id, kills, deaths, suicides, teamkills, teamdeaths ) VALUES (%s, %s, %s, %s, %s, %s, %s)' % (
            self._table, self.player_id, self.bodypart_id, self.kills, self.deaths, self.suicides, self.teamkills,
            self.teamdeaths)
        return q

    def _updatequery(self):
        q = 'UPDATE %s SET player_id=%s, bodypart_id=%s, kills=%s, deaths=%s, suicides=%s, teamkills=%s, teamdeaths=%s WHERE id=%s' % (
            self._table, self.player_id, self.bodypart_id, self.kills, self.deaths, self.suicides, self.teamkills,
            self.teamdeaths, self.id)
        return q


class PlayerMaps(StatObject):
    #default name of the table for this data object
    _table = 'playermaps'

    #fields of the table
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
        q = 'INSERT INTO %s ( player_id, map_id, kills, deaths, suicides, teamkills, teamdeaths, rounds ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)' % (
            self._table, self.player_id, self.map_id, self.kills, self.deaths, self.suicides, self.teamkills,
            self.teamdeaths, self.rounds)
        return q

    def _updatequery(self):
        q = 'UPDATE %s SET player_id=%s, map_id=%s, kills=%s, deaths=%s, suicides=%s, teamkills=%s, teamdeaths=%s, rounds=%s WHERE id=%s' % (
            self._table, self.player_id, self.map_id, self.kills, self.deaths, self.suicides, self.teamkills,
            self.teamdeaths, self.rounds, self.id)
        return q


class Opponents(StatObject):
    #default name of the table for this data object
    _table = 'opponents'

    #fields of the table
    id = None
    killer_id = 0
    target_id = 0
    kills = 0
    retals = 0

    def _insertquery(self):
        q = 'INSERT INTO %s (killer_id, target_id, kills, retals) VALUES (%s, %s, %s, %s)' % (
            self._table, self.killer_id, self.target_id, self.kills, self.retals)
        return q

    def _updatequery(self):
        q = 'UPDATE %s SET killer_id=%s, target_id=%s, kills=%s, retals=%s WHERE id=%s' % (
            self._table, self.killer_id, self.target_id, self.kills, self.retals, self.id)
        return q


class ActionStats(StatObject):
    #default name of the table for this data object
    _table = 'actionstats'

    #fields of the table
    id = None
    name = ''
    count = 0

    def _insertquery(self):
        q = 'INSERT INTO %s (name, count) VALUES ("%s", %s)' % (self._table, self.name, self.count)
        return q

    def _updatequery(self):
        q = 'UPDATE %s SET name="%s", count=%s WHERE id=%s' % (self._table, self.name, self.count, self.id)
        return q


class PlayerActions(StatObject):
    #default name of the table for this data object
    _table = 'playeractions'

    #fields of the table
    id = None
    player_id = 0
    action_id = 0
    count = 0

    def _insertquery(self):
        q = 'INSERT INTO %s ( player_id, action_id, count ) VALUES (%s, %s, %s)' % (
            self._table, self.player_id, self.action_id, self.count)
        return q

    def _updatequery(self):
        q = 'UPDATE %s SET player_id=%s, action_id=%s, count=%s WHERE id=%s' % (
            self._table, self.player_id, self.action_id, self.count, self.id)
        return q


if __name__ == '__main__':
    print '\nThis is version ' + __version__ + ' by ' + __author__ + ' for BigBrotherBot.\n'

"""\
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


# local variables:
# tab-width: 4
