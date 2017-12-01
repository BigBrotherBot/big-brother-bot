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

from mock import Mock, call, patch
from mockito import mock, when, any as anything
from b3.clients import Clients, Client
from b3.config import XmlConfigParser
from b3.events import Event
from b3.fake import FakeClient as original_FakeClient
from b3.output import VERBOSE2
from b3.parsers.iourt42 import Iourt42Parser, Iourt42Client
from tests import logging_disabled

log = logging.getLogger("test")
log.setLevel(logging.INFO)


# make sure to unpatch the Clients.newClient method and FakeClient
original_newClient = Clients.newClient
def tearDownModule():
    Clients.newClient = original_newClient


# We need our own FakeClient class to use the new auth() method from the Iourt42Client class
class FakeClient(original_FakeClient, Iourt42Client):
    # Python resolution rule for multiple inheritance will try to find the called methods in original_FakeClient class
    # first ; second from the b3.clients.Client class (which is inherited from the original_FakeClient class) ; third
    # from the Iourt42Client class ; and fourth from the b3.clients.Client class (which is inherited from the
    # Iourt42Client class).
    #
    # We want to have the methods from the original FakeClient class called preferably over the ones from
    # the Client Iourt42Client class, expected for the auth() method which has to be the one implemented in the
    # Iourt42Client class.
    #
    # So we have to keep the Iourt42Client class in second position and we overwrite the auth() method here to
    # control what code will be called in the end.
    def auth(self):
        return Iourt42Client.auth(self)


class Iourt42TestCase(unittest.TestCase):
    """
    Test case that is suitable for testing iourt42 parser specific features
    """
    @classmethod
    def setUpClass(cls):
        from b3.parsers.q3a.abstractParser import AbstractParser
        from b3.fake import FakeConsole
        AbstractParser.__bases__ = (FakeConsole,)
        # Now parser inheritance hierarchy is :
        # Iourt42TestCase -> AbstractParser -> FakeConsole -> Parser

    def setUp(self):
        self.parser_conf = XmlConfigParser()
        self.parser_conf.loadFromString("""<configuration>
                <settings name="server">
                    <set name="game_log"/>
                </settings>
            </configuration>""")
        with logging_disabled():
            self.console = Iourt42Parser(self.parser_conf)
        self.console.PunkBuster = None # no Punkbuster support in that game

        self.output_mock = mock()
        # simulate game server actions
        def write(*args, **kwargs):
            pretty_args = map(repr, args) + ["%s=%s" % (k, v) for k, v in kwargs.iteritems()]
            log.info("write(%s)" % ', '.join(pretty_args))
            if args == ("gamename",):
                return r'''"gamename" is:"q3urt42^7"'''
            return self.output_mock.write(*args, **kwargs)
        self.console.write = Mock(wraps=write)

        logging.getLogger('output').setLevel(VERBOSE2)

    def tearDown(self):
        if hasattr(self, "parser"):
            del self.parser.clients
            self.parser.working = False


