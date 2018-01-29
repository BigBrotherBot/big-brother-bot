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

import pytest

from textwrap import dedent
from time import sleep

from tests.plugins.afk import *
from mock import call, Mock

# This test suite makes sure `kick_client` is called appropriately when `ask_client` is run


@pytest.yield_fixture
def plugin(console):
    p = None
    with logging_disabled():
        p = plugin_maker_ini(console, dedent("""
            [settings]
            consecutive_deaths_threshold: 3
            inactivity_threshold: 30s
            last_chance_delay: 23
            kick_reason: AFK for too long on this server
            are_you_afk: Are you AFK?
            suspicion_announcement: {name} is AFK, kicking in {last_chance_delay}s
        """))
        plugin.inactivity_threshold_second = 0
        p.MIN_INGAME_PLAYERS = 0  # disable this check by default
        p.kick_client = Mock()
        p.console.say = Mock()
        p.onLoadConfig()
        p.onStartup()
    yield p
    p.disable()


def test_ask(plugin, joe):
    # GIVEN
    joe.message = Mock()
    # WHEN
    plugin.ask_client(joe)
    # THEN
    assert [call('Are you AFK?')] == joe.message.mock_calls
    assert joe in plugin.kick_timers
    assert [call("Joe is AFK, kicking in 23s")] == plugin.console.say.mock_calls


def test_no_response(plugin, joe):
    # GIVEN
    plugin.last_chance_delay = .005
    joe.message = Mock()
    joe.connects(1)
    # WHEN
    plugin.ask_client(joe)
    # THEN
    assert [call('Are you AFK?')] == joe.message.mock_calls
    assert [call("Joe is AFK, kicking in 0.005s")] == plugin.console.say.mock_calls
    # WHEN
    sleep(.01)
    # THEN
    assert [call(joe)] == plugin.kick_client.mock_calls


def test_response(plugin, joe):
    # GIVEN
    plugin.last_chance_delay = .005
    joe.message = Mock()
    joe.connects(1)
    # WHEN
    plugin.ask_client(joe)
    # THEN
    assert [call('Are you AFK?')] == joe.message.mock_calls
    assert [call("Joe is AFK, kicking in 0.005s")] == plugin.console.say.mock_calls
    # WHEN
    joe.says("hi")
    assert joe not in plugin.kick_timers
    sleep(.01)
    # THEN
    assert [] == plugin.kick_client.mock_calls
    assert joe not in plugin.kick_timers


def test_make_kill(plugin, joe):
    # GIVEN
    plugin.last_chance_delay = .005
    joe.message = Mock()
    joe.connects(1)
    # WHEN
    plugin.ask_client(joe)
    # THEN
    assert [call('Are you AFK?')] == joe.message.mock_calls
    assert [call("Joe is AFK, kicking in 0.005s")] == plugin.console.say.mock_calls
    # WHEN
    joe.kills(joe)
    assert joe not in plugin.kick_timers
    sleep(.01)
    assert [] == plugin.kick_client.mock_calls


def test_ask_twice(plugin, joe):
    # GIVEN
    joe.message = Mock()
    # WHEN
    plugin.ask_client(joe)
    # THEN
    assert [call('Are you AFK?')] == joe.message.mock_calls
    assert joe in plugin.kick_timers
    assert [call("Joe is AFK, kicking in 23s")] == plugin.console.say.mock_calls
    # WHEN
    plugin.ask_client(joe)
    assert [call('Are you AFK?')] == joe.message.mock_calls
    assert joe in plugin.kick_timers
    assert [call("Joe is AFK, kicking in 23s")] == plugin.console.say.mock_calls
