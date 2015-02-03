# coding=UTF-8
#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2014 Courgette
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
#

import os
import sys
import unittest2 as unittest

from mock import Mock
from mock import patch
from mock import call
from mockito import when
from b3 import TEAM_BLUE
from b3 import TEAM_RED
from b3 import TEAM_UNKNOWN
from b3 import TEAM_SPEC
from b3.clients import Client
from b3.config import XmlConfigParser
from b3.config import CfgConfigParser
from b3.fake import FakeClient
from b3.parsers.insurgency import InsurgencyParser
from b3.parsers.insurgency import GAME_MODES_FOR_MAP
from b3.plugins.admin import AdminPlugin
from b3 import __file__ as b3_module__file__

ADMIN_CONFIG_FILE = os.path.normpath(os.path.join(os.path.dirname(b3_module__file__), "conf/plugin_admin.ini"))

STATUS_RESPONSE = '''\
hostname: Courgette's Server
version : 1.17.5.1/11751 5038 secure
udp/ip  : 11.23.32.44:27015  (public ip: 11.23.32.44)
os      :  Linux
type    :  community dedicated
map     : cs_foobar
players : 1 humans, 10 bots (20/20 max) (not hibernating)

# userid name uniqueid connected ping loss state rate adr
#224 "Moe" BOT active
# 194 2 "courgette" STEAM_1:0:1111111 33:48 67 0 active 20000 11.222.111.222:27005
#225 "Quintin" BOT active
#226 "Kurt" BOT active
#227 "Arnold" BOT active
#228 "Rip" BOT active
#229 "Zach" BOT active
#230 "Wolf" BOT active
#231 "Minh" BOT active
#232 "Ringo" BOT active
#233 "Quade" BOT active
#end
L 08/28/2012 - 01:28:40: rcon from "11.222.111.222:4181": command "status"
'''

def client_equal(client_a, client_b):
    if client_a is None and client_b is not None:
        return False
    if client_a is not None and client_b is None:
        return False
    #    for p in ('cid', 'guid', 'name', 'ip', 'ping'):
    #        if client_a.get(p, None) != client_b.get(p, None):
    #            return False
    return all(
        map(lambda x: getattr(client_a, x, None) == getattr(client_b, x, None), ('cid', 'guid', 'name', 'ip', 'ping')))

    #return True

WHATEVER = object()  # sentinel used in InsurgencyTestCase.assert_has_event

class InsurgencyTestCase(unittest.TestCase):
    """
    Test case that is suitable for testing Insurgency parser specific features
    """

    @classmethod
    def setUpClass(cls):
        from b3.fake import FakeConsole
        InsurgencyParser.__bases__ = (FakeConsole,)
        # Now parser inheritance hierarchy is :
        # InsurgencyParser -> FakeConsole -> Parser

    def setUp(self):
        self.status_response = None  # defaults to STATUS_RESPONSE module attribute
        self.conf = XmlConfigParser()
        self.conf.loadFromString("""<configuration></configuration>""")
        self.parser = InsurgencyParser(self.conf)
        self.parser.output = Mock()
        self.parser.output.write = Mock(wraps=self.output_write)
        when(self.parser).is_sourcemod_installed().thenReturn(True)

        self.evt_queue = []

        def queue_event(evt):
            self.evt_queue.append(evt)

        self.queueEvent_patcher = patch.object(self.parser, "queueEvent", wraps=queue_event)
        self.queueEvent_mock = self.queueEvent_patcher.start()
        self.parser.startup()

    def tearDown(self):
        self.queueEvent_patcher.stop()
        if hasattr(self, "parser"):
            del self.parser.clients
            self.parser.working = False

    def clear_events(self):
        """
        clear the event queue, so when assert_has_event is called, it will look only at the newly caught events.
        """
        self.evt_queue = []

    def assert_has_event(self, event_type, data=WHATEVER, client=WHATEVER, target=WHATEVER):
        """
        assert that self.evt_queue contains at least one event for the given type that has the given characteristics.
        """
        assert isinstance(event_type, basestring)
        expected_event = self.parser.getEvent(event_type, data, client, target)

        if not len(self.evt_queue):
            self.fail("expecting %s. Got no event instead" % expected_event)
        elif len(self.evt_queue) == 1:
            actual_event = self.evt_queue[0]
            self.assertEqual(expected_event.type, actual_event.type)
            if data != WHATEVER:
                self.assertEqual(expected_event.data, actual_event.data)
            if client != WHATEVER:
                self.assertTrue(client_equal(expected_event.client, actual_event.client))
            if target != WHATEVER:
                self.assertTrue(client_equal(expected_event.target, actual_event.target))
        else:
            for evt in self.evt_queue:
                if expected_event.type == evt.type \
                        and (expected_event.data == evt.data or data == WHATEVER) \
                        and (client_equal(expected_event.client, evt.client) or client == WHATEVER) \
                        and (client_equal(expected_event.target, evt.target) or target == WHATEVER):
                    return

            self.fail("expecting event %s. Got instead: %s" % (expected_event, map(str, self.evt_queue)))

    def assert_has_not_event(self, event_type, data=None, client=None, target=None):
        """
        assert that self.evt_queue does not contain at least one event for the given type that has the given characteristics.
        """
        assert isinstance(event_type, basestring)
        unexpected_event = self.parser.getEvent(event_type, data, client, target)

        if not len(self.evt_queue):
            return
        else:
            def event_match(evt):
                return (
                    unexpected_event.type == evt.type
                    and (data is None or data == evt.data)
                    and (client is None or client_equal(client, evt.client))
                    and (target is None or client_equal(target, evt.target))
                )

            if any(map(event_match, self.evt_queue)):
                self.fail("not expecting event %s" % (filter(event_match, self.evt_queue)))

    def output_write(self, *args, **kwargs):
        """
        Used to override parser self.output.write method so we can control the
        response given to the 'status' rcon command
        """
        if len(args) and args[0] == "status":
            if self.status_response is not None:
                return self.status_response
            else:
                return STATUS_RESPONSE


