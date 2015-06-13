# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2012 Thomas LEVEIL <courgette@bigbrotherbot.net>
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


from textwrap import dedent
from mockito import when
from b3 import TEAM_RED
from b3.fake import FakeClient
from b3.plugins.admin import AdminPlugin
from tests import B3TestCase, logging_disabled
from b3.plugins.stats import StatsPlugin
from b3.config import CfgConfigParser


class StatPluginTestCase(B3TestCase):

    def setUp(self):
        B3TestCase.setUp(self)

        with logging_disabled():
            admin_conf = CfgConfigParser()
            admin_plugin = AdminPlugin(self.console, admin_conf)
            admin_plugin.onLoadConfig()
            admin_plugin.onStartup()
            when(self.console).getPlugin('admin').thenReturn(admin_plugin)

        conf = CfgConfigParser()
        conf.loadFromString(dedent(r"""
            [commands]
            mapstats-stats: 0
            testscore-ts: 0
            topstats-top: 0
            topxp: 0

            [settings]
            startPoints: 100
            resetscore: no
            resetxp: no
            show_awards: no
            show_awards_xp: no
        """))
        self.p = StatsPlugin(self.console, conf)
        self.p.onLoadConfig()
        self.p.onStartup()

        self.joe = FakeClient(self.console, name="Joe", guid="joeguid", groupBits=1, team=TEAM_RED)
        self.mike = FakeClient(self.console, name="Mike", guid="mikeguid", groupBits=1, team=TEAM_RED)
        self.joe.connects(1)
        self.mike.connects(2)