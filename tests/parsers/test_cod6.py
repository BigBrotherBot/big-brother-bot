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
from b3.parsers.cod6 import Cod6Parser

log = logging.getLogger("test")
log.setLevel(logging.INFO)


class Cod6TestCase(unittest.TestCase):
    """
    Test case that is suitable for testing Cod6 parser specific features
    """

    @classmethod
    def setUpClass(cls):
        from b3.parsers.q3a.abstractParser import AbstractParser
        from b3.fake import FakeConsole
        AbstractParser.__bases__ = (FakeConsole,)
        # Now parser inheritance hierarchy is :
        # Cod6Parser -> AbstractParser -> FakeConsole -> Parser

        logging.getLogger('output').setLevel(logging.ERROR)

    def setUp(self):
        self.parser_conf = XmlConfigParser()
        self.parser_conf.loadFromString("""<configuration>
                <settings name="server">
                    <set name="game_log"/>
                </settings>
            </configuration>""")
        self.console = Cod6Parser(self.parser_conf)

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




class Test_parser_API(Cod6TestCase):

    def test_getPlayerList_without_punkbuster(self):
        # GIVEN
        self.console.PunkBuster = None
        when(self.console).write('status', maxRetries=anything()).thenReturn('''\
map: mp_highrise
num score ping guid                             name            lastmsg address               qport rate
--- ----- ---- -------------------------------- --------------- ------- --------------------- ----- -----
  0     1   69                 011000010002d113 Minikruku!^7            0 11.11.11.11:16864    20125 25000
  1     1  101                 011000010002caf1 GuMaK111^7             50 11.11.11.11:4294934838  690 25000
  2     1  175                 0110000100003fb4 phantom1151^7           0 11.11.11.11:28960    10929 25000
  3     1   49                 011000010003ed88 isidora10^7             0 11.11.11.11:429496262727388 25000
  4     1   31                 011000018e87f252 [^5RnK^0] ^4B^7              50 11.11.11.11:28960  26213 25000
''')
        # WHEN
        rv = self.console.getPlayerList()
        # THEN
        self.assertDictContainsSubset({
            'slot': '0', 'score': '1', 'ping': '69', 'guid': '011000010002d113', 'name': 'Minikruku!^7', 'last': '0', 'ip': '11.11.11.11', 'pbid': None
        }, rv.get('0', {}))
        self.assertDictContainsSubset({
            'slot': '1', 'score': '1', 'ping': '101', 'guid': '011000010002caf1', 'name': 'GuMaK111^7', 'last': '50', 'ip': '11.11.11.11', 'pbid': None
        }, rv.get('1', {}))
        self.assertDictContainsSubset({
            'slot': '2', 'score': '1', 'ping': '175', 'guid': '0110000100003fb4', 'name': 'phantom1151^7', 'last': '0', 'ip': '11.11.11.11', 'pbid': None
        }, rv.get('2', {}))
        self.assertDictContainsSubset({
            'slot': '3', 'score': '1', 'ping': '49', 'guid': '011000010003ed88', 'name': 'isidora10^7', 'last': '0', 'ip': '11.11.11.11', 'pbid': None
        }, rv.get('3', {}))
        self.assertDictContainsSubset({
            'slot': '4', 'score': '1', 'ping': '31', 'guid': '011000018e87f252', 'name': '[^5RnK^0] ^4B^7', 'last': '50', 'ip': '11.11.11.11', 'pbid': None
        }, rv.get('4', {}))
