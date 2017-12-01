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
from tests.plugins.afk import *
from mock import call, Mock
from b3 import TEAM_SPEC
from b3.events import Event

# This test suite makes sure `check_client` is called appropriately


@pytest.yield_fixture
def plugin(console):
    p = plugin_maker_ini(console, dedent("""
        [settings]
        consecutive_deaths_threshold: 3
        inactivity_threshold: 30s
        kick_reason: AFK for too long on this server
        are_you_afk: Are you AFK?
    """))
    p.MIN_INGAME_PLAYERS = 0  # disable this check by default
    p.onLoadConfig()
    p.onStartup()
    yield p
    p.disable()


def test_3_consecutive_deaths_with_no_activity(plugin, joe, jack):
    """
    player is killed 3 times in a row but shown some activity
    """
    # GIVEN
    plugin.check_client = Mock()
    joe.connects(1)
    jack.connects(2)
    # WHEN
    plugin.on_client_activity(Event("", None, client=jack))  # some activity
    joe.kills(jack)  # 1st death
    joe.kills(jack)  # 2nd death
    # THEN jack is not yet checked
    assert not plugin.check_client.called
    # WHEN
    joe.kills(jack)  # 3rd consecutive death with no activity
    # THEN jack is checked for inactivity
    assert [call(jack)] == plugin.check_client.mock_calls


def test_3_consecutive_deaths_with_some_activity(plugin, joe, jack):
    """
    player is killed 3 times in a row but shown some activity
    """
    # GIVEN
    plugin.check_client = Mock()
    joe.connects(1)
    jack.connects(2)
    # WHEN
    plugin.on_client_activity(Event("", None, client=jack))  # some activity
    joe.kills(jack)  # 1st death
    joe.kills(jack)  # 2nd death
    plugin.on_client_activity(Event("", None, client=jack))  # some activity
    # THEN jack is not yet checked
    assert not plugin.check_client.called
    # WHEN
    joe.kills(jack)  # 3rd death but with activity in between
    # THEN jack is still not checked
    assert not plugin.check_client.called


def testd_3_consecutive_deaths_with_no_activity_but_not_enough_players(plugin, joe, jack, bot):
    """
    player is killed 3 times in a row but shown some activity but he's the last player on the server
    """
    # GIVEN
    plugin.MIN_INGAME_PLAYERS = 1
    plugin.check_client = Mock()
    joe.connects(1)
    jack.connects(2)
    jack.team = TEAM_SPEC
    bot.connects(2)
    # WHEN
    plugin.on_client_activity(Event("", None, client=joe))  # some activity
    bot.kills(joe)  # 1st death
    bot.kills(joe)  # 2nd death
    # THEN jack is not yet checked
    assert not plugin.check_client.called
    # WHEN
    bot.kills(joe)  # 3rd consecutive death with no activity
    # THEN joe is not checked for inactivity as he is the last remaining human on the server (excluding spectators)
    assert not plugin.check_client.called

