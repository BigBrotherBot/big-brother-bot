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

    def test_getPlayerList_nominal(self):
        # GIVEN
        when(self.console).write('PB_SV_PList').thenReturn('''\
: Player List: [Slot #] [GUID] [Address] [Status] [Power] [Auth Rate] [Recent SS] [O/S] [Name]
: 4  27b26543216546163546513465135135(-) 111.11.1.11:28960 OK   1 3.0 0 (W) "ShyRat"
: 5 387852749658574858598854913cdf11(-) 222.222.222.222:28960 OK   1 10.0 0 (W) "shatgun"
: 6 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5.0 0 (W) "FATTYBMBLATY"
''')
        # WHEN
        rv = self.pb.getPlayerList()
        # THEN
        self.assertSetEqual(set(['3', '4', '5']), set(rv.keys()))
        self.assertDictContainsSubset({'slot': '4', 'pbid': '27b26543216546163546513465135135', 'guid': '27b26543216546163546513465135135', 'ip': '111.11.1.11'}, rv['3'])
        self.assertDictContainsSubset({'slot': '5', 'pbid': '387852749658574858598854913cdf11', 'guid': '387852749658574858598854913cdf11', 'ip': '222.222.222.222'}, rv['4'])
        self.assertDictContainsSubset({'slot': '6', 'pbid': '9732d328485274156125252141252ba1', 'guid': '9732d328485274156125252141252ba1', 'ip': '33.133.3.133'}, rv['5'])


    def test_getPlayerList_missing_chars_randomly(self):
        """ it was reported that PB responses miss a character in an inconsistent manner.
        We do our best to extract the only info we need.
        """
        # GIVEN
        when(self.console).write('PB_SV_PList').thenReturn('''\
: Player List: [Slot #] [GUID] [Address] [Status] [Power] [Auth Rate] [Recent SS] [O/S] [Name]
: 1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5.0 0 (W) "FATTYBMBLATY"
: 2 9732d328485274156125252141252ba1-) 33.133.3.133:-28960 OK   1 5.0 0 (W) "FATTYBMBLATY"
: 3 9732d328485274156125252141252ba1() 33.133.3.133:-28960 OK   1 5.0 0 (W) "FATTYBMBLATY"
: 4 9732d328485274156125252141252ba1(- 33.133.3.133:-28960 OK   1 5.0 0 (W) "FATTYBMBLATY"
: 5 9732d328485274156125252141252ba1(-)33.133.3.133:-28960 OK   1 5.0 0 (W) "FATTYBMBLATY"
: 6 9732d328485274156125252141252ba1(-) 33.133.3.133-28960 OK   1 5.0 0 (W) "FATTYBMBLATY"
: 7 9732d328485274156125252141252ba1(-) 33.133.3.133:28960 OK   1 5.0 0 (W) "FATTYBMBLATY"
: 8 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960OK   1 5.0 0 (W) "FATTYBMBLATY"
: 9 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 O   1 5.0 0 (W) "FATTYBMBLATY"
:10 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK    5.0 0 (W) "FATTYBMBLATY"
:11 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 50 0 (W) "FATTYBMBLATY"
:12 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5. 0 (W) "FATTYBMBLATY"
:13 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5.00 (W) "FATTYBMBLATY"
:14 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5.0  (W) "FATTYBMBLATY"
:15 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5.0 0(W) "FATTYBMBLATY"
:16 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5.0 0 W) "FATTYBMBLATY"
:17 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5.0 0 () "FATTYBMBLATY"
:18 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5.0 0 (W "FATTYBMBLATY"
:19 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5.0 0 (W)"FATTYBMBLATY"
:20 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5.0 0 (W) FATTYBMBLATY"
:21 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5.0 0 (W) "FATTYBMBLATY
''')
        # WHEN
        rv = self.pb.getPlayerList()
        # THEN
        for i in range(21):
            self.assertDictContainsSubset({'slot': str(i+1), 'pbid': '9732d328485274156125252141252ba1', 'guid': '9732d328485274156125252141252ba1', 'ip': '33.133.3.133'}, rv[str(i)])


