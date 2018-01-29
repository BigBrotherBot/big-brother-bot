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

from mock import Mock, patch
from b3.config import CfgConfigParser
from b3.plugins.poweradminurt import PoweradminurtPlugin
from tests.plugins.poweradminurt.iourt42 import Iourt42TestCase


class Test_cmd_ident(Iourt42TestCase):
    def setUp(self):
        super(Test_cmd_ident, self).setUp()
        self.conf = CfgConfigParser()
        self.conf.loadFromString("""
[commands]
paident-id: 20

[special]
paident_full_level: 40
        """)
        self.p = PoweradminurtPlugin(self.console, self.conf)
        self.init_default_cvar()
        self.parser_conf._settings.update({'b3': {"time_zone": "GMT", "time_format": "%I:%M%p %Z %m/%d/%y"}})
        self.p.onLoadConfig()
        self.p.onStartup()

        self.console.say = Mock()
        self.console.write = Mock()

        self.moderator.connects("2")
        self.moderator.message_history = []

    def test_no_parameter(self):
        # WHEN
        self.moderator.says("!id")
        # THEN
        self.assertListEqual(["Your id is @2"], self.moderator.message_history)

    def test_junk(self):
        # WHEN
        self.moderator.says("!id qsdfsqdq sqfd qf")
        # THEN
        self.assertListEqual(["No players found matching qsdfsqdq"], self.moderator.message_history)

    def test_nominal_under_full_level(self):
        # GIVEN
        self.joe.pbid = "joe_pbid"
        self.joe.connects('3')
        # WHEN
        with patch('time.time', return_value=0.0) as time_mock:
            self.moderator.says("!id joe")
        # THEN
        self.assertListEqual(['12:00AM GMT 01/01/70 @3 Joe'], self.moderator.message_history)

    def test_nominal_above_full_level(self):
        # GIVEN
        self.joe.pbid = "joe_pbid"
        self.joe.connects('3')
        self.joe.timeAdd = 90*60.0
        self.superadmin.connects('1')
        # WHEN
        with patch('time.time', return_value=180*60.0):
            self.superadmin.says("!id joe")
        # THEN
        self.assertListEqual(['03:00AM GMT 01/01/70 @3 Joe  [joe_pbid] since 01:30AM GMT 01/01/70'], self.superadmin.message_history)


