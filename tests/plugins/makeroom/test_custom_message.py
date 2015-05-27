# -*- encoding: utf-8 -*-
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

