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

class Cmd_viplist_TestCase(Bf3TestCase):
    def setUp(self):
        Bf3TestCase.setUp(self)
        self.conf = CfgConfigParser()
        self.conf.loadFromString("""[commands]
viplist: 20
        """)
        self.p = Poweradminbf3Plugin(self.console, self.conf)
        self.p.onLoadConfig()
        self.p.onStartup()

        self.console.say = Mock()
        self.console.saybig = Mock()

        self.moderator.connects("moderator")

        self.joe.connects('joe')
        self.joe.teamId = 2


class Test_cmd_viplist(Cmd_viplist_TestCase):
    def test_empty_vip_list(self):
        when(self.console).write(('reservedSlotsList.list', 0)).thenReturn([])
        self.moderator.connects("moderator")
        self.moderator.message_history = []
        self.moderator.says("!viplist")
        self.assertEqual(1, len(self.moderator.message_history))
        self.assertEqual('VIP list is empty', self.moderator.message_history[0])


    def test_4_vips(self):
        when(self.console).write(('reservedSlotsList.list', 0)).thenReturn(['name1', 'name2', 'name3', 'name2'])
        when(self.console).write(('reservedSlotsList.list', 4)).thenReturn(['name4'])
        when(self.console).write(('reservedSlotsList.list', 5)).thenReturn([])
        self.moderator.connects("moderator")
        self.moderator.message_history = []
        self.moderator.says("!viplist")
        self.assertEqual(1, len(self.moderator.message_history))
        self.assertEqual('VIPs: name1, name2, name3, name4', self.moderator.message_history[0])


    def test_4_vips_one_is_connected(self):
        when(self.console).write(('reservedSlotsList.list', 0)).thenReturn(['name1', 'name2', 'name3', 'Joe'])
        when(self.console).write(('reservedSlotsList.list', 4)).thenReturn([])
        self.joe.connects("Joe")
        self.moderator.connects("moderator")
        self.moderator.message_history = []
        self.moderator.says("!viplist")
        self.assertEqual(2, len(self.moderator.message_history))
        self.assertEqual('Connected VIPs: Joe', self.moderator.message_history[0])
        self.assertEqual('other VIPs: name1, name2, name3', self.moderator.message_history[1])


    def test_500_vips(self):
        list = ['Joe']
        list.extend(['name%s' % x for x in range(1,500)])
        when(self.console).write(('reservedSlotsList.list', 0)).thenReturn(list)
        when(self.console).write(('reservedSlotsList.list', 500)).thenReturn([])
        self.moderator.connects("moderator")
        self.moderator.message_history = []
        self.moderator.says("!viplist")
        self.assertEqual(1, len(self.moderator.message_history))
        self.assertEqual('VIPs: Joe, name1, name2, name3, name4, name5, name6, name7, name8, name9, name10, name11, name12, name13, name14 and 485 more...', self.moderator.message_history[0])


    def test_500_vips_3_are_connected(self):
        list = ['joe', 'moderator', 'simon']
        list.extend(['name%s' % x for x in range(1,20)])
        when(self.console).write(('reservedSlotsList.list', 0)).thenReturn(list)
        when(self.console).write(('reservedSlotsList.list', 22)).thenReturn([])
        self.joe.connects("joe")
        self.simon.connects("simon")
        self.reg.connects("reg")
        self.moderator.connects("moderator")
        self.moderator.message_history = []
        self.moderator.says("!viplist")
        self.assertEqual(2, len(self.moderator.message_history))
        self.assertEqual('Connected VIPs: joe, moderator, simon', self.moderator.message_history[0])
        self.assertEqual('other VIPs: name1, name2, name3, name4, name5, name6, name7, name8, name9, name10, name11, name12, name13, name14, name15 and 4 more...', self.moderator.message_history[1])