class AdminTestCase(unittest.TestCase):
    """
    Test case that is suitable for testing Insurgency parser specific features with the B3 admin plugin available
    """

    @classmethod
    def setUpClass(cls):
        from b3.fake import FakeConsole
        InsurgencyParser.__bases__ = (FakeConsole,)
        # Now parser inheritance hierarchy is :
        # InsurgencyParser -> FakeConsole -> Parser

    def setUp(self):
        self.status_response = None  # defaults to STATUS_RESPONSE module attribute
        self.conf = XmlConfigParser()
        self.conf.loadFromString("""<configuration></configuration>""")
        self.parser = InsurgencyParser(self.conf)
        self.parser.output = Mock()
        self.parser.output.write = Mock(wraps=sys.stdout.write)
        when(self.parser).is_sourcemod_installed().thenReturn(True)
        adminPlugin_conf = CfgConfigParser()
        adminPlugin_conf.load(ADMIN_CONFIG_FILE)
        adminPlugin = AdminPlugin(self.parser, adminPlugin_conf)
        adminPlugin.onLoadConfig()
        adminPlugin.onStartup()
        when(self.parser).getPlugin('admin').thenReturn(adminPlugin)
        when(self.parser).getAllAvailableMaps().thenReturn(GAME_MODES_FOR_MAP.keys())
        self.parser.startup()
        self.parser.patch_b3_admin_plugin() # seems that without this the test module doesn't patch the admin plugin

    def tearDown(self):
        if hasattr(self, "parser"):
            del self.parser.clients
            self.parser.working = False


class Test_gamelog_parsing(InsurgencyTestCase):

    def test_client_say(self):
        # GIVEN
        player = FakeClient(self.parser, name="courgette", guid="STEAM_1:0:1111111", team=TEAM_BLUE)
        player.connects("3")
        # WHEN
        self.clear_events()
        self.parser.parseLine('''L 04/01/2014 - 12:56:51: "courgette<3><STEAM_1:0:1111111><#Team_Security>" say "!pb @531 rule1"''')
        # THEN
        self.assert_has_event("EVT_CLIENT_SAY", "!pb @531 rule1", player)


class Test_parser_other(InsurgencyTestCase):

    def test_getTeam(self):
        self.assertEqual(TEAM_RED, self.parser.getTeam('#Team_Security'))
        self.assertEqual(TEAM_BLUE, self.parser.getTeam('#Team_Insurgent'))
        self.assertEqual(TEAM_SPEC, self.parser.getTeam('#Team_Spectators'))
        self.assertEqual(TEAM_UNKNOWN, self.parser.getTeam('#Team_Unassigned'))

