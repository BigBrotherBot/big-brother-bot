#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2012 Courgette
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
from mock import Mock
from mockito import mock, when, any as anything
import unittest2 as unittest
from b3.config import XmlConfigParser
from b3.parsers.cod7 import Cod7Parser

log = logging.getLogger("test")
log.setLevel(logging.INFO)


class Cod7TestCase(unittest.TestCase):
    """
    Test case that is suitable for testing Cod7 parser specific features
    """

    @classmethod
    def setUpClass(cls):
        from b3.parsers.q3a.abstractParser import AbstractParser
        from b3.fake import FakeConsole
        AbstractParser.__bases__ = (FakeConsole,)
        # Now parser inheritance hierarchy is :
        # Cod5Parser -> AbstractParser -> FakeConsole -> Parser

        logging.getLogger('output').setLevel(logging.ERROR)

    def setUp(self):
        self.parser_conf = XmlConfigParser()
        self.parser_conf.loadFromString("""<configuration>
                <settings name="server">
                    <set name="game_log"/>
                </settings>
            </configuration>""")
        self.console = Cod7Parser(self.parser_conf)

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




class Test_parser_API(Cod7TestCase):

    def test_getPlayerList_without_punkbuster(self):
        # GIVEN
        self.console.PunkBuster = None
        when(self.console).write('status', maxRetries=anything()).thenReturn('''\
map: mp_stadium
num score ping guid   name            lastmsg address               qport rate
--- ----- ---- ---------- --------------- ------- --------------------- ------ -----
  0     0    0      0 democlient^7       362150 unknown                 1773  5000
  1   200   47 8326146 ShaGGyTuBBs^7           0 11.11.11.11:524       16783 25000
  2  1360   61 56089378 fresh breeze^7          0 11.11.11.11:-27409   -7422 25000
  3   470   97 69406003 kossi__86^7             0 11.11.11.11:524      -24017 25000
''')
        # WHEN
        rv = self.console.getPlayerList()
        # THEN
        self.assertNotIn("0", rv)
        self.assertDictContainsSubset({'slot': '1', 'score': '200', 'ping': '47', 'guid': '8326146', 'name': 'ShaGGyTuBBs^7', 'last': '0', 'ip': '11.11.11.11', 'port': '524', 'qport': '16783', 'rate': '25000', 'pbid': None}, rv.get("1", {}))
        self.assertDictContainsSubset({'slot': '2', 'score': '1360', 'ping': '61', 'guid': '56089378', 'name': 'fresh breeze^7', 'last': '0', 'ip': '11.11.11.11', 'port': '-27409', 'qport': '7422', 'rate': '25000', 'pbid': None}, rv.get("2", {}))
        self.assertDictContainsSubset({'slot': '3', 'score': '470', 'ping': '97', 'guid': '69406003', 'name': 'kossi__86^7', 'last': '0', 'ip': '11.11.11.11', 'port': '524', 'qport': '24017', 'rate': '25000', 'pbid': None}, rv.get("3", {}))

