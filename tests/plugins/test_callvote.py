#
# Jumper Plugin for BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2013 Daniele Pantaleone <fenix@bigbrotherbot.net>
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

    def tearDown(self):
        self.console.working = False


class Test_events(CallvoteTestCase):

    def setUp(self):

        CallvoteTestCase.setUp(self)

        with logging_disabled():
            from b3.fake import FakeClient

        # create some clients
        self.mike = FakeClient(console=self.console, name="Mike", guid="mikeguid", team=TEAM_RED,  groupBits=128)
        self.bill = FakeClient(console=self.console, name="Bill", guid="billguid", team=TEAM_BLUE, groupBits=16)
        self.mark = FakeClient(console=self.console, name="Mark", guid="markguid", team=TEAM_RED,  groupBits=2)
        self.sara = FakeClient(console=self.console, name="Sara", guid="saraguid", team=TEAM_SPEC, groupBits=1)

        self.conf = CfgConfigParser()
        self.p = CallvotePlugin(self.console, self.conf)

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

    def tearDown(self):
        self.mike.disconnects()
        self.bill.disconnects()
        self.mark.disconnects()
        self.sara.disconnects()
        CallvoteTestCase.tearDown(self)

    def test_client_callvote_legit(self):
        # GIVEN
        self.init()
        self.mike.connects("1")
        self.bill.connects("2")
        self.mark.connects("3")
        self.sara.connects("4")
        # WHEN
        self.console.parseLine('''Callvote: 1 - "map ut4_dressingroom"''')
        # THEN
        self.assertIsNotNone(self.p.callvote)
        self.assertEqual(self.mike, self.p.callvote['client'])
        self.assertEqual('map', self.p.callvote['type'])
        self.assertEqual('ut4_dressingroom', self.p.callvote['args'])
        self.assertEqual(1399725576, self.p.callvote['time'])
        self.assertEqual(3, self.p.callvote['max_num'])

    def test_client_callvote_not_enough_level(self):
        # GIVEN
        self.init(dedent(r"""
            [callvoteminlevel]
            clientkick: admin
            clientkickreason: admin
            kick: admin
        """))
        self.mike.connects("1")
        self.bill.connects("2")
        self.mark.connects("3")
        self.sara.connects("4")
        # WHEN
        self.sara.clearMessageHistory()
        self.console.parseLine('''Callvote: 4 - "kick bill"''')
        # THEN
        self.assertIsNone(self.p.callvote)
        self.assertListEqual(["You can't issue this callvote. Required level: Admin"], self.sara.message_history)

    def test_client_callvote_map_not_enough_level(self):
        # GIVEN
        self.init(dedent(r"""
            [callvotespecialmaplist]
            ut4_abbey: admin
            ut4_abbeyctf: superadmin
        """))
        self.mike.connects("1")
        self.bill.connects("2")
        self.mark.connects("3")
        self.sara.connects("4")
        # WHEN
        self.sara.clearMessageHistory()
        self.console.parseLine('''Callvote: 4 - "map ut4_abbey"''')
        # THEN
        self.assertIsNone(self.p.callvote)
        self.assertListEqual(["You can't issue this callvote. Required level: Admin"], self.sara.message_history)

    def test_client_callvote_passed(self):
        # GIVEN
        self.init()
        self.mike.connects("1")
        self.bill.connects("2")
        self.mark.connects("3")
        self.sara.connects("4")
        # WHEN
        self.console.parseLine('''Callvote: 4 - "map ut4_casa"''')
        self.console.parseLine('''VotePassed: 3 - 0 - "map ut4_casa"''')
        # THEN
        self.assertIsNotNone(self.p.callvote)
        self.assertEqual(self.sara, self.p.callvote['client'])
        self.assertEqual('map', self.p.callvote['type'])
        self.assertEqual('ut4_casa', self.p.callvote['args'])
        self.assertEqual(1399725576, self.p.callvote['time'])
        self.assertEqual(4, self.p.callvote['max_num'])
        self.assertEqual(3, self.p.callvote['num_yes'])
        self.assertEqual(0, self.p.callvote['num_no'])

    def test_client_callvote_failed(self):
        # GIVEN
        self.init()
        self.mike.connects("1")
        self.bill.connects("2")
        self.mark.connects("3")
        self.sara.connects("4")
        # WHEN
        self.console.parseLine('''Callvote: 4 - "map ut4_casa"''')
        self.console.parseLine('''VotePassed: 1 - 3 - "map ut4_casa"''')
        # THEN
        self.assertIsNotNone(self.p.callvote)
        self.assertEqual(self.sara, self.p.callvote['client'])
        self.assertEqual('map', self.p.callvote['type'])
        self.assertEqual('ut4_casa', self.p.callvote['args'])
        self.assertEqual(1399725576, self.p.callvote['time'])
        self.assertEqual(4, self.p.callvote['max_num'])
        self.assertEqual(1, self.p.callvote['num_yes'])
        self.assertEqual(3, self.p.callvote['num_no'])

    def test_client_callvote_finish_with_none_callvote_object(self):
        # GIVEN
        self.init()
        self.mike.connects("1")
        self.bill.connects("2")
        self.mark.connects("3")
        self.sara.connects("4")
        # WHEN
        self.console.parseLine('''VotePassed: 3 - 0 - "map ut4_casa"''')
        # THEN
        self.assertIsNone(self.p.callvote)

    def test_client_callvote_finish_with_different_arguments(self):
        # GIVEN
        self.init()
        self.mike.connects("1")
        self.bill.connects("2")
        self.mark.connects("3")
        self.sara.connects("4")
        # WHEN
        self.console.parseLine('''Callvote: 4 - "map ut4_casa"''')
        self.console.parseLine('''VotePassed: 1 - 3 - "reload"''')
        # THEN
        self.assertIsNone(self.p.callvote)


