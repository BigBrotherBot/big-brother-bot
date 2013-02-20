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
from mock import Mock, patch, call, ANY
from mockito import mock, when, any as anything
import unittest2 as unittest
from b3.config import XmlConfigParser
from b3.fake import FakeClient
from b3.parsers.cod4 import Cod4Parser

log = logging.getLogger("test")
log.setLevel(logging.INFO)


class Cod4TestCase(unittest.TestCase):
    """
    Test case that is suitable for testing Cod4 parser specific features
    """

    @classmethod
    def setUpClass(cls):
        from b3.parsers.q3a.abstractParser import AbstractParser
        from b3.fake import FakeConsole
        AbstractParser.__bases__ = (FakeConsole,)
        # Now parser inheritance hierarchy is :
        # Cod4Parser -> AbstractParser -> FakeConsole -> Parser


    def setUp(self):
        self.parser_conf = XmlConfigParser()
        self.parser_conf.loadFromString("""<configuration>
                <settings name="server">
                    <set name="game_log"/>
                </settings>
            </configuration>""")
        self.console = Cod4Parser(self.parser_conf)

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




class Test_parser_API(Cod4TestCase):

    def test_getPlayerList_without_punkbuster(self):
        # See http://forum.bigbrotherbot.net/general-discussion/%27bug%27-in-cod4parser/msg38165/
        # See http://forum.bigbrotherbot.net/general-usage-support/b3-not-authenticate/msg38262/
        # GIVEN
        self.console.PunkBuster = None
        when(self.console).write('status', maxRetries=anything()).thenReturn('''\
map: mp_backlot
num score ping guid                             name            lastmsg address               qport rate
--- ----- ---- -------------------------------- --------------- ------- --------------------- ----- -----
  0     0   14 1aaaaaaaaaaaaaaaaaaaaaaaaaaaaaab player1^7               0 11.22.33.44:-6187 -1609 25000
  1     0   12 1ccccccccccccccccccccccccccccccc player2^7               0 22.33.44.55:-10803-23569 25000
  3   486  185 ecc77e3400a38cc71b3849207e20e1b0 GO_NINJA^7              0 111.222.111.111:-15535-2655 25000
  5    92  509 0123456789abcdef0123456789abcdef 7ajimaki^7            100 11.222.111.44:28960   -27329 25000
  6     0  206 0123456789a654654646545789abcdef [NRNS]ArmedGuy^7        0 11.22.111.44:28960    -21813 25000
  7    30  229 012343213211313213321313131bcdef Franco^7                0 111.22.111.111:23144  22922 25000
  8     0  110 a630006508000000000000000011d9a2 Badschga2002^7          0 11.11.11.6328960   -21738 25000
''')
        # WHEN
        rv = self.console.getPlayerList()
        # THEN
        self.assertDictEqual({'slot': '0', 'score': '0', 'ping': '14', 'guid': '1aaaaaaaaaaaaaaaaaaaaaaaaaaaaaab', 'name': 'player1^7', 'last': '0', 'ip': '11.22.33.44', 'port': '-6187', 'qport': '-1609', 'rate': '25000', 'pbid': None}, rv.get("0", {}), rv)
        self.assertDictEqual({'slot': '1', 'score': '0', 'ping': '12', 'guid': '1ccccccccccccccccccccccccccccccc', 'name': 'player2^7', 'last': '0', 'ip': '22.33.44.55', 'port': '-10803', 'qport': '-23569', 'rate': '25000', 'pbid': None}, rv.get("1", {}), rv)
        self.assertDictEqual({'slot': '3', 'score': '486', 'ping': '185', 'guid': 'ecc77e3400a38cc71b3849207e20e1b0', 'name': 'GO_NINJA^7', 'last': '0', 'ip': '111.222.111.111', 'port': '-15535', 'qport': '-2655', 'rate': '25000', 'pbid': None}, rv.get("3", {}), rv)
        self.assertDictEqual({'slot': '5', 'score': '92', 'ping': '509', 'guid': '0123456789abcdef0123456789abcdef', 'name': '7ajimaki^7', 'last': '100', 'ip': '11.222.111.44', 'port': '28960', 'qport': '-27329', 'rate': '25000', 'pbid': None}, rv.get("5", {}), rv)
        self.assertDictEqual({'slot': '6', 'score': '0', 'ping': '206', 'guid': '0123456789a654654646545789abcdef', 'name': '[NRNS]ArmedGuy^7', 'last': '0', 'ip': '11.22.111.44', 'port': '28960', 'qport': '-21813', 'rate': '25000', 'pbid': None}, rv.get("6", {}), rv)
        self.assertDictEqual({'slot': '7', 'score': '30', 'ping': '229', 'guid': '012343213211313213321313131bcdef', 'name': 'Franco^7', 'last': '0', 'ip': '111.22.111.111', 'port': '23144', 'qport': '22922', 'rate': '25000', 'pbid': None}, rv.get("7", {}), rv)
        self.assertDictEqual({'slot': '8', 'score': '0', 'ping': '110', 'guid': 'a630006508000000000000000011d9a2', 'name': 'Badschga2002^7', 'last': '0', 'ip': '11.11.11.63', 'port': '28960', 'qport': '-21738', 'rate': '25000', 'pbid': None}, rv.get("8", {}), rv)



class Test_cod4ClientAuthMethod(Cod4TestCase):

    def test_unexpected_exception(self):
        # GIVEN
        when(self.console.storage).getClient(anything()).thenRaise(NotImplementedError())
        joe = FakeClient(console=self.console, name="Joe", guid="joe_guid")
        # WHEN
        with patch.object(self.console, "error") as error_mock:
            joe.auth()
        # THEN
        error_mock.assert_called_with('auth self.console.storage.getClient(client) - Client<@0:joe_guid|:"Joe":None>',
                                   exc_info=ANY)
