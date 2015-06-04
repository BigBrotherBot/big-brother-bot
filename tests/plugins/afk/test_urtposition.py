# -*- encoding: utf-8 -*-
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
