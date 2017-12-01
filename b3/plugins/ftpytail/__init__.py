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
 
__version__ = '1.10'
__author__ = 'Bakes, Courgette'

import b3
import b3.plugin
import os.path
import threading
import ftplib
import time

from ConfigParser import NoOptionError
from ftplib import FTP
from b3 import functions


class FtpytailPlugin(b3.plugin.Plugin):

    requiresConfigFile = False
    buffer = None
    file = None
    ftpconfig = None
    lgame_log = None
    url_path = None

    ### settings
    _maxGap = 20480                  # max gap in bytes between remote file and local file
    _maxConsecutiveConnFailure = 30  # after that amount of consecutive failure, pause the bot for _long_delay seconds

    # time (in sec) to wait before reconnecting after loosing
    # FTP connection (if _nbConsecutiveConnFailure < _maxConsecutiveConnFailure)
    _short_delay = 1

    # time (in sec) to wait before reconnecting after loosing
    # FTP connection (if _nbConsecutiveConnFailure > _maxConsecutiveConnFailure)
    _long_delay = 15
    _connectionTimeout = 30
    _remoteFileOffset = None
    _nbConsecutiveConnFailure = 0
    _logAppend = False
    _ftplib_debug_level = 0         # 0: no debug, 1: normal debug, 2: extended debug
    
    _gamelog_read_delay = 0.150
    _use_windows_cache_fix = False
    _cache_refresh_delay = 1

    ####################################################################################################################
    #                                                                                                                  #
    #    STARTUP                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def onStartup(self):
        """
        Initialize plugin
        """
        if self.console.config.has_option('server', 'delay'):
            self._gamelog_read_delay = self.console.config.getfloat('server', 'delay')
        
        if self.console.config.has_option('server', 'local_game_log'):
            self.lgame_log = self.console.config.getpath('server', 'local_game_log')
        else:
            self.lgame_log = os.path.normpath(os.path.expanduser(self.console.input.name))

        self.lgame_log = b3.getWritableFilePath(self.lgame_log)
        self.debug('local game log is: %s' % self.lgame_log)

        if self.console.config.get('server', 'game_log')[0:6] == 'ftp://':
            self.init_thread(self.console.config.get('server', 'game_log'))
            
        if self.console.config.has_option('server', 'log_append'):
            self._logAppend = self.console.config.getboolean('server', 'log_append')
        else:
            self._logAppend = False
    
    def onLoadConfig(self):
        """
        Load plugin configuration.
        """
        # These values go in b3 xml, so check them first
        try:
            self._use_windows_cache_fix = self.console.config.getboolean('server', 'use_windows_cache_fix')
            self.debug('loaded server/use_windows_cache_fix: %s' % self._use_windows_cache_fix)
        except NoOptionError:
            self.debug('could not find server/use_windows_cache_fix in B3 config file, '
                       'using default: %s' % self._use_windows_cache_fix)
        except ValueError, e:
            self.error('could not load server/use_windows_cache_fix config value from B3 config file: %s' % e)
            self.debug('using default value (%s) for use_windows_cache_fix' % self._use_windows_cache_fix)

        if self._use_windows_cache_fix:

            try:
                self._cache_refresh_delay = self.console.config.getint('server', 'cache_refresh_delay')
                self.debug('loaded server/cache_refresh_delay: %s' % self._cache_refresh_delay)
            except NoOptionError:
                self.debug('could not find server/cache_refresh_delay in B3 config file, '
                         'using default: %s' % self._cache_refresh_delay)
            except ValueError, e:
                self.error('could not load server/cache_refresh_delay config value from B3 config file: %s' % e)
                self.debug('using default value (%s) for server/cache_refresh_delay' % self._cache_refresh_delay)

        # see if ftpytail has a config file before trying to load the rest of the values
        if self.config is None:
            return

        try:
            self._connectionTimeout = self.config.getint('settings', 'timeout')
            self.debug('loaded settings/timeout: %s' % self._connectionTimeout)
        except NoOptionError:
            self.warning('could not find settings/timeout in config file, '
                         'using default: %s' % self._connectionTimeout)
        except ValueError, e:
            self.error('could not load settings/timeout config value: %s' % e)
            self.debug('using default value (%s) for settings/timeout' % self._connectionTimeout)

        try:
            self._maxGap = self.config.getint('settings', 'maxGapBytes')
            self.debug('loaded settings/maxGapBytes: %s' % self._maxGap)
        except NoOptionError:
            self.warning('could not find settings/maxGapBytes in config file, '
                         'using default: %s' % self._maxGap)
        except ValueError, e:
            self.error('could not load settings/maxGapBytes config value: %s' % e)
            self.debug('using default value (%s) for settings/maxGapBytes' % self._maxGap)

        try:
            self._maxConsecutiveConnFailure = self.config.getint('settings', 'max_consecutive_failures')
            self.debug('loaded settings/max_consecutive_failures: %s' % self._maxConsecutiveConnFailure)
        except NoOptionError:
            self.warning('could not find settings/max_consecutive_failures in config file, '
                         'using default: %s' % self._maxConsecutiveConnFailure)
        except ValueError, e:
            self.error('could not load settings/max_consecutive_failures config value: %s' % e)
            self.debug('using default value (%s) for settings/max_consecutive_failures' % self._maxConsecutiveConnFailure)

        try:
            self._short_delay = self.config.getfloat('settings', 'short_delay')
            self.debug('loaded settings/short_delay: %s' % self._short_delay)
        except NoOptionError:
            self.warning('could not find settings/short_delay in config file, '
                         'using default: %s' % self._short_delay)
        except ValueError, e:
            self.error('could not load settings/short_delay config value: %s' % e)
            self.debug('using default value (%s) for settings/short_delay' % self._short_delay)

        try:
            self._long_delay = self.config.getint('settings', 'long_delay')
            self.debug('loaded settings/long_delay: %s' % self._long_delay)
        except NoOptionError:
            self.warning('could not find settings/long_delay in config file, '
                         'using default: %s' % self._long_delay)
        except ValueError, e:
            self.error('could not load settings/long_delay config value: %s' % e)
            self.debug('using default value (%s) for settings/long_delay' % self._long_delay)

        self.info("until %s consecutive errors are met, the bot will wait for %s seconds (short_delay), "
                  "then it will wait for %s seconds (long_delay)" % (self._maxConsecutiveConnFailure,
                                                                     self._short_delay, self._long_delay))

    def init_thread(self, ftpfiledsn):
        self.ftpconfig = functions.splitDSN(ftpfiledsn)
        # the '/' is not part of the uri-path according to RFC 1738 3.1. Common Internet Scheme Syntax
        self.url_path = self.ftpconfig['path'][1:]
        thread1 = threading.Thread(target=self.update)
        self.info("starting ftpytail thread")
        thread1.start()

    ####################################################################################################################
    #                                                                                                                  #
    #    OTHER METHODS                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def update(self):
        """
        Update the local log file.
        """
        def handle_download(block):
            #self.debug('received %s bytes' % len(block))
            self._remoteFileOffset += len(block)
            if self.buffer is None:
                self.buffer = block
            else:
                self.buffer = self.buffer + block
        
        def force_windows_cache_reload(_):
            # no need to do anything here so
            return
            
        ftp = None
        self.file = open(self.lgame_log, 'ab')
        self.file.write('\r\n')
        self.file.write('B3 has been restarted\r\n')
        self.file.write('\r\n')

        while self.console.working:

            try:

                if not ftp:

                    try:
                        ftp = self.ftpconnect()
                    except Exception, e:
                        self.error('could not connect with FTP server: %s' % e)
                        self.console.working = False
                        break
                    else:
                        self._nbConsecutiveConnFailure = 0
                        remotesize = ftp.size(os.path.basename(self.url_path))
                        self.verbose("connection successful: remote file size is %s" % remotesize)
                        if self._remoteFileOffset is None:
                            self._remoteFileOffset = remotesize
                        
                if self._use_windows_cache_fix:
                    time.sleep(self._cache_refresh_delay)
                    ftp.retrbinary('RETR ' + os.path.basename(self.url_path),
                                   force_windows_cache_reload, 1,
                                   rest=self._remoteFileOffset)
                    
                remotesize = ftp.size(os.path.basename(self.url_path))
                if remotesize < self._remoteFileOffset:
                    self.debug("remote file rotation detected")
                    self._remoteFileOffset = 0
                if remotesize > self._remoteFileOffset:
                    if (remotesize - self._remoteFileOffset) > self._maxGap:
                        gap = remotesize - self._remoteFileOffset
                        self.debug('gap between local and remote file too large (%s bytes)', gap)
                        self.debug('downloading only the last %s bytes' % self._maxGap)
                        self._remoteFileOffset = remotesize - self._maxGap
                    #self.debug('RETR from remote offset %s. (expecting to read at least %s '
                    #           'bytes)' % (self._remoteFileOffset, remoteSize - self._remoteFileOffset))
                    ftp.retrbinary('RETR ' + os.path.basename(self.url_path),
                                   handle_download,
                                   rest=self._remoteFileOffset)

                    if self.buffer:
                        self.file.write(self.buffer)
                        self.buffer = None
                        self.file.flush()

                    if self.console._paused:
                        self.console.unpause()
                        self.debug('unpausing')

            except ftplib.all_errors, e:
                self.debug(str(e))
                self._nbConsecutiveConnFailure += 1
                if self.console._paused is False:
                    self.console.pause()
                self.file.close()
                self.debug('FTP error: resetting local log file?')
                if self._logAppend:
                    try:
                        self.file = open(self.lgame_log, 'ab')
                        self.file.write('\r\n')
                        self.file.write('B3 has restarted writing the log file\r\n')
                        self.file.write('\r\n')
                    except IOError:
                        self.file = open(self.lgame_log, 'w')
                else:
                    self.file = open(self.lgame_log, 'w')

                self.file.close()
                self.file = open(self.lgame_log, 'ab')

                try:
                    ftp.close()
                    self.debug('FTP connection closed')
                except IOError:
                    pass

                ftp = None
                
                if self._nbConsecutiveConnFailure <= self._maxConsecutiveConnFailure:
                    time.sleep(self._short_delay)
                else:
                    self.debug('too many failures: sleeping %s sec' % self._long_delay)
                    time.sleep(self._long_delay)
            time.sleep(self._gamelog_read_delay)

        self.verbose("stopping Ftpytail update thread")

        try:
            ftp.close()
        except Exception:
            pass
        try:
            self.file.close()
        except Exception:
            pass
    
    def ftpconnect(self):
        self.verbose('connecting to %s:%s ...' % (self.ftpconfig["host"], self.ftpconfig["port"]))
        ftp = FTP()
        ftp.set_debuglevel(self._ftplib_debug_level)
        ftp.connect(self.ftpconfig['host'], self.ftpconfig['port'], self._connectionTimeout)
        ftp.login(self.ftpconfig['user'], self.ftpconfig['password'])
        ftp.voidcmd('TYPE I')
        d = os.path.dirname(self.url_path)
        self.debug('trying to cwd to [%s]' % d)
        ftp.cwd(d)
        self.console.clients.sync()
        return ftp
    
    
if __name__ == '__main__':
    from b3.fake import fakeConsole
    
    print "------------------------------------"
    config = b3.config.XmlConfigParser()
    config.setXml("""
    <configuration plugin="ftpytail">
        <settings name="settings">
            <!-- timeout to allow when connecting to FTP server -->
            <set name="timeout">5</set>
            <!-- how much bytes to read at most from game log file's tail (this is to avoid downloading megabytes) -->
            <set name="maxGapBytes">1024</set>
            <!-- The 3 settings below defines how aggressive will be B3 at 
            trying to reconnect after loosing the FTP connection.
            Before 'max_consecutive_failures' connections error, the bot will wait
            'short_delay' seconds before retrying. Then it will wait 'long_delay'. -->
            <set name="max_consecutive_failures">10</set>
            <set name="short_delay">2</set>
            <set name="long_delay">15</set>
        </settings>
    </configuration>
    """)
    p = FtpytailPlugin(fakeConsole, config)
    p.onStartup()

    p.init_thread('ftp://thomas@127.0.0.1/DRIVERS/test.txt')
    time.sleep(120)
    fakeConsole.shutdown()
    time.sleep(8)