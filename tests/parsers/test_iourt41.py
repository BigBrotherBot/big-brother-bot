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
from mockito import mock, when, any, verify
from mock import Mock, patch, ANY
import unittest2 as unittest
from b3.clients import Client
from b3.config import XmlConfigParser
from b3.parsers.iourt41 import Iourt41Parser

log = logging.getLogger("test")
log.setLevel(logging.INFO)

class Iourt41TestCase(unittest.TestCase):
    """
    Test case that is suitable for testing iourt41 parser specific features
    """

    @classmethod
    def setUpClass(cls):
        from b3.parsers.q3a.abstractParser import AbstractParser
        from b3.fake import FakeConsole
        AbstractParser.__bases__ = (FakeConsole,)
        # Now parser inheritance hierarchy is :
        # Iourt41Parser -> AbstractParser -> FakeConsole -> Parser

        logging.getLogger('output').setLevel(logging.ERROR)

    def setUp(self):
        self.parser_conf = XmlConfigParser()
        self.parser_conf.loadFromString("""
                    <configuration>
                    </configuration>
                """)
        self.console = Iourt41Parser(self.parser_conf)
        self.console.PunkBuster = None # no Punkbuster support in that game

        self.output_mock = mock()
        # simulate game server actions
        def write(*args, **kwargs):
            pretty_args = map(repr, args) + ["%s=%s" % (k, v) for k, v in kwargs.iteritems()]
            log.info("write(%s)" % ', '.join(pretty_args))
            return self.output_mock.write(*args, **kwargs)
        self.console.write = write


