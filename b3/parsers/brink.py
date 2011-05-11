# encoding: utf-8
#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2011 
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
#
__author__  = 'Courgette'
__version__ = '0.0'
from b3.parser import Parser
from b3.parsers.q3a.rcon import Rcon as Q3Rcon
import select



"""
 TIPS FOR CONTRIBUTORS :
 =======================

  * In your main config file, set log level down to 8 to see log message of
    type VERBOS2.  <set name="log_level">8</set>

  * You can add the section below in your b3.xml in order to display the log
    file on your console :
        <settings name="devmode">
            <set name="log2console">true</set>
        </settings>

"""



class BrinkRcon(Q3Rcon):
    rconsendstring = '\xff\xffrcon\xff%s\xff%s\xff'
    rconreplystring = '\xff\xffprint\x00'
    qserversendstring = '\xff\xff%s\xff'

    def readSocket(self, sock, size=4048, socketTimeout=None):
        if socketTimeout is None:
            socketTimeout = self.socket_timeout
        data = ''
        readables, writeables, errors = select.select([sock], [], [sock], socketTimeout)
        if not len(readables):
            raise Exception('No readable socket')
        d = str(sock.recv(size))
        if d:
            # remove rcon header
            data += d[12:]
            if len(d)==size:
                readables, writeables, errors = select.select([sock], [], [sock], socketTimeout)
                while len(readables):
                    self.console.verbose('RCON: More data to read in socket')
                    d = str(sock.recv(size))
                    if d:
                        data += d
                    readables, writeables, errors = select.select([sock], [], [sock], socketTimeout)
        return data.rstrip('\x00').strip()



class BrinkParser(Parser):
    gameName = 'brink'
    OutputClass = BrinkRcon
    rconTest = True
        
    def startup(self):
        pass



if __name__ == '__main__':
    from b3.fake import fakeConsole

    def test_rcon():
        server = BrinkRcon(fakeConsole, ('127.0.0.1', 27025), 'pass')

        data = server.sendRcon("serverinfo")

        for line in data.splitlines():
            if line == '\x00':
                print("-"*10)
            else:
                print(line)

        print("%r" % server.sendRcon("sys_cpuSpeed"))
        print('-'*20)


    test_rcon()
