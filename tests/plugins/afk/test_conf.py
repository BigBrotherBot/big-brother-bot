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
from tests.plugins.afk import *

DEFAULT_SUSPICION_ANNOUNCEMENT = "{name} suspected of being AFK, kicking in {last_chance_delay}s if no answer"


@pytest.mark.skipif(not os.path.exists(DEFAULT_PLUGIN_CONFIG_FILE), reason="Could not find default plugin config file %r" % DEFAULT_PLUGIN_CONFIG_FILE)
def test_default_conf(console):
    plugin = plugin_maker(console, DEFAULT_PLUGIN_CONFIG_FILE)
    plugin.onLoadConfig()
    assert 1 == plugin.min_ingame_humans
    assert 3 == plugin.consecutive_deaths_threshold
    assert 50 == plugin.inactivity_threshold_second
    assert 20 == plugin.last_chance_delay
    assert "AFK for too long on this server" == plugin.kick_reason
    assert "Are you AFK?" == plugin.are_you_afk
    assert DEFAULT_SUSPICION_ANNOUNCEMENT == plugin.suspicion_announcement


def test_empty_conf(console):
    plugin = plugin_maker_ini(console,  dedent(""""""))
    plugin.onLoadConfig()
    assert 1 == plugin.min_ingame_humans
    assert 3 == plugin.consecutive_deaths_threshold
    assert 50 == plugin.inactivity_threshold_second
    assert 20 == plugin.last_chance_delay
    assert "AFK for too long on this server" == plugin.kick_reason
    assert "Are you AFK?" == plugin.are_you_afk
    assert DEFAULT_SUSPICION_ANNOUNCEMENT == plugin.suspicion_announcement


def test_bad_values(console):
    plugin = plugin_maker_ini(console, dedent("""
        [settings]
        min_ingame_humans: mlkj
        consecutive_deaths_threshold: f00
        inactivity_threshold: bar
        last_chance_delay: f00
        kick_reason:
        are_you_afk:
        suspicion_announcement:
        """))
    plugin.onLoadConfig()
    assert 1 == plugin.min_ingame_humans
    assert 3 == plugin.consecutive_deaths_threshold
    assert 30 == plugin.inactivity_threshold_second
    assert 20 == plugin.last_chance_delay
    assert "AFK for too long on this server" == plugin.kick_reason
    assert "Are you AFK?" == plugin.are_you_afk
    assert DEFAULT_SUSPICION_ANNOUNCEMENT == plugin.suspicion_announcement


def test_min_ingame_humans(console):
    plugin = plugin_maker_ini(console, dedent("""
        [settings]
        min_ingame_humans: 3
        """))
    plugin.onLoadConfig()
    assert 3 == plugin.min_ingame_humans


def test_min_ingame_humans_too_low(console):
    plugin = plugin_maker_ini(console, dedent("""
        [settings]
        min_ingame_humans: -1
        """))
    plugin.onLoadConfig()
    assert 0 == plugin.min_ingame_humans


def test_consecutive_deaths_threshold(console):
    plugin = plugin_maker_ini(console, dedent("""
        [settings]
        consecutive_deaths_threshold: 2
        """))
    plugin.onLoadConfig()
    assert 2 == plugin.consecutive_deaths_threshold


def test_consecutive_deaths_threshold_too_low(console):
    plugin = plugin_maker_ini(console, dedent("""
        [settings]
        consecutive_deaths_threshold: -1
        """))
    plugin.onLoadConfig()
    assert 0 == plugin.consecutive_deaths_threshold


def test_inactivity_threshold_too_low(console):
    plugin = plugin_maker_ini(console, dedent("""
        [settings]
        inactivity_threshold: 5s
        """))
    plugin.onLoadConfig()
    assert 30 == plugin.inactivity_threshold_second


def test_inactivity_threshold_minute(console):
    plugin = plugin_maker_ini(console, dedent("""
        [settings]
        inactivity_threshold: 1m
        """))
    plugin.onLoadConfig()
    assert 60 == plugin.inactivity_threshold_second


def test_last_chance_delay(console):
    plugin = plugin_maker_ini(console, dedent("""
        [settings]
        last_chance_delay: 34
        """))
    plugin.onLoadConfig()
    assert 34 == plugin.last_chance_delay


def test_last_chance_delay_missing(console):
    plugin = plugin_maker_ini(console, dedent("""
        [settings]
        """))
    plugin.onLoadConfig()
    assert 20 == plugin.last_chance_delay


def test_last_chance_delay_empty(console):
    plugin = plugin_maker_ini(console, dedent("""
        [settings]
        last_chance_delay:
        """))
    plugin.onLoadConfig()
    assert 20 == plugin.last_chance_delay


def test_last_chance_delay_bad_value(console):
    plugin = plugin_maker_ini(console, dedent("""
        [settings]
        last_chance_delay: f00
        """))
    plugin.onLoadConfig()
    assert 20 == plugin.last_chance_delay


def test_last_chance_delay_too_low(console):
    plugin = plugin_maker_ini(console, dedent("""
        [settings]
        last_chance_delay: 14
        """))
    plugin.onLoadConfig()
    assert 15 == plugin.last_chance_delay


def test_last_chance_delay_too_high(console):
    plugin = plugin_maker_ini(console, dedent("""
        [settings]
        last_chance_delay: 61
        """))
    plugin.onLoadConfig()
    assert 60 == plugin.last_chance_delay


def test_immunity_level_missing(console):
    plugin = plugin_maker_ini(console, dedent("""
        [settings]
        """))
    plugin.onLoadConfig()
    assert 100 == plugin.immunity_level


def test_immunity_level_bad_value(console):
    plugin = plugin_maker_ini(console, dedent("""
        [settings]
        immunity_level: f00
        """))
    plugin.onLoadConfig()
    assert 100 == plugin.immunity_level


def test_immunity_level_nominal(console):
    plugin = plugin_maker_ini(console, dedent("""
        [settings]
        immunity_level: 40
        """))
    plugin.onLoadConfig()
    assert 40 == plugin.immunity_level


def test_suspicion_announcement(console):
    plugin = plugin_maker_ini(console, dedent("""
        [settings]
        suspicion_announcement: f00 {name} bar {last_chance_delay} foo
        """))
    plugin.onLoadConfig()
    assert "f00 {name} bar {last_chance_delay} foo" == plugin.suspicion_announcement


def test_suspicion_announcement_missing(console):
    plugin = plugin_maker_ini(console, dedent("""
        [settings]
        """))
    plugin.onLoadConfig()
    assert DEFAULT_SUSPICION_ANNOUNCEMENT == plugin.suspicion_announcement


def test_suspicion_announcement_empty(console):
    plugin = plugin_maker_ini(console, dedent("""
        [settings]
        suspicion_announcement:
        """))
    plugin.onLoadConfig()
    assert DEFAULT_SUSPICION_ANNOUNCEMENT == plugin.suspicion_announcement


def test_suspicion_announcement_missing_name(console):
    plugin = plugin_maker_ini(console, dedent("""
        [settings]
        suspicion_announcement: f00 {last_chance_delay}s bar
        """))
    plugin.onLoadConfig()
    assert DEFAULT_SUSPICION_ANNOUNCEMENT == plugin.suspicion_announcement


def test_suspicion_announcement_missing_last_chance_delay(console):
    plugin = plugin_maker_ini(console, dedent("""
        [settings]
        suspicion_announcement: f00 {name}s bar
        """))
    plugin.onLoadConfig()
    assert DEFAULT_SUSPICION_ANNOUNCEMENT == plugin.suspicion_announcement
