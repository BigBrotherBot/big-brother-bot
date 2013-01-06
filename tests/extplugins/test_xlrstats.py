#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2013 Courgette
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
import logging
import os
from mock import patch
from mockito import when
from b3 import __file__ as b3_module__file__, TEAM_RED, TEAM_BLUE
from b3.config import XmlConfigParser
from b3.extplugins.xlrstats import XlrstatsPlugin, __file__ as xlrstats__file__
from b3.plugins.admin import AdminPlugin
from tests import B3TestCase, logging_disabled
from b3.fake import FakeClient

DEFAULT_XLRSTATS_CONFIG_FILE = os.path.join(os.path.dirname(xlrstats__file__), 'conf/xlrstats.xml')
DEFAULT_ADMIN_CONFIG_FILE = os.path.normpath(os.path.join(os.path.dirname(b3_module__file__), "conf/plugin_admin.xml"))


# Setup the logging level we'd like to be spammed with during the tests
LOGGER = logging.getLogger('output')
LOGGER.setLevel(logging.DEBUG)


class XlrstatsTestCase(B3TestCase):

    def setUp(self):
        """
        This method is called before each test.
        It is meant to set up the SUT (System Under Test) in a manner that will ease the testing of its features.
        """
        with logging_disabled():
            # The B3TestCase class provides us a working B3 environment that does not require any database connexion.
            # The B3 console is then accessible with self.console
            B3TestCase.setUp(self)

            # set additional B3 console stuff that will be used by the XLRstats plugin
            self.console.gameName = "MyGame"
            self.parser_conf._settings.update({'b3': {'time_zone': 'GMT'}})

            # we make our own AdminPlugin and make sure it is the one return in any case
            self.adminPlugin = AdminPlugin(self.console, DEFAULT_ADMIN_CONFIG_FILE)
            when(self.console).getPlugin("admin").thenReturn(self.adminPlugin)
            self.adminPlugin.onLoadConfig()
            self.adminPlugin.onStartup()

            # We need a config for the Xlrstats plugin
            self.conf = XmlConfigParser()  # It is an empty config but we can fill it up later

            # Now we create an instance of the SUT (System Under Test) which is the XlrstatsPlugin
            self.p = XlrstatsPlugin(self.console, self.conf)

            # create a client object to represent the game server
            with patch("b3.clients.Clients.authorizeClients"):  # we patch authorizeClients or it will spawn a thread
                # with a 5 second timer
                self.console.clients.newClient(-1, name="WORLD", guid="WORLD", hide=True)


class Test_get_PlayerAnon(XlrstatsTestCase):

    def setUp(self):
        with logging_disabled():
            XlrstatsTestCase.setUp(self)
            self.conf.load(DEFAULT_XLRSTATS_CONFIG_FILE)
            self.p.onLoadConfig()
            self.p.onStartup()

    def test(self):
        # WHEN
        s = self.p.get_PlayerAnon()
        # THEN
        self.assertIsNotNone(s)
        self.assertEqual(self.p._world_clientid, s.client_id)
        self.assertEqual(0, s.kills)
        self.assertEqual(0, s.deaths)
        self.assertEqual(0, s.teamkills)
        self.assertEqual(0, s.teamdeaths)
        self.assertEqual(0, s.suicides)
        self.assertEqual(0, s.ratio)
        self.assertEqual(1000, s.skill)
        self.assertEqual(0, s.assists)
        self.assertEqual(0, s.assistskill)
        self.assertEqual(0, s.curstreak)
        self.assertEqual(0, s.winstreak)
        self.assertEqual(0, s.losestreak)
        self.assertEqual(0, s.rounds)
        self.assertEqual(0, s.hide)

