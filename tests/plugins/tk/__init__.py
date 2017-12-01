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

from b3.fake import FakeClient
from b3.plugins.tk import TkPlugin
from b3.plugins.admin import AdminPlugin
from b3.config import CfgConfigParser
from mockito import when
from tests import B3TestCase
from textwrap import dedent


class Test_Tk_plugin(B3TestCase):

    def setUp(self):
        super(Test_Tk_plugin, self).setUp()
        self.console.gameName = 'f00'
        self.conf = CfgConfigParser()
        self.p = TkPlugin(self.console, self.conf)


class Tk_functional_test(B3TestCase):

    def setUp(self):
        B3TestCase.setUp(self)

        self.console.gameName = 'f00'

        self.adminPlugin = AdminPlugin(self.console, '@b3/conf/plugin_admin.ini')
        when(self.console).getPlugin("admin").thenReturn(self.adminPlugin)
        self.adminPlugin.onLoadConfig()
        self.adminPlugin.onStartup()

        self.conf = CfgConfigParser()
        self.conf.loadFromString(dedent(r"""
            [settings]
            max_points: 400
            levels: 0,1,2,20,40
            round_grace: 7
            issue_warning: sfire
            grudge_enable: True
            private_messages: True
            damage_threshold: 100
            warn_level: 2
            halflife: 0
            warn_duration: 1h

            [messages]
            ban: ^7team damage over limit
            forgive: ^7$vname^7 has forgiven $aname [^3$points^7]
            grudged: ^7$vname^7 has a ^1grudge ^7against $aname [^3$points^7]
            forgive_many: ^7$vname^7 has forgiven $attackers
            forgive_warning: ^1ALERT^7: $name^7 auto-kick if not forgiven. Type ^3!forgive $cid ^7to forgive. [^3damage: $points^7]
            no_forgive: ^7no one to forgive
            no_punish: ^7no one to punish
            players: ^7Forgive who? %s
            forgive_info: ^7$name^7 has ^3$points^7 TK points
            grudge_info: ^7$name^7 is ^1grudged ^3$points^7 TK points
            forgive_clear: ^7$name^7 cleared of ^3$points^7 TK points
            tk_warning_reason: ^3Do not attack teammates, ^1Attacked: ^7$vname ^7[^3$points^7]
            tk_request_action: ^7type ^3!fp ^7 to forgive ^3%s

            [level_0]
            kill_multiplier: 2
            damage_multiplier: 1
            ban_length: 2

            [level_1]
            kill_multiplier: 2
            damage_multiplier: 1
            ban_length: 2

            [level_2]
            kill_multiplier: 1
            damage_multiplier: 0.5
            ban_length: 1

            [level_20]
            kill_multiplier: 1
            damage_multiplier: 0.5
            ban_length: 0

            [level_40]
            kill_multiplier: 0.75
            damage_multiplier: 0.5
            ban_length: 0
        """))
        self.p = TkPlugin(self.console, self.conf)
        self.p.onLoadConfig()
        self.p.onStartup()

        self.joe = FakeClient(self.console, name="Joe", guid="joeguid", groupBits=1, team=b3.TEAM_RED)
        self.mike = FakeClient(self.console, name="Mike", guid="mikeguid", groupBits=1, team=b3.TEAM_RED)
        self.bill = FakeClient(self.console, name="Bill", guid="billguid", groupBits=1, team=b3.TEAM_RED)
        self.superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128, team=b3.TEAM_RED)
