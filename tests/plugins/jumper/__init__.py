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

import json
import unittest2

from textwrap import dedent
from mockito import when
from b3.cvar import Cvar
from b3.config import MainConfig
from b3.config import XmlConfigParser
from b3.config import CfgConfigParser
from b3.parsers.iourt42 import Iourt42Parser
from b3.plugins.admin import AdminPlugin
from b3.plugins.jumper import JumperPlugin
from tests import logging_disabled

MAPDATA_JSON = '''{"ut4_uranus_beta1a": {"size": 1841559, "nom": "Uranus", "njump": "22", "mdate": "2013-01-16", "pk3":
"ut4_uranus_beta1a", "level": 50, "id": 308, "utversion": 2, "nway": 1, "howjump": "", "mapper": "Levant"},
"ut4_crouchtraining_a1": {"size": 993461, "nom": "Crouch Training", "njump": "11", "mdate": "2010-12-31",
"pk3": "ut4_crouchtraining_a1", "level": 79, "id": 346, "utversion": 2, "nway": 1, "howjump": "", "mapper": "spidercochon"}}'''


class JumperTestCase(unittest2.TestCase):

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

        self.conf = CfgConfigParser()
        self.conf.loadFromString(dedent(r"""
            [settings]
            demorecord: no
            skipstandardmaps: yes
            minleveldelete: senioradmin

            [commands]
            delrecord: guest
            maprecord: guest
            mapinfo: guest
            record: guest
            setway: senioradmin
            topruns: guest
            map: fulladmin
            maps: user
            setnextmap: admin
        """))

        self.p = JumperPlugin(self.console, self.conf)
        self.p.onLoadConfig()
        self.p.onStartup()

        # load fixed json data (do not contact urtjumpers api for testing)
        when(self.p).getMapsDataFromApi().thenReturn(json.loads(MAPDATA_JSON))

    def tearDown(self):
        self.console.working = False


