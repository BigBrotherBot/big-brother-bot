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
#   * Increase range header if last line is not found in the remote log chunk
#

__author__  = 'Freelander'
__version__ = '1.0.7'

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
    requiresConfigFile = False

    #Timout url set by gameservers.com
    _timeout_url = 'http://logs.gameservers.com/timeout'
    _default_timeout = 10

    def onLoadConfig(self):
        pass

    def initThread(self):
        thread1 = threading.Thread(target=self.processData)
        self.info("Starting cod7http thread")
        thread1.start()

    def onStartup(self):
        versionsearch = re.search("^((?P<mainversion>[0-9]).(?P<lowerversion>[0-9]+)?)", sys.version)
        version = int(versionsearch.group(3))
        if version < 6:
            self.error('Python Version %s, this is not supported and may lead to hangs. Please update Python to 2.6' % versionsearch.group(1))
            self.console.die()

        if self.console.config.has_option('server', 'local_game_log'):
            self.locallog = self.console.config.get('server', 'local_game_log')
        else:
            self.locallog = os.path.normpath(os.path.expanduser('games_mp.log'))

        if self.console.config.has_option('server', 'log_timeout'):
            self.timeout = self.console.config.get('server', 'log_timeout')
        else:
            #get timeout value set by gameservers.com
            try:
                self.timeout = int(urllib2.urlopen(self._timeout_url).read())
            except (urllib2.HTTPError, urllib2.URLError, socket.timeout), error: 
                self.timeout = _default_timeout
                self.error('ERROR: %s' % error)
                self.error('ERROR: Couldn\'t get timeout value. Using default %s seconds' % self.timeout)

        if self.console.config.get('server','game_log')[0:7] == 'http://' :
            self._url = self.console.config.get('server','game_log')
            self.initThread()
        else:
            self.error('Your game log url doesn\'t seem to be valid. Please check your config file')
            self.console.die()

    def getLastline(self, sfile):
        fh = open(sfile, "r")
        linelist = fh.readlines()
        fh.close()
        self.lastline = linelist[-3]+linelist[-2]+linelist[-1]

        return self.lastline

    def removeLastline(self, file):
        f = open(file, 'rb')
        pos = next = 0

        for line in f:
            pos = next # position of beginning of this line
            next += len(line) # compute position of beginning of next line

        f = open(file, 'ab')
        f.truncate(pos)

    def processData(self):
        _lastLine = True

        while self.console.working:
            remotelog = ''
            response = ''
            remote_log_compressed = ''

            #Specify range depending on if the last line
            #is in the remote log chunk or not
            if _lastLine:
                bytes = 'bytes=-10000'
            else:
                bytes = 'bytes=-20000'

            headers =  { 'User-Agent' : user_agent,
                         'Range' : bytes,
                         'Accept-encoding' : 'gzip' }

            self.verbose('Sending request')

            request = urllib2.Request(self._url, None, headers)

            #get remote log url response and headers
            try:
                response = urllib2.urlopen(request)
                headers = response.info()

                #buffer/download remote log
                if response != '':
                    remote_log_compressed = response.read()
                    remotelogsize = round((len(remote_log_compressed)/float(1024)), 2)
                    self.verbose('Downloaded: %s KB total' % remotelogsize)

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
            if len(remote_log_compressed) > 0:
                try:
                    compressedstream = StringIO.StringIO(remote_log_compressed)
                    gzipper = gzip.GzipFile(fileobj=compressedstream)
                    remotelog = gzipper.read()
                except IOError, error:
                    remotelog = ''
                    self.error('IOERROR: %s' % error)

            if os.path.exists(self.locallog) and os.path.getsize(self.locallog) > 0:
                #get the last line of our local log file
                lastline = self.getLastline(self.locallog)

                #check if last line is in the remote log chunk
                if remotelog.find(lastline) != -1:
                    #we'll get the new lines i.e what is available after the last line
                    #of our local log file
                    checklog = remotelog.rpartition(lastline)
                    addition = checklog[2]

                    #append the additions to our log
                    if len(addition) > 0:
                        output = open(self.locallog,'ab')
                        output.write(addition)
                        output.close()

                        self.verbose('Added: %s Byte(s) to log' % len(addition))
                    else:
                        self.verbose('No addition found, checking again')

                    #check if our new last line is complete or broken
                    #if it is not a complete line, remove it
                    newlastline = self.getLastline(self.locallog)

                    if not newlastline.endswith('\n'):
                        self.removeLastline(self.locallog)
                else:
                    _lastLine = False
                    self.debug('Can\'t find last line in the log chunk, checking again...')

            else:
                #pasue the bot from parsing, because we don't
                #want to parse the log from the beginning
                if self.console._paused is False:
                    self.console.pause()
                    self.debug('Pausing')

                #create the local log file
                #self.console.pause()
                output = open(self.locallog,'wb')
                output.write(remotelog)
                output.close()

                #remove the last line
                self.removeLastline(self.locallog)

                self.info('Remote log downoaded successfully')

                #we can now start parsing again
                if self.console._paused:
                    self.console.unpause()
                    self.debug('Unpausing')

            #calculate how long it took to process
            timespent = time.time() - start

            #calculate time to wait until next request. 
            timeout = float(self.timeout)

            self.verbose('Given timeout value is %s seconds' % timeout)
            self.verbose('Total time spent to process the downloaded file is %s seconds' % timespent)

            #Calculate sleep time for next request. Adding 0.1 secs to prevent HTTP Error 403 errors
            wait = float((timeout - timespent) + 0.1)

            if wait <= 0:
                wait = 1

            self.verbose('Next request in %s second(s)' % wait)

            time.sleep(wait)

        self.verbose('B3 is down, stopping Cod7Http Plugin')


if __name__ == '__main__':
    p = Cod7HttpPlugin()
    p.processData()