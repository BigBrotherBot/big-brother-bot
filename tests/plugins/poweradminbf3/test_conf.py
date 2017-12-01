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
from textwrap import dedent
from mock import Mock, call

from b3.plugins.poweradminbf3 import Poweradminbf3Plugin, __file__ as poweradminbf3_file
from b3.config import CfgConfigParser

from tests.plugins.poweradminbf3  import Bf3TestCase

class Test_conf(Bf3TestCase):

    def setUp(self):
        Bf3TestCase.setUp(self)
        self.conf = CfgConfigParser()
        self.p = Poweradminbf3Plugin(self.console, self.conf)
        logger = logging.getLogger('output')
        logger.setLevel(logging.INFO)


class Test_common(Test_conf):

    def test_1(self):
        self.conf.loadFromString("""[foo]""")
        self.p.onLoadConfig()
        # should not raise any error

    def test_issue_12(self):
        """See https://github.com/courgette/b3-plugin-poweradminbf3/issues/12"""
        self.conf.loadFromString("""[commands]
setmode-mode: 60
roundnext-rnext: 40
roundrestart-rrestart: 40
kill: 40
changeteam: 20
swap: 20
setnextmap-snmap: 20

[messages]
operation_denied: Operation denied
operation_denied_level: Operation denied because %(name)s is in the %(group)s group
        """)
        self.p._load_scrambler()
        # should not raise any error


class Test_load_scrambler__mode(Test_conf):

    def test_no_section(self):
        self.conf.loadFromString("""[foo]""")
        self.p._load_scrambler()
        self.assertFalse(self.p._autoscramble_rounds)
        self.assertFalse(self.p._autoscramble_maps)

    def test_no_option(self):
        self.conf.loadFromString("""
[scrambler]
""")
        self.p._load_scrambler()
        self.assertFalse(self.p._autoscramble_rounds)
        self.assertFalse(self.p._autoscramble_maps)

    def test_empty_option(self):
        self.conf.loadFromString("""
[scrambler]
mode: """)
        self.p._load_scrambler()
        self.assertFalse(self.p._autoscramble_rounds)
        self.assertFalse(self.p._autoscramble_maps)

    def test_bad_option(self):
        self.conf.loadFromString("""
[scrambler]
mode: foo""")
        self.p._load_scrambler()
        self.assertFalse(self.p._autoscramble_rounds)
        self.assertFalse(self.p._autoscramble_maps)

    def test_off(self):
        self.conf.loadFromString("""
[scrambler]
mode: off""")
        self.p._load_scrambler()
        self.assertFalse(self.p._autoscramble_rounds)
        self.assertFalse(self.p._autoscramble_maps)

    def test_round(self):
        self.conf.loadFromString("""
[scrambler]
mode: round""")
        self.p._load_scrambler()
        self.assertTrue(self.p._autoscramble_rounds)
        self.assertFalse(self.p._autoscramble_maps)

    def test_map(self):
        self.conf.loadFromString("""
[scrambler]
mode: map""")
        self.p._load_scrambler()
        self.assertFalse(self.p._autoscramble_rounds)
        self.assertTrue(self.p._autoscramble_maps)



class Test_load_scrambler__strategy(Test_conf):

    def setUp(self):
        super(Test_load_scrambler__strategy, self).setUp()
        self.setSTragegy_mock = self.p._scrambler.setStrategy = Mock(name="setStrategy", wraps=self.p._scrambler.setStrategy)

    def test_no_section(self):
        self.conf.loadFromString("""[foo]""")
        self.p._load_scrambler()
        self.setSTragegy_mock.assert_called_once_with('random')

    def test_no_option(self):
        self.conf.loadFromString("""
[scrambler]
""")
        self.p._load_scrambler()
        self.setSTragegy_mock.assert_called_once_with('random')

    def test_empty_option(self):
        self.conf.loadFromString("""
[scrambler]
strategy: """)
        self.p._load_scrambler()
        self.setSTragegy_mock.assert_has_calls([call(''), call('random')])

    def test_bad_option(self):
        self.conf.loadFromString("""
[scrambler]
strategy: foo""")
        self.p._load_scrambler()
        self.setSTragegy_mock.assert_has_calls([call('foo'), call('random')])


    def test_random(self):
        self.conf.loadFromString("""
[scrambler]
strategy: random""")
        self.p._load_scrambler()
        self.setSTragegy_mock.assert_called_once_with('random')

    def test_score(self):
        self.conf.loadFromString("""
[scrambler]
strategy: score""")
        self.p._load_scrambler()
        self.setSTragegy_mock.assert_called_once_with('score')