class Test_log_lines_parsing(Iourt42TestCase):

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

    def setUp(self):
        Iourt42TestCase.setUp(self)
        self.console.startup()
        self.joe = FakeClient(self.console, name="Joe", guid="000000000000000")
        self.bot = FakeClient(self.console, name="BOT", guid="BOT1", team=b3.TEAM_RED, bot=True)

    def test_Radio(self):
        self.joe.connects('0')
        self.assertEvent(r'''Radio: 0 - 7 - 2 - "New Alley" - "I'm going for the flag"''',
            event_type='EVT_CLIENT_RADIO',
            event_client=self.joe,
            event_data={'msg_group': '7', 'msg_id': '2', 'location': 'New Alley', 'text': "I'm going for the flag" })

    def test_botStatusAfterInitRound(self):
        self.bot.connects('0')
        self.assertEqual(self.bot.team, b3.TEAM_RED)
        self.assertTrue(self.bot.bot)
        self.console.parseLine('''InitRound: \sv_allowdownload\0\g_matchmode\0\g_gametype\4\sv_maxclients\16\sv_floodprotect\1\g_warmup\5\capturelimit\0''')
        self.assertEqual(self.bot.team, b3.TEAM_RED)
        self.assertTrue(self.bot.bot)

    def test_Hotpotato(self):
        self.assertEvent(r'''Hotpotato:''', event_type='EVT_GAME_FLAG_HOTPOTATO')

    def test_Callvote(self):
        self.joe.connects('1')
        self.assertEvent(r'''Callvote: 1 - "map dressingroom"''',
            event_type='EVT_CLIENT_CALLVOTE',
            event_client=self.joe,
            event_data="map dressingroom")

    def test_Vote(self):
        self.joe.connects('0')
        self.assertEvent(r'''Vote: 0 - 2''',
            event_type='EVT_CLIENT_VOTE',
            event_client=self.joe,
            event_data="2")

    def test_Votepassed(self):
        self.assertEvent(r'''VotePassed: 1 - 0 - "reload"''',
            event_type='EVT_VOTE_PASSED',
            event_data={"yes": 1, "no": 0, "what": "reload"})

    def test_Votefailed(self):
        self.assertEvent(r'''VoteFailed: 1 - 1 - "restart"''',
            event_type='EVT_VOTE_FAILED',
            event_data={"yes": 1, "no": 1, "what": "restart"})

    def test_Flagcapturetime(self):
        patate = FakeClient(self.console, name="Patate", guid="Patate_guid")
        patate.connects('0')
        self.assertEvent(r'''FlagCaptureTime: 0: 1234567890''',
            event_type='EVT_FLAG_CAPTURE_TIME',
            event_client=patate,
            event_data=1234567890)

    def test_Hit_1(self):
        fatmatic = FakeClient(self.console, name="Fat'Matic", guid="11111111111111")
        d4dou = FakeClient(self.console, name="[FR]d4dou", guid="11111111111111")
        fatmatic.connects('3')
        d4dou.connects('6')
        self.assertEvent(r'''Hit: 6 3 5 8: Fat'Matic hit [FR]d4dou in the Torso''',
            event_type='EVT_CLIENT_DAMAGE',
            event_client=fatmatic,
            event_target=d4dou,
            event_data=(17, '19', '5'))

    def test_Hit_2(self):
        fatmatic = FakeClient(self.console, name="Fat'Matic", guid="11111111111111")
        d4dou = FakeClient(self.console, name="[FR]d4dou", guid="11111111111111")
        fatmatic.connects('3')
        d4dou.connects('6')
        self.assertEvent(r'''Hit: 3 6 9 17: [FR]d4dou hit Fat'Matic in the Legs''',
            event_type='EVT_CLIENT_DAMAGE',
            event_client=d4dou,
            event_target=fatmatic,
            event_data=(13, '36', '9'))

    def test_Hit_unkown_location(self):
        fatmatic = FakeClient(self.console, name="Fat'Matic", guid="11111111111111")
        d4dou = FakeClient(self.console, name="[FR]d4dou", guid="11111111111111")
        fatmatic.connects('3')
        d4dou.connects('6')
        with patch.object(self.console, 'warning') as warning_mock:
            self.assertEvent(r'''Hit: 6 3 321 8: Fat'Matic hit [FR]d4dou in the Pinky''',
                event_type='EVT_CLIENT_DAMAGE',
                event_client=fatmatic,
                event_target=d4dou,
                event_data=(15, '19', '321'))
        self.assertListEqual([call('_getDamagePoints(19, 321) cannot find value : list index out of range')],
                             warning_mock.mock_calls)

    def test_Kill(self):
        patate = FakeClient(self.console, name="Patate", guid="Patate_guid")
        psyp = FakeClient(self.console, name="psyp", guid="psyp_guid")
        patate.connects('0')
        psyp.connects('1')
        self.assertEvent(r'''Kill: 0 1 38: Patate killed psyp by UT_MOD_GLOCK''',
            event_type='EVT_CLIENT_KILL',
            event_client=patate,
            event_target=psyp,
            event_data=(100, '38', 'body', 'UT_MOD_GLOCK'))

    def test_say(self):
        marcel = FakeClient(self.console, name="^5Marcel^2[^6CZARMY^2]", guid="11111111111111")
        marcel.connects('6')
        self.assertEvent(r'''say: 6 ^5Marcel^2[^6CZARMY^2]: !help''',
            event_type='EVT_CLIENT_SAY',
            event_client=marcel,
            event_data="!help")

    def test_ClientJumpRunStarted(self):
        marcel = FakeClient(self.console, name="^5Marcel^2[^6CZARMY^2]", guid="11111111111111")
        marcel.connects('0')
        self.assertEvent(r'''ClientJumpRunStarted: 0 - way: 1''',
            event_type='EVT_CLIENT_JUMP_RUN_START',
            event_client=marcel,
            event_data={'way_id': '1', 'attempt_num': None, 'attempt_max': None})

    def test_ClientJumpRunStarted_with_attempt(self):
        marcel = FakeClient(self.console, name="^5Marcel^2[^6CZARMY^2]", guid="11111111111111")
        marcel.connects('0')
        self.assertEvent(r'''ClientJumpRunStarted: 0 - way: 1 - attempt: 1 of 5''',
            event_type='EVT_CLIENT_JUMP_RUN_START',
            event_client=marcel,
            event_data={'way_id': '1', 'attempt_num': '1', 'attempt_max': '5'})

    def test_ClientJumpRunStopped(self):
        marcel = FakeClient(self.console, name="^5Marcel^2[^6CZARMY^2]", guid="11111111111111")
        marcel.connects('0')
        self.assertEvent(r'''ClientJumpRunStopped: 0 - way: 1 - time: 12345''',
            event_type='EVT_CLIENT_JUMP_RUN_STOP',
            event_client=marcel,
            event_data={'way_id': '1', 'way_time': '12345', 'attempt_max': None, 'attempt_num': None})

    def test_ClientJumpRunStopped_with_attempt(self):
        marcel = FakeClient(self.console, name="^5Marcel^2[^6CZARMY^2]", guid="11111111111111")
        marcel.connects('0')
        self.assertEvent(r'''ClientJumpRunStopped: 0 - way: 1 - time: 12345 - attempt: 1 of 5''',
            event_type='EVT_CLIENT_JUMP_RUN_STOP',
            event_client=marcel,
            event_data={'way_id': '1', 'way_time': '12345', 'attempt_max': '5', 'attempt_num': '1'})

    def test_ClientJumpRunCancelled(self):
        marcel = FakeClient(self.console, name="^5Marcel^2[^6CZARMY^2]", guid="11111111111111")
        marcel.connects('0')
        self.assertEvent(r'''ClientJumpRunCanceled: 0 - way: 1''',
            event_type='EVT_CLIENT_JUMP_RUN_CANCEL',
            event_client=marcel,
            event_data={'way_id': '1', 'attempt_max': None, 'attempt_num': None})

    def test_ClientJumpRunCancelled_with_attempt(self):
        marcel = FakeClient(self.console, name="^5Marcel^2[^6CZARMY^2]", guid="11111111111111")
        marcel.connects('0')
        self.assertEvent(r'''ClientJumpRunCanceled: 0 - way: 1 - attempt: 1 of 5''',
            event_type='EVT_CLIENT_JUMP_RUN_CANCEL',
            event_client=marcel,
            event_data={'way_id': '1', 'attempt_max': '5', 'attempt_num': '1'})


    def test_ClientSavePosition(self):
        marcel = FakeClient(self.console, name="^5Marcel^2[^6CZARMY^2]", guid="11111111111111")
        marcel.connects('0')
        self.assertEvent(r'''ClientSavePosition: 0 - 335.384887 - 67.469154 - -23.875000''',
            event_type='EVT_CLIENT_POS_SAVE',
            event_client=marcel,
            event_data={'position': (335.384887, 67.469154, -23.875)})

    def test_ClientLoadPosition(self):
        marcel = FakeClient(self.console, name="^5Marcel^2[^6CZARMY^2]", guid="11111111111111")
        marcel.connects('0')
        self.assertEvent(r'''ClientLoadPosition: 0 - 335.384887 - 67.469154 - -23.875000''',
            event_type='EVT_CLIENT_POS_LOAD',
            event_client=marcel,
            event_data={'position': (335.384887, 67.469154, -23.875)})
        
    def test_ClientGoto(self):
        patate = FakeClient(self.console, name="Patate", guid="Patate_guid")
        psyp = FakeClient(self.console, name="psyp", guid="psyp_guid")
        patate.connects('0')
        psyp.connects('1')
        self.assertEvent(r'''ClientGoto: 0 - 1 - 335.384887 - 67.469154 - -23.875000''',
            event_type='EVT_CLIENT_GOTO',
            event_client=patate,
            event_target=psyp,
            event_data={'position': (335.384887, 67.469154, -23.875)})

    def test_ClientSpawn(self):
        patate = FakeClient(self.console, name="Patate", guid="Patate_guid")
        patate.connects('0')
        self.assertEvent(r'''ClientSpawn: 0''',
            event_type='EVT_CLIENT_SPAWN',
            event_client=patate,
            event_data=None)

    def test_client_freeze(self):
        alice = FakeClient(self.console, name="Alice", guid="aliceguid")
        alice.connects('0')
        bob = FakeClient(self.console, name="Bob", guid="bobguid")
        bob.connects('1')
        self.assertEvent(r'''Freeze: 0 1 16: Alice froze Bob by UT_MOD_SPAS''',
                         event_type='EVT_CLIENT_FREEZE',
                         event_client=alice,
                         event_target=bob,
                         event_data=Iourt42Parser.UT_MOD_SPAS)

    def test_client_thawout_started(self):
        alice = FakeClient(self.console, name="Alice", guid="aliceguid")
        alice.connects('0')
        bob = FakeClient(self.console, name="Bob", guid="bobguid")
        bob.connects('1')
        self.assertEvent(r'''ThawOutStarted: 0 1: Alice started thawing out Biddle''',
                         event_type='EVT_CLIENT_THAWOUT_STARTED',
                         event_client=alice,
                         event_target=bob)

    def test_client_thawout_finished(self):
        alice = FakeClient(self.console, name="Alice", guid="aliceguid")
        alice.connects('0')
        bob = FakeClient(self.console, name="Bob", guid="bobguid")
        bob.connects('1')
        self.assertEvent(r'''ThawOutFinished: 0 1: Fenix thawed out Biddle''',
                         event_type='EVT_CLIENT_THAWOUT_FINISHED',
                         event_client=alice,
                         event_target=bob)

    def test_client_melted(self):
        alice = FakeClient(self.console, name="Alice", guid="aliceguid")
        alice.connects('0')
        self.assertEvent(r'''ClientMelted: 0''', event_type='EVT_CLIENT_MELTED', event_client=alice)

    def test_SurvivorWinner_player(self):
        marcel = FakeClient(self.console, name="^5Marcel^2[^6CZARMY^2]", guid="11111111111111")
        marcel.connects('0')
        self.assertEvent(r'''SurvivorWinner: 0''', event_type='EVT_CLIENT_SURVIVOR_WINNER', event_client=marcel)

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

        # GIVEN a known player with FSA louk, cl_guid "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA" that will connect on slot 2
        player = FakeClient(console=self.console, name="Chucky", guid="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", pbid="louk")
        player.connects("2")

        # THEN
        assert_new_name_and_text_does_not_break_auth("joe")
        assert_new_name_and_text_does_not_break_auth("joe:")
        assert_new_name_and_text_does_not_break_auth("jo:e")
        assert_new_name_and_text_does_not_break_auth("j:oe")
        assert_new_name_and_text_does_not_break_auth(":joe")
        assert_new_name_and_text_does_not_break_auth("joe", "what does the fox say: Ring-ding-ding-ding-dingeringeding!")
        assert_new_name_and_text_does_not_break_auth("joe:", "what does the fox say: Ring-ding-ding-ding-dingeringeding!")
        assert_new_name_and_text_does_not_break_auth("jo:e", "what does the fox say: Ring-ding-ding-ding-dingeringeding!")
        assert_new_name_and_text_does_not_break_auth("j:oe", "what does the fox say: Ring-ding-ding-ding-dingeringeding!")
        assert_new_name_and_text_does_not_break_auth(":joe", "what does the fox say: Ring-ding-ding-ding-dingeringeding!")
        assert_new_name_and_text_does_not_break_auth("joe:foo")
        assert_new_name_and_text_does_not_break_auth("joe:foo", "what does the fox say: Ring-ding-ding-ding-dingeringeding!")
        assert_new_name_and_text_does_not_break_auth("j:oe", ":")
        assert_new_name_and_text_does_not_break_auth("j:oe", " :")
        assert_new_name_and_text_does_not_break_auth("j:oe", " : ")
        assert_new_name_and_text_does_not_break_auth("j:oe", ": ")


