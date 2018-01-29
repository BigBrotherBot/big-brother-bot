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

import sys
import threading
import unittest

import logging
logging.raiseExceptions = False  # get rid of 'No handlers could be found for logger output' message
from b3 import TEAM_UNKNOWN
from b3.config import XmlConfigParser
from b3.parsers.bf3 import Bf3Parser, __version__ as bf3_version
from b3.plugins.admin import AdminPlugin
from tests import logging_disabled
import b3.output # do not remove, needed because the module alters some defaults of the logging module

class Bf3TestCase(unittest.TestCase):
    """
    Test case that is suitable for testing BF3 parser specific features
    """
    @classmethod
    def setUpClass(cls):
        # less logging
        logging.getLogger('output').setLevel(logging.ERROR)

        with logging_disabled():
            from b3.parsers.frostbite2.abstractParser import AbstractParser
            from b3.fake import FakeConsole
        AbstractParser.__bases__ = (FakeConsole,)
        # Now parser inheritance hierarchy is :
        # Bf3Parser -> AbstractParser -> FakeConsole -> Parser

        # add method changes_team(newTeam, newSquad=None) to FakeClient
        def changes_team(self, newTeam, newSquad=None):
            self.console.OnPlayerTeamchange(None, data=[self.cid, newTeam, newSquad if newSquad else self.squad])

        from b3.fake import FakeClient
        FakeClient.changes_team = changes_team

    def setUp(self):
        # create a BF3 parser
        self.parser_conf = XmlConfigParser()
        self.parser_conf.loadFromString("""<configuration />""")
        with logging_disabled():
            self.console = Bf3Parser(self.parser_conf)

        # alter a few settings to speed up the tests
        self.console.sayqueue_get_timeout = 0
        self.console._message_delay = 0

        with logging_disabled():
            self.console.startup()

        # load the admin plugin
        with logging_disabled():
            self.adminPlugin = AdminPlugin(self.console, '@b3/conf/plugin_admin.ini')
            self.adminPlugin.onStartup()

        # make sure the admin plugin obtained by other plugins is our admin plugin
        def getPlugin(name):
            if name == 'admin':
                return self.adminPlugin
            else:
                return self.console.getPlugin(name)
        self.console.getPlugin = getPlugin

        self.console.patch_b3_admin_plugin()

        # prepare a few players
        with logging_disabled():
            from b3.fake import FakeClient
            self.joe = FakeClient(self.console, name="Joe", exactName="Joe", guid="zaerezarezar", groupBits=1, team=TEAM_UNKNOWN, teamId=0, squad=0)
            self.simon = FakeClient(self.console, name="Simon", exactName="Simon", guid="qsdfdsqfdsqf", groupBits=0, team=TEAM_UNKNOWN, teamId=0, squad=0)
            self.reg = FakeClient(self.console, name="Reg", exactName="Reg", guid="qsdfdsqfdsqf33", groupBits=4, team=TEAM_UNKNOWN, teamId=0, squad=0)
            self.moderator = FakeClient(self.console, name="Moderator", exactName="Moderator", guid="sdf455ezr", groupBits=8, team=TEAM_UNKNOWN, teamId=0, squad=0)
            self.admin = FakeClient(self.console, name="Level-40-Admin", exactName="Level-40-Admin", guid="875sasda", groupBits=16, team=TEAM_UNKNOWN, teamId=0, squad=0)
            self.superadmin = FakeClient(self.console, name="God", exactName="God", guid="f4qfer654r", groupBits=128, team=TEAM_UNKNOWN, teamId=0, squad=0)

    def tearDown(self):
        self.console.working = False
        self.console.wait_for_threads()
        sys.stdout.write("\tactive threads count : %s " % threading.activeCount())
#        sys.stderr.write("%s\n" % threading.enumerate())
