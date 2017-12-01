# -*- coding: utf-8 -*-

# ################################################################### #
#                                                                     #
#  BigBrotherBot(B3) (www.bigbrotherbot.net)                          #
#  Copyright (C) 2005 Michael "ThorN" Thornton                        #
#                                                                     #
#  This program is free software; you can redistribute it and/or      #
#  modify it under the terms of the GNU General Public License        #
#  as published by the Free Software Foundation; either version 2     #
#  of the License, or (at your option) any later version.             #
#                                                                     #
#  This program is distributed in the hope that it will be useful,    #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of     #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the       #
#  GNU General Public License for more details.                       #
#                                                                     #
#  You should have received a copy of the GNU General Public License  #
#  along with this program; if not, write to the Free Software        #
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA      #
#  02110-1301, USA.                                                   #
#                                                                     #
# ################################################################### #

import b3
import logging
import unittest2 as unittest

from mockito import mock, when, any as anything, verify
from mock import Mock, patch, ANY
from b3.clients import Client
from b3.config import XmlConfigParser
from b3.events import Event
from b3.fake import FakeClient
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

    def setUp(self):
        self.parser_conf = XmlConfigParser()
        self.parser_conf.loadFromString("""<configuration>
                <settings name="server">
                    <set name="game_log"/>
                </settings>
            </configuration>""")
        self.console = Iourt41Parser(self.parser_conf)
        self.console.PunkBuster = None # no Punkbuster support in that game

        self.output_mock = mock()
        # simulate game server actions
        def write(*args, **kwargs):
            pretty_args = map(repr, args) + ["%s=%s" % (k, v) for k, v in kwargs.iteritems()]
            log.info("write(%s)" % ', '.join(pretty_args))
            return self.output_mock.write(*args, **kwargs)
        self.console.write = write

    def tearDown(self):
        if hasattr(self, "parser"):
            del self.parser.clients
            self.parser.working = False

    def assertEvent(self, log_line, event_type, event_client=None, event_data=None, event_target=None):
        with patch.object(self.console, 'queueEvent') as queueEvent:
            self.console.parseLine(log_line)
            if event_type is None:
                assert not queueEvent.called
                return
            assert queueEvent.called, "No event was fired"
            args = queueEvent.call_args

        if type(event_type) is basestring:
            event_type_name = event_type
        else:
            event_type_name = self.console.getEventName(event_type)
            self.assertIsNotNone(event_type_name, "could not find event with name '%s'" % event_type)

        eventraised = args[0][0]
        self.assertIsInstance(eventraised, Event)
        self.assertEquals(self.console.getEventName(eventraised.type), event_type_name)
        self.assertEquals(eventraised.data, event_data)
        self.assertEquals(eventraised.target, event_target)
        self.assertEquals(eventraised.client, event_client)


