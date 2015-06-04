# -*- encoding: utf-8 -*-
from textwrap import dedent
from time import time
from tests.plugins.afk import *
from mock import call, Mock
from b3.events import Event

# This test suite makes sure `ask_client` is called appropriately when `check_client` is run


@pytest.yield_fixture
def plugin(console):
    p = plugin_maker_ini(console, dedent("""
        [settings]
        consecutive_deaths_threshold: 3
        inactivity_threshold: 30s
        kick_reason: AFK for too long on this server
        are_you_afk: Are you AFK?
    """))
    p.ask_client = Mock()
    p.onLoadConfig()
    p.onStartup()
    yield p
    p.disable()


def test_active_recently(plugin, joe):
    """
    check a player who was active 20s ago
    """
    # GIVEN
    now = time()
    joe.connects(1)
    plugin.on_client_activity(Event("", None, client=joe), now=(now - 20))  # some activity 20s ago
    # WHEN
    plugin.check_client(joe)
    # THEN joe is not asked if AFK
    assert not plugin.ask_client.called


def test_not_active_recently(plugin, joe):
    """
    check a player who was active 50s ago
    """
    # GIVEN
    now = time()
    joe.connects(1)
    plugin.on_client_activity(Event("", None, client=joe), now=(now - 50))  # some activity 50s ago
    # WHEN
    plugin.check_client(joe)
    # THEN joe is asked if AFK
    assert [call(joe)] == plugin.ask_client.mock_calls


def test_not_active_recently_but_superadmin(plugin, superadmin):
    """
    check an immune player who was active 50s ago
    """
    # GIVEN
    now = time()
    superadmin.connects(1)
    plugin.on_client_activity(Event("", None, client=superadmin), now=(now - 50))  # some activity 50s ago
    # WHEN
    plugin.check_client(superadmin)
    # THEN joe is not asked if AFK
    assert not plugin.ask_client.called


def test_not_active_recently_but_bot(plugin, bot):
    """
    check a bot who was active 50s ago
    """
    # GIVEN
    now = time()
    bot.connects(1)
    bot.bot = True
    plugin.on_client_activity(Event("", None, client=bot), now=(now - 50))  # some activity 50s ago
    # WHEN
    plugin.check_client(bot)
    # THEN bot is not asked if AFK
    assert not plugin.ask_client.called

