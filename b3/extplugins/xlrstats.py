##################################################################
#
# XLRstats
# statistics-generating plugin for B3 (www.bigbrotherbot.net)
# (c) 2004, 2005 Tim ter Laak (ttlogic@xlr8or.com)
#
# This program is free software and licensed under the terms of
# the GNU General Public License (GPL), version 2.
#
##################################################################
# CHANGELOG
# 5/6/2008 - 0.6.0 - Mark Weirath (xlr8or@xlr8or.com)
#   Added weapon replacements
#   Added commands !xlrtopstats and !xlrhide
# 8/9/2008 - 0.6.1 - Mark Weirath (xlr8or@xlr8or.com)
#   Added onemaponly for 24/7 servers to count rounds correct
# 27/6/2009 - 0.6.5 - Mark Weirath (xlr8or@xlr8or.com)
#   No longer save worldkills
# 28/6/2009 - 1.0.0 - Mark Weirath (xlr8or@xlr8or.com)
#   Added Action classes
# 5/2/2010 - 2.0.0 - Mark Weirath (xlr8or@xlr8or.com)
#   Added Assist Bonus and History
# 21/2/2010 - 2.1.0 - Mark Weirath (xlr8or@xlr8or.com)
#   Better assist mechanism
# 23/2/2010 - 2.2.0 - Mark Weirath (xlr8or@xlr8or.com)
#   Adding table maintenance on startup
# 24/2/2010 - 2.2.1 - Mark Weirath (xlr8or@xlr8or.com)
#   Repaired self._xlrstatstables bug
# 24/2/2010 - 2.2.2 - Mark Weirath (xlr8or@xlr8or.com)
#   Repaired updateTableColumns() bug
# 24-3-2010 - 2.2.3 - Mark Weirath - Minor fix in onEvent()
# 10-8-2010 - 2.2.4 - Mark Weirath - BFBC2 adaptions (Bot Guid is Server, not WORLD) 
# 20-8-2010 - 2.2.5 - Mark Weirath
#   Allow external function call for cmd_xlrtopstats
#   Retrieve variables from webfront installation for topstats results
# 23-8-2010 - 2.2.6 - Mark Weirath
#   BugFix: Requires ConfigFile for the commands
# 3-9-2010 - 2.2.7 - Mark Weirath
#   Default action bonus set to +3 skillpoints (was 0)
# 13-10-2010 - 2.2.8 - Mark Weirath
#   BugFix: Empty field webfront Url is now allowed in config
# 08-11-2010 - 2.2.9 - Mark Weirath
#   Harden retrieval of webfront variables
# 07-01-2011 - 2.3 - Mark Weirath
#   XLRstats can now install default database tables when missing
# 07-01-2011 - 2.3.1 - Mark Weirath
#   Ability to disable plugin when not enough players are online
# 07-01-2011 - 2.3.2 - Mark Weirath
#   Update weapon tables for cod7.

# This section is DoxuGen information. More information on how to comment your code
# is available at http://wiki.bigbrotherbot.net/doku.php/customize:doxygen_rules
## @file
# XLRstats Real Time playerstats plugin

__author__  = 'Tim ter Laak / Mark Weirath'
__version__ = '2.3.2'

# Version = major.minor.patches

import string
import time
import re
import thread
import urllib2 
import b3
import b3.events
import b3.plugin

KILLER = "killer"
VICTIM = "victim"
ASSISTER = "assister"


