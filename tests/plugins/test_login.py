#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2012 Courgette
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
import logging
import os
from mockito import when
from b3.fake import FakeClient
from b3.plugins.admin import AdminPlugin
from tests import B3TestCase
import unittest2 as unittest

from b3.plugins.login import LoginPlugin
from b3.config import XmlConfigParser

from b3 import __file__ as b3__file__

default_plugin_file = os.path.normpath(os.path.join(os.path.dirname(b3__file__), "conf/plugin_login.xml"))
ADMIN_CONFIG_FILE = os.path.normpath(os.path.join(os.path.dirname(b3__file__), "conf/plugin_admin.xml"))

F00_MD5 = '9f06f2538cdbb40bce9973f60506de09'

class LoginTestCase(B3TestCase):
    """ Ease testcases that need an working B3 console and need to control the censor plugin config """

    def setUp(self):
        self.log = logging.getLogger('output')
        self.log.propagate = False

        B3TestCase.setUp(self)

        admin_conf = XmlConfigParser()
        admin_conf.load(ADMIN_CONFIG_FILE)
        self.adminPlugin = AdminPlugin(self.console, admin_conf)
        when(self.console).getPlugin("admin").thenReturn(self.adminPlugin)
        self.adminPlugin.onLoadConfig()
        self.adminPlugin.onStartup()

        self.console.gameName = "theGame"
        self.console.startup()
        self.log.propagate = True


    def tearDown(self):
        B3TestCase.tearDown(self)

    def init_plugin(self, config_content=None):
        self.conf = XmlConfigParser()
        if config_content:
            self.conf.setXml(config_content)
        else:
            self.conf.load(default_plugin_file)
        self.p = LoginPlugin(self.console, self.conf)

        self.log.setLevel(logging.DEBUG)
        self.log.info("============================= Login plugin: loading config ============================")
        self.p.onLoadConfig()
        self.log.info("============================= Login plugin: starting  =================================")
        self.p.onStartup()




@unittest.skipUnless(os.path.exists(default_plugin_file), reason="cannot get default plugin_login.xml config file at %s" % default_plugin_file)
class Test_default_config(LoginTestCase):

    def setUp(self):
        LoginTestCase.setUp(self)
        self.init_plugin()

    def test_thresholdlevel(self):
        self.assertEqual(40, self.p.threshold)

    def test_passwdlevel(self):
        self.assertEqual(40, self.p.passwdlevel)


class Test_load_config(LoginTestCase):

    def test_empty_conf(self):
        self.init_plugin("""<configuration plugin="login">
            <settings name="settings"/>
        </configuration>""")
        self.assertEqual(1000, self.p.threshold)
        self.assertEqual(100, self.p.passwdlevel)

    def test_thresholdlevel_empty(self):
        self.init_plugin("""<configuration plugin="login">
            <settings name="settings">
                <set name="thresholdlevel"></set>
            </settings>
        </configuration>""")
        self.assertEqual(1000, self.p.threshold)

    def test_thresholdlevel_junk(self):
        self.init_plugin("""<configuration plugin="login">
            <settings name="settings">
                <set name="thresholdlevel">f00</set>
            </settings>
        </configuration>""")
        self.assertEqual(1000, self.p.threshold)

    def test_passwdlevel_empty(self):
        self.init_plugin("""<configuration plugin="login">
            <settings name="settings">
                <set name="passwdlevel"></set>
            </settings>
        </configuration>""")
        self.assertEqual(100, self.p.passwdlevel)

    def test_passwdlevel_junk(self):
        self.init_plugin("""<configuration plugin="login">
            <settings name="settings">
                <set name="passwdlevel">f00</set>
            </settings>
        </configuration>""")
        self.assertEqual(100, self.p.passwdlevel)


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
        self.assertEqual(['usage: !setpassword <new password> [name]'], self.joe.message_history)
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
        self.assertEqual(['your new password is saved'], self.joe.message_history)
        self.assertEqual(F00_MD5, self.joe.password)
        joe_db = self.p._get_client_from_db(self.joe.id)
        self.assertEqual(F00_MD5, joe_db.password)


    def test_change_someone_else(self):
        # GIVEN
        self.joe.connects("0")
        self.joe._groupBits = 128 # force superadmin

        jack = FakeClient(self.console, name="Jack", guid="jackguid")
        jack.connects("1")
        self.assertEqual('', jack.password)
        jack_db = self.p._get_client_from_db(jack.id)
        self.assertEqual('', jack_db.password)

        # WHEN
        self.joe.clearMessageHistory()
        self.joe.says("!setpassword f00 jack")

        # THEN
        self.assertEqual(['new password for Jack saved'], self.joe.message_history)
        self.assertEqual(F00_MD5, jack.password)
        jack_db = self.p._get_client_from_db(jack.id)
        self.assertEqual(F00_MD5, jack_db.password)


    def test_change_someone_else_not_found(self):
        # GIVEN
        self.joe.connects("0")
        self.joe._groupBits = 128 # force superadmin

        # WHEN
        self.joe.clearMessageHistory()
        self.joe.says("!setpassword new_password jack")

        # THEN
        self.assertEqual(['No players found matching jack'], self.joe.message_history)



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
        self.assertEqual(['You need a password to use all your privileges. Ask the administrator to set a password for you.'], joe.message_history)
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
        self.assertEqual(['You are already logged in.'], joe.message_history)

    def test_low_level(self):
        # GIVEN
        joe = FakeClient(self.console, name="Joe", guid="joeguid", groupBits=8)
        joe.connects("0")
        # WHEN
        joe.clearMessageHistory()
        joe.says("!login")
        # THEN
        self.assertEqual(['You do not need to log in.'], joe.message_history)
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
        self.assertEqual(['You are successfully logged in.'], self.jack.message_history)
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
        self.assertEqual(['You are successfully logged in.'], self.jack.message_history)
        self.assertEqual(128, self.jack.groupBits)
        self.assertTrue(self.jack.isvar(self.p, 'loggedin'))
