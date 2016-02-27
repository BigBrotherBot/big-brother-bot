# -*- encoding: utf-8 -*-
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

