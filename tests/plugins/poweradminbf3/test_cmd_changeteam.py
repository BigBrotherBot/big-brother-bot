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

import b3
from b3.config import CfgConfigParser
from b3.parsers.frostbite2.protocol import CommandFailedError
from b3.plugins.poweradminbf3 import Poweradminbf3Plugin
from mock import call, patch, Mock
from mockito import when, verify
from tests.plugins.poweradminbf3 import Bf3TestCase, logging_disabled


class Test_cmd_changeteam(Bf3TestCase):
    def setUp(self):
        super(Test_cmd_changeteam, self).setUp()
        self.conf = CfgConfigParser()
        self.conf.loadFromString("""
[commands]
changeteam: mod
        """)
        with logging_disabled():
            self.p = Poweradminbf3Plugin(self.console, self.conf)
            self.p.onLoadConfig()
            self.p.onStartup()

        def my_write(data):
            if data[0] == 'admin.movePlayer':
                self.console.routeFrostbitePacket(['player.onTeamChange', data[1], data[2], data[3]])
                return ['OK']
            else:
                return Mock()

        self.write_patcher = patch.object(self.console, "write", side_effect=my_write)
        self.write_mock = self.write_patcher.start()

    def tearDown(self):
        Bf3TestCase.tearDown(self)
        self.write_patcher.stop()

    def test_frostbite_error(self):
        self.joe.connects("joe")
        self.joe.team = b3.TEAM_BLUE
        self.joe.teamId = 1
        self.joe.squad = 1

        # simulate Frostbite error when moving a player
        when(self.console).write(('admin.movePlayer', 'joe', 2, 0, 'true')).thenRaise(
            CommandFailedError(['SetTeamFailed']))

        self.superadmin.connects('superadmin')
        self.superadmin.message_history = []
        self.superadmin.says("!changeteam joe")

        self.assertEqual(1, self.joe.teamId)
        self.assertEqual(["Error, server replied ['SetTeamFailed']"], self.superadmin.message_history)


    def test_no_argument(self):
        self.superadmin.connects('superadmin')
        self.superadmin.message_history = []
        self.superadmin.says('!changeteam')
        self.assertEqual(['Invalid data, try !help changeteam'], self.superadmin.message_history)


    def test_unknown_player(self):
        self.superadmin.connects('superadmin')
        self.superadmin.message_history = []
        self.superadmin.says('!changeteam f00')
        self.assertEqual(['No players found matching f00'], self.superadmin.message_history)


    def test_trying_to_changeteam_on_an_higher_level_player(self):
        # GIVEN
        self.console.getPlugin('admin')._warn_command_abusers = True
        self.joe.connects('Joe')
        self.superadmin.connects('superadmin')
        self.superadmin.teamId = 2
        self.superadmin.squad = 1
        self.assertLess(self.joe.maxLevel, self.superadmin.maxLevel)
        self.joe.message_history = []
        # WHEN
        self.joe.says('!changeteam god')
        # THEN
        self.assertEqual(2, self.superadmin.teamId)
        self.assertEqual(1, self.superadmin.squad)
        self.assertEqual(1, len(self.joe.message_history))


    def assert_moved_from_team_1_to_2_to_1(self):
        self.console.getServerInfo()
        self.joe.connects('Joe')
        self.superadmin.connects('superadmin')

        # GIVEN
        self.superadmin.message_history = []
        self.joe.teamId = 1
        # WHEN
        self.superadmin.says('!changeteam joe')
        # THEN
        verify(self.console).write(('admin.movePlayer', self.joe.cid, 2, 0, 'true'))
        self.assertEqual(['Joe forced from team 1 to team 2'], self.superadmin.message_history)

        # GIVEN
        self.superadmin.message_history = []
        self.joe.teamId = 2
        # WHEN
        self.superadmin.says('!changeteam joe')
        # THEN
        verify(self.console).write(('admin.movePlayer', self.joe.cid, 1, 0, 'true'))
        self.assertEqual(['Joe forced from team 2 to team 1'], self.superadmin.message_history)

    def test_ConquestLarge0(self):
        # GIVEN
        when(self.console).write(('serverInfo',)).thenReturn(
            ['i3D.net - BigBrotherBot #3 (DE)', '0', '16', 'ConquestLarge0', 'MP_007', '0', '2',
             '2', '300', '300', '0', '', 'false', 'true', 'false', '197758', '197735', '', '', '', 'EU', 'AMS', 'DE'])
        self.assert_moved_from_team_1_to_2_to_1()

    def test_ConquestSmall0(self):
        when(self.console).write(('serverInfo',)).thenReturn(
            ['i3D.net - BigBrotherBot #3 (DE)', '0', '16', 'ConquestSmall0', 'MP_001', '1', '2',
             '2', '250', '250', '0', '', 'false', 'true', 'false', '197774', '1', '', '', '', 'EU', 'AMS', 'DE'])
        self.assert_moved_from_team_1_to_2_to_1()

    def test_RushLarge0(self):
        # set the BF3 server
        # despite showing 0 teams in the serverInfo response, this gamemode has 2 teams (id 1 and 2)
        when(self.console).write(('serverInfo',)).thenReturn(
            ['i3D.net - BigBrotherBot #3 (DE)', '0', '16', 'RushLarge0', 'MP_001', '0', '2',
             '0', '0', '', 'false', 'true', 'false', '197817', '2', '', '', '', 'EU', 'AMS', 'DE'])
        self.assert_moved_from_team_1_to_2_to_1()

    def test_SquadRush0(self):
        # despite showing 0 teams in the serverInfo response, this gamemode has 2 teams (id 1:attackers and 2:defenders)
        when(self.console).write(('serverInfo',)).thenReturn(
            ['i3D.net - BigBrotherBot #3 (DE)', '0', '8', 'SquadRush0', 'MP_001', '1', '2',
             '0', '0', '', 'false', 'true', 'false', '197928', '0', '', '', '', 'EU', 'AMS', 'DE'])
        self.assert_moved_from_team_1_to_2_to_1()

    def test_TeamDeathMatch0(self):
        when(self.console).write(('serverInfo',)).thenReturn(
            ['i3D.net - BigBrotherBot #3 (DE)', '0', '16', 'TeamDeathMatch0', 'MP_001', '1', '2',
             '2', '0', '0', '100', '', 'false', 'true', 'false', '198148', '0', '', '', '', 'EU', 'AMS', 'DE'])
        self.assert_moved_from_team_1_to_2_to_1()

    def test_SquadDeathMatch0(self):
        when(self.console).write(('serverInfo',)).thenReturn(
            ['i3D.net - BigBrotherBot #3 (DE)', '0', '16', 'SquadDeathMatch0', 'MP_001', '0', '2',
             '4', '0', '0', '0', '0', '50', '', 'false', 'true', 'false', '198108', '0', '', '', '', 'EU', 'AMS', 'DE'])
        self.console.getServerInfo()
        self.joe.connects('Joe')
        self.superadmin.connects('superadmin')
        self.superadmin.message_history = []

        # GIVEN
        self.joe.teamId = 1
        # WHEN
        self.superadmin.says('!changeteam joe')
        # THEN
        verify(self.console).write(('admin.movePlayer', self.joe.cid, 2, 0, 'true'))
        self.assertEqual(['Joe forced from team 1 to team 2'], self.superadmin.message_history)

        # GIVEN
        self.joe.teamId = 2
        # WHEN
        self.superadmin.says('!changeteam joe')
        # THEN
        verify(self.console).write(('admin.movePlayer', self.joe.cid, 3, 0, 'true'))

        # GIVEN
        self.joe.teamId = 3
        # WHEN
        self.superadmin.says('!changeteam joe')
        # THEN
        verify(self.console).write(('admin.movePlayer', self.joe.cid, 4, 0, 'true'))

        # GIVEN
        self.joe.teamId = 4
        # WHEN
        self.superadmin.says('!changeteam joe')
        # THEN
        verify(self.console).write(('admin.movePlayer', self.joe.cid, 1, 0, 'true'))

        self.assertEqual(['Joe forced from team 1 to team 2', 'Joe forced from team 2 to team 3',
                          'Joe forced from team 3 to team 4', 'Joe forced from team 4 to team 1'],
            self.superadmin.message_history)


class Test_issue_14(Bf3TestCase):
    def setUp(self):
        super(Test_issue_14, self).setUp()
        self.conf = CfgConfigParser()
        self.conf.loadFromString("""
[commands]
changeteam: guest
[preferences]
no_level_check_level: 20
        """)
        self.p = Poweradminbf3Plugin(self.console, self.conf)
        self.p.onLoadConfig()
        self.p.onStartup()


    def test_above__no_level_check_level(self):
        assert self.p.no_level_check_level == 20

        self.superadmin.connects('God')
        self.superadmin.teamId = 2

        self.moderator.connects('moderator')
        self.moderator.teamId = 2

        with patch.object(self.console, 'write') as write_mock:
            self.moderator.says("!changeteam God")
        self.assertListEqual([call(('admin.movePlayer', 'God', 1, 0, 'true'))], write_mock.mock_calls)


    def test_below__no_level_check_level(self):
        assert self.p.no_level_check_level == 20

        self.simon.connects("simon")
        self.simon.teamId = 1

        self.moderator.connects('moderator')
        self.moderator.teamId = 2

        self.simon.message_history = []
        self.simon.says("!changeteam modera")
        self.assertEqual(['Operation denied because Moderator is in the Moderator group'], self.simon.message_history)
