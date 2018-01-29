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

from mock import  call, Mock
from b3.config import CfgConfigParser
from b3.plugins.poweradminurt import PoweradminurtPlugin
from tests.plugins.poweradminurt.iourt42 import Iourt42TestCase
from b3 import TEAM_BLUE, TEAM_RED
from tests import logging_disabled
from textwrap import dedent

class Test_cmd_balance(Iourt42TestCase):

    def setUp(self):
        super(Test_cmd_balance, self).setUp()
        self.conf = CfgConfigParser()
        self.conf.loadFromString(dedent("""
        [commands]
        pabalance-balance: 1

        [skillbalancer]
        min_bal_interval: 1
        interval: 0
        difference: 0.5
        mode: 2
        """))
        self.p = PoweradminurtPlugin(self.console, self.conf)
        self.init_default_cvar()
        self.p.onLoadConfig()
        self.p.onStartup()

        self.console.say = Mock()
        self.console.write = Mock()

        with logging_disabled():
            from b3.fake import FakeClient
            self.blue1 = FakeClient(self.console, name="Blue1", guid="zaerezarezar", groupBits=1, team=TEAM_BLUE)
            self.blue2 = FakeClient(self.console, name="Blue2", guid="qsdfdsqfdsqf", groupBits=1, team=TEAM_BLUE)
            self.blue3 = FakeClient(self.console, name="Blue3", guid="qsdfdsqfdsqf33", groupBits=1, team=TEAM_BLUE)
            self.blue4 = FakeClient(self.console, name="Blue4", guid="sdf455ezr", groupBits=1, team=TEAM_BLUE)
            self.red1 = FakeClient(self.console, name="Red1", guid="875sasda", groupBits=1, team=TEAM_RED)
            self.red2 = FakeClient(self.console, name="Red2", guid="f4qfer654r", groupBits=1, team=TEAM_RED)

        # connect clients
        self.blue1.connects('1')
        self.blue2.connects('2')
        self.blue3.connects('3')
        self.blue4.connects('4')
        self.red1.connects('5')
        self.red2.connects('6')

        self.p.countteams = Mock(return_value=True)
        self.p._teamred = 2
        self.p._teamblue = 4

    def test_balancing_already_done(self):
        # GIVEN
        self.blue1.clearMessageHistory()
        self.p._lastbal = 0
        self.p.ignoreCheck = Mock(return_value=True)
        self.console.time = Mock(return_value=10)
        # WHEN
        self.blue1.says('!balance')
        # THEN
        self.assertEqual(self.blue1.message_history, ['Teams changed recently, please wait a while'])

    def test_non_round_based_gametype(self):
        # GIVEN
        self.blue1.clearMessageHistory()
        self.p._lastbal = 0
        self.p.ignoreCheck = Mock(return_value=False)
        self.console.time = Mock(return_value=120)
        self.console.game.gameType = 'tdm'
        # WHEN
        self.blue1.says('!balance')
        # THEN
        self.console.write.assert_has_calls([call('bigtext "Balancing teams!"')])

    def test_round_based_gametype_delayed_announce_only(self):
        # GIVEN
        self.blue1.clearMessageHistory()
        self.p._lastbal = 0
        self.p.ignoreCheck = Mock(return_value=False)
        self.console.time = Mock(return_value=120)
        self.console.game.gameType = 'bm'
        # WHEN
        self.blue1.says('!balance')
        # THEN
        self.assertEqual(self.blue1.message_history, ['Teams will be balanced at the end of this round'])
        self.assertFalse(self.p._pending_teambalance)
        self.assertTrue(self.p._pending_skillbalance)
        self.assertEqual(self.p.cmd_pabalance, self.p._skillbalance_func)

    def test_round_based_gametype_delayed_execution(self):
        # GIVEN
        self.blue1.clearMessageHistory()
        self.p._lastbal = 0
        self.p.ignoreCheck = Mock(return_value=False)
        self.console.time = Mock(return_value=120)
        self.console.game.gameType = 'bm'
        self.blue1.says('!balance')
        self.assertEqual(self.blue1.message_history, ['Teams will be balanced at the end of this round'])
        self.assertFalse(self.p._pending_teambalance)
        self.assertTrue(self.p._pending_skillbalance)
        self.assertEqual(self.p.cmd_pabalance, self.p._skillbalance_func)
        # WHEN
        self.console.queueEvent(self.console.getEvent('EVT_GAME_ROUND_END'))
        # THEN
        self.console.write.assert_has_calls([call('bigtext "Balancing teams!"')])
        self.assertFalse(self.p._pending_teambalance)
        self.assertFalse(self.p._pending_skillbalance)
        self.assertIsNone(self.p._skillbalance_func)