#
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
#
# CHANGELOG:
# 2010-09-04 - 0.1 - GrosBedo
#     Initial release, with htaccess authentication support.
# 2011-03-17 - 0.2 - Courgette
#     Make sure that maxGapBytes is never exceeded

__version__ = '0.2'
__author__ = 'GrosBedo'
 
import b3, threading
from b3 import functions
import b3.events
import b3.plugin
import os.path
import time
import re
import sys
import urllib2, urllib

user_agent =  "B3 Httpytail plugin/%s" % __version__
#--------------------------------------------------------------------------------------------------
class HttpytailPlugin(b3.plugin.Plugin):
    ### settings
    _maxGap = 20480 # max gap in bytes between remote file and local file
    _waitBeforeReconnect = 15 # time (in sec) to wait before reconnecting after loosing HTTP connection : 
    _connectionTimeout = 30
    
    requiresConfigFile = False
    httpconfig = None
    buffer = None
    _remoteFileOffset = None
    _nbConsecutiveConnFailure = 0
    
    _httpdelay = 0.150
    
    def onStartup(self):
        versionsearch = re.search("^((?P<mainversion>[0-9]).(?P<lowerversion>[0-9]+)?)", sys.version)
        version = int(versionsearch.group(3))
        if version < 6:
            self.error('Python Version %s, this is not supported and may lead to hangs. Please update Python to 2.6' % versionsearch.group(1))
            self.console.die()

        if self.console.config.has_option('server', 'delay'):
            self._httpdelay = self.console.config.getfloat('server', 'delay')
        
        if self.console.config.has_option('server', 'local_game_log'):
            self.lgame_log = self.console.config.getfloat('server', 'local_game_log')
        else:
            self.lgame_log = os.path.normpath(os.path.expanduser('games_mp.log'))
            
        if self.console.config.get('server','game_log')[0:7] == 'http://' :
            self.initThread(self.console.config.get('server','game_log'))
    
    def onLoadConfig(self):
        try:
            self._connectionTimeout = self.config.getint('settings', 'timeout')
        except: 
            self.warning("Error reading timeout from config file. Using default value")
        self.info("HTTP connection timeout: %s" % self._connectionTimeout)

        try:
            self._maxGap = self.config.getint('settings', 'maxGapBytes')
        except: 
            self.warning("Error reading maxGapBytes from config file. Using default value")
        self.info("Maximum gap allowed between remote and local gamelog: %s bytes" % self._maxGap)
    
    def initThread(self, httpfileDSN):
        self.httpconfig = functions.splitDSN(httpfileDSN)
        self.url = httpfileDSN
        thread1 = threading.Thread(target=self.update)
        self.info("Starting httpytail thread")
        thread1.start()

    class DiffURLOpener(urllib2.HTTPRedirectHandler, urllib2.HTTPDefaultErrorHandler):
        """Create sub-class in order to overide error 206.  This error means a
           partial file is being sent,
           which is ok in this case.  Do nothing with this error.
        """
        def http_error_206(self, url, fp, errcode, errmsg, headers, data=None):
            pass

    def update(self):
        while self.console.working:
            try:
                # Opening the local temporary file
                self.file = open(self.lgame_log, 'ab')
                
                # Crafting the HTTP request
                # - user agent header
                headers =  { 'User-Agent'  : user_agent  }
                
                # - file url
                if self.httpconfig['port']:
                    logurl = self.httpconfig['protocol']+'://'+self.httpconfig['host']+':'+self.httpconfig['port']+'/'+self.httpconfig['path']
                else:
                    logurl = self.httpconfig['protocol']+'://'+self.httpconfig['host']+'/'+self.httpconfig['path']
                
                req =  urllib2.Request(logurl, None, headers)

                # - htaccess authentication
                # we login if the file is protected by a .htaccess and .htpasswd and the user specified a username and password in the b3 config (eg : http://user:password@host/path)
                if self.httpconfig['user']:
                    username = self.httpconfig['user']
                    if self.httpconfig['password']:
                        password = self.httpconfig['password']
                    # create a password manager
                    password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
                    
                    # Add the username and password.
                    # If we knew the realm, we could use it instead of ``None``.
                    top_level_url = logurl
                    password_mgr.add_password(None, top_level_url, username, password)
                    
                    handler = urllib2.HTTPBasicAuthHandler(password_mgr)

                    # We store these parameters in an opener
                    opener = urllib2.build_opener(handler)
                else:
                    # Else if no authentication is needed, then we create a standard opener
                    opener = urllib2.build_opener()


                # Opening the full file and detect its size
                webFile =  opener.open(req)
                urllib2.install_opener(opener)
                filestats = webFile.info()
                remoteSize = filestats.getheader('Content-Length')
                webFile.close() # We close the remote connection as soon as possible to avoid spamming the server, and thus blacklisting us for an amount of time
                
                # If we just started B3, we move the cursor to the current file size
                if self._remoteFileOffset is None:
                        self._remoteFileOffset = remoteSize
                
                # debug line
                #self.debug('Diff - current cursor: %s - remote file size: %s' % (str(self._remoteFileOffset), str(remoteSize)) ) # please leave this debug line, it can be very useful for users to catch some weird things happening without errors, like if the webserver redirects the request because of too many connections (b3/delay is too short)

                # Detecting log rotation if remote file size is lower than our current cursor position
                if remoteSize < self._remoteFileOffset:
                    self.debug("remote file rotation detected")
                    self._remoteFileOffset = 0
                
                # Fetching the diff of the remote file if our cursor is lower than the remote file size
                if remoteSize > self._remoteFileOffset:
                    # For that, we use a custom made opener so that we can download only the diff between what has been added since last cycle
                    DiffURLOpener = self.DiffURLOpener()
                    httpopener = urllib2.build_opener(DiffURLOpener)
                    
                    b1 = self._remoteFileOffset
                    b2 = remoteSize
                    if int(b2) - int(b1) > self._maxGap:
                        b1 = int(b2) - self._maxGap
                    
                    # We add the Range header here, this is the one permitting to fetch only a part of an http remote file
                    range_bytes = "bytes=%s-%s" % (b1, b2)
                    self.verbose("requesting range %s" % range_bytes)
                    req.add_header("Range",range_bytes)
                    # Opening the section we want from the remote file
                    webFileDiff = httpopener.open(req)

                    # Adding the difference to our file (the file is cleaned at each startup by b3, in parser.py)
                    self.file.write(webFileDiff.read())
                    # We update the current cursor position to the size of the remote file
                    self._remoteFileOffset = remoteSize
                    
                    self.verbose("%s bytes downloaded" % webFileDiff.info().getheader('Content-Length'))
                    # Finally, we close the distant file
                    webFileDiff.close()

                # Closing the local temporary file
                self.file.close()
            except Exception, e:
                if hasattr(e, 'reason'):
                    self.error(str(e.reason))
                if hasattr(e, 'code'):
                    self.error(str(e.code))
                self.debug(str(e))
            except IOError, e:
                if hasattr(e, 'reason'):
                    self.error('Failed to reach the server. Reason : %s' % str(e.reason))
                if hasattr(e, 'code'):
                    self.error('The server could not fulfill the request. Error code : %s' % str(e.code))
                self.debug(str(e))

                self.file.close()
                self.file = open(self.lgame_log, 'w')
                self.file.close()
                self.file = open(self.lgame_log, 'ab')
                try:
                    self.webFile.close()
                    self.webFileDiff.close()
                    self.debug('HTTP Connection Closed')
                except:
                    pass
                webFile = None
                
                if self._nbConsecutiveConnFailure <= 30:
                    time.sleep(1)
                else:
                    self.debug('too many failures, sleeping %s sec' % self._waitBeforeReconnect)
                    time.sleep(self._waitBeforeReconnect)
            time.sleep(self._httpdelay)
        self.verbose("B3 is down, stopping Httpytail thread")
        try:
            webFile.close()
        except:
            pass
        try:
            self.file.close()
        except:
            pass
    
    
if __name__ == '__main__':
    from b3.fake import fakeConsole
    
    print "------------------------------------"
    config = b3.config.XmlConfigParser()
    config.setXml("""
    <configuration plugin="httpytail">
        <settings name="settings">
            <set name="timeout">15</set>
            <set name="maxGapBytes">1024</set>
        </settings>
    </configuration>
    """)
    p = HttpytailPlugin(fakeConsole, config)
    p.onStartup()
    p._httpdelay = 5
    p.initThread('http://www.somewhere.tld/somepath/somefile.log')
    time.sleep(300)
    fakeConsole.shutdown()
    time.sleep(8)