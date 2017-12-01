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


class Test_cmd_setpassword(LoginTestCase):

    def setUp(self):
        LoginTestCase.setUp(self)
        self.init_plugin()
        self.joe = FakeClient(self.console, name="Joe", guid="joeguid", groupBits=128)

    def test_no_parameter(self):
        # GIVEN
        self.joe.connects("0")
        self.joe._groupBits = 128 # force superadmin
        self.assertEqual('', self.joe.password)
        joe_db = self.p._get_client_from_db(self.joe.id)
        self.assertEqual('', joe_db.password)
        # WHEN
        self.joe.clearMessageHistory()
        self.joe.says("!setpassword")
        # THEN
        self.assertEqual(['Usage: !setpassword <new password> [<client>]'], self.joe.message_history)
        self.assertEqual('', self.joe.password)
        joe_db = self.p._get_client_from_db(self.joe.id)
        self.assertEqual('', joe_db.password)

    def test_nominal(self):
        # GIVEN
        self.joe.connects("0")
        self.joe._groupBits = 128 # force superadmin
        self.assertEqual('', self.joe.password)
        joe_db = self.p._get_client_from_db(self.joe.id)
        self.assertEqual('', joe_db.password)
        # WHEN
        self.joe.clearMessageHistory()
        self.joe.says("!setpassword f00")
        # THEN
        self.assertEqual(['Your new password has been saved'], self.joe.message_history)
        self.assertEqual(F00_MD5, self.joe.password)
        joe_db = self.p._get_client_from_db(self.joe.id)
        self.assertEqual(F00_MD5, joe_db.password)

    def test_change_someone_else(self):
        # GIVEN
        self.joe.connects("0")
        self.joe._groupBits = 128  # force superadmin
        jack = FakeClient(self.console, name="Jack", guid="jackguid")
        jack.connects("1")
        self.assertEqual('', jack.password)
        jack_db = self.p._get_client_from_db(jack.id)
        self.assertEqual('', jack_db.password)
        # WHEN
        self.joe.clearMessageHistory()
        self.joe.says("!setpassword f00 jack")
        # THEN
        self.assertEqual(['New password for Jack saved'], self.joe.message_history)
        self.assertEqual(F00_MD5, jack.password)
        jack_db = self.p._get_client_from_db(jack.id)
        self.assertEqual(F00_MD5, jack_db.password)

    def test_change_someone_else_not_found(self):
        # GIVEN
        self.joe.connects("0")
        self.joe._groupBits = 128  # force superadmin
        # WHEN
        self.joe.clearMessageHistory()
        self.joe.says("!setpassword new_password jack")
        # THEN
        self.assertEqual(['No players found matching jack'], self.joe.message_history)



class Test_cmd_login(LoginTestCase):

    def setUp(self):
        LoginTestCase.setUp(self)
        self.init_plugin()
        # create a client which needs to log in and has a password saved in database
        self.jack = FakeClient(self.console, name="Jack", guid="jackguid", groupBits=128, password=F00_MD5)
        self.jack.save()

    def test_already_logged_in(self):
        # GIVEN
        joe = FakeClient(self.console, name="Joe", guid="joeguid", groupBits=128)
        joe.setvar(self.p, 'loggedin', 1)
        joe.connects("0")
        # WHEN
        joe.clearMessageHistory()
        joe.says("!login")
        # THEN
        self.assertEqual(['You are already logged in'], joe.message_history)

    def test_low_level(self):
        # GIVEN
        joe = FakeClient(self.console, name="Joe", guid="joeguid", groupBits=8)
        joe.connects("0")
        # WHEN
        joe.clearMessageHistory()
        joe.says("!login")
        # THEN
        self.assertEqual(['You do not need to log in'], joe.message_history)
        self.assertFalse(self.jack.isvar(self.p, 'loggedin'))

    def test_high_level_no_parameter(self):
        # GIVEN
        self.jack.connects("0")
        self.assertEqual(2, self.jack.groupBits) # the login plugin set his level down to 2 while waiting for the password
        # WHEN
        self.jack.clearMessageHistory()
        self.jack.says("!login")
        # THEN
        self.assertEqual(['Usage (via console): /tell 0 !login yourpassword'], self.jack.message_history)
        self.assertEqual(2, self.jack.groupBits)
        self.assertFalse(self.jack.isvar(self.p, 'loggedin'))

    def test_high_level_wrong_password(self):
        # GIVEN
        self.jack.connects("0")
        self.assertEqual(2, self.jack.groupBits) # the login plugin set his level down to 2 while waiting for the password
        # WHEN
        self.jack.clearMessageHistory()
        self.jack.says("!login qsfddqsf")
        # THEN
        self.assertEqual(['***Access denied***'], self.jack.message_history)
        self.assertEqual(2, self.jack.groupBits)
        self.assertFalse(self.jack.isvar(self.p, 'loggedin'))

    def test_high_level_correct_password(self):
        # GIVEN
        self.jack.connects("0")
        self.assertEqual(2, self.jack.groupBits) # the login plugin set his level down to 2 while waiting for the password
        # WHEN
        self.jack.clearMessageHistory()
        self.jack.says("!login f00")
        # THEN
        self.assertEqual(['You are successfully logged in'], self.jack.message_history)
        self.assertEqual(128, self.jack.groupBits)
        self.assertTrue(self.jack.isvar(self.p, 'loggedin'))

    def test_high_level_spoofed_password_with_compromised_client_object(self):
        """
        in some B3 game parser implementation there is an issue which could let the 'password' property of client
        objects be compromised.
        """
        # GIVEN
        batman_md5 = 'ec0e2603172c73a8b644bb9456c1ff6e'
        self.jack.connects("0")
        self.assertEqual(2, self.jack.groupBits) # the login plugin set his level down to 2 while waiting for the password
        self.jack.password = batman_md5
        # WHEN
        self.jack.clearMessageHistory()
        self.jack.says("!login batman")
        # THEN
        self.assertEqual(['***Access denied***'], self.jack.message_history)
        self.assertEqual(2, self.jack.groupBits)
        self.assertFalse(self.jack.isvar(self.p, 'loggedin'))

    def test_high_level_correct_password_with_compromised_client_object(self):
        """
        in some B3 game parser implementation there is an issue which could let the 'password' property of client
        objects be compromised.
        """
        # GIVEN
        batman_md5 = 'ec0e2603172c73a8b644bb9456c1ff6e'
        self.jack.connects("0")
        self.assertEqual(2, self.jack.groupBits) # the login plugin set his level down to 2 while waiting for the password
        self.jack.password = batman_md5
        # WHEN
        self.jack.clearMessageHistory()
        self.jack.says("!login f00")
        # THEN
        self.assertEqual(['You are successfully logged in'], self.jack.message_history)
        self.assertEqual(128, self.jack.groupBits)
        self.assertTrue(self.jack.isvar(self.p, 'loggedin'))
