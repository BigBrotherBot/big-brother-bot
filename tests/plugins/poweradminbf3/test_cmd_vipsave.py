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

from mockito import when
from b3.config import CfgConfigParser
from b3.parsers.frostbite2.protocol import CommandFailedError
from b3.plugins.poweradminbf3 import Poweradminbf3Plugin
from tests.plugins.poweradminbf3 import Bf3TestCase


class Test_cmd_vipsave(Bf3TestCase):
    def setUp(self):
        Bf3TestCase.setUp(self)
        self.conf = CfgConfigParser()
        self.conf.loadFromString("""[commands]
vipsave: 20
        """)
        self.p = Poweradminbf3Plugin(self.console, self.conf)
        self.p.onLoadConfig()
        self.p.onStartup()

        self.moderator.connects("moderator")


    def test_nominal(self):
        when(self.console).write(('reservedSlotsList.list', 0)).thenReturn([])
        when(self.console).write(('reservedSlotsList.save',)).thenReturn([])
        self.moderator.connects("moderator")
        self.moderator.message_history = []
        self.moderator.says("!vipsave")
        self.assertEqual(1, len(self.moderator.message_history))
        self.assertEqual('VIP list saved to disk (0 name written)', self.moderator.message_history[0])

    def test_nominal_2(self):
        when(self.console).write(('reservedSlotsList.list', 0)).thenReturn(['foo', 'bar'])
        when(self.console).write(('reservedSlotsList.list', 2)).thenReturn([])
        when(self.console).write(('reservedSlotsList.save',)).thenReturn([])
        self.moderator.connects("moderator")
        self.moderator.message_history = []
        self.moderator.says("!vipsave")
        self.assertEqual(1, len(self.moderator.message_history))
        self.assertEqual('VIP list saved to disk (2 names written)', self.moderator.message_history[0])

    def test_frostbite_error(self):
        when(self.console).write(('reservedSlotsList.list', 0)).thenReturn([])
        when(self.console).write(('reservedSlotsList.save',)).thenRaise(CommandFailedError(['f00']))
        self.moderator.connects("moderator")
        self.moderator.message_history = []
        self.moderator.says("!vipsave")
        self.assertEqual(["Error: f00"], self.moderator.message_history)