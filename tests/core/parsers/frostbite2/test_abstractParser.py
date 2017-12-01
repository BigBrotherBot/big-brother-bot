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

import logging
import re
import unittest2 as unittest

from mock import Mock, patch, call
from b3.clients import Client
from b3.plugins.admin import AdminPlugin
from b3.config import XmlConfigParser
from b3.parsers.frostbite2.protocol import CommandFailedError
from b3.parsers.frostbite2.abstractParser import AbstractParser

sleep_patcher = None
def setUpModule():
    sleep_patcher = patch("time.sleep")
    sleep_patcher.start()

def tearDownModule():
    if sleep_patcher:
        sleep_patcher.stop()



class ConcretegameParser(AbstractParser):
    gameName = 'thegame'


class AbstractParser_TestCase(unittest.TestCase):
    """
    Test case that is suitable for testing AbstractParser parser specific features
    """

    @classmethod
    def setUpClass(cls):
        from b3.fake import FakeConsole

        AbstractParser.__bases__ = (FakeConsole,)
        # Now parser inheritance hierarchy is :
        # AbstractParser -> FakeConsole -> Parser

    def tearDown(self):
        if hasattr(self, "parser"):
            for c in self.parser.clients.values():
                if hasattr(c, 'messagequeue'):
                    c.messagequeue.queue.clear()
            del self.parser.clients
            self.parser.working = False # this tells some parser threads to end


########################################################################################################################
#
#  T E S T    B 3    P A R S E R    A P I    I M P L E M E N T A T I O N
#
########################################################################################################################
class Test_saybig(AbstractParser_TestCase):
    def setUp(self):
        self.conf = XmlConfigParser()
        self.conf.loadFromString("""
                <configuration>
                </configuration>
            """)
        self.parser = ConcretegameParser(self.conf)
        self.parser._big_msg_duration = '3.1'

        self.write_patcher = patch.object(AbstractParser, 'write')
        self.write_mock = self.write_patcher.start()

    def tearDown(self):
        AbstractParser_TestCase.tearDown(self)
        self.write_patcher.stop()

    def test_saybig_big_msg_repeat_off(self):
        # GIVEN
        self.parser._big_msg_repeat = 'off'
        # WHEN
        self.parser.saybig('test')
        # THEN
        self.assertListEqual([call(('admin.yell', 'test', '3'))], self.write_mock.mock_calls)

    def test_saybig_big_msg_repeat_pm(self):
        # GIVEN
        self.parser._big_msg_repeat = 'pm'
        # WHEN
        self.parser.saybig('test')
        # THEN
        self.assertListEqual([call(('admin.yell', 'test', '3'))], self.write_mock.mock_calls)

    def test_saybig_when_big_msg_repeat_all(self):
        # GIVEN
        self.parser._big_msg_repeat = 'all'
        # WHEN
        self.parser.saybig('test')
        # THEN
        self.assertListEqual([
                                 call(('admin.yell', 'test', '3')),
                                 call(('admin.say', 'test', 'all'))
                             ], self.write_mock.mock_calls)

class Test_message(AbstractParser_TestCase):
    def setUp(self):
        self.conf = XmlConfigParser()

    def init(self, config_content):
        self.conf.loadFromString(config_content)
        self.parser = ConcretegameParser(self.conf)
        self.parser.startup()
        self.parser._big_msg_duration = '3.1'

        self.write_patcher = patch.object(AbstractParser, 'write')
        self.write_mock = self.write_patcher.start()

        self.player_mock = Mock(spec=Client, name="player")
        self.player_mock.cid = 'theplayer'

    def tearDown(self):
        AbstractParser_TestCase.tearDown(self)
        self.write_patcher.stop()


    def test_message__no_big_when_big_msg_repeat_off(self):
        # GIVEN
        self.init("""
            <configuration>
                <settings name="thegame">
                    <set name="big_b3_private_responses">off</set>
                    <set name="big_msg_repeat">off</set>
                </settings>
            </configuration>
        """)
        # WHEN
        self.parser.message(self.player_mock, 'test')
        # THEN
        self.assertListEqual([
                                 call(('admin.say', 'test', 'player', self.player_mock.cid))
                             ], self.write_mock.mock_calls)

    def test_message__no_big_when_big_msg_repeat_pm(self):
        # GIVEN
        self.init("""
            <configuration>
                <settings name="thegame">
                    <set name="big_b3_private_responses">off</set>
                    <set name="big_msg_repeat">pm</set>
                </settings>
            </configuration>
        """)
        # WHEN
        self.parser.message(self.player_mock, 'test')
        # THEN
        self.assertListEqual([
                                 call(('admin.say', 'test', 'player', 'theplayer'))
                             ], self.write_mock.mock_calls)

    def test_message__no_big_when_big_msg_repeat_all(self):
        # GIVEN
        self.init("""
            <configuration>
                <settings name="thegame">
                    <set name="big_b3_private_responses">off</set>
                    <set name="big_msg_repeat">all</set>
                </settings>
            </configuration>
        """)
        # WHEN
        self.parser.message(self.player_mock, 'test')
        # THEN
        self.assertListEqual([
                                 call(('admin.say', 'test', 'player', self.player_mock.cid))
                             ], self.write_mock.mock_calls)


    def test_message__when_big_msg_repeat_off(self):
        # GIVEN
        self.init("""
            <configuration>
                <settings name="thegame">
                    <set name="big_b3_private_responses">on</set>
                    <set name="big_msg_repeat">off</set>
                </settings>
            </configuration>
        """)
        # WHEN
        self.parser.message(self.player_mock, 'test')
        # THEN
        self.assertListEqual([
                                 call(('admin.yell', 'test', '3', 'player', self.player_mock.cid))
                             ], self.write_mock.mock_calls)

    def test_message__when_big_msg_repeat_pm(self):
        # GIVEN
        self.init("""
            <configuration>
                <settings name="thegame">
                    <set name="big_b3_private_responses">on</set>
                    <set name="big_msg_repeat">pm</set>
                </settings>
            </configuration>
        """)
        # WHEN
        self.parser.message(self.player_mock, 'test')
        # THEN
        self.assertListEqual([
                                 call(('admin.yell', 'test', '3', 'player', self.player_mock.cid)),
                                 call(('admin.say', 'test', 'player', 'theplayer'))
                             ], self.write_mock.mock_calls)

    def test_message__when_big_msg_repeat_all(self):
        # GIVEN
        self.init("""
            <configuration>
                <settings name="thegame">
                    <set name="big_b3_private_responses">on</set>
                    <set name="big_msg_repeat">all</set>
                </settings>
            </configuration>
        """)
        # WHEN
        self.parser.message(self.player_mock, 'test')
        # THEN
        self.assertListEqual([
                                 call(('admin.yell', 'test', '3', 'player', self.player_mock.cid)),
                                 call(('admin.say', 'test', 'player', self.player_mock.cid))
                             ], self.write_mock.mock_calls)



