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
import pytest


@pytest.fixture
def plugin(console):
    p = plugin_maker_xml(console, """
        <configuration>
            <settings name="commands">
                <set name="makeroomauto-mrauto">20</set>
            </settings>
            <settings name="automation">
                <set name="enabled">no</set>
                <set name="total_slots">3</set>
                <set name="min_free_slots">1</set>
            </settings>
        </configuration>
    """)
    p._delay = 0
    return p


def test_no_arg(plugin, superadmin):
    superadmin.connects(0)
    superadmin.says('!makeroomauto')
    assert ["expecting 'on' or 'off'"] == superadmin.message_history


def test_off(plugin, superadmin):
    superadmin.connects(0)
    plugin._automation_enabled = True
    superadmin.says('!makeroomauto off')
    assert False == plugin._automation_enabled
    assert ['Makeroom automation is OFF'] == superadmin.message_history


def test_on(plugin, superadmin):
    superadmin.connects(0)
    superadmin.says('!makeroomauto on')
    assert True == plugin._automation_enabled
    assert ['Makeroom automation is ON'] == superadmin.message_history


def test_junk(plugin, superadmin):
    superadmin.connects(0)
    superadmin.says('!makeroomauto f00')
    assert ["expecting 'on' or 'off'"] == superadmin.message_history

