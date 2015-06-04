# -*- encoding: utf-8 -*-
from textwrap import dedent
from tests.plugins.afk import *
from mock import Mock



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


def test_game_break(plugin, joe):
    # GIVEN
    joe.connects(1)
    plugin.ask_client(joe)
    assert joe in plugin.kick_timers
    # WHEN
    plugin.on_game_break(None)
    # THEN
    assert joe not in plugin.kick_timers

