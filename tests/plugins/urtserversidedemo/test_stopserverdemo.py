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
from tests.plugins.urtserversidedemo import PluginTestCase
from b3.fake import FakeClient


class Test_stopserverdemo(PluginTestCase):
    CONF = """\
[commands]
stopserverdemo = 20
"""
    def setUp(self):
        PluginTestCase.setUp(self)
        self.p.onStartup()
        self.moderator = FakeClient(self.console, name="Moderator", exactName="Moderator", guid="654654654654654654", groupBits=8)
        self.moderator.connects('0')
        self.moderator.clearMessageHistory()


    def test_no_parameter(self):
        self.moderator.says("!stopserverdemo")
        self.assertListEqual(["specify a player name or 'all'"], self.moderator.message_history)

    def test_non_existing_player(self):
        self.moderator.says("!stopserverdemo foo")
        self.assertListEqual(['No players found matching foo'], self.moderator.message_history)

    def test_all(self):
        self.p._recording_all_players = True
        when(self.console).write("stopserverdemo all").thenReturn("stopserverdemo: stopped recording laCourge")
        self.moderator.says("!stopserverdemo all")
        self.assertFalse(self.p._recording_all_players)
        self.assertListEqual(['stopserverdemo: stopped recording laCourge'], self.moderator.message_history)

    def test_existing_player(self):
        joe = FakeClient(self.console, name="Joe", guid="01230123012301230123", groupBits=1)
        joe.connects('1')
        self.assertEqual(joe, self.console.clients['1'])
        when(self.console).write("stopserverdemo 1").thenReturn("stopserverdemo: stopped recording Joe")
        self.moderator.says("!stopserverdemo joe")