class Test_cmd_viplist_filtered(Cmd_viplist_TestCase):
    def test_empty_vip_list(self):
        when(self.console).write(('reservedSlotsList.list', 0)).thenReturn([])
        self.moderator.connects("moderator")
        self.moderator.message_history = []
        self.moderator.says("!viplist")
        self.assertEqual(1, len(self.moderator.message_history))
        self.assertEqual('VIP list is empty', self.moderator.message_history[0])


    def test_4_vips_matching_filter(self):
        when(self.console).write(('reservedSlotsList.list', 0)).thenReturn(['name1', 'name2', 'name3', 'name2'])
        when(self.console).write(('reservedSlotsList.list', 4)).thenReturn(['name4'])
        when(self.console).write(('reservedSlotsList.list', 5)).thenReturn([])
        self.moderator.connects("moderator")
        self.moderator.message_history = []
        self.moderator.says("!viplist name")
        self.assertEqual(1, len(self.moderator.message_history))
        self.assertEqual('VIPs: name1, name2, name3, name4', self.moderator.message_history[0])


    def test_4_vips_only_one_matching_filter(self):
        when(self.console).write(('reservedSlotsList.list', 0)).thenReturn(['name1', 'foo', 'name3', 'name2'])
        when(self.console).write(('reservedSlotsList.list', 4)).thenReturn(['name4'])
        when(self.console).write(('reservedSlotsList.list', 5)).thenReturn([])
        self.moderator.connects("moderator")
        self.moderator.message_history = []
        self.moderator.says("!viplist fo")
        self.assertEqual(1, len(self.moderator.message_history))
        self.assertEqual('VIPs: foo', self.moderator.message_history[0])


    def test_4_vips_one_is_connected_not_matching(self):
        when(self.console).write(('reservedSlotsList.list', 0)).thenReturn(['name1', 'name2', 'name3', 'Joe'])
        when(self.console).write(('reservedSlotsList.list', 4)).thenReturn([])
        self.joe.connects("Joe")
        self.moderator.connects("moderator")
        self.moderator.message_history = []
        self.moderator.says("!viplist foo")
        self.assertEqual(1, len(self.moderator.message_history))
        self.assertEqual("no VIP matching 'foo' found over the 4 existing VIPs", self.moderator.message_history[0])


    def test_4_vips_one_is_connected_matching(self):
        when(self.console).write(('reservedSlotsList.list', 0)).thenReturn(['name1', 'name2', 'name3', 'Joe'])
        when(self.console).write(('reservedSlotsList.list', 4)).thenReturn([])
        self.joe.connects("Joe")
        self.moderator.connects("moderator")
        self.moderator.message_history = []
        self.moderator.says("!viplist JOE")
        self.assertEqual(1, len(self.moderator.message_history))
        self.assertEqual('Connected VIPs: Joe', self.moderator.message_history[0])


    def test_lots_of_vips_non_matching(self):
        list = ['Joe']
        list.extend(['name%s' % x for x in range(1,50)])
        when(self.console).write(('reservedSlotsList.list', 0)).thenReturn(list)
        when(self.console).write(('reservedSlotsList.list', 50)).thenReturn([])
        self.moderator.connects("moderator")
        self.moderator.message_history = []
        self.moderator.says("!viplist foo")
        self.assertEqual(1, len(self.moderator.message_history))
        self.assertEqual("no VIP matching 'foo' found over the 50 existing VIPs", self.moderator.message_history[0])

    def test_lots_of_vips_matching(self):
        list = ['Joe']
        list.extend(['name%s' % x for x in range(1,25)])
        list.extend(['foo%s' % x for x in range(25,50)])
        when(self.console).write(('reservedSlotsList.list', 0)).thenReturn(list)
        when(self.console).write(('reservedSlotsList.list', 50)).thenReturn([])
        self.moderator.connects("moderator")
        self.moderator.message_history = []
        self.moderator.says("!viplist foo")
        self.assertEqual(1, len(self.moderator.message_history))
        self.assertEqual('VIPs: foo25, foo26, foo27, foo28, foo29, foo30, foo31, foo32, foo33, foo34, foo35, foo36, foo37, foo38, foo39 and 10 more...', self.moderator.message_history[0])


    def test_lots_of_matching_vips_3_are_connected(self):
        list = ['joe', 'moderator', 'simon']
        list.extend(['name%s' % x for x in range(3,12)])
        list.extend(['foo%s' % x for x in range(12,25)])
        when(self.console).write(('reservedSlotsList.list', 0)).thenReturn(list)
        when(self.console).write(('reservedSlotsList.list', 25)).thenReturn([])
        self.joe.connects("joe")
        self.simon.connects("simon")
        self.reg.connects("reg")
        self.moderator.connects("moderator")
        self.moderator.message_history = []
        self.moderator.says("!viplist o")
        self.assertEqual(2, len(self.moderator.message_history))
        self.assertEqual('Connected VIPs: joe, moderator, simon', self.moderator.message_history[0])
        self.assertEqual('other VIPs: foo12, foo13, foo14, foo15, foo16, foo17, foo18, foo19, foo20, foo21, foo22, foo23, foo24', self.moderator.message_history[1])



    def test_only_connected_are_matching(self):
        list = ['joe', 'moderator', 'simon']
        list.extend(['name%s' % x for x in range(3,15)])
        when(self.console).write(('reservedSlotsList.list', 0)).thenReturn(list)
        when(self.console).write(('reservedSlotsList.list', 15)).thenReturn([])
        self.joe.connects("joe")
        self.simon.connects("simon")
        self.reg.connects("reg")
        self.moderator.connects("moderator")
        self.moderator.message_history = []
        self.moderator.says("!viplist o")
        self.assertEqual(1, len(self.moderator.message_history))
        self.assertEqual('Connected VIPs: joe, moderator, simon', self.moderator.message_history[0])

