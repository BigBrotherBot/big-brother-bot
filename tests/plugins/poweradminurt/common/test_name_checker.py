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
from mock import patch, call, Mock, ANY
from b3.config import CfgConfigParser
from b3.fake import FakeClient
from b3.plugins.poweradminurt import PoweradminurtPlugin
from tests.plugins.poweradminurt.iourt41 import Iourt41TestCase
from tests.plugins.poweradminurt.iourt42 import Iourt42TestCase

class mixin_name_checker(object):

    def setUp(self):
        super(mixin_name_checker, self).setUp()
        self.conf = CfgConfigParser()
        self.conf.loadFromString("""
[namechecker]
checkdupes: True
checkunknown: True
checkbadnames: True
        """)
        self.p = PoweradminurtPlugin(self.console, self.conf)
        self.init_default_cvar()
        self.p.onLoadConfig()
        self.p.onStartup()

        self.sleep_patcher = patch.object(time, 'sleep')
        self.sleep_patcher.start()

        self.console.say = Mock()
        self.console.write = Mock()

        self.p._ignoreTill = 0


    def tearDown(self):
        super(mixin_name_checker, self).tearDown()
        self.sleep_patcher.stop()


    def test_checkdupes_no_dup(self):
        # GIVEN
        p1 = FakeClient(self.console, name="theName", guid="p1guid")
        p1.warn = Mock()
        p1.connects("1")
        p2 = FakeClient(self.console, name="anotherName", guid="p2guid")
        p2.warn = Mock()
        p2.connects("2")
        # WHEN
        self.assertFalse(p1.name == p2.name)
        self.p.namecheck()
        # THEN
        self.assertFalse(p1.warn.called)
        self.assertFalse(p2.warn.called)


    def test_checkdupes_with_dup(self):
        # GIVEN
        p1 = FakeClient(self.console, name="sameName", guid="p1guid")
        p1.warn = Mock()
        p1.connects("1")
        p2 = FakeClient(self.console, name="sameName", guid="p2guid")
        p2.warn = Mock()
        p2.connects("2")
        # WHEN
        self.assertTrue(p1.name == p2.name)
        self.p.namecheck()
        # THEN
        p1.warn.assert_has_calls([call(ANY, ANY, 'badname', None, '')])
        p2.warn.assert_has_calls([call(ANY, ANY, 'badname', None, '')])


    def test_checkdupes_with_player_reconnecting(self):
        # GIVEN
        p1 = FakeClient(self.console, name="sameName", guid="p1guid")
        p1.warn = Mock()
        p1.connects("1")
        # WHEN
        p1.disconnects()
        p1.connects("2")
        self.p.namecheck()
        # THEN
        self.assertFalse(p1.warn.called)


    def test_checkunknown(self):
        # GIVEN
        p1 = FakeClient(self.console, name="New UrT Player", guid="p1guid")
        p1.warn = Mock()
        p1.connects("1")
        # WHEN
        self.p.namecheck()
        # THEN
        p1.warn.assert_has_calls([call(ANY, ANY, 'badname', None, '')])


    def test_checkbadnames(self):
        # GIVEN
        p1 = FakeClient(self.console, name="all", guid="p1guid")
        p1.warn = Mock()
        p1.connects("1")
        # WHEN
        self.p.namecheck()
        # THEN
        p1.warn.assert_has_calls([call(ANY, ANY, 'badname', None, '')])



class Test_cmd_nuke_41(mixin_name_checker, Iourt41TestCase):
    """
    call the mixin test using the Iourt41TestCase parent class
    """

class Test_cmd_nuke_42(mixin_name_checker, Iourt42TestCase):
    """
    call the mixin test using the Iourt42TestCase parent class
    """
