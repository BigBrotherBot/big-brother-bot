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

import pytest
from mock import call, Mock
from tests.plugins.makeroom import *


@pytest.fixture
def plugin(console):
    p = plugin_maker_ini(console, dedent("""
        [commands]
        makeroom: 20
        [messages]
        kick_message: kicking $clientname to make room for a member xxxxxxxxxx
        kick_reason: to free a slot ! mlkjmlkj
    """))
    p._delay = 0
    p.console.say = Mock()
    return p


def test_custom_message(plugin, moderator, joe):
    # GIVEN
    moderator.connects('0')
    joe.connects('1')
    joe.kick = Mock()
    # WHEN
    moderator.says('!makeroom')
    # THEN
    assert [call('kicking Joe to make room for a member xxxxxxxxxx')] == plugin.console.say.mock_calls
    assert [call(admin=moderator, reason='to free a slot ! mlkjmlkj', silent=True,
                 keyword='makeroom')] == joe.kick.mock_calls

