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

import os
from mock import patch
from b3.config import CfgConfigParser
from b3.plugins.poweradminbf3 import Poweradminbf3Plugin
from tests.plugins.poweradminbf3 import Bf3TestCase


class Test_cmd_listconfig(Bf3TestCase):

    def setUp(self):
        super(Test_cmd_listconfig, self).setUp()
        self.conf = CfgConfigParser()
        self.conf.loadFromString("""[commands]
listconfig: 40

[preferences]
config_path: %(script_dir)s
            """ % {'script_dir': os.path.abspath(
            os.path.join(os.path.dirname(__file__), '../extplugins/conf/serverconfigs'))})
        self.p = Poweradminbf3Plugin(self.console, self.conf)
        self.p.onLoadConfig()
        self.p.onStartup()
        self.admin.connects("admin")
        self.admin.clearMessageHistory()

    def test_nominal(self):
        with patch.object(os, "listdir") as listdir_mock:
            listdir_mock.return_value = ["junk.txt", "conf1.cfg", "conf2.cfg", "hardcore.cfg"]
            self.admin.says('!listconfig')
            self.assertEqual(['Available config files: conf1, conf2, hardcore'], self.admin.message_history)

    def test_no_config(self):
        with patch.object(os, "listdir") as listdir_mock:
            listdir_mock.return_value = ["junk.txt"]
            self.admin.says('!listconfig')
            self.assertEqual(['No server config files found'], self.admin.message_history)
