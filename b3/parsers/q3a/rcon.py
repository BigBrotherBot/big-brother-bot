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
#
__author__ = 'ThorN'
__version__ = '1.11'

import re
import socket
import select
import time
import thread
import threading
import Queue

class Rcon(object):

    host = ()
    password = None
    lock = thread.allocate_lock()
    socket = None
    queue = None
    console = None
    socket_timeout = 0.80
    rconsendstring = '\377\377\377\377rcon "%s" %s\n'
    rconreplystring = '\377\377\377\377print\n'
    qserversendstring = '\377\377\377\377%s\n'

    # default expiretime for the status cache in seconds and cache type
    status_cache_expire_time = 2
    status_cache = False
    status_cache_expired = None
    status_cache_data = ''

    def __init__(self, console, host, password):
        """
        Object contructor.
        :param console: The console implementation
        :param host: The host where to send RCON commands
        :param password: The RCON password
        """
        self.console = console
        self.queue = Queue.Queue()

        if self.console.config.has_option('caching', 'status_cache_type'):
            status_cache_type = self.console.config.get('caching', 'status_cache_type').lower()
            if status_cache_type == 'memory':
                self.status_cache = True

        if self.console.config.has_option('caching', 'status_cache_expire'):
            self.status_cache_expire_time = abs(self.console.config.getint('caching', 'status_cache_expire'))
            if self.status_cache_expire_time > 5:
                self.status_cache_expire_time = 5
        # set the cacche expire time to now, so the first status request will retrieve a status from the server
        status_cache_expired = time.time()

        self.console.bot('Rcon status cache expire time: [%s sec] Type: [%s]' % (self.status_cache_expire_time,
                                                                                 self.status_cache))
        self.console.bot('Game name is: %s' % self.console.gameName)
        self.socket = socket.socket(type=socket.SOCK_DGRAM)
        self.host = host
        self.password = password
        self.socket.settimeout(2)
        self.socket.connect(self.host)

        self._stopEvent = threading.Event()
        thread.start_new_thread(self._writelines, ())

    def encode_data(self, data, source):
        """
        Encode data before sending them onto the socket.
        :param data: The string to be encoded
        :param source: Who requested the encoding
        """
        try:
            if isinstance(data, str):
                data = unicode(data, errors='ignore')
            data = data.encode(self.console.encoding, 'replace')
        except Exception, msg:
            self.console.warning('%s: error encoding data: %r', source, msg)
            data = 'Encoding error'
            
        return data
        
    def send(self, data, maxRetries=None, socketTimeout=None):
        """
        Send data over the socket.
        :param data: The string to be sent
        :param maxRetries: How many times we have to retry the sending upon failure
        :param socketTimeout: The socket timeout value
        """
        if socketTimeout is None:
            socketTimeout = self.socket_timeout
        if maxRetries is None:
            maxRetries = 2

        data = data.strip()
        # encode the data
        if self.console.encoding:
            data = self.encode_data(data, 'QSERVER')

        self.console.verbose('QSERVER sending (%s:%s) %r', self.host[0], self.host[1], data)
        start_time = time.time()

        retries = 0
        while time.time() - start_time < 5:
            readables, writeables, errors = select.select([], [self.socket], [self.socket], socketTimeout)
            if len(errors) > 0:
                self.console.warning('QSERVER: %r', errors)
            elif len(writeables) > 0:
                try:
                    writeables[0].send(self.qserversendstring % data)
                except Exception, msg:
                    self.console.warning('QSERVER: error sending: %r', msg)
                else:
                    try:
                        data = self.readSocket(self.socket, socketTimeout=socketTimeout)
                        self.console.verbose2('QSERVER: received %r' % data)
                        return data
                    except Exception, msg:
                        self.console.warning('QSERVER: error reading: %r', msg)
            else:
                self.console.verbose('QSERVER: no writeable socket')

            time.sleep(0.05)
            retries += 1

            if retries >= maxRetries:
                self.console.error('QSERVER: too many tries: aborting (%r)', data.strip())
                break

            self.console.verbose('QSERVER: retry sending %r (%s/%s)...', data.strip(), retries, maxRetries)

        self.console.debug('QSERVER: did not send any data')
        return ''

    def sendRcon(self, data, maxRetries=None, socketTimeout=None):
        """
        Send an RCON command.
        :param data: The string to be sent
        :param maxRetries: How many times we have to retry the sending upon failure
        :param socketTimeout: The socket timeout value
        """
        if socketTimeout is None:
            socketTimeout = self.socket_timeout
        if maxRetries is None:
            maxRetries = 2

        data = data.strip()
        # encode the data
        if self.console.encoding:
            data = self.encode_data(data, 'RCON')

        self.console.verbose('RCON sending (%s:%s) %r', self.host[0], self.host[1], data)
        start_time = time.time()

        retries = 0
        while time.time() - start_time < 5:
            readables, writeables, errors = select.select([], [self.socket], [self.socket], socketTimeout)

            if len(errors) > 0:
                self.console.warning('RCON: %s', str(errors))
            elif len(writeables) > 0:
                try:
                    writeables[0].send(self.rconsendstring % (self.password, data))
                except Exception, msg:
                    self.console.warning('RCON: error sending: %r', msg)
                else:
                    try:
                        data = self.readSocket(self.socket, socketTimeout=socketTimeout)
                        self.console.verbose2('RCON: received %r' % data)
                        return data
                    except Exception, msg:
                        self.console.warning('RCON: error reading: %r', msg)

                if re.match(r'^quit|map(_rotate)?.*', data):
                    # do not retry quits and map changes since they prevent the server from responding
                    self.console.verbose2('RCON: no retry for %r', data)
                    return ''

            else:
                self.console.verbose('RCON: no writeable socket')

            time.sleep(0.05)

            retries += 1

            if retries >= maxRetries:
                self.console.error('RCON: too many tries: aborting (%r)', data.strip())
                break

            self.console.verbose('RCON: retry sending %r (%s/%s)...', data.strip(), retries, maxRetries)

        self.console.debug('RCON: did not send any data')
        return ''

    def stop(self):
        """
        Stop the rcon writelines queue.
        """
        self._stopEvent.set()

    def _writelines(self):
        """
        Write multiple RCON commands on the socket.
        """
        while not self._stopEvent.isSet():
            lines = self.queue.get(True)
            for cmd in lines:
                if not cmd:
                    continue
                with self.lock:
                    self.sendRcon(cmd, maxRetries=1)

    def writelines(self, lines):
        """
        Enqueue multiple RCON commands for later processing.
        :param lines: A list of RCON commands.
        """
        self.queue.put(lines)

    def write(self, cmd, maxRetries=None, socketTimeout=None):
        """
        Write a RCON command.
        :param cmd: The string to be sent
        :param maxRetries: How many times we have to retry the sending upon failure
        :param socketTimeout: The socket timeout value
        """
        # intercept status request for caching construct
        if (cmd == 'status' or cmd == 'PB_SV_PList') and self.status_cache:
            if time.time() < self.status_cache_expired:
                self.console.verbose2('Using Status: Cached %s' % cmd)
                return self.status_cache_data
            else:
                with self.lock:
                    data = self.sendRcon(cmd, maxRetries=maxRetries, socketTimeout=socketTimeout)
                    if data:
                        self.status_cache_data = data
                        self.status_cache_expired = time.time() + self.status_cache_expire_time
                        self.console.verbose2('Using Status: Fresh %s' % cmd)
                    else:
                        # if no data returned set the cached status to empty, but don't update the expired timer so next attempt will try 
                        # to read a new value
                        self.status_cache_data = ''
                return self.status_cache_data
        
        with self.lock:
            data = self.sendRcon(cmd, maxRetries=maxRetries, socketTimeout=socketTimeout)
        return data if data else ''

    def flush(self):
        pass

    def readNonBlocking(self, sock):
        """
        Read data from the socket (non blocking).
        :param sock: The socket from where to read data
        """
        sock.settimeout(2)
        start_time = time.time()
        data = ''
        while time.time() - start_time < 1:
            try:
                d = str(sock.recv(4096))
            except socket.error, detail:
                self.console.debug('RCON: error reading: %s' % detail)
                break
            else:
                if d:
                    # remove rcon header
                    data += d.replace(self.rconreplystring, '')
                elif len(data) > 0 and ord(data[-1:]) == 10:
                    break

        return data.strip()

    def readSocket(self, sock, size=4096, socketTimeout=None):
        """
        Read data from the socket.
        :param sock: The socket from where to read data
        :param size: The read size
        :param socketTimeout: The socket timeout value
        """
        if socketTimeout is None:
            socketTimeout = self.socket_timeout

        data = ''
        readables, writeables, errors = select.select([sock], [], [sock], socketTimeout)

        if not len(readables):
            self.console.verbose('No readable socket')
            return ''

        while len(readables):
            d = str(sock.recv(size))

            if d:
                # remove rcon header
                data += d.replace(self.rconreplystring, '')

            readables, writeables, errors = select.select([sock], [], [sock], socketTimeout)
            if len(readables):
                self.console.verbose('RCON: more data to read in socket')

        return data

    def close(self):
        pass

    def getRules(self):
        self.lock.acquire()
        try:
            data = self.send('getstatus')
        finally:
            self.lock.release()
        return data if data else ''

    def getInfo(self):
        self.lock.acquire()
        try:
            data = self.send('getinfo')
        finally:
            self.lock.release()
        return data if data else ''

