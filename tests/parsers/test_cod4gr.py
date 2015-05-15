#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2012 Daniele Pantaleone <fenix@bigbrotherbot.net>
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
import unittest2 as unittest

from mock import Mock, patch, ANY
from mockito import mock, when, any as anything
from b3.clients import Client
from b3.config import XmlConfigParser
from b3.fake import FakeClient
from b3.parsers.cod4gr import Cod4grParser

log = logging.getLogger("test")
log.setLevel(logging.INFO)

original_client_auth = Client.auth


def tearDownModule():
    # restore core B3 stuff
    Client.auth = original_client_auth


class Cod4grTestCase(unittest.TestCase):
    """
    Test case that is suitable for testing Cod4gr parser specific features
    """
    @classmethod
    def setUpClass(cls):
        from b3.parsers.q3a.abstractParser import AbstractParser
        from b3.fake import FakeConsole
        AbstractParser.__bases__ = (FakeConsole,)
        # Now parser inheritance hierarchy is :
        # Cod4grParser -> AbstractParser -> FakeConsole -> Parser


    def setUp(self):
        self.parser_conf = XmlConfigParser()
        self.parser_conf.loadFromString("""<configuration>
                <settings name="server">
                    <set name="game_log"/>
                </settings>
            </configuration>""")
        self.console = Cod4grParser(self.parser_conf)
        self.output_mock = mock()

        # simulate game server actions
        def write(*args, **kwargs):
            pretty_args = map(repr, args) + ["%s=%s" % (k, v) for k, v in kwargs.iteritems()]
            log.info("write(%s)" % ', '.join(pretty_args))
            return self.output_mock.write(*args, **kwargs)
        self.console.write = Mock(wraps=write)

        self.player = self.console.clients.newClient(cid="4", guid="theGuid", name="theName", ip="11.22.33.44")


    def tearDown(self):
        if hasattr(self, "parser"):
            del self.parser.clients
            self.parser.working = False


class Test_parser_API(Cod4grTestCase):

    def test_getPlayerList_without_punkbuster(self):
        # GIVEN
        self.console.PunkBuster = None
        when(self.console).write('status', maxRetries=anything()).thenReturn("""
map: mp_backlot
num score ping guid                             name            lastmsg address               qport rate
--- ----- ---- -------------------------------- --------------- ------- --------------------- ----- -----
  0     0    3 GameRanger-Account-ID_0006400896 Ranger^7             50 103.231.162.141:16000  7068 25000
""")
        # WHEN
        rv = self.console.getPlayerList()
        # THEN
        self.assertDictEqual({'slot': '0', 'score': '0', 'ping': '3', 'guid': '0006400896', 'name': 'Ranger^7', 'last': '50', 'ip': '103.231.162.141', 'port': '16000', 'qport': '7068', 'rate': '25000', 'pbid': None}, rv.get("0", {}), rv)