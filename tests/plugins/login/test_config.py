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


from textwrap import dedent
from tests.plugins.login import LoginTestCase

class Test_default_config(LoginTestCase):

    def setUp(self):
        LoginTestCase.setUp(self)
        self.init_plugin()

    def test_thresholdlevel(self):
        self.assertEqual(40, self.p._threshold)

    def test_passwdlevel(self):
        self.assertEqual(40, self.p._passwdlevel)


class Test_load_config(LoginTestCase):

    def test_empty_conf(self):
        self.init_plugin(dedent("""
            [settings]
        """))
        self.assertEqual(1000, self.p._threshold)
        self.assertEqual(100, self.p._passwdlevel)

    def test_thresholdlevel_empty(self):
        self.init_plugin(dedent("""
            [settings]
            thresholdlevel:
        """))
        self.assertEqual(1000, self.p._threshold)

    def test_thresholdlevel_junk(self):
        self.init_plugin(dedent("""
            [settings]
            thresholdlevel: f00
        """))
        self.assertEqual(1000, self.p._threshold)

    def test_passwdlevel_empty(self):
        self.init_plugin(dedent("""
            [settings]
            passwdlevel:
        """))
        self.assertEqual(100, self.p._passwdlevel)

    def test_passwdlevel_junk(self):
        self.init_plugin(dedent("""
            [settings]
            passwdlevel: f00
        """))
        self.assertEqual(100, self.p._passwdlevel)
