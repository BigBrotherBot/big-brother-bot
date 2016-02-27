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

__author__ = 'GrosBedo, 82ndab-Bravo17, Courgette'
__version__ = '1.6'

import b3
import threading
import b3.events
import b3.plugin
import os.path
import time
import urllib2

from b3 import functions
from ConfigParser import NoOptionError

user_agent = "B3 Httpytail plugin/%s" % __version__


class HttpytailPlugin(b3.plugin.Plugin):

    requiresConfigFile = False
    httpconfig = None
    buffer = None
    lgame_log = None
    file = None
    url = None

    ## settings
    _maxGap = 20480             # max gap in bytes between remote file and local file
    _waitBeforeReconnect = 15   # time (in sec) to wait before reconnecting after loosing HTTP connection :

    _connectionTimeout = 30
    _remoteFileOffset = None
    _nbConsecutiveConnFailure = 0
    _logAppend = False
    _httpdelay = 0.150

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
        self.thread1 = None
        self.stop_event = threading.Event()
        b3.plugin.Plugin.__init__(self, console=console, config=config)

    def onStartup(self):
        """
        Plugin startup.
        """
        if self.console.config.has_option('server', 'delay'):
            self._httpdelay = self.console.config.getfloat('server', 'delay')

        if self.console.config.has_option('server', 'local_game_log'):
            self.lgame_log = self.console.config.getpath('server', 'local_game_log')
        else:
            self.lgame_log = os.path.normpath(os.path.expanduser(self.console.input.name))

        self.lgame_log = b3.getWritableFilePath(self.lgame_log)
        self.debug('local game log is: %s' % self.lgame_log)

        if self.console.config.get('server', 'game_log')[0:7] == 'http://':
            self.initThread(self.console.config.get('server', 'game_log'))

        if self.console.config.has_option('server', 'log_append'):
            self._logAppend = self.console.config.getboolean('server', 'log_append')
        else:
            self._logAppend = False

    def onLoadConfig(self):
        """
        Load plugin configuration.
        """
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

    def initThread(self, httpfileDSN):
        self.httpconfig = functions.splitDSN(httpfileDSN)
        self.url = httpfileDSN
        self.stop_event.clear()
        self.thread1 = threading.Thread(target=self.update)
        self.info("Starting httpytail thread")
        self.thread1.start()

    ####################################################################################################################
    #                                                                                                                  #
    #    EVENTS                                                                                                        #
    #                                                                                                                  #
    ####################################################################################################################

    def onExit(self, event):
        """
        Handle EVT_EXIT
        """
        self.onShutdown(event)

    def onStop(self, event):
        """
        Handle EVT_STOP
        """
        self.onShutdown(event)

    def onShutdown(self, _):
        """
        Handle intercepted events
        """
        if self.thread1 and self.thread1.is_alive():
            self.debug("stopping thread")
            self.stop_event.set()
            self.thread1.join()
            self.debug("thread stopped")

    ####################################################################################################################
    #                                                                                                                  #
    #    OTHER METHODS                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    class DiffURLOpener(urllib2.HTTPRedirectHandler, urllib2.HTTPDefaultErrorHandler):
        """
        Create sub-class in order to overide error 206.
        This error means a partial file is being sent,
        which is ok in this case.  Do nothing with this error.
        """
        def http_error_206(self, url, fp, errcode, errmsg, headers, data=None):
            pass

    def update(self):
        """
        Update the local log file.
        """
        try:
            self.file = open(self.lgame_log, 'ab')
            self.file.write('\r\n')
            self.file.write('B3 has been restarted\r\n')
            self.file.write('\r\n')
            self.file.close()
        except Exception, e:
            if hasattr(e, 'reason'):
                self.error(str(e.reason))
            if hasattr(e, 'code'):
                self.error(str(e.code))
            self.debug(str(e))

        webFile = None
        webFileDiff = None

        while not self.stop_event.is_set() and self.console.working:

            try:
                # Opening the local temporary file
                self.file = open(self.lgame_log, 'ab')
                # Crafting the HTTP request
                # - user agent header
                headers = {'User-Agent': user_agent}

                # - file url
                if self.httpconfig['port']:
                    logurl = self.httpconfig['protocol'] + '://' + self.httpconfig['host'] + ':' + \
                             str(self.httpconfig['port']) + '/' + self.httpconfig['path']
                else:
                    logurl = self.httpconfig['protocol'] + '://' + self.httpconfig['host'] + '/' + \
                             self.httpconfig['path']

                req = urllib2.Request(logurl, None, headers)

                # - htaccess authentication
                # we login if the file is protected by a .htaccess and .htpasswd and the user specified a username and
                # password in the b3 config (eg : http://user:password@host/path)
                if self.httpconfig['user']:
                    password = ''
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

                # opening the full file and detect its size
                webFile = opener.open(req)
                urllib2.install_opener(opener)
                filestats = webFile.info()
                remoteSize = filestats.getheader('Content-Length')
                webFile.close() # We close the remote connection as soon as possible to avoid spamming the server, and
                # thus blacklisting us for an amount of time

                # If we just started B3, we move the cursor to the current file size
                if self._remoteFileOffset is None:
                    self._remoteFileOffset = remoteSize

                # debug line
                #self.debug('current cursor: %s - remote file size: %s' % (str(self._remoteFileOffset), str(remoteSize)))
                # please leave this debug line, it can be very useful for users to catch some
                # weird things happening without errors, like if the webserver redirects the request because of too
                # many connections (b3/delay is too short)

                # Detecting log rotation if remote file size is lower than our current cursor position
                if remoteSize < self._remoteFileOffset:
                    self.debug("remote file rotation detected")
                    self._remoteFileOffset = 0

                # fetching the diff of the remote file if our cursor is lower than the remote file size
                if remoteSize > self._remoteFileOffset:
                    # For that, we use a custom made opener so that we can download only the
                    # diff between what has been added since last cycle
                    DiffURLOpener = self.DiffURLOpener()
                    httpopener = urllib2.build_opener(DiffURLOpener)

                    b1 = self._remoteFileOffset
                    b2 = remoteSize
                    if int(b2) - int(b1) > self._maxGap:
                        b1 = int(b2) - self._maxGap

                    # We add the Range header here, this is the one permitting to fetch only a part of an http remote
                    # file
                    range_bytes = "bytes=%s-%s" % (b1, b2)
                    self.verbose("requesting range %s" % range_bytes)
                    req.add_header("Range", range_bytes)
                    # Opening the section we want from the remote file
                    webFileDiff = httpopener.open(req)

                    # Adding the difference to our file (the file is cleaned at each startup by b3, in parser.py)
                    self.file.write(webFileDiff.read())
                    # We update the current cursor position to the size of the remote file
                    self._remoteFileOffset = remoteSize

                    self.verbose("%s bytes downloaded" % webFileDiff.info().getheader('Content-Length'))
                    # Finally, we close the distant file
                    webFileDiff.close()

                # closing the local temporary file
                self.file.close()

            except IOError, e:
                if hasattr(e, 'reason'):
                    self.error('failed to reach the server: %s' % str(e.reason))
                if hasattr(e, 'code'):
                    self.error('the server could not fulfill the request: error code: %s' % str(e.code))
                self.debug(str(e))

                self.file.close()
                self.debug('HTTP error: resetting local log file?')
                if self._logAppend:
                    try:
                        self.file = open(self.lgame_log, 'ab')
                        self.file.write('\r\n')
                        self.file.write('B3 has restarted writing the log file\r\n')
                        self.file.write('\r\n')
                    except:
                        self.file = open(self.lgame_log, 'w')
                else:
                    self.file = open(self.lgame_log, 'w')

                self.file.close()
                self.file = open(self.lgame_log, 'ab')
                try:
                    webFile.close()
                    webFileDiff.close()
                    self.debug('HTTP Connection Closed')
                except:
                    pass

                webFile = None

                if self._nbConsecutiveConnFailure <= 30:
                    time.sleep(1)
                else:
                    self.debug('too many failures: sleeping %s sec' % self._waitBeforeReconnect)
                    time.sleep(self._waitBeforeReconnect)

            except Exception, e:
                if hasattr(e, 'reason'):
                    self.error(str(e.reason))
                if hasattr(e, 'code'):
                    self.error(str(e.code))
                self.debug(str(e))

            time.sleep(self._httpdelay)

        self.verbose("B3 is down: stopping Httpytail thread")

        try:
            webFile.close()
        except Exception:
            pass
        try:
            self.file.close()
        except Exception:
            pass