class Test_tempban(AbstractParser_TestCase):
    def setUp(self):
        AbstractParser_TestCase.setUp(self)
        log = logging.getLogger('output')
        log.setLevel(logging.NOTSET)

        self.conf = XmlConfigParser()
        self.conf.loadFromString("<configuration/>")
        self.parser = ConcretegameParser(self.conf)
        self.parser.PunkBuster = None
        self.parser.ban_with_server = True

        self.getMessage_patcher = patch.object(self.parser, "getMessage")
        getMessage_mock = self.getMessage_patcher.start()
        getMessage_mock.return_value = ""

        self.foo = Mock(spec=Client)
        self.foo.cid = 'f00'
        self.foo.guid = 'EA_AAABBBBCCCCDDDDEEEEFFFF00000'
        self.foo.name = 'f00'

    def tearDown(self):
        AbstractParser_TestCase.tearDown(self)
        self.getMessage_patcher.stop()


    def test_kick_having_cid_and_guid(self):
        with patch.object(AbstractParser, 'write') as write_mock:
            # GIVEN
            self.assertTrue(self.foo.cid)
            self.assertTrue(self.foo.guid)

            # WHEN
            self.parser.tempban(self.foo)

            # THEN
            self.assertTrue(write_mock.called)
            write_mock.assert_has_calls([call(('banList.add', 'guid', self.foo.guid, 'seconds', '120', ''))])


    def test_kick_having_cid_and_empty_guid(self):
        with patch.object(AbstractParser, 'write') as write_mock:
            # GIVEN
            self.foo.guid = ''
            self.assertTrue(self.foo.cid)
            self.assertFalse(self.foo.guid)

            # WHEN
            self.parser.tempban(self.foo)

            # THEN
            self.assertTrue(write_mock.called)
            write_mock.assert_has_calls([call(('banList.add', 'name', self.foo.name, 'seconds', '120', ''))])


    def test_kick_having_no_cid(self):
        with patch.object(AbstractParser, 'write') as write_mock:
            # GIVEN
            self.foo.cid = None
            self.assertFalse(self.foo.cid)

            # WHEN
            self.parser.tempban(self.foo)

            # THEN
            self.assertTrue(write_mock.called)
            write_mock.assert_has_calls([call(('banList.add', 'guid', self.foo.guid, 'seconds', '120', ''))])



