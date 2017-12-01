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
import os

from b3.config import CfgConfigParser
from tests.plugins.urtserversidedemo import PluginTestCase
from b3.plugins.urtserversidedemo import UrtserversidedemoPlugin


class ConfTestCase(PluginTestCase):

    def setUp(self):
        PluginTestCase.setUp(self)
        self.conf = CfgConfigParser()
        self.p = UrtserversidedemoPlugin(self.console, self.conf)
        logging.getLogger('output').setLevel(logging.NOTSET)


class Test_default_conf(ConfTestCase):

    def setUp(self):
        ConfTestCase.setUp(self)
        self.conf.load(os.path.join(os.path.dirname(__file__), '../../../b3/conf/plugin_urtserversidedemo.ini'))
        self.p.onLoadConfig()


    def test_command_startserverdemo(self):
        self.assertEqual('mod', self.p.config.get('commands', 'startserverdemo-startdemo'))
        self.p.onStartup()
        self.assertIn('startserverdemo', self.adminPlugin._commands)
        cmd = self.adminPlugin._commands['startserverdemo']
        self.assertTupleEqual((20, 100), cmd.level)
        self.assertEqual('startdemo', cmd.alias)


    def test_command_stopserverdemo(self):
        self.assertEqual('mod', self.p.config.get('commands', 'stopserverdemo-stopdemo'))
        self.p.onStartup()
        self.assertIn('stopserverdemo', self.adminPlugin._commands)
        cmd = self.adminPlugin._commands['stopserverdemo']
        self.assertTupleEqual((20, 100), cmd.level)
        self.assertEqual('stopdemo', cmd.alias)


    def test_haxbusterurt_demo_duration(self):
        self.assertEqual(4, self.p.config.getint('haxbusterurt', 'demo_duration'))
        self.p.onStartup()
        self.assertEqual(4, self.p._haxbusterurt_demo_duration)



class Test_commands(ConfTestCase):

    def assertCmdMinLevel(self, cmd_name, min_level):
        self.assertIn(cmd_name, self.adminPlugin._commands)
        cmd = self.adminPlugin._commands[cmd_name]
        self.assertTupleEqual((min_level, 100), cmd.level)


    def test_startserverdemo(self):
        self.conf.loadFromString("""
[commands]
startserverdemo: 40
""")
        self.p.onStartup()
        self.assertCmdMinLevel('startserverdemo', 40)


    def test_stopserverdemo(self):
        self.conf.loadFromString("""
[commands]
stopserverdemo: 40
""")
        self.p.onStartup()
        self.assertCmdMinLevel('stopserverdemo', 40)



class Test_haxbusterurt(ConfTestCase):

    def test_demo_duration_nominal(self):
        self.conf.loadFromString("""
[haxbusterurt]
demo_duration: 3
""")
        self.p.onLoadConfig()
        self.assertEqual(3, self.p._haxbusterurt_demo_duration)


    def test_demo_duration_bad(self):
        self.conf.loadFromString("""
[haxbusterurt]
demo_duration: f00
""")
        self.p.onLoadConfig()
        self.assertEqual(0, self.p._haxbusterurt_demo_duration)



class Test_follow(ConfTestCase):

    def test_demo_duration_nominal(self):
        self.conf.loadFromString("""
[follow]
demo_duration: 3
""")
        self.p.onLoadConfig()
        self.assertEqual(3, self.p._follow_demo_duration)


    def test_demo_duration_bad(self):
        self.conf.loadFromString("""
[follow]
demo_duration: f00
""")
        self.p.onLoadConfig()
        self.assertEqual(0, self.p._follow_demo_duration)
