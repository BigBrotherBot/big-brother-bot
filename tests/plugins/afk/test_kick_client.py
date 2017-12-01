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

from textwrap import dedent
from time import time
from tests.plugins.afk import *
from mock import call, Mock

# This test suite makes sure clients are kicked appropriately when `kick_client` is run
from b3 import TEAM_SPEC, TEAM_RED


@pytest.yield_fixture
def plugin(console):
    with logging_disabled():
        p = plugin_maker_ini(console, dedent("""
            [settings]
        """))
        p.inactivity_threshold_second = 0.05
        p.onLoadConfig()
        p.onStartup()
    yield p
    p.disable()


def too_long_ago():
    return time() - 10


def very_recently():
    return time() - 0.001


def test_nominal(plugin, joe):
    # GIVEN
    joe.kick = Mock()
    plugin.min_ingame_humans = 0
    joe.connects(1)
    # WHEN
    joe.last_activity_time = too_long_ago()
    plugin.kick_client(joe)
    # THEN
    assert [call(reason='AFK for too long on this server')] == joe.kick.mock_calls


def test_too_few_players_remaining(plugin, joe, jack):
    # GIVEN
    joe.kick = Mock()
    plugin.min_ingame_humans = 1
    joe.connects(1)
    jack.connects(2)
    jack.team = TEAM_SPEC

    # WHEN
    joe.last_activity_time = too_long_ago()
    plugin.kick_client(joe)
    # THEN
    assert [] == joe.kick.mock_calls

    # WHEN
    jack.team = TEAM_RED
    joe.last_activity_time = too_long_ago()
    plugin.kick_client(joe)
    # THEN
    assert [call(reason='AFK for too long on this server')] == joe.kick.mock_calls


def test_activity_at_the_last_second(plugin, joe):
    # GIVEN
    joe.kick = Mock()
    plugin.min_ingame_humans = 0
    joe.connects(1)
    # WHEN
    joe.last_activity_time = very_recently()
    plugin.kick_client(joe)
    # THEN
    assert [] == joe.kick.mock_calls

    # WHEN
    joe.last_activity_time = too_long_ago()
    plugin.kick_client(joe)
    # THEN
    assert [call(reason='AFK for too long on this server')] == joe.kick.mock_calls


def test_player_moved_to_spec(plugin, joe, jack):
    # GIVEN
    joe.kick = Mock()
    plugin.min_ingame_humans = 0
    joe.connects(1)
    jack.connects(2)

    # WHEN
    joe.team = TEAM_SPEC
    joe.last_activity_time = too_long_ago()
    plugin.kick_client(joe)
    # THEN
    assert [] == joe.kick.mock_calls

    # WHEN
    joe.team = TEAM_RED
    joe.last_activity_time = too_long_ago()
    plugin.kick_client(joe)
    # THEN
    assert [call(reason='AFK for too long on this server')] == joe.kick.mock_calls