class Test_ban(AbstractParser_TestCase):
    def setUp(self):
        AbstractParser_TestCase.setUp(self)
        log = logging.getLogger('output')
        log.setLevel(logging.NOTSET)

        self.conf = XmlConfigParser()
        self.conf.loadFromString("<configuration/>")
        self.parser = ConcretegameParser(self.conf)
        self.parser.PunkBuster = None
        self.parser.ban_with_server = True

        self.getMessage_patcher = patch.object(self.parser, "getMessage")
        getMessage_mock = self.getMessage_patcher.start()
        getMessage_mock.return_value = ""

        self.foo = Mock(spec=Client)
        self.foo.cid = 'f00'
        self.foo.guid = 'EA_AAABBBBCCCCDDDDEEEEFFFF00000'
        self.foo.name = 'f00'
        self.foo.ip = '11.22.33.44'

    def tearDown(self):
        AbstractParser_TestCase.tearDown(self)
        self.getMessage_patcher.stop()


    def test_kick_having_cid_and_guid(self):
        with patch.object(AbstractParser, 'write') as write_mock:
            # GIVEN
            self.assertTrue(self.foo.cid)
            self.assertTrue(self.foo.guid)

            # WHEN
            self.parser.ban(self.foo)

            # THEN
            self.assertTrue(write_mock.called)
            write_mock.assert_has_calls([call(('banList.add', 'guid', self.foo.guid, 'perm', ''))])


    def test_kick_having_cid_and_empty_guid(self):
        with patch.object(AbstractParser, 'write') as write_mock:
            # GIVEN
            self.foo.guid = ''
            self.assertTrue(self.foo.cid)
            self.assertFalse(self.foo.guid)

            # WHEN
            self.parser.ban(self.foo)

            # THEN
            self.assertTrue(write_mock.called)
            write_mock.assert_has_calls([call(('banList.add', 'name', self.foo.name, 'perm', ''))])


    def test_kick_having_no_cid(self):
        with patch.object(AbstractParser, 'write') as write_mock:
            # GIVEN
            self.foo.cid = None
            self.assertFalse(self.foo.cid)

            # WHEN
            self.parser.ban(self.foo)

            # THEN
            self.assertTrue(write_mock.called)
            write_mock.assert_has_calls([call(('banList.add', 'guid', self.foo.guid, 'perm', ''))])



########################################################################################################################
#
#  T E S T    G A M E    E V E N T S
#
########################################################################################################################
class Test_OnPlayerChat(AbstractParser_TestCase):
    def setUp(self):
        log = logging.getLogger('output')
        log.setLevel(logging.NOTSET)

        self.conf = XmlConfigParser()
        self.conf.loadFromString("""
                <configuration>
                </configuration>
            """)
        self.parser = ConcretegameParser(self.conf)

        self.admin_plugin_mock = Mock(spec=AdminPlugin)
        self.admin_plugin_mock._commands = {}
        self.admin_plugin_mock.cmdPrefix = '!'
        self.admin_plugin_mock.cmdPrefixLoud = '@'
        self.admin_plugin_mock.cmdPrefixBig = '&'
        self.parser.getPlugin = Mock(return_value=self.admin_plugin_mock)

        self.joe = Mock(spec=Client)
        self.parser.getClient = Mock(return_value=self.joe)



    def test_normal_text(self):
        self.assertEqual('foo', self.parser.OnPlayerChat(action=None, data=('joe', 'foo', 'all')).data)
        self.assertEqual('  foo', self.parser.OnPlayerChat(action=None, data=('joe', '  foo', 'all')).data)

    def test_command(self):
        self.assertEqual('!1', self.parser.OnPlayerChat(action=None, data=('joe', '!1', 'all')).data)
        self.assertEqual('!foo', self.parser.OnPlayerChat(action=None, data=('joe', '!foo', 'all')).data)
        self.assertEqual('!!foo', self.parser.OnPlayerChat(action=None, data=('joe', '!!foo', 'all')).data)
        self.assertEqual('@foo', self.parser.OnPlayerChat(action=None, data=('joe', '@foo', 'all')).data)
        self.assertEqual('@@foo', self.parser.OnPlayerChat(action=None, data=('joe', '@@foo', 'all')).data)
        self.assertEqual(r'&foo', self.parser.OnPlayerChat(action=None, data=('joe', r'&foo', 'all')).data)
        self.assertEqual(r'&&foo', self.parser.OnPlayerChat(action=None, data=('joe', r'&&foo', 'all')).data)

    def test_slash_prefix(self):
        self.assertEqual('!1', self.parser.OnPlayerChat(action=None, data=('joe', '/!1', 'all')).data)
        self.assertEqual('!foo', self.parser.OnPlayerChat(action=None, data=('joe', '/!foo', 'all')).data)
        self.assertEqual('@foo', self.parser.OnPlayerChat(action=None, data=('joe', '/@foo', 'all')).data)
        self.assertEqual(r'&foo', self.parser.OnPlayerChat(action=None, data=('joe', r'/&foo', 'all')).data)

    def test_slash_no_prefix_no_command(self):
        self.assertNotIn('non_existing_command', self.admin_plugin_mock._commands)
        self.assertEqual('/non_existing_command', self.parser.OnPlayerChat(action=None, data=('joe', '/non_existing_command', 'all')).data)

    def test_slash_no_prefix_command(self):
        self.admin_plugin_mock._commands['exiting_command'] = Mock()
        self.assertIn('exiting_command', self.admin_plugin_mock._commands)
        self.assertEqual('!exiting_command', self.parser.OnPlayerChat(action=None, data=('joe', '/exiting_command', 'all')).data)
        self.assertEqual('!exiting_command', self.parser.OnPlayerChat(action=None, data=('joe', '!exiting_command', 'all')).data)
        self.admin_plugin_mock._commands['a'] = Mock()
        self.assertIn('a', self.admin_plugin_mock._commands)
        self.assertEqual('!a', self.parser.OnPlayerChat(action=None, data=('joe', '/a', 'all')).data)
        self.assertEqual('!a', self.parser.OnPlayerChat(action=None, data=('joe', '!a', 'all')).data)



