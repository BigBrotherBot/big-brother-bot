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

from b3.fake import FakeClient
from tests.plugins.login import LoginTestCase, F00_MD5


class Test_auth(LoginTestCase):

    def setUp(self):
        LoginTestCase.setUp(self)
        self.init_plugin()

    def test_low_level(self):
        # GIVEN
        joe = FakeClient(self.console, name="Joe", guid="joeguid", groupBits=8)
        # WHEN
        joe.clearMessageHistory()
        joe.connects("0")
        # THEN
        self.assertEqual([], joe.message_history)
        self.assertEqual(8, joe.groupBits)

    def test_high_level_no_password_set(self):
        # GIVEN
        joe = FakeClient(self.console, name="Joe", guid="joeguid", groupBits=128)
        # WHEN
        joe.clearMessageHistory()
        joe.connects("0")
        # THEN
        self.assertEqual(['You need a password to use all your privileges: ask the administrator to set a password for you'], joe.message_history)
        self.assertEqual(2, joe.groupBits)

    def test_high_level_having_password(self):
        # GIVEN
        joe = FakeClient(self.console, name="Joe", guid="joeguid", groupBits=128, password=F00_MD5)
        joe.save()
        # WHEN
        joe.clearMessageHistory()
        joe.connects("0")
        # THEN
        self.assertEqual(['Login via console: /tell 0 !login yourpassword'], joe.message_history)
        self.assertEqual(2, joe.groupBits)