class XlrstatsPlugin(b3.plugin.Plugin):
    requiresConfigFile = True
    
    _world_clientid = None
    _ffa = ['dm', 'ffa', 'syc-ffa']
    _damage_able_games = ['cod'] # will only count assists when damage is 50 points or more.
    _damage_ability = False
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
    minPlayers = 3 # minimum number of players to collect stats
    _currentNrPlayers = 0 # current number of players present
   
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
    history_monthly_table = 'xlr_history_monthly'
    history_weekly_table = 'xlr_history_weekly'
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
        if self._defaultTableNames:
            self.console.storage.queryFromFile("@b3/sql/xlrstats.sql", silent=True)

        # register the events we're interested in.
        self.registerEvent(b3.events.EVT_CLIENT_JOIN)
        self.registerEvent(b3.events.EVT_CLIENT_KILL)
        self.registerEvent(b3.events.EVT_CLIENT_KILL_TEAM)
        self.registerEvent(b3.events.EVT_CLIENT_SUICIDE)
        self.registerEvent(b3.events.EVT_GAME_ROUND_START)
        self.registerEvent(b3.events.EVT_CLIENT_ACTION) #for game-events/actions
        self.registerEvent(b3.events.EVT_CLIENT_DAMAGE) #for assist recognition
        
        # get the Client.id for the bot itself (guid: WORLD or Server(bfbc2))
        sclient = self.console.clients.getByGUID("WORLD")
        if sclient is None:
            sclient = self.console.clients.getByGUID("Server")
        if (sclient is not None):
            self._world_clientid = sclient.id
        self.debug('Got client id for B3: %s; %s' %(self._world_clientid, sclient.name))

        #determine the ability to work with damage based assists
        if ( self.console.gameName[:3] in self._damage_able_games ):
            self._damage_ability = True
            self.assist_timespan = self.damage_assist_release

        self._xlrstatstables = [self.playerstats_table, self.weaponstats_table, self.weaponusage_table, self.bodyparts_table, self.playerbody_table, self.opponents_table, self.mapstats_table, self.playermaps_table, self.actionstats_table, self.playeractions_table]
        if self.keep_history:
            self._xlrstatstables = [self.playerstats_table, self.weaponstats_table, self.weaponusage_table, self.bodyparts_table, self.playerbody_table, self.opponents_table, self.mapstats_table, self.playermaps_table, self.actionstats_table, self.playeractions_table, self.history_monthly_table, self.history_weekly_table]
            _tables = self.showTables(xlrstats=True)
            if ( (self.history_monthly_table in _tables) and (self.history_monthly_table in _tables) ):
                self.verbose('History Tables are present! Installing history Crontabs:')
                # remove existing crontabs
                if self._cronTabMonth:
                    self.console.cron - self._cronTabMonth
                if self._cronTabWeek:
                    self.console.cron - self._cronTabWeek
                # install crontabs
                self._cronTabMonth = b3.cron.PluginCronTab(self, self.snapshot_month, 0, 0, 0, 1, '*', '*')
                self.console.cron + self._cronTabMonth
                self._cronTabWeek = b3.cron.PluginCronTab(self, self.snapshot_week, 0, 0, 0, '*', '*', 1) # day 1 is monday
                self.console.cron + self._cronTabWeek
            else:
                self.keep_history = False
                self._xlrstatstables = [self.playerstats_table, self.weaponstats_table, self.weaponusage_table, self.bodyparts_table, self.playerbody_table, self.opponents_table, self.mapstats_table, self.playermaps_table, self.actionstats_table, self.playeractions_table]
                self.error('History Tables are NOT present! Please run b3/docs/xlrstats.sql on your database to install missing tables!')

        #check and update columns in existing tables
        self.updateTableColumns()

        #optimize xlrstats tables
        self.optimizeTables(self._xlrstatstables)

        #let's try and get some variables from our webfront installation
        if self.webfrontUrl and self.webfrontUrl != '':
            _request = str(self.webfrontUrl.rstrip('/')) + '/?config=' + str(self.webfrontConfigNr) + '&func=pluginreq'
            try:
                f = urllib2.urlopen(_request)
                _result = f.readline().split(',')
                # Our webfront will present us 3 values
                if len(_result) == 3:
                    # Force the collected strings to their final type. If an error occurs they will fail the try statement.
                    self._minKills = int(_result[0])
                    self._minRounds = int(_result[1])
                    self._maxDays = int(_result[2])
                    self.debug('Successfuly retrieved webfront variables: minkills: %i, minrounds: %i, maxdays: %i' %(self._minKills, self._minRounds, self._maxDays))
            except:
                self.debug('Couldn\'t retrieve webfront variables, using defaults')
        else:
            self.debug('No Webfront Url available, using defaults')
        
        #set proper kill_bonus and crontab
        self.calculateKillBonus()
        if self._cronTabKillBonus:
            self.console.cron - self._cronTabKillBonus
        self._cronTabKillBonus = b3.cron.PluginCronTab(self, self.calculateKillBonus, 0, '*/10')
        self.console.cron + self._cronTabKillBonus

        #start the xlrstats controller
        p = XlrstatscontrollerPlugin(self.console, self.minPlayers)
        p.startup()

        #end startup sequence

    def onLoadConfig(self):
        try:
            self.minPlayers = self.config.getint('settings', 'minplayers')
        except:
            self.debug('Using default value (%s) for settings::minplayers', self.minPlayers)

        try:
            self.webfrontUrl = self.config.get('settings', 'webfronturl')    
        except:
            self.debug('Using default value (%s) for settings::webfronturl', self.webfrontUrl)

        try:
            self.webfrontConfigNr = self.config.getint('settings', 'servernumber')    
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
            self.minlevel = self.config.getint('settings', 'minlevel')    
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
            self.playerstats_table = self.config.get('tables', 'playerstats')
            self._defaultTableNames = False
        except:
            self.debug('Using default value (%s) for tables::playerstats', self.playerstats_table)

        try:
            self.weaponstats_table = self.config.get('tables', 'weaponstats')
            self._defaultTableNames = False
        except:
            self.debug('Using default value (%s) for tables::weaponstats', self.weaponstats_table)
            
        try:
            self.weaponusage_table = self.config.get('tables', 'weaponusage')
            self._defaultTableNames = False
        except:
            self.debug('Using default value (%s) for tables::weaponusage', self.weaponusage_table)
            
        try:
            self.bodyparts_table = self.config.get('tables', 'bodyparts')
            self._defaultTableNames = False
        except:
            self.debug('Using default value (%s) for tables::bodyparts', self.bodyparts_table)
           
        try:
            self.playerbody_table = self.config.get('tables', 'playerbody')
            self._defaultTableNames = False
        except:
            self.debug('Using default value (%s) for tables::playerbody', self.playerbody_table)
            
        try:
            self.opponents_table = self.config.get('tables', 'opponents')
            self._defaultTableNames = False
        except:
            self.debug('Using default value (%s) for tables::opponents', self.opponents_table)
            
        try:
            self.mapstats_table = self.config.get('tables', 'mapstats')
            self._defaultTableNames = False
        except:
            self.debug('Using default value (%s) for tables::mapstats', self.mapstats_table)
            
        try:
            self.playermaps_table = self.config.get('tables', 'playermaps')
            self._defaultTableNames = False
        except:
            self.debug('Using default value (%s) for tables::playermaps', self.playermaps_table)
                      
        try:
            self.actionstats_table = self.config.get('tables', 'actionstats')
            self._defaultTableNames = False
        except:
            self.debug('Using default value (%s) for tables::actionstats', self.actionstats_table)

        try:
            self.playeractions_table = self.config.get('tables', 'playeractions')
            self._defaultTableNames = False
        except:
            self.debug('Using default value (%s) for tables::playeractions', self.playeractions_table)

        #history tables
        try:
            self.history_monthly_table = self.config.get('tables', 'history_monthly')    
            self._defaultTableNames = False
        except:
            self.history_monthly_table = 'xlr_history_monthly'
            self.debug('Using default value (%s) for tables::history_monthly', self.history_monthly_table)

        try:
            self.history_weekly_table = self.config.get('tables', 'history_weekly')    
            self._defaultTableNames = False
        except:
            self.history_weekly_table = 'xlr_history_weekly'
            self.debug('Using default value (%s) for tables::history_weekly', self.history_weekly_table)

        return
    

    def getCmd(self, cmd):
        cmd = 'cmd_%s' % cmd
        if hasattr(self, cmd):
            func = getattr(self, cmd)
            return func
    
        return None


    def onEvent(self, event):

        if (event.type == b3.events.EVT_CLIENT_JOIN):
            self.join(event.client)
        elif (event.type == b3.events.EVT_CLIENT_KILL):
            self.kill(event.client, event.target, event.data)
        elif (event.type == b3.events.EVT_CLIENT_KILL_TEAM):
            if self.console.game.gameType in self._ffa:
                self.kill(event.client, event.target, event.data)
            else:
                self.teamkill(event.client, event.target, event.data)
        elif (event.type == b3.events.EVT_CLIENT_DAMAGE):
            self.damage(event.client, event.target, event.data)
        elif (event.type == b3.events.EVT_CLIENT_SUICIDE):
            self.suicide(event.client, event.target, event.data)
        elif (event.type == b3.events.EVT_GAME_ROUND_START):
            self.roundstart()
        elif (event.type == b3.events.EVT_CLIENT_ACTION):
            self.action(event.client, event.data)
        else:       
            self.dumpEvent(event)


    def dumpEvent(self, event):
        self.debug('xlrstats.dumpEvent -- Type %s, Client %s, Target %s, Data %s',
            event.type, event.client, event.target, event.data)
        
    def win_prob(self, player_skill, opponent_skill):    
        return ( 1 / ( 10 ** ( (opponent_skill - player_skill) / self.steepness ) + 1 ) )
     
     
    # Retrieves an existing stats record for given client,
    # or makes a new one IFF client's level is high enough
    # Otherwise (also on error), it returns None.
    def get_PlayerStats(self, client=None):
        if (client is None):
            id = self._world_clientid
        else:
            id = client.id
        q = 'SELECT * from %s WHERE client_id = %s LIMIT 1' % (self.playerstats_table, id)
        cursor = self.query(q)
        if (cursor and (cursor.rowcount > 0) ):
            r = cursor.getRow()
            s = PlayerStats()
            s.id = r['id']
            s.client_id = r['client_id']
            s.kills = r['kills']
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
            return s
        elif ( (client is None) or (client.maxLevel >= self.minlevel) ):
            s = PlayerStats()
            s._new = True
            s.skill = self.defaultskill
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
        if (cursor and (cursor.rowcount > 0) ):
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
        if (cursor and (cursor.rowcount > 0) ):
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
        if (cursor and (cursor.rowcount > 0) ):
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
        q = 'SELECT * from %s WHERE weapon_id = %s AND player_id = %s LIMIT 1' % (self.weaponusage_table, weaponid, playerid)
        cursor = self.query(q)
        if (cursor and (cursor.rowcount > 0) ):
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
        q = 'SELECT * from %s WHERE killer_id = %s AND target_id = %s LIMIT 1' % (self.opponents_table, killerid, targetid)
        cursor = self.query(q)
        if (cursor and (cursor.rowcount > 0) ):
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
        q = 'SELECT * from %s WHERE bodypart_id = %s AND player_id = %s LIMIT 1' % (self.playerbody_table, bodypartid, playerid)
        cursor = self.query(q)
        if (cursor and (cursor.rowcount > 0) ):
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
        s = PlayerMaps()
        q = 'SELECT * from %s WHERE map_id = %s AND player_id = %s LIMIT 1' % (self.playermaps_table, mapid, playerid)
        cursor = self.query(q)
        if (cursor and (cursor.rowcount > 0) ):
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
        if (cursor and (cursor.rowcount > 0) ):
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
        q = 'SELECT * from %s WHERE action_id = %s AND player_id = %s LIMIT 1' % (self.playeractions_table, actionid, playerid)
        cursor = self.query(q)
        if (cursor and (cursor.rowcount > 0) ):
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
            #self.debug('Inserting using: ', q)
            cursor = self.query(q)
            if (cursor.rowcount > 0):
                stat.id = cursor.lastrowid
                delattr(stat, '_new')
        else:
            q = stat._updatequery()
            #self.debug('Updating using: ', q)
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
        self.verbose('----> XLRstats: %s Killed %s (%s), checking for assists' %(client.name, target.name, etype))

        try:
            ainfo = target._attackers
        except:
            target._attackers = {}
            ainfo = target._attackers

        for k, v in ainfo.iteritems():
            if (k == client.cid):
                #don't award the killer for the assist aswell
                continue
            elif (time.time() - v < self.assist_timespan):
                assister = self.console.clients.getByCID(k)
                self.verbose('----> XLRstats: assister = %s' %(assister.name))

                anonymous = None
               
                victimstats = self.get_PlayerStats(target)
                assiststats = self.get_PlayerStats(assister)

                # if both should be anonymous, we have no work to do
                if ( (assiststats is None) and (victimstats is None) ):
                    self.verbose('----> XLRstats: check_Assists: %s & %s both anonymous, continueing' %(assister.name, target.name))
                    continue
                    
                if (victimstats == None):
                    anonymous = VICTIM
                    victimstats = self.get_PlayerAnon()
                    if (victimstats == None):
                        continue

                if (assiststats == None):
                    anonymous = ASSISTER
                    assiststats = self.get_PlayerAnon()
                    if (assiststats == None):
                        continue

                #calculate the win probability for the assister and victim
                assist_prob = self.win_prob(assiststats.skill, victimstats.skill)
                victim_prob = self.win_prob(victimstats.skill, assiststats.skill)
                self.verbose('----> XLRstats: win probability for %s: %s' %(assister.name, assist_prob))
                self.verbose('----> XLRstats: win probability for %s: %s' %(target.name, victim_prob))

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
                if ( anonymous != ASSISTER ):
                    if (assiststats.kills > self.Kswitch_kills):
                        Kfactor = self.Kfactor_low
                    else:
                        Kfactor = self.Kfactor_high
    
                    oldskill = assiststats.skill
                    if (( target.team == assister.team ) and not ( self.console.game.gameType in self._ffa )):
                        #assister is a teammate and needs skill and assists reduced
                        _assistbonus = self.assist_bonus * Kfactor * weapon_factor * (0-assist_prob)
                        assiststats.skill = float(assiststats.skill) + _assistbonus
                        assiststats.assistskill = float(assiststats.assistskill) + _assistbonus
                        assiststats.assists -= 1 #negative assist
                        self.verbose('----> XLRstats: Assistpunishment deducted for %s: %s (oldsk: %.3f - newsk: %.3f)' %(assister.name, assiststats.skill-oldskill, oldskill, assiststats.skill))
                        _count += 1
                        _sum += _assistbonus
                        if self.announce and not assiststats.hide:
                            assister.message('^5XLRstats:^7 Teamdamaged (%s) -> skill: ^1%.3f^7 -> ^2%.1f^7' %(target.name, assiststats.skill-oldskill, assiststats.skill))
                    else:
                        #this is a real assist
                        _assistbonus = self.assist_bonus * Kfactor * weapon_factor * (1-assist_prob)
                        assiststats.skill = float(assiststats.skill) + _assistbonus
                        assiststats.assistskill = float(assiststats.assistskill) + _assistbonus
                        assiststats.assists += 1
                        self.verbose('----> XLRstats: Assistbonus awarded for %s: %s (oldsk: %.3f - newsk: %.3f)' %(assister.name, assiststats.skill-oldskill, oldskill, assiststats.skill))
                        _count += 1
                        _sum += _assistbonus
                        if self.announce and not assiststats.hide:
                            assister.message('^5XLRstats:^7 Assistbonus (%s) -> skill: ^2+%.3f^7 -> ^2%.1f^7' %(target.name, assiststats.skill-oldskill, assiststats.skill))
                    self.save_Stat(assiststats)

                #calculate new skill for the victim
                if (anonymous != VICTIM):
                    if (victimstats.kills > self.Kswitch_kills):
                        Kfactor = self.Kfactor_low
                    else:
                        Kfactor = self.Kfactor_high
    
                    oldskill = victimstats.skill
                    if (( target.team == assister.team ) and not ( self.console.game.gameType in self._ffa )):
                        #assister was a teammate, this should not affect victims skill.
                        pass
                    else:
                        #this is a real assist
                        _assistdeduction = self.assist_bonus * Kfactor * weapon_factor * (0-victim_prob)
                        victimstats.skill = float(victimstats.skill) + _assistdeduction
                        self.verbose('----> XLRstats: Assist skilldeduction for %s: %s (oldsk: %.3f - newsk: %.3f)' %(target.name, victimstats.skill-oldskill, oldskill, victimstats.skill))
                        _vsum += _assistdeduction
                    self.save_Stat(victimstats)

        #end of assist reward function, return the number of assists 
        return _count, _sum, _vsum

    def kill(self, client, target, data):
        if (client == None) or (client.id == self._world_clientid):
            return
        if (target == None):
            return
        if (data == None):
            return
            
        _assists_count, _assists_sum, _victim_sum = self.check_Assists(client, target, data, 'kill')

        anonymous = None
       
        killerstats = self.get_PlayerStats(client)
        victimstats = self.get_PlayerStats(target)

        # if both should be anonymous, we have no work to do
        if ( (killerstats is None) and (victimstats is None) ):
            return
            
        if (killerstats == None):
            anonymous = KILLER
            killerstats = self.get_PlayerAnon()
            if (killerstats is None):
                return
            killerstats.skill = self.defaultskill
                
        if (victimstats == None):
            anonymous = VICTIM
            victimstats = self.get_PlayerAnon()
            if (victimstats == None):
                return

        #calculate winning probabilities for both players
        killer_prob = self.win_prob(killerstats.skill, victimstats.skill)
        victim_prob = self.win_prob(victimstats.skill, killerstats.skill)

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
        if ( anonymous != KILLER ):
            if (killerstats.kills > self.Kswitch_kills):
                Kfactor = self.Kfactor_low
            else:
                Kfactor = self.Kfactor_high
                
            oldskill = killerstats.skill
            #pure skilladdition for a 100% kill
            _skilladdition = self.kill_bonus * Kfactor * weapon_factor * (1-killer_prob)
            #deduct the assists from the killers skill, but no more than 50%
            if ( _assists_sum == 0 ):
                pass
            elif (_assists_sum >= ( _skilladdition / 2 )):
                _skilladdition /= 2
                self.verbose('----> XLRstats: Killer: assists > 50perc: %.3f - skilladd: %.3f' %(_assists_sum, _skilladdition))
            else:
                _skilladdition -= _assists_sum
                self.verbose('----> XLRstats: Killer: assists < 50perc: %.3f - skilladd: %.3f' %(_assists_sum, _skilladdition))

            killerstats.skill = float(killerstats.skill) + _skilladdition
            self.verbose('----> XLRstats: Killer: oldsk: %.3f - newsk: %.3f' %(oldskill, killerstats.skill))
            killerstats.kills = int(killerstats.kills) + 1
 
            if ( int(killerstats.deaths) != 0):
                killerstats.ratio = float(killerstats.kills) / float(killerstats.deaths)
            else:
                killerstats.ratio = 0.0

            if ( int(killerstats.curstreak) > 0):
                killerstats.curstreak = int(killerstats.curstreak) + 1
            else:
                killerstats.curstreak = 1

            if ( int(killerstats.curstreak) > int(killerstats.winstreak) ):
                killerstats.winstreak = int(killerstats.curstreak)
            else:
                killerstats.winstreak = int(killerstats.winstreak)        
        
            if self.announce and not killerstats.hide:
                client.message('^5XLRstats:^7 Killed %s -> skill: ^2+%.3f^7 -> ^2%.1f^7' %(target.name, (killerstats.skill-oldskill), killerstats.skill))
            self.save_Stat(killerstats)

        #calculate new stats for the victim
        if (anonymous != VICTIM):
            if (victimstats.kills > self.Kswitch_kills):
                Kfactor = self.Kfactor_low
            else:
                Kfactor = self.Kfactor_high    
                
            oldskill = victimstats.skill

            #pure skilldeduction for a 100% kill
            _skilldeduction = Kfactor * weapon_factor * (0-victim_prob)
            #deduct the assists from the victims skill deduction, but no more than 50%
            if ( _victim_sum == 0 ):
                pass
            elif ( _victim_sum <= ( _skilldeduction / 2 )): #carefull, negative numbers here
                _skilldeduction /= 2
                self.verbose('----> XLRstats: Victim: assists > 50perc: %.3f - skilldeduct: %.3f' %( _victim_sum, _skilldeduction))
            else:
                _skilldeduction -=  _victim_sum
                self.verbose('----> XLRstats: Victim: assists < 50perc: %.3f - skilldeduct: %.3f' %( _victim_sum, _skilldeduction))

            victimstats.skill = float(victimstats.skill) + _skilldeduction
            self.verbose('----> XLRstats: Victim: oldsk: %.3f - newsk: %.3f' %(oldskill, victimstats.skill))
            victimstats.deaths = int(victimstats.deaths) + 1

            victimstats.ratio = float(victimstats.kills) / float(victimstats.deaths)

            if ( int(victimstats.curstreak) < 0):
                victimstats.curstreak = int(victimstats.curstreak) - 1
            else:
                victimstats.curstreak = -1

            if ( victimstats.curstreak < int(victimstats.losestreak) ):
                victimstats.losestreak = victimstats.curstreak
            else:
                victimstats.losestreak = int(victimstats.losestreak)        
        
            if self.announce and not victimstats.hide:
                target.message('^5XLRstats:^7 Killed by %s -> skill: ^1%.3f^7 -> ^2%.1f^7' %(client.name, (victimstats.skill-oldskill), victimstats.skill))
            self.save_Stat(victimstats)

        #make sure the record for anonymous is really created with an insert once
        if (anonymous):
            if ( (anonymous == KILLER) and (hasattr(killerstats, '_new')) ):
                self.save_Stat(killerstats)
            elif ( (anonymous == VICTIM) and (hasattr(victimstats, '_new')) ):
                self.save_Stat(victimstats)  
        
        #adjust the "opponents" table to register who killed who
        opponent = self.get_Opponent(targetid=victimstats.id, killerid=killerstats.id)
        retal = self.get_Opponent(targetid=killerstats.id, killerid=victimstats.id)
        #the above should always succeed, but you never know...
        if (opponent and retal):
            opponent.kills += 1
            retal.retals += 1
            self.save_Stat(opponent)
            self.save_Stat(retal)
            
        #adjust weapon statistics
        weaponstats = self.get_WeaponStats(name=actualweapon)
        if (weaponstats):
            weaponstats.kills += 1
            self.save_Stat(weaponstats)
            
            w_usage_killer = self.get_WeaponUsage(playerid=killerstats.id, weaponid=weaponstats.id)
            w_usage_victim = self.get_WeaponUsage(playerid=victimstats.id, weaponid=weaponstats.id)
            if (w_usage_killer and w_usage_victim):
                w_usage_killer.kills += 1
                w_usage_victim.deaths += 1
                self.save_Stat(w_usage_killer)
                self.save_Stat(w_usage_victim)
        
        #adjust bodypart statistics
        bodypart = self.get_Bodypart(name=data[2])
        if (bodypart):
            bodypart.kills += 1
            self.save_Stat(bodypart)
         
            bp_killer = self.get_PlayerBody(playerid=killerstats.id, bodypartid=bodypart.id)
            bp_victim = self.get_PlayerBody(playerid=victimstats.id, bodypartid=bodypart.id)
            if (bp_killer and bp_victim):
                bp_killer.kills += 1
                bp_victim.deaths += 1
                self.save_Stat(bp_killer)
                self.save_Stat(bp_victim)

        #adjust map statistics
        map = self.get_MapStats(self.console.game.mapName)
        if (map):
            map.kills += 1
            self.save_Stat(map)
            
            map_killer = self.get_PlayerMaps(playerid=killerstats.id, mapid=map.id)
            map_victim = self.get_PlayerMaps(playerid=victimstats.id, mapid=map.id)
            if (map_killer and map_victim):
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
        if (client.cid == target.cid):
            self.verbose('----> XLRstats: onDamage: self damage: %s damaged %s, continueing' %(client.name, target.name))
            return None

        #check if game is _damage_able -> 50 points or more damage will award an assist
        if ( self._damage_ability and data[0] < 50 ):
            self.verbose('---> XLRstats: Not enough damage done to award an assist')
            return

        try:
            target._attackers[client.cid] = time.time()
        except:
            target._attackers = {}
            target._attackers[client.cid] = time.time()
        self.verbose('----> XLRstats: onDamage: attacker added: %s (%s) damaged %s (%s)' %(client.name, client.cid, target.name, target.cid))
        self.verbose('----> XLRstats: Assistinfo: %s' %(target._attackers))

    def suicide(self, client, target, data):
        if (client == None):
            return
        if (target == None):
            return
        if (data == None):
            return

        self.check_Assists(client, target, data, 'suicide')

        playerstats = self.get_PlayerStats(client)

        if (playerstats is None):
            #anonymous player. We're not interested :)
            return
        
        playerstats.suicides += 1
        if ( playerstats.curstreak < 0):
            playerstats.curstreak -= 1
        else:
            playerstats.curstreak = -1
        if ( playerstats.curstreak < playerstats.losestreak ):
            playerstats.losestreak = playerstats.curstreak
        
        oldskill = playerstats.skill
        playerstats.skill = (1 - (self.suicide_penalty_percent / 100.0) ) * float(playerstats.skill)
        if self.announce and not playerstats.hide:
            client.message('^5XLRstats:^7 Suicide -> skill: ^1%.3f^7 -> ^2%.1f^7' %(playerstats.skill-oldskill, playerstats.skill))
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
        if (weaponstats):
            weaponstats.suicides += 1
            self.save_Stat(weaponstats)
            
            w_usage = self.get_WeaponUsage(playerid=playerstats.id, weaponid=weaponstats.id)
            if (w_usage):
                w_usage.suicides += 1
                self.save_Stat(w_usage)
                
        #update bodypart stats
        bodypart = self.get_Bodypart(name=data[2])
        if (bodypart):
            bodypart.suicides += 1
            self.save_Stat(bodypart)
            
            bp_player = self.get_PlayerBody(playerid=playerstats.id, bodypartid=bodypart.id)
            if(bp_player):
                bp_player.suicides = int(bp_player.suicides) + 1
                self.save_Stat(bp_player)

        #adjust map statistics
        map = self.get_MapStats(self.console.game.mapName)
        if (map):
            map.suicides += 1
            self.save_Stat(map)
            
            map_player = self.get_PlayerMaps(playerid=playerstats.id, mapid=map.id)
            if (map_player):
                map_player.suicides += 1
                self.save_Stat(map_player)

        #end of function suicide
        return
        
    def teamkill(self, client, target, data):
        if (client == None):
            return
        if (target == None):
            return
        if (data == None):
            return

        anonymous = None

        self.check_Assists(client, target, data, 'teamkill')

        killerstats = self.get_PlayerStats(client)
        victimstats = self.get_PlayerStats(target)

        # if both should be anonymous, we have no work to do
        if ( (killerstats is None) and (victimstats is None) ):
            return

        if (killerstats == None):
            anonymous = KILLER
            killerstats = self.get_PlayerAnon()
            if (killerstats is None):
                return
            killerstats.skill = self.defaultskill
                
        if (victimstats == None):
            anonymous = VICTIM
            victimstats = self.get_PlayerAnon()
            if (victimstats == None):
                return
            victimstats.skill = self.defaultskill

        if (anonymous != KILLER):
            #Calculate new stats for the killer
            oldskill = killerstats.skill
            killerstats.skill = (1 - (self.tk_penalty_percent / 100.0) ) * float(killerstats.skill) 
            killerstats.teamkills += 1
            killerstats.curstreak = 0   # break off current streak as it is now "impure"
            if self.announce and not killerstats.hide:
                client.message('^5XLRstats:^7 Teamkill -> skill: ^1%.3f^7 -> ^2%.1f^7' %(killerstats.skill-oldskill, killerstats.skill))
            self.save_Stat(killerstats)

        if (anonymous !=VICTIM):
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
        if (weaponstats):
            weaponstats.teamkills += 1
            self.save_Stat(weaponstats)
            
            w_usage_killer = self.get_WeaponUsage(playerid=killerstats.id, weaponid=weaponstats.id)
            w_usage_victim = self.get_WeaponUsage(playerid=victimstats.id, weaponid=weaponstats.id)
            if (w_usage_killer and w_usage_victim):
                w_usage_killer.teamkills += 1
                w_usage_victim.teamdeaths += 1
                self.save_Stat(w_usage_killer)
                self.save_Stat(w_usage_victim)
        
        #adjust bodypart statistics
        bodypart = self.get_Bodypart(name=data[2])
        if (bodypart):
            bodypart.teamkills += 1
            self.save_Stat(bodypart)

            bp_killer = self.get_PlayerBody(playerid=killerstats.id, bodypartid=bodypart.id)
            bp_victim = self.get_PlayerBody(playerid=victimstats.id, bodypartid=bodypart.id)
            if (bp_killer and bp_victim):
                bp_killer.teamkills += 1
                bp_victim.teamdeaths += 1
                self.save_Stat(bp_killer)
                self.save_Stat(bp_victim)
           
        #adjust map statistics
        map = self.get_MapStats(self.console.game.mapName)
        if (map):
            map.teamkills += 1
            self.save_Stat(map)
            
            map_killer = self.get_PlayerMaps(playerid=killerstats.id, mapid=map.id)
            map_victim = self.get_PlayerMaps(playerid=victimstats.id, mapid=map.id)
            if (map_killer and map_victim):
                map_killer.teamkills += 1
                map_victim.teamdeaths += 1
                self.save_Stat(map_killer)
                self.save_Stat(map_victim)
            
        #end of function teamkill
        return
            
            
    def join(self, client):
        if (client == None):
            return

        player = self.get_PlayerStats(client)
        if (player):
            player.rounds = int(player.rounds) + 1
            self.save_Stat(player)
            
            map = self.get_MapStats(self.console.game.mapName)
            if (map):
                playermap = self.get_PlayerMaps(player.id, map.id)
                if (playermap):
                    playermap.rounds += 1
                    self.save_Stat(playermap)
        return

    def roundstart(self):
        #disable k/d counting if minimum players are not met

        if ( self.last_map == None):
            self.last_map = self.console.game.mapName
            #self.last_roundtime = self.console.game._roundTimeStart
        else:
            if ( not self.onemaponly and ( self.last_map == self.console.game.mapName) and  (self.console.game.roundTime() < self.prematch_maxtime) ):
                #( self.console.game._roundTimeStart - self.last_roundtime < self.prematch_maxtime) ):
                return
            else:
                self.last_map = self.console.game.mapName
                #self.last_roundtime = self.console.game._roundTimeStart

        map = self.get_MapStats(self.console.game.mapName)
        if (map):
            map.rounds += 1
            self.save_Stat(map)

        return

    def action(self, client, data):
        #self.verbose('----> XLRstats: Entering actionfunc.')
        if client == None:
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
        if playerstats == None:
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
                message = '^3XLR Stats: ^7%s ^7: K ^2%s ^7D ^3%s ^7TK ^1%s ^7Ratio ^5%1.02f ^7Skill ^3%1.02f' % (sclient.exactName, stats.kills, stats.deaths, stats.teamkills, stats.ratio, stats.skill)
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


        #q = 'SELECT `%s`.name, `%s`.time_edit, `%s`.id, kills, deaths, ratio, skill, winstreak, losestreak, rounds, fixed_name, ip FROM `%s`, `%s` WHERE (`%s`.id = `%s`.client_id) AND ((`%s`.kills > 100) OR (`%s`.rounds > 10)) AND (`%s`.hide = 0) AND (UNIX_TIMESTAMP(NOW()) - `%s`.time_edit  < 14*60*60*24) AND `%s`.id NOT IN ( SELECT distinct(target.id) FROM `%s` as penalties, `%s` as target WHERE (penalties.type = "Ban" OR penalties.type = "TempBan") AND inactive = 0 AND penalties.client_id = target.id AND ( penalties.time_expire = -1 OR penalties.time_expire > UNIX_TIMESTAMP(NOW()) ) ) ORDER BY `%s`.`skill` DESC LIMIT %s' % (self.clients_table, self.clients_table, self.playerstats_table, self.clients_table, self.playerstats_table, self.clients_table, self.playerstats_table, self.playerstats_table, self.playerstats_table, self.playerstats_table, self.clients_table, self.clients_table, self.penalties_table, self.clients_table, self.playerstats_table, limit)
        q = 'SELECT `%s`.name, `%s`.time_edit, `%s`.id, kills, deaths, ratio, skill, winstreak, losestreak, rounds, fixed_name, ip \
        FROM `%s`, `%s` \
            WHERE (`%s`.id = `%s`.client_id) \
            AND ((`%s`.kills > %s) \
            OR (`%s`.rounds > %s)) \
            AND (`%s`.hide = 0) \
            AND (UNIX_TIMESTAMP(NOW()) - `%s`.time_edit  < %s*60*60*24) \
            AND `%s`.id NOT IN \
                ( SELECT distinct(target.id) FROM `%s` as penalties, `%s` as target \
                WHERE (penalties.type = "Ban" \
                OR penalties.type = "TempBan") \
                AND inactive = 0 \
                AND penalties.client_id = target.id \
                AND ( penalties.time_expire = -1 \
                OR penalties.time_expire > UNIX_TIMESTAMP(NOW()) ) ) \
        ORDER BY `%s`.`skill` DESC LIMIT %s' \
        % (self.clients_table, self.clients_table, self.playerstats_table, self.clients_table, self.playerstats_table, \
        self.clients_table, self.playerstats_table, self.playerstats_table, self._minKills, self.playerstats_table, \
        self._minRounds, self.playerstats_table, self.clients_table, self._maxDays, self.clients_table, self.penalties_table, \
        self.clients_table, self.playerstats_table, limit)

        cursor = self.query(q)
        if (cursor and (cursor.rowcount > 0) ):
            message = '^3XLR Stats Top %s Players:' % (limit)
            if ext:
                self.console.say(message)
            else:
                cmd.sayLoudOrPM(client, message)
            c = 1
            while not cursor.EOF:
                r = cursor.getRow()
                message = '^3# %s: ^7%s ^7: Skill ^3%1.02f ^7Ratio ^5%1.02f ^7Kills: ^2%s' % (c, r['name'], r['skill'], r['ratio'], r['kills'])
                if ext:
                    self.console.say(message)
                else:
                    cmd.sayLoudOrPM(client, message)
                cursor.moveNext()
                c += 1
                time.sleep(1)
        else:
            self.debug('No players qualified for the toplist yet...')
            message = 'Qualify for the toplist by making %i kills, or playing %i rounds!' % (self._minKills, self._minRounds)
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
    
        if not len(input[1]):
            client.message('^7Missing data, try !help xlrhide')
            return False
        
        m = input[1]
        if m in ('on','1'):
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
        if (player):
            player.hide = int(hide)
            self.save_Stat(player)
            
        return

    def snapshot_month(self):
        sql = ('INSERT INTO ' + self.history_monthly_table + ' (`client_id` , `kills` , `deaths` , `teamkills` , `teamdeaths` , `suicides` ' +
            ', `ratio` , `skill` , `assists` , `assistskill` , `winstreak` , `losestreak` , `rounds`, `year`, `month`, `week`, `day`)' +
            '  SELECT `client_id` , `kills`, `deaths` , `teamkills` , `teamdeaths` , `suicides` , `ratio` , `skill` , `assists` , `assistskill` , `winstreak` ' +
            ', `losestreak` , `rounds`, YEAR(NOW()), MONTH(NOW()), WEEK(NOW(),3), DAY(NOW())' + 
            '  FROM `' + PlayerStats._table + '`' )
        try:
            self.query(sql, silent=True)
            self.verbose('Monthly XLRstats snapshot created')
        except Exception, msg:
            self.error('Creating history snapshot failed: %s' %msg)
   
    def snapshot_week(self):
        sql = ('INSERT INTO ' + self.history_weekly_table + ' (`client_id` , `kills` , `deaths` , `teamkills` , `teamdeaths` , `suicides` ' +
            ', `ratio` , `skill` , `assists` , `assistskill` , `winstreak` , `losestreak` , `rounds`, `year`, `month`, `week`, `day`)' +
            '  SELECT `client_id` , `kills`, `deaths` , `teamkills` , `teamdeaths` , `suicides` , `ratio` , `skill` , `assists` , `assistskill` , `winstreak` ' +
            ', `losestreak` , `rounds`, YEAR(NOW()), MONTH(NOW()), WEEK(NOW(),3), DAY(NOW())' + 
            '  FROM `' + PlayerStats._table + '`' )
        try:
            self.query(sql, silent=True)
            self.verbose('Weekly XLRstats snapshot created')
        except Exception, msg:
            self.error('Creating history snapshot failed: %s' %msg)

    def updateTableColumns(self):
        self.verbose('Checking if we need to update tables for version 2.0.0')
        #todo: add mysql condition
        #v2.0.0 additions to the playerstats table:
        self._addTableColumn('assists', PlayerStats._table, 'MEDIUMINT( 8 ) NOT NULL DEFAULT "0" AFTER `skill`')
        self._addTableColumn('assistskill', PlayerStats._table, 'FLOAT NOT NULL DEFAULT "0" AFTER `assists`')
        #alterations to columns in existing tables:
        self._updateTableColumns()
        return None
        #end of update check

    def _addTableColumn(self, c1, t1, specs):
        try:
            self.query('SELECT `%s` FROM %s limit 1;' %(c1, t1), silent=True)
        except Exception, e:
            if e[0] == 1054:
                self.console.debug('Column does not yet exist: %s' % (e))
                self.query('ALTER TABLE %s ADD `%s` %s ;' %(t1, c1, specs))
                self.console.info('Created new column `%s` on %s' %(c1, t1))
            else:
                self.console.error('Query failed - %s: %s' % (type(e), e))

    def _updateTableColumns(self):
        try:
            #need to update the weapon-identifier columns in these tables for cod7. This game knows over 255 weapons/variations
            self.query('ALTER TABLE  `%s` CHANGE  `id`  `id` SMALLINT( 5 ) UNSIGNED NOT NULL AUTO_INCREMENT;' %(WeaponStats._table))
            self.query('ALTER TABLE  `%s` CHANGE  `weapon_id`  `weapon_id` SMALLINT( 5 ) UNSIGNED NOT NULL DEFAULT  "0";' %(WeaponUsage._table))
        except:
            pass

    def showTables(self, xlrstats=False):
        _tables = []
        q = 'SHOW TABLES'
        cursor = self.query(q)
        if (cursor and (cursor.rowcount > 0) ):
            while not cursor.EOF:
                r = cursor.getRow()
                n = str(r.values()[0])
                if xlrstats and not n in self._xlrstatstables:
                    pass
                else:
                    _tables.append(r.values()[0])
                cursor.moveNext()
        if xlrstats:
            self.console.verbose('Available XLRstats tables in this database: %s' %_tables)
        else:
            self.console.verbose('Available tables in this database: %s' %_tables)
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
            self.query('OPTIMIZE TABLE %s' % _tables )
            self.debug('Optimize Success')
        except Exception, msg:
            self.error('Optimizing Table(s) Failed: %s, trying to repair...' %msg)
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
            self.query('REPAIR TABLE %s' % _tables )
            self.debug('Repair Success')
        except Exception, msg:
            self.error('Repairing Table(s) Failed: %s' %msg)

    def calculateKillBonus(self):
        self.debug('Calculating kill_bonus')
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
            self.kill_bonus = round(c,1)
        self.assist_bonus = self.kill_bonus/3
        if self.kill_bonus != _oldkillbonus:
            self.debug('kill_bonus set to: %s' % self.kill_bonus)
            self.debug('assist_bonus set to: %s' % self.assist_bonus)


