# -*- encoding: utf-8 -*-
import time
import pytest
from textwrap import dedent
from tests.plugins.makeroom import *
from mock import call, Mock


@pytest.fixture
def plugin(console):
    p = plugin_maker_ini(console, dedent("""
        [commands]
        makeroomauto-mrauto: 20
        [automation]
        enabled: no
        total_slots: 3
        min_free_slots: 1
    """))
    p._delay = 0
    return p


def test_kick_last_connected_non_member_when_on(plugin, superadmin, joe, moderator):
    # GIVEN
    plugin._automation_enabled = True
    plugin._total_slots = 3
    plugin._min_free_slots = 1
    joe.kick = Mock()
    moderator.kick = Mock()
    # WHEN
    superadmin.connects(0)
    joe.connects(1)
    moderator.connects(2)
    # THEN
    assert [] == moderator.kick.mock_calls
    assert [call(admin=None, reason='to free a slot', silent=True, keyword='makeroom')] == joe.kick.mock_calls


def test_kick_non_member_when_on(plugin, superadmin, joe):
    # GIVEN
    plugin._automation_enabled = True
    plugin._total_slots = 2
    plugin._min_free_slots = 1
    joe.kick = Mock()
    # WHEN
    superadmin.connects(0)
    joe.connects(1)
    # THEN
    assert [call(reason='to free a slot', silent=True, keyword='makeroom')] == joe.kick.mock_calls


def test_kick_non_member_when_on_with_delay(plugin, superadmin, joe):
    # GIVEN
    plugin._automation_enabled = True
    plugin._total_slots = 2
    plugin._min_free_slots = 1
    plugin._delay = .1
    joe.kick = Mock()
    # WHEN
    superadmin.connects(0)
    joe.connects(1)
    # THEN
    time.sleep(.2)
    assert [call(reason='to free a slot', silent=True, keyword='makeroom')] == joe.kick.mock_calls


def test_no_kick_non_member_when_on_and_enough_free_slots(plugin, superadmin, joe):
    # GIVEN
    plugin._automation_enabled = True
    plugin._total_slots = 3
    plugin._min_free_slots = 1
    joe.kick = Mock()
    # WHEN
    superadmin.connects(0)
    joe.connects(1)
    # THEN
    assert [] == joe.kick.mock_calls


def test_no_kick_member_when_off(plugin, superadmin, joe):
    # GIVEN
    plugin._automation_enabled = False
    plugin._total_slots = 2
    plugin._min_free_slots = 1
    joe._groupBits = 8
    joe.kick = Mock()
    # WHEN
    superadmin.connects(0)
    joe.connects(1)
    # THEN
    assert [] == joe.kick.mock_calls


def test_no_kick_non_member_when_off(plugin, superadmin, joe):
    # GIVEN
    plugin._automation_enabled = False
    plugin._total_slots = 2
    plugin._min_free_slots = 1
    joe.kick = Mock()
    # WHEN
    superadmin.connects(0)
    joe.connects(1)
    # THEN
    assert [] == joe.kick.mock_calls
