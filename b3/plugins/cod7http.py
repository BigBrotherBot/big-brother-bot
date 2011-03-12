# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2010
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
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
# CHANGELOG
#
# 15.01.2011 - 1.0.0 - Freelander
#   * Initial release
# 16.01.2011 - 1.0.1 - Freelander
#   * Added user-agent in the http header
#   * Added exceptions for socket timeout, IOError and URLError
# 17.01.2011 - 1.0.2 - Freelander
#   * Better handling of socket timeout error
# 17.01.2011 - 1.0.3 - Freelander
#   * Fixed local gamelog option
# 19.01.2011 - 1.0.4 - Freelander
#   * Increased sleep time to prevent HTTP 403 errors
#   * Timout value falls back to default 10 seconds if timeout value can't be
#     parsed from http://logs.gameservers.com/timeout
#   * Added option for manually setting timout value in b3.xml
# 21.01.2011 - 1.0.5 - Freelander
#   * Refactoring code for better timeout handling and get rid of redundant
#     getRemotelog function
# 31.01.2011 - 1.0.6 - Freelander
#   * Added range header to limit download size
# 02.02.2011 - 1.0.7 - Freelander
#   * Added error handling while closing remote file to prevent plugin crash
#   * Check Python version to be minimum 2.6
#   * Now checking last 3 lines instead of last single line
#   * Increase range header if last line is not found in the remote log chunk.
# 03.02.2011 - 1.0.8 - Freelander
#   * If still unable to find the last line after increasing range header,
#     restart downloading process. That happens if logs are rotated or server restarted.
#     In that case last line will never be found.
# 05.02.2011 - 1.0.9 - Bravo17
#   * Added log_append config variable to control whether local log is deleted on startup
#   * Changed lastlines functionality to being stored in memory rather than getting from local log 
#     using Just a baka's lazy cursor
#   * Make sure that we have something worth decompressing before we attempt to do so
#   * Added user agent to timeout request
# 08.02.2011 - 1.0.10 - Just a baka
#   * Fixed the bug which prevented b3 from parsing while the gzipped remote log is < 500 bytes
# 10.02.2011 - 1.0.11 - Just a baka
#   * Rewritten the inter-cycle sleeping mechanism to achieve a nearly-instant thread exit time
# 25.02.2011 - 1.0.12 - Freelander
#   * Reduced default timeout to 5 seconds
#   * Arranged log messages
#   * Fixed a minor bug
# 02.03.2011 - 1.0.13 - Freelander
#   * Added exception for ValueError that may occur on an interrupted internet connection
# 02.03.2011 - 1.0.14 - Bravo17
#   * Added method to test whether processData thread is still running, for use by parser
#

## @file
#  This plugin downloads and maintains CoD7 game log file

__author__  = 'Freelander, Bravo17, Just a baka'
__version__ = '1.0.14'

import b3, threading
from b3 import functions
import b3.events
import b3.plugin
import urllib2, urllib
import os.path
import StringIO
import gzip
import time
import socket
import re, sys

user_agent =  "B3 Cod7Http plugin/%s" % __version__

