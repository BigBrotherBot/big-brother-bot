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
from b3.parsers.cod5 import Cod5Parser

log = logging.getLogger("test")
log.setLevel(logging.INFO)


class Cod5TestCase(unittest.TestCase):
    """
    Test case that is suitable for testing Cod5 parser specific features
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
        self.console = Cod5Parser(self.parser_conf)

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




class Test_parser_API(Cod5TestCase):

    def test_getPlayerList_without_punkbuster(self):
        # GIVEN
        self.console.PunkBuster = None
        when(self.console).write('status', maxRetries=anything()).thenReturn('''\
map: mp_gits_tanks
num score ping guid       name            lastmsg address               qport  rate
--- ----- ---- ---------- --------------- ------- --------------------- ------ -----
  0     0  349 784729936 BagpipeHero^7          50 11.11.11.11:28960   7309 25000
  1     0  999 680213351 US_Wannabe^7          750 11.11.11.11:28960   -13830 25000
  2  1230  159 1689890858 2cool4yaD^7             0 11.11.11.11:-9427     31128 25000
  3  1520  163 763506664 SestaPT^7               0 11.11.11.11:28960   -9436 25000
  4   410  129 281198399 xRedoxX^7               0 11.11.11.11:29195    -28834 25000
  5     0  999 1359560555 MikeIsDaBomb^7          0 11.11.11.11:28960   -20411 25000
''')
        # WHEN
        rv = self.console.getPlayerList()
        # THEN
        self.assertDictEqual({'slot': '0', 'score': '0', 'ping': '349', 'guid': '784729936', 'name': 'BagpipeHero^7', 'last': '50', 'ip': '11.11.11.11', 'port': '28960', 'qport': '7309', 'rate': '25000', 'pbid': None}, rv.get("0", {}))
        self.assertDictEqual({'slot': '1', 'score': '0', 'ping': '999', 'guid': '680213351', 'name': 'US_Wannabe^7', 'last': '750', 'ip': '11.11.11.11', 'port': '28960', 'qport': '-13830', 'rate': '25000', 'pbid': None}, rv.get("1", {}))
        self.assertDictEqual({'slot': '2', 'score': '1230', 'ping': '159', 'guid': '1689890858', 'name': '2cool4yaD^7', 'last': '0', 'ip': '11.11.11.11', 'port': '-9427', 'qport': '31128', 'rate': '25000', 'pbid': None}, rv.get("2", {}))
        self.assertDictEqual({'slot': '3', 'score': '1520', 'ping': '163', 'guid': '763506664', 'name': 'SestaPT^7', 'last': '0', 'ip': '11.11.11.11', 'port': '28960', 'qport': '-9436', 'rate': '25000', 'pbid': None}, rv.get("3", {}))
        self.assertDictEqual({'slot': '4', 'score': '410', 'ping': '129', 'guid': '281198399', 'name': 'xRedoxX^7', 'last': '0', 'ip': '11.11.11.11', 'port': '29195', 'qport': '-28834', 'rate': '25000', 'pbid': None}, rv.get("4", {}))
        self.assertDictEqual({'slot': '5', 'score': '0', 'ping': '999', 'guid': '1359560555', 'name': 'MikeIsDaBomb^7', 'last': '0', 'ip': '11.11.11.11', 'port': '28960', 'qport': '-20411', 'rate': '25000', 'pbid': None}, rv.get("5", {}))

