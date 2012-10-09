#!/usr/bin/python
# -*- coding: utf-8 -*-

#------------------------------------------------------------------------------
# SourceRcon - Python class for executing commands on Source Dedicated Servers
# Copyright (c) 2010 Andreas Klauer <Andreas.Klauer@metamorpher.de>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#------------------------------------------------------------------------------

"""http://developer.valvesoftware.com/wiki/Source_RCON_Protocol"""

import select, socket, struct

SERVERDATA_AUTH = 3
SERVERDATA_AUTH_RESPONSE = 2

SERVERDATA_EXECCOMMAND = 2
SERVERDATA_RESPONSE_VALUE = 0

MAX_COMMAND_LENGTH=510 # found by trial & error

MIN_MESSAGE_LENGTH=4+4+1+1 # command (4), id (4), string1 (1), string2 (1)
MAX_MESSAGE_LENGTH=4+4+4096+1 # command (4), id (4), string (4096), string2 (1)

# there is no indication if a packet was split, and they are split by lines
# instead of bytes, so even the size of split packets is somewhat random.
# Allowing for a line length of up to 400 characters, risk waiting for an
# extra packet that may never come if the previous packet was this large.
PROBABLY_SPLIT_IF_LARGER_THAN = MAX_MESSAGE_LENGTH - 400

class SourceRconError(Exception):
    pass

class SourceRcon(object):
    """Example usage:

       import SourceRcon
       server = SourceRcon.SourceRcon('1.2.3.4', 27015, 'secret')
       print server.rcon('cvarlist')
    """
    def __init__(self, host, port=27015, password='', timeout=1.0):
        self.host = host
        self.port = port
        self.password = password
        self.timeout = timeout
        self.tcp = False
        self.reqid = 0

    def disconnect(self):
        """Disconnect from the server."""
        if self.tcp:
            self.tcp.close()

    def connect(self):
        """Connect to the server. Should only be used internally."""
        self.tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp.settimeout(self.timeout)
        self.tcp.connect((self.host, self.port))

    def send(self, cmd, message):
        """Send command and message to the server. Should only be used internally."""
        if len(message) > MAX_COMMAND_LENGTH:
            raise SourceRconError('RCON message too large to send')

        self.reqid += 1
        data = struct.pack('<l', self.reqid) + struct.pack('<l', cmd) + message + '\x00\x00'
        self.tcp.send(struct.pack('<l', len(data)) + data)

    def receive(self):
        """Receive a reply from the server. Should only be used internally."""
        packetsize = False
        requestid = False
        response = False
        message = ''
        message2 = ''

        # response may be split into multiple packets, we don't know how many
        # so we loop until we decide to finish
        while 1:
            # read the size of this packet
            buf = ''

            while len(buf) < 4:
                try:
                    recv = self.tcp.recv(4 - len(buf))
                    if not len(recv):
                        raise SourceRconError('RCON connection unexpectedly closed by remote host')
                    buf += recv
                except SourceRconError:
                    raise
                except:
                    break

            if len(buf) != 4:
                # we waited for a packet but there isn't anything
                break

            packetsize = struct.unpack('<l', buf)[0]

            if packetsize < MIN_MESSAGE_LENGTH or packetsize > MAX_MESSAGE_LENGTH:
                raise SourceRconError('RCON packet claims to have illegal size: %d bytes' % (packetsize,))

            # read the whole packet
            buf = ''

            while len(buf) < packetsize:
                try:
                    recv = self.tcp.recv(packetsize - len(buf))
                    if not len(recv):
                        raise SourceRconError('RCON connection unexpectedly closed by remote host')
                    buf += recv
                except SourceRconError:
                    raise
                except:
                    break

            if len(buf) != packetsize:
                raise SourceRconError('Received RCON packet with bad length (%d of %d bytes)' % (len(buf),packetsize,))

            # parse the packet
            requestid = struct.unpack('<l', buf[:4])[0]

            if requestid == -1:
                self.disconnect()
                raise SourceRconError('Bad RCON password')

            elif requestid != self.reqid:
                raise SourceRconError('RCON request id error: %d, expected %d' % (requestid,self.reqid,))

            response = struct.unpack('<l', buf[4:8])[0]

            if response == SERVERDATA_AUTH_RESPONSE:
                # This response says we're successfully authed.
                return True

            elif response != SERVERDATA_RESPONSE_VALUE:
                raise SourceRconError('Invalid RCON command response: %d' % (response,))

            # extract the two strings using index magic
            str1 = buf[8:]
            pos1 = str1.index('\x00')
            str2 = str1[pos1+1:]
            pos2 = str2.index('\x00')
            crap = str2[pos2+1:]

            if crap:
                raise SourceRconError('RCON response contains %d superfluous bytes' % (len(crap),))

            # add the strings to the full message result
            message += str1[:pos1]
            message2 += str2[:pos2]

            # unconditionally poll for more packets
            poll = select.select([self.tcp], [], [], 0)

            if not len(poll[0]) and packetsize < PROBABLY_SPLIT_IF_LARGER_THAN:
                # no packets waiting, previous packet wasn't large: let's stop here.
                break

        if response is False:
            raise SourceRconError('Timed out while waiting for reply')

        elif message2:
            raise SourceRconError('Invalid response message: %s' % (repr(message2),))

        return message

    def rcon(self, command):
        """Send RCON command to the server. Connect and auth if necessary,
           handle dropped connections, send command and return reply."""
        # special treatment for sending whole scripts
        if '\n' in command:
            commands = command.split('\n')
            def f(x): y = x.strip(); return len(y) and not y.startswith("//")
            commands = filter(f, commands)
            results = map(self.rcon, commands)
            return "".join(results)

        # send a single command. connect and auth if necessary.
        try:
            self.send(SERVERDATA_EXECCOMMAND, command)
            return self.receive()
        except:
            # timeout? invalid? we don't care. try one more time.
            self.disconnect()
            self.connect()
            self.send(SERVERDATA_AUTH, self.password)

            auth = self.receive()
            # the first packet may be a "you have been banned" or empty string.
            # in the latter case, fetch the second packet
            if auth == '':
                auth = self.receive()

            if auth is not True:
                self.disconnect()
                raise SourceRconError('RCON authentication failure: %s' % (repr(auth),))

            self.send(SERVERDATA_EXECCOMMAND, command)
            return self.receive()
