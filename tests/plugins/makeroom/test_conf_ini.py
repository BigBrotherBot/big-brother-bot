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

import os
import pytest
from textwrap import dedent
from tests.plugins.makeroom import *


@pytest.mark.skipif(not os.path.exists(DEFAULT_PLUGIN_CONFIG_FILE), reason="Could not find default plugin config file %r" % DEFAULT_PLUGIN_CONFIG_FILE)
def test_default_conf(console):
    plugin = plugin_maker(console,  DEFAULT_PLUGIN_CONFIG_FILE)
    # [global_settings]
    assert 2 == plugin._non_member_level
    assert 2.0 == plugin._delay
    assert 15 == plugin._retain_free_duration
    # [automation]
    assert False is plugin._automation_enabled
    assert 32 is plugin._total_slots
    assert 1 is plugin._min_free_slots
    # [messages]
    assert plugin.config.get('messages', 'kick_message') == 'kicking $clientname to free a slot'
    assert plugin.config.get('messages', 'kick_reason') == 'to make room for a server member'
    assert plugin.config.get('messages', 'info_message') == 'Making room for clan member, please come back again'
    # [commands]
    admin_plugin = console.getPlugin('admin')
    assert 'makeroom' in admin_plugin._commands
    assert admin_plugin._commands['makeroom'].level == (20, 100)
    assert 'mkr' in admin_plugin._commands
    assert admin_plugin._commands['mkr'].level == (20, 100)
    assert 'makeroomauto' in admin_plugin._commands
    assert admin_plugin._commands['makeroomauto'].level == (60, 100)
    assert 'mrauto' in admin_plugin._commands
    assert admin_plugin._commands['mrauto'].level == (60, 100)


def test_empty_conf(console):
    plugin = plugin_maker_ini(console,  dedent(""""""))
    assert 2 == plugin._non_member_level
    assert 5.0 == plugin._delay
    assert None is plugin._automation_enabled
    assert None is plugin._total_slots
    assert None is plugin._min_free_slots


def test_non_member_level(console):
    plugin = plugin_maker_ini(console, dedent("""
        [global_settings]
        non_member_level: 20
        """))
    assert 20 == plugin._non_member_level


def test_non_member_level_with_group_names(console):
    plugin = plugin_maker_ini(console, dedent("""
        [global_settings]
        non_member_level: mod
        """))
    assert 20 == plugin._non_member_level


def test_delay(console):
    plugin = plugin_maker_ini(console, dedent("""
        [global_settings]
        delay: 20
        """))
    assert 20 == plugin._delay


def test_automation_missing_enabled(console):
    plugin = plugin_maker_ini(console, dedent("""
        [automation]
        total_slots: 5
        min_free_slots: 1
        """))
    assert None is plugin._automation_enabled


def test_automation_junk_enabled(console):
    plugin = plugin_maker_ini(console, dedent("""
        [automation]
        enabled: f00
        """))
    assert None is plugin._automation_enabled


def test_automation_off(console):
    plugin = plugin_maker_ini(console, dedent("""
        [automation]
        enabled: no
        total_slots: 5
        min_free_slots: 1
        """))
    assert False is plugin._automation_enabled


def test_automation_on(console):
    plugin = plugin_maker_ini(console, dedent("""
        [automation]
        enabled: yes
        total_slots: 5
        min_free_slots: 1
        """))
    assert True is plugin._automation_enabled


def test_automation_total_slots(console):
    plugin = plugin_maker_ini(console, dedent("""
        [automation]
        enabled: yes
        total_slots: 6
        min_free_slots: 1
        """))
    assert 6 == plugin._total_slots


def test_automation_min_free_slots(console):
    plugin = plugin_maker_ini(console, dedent("""
        [automation]
        enabled: yes
        total_slots: 6
        min_free_slots: 3
        """))
    assert 3 == plugin._min_free_slots


def test_automation_min_free_slots_junk(console):
    plugin = plugin_maker_ini(console, dedent("""
        [automation]
        enabled: yes
        total_slots: 6
        min_free_slots: f00
        """))
    assert None is plugin._automation_enabled


def test_automation_min_free_slots_negative(console):
    plugin = plugin_maker_ini(console, dedent("""
        [automation]
        enabled: yes
        total_slots: 6
        min_free_slots: -5
        """))
    assert None is plugin._automation_enabled


def test_automation_min_free_slots_higher_than_total_slots(console):
    plugin = plugin_maker_ini(console, dedent("""
        [automation]
        enabled: yes
        total_slots: 6
        min_free_slots: 7
        """))
    assert None is plugin._automation_enabled


def test_automation_total_slots_cannot_be_less_than_2(console):
    plugin = plugin_maker_ini(console, dedent("""
        [automation]
        enabled: yes
        total_slots: 1
        min_free_slots: 1
        """))
    assert None is plugin._automation_enabled


def test_retain_free_duration(console):
    plugin = plugin_maker_ini(console, dedent("""
        [global_settings]
        retain_free_duration: 20
        """))
    assert 20 == plugin._retain_free_duration


def test_retain_free_duration_junk(console):
    plugin = plugin_maker_ini(console, dedent("""
        [global_settings]
        retain_free_duration: f00
        """))
    assert 0 is plugin._retain_free_duration


def test_retain_free_duration_negative(console):
    plugin = plugin_maker_ini(console, dedent("""
        [global_settings]
        retain_free_duration: -5
        """))
    assert 0 is plugin._retain_free_duration


def test_retain_free_duration_zero(console):
    plugin = plugin_maker_ini(console, dedent("""
        [global_settings]
        retain_free_duration: 0
        """))
    assert 0 is plugin._retain_free_duration


def test_retain_free_duration_too_high(console):
    plugin = plugin_maker_ini(console, dedent("""
        [global_settings]
        retain_free_duration: 40
        """))
    assert 30 == plugin._retain_free_duration