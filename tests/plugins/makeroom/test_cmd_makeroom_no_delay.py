# -*- encoding: utf-8 -*-
import time
import pytest
from textwrap import dedent
from tests.plugins.makeroom import *
from mock import Mock


t = int(time.time())


@pytest.fixture
def plugin(console):
    p = plugin_maker_ini(console, dedent("""
        [global_settings]
        non_member_level: 2
        delay: 0
        [commands]
        makeroom-mr: 20
    """))
    return p


def test_no_player_to_kick(plugin, superadmin):
    # GIVEN
    superadmin.connects(0)
    # WHEN
    superadmin.says('!makeroom')
    # THEN
    assert ['No non-member found to kick !'] == superadmin.message_history


def test_no_non_member_to_kick(plugin, superadmin, moderator):
    # GIVEN
    superadmin.connects(0)
    moderator.connects(1)
    # WHEN
    superadmin.says('!makeroom')
    # THEN
    assert ['No non-member found to kick !'] == superadmin.message_history


def test_one_player_to_kick(plugin, superadmin, joe):
    # GIVEN
    superadmin.connects(0)
    joe.connects(1)
    joe.kick = Mock()
    # WHEN
    superadmin.says('!makeroom')
    # THEN
    assert 1 == joe.kick.call_count
    assert ['Joe was kicked to free a slot'] == superadmin.message_history


def test_kick_last_connected_player(plugin, superadmin, joe, jack):
    # GIVEN
    superadmin.connects(0)
    joe.connects(1)
    joe.timeAdd = t
    joe.kick = Mock()
    jack.connects(2)
    jack.timeAdd = t + 1
    jack.kick = Mock()
    # WHEN
    superadmin.says('!makeroom')
    # THEN
    assert 0 == joe.kick.call_count
    assert 1 == jack.kick.call_count
    assert ['Jack was kicked to free a slot'] == superadmin.message_history


def test_kick_player_of_lowest_B3_group(plugin, superadmin, joe, moderator):
    # GIVEN
    superadmin.connects(0)
    joe.connects(1)
    joe.timeAdd = t
    joe.kick = Mock()
    moderator.connects(2)
    moderator.timeAdd = t + 1
    moderator.kick = Mock()
    # WHEN
    superadmin.says('!makeroom')
    # THEN
    assert 1 == joe.kick.call_count
    assert 0 == moderator.kick.call_count
    assert ['Joe was kicked to free a slot'] == superadmin.message_history


def test_makeroom_called_during_retain_free_slot_duration(plugin, superadmin, joe):
    # GIVEN
    plugin._retain_free_duration = 5
    superadmin.connects(0)
    joe.connects(1)
    # WHEN
    superadmin.says('!makeroom')
    time.sleep(.3)
    superadmin.says('!makeroom')
    # THEN
    assert ['Joe was kicked to free a slot. A member has 5s to join the server',
            'There is already a makeroom request in progress. Try again later in 4s'] == superadmin.message_history
