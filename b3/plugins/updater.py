#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2014 Daniele Pantaleone <fenix@bigbrotherbot.net>
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
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA
#
# CHANGELOG:
#
# 11/12/2014 - 1.0   - Fenix - initial release
# 13/12/2014 - 1.1   - Fenix - minor fixes to version compare
#                            - removed crontab: contacting the update server is not so much expensive in terms of
#                              performances, thus is better to check for an update in real time whenever a superadmin
#                              connects to the server.
#                            - increased _update_check_connect_delay to 30 seconds
# 14/12/2014 - 1.1.1 - Fenix - use B3 autorestart mode to reboot B3 after a successfull B3 update install
# 16/12/2014 - 1.1.2 - Fenix - use EVT_PUNKBUSTER_NEW_CONNECTION instead of EVT_CLIENT_AUTH in Frostbite games

__author__ = 'Fenix'
__version__ = '1.1.2'

import b3
import b3.cron
import b3.events
import b3.functions
import b3.plugin
import json
import os
import re
import sys

from b3 import __version__ as b3_version
from b3.update import B3version
from b3.update import getDefaultChannel
from b3.update import URL_B3_LATEST_VERSION
from tempfile import gettempdir
from threading import Thread
from threading import Timer
from urllib2 import urlopen
from urllib2 import URLError


class UpdateError(Exception):

     def __init__(self, message, throwable=None):
        super(UpdateError, self).__init__(message)
        self.throwable = throwable

     def __str__(self):
         return self.message

     def __repr__(self):
         if not self.throwable:
             return '%s: %s' % (self.__class__.__name__, self.message)
         return '%s: %s - caused by %s: %s' % (self.__class__.__name__, self.message,
                                              self.throwable.__class__.__name__, self.throwable)