########################################################################################################################
#
# import sys
#
# if __name__ == '__main__':
#     # To run tests : python b3/parsers/q3a_rcon.py <rcon_ip> <rcon_port> <rcon_password>
#     from b3.fake import fakeConsole
#     r = Rcon(fakeConsole, (sys.argv[1], int(sys.argv[2])), sys.argv[3])
#
#     for cmd in ['say "test1"', 'say "test2"', 'say "test3"', 'say "test4"', 'say "test5"']:
#         fakeConsole.info('Writing %s', cmd)
#         data = r.write(cmd)
#         fakeConsole.info('Received %s', data)
#
#     print '----------------------------------------'
#     for cmd in ['say "test1"', 'say "test2"', 'say "test3"', 'say "test4"', 'say "test5"']:
#         fakeConsole.info('Writing %s', cmd)
#         data = r.write(cmd, socketTimeout=0.45)
#         fakeConsole.info('Received %s', data)
#
#     print '----------------------------------------'
#     for cmd in ['.B3', '.Administrator', '.Admin', 'status', 'sv_mapRotation', 'players']:
#         fakeConsole.info('Writing %s', cmd)
#         data = r.write(cmd)
#         fakeConsole.info('Received %s', data)
#
#     print '----------------------------------------'
#     for cmd in ['.B3', '.Administrator', '.Admin', 'status', 'sv_mapRotation', 'players']:
#         fakeConsole.info('Writing %s', cmd)
#         data = r.write(cmd, socketTimeout=0.55)
#         fakeConsole.info('Received %s', data)
#
#     print '----------------------------------------'
#     fakeConsole.info('getRules')
#     data = r.getRules()
#     fakeConsole.info('Received %s', data)
#
#     print '----------------------------------------'
#     fakeConsole.info('getInfo')
#     data = r.getInfo()
#     fakeConsole.info('Received %s', data)