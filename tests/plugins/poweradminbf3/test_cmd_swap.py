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

from mock import Mock
from mockito import verify, when
import b3
from b3.config import CfgConfigParser
from b3.parsers.frostbite2.protocol import CommandFailedError
from b3.plugins.poweradminbf3 import Poweradminbf3Plugin
from tests.plugins.poweradminbf3 import Bf3TestCase


class Test_cmd_swap(Bf3TestCase):

    def setUp(self):
        super(Test_cmd_swap, self).setUp()
        self.conf = CfgConfigParser()
        self.conf.loadFromString("""[commands]
swap: 20
        """)
        self.p = Poweradminbf3Plugin(self.console, self.conf)
        self.p.onLoadConfig()
        self.p.onStartup()


    def test_frostbite_error(self):

        self.joe.connects("joe")
        self.joe.team = b3.TEAM_BLUE
        self.joe.teamId = 1
        self.joe.squad = 1

        self.moderator.connects("moderator")
        self.moderator.team = b3.TEAM_RED
        self.moderator.teamId = 2
        self.moderator.squad = 2

        # simulate Frostbite error when moving a player
        self.p._movePlayer = Mock(side_effect=CommandFailedError(['SetTeamFailed']))

        self.superadmin.connects('superadmin')
        self.superadmin.message_history = []
        self.superadmin.says("!swap joe moder")

        self.assertEqual(1, len(self.superadmin.message_history))
        self.assertEqual("Error while trying to swap joe with moderator. (SetTeamFailed)", self.superadmin.message_history[0])


    def test_superadmin_swap_joe(self):
        when(self.console).write()
        self.joe.connects('Joe')
        self.joe.teamId = 1
        self.joe.squad = 7

        self.superadmin.connects('superadmin')
        self.superadmin.teamId = 2
        self.superadmin.squad = 6

        self.superadmin.message_history = []
        self.superadmin.says('!swap joe')
        verify(self.console).write(('admin.movePlayer', self.joe.cid, self.superadmin.teamId, self.superadmin.squad, 'true'))
        verify(self.console).write(('admin.movePlayer', self.superadmin.cid, self.joe.teamId, self.joe.squad, 'true'))


    def test_superadmin_swap_joe_from_same_squad(self):

        self.joe.connects('Joe')
        self.joe.teamId = 2
        self.joe.squad = 6

        self.superadmin.connects('superadmin')
        self.superadmin.teamId = 2
        self.superadmin.squad = 6

        self.superadmin.message_history = []
        self.superadmin.says('!swap joe')
        self.assertEqual(['both players are in the same team and squad. Cannot swap'], self.superadmin.message_history)


    def test_superadmin_swap_players_from_same_team_and_squad(self):
        self.joe.connects('joe')
        self.joe.teamId = 1
        self.joe.squad = 6

        self.simon.connects('simon')
        self.simon.teamId = 1
        self.simon.squad = 6

        self.superadmin.connects('superadmin')
        self.superadmin.message_history = []
        self.superadmin.says("!swap joe simon")

        self.assertEqual(['both players are in the same team and squad. Cannot swap'], self.superadmin.message_history)


    def test_superadmin_swap_players_from_same_team_and_but_different_squads(self):
        when(self.console).write()
        self.joe.connects('joe')
        self.joe.teamId = 1
        self.joe.squad = 6

        self.simon.connects('simon')
        self.simon.teamId = 1
        self.simon.squad = 2

        self.superadmin.connects('superadmin')
        self.superadmin.message_history = []
        self.superadmin.says("!swap joe simon")

        verify(self.console).write(('admin.movePlayer', self.joe.cid, self.simon.teamId, self.simon.squad, 'true'))
        verify(self.console).write(('admin.movePlayer', self.simon.cid, self.joe.teamId, self.joe.squad, 'true'))
        self.assertEqual(['swapped player joe with simon'], self.superadmin.message_history)


class Test_issue_14(Bf3TestCase):

    def setUp(self):
        super(Test_issue_14, self).setUp()
        self.conf = CfgConfigParser()
        self.conf.loadFromString("""[commands]
swap: 0

[preferences]
no_level_check_level: 20
        """)
        self.p = Poweradminbf3Plugin(self.console, self.conf)
        self.p.onLoadConfig()
        self.p.onStartup()


    def test_above__no_level_check_level(self):

        when(self.console).write()
        assert self.p.no_level_check_level == 20

        self.superadmin.connects('God')
        self.superadmin.teamId = 2
        self.superadmin.squad = 6

        self.moderator.connects('moderator')
        self.moderator.teamId = 2
        self.moderator.squad = 5

        self.moderator.says("!swap God")
        verify(self.console).write(('admin.movePlayer', 'God', 2, 5, 'true'))

    def test_below__no_level_check_level(self):

        assert self.p.no_level_check_level == 20

        self.simon.connects("simon")
        self.simon.teamId = 1
        self.simon.squad = 7

        self.moderator.connects('moderator')
        self.moderator.teamId = 2
        self.moderator.squad = 5

        self.simon.message_history = []
        self.simon.says("!swap modera")
        self.assertEqual(['Operation denied because Moderator is in the Moderator group'], self.simon.message_history)
