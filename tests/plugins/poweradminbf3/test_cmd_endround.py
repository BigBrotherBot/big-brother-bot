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

import time
# http://www.voidspace.org.uk/python/mock/mock.html
from mock import patch
from mockito import when, verify
from b3.config import CfgConfigParser
from b3.plugins.poweradminbf3 import Poweradminbf3Plugin
from tests.plugins.poweradminbf3 import Bf3TestCase, logging_disabled


class Test_cmd_endround(Bf3TestCase):

    @classmethod
    def setUpClass(cls):
        Bf3TestCase.setUpClass()
        cls.sleep_patcher = patch.object(time, "sleep")
        cls.sleep_patcher.start()

    @classmethod
    def tearDownClass(cls):
        cls.sleep_patcher.stop()

    def setUp(self):
        Bf3TestCase.setUp(self)
        self.conf = CfgConfigParser()
        self.conf.loadFromString("""[commands]
endround: 20
        """)
        with logging_disabled():
            self.p = Poweradminbf3Plugin(self.console, self.conf)
            self.p.onLoadConfig()
            self.p.onStartup()
            self.superadmin.connects('superadmin')


    def test_frostbite_error(self):
        when(self.console).write(('serverInfo',)).thenReturn(['i3D.net - BigBrotherBot #3 (DE)', '0', '16', 'ConquestLarge0', 'MP_007', '0', '2',
                                                               '2', '300', '300', '0', '', 'false', 'true', 'false', '105473', '105450', '', '', '', 'EU', 'AMS', 'DE'])
        self.superadmin.message_history = []
        self.superadmin.says("!endround")
        self.assertEqual([], self.superadmin.message_history)
        verify(self.console).write(('mapList.endRound', '1'))


    def test_no_argument_team1_winning(self):
        when(self.console).write(('serverInfo',)).thenReturn(['i3D.net - BigBrotherBot #3 (DE)', '0', '16', 'ConquestLarge0', 'MP_007', '0', '2',
                                                               '2', '800', '90', '0', '', 'true', 'true', 'false', '105473', '105450', '', '', '', 'EU', 'AMS', 'DE'])
        self.superadmin.message_history = []
        self.superadmin.says("!endround")
        self.assertEqual([], self.superadmin.message_history)
        verify(self.console).write(('mapList.endRound', '1'))

    def test_no_argument_team2_winning(self):
        when(self.console).write(('serverInfo',)).thenReturn(['i3D.net - BigBrotherBot #3 (DE)', '0', '16', 'ConquestLarge0', 'MP_007', '0', '2',
                                                               '2', '400', '1300', '0', '', 'true', 'true', 'false', '105473', '105450', '', '', '', 'EU', 'AMS', 'DE'])

        self.superadmin.message_history = []
        self.superadmin.says("!endround")
        verify(self.console).write(('mapList.endRound', '2'))
        self.assertEqual([], self.superadmin.message_history)


    def test_no_argument_team4_winning(self):
        when(self.console).write(('serverInfo',)).thenReturn(['i3D.net - BigBrotherBot #3 (DE)', '0', '16', 'ConquestLarge0', 'MP_007', '0', '2',
                                                               '4', '400', '1300', '45', '1651' '0', '', 'true', 'true', 'false', '105473', '105450', '', '', '', 'EU', 'AMS', 'DE'])

        self.superadmin.message_history = []
        self.superadmin.says("!endround")
        verify(self.console).write(('mapList.endRound', '4'))
        self.assertEqual([], self.superadmin.message_history)


    def test_0(self):
        when(self.console).write().thenReturn()
        self.superadmin.message_history = []
        self.superadmin.says("!endround 0")
        verify(self.console).write(('mapList.endRound', '0'))
        self.assertEqual([], self.superadmin.message_history)


    def test_1(self):
        when(self.console).write().thenReturn()
        self.superadmin.message_history = []
        self.superadmin.says("!endround 1")
        verify(self.console).write(('mapList.endRound', '1'))
        self.assertEqual([], self.superadmin.message_history)