class Test_load_scrambler__gamemodes_blacklist(Test_conf):

    def test_no_section(self):
        self.conf.loadFromString("""[foo]""")
        self.p._load_scrambler()
        self.assertEqual([], self.p._autoscramble_gamemode_blacklist)

    def test_no_option(self):
        self.conf.loadFromString("""
[scrambler]
""")
        self.p._load_scrambler()
        self.assertEqual([], self.p._autoscramble_gamemode_blacklist)

    def test_empty_option(self):
        self.conf.loadFromString("""
[scrambler]
gamemodes_blacklist: """)
        self.p._load_scrambler()
        self.assertEqual([], self.p._autoscramble_gamemode_blacklist)

    def test_bad_option(self):
        self.conf.loadFromString("""
[scrambler]
gamemodes_blacklist: foo""")
        self.p._load_scrambler()
        self.assertEqual([], self.p._autoscramble_gamemode_blacklist)


    def test_one_valid_gamemode(self):
        self.conf.loadFromString("""
[scrambler]
gamemodes_blacklist: SquadRush0""")
        self.p._load_scrambler()
        self.assertEqual(['SquadRush0'], self.p._autoscramble_gamemode_blacklist)

    def test_multiple_valid_gamemode(self):
        self.conf.loadFromString("""
[scrambler]
gamemodes_blacklist: SquadRush0|SquadDeathMatch0""")
        self.p._load_scrambler()
        self.assertEqual(['SquadRush0', 'SquadDeathMatch0'], self.p._autoscramble_gamemode_blacklist)

    def test_mix_valid_and_invalid_gamemode(self):
        self.conf.loadFromString("""
[scrambler]
gamemodes_blacklist: SquadRush0,SquadDeathMatch0 foo | Rush3 , bar ! Conquest4
""")
        self.p._load_scrambler()
        self.assertEqual(['SquadRush0', 'SquadDeathMatch0', 'Rush3', 'Conquest4'], self.p._autoscramble_gamemode_blacklist)


class Test_load_autobalance_settings__no_autoassign_level(Test_conf):

    default_value = 20

    def test_no_section(self):
        self.conf.loadFromString("""[foo]""")
        self.p._load_autobalance_settings()
        self.assertEqual(self.default_value, self.p._no_autoassign_level)

    def test_no_option(self):
        self.conf.loadFromString(dedent("""
            [preferences]
        """))
        self.p._load_autobalance_settings()
        self.assertEqual(self.default_value, self.p._no_autoassign_level)

    def test_nominal(self):
        self.conf.loadFromString(dedent("""
            [preferences]
            no_autoassign_level: superadmin
        """))
        self.p._load_autobalance_settings()
        self.assertEqual(100, self.p._no_autoassign_level)


class Test_load_no_level_check_level(Test_conf):

    default_value = 100

    def test_no_section(self):
        self.conf.loadFromString("""[foo]""")
        self.p._load_no_level_check_level()
        self.assertEqual(self.default_value, self.p.no_level_check_level)

    def test_no_option(self):
        self.conf.loadFromString(dedent("""
            [preferences]
        """))
        self.p._load_no_level_check_level()
        self.assertEqual(self.default_value, self.p.no_level_check_level)

    def test_nominal(self):
        self.conf.loadFromString(dedent("""
            [preferences]
            no_level_check_level: senioradmin
        """))
        self.p._load_no_level_check_level()
        self.assertEqual(80, self.p.no_level_check_level)
