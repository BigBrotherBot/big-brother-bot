# Jumper Plugin for BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2013 Daniele Pantaleone <fenix@bigbrotherbot.net>
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
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA

__author__ = 'Fenix'
__version__ = '2.30'

import b3
import b3.plugin
import b3.events
import time
import datetime
import requests
import os
import re

from b3.functions import getCmd
from b3.functions import getStuffSoundingLike
from b3.functions import right_cut
from ConfigParser import NoOptionError
from threading import Timer

########################################################################################################################
#                                                                                                                      #
#   JUMPRUN DEDICATED CODE                                                                                             #
#                                                                                                                      #
########################################################################################################################

class JumpRun(object):

    p = None

    client = None
    mapname = None
    way_id = None
    demo = None
    way_time = None
    time_add = None
    time_edit = None
    jumprun_id = None

    def __init__(self, plugin, **kwargs):
        """
        Object constructor.
        """
        self.p = plugin
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    def start(self):
        """
        Perform operations on jumprun start.
        """
        self.startdemo()

    def stop(self, way_time):
        """
        Perform operations on jumprun stop.
        """
        self.way_time = way_time
        self.time_add = self.p.console.time()
        self.time_edit = self.p.console.time()
        self.stopdemo()

        if not self.is_personal_record():
            self.client.message(self.p.getMessage('personal_record_failed', {'client': self.client.name}))
            self.unlinkdemo()
        else:
            if self.is_map_record():
                self.p.console.saybig(self.p.getMessage('map_record_established', {'client': self.client.name}))
            else:
                self.client.message(self.p.getMessage('personal_record_established', {'mapname': self.mapname}))

    def cancel(self):
        """
        Perform operations on jumprun cancel.
        """
        if self.p._demo_record and self.p.serverSideDemoPlugin and self.demo is not None:
            self.stopdemo()
            self.unlinkdemo()

    ####################################################################################################################
    #                                                                                                                  #
    #   OTHER METHODS                                                                                                  #
    #                                                                                                                  #
    ####################################################################################################################

    def startdemo(self):
        """
        Start recording the client's jumprun.
        """
        if self.p._demo_record and self.p.serverSideDemoPlugin:
            rv = self.p.serverSideDemoPlugin.start_recording_player(self.client)
            match = self.p.serverSideDemoPlugin._re_startserverdemo_success.match(rv)
            if not match:
                self.p.warning('could not retrieve demo filename for client @%s : %s' % (self.client.id, rv))
                self.demo = None
            else:
                self.p.debug('started recording demo for client @%s : %s' % (self.client.id, match.group('file')))
                self.demo = match.group('file')

    def stopdemo(self):
        """
        Stop recording the client's jumprun.
        """
        if self.p._demo_record and self.p.serverSideDemoPlugin:
            self.p.serverSideDemoPlugin.stop_recording_player(self.client)

    def unlinkdemo(self):
        """
        Delete the demo connected to this jumprun.
        """
        if self.demo is None:
            self.p.debug('not removing jumprun demo for client @%s : no demo has been recorded' % self.client.id)
        else:

            # check for fs_game not to be None
            if self.p.console.game.fs_game is None:

                try:
                    self.p.console.game.fs_game = right_cut(self.p.console.getCvar('fs_game').getString(), '/')
                    self.p.debug('retrieved server cvar <fs_game> : %s' % self.p.console.game.fs_game)
                except AttributeError, e:
                    self.p.warning('could not retrieve server cvar <fs_game> : %s' % e)
                    return

            # check for fs_basepath not to be None
            if self.p.console.game.fs_basepath is None:

                try:
                    self.p.console.game.fs_basepath = self.p.console.getCvar('fs_basepath').getString().rstrip('/')
                    self.p.debug('retrieved server cvar <fs_basepath> : %s' % self.p.console.game.fs_basepath)
                except AttributeError, e:
                    self.p.warning('could not retrieve server cvar <fs_basepath> : %s' % e)
                    return

            # construct a possible demo filepath where to search the demo which is going to be deleted
            path = os.path.normpath(os.path.join(self.p.console.game.fs_basepath, self.p.console.game.fs_game, self.demo))

            if not os.path.isfile(path):

                # could not find a demo under fs_basepath: try fs_homepath
                self.p.debug('demo not found under fs_basepath : %s' % path)
                if self.p.console.game.fs_homepath is None:

                    try:
                        self.p.console.game.fs_homepath = self.p.console.getCvar('fs_homepath').getString().rstrip('/')
                        self.p.debug('retrieved server cvar <fs_homepath> : %s' % self.p.console.game.fs_basepath)
                    except AttributeError, e:
                        self.p.warning('could not retrieve server cvar <fs_homepath> : %s' % e)
                        return

                # construct a possible demo filepath where to search the demo which is going to be deleted
                path = os.path.normpath(os.path.join(self.p.console.game.fs_homepath, self.p.console.game.fs_game, self.demo))

                if not os.path.isfile(path):
                    self.p.debug('demo not found under fs_homepath : %s' % path)
                    return

            try:
                os.unlink(path)
                self.p.debug('removed jumprun demo file : %s' % path)
            except os.error, (errno, errstr):
                # when this happen is mostly a problem related to misconfiguration
                self.p.error("could not remove jumprun demo file : %s | [%d] %s" % (path, errno, errstr))

    def is_personal_record(self):
        """
        Return True if the client established his new personal record on this map and on the given way_id, False
        otherwise. The function will also update values in the database and perform some other operations
        if the client made a new personal record.
        """
        # check if the client made his personal record on this map and this way
        cursor = self.p.console.storage.query(self.p.sql['jr1'] % (self.client.id, self.mapname, self.way_id))
        if cursor.EOF:
            self.insert()
            cursor.close()
            return True

        r = cursor.getRow()
        if self.way_time < int(r['way_time']):
            if r['demo'] is not None:
                jumprun = JumpRun(plugin=self.p, client=self.client, mapname=r['mapname'], way_id=int(r['way_id']),
                                  demo=r['demo'], way_time=int(r['way_time']), time_add=int(r['time_add']),
                                  time_edit=int(r['time_edit']), jumprun_id=int(r['id']))

                # remove previously stored demo
                jumprun.unlinkdemo()
                del jumprun

            self.update()
            cursor.close()
            return True

        cursor.close()
        return False

    def is_map_record(self):
        """
        Return True if the client established a new absolute record on this map and on the given way_id, False otherwise.
        """
        # check if the client made an absolute record on this map on the specified way_id
        cursor = self.p.console.storage.query(self.p.sql['jr2'] % (self.mapname, self.way_id, self.way_time))
        if cursor.EOF:
            cursor.close()
            return True

        cursor.close()
        return False

    ####################################################################################################################
    #                                                                                                                  #
    #   STORAGE METHODS                                                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    def insert(self):
        """
        Insert the jumprun in the storage.
        """
        demo = self.demo.replace("'", "\'") if self.demo else None
        self.p.console.storage.query(self.p.sql['jr7'] % (self.client.id, self.mapname, self.way_id, self.way_time,
                                                          self.time_add, self.time_edit, demo))
        self.p.debug('stored new jumprun : %r' % self)

    def update(self):
        """
        Update the jumprun in the storage.
        """
        demo = self.demo.replace("'", "\'") if self.demo else None
        self.p.console.storage.query(self.p.sql['jr8'] % (self.way_time, self.time_add, demo,
                                                          self.client.id, self.mapname, self.way_id))
        self.p.debug('updated jumprun : %r' % self)

    def delete(self):
        """
        Delete the jumprun from the storage.
        """
        self.unlinkdemo()
        self.p.console.storage.query(self.p.sql['jr9'] % self.jumprun_id)
        self.p.debug('removed jumprun : %r' % self)

    def __repr__(self):
        """
        Object representation.
        """
        return 'JumpRun<id=%s,client=%s,mapname=%s,way_id=%s,way_time=%s,demo=%s>' % (self.jumprun_id or 'NEW',
                self.client.id, self.mapname, self.way_id, self.way_time, self.demo or 'NONE')