class XlrstatscontrollerPlugin(b3.plugin.Plugin):
    """This is a helper class/plugin that enables and disables the main xlrstats plugin"""

    def __init__(self, console, minPlayers=3):
        self.console = console
        self.minPlayers = minPlayers
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
        if (event.type == b3.events.EVT_CLIENT_JOIN):
            self.checkMinPlayers()
        elif (event.type == b3.events.EVT_GAME_ROUND_START):
            self.checkMinPlayers(_roundstart=True)

    def checkMinPlayers(self, _roundstart=False):
        """Checks if minimum amount of players are present
        if minimum amount of players is reached will enable stats collecting
        and if not it disables stats counting on next roundstart"""
        self._currentNrPlayers = len(self.console.clients.getList())
        self.debug('Checking number of players online. Minimum = %s, Current = %s' %(self.minPlayers, self._currentNrPlayers) )
        if self._currentNrPlayers < self.minPlayers and self._xlrstatsPlugin.isEnabled() and _roundstart:
            self.info('Disabling XLRstats: Not enough players online')
            self.console.say('XLRstats Disabled: Not enough players online!')
            self._xlrstatsPlugin.disable()
        elif self._currentNrPlayers >= self.minPlayers and not self._xlrstatsPlugin.isEnabled():
            self.info('Enabling XLRstats: Collecting Stats')
            self.console.say('XLRstats Enabled: Now collecting stats!')
            self._xlrstatsPlugin.enable()
        else:
            if self._xlrstatsPlugin.isEnabled():
                _status = 'Enabled'
            else:
                _status = 'Disabled'
            self.debug('Nothing to do at the moment. XLRstats is already %s' %(_status) )


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

    def _insertquery(self):
        q = 'INSERT INTO %s ( client_id, kills, deaths, teamkills, teamdeaths, suicides, ratio, skill, assists, assistskill, curstreak, winstreak, losestreak, rounds, hide ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)' % (self._table, self.client_id, self.kills, self.deaths,  self.teamkills, self.teamdeaths, self.suicides, self.ratio, self.skill, self.assists, self.assistskill, self.curstreak, self.winstreak, self.losestreak, self.rounds, self.hide)
        return q
        
    def _updatequery(self):
        q = 'UPDATE %s SET client_id=%s, kills=%s, deaths=%s, teamkills=%s, teamdeaths=%s, suicides=%s, ratio=%s, skill=%s, assists=%s, assistskill=%s, curstreak=%s, winstreak=%s, losestreak=%s, rounds=%s, hide=%s WHERE id=%s' % (self._table, self.client_id, self.kills, self.deaths, self.teamkills, self.teamdeaths, self.suicides, self.ratio, self.skill, self.assists, self.assistskill, self.curstreak, self.winstreak, self.losestreak, self.rounds, self.hide, self.id)
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
        q = 'INSERT INTO %s ( name, kills, suicides, teamkills ) VALUES ("%s", %s, %s, %s)' % (self._table, self.name, self.kills, self.suicides, self.teamkills)
        return q
        
    def _updatequery(self):
        q = 'UPDATE %s SET name="%s", kills=%s, suicides=%s, teamkills=%s WHERE id=%s' % (self._table, self.name, self.kills, self.suicides, self.teamkills, self.id)
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
        q = 'INSERT INTO %s ( player_id, weapon_id, kills, deaths, suicides, teamkills, teamdeaths ) VALUES (%s, %s, %s, %s, %s, %s, %s)' % (self._table, self.player_id, self.weapon_id, self.kills, self.deaths, self.suicides, self.teamkills, self.teamdeaths)
        return q
        
    def _updatequery(self):
        q = 'UPDATE %s SET player_id=%s, weapon_id=%s, kills=%s, deaths=%s, suicides=%s, teamkills=%s, teamdeaths=%s WHERE id=%s' % (self._table, self.player_id, self.weapon_id, self.kills, self.deaths, self.suicides, self.teamkills, self.teamdeaths, self.id)
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
        q = 'INSERT INTO %s ( name, kills, suicides, teamkills ) VALUES ("%s", %s, %s, %s)' % (self._table, self.name, self.kills, self.suicides, self.teamkills)
        return q
        
    def _updatequery(self):
        q = 'UPDATE %s SET name="%s", kills=%s, suicides=%s, teamkills=%s WHERE id=%s' % (self._table, self.name, self.kills, self.suicides, self.teamkills, self.id)
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
        q = 'INSERT INTO %s ( name, kills, suicides, teamkills, rounds ) VALUES ("%s", %s, %s, %s, %s)' % (self._table, self.name, self.kills, self.suicides, self.teamkills, self.rounds)
        return q
        
    def _updatequery(self):
        q = 'UPDATE %s SET name="%s", kills=%s, suicides=%s, teamkills=%s, rounds=%s WHERE id=%s' % (self._table, self.name, self.kills, self.suicides, self.teamkills, self.rounds, self.id)
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
        q = 'INSERT INTO %s ( player_id, bodypart_id, kills, deaths, suicides, teamkills, teamdeaths ) VALUES (%s, %s, %s, %s, %s, %s, %s)' % (self._table, self.player_id, self.bodypart_id, self.kills, self.deaths, self.suicides, self.teamkills, self.teamdeaths)
        return q
        
    def _updatequery(self):
        q = 'UPDATE %s SET player_id=%s, bodypart_id=%s, kills=%s, deaths=%s, suicides=%s, teamkills=%s, teamdeaths=%s WHERE id=%s' % (self._table, self.player_id, self.bodypart_id, self.kills, self.deaths, self.suicides, self.teamkills, self.teamdeaths, self.id)
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
        q = 'INSERT INTO %s ( player_id, map_id, kills, deaths, suicides, teamkills, teamdeaths, rounds ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)' % (self._table, self.player_id, self.map_id, self.kills, self.deaths, self.suicides, self.teamkills, self.teamdeaths, self.rounds)
        return q
        
    def _updatequery(self):
        q = 'UPDATE %s SET player_id=%s, map_id=%s, kills=%s, deaths=%s, suicides=%s, teamkills=%s, teamdeaths=%s, rounds=%s WHERE id=%s' % (self._table, self.player_id, self.map_id, self.kills, self.deaths, self.suicides, self.teamkills, self.teamdeaths, self.rounds, self.id)
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
        q = 'INSERT INTO %s (killer_id, target_id, kills, retals) VALUES (%s, %s, %s, %s)' % (self._table, self.killer_id, self.target_id, self.kills, self.retals)
        return q

    def _updatequery(self):
        q = 'UPDATE %s SET killer_id=%s, target_id=%s, kills=%s, retals=%s WHERE id=%s' % (self._table, self.killer_id, self.target_id, self.kills, self.retals, self.id)
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
        q = 'INSERT INTO %s ( player_id, action_id, count ) VALUES (%s, %s, %s)' % (self._table, self.player_id, self.action_id, self.count)
        return q
        
    def _updatequery(self):
        q = 'UPDATE %s SET player_id=%s, action_id=%s, count=%s WHERE id=%s' % (self._table, self.player_id, self.action_id, self.count, self.id)
        return q
    

if __name__ == '__main__':
    print '\nThis is version '+__version__+' by '+__author__+' for BigBrotherBot.\n'

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
