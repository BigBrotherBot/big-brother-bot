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
#

import b3
import b3.events
import os
import re
import codecs

from mockito import when
from mock import ANY
from b3 import TEAM_RED, TEAM_BLUE
from b3.config import CfgConfigParser
from b3.plugins.chatlogger import ChatloggerPlugin
from tests import logging_disabled
from tests.plugins.chatlogger import ChatloggerTestCase
from textwrap import dedent
from tempfile import mkdtemp


with logging_disabled():

    from b3.fake import FakeClient

    def sendsPM(self, msg, target):
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_PRIVATE_SAY', msg, self, target))

    FakeClient.sendsPM = sendsPM


class Test_chatlogfile(ChatloggerTestCase):

    def setUp(self):
        ChatloggerTestCase.setUp(self)
        with logging_disabled():
            self.console.startup()
            self.conf = CfgConfigParser()
            self.p = ChatloggerPlugin(self.console, self.conf)

        when(self.console.config).get('b3', 'time_zone').thenReturn('GMT')

        self.conf.loadFromString(dedent("""
            [general]
            save_to_database: no
            save_to_file: yes

            [file]
            logfile: @conf/chat.log
            rotation_rate: D

            [purge]
            max_age: 0
            hour: 0
            min: 0
        """))
        self.temp_conf_folder = mkdtemp(suffix="b3_conf")
        when(b3).getConfPath(decode=ANY, conf=None).thenReturn(self.temp_conf_folder)
        with logging_disabled():
            self.p.onLoadConfig()
            self.p.onStartup()

        self.chat_log_file = os.path.join(self.temp_conf_folder, 'chat.log')

        with logging_disabled():
            self.joe = FakeClient(self.console, name="Joe", guid="joe_guid", team=TEAM_RED)
            self.simon = FakeClient(self.console, name="Simon", guid="simon_guid", team=TEAM_BLUE)
            self.joe.connects(1)
            self.simon.connects(3)

    def get_all_chatlog_lines_from_logfile(self):
        lines = []
        with codecs.open(self.chat_log_file, "r", encoding="utf-8") as f:
            for l in f.readlines():
                lines.append(l.strip())
        return lines

    def count_chatlog_lines(self):
        return len(self.get_all_chatlog_lines_from_logfile())

    def assert_log_line(self, line, expected):
        """
        remove time stamp at the beginning of the line and compare the remainder
        """
        clean_line = re.sub(r"^\d+-\d+-\d+ \d\d:\d\d:\d\d\t", "", line)
        self.assertEqual(clean_line, expected)

    def test_global_chat(self):
        # WHEN
        self.joe.says("hello")
        # THEN
        self.assertEqual(1, self.count_chatlog_lines())
        self.assert_log_line(self.get_all_chatlog_lines_from_logfile()[0], "@1 [Joe] to ALL:\thello")

    def test_team_chat(self):
        # WHEN
        self.joe.says2team("hello")
        # THEN
        self.assertEqual(1, self.count_chatlog_lines())
        self.assert_log_line(self.get_all_chatlog_lines_from_logfile()[0], "@1 [Joe] to TEAM:\thello")

    def test_squad_chat(self):
        # WHEN
        self.joe.says2squad("hi")
        # THEN
        self.assertEqual(1, self.count_chatlog_lines())
        self.assert_log_line(self.get_all_chatlog_lines_from_logfile()[0], "@1 [Joe] to SQUAD:\thi")

    def test_private_chat(self):
        # WHEN
        self.joe.sendsPM("hi", self.simon)
        # THEN
        self.assertEqual(1, self.count_chatlog_lines())
        self.assert_log_line(self.get_all_chatlog_lines_from_logfile()[0], "@1 [Joe] to PM:\thi")

    def test_unicode(self):
        # WHEN
        self.joe.name = u"★joe★"
        self.simon.name = u"❮❮simon❯❯"
        self.joe.sendsPM(u"hi ✪", self.simon)
        # THEN
        self.assertEqual(1, self.count_chatlog_lines())
        self.assert_log_line(self.get_all_chatlog_lines_from_logfile()[0], u"@1 [★joe★] to PM:\thi ✪")
