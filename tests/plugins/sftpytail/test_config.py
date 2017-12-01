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
from textwrap import dedent

class Test_config_timeout(Test_Sftpytail_plugin):

    DEFAULT_TIMEOUT = 30

    def test_no_setting(self):
        self.conf.loadFromString(dedent(r"""
            [settings]
        """))
        self.p.onLoadConfig()
        self.assertEqual(Test_config_timeout.DEFAULT_TIMEOUT, self.p._connectionTimeout)

    def test_nominal(self):
        self.conf.loadFromString(dedent(r"""
            [settings]
            timeout: 123
        """))
        self.p.onLoadConfig()
        self.assertEqual(123, self.p._connectionTimeout)

    def test_empty(self):
        self.conf.loadFromString(dedent(r"""
            [settings]
            timeout:
        """))
        self.p.onLoadConfig()
        self.assertEqual(Test_config_timeout.DEFAULT_TIMEOUT, self.p._connectionTimeout)

    def test_negative(self):
        self.conf.loadFromString(dedent(r"""
            [settings]
            timeout: -45
        """))
        self.p.onLoadConfig()
        self.assertEqual(Test_config_timeout.DEFAULT_TIMEOUT, self.p._connectionTimeout)

    def test_junk(self):
        self.conf.loadFromString(dedent(r"""
            [settings]
            timeout: f00
        """))
        self.p.onLoadConfig()
        self.assertEqual(Test_config_timeout.DEFAULT_TIMEOUT, self.p._connectionTimeout)


class Test_config_maxGapBytes(Test_Sftpytail_plugin):

    DEFAULT_MAXGAPBYTES = 20480

    def test_no_setting(self):
        self.conf.loadFromString(dedent(r"""
            [settings]
        """))
        self.p.onLoadConfig()
        self.assertEqual(Test_config_maxGapBytes.DEFAULT_MAXGAPBYTES, self.p._maxGap)

    def test_nominal(self):
        self.conf.loadFromString(dedent(r"""
            [settings]
            maxGapBytes: 1234
        """))
        self.p.onLoadConfig()
        self.assertEqual(1234, self.p._maxGap)

    def test_empty(self):
        self.conf.loadFromString(dedent(r"""
            [settings]
            maxGapBytes:
        """))
        self.p.onLoadConfig()
        self.assertEqual(Test_config_maxGapBytes.DEFAULT_MAXGAPBYTES, self.p._maxGap)

    def test_negative(self):
        self.conf.loadFromString(dedent(r"""
            [settings]
            maxGapBytes: -45
        """))
        self.p.onLoadConfig()
        self.assertEqual(Test_config_maxGapBytes.DEFAULT_MAXGAPBYTES, self.p._maxGap)

    def test_junk(self):
        self.conf.loadFromString(dedent(r"""
            [settings]
            maxGapBytes: f00
        """))
        self.p.onLoadConfig()
        self.assertEqual(Test_config_maxGapBytes.DEFAULT_MAXGAPBYTES, self.p._maxGap)


class Test_config_known_hosts_file(Test_Sftpytail_plugin):

    def test_no_setting(self):
        self.conf.loadFromString(dedent(r"""
            [settings]
        """))
        self.p.onLoadConfig()
        self.assertIsNone(self.p.known_hosts_file)

    def test_nominal(self):
        # GIVEN
        existing_file_path = b3.getAbsolutePath('/a/file/that/exists')
        when(os.path).isfile(existing_file_path).thenReturn(True)
        self.conf.loadFromString(dedent(r"""
            [settings]
            known_hosts_file: /a/file/that/exists
        """))
        # WHEN
        self.p.onLoadConfig()
        # THEN
        self.assertIsNotNone(self.p.known_hosts_file)
        self.assertEqual(existing_file_path, b3.getAbsolutePath(self.p.known_hosts_file))

    def test_empty(self):
        self.conf.loadFromString(dedent(r"""
            [settings]
            known_hosts_file:
        """))
        self.p.onLoadConfig()
        self.assertIsNone(self.p.known_hosts_file)

    def test_non_existing_file(self):
        self.conf.loadFromString(dedent(r"""
            [settings]
            known_hosts_file: /a/file/that/does/not/exist
        """))
        self.p.onLoadConfig()
        self.assertIsNone(self.p.known_hosts_file)

    def test_junk(self):
        self.conf.loadFromString(dedent(r"""
            [settings]
            known_hosts_file: f00
        """))
        self.p.onLoadConfig()
        self.assertIsNone(self.p.known_hosts_file)


class Test_config_private_key_file(Test_Sftpytail_plugin):

    def test_no_setting(self):
        self.conf.loadFromString(dedent(r"""
            [settings]
        """))
        self.p.onLoadConfig()
        self.assertIsNone(self.p.private_key_file)

    def test_nominal(self):
        # GIVEN
        existing_file_path = b3.getAbsolutePath('/a/file/that/exists')
        when(os.path).isfile(existing_file_path).thenReturn(True)
        self.conf.loadFromString(dedent(r"""
            [settings]
            private_key_file: /a/file/that/exists
        """))
        # WHEN
        self.p.onLoadConfig()
        # THEN
        self.assertIsNotNone(self.p.private_key_file)
        self.assertEqual(existing_file_path, b3.getAbsolutePath(self.p.private_key_file))

    def test_empty(self):
        self.conf.loadFromString(dedent(r"""
            [settings]
            private_key_file:
        """))
        self.p.onLoadConfig()
        self.assertIsNone(self.p.private_key_file)

    def test_non_existing_file(self):
        self.conf.loadFromString(dedent(r"""
            [settings]
            private_key_file: /a/file/that/does/not/exist
        """))
        self.p.onLoadConfig()
        self.assertIsNone(self.p.private_key_file)

    def test_junk(self):
        self.conf.loadFromString(dedent(r"""
            [settings]
            private_key_file: f00
        """))
        self.p.onLoadConfig()
        self.assertIsNone(self.p.private_key_file)