class UpdaterPlugin(b3.plugin.Plugin):

    _adminPlugin = None
    _frostBiteGameNames = ['bfbc2', 'moh', 'bf3', 'bf4']
    _re_filename = re.compile(r'''.+/(?P<archive_name>.+)''')
    _re_sql = re.compile(r'''^(?P<script>b3-update-(?P<version>.+)\.sql)$''')
    _socket_timeout = 4
    _update_check_connect_delay = 30
    _updating = False

    ####################################################################################################################
    ##                                                                                                                ##
    ##   STARTUP                                                                                                      ##
    ##                                                                                                                ##
    ####################################################################################################################

    def onStartup(self):
        """
        Initialize plugin settings.
        """
        self._adminPlugin = self.console.getPlugin('admin')
        if not self._adminPlugin:
            self.error('could not start without admin plugin')
            return

        # create an events for a proper B3 shutdown: the updating thread fails to shutdown B3 properly when
        # invoking self.console.die() from whithin the thread itself so we need to to handle this from outside
        self.console.Events.createEvent('EVT_SHUTDOWN_REQUEST', 'Shutdown request')

        # register commands
        self._adminPlugin.registerCommand(self, 'update', 100, self.cmd_update)
        self._adminPlugin.registerCommand(self, 'checkupdate', 100, self.cmd_checkupdate)

        # register events needed
        self.registerEvent(self.console.getEventID('EVT_SHUTDOWN_REQUEST'), self.onShutdownRequest)

        if self.console.gameName in self._frostBiteGameNames:
            self.registerEvent(self.console.getEventID('EVT_PUNKBUSTER_NEW_CONNECTION'), self.onAuth)
        else:
            self.registerEvent(self.console.getEventID('EVT_CLIENT_AUTH'), self.onAuth)

        # notice plugin started
        self.debug('plugin started')

    ####################################################################################################################
    ##                                                                                                                ##
    ##   HANDLE EVENTS                                                                                                ##
    ##                                                                                                                ##
    ####################################################################################################################

    def onShutdownRequest(self, event):
        """
        Handle the request of a B3 shutdown
        :param event: The event to be handled
        """
        client = event.client
        if self.console.autorestart:
            # running autorestart mode, so do not shutdown B3
            client.message("^7Shutting down for restart")
            self.console.restart()
        else:
            client.message('^7Please reboot your B3 manually')
            client.message('^7Shutting down...')
            self.console.die()

    def onAuth(self, event):
        """
        Handle new client authentications
        :param event: The event to be handled
        """
        client = event.client
        if client.maxGroup.id >= 128 and not client.isvar(self, 'check_update'):
            self.debug('superadmin connected: starting update check routine...')
            wthread = Timer(self._update_check_connect_delay, self.check_update, (client,))
            wthread.start()

    ####################################################################################################################
    ##                                                                                                                ##
    ##   OTHER METHODS                                                                                                ##
    ##                                                                                                                ##
    ####################################################################################################################

    def check_update(self, client):
        """
        Announce that a B3 update is available to the given client.
        :param client: The client to notice the update to
        """
        update_data = self.get_update_data(getDefaultChannel(b3_version))
        if update_data:
            client.message('^7Hello %s, a B3 update is available: ^4%s' % (client.name, update_data['latest_version']))
            client.message('^7You are currently running version ^1%s' % update_data['current_version'])
            client.message('^7Type ^3%s^7update in chat to install it' % self._adminPlugin.cmdPrefix)
            client.setvar(self, 'check_update', True)  # do not inform again

    def get_update_data(self, channel):
        """
        Get update data from the update server.
        :param channel: The channel for which to get update data
        :raise UpdateError: If an error occurs while dealing with update information
        :return: A Dict filled with update information if a new B3 version is available, otherwise None
        """
        self.debug('checking for available update on channel %s' % channel)

        try:
            json_data = urlopen(URL_B3_LATEST_VERSION, timeout=self._socket_timeout).read()
        except URLError, err:
            raise UpdateError('could not retrieve update information', err)

        version_info = json.loads(json_data)

        try:
            channels = version_info['B3']['channels']
        except KeyError, err:
            raise UpdateError('could not parse update channels from retrieved data', err)

        if channel not in channels:
            raise UpdateError('unknown channel: %s - expecting %s' % (channel, ', '.join(channels.keys())))

        try:
            lt_version = channels[channel]['latest-version']
        except KeyError, err:
            raise UpdateError('could not retrieve latest version number from %s channel' % channel, err)

        C_version = B3version(b3_version)
        L_version = B3version(lt_version)

        if C_version >= L_version:
            self.debug('B3 is up to date: current version = [%s] - latest version = [%s]' % (b3_version, lt_version))
            return None

        try:

            match = self._re_filename.match(channels[channel]['src-dl'])
            if not match:
                raise UpdateError('could not parse B3 package name from retrieved information')

            self.debug('a new B3 update is available:  current version = [%s] - latest version = [%s]' % (b3_version, lt_version))

            return { 'channel': channel,
                     'current_version': b3_version,
                     'latest_version': lt_version,
                     'package_name': match.group('archive_name'),
                     'source_url': channels[channel]['src-dl'],
                     'url': channels[channel]['url'] }

        except KeyError, err:
            raise UpdateError('could not retrieve download url from %s channel' % channel, err)

    def download_update(self, update_data):
        """
        Download and uncompress B3 update package.
        :param update_data: A Dict filled with update information
        :raise UpdateError: If an error occurs while downloading the update package
        :return: A Tuple with the path of the downloaded update archive and the path of the uncompressed B3 update archive
        """
        # before we do anything else, remove shadow copies being left from previous update attempts
        filepath = os.path.join(gettempdir(), update_data['package_name'])
        archive_directory = b3.functions.split_extension(filepath)[0]

        try:
            b3.functions.rm_file(filepath)
            b3.functions.rm_dir(archive_directory)
        except OSError, err:
            raise UpdateError('could not remove previously downloaded B3 update archive', err)

        self.debug('downloading B3 update [v%s] from %s' % (update_data['latest_version'], update_data['source_url']))

        try:
            response = urlopen(update_data['source_url'], timeout=self._socket_timeout)
        except URLError, err:
            raise UpdateError('could not download update package', err)

        try:
            with open(filepath, "wb") as archive:
                archive.write(response.read())
        except (IOError, OSError), err:
            raise UpdateError('could not store B3 update archive', err)

        self.debug('B3 update package downloaded (%s bytes): %s' % (os.path.getsize(filepath), filepath))

        try:
            self.debug('uncompressing B3 update archive: %s -> %s' % (filepath, archive_directory))
            b3.functions.unzip(filepath, archive_directory)
        except OSError, err:
            raise UpdateError('could not uncompress B3 update archive', err)

        # on some systems when a archive is uncompressed, a duplicate folder used: one to store the
        # uncompressed archive + a subfolder containing the archive files (both have the same name though)
        if not 'b3' in os.listdir(archive_directory):
            match = self._re_filename.match(archive_directory)
            if match:
                archive_directory = os.path.join(archive_directory, match.group('archive_name'))

        return filepath, archive_directory

    def install_update(self, update_data, update_basepath):
        """
        Install the update.
        :param update_data: A Dict filled with update information
        :param update_basepath: The update basepath
        :raise UpdateError: If it's not possible to install the update
        """
        b3_basepath = b3.functions.right_cut(b3.functions.right_cut(sys.path[0], 'b3'), os.path.sep)
        self.debug('installing B3 update: %s -> %s' % (update_basepath, b3_basepath))

        # in the following paths, installer behaviour changes a bit: we won't overwrite file, since we could
        # break users configurations; we will simply copy the new configuration files inside a subfolder so users
        # can manually update them if needed
        b3_config_paths = [os.path.join(b3_basepath, 'b3', 'conf'),
                           os.path.join(b3_basepath, 'b3', 'extplugins', 'conf')]

        for path in b3_config_paths:
            self.verbose('using configuration files path: %s' % path)

        try:

            self.debug('updating B3 files...')

            for root, directories, files in os.walk(update_basepath):

                # this will hold the path in which we are going to copy files over
                b3_current_path = os.path.join(b3_basepath, b3.functions.left_cut(root, update_basepath))
                self.verbose('current b3 path: %s' % b3_current_path)

                # create necessary directories in case there are new: those will be iterated
                # later in the loop when a new root directory will be processed
                for directory in directories:
                    directory_path = os.path.join(b3_current_path, directory)
                    if not os.path.isdir(directory_path):
                        self.verbose('creating directory: %s' % directory_path)
                        b3.functions.mkdir(directory_path)

                if b3_current_path in b3_config_paths:
                    # create a subfolder where to store new configuration files
                    b3.functions.mkdir(os.path.join(b3_current_path, update_data['latest_version']))
                    for filename in files:
                        src = os.path.join(root, filename)
                        dst = os.path.join(b3_current_path, update_data['latest_version'], filename)
                        self.verbose('copying file: %s -> %s' % (src, dst))
                        b3.functions.copy_file(src, dst)
                else:
                    for filename in files:
                        src = os.path.join(root, filename)
                        dst = os.path.join(b3_current_path, filename)
                        self.verbose('copying file: %s -> %s' % (src, dst))
                        b3.functions.copy_file(src, dst)
                        # only check MD5 digest for python modules
                        if b3.functions.split_extension(src)[1] == 'py':
                            loop, maxloop = 0, 5
                            while b3.functions.hash_file(src) != b3.functions.hash_file(dst) and loop < maxloop:
                                self.warning('python module "%s" is corrupted, trying to fix it...' % dst)
                                self.verbose('copying file: %s -> %s' % (src, dst))
                                b3.functions.copy_file(src, dst)
                                loop += 1
                            if loop >= maxloop:
                                raise IOError('python module "%s" is corrupted: could not fix automatically' % dst)

            # update database tables
            self.debug('updating B3 database...')

            # we need to execute all the SQL scripts to update from current version
            b3_sql_path = os.path.join(b3_basepath, 'b3', 'sql')
            b3_sql_files = [m.group("script") for f in os.listdir(b3_sql_path) for m in [self._re_sql.search(f)] if m]

            def sql_cmp(x, y):
                re_sql = re.compile(r'''^(?P<script>b3-update-(?P<version>.+)\.sql)$''')
                x_version = B3version(re_sql.match(x).group('version'))
                y_version = B3version(re_sql.match(y).group('version'))
                if x_version < y_version:
                    return -1
                if x_version > y_version:
                    return 1
                return 0

            b3_sql_files.sort(cmp=sql_cmp)
            b3_current_version = B3version(update_data['current_version'])

            for b3_sql_file in b3_sql_files:
                b3_sql_version = B3version(self._re_sql.match(b3_sql_file).group('version'))
                if b3_sql_version > b3_current_version:
                    b3_sql_filepath = os.path.join(b3_sql_path, b3_sql_file)
                    self.verbose('executing SQL file: %s' % b3_sql_filepath)
                    self.console.storage.queryFromFile(b3_sql_filepath)

        except Exception, err:
            # stop processing the archive whenever an exception is raised
            raise UpdateError('could not install B3 update archive', err)

    def do_update(self, client):
        """
        Threaded code.
        :param client: The client who launched the update
        """
        try:

            self._updating = True
            update_data = self.get_update_data(getDefaultChannel(b3_version))
            if not update_data:
                client.message('^7B3 is up to date')
                client.message('^7you are currently running B3 version ^2%s' % b3_version)
            else:
                client.message('^7B3 update available: ^1%s' % update_data['latest_version'])
                client.message('^7[1/3] downloading update...')
                update_archive, update_basepath = self.download_update(update_data)

                client.message('^7[2/3] installing update...')
                self.install_update(update_data, update_basepath)

                client.message('^7[3/3] completing installation...')

                try:
                    b3.functions.rm_file(update_archive)
                    b3.functions.rm_dir(update_basepath)
                except OSError:
                    # do not bother with errors since this is not strictly needed
                    # and also B3 will remove garbage files on fuiture updates
                    pass

                client.message('^7B3 updated successfully to version ^2%s' % update_data['latest_version'])
                self.console.queueEvent(self.console.getEvent('EVT_SHUTDOWN_REQUEST', client=client))

        except UpdateError, err:
            client.message('^1ERROR:^7 %s' % err)
            self.error('%r' % err)
        finally:
            self._updating = False

    ####################################################################################################################
    ##                                                                                                                ##
    ##   COMMANDS                                                                                                     ##
    ##                                                                                                                ##
    ####################################################################################################################

    def cmd_update(self, data, client, cmd=None):
        """
        - update B3 to the latest available version depeding on the configured update channel
        """
        if self._updating:
            client.message('update already in progress, please wait...')
            return

        uthread = Thread(target=self.do_update, args=(client,))
        uthread.setDaemon(True)
        uthread.start()

    def cmd_checkupdate(self, data, client, cmd=None):
        """
        - checks whether there is a new B3 version available
        """
        update_data = self.get_update_data(getDefaultChannel(b3_version))
        if not update_data:
            client.message('^7B3 is up to date')
            client.message('^7you are currently running B3 version ^2%s' % b3_version)
        else:
            client.message('^7A B3 update is available: ^4%s' % update_data['latest_version'])
            client.message('^7Type ^3%s^7update in chat to install it' % self._adminPlugin.cmdPrefix)
