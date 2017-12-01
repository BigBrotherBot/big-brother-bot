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

from mock import call, Mock
from mockito import when
from b3.config import CfgConfigParser
from b3.plugins.poweradminbf3 import Poweradminbf3Plugin
from tests.plugins.poweradminbf3 import Bf3TestCase


class Test_cmd_vips(Bf3TestCase):
    def setUp(self):
        Bf3TestCase.setUp(self)
        self.conf = CfgConfigParser()
        self.conf.loadFromString("""
[commands]
vips: mod
""")
        self.p = Poweradminbf3Plugin(self.console, self.conf)
        self.p.onLoadConfig()
        self.p.onStartup()

        self.console.say = Mock()
        self.console.saybig = Mock()

        self.moderator.connects("moderator")

        self.joe.connects('joe')
        self.joe.teamId = 2


    def test_empty_vip_list(self):
        when(self.console).write(('reservedSlotsList.list', 0)).thenReturn([])
        self.moderator.connects("moderator")
        self.moderator.message_history = []
        self.moderator.says("!vips")
        self.assertEqual(1, len(self.moderator.message_history))
        self.assertEqual('No VIP connected', self.moderator.message_history[0])


    def test_4_vips(self):
        when(self.console).write(('reservedSlotsList.list', 0)).thenReturn(['name1', 'name2', 'name3', 'name2'])
        when(self.console).write(('reservedSlotsList.list', 4)).thenReturn(['name4'])
        when(self.console).write(('reservedSlotsList.list', 5)).thenReturn([])
        self.moderator.connects("moderator")
        self.moderator.message_history = []
        self.moderator.says("!vips")
        self.assertEqual(1, len(self.moderator.message_history))
        self.assertEqual('No VIP connected', self.moderator.message_history[0])


    def test_4_vips_one_is_connected(self):
        when(self.console).write(('reservedSlotsList.list', 0)).thenReturn(['name1', 'name2', 'name3', 'Joe'])
        when(self.console).write(('reservedSlotsList.list', 4)).thenReturn([])
        self.joe.connects("Joe")
        self.moderator.connects("moderator")
        self.moderator.message_history = []
        self.moderator.says("!vips")
        self.assertEqual(1, len(self.moderator.message_history))
        self.assertEqual('Connected VIPs: Joe', self.moderator.message_history[0])