class Test_parser_API_implementation(Iourt41TestCase):
    """Test case that is responsible for testing all methods of the b3.parser.Parser class API that
    have to override because they have to talk to their targeted game server in their specific way"""

    def test_getPlayerList(self):
        """
        Query the game server for connected players.
        return a dict having players' id for keys and players' data as another dict for values
        """
        when(self.output_mock).write('status', maxRetries=anything()).thenReturn("""
map: ut4_casa
num score ping name            lastmsg  address              qport rate
--- ----- ---- --------------- ------- --------------------- ----- -----
10     0   13 snowwhite        0       192.168.1.11:51034     9992 15000
12     0   10 superman         0       192.168.1.12:53039     9993 15000
""")
        result = self.console.getPlayerList()
        verify(self.output_mock).write('status', maxRetries=anything())
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
        """
        For all connected players, fill the client object with properties allowing to find
        the user in the database (usualy guid, or punkbuster id, ip) and call the
        Client.auth() method
        """
        superman = mock()
        self.console.clients = mock()
        when(self.console.clients).getByCID("12").thenReturn(superman)
        when(self.output_mock).write('status', maxRetries=anything()).thenReturn("""
map: ut4_casa
num score ping name            lastmsg  address              qport rate
--- ----- ---- --------------- ------- --------------------- ----- -----
12     0   10 superman         0       192.168.1.12:53039     9993 15000
""")
        self.console.authorizeClients()
        verify(self.output_mock).write('status', maxRetries=anything())
        verify(superman).auth()


    def test_sync(self):
        """
        For all connected players returned by self.getPlayerList(), get the matching Client
        object from self.clients (with self.clients.getByCID(cid) or similar methods) and
        look for inconsistencies. If required call the client.disconnect() method to remove
        a client from self.clients.
        This is mainly useful for games where clients are identified by the slot number they
        occupy. On map change, a player A on slot 1 can leave making room for player B who
        connects on slot 1.
        """
        self.console.sync()
        verify(self.output_mock).write('status', maxRetries=anything())

    def test_say(self):
        """
        broadcast a message to all players
        """
        self.console.msgPrefix = "B3:"
        self.console.say("something")
        verify(self.output_mock).write('say B3: something')

    def test_saybig(self):
        """
        broadcast a message to all players in a way that will catch their attention.
        """
        self.console.msgPrefix = "B3:"
        self.console.saybig("something")
        verify(self.output_mock).write('bigtext "B3: something"')


    def test_message(self):
        """
        display a message to a given player
        """
        superman = Client(console=self.console, cid="11")
        self.console.msgPrefix = "B3:"
        self.console.message(superman, "something")
        verify(self.output_mock).write('tell 11 B3: ^8[pm]^7 something')

    def test_kick(self):
        """
        kick a given player
        """
        self.console.getMessage = Mock(return_value="")
        superman = mock()
        superman.cid="11"
        self.console.kick(superman)
        verify(self.output_mock).write('clientkick 11')
        verify(superman).disconnect()

    def test_ban(self):
        """
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
        """
        unban a given player on the game server
        """
        superman = mock()
        superman.ip="1.1.3.4"
        self.console.unban(superman)
        verify(self.output_mock, times=5).write('removeip 1.1.3.4')

    def test_tempban(self):
        """
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
        """
        return the current map/level name
        """
        when(self.output_mock).write('status').thenReturn("""\
map: ut4_casa
num score ping name            lastmsg  address              qport rate
--- ----- ---- --------------- ------- --------------------- ----- -----
12     0   10 superman         0       192.168.1.12:53039     9993 15000
""")
        m = self.console.getMap()
        verify(self.output_mock).write('status')
        self.assertEqual("ut4_casa", m)

    def test_getMaps(self):
        """
        return the available maps/levels name
        """
        when(self.output_mock).write('fdir *.bsp', socketTimeout=anything()).thenReturn("""\

---------------
maps/ut4_abbey.bsp
maps/ut4_algiers.bsp
maps/ut4_austria.bsp
maps/ut4_casa.bsp
""")
        maps = self.console.getMaps()
        verify(self.output_mock).write('fdir *.bsp', socketTimeout=anything())
        self.assertSetEqual({'ut4_abbey', 'ut4_algiers', 'ut4_austria', 'ut4_casa'}, set(maps))

    def test_rotateMap(self):
        """
        load the next map/level
        """
        with patch("time.sleep"):
            self.console.rotateMap()
        verify(self.output_mock).write('cyclemap')

    @patch("time.sleep")
    def test_changeMap(self, sleep_mock):
        """
        load a given map/level
        return a list of suggested map names in cases it fails to recognize the map that was provided
        """
        when(self.output_mock).write('fdir *.bsp', socketTimeout=anything()).thenReturn("""\

---------------
maps/ut4_abbey.bsp
maps/ut4_abbeyctf.bsp
maps/ut4_algiers.bsp
maps/ut4_austria.bsp
maps/ut4_casa.bsp
""")
        suggestions = self.console.changeMap('algier')
        self.assertIsNone(suggestions)
        verify(self.output_mock).write('map ut4_algiers')

        suggestions = self.console.changeMap('bey')
        self.assertIsNotNone(suggestions)
        self.assertSetEqual({'ut4_abbey', 'ut4_abbeyctf'}, set(suggestions))


    @patch("time.sleep")
    def test_changeMap_2(self, sleep_mock):
        """
        see http://forum.bigbrotherbot.net/urt/!map-x-bug/msg37759/#msg37759
        """
        when(self.output_mock).write('fdir *.bsp', socketTimeout=anything()).thenReturn("""\
---------------
maps/ut4_abbey.bsp
maps/ut4_abbeyctf.bsp
maps/ut4_algiers.bsp
maps/ut4_ambush.bsp
maps/ut4_area3_b4.bsp
maps/ut4_asylum_b1.bsp
maps/ut4_austria.bsp
maps/ut4_aztek_b2.bsp
maps/ut4_baeza.bsp
maps/ut4_beijing_b3.bsp
maps/ut4_blackhawk.bsp
maps/ut4_blitzkrieg.bsp
maps/ut4_boxtrot_x6.bsp
maps/ut4_cambridge_b1.bsp
maps/ut4_cambridge_fixed.bsp
maps/ut4_casa.bsp
maps/ut4_commune.bsp
maps/ut4_company.bsp
maps/ut4_crossing.bsp
maps/ut4_deception_v2.bsp
maps/ut4_desolate_rc1.bsp
maps/ut4_docks.bsp
maps/ut4_dressingroom.bsp
maps/ut4_druglord2.bsp
maps/ut4_dust2_v2.bsp
maps/ut4_dust2_v3b.bsp
maps/ut4_eagle.bsp
maps/ut4_eezabad.bsp
maps/ut4_elgin.bsp
maps/ut4_exhibition_a24.bsp
maps/ut4_facade_b5.bsp
maps/ut4_ferguson_b12.bsp
maps/ut4_firingrange.bsp
maps/ut4_granja.bsp
maps/ut4_guerrilla.bsp
maps/ut4_harbortown.bsp
maps/ut4_heroic_beta1.bsp
maps/ut4_herring.bsp
maps/ut4_horror.bsp
maps/ut4_kingdom.bsp
maps/ut4_kingdom_rc6.bsp
maps/ut4_kingpin.bsp
maps/ut4_mandolin.bsp
maps/ut4_maximus_v1.bsp
maps/ut4_maya.bsp
maps/ut4_metropolis_b2.bsp
maps/ut4_oildepot.bsp
maps/ut4_orbital_sl.bsp
maps/ut4_pandora_b7.bsp
maps/ut4_paradise.bsp
maps/ut4_paris_v2.bsp
maps/ut4_poland_b11.bsp
maps/ut4_prague.bsp
maps/ut4_ramelle.bsp
maps/ut4_ricochet.bsp
maps/ut4_riyadh.bsp
maps/ut4_roma_beta2b.bsp
maps/ut4_sanc.bsp
maps/ut4_shahideen.bsp
maps/ut4_snoppis.bsp
maps/ut4_subterra.bsp
maps/ut4_suburbs.bsp
maps/ut4_subway.bsp
maps/ut4_swim.bsp
maps/ut4_terrorism7.bsp
maps/ut4_thingley.bsp
maps/ut4_tohunga_b8.bsp
maps/ut4_tombs.bsp
maps/ut4_toxic.bsp
maps/ut4_train_dl1.bsp
maps/ut4_tunis.bsp
maps/ut4_turnpike.bsp
maps/ut4_uptown.bsp
maps/ut4_venice_b7.bsp
maps/ut4_village.bsp
75 files listed
""")
        suggestions = self.console.changeMap('tohunga')
        self.assertIsNone(suggestions)
        verify(self.output_mock).write('map ut4_tohunga_b8')

    def test_getPlayerPings(self):
        """
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
        """
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


