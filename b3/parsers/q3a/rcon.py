#
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
# Changelog :
# 2009/12/06 - 1.3.5 - Courgette
# * make default socket_timeout 800 ms
# * custom socket_timeout and maxRetries can be specified on a per
# call basis
# 2009/12/11 - 1.3.6 - Courgette
# * make errors warnings until maxRetries is not reached
# 2011/2/1 - 1.3.7 - Bravo17
# * added variables for rcon & qserver send & reply strings
# 2011/04/02 - 1.3.8 - Just a baka
# * Quit command should never be retried
# 2011/04/13 - 1.3.9 - Courgette
# * hopefully filter out non ascii characters
# 2011/04/13 - 1.3.10 - Courgette
# * should get rid of UnicodeDecodeError
# 2011/04/20 - 1.4 - Courgette
# * now sent data is encoded as UTF-8
#
 
__author__ = 'ThorN'
__version__ = '1.4'
 
import socket
import sys
import select
import re
import time
import thread
import threading
import Queue
from b3.lib.beaker.cache import CacheManager
from b3.lib.beaker.util import parse_cache_config_options

#--------------------------------------------------------------------------------------------------
class Rcon:
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

    #caching options
    cache_opts = {
    'cache.data_dir': 'b3/cache/data',
    'cache.lock_dir': 'b3/cache/lock',
    }
    #create cache
    cache = CacheManager(**parse_cache_config_options(cache_opts))
    #default expiretime for the status cache in seconds and cache type
    statusCacheExpireTime = 2
    statusCacheType = 'memory'

    def __init__(self, console, host, password):
        self.console = console
        self.queue = Queue.Queue()

        if self.console.config.has_option('caching', 'status_cache_type'):
            self.statusCacheType = self.console.config.get('caching', 'status_cache_type').lower()
            if self.statusCacheType not in ['file', 'memory']:
                self.statusCacheType = 'memory'
        if self.console.config.has_option('caching', 'status_cache_expire'):
            self.statusCacheExpireTime = abs(self.console.config.getint('caching', 'status_cache_expire'))
            if self.statusCacheExpireTime > 5:
                self.statusCacheExpireTime = 5
        self.console.bot('rcon status Cache Expire Time: [%s sec] Type: [%s]' %(self.statusCacheExpireTime, self.statusCacheType))

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.host = host
        self.password = password
        self.socket.settimeout(2)
        self.socket.connect(self.host)

        self._stopEvent = threading.Event()
        thread.start_new_thread(self._writelines, ())

    def send(self, data, maxRetries=None, socketTimeout=None):
        if socketTimeout is None:
            socketTimeout = self.socket_timeout
        if maxRetries is None:
            maxRetries = 2
            
        data = data.strip()
        self.console.verbose('QSERVER sending (%s:%s) %r', self.host[0], self.host[1], data)
        startTime = time.time()

        retries = 0
        while time.time() - startTime < 5:
            readables, writeables, errors = select.select([], [self.socket], [self.socket], socketTimeout)

            if len(errors) > 0:
                self.console.warning('QSERVER: %r', errors)
            elif len(writeables) > 0:
                try:
                    writeables[0].send(self.qserversendstring % unicode(data).encode('UTF-8'))
                except Exception, msg:
                    self.console.warning('QSERVER: ERROR sending: %r', msg)
                else:
                    try:
                        data = self.readSocket(self.socket, socketTimeout=socketTimeout)
                        self.console.verbose2('QSERVER: Received %r' % data)
                        return data
                    except Exception, msg:
                        self.console.warning('QSERVER: ERROR reading: %r', msg)
                    
            else:
                self.console.verbose('QSERVER: no writeable socket')

            time.sleep(0.05)

            retries += 1

            if retries >= maxRetries:
                self.console.error('QSERVER: too much tries. Abording (%r)', data.strip())
                break
 
            self.console.verbose('QSERVER: retry sending %r (%s/%s)...', data.strip(), retries, maxRetries)
 
 
        self.console.debug('QSERVER: Did not send any data')
        return ''
        
    def sendRcon(self, data, maxRetries=None, socketTimeout=None):
        if socketTimeout is None:
            socketTimeout = self.socket_timeout
        if maxRetries is None:
            maxRetries = 2
            
        data = data.strip()
        self.console.verbose('RCON sending (%s:%s) %r', self.host[0], self.host[1], data)
        startTime = time.time()

        retries = 0
        while time.time() - startTime < 5:
            readables, writeables, errors = select.select([], [self.socket], [self.socket], socketTimeout)

            if len(errors) > 0:
                self.console.warning('RCON: %s', str(errors))
            elif len(writeables) > 0:
                try:
                    writeables[0].send(self.rconsendstring % (self.password, unicode(data).encode('UTF-8')))
                except Exception, msg:
                    self.console.warning('RCON: ERROR sending: %r', msg)
                else:
                    try:
                        data = self.readSocket(self.socket, socketTimeout=socketTimeout)
                        self.console.verbose2('RCON: Received %r' % data)
                        return data
                    except Exception, msg:
                        self.console.warning('RCON: ERROR reading: %r', msg)

                if re.match(r'^quit|map(_rotate)?.*', data):
                    # do not retry quits and map changes since they prevent the server from responding
                    self.console.verbose2('RCON: no retry for %r', data)
                    return ''
                    
            else:
                self.console.verbose('RCON: no writeable socket')

            time.sleep(0.05)

            retries += 1

            if retries >= maxRetries:
                self.console.error('RCON: too much tries. Abording (%r)', data.strip())
                break
            self.console.verbose('RCON: retry sending %r (%s/%s)...', data.strip(), retries, maxRetries)



        self.console.debug('RCON: Did not send any data')
        return ''


    def stop(self):
        """Stop the rcon writelines queue"""
        self._stopEvent.set()

    def _writelines(self):
        while not self._stopEvent.isSet():
            lines = self.queue.get(True)

            self.lock.acquire()
            try:
                data = ''

                i = 0
                for cmd in lines:
                    if i > 0:
                        # pause and give time for last send to finish
                        time.sleep(1)

                    if not cmd: 
                        continue

                    d = self.sendRcon(cmd)
                    if d:
                        data += d

                    i+=1
            finally:
                self.lock.release()

    def writelines(self, lines):
        self.queue.put(lines)

    def write(self, cmd, maxRetries=None, socketTimeout=None, Cached=True):
        #intercept status request for caching construct
        if cmd == 'status' and Cached:
            status_cache = self.cache.get_cache('status', type=self.statusCacheType, expire=self.statusCacheExpireTime)
            data = status_cache.get(key='status', createfunc=self._requestStatusCached)
            return data

        self.lock.acquire()
        try:
            data = self.sendRcon(cmd, maxRetries=maxRetries, socketTimeout=socketTimeout)
        finally:
            self.lock.release()

        if data:
            return data
        else:
            return ''

    def _requestStatusCached(self):
        self.lock.acquire()
        try:
            data = self.sendRcon('status', maxRetries=5)
        finally:
            self.lock.release()
        if data:
            return data
        else:
            return ''


    def flush(self):
        pass

    def readNonBlocking(self, sock):
        sock.settimeout(2)

        startTime = time.time()

        data = ''
        while time.time() - startTime < 1:
            try:
                d = str(sock.recv(4096))
            except socket.error, detail:
                self.console.debug('RCON: ERROR reading: %s' % detail)
                break
            else:
                if d:
                    # remove rcon header
                    data += d.replace(self.rconreplystring, '')
                elif len(data) > 0 and ord(data[-1:]) == 10:
                    break

        return data.strip()

    def readSocket(self, sock, size=4096, socketTimeout=None):
        if socketTimeout is None:
            socketTimeout = self.socket_timeout
            
        data = ''

        readables, writeables, errors = select.select([sock], [], [sock], socketTimeout)
        
        if not len(readables):
            raise Exception('No readable socket')

        while len(readables):
            d = str(sock.recv(size))

            if d:
                # remove rcon header
                data += d.replace(self.rconreplystring, '')
            
            readables, writeables, errors = select.select([sock], [], [sock], socketTimeout)

            if len(readables):
                self.console.verbose('RCON: More data to read in socket')

        return data.strip()

    def close(self):
        pass
        
    def getRules(self):
        self.lock.acquire()
        try:
            data = self.send('getstatus')
        finally:
            self.lock.release()

        if data:
            return data
        else:
            return ''
            
    def getInfo(self):
        self.lock.acquire()
        try:
            data = self.send('getinfo')
        finally:
            self.lock.release()

        if data:
            return data
        else:
            return ''
            
