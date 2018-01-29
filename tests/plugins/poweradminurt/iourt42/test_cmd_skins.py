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


class Test_cmd_skins(Iourt42TestCase):
    def setUp(self):
        super(Test_cmd_skins, self).setUp()
        self.conf = CfgConfigParser()
        self.conf.loadFromString("""
[commands]
pagoto-goto: 20         ; set the goto <on/off>
        """)
        self.p = PoweradminurtPlugin(self.console, self.conf)
        self.init_default_cvar()
        self.p.onLoadConfig()
        self.p.onStartup()

        self.console.say = Mock()
        self.console.write = Mock()

        self.moderator.connects("2")

    def test_missing_parameter(self):
        self.moderator.message_history = []
        self.moderator.says("!goto")
        self.assertListEqual(["invalid or missing data, try !help pagoto"], self.moderator.message_history)

    def test_junk(self):
        self.moderator.message_history = []
        self.moderator.says("!goto qsdf")
        self.assertListEqual(["invalid or missing data, try !help pagoto"], self.moderator.message_history)

    def test_on(self):
        self.moderator.says("!goto on")
        self.console.write.assert_has_calls([call('set g_allowgoto "1"')])

    def test_off(self):
        self.moderator.says("!goto off")
        self.console.write.assert_has_calls([call('set g_allowgoto "0"')])