class Test_log_lines_parsing(Iourt41TestCase):

    def setUp(self):
        Iourt41TestCase.setUp(self)
        self.console.startup()
        self.joe = FakeClient(self.console, name="Joe", guid="000000000000000")

    def test_SurvivorWinner_team(self):
        self.assertEvent(r'''SurvivorWinner: Red''', event_type='EVT_SURVIVOR_WIN', event_data="Red")
        self.assertEvent(r'''SurvivorWinner: Blue''', event_type='EVT_SURVIVOR_WIN', event_data="Blue")

    def test_bomb_related(self):
        self.joe.connects('2')
        self.assertEvent(r'''Bomb was tossed by 2''', event_type='EVT_CLIENT_ACTION', event_data="bomb_tossed", event_client=self.joe)
        self.assertEvent(r'''Bomb was planted by 2''', event_type='EVT_CLIENT_ACTION', event_data="bomb_planted", event_client=self.joe)
        self.assertEvent(r'''Bomb was defused by 2!''', event_type='EVT_CLIENT_ACTION', event_data="bomb_defused", event_client=self.joe)
        self.assertEvent(r'''Bomb has been collected by 2''', event_type='EVT_CLIENT_ACTION', event_data="bomb_collected", event_client=self.joe)
        self.assertEvent(r'''Pop!''', event_type='EVT_BOMB_EXPLODED', event_data=None, event_client=None)

    def test_say_after_player_changed_name(self):
        def assert_new_name_and_text_does_not_break_auth(new_name, text="!help"):
            # WHEN the player renames himself
            self.console.parseLine(r'''777:16 ClientUserinfoChanged: 2 n\%s\t\3\r\1\tl\0\f0\\f1\\f2\\a0\0\a1\255\a2\0''' % new_name)
            self.console.parseLine(r'''777:16 AccountValidated: 2 - louk - 6 - "basic"''')
            self.console.parseLine(r'''777:16 ClientUserinfo: 2 \name\%s\ip\49.111.22.33:27960\password\xxxxxx\racered\0\raceblue\0\rate\16000\ut_timenudge\0\cg_rgb\0 255 0\funred\ninja,caprd,bartsor\funblue\ninja,gasmask,capbl\cg_physics\1\snaps\20\color1\4\color2\5\handicap\100\sex\male\cg_autoPickup\-1\cg_ghost\0\cl_time\n34|0610q5qH=t<a\racefree\1\gear\GZAAVWT\authc\2708\cl_guid\AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\weapmodes\01000110220000020002000''' % new_name)
            self.console.parseLine(r'''777:16 ClientUserinfoChanged: 2 n\%s\t\3\r\1\tl\0\f0\\f1\\f2\\a0\0\a1\255\a2\0''' % new_name)
            # THEN the next chat line should work
            self.assertEvent(r'''777:18 say: 2 %s: %s''' % (new_name, text),
                event_type='EVT_CLIENT_SAY',
                event_client=player,
                event_data=text.lstrip())

        # GIVEN a known player with cl_guid "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA" that will connect on slot 2
        player = FakeClient(console=self.console, name="Chucky", guid="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
        player.connects("2")

        # THEN
        assert_new_name_and_text_does_not_break_auth("joe")
        assert_new_name_and_text_does_not_break_auth("joe:")
        assert_new_name_and_text_does_not_break_auth("jo:e")
        assert_new_name_and_text_does_not_break_auth("j:oe")
        assert_new_name_and_text_does_not_break_auth(":joe")
        assert_new_name_and_text_does_not_break_auth("joe:")
        assert_new_name_and_text_does_not_break_auth("joe:foo")
        assert_new_name_and_text_does_not_break_auth("joe", "what does the fox say: Ring-ding-ding-ding-dingeringeding!")
        assert_new_name_and_text_does_not_break_auth("joe:", "what does the fox say: Ring-ding-ding-ding-dingeringeding!")
        assert_new_name_and_text_does_not_break_auth("jo:e", "what does the fox say: Ring-ding-ding-ding-dingeringeding!")
        assert_new_name_and_text_does_not_break_auth("j:oe", "what does the fox say: Ring-ding-ding-ding-dingeringeding!")
        assert_new_name_and_text_does_not_break_auth(":joe", "what does the fox say: Ring-ding-ding-ding-dingeringeding!")
        assert_new_name_and_text_does_not_break_auth("joe:", "what does the fox say: Ring-ding-ding-ding-dingeringeding!")
        assert_new_name_and_text_does_not_break_auth("joe:foo", "what does the fox say: Ring-ding-ding-ding-dingeringeding!")
        assert_new_name_and_text_does_not_break_auth("j:oe", ":")
        assert_new_name_and_text_does_not_break_auth("j:oe", " :")
        assert_new_name_and_text_does_not_break_auth("j:oe", " : ")
        assert_new_name_and_text_does_not_break_auth("j:oe", ": ")


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

    def test_client_with_password_gamepassword(self):
        """
        Case where a player saved the password to join the game in its UrT config. As a result, we find a 'password'
        field in the clientuserinfo line.
        This value must not overwrite the 'password' property of the Client object.
        """
        # GIVEN a known client
        c = FakeClient(console=self.console, name="Zesco", guid="58D4069246865BB5A85F20FB60ED6F65", login="login_in_database", password="password_in_database")
        c.save()
        c.connects('15')
        self.assertEqual('password_in_database', c.password)
        # WHEN
        infoline = r"15 \ip\1.2.3.4:27960\name\Zesco\password\some_password_here\racered\2\raceblue\3\rate\8000\ut_timenudge\0\cg_rgb\128 128 128\cg_predictitems\0\cg_physics\1\snaps\20\model\sarge\headmodel\sarge\team_model\james\team_headmodel\*james\color1\4\color2\5\handicap\100\sex\male\cl_anonymous\0\gear\GMIORAA\teamtask\0\cl_guid\58D4069246865BB5A85F20FB60ED6F65\weapmodes\00000110120000020002"
        self.assertTrue('15' in self.console.clients)
        self.console.OnClientuserinfo(action=None, data=infoline)
        # THEN
        client = self.console.clients['15']
        self.assertEqual('1.2.3.4', client.ip)
        self.assertEqual('Zesco^7', client.exactName)
        self.assertEqual('Zesco', client.name)
        self.assertEqual('58D4069246865BB5A85F20FB60ED6F65', client.guid)
        self.assertEqual('password_in_database', client.password)


class Test_OnClientuserinfochanged(Iourt41TestCase):

    def setUp(self):
        super(Test_OnClientuserinfochanged, self).setUp()
        self.console.PunkBuster = None

    def test_ioclient(self):
        # do OnClientuserinfo at first so it generates the client entry
        infoline = r"2 \ip\145.99.135.227:27960\challenge\-232198920\qport\2781\protocol\68\battleye\1\name\[SNT]^1XLR^78or\rate\8000\cg_predictitems\0\snaps\20\model\sarge\headmodel\sarge\team_model\james\team_headmodel\*james\color1\4\color2\5\handicap\100\sex\male\cl_anonymous\0\teamtask\0\cl_guid\58D4069246865BB5A85F20FB60ED6F65"
        self.assertFalse('2' in self.console.clients)
        self.console.OnClientuserinfo(action=None, data=infoline)
        self.assertTrue('2' in self.console.clients)
        client = self.console.clients['2']
        self.assertEqual('145.99.135.227', client.ip)
        self.assertEqual('[SNT]^1XLR^78or^7', client.exactName)
        self.assertEqual('[SNT]XLR8or', client.name)
        self.assertEqual('58D4069246865BB5A85F20FB60ED6F65', client.guid)
        # noew test OnClientuserinfochanged
        infoline = r"2 n\UnnamedOne\t\2\r\2\tl\0\f0\\f1\\f2\\a0\200\a1\\0\a2\20'"
        self.console.OnClientuserinfochanged(action=None, data=infoline)
        client = self.console.clients['2']
        self.assertEqual('UnnamedOne^7', client.exactName)
        self.assertEqual('UnnamedOne', client.name)
        self.assertEqual(b3.TEAM_BLUE, client.team)


class Test_pluginsStarted(Iourt41TestCase):

    def test_hacker_with_no_ip(self):
        """ see http://forum.bigbrotherbot.net/general-usage-support/iourt41-py-1-11-5-error/msg34328/ """
        when(self.console).write("status", maxRetries=ANY).thenReturn(r"""
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


class Test_OnKill(Iourt41TestCase):

    def setUp(self):
        Iourt41TestCase.setUp(self)
        self.console.startup()
        self.joe = FakeClient(self.console, name="Joe", guid="000000000000000")
        self.joe.connects('0')
        self.bob = FakeClient(self.console, name="Bob", guid="111111111111111")
        self.bob.connects('1')
        self.world = self.console.clients['-1']

    def test_nuke(self):
        self.assertEvent('5:19 Kill: 0 0 34: Joe killed Joe by UT_MOD_NUKED',
            event_type='EVT_CLIENT_KILL',
            event_client=self.world,
            event_target=self.joe,
            event_data=(100, self.console.UT_MOD_NUKED, 'body', 'UT_MOD_NUKED'))

    def test_lava(self):
        self.assertEvent('5:19 Kill: 1022 0 3: <world> killed Joe by MOD_LAVA',
            event_type='EVT_CLIENT_SUICIDE',
            event_client=self.joe,
            event_target=self.joe,
            event_data=(100, self.console.MOD_LAVA, 'body', 'MOD_LAVA'))

    def test_mr_sentry(self):
        self.assertEvent('5:19 Kill: 1022 0 14: <world> killed Joe by UT_MOD_BERETTA',
                         event_type='EVT_SENTRY_KILL',
                         event_client=None,
                         event_target=self.joe,
                         event_data=None)

    def test_constants(self):
        def assert_mod(kill_mod_number, kill_mod_name):
            self.assertTrue(hasattr(self.console, kill_mod_name), "expecting parser to have a constant named %s" % kill_mod_name)
            with patch.object(self.console, 'queueEvent') as queueEvent:
                self.console.parseLine(r'''Kill: 0 1 %s: Joe killed Bob by %s''' % (kill_mod_number, kill_mod_name))
                assert queueEvent.called, "No event was fired"
                args = queueEvent.call_args
            event_type_name = ('EVT_CLIENT_KILL', 'EVT_CLIENT_SUICIDE')
            eventraised = args[0][0]
            self.assertIsInstance(eventraised, Event)
            self.assertIn(self.console.getEventKey(eventraised.type), event_type_name)
            self.assertEquals(eventraised.data[0], 100)
            self.assertEquals(eventraised.data[1], getattr(self.console, kill_mod_name))
            self.assertEquals(eventraised.data[2], 'body')
            self.assertEquals(eventraised.data[3], kill_mod_name)

        assert_mod('1', 'MOD_WATER')
        assert_mod('3', 'MOD_LAVA')
        assert_mod('5', 'MOD_TELEFRAG')
        assert_mod('6', 'MOD_FALLING')
        assert_mod('7', 'MOD_SUICIDE')
        assert_mod('9', 'MOD_TRIGGER_HURT')
        assert_mod('10', 'MOD_CHANGE_TEAM')
        assert_mod('12', 'UT_MOD_KNIFE')
        assert_mod('13', 'UT_MOD_KNIFE_THROWN')
        assert_mod('14', 'UT_MOD_BERETTA')
        assert_mod('15', 'UT_MOD_DEAGLE')
        assert_mod('16', 'UT_MOD_SPAS')
        assert_mod('17', 'UT_MOD_UMP45')
        assert_mod('18', 'UT_MOD_MP5K')
        assert_mod('19', 'UT_MOD_LR300')
        assert_mod('20', 'UT_MOD_G36')
        assert_mod('21', 'UT_MOD_PSG1')
        assert_mod('22', 'UT_MOD_HK69')
        assert_mod('23', 'UT_MOD_BLED')
        assert_mod('24', 'UT_MOD_KICKED')
        assert_mod('25', 'UT_MOD_HEGRENADE')
        assert_mod('28', 'UT_MOD_SR8')
        assert_mod('30', 'UT_MOD_AK103')
        assert_mod('31', 'UT_MOD_SPLODED')
        assert_mod('32', 'UT_MOD_SLAPPED')
        assert_mod('33', 'UT_MOD_BOMBED')
        assert_mod('34', 'UT_MOD_NUKED')
        assert_mod('35', 'UT_MOD_NEGEV')
        assert_mod('37', 'UT_MOD_HK69_HIT')
        assert_mod('38', 'UT_MOD_M4')
        assert_mod('39', 'UT_MOD_FLAG')
        assert_mod('40', 'UT_MOD_GOOMBA')


class Test_getMapsSoundingLike(Iourt41TestCase):

    def setUp(self):
        Iourt41TestCase.setUp(self)
        self.console.startup()

    def test_no_map(self):
        # GIVEN
        when(self.console).getMaps().thenReturn([])
        rv = self.console.getMapsSoundingLike('tohunga')
        # THEN
        self.assertEqual([], rv)

    def test_one_map(self):
        # GIVEN
        when(self.console).getMaps().thenReturn(["ut4_baeza"])
        rv = self.console.getMapsSoundingLike('tohunga')
        # THEN
        self.assertEqual('ut4_baeza', rv)

    def test_lots_of_maps(self):
        # GIVEN
        when(self.console).getMaps().thenReturn(["ut4_abbey", "ut4_abbeyctf", "ut4_algiers", "ut4_ambush", "ut4_area3_b4",
             "ut4_asylum_b1", "ut4_austria", "ut4_aztek_b2", "ut4_baeza", "ut4_beijing_b3", "ut4_blackhawk", "ut4_blitzkrieg",
             "ut4_boxtrot_x6", "ut4_cambridge_b1", "ut4_cambridge_fixed", "ut4_casa", "ut4_commune", "ut4_company",
             "ut4_crossing", "ut4_deception_v2", "ut4_desolate_rc1", "ut4_docks", "ut4_dressingroom", "ut4_druglord2",
             "ut4_dust2_v2", "ut4_dust2_v3b", "ut4_eagle", "ut4_eezabad", "ut4_elgin", "ut4_exhibition_a24", "ut4_facade_b5",
             "ut4_ferguson_b12", "ut4_firingrange", "ut4_granja", "ut4_guerrilla", "ut4_harbortown", "ut4_heroic_beta1",
             "ut4_herring", "ut4_horror", "ut4_kingdom", "ut4_kingdom_rc6", "ut4_kingpin", "ut4_mandolin",
             "ut4_maximus_v1", "ut4_maya", "ut4_metropolis_b2", "ut4_oildepot", "ut4_orbital_sl", "ut4_pandora_b7",
             "ut4_paradise", "ut4_paris_v2", "ut4_poland_b11", "ut4_prague", "ut4_ramelle", "ut4_ricochet", "ut4_riyadh",
             "ut4_roma_beta2b", "ut4_sanc", "ut4_shahideen", "ut4_snoppis", "ut4_subterra", "ut4_suburbs", "ut4_subway",
             "ut4_swim", "ut4_terrorism7", "ut4_thingley", "ut4_tohunga_b8", "ut4_tombs", "ut4_toxic", "ut4_train_dl1",
             "ut4_tunis", "ut4_turnpike", "ut4_uptown", "ut4_venice_b7", "ut4_village"])
        # THEN
        self.assertEqual('ut4_tohunga_b8', self.console.getMapsSoundingLike('ut4_tohunga_b8'))
        self.assertEqual('ut4_tohunga_b8', self.console.getMapsSoundingLike('tohunga_b8'))
        self.assertEqual('ut4_tohunga_b8', self.console.getMapsSoundingLike('tohunga'))
        self.assertEqual('ut4_tohunga_b8', self.console.getMapsSoundingLike('tohung'))


class Test_misc(Iourt41TestCase):

    def setUp(self):
        Iourt41TestCase.setUp(self)

    def test_cvarlist(self):
        # GIVEN
        when(self.console).write("cvarlist").thenReturn(r"""cvarlist
        g_spskill "4"
        _B3 "B3 v1.9.0b2 [nt]"
S R     auth_status "public"
S R     auth "1"
S     C g_antilagvis "0"
     L  g_bombPlantTime "3"
S        Admin "Courgette"
     L  net_ip "localhost"
    AL  com_zoneMegs "32"
  R     sv_cheats "1"

347 total cvars
347 cvar indexes
""")
        # WHEN
        rv = self.console.cvarList()
        # THEN
        self.assertDictEqual({
            ' admin': 'Courgette',
            '_b3': 'B3 v1.9.0b2 [nt]',
            'auth': '1',
            'auth_status': 'public',
            'com_zonemegs': '32',
            'g_antilagvis': '0',
            'g_bombplanttime': '3',
            'g_spskill': '4',
            'net_ip': 'localhost',
            'sv_cheats': '1'
        }, rv)

    def test_cvarlist_with_filter(self):
        # GIVEN
        with patch.object(self.console, "cvarList") as cvarList_mock:
            # WHEN
            rv = self.console.cvarList("*the*filter*")
            # THEN
            cvarList_mock.assert_called_with("*the*filter*")

    def test_parseUserInfo(self):
        self.assertDictEqual({
            'cid': '7',
            'n': '[SNT]^1XLR^78or',
            't': '3',
            'r': '2',
            'tl': '0',
            'a0': '0',
            'a1': '0',
            'a2': '0',
        }, self.console.parseUserInfo(r'7 n\[SNT]^1XLR^78or\t\3\r\2\tl\0\f0\\f1\\f2\\a0\0\a1\0\a2\0'))