########################################################################################################################
#                                                                                                                      #
#   PLUGIN IMPLEMENTATION                                                                                              #
#                                                                                                                      #
########################################################################################################################

class JumperPlugin(b3.plugin.Plugin):

    adminPlugin = None
    powerAdminUrtPlugin = None
    serverSideDemoPlugin = None

    requiresParsers = ['iourt42']
    loadAfterPlugins = ['poweradminurt', 'urtserversidedemo']

    _maps_data_from_api = {}

    standard_maplist = [
        'ut4_abbey', 'ut4_abbeyctf', 'ut4_algiers', 'ut4_ambush', 'ut4_austria',
        'ut4_bohemia', 'ut4_casa', 'ut4_cascade', 'ut4_commune', 'ut4_company', 'ut4_crossing',
        'ut4_docks', 'ut4_dressingroom', 'ut4_eagle', 'ut4_elgin', 'ut4_firingrange',
        'ut4_ghosttown_rc4', 'ut4_harbortown', 'ut4_herring', 'ut4_horror', 'ut4_kingdom',
        'ut4_kingpin', 'ut4_mandolin', 'ut4_maya', 'ut4_oildepot', 'ut4_prague', 'ut4_prague_v2',
        'ut4_raiders', 'ut4_ramelle', 'ut4_ricochet', 'ut4_riyadh', 'ut4_sanc', 'ut4_snoppis',
        'ut4_suburbs', 'ut4_subway', 'ut4_swim', 'ut4_thingley', 'ut4_tombs', 'ut4_toxic',
        'ut4_tunis', 'ut4_turnpike', 'ut4_uptown'
    ]

    sql = {
        'jr1': """SELECT * FROM jumpruns WHERE client_id = '%s' AND mapname = '%s' AND way_id = '%d'""",
        'jr2': """SELECT * FROM jumpruns WHERE mapname = '%s' AND way_id = '%d' AND way_time < '%d'""",
        'jr3': """SELECT jr.id AS jumprun_id, jr.client_id AS client_id, jr.way_id AS way_id, jr.way_time AS way_time,
                  jr.time_add AS time_add, jr.time_edit AS time_edit, jr.demo AS demo, jw.way_name
                  AS way_name FROM jumpruns AS jr LEFT OUTER JOIN jumpways AS jw ON jr.way_id = jw.way_id
                  AND jr.mapname = jw.mapname WHERE jr.mapname = '%s' AND jr.way_time IN (SELECT MIN(way_time)
                  FROM jumpruns WHERE mapname = '%s' GROUP BY way_id) ORDER BY jr.way_id ASC""",
        'jr4': """SELECT jr.id AS jumprun_id, jr.way_id AS way_id, jr.way_time AS way_time, jr.time_add AS time_add,
                  jr.time_edit AS time_edit, jr.demo AS demo, jw.way_name AS way_name FROM jumpruns AS jr
                  LEFT OUTER JOIN  jumpways AS jw ON  jr.way_id = jw.way_id
                  AND jr.mapname = jw.mapname WHERE jr.client_id = '%s' AND jr.mapname = '%s'
                  ORDER BY jr.way_id ASC""",
        'jr5': """SELECT DISTINCT way_id FROM jumpruns WHERE mapname = '%s' ORDER BY way_id ASC""",
        'jr6': """SELECT jr.id AS jumprun_id, jr.client_id AS client_id, jr.way_id AS way_id, jr.way_time AS way_time,
                  jr.time_add AS time_add, jr.time_edit AS time_edit, jr.demo AS demo, jw.way_name AS way_name
                  FROM jumpruns AS jr LEFT OUTER JOIN jumpways AS jw ON jr.way_id = jw.way_id
                  AND jr.mapname = jw.mapname WHERE jr.mapname = '%s' AND jr.way_id = '%d'
                  ORDER BY jr.way_time ASC LIMIT 3""",
        'jr7': """INSERT INTO jumpruns VALUES (NULL, '%s', '%s', '%d', '%d', '%d', '%d', '%s')""",
        'jr8': """UPDATE jumpruns SET way_time = '%d', time_edit = '%d', demo = '%s' WHERE client_id = '%s'
                  AND mapname = '%s' AND way_id = '%d'""",
        'jr9': """DELETE FROM jumpruns WHERE id = '%d'""",
        'jw1': """SELECT * FROM jumpways WHERE mapname = '%s' AND way_id = '%d'""",
        'jw2': """INSERT INTO jumpways VALUES (NULL, '%s', '%d', '%s')""",
        'jw3': """UPDATE jumpways SET way_name = '%s' WHERE mapname = '%s' AND way_id = '%d'""",
    }
    
    _demo_record = True
    _skip_standard_maps = True
    _min_level_delete = 80
    _max_cycle_count = 5
    _cycle_count = 0
    _timeout = 4

    ####################################################################################################################
    #                                                                                                                  #
    #   STARTUP                                                                                                        #
    #                                                                                                                  #
    ####################################################################################################################
     
    def onLoadConfig(self):
        """
        Load plugin configuration.
        """
        self._demo_record = self.getSetting('settings', 'demorecord', b3.BOOL, self._demo_record)
        self._skip_standard_maps = self.getSetting('settings', 'skipstandardmaps', b3.BOOL, self._skip_standard_maps)
        self._min_level_delete = self.getSetting('settings', 'minleveldelete', b3.LEVEL, self._min_level_delete)

        self._default_messages = {
            'client_record_unknown': '''^7no record found for ^3$client ^7(^4@$id^7) on ^3$mapname''',
            'client_record_deleted': '''^7removed ^3$num ^7record$plural for ^3$client ^7(^4@$id^7) on ^3$mapname''',
            'client_record_header': '''^7listing records for ^3$client ^7(^4@$id^7) on ^3$mapname^7:''',
            'client_record_pattern': '''^7[^3$way^7] ^2$time ^7since ^3$date''',
            'map_record_established': '''^3$client ^7established a new map record^7!''',
            'map_record_unknown': '''^7no record found on ^3$mapname''',
            'map_record_header': '''^7listing map records on ^3$mapname^7:''',
            'map_record_pattern': '''^7[^3$way^7] ^3$client ^7(^4@$id^7) with ^2$time''',
            'map_toprun_header': '''^7listing top runs on ^3$mapname^7:''',
            'map_toprun_pattern': '''^7[^3$way^7] #$place ^3$client ^7(^4@$id^7) with ^2$time''',
            'mapinfo_failed': '''^7could not query remote server to get maps data''',
            'mapinfo_empty': '''^7could not find info for map ^1$mapname''',
            'mapinfo_author_unknown': '''^7I don't know who created ^3$mapname''',
            'mapinfo_author': '''^3$mapname ^7has been created by ^3$author''',
            'mapinfo_released': '''^7it has been released on ^3$date''',
            'mapinfo_ways': '''^7it's composed of ^3$way ^7way$plural''',
            'mapinfo_jump_ways': '''^7it's composed of ^3$jumps ^7jumps and ^3$way ^7way$plural''',
            'mapinfo_level': '''^7level: ^3$level^7/^3100''',
            'personal_record_failed': '''^7you can do better ^3$client^7...try again!''',
            'personal_record_established': '''^7you established a new personal record on ^3$mapname^7!''',
            'record_delete_denied': '''^7you can't delete ^1$client ^7(^4@$id^7) records'''
        }

    def onStartup(self):
        """
        Initialize plugin settings.
        """
        # get the admin plugin
        self.adminPlugin = self.console.getPlugin('admin')

        # get the poweradminurt plugin
        self.powerAdminUrtPlugin = self.console.getPlugin('poweradminurt')

        if self._demo_record:
            self.serverSideDemoPlugin = self.console.getPlugin('urtserversidedemo')
            if not self.serverSideDemoPlugin:
                self._demo_record = False
                self.warning("automatic demo recording is enabled in configuration file but plugin 'urtserversidedemo' "
                             "has not been loaded in B3 main configuration file: automatic demo recording will be disabled")

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
                    self.adminPlugin.registerCommand(self, cmd, level, func, alias)

        for cmd in ('map', 'maps', 'pasetnextmap'):

            try:
                alias = self.adminPlugin._commands[cmd].alias
                level = '-'.join(map(str, self.adminPlugin._commands[cmd].level))
                func = getCmd(self, cmd)
                self.adminPlugin.unregisterCommand(cmd)
                self.adminPlugin.registerCommand(self, cmd, level, func, alias)
            except KeyError:
                self.debug('not overriding command (%s) : it has not been registered by any other plugin')

        # create database tables (if needed)
        current_tables = self.console.storage.getTables()
        if 'jumpruns' not in current_tables or 'jumpways' not in current_tables:
            sql_path_main = b3.getAbsolutePath('@b3/plugins/jumper/sql')
            sql_path = os.path.join(sql_path_main, self.console.storage.dsnDict['protocol'], 'jumper.sql')
            self.console.storage.queryFromFile(sql_path)

        self.registerEvent('EVT_CLIENT_JUMP_RUN_START', self.onJumpRunStart)
        self.registerEvent('EVT_CLIENT_JUMP_RUN_STOP', self.onJumpRunStop)
        self.registerEvent('EVT_CLIENT_JUMP_RUN_CANCEL', self.onJumpRunCancel)
        self.registerEvent('EVT_CLIENT_TEAM_CHANGE', self.onTeamChange)
        self.registerEvent('EVT_CLIENT_DISCONNECT', self.onDisconnect)
        self.registerEvent('EVT_GAME_MAP_CHANGE', self.onMapChange)
        self.registerEvent('EVT_PLUGIN_ENABLED', self.onPluginEnabled)
        self.registerEvent('EVT_PLUGIN_DISABLED', self.onPluginDisabled)

        # make sure to stop all the demos being recorded or the plugin
        # will go out of sync: will not be able to retrieve demos for players
        # who are already in a jumprun and being recorded
        if self._demo_record and self.serverSideDemoPlugin:
            self.serverSideDemoPlugin.stop_recording_all_players()

        # notice plugin startup
        self.debug('plugin started')

    def onDisable(self):
        """
        Called when the plugin is disabled
        """
        # stop all the jumpruns
        for client in self.console.clients.getList():
            if client.isvar(self, 'jumprun'):
                jumprun = client.var(self, 'jumprun').value
                jumprun.cancel()
                client.delvar(self, 'jumprun')

    def onEnable(self):
        """
        Called when the plugin is enabled
        """
        if self._skip_standard_maps:
            mapname = self.console.game.mapName
            if mapname in self.standard_maplist:
                self.console.say('^7built-in map detected: cycling map ^3%s...' % mapname)
                self.debug('built-in map detected: cycling map %s...' % mapname)
                self._cycle_count += 1
                self.console.write('cyclemap')

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENTS                                                                                                         #
    #                                                                                                                  #
    ####################################################################################################################

    def onPluginEnabled(self, event):
        """
        Handle EVT_PLUGIN_ENABLED
        """
        if self.serverSideDemoPlugin and event.data == 'urtserversidedemo':
            self._demo_record = True

    def onPluginDisabled(self, event):
        """
        Handle EVT_PLUGIN_DISABLED
        """
        if self._demo_record and event.data == 'urtserversidedemo':
            self._demo_record = False

    def onJumpRunStart(self, event):
        """
        Handle EVT_CLIENT_JUMP_RUN_START
        """
        client = event.client
        if client.isvar(self, 'jumprun'):
            jumprun = client.var(self, 'jumprun').value
            jumprun.cancel()
            client.delvar(self, 'jumprun')

        jumprun = JumpRun(plugin=self, client=client, mapname=self.console.game.mapName, way_id=int(event.data['way_id']))
        jumprun.start()

        client.setvar(self, 'jumprun', jumprun)

    def onJumpRunCancel(self, event):
        """
        Handle EVT_CLIENT_JUMP_RUN_CANCEL
        """
        client = event.client
        if client.isvar(self, 'jumprun'):
            jumprun = client.var(self, 'jumprun').value
            jumprun.cancel()
            client.delvar(self, 'jumprun')

    def onJumpRunStop(self, event):
        """
        Handle EVT_CLIENT_JUMP_RUN_STOP
        """
        client = event.client
        if client.isvar(self, 'jumprun'):
            jumprun = client.var(self, 'jumprun').value
            jumprun.stop(int(event.data['way_time']))
            client.delvar(self, 'jumprun')

    def onDisconnect(self, event):
        """
        Handle EVT_CLIENT_DISCONNECT
        """
        client = event.client
        if client.isvar(self, 'jumprun'):
            jumprun = client.var(self, 'jumprun').value
            jumprun.unlinkdemo()
            client.delvar(self, 'jumprun')

    def onTeamChange(self, event):
        """
        Handle EVT_CLIENT_TEAM_CHANGE
        """
        if event.data == b3.TEAM_SPEC:
            client = event.client
            if client.isvar(self, 'jumprun'):
                jumprun = client.var(self, 'jumprun').value
                jumprun.cancel()
                client.delvar(self, 'jumprun')

    def onMapChange(self, event):
        """
        Handle EVT_GAME_MAP_CHANGE
        """
        # cancel all the jumpruns
        for client in self.console.clients.getList():
            if client.isvar(self, 'jumprun'):
                jumprun = client.var(self, 'jumprun').value
                jumprun.cancel()
                client.delvar(self, 'jumprun')

        if self._skip_standard_maps:
            mapname = self.console.game.mapName
            mapname = mapname.lower()
            if mapname in self.standard_maplist:
                # endless loop protection
                if self._cycle_count < self._max_cycle_count:
                    self.debug('built-in map detected: cycling map %s...' % mapname)
                    self._cycle_count += 1
                    self.console.write('cyclemap')
                    return

                # we should have cycled this map but too many consequent cyclemap
                # has been issued: this should never happen unless some idiots keep
                # voting for standard maps. However I'll handle this in another plugin
                self.debug('built-in map detected: could not cycle map %s due to endless loop protection...' % mapname)

        self._cycle_count = 0

        # refresh maps data if they are available
        maps_data_from_api = self.getMapsDataFromApi()
        if maps_data_from_api:
            self._maps_data_from_api = maps_data_from_api

        # welcome the clients on the new level
        thread = Timer(30.0, self.welcomeClients, (event.data['new'].lower(),))
        thread.setDaemon(True)
        thread.start()

    ####################################################################################################################
    #                                                                                                                  #
    #   OTHER METHODS                                                                                                  #
    #                                                                                                                  #
    ####################################################################################################################

    @staticmethod
    def getDateString(msec):
        """
        Return a date string ['Thu, 28 Jun 2001']
        """
        return time.strftime("%a, %d %b %Y", time.gmtime(msec))

    @staticmethod
    def getTimeString(msec):
        """
        Return a time string given it's value expressed in milliseconds [H:mm:ss:ms]
        """
        secs = msec / 1000
        msec -= secs * 1000
        mins = secs / 60
        secs -= mins * 60
        hour = mins / 60
        mins -= hour * 60
        return "%01d:%02d:%02d.%03d" % (hour, mins, secs, msec)

    def welcomeClients(self, mapname):
        """
        Welcome online players on the new map printing some information.
        """
        self.console.say('^7Welcome to ^3%s' % mapname)
        if not self._maps_data_from_api:
            self.warning('could not display map information : no map information available')
        elif mapname not in self._maps_data_from_api:
            self.debug('not displaying map information : map %s has no information returned by the api' % mapname)
        else:
            a = self._maps_data_from_api[mapname]['mapper']
            d = self._maps_data_from_api[mapname]['mdate']
            t = int(datetime.datetime.strptime(d, '%Y-%m-%d').strftime('%s'))

            if a:
                self.console.say('^7This map has been created by ^3%s ^7on ^3%s' % (a, self.getDateString(t)))
                self.console.say('^7Type ^4!^7mapinfo in chat to have more information')

    def getMapsDataFromApi(self):
        """
        Retrieve map info from UrTJumpers API
        """
        try:
            self.debug('contacting http://api.urtjumpers.com to retrieve maps data...')
            rt = requests.get('http://api.urtjumpers.com/?key=B3urtjumpersplugin&liste=maps&format=json', timeout=self._timeout).json()
        except Exception, e:
            self.warning('could not connect to http://api.urtjumpers.com: %s' % e)
            return {}
        else:
            data = {d['pk3'].lower(): d for d in rt}
            self.debug('retrieved %d maps from http://api.urtjumpers.com' % len(data))
            return data

    def getMapsFromListSoundingLike(self, mapname):
        """
        Return a list of maps matching the given search key
        The search is performed on the maplist retrieved from the API
        """
        mapname = mapname.lower()
        # check exact match at first
        if mapname in self._maps_data_from_api:
            return [mapname]
        # check with substring matching
        return [x for x in self._maps_data_from_api if mapname in x]

    def getMapsSoundingLike(self, mapname):
        """
        Return a valid mapname.
        If no exact match is found, then return close candidates as a list.
        """
        wanted_map = mapname.lower()
        maps = self.console.getMaps()

        supported_maps = []
        if not self._skip_standard_maps:
            supported_maps = maps
        else:
            for m in maps:
                if self._skip_standard_maps:
                    if m.lower() in self.standard_maplist:
                        continue
                supported_maps.append(m)

        if wanted_map in supported_maps:
            return wanted_map

        cleaned_supported_maps = {}
        for map_name in supported_maps:
            cleaned_supported_maps[re.sub("^ut4?_", '', map_name, count=1)] = map_name

        if wanted_map in cleaned_supported_maps:
            return cleaned_supported_maps[wanted_map]

        cleaned_wanted_map = re.sub("^ut4?_", '', wanted_map, count=1)

        matches = [cleaned_supported_maps[match] for match in getStuffSoundingLike(cleaned_wanted_map,
                                                                                   cleaned_supported_maps.keys())]
        if len(matches) == 1:
            # one match, get the map id
            return matches[0]

        # multiple matches, provide suggestions
        return matches

    ####################################################################################################################
    #                                                                                                                  #
    #   STORAGE METHODS                                                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    def getMapRecords(self, mapname):
        """
        Return a list of jumprun records for the given map
        """
        cursor = self.console.storage.query(self.sql['jr3'] % (mapname, mapname))
        if cursor.EOF:
            cursor.close()
            return []

        records = []
        while not cursor.EOF:
            r = cursor.getRow()
            client = self.adminPlugin.findClientPrompt('@%s' % r['client_id'])
            if not client:
                self.warning('client @%s has jumpruns data but he is missing from clients table' % r['client_id'])
            else:
                jumprun = JumpRun(self, client=client, mapname=mapname, way_id=int(r['way_id']), demo=r['demo'],
                                  way_time=int(r['way_time']), way_name=r['way_name'], time_add=int(r['time_add']),
                                  time_edit=int(r['time_edit']), jumprun_id=int(r['jumprun_id']))

                records.append(jumprun)

            cursor.moveNext()

        cursor.close()
        return records

    def getClientRecords(self, client, mapname):
        """
        Return a list of jumprun records for the given client on the given mapname
        """
        cursor = self.console.storage.query(self.sql['jr4'] % (client.id, mapname))
        if cursor.EOF:
            cursor.close()
            return []

        records = []
        while not cursor.EOF:
            r = cursor.getRow()
            jumprun = JumpRun(self, client=client, mapname=mapname, way_id=int(r['way_id']), demo=r['demo'],
                              way_time=int(r['way_time']), way_name=r['way_name'], time_add=int(r['time_add']),
                              time_edit=int(r['time_edit']), jumprun_id=int(r['jumprun_id']))

            records.append(jumprun)
            cursor.moveNext()

        cursor.close()
        return records

    def getTopRuns(self, mapname):
        """
        Return a list of top jumpruns for the given mapname
        """
        c1 = self.console.storage.query(self.sql['jr5'] % mapname)
        if c1.EOF:
            c1.close()
            return []

        records = []
        while not c1.EOF:
            r1 = c1.getRow()
            c2 = self.console.storage.query(self.sql['jr6'] % (mapname, int(r1['way_id'])))
            while not c2.EOF:
                r2 = c2.getRow()
                client = self.adminPlugin.findClientPrompt('@%s' % r2['client_id'])
                if not client:
                    self.warning('client @%s has jumpruns data but he is missing from clients table' % r1['client_id'])
                else:
                    jumprun = JumpRun(self, client=client, mapname=mapname, way_id=int(r2['way_id']),
                                      demo=r2['demo'], way_time=int(r2['way_time']), way_name=r2['way_name'],
                                      time_add=int(r2['time_add']), time_edit=int(r2['time_edit']),
                                      jumprun_id=int(r2['jumprun_id']))

                    records.append(jumprun)

                c2.moveNext()

            c1.moveNext()
            c2.close()

        c1.close()
        return records

    ####################################################################################################################
    #                                                                                                                  #
    #   COMMANDS                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def cmd_record(self, data, client, cmd=None):
        """
        [<client>] [<mapname>] - display the best run(s) of a client on a specific map
        """
        cl = client
        mp = self.console.game.mapName
        ps = self.adminPlugin.parseUserCmd(data)
        if ps:
            cl = self.adminPlugin.findClientPrompt(ps[0], client)
            if not cl:
                # a list of closest matches will be displayed
                # to the client so he can retry with a more specific handle
                return

            if ps[1]:
                mp = self.getMapsSoundingLike(ps[1])
                if isinstance(mp, list):
                    client.message('do you mean: ^3%s?' % '^7, ^3'.join(mp[:5]))
                    return

                if not isinstance(mp, basestring):
                    client.message('^7could not find any map matching ^1%s' % ps[1])
                    return

        # get the records of the client
        records = self.getClientRecords(cl, mp)
        if len(records) == 0:
            cmd.sayLoudOrPM(client, self.getMessage('client_record_unknown', {'client': cl.name, 'id': cl.id, 'mapname': mp}))
            return

        if len(records) > 1:
            # print a sort of a list header so players will know what's going on
            cmd.sayLoudOrPM(client, self.getMessage('client_record_header', {'client': cl.name, 'id': cl.id, 'mapname': mp}))

        for jumprun in records:
            wi = jumprun.way_name if jumprun.way_name else str(jumprun.way_id)
            tm = self.getTimeString(jumprun.way_time)
            dt = self.getDateString(jumprun.time_edit)
            cmd.sayLoudOrPM(client, self.getMessage('client_record_pattern', {'way': wi, 'time': tm, 'date': dt}))

    def cmd_maprecord(self, data, client, cmd=None):
        """
        [<mapname>] - display map best jump run(s)
        """
        mp = self.console.game.mapName
        if data:
            mp = self.getMapsSoundingLike(data)
            if isinstance(mp, list):
                client.message('do you mean: ^3%s?' % '^7, ^3'.join(mp[:5]))
                return

            if not isinstance(mp, basestring):
                client.message('^7could not find any map matching ^1%s' % data)
                return

        # get the map records
        records = self.getMapRecords(mp)
        if len(records) == 0:
            cmd.sayLoudOrPM(client, self.getMessage('map_record_unknown', {'mapname': mp}))
            return

        if len(records) > 1:
            # print a sort of a list header so players will know what's going on
            cmd.sayLoudOrPM(client, self.getMessage('map_record_header', {'mapname': mp}))

        for jumprun in records:
            wi = jumprun.way_name if jumprun.way_name else str(jumprun.way_id)
            tm = self.getTimeString(jumprun.way_time)
            cmd.sayLoudOrPM(client, self.getMessage('map_record_pattern', {'way': wi, 'client': jumprun.client.name,
                                                                           'id':  jumprun.client.id, 'time': tm}))

    def cmd_topruns(self, data, client, cmd=None):
        """
        [<mapname>] - display map top runs
        """
        mp = self.console.game.mapName
        if data:
            mp = self.getMapsSoundingLike(data)
            if isinstance(mp, list):
                client.message('do you mean: ^3%s?' % '^7, ^3'.join(mp[:5]))
                return

            if not isinstance(mp, basestring):
                client.message('^7could not find any map matching ^1%s' % data)
                return

        # get the top runs
        records = self.getTopRuns(mp)
        if len(records) == 0:
            cmd.sayLoudOrPM(client, self.getMessage('map_record_unknown', {'mapname': mp}))
            return

        if len(records) > 1:
            # print a sort of a list header so players will know what's going on
            cmd.sayLoudOrPM(client, self.getMessage('map_toprun_header', {'mapname': mp}))

        place = 0
        last_way_id = None
        for jumprun in records:

            # if the way id changed, reset the place counter
            if last_way_id and last_way_id != jumprun.way_id:
                place = 0

            place += 1
            last_way_id = jumprun.way_id
            way_id = jumprun.way_name if jumprun.way_name else str(jumprun.way_id)
            way_time = self.getTimeString(jumprun.way_time)
            cmd.sayLoudOrPM(client, self.getMessage('map_toprun_pattern', {'way': way_id, 'place': place,
                                                                           'client': jumprun.client.name,
                                                                           'id': jumprun.client.id, 'time': way_time}))

    def cmd_delrecord(self, data, client, cmd=None):
        """
        [<client>] [<mapname>] - delete the best run(s) of a client on a specific map
        """
        cl = client
        mp = self.console.game.mapName
        ps = self.adminPlugin.parseUserCmd(data)
        if ps:
            cl = self.adminPlugin.findClientPrompt(ps[0], client)
            if not cl:
                return

            if ps[1]:
                mp = self.getMapsSoundingLike(ps[1])
                if isinstance(mp, list):
                    client.message('do you mean: ^3%s?' % '^7, ^3'.join(mp[:5]))
                    return

                if not isinstance(mp, basestring):
                    client.message('^7could not find any map matching ^1%s' % ps[1])
                    return

        if cl != client:
            if client.maxLevel < self._min_level_delete or client.maxLevel < cl.maxLevel:
                cmd.sayLoudOrPM(client, self.getMessage('record_delete_denied', {'client': cl.name, 'id': cl.id}))
                return

        records = self.getClientRecords(cl, mp)
        if len(records) == 0:
            cmd.sayLoudOrPM(client, self.getMessage('client_record_unknown', {'client': cl.name, 'id': cl.id, 'mapname': mp}))
            return

        for jumprun in records:
            jumprun.delete()

        num = len(records)
        self.verbose('removed %d record%s for client @%s on %s' % (num, 's' if num > 1 else '', cl.id, mp))
        cmd.sayLoudOrPM(client, self.getMessage('client_record_deleted', {'num': num, 'plural': 's' if num > 1 else '',
                                                                          'client': cl.name, 'id': cl.id, 'mapname': mp}))

    def cmd_mapinfo(self, data, client, cmd=None):
        """
        [<mapname>] - display map specific informations
        """
        if not self._maps_data_from_api:
            # retrieve data from the api
            self._maps_data_from_api = self.getMapsDataFromApi()

        if not self._maps_data_from_api:
            cmd.sayLoudOrPM(client, self.getMessage('mapinfo_failed'))
            return

        mp = self.console.game.mapName
        if data:
            # search info for the specified map
            match = self.getMapsFromListSoundingLike(data)

            if len(match) == 0:
                client.message('^7could not find any map matching ^1%s' % data)
                return

            if len(match) > 1:
                client.message('do you mean: ^3%s?' % '^7, ^3'.join(match[:5]))
                return

            mp = match[0]

        mp = mp.lower()
        if mp not in self._maps_data_from_api:
            cmd.sayLoudOrPM(client, self.getMessage('mapinfo_empty', {'mapname': mp}))
            return

        # fetch informations
        n = self._maps_data_from_api[mp]['nom']
        a = self._maps_data_from_api[mp]['mapper']
        d = self._maps_data_from_api[mp]['mdate']
        j = self._maps_data_from_api[mp]['njump']
        t = int(datetime.datetime.strptime(d, '%Y-%m-%d').strftime('%s'))
        l = int(self._maps_data_from_api[mp]['level'])
        w = int(self._maps_data_from_api[mp]['nway'])

        if not a:
            message = self.getMessage('mapinfo_author_unknown', {'mapname': n})
        else:
            message = self.getMessage('mapinfo_author', {'mapname': n, 'author': a})

        # send the computed message
        cmd.sayLoudOrPM(client, message)

        # we always know when the map has been released
        cmd.sayLoudOrPM(client, self.getMessage('mapinfo_released', {'date': self.getDateString(t)}))

        if not j:
            message = self.getMessage('mapinfo_ways', {'way': w, 'plural': 's' if w > 1 else ' only'})
        else:
            message = self.getMessage('mapinfo_jump_ways', {'jumps': j, 'way': w, 'plural': 's' if w > 1 else ''})

        # send the computed message
        cmd.sayLoudOrPM(client, message)

        if l > 0:
            cmd.sayLoudOrPM(client, self.getMessage('mapinfo_level', {'level': l}))

    def cmd_setway(self, data, client, cmd=None):
        """
        <way-id> <name> - set a name for the specified way id
        """
        if not data:
            client.message('invalid data, try ^3!^7help jmpsetway')
            return

        # parsing user input
        r = re.compile(r'''^(?P<way_id>\d+) (?P<way_name>.+)$''')
        m = r.match(data)
        if not m:
            client.message('invalid data, try ^3!^7help jmpsetway')
            return

        way_id = int(m.group('way_id'))
        way_name = m.group('way_name')

        mapname = self.console.game.mapName
        cursor = self.console.storage.query(self.sql['jw1'] % (mapname, way_id))

        if cursor.EOF:
            # new entry for this way_id on this map
            self.console.storage.query(self.sql['jw2'] % (mapname, way_id, way_name))
            client.message('^7added alias for way ^3%d^7: ^2%s' % (way_id, way_name))
        else:
            # update old entry with the new name
            self.console.storage.query(self.sql['jw3'] % (way_name, mapname, way_id))
            client.message('^7updated alias for way ^3%d^7: ^2%s' % (way_id, way_name))

        cursor.close()

    def cmd_map(self, data, client, cmd=None):
        """
        <map> - switch current map
        """
        if not data:
            client.message('^7missing data, try ^3!^7help map')
            return

        match = self.getMapsSoundingLike(data)
        if isinstance(match, list):
            client.message('^7do you mean: %s?' % ', '.join(match[:5]))
            return

        if isinstance(match, basestring):
            cmd.sayLoudOrPM(client, '^7changing map to ^3%s' % match)
            time.sleep(1)
            self.console.write('map %s' % match)
            return

        # no map found
        client.message('^7could not find any map matching ^1%s' % data)

    def cmd_pasetnextmap(self, data, client=None, cmd=None):
        """
        <mapname> - Set the nextmap (partial map name works)
        """
        if not data:
            client.message('^7missing data, try ^3!^7help setnextmap')
            return

        match = self.getMapsSoundingLike(data)
        if isinstance(match, list):
            client.message('^7do you mean: %s?' % ', '.join(match[:5]))
            return

        if isinstance(match, basestring):
            self.console.setCvar('g_nextmap', match)
            if client:
                client.message('^7nextmap set to ^3%s' % match)
            return

        # no map found
        client.message('^7could not find any map matching ^1%s' % data)

    def cmd_maps(self, data, client=None, cmd=None):
        """
        List the server map rotation
        """
        if not self.adminPlugin.aquireCmdLock(cmd, client, 60, True):
            client.message('^7do not spam commands')
            return
        
        maps = self.console.getMaps()
        if maps is None:
            client.message('^1ERROR: ^7could not get map list')
            return
    
        if not len(maps):
            cmd.sayLoudOrPM(client, '^7map rotation list is empty')
            return
        
        maplist = []
        for m in maps:
            if self._skip_standard_maps:
                if m.lower() in self.standard_maplist:
                    continue
            maplist.append(m)

        if not len(maplist):
            cmd.sayLoudOrPM(client, '^7map rotation list is empty')
            return
            
        # display the map rotation
        cmd.sayLoudOrPM(client, '^7map rotation: %s' % ', '.join(maplist))