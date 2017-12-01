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

from mockito import when
from b3.config import CfgConfigParser
from b3.plugins.customcommands import CustomcommandsPlugin
from tests import logging_disabled
from tests.plugins.customcommands import CustomcommandsTestCase


with logging_disabled():
    from b3.fake import FakeClient


class Test_render_cmd_template(CustomcommandsTestCase):

    def setUp(self):
        CustomcommandsTestCase.setUp(self)
        self.conf = CfgConfigParser()
        self.p = CustomcommandsPlugin(self.console, self.conf)
        self.p.onLoadConfig()
        self.p.onStartup()
        self.player1 = FakeClient(console=self.console, name="Player1", guid="player1GUID", pbid="player1PBID")
        self.player2 = FakeClient(console=self.console, name="Player2", guid="player2GUID", pbid="player2PBID")
        self.player1.connects(cid="slot1")
        self.player2.connects(cid="slot2")

    def test_no_placeholder(self):
        self.assertEqual("f00", self.p._render_cmd_template("f00", data="", client=self.player1))

    def test_ARG(self):
        self.assertEqual("f00 bill bar", self.p._render_cmd_template("f00 <ARG> bar", data="bill", client=self.player1))
        self.assertRaises(ValueError, self.p._render_cmd_template, "f00 <ARG> bar", data="", client=self.player1)

    def test_ARG_OPT(self):
        self.assertEqual("hi", self.p._render_cmd_template("hi <ARG:OPT:>", data="", client=self.player1))
        self.assertEqual("hi f00", self.p._render_cmd_template("hi <ARG:OPT:f00>", data="", client=self.player1))
        self.assertEqual("hi bar", self.p._render_cmd_template("hi <ARG:OPT:f00>", data="bar", client=self.player1))
        self.assertEqual("hi foo bar", self.p._render_cmd_template("hi <ARG:OPT:f00>", data="foo bar", client=self.player1))

    def test_ARG_FIND_MAP_errors(self):
        # GIVEN
        when(self.p.console).getMaps().thenReturn(["map1", "map2", "map3", "ut4_turnpike", "ut4_casa"])
        # THEN
        self.assertRaises(ValueError, self.p._render_cmd_template, "map <ARG:FIND_MAP>", data="", client=self.player1)
        self.assertRaisesRegexp(ValueError, "do you mean : map2, map3, map1 ?",
                                self.p._render_cmd_template, "map <ARG:FIND_MAP>", data="map", client=self.player1)

    def test_ARG_FIND_MAP_nominal(self):
        def assertFoundMap(expected_map, cmd_parameter):
            self.assertEqual("map " + expected_map, self.p._render_cmd_template("map <ARG:FIND_MAP>",
                                                                                data=cmd_parameter, client=self.player1))
        # GIVEN
        when(self.p.console).getMaps().thenReturn(["map1", "map2", "map3", "ut4_turnpike", "ut4_casa"])
        # THEN
        assertFoundMap("map1", "map1")
        assertFoundMap("map1", " map1 ")
        assertFoundMap("ut4_casa", "ut4_casa")
        assertFoundMap("ut4_casa", "casa")

    def test_ARG_FIND_PLAYER_nominal(self):
        # GIVEN
        when(self.p._adminPlugin).findClientPrompt("f00", self.player1).thenReturn(self.player2)
        # THEN
        self.assertEqual("kick slot2", self.p._render_cmd_template("kick <ARG:FIND_PLAYER:PID>", data="f00", client=self.player1))
        self.assertEqual("kick player2PBID", self.p._render_cmd_template("kick <ARG:FIND_PLAYER:PBID>", data="f00", client=self.player1))
        self.assertEqual("kick player2GUID", self.p._render_cmd_template("kick <ARG:FIND_PLAYER:GUID>", data="f00", client=self.player1))
        self.assertEqual("kick Player2", self.p._render_cmd_template("kick <ARG:FIND_PLAYER:NAME>", data="f00", client=self.player1))
        self.assertEqual("kick Player2^7", self.p._render_cmd_template("kick <ARG:FIND_PLAYER:EXACTNAME>", data="f00", client=self.player1))
        self.assertEqual("kick @%s" % self.player2.id, self.p._render_cmd_template("kick <ARG:FIND_PLAYER:B3ID>", data="f00", client=self.player1))

    def test_PLAYER(self):
        self.assertEqual("f00 slot1", self.p._render_cmd_template("f00 <PLAYER:PID>", data="", client=self.player1))
        self.assertEqual("f00 player1PBID", self.p._render_cmd_template("f00 <PLAYER:PBID>", data="", client=self.player1))
        self.assertEqual("f00 player1GUID", self.p._render_cmd_template("f00 <PLAYER:GUID>", data="", client=self.player1))
        self.assertEqual("f00 Player1", self.p._render_cmd_template("f00 <PLAYER:NAME>", data="", client=self.player1))
        self.assertEqual("f00 Player1^7", self.p._render_cmd_template("f00 <PLAYER:EXACTNAME>", data="", client=self.player1))
        self.assertEqual("f00 @1", self.p._render_cmd_template("f00 <PLAYER:B3ID>", data="", client=self.player1))

    def test_LAST_KILLER(self):
        self.assertRaisesRegexp(ValueError, "your last killer is unknown", self.p._render_cmd_template, "f00 <LAST_KILLER:PID>", data="", client=self.player1)
        self.assertRaisesRegexp(ValueError, "your last killer is unknown", self.p._render_cmd_template, "f00 <LAST_KILLER:PBID>", data="", client=self.player1)
        self.assertRaisesRegexp(ValueError, "your last killer is unknown", self.p._render_cmd_template, "f00 <LAST_KILLER:GUID>", data="", client=self.player1)
        self.assertRaisesRegexp(ValueError, "your last killer is unknown", self.p._render_cmd_template, "f00 <LAST_KILLER:NAME>", data="", client=self.player1)
        self.assertRaisesRegexp(ValueError, "your last killer is unknown", self.p._render_cmd_template, "f00 <LAST_KILLER:EXACTNAME>", data="", client=self.player1)
        self.assertRaisesRegexp(ValueError, "your last killer is unknown", self.p._render_cmd_template, "f00 <LAST_KILLER:B3ID>", data="", client=self.player1)
        # WHEN
        self.player2.kills(self.player1)
        # THEN
        self.assertEqual("f00 slot2", self.p._render_cmd_template("f00 <LAST_KILLER:PID>", data="", client=self.player1))
        self.assertEqual("f00 player2PBID", self.p._render_cmd_template("f00 <LAST_KILLER:PBID>", data="", client=self.player1))
        self.assertEqual("f00 player2GUID", self.p._render_cmd_template("f00 <LAST_KILLER:GUID>", data="", client=self.player1))
        self.assertEqual("f00 Player2", self.p._render_cmd_template("f00 <LAST_KILLER:NAME>", data="", client=self.player1))
        self.assertEqual("f00 Player2^7", self.p._render_cmd_template("f00 <LAST_KILLER:EXACTNAME>", data="", client=self.player1))
        self.assertEqual("f00 @2", self.p._render_cmd_template("f00 <LAST_KILLER:B3ID>", data="", client=self.player1))

    def test_LAST_VICTIM(self):
        self.assertRaisesRegexp(ValueError, "your last victim is unknown", self.p._render_cmd_template, "f00 <LAST_VICTIM:PID>", data="", client=self.player1)
        self.assertRaisesRegexp(ValueError, "your last victim is unknown", self.p._render_cmd_template, "f00 <LAST_VICTIM:PBID>", data="", client=self.player1)
        self.assertRaisesRegexp(ValueError, "your last victim is unknown", self.p._render_cmd_template, "f00 <LAST_VICTIM:GUID>", data="", client=self.player1)
        self.assertRaisesRegexp(ValueError, "your last victim is unknown", self.p._render_cmd_template, "f00 <LAST_VICTIM:NAME>", data="", client=self.player1)
        self.assertRaisesRegexp(ValueError, "your last victim is unknown", self.p._render_cmd_template, "f00 <LAST_VICTIM:EXACTNAME>", data="", client=self.player1)
        self.assertRaisesRegexp(ValueError, "your last victim is unknown", self.p._render_cmd_template, "f00 <LAST_VICTIM:B3ID>", data="", client=self.player1)
        # WHEN
        self.player1.kills(self.player2)
        # THEN
        self.assertEqual("f00 slot2", self.p._render_cmd_template("f00 <LAST_VICTIM:PID>", data="", client=self.player1))
        self.assertEqual("f00 player2PBID", self.p._render_cmd_template("f00 <LAST_VICTIM:PBID>", data="", client=self.player1))
        self.assertEqual("f00 player2GUID", self.p._render_cmd_template("f00 <LAST_VICTIM:GUID>", data="", client=self.player1))
        self.assertEqual("f00 Player2", self.p._render_cmd_template("f00 <LAST_VICTIM:NAME>", data="", client=self.player1))
        self.assertEqual("f00 Player2^7", self.p._render_cmd_template("f00 <LAST_VICTIM:EXACTNAME>", data="", client=self.player1))
        self.assertEqual("f00 @2", self.p._render_cmd_template("f00 <LAST_VICTIM:B3ID>", data="", client=self.player1))

    def test_ADMINGROUP_SHORT(self):
        groups = {0: 'guest', 1: 'user', 2: 'reg', 8: 'mod', 16: 'admin', 32: 'fulladmin', 64: 'senioradmin', 128: 'superadmin'}
        for groupBits, group_keyword in groups.items():
            # WHEN
            self.player1.groupBits = groupBits
            # THEN
            self.assertEqual("f00 %s" % group_keyword,
                             self.p._render_cmd_template("f00 <PLAYER:ADMINGROUP_SHORT>", data="", client=self.player1),
                             "failed with group %s" % group_keyword)

    def test_ADMINGROUP_LONG(self):
        groups = {0: 'Guest', 1: 'User', 2: 'Regular', 8: 'Moderator', 16: 'Admin', 32: 'Full Admin', 64: 'Senior Admin', 128: 'Super Admin'}
        for groupBits, group_name in groups.items():
            # WHEN
            self.player1.groupBits = groupBits
            # THEN
            self.assertEqual("f00 %s" % group_name,
                             self.p._render_cmd_template("f00 <PLAYER:ADMINGROUP_LONG>", data="", client=self.player1),
                             "failed with group %s" % group_name)

    def test_ADMINGROUP_LEVEL(self):
        groups = {0: 0, 1: 1, 2: 2, 8: 20, 16: 40, 32: 60, 64: 80, 128: 100}
        for groupBits, group_level in groups.items():
            # WHEN
            self.player1.groupBits = groupBits
            # THEN
            self.assertEqual("f00 %s" % group_level,
                             self.p._render_cmd_template("f00 <PLAYER:ADMINGROUP_LEVEL>", data="", client=self.player1),
                             "failed with group %s" % group_level)