########################################################################################################################
#
#  T E S T    P U N K B U S T E R    E V E N T S
#
########################################################################################################################
class Test_OnPBPlayerGuid(AbstractParser_TestCase):
    def setUp(self):
        log = logging.getLogger('output')
        log.setLevel(logging.NOTSET)

        self.conf = XmlConfigParser()
        self.conf.loadFromString("""
                <configuration>
                </configuration>
            """)
        self.parser = ConcretegameParser(self.conf)

        self.event_raw_data = ["punkBuster.onMessage", 'PunkBuster Server: 14 300000aaaaaabbbbbbccccc111223300(-) 11.122.103.24:3659 OK   1 3.0 0 (W) "Snoopy"']
        regex_for_OnPBPlistItem = [x for (x, y) in self.parser._punkbusterMessageFormats if y == 'OnPBPlistItem'][0]
        self.event_match = Mock(wraps=re.match(regex_for_OnPBPlistItem, self.event_raw_data[1]))
        self.event_match.__eq__ = Test_OnPBPlayerGuid.SREMatch_equals

    @staticmethod
    def SREMatch_equals(m1, m2):
        """
        @return True if m1 and m2 could be re.match responses for the same regex and data to match
        """
        if m2 is None:
            return False
        else:
            return m1.groups() == m2.groups()


    def test_OnPBPlistItem_is_called(self):
        with patch.object(self.parser, "OnPBPlistItem") as OnPBPlistItem_mock:
            # WHEN
            self.parser.routeFrostbitePacket(self.event_raw_data)
            # THEN
            OnPBPlistItem_mock.assert_called_once_with(self.event_match, self.event_raw_data[1])

    def test_OnPBPlayerGuid_is_called(self):
        with patch.object(self.parser, "OnPBPlayerGuid") as OnPBPlayerGuid_mock:
            # WHEN
            self.parser.routeFrostbitePacket(self.event_raw_data)
            # THEN
            OnPBPlayerGuid_mock.assert_called_once_with(self.event_match, self.event_raw_data[1])

    def test_OnPBPlayerGuid_saves_client_with_guid(self):
        with patch.object(self.parser, "getClient") as getClient_mock:
            # GIVEN
            snoopy = Mock()
            snoopy.guid = 'EA_AAAAAAAABBBBBBBBBBBBBB00000000000012222'
            getClient_mock.return_value = snoopy
            # WHEN
            self.parser.routeFrostbitePacket(self.event_raw_data)
            # THEN
            getClient_mock.assert_called_once_with("Snoopy")
            snoopy.save.assert_called_once_with()

    def test_OnPBPlayerGuid_does_not_save_client_without_guid(self):
        with patch.object(self.parser, "getClient") as getClient_mock:
            # GIVEN
            snoopy = Mock()
            snoopy.guid = ''
            getClient_mock.return_value = snoopy
            # WHEN
            self.parser.routeFrostbitePacket(self.event_raw_data)
            # THEN
            getClient_mock.assert_called_once_with("Snoopy")
            self.assertFalse(snoopy.save.called)







