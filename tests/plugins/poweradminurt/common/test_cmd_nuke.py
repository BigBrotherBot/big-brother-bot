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
import thread
from mock import patch, call, Mock
from b3.config import CfgConfigParser
from b3.plugins.poweradminurt import PoweradminurtPlugin
from tests.plugins.poweradminurt.iourt41 import Iourt41TestCase
from tests.plugins.poweradminurt.iourt42 import Iourt42TestCase

class mixin_cmd_nuke(object):

    def setUp(self):
        super(mixin_cmd_nuke, self).setUp()
        self.conf = CfgConfigParser()
        self.conf.loadFromString("""
[commands]
panuke-nuke: 20
        """)
        self.p = PoweradminurtPlugin(self.console, self.conf)
        self.init_default_cvar()
        self.p.onLoadConfig()
        self.p.onStartup()

        self.sleep_patcher = patch.object(time, 'sleep')
        self.sleep_patcher.start()

        self.console.say = Mock()
        self.console.saybig = Mock()
        self.console.write = Mock()

        self.moderator.connects("2")

    def tearDown(self):
        super(mixin_cmd_nuke, self).tearDown()
        self.sleep_patcher.stop()

    def test_no_argument(self):
        self.moderator.message_history = []
        self.moderator.says("!nuke")
        self.assertEqual(['Invalid data, try !help panuke'], self.moderator.message_history)
        self.console.write.assert_has_calls([])

    def test_unknown_player(self):
        self.moderator.message_history = []
        self.moderator.says("!nuke f00")
        self.assertEqual(['No players found matching f00'], self.moderator.message_history)
        self.console.write.assert_has_calls([])

    def test_joe(self):
        self.joe.connects('3')
        self.moderator.message_history = []
        self.moderator.says("!nuke joe")
        self.assertEqual([], self.moderator.message_history)
        self.assertEqual([], self.joe.message_history)
        self.console.write.assert_has_calls([call('nuke 3')])

    def test_joe_multi(self):

        def _start_new_thread(function, args):
            function(*args)

        with patch.object(thread, 'start_new_thread', wraps=_start_new_thread):
            self.joe.connects('3')
            self.moderator.message_history = []
            self.moderator.says("!nuke joe 3")
            self.assertEqual([], self.moderator.message_history)
            self.assertEqual([], self.joe.message_history)
            self.console.write.assert_has_calls([call('nuke 3'), call('nuke 3'), call('nuke 3')])


class Test_cmd_nuke_41(mixin_cmd_nuke, Iourt41TestCase):
    """
    call the mixin_cmd_nuke test using the Iourt41TestCase parent class
    """

class Test_cmd_nuke_42(mixin_cmd_nuke, Iourt42TestCase):
    """
    call the mixin_cmd_nuke test using the Iourt42TestCase parent class
    """
