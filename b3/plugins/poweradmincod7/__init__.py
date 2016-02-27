#
# PowerAdmin Plugin for BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2011 Freelander - www.fps-gamer.net
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

__version__ = '1.4'
__author__  = 'Freelander'

import b3
import b3.events
import b3.plugin
import os
import threading
import time
import string

from b3.functions import getCmd

class Poweradmincod7Plugin(b3.plugin.Plugin):

    requiresParsers = ['cod7']

    _adminPlugin = None
    _isranked = None
    _issetmap = False
    _isplaylist_enabled = True
    _admin_excluded_maps = None
    
    _cod7maps = { 
        'mp_array': 'array',
        'mp_cracked': 'cracked',
        'mp_crisis': 'crisis',
        'mp_firingrange': 'firing range',
        'mp_duga': 'grid',
        'mp_hanoi': 'hanoi',
        'mp_cairo': 'havana',
        'mp_havoc': 'jungle',
        'mp_cosmodrome': 'launch',
        'mp_nuked': 'nuketown',
        'mp_radiation': 'radiation',
        'mp_mountain': 'summit',
        'mp_villa': 'villa',
        'mp_russianbase': 'wmd',
        'mp_berlinwall2': 'berlin wall',
        'mp_discovery': 'discovery',
        'mp_kowloon': 'kowloon',
        'mp_stadium': 'stadium',
        'mp_gridlock': 'convoy',
        'mp_hotel': 'hotel',
        'mp_outskirts': 'stockpile',
        'mp_zoo': 'zoo',
        'mp_area51': 'hangar 18',
        'mp_drivein': 'drive-in',
        'mp_silo': 'silo',
        'mp_golfcourse': 'hazard'
    }

    _playlists = {
        1: 'Team Deathmatch',
        2: 'Free For All',
        3: 'Capture The Flag',
        4: 'Search & Destroy',
        5: 'Headquarters',
        6: 'Domination',
        7: 'Sabotage',
        8: 'Demolition',
        9: 'Hardcore Team Deathmatch',
        10: 'Hardcore Free For All',
        11: 'Hardcore Capture The Flag',
        12: 'Hardcore Search & Destroy',
        13: 'Hardcore Headquarters',
        14: 'Hardcore Domination',
        15: 'Hardcore Sabotage',
        16: 'Hardcore Demolition',
        17: 'Barebones Team Deathmatch',
        18: 'Barebones Free For All',
        19: 'Barebones Capture The Flag',
        20: 'Barebones Search & Destroy',
        21: 'Barebones Headquarters',
        22: 'Barebones Domination',
        23: 'Barebones Sabotage',
        24: 'Barebones Demolition',
        25: 'Team Tactical'
    }

    ####################################################################################################################
    #                                                                                                                  #
    #    STARTUP                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def onStartup(self):
        """
        Initialize plugin settings
        """
        # get the admin plugin so we can register commands
        self._adminPlugin = self.console.getPlugin('admin')
        if not self._adminPlugin:
            # something is wrong, can't start without admin plugin
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

        # register our events
        self.registerEvent('EVT_GAME_ROUND_START', self.onGameRoundStart)

        # check if server is ranked/unranked
        self._isranked = self.isranked()
        self.debug('This server is %s' % 'ranked' if self._isranked else 'unranked')
        if not self._isranked:
            # check playlist status
            self._isplaylist_enabled = self.isplaylist_enabled()

        # get maplist excluded by server admin
        m = self.console.getCvar('playlist_excludeMap')
        if m:
            self._admin_excluded_maps = m.value
            if self._admin_excluded_maps != '':
                self.debug('Excluded maps by admin are: %s' % self._admin_excluded_maps)
            else:
                self.debug('No maps found in map exclusion list')

    def onGameRoundStart(self, _):
        """
        Handle EVT_GAME_ROUND_START.
        """
        if self._issetmap:
            self.console.write ('setadmindvar playlist_excludeMap "%s"' % self._admin_excluded_maps, maxRetries=5)
            self._issetmap = False
            self.debug('clearing map exclusion list')

    ####################################################################################################################
    #                                                                                                                  #
    #    COMMANDS                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def cmd_paplaylist(self, data, client, cmd):
        """
        Display current playlist.
        (You can safely use the command without the 'pa' at the beginning)
        """
        cvar = self.console.getCvar('playlist')
        if cvar:
            playlist = cvar.getInt()
            cmd.sayLoudOrPM(client, '^7Current Playlist is ^3%s - %s' % (playlist, self._playlists[playlist]))

    def cmd_pagetplaylists(self, data, client, cmd):
        """
        Display available playlists
        (You can safely use the command without the 'pa' at the beginning)
        """
        for n, p in sorted(self._playlists.iteritems()):
            cmd.sayLoudOrPM(client, '%s - %s' % (n, p))
            time.sleep(1)

    def cmd_pasetplaylist(self, data, client, cmd):
        """
        <playlist_number> - Set a playlist
        (You can safely use the command without the 'pa' at the beginning)
        """
        if not self._isplaylist_enabled and not self._isranked:
            client.message('Playlists are not enabled in this server. You can\'t set a playlist!')
            return

        _number_of_playlists = len(self._playlists)

        if not data:
            client.message('missing parameter, try !help pasetplaylist')
            return

        try:
            float(data)
        except ValueError:
            client.message('Please use a playlist number, %s is not a numeric value' % data)
            return

        data = int(data)
        if data not in range(1, _number_of_playlists + 1):
            client.message('Playlist number %s out of range! Please enter a valid number' % data)
        else:
            self.console.write('setadmindvar playlist %s' % data, maxRetries=5)
            client.message('Changing playlist to ^3%s - %s' % (data, self._playlists[data]))

    def cmd_pasetmap(self, data, client, cmd=None):
        """
        <mapname> - Set the next map in rotation
        (You can safely use the command without the 'pa' at the beginning)
        """
        if not self._isranked:
            client.message('This command is not functional in unranked servers. '
                           'You can use ^2!map ^7or ^2!maprotate ^7 commands instead.')
            return

        if not data:
            client.message('missing parameter, try !help pasetmap')
            return

        self.debug('Requested map for next round is %s' % data)
        data = data.lower()

        if data in self._cod7maps.keys():
            mapname = data
            self.debug('%s is a console mapname' % data)
        elif ('mp_%s' % data) in self._cod7maps.keys():
            mapname = ('mp_%s' % data)
            self.debug('%s is considered to be %s' % (data, mapname))
        elif data in self._cod7maps.values():
            cod7maps_inverse = dict((self._cod7maps[k], k) for k in self._cod7maps)
            mapname = cod7maps_inverse[data]
            self.debug('%s is an easy mapname, console name is %s' % (data, mapname))
        else:
            client.message('%s is not a stock CoD7 map, please check your spelling and try again!' % data)
            return

        excludeMaps = self._cod7maps.keys()
        excludeMaps.remove(mapname)
        self.console.write('setadmindvar playlist_excludeMap "%s"' % ' '.join(excludeMaps), maxRetries=5)
        client.message('Setting map ^3%s for next round' % self._cod7maps[mapname].title())
        self._issetmap = True

    def cmd_paexcludemaps(self, data, client, cmd=None):
        """
        <mapnames> Excludes entered maps from rotation. 
        Leave a space between mapnames. Example: !paexludemaps mp_villa mp_nuked mp_array
        (You can safely use the command without the 'pa' at the beginning)
        """
        if not self._isplaylist_enabled and not self._isranked:
            client.message('Playlists are not enabled in this server. You can\'t make an exclusion list!')
            return

        if not data:
            client.message('missing parameter, try !help pasetplaylist')
            return

        # check if mapnames typed correctly
        mapnames = data.split(' ')
        for m in mapnames:
            if m not in self._cod7maps.keys():
                client.message('%s is not a valid mapname, please check your spelling and try again' % m)
                return False

        self.console.write('setadmindvar playlist_excludeMap "%s"' % data, maxRetries=5)
        # updating exclusion list variable
        self._admin_excluded_maps = data
        self.debug('Maps: %s excluded from current playlist' % mapnames)

    def cmd_paversion(self, data, client, cmd=None):
        """
        This command identifies PowerAdminCoD7 version and creator.
        """
        cmd.sayLoudOrPM(client, 'I am PowerAdminCoD7 version %s by %s' % (__version__, __author__))

    def cmd_paident(self, data, client, cmd=None):
        """
        [<name>] - show the ip and guid of a player
        """
        x = self._adminPlugin.parseUserCmd(data)
        if not x:
            try:
                cmd.sayLoudOrPM(client, '%s: %s - %s' % (client.name, client.ip, client.guid))
            except Exception, err:
                client.message('Error, server replied %s' % err)
        else:
            try:
                sclient = self._adminPlugin.findClientPrompt(x[0], client)
                if sclient:
                    cmd.sayLoudOrPM(client, '%s: %s - %s' % (sclient.name, sclient.ip, sclient.guid))
            except Exception, err:
                client.message('Error, server replied %s' % err)

    def cmd_paset(self, data, client, cmd=None):
        """
        <cvar> <value> - Set a server cvar to a certain value.
        (You must use the command exactly as it is! )
        """
        if not data:
            client.message('^7Invalid or missing data, try !help paset')
        else:
            x = data.split(' ',1)
            cvarName = x[0].lower()
            value = x[1]
            self.console.setCvar(cvarName, value)
            client.message('Setting %s to %s' % (cvarName, value))
            # check if we are setting a new map exclusion list
            # then we'll need to update exclusion list made by server admin
            if cvarName.lower() == 'playlist_excludemap':
                self._admin_excluded_maps = value

    def cmd_paget(self, data, client, cmd=None):
        """
        <cvar> - Returns the value of a servercvar.
        (You must use the command exactly as it is! )
        """
        if not data:
            client.message('^7Invalid or missing data, try !help paget')
        else:
            # are we still here? Let's write it to console
            getcvar = data.split(' ')
            getcvarvalue = self.console.getCvar( '%s' % getcvar[0] )
            cmd.sayLoudOrPM(client, '%s' % getcvarvalue)

    def cmd_pafastrestart(self, data, client, cmd):
        """
        Restart a map without reloading it
        (You can safely use the command without the 'pa' at the beginning)
        """
        if self._isranked:
            client.message('You can\'t restart a map on ranked servers')
        else:
            self.console.say('Fast restarting map in 2 seconds...')
            time.sleep(2)
            self.console.write('fast_restart', maxRetries=5)

    def cmd_pamaprestart(self, data, client, cmd):
        """
        Restart a map
        (You can safely use the command without the 'pa' at the beginning)
        """
        if self._isranked:
            client.message('You can\'t restart a map on ranked servers')
        else:
            self.console.say('Restarting map in 2 seconds...')
            time.sleep(2)
            self.console.write('map_restart', maxRetries=5)

    def cmd_pagametype(self, data, client, cmd):
        """
        <gametype> Change gametype. Example: !gametype tdm
        (You can safely use the command without the 'pa' at the beginning)
        """
        if self._isranked:
            client.message('This command is not available on ranked servers!')
            return

        gametypes = { 
            'dm' : 'Free-For-All',
            'tdm' : 'Team Deathmatch',
            'sd' : 'Search and Destroy',
            'dom' : 'Domination',
            'sab' : 'Sabotage',
            'ctf' : 'Capture the Flag',
            'koth' : 'Headquarters',
            'dem' : 'Demolition',
            'oic' : 'One in the Chamber',
            'hlnd' : 'Sticks and Stones',
            'gun' : 'Gun Game',
            'shrp' : 'Sharpshooter'
        }

        if not data:
            client.message('missing parameter, try !help pagametype')
        else:
            # check if gametype is valid
            data = data.split(' ')
            gametype = data[0].lower()
            for g in gametypes:
                if gametype not in gametypes.keys():
                    client.message('^3%s ^7is not a valid gametype, please try again!' % gametype)
                    return False

            self.console.say('Changing gametype to %s, map will restart in 5 seconds' % gametypes[gametype])
            self.console.write('g_gametype %s' % gametype, maxRetries=5)
            time.sleep(5)
            self.console.write('map_restart', maxRetries=5)

    def cmd_pasetdlc(self, data, client, cmd):
        """
        <dlc number> <on | off> - Turn given DLC mappack on or off. Example: !pasetdlc 1 off.
        (You can safely use the command without the 'pa' at the beginning)
        """
        if not data:
            client.message('Missing parameter, try !help pasetdlc')
        else:
            data = data.split(' ')
            if len(data) < 2:
                client.message('Missing parameter, try !help pasetdlc')
                return

            if not data[0].isdigit():
                client.message('Invalid DLC number!')
                return
            else:
                data[0] = int(data[0])
                # Treyarch is counting DLC numbers starting from 2
                dlcnumber = data[0] + 1

            if data[1].lower() in ('on', 'off'):
                if data[1].lower() == 'off':
                    self.console.write('setadmindvar playlist_excludeDlc%s "1"' % dlcnumber, maxRetries=5)
                    client.message('DLC%s Mappack is OFF' % data[0])
                if data[1].lower() == 'on':
                    self.console.write('setadmindvar playlist_excludeDlc%s "0"' % dlcnumber, maxRetries=5)
                    client.message('DLC%s Mappack is ON' % data[0])
            else:
                print("Invalid data, expecting 'on' or 'off'")

    def cmd_palistcfg(self, data, client, cmd):
        """
        List available server config files in b3 conf folder
        (You can safely use the command without the 'pa' at the beginning)
        """
        config_files = []
        filenames = os.listdir(b3.getConfPath())
        for filename in filenames:
            if filename.endswith('.cfg'):
                config_files.append(filename)

        if not config_files:
            client.message('No server config files found')
        else:
            client.message('^3Available config files are:^7 %s' % string.join(config_files, ', '))

    def cmd_paload(self, data, client, cmd=None):
        """
        <configfile.cfg> - Load a server configfile.
        (You can safely use the command without the 'pa' at the beginning)
        """
        if not data:
            client.message('^7Invalid or missing data, try !help paload')
            return
        if not data.endswith('.cfg'):
            client.message('%s is not a valid server config file!' % data)
            return
        else:
            if not os.path.isfile(os.path.join(b3.getConfPath(), data)):
                client.message("Cannot find file %s in B3 config folder" % data)
            else:
                self.info("Config loader thread is starting")
                client.message("^1Loading %s. This may take a while depending on the file size, please wait..." % data)
                thread_configloader = threading.Thread(target=self._configloader(data))
                thread_configloader.start()
                client.message("^1%s successfully loaded!" % data)

    ####################################################################################################################
    #                                                                                                                  #
    #    OTHER METHODS                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def _configloader(self, configfile):
        """
        Process each line of a config file
        """
        with open(os.path.join(b3.getConfPath(), configfile), 'r') as f:
            for line in f:
                if not line.startswith('//') and not line.startswith('\r\n'):
                    self.console.write(line, maxRetries=5)
                    time.sleep(1)

    def isranked(self):
        """
        Returns true if server is ranked
        """
        rank = self.console.getCvar('sv_ranked')
        return rank and rank.getInt() == 2

    def isplaylist_enabled(self):
        """
        Returns true if playlists are enabled
        """
        status = self.console.getCvar('playlist_enabled')
        if status:
            if status.getBoolean():
                self.debug('Playlist Enabled')
                return True
            else:
                self.debug('Playlist Disabled')
                return False