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
