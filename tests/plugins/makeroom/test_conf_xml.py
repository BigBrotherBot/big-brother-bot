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

from tests.plugins.makeroom import *


def test_empty_conf(console):
    plugin = plugin_maker_xml(console, "<configuration/>")
    assert 2 == plugin._non_member_level
    assert 5.0 == plugin._delay
    assert None is plugin._automation_enabled
    assert None is plugin._total_slots
    assert None is plugin._min_free_slots


def test_non_member_level(console):
    plugin = plugin_maker_xml(console, """<configuration>
            <settings name="global_settings">
                <set name="non_member_level">20</set>
            </settings>
        </configuration>""")
    assert 20 == plugin._non_member_level


def test_non_member_level_with_group_names(console):
    plugin = plugin_maker_xml(console, """<configuration>
            <settings name="global_settings">
                <set name="non_member_level">mod</set>
            </settings>
        </configuration>""")
    assert 20 == plugin._non_member_level


def test_delay(console):
    plugin = plugin_maker_xml(console, """<configuration>
            <settings name="global_settings">
                <set name="delay">20</set>
            </settings>
        </configuration>""")
    assert 20 == plugin._delay


def test_automation_missing_enabled(console):
    plugin = plugin_maker_xml(console, """<configuration>
            <settings name="automation">
                <set name="total_slots">5</set>
                <set name="min_free_slots">1</set>
            </settings>
        </configuration>""")
    assert None is plugin._automation_enabled


def test_automation_off(console):
    plugin = plugin_maker_xml(console, """<configuration>
            <settings name="automation">
                <set name="enabled">no</set>
                <set name="total_slots">5</set>
                <set name="min_free_slots">1</set>
            </settings>
        </configuration>""")
    assert False is plugin._automation_enabled


def test_automation_on(console):
    plugin = plugin_maker_xml(console, """<configuration>
            <settings name="automation">
                <set name="enabled">yes</set>
                <set name="total_slots">5</set>
                <set name="min_free_slots">1</set>
            </settings>
        </configuration>""")
    assert True is plugin._automation_enabled


def test_automation_total_slots(console):
    plugin = plugin_maker_xml(console, """<configuration>
            <settings name="automation">
                <set name="enabled">yes</set>
                <set name="total_slots">6</set>
                <set name="min_free_slots">1</set>
            </settings>
        </configuration>""")
    assert 6 == plugin._total_slots


def test_automation_min_free_slots(console):
    plugin = plugin_maker_xml(console, """<configuration>
            <settings name="automation">
                <set name="enabled">yes</set>
                <set name="total_slots">6</set>
                <set name="min_free_slots">3</set>
            </settings>
        </configuration>""")
    assert 3 == plugin._min_free_slots


def test_automation_total_slots_cannot_be_less_than_2(console):
    plugin = plugin_maker_xml(console, """<configuration>
            <settings name="automation">
                <set name="enabled">yes</set>
                <set name="total_slots">1</set>
                <set name="min_free_slots">1</set>
            </settings>
        </configuration>""")
    assert None is plugin._automation_enabled
