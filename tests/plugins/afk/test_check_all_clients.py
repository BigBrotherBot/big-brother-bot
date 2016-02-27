# -*- encoding: utf-8 -*-
from time import time
from textwrap import dedent
from tests.plugins.afk import *
from mock import call, Mock

# This test suite makes sure `check_all_clients` is called appropriately
from b3.fake import FakeClient


def a_long_time_ago():
    return time() - 40


def fakeclient_repr(self):
    return self.name
FakeClient.__repr__ = fakeclient_repr


@pytest.yield_fixture
def plugin(console):
    p = plugin_maker_ini(console, dedent("""
        [settings]
        inactivity_threshold: 30s
    """))
    p.last_global_check_time = a_long_time_ago()
    p.check_client = Mock()
    p.onLoadConfig()
    p.onStartup()
    yield p
    p.disable()


def test_someone_saying_afk_triggers_check(plugin, bot, joe, jack):
    # GIVEN
    bot.connects(1)
    joe.connects(2)
    jack.connects(3)
    bot.last_activity_time = a_long_time_ago()
    joe.last_activity_time = a_long_time_ago()
    jack.last_activity_time = a_long_time_ago()
    # WHEN
    jack.says("Joe is afk!!!")
    # THEN
    assert [call(joe), call(jack)] == plugin.check_client.mock_calls


def test_do_not_check_all_players_too_often(plugin, joe):
    # GIVEN
    now = time()
    joe.connects(2)
    # WHEN
    plugin.check_all_clients(now=now)
    # THEN
    assert [call(joe)] == plugin.check_client.mock_calls
    # WHEN
    plugin.check_all_clients(now=now + 10)
    # THEN
    assert [call(joe)] == plugin.check_client.mock_calls
    # WHEN
    plugin.check_all_clients(now=now + 16)
    # THEN
    assert [call(joe), call(joe)] == plugin.check_client.mock_calls
