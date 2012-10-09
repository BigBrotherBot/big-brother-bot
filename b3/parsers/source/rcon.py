# coding=UTF-8
#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2012 <courgette@bigbrotherbot.net>
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
# 1.1
# - patch SourceRcon to detect bad rcon password with CS:GO
# - can send unicode commands
# 1.2
# - fix write() method that failed when called with named parameter 'maxRetries'
#
from threading import Event, Lock
from socket import timeout
from Queue import Queue
from b3.lib.sourcelib.SourceRcon import SourceRcon, SERVERDATA_EXECCOMMAND, SERVERDATA_AUTH, SourceRconError

__version__ = '1.2'
__author__ = 'Courgette'



#####################################################################################################
# patch SourceRcon.receive class to detect bad rcon password

legacy_receive = SourceRcon.receive

def receive_wrapper(self):
    rv = legacy_receive(self)
    if isinstance(rv, basestring) and rv.strip().endswith(": Bad Password"):
        raise SourceRconError('Bad RCON password (patched SourceRcon)')
    else:
        return rv

SourceRcon.receive = receive_wrapper

#####################################################################################################



class Rcon(object):
    """
    Facade to expose the SourceRcon class with an API as expected by B3 parsers
    """
    lock = Lock()

    def __init__(self, console, host, password):
        self.console = console
        self.host, self.port = host
        self.password = password
        self.timeout = 1.0
        self.queue = Queue()
        self.stop_event = Event()
        self.server = SourceRcon(self.host, self.port, self.password, self.timeout)

        self.console.info("RCON: connecting to Source game server")
        try:
            self.server.connect()
        except timeout, err:
            self.console.error("RCON: timeout error while trying to connect to game server at %s:%s. "
                               "Make sure the rcon_ip and port are correct and that the game server is "
                               "running" % (self.host, self.port))


    ########################################################
    #
    #   expected B3 Rcon API
    #
    ########################################################

    def writelines(self, lines):
        """
        Sends multiple rcon commands and do not wait for responses (non blocking)
        """
        self.queue.put(lines)


    def write(self, cmd, *args, **kwargs):
        """
        Sends a rcon command and return the response (blocking until timeout)
        """
        with Rcon.lock:
            try:
                self.console.info("RCON SEND: %s" % cmd)
                raw_data = self.server.rcon(self.encode_data(cmd))
                if raw_data:
                    data = raw_data.decode('UTF-8', 'replace')
                    self.console.info("RCON RECEIVED: %s" % data)
                    return data
            except timeout:
                self.console.error("RCON: timeout error while trying to connect to game server at %s:%s. "
                                   "Make sure the rcon_ip and port are correct and that the game server is "
                                   "running" % (self.host, self.port))


    def flush(self):
        pass


    def close(self):
        if self.server:
            try:
                self.console.info("RCON disconnecting from Source game server")
                self.server.disconnect()
                self.console.verbose("RCON disconnected from Source game server")
            finally:
                self.server = None
                del self.server


    ########################################################
    #
    #   others
    #
    ########################################################

    def _writelines(self):
        while not self.stop_event.isSet():
            lines = self.queue.get(True)
            for cmd in lines:
                if not cmd:
                    continue
                with self.lock:
                    self.rconNoWait(cmd)


    def rconNoWait(self, cmd):
        """
        send a single command, do not wait for any response.
        connect and auth if necessary.
        """
        try:
            self.console.info("RCON SEND: %s" % cmd)
            self.server.send(SERVERDATA_EXECCOMMAND, self.encode_data(cmd))
        except Exception:
            # timeout? invalid? we don't care. try one more time.
            self.server.disconnect()
            self.server.connect()
            self.server.send(SERVERDATA_AUTH, self.password)

            auth = self.server.receive()
            # the first packet may be a "you have been banned" or empty string.
            # in the latter case, fetch the second packet
            if auth == '':
                auth = self.server.receive()

            if auth is not True:
                self.server.disconnect()
                raise SourceRconError('RCON authentication failure: %s' % (repr(auth),))

            self.server.send(SERVERDATA_EXECCOMMAND, self.encode_data(cmd))


    def encode_data(self, data):
        if not data:
            return data
        if type(data) is unicode:
            return data.encode('UTF-8')
        else:
            return data


if __name__ == '__main__':
    '''
    To run tests : python b3/parsers/source/rcon.py <rcon_ip> <rcon_port> <rcon_password>
    '''
    import sys, os, time

    host = port = pw = None

    from ConfigParser import SafeConfigParser
    test_config_file = os.path.join(os.path.dirname(__file__), 'test_rcon.ini')
    if os.path.isfile(test_config_file):
        try:
            conf = SafeConfigParser()
            conf.read(test_config_file)
            host = conf.get("server", "host")
            port = int(conf.get("server", "port"))
            pw = conf.get("server", "password")
        except:
            pass

    if not host and not port and not pw:
        if len(sys.argv) != 4:
            host = raw_input('Enter game server host IP/name: ')
            port = int(raw_input('Enter host port: '))
            pw = raw_input('Enter password: ')
        else:
            host = sys.argv[1]
            port = int(sys.argv[2])
            pw = sys.argv[3]

    with open(test_config_file, "w") as f:
        conf = SafeConfigParser()
        conf.add_section('server')
        conf.set("server", "host", host)
        conf.set("server", "port", str(port))
        conf.set("server", "password", pw)
        conf.write(f)

    from b3.fake import fakeConsole

    r = Rcon(fakeConsole, (host, port), pw)
    r.write('sm_say %s' % u"hello ÄÖtest")
