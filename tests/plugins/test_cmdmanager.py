#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2014 Daniele Pantaleone <fenix@bigbrotherbot.net>
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
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
#

import os
import b3
import unittest2 as unittest

from textwrap import dedent
from mock import Mock
from mock import patch
from mockito import when
from b3.plugins.admin import AdminPlugin
from b3.plugins.cmdmanager import CmdmanagerPlugin
from b3.config import CfgConfigParser
from b3.fake import FakeClient

from tests import B3TestCase

from b3 import __file__ as b3_module__file__


ADMIN_CONFIG_FILE = os.path.normpath(os.path.join(os.path.dirname(b3_module__file__), "conf/plugin_admin.ini"))


@unittest.skipUnless(os.path.exists(ADMIN_CONFIG_FILE), reason="cannot get default plugin config file at %s" % ADMIN_CONFIG_FILE)
class Cmdmanager_TestCase(B3TestCase):

    def setUp(self):

        B3TestCase.setUp(self)
        self.console.gameName = 'f00'

        self.adminPlugin = AdminPlugin(self.console, ADMIN_CONFIG_FILE)
        when(self.console).getPlugin("admin").thenReturn(self.adminPlugin)
        self.adminPlugin.onLoadConfig()
        self.adminPlugin.onStartup()

        self.conf = CfgConfigParser()
        self.conf.loadFromString(dedent(r"""
            [settings]
            update_config_file: no

            [commands]
            cmdlevel: fulladmin
            cmdalias: fulladmin
        """))

        self.p = CmdmanagerPlugin(self.console, self.conf)
        self.p.onLoadConfig()
        self.p.onStartup()


@unittest.skipUnless(os.path.exists(ADMIN_CONFIG_FILE), reason="cannot get default plugin config file at %s" % ADMIN_CONFIG_FILE)
class Test_commands(Cmdmanager_TestCase):

    ####################################################################################################################
    ##                                                                                                                ##
    ## CMD LEVEL NO PARAMETER                                                                                         ##
    ##                                                                                                                ##
    ####################################################################################################################

    def test_cmdlevel_no_parameter(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!cmdlevel help")
        # THEN
        self.assertListEqual(['command !help level: guest'], superadmin.message_history)

    def test_cmdlevel_no_parameter_no_access(self):
        # GIVEN
        mike = FakeClient(self.console, name="Mike", guid="mikeguid", groupBits=32)
        mike.connects("1")
        # WHEN
        mike.clearMessageHistory()
        mike.says("!cmdlevel die")
        # THEN
        self.assertListEqual(['no sufficient access to !die command'], mike.message_history)

    def test_cmdlevel_invalid_command(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!cmdlevel fakecommand")
        # THEN
        self.assertListEqual(['could not find command !fakecommand'], superadmin.message_history)

    ####################################################################################################################
    ##                                                                                                                ##
    ## CMD LEVEL SINGLE PARAMETER                                                                                     ##
    ##                                                                                                                ##
    ####################################################################################################################

    def test_cmdlevel_single_valid_minlevel(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!cmdlevel help admin")
        # THEN
        self.assertListEqual(['command !help level changed: admin'], superadmin.message_history)

    def test_cmdlevel_single_invalid_minlevel(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!cmdlevel help fakegroup")
        # THEN
        self.assertListEqual(['invalid level specified: fakegroup'], superadmin.message_history)

    ####################################################################################################################
    ##                                                                                                                ##
    ## CMD LEVEL DOUBLE PARAMETER                                                                                     ##
    ##                                                                                                                ##
    ####################################################################################################################

    def test_cmdlevel_double_valid_minlevel_maxlevel(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!cmdlevel help admin-senioradmin")
        # THEN
        self.assertListEqual(['command !help level changed: admin-senioradmin'], superadmin.message_history)

    def test_cmdlevel_double_invalid_minlevel_maxlevel(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!cmdlevel help admin-fakegroup")
        # THEN
        self.assertListEqual(['invalid level specified: fakegroup'], superadmin.message_history)

    def test_cmdlevel_double_minlevel_greater_than_maxlevel(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!cmdlevel help fulladmin-admin")
        # THEN
        self.assertListEqual(['invalid level: fulladmin is greater than admin'], superadmin.message_history)

    ####################################################################################################################
    ##                                                                                                                ##
    ## CMD ALIAS NO PARAMETER                                                                                         ##
    ##                                                                                                                ##
    ####################################################################################################################

    def test_cmdalias_invalid_command(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!cmdalias fakecommand")
        # THEN
        self.assertListEqual(['could not find command !fakecommand'], superadmin.message_history)

    def test_cmdalias_no_parameter(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!cmdalias help")
        # THEN
        self.assertListEqual(['command !help alias: !h'], superadmin.message_history)

    def test_cmdalias_no_parameter_no_alias(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!cmdalias register")
        # THEN
        self.assertListEqual(['command !register has not alias set'], superadmin.message_history)

    def test_cmdalias_no_parameter_no_access(self):
        # GIVEN
        mike = FakeClient(self.console, name="Mike", guid="mikeguid", groupBits=32)
        mike.connects("1")
        # WHEN
        mike.clearMessageHistory()
        mike.says("!cmdalias die")
        # THEN
        self.assertListEqual(['no sufficient access to !die command'], mike.message_history)

    ####################################################################################################################
    ##                                                                                                                ##
    ## CMD ALIAS WITH PARAMETER                                                                                       ##
    ##                                                                                                                ##
    ####################################################################################################################

    def test_cmdalias_invalid_alias_specified(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!cmdalias help !")
        # THEN
        self.assertListEqual(['invalid alias specified'], superadmin.message_history)

    def test_cmdalias_already_in_use(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!cmdalias ban tempban")
        # THEN
        self.assertListEqual(['command !tempban is already in use'], superadmin.message_history)

    def test_cmdalias_add_alias(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!cmdalias register newregister")
        # THEN
        self.assertListEqual(['added alias for command !register: !newregister'], superadmin.message_history)

    def test_cmdalias_update_alias(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!cmdalias help newhelp")
        # THEN
        self.assertListEqual(['updated alias for command !help: !newhelp'], superadmin.message_history)