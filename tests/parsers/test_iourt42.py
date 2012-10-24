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
from mockito import mock, when, any as anything
import unittest2 as unittest
from b3.clients import Clients
from b3.config import XmlConfigParser
from b3.events import Event
from b3.fake import FakeClient
from b3.parsers.iourt42 import Iourt42Parser

log = logging.getLogger("test")
log.setLevel(logging.INFO)


# make sure to unpatch the Clients.newClient method
original_newClient = Clients.newClient
def tearDownModule():
    Clients.newClient = original_newClient


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

        self.player = self.console.clients.newClient(cid="4", guid="theGuid", name="theName", ip="11.22.33.44")


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


    def test_say(self):
        marcel = FakeClient(self.console, name="^5Marcel ^2[^6CZARMY^2]", guid="11111111111111")
        marcel.connects('6')
        self.assertEvent(r'''say: 6 ^5Marcel ^2[^6CZARMY^2]: !help''',
            event_type='EVT_CLIENT_SAY',
            event_client=marcel,
            event_data="!help")



class Test_OnClientuserinfo(Iourt42TestCase):

    def setUp(self):
        super(Test_OnClientuserinfo, self).setUp()
        self.console.PunkBuster = None

    def test_ioclient(self):
        infoline = r'''2 \ip\11.22.33.44:27961\challenge\-284496317\qport\13492\protocol\68\name\laCourge\racered\2\raceblue\2\rate\16000\ut_timenudge\0\cg_rgb\128 128 128\cg_predictitems\0\cg_physics\1\cl_anonymous\0\sex\male\handicap\100\color2\5\color1\4\team_headmodel\*james\team_model\james\headmodel\sarge\model\sarge\snaps\20\cg_autoPickup\-1\gear\GLAORWA\authc\0\teamtask\0\cl_guid\00000000011111111122222223333333\weapmodes\00000110220000020002'''
        self.assertFalse('2' in self.console.clients)
        self.console.OnClientuserinfo(action=None, data=infoline)
        self.assertTrue('2' in self.console.clients)
        client = self.console.clients['2']
        self.assertEqual('11.22.33.44', client.ip)
        self.assertEqual('laCourge^7', client.exactName)
        self.assertEqual('laCourge', client.name)
        self.assertEqual('00000000011111111122222223333333', client.guid)

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



class Test_auth(Iourt42TestCase):

    def test_queryClientFrozenSandAccount_authed(self):
        # GIVEN
        when(self.console).write('auth-whois 0').thenReturn(r'''auth: id: 0 - name: ^7laCourge - login: courgette - notoriety: serious - level: -1''')
        # WHEN
        data = self.console.queryClientFrozenSandAccount('0')
        # THEN
        self.assertDictEqual({'cid': '0', 'name': 'laCourge', 'login': 'courgette', 'notoriety': 'serious', 'level': '-1', 'extra': None}, data)

    def test_queryClientFrozenSandAccount_not_active(self):
        # GIVEN
        when(self.console).write('auth-whois 3').thenReturn(r'''Client 3 is not active.''')
        # WHEN
        data = self.console.queryClientFrozenSandAccount('3')
        # THEN
        self.assertDictEqual({}, data)

    def test_queryClientFrozenSandAccount_no_account(self):
        # GIVEN
        when(self.console).write('auth-whois 3').thenReturn(r'''auth: id: 3 - name: ^7laCourge - login:  - notoriety: 0 - level: 0  - ^7no account''')
        # WHEN
        data = self.console.queryClientFrozenSandAccount('3')
        # THEN
        self.assertDictEqual({'cid': '3', 'name': 'laCourge', 'login': '', 'notoriety': '0', 'level': '0', 'extra': '^7no account'}, data)

    def test_queryAllFrozenSandAccount(self):
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