class FunctionalTest(AdminTestCase):

    def test_permban(self):
        # GIVEN
        superadmin = FakeClient(self.parser, name="superadmin", guid="guid_superadmin", groupBits=128, team=TEAM_UNKNOWN)
        superadmin.connects("1")
        bill = FakeClient(self.parser, name="bill", guid="guid_bill", team=TEAM_UNKNOWN)
        bill.connects("2")
        # WHEN
        superadmin.says("!permban bill rule1")
        # THEN
        superadmin.says('!baninfo @%s' % bill.id)
        self.assertListEqual(['Banned: bill (@2) has been added to banlist', 'bill has 1 active bans',], superadmin.message_history)

    def test_map_with_no_parameters(self):
        # GIVEN
        superadmin = FakeClient(self.parser, name="superadmin", guid="guid_superadmin", groupBits=128, team=TEAM_UNKNOWN)
        superadmin.connects("1")
        # WHEN
        superadmin.says("!map")
        # THEN
        self.assertListEqual(["Fully supported map names are : " + ', '.join(m for m in GAME_MODES_FOR_MAP.keys()),
                              "You can use these with the optional '-force' parameter, which will disable map/gamemode "
                              "pair checking and will need a server restart if an invalid pairing is given:",
                              "For more help, type !help map"],
                             superadmin.message_history)

    def test_map_with_invalid_map_name(self):
        # GIVEN
        superadmin = FakeClient(self.parser, name="superadmin", guid="guid_superadmin", groupBits=128, team=TEAM_UNKNOWN)
        superadmin.connects("1")
        # WHEN
        superadmin.says("!map blargh blub")
        # THEN
        self.assertListEqual(["do you mean : buhriz, district, sinjar, siege, uprising, ministry, revolt, heights, "
                              "contact, peak, panj, market ?"], superadmin.message_history)

    def test_map_with_correct_parameters(self):
         # GIVEN
         superadmin = FakeClient(self.parser, name="superadmin", guid="guid_superadmin", groupBits=128, team=TEAM_UNKNOWN)
         superadmin.connects("1")
         # WHEN
         superadmin.says("!map market push")
         # THEN
         self.parser.output.write.assert_has_calls([call('changelevel market push')])

    def test_say(self):
        self.parser.msgPrefix = "[Pre]"
        with patch.object(self.parser.output, 'write') as write_mock:
            self.parser.say("f00")
            write_mock.assert_has_calls([call('sm_say [Pre] f00')])

    def test_say_with_color_codes(self):
        self.parser.msgPrefix = "[Pre]"
        with patch.object(self.parser.output, 'write') as write_mock:
            self.parser.say("^7message ^1with ^2color ^8codes")
            write_mock.assert_has_calls([call('sm_say [Pre] message with color codes')])

    def test_saybig(self):
        self.parser.msgPrefix = "[Pre]"
        with patch.object(self.parser.output, 'write') as write_mock:
            self.parser.saybig("f00")
            write_mock.assert_has_calls([call('sm_hsay [Pre] f00')])

    def test_saybig_with_color_codes(self):
        self.parser.msgPrefix = "[Pre]"
        with patch.object(self.parser.output, 'write') as write_mock:
            self.parser.saybig("^7message ^1with ^2color ^8codes")
            write_mock.assert_has_calls([call('sm_hsay [Pre] message with color codes')])

#    @unittest.skipIf(WAS_FROSTBITE_LOADED, "Frostbite(1|2) parsers monkey patch the Client class and make this test fail")
    def test_message(self):
        self.parser.msgPrefix = "[Pre]"
        player = Client(console=self.parser, guid="theGuid")
        with patch.object(self.parser.output, 'write') as write_mock:
            player.message("f00")
            write_mock.assert_has_calls([call('sm_psay #theGuid "[Pre] f00"')])

    def test_message_with_color_codes(self):
        self.parser.msgPrefix = "[Pre]"
        player = Client(console=self.parser, guid="theGuid")
        with patch.object(self.parser.output, 'write') as write_mock:
            player.message("^7message ^1with ^2color ^8codes")
            write_mock.assert_has_calls([call('sm_psay #theGuid "[Pre] message with color codes"')])

class Test_getClientOrCreate(InsurgencyTestCase):

    def test_changing_team(self):
        # GIVEN
        client = self.parser.getClientOrCreate(cid="2", guid="AAAAAAAAAAAA000000000000000", name="theName", team="#Team_Security")
        self.assertEqual(TEAM_RED, client.team)

        def assertTeam(excepted_team, new_team):
            # WHEN
            self.parser.getClientOrCreate(cid="2", guid="AAAAAAAAAAAA000000000000000", name="theName", team=new_team)
            # THEN
            self.assertEqual(excepted_team, client.team)

        assertTeam(TEAM_RED, "#Team_Security")
        assertTeam(TEAM_RED, None)
        assertTeam(TEAM_RED, "")
        assertTeam(TEAM_RED, "f00")
        assertTeam(TEAM_RED, "#Team_Unassigned")
        assertTeam(TEAM_BLUE, "#Team_Insurgent")