class Test_parser_API_implementation(Iourt41TestCase):
    """Test case that is responsible for testing all methods of the b3.parser.Parser class API that
    have to override because they have to talk to their targeted game server in their specific way"""

    def test_getPlayerList(self):
        """\
        Query the game server for connected players.
        return a dict having players' id for keys and players' data as another dict for values
        """
        when(self.output_mock).write('status', maxRetries=any()).thenReturn("""\
map: ut4_casa
num score ping name            lastmsg  address              qport rate
--- ----- ---- --------------- ------- --------------------- ----- -----
10     0   13 snowwhite        0       192.168.1.11:51034     9992 15000
12     0   10 superman         0       192.168.1.12:53039     9993 15000
""")
        result = self.console.getPlayerList()
        verify(self.output_mock).write('status', maxRetries=any())
        self.assertDictEqual({'10': {'ip': '192.168.1.11',
                                     'last': '0',
                                     'name': 'snowwhite',
                                     'pbid': None,
                                     'ping': '13',
                                     'port': '51034',
                                     'qport': '9992',
                                     'rate': '15000',
                                     'score': '0',
                                     'slot': '10'},
                              '12': {'ip': '192.168.1.12',
                                     'last': '0',
                                     'name': 'superman',
                                     'pbid': None,
                                     'ping': '10',
                                     'port': '53039',
                                     'qport': '9993',
                                     'rate': '15000',
                                     'score': '0',
                                     'slot': '12'}}
            , result)


    def test_authorizeClients(self):
        """\
        For all connected players, fill the client object with properties allowing to find
        the user in the database (usualy guid, or punkbuster id, ip) and call the
        Client.auth() method
        """
        superman = mock()
        self.console.clients = mock()
        when(self.console.clients).getByCID("12").thenReturn(superman)
        when(self.output_mock).write('status', maxRetries=any()).thenReturn("""\
map: ut4_casa
num score ping name            lastmsg  address              qport rate
--- ----- ---- --------------- ------- --------------------- ----- -----
12     0   10 superman         0       192.168.1.12:53039     9993 15000
""")
        self.console.authorizeClients()
        verify(self.output_mock).write('status', maxRetries=any())
        verify(superman).auth()


    def test_sync(self):
        """\
        For all connected players returned by self.getPlayerList(), get the matching Client
        object from self.clients (with self.clients.getByCID(cid) or similar methods) and
        look for inconsistencies. If required call the client.disconnect() method to remove
        a client from self.clients.
        This is mainly useful for games where clients are identified by the slot number they
        occupy. On map change, a player A on slot 1 can leave making room for player B who
        connects on slot 1.
        """
        self.console.sync()
        verify(self.output_mock).write('status', maxRetries=any())


    def test_say(self):
        """\
        broadcast a message to all players
        """
        self.console.msgPrefix = "B3:"
        self.console.say("something")
        verify(self.output_mock).write('say B3: something')


    def test_saybig(self):
        """\
        broadcast a message to all players in a way that will catch their attention.
        """
        self.console.msgPrefix = "B3:"
        self.console.saybig("something")
        verify(self.output_mock).write('bigtext "B3: something"')


    def test_message(self):
        """\
        display a message to a given player
        """
        superman = Client(console=self.console, cid="11")
        self.console.msgPrefix = "B3:"
        self.console.message(superman, "something")
        verify(self.output_mock).write('tell 11 B3: ^3[pm]^7 something')


    def test_kick(self):
        """\
        kick a given player
        """
        self.console.getMessage = Mock(return_value="")
        superman = mock()
        superman.cid="11"
        self.console.kick(superman)
        verify(self.output_mock).write('clientkick 11')
        verify(superman).disconnect()

    def test_ban(self):
        """\
        ban a given player on the game server and in case of success
        fire the event ('EVT_CLIENT_BAN', data={'reason': reason,
        'admin': admin}, client=target)
        """
        self.console.getMessage = Mock(return_value="")
        superman = mock()
        superman.cid="11"
        self.console.ban(superman)
        verify(self.output_mock).write('addip 11')
        verify(superman).disconnect()


    def test_unban(self):
        """\
        unban a given player on the game server
        """
        superman = mock()
        superman.ip="1.1.3.4"
        self.console.unban(superman)
        verify(self.output_mock, times=5).write('removeip 1.1.3.4')


    def test_tempban(self):
        """\
        tempban a given player on the game server and in case of success
        fire the event ('EVT_CLIENT_BAN_TEMP', data={'reason': reason,
        'duration': duration, 'admin': admin}, client=target)
        """
        self.console.getMessage = Mock(return_value="")
        superman = mock()
        superman.cid="11"
        self.console.tempban(superman)
        verify(self.output_mock).write('clientkick 11')
        verify(superman).disconnect()


    def test_getMap(self):
        """\
        return the current map/level name
        """
        when(self.output_mock).write('status').thenReturn("""\
map: ut4_casa
num score ping name            lastmsg  address              qport rate
--- ----- ---- --------------- ------- --------------------- ----- -----
12     0   10 superman         0       192.168.1.12:53039     9993 15000
""")
        map = self.console.getMap()
        verify(self.output_mock).write('status')
        self.assertEqual("ut4_casa", map)


    def test_getMaps(self):
        """\
        return the available maps/levels name
        """
        when(self.output_mock).write('fdir *.bsp').thenReturn("""\

---------------
maps/ut4_abbey.bsp
maps/ut4_algiers.bsp
maps/ut4_austria.bsp
maps/ut4_casa.bsp
""")
        maps = self.console.getMaps()
        verify(self.output_mock).write('fdir *.bsp')
        self.assertSetEqual(set(['ut4_abbey', 'ut4_algiers', 'ut4_austria', 'ut4_casa']), set(maps))


    def test_rotateMap(self):
        """\
        load the next map/level
        """
        with patch("time.sleep"):
            self.console.rotateMap()
        verify(self.output_mock).write('cyclemap')


    def test_changeMap(self):
        """\
        load a given map/level
        return a list of suggested map names in cases it fails to recognize the map that was provided
        """
        when(self.output_mock).write('fdir *.bsp').thenReturn("""\

---------------
maps/ut4_abbey.bsp
maps/ut4_abbeyctf.bsp
maps/ut4_algiers.bsp
maps/ut4_austria.bsp
maps/ut4_casa.bsp
""")
        with patch("time.sleep"):
            suggestions = self.console.changeMap('algier')
        verify(self.output_mock).write('map ut4_algiers')
        self.assertIsNone(suggestions)

        with patch("time.sleep"):
            suggestions = self.console.changeMap('bey')
        self.assertIsNotNone(suggestions)
        self.assertSetEqual(set(['ut4_abbey', 'ut4_abbeyctf']), set(suggestions))


    def test_getPlayerPings(self):
        """\
        returns a dict having players' id for keys and players' ping for values
        """
        when(self.output_mock).write('status').thenReturn("""\
map: ut4_casa
num score ping name            lastmsg  address              qport rate
--- ----- ---- --------------- ------- --------------------- ----- -----
10     0   13 snowwhite        0       192.168.1.11:51034     9992 15000
12     0  110 superman         0       192.168.1.12:53039     9993 15000
""")
        pings = self.console.getPlayerPings()
        self.assertDictEqual({'10': 13, '12': 110}, pings)


    def test_getPlayerScores(self):
        """\
        returns a dict having players' id for keys and players' scores for values
        """
        when(self.output_mock).write('status').thenReturn("""\
map: ut4_casa
num score ping name            lastmsg  address              qport rate
--- ----- ---- --------------- ------- --------------------- ----- -----
10     5   13 snowwhite        0       192.168.1.11:51034     9992 15000
12    27  110 superman         0       192.168.1.12:53039     9993 15000
""")
        pings = self.console.getPlayerScores()
        self.assertDictEqual({'10': 5, '12': 27}, pings)


    def test_inflictCustomPenalty(self):
        """
        Called if b3.admin.penalizeClient() does not know a given penalty type.
        Overwrite this to add customized penalties for your game like 'slap', 'nuke',
        'mute', 'kill' or anything you want.
        /!\ This method must return True if the penalty was inflicted.
        """
        superman = mock()
        superman.cid="11"
        # slap
        result = self.console.inflictCustomPenalty('slap', superman)
        verify(self.output_mock).write('slap 11')
        self.assertTrue(result)
        # nuke
        result = self.console.inflictCustomPenalty('nuke', superman)
        verify(self.output_mock).write('nuke 11')
        self.assertTrue(result)
        # mute
        result = self.console.inflictCustomPenalty('mute', superman, duration="15s")
        verify(self.output_mock).write('mute 11 15.0')
        self.assertTrue(result)



