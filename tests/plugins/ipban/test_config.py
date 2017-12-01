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
from tests.plugins.ipban import IpbanTestCase

class Test_config(IpbanTestCase):

    def test_with_config_content(self):
        # GIVEN
        self.init(dedent(r"""
            [settings]
            maxlevel: admin
        """))
        # THEN
        self.assertEqual(self.p._maxLevel, 40)

    def test_with_empty_config(self):
        # GIVEN
        self.init(dedent(r"""
            [settings]
        """))
        # THEN
        self.assertEqual(self.p._maxLevel, 1)