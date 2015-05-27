# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2005 Michael "ThorN" Thornton
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

__author__ = 'Freelander, Bravo17, Just a baka'
__version__ = '1.2'

import b3
import b3.events
import b3.plugin
import os.path
import gzip
import socket
import StringIO
import time
import threading
import urllib2

user_agent = "B3 Cod7Http plugin/%s" % __version__


class Cod7HttpPlugin(b3.plugin.Plugin):
    """
    Downloads and appends the remote game log file for CoD7
    to a local log file from a http location given by GSP.
    """
    requiresConfigFile = False

    # Timeout url set by gameservers.com
    _timeout_url = 'http://logs.gameservers.com/timeout'
    _default_timeout = 5
    _logAppend = True

    _publicIp = None
    _port = None
    _url = None

    lastlines = ''
    locallog = None
    httpthreadinst = None
    timeout = _default_timeout

    ####################################################################################################################
    #                                                                                                                  #
    #    STARTUP                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def onLoadConfig(self):
        """
        Load plugin configuration.
        """
        pass

    def onStartup(self):
        """
        Sets and loads config values from the main config file.
        """
        if self.console.config.has_option('server', 'local_game_log'):
            self.locallog = self.console.config.getpath('server', 'local_game_log')
        else:
            # setup ip addresses
            self._publicIp = self.console.config.get('server', 'public_ip')
            self._port = self.console.config.getint('server', 'port')

            if self._publicIp[0:1] == '~' or self._publicIp[0:1] == '/':
                # load ip from a file
                f = file(self.console.getAbsolutePath(self._publicIp))
                self._publicIp = f.read().strip()
                f.close()

            logext = str(self._publicIp.replace('.', '_'))
            logext = 'games_mp_' + logext + '_' + str(self._port) + '.log'
            self.locallog = os.path.normpath(os.path.expanduser(logext))

        self.locallog = b3.getWritableFilePath(self.locallog)
        self.debug('local game log is :%s' % self.locallog)

        if self.console.config.has_option('server', 'log_append'):
            self._logAppend =self.console.config.getboolean('server', 'log_append')
        else:
            self._logAppend = False

        if self.console.config.has_option('server', 'log_timeout'):
            self.timeout = self.console.config.get('server', 'log_timeout')
        else:
            # get timeout value set by gameservers.com
            try:
                
                req = urllib2.Request(self._timeout_url)
                req.headers['User-Agent'] = user_agent
                f = urllib2.urlopen(req)
                self.timeout = int(f.readlines()[0])
                f.close()
                self.debug('using timeout value of %s seconds' % self.timeout)
                
            except (urllib2.HTTPError, urllib2.URLError, socket.timeout), error: 
                self.timeout = self._default_timeout
                self.error('ERROR: %s' % error)
                self.error('ERROR: Couldn\'t get timeout value. Using default %s seconds' % self.timeout)

        if self.console.config.get('server','game_log')[0:7] == 'http://' :
            self._url = self.console.config.get('server','game_log')
            self.initThread()
        else:
            self.error('your game log url doesn\'t seem to be valid: please check your config file')
            self.console.die()

    def initThread(self):
        """
        Starts a thread for cod7http plugin.
        """
        thread1 = threading.Thread(target=self.processData)
        self.info("starting cod7http thread")
        thread1.start()
        self.httpthreadinst = thread1

    ####################################################################################################################
    #                                                                                                                  #
    #    OTHER METHODS                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def httpThreadalive(self):
        """
        Test whether processData thread is still running.
        """
        return self.httpthreadinst.isAlive()

    def writeCompletelog(self, locallog, remotelog):
        """
        Will restart writing the local log when bot started for the first time
        or if last line cannot be found in remote chunk
        """

        # pause the bot from parsing, because we don't
        # want to parse the log from the beginning
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

        # create or open the local log file
        if self._logAppend:
            output = open(locallog, 'ab')
        else:
            output = open(locallog, 'wb')

        output.write('\r\n')
        output.write('B3 has restarted writing the log file\r\n')
        output.write('\r\n')
        output.close()

        self.info('remote log downloaded successfully')

        # we can now start parsing again
        if self.console._paused:
            self.console.unpause()
            self.debug('unpausing')

    def processData(self):
        """
        Main method for plugin.
        It's processed by initThread method.
        """
        _lastLine = True
        _firstRead = True
        n = 0
        while self.console.working:
            remotelog = ''
            response = ''
            remote_log_data = ''
            remotelogsize = 0

            # specify range depending on if the last line
            # is in the remote log chunk or not
            if _lastLine:
                b = 'bytes=-10000'
            else:
                b = 'bytes=-100000'

            headers =  {
                'User-Agent' : user_agent,
                'Range' : b,
                'Accept-encoding' : 'gzip'
            }

            request = urllib2.Request(self._url, None, headers)

            # get remote log url response and headers
            try:
                response = urllib2.urlopen(request)
                headers = response.info()

                # buffer/download remote log
                if response != '':
                    remote_log_data = response.read()
                    remotelogsize = round((len(remote_log_data) / float(1024)), 2)
                    # self.verbose('Downloaded: %s KB total' % remotelogsize)

                try:
                    # close remote file
                    response.close()
                except AttributeError, e:
                    self.error('ERROR: %s' % e)

            except (urllib2.HTTPError, urllib2.URLError), e:
                self.error('HTTP ERROR: %s' % e)
            except socket.timeout:
                self.error('TIMEOUT ERROR: socket timed out!')

            # start keeping the time
            start = time.time()

            # decompress remote log and return for use
            # First, make sure that there is domething worth decompressing
            # In case the server has just done a restart
            if len(remote_log_data) > 0:
                try:
                    #self.debug('Content-Encoding: %s' % headers.get('Content-Encoding'))
                    if headers.get('Content-Encoding') == 'gzip':
                        compressedstream = StringIO.StringIO(remote_log_data)
                        gzipper = gzip.GzipFile(fileobj=compressedstream)
                        remotelog = gzipper.read()
                    else:
                        remotelog = remote_log_data
                except IOError, e:
                    remotelog = ''
                    self.error('IOERROR: %s' % e)

                if os.path.exists(self.locallog) and os.path.getsize(self.locallog) > 0 and not _firstRead:

                    # check if last line is in the remote log chunk
                    if remotelog.find(self.lastlines) != -1:
                        _lastLine = True
                        n = 0

                        # we'll get the new lines i.e what is available after the last line
                        # of our local log file
                        try:
                            checklog = remotelog.rpartition(self.lastlines)
                            newlog = checklog[2]
                            # remove any broken last line
                            i = newlog.rfind ('\r\n')
                            newlog = newlog[:i + 2]
                            # remove any blank lines
                            while newlog[-4:-2] == '\r\n':
                                newlog = newlog[:-2]
                        except ValueError, error:
                            self.error ('ValueError: %s' % error)
                            newlog = ''

                        # remove any blank lines from end
                        # append the additions to our log if there is something and update lazy cursor
                        if len(newlog) > 0:
                            output = open(self.locallog,'ab')
                            output.write(newlog)
                            output.close()
                            self.lastlines = remotelog[-1000:]                        
                            self.debug('downloaded %s KB and added %s char(s) to log' % (remotelogsize, len(newlog)))

                    else:
                        _lastLine = False
                        self.debug('can\'t find last line in the log chunk: checking again...')
                        n += 1

                        # check once in a larger chunk and if we are still unable to find last line
                        # in the remote chunk, restart the process
                        if n == 2:
                            self.debug('Logs rotated or unable to find last line in remote log, restarting process...')
                            self.writeCompletelog(self.locallog, remotelog)
                            _lastLine = True
                            n = 0

                else:
                    self.debug('writing first log read')
                    self.writeCompletelog(self.locallog, remotelog)
                    _firstRead = False

            # calculate how long it took to process
            timespent = time.time() - start

            # calculate time to wait until next request.
            timeout = float(self.timeout)

            # self.verbose('Given timeout value is %s seconds' % timeout)
            # self.verbose('Total time spent to process the downloaded file is %s seconds' % timespent)

            # Calculate sleep time for next request. Adding 0.1 secs to prevent HTTP Error 403 errors
            wait = float((timeout - timespent) + 0.1)

            if wait <= 0:
                wait = 1

            # make the plugin thread fast-killable
            i = 0
            w = int(wait)
            while i < w and self.console.working:
                time.sleep(1)
                i += 1
            time.sleep(wait - w)

        self.verbose('B3 is down: stopping Cod7Http plugin')


if __name__ == '__main__':
    from b3.fake import fakeConsole
    p = Cod7HttpPlugin(fakeConsole)
    p._url = "http://www.example.com"
    p.timeout = 5
    p.locallog = 'test.log'
    p.processData()