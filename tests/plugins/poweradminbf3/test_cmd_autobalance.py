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
from mock import Mock, patch # http://www.voidspace.org.uk/python/mock/mock.html
from b3.config import CfgConfigParser
from b3.plugins.poweradminbf3 import Poweradminbf3Plugin
from tests.plugins.poweradminbf3 import Bf3TestCase



class Test_cmd_autobalance(Bf3TestCase):

    def setUp(self):
        super(Test_cmd_autobalance, self).setUp()
        self.conf = CfgConfigParser()
        self.conf.loadFromString("""
[commands]
autobalance: mod
""")
        self.p = Poweradminbf3Plugin(self.console, self.conf)
        self.p.onLoadConfig()
        self.p.onStartup()
        self.p.console._cron = Mock()


    def test_no_argument_while_off(self):
        self.p._autobalance = False
        self.moderator.connects("moderator")
        self.moderator.message_history = []
        self.moderator.says("!autobalance")
        self.assertEqual(1, len(self.moderator.message_history))
        self.assertEqual("Autobalance is currently off, use !autobalance on to turn on", self.moderator.message_history[0])


    def test_no_argument_while_on(self):
        self.p._autobalance = True
        self.moderator.connects("moderator")
        self.moderator.message_history = []
        self.moderator.says("!autobalance")
        self.assertEqual(1, len(self.moderator.message_history))
        self.assertEqual("Autobalance is currently on, use !autobalance off to turn off", self.moderator.message_history[0])


    def test_with_argument_foo(self):
        self.moderator.connects("moderator")
        self.moderator.message_history = []
        self.moderator.says("!autobalance foo")
        self.assertIn("invalid data. Expecting on, off or now", self.moderator.message_history)


    def test_with_argument_now(self):
        self.p.run_autobalance = Mock()
        self.moderator.connects("moderator")
        self.moderator.message_history = []
        self.moderator.says("!autobalance now")
        self.assertTrue(self.p.run_autobalance.called)


    def test_with_argument_on_while_currently_off_and_autoassign_off(self):
        self.p._autobalance = False
        self.p._autoassign = False
        self.p._one_round_over = False
        self.moderator.connects("moderator")
        self.moderator.message_history = []
        self.moderator.says("!autobalance on")
        self.assertIn("Autobalance will be enabled on next round start", self.moderator.message_history)
        self.assertIn("Autoassign now enabled", self.moderator.message_history)
        self.assertTrue(self.p._autobalance)
        self.assertTrue(self.p._autoassign)


    @patch("b3.cron.Cron")
    def test_with_argument_on_while_currently_off_and_one_round_is_over(self, MockCron):
        self.p._autobalance = False
        self.p._one_round_over = True
        self.p._cronTab_autobalance = None
        self.p.console._cron.__add__ = Mock()
        self.moderator.connects("moderator")
        self.moderator.message_history = []
        self.moderator.says("!autobalance on")
        self.assertIn("Autobalance now enabled", self.moderator.message_history)
        self.assertTrue(self.p._autobalance)
        self.assertIsNotNone(self.p._cronTab_autobalance)
        self.console.cron.__add__.assert_called_once_with(self.p._cronTab_autobalance)


    @patch("b3.cron.Cron")
    def test_with_argument_on_while_currently_off_and_no_round_is_over(self, MockCron):
        self.p._autobalance = False
        self.p._one_round_over = False
        self.p._cronTab_autobalance = None
        self.p.console._cron.__add__ = Mock()
        self.moderator.connects("moderator")
        self.moderator.message_history = []
        self.moderator.says("!autobalance on")
        self.assertIn("Autobalance will be enabled on next round start", self.moderator.message_history)
        self.assertTrue(self.p._autobalance)
        self.assertIsNone(self.p._cronTab_autobalance)
        self.assertFalse(self.p.console.cron.__add__.called)


    def test_with_argument_on_while_already_on(self):
        self.p._autobalance = True
        self.moderator.connects("moderator")
        self.moderator.message_history = []
        self.moderator.says("!autobalance on")
        self.assertEqual(["Autobalance is already enabled"], self.moderator.message_history)
        self.assertTrue(self.p._autobalance)


    @patch("b3.cron.Cron")
    def test_with_argument_off_while_currently_on(self, MockCron):
        self.p._autobalance = True
        self.p.console._cron.__sub__ = Mock()
        self.p._cronTab_autobalance = Mock()
        self.moderator.connects("moderator")
        self.moderator.message_history = []
        self.moderator.says("!autobalance off")
        self.assertEqual(["Autobalance now disabled"], self.moderator.message_history)
        self.assertFalse(self.p._autobalance)
        self.p.console.cron.__sub__.assert_called_once_with(self.p._cronTab_autobalance)


    def test_with_argument_off_while_already_off(self):
        self.p._autobalance = False
        self.moderator.connects("moderator")
        self.moderator.message_history = []
        self.moderator.says("!autobalance off")
        self.assertEqual(["Autobalance now disabled"], self.moderator.message_history)
        self.assertFalse(self.p._autobalance)
