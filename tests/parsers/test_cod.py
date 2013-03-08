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
from b3.parsers.cod import CodParser

log = logging.getLogger("test")
log.setLevel(logging.INFO)


class CodTestCase(unittest.TestCase):
    """
    Test case that is suitable for testing Cod parser specific features
    """

    @classmethod
    def setUpClass(cls):
        from b3.parsers.q3a.abstractParser import AbstractParser
        from b3.fake import FakeConsole
        AbstractParser.__bases__ = (FakeConsole,)
        # Now parser inheritance hierarchy is :
        # CodParser -> AbstractParser -> FakeConsole -> Parser

        logging.getLogger('output').setLevel(logging.ERROR)

    def setUp(self):
        self.parser_conf = XmlConfigParser()
        self.parser_conf.loadFromString("""<configuration>
                <settings name="server">
                    <set name="game_log"/>
                </settings>
            </configuration>""")
        self.console = CodParser(self.parser_conf)

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




class Test_parser_API(CodTestCase):

    def test_getPlayerList_without_punkbuster(self):
        # GIVEN
        self.console.PunkBuster = None
        when(self.console).write('status', maxRetries=anything()).thenReturn('''\
map: mp_villa
num score ping guid   name            lastmsg address               qport rate
--- ----- ---- ---------- --------------- ------- --------------------- ------ -----
  0     0    0      0 democlient^7         1650 unknown                 1773  5000
  1     0   55 63281996 BandAid^7              50 11.11.11.11:524        8045 25000
  2     0  157 81554346 hugobongenhielm^7      50 11.11.11.11:524    22481 25000
  3     0  156 86330555 Irish^7                 0 11.11.11.11:9162     14288 25000
  4     0  999 68003079 Ashhole^7             750 11.11.11.11:19978 19033 25000
  5     5   53 318670 bigredtwit^7            011.11.11.11:28966     1259 25000
''')
        # WHEN
        rv = self.console.getPlayerList()
        # THEN
        self.assertDictContainsSubset({
            'slot': '1', 'score': '0', 'ping': '55', 'guid': '63281996', 'name': 'BandAid^7', 'last': '50', 'ip': '11.11.11.11', 'pbid': None
        }, rv.get('1', {}), rv)
        self.assertDictContainsSubset({
            'slot': '2', 'score': '0', 'ping': '157', 'guid': '81554346', 'name': 'hugobongenhielm^7', 'last': '50', 'ip': '11.11.11.11', 'pbid': None
        }, rv.get('2', {}), rv)
        self.assertDictContainsSubset({
            'slot': '3', 'score': '0', 'ping': '156', 'guid': '86330555', 'name': 'Irish^7', 'last': '0', 'ip': '11.11.11.11', 'pbid': None
        }, rv.get('3', {}), rv)
        self.assertDictContainsSubset({
            'slot': '4', 'score': '0', 'ping': '999', 'guid': '68003079', 'name': 'Ashhole^7', 'last': '750', 'ip': '11.11.11.11', 'pbid': None
        }, rv.get('4', {}), rv)
        self.assertDictContainsSubset({
            'slot': '5', 'score': '5', 'ping': '53', 'guid': '318670', 'name': 'bigredtwit^7', 'last': '0', 'ip': '11.11.11.11', 'pbid': None
        }, rv.get('5', {}), rv)

