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
from mock import patch, Mock, call
from b3.config import CfgConfigParser
from b3.plugins.poweradminurt import PoweradminurtPlugin
from tests.plugins.poweradminurt.iourt41 import Iourt41TestCase
from tests.plugins.poweradminurt.iourt42 import Iourt42TestCase


class mixin_cmd_paset(object):
    def setUp(self):
        super(mixin_cmd_paset, self).setUp()
        self.conf = CfgConfigParser()
        self.conf.loadFromString("""
[commands]
paset: 20
        """)
        self.p = PoweradminurtPlugin(self.console, self.conf)
        self.init_default_cvar()
        self.p.onLoadConfig()
        self.p.onStartup()

        self.sleep_patcher = patch.object(time, 'sleep')
        self.sleep_patcher.start()
        self.setCvar_patcher = patch.object(self.console, 'setCvar')
        self.setCvar_mock = self.setCvar_patcher.start()

        self.moderator.connects("2")

    def assert_setCvar_calls(self, expected_calls):
        self.assertListEqual(expected_calls, self.setCvar_mock.mock_calls)

    def tearDown(self):
        super(mixin_cmd_paset, self).tearDown()
        self.sleep_patcher.stop()
        self.setCvar_patcher.stop()


    def test_nominal(self):
        # WHEN
        self.moderator.says('!paset sv_foo bar')
        # THEN
        self.assert_setCvar_calls([call('sv_foo', 'bar')])
        self.assertListEqual([], self.moderator.message_history)

    def test_no_parameter(self):
        # WHEN
        self.moderator.says('!paset')
        # THEN
        self.assert_setCvar_calls([])
        self.assertListEqual(['Invalid or missing data, try !help paset'], self.moderator.message_history)

    def test_no_value(self):
        # WHEN
        self.moderator.says('!paset sv_foo')
        # THEN
        self.assert_setCvar_calls([call('sv_foo', '')])
        self.assertListEqual([], self.moderator.message_history)


class Test_cmd_nuke_41(mixin_cmd_paset, Iourt41TestCase):
    """
    call the mixin test using the Iourt41TestCase parent class
    """

class Test_cmd_nuke_42(mixin_cmd_paset, Iourt42TestCase):
    """
    call the mixin test using the Iourt42TestCase parent class
    """
