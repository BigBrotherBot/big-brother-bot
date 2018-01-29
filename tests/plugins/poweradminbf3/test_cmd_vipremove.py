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

from mockito import when, verify
from b3.config import CfgConfigParser
from b3.parsers.frostbite2.protocol import CommandFailedError
from b3.plugins.poweradminbf3 import Poweradminbf3Plugin
from tests.plugins.poweradminbf3 import Bf3TestCase


class Test_cmd_vipremove(Bf3TestCase):
    def setUp(self):
        super(Test_cmd_vipremove, self).setUp()
        self.conf = CfgConfigParser()
        self.conf.loadFromString("""[commands]
vipremove: 0
        """)
        self.p = Poweradminbf3Plugin(self.console, self.conf)
        self.p.onLoadConfig()
        self.p.onStartup()

    def test_missing_parameter(self):
        self.superadmin.connects('superadmin')
        self.superadmin.clearMessageHistory()
        self.superadmin.says('!vipremove')
        self.assertEqual(['Usage: !vipremove <player>'], self.superadmin.message_history)


    def test_non_existing_player(self):
        when(self.console).write(('reservedSlotsList.list', 0)).thenReturn([])
        self.superadmin.connects('superadmin')
        self.superadmin.clearMessageHistory()
        self.superadmin.says('!vipremove joe')
        self.assertEqual(["No VIP named 'joe' found"], self.superadmin.message_history)


    def test_frostbite_error(self):
        self.joe.connects("joe")
        self.superadmin.connects('superadmin')
        when(self.console).write(('reservedSlotsList.remove', u'Joe')).thenRaise(CommandFailedError(['f00']))
        self.superadmin.clearMessageHistory()
        self.superadmin.says("!vipremove joe")
        self.assertEqual(["Error: f00"], self.superadmin.message_history)


    def test_frostbite_error_PlayerNotInList(self):
        self.joe.connects("joe")
        self.superadmin.connects('superadmin')
        when(self.console).write(('reservedSlotsList.remove', u'Joe')).thenRaise(CommandFailedError(['PlayerNotInList']))
        self.superadmin.clearMessageHistory()
        self.superadmin.says("!vipremove joe")
        self.assertEqual(["There is no VIP named 'Joe'"], self.superadmin.message_history)


    def test_nominal_on_connected_player(self):
        when(self.console).write()
        self.joe.connects('Joe')
        self.superadmin.connects('superadmin')
        self.superadmin.clearMessageHistory()
        self.superadmin.says('!vipremove jo')
        self.assertEqual(['VIP privileges removed for Joe'], self.superadmin.message_history)
        verify(self.console).write(('reservedSlotsList.remove', 'Joe'))


    def test_nominal_on_not_connected_player(self):
        when(self.console).write(('reservedSlotsList.list', 0)).thenReturn(['Joe'])
        when(self.console).write(('reservedSlotsList.list', 1)).thenReturn([])
        self.superadmin.connects('superadmin')
        self.superadmin.clearMessageHistory()
        self.superadmin.says('!vipremove joe')
        self.assertEqual(['VIP privileges removed for joe'], self.superadmin.message_history)
        verify(self.console).write(('reservedSlotsList.remove', 'joe'))


    def test_no_right(self):
        when(self.console).write(('reservedSlotsList.list', 0)).thenReturn(['Joe'])
        self.joe.connects('Joe')
        self.joe.save()
        self.superadmin.connects('God')
        self.joe.clearMessageHistory()
        self.joe.says('!vipremove God')
        self.assertEqual(['Operation denied because God is in the Super Admin group'], self.joe.message_history)

