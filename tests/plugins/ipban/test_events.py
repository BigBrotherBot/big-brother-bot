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


from mock import Mock
from tests.plugins.ipban import IpbanTestCase

class Test_events(IpbanTestCase):

    def test_higher_group_level_client_connect(self):
        # GIVEN
        self.init()
        self.mike.kick = Mock()
        # WHEN
        self.mike.connects('1')
        # THEN
        self.assertGreater(self.mike.maxLevel, self.p._maxLevel)
        self.assertEqual(self.mike.kick.call_count, 0)

    def test_ip_banned_client_connect(self):
        # GIVEN
        self.init()
        self.paul.kick = Mock()
        # WHEN
        self.paul.connects('1')
        # THEN
        self.assertLessEqual(self.paul.maxLevel, self.p._maxLevel)
        self.assertIn(self.paul.ip, self.p.getBanIps())
        self.paul.kick.assert_called_once_with('IPBan: client refused: 2.2.2.2 (Paul) has an active Ban')

    def test_ip_temp_banned_client_connect(self):
        # GIVEN
        self.init()
        self.john.kick = Mock()
        # WHEN
        self.john.connects('1')
        # THEN
        self.assertLessEqual(self.paul.maxLevel, self.p._maxLevel)
        self.assertIn(self.john.ip, self.p.getTempBanIps())
        self.john.kick.assert_called_once_with('IPBan: client refused: 3.3.3.3 (John) has an active TempBan')

    def test_clean_client_connect(self):
        # GIVEN
        self.init()
        self.mary.kick = Mock()
        # WHEN
        self.mary.connects('1')
        # THEN
        self.assertLessEqual(self.paul.maxLevel, self.p._maxLevel)
        self.assertNotIn(self.mary.ip, self.p.getBanIps())
        self.assertNotIn(self.mary.ip, self.p.getTempBanIps())
        self.assertEqual(self.mary.kick.call_count, 0)