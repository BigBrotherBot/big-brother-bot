# -*- encoding: utf-8 -*-

import logging
import os
import pytest
from mockito import when
from b3 import TEAM_UNKNOWN
from b3.config import XmlConfigParser, CfgConfigParser
from b3.plugins.admin import AdminPlugin
from b3.plugins.makeroom import MakeroomPlugin


DEFAULT_PLUGIN_CONFIG_FILE = os.path.join(os.path.dirname(__file__), '../../../b3/conf/plugin_makeroom.ini')


class logging_disabled(object):
    """
    context manager that temporarily disable logging.

    USAGE:
        with logging_disabled():
            # do stuff
    """
    DISABLED = False

    def __init__(self):
        self.nested = logging_disabled.DISABLED

    def __enter__(self):
        if not self.nested:
            logging.getLogger('output').propagate = False
            logging_disabled.DISABLED = True

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.nested:
            logging.getLogger('output').propagate = True
            logging_disabled.DISABLED = False


@pytest.fixture
def console():
    with logging_disabled():
        from b3.fake import FakeConsole
        fake_console = FakeConsole('@b3/conf/b3.distribution.xml')

    # load the admin plugin
    with logging_disabled():
        admin_plugin = AdminPlugin(fake_console, '@b3/conf/plugin_admin.ini')
        admin_plugin._commands = {}  # work around known bug in the Admin plugin which makes the _command property shared between all instances
        admin_plugin.onStartup()

    # make sure the admin plugin obtained by other plugins is our admin plugin
    when(fake_console).getPlugin('admin').thenReturn(admin_plugin)

    return fake_console


def plugin_maker(console_obj, conf):
    p = MakeroomPlugin(console_obj, conf)
    p.onLoadConfig()
    p.onStartup()
    return p


def plugin_maker_xml(console_obj, conf_content):
    conf = XmlConfigParser()
    conf.loadFromString(conf_content)
    return plugin_maker(console_obj, conf)


def plugin_maker_ini(console_obj, conf_content):
    conf = CfgConfigParser()
    conf.loadFromString(conf_content)
    return plugin_maker(console_obj, conf)


@pytest.fixture
def superadmin(console):
    with logging_disabled():
        from b3.fake import FakeClient
    superadmin = FakeClient(console, name="Superadmin", guid="Superadmin_guid", groupBits=128, team=TEAM_UNKNOWN)
    superadmin.clearMessageHistory()
    return superadmin


@pytest.fixture
def moderator(console):
    with logging_disabled():
        from b3.fake import FakeClient
    moderator = FakeClient(console, name="Moderator", guid="moderator_guid", groupBits=8, team=TEAM_UNKNOWN)
    moderator.clearMessageHistory()
    return moderator


@pytest.fixture
def joe(console):
    with logging_disabled():
        from b3.fake import FakeClient
    joe = FakeClient(console, name="Joe", guid="joe_guid", groupBits=1, team=TEAM_UNKNOWN)
    joe.clearMessageHistory()
    return joe


@pytest.fixture
def jack(console):
    with logging_disabled():
        from b3.fake import FakeClient
    jack = FakeClient(console, name="Jack", guid="jack_guid", groupBits=1, team=TEAM_UNKNOWN)
    jack.clearMessageHistory()
    return jack