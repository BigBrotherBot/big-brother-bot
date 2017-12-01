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
import time
from tests.plugins.makeroom import *
from mock import Mock
import pytest


fake_time = int(time.time())


def get_fake_time():
    global fake_time
    return fake_time


@pytest.fixture
def plugin(console, monkeypatch):
    p = plugin_maker_ini(console, dedent("""
        [global_settings]
        joe_level: reg
        delay: 0
        retain_free_duration: 10
        [commands]
        makeroom-mr: 20
    """))
    monkeypatch.setattr(time, 'time', get_fake_time)
    return p


def test_kick_non_member_during_retain_free_duration(plugin, superadmin, joe, jack):
    global fake_time
    assert plugin._retain_free_duration == 10
    joe.kick = Mock()
    jack.kick = Mock()
    fake_time += 0  # t0

    # GIVEN superadmin called freed a slot
    superadmin.connects(0)
    joe.connects(1)
    superadmin.says('!makeroom')
    assert joe.kick.call_count == 1

    # WHEN a non-member connects during the retain_free_duration
    fake_time += 1  # t1
    jack.connects(2)
    # THEN he must be kicked
    assert jack.kick.call_count == 1


def test_dont_kick_non_member_after_retain_free_duration(plugin, superadmin, joe, jack):
    global fake_time
    assert plugin._retain_free_duration == 10
    joe.kick = Mock()
    jack.kick = Mock()
    fake_time += 0  # t0

    # GIVEN superadmin called freed a slot
    superadmin.connects(0)
    joe.connects(1)
    superadmin.says('!makeroom')
    assert joe.kick.call_count == 1

    # WHEN a non-member connects after the retain_free_duration
    fake_time += 11  # t11
    jack.connects(2)
    # THEN he must not be kicked
    assert jack.kick.call_count == 0


def test_non_members_can_connect_during_retain_free_duration_if_a_member_joined(plugin, superadmin, moderator, joe, jack):
    global fake_time
    assert plugin._retain_free_duration == 10
    joe.kick = Mock()
    jack.kick = Mock()
    fake_time += 0  # t+0s

    # GIVEN superadmin called freed a slot
    superadmin.connects(0)
    joe.connects(1)
    superadmin.says('!makeroom')
    assert joe.kick.call_count == 1

    # AND a member connects before the end of the retain_free_duration
    fake_time += 1  # t+1s
    moderator.connects(3)

    # THEN a non-member can connect before the end of the retain_free_duration
    fake_time += 1  # t+2s
    jack.connects(4)
    assert jack.kick.call_count == 0


def test_dont_kick_joes_during_retain_free_duration_of_zero(plugin, superadmin, joe, jack):
    global fake_time
    plugin._retain_free_duration = 0
    # define a few aliases
    joe = joe
    joe.kick = Mock()
    jack = jack
    jack.kick = Mock()
    # GIVEN 2 connected players
    fake_time += 0  # t0
    superadmin.connects(0)
    joe.connects(1)
    # WHEN
    superadmin.says('!makeroom')
    # THEN the non-member gets kicked
    assert joe.kick.call_count == 1
    # WHEN a non-member connects
    fake_time += 1  # t1
    jack.connects(2)
    # THEN he must not be kicked
    assert jack.kick.call_count == 0