########################################################################################################################
#
#  T E S T    C O N F I G
#
########################################################################################################################
class Test_config(AbstractParser_TestCase):
    def setUp(self):
        self.conf = XmlConfigParser()
        self.conf.loadFromString("""<configuration/>""")
        self.parser = ConcretegameParser(self.conf)
        log = logging.getLogger('output')
        log.setLevel(logging.DEBUG)



    def assert_big_b3_private_responses(self, expected, config):
        self.parser._big_b3_private_responses = None
        self.conf.loadFromString(config)
        self.parser.load_conf_big_b3_private_responses()
        self.assertEqual(expected, self.parser._big_b3_private_responses)

    def test_big_b3_private_responses_on(self):
        self.assert_big_b3_private_responses(True, """<configuration>
                    <settings name="thegame">
                        <set name="big_b3_private_responses">on</set>
                    </settings>
                </configuration>""")

        self.assert_big_b3_private_responses(False, """<configuration>
                    <settings name="thegame">
                        <set name="big_b3_private_responses">off</set>
                    </settings>
                </configuration>""")

        self.assert_big_b3_private_responses(False, """<configuration>
                    <settings name="thegame">
                        <set name="big_b3_private_responses">off</set>
                    </settings>
                </configuration>""")

        self.assert_big_b3_private_responses(False, """<configuration>
                    <settings name="thegame">
                        <set name="big_b3_private_responses">f00</set>
                    </settings>
                </configuration>""")

        self.assert_big_b3_private_responses(False, """<configuration>
                    <settings name="thegame">
                        <set name="big_b3_private_responses"></set>
                    </settings>
                </configuration>""")


    def assert_big_msg_duration(self, expected, config):
        self.parser._big_msg_duration = None
        self.conf.loadFromString(config)
        self.parser.load_conf_big_msg_duration()
        self.assertEqual(expected, self.parser._big_msg_duration)

    def test_big_msg_duration(self):
        default_value = 4
        self.assert_big_msg_duration(0, """<configuration>
                    <settings name="thegame">
                        <set name="big_msg_duration">0</set>
                    </settings>
                </configuration>""")

        self.assert_big_msg_duration(5, """<configuration>
                    <settings name="thegame">
                        <set name="big_msg_duration">5</set>
                    </settings>
                </configuration>""")

        self.assert_big_msg_duration(default_value, """<configuration>
                    <settings name="thegame">
                        <set name="big_msg_duration">5.6</set>
                    </settings>
                </configuration>""")

        self.assert_big_msg_duration(30, """<configuration>
                    <settings name="thegame">
                        <set name="big_msg_duration">30</set>
                    </settings>
                </configuration>""")

        self.assert_big_msg_duration(default_value, """<configuration>
                    <settings name="thegame">
                        <set name="big_msg_duration">f00</set>
                    </settings>
                </configuration>""")

        self.assert_big_msg_duration(default_value, """<configuration>
                    <settings name="thegame">
                        <set name="big_msg_duration"></set>
                    </settings>
                </configuration>""")

    def assert_big_msg_repeat(self, expected, config):
        self.parser._big_msg_repeat = None
        self.conf.loadFromString(config)
        self.parser.load_conf_big_b3_private_responses()
        self.parser.load_conf_big_msg_repeat()
        self.assertEqual(expected, self.parser._big_msg_repeat)

    def test_big_msg_repeat(self):
        default_value = 'pm'
        self.assert_big_msg_repeat('all', """<configuration>
                    <settings name="thegame">
                        <set name="big_b3_private_responses">on</set>
                        <set name="big_msg_repeat">all</set>
                    </settings>
                </configuration>""")

        self.assert_big_msg_repeat('off', """<configuration>
                    <settings name="thegame">
                        <set name="big_msg_repeat">off</set>
                    </settings>
                </configuration>""")

        self.assert_big_msg_repeat(default_value, """<configuration>
                    <settings name="thegame">
                        <set name="big_b3_private_responses">on</set>
                        <set name="big_msg_repeat">pm</set>
                    </settings>
                </configuration>""")

        self.assert_big_msg_repeat(default_value, """<configuration>
                    <settings name="thegame">
                        <set name="big_b3_private_responses">on</set>
                        <set name="big_msg_repeat"></set>
                    </settings>
                </configuration>""")

        self.assert_big_msg_repeat('off', """<configuration>
                    <settings name="thegame">
                        <set name="big_msg_repeat">OFF</set>
                    </settings>
                </configuration>""")

        self.assert_big_msg_repeat(default_value, """<configuration>
                    <settings name="thegame">
                        <set name="big_b3_private_responses">on</set>
                        <set name="big_msg_repeat">junk</set>
                    </settings>
                </configuration>""")

class Test_config_ban_agent(AbstractParser_TestCase):

    def setUp(self):
        self.conf = XmlConfigParser()
        self.conf.loadFromString("""<configuration/>""")
        self.parser = AbstractParser(self.conf)
        log = logging.getLogger('output')
        log.setLevel(logging.DEBUG)


    def assert_both(self, config):
        self.conf.loadFromString(config)
        self.parser.load_conf_ban_agent()
        self.assertNotEqual(None, self.parser.PunkBuster)
        self.assertTrue(self.parser.ban_with_server)

    def assert_punkbuster(self, config):
        self.conf.loadFromString(config)
        self.parser.load_conf_ban_agent()
        self.assertNotEqual(None, self.parser.PunkBuster)
        self.assertFalse(self.parser.ban_with_server)

    def assert_frostbite(self, config):
        self.conf.loadFromString(config)
        self.parser.load_conf_ban_agent()
        self.assertEqual(None, self.parser.PunkBuster)
        self.assertTrue(self.parser.ban_with_server)

    def test_both(self):
        self.assert_both("""<configuration><settings name="server"><set name="ban_agent">both</set></settings></configuration>""")
        self.assert_both("""<configuration><settings name="server"><set name="ban_agent">BOTH</set></settings></configuration>""")

    def test_punkbuster(self):
        self.assert_punkbuster("""<configuration><settings name="server"><set name="ban_agent">punkbuster</set></settings></configuration>""")
        self.assert_punkbuster("""<configuration><settings name="server"><set name="ban_agent">PUNKBUSTER</set></settings></configuration>""")

    def test_frostbite(self):
        self.assert_frostbite("""<configuration><settings name="server"><set name="ban_agent">server</set></settings></configuration>""")
        self.assert_frostbite("""<configuration><settings name="server"><set name="ban_agent">SERVER</set></settings></configuration>""")

    def test_default(self):
        self.assert_frostbite("""<configuration/>""")
        self.assert_frostbite("""<configuration><settings name="server"><set name="ban_agent"></set></settings></configuration>""")
        self.assert_frostbite("""<configuration><settings name="server"><set name="ban_agent"/></settings></configuration>""")

