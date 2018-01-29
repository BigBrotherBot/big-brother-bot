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
from b3 import TEAM_SPEC

# This test suite makes sure `check_client` is called appropriately


@pytest.yield_fixture
def plugin(console):
    p = plugin_maker_ini(console, dedent("""
        [settings]
    """))
    p.onLoadConfig()
    p.onStartup()
    yield p
    p.disable()


def test_count_ingame_humans(plugin, joe, jack, bot):
    assert 0 == plugin.count_ingame_humans()
    joe.connects(1)
    assert 1 == plugin.count_ingame_humans()
    bot.connects(2)
    assert 1 == plugin.count_ingame_humans()
    jack.connects(3)
    assert 2 == plugin.count_ingame_humans()
    joe.team = TEAM_SPEC
    assert 1 == plugin.count_ingame_humans()


def test_client_disconnection_clears_kick_timer(plugin, joe):
    # GIVEN
    plugin.last_chance_delay = 10

    # WHEN
    joe.connects(1)
    joe.says("hi")
    # THEN
    assert hasattr(joe, 'last_activity_time')

    # WHEN
    plugin.ask_client(joe)
    # THEN
    assert 1 == len(plugin.kick_timers)
    assert joe in plugin.kick_timers

    # WHEN
    joe.disconnects()
    # THEN
    assert 0 == len(plugin.kick_timers)
    assert joe not in plugin.kick_timers
    assert not hasattr(joe, 'last_activity_time')

