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

import unittest
from mock import Mock # http://www.voidspace.org.uk/python/mock/mock.html
from b3.plugins.poweradminbf3 import Poweradminbf3Plugin


class Test_getConfigSoundingLike(unittest.TestCase):

    def setUp(self):
        self.available_names = ["hardcore", "normal", "infantry", "tdm", "conquest", "rush", "quickmatch", "hardcore-tdm", "hardcore-conquest"]
        self.console = Mock()
        self.p = Poweradminbf3Plugin(self.console)
        self.p._list_available_server_config_files = lambda: self.available_names

    def test_no_available_config(self):
        self.p._list_available_server_config_files = lambda: []
        self.assertListEqual([], self.p._getConfigSoundingLike(""))
        self.assertListEqual([], self.p._getConfigSoundingLike("qsfqsdf q"))

    def test_no_match(self):
        self.assertEqual(9, len(self.p._getConfigSoundingLike("qsfqsdf qqsfdsdqfqsfd qsf qsfd q fsdf")))

    def test_exact_name(self):
        self.assertListEqual(["hardcore"], self.p._getConfigSoundingLike("hardcore"))

    def test_substring_one_match(self):
        self.assertListEqual(["infantry"], self.p._getConfigSoundingLike("infan"))

    def test_substring_many_matches(self):
        self.assertListEqual(['hardcore', 'hardcore-tdm', 'hardcore-conquest'], self.p._getConfigSoundingLike("hardco"))

    def test_soundex_one_match(self):
        self.assertListEqual(['quickmatch'], self.p._getConfigSoundingLike("quickmtch"))

    def test_soundex_many_matches(self):
        self.available_names = ["wasabi21", "wasabi2", "wasabi22", "tdm", "conquest"]
        self.assertListEqual(['wasabi2', 'wasabi21', 'wasabi22'], self.p._getConfigSoundingLike("wsbi2"))

    def test_levenshteinDistance(self):
        self.assertEqual(9, len(self.p._getConfigSoundingLike("")))