class Test_OnClientuserinfo(Iourt41TestCase):

    def setUp(self):
        super(Test_OnClientuserinfo, self).setUp()
        self.console.PunkBuster = None

    def test_ioclient(self):
        infoline = r"2 \ip\145.99.135.227:27960\challenge\-232198920\qport\2781\protocol\68\battleye\1\name\[SNT]^1XLR^78or\rate\8000\cg_predictitems\0\snaps\20\model\sarge\headmodel\sarge\team_model\james\team_headmodel\*james\color1\4\color2\5\handicap\100\sex\male\cl_anonymous\0\teamtask\0\cl_guid\58D4069246865BB5A85F20FB60ED6F65"
        self.assertFalse('2' in self.console.clients)
        self.console.OnClientuserinfo(action=None, data=infoline)
        self.assertTrue('2' in self.console.clients)
        client = self.console.clients['2']
        self.assertEqual('145.99.135.227', client.ip)
        self.assertEqual('[SNT]^1XLR^78or^7', client.exactName)
        self.assertEqual('[SNT]XLR8or', client.name)
        self.assertEqual('58D4069246865BB5A85F20FB60ED6F65', client.guid)

    def test_bot(self):
        infoline = r"0 \gear\GMIORAA\team\blue\skill\5.000000\characterfile\bots/ut_chicken_c.c\color\4\sex\male\race\2\snaps\20\rate\25000\name\InviteYourFriends!"
        self.assertFalse('0' in self.console.clients)
        self.console.OnClientuserinfo(action=None, data=infoline)
        self.assertTrue('0' in self.console.clients)
        client = self.console.clients['0']
        self.assertEqual('0.0.0.0', client.ip)
        self.assertEqual('InviteYourFriends!^7', client.exactName)
        self.assertEqual('InviteYourFriends!', client.name)
        self.assertEqual('BOT0', client.guid)


    def test_quake3_client(self):
        infoline = r"2 \ip\145.99.135.227:27960\challenge\-232198920\qport\2781\protocol\68\battleye\1\name\[SNT]^1XLR^78or\rate\8000\cg_predictitems\0\snaps\20\model\sarge\headmodel\sarge\team_model\james\team_headmodel\*james\color1\4\color2\5\handicap\100\sex\male\cl_anonymous\0\teamtask\0"
        self.assertFalse('2' in self.console.clients)
        self.console.OnClientuserinfo(action=None, data=infoline)
        self.assertTrue('2' in self.console.clients)
        client = self.console.clients['2']
        self.assertEqual('145.99.135.227', client.ip)
        self.assertEqual('[SNT]^1XLR^78or^7', client.exactName)
        self.assertEqual('[SNT]XLR8or', client.name)
        self.assertEqual('145.99.135.227', client.guid)




class Test_pluginsStarted(Iourt41TestCase):

    def test_hacker_with_no_ip(self):
        """ see http://forum.bigbrotherbot.net/general-usage-support/iourt41-py-1-11-5-error/msg34328/ """
        when(self.console).write("status", maxRetries=ANY).thenReturn(r"""\
map: ut4_uberjumps_beta3
num score ping name            lastmsg address               qport rate
--- ----- ---- --------------- ------- --------------------- ----- -----
10    -2   53 [PoliSh TeAm] Haxxer^7      0 80.54.100.100:27960      31734 25000""")

        when(self.console).write('dumpuser 10').thenReturn('userinfo\n--------\ngear                FLAATWA\ncl_packetdup        2\nrate                25000\nname                [PoliSh TeAm] Haxxer\nracered             2\nraceblue            2\nut_timenudge        0\ncg_rgb              255 255 0\nfunred              patch,ninja,phat\nfunblue             Diablo\ncg_predictitems     0\ncg_physics          1\ncl_anonymous        0\nsex                 male\nhandicap            100\ncolor2              5\ncolor1              4\nteam_headmodel      *james\nteam_model          james\nheadmodel           sarge\nmodel               sarge\nsnaps               20\nteamtask            0\ncl_guid             4128583FD6F924B081D7E10F39712FBB\nweapmodes           00000110220000020002')

        logging.getLogger('output').setLevel(logging.NOTSET)
        self.console.pluginsStarted()

        verify(self.console, atleast=1).write('status', maxRetries=ANY)
        verify(self.console).write('dumpuser 10')
        self.assertIn('10', self.console.clients)
        client = self.console.clients['10']
        self.assertEqual('[PoliShTeAm]Haxxer', client.name)
        self.assertEqual('[PoliShTeAm]Haxxer^7', client.exactName)
        self.assertEqual('4128583FD6F924B081D7E10F39712FBB', client.guid)
        self.assertEqual('80.54.100.100', client.ip)