class Test_kill_mods(Test_log_lines_parsing):

    def setUp(self):
        Test_log_lines_parsing.setUp(self)
        self.joe = FakeClient(self.console, name="Joe", guid="000000000000000")
        self.joe.connects('0')
        self.bob = FakeClient(self.console, name="Bob", guid="111111111111111")
        self.bob.connects('1')
        self.world = self.console.clients['-1']

    def test_mod_water(self):
        self.assertEvent('0:56 Kill: 1022 0 1: <world> killed Joe by MOD_WATER',
            event_type='EVT_CLIENT_SUICIDE',
            event_client=self.joe,
            event_target=self.joe,
            event_data=(100, self.console.MOD_WATER, 'body', 'MOD_WATER')
        )

    def test_nuke(self):
        self.assertEvent('5:19 Kill: 0 0 35: Joe killed Joe by UT_MOD_NUKED',
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

    def test_falling(self):
        self.assertEvent('0:32 Kill: 1022 0 6: <world> killed Joe by MOD_FALLING',
            event_type='EVT_CLIENT_SUICIDE',
            event_client=self.joe,
            event_target=self.joe,
            event_data=(100, self.console.MOD_FALLING, 'body', 'MOD_FALLING'))

    def test_unknown_kill_mode(self):
        self.assertEvent('5:19 Kill: 0 0 1234: Joe killed Joe by MOD_F00',
            event_type='EVT_CLIENT_SUICIDE',
            event_client=self.joe,
            event_target=self.joe,
            event_data=(100, '1234', 'body', 'MOD_F00'))

    def test_constants(self):
        def assert_mod(kill_mod_number, kill_mod_name):
            self.assertTrue(hasattr(self.console, kill_mod_name), "expecting parser to have a constant named %s = '%s'" % (kill_mod_name, kill_mod_number))
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
        assert_mod('33', 'UT_MOD_SMITED')
        assert_mod('34', 'UT_MOD_BOMBED')
        assert_mod('35', 'UT_MOD_NUKED')
        assert_mod('36', 'UT_MOD_NEGEV')
        assert_mod('37', 'UT_MOD_HK69_HIT')
        assert_mod('38', 'UT_MOD_M4')
        assert_mod('39', 'UT_MOD_GLOCK')
        assert_mod('40', 'UT_MOD_COLT1911')
        assert_mod('41', 'UT_MOD_MAC11')
        assert_mod('42', 'UT_MOD_FLAG')
        assert_mod('43', 'UT_MOD_GOOMBA')


class Test_OnClientuserinfo(Iourt42TestCase):

    def setUp(self):
        super(Test_OnClientuserinfo, self).setUp()
        self.console.PunkBuster = None

    def test_ioclient(self):
        self.console.queryClientFrozenSandAccount = Mock(return_value={})
        infoline = r'''2 \ip\11.22.33.44:27961\challenge\-284496317\qport\13492\protocol\68\name\laCourge\racered\2\raceblue\2\rate\16000\ut_timenudge\0\cg_rgb\128 128 128\cg_predictitems\0\cg_physics\1\cl_anonymous\0\sex\male\handicap\100\color2\5\color1\4\team_headmodel\*james\team_model\james\headmodel\sarge\model\sarge\snaps\20\cg_autoPickup\-1\gear\GLAORWA\authc\0\teamtask\0\cl_guid\00000000011111111122222223333333\weapmodes\00000110220000020002'''
        self.assertFalse('2' in self.console.clients)
        self.console.OnClientuserinfo(action=None, data=infoline)
        self.assertTrue('2' in self.console.clients)
        client = self.console.clients['2']
        self.assertEqual('11.22.33.44', client.ip)
        self.assertEqual('laCourge^7', client.exactName)
        self.assertEqual('laCourge', client.name)
        self.assertEqual('00000000011111111122222223333333', client.guid)
        self.assertEqual(self.console.queryClientFrozenSandAccount.call_count, 2) # both on connect and auth

    def test_ioclient_with_authl_token(self):
        self.console.queryClientFrozenSandAccount = Mock(return_value={})
        infoline = r'''2 \ip\11.22.33.44:27961\challenge\-284496317\qport\13492\protocol\68\name\laCourge\racered\2\raceblue\2\rate\16000\ut_timenudge\0\cg_rgb\128 128 128\cg_predictitems\0\cg_physics\1\cl_anonymous\0\sex\male\handicap\100\color2\5\color1\4\team_headmodel\*james\team_model\james\headmodel\sarge\model\sarge\snaps\20\cg_autoPickup\-1\gear\GLAORWA\authl\lacourge\authc\0\teamtask\0\cl_guid\00000000011111111122222223333333\weapmodes\00000110220000020002'''
        self.assertFalse('2' in self.console.clients)
        self.console.OnClientuserinfo(action=None, data=infoline)
        self.assertTrue('2' in self.console.clients)
        client = self.console.clients['2']
        self.assertEqual('11.22.33.44', client.ip)
        self.assertEqual('laCourge^7', client.exactName)
        self.assertEqual('laCourge', client.name)
        self.assertEqual('lacourge', client.pbid)
        self.assertEqual('00000000011111111122222223333333', client.guid)
        self.assertEqual(self.console.queryClientFrozenSandAccount.call_count, 0)

    @unittest.skip("need to validate rcon responses from real 4.2 gameserver")
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

    @unittest.skip("will there still be Q3 mod ?")
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

    def test_ioclient_overflowing_userinfostring_with_kick(self):
        self.console.queryClientFrozenSandAccount = Mock(return_value={})
        infoline = r'''2 \ip\11.22.33.44:27961\challenge\-284496317\qport\13492\protocol\68\name\aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\racered\2\raceblue\2\rate\16000\ut_timenudge\0\cg_rgb\128 128 128\cg_predictitems\0\cg_physics\1\cl_anonymous\0\sex\male\handicap\100\color2\5\color1\4\team_headmodel\*james\team_model\james\headmodel\sarge\model\sarge\snaps\20\cg_autoPickup\-1\gear\GLAORWA\authc\0\teamtask\0\cl_guid\00000000011111111122222223333333\weapmodes\00000110220000020002'''
        self.assertFalse('2' in self.console.clients)
        self.console.OnClientuserinfo(action=None, data=infoline)
        self.assertFalse('2' in self.console.clients)

    def test_ioclient_overflowing_userinfostring_with_rename(self):
        self.console._allow_userinfo_overflow = True
        self.console.queryClientFrozenSandAccount = Mock(return_value={})
        infoline = r'''2 \ip\11.22.33.44:27961\challenge\-284496317\qport\13492\protocol\68\name\aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\racered\2\raceblue\2\rate\16000\ut_timenudge\0\cg_rgb\128 128 128\cg_predictitems\0\cg_physics\1\cl_anonymous\0\sex\male\handicap\100\color2\5\color1\4\team_headmodel\*james\team_model\james\headmodel\sarge\model\sarge\snaps\20\cg_autoPickup\-1\gear\GLAORWA\authc\0\teamtask\0\cl_guid\00000000011111111122222223333333\weapmodes\00000110220000020002'''
        self.assertFalse('2' in self.console.clients)
        self.console.OnClientuserinfo(action=None, data=infoline)
        self.assertTrue('2' in self.console.clients)
        client = self.console.clients.getByCID('2')
        self.assertEqual(32, len(client.name))


class Test_OnClientuserinfochanged(Iourt42TestCase):

    def setUp(self):
        super(Test_OnClientuserinfochanged, self).setUp()
        self.console.PunkBuster = None

    def test_ioclient(self):
        # do OnClientuserinfo first to generate the client
        infoline = r'''2 \ip\11.22.33.44:27961\challenge\-284496317\qport\13492\protocol\68\name\laCourge\racered\2\raceblue\2\rate\16000\ut_timenudge\0\cg_rgb\128 128 128\cg_predictitems\0\cg_physics\1\cl_anonymous\0\sex\male\handicap\100\color2\5\color1\4\team_headmodel\*james\team_model\james\headmodel\sarge\model\sarge\snaps\20\cg_autoPickup\-1\gear\GLAORWA\authc\0\teamtask\0\cl_guid\00000000011111111122222223333333\weapmodes\00000110220000020002'''
        self.assertFalse('2' in self.console.clients)
        self.console.OnClientuserinfo(action=None, data=infoline)
        self.assertTrue('2' in self.console.clients)
        client = self.console.clients['2']
        self.assertEqual('11.22.33.44', client.ip)
        self.assertEqual('laCourge^7', client.exactName)
        self.assertEqual('laCourge', client.name)
        self.assertEqual('00000000011111111122222223333333', client.guid)
        # now test OnClientuserinfochanged
        infoline = r'''2 n\UnnamedOne\t\3\r\2\tl\0\f0\\f1\\f2\\a0\0\a1\0\a2\0'''
        self.console.OnClientuserinfochanged(action=None, data=infoline)
        client = self.console.clients['2']
        self.assertEqual('UnnamedOne^7', client.exactName)
        self.assertEqual('UnnamedOne', client.name)
        self.assertEqual(b3.TEAM_SPEC, client.team)


class Test_queryClientFrozenSandAccount(Iourt42TestCase):

    def test_authed(self):
        # GIVEN
        when(self.console).write('auth-whois 0').thenReturn(r'''auth: id: 0 - name: ^7laCourge - login: courgette - notoriety: serious - level: -1''')
        # WHEN
        data = self.console.queryClientFrozenSandAccount('0')
        # THEN
        self.assertDictEqual({'cid': '0', 'name': 'laCourge', 'login': 'courgette', 'notoriety': 'serious', 'level': '-1', 'extra': None}, data)

    def test_authed_with_newline_char(self):
        # GIVEN
        when(self.console).write('auth-whois 0').thenReturn(r'''auth: id: 0 - name: ^7laCourge - login: courgette - notoriety: serious - level: -1
''')
        # WHEN
        data = self.console.queryClientFrozenSandAccount('0')
        # THEN
        self.assertDictEqual({'cid': '0', 'name': 'laCourge', 'login': 'courgette', 'notoriety': 'serious', 'level': '-1', 'extra': None}, data)

    def test_not_active(self):
        # GIVEN
        when(self.console).write('auth-whois 3').thenReturn(r'''Client 3 is not active.''')
        # WHEN
        data = self.console.queryClientFrozenSandAccount('3')
        # THEN
        self.assertDictEqual({}, data)

    def test_no_account(self):
        # GIVEN
        when(self.console).write('auth-whois 3').thenReturn(r'''auth: id: 3 - name: ^7laCourge - login:  - notoriety: 0 - level: 0  - ^7no account''')
        # WHEN
        data = self.console.queryClientFrozenSandAccount('3')
        # THEN
        self.assertDictEqual({'cid': '3', 'name': 'laCourge', 'login': '', 'notoriety': '0', 'level': '0', 'extra': '^7no account'}, data)

    def test_all(self):
        # GIVEN
        when(self.console).write('auth-whois all', maxRetries=anything()).thenReturn(r'''No player found for "all".
auth: id: 0 - name: ^7laCourge - login: courgette - notoriety: serious - level: -1
auth: id: 1 - name: ^7f00 - login:  - notoriety: 0 - level: 0  - ^7no account
auth: id: 2 - name: ^7Qant - login: qant - notoriety: basic - level: -1
''')
        # WHEN
        data = self.console.queryAllFrozenSandAccount()
        # THEN
        self.assertDictEqual({'0': {'cid': '0', 'extra': None, 'level': '-1', 'login': 'courgette', 'name': 'laCourge', 'notoriety': 'serious'},
                              '1': {'cid': '1', 'extra': "^7no account", 'level': '0', 'login': '', 'name': 'f00', 'notoriety': '0'},
                              '2': {'cid': '2', 'extra': None, 'level': '-1', 'login': 'qant', 'name': 'Qant', 'notoriety': 'basic'}
                            }, data)


class Test_auth_without_FSA(Iourt42TestCase):

    def setUp(self):
        Iourt42TestCase.setUp(self)
        # GIVEN a player without FSA joe_fsa that will connect on slot 3
        when(self.console).write('auth-whois 3').thenReturn(r'''auth: id: 3 - name: ^7Joe - login:  - notoriety: 0 - level: 0  - ^7no account''')

    def test_unknown_cl_guid(self):
        # GIVEN a player with a unknown cl_guid
        player = FakeClient(console=self.console, name="Joe", guid="joe_cl_guid")
        self.assertEqual(0, len(self.console.clients))
        self.assertDictEqual({'Kicks': 0, 'TempBans': 0, 'clients': 0, 'Bans': 0, 'Warnings': 0}, self.console.storage.getCounts())
        # WHEN player connects on slot 3
        player.connects("3")
        # THEN player is authenticated
        self.assertEqual(1, len(self.console.clients))
        self.assertTrue(player.authed)
        # THEN a new player entry is created in database
        self.assertDictEqual({'Kicks': 0, 'TempBans': 0, 'clients': 1, 'Bans': 0, 'Warnings': 0}, self.console.storage.getCounts())
        self.assertNotEqual(0, player.id)
        # THEN the new entry in database has the correct cl_guid and no FSA
        player_from_db = self.console.storage.getClient(Client(id=player.id))
        self.assertEqual("joe_cl_guid", player_from_db.guid)
        self.assertEqual('', player_from_db.pbid)

    def test_known_cl_guid(self):
        # GIVEN a known player in database with cl_guid "joe_cl_guid"
        known_player = FakeClient(console=self.console, name="Joe", guid="joe_cl_guid")
        known_player.save()
        self.assertNotEqual(0, known_player.id)
        self.assertDictEqual({'Kicks': 0, 'TempBans': 0, 'clients': 1, 'Bans': 0, 'Warnings': 0}, self.console.storage.getCounts())
        self.assertEqual(0, len(self.console.clients))
        # WHEN a player connects on slot 3 with cl_guid "joe_cl_guid" and no FSA
        player = FakeClient(console=self.console, name="Joe", guid="joe_cl_guid")
        player.connects("3")
        # THEN player is authenticated
        self.assertEqual(1, len(self.console.clients))
        self.assertTrue(player.authed)
        # THEN no new entry is created in database
        self.assertDictEqual({'Kicks': 0, 'TempBans': 0, 'clients': 1, 'Bans': 0, 'Warnings': 0}, self.console.storage.getCounts())
        self.assertEqual(known_player.id, player.id)


class Test_auth_with_unknown_FSA(Iourt42TestCase):

    def setUp(self):
        Iourt42TestCase.setUp(self)
        # GIVEN a player with FSA joe_fsa that will connect on slot 3
        when(self.console).write('auth-whois 3').thenReturn(r'''auth: id: 3 - name: ^7Joe - login: joe_fsa - notoriety: serious - level: -1''')

    def test_unknown_cl_guid(self):
        # GIVEN a player with cl_guid "joe_cl_guid" that does not exists in database
        player = FakeClient(console=self.console, name="Joe", guid="joe_cl_guid")
        self.assertEqual(0, len(self.console.clients))
        self.assertDictEqual({'Kicks': 0, 'TempBans': 0, 'clients': 0, 'Bans': 0, 'Warnings': 0}, self.console.storage.getCounts())
        # WHEN player connects
        player.connects("3")
        # THEN player is authenticated
        self.assertEqual(1, len(self.console.clients))
        self.assertTrue(player.authed)
        # THEN a new player entry is created in database
        self.assertDictEqual({'Kicks': 0, 'TempBans': 0, 'clients': 1, 'Bans': 0, 'Warnings': 0}, self.console.storage.getCounts())
        self.assertNotEqual(0, player.id)
        # THEN database entry has the new FSA value
        player_from_db = self.console.storage.getClient(Client(id=player.id))
        self.assertEqual('joe_fsa', player_from_db.pbid)

    def test_known_cl_guid(self):
        # GIVEN a known player in database with cl_guid "joe_cl_guid"
        known_player = FakeClient(console=self.console, name="Joe", guid="joe_cl_guid")
        known_player.save()
        self.assertNotEqual(0, known_player.id)
        self.assertDictEqual({'Kicks': 0, 'TempBans': 0, 'clients': 1, 'Bans': 0, 'Warnings': 0}, self.console.storage.getCounts())
        self.assertEqual(0, len(self.console.clients))
        # WHEN a player connects on slot 3 with cl_guid "joe_cl_guid" and no FSA
        player = FakeClient(console=self.console, name="Joe", guid="joe_cl_guid")
        player.connects("3")
        # THEN player is authenticated
        self.assertEqual(1, len(self.console.clients))
        self.assertTrue(player.authed)
        # THEN no new entry is created in DB
        self.assertDictEqual({'Kicks': 0, 'TempBans': 0, 'clients': 1, 'Bans': 0, 'Warnings': 0}, self.console.storage.getCounts())
        self.assertEqual(known_player.id, player.id)


class Test_auth_with_uniquely_known_FSA(Iourt42TestCase):

    def setUp(self):
        Iourt42TestCase.setUp(self)
        # GIVEN a known player with FSA joe_fsa, cl_guid "cl_guid_A" that will connect on slot 3
        when(self.console).write('auth-whois 3').thenReturn(r'''auth: id: 3 - name: ^7Joe - login: joe_fsa - notoriety: serious - level: -1''')
        player = FakeClient(console=self.console, name="Joe", guid="cl_guid_A", pbid="joe_fsa")
        player.save()
        self.known_player_db_id = player.id
        # THEN we have 0 connected players and 1 player known in database
        self.assertDictEqual({'Kicks': 0, 'TempBans': 0, 'clients': 1, 'Bans': 0, 'Warnings': 0}, self.console.storage.getCounts())
        self.assertEqual(0, len(self.console.clients))

    def test_unknown_cl_guid(self):
        # GIVEN player with known FSA and unknown cl_guid
        player = FakeClient(console=self.console, name="Joe", guid="cl_guid_B")
        # WHEN player connects
        player.connects("3")
        # THEN player auth against the known database entry
        self.assertEqual(1, len(self.console.clients))
        self.assertTrue(player.authed)
        self.assertEqual(self.known_player_db_id, player.id)
        # THEN no new client entry must be created in database
        self.assertDictEqual({'Kicks': 0, 'TempBans': 0, 'clients': 1, 'Bans': 0, 'Warnings': 0}, self.console.storage.getCounts())
        # THEN the DB player entry cl_guid is replaced with the new value
        player_from_db = self.console.storage.getClient(Client(id=player.id))
        self.assertEqual("cl_guid_B", player_from_db.guid)

    def test_known_cl_guid_for_that_fsa(self):
        # GIVEN player with known FSA and known cl_guid for that FSA
        player = FakeClient(console=self.console, name="Joe", guid="cl_guid_A")
        # WHEN player connects
        player.connects("3")
        # THEN player auth against the known DB entry
        self.assertEqual(1, len(self.console.clients))
        self.assertTrue(player.authed)
        self.assertEqual(self.known_player_db_id, player.id)
        # THEN no new client entry must be created in database
        self.assertDictEqual({'Kicks': 0, 'TempBans': 0, 'clients': 1, 'Bans': 0, 'Warnings': 0}, self.console.storage.getCounts())
        # THEN the DB player entry cl_guid is still "cl_guid_A"
        player_from_db = self.console.storage.getClient(Client(id=player.id))
        self.assertEqual("cl_guid_A", player_from_db.guid)

    def test_known_cl_guid_for_another_fsa(self):
        # GIVEN another known player with FSA jack_fsa, cl_guid "cl_guid_X"
        the_other_player = FakeClient(console=self.console, name="Jack", guid="cl_guid_X", pbid="jack_fsa")
        the_other_player.save()
        the_other_player_db_id = the_other_player.id
        # THEN we have 0 connected players and 2 players known in database
        self.assertDictEqual({'Kicks': 0, 'TempBans': 0, 'clients': 2, 'Bans': 0, 'Warnings': 0}, self.console.storage.getCounts())
        self.assertEqual(0, len(self.console.clients))
        # GIVEN player with known FSA and known cl_guid for another FSA
        player = FakeClient(console=self.console, name="Joe", guid="cl_guid_X")
        # WHEN player connects
        player.connects("3")
        # THEN player auth against the known DB entry that matches the FSA
        self.assertEqual(1, len(self.console.clients))
        self.assertTrue(player.authed)
        self.assertEqual(self.known_player_db_id, player.id)
        self.assertNotEqual(the_other_player_db_id, player.id)
        # THEN no new client entry must be created in database
        self.assertDictEqual({'Kicks': 0, 'TempBans': 0, 'clients': 2, 'Bans': 0, 'Warnings': 0}, self.console.storage.getCounts())
        # THEN the DB player entry cl_guid remains unchanged
        player_from_db = self.console.storage.getClient(Client(id=player.id))
        self.assertEqual("cl_guid_A", player_from_db.guid)


class Test_auth_with_non_uniquely_known_FSA(Iourt42TestCase):

    def setUp(self):
        Iourt42TestCase.setUp(self)
        # GIVEN a known player with FSA joe_fsa, cl_guid "cl_guid_A" that will connect on slot 3
        when(self.console).write('auth-whois 3').thenReturn(r'''auth: id: 3 - name: ^7Joe - login: joe_fsa - notoriety: serious - level: -1''')
        player = FakeClient(console=self.console, name="Joe", guid="cl_guid_A", pbid="joe_fsa")
        player.save()
        self.known_player_db_id = player.id
        # GIVEN another known player with FSA joe_fsa and cl_guid "cl_guid_B" that we do not expect to connect
        the_other_player = FakeClient(console=self.console, name="Jack", guid="cl_guid_B", pbid="joe_fsa")
        the_other_player.save()
        # THEN we have 0 connected players and 2 players known in database
        self.assertDictEqual({'Kicks': 0, 'TempBans': 0, 'clients': 2, 'Bans': 0, 'Warnings': 0}, self.console.storage.getCounts())
        self.assertEqual(0, len(self.console.clients))

    def test_unknown_cl_guid(self):
        # GIVEN player with known FSA and unknown cl_guid
        player = FakeClient(console=self.console, name="Joe", guid="cl_guid_f00")
        # WHEN player connects
        player.connects("3")
        # THEN player is authenticated
        self.assertEqual(1, len(self.console.clients))
        self.assertTrue(player.authed)
        # THEN a new client entry is be created in database
        self.assertDictEqual({'Kicks': 0, 'TempBans': 0, 'clients': 3, 'Bans': 0, 'Warnings': 0}, self.console.storage.getCounts())
        # THEN the new database player entry has the current values for cl_guid and FSA
        player_from_db = self.console.storage.getClient(Client(id=player.id))
        self.assertEqual("cl_guid_f00", player_from_db.guid)
        self.assertEqual("joe_fsa", player_from_db.pbid)
        # THEN we now have 3 database entries for FSA joe_fsa
        self.assertEqual(3, len(self.console.storage.getClientsMatching({'pbid': "joe_fsa"})))

    def test_known_cl_guid_for_that_fsa(self):
        # GIVEN player with known FSA and known cl_guid for that FSA
        player = FakeClient(console=self.console, name="Joe", guid="cl_guid_A")
        # WHEN player connects
        player.connects("3")
        # THEN player auth against the known DB entry
        self.assertEqual(1, len(self.console.clients))
        self.assertTrue(player.authed)
        self.assertEqual(self.known_player_db_id, player.id)
        # THEN no new client entry must be created in database
        self.assertDictEqual({'Kicks': 0, 'TempBans': 0, 'clients': 2, 'Bans': 0, 'Warnings': 0}, self.console.storage.getCounts())
        # THEN the DB player entry cl_guid is still "cl_guid_A"
        player_from_db = self.console.storage.getClient(Client(id=player.id))
        self.assertEqual("cl_guid_A", player_from_db.guid)



class Test_parser_API(Iourt42TestCase):

    def setUp(self):
        Iourt42TestCase.setUp(self)
        self.player = self.console.clients.newClient(cid="4", guid="theGuid", name="theName", ip="11.22.33.44")

    def test_getPlayerList(self):
        # GIVEN
        when(self.console).write('status', maxRetries=anything()).thenReturn('''\
map: ut4_casa
num score ping name            lastmsg address               qport rate
--- ----- ---- --------------- ------- --------------------- ----- -----
  4     0  141 theName^7              0 11.22.33.44:27961     38410  8000
  5     0   48 theName2^7             0 11.22.33.45:27961     38410  8000
''')
        # WHEN
        rv = self.console.getPlayerList()
        # THEN
        self.assertDictContainsSubset({
            '5': {'slot': '5', 'last': '0', 'name': 'theName2^7', 'ip': '11.22.33.45', 'ping': '48', 'pbid': None, 'qport': '38410', 'rate': '8000', 'score': '0', 'port': '27961'},
            '4': {'slot': '4', 'last': '0', 'name': 'theName^7', 'ip': '11.22.33.44', 'ping': '141', 'pbid': None, 'qport': '38410', 'rate': '8000', 'score': '0', 'port': '27961'}
        }, rv)



    def test_sync(self):
        # GIVEN
        when(self.console).write('status', maxRetries=anything()).thenReturn('''\
map: ut4_casa
num score ping name            lastmsg address               qport rate
--- ----- ---- --------------- ------- --------------------- ----- -----
  0     0   48 laCourge^7              0 11.22.33.44:27961  13492 16000
''')
        when(self.console).write('dumpuser 0').thenReturn('''\
userinfo
--------
ip                  11.22.33.44:27961
name                laCourge
cl_guid             00000000000000014111111111111111
''')
        when(self.console).write('auth-whois 0').thenReturn('''\
auth: id: 0 - name: ^7laCourge - login: courgette - notoriety: serious - level: -1
''')
        # WHEN
        mlist = self.console.sync()
        # THEN
        self.assertIn("0", mlist)
        player = mlist.get("0", None)
        self.assertIsNotNone(player)
        self.assertEqual('00000000000000014111111111111111', player.guid)
        self.assertEqual('courgette', player.pbid)
        self.assertTrue(player.authed)


    def test_say(self):
        self.console.say("f00")
        self.console.write.assert_has_calls([call('say f00')])


    def test_saybig(self):
        self.console.saybig("f00")
        self.console.write.assert_has_calls([call('bigtext "f00"')])


    def test_message(self):
        self.console.message(self.player, "f00")
        self.console.write.assert_has_calls([call('tell 4 ^8[pm]^7 f00')])


    def test_kick(self):
        self.console.kick(self.player, reason="f00")
        self.console.write.assert_has_calls([call('kick 4 "f00"'), call('say theName^7 was kicked f00')])


    def test_ban(self):
        self.console.ban(self.player, reason="f00")
        self.console.write.assert_has_calls([call('addip 4'), call('say theName^7 was banned f00')])


    def test_unban(self):
        self.console.unban(self.player, reason='f00')
        self.console.write.assert_has_calls([call('removeip 11.22.33.44'),
                                          call('removeip 11.22.33.44'),
                                          call('removeip 11.22.33.44'),
                                          call('removeip 11.22.33.44'),
                                          call('removeip 11.22.33.44')])


    def test_tempban(self):
        self.console.tempban(self.player, reason="f00", duration="1h")
        self.console.write.assert_has_calls([call('kick 4 "f00"'), call('say theName^7 was temp banned for 1 hour^7 f00')])


    def test_getMap(self):
        # GIVEN
        when(self.console).write('status').thenReturn('''\
map: ut4_casa
num score ping name            lastmsg address               qport rate
--- ----- ---- --------------- ------- --------------------- ----- -----
''')
        # WHEN
        rv = self.console.getMap()
        # THEN
        self.assertEqual('ut4_casa', rv)


    def test_getMaps(self):
        # GIVEN
        when(self.console).write('fdir *.bsp', socketTimeout=anything()).thenReturn('''\
---------------
maps/ut4_abbey.bsp
maps/ut4_algiers.bsp
maps/ut4_ambush.bsp
3 files listed
''')
        # WHEN
        rv = self.console.getMaps()
        # THEN
        self.assertListEqual(['ut4_abbey', 'ut4_algiers', 'ut4_ambush'], rv)


    @patch('time.sleep')
    def test_rotateMap(self, sleep_mock):
        self.console.rotateMap()
        self.console.write.assert_has_calls([call('say ^7Changing to next map'), call('cyclemap')])
        sleep_mock.assert_called_once_with(1)


    @patch('time.sleep')
    def test_changeMap(self, sleep_mock):
        # GIVEN
        when(self.output_mock).write('fdir *.bsp', socketTimeout=anything()).thenReturn("""\
---------------
maps/ut4_foo.bsp
1 files listed
""")
        # WHEN
        suggestions = self.console.changeMap('ut4_f00')
        # THEN
        self.assertIsNone(suggestions)
        self.console.write.assert_has_calls([call('map ut4_foo')])
        sleep_mock.assert_called_once_with(1)


    def test_getPlayerPings(self):
        # GIVEN
        when(self.console).write('status').thenReturn('''\
map: ut4_casa
num score ping name            lastmsg address               qport rate
--- ----- ---- --------------- ------- --------------------- ----- -----
  4     0  141 theName^7              0 11.22.33.44:27961     38410  8000
  5     0   48 theName2^7             0 11.22.33.45:27961     38410  8000
''')
        # WHEN
        rv = self.console.getPlayerPings()
        # THEN
        self.assertDictEqual({"4": 141, "5": 48}, rv)


    def test_getPlayerScores(self):
        # GIVEN
        when(self.console).write('status').thenReturn('''\
map: ut4_casa
num score ping name            lastmsg address               qport rate
--- ----- ---- --------------- ------- --------------------- ----- -----
  4    11  141 theName^7              0 11.22.33.44:27961     38410  8000
  5    25   48 theName2^7             0 11.22.33.45:27961     38410  8000
''')
        # WHEN
        rv = self.console.getPlayerScores()
        # THEN
        self.assertDictEqual({"4": 11, "5": 25}, rv)




class Test_inflictCustomPenalty(Iourt42TestCase):
    """
    Called if b3.admin.penalizeClient() does not know a given penalty type.
    Overwrite this to add customized penalties for your game like 'slap', 'nuke',
    'mute', 'kill' or anything you want.
    /!\ This method must return True if the penalty was inflicted.
    """
    def setUp(self):
        Iourt42TestCase.setUp(self)
        self.player = self.console.clients.newClient(cid="4", guid="theGuid", name="theName", ip="11.22.33.44")

    def test_slap(self):
        result = self.console.inflictCustomPenalty('slap', self.player)
        self.console.write.assert_has_calls([call('slap 4')])
        self.assertTrue(result)

    def test_nuke(self):
        result = self.console.inflictCustomPenalty('nuke', self.player)
        self.console.write.assert_has_calls([call('nuke 4')])
        self.assertTrue(result)

    def test_mute(self):
        result = self.console.inflictCustomPenalty('mute', self.player, duration="15s")
        self.console.write.assert_has_calls([call('mute 4 15.0')])
        self.assertTrue(result)

    def test_kill(self):
        result = self.console.inflictCustomPenalty('kill', self.player)
        self.console.write.assert_has_calls([call('smite 4')])
        self.assertTrue(result)




class Test_load_conf_frozensand_ban_settings(Iourt42TestCase):

    def setUp(self):
        Iourt42TestCase.setUp(self)
        self.console.load_conf_permban_with_frozensand = Mock()
        self.console.load_conf_tempban_with_frozensand = Mock()


    def test_auth_public(self):
        # GIVEN
        when(self.console).write("auth").thenReturn('"auth" is:"1^7"')
        when(self.console).write("auth_owners").thenReturn('"auth_owners" is:"452^7" default:"^7"')
        # WHEN
        self.console.load_conf_frozensand_ban_settings()
        # THEN
        self.assertEqual(1, self.console.load_conf_permban_with_frozensand.call_count)
        self.assertEqual(1, self.console.load_conf_tempban_with_frozensand.call_count)


    def test_auth_notoriety(self):
        # GIVEN
        when(self.console).write("auth").thenReturn('"auth" is:"-1^7"')
        when(self.console).write("auth_owners").thenReturn('"auth_owners" is:"452^7" default:"^7"')
        # WHEN
        self.console.load_conf_frozensand_ban_settings()
        # THEN
        self.assertEqual(1, self.console.load_conf_permban_with_frozensand.call_count)
        self.assertEqual(1, self.console.load_conf_tempban_with_frozensand.call_count)


    def test_auth_private(self):
        # GIVEN
        when(self.console).write("auth").thenReturn('"auth" is:"-2^7"')
        when(self.console).write("auth_owners").thenReturn('"auth_owners" is:"452^7" default:"^7"')
        # WHEN
        self.console.load_conf_frozensand_ban_settings()
        # THEN
        self.assertEqual(1, self.console.load_conf_permban_with_frozensand.call_count)
        self.assertEqual(1, self.console.load_conf_tempban_with_frozensand.call_count)


    def test_auth_off(self):
        # GIVEN
        when(self.console).write("auth").thenReturn('"auth" is:"0^7"')
        when(self.console).write("auth_owners").thenReturn('"auth_owners" is:"452^7" default:"^7"')
        # WHEN
        self.console.load_conf_frozensand_ban_settings()
        # THEN
        self.assertEqual(0, self.console.load_conf_permban_with_frozensand.call_count)
        self.assertEqual(0, self.console.load_conf_tempban_with_frozensand.call_count)


    def test_no_authowners(self):
        # GIVEN
        when(self.console).write("auth").thenReturn('"auth" is:"1^7"')
        when(self.console).write("auth_owners").thenReturn('"auth_owners" is:"^7" default:"^7"')
        # WHEN
        self.console.load_conf_frozensand_ban_settings()
        # THEN
        self.assertEqual(0, self.console.load_conf_permban_with_frozensand.call_count)
        self.assertEqual(0, self.console.load_conf_tempban_with_frozensand.call_count)






@patch("time.sleep")
class Test_ban_with_FrozenSand_auth(Iourt42TestCase):

    def setUp(self):
        Iourt42TestCase.setUp(self)
        self.player = self.console.clients.newClient(cid="4", guid="theGuid", name="theName", ip="11.22.33.44")
        self.player.pbid = "thePlayerAccount"

    #-------------------------------------------------------------------------------------------------------------------
    @staticmethod
    def mock_authban(client, response="auth: sending ban for slot %(cid)s : %(pbid)s", disconnect=True):
        def write(cmd):
            if cmd.startswith("auth-ban %s " % client.cid):
                if disconnect:
                    client.disconnect()
                return response % {'cid': client.cid, 'pbid': client.pbid}
        return write

    @staticmethod
    def mock_authban_no_auth(client):
        return Test_ban_with_FrozenSand_auth.mock_authban(client, response="Auth services disabled", disconnect=False)

    @staticmethod
    def mock_authban_no_authowner(client):
        return Test_ban_with_FrozenSand_auth.mock_authban(client, response="auth: not banlist available. Please set correctly auth_owners.", disconnect=False)
    #-------------------------------------------------------------------------------------------------------------------

    def test_ban_with_frozensand(self, mock_sleep):
        # GIVEN
        self.console._permban_with_frozensand = True
        with patch.object(self.console, "write", wraps=Test_ban_with_FrozenSand_auth.mock_authban(self.player)) as write_mock:
            # WHEN
            self.console.ban(self.player, reason="f00")
        # THEN
        write_mock.assert_has_calls([call('auth-ban 4 0 0 0'),
                                     call('say theName^7 was banned f00')])


    def test_ban_with_frozensand_no_auth(self, mock_sleep):
        # GIVEN
        self.console._permban_with_frozensand = True
        with patch.object(self.console, "write", wraps=Test_ban_with_FrozenSand_auth.mock_authban_no_auth(self.player)) as write_mock:
            # WHEN
            self.console.ban(self.player, reason="f00")
        # THEN
        write_mock.assert_has_calls([call('auth-ban 4 0 0 0'),
                                     call('addip 4'),
                                     call('say theName^7 was banned f00')])



    def test_ban_with_frozensand_no_authowners(self, mock_sleep):
        # GIVEN
        self.console._permban_with_frozensand = True
        with patch.object(self.console, "write", wraps=Test_ban_with_FrozenSand_auth.mock_authban_no_authowner(self.player)) as write_mock:
            # WHEN
            self.console.ban(self.player, reason="f00")
        # THEN
        write_mock.assert_has_calls([call('auth-ban 4 0 0 0'),
                                     call('addip 4'),
                                     call('say theName^7 was banned f00')])


    def test_tempban_with_frozensand_1minute(self, mock_sleep):
        # GIVEN
        self.console._tempban_with_frozensand = True
        with patch.object(self.console, "write", wraps=Test_ban_with_FrozenSand_auth.mock_authban(self.player)) as write_mock:
            # WHEN
            self.console.tempban(self.player, duration="1m", reason="f00")
        # THEN
        write_mock.assert_has_calls([call('auth-ban 4 0 0 1'),
                                     call('say theName^7 was temp banned for 1 minute^7 f00')])


    def test_tempban_with_frozensand_90min(self, mock_sleep):
        # GIVEN
        self.console._tempban_with_frozensand = True
        with patch.object(self.console, "write", wraps=Test_ban_with_FrozenSand_auth.mock_authban(self.player)) as write_mock:
            # WHEN
            self.console.tempban(self.player, duration="90m", reason="f00")
        # THEN
        write_mock.assert_has_calls([call('auth-ban 4 0 1 30'),
                                     call('say theName^7 was temp banned for 1.5 hour^7 f00')])


    def test_tempban_with_frozensand_40days(self, mock_sleep):
        # GIVEN
        self.console._tempban_with_frozensand = True
        with patch.object(self.console, "write", wraps=Test_ban_with_FrozenSand_auth.mock_authban(self.player)) as write_mock:
            # WHEN
            self.console.tempban(self.player, duration="40d", reason="f00")
        # THEN
        write_mock.assert_has_calls([call('auth-ban 4 40 0 0'),
                                     call('say theName^7 was temp banned for 5.7 weeks^7 f00')])



    def test_tempban_with_frozensand_no_auth(self, mock_sleep):
        # GIVEN
        self.console._tempban_with_frozensand = True
        with patch.object(self.console, "write", wraps=Test_ban_with_FrozenSand_auth.mock_authban_no_auth(self.player)) as write_mock:
            # WHEN
            self.console.tempban(self.player, duration="1m", reason="f00")
        # THEN
        write_mock.assert_has_calls([call('auth-ban 4 0 0 1'),
                                     call('kick 4 "f00"'),
                                     call('say theName^7 was temp banned for 1 minute^7 f00')])



    def test_tempban_with_frozensand_no_authowners(self, mock_sleep):
        # GIVEN
        self.console._tempban_with_frozensand = True
        with patch.object(self.console, "write", wraps=Test_ban_with_FrozenSand_auth.mock_authban_no_authowner(self.player)) as write_mock:
            # WHEN
            self.console.tempban(self.player, duration="1m", reason="f00")
        # THEN
        write_mock.assert_has_calls([call('auth-ban 4 0 0 1'),
                                     call('kick 4 "f00"'),
                                     call('say theName^7 was temp banned for 1 minute^7 f00')])





class Test_config(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from b3.parsers.q3a.abstractParser import AbstractParser
        from b3.fake import FakeConsole
        AbstractParser.__bases__ = (FakeConsole,)
        # Now parser inheritance hierarchy is :
        # Iourt42TestCase -> AbstractParser -> FakeConsole -> Parser
        logging.getLogger('output').setLevel(logging.ERROR)


    def setUp(self):
        self.parser_conf = XmlConfigParser()
        self.parser_conf.loadFromString("""<configuration>
                <settings name="server">
                    <set name="game_log"/>
                </settings>
            </configuration>""")
        self.console = Iourt42Parser(self.parser_conf)
        self.console.PunkBuster = None # no Punkbuster support in that game


    def tearDown(self):
        if hasattr(self, "parser"):
            del self.parser.clients
            self.parser.working = False




class Test_load_conf_permban_with_frozensand(Test_config):

    def test_yes(self):
        # GIVEN
        self.parser_conf.loadFromString("""<configuration>
                <settings name="server">
                    <set name="game_log"/>
                    <set name="permban_with_frozensand">yes</set>
                </settings>
            </configuration>""")
        self.console.loadConfig(self.parser_conf)
        self.assertTrue(self.parser_conf.has_option("server", "permban_with_frozensand"))
        # WHEN
        self.console.load_conf_permban_with_frozensand()
        # THEN
        self.assertTrue(self.console._permban_with_frozensand)


    def test_missing(self):
        # GIVEN
        self.parser_conf.loadFromString("""<configuration>
                <settings name="server">
                    <set name="game_log"/>
                </settings>
            </configuration>""")
        self.console.loadConfig(self.parser_conf)
        self.assertFalse(self.parser_conf.has_option("server", "permban_with_frozensand"))
        # WHEN
        self.console.load_conf_permban_with_frozensand()
        # THEN
        self.assertFalse(self.console._permban_with_frozensand)


    def test_empty(self):
        # GIVEN
        self.parser_conf.loadFromString("""<configuration>
                <settings name="server">
                    <set name="game_log"/>
                    <set name="permban_with_frozensand"/>
                </settings>
            </configuration>""")
        self.console.loadConfig(self.parser_conf)
        self.assertTrue(self.parser_conf.has_option("server", "permban_with_frozensand"))
        # WHEN
        self.console.load_conf_permban_with_frozensand()
        # THEN
        self.assertFalse(self.console._permban_with_frozensand)


    def test_no(self):
        # GIVEN
        self.parser_conf.loadFromString("""<configuration>
                <settings name="server">
                    <set name="game_log"/>
                    <set name="permban_with_frozensand">no</set>
                </settings>
            </configuration>""")
        self.console.loadConfig(self.parser_conf)
        self.assertTrue(self.parser_conf.has_option("server", "permban_with_frozensand"))
        # WHEN
        self.console.load_conf_permban_with_frozensand()
        # THEN
        self.assertFalse(self.console._permban_with_frozensand)


    def test_foo(self):
        # GIVEN
        self.parser_conf.loadFromString("""<configuration>
                <settings name="server">
                    <set name="game_log"/>
                    <set name="permban_with_frozensand">foo</set>
                </settings>
            </configuration>""")
        self.console.loadConfig(self.parser_conf)
        self.assertTrue(self.parser_conf.has_option("server", "permban_with_frozensand"))
        # WHEN
        self.console.load_conf_permban_with_frozensand()
        # THEN
        self.assertFalse(self.console._permban_with_frozensand)





class Test_load_conf_tempban_with_frozensand(Test_config):

    def test_yes(self):
        # GIVEN
        self.parser_conf.loadFromString("""<configuration>
                <settings name="server">
                    <set name="game_log"/>
                    <set name="tempban_with_frozensand">yes</set>
                </settings>
            </configuration>""")
        self.console.loadConfig(self.parser_conf)
        self.assertTrue(self.parser_conf.has_option("server", "tempban_with_frozensand"))
        # WHEN
        self.console.load_conf_tempban_with_frozensand()
        # THEN
        self.assertTrue(self.console._tempban_with_frozensand)


    def test_missing(self):
        # GIVEN
        self.parser_conf.loadFromString("""<configuration>
                <settings name="server">
                    <set name="game_log"/>
                </settings>
            </configuration>""")
        self.console.loadConfig(self.parser_conf)
        self.assertFalse(self.parser_conf.has_option("server", "tempban_with_frozensand"))
        # WHEN
        self.console.load_conf_tempban_with_frozensand()
        # THEN
        self.assertFalse(self.console._tempban_with_frozensand)


    def test_empty(self):
        # GIVEN
        self.parser_conf.loadFromString("""<configuration>
                <settings name="server">
                    <set name="game_log"/>
                    <set name="tempban_with_frozensand"/>
                </settings>
            </configuration>""")
        self.console.loadConfig(self.parser_conf)
        self.assertTrue(self.parser_conf.has_option("server", "tempban_with_frozensand"))
        # WHEN
        self.console.load_conf_tempban_with_frozensand()
        # THEN
        self.assertFalse(self.console._tempban_with_frozensand)


    def test_no(self):
        # GIVEN
        self.parser_conf.loadFromString("""<configuration>
                <settings name="server">
                    <set name="game_log"/>
                    <set name="tempban_with_frozensand">no</set>
                </settings>
            </configuration>""")
        self.console.loadConfig(self.parser_conf)
        self.assertTrue(self.parser_conf.has_option("server", "tempban_with_frozensand"))
        # WHEN
        self.console.load_conf_tempban_with_frozensand()
        # THEN
        self.assertFalse(self.console._tempban_with_frozensand)


    def test_foo(self):
        # GIVEN
        self.parser_conf.loadFromString("""<configuration>
                <settings name="server">
                    <set name="game_log"/>
                    <set name="tempban_with_frozensand">foo</set>
                </settings>
            </configuration>""")
        self.console.loadConfig(self.parser_conf)
        self.assertTrue(self.parser_conf.has_option("server", "tempban_with_frozensand"))
        # WHEN
        self.console.load_conf_tempban_with_frozensand()
        # THEN
        self.assertFalse(self.console._tempban_with_frozensand)


class Test_newGetByMagic(Iourt42TestCase):

    def setUp(self):
        Iourt42TestCase.setUp(self)
        self.console.startup()
        self.mike = FakeClient(self.console, name="Mike", guid="000000000000000", pbid="wizard")
        self.john = FakeClient(self.console, name="John", guid="111111111111111", pbid="miles")
        self.matt = FakeClient(self.console, name="Matt", guid="222222222222222", pbid="johndoe")
        self.mark = FakeClient(self.console, name="Mark", guid="333333333333333", pbid="markus")
        self.mike.connects("1")
        self.john.connects("2")
        self.matt.connects("3")
        self.mark.connects("4")

    def test_get_by_name(self):
        # WHEN
        clients = self.console.clients.getByMagic("mike")
        # THEN
        self.assertListEqual(clients, [self.mike])

    def test_get_by_pbid(self):
        # WHEN
        clients = self.console.clients.getByMagic("miles")
        # THEN
        self.assertListEqual(clients, [self.john])

    def test_get_by_name_and_pbid(self):
        # WHEN
        clients = self.console.clients.getByMagic("jo")
        # THEN
        self.assertListEqual(clients, [self.matt, self.john])

    def test_empty_set(self):
        # WHEN
        clients = self.console.clients.getByMagic("asd")
        # THEN
        self.assertListEqual(clients, [])