class Test_bf3_config_message_delay(AbstractParser_TestCase):

    def setUp(self):
        self.conf = XmlConfigParser()
        self.conf.loadFromString("""<configuration/>""")
        self.parser = ConcretegameParser(self.conf)

        self.MESSAGE_DELAY__DEFAULT = self.parser._message_delay
        self.MESSAGE_DELAY__MIN = .5
        self.MESSAGE_DELAY__MAX = 3

        log = logging.getLogger('output')
        log.setLevel(logging.DEBUG)


    def _test_message_delay(self, conf_data=None, expected=None):
        self.conf.loadFromString("""
            <configuration>
                <settings name="thegame">%s</settings>
            </configuration>
            """ % (('<set name="message_delay">%s</set>' % conf_data) if conf_data is not None else ''))
        self.parser.load_config_message_delay()
        if expected:
            self.assertEqual(expected, self.parser._message_delay)


    def test_message_delay__None(self):
        self._test_message_delay(conf_data=None, expected=self.MESSAGE_DELAY__DEFAULT)

    def test_message_delay__empty(self):
        self._test_message_delay(conf_data='', expected=self.MESSAGE_DELAY__DEFAULT)

    def test_message_delay__nan(self):
        self._test_message_delay(conf_data='foo', expected=self.MESSAGE_DELAY__DEFAULT)

    def test_message_delay__too_low(self):
        self._test_message_delay(conf_data=self.MESSAGE_DELAY__MIN-.1, expected=self.MESSAGE_DELAY__MIN)

    def test_message_delay__minimum(self):
        self._test_message_delay(conf_data=self.MESSAGE_DELAY__MIN, expected=self.MESSAGE_DELAY__MIN)

    def test_message_delay__2(self):
        self._test_message_delay(conf_data='2', expected=2)

    def test_message_delay__maximum(self):
        self._test_message_delay(conf_data=self.MESSAGE_DELAY__MAX, expected=self.MESSAGE_DELAY__MAX)

    def test_message_delay__too_high(self):
        self._test_message_delay(conf_data=self.MESSAGE_DELAY__MAX+1, expected=self.MESSAGE_DELAY__MAX)



########################################################################################################################
#
#  T E S T    O T H E R    S T U F F
#
########################################################################################################################
class Map_related_TestCase(AbstractParser_TestCase):
    """
    Test case that controls replies given by the parser write method as follow :

    ## mapList.list
    Responds with the maps found on test class properties 'maps'.
    Response contains 5 maps at most ; to get other maps, you have to use the 'StartOffset' command parameter that appears
    from BF3 R12 release.

    ## mapList.getMapIndices
    Responds with the value of the test class property 'map_indices'.

    ## getEasyName
    Responds with whatever argument was passed to it.

    ## getGameMode
    Responds with whatever argument was passed to it.
    """

    maps = (
        ('MP_001 ', 'ConquestLarge0', '2'),
        ('MP_002 ', 'Rush0', '2'),
        ('MP_003 ', 'ConquestLarge0', '2'),
        )
    map_indices = [1, 2]

    def setUp(self):
        self.conf = XmlConfigParser()
        self.conf.loadFromString("""
                <configuration>
                </configuration>
            """)
        self.parser = ConcretegameParser(self.conf)
        self.parser.startup()

        # simulate responses we can expect from the rcon command mapList.list
        def write(data):
            if type(data) in (tuple, list):
                if data[0].lower() == 'maplist.list':
                    offset = 0
                    if len(data) > 1:
                        try:
                            offset = int(data[1])
                        except ValueError:
                            raise CommandFailedError(['InvalidArguments'])
                            # simulate that the Frostbite2 server responds with 5 maps at most for the mapList.list command
                    maps_to_send = self.__class__.maps[offset:offset + 5]
                    return [len(maps_to_send), 3] + list(reduce(tuple.__add__, maps_to_send, tuple()))
                elif data[0].lower() == 'maplist.getmapindices':
                    return self.__class__.map_indices
            return []

        self.parser.write = Mock(side_effect=write)

        self.parser.getEasyName = Mock(side_effect=lambda x: x)
        self.parser.getGameMode = Mock(side_effect=lambda x: x)



class Test_getNextMap(Map_related_TestCase):
    def test_empty(self):
        # setup context
        Map_related_TestCase.maps = tuple()
        Map_related_TestCase.map_indices = [0, 0]
        self.parser.game.serverinfo = {'roundsTotal': 2}
        self.parser.game.mapName = 'map_foo'
        self.parser.game.gameType = 'gametype_foo'
        # verify
        self.assertEqual('map_foo (gametype_foo) 2 rounds', self.parser.getNextMap())

    def test_one_map(self):
        # setup context
        Map_related_TestCase.maps = (('MP_001', 'ConquestLarge0', '3'),)
        Map_related_TestCase.map_indices = [0, 0]
        # verify
        self.assertEqual('MP_001 (ConquestLarge0) 3 rounds', self.parser.getNextMap())

    def test_two_maps_0(self):
        # setup context
        Map_related_TestCase.maps = (
            ('MP_001', 'ConquestLarge0', '1'),
            ('MP_002', 'Rush0', '1'),
            )
        Map_related_TestCase.map_indices = [0, 0]
        # verify
        self.assertEqual('MP_001 (ConquestLarge0) 1 round', self.parser.getNextMap())

    def test_two_maps_1(self):
        # setup context
        Map_related_TestCase.maps = (
            ('MP_001', 'ConquestLarge0', '2'),
            ('MP_002', 'Rush0', '1'),
            )
        Map_related_TestCase.map_indices = [0, 1]
        # verify
        self.assertEqual('MP_002 (Rush0) 1 round', self.parser.getNextMap())


