# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2010 GrosBedo
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

import b3
import b3.plugin
import b3.output
import logging
import os.path
import time
import threading

from b3 import functions
from ConfigParser import NoOptionError

try:
    import paramiko
except ImportError, ee:
    paramiko = None # just to remove a warning
    log = b3.output.getInstance()
    log.critical("Missing module paramiko. The paramiko module is required to connect with SFTP. "
                 "Install pycrypto from http://www.voidspace.org.uk/python/modules.shtml#pycrypto and "
                 "paramiko from http://www.lag.net/paramiko/")
    raise ee

__version__ = '1.3'
__author__ = 'Courgette'


class SftpytailPlugin(b3.plugin.Plugin):

    requiresConfigFile = False
    default_connection_timeout = 30  # time (in sec) to wait before reconnecting after loosing FTP connection
    default_maxGap = 20480           # max gap in bytes between remote file and local file

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
        b3.plugin.Plugin.__init__(self, console, config)
        self._maxGap = SftpytailPlugin.default_maxGap
        self._waitBeforeReconnect = 15
        self._connectionTimeout = SftpytailPlugin.default_connection_timeout
        self._nbConsecutiveConnFailure = 0
        self._logAppend = False
        self._publicIp = None
        self._remoteFileOffset = None
        self._sftpdelay = 0.150
        self.buffer = None
        self.file = None
        self.lgame_log = None
        self.sftpconfig = None
        self.known_hosts_file = None
        self.private_key_file = None

    def onStartup(self):
        """
        Initialize plugin.
        """
        if self.console.config.has_option('server', 'delay'):
            self._sftpdelay = self.console.config.getfloat('server', 'delay')
        
        if self.console.config.has_option('server', 'local_game_log'):
            self.lgame_log = self.console.config.getpath('server', 'local_game_log')
        else:
            self.lgame_log = os.path.normpath(os.path.expanduser(self.console.input.name))

        self.lgame_log = b3.getWritableFilePath(self.lgame_log)
        self.debug('local game log is: %s' % self.lgame_log)

        if self.console.config.get('server', 'game_log')[0:7] == 'sftp://':
            self.init_thread(self.console.config.get('server', 'game_log'))

        if self.console.config.has_option('server', 'log_append'):
            self._logAppend = self.console.config.getboolean('server', 'log_append')
        else:
            self._logAppend = False

        # get rid of "no handler found for paramiko.transport" errors
        paramiko_logger = logging.getLogger('paramiko')
        paramiko_logger.handlers = [logging.NullHandler()]
        paramiko_logger.propagate = False

    def onLoadConfig(self):
        """
        Load configuration file.
        """
        if self.config is None:
            return
        try:
            self._connectionTimeout = self.config.getint('settings', 'timeout')
            if self._connectionTimeout < 0:
                raise ValueError("timeout cannot be negative")
            self.debug('loaded settings/timeout: %s' % self._connectionTimeout)
        except NoOptionError:
            self.warning('could not find settings/timeout in config file, '
                         'using default: %s' % self._connectionTimeout)
        except ValueError, e:
            self._connectionTimeout = SftpytailPlugin.default_connection_timeout
            self.error('could not load settings/timeout config value: %s' % e)
            self.debug('using default value (%s) for settings/timeout' % self._connectionTimeout)

        try:
            self._maxGap = self.config.getint('settings', 'maxGapBytes')
            if self._maxGap < 0:
                raise ValueError("maxGapBytes cannot be negative")
            self.debug('loaded settings/maxGapBytes: %s' % self._maxGap)
        except NoOptionError:
            self.warning('could not find settings/maxGapBytes in config file, '
                         'using default: %s' % self._maxGap)
        except ValueError, e:
            self._maxGap = SftpytailPlugin.default_maxGap
            self.error('could not load settings/maxGapBytes config value: %s' % e)
            self.debug('using default value (%s) for settings/maxGapBytes' % self._maxGap)

        try:
            self.known_hosts_file = self.config.getpath('settings', 'known_hosts_file')
            if not os.path.isfile(self.known_hosts_file):
                raise ValueError("known_host file %r does not exists" % self.known_hosts_file)
            self.debug('loaded settings/known_hosts_file: %s' % self.known_hosts_file)
        except (NoOptionError, KeyError):
            pass
        except ValueError, e:
            self.known_hosts_file = None
            self.error('could not load settings/known_host config value: %s' % e)
            self.debug('known_host_file set to: %r' % self.known_hosts_file)

        try:
            self.private_key_file = self.config.getpath('settings', 'private_key_file')
            if not os.path.isfile(self.private_key_file):
                raise ValueError("private key file %r does not exists" % self.private_key_file)
            self.debug('loaded settings/private_key_file: %s' % self.private_key_file)
        except (NoOptionError, KeyError):
            pass
        except ValueError, e:
            self.private_key_file = None
            self.error('could not load settings/private_key_file config value: %s' % e)
            self.debug('private_key_file set to: %r' % self.private_key_file )

    def init_thread(self, ftpfiledsn):
        self.sftpconfig = functions.splitDSN(ftpfiledsn)
        thread1 = threading.Thread(target=self.update)
        self.info("starting sftpytail thread")
        thread1.start()
        return thread1

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
            self.verbose('received %s bytes' % len(block))
            self._remoteFileOffset += len(block)
            if self.buffer is None:
                self.buffer = block
            else:
                self.buffer = self.buffer + block
        transport = sftp = None
        rfile = None
        self.file = open(self.lgame_log, 'ab')
        self.file.write('\r\n')
        self.file.write('B3 has been restarted\r\n')
        self.file.write('\r\n')
        while self.console.working:
            try:
                if not sftp:
                    transport, sftp = self.sftpconnect()
                    rfile = None
                    self._nbConsecutiveConnFailure = 0
                try:
                    #self.verbose("Getting remote file size for %s" % self.sftpconfig['path'])
                    remotesize = sftp.stat(self.sftpconfig['path']).st_size
                    #self.verbose("Remote file size is %s" % remoteSize)
                except IOError, err:
                    self.critical(err)
                    raise err
                if self._remoteFileOffset is None:
                    self._remoteFileOffset = remotesize
                if remotesize < self._remoteFileOffset:
                    self.debug("remote file rotation detected")
                    self._remoteFileOffset = 0
                if remotesize > self._remoteFileOffset:
                    if (remotesize - self._remoteFileOffset) > self._maxGap:
                        gap = remotesize - self._remoteFileOffset
                        self.verbose('gap between local and remote file too large (%s bytes)', gap)
                        self.verbose('downloading only the last %s bytes' % self._maxGap)
                        self._remoteFileOffset = remotesize - self._maxGap
                    #self.debug('RETR from remote offset %s. (expecting to read at least %s bytes)' % (
                    #           self._remoteFileOffset, remoteSize - self._remoteFileOffset))
                    if not rfile:
                        self.debug('opening remote game log file %s for reading' % self.sftpconfig['path'])
                        rfile = sftp.open(self.sftpconfig['path'], 'r')
                    rfile.seek(self._remoteFileOffset)
                    self.debug('reading remote game log file from offset %s' % self._remoteFileOffset)
                    handle_download(rfile.read())
                    if self.buffer:
                        self.file.write(self.buffer)
                        self.buffer = None
                        self.file.flush()
                    if self.console._paused:
                        self.console.unpause()
                        self.debug('Unpausing')
            except paramiko.SSHException, err:
                self.warning(str(err))
                self._nbConsecutiveConnFailure += 1
                self.verbose('lost connection to server: pausing until updated properly')
                if self.console._paused is False:
                    self.console.pause()
                self.file.close()
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
                    if rfile is not None:
                        rfile.close()
                    if transport is not None:
                        transport.close()
                    self.debug('sFTP connection closed')
                except IOError:
                    pass
                rfile = None
                sftp = None
                
                if self._nbConsecutiveConnFailure <= 30:
                    time.sleep(1)
                else:
                    self.debug('too many failures: sleeping %s sec' % self._waitBeforeReconnect)
                    time.sleep(self._waitBeforeReconnect)
            time.sleep(self._sftpdelay)

        self.verbose("B3 is down: stopping sFtpytail thread")

        try:
            rfile.close()
        except IOError:
            pass
        try:
            transport.close()
        except IOError:
            pass
        try:
            self.file.close()
        except IOError:
            pass
    
    def sftpconnect(self):
        """
        Connect to the sFTP server.
        """
        hostname = self.sftpconfig['host']
        port = self.sftpconfig['port']
        username = self.sftpconfig['user']
        password = self.sftpconfig['password']
        
        # get host key, if we know one
        hostkey = None
        host_keys = self.get_host_keys()
        if hostname in host_keys:
            hostkeytype = host_keys[hostname].keys()[0]
            hostkey = host_keys[hostname][hostkeytype]
            self.info('using host key of type %s' % hostkeytype)

        self.info('connecting to %s ...', self.sftpconfig["host"])
        # now, connect and use paramiko Transport to negotiate SSH2 across the connection
        t = paramiko.Transport((hostname, port))
        private_key = self.get_private_key(password)
        if private_key is None:
            t.connect(username=username, password=password, hostkey=hostkey)
        else:
            t.connect(username=username, hostkey=hostkey, pkey=private_key)
        sftp = paramiko.SFTPClient.from_transport(t)
        channel = sftp.get_channel()
        channel.settimeout(self._connectionTimeout)
        self.console.clients.sync()
        self.info("connection successful")
        return t, sftp

    def get_host_keys_file(self):
        """
        Get the path of the host keys file.
        The host key file can either be defined in the plugin config file or well known locations:
            ~/.ssh/known_hosts
            ~/ssh/known_hosts
        """
        host_keys_file = self.known_hosts_file
        for potential_location in ['~/.ssh/known_hosts', '~/ssh/known_hosts']:
            if host_keys_file is not None:
                break
            path = b3.getAbsolutePath(potential_location)
            if os.path.isfile(path):
                host_keys_file = path
        return host_keys_file

    def get_host_keys(self):
        host_keys_file = self.get_host_keys_file()
        host_keys = {}
        try:
            host_keys = paramiko.util.load_host_keys(host_keys_file)
        except Exception, err:
            self.warning("cannot read host keys file: %r. " % host_keys_file, exc_info=err)
        return host_keys

    def get_private_key(self, password=None):
        if self.private_key_file is not None:
            with open(self.private_key_file, "r") as f:
                key_head = f.readline()
            if 'DSA' in key_head:
                key_type = paramiko.DSSKey
            elif 'RSA' in key_head:
                key_type = paramiko.RSAKey
            else:
                raise ValueError("can't identify private key type")
            with open(self.private_key_file, "r") as f:
                return key_type.from_private_key(f, password=password)