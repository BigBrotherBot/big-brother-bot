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

from types import MethodType
from textwrap import dedent
from tests.plugins.afk import *
from mock import call, Mock

# This test suite makes sure `check_client` is called appropriately


def evt_client_move(self, client):
    self.console.queueEvent(self.console.getEvent('EVT_CLIENT_MOVE', client=client))


def evt_client_standing(self, client):
    self.console.queueEvent(self.console.getEvent('EVT_CLIENT_STANDING', client=client))


@pytest.yield_fixture
def plugin(console):
    console.createEvent('EVT_CLIENT_MOVE', 'Event client move')
    console.createEvent('EVT_CLIENT_STANDING', 'Event client standing')

    p = plugin_maker_ini(console, dedent("""
        [settings]
        consecutive_deaths_threshold: 3
        inactivity_threshold: 30s
        kick_reason: AFK for too long on this server
        are_you_afk: Are you AFK?
    """))
    p.evt_client_move = MethodType(evt_client_move, p, AfkPlugin)
    p.evt_client_standing = MethodType(evt_client_standing, p, AfkPlugin)
    p.MIN_INGAME_PLAYERS = 0  # disable this check by default
    p.onLoadConfig()
    p.onStartup()
    yield p
    p.disable()


def test_evt_client_standing(plugin, joe):
    """
    EVT_CLIENT_STANDING is received
    """
    # GIVEN
    plugin.check_client = Mock()
    joe.connects(1)
    # WHEN
    plugin.evt_client_standing(joe)
    # THEN
    assert [call(joe)] == plugin.check_client.mock_calls


def test_evt_client_move(plugin, joe):
    """
    EVT_CLIENT_MOVE is considered as player activity
    """
    # GIVEN
    past_activity_time = 123654
    joe.connects(1)
    joe.last_activity_time = past_activity_time
    # WHEN
    plugin.evt_client_move(joe)
    # THEN
    assert joe.last_activity_time > past_activity_time
