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
#   * Increased sleep time by 0.5 second to prevent HTTP 403 errors, although
#     requests are not sent less than timeout value
#   * Timout value falls back to default 10 seconds if timeout value can't be
#     parsed from http://logs.gameservers.com/timeout
#   * Added option for manually setting timout value in b3.xml
#

__author__  = 'Freelander'
__version__ = '1.0.4'

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

    def getRemotelog(self):
        start = time.time()
        headers =  { 'User-Agent'  : user_agent  }

        #request remote log
        request = urllib2.Request(self._url, None, headers)

        #tell the server we like compressed data, and get the log as compressed data
        request.add_header('Accept-encoding', 'gzip')

        try:
            response = urllib2.urlopen(request)

            #compressed remote log
            remote_log_compressed = response.read()

            #get http headers in case needed
            headers = response.info()

            #size of the compressed log we just downloaded
            #can be used for information
            remotelogsize = len(remote_log_compressed)/1024
            self.verbose('Downloaded: %s KB total' % remotelogsize)
        except (urllib2.HTTPError, urllib2.URLError), error: 
            remotelog = ''
            remote_log_compressed = ''
            self.error('HTTP ERROR: %s' % error)
        except socket.timeout:
            remotelog = ''
            remote_log_compressed = ''
            self.error('TIMEOUT ERROR: Socket Timed out!')

        #decompress remote log and return for use
        if len(remote_log_compressed) > 0:
            try:
                compressedstream = StringIO.StringIO(remote_log_compressed)
                gzipper = gzip.GzipFile(fileobj=compressedstream)
                remotelog = gzipper.read()
            except IOError, error:
                remotelog = ''
                self.error('IOERROR: %s' % error)

        #calculate how long it took from sending request until completing the download
        timespent = time.time() - start

        return (remotelog, timespent)

    def getLastline(self, sfile):
        fh = open(sfile, "r")
        linelist = fh.readlines()
        fh.close()
        self.lastline = linelist[-1]

        #incase last line is empty
        if self.lastline == '\n':
            self.lastline = linelist[-2]

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
        while self.console.working:
            log = self.getRemotelog()
            if not log:
                return False

            remotelog, timespent = log

            if os.path.exists(self.locallog) and os.path.getsize(self.locallog) > 0:
                #get the last line of our local log file
                lastline = self.getLastline(self.locallog).strip()

                #we'll get the new lines i.e what is available after the last line
                #of our local log file
                checklog = remotelog.rpartition(lastline)
                addition = checklog[2].lstrip()

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
                #pasue the bot from parsing, because we don't
                #want to parse the log from the beginning
                if self.console._paused is False:
                    self.console.pause()
                    self.debug('Pausing')

                #create the local log file
                self.console.pause()
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

            #calculate time to wait until next request. 
            timeout = float(self.timeout)

            self.verbose('Given timeout value is %s seconds' % timeout)
            self.verbose('Total time spent to download the file is %s seconds' % timespent)

            #Calculate sleep time for next request. Adding 0.5 secs to prevent 
            #too much HTTP Error 403 errors
            wait = float((timeout - timespent) + 0.5)

            if wait <= 0:
                wait = 1

            self.verbose('Next request in %s second(s)' % wait)

            time.sleep(wait)

        self.verbose('B3 is down, stopping Cod7Http Plugin')

if __name__ == '__main__':
    p = Cod7httpPlugin()
    p.processData()
