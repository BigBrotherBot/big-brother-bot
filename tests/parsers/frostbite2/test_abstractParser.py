#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2011 Courgette
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

import unittest
from mock import Mock
from tests import B3TestCase
from b3.config import XmlConfigParser
from b3.parsers.frostbite2.protocol import CommandFailedError
from b3.parsers.frostbite2.abstractParser import AbstractParser



class AbstractParser_TestCase(B3TestCase):
    """
    Test case that is suitable for testing AbstractParser parser specific features
    """

    @classmethod
    def setUpClass(cls):
        from b3.parsers.frostbite2.abstractParser import AbstractParser
        from b3.fake import FakeConsole
        AbstractParser.__bases__ = (FakeConsole,)
        # Now parser inheritance hierarchy is :
        # AbstractParser -> FakeConsole -> Parser



class Write_controlled_TestCase(AbstractParser_TestCase):
    """
    Test case that controls replies given by the parser write method as follow :

    ## mapList.list
    Responds with the maps found on class properties 'maps'.
    Response contains 5 maps at most ; to get other maps, you have to use the 'StartOffset' command parameter that appears
    from BF3 R12 release.

    ## mapList.getMapIndices
    Responds with the value of the class property 'map_indices'.

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
        self.parser = AbstractParser(self.conf)
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
                    maps_to_send = self.__class__.maps[offset:offset+5]
                    return [len(maps_to_send), 3] + list(reduce(tuple.__add__, maps_to_send, tuple()))
                elif data[0].lower() == 'maplist.getmapindices':
                    return self.__class__.map_indices
            return []
        self.parser.write = Mock(side_effect=write)

        self.parser.getEasyName = Mock(side_effect=lambda x:x)
        self.parser.getGameMode = Mock(side_effect=lambda x:x)



class Test_getNextMap(Write_controlled_TestCase):

    def test_empty(self):
        # setup context
        Write_controlled_TestCase.maps = tuple()
        Write_controlled_TestCase.map_indices = [0, 0]
        self.parser.game.mapName = 'map_foo'
        self.parser.game.gameType = 'gametype_foo'
        # verify
        self.assertEqual('%s (%s)' % (self.parser.game.mapName, self.parser.game.gameType), self.parser.getNextMap())

    def test_one_map(self):
        # setup context
        Write_controlled_TestCase.maps = (('MP_001', 'ConquestLarge0', '2'),)
        Write_controlled_TestCase.map_indices = [0, 0]
        # verify
        self.assertEqual('MP_001 (ConquestLarge0)', self.parser.getNextMap())

    def test_two_maps_0(self):
        # setup context
        Write_controlled_TestCase.maps = (
            ('MP_001', 'ConquestLarge0', '2'),
            ('MP_002', 'Rush0', '1'),
        )
        Write_controlled_TestCase.map_indices = [0, 0]
        # verify
        self.assertEqual('MP_001 (ConquestLarge0)', self.parser.getNextMap())

    def test_two_maps_1(self):
        # setup context
        Write_controlled_TestCase.maps = (
            ('MP_001', 'ConquestLarge0', '2'),
            ('MP_002', 'Rush0', '1'),
        )
        Write_controlled_TestCase.map_indices = [0, 1]
        # verify
        self.assertEqual('MP_002 (Rush0)', self.parser.getNextMap())




class Test_getFullMapRotationList(Write_controlled_TestCase):
    """
    getFullMapRotationList is a method of AbstractParser that calls the Frostbite2 mapList.list command the number of
    times required to obtain the exhaustive list of map in the current rotation list.
    """

    @classmethod
    def setUpClass(cls):
        super(Test_getFullMapRotationList, cls).setUpClass()
        Write_controlled_TestCase.map_indices = [0, 0]


    def test_empty(self):
        # setup context
        Write_controlled_TestCase.maps = tuple()
        # verify
        mlb = self.parser.getFullMapRotationList()
        self.assertEqual(0, len(mlb))
        self.assertEqual(1, self.parser.write.call_count)

    def test_one_map(self):
        # setup context
        Write_controlled_TestCase.maps = (('MP_001', 'ConquestLarge0', '2'),)
        # verify
        mlb = self.parser.getFullMapRotationList()
        self.assertEqual('MapListBlock[MP_001:ConquestLarge0:2]', repr(mlb))
        self.assertEqual(2, self.parser.write.call_count)

    def test_two_maps(self):
        # setup context
        Write_controlled_TestCase.maps = (
            ('MP_001', 'ConquestLarge0', '2'),
            ('MP_002', 'Rush0', '1'),
            )
        # verify
        mlb = self.parser.getFullMapRotationList()
        self.assertEqual('MapListBlock[MP_001:ConquestLarge0:2, MP_002:Rush0:1]', repr(mlb))
        self.assertEqual(2, self.parser.write.call_count)


    def test_lots_of_maps(self):
        # setup context
        Write_controlled_TestCase.maps = (
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



class Test_getFullBanList(Write_controlled_TestCase):
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
        self.parser = AbstractParser(self.conf)
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
                    bans_to_send = self.__class__.bans[offset:offset+5]
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
        self.assertEqual("BanlistContent[{'idType': 'name', 'seconds_left': '0', 'reason': 'Banned by admin', 'banType': 'perm', 'rounds_left': '0', 'id': 'Foo1 '}]", repr(mlb))
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
{'idType': 'name', 'seconds_left': '0', 'reason': 'Banned by admin', 'banType': 'perm', 'rounds_left': '0', 'id': 'Foo2 '}]", repr(mlb))
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
        self.parser = AbstractParser(self.conf)
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