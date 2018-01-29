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

import unittest2

from textwrap import dedent
from mockito import when
from b3 import TEAM_BLUE
from b3 import TEAM_RED
from b3 import TEAM_SPEC
from b3.cvar import Cvar
from b3.config import MainConfig
from b3.config import CfgConfigParser
from b3.config import XmlConfigParser
from b3.plugins.admin import AdminPlugin
from b3.plugins.callvote import CallvotePlugin
from b3.parsers.iourt42 import Iourt42Parser
from tests import logging_disabled

class CallvoteTestCase(unittest2.TestCase):

    @classmethod
    def setUpClass(cls):
        with logging_disabled():
            from b3.parsers.q3a.abstractParser import AbstractParser
            from b3.fake import FakeConsole
            AbstractParser.__bases__ = (FakeConsole,)
            # Now parser inheritance hierarchy is :
            # Iourt41Parser -> abstractParser -> FakeConsole -> Parser

    def setUp(self):
        # create a Iourt42 parser
        parser_conf = XmlConfigParser()
        parser_conf.loadFromString(dedent(r"""
            <configuration>
                <settings name="server">
                    <set name="game_log"></set>
                </settings>
            </configuration>
        """))

        self.parser_conf = MainConfig(parser_conf)
        self.console = Iourt42Parser(self.parser_conf)

        # initialize some fixed cvars which will be used by both the plugin and the iourt42 parser
        when(self.console).getCvar('auth').thenReturn(Cvar('auth', value='0'))
        when(self.console).getCvar('fs_basepath').thenReturn(Cvar('fs_basepath', value='/fake/basepath'))
        when(self.console).getCvar('fs_homepath').thenReturn(Cvar('fs_homepath', value='/fake/homepath'))
        when(self.console).getCvar('fs_game').thenReturn(Cvar('fs_game', value='q3ut4'))
        when(self.console).getCvar('gamename').thenReturn(Cvar('gamename', value='q3urt42'))

        # start the parser
        self.console.startup()

        with logging_disabled():
            self.adminPlugin = AdminPlugin(self.console, '@b3/conf/plugin_admin.ini')
            self.adminPlugin.onLoadConfig()
            self.adminPlugin.onStartup()

        # make sure the admin plugin obtained by other plugins is our admin plugin
        when(self.console).getPlugin('admin').thenReturn(self.adminPlugin)

        with logging_disabled():
            from b3.fake import FakeClient

        # create some clients
        self.mike = FakeClient(console=self.console, name="Mike", guid="mikeguid", team=TEAM_RED,  groupBits=128)
        self.bill = FakeClient(console=self.console, name="Bill", guid="billguid", team=TEAM_BLUE, groupBits=16)
        self.mark = FakeClient(console=self.console, name="Mark", guid="markguid", team=TEAM_RED,  groupBits=2)
        self.sara = FakeClient(console=self.console, name="Sara", guid="saraguid", team=TEAM_SPEC, groupBits=1)

        self.conf = CfgConfigParser()
        self.p = CallvotePlugin(self.console, self.conf)

    def tearDown(self):
        self.console.working = False
        self.mike.disconnects()
        self.bill.disconnects()
        self.mark.disconnects()
        self.sara.disconnects()

    def init(self, config_content=None):
        if config_content:
            self.conf.loadFromString(config_content)
        else:
            self.conf.loadFromString(dedent(r"""
                [callvoteminlevel]
                capturelimit: guest
                clientkick: guest
                clientkickreason: guest
                cyclemap: guest
                exec: guest
                fraglimit: guest
                kick: guest
                map: guest
                reload: guest
                restart: guest
                shuffleteams: guest
                swapteams: guest
                timelimit: guest
                g_bluewaverespawndelay: guest
                g_bombdefusetime: guest
                g_bombexplodetime: guest
                g_capturescoretime: guest
                g_friendlyfire: guest
                g_followstrict: guest
                g_gametype: guest
                g_gear: guest
                g_matchmode: guest
                g_maxrounds: guest
                g_nextmap: guest
                g_redwaverespawndelay: guest
                g_respawndelay: guest
                g_roundtime: guest
                g_timeouts: guest
                g_timeoutlength: guest
                g_swaproles: guest
                g_waverespawns: guest

                [callvotespecialmaplist]
                #ut4_abbey: guest
                #ut4_abbeyctf: guest

                [commands]
                lastvote: mod
                veto: mod
            """))

        self.p.onLoadConfig()
        self.p.onStartup()

        # return a fixed timestamp
        when(self.p).getTime().thenReturn(1399725576)