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

from mock import Mock, call
from mockito import when

from b3.plugins.poweradminbf3 import Poweradminbf3Plugin
from b3.config import CfgConfigParser
from tests.plugins.poweradminbf3  import Bf3TestCase, logging_disabled


class Test_events(Bf3TestCase):

    def setUp(self):
        Bf3TestCase.setUp(self)
        self.conf = CfgConfigParser()
        with logging_disabled():
            self.p = Poweradminbf3Plugin(self.console, self.conf)
        when(self.console).write(('vars.roundStartPlayerCount',)).thenReturn(['0'])
        when(self.console).write(('vars.roundLockdownCountdown',)).thenReturn(['3'])
        self.scrambleTeams_mock = self.p._scrambler.scrambleTeams = Mock(name="scrambleTeams", wraps=self.p._scrambler.scrambleTeams)
        self.scrambleTeams_mock.reset_mock()

    ###############################################################
    # utilities
    ###############################################################

    def _assert_scrambleTeams_has_calls_on_level_started(self, scramble_mode, gamemode_blacklist, next_gamemode, next_round_number, expected_calls):
        # Given
        self.conf.loadFromString("""
[scrambler]
mode: %s
strategy: random
gamemodes_blacklist: %s""" % (scramble_mode, '|'.join(gamemode_blacklist)))
        with logging_disabled():
            self.p.onLoadConfig()
            self.p.onStartup()

        # Make sure context is
        self.assertEqual(gamemode_blacklist, self.p._autoscramble_gamemode_blacklist)
        if scramble_mode == 'round':
            self.assertTrue(self.p._autoscramble_rounds)
            self.assertFalse(self.p._autoscramble_maps)
        elif scramble_mode == 'map':
            self.assertFalse(self.p._autoscramble_rounds)
            self.assertTrue(self.p._autoscramble_maps)
        elif scramble_mode == 'off':
            self.assertFalse(self.p._autoscramble_rounds)
            self.assertFalse(self.p._autoscramble_maps)
        else:
            self.fail("unsupported scramble mode : " + scramble_mode)

        # When
        self.joe.connects('joe')
        when(self.console).write(('serverInfo',)).thenReturn([ 'i3D.net - BigBrotherBot #3 (DE)', '1', '16',
                                                                next_gamemode, 'MP_007', str(next_round_number), '2', '4', '0', '0', '0', '0', '50', '', 'false', 'true',
                                                                'false', '790596', '1484', '', '', '', 'EU', 'AMS', 'DE', 'false'])
        self.console.routeFrostbitePacket(['server.onLevelLoaded', 'MP_007', next_gamemode, str(next_round_number), '2'])
        when(self.console).getClient('joe').thenReturn(self.joe)
        self.console.routeFrostbitePacket(['player.onSpawn', 'joe', '1'])

        # Then
        self.scrambleTeams_mock.assert_has_calls(expected_calls)


    def assert_scrambleTeams_has_calls_on_round_change(self, scramble_mode, gamemode_blacklist, next_gamemode, expected_calls):
        self._assert_scrambleTeams_has_calls_on_level_started(scramble_mode=scramble_mode,
            gamemode_blacklist=gamemode_blacklist, next_gamemode=next_gamemode, next_round_number=1,
            expected_calls=expected_calls)

    def assert_scrambleTeams_has_calls_on_map_change(self, scramble_mode, gamemode_blacklist, next_gamemode, expected_calls):
        self._assert_scrambleTeams_has_calls_on_level_started(scramble_mode=scramble_mode,
            gamemode_blacklist=gamemode_blacklist, next_gamemode=next_gamemode, next_round_number=0,
            expected_calls=expected_calls)

    ###############################################################
    # Actual tests
    ###############################################################

    def test_auto_scramble_ignore_blacklisted_gamemodes_on_round_change(self):
        self.assert_scrambleTeams_has_calls_on_round_change(
            scramble_mode='round',
            gamemode_blacklist=['SquadDeathMatch0'],
            next_gamemode='SquadDeathMatch0',
            expected_calls=[])

    def test_auto_scramble_on_round_change(self):
        self.assert_scrambleTeams_has_calls_on_round_change(
            scramble_mode='round',
            gamemode_blacklist=['SquadDeathMatch0'],
            next_gamemode='Rush0',
            expected_calls=[call()])
        self.assert_scrambleTeams_has_calls_on_round_change(
            scramble_mode='off',
            gamemode_blacklist=['SquadDeathMatch0'],
            next_gamemode='Rush0',
            expected_calls=[])

    def test_auto_scramble_ignore_blacklisted_gamemodes_on_map_change(self):
        self.assert_scrambleTeams_has_calls_on_map_change(
            scramble_mode='map',
            gamemode_blacklist=['SquadDeathMatch0', 'Conquest0'],
            next_gamemode='SquadDeathMatch0',
            expected_calls=[])

    def test_auto_scramble_on_map_change(self):
        self.assert_scrambleTeams_has_calls_on_map_change(
            scramble_mode='map',
            gamemode_blacklist=['SquadDeathMatch0'],
            next_gamemode='Rush0',
            expected_calls=[call()])
        self.assert_scrambleTeams_has_calls_on_map_change(
            scramble_mode='off',
            gamemode_blacklist=['SquadDeathMatch0'],
            next_gamemode='Rush0',
            expected_calls=[])

