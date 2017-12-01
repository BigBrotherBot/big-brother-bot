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
import os

from mockito import when
from tests.plugins.sftpytail import Test_Sftpytail_plugin

class Test_get_host_keys_file(Test_Sftpytail_plugin):

    def setUp(self):
        Test_Sftpytail_plugin.setUp(self)
        self.p.onLoadConfig()
        self.assertIsNone(self.p.known_hosts_file)
        self.sentinels = {
            '~/.ssh/known_hosts': object(),
            '~/ssh/known_hosts': object(),
        }

    def init(self, existing_file_path=None):
        for path, sentinel in self.sentinels.items():
            when(b3).getAbsolutePath(path).thenReturn(sentinel)
            when(os.path).isfile(sentinel).thenReturn(path == existing_file_path)

    def test_fallback_on_user_dot_ssh_directory(self):
        self.init(existing_file_path='~/.ssh/known_hosts')
        self.assertEqual(self.sentinels['~/.ssh/known_hosts'], self.p.get_host_keys_file())

    def test_fallback_on_user_ssh_directory(self):
        self.init(existing_file_path='~/ssh/known_hosts')
        self.assertEqual(self.sentinels['~/ssh/known_hosts'], self.p.get_host_keys_file())

    def test_no_fallback_found(self):
        self.init(existing_file_path=None)
        self.assertIsNone(self.p.get_host_keys_file())