# -*- encoding: utf-8 -*-
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

