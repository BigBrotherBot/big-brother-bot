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
from b3.parsers.frostbite.abstractParser import AbstractParser


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
            self.parser.working = False # this tells some parser threads to end


########################################################################################################################
#
#  T E S T    B 3    P A R S E R    A P I    I M P L E M E N T A T I O N
#
########################################################################################################################


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

        self.event_raw_data = ["punkBuster.onMessage", 'servername: Player GUID Computed 03121513135AAFF(-) (slot #12) 11.22.44.33:1254 Snoopy']
        regex_for_OnPBPlayerGuid = [x for (x, y) in self.parser._punkbusterMessageFormats if y == 'OnPBPlayerGuid'][0]
        self.event_match = Mock(wraps=re.match(regex_for_OnPBPlayerGuid, self.event_raw_data[1]))
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

    def test_OnPBPlayerGuid_is_called(self):
        with patch.object(self.parser, "OnPBPlayerGuid") as OnPBPlayerGuid_mock:
            # WHEN
            self.parser.routeFrostbitePacket(self.event_raw_data)
            # THEN
            OnPBPlayerGuid_mock.assert_called_once_with(self.event_match, self.event_raw_data[1])

    def test_OnPBPlayerGuid_saves_client(self):
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





########################################################################################################################
#
#  T E S T    C O N F I G
#
########################################################################################################################



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

