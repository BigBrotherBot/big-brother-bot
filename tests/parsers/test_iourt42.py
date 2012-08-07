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
from mock import Mock, call, patch
from mockito import mock, verify
import unittest2 as unittest
from b3.config import XmlConfigParser
from b3.events import Event
from b3.fake import FakeClient
from b3.parsers.iourt42 import Iourt42Parser

log = logging.getLogger("test")
log.setLevel(logging.INFO)

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

        self.output_mock = mock()
        # simulate game server actions
        def write(*args, **kwargs):
            pretty_args = map(repr, args) + ["%s=%s" % (k, v) for k, v in kwargs.iteritems()]
            log.info("write(%s)" % ', '.join(pretty_args))
            return self.output_mock.write(*args, **kwargs)
        self.console.write = Mock(wraps=write)

    def tearDown(self):
        self.console.working = False


class Test_inflictCustomPenalty(Iourt42TestCase):
    """
    Called if b3.admin.penalizeClient() does not know a given penalty type.
    Overwrite this to add customized penalties for your game like 'slap', 'nuke',
    'mute', 'kill' or anything you want.
    /!\ This method must return True if the penalty was inflicted.
    """

    def setUp(self):
        Iourt42TestCase.setUp(self)
        self.superman = mock()
        self.superman.cid = "11"

    def test_slap(self):
        self.console.write.reset_mock()
        result = self.console.inflictCustomPenalty('slap', self.superman)
        self.console.write.assert_has_calls([call('slap 11')])
        self.assertTrue(result)

    def test_nuke(self):
        self.console.write.reset_mock()
        result = self.console.inflictCustomPenalty('nuke', self.superman)
        self.console.write.assert_has_calls([call('nuke 11')])
        self.assertTrue(result)

    def test_mute(self):
        self.console.write.reset_mock()
        result = self.console.inflictCustomPenalty('mute', self.superman, duration="15s")
        self.console.write.assert_has_calls([call('mute 11 15.0')])
        self.assertTrue(result)

    def test_kill(self):
        self.console.write.reset_mock()
        result = self.console.inflictCustomPenalty('kill', self.superman)
        self.console.write.assert_has_calls([call('smite 11')])
        self.assertTrue(result)




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

    def setUp(self):
        Iourt42TestCase.setUp(self)
        self.console.startup()
        self.joe = FakeClient(self.console, name="Joe", guid="000000000000000")

    def test_Radio(self):
        self.joe.connects('0')
        self.assertEvent(r'''Radio: 0 - 7 - 2 - "New Alley" - "I'm going for the flag"''',
            event_type='EVT_CLIENT_RADIO',
            event_client=self.joe,
            event_data={'msg_group': '7', 'msg_id': '2', 'location': 'New Alley', 'text': "I'm going for the flag" })

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

    def test_Hit_1(self):
        fatmatic = FakeClient(self.console, name="Fat'Matic", guid="11111111111111")
        d4dou = FakeClient(self.console, name="[FR]d4dou", guid="11111111111111")
        fatmatic.connects('3')
        d4dou.connects('6')
        self.assertEvent(r'''Hit: 6 3 5 8: Fat'Matic hit [FR]d4dou in the Torso''',
            event_type='EVT_CLIENT_DAMAGE',
            event_client=fatmatic,
            event_target=d4dou,
            event_data=(15, '19', '5'))

    def test_Hit_2(self):
        fatmatic = FakeClient(self.console, name="Fat'Matic", guid="11111111111111")
        d4dou = FakeClient(self.console, name="[FR]d4dou", guid="11111111111111")
        fatmatic.connects('3')
        d4dou.connects('6')
        self.assertEvent(r'''Hit: 3 6 9 17: [FR]d4dou hit Fat'Matic in the Legs''',
            event_type='EVT_CLIENT_DAMAGE',
            event_client=d4dou,
            event_target=fatmatic,
            event_data=(15, '35', '9'))



@unittest.skip("need to validate rcon responses from real 4.2 gameserver")
class Test_OnClientuserinfo(Iourt42TestCase):

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



