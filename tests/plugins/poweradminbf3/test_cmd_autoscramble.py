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


from mock import Mock
from b3.config import CfgConfigParser
from b3.plugins.poweradminbf3 import Poweradminbf3Plugin
from tests.plugins.poweradminbf3 import Bf3TestCase


class Test_cmd_autoscramble(Bf3TestCase):

    def setUp(self):
        Bf3TestCase.setUp(self)
        self.conf = CfgConfigParser()
        self.conf.loadFromString("""
[commands]
autoscramble: mod
""")
        self.p = Poweradminbf3Plugin(self.console, self.conf)
        self.p.onLoadConfig()
        self.p.onStartup()
        self.p._scrambler = Mock()
        self.superadmin.connects('superadmin')
        self.superadmin.clearMessageHistory()
        self.p._autoscramble_rounds = None
        self.p._autoscramble_maps = None

    def test_no_arguments(self):
        self.superadmin.says('!autoscramble')
        self.assertEqual(["invalid data. Expecting one of [off, round, map]"], self.superadmin.message_history)
        self.assertIsNone(self.p._autoscramble_rounds)
        self.assertIsNone(self.p._autoscramble_maps)

    def test_bad_arguments(self):
        self.superadmin.says('!autoscramble f00')
        self.assertEqual(["invalid data. Expecting one of [off, round, map]"], self.superadmin.message_history)
        self.assertIsNone(self.p._autoscramble_rounds)
        self.assertIsNone(self.p._autoscramble_maps)

    def test_round(self):
        self.superadmin.says('!autoscramble round')
        self.assertEqual(['Auto scrambler will run at every round start'], self.superadmin.message_history)
        self.assertTrue(self.p._autoscramble_rounds)
        self.assertFalse(self.p._autoscramble_maps)

    def test_r(self):
        self.superadmin.says('!autoscramble r')
        self.assertEqual(['Auto scrambler will run at every round start'], self.superadmin.message_history)
        self.assertTrue(self.p._autoscramble_rounds)
        self.assertFalse(self.p._autoscramble_maps)

    def test_map(self):
        self.superadmin.says('!autoscramble map')
        self.assertEqual(['Auto scrambler will run at every map change'], self.superadmin.message_history)
        self.assertFalse(self.p._autoscramble_rounds)
        self.assertTrue(self.p._autoscramble_maps)

    def test_m(self):
        self.superadmin.says('!autoscramble m')
        self.assertEqual(['Auto scrambler will run at every map change'], self.superadmin.message_history)
        self.assertFalse(self.p._autoscramble_rounds)
        self.assertTrue(self.p._autoscramble_maps)

    def test_off(self):
        self.superadmin.says('!autoscramble off')
        self.assertEqual(['Auto scrambler now disabled'], self.superadmin.message_history)
        self.assertFalse(self.p._autoscramble_rounds)
        self.assertFalse(self.p._autoscramble_maps)