class Cod7HttpPlugin(b3.plugin.Plugin):
    """Downloads and appends the remote game log file for CoD7 to a local
    log file from a http location given by GSP.
    """

    requiresConfigFile = False

    #Timout url set by gameservers.com
    _timeout_url = 'http://logs.gameservers.com/timeout'
    _default_timeout = 5
    _logAppend = True
    lastlines = ''
    httpthreadinst = None

    def onLoadConfig(self):
        pass

    def initThread(self):
        """Starts a thread for cod7http plugin."""

        thread1 = threading.Thread(target=self.processData)
        self.info("Starting cod7http thread")
        thread1.start()
        self.httpthreadinst = thread1

    def onStartup(self):
        """Sets and loads config values from the main config file."""

        versionsearch = re.search("^((?P<mainversion>[0-9]).(?P<lowerversion>[0-9]+)?)", sys.version)
        version = int(versionsearch.group(3))
        if version < 6:
            self.error('Python Version %s, this is not supported and may lead to hangs. Please update Python to 2.6' % versionsearch.group(1))
            self.console.die()

        if self.console.config.has_option('server', 'local_game_log'):
            self.locallog = self.console.config.get('server', 'local_game_log')
        else:
            self.locallog = os.path.normpath(os.path.expanduser('games_mp.log'))

        if self.console.config.has_option('server', 'log_append'):
            self._logAppend =self.console.config.getboolean('server', 'log_append')
        else:
            self._logAppend = False

        if self.console.config.has_option('server', 'log_timeout'):
            self.timeout = self.console.config.get('server', 'log_timeout')
        else:
            #get timeout value set by gameservers.com
            try:
                
                req = urllib2.Request(self._timeout_url)
                req.headers['User-Agent'] = user_agent
                f = urllib2.urlopen(req)
                self.timeout = int(f.readlines()[0])
                f.close()
                self.debug('Using timeout value of %s seconds' % self.timeout)
                
            except (urllib2.HTTPError, urllib2.URLError, socket.timeout), error: 
                self.timeout = self._default_timeout
                self.error('ERROR: %s' % error)
                self.error('ERROR: Couldn\'t get timeout value. Using default %s seconds' % self.timeout)

        if self.console.config.get('server','game_log')[0:7] == 'http://' :
            self._url = self.console.config.get('server','game_log')
            self.initThread()
        else:
            self.error('Your game log url doesn\'t seem to be valid. Please check your config file')
            self.console.die()

    def httpThreadalive(self):
        """Test whether processData thread is still running."""
        return self.httpthreadinst.isAlive()

    def writeCompletelog(self, locallog, remotelog):
        """Will restart writing the local log when bot started for the first time
        or if last line cannot be found in remote chunk
        """

        #pause the bot from parsing, because we don't
        #want to parse the log from the beginning
        if self.console._paused is False:
            self.console.pause()
            self.debug('Pausing')
        # Remove last line if not complete
        i = remotelog.rfind ('\r\n')
        remotelog = remotelog[:i + 2]
        # remove any blank lines
        while remotelog[-4:-2] == '\r\n':
            remotelog = remotelog[:-2]
        
        # use Just a baka's lazy cursor
        self.lastlines = remotelog[-1000:]

        #create or open the local log file
        if self._logAppend:
            output = open(locallog, 'ab')
        else:
            output = open(locallog, 'wb')

        output.write('\r\n')
        output.write('B3 has restarted writing the log file\r\n')
        output.write('\r\n')
        output.close()

        self.info('Remote log downloaded successfully')

        #we can now start parsing again
        if self.console._paused:
            self.console.unpause()
            self.debug('Unpausing')

    def processData(self):
        """Main method for plugin. It's processed by initThread method."""

        _lastLine = True
        _firstRead = True
        n = 0

        while self.console.working:
            remotelog = ''
            response = ''
            remote_log_compressed = ''

            #Specify range depending on if the last line
            #is in the remote log chunk or not
            if _lastLine:
                bytes = 'bytes=-10000'
            else:
                bytes = 'bytes=-100000'

            headers =  { 'User-Agent' : user_agent,
                         'Range' : bytes,
                         'Accept-encoding' : 'gzip' }

            #self.verbose('Sending request')

            request = urllib2.Request(self._url, None, headers)

            #get remote log url response and headers
            try:
                response = urllib2.urlopen(request)
                headers = response.info()

                #buffer/download remote log
                if response != '':
                    remote_log_compressed = response.read()
                    remotelogsize = round((len(remote_log_compressed)/float(1024)), 2)
                    #self.verbose('Downloaded: %s KB total' % remotelogsize)

                try:
                    #close remote file
                    response.close()
                except AttributeError, error:
                    self.error('ERROR: %s' % error)

            except (urllib2.HTTPError, urllib2.URLError), error:
                self.error('HTTP ERROR: %s' % error)
            except socket.timeout:
                self.error('TIMEOUT ERROR: Socket Timed out!')

            #start keeping the time
            start = time.time()

            #decompress remote log and return for use
            # First, make sure that there is domething worth decompressing
            # In case the server has just done a restart
            if len(remote_log_compressed) > 0:
                try:
                    compressedstream = StringIO.StringIO(remote_log_compressed)
                    gzipper = gzip.GzipFile(fileobj=compressedstream)
                    remotelog = gzipper.read()
                except IOError, error:
                    remotelog = ''
                    self.error('IOERROR: %s' % error)

                if os.path.exists(self.locallog) and os.path.getsize(self.locallog) > 0 and not _firstRead:

                    #check if last line is in the remote log chunk
                    if remotelog.find(self.lastlines) != -1:
                        _lastLine = True
                        n = 0

                        #we'll get the new lines i.e what is available after the last line
                        #of our local log file
                        try:
                            checklog = remotelog.rpartition(self.lastlines)
                            newlog = checklog[2]
                            # Remove any broken last line
                            i = newlog.rfind ('\r\n')
                            newlog = newlog[:i + 2]
                            # Remove any blank lines
                            while newlog[-4:-2] == '\r\n':
                                newlog = newlog[:-2]
                        except ValueError, error:
                            self.error ('ValueError: %s' % error)
                            newlog = ''

                        # Remove any blank lines from end
                        
                        #append the additions to our log if there is something and update lazy cursor
                        if len(newlog) > 0:
                            output = open(self.locallog,'ab')
                            output.write(newlog)
                            output.close()
                            self.lastlines = remotelog[-1000:]                        
                            self.debug('Downloaded %s KB and added %s char(s) to log' % (remotelogsize, len(newlog)))

                    else:
                        _lastLine = False
                        self.debug('Can\'t find last line in the log chunk, checking again...')
                        n += 1

                        #check once in a larger chunk and if we are still unable to find last line
                        #in the remote chunk, restart the process
                        if n == 2:
                            self.debug('Logs rotated or unable to find last line in remote log, restarting process...')
                            self.writeCompletelog(self.locallog, remotelog)
                            _lastLine = True
                            n = 0

                else:
                    self.debug('Writing first log read')
                    self.writeCompletelog(self.locallog, remotelog)
                    _firstRead = False

            #calculate how long it took to process
            timespent = time.time() - start

            #calculate time to wait until next request. 
            timeout = float(self.timeout)

            #self.verbose('Given timeout value is %s seconds' % timeout)
            #self.verbose('Total time spent to process the downloaded file is %s seconds' % timespent)

            #Calculate sleep time for next request. Adding 0.1 secs to prevent HTTP Error 403 errors
            wait = float((timeout - timespent) + 0.1)

            if wait <= 0:
                wait = 1

            #self.verbose('Next request in %s second(s)' % wait)

            # Make the plugin thread fast-killable
            i = 0
            w = int(wait)
            while i < w and self.console.working:
                time.sleep(1)
                i += 1
            time.sleep(wait - w)

        self.verbose('B3 is down, stopping Cod7Http Plugin')


if __name__ == '__main__':
    p = Cod7HttpPlugin()
    p.processData()