class Test_getFullMapRotationList(Map_related_TestCase):
    """
    getFullMapRotationList is a method of AbstractParser that calls the Frostbite2 mapList.list command the number of
    times required to obtain the exhaustive list of map in the current rotation list.
    """

    @classmethod
    def setUpClass(cls):
        super(Test_getFullMapRotationList, cls).setUpClass()
        Map_related_TestCase.map_indices = [0, 0]


    def test_empty(self):
        # setup context
        Map_related_TestCase.maps = tuple()
        # verify
        mlb = self.parser.getFullMapRotationList()
        self.assertEqual(0, len(mlb))
        self.assertEqual(1, self.parser.write.call_count)

    def test_one_map(self):
        # setup context
        Map_related_TestCase.maps = (('MP_001', 'ConquestLarge0', '2'),)
        # verify
        mlb = self.parser.getFullMapRotationList()
        self.assertEqual('MapListBlock[MP_001:ConquestLarge0:2]', repr(mlb))
        self.assertEqual(2, self.parser.write.call_count)

    def test_two_maps(self):
        # setup context
        Map_related_TestCase.maps = (
            ('MP_001', 'ConquestLarge0', '2'),
            ('MP_002', 'Rush0', '1'),
            )
        # verify
        mlb = self.parser.getFullMapRotationList()
        self.assertEqual('MapListBlock[MP_001:ConquestLarge0:2, MP_002:Rush0:1]', repr(mlb))
        self.assertEqual(2, self.parser.write.call_count)


    def test_lots_of_maps(self):
        # setup context
        Map_related_TestCase.maps = (
            ('MP_001 ', 'ConquestLarge0', '2'), # first batch
            ('MP_002 ', 'ConquestLarge0', '2'),
            ('MP_003 ', 'ConquestLarge0', '2'),
            ('MP_004 ', 'ConquestLarge0', '2'),
            ('MP_005 ', 'ConquestLarge0', '2'),
            ('MP_006 ', 'ConquestLarge0', '2'), # 2nd
            ('MP_007 ', 'ConquestLarge0', '2'),
            ('MP_008 ', 'ConquestLarge0', '2'),
            ('MP_009 ', 'ConquestLarge0', '2'),
            ('MP_0010', 'ConquestLarge0', '2'),
            ('MP_0011', 'ConquestLarge0', '2'), # 3rd
            ('MP_0012', 'ConquestLarge0', '2'),
            )
        # verify
        mlb = self.parser.getFullMapRotationList()
        self.assertEqual(12, len(mlb))
        # check in details what were the 4 calls made to the write method
        assert [
            ((('mapList.list', 0),), {}),
            ((('mapList.list', 5),), {}),
            ((('mapList.list', 10),), {}),
            ((('mapList.list', 15),), {}),
        ], self.parser.write.call_args_list


