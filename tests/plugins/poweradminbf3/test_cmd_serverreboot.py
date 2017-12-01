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

import time
from mock import patch
from mockito import when, verify
from b3.config import CfgConfigParser
from b3.parsers.frostbite2.protocol import CommandFailedError
from b3.plugins.poweradminbf3 import Poweradminbf3Plugin
from tests.plugins.poweradminbf3 import Bf3TestCase

@patch.object(time, 'sleep')
class Test_cmd_serverreboot(Bf3TestCase):
    def setUp(self):
        super(Test_cmd_serverreboot, self).setUp()
        self.conf = CfgConfigParser()
        self.conf.loadFromString("""[commands]
serverreboot: 100
        """)
        self.p = Poweradminbf3Plugin(self.console, self.conf)
        self.p.onLoadConfig()
        self.p.onStartup()


    def test_nominal(self, sleep_mock):
        when(self.console).write()
        self.superadmin.connects("god")
        self.superadmin.says("!serverreboot")
        verify(self.console).write(('admin.shutDown',))

    def test_frostbite_error(self, sleep_mock):
        when(self.console).write(('admin.shutDown',)).thenRaise(CommandFailedError(['fOO']))
        self.superadmin.connects("god")
        self.superadmin.message_history = []
        self.superadmin.says("!serverreboot")
        self.assertEqual(['Error: fOO'], self.superadmin.message_history)

