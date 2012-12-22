#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2012 Courgette
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
from mock import Mock
from mockito import when
import unittest2 as unittest
from b3.parsers.punkbuster import PunkBuster


class Test_Punkbuster(unittest.TestCase):

    def setUp(self):
        self.console = Mock()
        self.pb = PunkBuster(self.console)

    def test_getPlayerList(self):
        # GIVEN
        when(self.console).write('PB_SV_PList').thenReturn('''\
: Player List: [Slot #] [GUID] [Address] [Status] [Power] [Auth Rate] [Recent SS] [O/S] [Name]
: 4  27b26543216546163546513465135135(-) 111.11.1.11:28960 OK   1 3.0 0 (W) "ShyRat"
: 5 387852749658574858598854913cdf11(-) 222.222.222.222:28960 OK   10.0 0 (W) "shatgun"
: 6 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5.0 0 (W) "FATTYBMBLATY"
''')
        # WHEN
        rv = self.pb.getPlayerList()
        # THEN
        self.assertDictContainsSubset({
            '3': {'slot': '4', 'pbid': '27b26543216546163546513465135135', 'guid': '27b26543216546163546513465135135', 'ip': '111.11.1.11', 'port': '28960', 'status': 'OK', 'power': '1', 'auth': '3.0', 'ss': '0', 'os': 'W', 'name': 'ShyRat'},
            '4': {'slot': '5', 'pbid': '387852749658574858598854913cdf11', 'guid': '387852749658574858598854913cdf11', 'ip': '222.222.222.222', 'port': '28960', 'status': 'OK', 'power': None, 'auth': '10.0', 'ss': '0', 'os': 'W', 'name': 'shatgun'},
            '5': {'slot': '6', 'pbid': '9732d328485274156125252141252ba1', 'guid': '9732d328485274156125252141252ba1', 'ip': '33.133.3.133', 'port': '-28960', 'status': 'OK', 'power': '1', 'auth': '5.0', 'ss': '0', 'os': 'W', 'name': 'FATTYBMBLATY'}
        }, rv)