if __name__ == '__main__':
    """
To run tests : python b3/parsers/q3a_rcon.py <rcon_ip> <rcon_port> <rcon_password>
"""
    
    from b3.fake import fakeConsole

    r = Rcon(fakeConsole, (sys.argv[1], int(sys.argv[2])), sys.argv[3])
    
    for cmd in ['say "test1"', 'say "test2"', 'say "test3"', 'say "test4"', 'say "test5"']:
        fakeConsole.info('Writing %s', cmd)
        data = r.write(cmd)
        fakeConsole.info('Recieved %s', data)

    print '----------------------------------------'
    for cmd in ['say "test1"', 'say "test2"', 'say "test3"', 'say "test4"', 'say "test5"']:
        fakeConsole.info('Writing %s', cmd)
        data = r.write(cmd, socketTimeout=0.45)
        fakeConsole.info('Recieved %s', data)

    print '----------------------------------------'
    for cmd in ['.B3', '.Administrator', '.Admin', 'status', 'sv_mapRotation', 'players']:
        fakeConsole.info('Writing %s', cmd)
        data = r.write(cmd)
        fakeConsole.info('Recieved %s', data)
        
    print '----------------------------------------'
    for cmd in ['.B3', '.Administrator', '.Admin', 'status', 'sv_mapRotation', 'players']:
        fakeConsole.info('Writing %s', cmd)
        data = r.write(cmd, socketTimeout=0.55)
        fakeConsole.info('Recieved %s', data)
    
    print '----------------------------------------'
    fakeConsole.info('getRules')
    data = r.getRules()
    fakeConsole.info('Recieved %s', data)
    
    print '----------------------------------------'
    fakeConsole.info('getInfo')
    data = r.getInfo()
    fakeConsole.info('Recieved %s', data)