class Test_getFullBanList(AbstractParser_TestCase):
    """
    getFullBanList is a method of AbstractParser that calls the Frostbite2 banList.list command the number of
    times required to obtain the exhaustive list of bans.
    """

    bans = (
        ('name', 'Joe', 'perm', '0', '0', 'Banned by admin'),
        ('name', 'Jack', 'rounds', '0', '4', 'tk'),
        ('name', 'Averell', 'seconds', '3576', '0', 'being stupid'),
        ('name', 'William', 'perm', '0', '0', 'hacking'),
        )

    def setUp(self):
        self.conf = XmlConfigParser()
        self.conf.loadFromString("""
                <configuration>
                </configuration>
            """)
        self.parser = ConcretegameParser(self.conf)
        self.parser.startup()

        # simulate responses we can expect from the rcon command mapList.list
        def write(data):
            if type(data) in (tuple, list):
                if data[0].lower() == 'banlist.list':
                    offset = 0
                    if len(data) > 1:
                        try:
                            offset = int(data[1])
                        except ValueError:
                            raise CommandFailedError(['InvalidArguments'])
                            # simulate that the Frostbite2 server responds with 5 bans at most for the banList.list command
                    bans_to_send = self.__class__.bans[offset:offset + 5]
                    return list(reduce(tuple.__add__, bans_to_send, tuple()))
            return []

        self.parser.write = Mock(side_effect=write)




    def test_empty(self):
        # setup context
        self.__class__.bans = tuple()
        # verify
        bl = self.parser.getFullBanList()
        self.assertEqual(0, len(bl))
        self.assertEqual(1, self.parser.write.call_count)

    def test_one_ban(self):
        # setup context
        self.__class__.bans = (('name', 'Foo1 ', 'perm', '0', '0', 'Banned by admin'),)
        # verify
        mlb = self.parser.getFullBanList()
        self.assertEqual(
            "BanlistContent[{'idType': 'name', 'seconds_left': '0', 'reason': 'Banned by admin', 'banType': 'perm', 'rounds_left': '0', 'id': 'Foo1 '}]"
            , repr(mlb))
        self.assertEqual(2, self.parser.write.call_count)

    def test_two_bans(self):
        # setup context
        self.__class__.bans = (
            ('name', 'Foo1 ', 'perm', '0', '0', 'Banned by admin'),
            ('name', 'Foo2 ', 'perm', '0', '0', 'Banned by admin'),
            )
        # verify
        mlb = self.parser.getFullBanList()
        self.assertEqual("BanlistContent[{'idType': 'name', 'seconds_left': '0', 'reason': 'Banned by admin', 'banType': 'perm', 'rounds_left': '0', 'id': 'Foo1 '}, \
{'idType': 'name', 'seconds_left': '0', 'reason': 'Banned by admin', 'banType': 'perm', 'rounds_left': '0', 'id': 'Foo2 '}]"
            , repr(mlb))
        self.assertEqual(2, self.parser.write.call_count)


    def test_lots_of_bans(self):
        # setup context
        self.__class__.bans = (
            ('name', 'Foo1 ', 'perm', '0', '0', 'Banned by admin'),
            ('name', 'Foo2 ', 'perm', '0', '0', 'Banned by admin'),
            ('name', 'Foo3 ', 'perm', '0', '0', 'Banned by admin'),
            ('name', 'Foo4 ', 'perm', '0', '0', 'Banned by admin'),
            ('name', 'Foo5 ', 'perm', '0', '0', 'Banned by admin'),
            ('name', 'Foo6 ', 'perm', '0', '0', 'Banned by admin'),
            ('name', 'Foo7 ', 'perm', '0', '0', 'Banned by admin'),
            ('name', 'Foo8 ', 'perm', '0', '0', 'Banned by admin'),
            ('name', 'Foo9 ', 'perm', '0', '0', 'Banned by admin'),
            )
        # verify
        mlb = self.parser.getFullBanList()
        self.assertEqual(9, len(mlb))
        # check in details what were the 3 calls made to the write method
        assert [
            ((('banList.list', 0),), {}),
            ((('banList.list', 5),), {}),
            ((('banList.list', 10),), {}),
        ], self.parser.write.call_args_list


class Test_patch_b3_clients_getByMagic(AbstractParser_TestCase):
    def setUp(self):
        self.conf = XmlConfigParser()
        self.conf.loadFromString("""
                <configuration>
                </configuration>
            """)
        self.parser = ConcretegameParser(self.conf)
        # setup context
        self.foobar = self.parser.clients.newClient(cid='Foobar', name='Foobar', guid="aaaaaaa5555555")
        self.joe = self.parser.clients.newClient(cid='joe', name='joe', guid="bbbbbbbb5555555")
        self.jack = self.parser.clients.newClient(cid='jack', name='jack', guid="ccccccccc5555555")
        self.jacky = self.parser.clients.newClient(cid='jacky', name='jacky', guid="ddddddddd5555555")
        self.p123456 = self.parser.clients.newClient(cid='123456', name='123456', guid="eeeeeee5555555")


    def test_exact_name(self):
        self.assertEqual([self.foobar], self.parser.clients.getByMagic('Foobar'))
        self.assertEqual([self.foobar], self.parser.clients.getByMagic('fOObAr'))

    def test_partial_name(self):
        self.assertEqual([self.foobar], self.parser.clients.getByMagic('foo'))
        self.assertEqual([self.foobar], self.parser.clients.getByMagic('oba'))
        self.assertSetEqual(set([self.jacky, self.jack]), set(self.parser.clients.getByMagic('jac')))
        self.assertSetEqual(set([self.jacky, self.jack]), set(self.parser.clients.getByMagic('jack')))

    def test_player_123456_with_exact_name(self):
        self.assertEqual([self.p123456], self.parser.clients.getByMagic('123456'))

    def test_player_123456_with_partial_name(self):
        """
        This test will fail if the b3.clients.Clients.getByMagic method was not patched
        """
        self.assertEqual([self.p123456], self.parser.clients.getByMagic('345'))


class Test_patch_b3_client_yell(AbstractParser_TestCase):
    def setUp(self):
        self.conf = XmlConfigParser()
        self.conf.loadFromString("""
                <configuration>
                </configuration>
            """)
        self.parser = ConcretegameParser(self.conf)
        self.parser._big_msg_duration = '3.1'
        # setup context
        self.joe = self.parser.clients.newClient(cid='joe', name='joe', guid="bbbbbbbb5555555")


    def test_client_yell(self):
        with patch.object(AbstractParser, 'write') as write_mock:

            self.joe.yell('test')
            self.joe.yell('test2')
            self.joe.yell('test3')

            self.assertTrue(write_mock.called)
            write_mock.assert_any_call(('admin.yell', '[pm] test', '3', 'player', 'joe'))
            write_mock.assert_any_call(('admin.yell', '[pm] test2', '3', 'player', 'joe'))
            write_mock.assert_any_call(('admin.yell', '[pm] test3', '3', 'player', 'joe'))