class Test_parser_API(Iourt42TestCase):

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
        self.console.write.assert_has_calls([call('say  f00')])


    def test_saybig(self):
        self.console.saybig("f00")
        self.console.write.assert_has_calls([call('bigtext " f00"')])


    def test_message(self):
        self.console.message(self.player, "f00")
        self.console.write.assert_has_calls(call('tell 4  ^3[pm]^7 f00'))


    def test_kick(self):
        self.console.kick(self.player, reason="f00")
        self.console.write.assert_has_calls([call('kick 4 "f00"'), call('say  theName^7 was kicked f00')])


    def test_ban(self):
        self.console.ban(self.player, reason="f00")
        self.console.write.assert_has_calls([call('addip 4'), call('say  theName^7 was banned f00')])


    def test_unban(self):
        self.console.unban(self.player, reason='f00')
        self.console.write.assert_has_calls([call('removeip 11.22.33.44'),
                                          call('removeip 11.22.33.44'),
                                          call('removeip 11.22.33.44'),
                                          call('removeip 11.22.33.44'),
                                          call('removeip 11.22.33.44')])


    def test_tempban(self):
        self.console.tempban(self.player, reason="f00", duration="1h")
        self.console.write.assert_has_calls([call('kick 4 "f00"'), call('say  theName^7 was temp banned for 1 hour^7 f00')])


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
        when(self.console).write('fdir *.bsp').thenReturn('''\
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
        self.console.write.assert_has_calls([call('say  ^7Changing to next map'), call('cyclemap')])
        sleep_mock.assert_called_once_with(1)


    @patch('time.sleep')
    def test_changeMap(self, sleep_mock):
        # GIVEN
        when(self.output_mock).write('fdir *.bsp').thenReturn("""\
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


    def test_nominal(self):
        # GIVEN
        when(self.console).write("auth").thenReturn('"auth" is:"1^7"')
        when(self.console).write("auth_owners").thenReturn('"auth_owners" is:"452^7" default:"^7"')
        # WHEN
        self.console.load_conf_frozensand_ban_settings()
        # THEN
        self.assertEqual(1, self.console.load_conf_permban_with_frozensand.call_count)
        self.assertEqual(1, self.console.load_conf_tempban_with_frozensand.call_count)


    def test_no_authl(self):
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
                                     call('say  theName^7 was banned f00')])


    def test_ban_with_frozensand_no_auth(self, mock_sleep):
        # GIVEN
        self.console._permban_with_frozensand = True
        with patch.object(self.console, "write", wraps=Test_ban_with_FrozenSand_auth.mock_authban_no_auth(self.player)) as write_mock:
            # WHEN
            self.console.ban(self.player, reason="f00")
        # THEN
        write_mock.assert_has_calls([call('auth-ban 4 0 0 0'),
                                     call('addip 4'),
                                     call('say  theName^7 was banned f00')])



    def test_ban_with_frozensand_no_authowners(self, mock_sleep):
        # GIVEN
        self.console._permban_with_frozensand = True
        with patch.object(self.console, "write", wraps=Test_ban_with_FrozenSand_auth.mock_authban_no_authowner(self.player)) as write_mock:
            # WHEN
            self.console.ban(self.player, reason="f00")
        # THEN
        write_mock.assert_has_calls([call('auth-ban 4 0 0 0'),
                                     call('addip 4'),
                                     call('say  theName^7 was banned f00')])


    def test_tempban_with_frozensand_1minute(self, mock_sleep):
        # GIVEN
        self.console._tempban_with_frozensand = True
        with patch.object(self.console, "write", wraps=Test_ban_with_FrozenSand_auth.mock_authban(self.player)) as write_mock:
            # WHEN
            self.console.tempban(self.player, duration="1m", reason="f00")
        # THEN
        write_mock.assert_has_calls([call('auth-ban 4 0 0 1'),
                                     call('say  theName^7 was temp banned for 1 minute^7 f00')])


    def test_tempban_with_frozensand_90min(self, mock_sleep):
        # GIVEN
        self.console._tempban_with_frozensand = True
        with patch.object(self.console, "write", wraps=Test_ban_with_FrozenSand_auth.mock_authban(self.player)) as write_mock:
            # WHEN
            self.console.tempban(self.player, duration="90m", reason="f00")
        # THEN
        write_mock.assert_has_calls([call('auth-ban 4 0 1 30'),
                                     call('say  theName^7 was temp banned for 1.5 hour^7 f00')])


    def test_tempban_with_frozensand_40days(self, mock_sleep):
        # GIVEN
        self.console._tempban_with_frozensand = True
        with patch.object(self.console, "write", wraps=Test_ban_with_FrozenSand_auth.mock_authban(self.player)) as write_mock:
            # WHEN
            self.console.tempban(self.player, duration="40d", reason="f00")
        # THEN
        write_mock.assert_has_calls([call('auth-ban 4 40 0 0'),
                                     call('say  theName^7 was temp banned for 5.7 weeks^7 f00')])



    def test_tempban_with_frozensand_no_auth(self, mock_sleep):
        # GIVEN
        self.console._tempban_with_frozensand = True
        with patch.object(self.console, "write", wraps=Test_ban_with_FrozenSand_auth.mock_authban_no_auth(self.player)) as write_mock:
            # WHEN
            self.console.tempban(self.player, duration="1m", reason="f00")
        # THEN
        write_mock.assert_has_calls([call('auth-ban 4 0 0 1'),
                                     call('kick 4 "f00"'),
                                     call('say  theName^7 was temp banned for 1 minute^7 f00')])



    def test_tempban_with_frozensand_no_authowners(self, mock_sleep):
        # GIVEN
        self.console._tempban_with_frozensand = True
        with patch.object(self.console, "write", wraps=Test_ban_with_FrozenSand_auth.mock_authban_no_authowner(self.player)) as write_mock:
            # WHEN
            self.console.tempban(self.player, duration="1m", reason="f00")
        # THEN
        write_mock.assert_has_calls([call('auth-ban 4 0 0 1'),
                                     call('kick 4 "f00"'),
                                     call('say  theName^7 was temp banned for 1 minute^7 f00')])





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


