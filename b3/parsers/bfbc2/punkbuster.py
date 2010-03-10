#
# BigBrotherBot(B3) (www.bigbrotherbot.com)
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

__author__  = 'Courgette'
__version__ = '1.0'

import re
import b3.parsers.punkbuster

#--------------------------------------------------------------------------------------------------
class PunkBuster(b3.parsers.punkbuster.PunkBuster):
    regPlayer = re.compile(r'^.*?:\s+(?P<slot>[0-9]+)\s+(?P<pbid>[a-z0-9]+)\s?\([^>)]+\)\s(?P<ip>[0-9.:]+):(?P<port>[0-9-]+) (?P<status>[a-z]+)\s+(?P<power>[0-9]+)\s+(?P<auth>[0-9.]+)\s+(?P<ss>[0-9]+)(\{[^}]+\})?\s+\((?P<os>[^)]+)\)\s+"?(?P<name>[^"]+)"?$', re.I)

    def send(self, command):
        return self.console.write(('punkBuster.pb_sv_command', command))

    def getPlayerList(self):
        data = self.pList()
        if not data:
            return {}

        players = {}
        for line in data.split('\n'):
            m = re.match(self.regPlayer, line)
            if m:
                d = m.groupdict()
                d['guid'] = d['pbid']
                players[int(m.group('slot')) - 1] = d

        return players

