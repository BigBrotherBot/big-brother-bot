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
from tests.plugins.poweradminbf3 import Bf3TestCase
from b3.config import CfgConfigParser
from b3.plugins.poweradminbf3 import Poweradminbf3Plugin

class Test_cmd_autoassign(Bf3TestCase):

    def setUp(self):
        super(Test_cmd_autoassign, self).setUp()
        self.conf = CfgConfigParser()
        self.conf.loadFromString("""
[commands]
autoassign: mod
""")
        self.p = Poweradminbf3Plugin(self.console, self.conf)
        self.p.onLoadConfig()
        self.p.onStartup()


    def test_no_argument_while_off(self):
        self.p._autoassign = False
        self.moderator.connects("moderator")
        self.moderator.message_history = []
        self.moderator.says("!autoassign")
        self.assertEqual(1, len(self.moderator.message_history))
        self.assertEqual("Autoassign is currently off, use !autoassign on to turn on", self.moderator.message_history[0])


    def test_no_argument_while_on(self):
        self.p._autoassign = True
        self.moderator.connects("moderator")
        self.moderator.message_history = []
        self.moderator.says("!autoassign")
        self.assertEqual(1, len(self.moderator.message_history))
        self.assertEqual("Autoassign is currently on, use !autoassign off to turn off", self.moderator.message_history[0])


    def test_with_argument_foo(self):
        self.moderator.connects("moderator")
        self.moderator.message_history = []
        self.moderator.says("!autoassign foo")
        self.assertIn("invalid data. Expecting on or off", self.moderator.message_history)


    def test_with_argument_on(self):
        self.p._autoassign = False
        self.moderator.connects("moderator")
        self.moderator.message_history = []
        self.moderator.says("!autoassign on")
        self.assertIn("Autoassign now enabled", self.moderator.message_history)
        self.assertTrue(self.p._autoassign)


    def test_with_argument_off_with_autobalance_on(self):
        self.p._autoassign = True
        self.p._autobalance = True
        self.moderator.connects("moderator")
        self.moderator.message_history = []
        self.moderator.says("!autoassign off")
        self.assertIn("Autoassign now disabled", self.moderator.message_history)
        self.assertFalse(self.p._autoassign)
        self.assertIn("Autobalance now disabled", self.moderator.message_history)
        self.assertFalse(self.p._autobalance)


    def test_with_argument_off_with_autobalance_off(self):
        self.p._autoassign = True
        self.p._autobalance = False
        self.moderator.connects("moderator")
        self.moderator.message_history = []
        self.moderator.says("!autoassign off")
        self.assertIn("Autoassign now disabled", self.moderator.message_history)
        self.assertFalse(self.p._autoassign)
        self.assertNotIn("Autobalance now disabled", self.moderator.message_history)
        self.assertFalse(self.p._autobalance)
