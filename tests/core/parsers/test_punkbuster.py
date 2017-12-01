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
import logging
from mockito import when
from b3.parsers.punkbuster import PunkBuster
from tests import B3TestCase
from b3.output import VERBOSE2


class Test_Punkbuster(B3TestCase):

    def setUp(self):
        logger = logging.getLogger('output')
        logger.propagate = False
        B3TestCase.setUp(self)
        self.pb = PunkBuster(self.console)
        logger.setLevel(VERBOSE2)
        logger.propagate = True

    def test_getPlayerList_nominal(self):
        # GIVEN
        when(self.console).write('PB_SV_PList').thenReturn('''\
: Player List: [Slot #] [GUID] [Address] [Status] [Power] [Auth Rate] [Recent SS] [O/S] [Name]
: 4  27b26543216546163546513465135135(-) 111.11.1.11:28960 OK   1 3.0 0 (W) "ShyRat"
: 5 387852749658574858598854913cdf11(-) 222.222.222.222:28960 OK   1 10.0 0 (W) "shatgun"
: 6 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5.0 0 (W) "FATTYBMBLATY"
^3PunkBuster Server: 7 290d4ad01d240000000026f304572ea(VALID) 11.43.50.163:28960 OK   1 3.0 0 (W) "RascalJr>XI<"
^3PunkBuster Server: 8290d4ad01d240000000026f304572eaf(VALID) 11.43.50.163:28960 OK   1 3.0 0 (W) "RascalJr>XI<"
''')
        # WHEN
        rv = self.pb.getPlayerList()
        # THEN
        self.assertDictContainsSubset({'slot': '4', 'pbid': '27b26543216546163546513465135135', 'guid': '27b26543216546163546513465135135', 'ip': '111.11.1.11', 'name': 'ShyRat'}, rv.get('3', {}))
        self.assertDictContainsSubset({'slot': '5', 'pbid': '387852749658574858598854913cdf11', 'guid': '387852749658574858598854913cdf11', 'ip': '222.222.222.222', 'name': 'shatgun'}, rv.get('4', {}))
        self.assertDictContainsSubset({'slot': '6', 'pbid': '9732d328485274156125252141252ba1', 'guid': '9732d328485274156125252141252ba1', 'ip': '33.133.3.133', 'name': 'FATTYBMBLATY'}, rv.get('5', {}))
        self.assertDictContainsSubset({'slot': '7', 'pbid': '290d4ad01d240000000026f304572ea', 'guid': '290d4ad01d240000000026f304572ea', 'ip': '11.43.50.163', 'name': 'RascalJr>XI<'}, rv.get('6', {}))
        self.assertDictContainsSubset({'slot': '8', 'pbid': '290d4ad01d240000000026f304572eaf', 'guid': '290d4ad01d240000000026f304572eaf', 'ip': '11.43.50.163', 'name': 'RascalJr>XI<'}, rv.get('7', {}))

    def test_getPlayerList_with_color_prefix(self):
        # GIVEN
        when(self.console).write('PB_SV_PList').thenReturn('''\
^3PunkBuster Server: Player List: [Slot #] [GUID] [Address] [Status] [Power] [Auth Rate] [Recent SS] [O/S] [Name]
^3PunkBuster Server: 1  290d4ad01d240000000026f3045720ea(VALID) 11.43.50.163:28960 OK   1 3.0 0 (W) "RascalJr>XI<"
^3PunkBuster Server: 2  a645e2a3a37200000000c5cebc1fc23f(VALID) 11.70.166.147:28960 OK   1 3.3 0 (W) "Szopen"
^3PunkBuster Server: 3  a251eea4c887000000000645f5ddca23(VALID) 11.93.170.145:28960 OK   1 3.0 0 (W) "Gatorgirl>XI<"
^3PunkBuster Server: 4  70b4914e81120000000020766dc48450(VALID) 11.126.17.53:28962 OK   1 3.0 0 (W) "chewmysaxJR>XI<"
^3PunkBuster Server: 5  01f540988986000000000a0f7c7bf48f(VALID) 11.197.210.166:28960 OK   1 3.0 0 (W) "|B|HELLSPAWN"
^3PunkBuster Server: 6  38e7b5ab9c6100000000cbe75d7ce9c2(VALID) 11.216.172.20:28960 OK   1 3.1 0 (W) "Xp3rT>XI<"
^3PunkBuster Server: 7  f8dfea9a5e2300000000876c14403b94(VALID) 11.212.246.118:28960 OK   1 3.0 0 (W) "[TO]Patriot"
^3PunkBuster Server: 8  e0fc8351d95c00000000f048e961eedc(VALID) 11.213.226.170:28960 OK   1 3.0 0 (W) "^2|D2|^1Corp"
^3PunkBuster Server: 9  a251eea4c887000000000645f5ddca23(VALID) 11.93.170.145:56969 OK   1 3.0 0 (W) "Angus >XI<"
^3PunkBuster Server: 10 71305d46e6a000000000a71501d23a48(VALID) 11.228.145.96:28960 OK   1 3.0 0 (W) ":.:RaDaR:.:"
^3PunkBuster Server: 11 33f77d20d6d000000000b08807defb1(VALID) 11.252.69.220:28960 OK   1 3.0 0 (W) "motodude>XI<"
^3PunkBuster Server: 12 adb91dcf5277000000004fff22df9930(VALID) 11.55.191.99:28960 OK   1 3.0 0 (W) "<X> Art Intel"
^3PunkBuster Server: 13 bda238afe0a900000000a91512f3d8ed(VALID) 11.235.70.149:28960 OK   1 3.0 0 (W) "UnChileno>XI<AD"
^3PunkBuster Server: 14 fe64aacedc6c0000000061271334da91(VALID) 11.43.34.219:28960 OK   1 3.0 0 (W) "UnArmed>XI<"
^3PunkBuster Server: 15 3c5c02546bd900000000bdcee588b243(VALID) 11.248.226.6:45696 OK   1 3.1 0 (M) "Kato"
^3PunkBuster Server: 16 d5f52bcc8ccb00000000453ea2c40266(VALID) 11.201.169.193:51461 OK   1 3.0 0 (W) "Xalandra"
^3PunkBuster Server: 17 3634bef3586c00000000be14cfc6d6c0(VALID) 11.177.104.230:28960 OK   1 3.1 0 (W) "=GEG=Devil"
^3PunkBuster Server: 18 896f2a1b018500000000bd3d4719fa20(VALID) 11.53.2.85:28960 OK   1 3.0 0 (W) "gi.Timmah!"
^3PunkBuster Server: 19 ea6c0590d1700000000087dac8a4a4bd(VALID) 11.51.188.97:28960 OK   1 3.0 0 (M) "chomama>XI<"
^3PunkBuster Server: 20 3a432901787e000000003ce5525dbfc3(VALID) 11.141.203.77:28960 OK   1 3.0 0 (W) "Sheepdog45>XI<"
^3PunkBuster Server: 21 a1f6548635d1000000004e623aa78271(VALID) 11.183.5.54:28960 OK   1 3.0 0 (W) "KillerKitty>XI<"
^3PunkBuster Server: 22 951d9c7e0ec400000000afccff20a5e7(VALID) 11.94.100.12:55959 OK   1 3.0 0 (W) "Bama>XI<ADM"
^3PunkBuster Server: 23 ea8d4efaed70000000004cf39b04816c(VALID) 11.193.122.135:28960 OK   1 3.0 0 (W) "^6P!nk^0>XI<Adm"
^3PunkBuster Server: 24 639d096de997000000001af19daef6ea(VALID) 11.108.11.19:62451 OK   1 3.2 0 (W) "Iron Belly>XI<"
^3PunkBuster Server: 25 b86f0bb06a0f00000000ee6fab2f33ef(VALID) 11.10.109.13:28960 OK   1 3.0 0 (W) "criss59"
^3PunkBuster Server: 26 1c8500be8b0100000000b76a4e0c2b96(VALID) 11.227.254.172:43459 OK   1 3.0 0 (M) "snipeRover"
^3PunkBuster Server: 27 f2b31d7bb120000000005a3913b0df1a(VALID) 11.214.133.187:28960 OK   1 3.0 0 (W) "^4google>XI<"
^3PunkBuster Server: 280e038f99dbf000000000980bc3c34567(VALID) 11.213.204.52:28960 OK   1 3.0 0 (W) "snaFU73 >XI<"
^3PunkBuster Server: 30 7a0b82d0396f000000003fa9a94f77b6(VALID) 11.2.215.216:28960 OK   1 3.0 0 (W) "drunksniper>XI<"
^3PunkBuster Server: 31 015dd0825cb100000000ee2500094db9(VALID) 11.138.243.153:63489 OK   1 3.0 0 (W) "RUSOKINGNOOB"
^3PunkBuster Server: 32 35731f786cc6000000003cefbf06ad53(VALID) 11.67.148.6:28960 OK   1 3.0 0 (W) "Deckard>XI<"
^3PunkBuster Server: 33 cc2f13bed79a00000000c43d2261425e(VALID) 11.145.139.44:28960 OK   1 3.0 0 (W) "ZABluesilver"
^3PunkBuster Server: End of Player List (32 Players)
''')
        # WHEN
        rv = self.pb.getPlayerList()
        # THEN
        self.assertDictContainsSubset({'slot': '1', 'pbid': '290d4ad01d240000000026f3045720ea', 'guid': '290d4ad01d240000000026f3045720ea', 'ip': '11.43.50.163', 'name': 'RascalJr>XI<'}, rv.get('0', {}))
        self.assertDictContainsSubset({'slot': '2', 'pbid': 'a645e2a3a37200000000c5cebc1fc23f', 'guid': 'a645e2a3a37200000000c5cebc1fc23f', 'ip': '11.70.166.147', 'name': 'Szopen'}, rv.get('1', {}))
        self.assertDictContainsSubset({'slot': '3', 'pbid': 'a251eea4c887000000000645f5ddca23', 'guid': 'a251eea4c887000000000645f5ddca23', 'ip': '11.93.170.145', 'name': 'Gatorgirl>XI<'}, rv.get('2', {}))
        self.assertDictContainsSubset({'slot': '4', 'pbid': '70b4914e81120000000020766dc48450', 'guid': '70b4914e81120000000020766dc48450', 'ip': '11.126.17.53', 'name': 'chewmysaxJR>XI<'}, rv.get('3', {}))
        self.assertDictContainsSubset({'slot': '5', 'pbid': '01f540988986000000000a0f7c7bf48f', 'guid': '01f540988986000000000a0f7c7bf48f', 'ip': '11.197.210.166', 'name': '|B|HELLSPAWN'}, rv.get('4', {}))
        self.assertDictContainsSubset({'slot': '6', 'pbid': '38e7b5ab9c6100000000cbe75d7ce9c2', 'guid': '38e7b5ab9c6100000000cbe75d7ce9c2', 'ip': '11.216.172.20', 'name': 'Xp3rT>XI<'}, rv.get('5', {}))
        self.assertDictContainsSubset({'slot': '7', 'pbid': 'f8dfea9a5e2300000000876c14403b94', 'guid': 'f8dfea9a5e2300000000876c14403b94', 'ip': '11.212.246.118', 'name': '[TO]Patriot'}, rv.get('6', {}))
        self.assertDictContainsSubset({'slot': '8', 'pbid': 'e0fc8351d95c00000000f048e961eedc', 'guid': 'e0fc8351d95c00000000f048e961eedc', 'ip': '11.213.226.170', 'name': '^2|D2|^1Corp'}, rv.get('7', {}))
        self.assertDictContainsSubset({'slot': '9', 'pbid': 'a251eea4c887000000000645f5ddca23', 'guid': 'a251eea4c887000000000645f5ddca23', 'ip': '11.93.170.145', 'name': 'Angus >XI<'}, rv.get('8', {}))
        self.assertDictContainsSubset({'slot': '10', 'pbid': '71305d46e6a000000000a71501d23a48', 'guid': '71305d46e6a000000000a71501d23a48', 'ip': '11.228.145.96', 'name': ':.:RaDaR:.:'}, rv.get('9', {}))
        self.assertDictContainsSubset({'slot': '11', 'pbid': '33f77d20d6d000000000b08807defb1', 'guid': '33f77d20d6d000000000b08807defb1', 'ip': '11.252.69.220', 'name': 'motodude>XI<'}, rv.get('10', {}))
        self.assertDictContainsSubset({'slot': '12', 'pbid': 'adb91dcf5277000000004fff22df9930', 'guid': 'adb91dcf5277000000004fff22df9930', 'ip': '11.55.191.99', 'name': '<X> Art Intel'}, rv.get('11', {}))
        self.assertDictContainsSubset({'slot': '13', 'pbid': 'bda238afe0a900000000a91512f3d8ed', 'guid': 'bda238afe0a900000000a91512f3d8ed', 'ip': '11.235.70.149', 'name': 'UnChileno>XI<AD'}, rv.get('12', {}))
        self.assertDictContainsSubset({'slot': '14', 'pbid': 'fe64aacedc6c0000000061271334da91', 'guid': 'fe64aacedc6c0000000061271334da91', 'ip': '11.43.34.219', 'name': 'UnArmed>XI<'}, rv.get('13', {}))
        self.assertDictContainsSubset({'slot': '15', 'pbid': '3c5c02546bd900000000bdcee588b243', 'guid': '3c5c02546bd900000000bdcee588b243', 'ip': '11.248.226.6', 'name': 'Kato'}, rv.get('14', {}))
        self.assertDictContainsSubset({'slot': '16', 'pbid': 'd5f52bcc8ccb00000000453ea2c40266', 'guid': 'd5f52bcc8ccb00000000453ea2c40266', 'ip': '11.201.169.193', 'name': 'Xalandra'}, rv.get('15', {}))
        self.assertDictContainsSubset({'slot': '17', 'pbid': '3634bef3586c00000000be14cfc6d6c0', 'guid': '3634bef3586c00000000be14cfc6d6c0', 'ip': '11.177.104.230', 'name': '=GEG=Devil'}, rv.get('16', {}))
        self.assertDictContainsSubset({'slot': '18', 'pbid': '896f2a1b018500000000bd3d4719fa20', 'guid': '896f2a1b018500000000bd3d4719fa20', 'ip': '11.53.2.85', 'name': 'gi.Timmah!'}, rv.get('17', {}))
        self.assertDictContainsSubset({'slot': '19', 'pbid': 'ea6c0590d1700000000087dac8a4a4bd', 'guid': 'ea6c0590d1700000000087dac8a4a4bd', 'ip': '11.51.188.97', 'name': 'chomama>XI<'}, rv.get('18', {}))
        self.assertDictContainsSubset({'slot': '20', 'pbid': '3a432901787e000000003ce5525dbfc3', 'guid': '3a432901787e000000003ce5525dbfc3', 'ip': '11.141.203.77', 'name': 'Sheepdog45>XI<'}, rv.get('19', {}))
        self.assertDictContainsSubset({'slot': '21', 'pbid': 'a1f6548635d1000000004e623aa78271', 'guid': 'a1f6548635d1000000004e623aa78271', 'ip': '11.183.5.54', 'name': 'KillerKitty>XI<'}, rv.get('20', {}))
        self.assertDictContainsSubset({'slot': '22', 'pbid': '951d9c7e0ec400000000afccff20a5e7', 'guid': '951d9c7e0ec400000000afccff20a5e7', 'ip': '11.94.100.12', 'name': 'Bama>XI<ADM'}, rv.get('21', {}))
        self.assertDictContainsSubset({'slot': '23', 'pbid': 'ea8d4efaed70000000004cf39b04816c', 'guid': 'ea8d4efaed70000000004cf39b04816c', 'ip': '11.193.122.135', 'name': '^6P!nk^0>XI<Adm'}, rv.get('22', {}))
        self.assertDictContainsSubset({'slot': '24', 'pbid': '639d096de997000000001af19daef6ea', 'guid': '639d096de997000000001af19daef6ea', 'ip': '11.108.11.19', 'name': 'Iron Belly>XI<'}, rv.get('23', {}))
        self.assertDictContainsSubset({'slot': '25', 'pbid': 'b86f0bb06a0f00000000ee6fab2f33ef', 'guid': 'b86f0bb06a0f00000000ee6fab2f33ef', 'ip': '11.10.109.13', 'name': 'criss59'}, rv.get('24', {}))
        self.assertDictContainsSubset({'slot': '26', 'pbid': '1c8500be8b0100000000b76a4e0c2b96', 'guid': '1c8500be8b0100000000b76a4e0c2b96', 'ip': '11.227.254.172', 'name': 'snipeRover'}, rv.get('25', {}))
        self.assertDictContainsSubset({'slot': '27', 'pbid': 'f2b31d7bb120000000005a3913b0df1a', 'guid': 'f2b31d7bb120000000005a3913b0df1a', 'ip': '11.214.133.187', 'name': '^4google>XI<'}, rv.get('26', {}))
        self.assertDictContainsSubset({'slot': '28', 'pbid': '0e038f99dbf000000000980bc3c34567', 'guid': '0e038f99dbf000000000980bc3c34567', 'ip': '11.213.204.52', 'name': 'snaFU73 >XI<'}, rv.get('27', {}))
        self.assertDictContainsSubset({'slot': '30', 'pbid': '7a0b82d0396f000000003fa9a94f77b6', 'guid': '7a0b82d0396f000000003fa9a94f77b6', 'ip': '11.2.215.216', 'name': 'drunksniper>XI<'}, rv.get('29', {}))
        self.assertDictContainsSubset({'slot': '31', 'pbid': '015dd0825cb100000000ee2500094db9', 'guid': '015dd0825cb100000000ee2500094db9', 'ip': '11.138.243.153', 'name': 'RUSOKINGNOOB'}, rv.get('30', {}))
        self.assertDictContainsSubset({'slot': '32', 'pbid': '35731f786cc6000000003cefbf06ad53', 'guid': '35731f786cc6000000003cefbf06ad53', 'ip': '11.67.148.6', 'name': 'Deckard>XI<'}, rv.get('31', {}))
        self.assertDictContainsSubset({'slot': '33', 'pbid': 'cc2f13bed79a00000000c43d2261425e', 'guid': 'cc2f13bed79a00000000c43d2261425e', 'ip': '11.145.139.44', 'name': 'ZABluesilver'}, rv.get('32', {}))


    def test_getPlayerList_missing_chars_randomly(self):
        """ it was reported that PB responses miss a character in an inconsistent manner.
        We do our best to extract the only info we need.
        """
        lines = '''\
^3PunkBuster Server:  1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5.0 0 (W) "FATTYBMBLATY"
3PunkBuster Server:  1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5.0 0 (W) "FATTYBMBLATY"
^PunkBuster Server:  1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5.0 0 (W) "FATTYBMBLATY"
^3unkBuster Server:  1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5.0 0 (W) "FATTYBMBLATY"
^3PunkBusterServer:  1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5.0 0 (W) "FATTYBMBLATY"
^3PunkBuster erver:  1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5.0 0 (W) "FATTYBMBLATY"
^3PunkBuster Server  1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5.0 0 (W) "FATTYBMBLATY"
^3PunkBuster Server:1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5.0 0 (W) "FATTYBMBLATY"
^3PunkBuster Server: 19732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5.0 0 (W) "FATTYBMBLATY"
^3PunkBuster Server: 1 9732d328485274156125252141252ba1-) 33.133.3.133:-28960 OK   1 5.0 0 (W) "FATTYBMBLATY"
^3PunkBuster Server: 1 9732d328485274156125252141252ba1() 33.133.3.133:-28960 OK   1 5.0 0 (W) "FATTYBMBLATY"
^3PunkBuster Server: 1 9732d328485274156125252141252ba1(- 33.133.3.133:-28960 OK   1 5.0 0 (W) "FATTYBMBLATY"
^3PunkBuster Server: 1 9732d328485274156125252141252ba1(-)33.133.3.133:-28960 OK   1 5.0 0 (W) "FATTYBMBLATY"
^3PunkBuster Server: 1 9732d328485274156125252141252ba1(-) 33.133.3.133-28960 OK   1 5.0 0 (W) "FATTYBMBLATY"
^3PunkBuster Server: 1 9732d328485274156125252141252ba1(-) 33.133.3.133:28960 OK   1 5.0 0 (W) "FATTYBMBLATY"
^3PunkBuster Server: 1 9732d328485274156125252141252ba1(-) 33.133.3.133:-2960 OK   1 5.0 0 (W) "FATTYBMBLATY"
^3PunkBuster Server: 1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960OK   1 5.0 0 (W) "FATTYBMBLATY"
^3PunkBuster Server: 1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 K   1 5.0 0 (W) "FATTYBMBLATY"
^3PunkBuster Server: 1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK1 5.0 0 (W) "FATTYBMBLATY"
^3PunkBuster Server: 1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   5.0 0 (W) "FATTYBMBLATY"
^3PunkBuster Server: 1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   15.0 0 (W) "FATTYBMBLATY"
^3PunkBuster Server: 1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 .0 0 (W) "FATTYBMBLATY"
^3PunkBuster Server: 1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 50 0 (W) "FATTYBMBLATY"
^3PunkBuster Server: 1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5. 0 (W) "FATTYBMBLATY"
^3PunkBuster Server: 1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5.00 (W) "FATTYBMBLATY"
^3PunkBuster Server: 1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5.0  (W) "FATTYBMBLATY"
^3PunkBuster Server: 1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5.0 0(W) "FATTYBMBLATY"
^3PunkBuster Server: 1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5.0 0 W) "FATTYBMBLATY"
^3PunkBuster Server: 1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5.0 0 () "FATTYBMBLATY"
^3PunkBuster Server: 1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5.0 0 (W "FATTYBMBLATY"
^3PunkBuster Server: 1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5.0 0 (W)"FATTYBMBLATY"
^3PunkBuster Server: 1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5.0 0 (W) FATTYBMBLATY"
^3PunkBuster Server: 1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5.0 0 (W) "FATTYBMBLATY
: 1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5.0 0 (W) "FATTYBMBLATY"
'''
        for line in lines.split('\n'):
            if not line: # avoid empty lines
                continue
                # GIVEN
            when(self.console).write('PB_SV_PList').thenReturn(line)
            # WHEN
            rv = self.pb.getPlayerList()
            # THEN
            self.assertIn('0', rv, repr(line))
            self.assertDictContainsSubset(
                {'slot': '1', 'pbid': '9732d328485274156125252141252ba1', 'guid': '9732d328485274156125252141252ba1', 'ip': '33.133.3.133', 'name': 'FATTYBMBLATY'}, rv['0'],
                msg=repr(line)
            )

    def test_getPlayerList_missing_chars_randomly_no_pb_prefix(self):
        """ it was reported that PB responses miss a character in an inconsistent manner.
        We do our best to extract the only info we need.
        """
        lines = '''\
:  1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5.0 0 (W) "FATTYBMBLATY"
:  1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5.0 0 (W) "FATTYBMBLATY"
:  1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5.0 0 (W) "FATTYBMBLATY"
:  1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5.0 0 (W) "FATTYBMBLATY"
:  1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5.0 0 (W) "FATTYBMBLATY"
:  1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5.0 0 (W) "FATTYBMBLATY"
  1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5.0 0 (W) "FATTYBMBLATY"
:1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5.0 0 (W) "FATTYBMBLATY"
: 19732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5.0 0 (W) "FATTYBMBLATY"
: 1 9732d328485274156125252141252ba1-) 33.133.3.133:-28960 OK   1 5.0 0 (W) "FATTYBMBLATY"
: 1 9732d328485274156125252141252ba1() 33.133.3.133:-28960 OK   1 5.0 0 (W) "FATTYBMBLATY"
: 1 9732d328485274156125252141252ba1(- 33.133.3.133:-28960 OK   1 5.0 0 (W) "FATTYBMBLATY"
: 1 9732d328485274156125252141252ba1(-)33.133.3.133:-28960 OK   1 5.0 0 (W) "FATTYBMBLATY"
: 1 9732d328485274156125252141252ba1(-) 33.133.3.133-28960 OK   1 5.0 0 (W) "FATTYBMBLATY"
: 1 9732d328485274156125252141252ba1(-) 33.133.3.133:28960 OK   1 5.0 0 (W) "FATTYBMBLATY"
: 1 9732d328485274156125252141252ba1(-) 33.133.3.133:-2960 OK   1 5.0 0 (W) "FATTYBMBLATY"
: 1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960OK   1 5.0 0 (W) "FATTYBMBLATY"
: 1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 K   1 5.0 0 (W) "FATTYBMBLATY"
: 1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK1 5.0 0 (W) "FATTYBMBLATY"
: 1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   5.0 0 (W) "FATTYBMBLATY"
: 1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   15.0 0 (W) "FATTYBMBLATY"
: 1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 .0 0 (W) "FATTYBMBLATY"
: 1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 50 0 (W) "FATTYBMBLATY"
: 1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5. 0 (W) "FATTYBMBLATY"
: 1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5.00 (W) "FATTYBMBLATY"
: 1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5.0  (W) "FATTYBMBLATY"
: 1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5.0 0(W) "FATTYBMBLATY"
: 1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5.0 0 W) "FATTYBMBLATY"
: 1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5.0 0 () "FATTYBMBLATY"
: 1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5.0 0 (W "FATTYBMBLATY"
: 1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5.0 0 (W)"FATTYBMBLATY"
: 1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5.0 0 (W) FATTYBMBLATY"
: 1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5.0 0 (W) "FATTYBMBLATY
: 1 9732d328485274156125252141252ba1(-) 33.133.3.133:-28960 OK   1 5.0 0 (W) "FATTYBMBLATY"
'''
        for line in lines.split('\n'):
            if not line: # avoid empty lines
                continue
                # GIVEN
            when(self.console).write('PB_SV_PList').thenReturn(line)
            # WHEN
            rv = self.pb.getPlayerList()
            # THEN
            self.assertIn('0', rv, repr(line))
            self.assertDictContainsSubset(
                {'slot': '1', 'pbid': '9732d328485274156125252141252ba1', 'guid': '9732d328485274156125252141252ba1', 'ip': '33.133.3.133', 'name': 'FATTYBMBLATY'}, rv['0'],
                msg=repr(line)
            )



    def test_getPlayerList_cod5(self):
        # GIVEN
        when(self.console).write('PB_SV_PList').thenReturn('''\
whatever: 19 c0356dc89ddb0000000d4f9509db46d1(-) 11.111.111.11:28960 OK 0 2.9 0 (W) "FATTYBMBLATY"
''')
        # WHEN
        rv = self.pb.getPlayerList()
        # THEN
        self.assertDictContainsSubset({'slot': '19', 'pbid': 'c0356dc89ddb0000000d4f9509db46d1', 'guid': 'c0356dc89ddb0000000d4f9509db46d1', 'ip': '11.111.111.11', 'name': 'FATTYBMBLATY'}, rv.get('18', {}))

    def test_getPlayerList_cod5_missing_chars_randomly(self):
        """ it was reported that PB responses miss a character in an inconsistent manner.
        We do our best to extract the only info we need.
        """
        lines = '''\
whatever: 19 c0356dc89ddb0000000d4f9509db46d1(-) 11.111.111.11:28960 OK   0 2.9 0 (W) "FATTYBMBLATY"
whatever 19 c0356dc89ddb0000000d4f9509db46d1(-) 11.111.111.11:28960 OK   0 2.9 0 (W) "FATTYBMBLATY"
whatever: 19 c0356dc89ddb0000000d4f9509db46d1(-) 11.111.111.11:28960 OK   0 2.9 0 (W) "FATTYBMBLATY"
whatever: 19 c0356dc89ddb0000000d4f9509db46d1(-) 11.111.111.11:28960 OK   0 2.9 0 (W) "FATTYBMBLATY"
whatever 19 c0356dc89ddb0000000d4f9509db46d1(-) 11.111.111.11:28960 OK   0 2.9 0 (W) "FATTYBMBLATY"
whatever:19 c0356dc89ddb0000000d4f9509db46d1(-) 11.111.111.11:28960 OK   0 2.9 0 (W) "FATTYBMBLATY"
whatever 19c0356dc89ddb0000000d4f9509db46d1(-) 11.111.111.11:28960 OK   0 2.9 0 (W) "FATTYBMBLATY"
whatever 19 c0356dc89ddb0000000d4f9509db46d1(-) 11.111.111.11:28960 OK   0 2.9 0 (W) "FATTYBMBLATY"
whatever 19 c0356dc89ddb0000000d4f9509db46d1-) 11.111.111.11:28960 OK   0 2.9 0 (W) "FATTYBMBLATY"
whatever 19 c0356dc89ddb0000000d4f9509db46d1() 11.111.111.11:28960 OK   0 2.9 0 (W) "FATTYBMBLATY"
whatever 19 c0356dc89ddb0000000d4f9509db46d1(- 11.111.111.11:28960 OK   0 2.9 0 (W) "FATTYBMBLATY"
whatever 19 c0356dc89ddb0000000d4f9509db46d1(-)11.111.111.11:28960 OK   0 2.9 0 (W) "FATTYBMBLATY"
whatever 19 c0356dc89ddb0000000d4f9509db46d1(-) 11.111.111.11:28960OK   0 2.9 0 (W) "FATTYBMBLATY"
whatever 19 c0356dc89ddb0000000d4f9509db46d1(-) 11.111.111.11:28960 K   0 2.9 0 (W) "FATTYBMBLATY"
whatever 19 c0356dc89ddb0000000d4f9509db46d1(-) 11.111.111.11:28960 O   0 2.9 0 (W) "FATTYBMBLATY"
whatever 19 c0356dc89ddb0000000d4f9509db46d1(-) 11.111.111.11:28960 OK    2.9 0 (W) "FATTYBMBLATY"
whatever 19 c0356dc89ddb0000000d4f9509db46d1(-) 11.111.111.11:28960 OK   02.9 0 (W) "FATTYBMBLATY"
whatever 19 c0356dc89ddb0000000d4f9509db46d1(-) 11.111.111.11:28960 OK   0 29 0 (W) "FATTYBMBLATY"
whatever 19 c0356dc89ddb0000000d4f9509db46d1(-) 11.111.111.11:28960 OK   0 2.90 (W) "FATTYBMBLATY"
whatever 19 c0356dc89ddb0000000d4f9509db46d1(-) 11.111.111.11:28960 OK   0 2.9  (W) "FATTYBMBLATY"
whatever 19 c0356dc89ddb0000000d4f9509db46d1(-) 11.111.111.11:28960 OK   0 2.9 0 W) "FATTYBMBLATY"
whatever 19 c0356dc89ddb0000000d4f9509db46d1(-) 11.111.111.11:28960 OK   0 2.9 0 () "FATTYBMBLATY"
whatever 19 c0356dc89ddb0000000d4f9509db46d1(-) 11.111.111.11:28960 OK   0 2.9 0 (W "FATTYBMBLATY"
whatever 19 c0356dc89ddb0000000d4f9509db46d1(-) 11.111.111.11:28960 OK   0 2.9 0 (W)"FATTYBMBLATY"
whatever 19 c0356dc89ddb0000000d4f9509db46d1(-) 11.111.111.11:28960 OK   0 2.9 0 (W) FATTYBMBLATY"
whatever 19 c0356dc89ddb0000000d4f9509db46d1(-) 11.111.111.11:28960 OK   0 2.9 0 (W) "FATTYBMBLATY
'''
        for line in lines.split('\n'):
            if not line: # avoid empty lines
                continue
                # GIVEN
            when(self.console).write('PB_SV_PList').thenReturn(line)
            # WHEN
            rv = self.pb.getPlayerList()
            # THEN
            self.assertIn('18', rv, msg="for test line %r" % line)
            self.assertDictContainsSubset(
                {'slot': '19', 'pbid': 'c0356dc89ddb0000000d4f9509db46d1', 'guid': 'c0356dc89ddb0000000d4f9509db46d1', 'ip': '11.111.111.11', 'name': 'FATTYBMBLATY'}, rv['18'],
                msg="for test line %r" % line
            )
