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
import b3.events
import os
import unittest2 as unittest
import sys

from mockito import when
from mock import Mock, ANY
from b3.config import CfgConfigParser
from b3.plugins.chatlogger import ChatloggerPlugin
from tests import logging_disabled
from tests.plugins.chatlogger import ChatloggerTestCase
from textwrap import dedent


def flush_console_streams():
    sys.stderr.flush()
    sys.stdout.flush()


class Test_config(ChatloggerTestCase):

    def setUp(self):
        ChatloggerTestCase.setUp(self)
        with logging_disabled():
            self.console.startup()

        self.conf = CfgConfigParser()
        self.p = ChatloggerPlugin(self.console, self.conf)

        when(self.console.config).get('b3', 'time_zone').thenReturn('GMT')
        self.p.setup_fileLogger = Mock()

    def init(self, config_content=None):
        """ load plugin config and initialise the plugin """
        if config_content:
            self.conf.loadFromString(config_content)
        else:
            if os.path.isfile(b3.getAbsolutePath('@b3/conf/plugin_chatlogger.ini')):
                self.conf.load(b3.getAbsolutePath('@b3/conf/plugin_chatlogger.ini'))
            else:
                raise unittest.SkipTest("default config file '%s' does not exists" % b3.getAbsolutePath('@b3/conf/plugin_chatlogger.ini'))
        self.p.onLoadConfig()
        self.p.onStartup()

    def test_default_config(self):
        # GIVEN
        when(b3).getB3Path(decode=ANY).thenReturn("c:\\b3_folder")
        when(b3).getConfPath(decode=ANY).thenReturn("c:\\b3_conf_folder")
        # WHEN
        self.init()
        # THEN
        self.assertTrue(self.p._save2db)
        self.assertTrue(self.p._save2file)
        expected_log_file = 'c:\\b3_conf_folder\\chat.log' if sys.platform == 'win32' else 'c:\\b3_conf_folder/chat.log'
        self.assertEqual(expected_log_file, self.p._file_name)
        self.assertEqual("D", self.p._file_rotation_rate)
        self.assertEqual(0, self.p._max_age_in_days)
        self.assertEqual(0, self.p._max_age_cmd_in_days)
        self.assertEqual(0, self.p._hours)
        self.assertEqual(0, self.p._minutes)

    def test_empty_config(self):
        self.init("""
        """)
        self.assertTrue(self.p._save2db)
        self.assertFalse(self.p._save2file)
        self.assertIsNone(self.p._file_name)
        self.assertIsNone(self.p._file_rotation_rate)
        self.assertEqual(0, self.p._max_age_in_days)
        self.assertEqual(0, self.p._max_age_cmd_in_days)
        self.assertEqual(0, self.p._hours)
        self.assertEqual(0, self.p._minutes)
        self.assertEqual("chatlog", self.p._db_table)
        self.assertEqual("cmdlog", self.p._db_table_cmdlog)

    def test_conf1(self):
        self.init(dedent("""
            [purge]
            max_age:7d
            hour:4
            min:0
        """))
        self.assertTrue(self.p._save2db)
        self.assertFalse(self.p._save2file)
        self.assertIsNone(self.p._file_name)
        self.assertIsNone(self.p._file_rotation_rate)
        self.assertEqual(7, self.p._max_age_in_days)
        self.assertEqual(0, self.p._max_age_cmd_in_days)
        self.assertEqual(4, self.p._hours)
        self.assertEqual(0, self.p._minutes)