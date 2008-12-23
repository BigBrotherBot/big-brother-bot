##################################################################
#
# XLRstats
# statistics-generating plugin for B3 (www.bigbrotherbot.com)
# (c) 2004, 2005 Tim ter Laak (ttlogic@xlr8or.com)
#
# This program is free software and licensed under the terms of
# the GNU General Public License (GPL), version 2.
#
##################################################################
# CHANGELOG
#    5/6/2008 - 0.6.0 - Mark Weirath (xlr8or@xlr8or.com)
#                       Added weapon replacements
#                       Added commands !xlrtopstats and !xlrhide

__author__  = 'Tim ter Laak'
__version__ = '0.6.0'

# Version = major.minor.patches

# emacs-mode: -*- python-*-

import string, time, re, thread

import b3
import b3.events
import b3.plugin

KILLER = "killer"
VICTIM = "victim"


class XlrstatsPlugin(b3.plugin.Plugin):
    
    _world_clientid = None

    # config variables
    defaultskill = None
    minlevel = None

    Kfactor_high = None
    Kfactor_low = None
    Kswitch_kills = None

    steepness = None
    suicide_penalty_percent = None
    tk_penalty_percent = None
    kill_bonus = None
    prematch_maxtime = None
    
    # keep some private map data to detect prematches and restarts
    last_map = None
    last_roundtime = None
    
    # names for various stats tables
    playerstats_table = None
    weaponstats_table = None
    weaponusage_table = None
    bodyparts_table = None
    playerbody_table = None
    opponents_table = None
    mapstats_table = None
    playermaps_table = None
    

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

        # register the events we're interested in. 
        self.registerEvent(b3.events.EVT_CLIENT_JOIN)
        self.registerEvent(b3.events.EVT_CLIENT_KILL)
        self.registerEvent(b3.events.EVT_CLIENT_KILL_TEAM)
        self.registerEvent(b3.events.EVT_CLIENT_SUICIDE)
        self.registerEvent(b3.events.EVT_GAME_ROUND_START)
        
        # get the Client.id for the bot itself (guid: WORLD)
        sclient = self.console.clients.getByGUID("WORLD");
        if (sclient != None):
            self._world_clientid = sclient.id
        self.debug('Got client id for WORLD: %s', self._world_clientid)

    def onLoadConfig(self):
        try:
            self.minlevel = self.config.getint('settings', 'minlevel')    
        except:
            self.minlevel = 1
            self.debug('Using default value (%i) for settings::minlevel', self.minlevel)

        try:
            self.defaultskill = self.config.getint('settings', 'defaultskill')  
        except:
            self.defaultskill = 1000
            self.debug('Using default value (%i) for settings::defaultskill', self.defaultskill)
            
        try:
            self.Kfactor_high = self.config.getint('settings', 'Kfactor_high')   
        except:
            self.Kfactor_high = 16
            self.debug('Using default value (%i) for settings::Kfactor_high', self.Kfactor_high)
            
        try:
            self.Kfactor_low = self.config.getint('settings', 'Kfactor_low')    
        except:
            self.Kfactor_low = 4
            self.debug('Using default value (%i) for settings::Kfactor_low', self.Kfactor_low)
            
        try:
            self.Kswitch_kills = self.config.getint('settings', 'Kswitch_kills')    
        except:
            self.Kswitch_kills = 100
            self.debug('Using default value (%i) for settings::Kswitch_kills', self.Kswitch_kills)
            
        try:
            self.steepness = self.config.getint('settings', 'steepness')
        except:
            self.steepness = 600
            self.debug('Using default value (%i) for settings::steepness', self.steepness)
            
        try:
            self.suicide_penalty_percent = self.config.getfloat('settings', 'suicide_penalty_percent')
        except:
            self.suicide_penalty_percent = 0.05
            self.debug('Using default value (%f) for settings::suicide_penalty_percent', self.suicide_penalty_percent)

        try:
            self.tk_penalty_percent = self.config.getfloat('settings', 'tk_penalty_percent')
        except:
            self.tk_penalty_percent = 0.1
            self.debug('Using default value (%f) for settings::tk_penalty_percent', self.tk_penalty_percent)
            
        try:
            self.kill_bonus = self.config.getfloat('settings', 'kill_bonus')
        except:
            self.kill_bonus = 1.2
            self.debug('Using default value (%f) for settings::kill_bonus', self.kill_bonus)
            
        try:
            self.prematch_maxtime = self.config.getint('settings', 'prematch_maxtime')
        except:
            self.prematch_maxtime = 70
            self.debug('Using default value (%d) for settings::prematch_maxtime', self.prematch_maxtime)

            
        try:
            self.playerstats_table = self.config.get('tables', 'playerstats')
        except:
            self.playerstats_table = 'xlr_playerstats'
            self.debug('Using default value (%s) for tables::playerstats', self.playerstats_table)
            
            
        try:
            self.weaponstats_table = self.config.get('tables', 'weaponstats')
        except:
            self.weaponstats_table = 'xlr_weaponstats'
            self.debug('Using default value (%s) for tables::weaponstats', self.weaponstats_table)
            
        try:
            self.weaponusage_table = self.config.get('tables', 'weaponusage')
        except:
            self.weaponusage_table = 'xlr_weaponusage'
            self.debug('Using default value (%s) for tables::weaponusage', self.weaponusage_table)
            
        try:
            self.bodyparts_table = self.config.get('tables', 'bodyparts')
        except:
            self.bodyparts_table = 'xlr_bodyparts'
            self.debug('Using default value (%s) for tables::bodyparts', self.bodyparts_table)
           
        try:
            self.playerbody_table = self.config.get('tables', 'playerbody')
        except:
            self.playerbody_table = 'xlr_playerbody'
            self.debug('Using default value (%s) for tables::playerbody', self.playerbody_table)
            
        try:
            self.opponents_table = self.config.get('tables', 'opponents')
        except:
            self.opponents_table = 'xlr_opponents'
            self.debug('Using default value (%s) for tables::opponents', self.opponents_table)
            
        try:
            self.mapstats_table = self.config.get('tables', 'mapstats')
        except:
            self.mapstats_table = 'xlr_mapstats'
            self.debug('Using default value (%s) for tables::mapstats', self.mapstats_table)
            
        try:
            self.playermaps_table = self.config.get('tables', 'playermaps')
        except:
            self.playermaps_table = 'xlr_playermaps'
            self.debug('Using default value (%s) for tables::playermaps', self.playermaps_table)
                      
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
        if (event.type == b3.events.EVT_CLIENT_KILL):
            self.kill(event.client, event.target, event.data)
        elif (event.type == b3.events.EVT_CLIENT_KILL_TEAM):
            self.teamkill(event.client, event.target, event.data)
        elif (event.type == b3.events.EVT_CLIENT_SUICIDE):
            self.suicide(event.client, event.target, event.data)
        elif (event.type == b3.events.EVT_GAME_ROUND_START):
            self.roundstart()
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


    def save_Stat(self, stat):
        #self.debug('Saving statistics for ', typeof(stat))
        #self.debug9'Contents: ', stat)
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
        

    def kill(self, client, target, data):
        if (client == None):
            return
        if (target == None):
            return
        if (data == None):
            return
            
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
         
        #Calculate new stats for the killer
        if ( anonymous != KILLER ):
            if (killerstats.kills > self.Kswitch_kills):
                Kfactor = self.Kfactor_low
            else:
                Kfactor = self.Kfactor_high
                
            killerstats.skill = int(killerstats.skill) + ( self.kill_bonus * Kfactor * weapon_factor * (1-killer_prob) )
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
        
            self.save_Stat(killerstats)

        #Calculate new stats for the victim
        if (anonymous != VICTIM):
            if (victimstats.kills > self.Kswitch_kills):
                Kfactor = self.Kfactor_low
            else:
                Kfactor = self.Kfactor_high    
                
            victimstats.skill = int(victimstats.skill) + ( Kfactor * weapon_factor * (0-victim_prob) )
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
        
            self.save_Stat(victimstats)

        #make sure the record for anonymous is really created with an insert once
        if (anonymous):
            if ( (anonymous == KILLER) and (hasattr(killerstats, '_new')) ):
                self.save_Stat(killerstats)
            elif ( (anonymous == VICTIM) and (hasattr(victimstats, '_new')) ):
                self.save_Stat(victimstats)  
        
        # adjust the "opponents" table to register who killed who
        opponent = self.get_Opponent(targetid=victimstats.id, killerid=killerstats.id)
        retal = self.get_Opponent(targetid=killerstats.id, killerid=victimstats.id)
        # The above should always succeed, but you never know...
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


    def suicide(self, client, target, data):
        if (client == None):
            return
        if (target == None):
            return
        if (data == None):
            return

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
        
        playerstats.skill = (1 - (self.suicide_penalty_percent / 100.0) ) * float(playerstats.skill)
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
            killerstats.skill = (1 - (self.tk_penalty_percent / 100.0) ) * float(killerstats.skill) 
            killerstats.teamkills += 1
            killerstats.curstreak = 0   # break off current streak as it is now "impure"
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
        if ( self.last_map == None):
            self.last_map = self.console.game.mapName
            #self.last_roundtime = self.console.game._roundTimeStart
        else:
            if (  ( self.last_map == self.console.game.mapName) and  (self.console.game.roundTime() < self.prematch_maxtime) ):
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
    def cmd_xlrtopstats(self, data, client, cmd=None):
        """\
        [<#>] - list the top # players.
        """
        thread.start_new_thread(self.doTopList, (data, client, cmd))

        return

    # Retrieves the Top # Players
    def doTopList(self, data, client, cmd=None):
        if data:
            if re.match('^[0-9]+$', data, re.I):
                limit = int(data)
                if limit > 10:
                    limit = 10
        else:
            limit = 3

        q = 'SELECT * FROM %s INNER JOIN `clients` ON (`%s`.`client_id` = `clients`.`id`) WHERE (`%s`.`hide` <> 1) ORDER BY `%s`.`skill` DESC LIMIT %s' % (self.playerstats_table, self.playerstats_table, self.playerstats_table, self.playerstats_table, limit)

        cursor = self.query(q)
        if (cursor and (cursor.rowcount > 0) ):
            message = '^3XLR Stats Top %s Players:' % (limit)
            cmd.sayLoudOrPM(client, message)
            c = 1
            while not cursor.EOF:
                r = cursor.getRow()
                message = '^3# %s: ^7%s ^7: Skill ^3%1.02f ^7Ratio ^5%1.02f ^7Kills: ^2%s' % (c, r['name'], r['skill'], r['ratio'], r['kills'])
                cmd.sayLoudOrPM(client, message)
                cursor.moveNext()
                c += 1
                time.sleep(1)
        else:
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
            sclient.message('^3You are invisible in xlrstats!')
            client.message('^3%s INVISIBLE in xlrstats!' % sclient.exactName)
            hide = 1
        elif m in ('off', '0'):
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
    curstreak = 0
    winstreak = 0
    losestreak = 0
    rounds = 0
    hide = 0    
    
    # the following fields are used only by the PHP presentation code
    fixed_name = "" 

    def _insertquery(self):
        q = 'INSERT INTO %s ( client_id, kills, deaths, teamkills, teamdeaths, suicides, ratio, skill, curstreak, winstreak, losestreak, rounds, hide ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)' % (self._table, self.client_id, self.kills, self.deaths,  self.teamkills, self.teamdeaths, self.suicides, self.ratio, self.skill, self.curstreak, self.winstreak, self.losestreak, self.rounds, self.hide)
        return q
        
    def _updatequery(self):
        q = 'UPDATE %s SET client_id=%s, kills=%s, deaths=%s, teamkills=%s, teamdeaths=%s, suicides=%s, ratio=%s, skill=%s, curstreak=%s, winstreak=%s, losestreak=%s, rounds=%s, hide=%s WHERE id=%s' % (self._table, self.client_id, self.kills, self.deaths, self.teamkills, self.teamdeaths, self.suicides, self.ratio, self.skill, self.curstreak, self.winstreak, self.losestreak, self.rounds, self.hide, self.id)
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

# local variables:
# tab-width: 4
