#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2009 James "Bakes" Baker
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
#
# CHANGELOG:
# 22/10/2010 - 1.0 - Courgette
#   * obbey the SFTP URI scheme as described in http://tools.ietf.org/html/draft-ietf-secsh-scp-sftp-ssh-uri-04
# 07/09/2010 - 0.1.1 - GrosBedo
#   * b3/delay option now specify the delay between each ftp log fetching
#   * b3/local_game_log option to specify the temporary local log name (permits to manage remotely several servers at once)
# 01/09/2010 - 0.1 - Courgette
# * first attempt. Briefly tested. Seems to work


__version__ = '1.0'
__author__ = 'Courgette'
 
import b3, threading
from b3 import functions
import b3.plugin
import os.path
import time
import re
import sys
try:
    import paramiko
except ImportError, e:
    log = b3.output.getInstance()
    log.critical("""Missing module paramiko. The paramiko module is required to connect with SFTP.
Install pycrypto from http://www.voidspace.org.uk/python/modules.shtml#pycrypto and paramiko from http://www.lag.net/paramiko/
""")
    raise e

#--------------------------------------------------------------------------------------------------
class SftpytailPlugin(b3.plugin.Plugin):
    ### settings
    _maxGap = 20480 # max gap in bytes between remote file and local file
    _waitBeforeReconnect = 15 # time (in sec) to wait before reconnecting after loosing FTP connection : 
    _connectionTimeout = 30
    
    requiresConfigFile = False
    sftpconfig = None
    buffer = None
    _remoteFileOffset = None
    _nbConsecutiveConnFailure = 0
    
    _sftpdelay = 0.150
    
    def onStartup(self):
        if self.console.config.has_option('server', 'delay'):
            self._sftpdelay = self.console.config.getfloat('server', 'delay')
        
        if self.console.config.has_option('server', 'local_game_log'):
            self.lgame_log = self.console.config.getfloat('server', 'local_game_log')
        else:
            self.lgame_log = os.path.normpath(os.path.expanduser('games_mp.log'))

        if self.console.config.get('server','game_log')[0:7] == 'sftp://' :
            self.initThread(self.console.config.get('server','game_log'))
        
    def onLoadConfig(self):
        try:
            self._connectionTimeout = self.config.getint('settings', 'timeout')
        except: 
            self.warning("Error reading timeout from config file. Using default value")
        self.info("FTP connection timeout: %s" % self._connectionTimeout)

        try:
            self._maxGap = self.config.getint('settings', 'maxGapBytes')
        except: 
            self.warning("Error reading maxGapBytes from config file. Using default value")
        self.info("Maximum gap allowed between remote and local gamelog: %s bytes" % self._maxGap)
        
    
    def initThread(self, ftpfileDSN):
        self.sftpconfig = functions.splitDSN(ftpfileDSN)
        thread1 = threading.Thread(target=self.update)
        self.info("Starting sftpytail thread")
        thread1.start()
    
    def update(self):
        def handleDownload(block):
            self.debug('received %s bytes' % len(block))
            self._remoteFileOffset += len(block)
            if self.buffer == None:
                self.buffer = block
            else:
                self.buffer = self.buffer + block
        transport = sftp = None
        rfile = None
        self.file = open(self.lgame_log, 'ab')
        while self.console.working:
            try:
                if not sftp:
                    transport, sftp = self.sftpconnect()
                    rfile = None
                    self._nbConsecutiveConnFailure = 0
                try:
                    #self.debug("Getting remote file size for %s" % self.sftpconfig['path'])
                    remoteSize = sftp.stat(self.sftpconfig['path']).st_size
                    #self.verbose("Remote file size is %s" % remoteSize)
                except IOError, e:
                    self.critical(e)
                    raise e
                if self._remoteFileOffset is None:
                    self._remoteFileOffset = remoteSize
                if remoteSize < self._remoteFileOffset:
                    self.debug("remote file rotation detected")
                    self._remoteFileOffset = 0
                if remoteSize > self._remoteFileOffset:
                    if  (remoteSize - self._remoteFileOffset) > self._maxGap:
                        self.debug('gap between local and remote file too large (%s bytes)', (remoteSize - self._remoteFileOffset))
                        self.debug('downloading only the last %s bytes' % self._maxGap)
                        self._remoteFileOffset = remoteSize - self._maxGap
                    #self.debug('RETR from remote offset %s. (expecting to read at least %s bytes)' % (self._remoteFileOffset, remoteSize - self._remoteFileOffset))
                    if not rfile:
                        self.debug('opening remote game log file %s for reading' % self.sftpconfig['path'])
                        rfile = sftp.open(self.sftpconfig['path'], 'r')
                    rfile.seek(self._remoteFileOffset)
                    self.debug('reading remote game log file from offset %s' % self._remoteFileOffset)
                    handleDownload(rfile.read())      
                    if self.buffer:
                        self.file.write(self.buffer)
                        self.buffer = None
                        self.file.flush()
                    if self.console._paused:
                        self.console.unpause()
                        self.debug('Unpausing')
            except (paramiko.SSHException), e:
                self.debug(str(e))
                self._nbConsecutiveConnFailure += 1
                self.verbose('Lost connection to server, pausing until updated properly')
                if self.console._paused is False:
                    self.console.pause()
                self.file.close()
                self.file = open(self.lgame_log, 'w')
                self.file.close()
                self.file = open(self.lgame_log, 'ab')
                try:
                    rfile.close()
                    transport.close()
                    self.debug('sFTP Connection Closed')
                except:
                    pass
                rfile = None
                sftp = None
                
                if self._nbConsecutiveConnFailure <= 30:
                    time.sleep(1)
                else:
                    self.debug('too many failures, sleeping %s sec' % self._waitBeforeReconnect)
                    time.sleep(self._waitBeforeReconnect)
            time.sleep(self._sftpdelay)
        self.verbose("B3 is down, stopping sFtpytail thread")
        try: rfile.close()
        except: pass
        try: transport.close()
        except: pass
        try: self.file.close()
        except: pass
    
    def sftpconnect(self):
        hostname = self.sftpconfig['host']
        port = self.sftpconfig['port']
        username = self.sftpconfig['user']
        password = self.sftpconfig['password']
        
        # get host key, if we know one
        hostkeytype = None
        hostkey = None
        sftp = None
        try:
            host_keys = paramiko.util.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))
        except IOError:
            try:
                # try ~/ssh/ too, because windows can't have a folder named ~/.ssh/
                host_keys = paramiko.util.load_host_keys(os.path.expanduser('~/ssh/known_hosts'))
            except IOError:
                self.debug('*** Unable to open host keys file')
                host_keys = {}
                
        if host_keys.has_key(hostname):
            hostkeytype = host_keys[hostname].keys()[0]
            hostkey = host_keys[hostname][hostkeytype]
            self.info('Using host key of type %s' % hostkeytype)
        self.verbose('Connecting to %s ...', self.sftpconfig["host"])
        
        # now, connect and use paramiko Transport to negotiate SSH2 across the connection
        t = paramiko.Transport((hostname, port))
        t.connect(username=username, password=password, hostkey=hostkey)
        sftp = paramiko.SFTPClient.from_transport(t)
        channel = sftp.get_channel()
        channel.settimeout(self._connectionTimeout)
        self.console.clients.sync()
        self.verbose("Connection successful")
        return (t, sftp)
    
    
if __name__ == '__main__':
    from b3.fake import fakeConsole
    
    print "------------------------------------"
    config = b3.config.XmlConfigParser()
    config.setXml("""
    <configuration plugin="sftpytail">
        <settings name="settings">
            <set name="timeout">15</set>
            <set name="maxGapBytes">1024</set>
        </settings>
    </configuration>
    """)
    p = SftpytailPlugin(fakeConsole, config)

    
    print "------------------------------------"
    p = SftpytailPlugin(fakeConsole)

    p.initThread('sftp://www.somewhere.tld/somepath/somefile.log')
    time.sleep(30)
    fakeConsole.shutdown()
    time.sleep(8)