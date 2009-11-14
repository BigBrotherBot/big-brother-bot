#
# BigBrotherBot(B3) (www.bigbrotherbot.com)
# Copyright (C) 2005 Michael "ThorN" Thornton
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

__author__  = 'ThorN'
__version__ = '1.3.4'

import socket, sys, select, re, time, thread, threading, Queue

#--------------------------------------------------------------------------------------------------
class Rcon:
    host = ()
    password = None
    lock = thread.allocate_lock()
    socket = None
    queue = None
    console = None
    socket_timeout = 0.55

    def __init__(self, console, host, password):
        self.console = console
        self.queue = Queue.Queue()

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.host = host
        self.password = password
        self.socket.settimeout(2)
        self.socket.connect(self.host)

        self._stopEvent = threading.Event()
        thread.start_new_thread(self._writelines, ())

    def send(self, data):
        data = data.strip()
        self.console.verbose('QSERVER sending (%s:%s) %s', self.host[0], self.host[1], data)
        startTime = time.time()

        retries = 0
        while time.time() - startTime < 5:
            readables, writeables, errors = select.select([], [self.socket], [self.socket], self.socket_timeout)

            if len(errors) > 0:
                self.console.error('QSERVER: %s', str(errors))
            elif len(writeables) > 0:
                try:
                    writeables[0].send('\377\377\377\377%s\n' % data)
                except Exception, msg:
                    self.console.error('QSERVER: ERROR sending: %s', msg)
                else:
                    try:
                        data = self.readSocket(self.socket)
                        self.console.verbose2('QSERVER: Received %s' % data)
                        return data
                    except Exception, msg:
                        self.console.error('QSERVER: ERROR reading: %s', msg)
                    
            else:
                self.console.verbose('QSERVER: no writeable socket')

            time.sleep(0.05)

            retries += 1

            if retries >= 2:
                break

            self.console.verbose('QSERVER: retry sending %s...', data.strip())


        self.console.debug('QSERVER: Did not send any data')
        return ''
        
    def sendRcon(self, data):
        data = data.strip()
        self.console.verbose('RCON sending (%s:%s) %s', self.host[0], self.host[1], data)
        startTime = time.time()

        retries = 0
        while time.time() - startTime < 5:
            readables, writeables, errors = select.select([], [self.socket], [self.socket], self.socket_timeout)

            if len(errors) > 0:
                self.console.error('RCON: %s', str(errors))
            elif len(writeables) > 0:
                try:
                    writeables[0].send('\377\377\377\377rcon "%s" %s\n' % (self.password, data))
                except Exception, msg:
                    self.console.error('RCON: ERROR sending: %s', msg)
                else:
                    try:
                        data = self.readSocket(self.socket)
                        self.console.verbose2('RCON: Received %s' % data)
                        return data
                    except Exception, msg:
                        self.console.error('RCON: ERROR reading: %s', msg)

                if re.match(r'^map(_rotate)?.*', data):
                    # do not retry map changes since they prevent the server from responding
                    self.console.verbose2('RCON: no retry for %s', data)
                    return ''
                    
            else:
                self.console.verbose('RCON: no writeable socket')

            time.sleep(0.05)

            retries += 1

            if retries >= 2:
                break

            self.console.verbose('RCON: retry sending %s...', data.strip())


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

    def write(self, cmd):
        self.lock.acquire()
        try:
            data = self.sendRcon(cmd)
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
                    data += d.replace('\377\377\377\377print\n', '')
                elif len(data) > 0 and ord(data[-1:]) == 10:
                    break

        return data.strip()

    def readSocket(self, sock, size=4096):
        data = ''

        readables, writeables, errors = select.select([sock], [], [sock], self.socket_timeout)
        
        if not len(readables):
            raise Exception('No readable socket')

        while len(readables):
            d = str(sock.recv(size))

            if d:
                # remove rcon header
                data += d.replace('\377\377\377\377print\n', '')
            
            readables, writeables, errors = select.select([sock], [], [sock], self.socket_timeout)

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
    
    from b3.fake import FakeConsole

    c = FakeConsole()
    r = Rcon(c, (sys.argv[1], int(sys.argv[2])), sys.argv[3])
    
    r.socket_timeout = 1
    for cmd in ['say "test1"', 'say "test2"', 'say "test3"', 'say "test4"', 'say "test5"']:
        c.info('Writing %s', cmd)
        data = r.write(cmd)
        c.info('Recieved %s', data)

    r.socket_timeout = 0.1
    for cmd in ['say "test1"', 'say "test2"', 'say "test3"', 'say "test4"', 'say "test5"']:
        c.info('Writing %s', cmd)
        data = r.write(cmd)
        c.info('Recieved %s', data)

    r.socket_timeout = 1
    for cmd in ['.B3', '.Administrator', '.Admin', 'status', 'sv_mapRotation', 'players']:
        c.info('Writing %s', cmd)
        data = r.write(cmd)
        c.info('Recieved %s', data)
        
    r.socket_timeout = 0.1
    for cmd in ['.B3', '.Administrator', '.Admin', 'status', 'sv_mapRotation', 'players']:
        c.info('Writing %s', cmd)
        data = r.write(cmd)
        c.info('Recieved %s', data)
    
    r.socket_timeout = 1
    c.info('getRules')
    data = r.getRules()
    c.info('Recieved %s', data)
    c.info('getInfo')
    data = r.getInfo()
    c.info('Recieved %s', data)