class Test_commands(CallvoteTestCase):

    def setUp(self):

        CallvoteTestCase.setUp(self)

        with logging_disabled():
            from b3.fake import FakeClient

        # create some clients
        self.mike = FakeClient(console=self.console, name="Mike", guid="mikeguid", team=TEAM_RED,  groupBits=128)
        self.bill = FakeClient(console=self.console, name="Bill", guid="billguid", team=TEAM_BLUE, groupBits=16)
        self.mark = FakeClient(console=self.console, name="Mark", guid="markguid", team=TEAM_RED,  groupBits=2)
        self.sara = FakeClient(console=self.console, name="Sara", guid="saraguid", team=TEAM_SPEC, groupBits=1)

        self.conf = CfgConfigParser()
        self.p = CallvotePlugin(self.console, self.conf)

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

    def tearDown(self):
        self.mike.disconnects()
        self.bill.disconnects()
        self.mark.disconnects()
        self.sara.disconnects()
        CallvoteTestCase.tearDown(self)

    def test_cmd_veto(self):
        # GIVEN
        self.init()
        self.mike.connects("1")
        self.bill.connects("2")
        self.mark.connects("3")
        self.sara.connects("4")
        # WHEN
        self.console.parseLine('''Callvote: 4 - "map ut4_dressingroom"''')
        self.mike.says('!veto')
        # THEN
        self.assertIsNone(self.p.callvote)


    def test_cmd_lastvote_legit(self):
        # GIVEN
        self.init()
        self.mike.connects("1")
        self.bill.connects("2")
        self.mark.connects("3")
        self.sara.connects("4")
        # WHEN
        self.console.parseLine('''Callvote: 4 - "map ut4_casa"''')
        self.p.callvote['time'] = self.p.getTime() - 10  # fake timestamp
        self.console.parseLine('''VotePassed: 3 - 0 - "map ut4_casa"''')
        self.mike.clearMessageHistory()
        self.mike.says('!lastvote')
        # THEN
        self.assertIsNotNone(self.p.callvote)
        self.assertListEqual(["Last vote issued by Sara 10 seconds ago",
                              "Type: map - Data: ut4_casa",
                              "Result: 3:0 on 4 clients"], self.mike.message_history)