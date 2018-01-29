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

from b3.plugins.cmdmanager import GRANT_SET_ATTR
from b3.fake import FakeClient
from tests.plugins.cmdmanager import Cmdmanager_TestCase

class Test_commands(Cmdmanager_TestCase):

    ####################################################################################################################
    #                                                                                                                  #
    #   CMD LEVEL NO PARAMETER                                                                                         #
    #                                                                                                                  #
    ####################################################################################################################

    def test_cmdlevel_no_parameter(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!cmdlevel help")
        # THEN
        self.assertListEqual(['command help level: guest'], superadmin.message_history)

    def test_cmdlevel_no_parameter_no_access(self):
        # GIVEN
        mike = FakeClient(self.console, name="Mike", guid="mikeguid", groupBits=32)
        mike.connects("1")
        # WHEN
        mike.clearMessageHistory()
        mike.says("!cmdlevel die")
        # THEN
        self.assertListEqual(['no sufficient access to die command'], mike.message_history)

    def test_cmdlevel_invalid_command(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!cmdlevel fakecommand")
        # THEN
        self.assertListEqual(['could not find command fakecommand'], superadmin.message_history)

    ####################################################################################################################
    #                                                                                                                  #
    #   CMD LEVEL SINGLE PARAMETER                                                                                     #
    #                                                                                                                  #
    ####################################################################################################################

    def test_cmdlevel_single_valid_minlevel(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")

        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!cmdlevel help admin")
        # THEN
        self.assertListEqual(['command help level changed: admin'], superadmin.message_history)
        self.assert_cmd_groups("help", "^2admin")

    def test_cmdlevel_single_invalid_minlevel(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        self.assert_cmd_groups("help", "^2guest")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!cmdlevel help fakegroup")
        # THEN
        self.assertListEqual(['invalid level specified: fakegroup'], superadmin.message_history)
        self.assert_cmd_groups("help", "^2guest")

    ####################################################################################################################
    #                                                                                                                  #
    #   CMD LEVEL DOUBLE PARAMETER                                                                                     #
    #                                                                                                                  #
    ####################################################################################################################

    def test_cmdlevel_double_valid_minlevel_maxlevel(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        self.assert_cmd_groups("help", "^2guest")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!cmdlevel help admin-senioradmin")
        # THEN
        self.assertListEqual(['command help level changed: admin-senioradmin'], superadmin.message_history)
        self.assert_cmd_groups("help", "^2admin^7-^2senioradmin")

    def test_cmdlevel_double_invalid_minlevel_maxlevel(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        self.assert_cmd_groups("help", "^2guest")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!cmdlevel help admin-fakegroup")
        # THEN
        self.assertListEqual(['invalid level specified: fakegroup'], superadmin.message_history)
        self.assert_cmd_groups("help", "^2guest")

    def test_cmdlevel_double_minlevel_greater_than_maxlevel(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        self.assert_cmd_groups("help", "^2guest")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!cmdlevel help fulladmin-admin")
        # THEN
        self.assertListEqual(['invalid level: fulladmin is greater than admin'], superadmin.message_history)
        self.assert_cmd_groups("help", "^2guest")

    ####################################################################################################################
    #                                                                                                                  #
    #   CMD ALIAS NO PARAMETER                                                                                         #
    #                                                                                                                  #
    ####################################################################################################################

    def test_cmdalias_invalid_command(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!cmdalias fakecommand")
        # THEN
        self.assertListEqual(['could not find command fakecommand'], superadmin.message_history)

    def test_cmdalias_no_parameter(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!cmdalias help")
        # THEN
        self.assertListEqual(['command help alias: h'], superadmin.message_history)

    def test_cmdalias_no_parameter_no_alias(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!cmdalias register")
        # THEN
        self.assertListEqual(['command register has not alias set'], superadmin.message_history)

    def test_cmdalias_no_parameter_no_access(self):
        # GIVEN
        mike = FakeClient(self.console, name="Mike", guid="mikeguid", groupBits=32)
        mike.connects("1")
        # WHEN
        mike.clearMessageHistory()
        mike.says("!cmdalias die")
        # THEN
        self.assertListEqual(['no sufficient access to die command'], mike.message_history)

    ####################################################################################################################
    #                                                                                                                  #
    #   CMD ALIAS WITH PARAMETER                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def test_cmdalias_invalid_alias_specified(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        self.assert_cmd_alias("help", "h")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!cmdalias help !")
        # THEN
        self.assertListEqual(['invalid data, try !help cmdalias'], superadmin.message_history)
        self.assert_cmd_alias("help", "h")

    def test_cmdalias_already_in_use(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        self.assert_cmd_alias("ban", "b")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!cmdalias ban tempban")
        # THEN
        self.assertListEqual(['command tempban is already in use'], superadmin.message_history)
        self.assert_cmd_alias("ban", "b")

    def test_cmdalias_add_alias(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        self.assert_cmd_alias("register", None)
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!cmdalias register newregister")
        # THEN
        self.assertListEqual(['added alias for command register: newregister'], superadmin.message_history)
        self.assert_cmd_alias("register", "newregister")

    def test_cmdalias_update_alias(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        self.assert_cmd_alias("help", "h")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!cmdalias help newhelp")
        # THEN
        self.assertListEqual(['updated alias for command help: newhelp'], superadmin.message_history)
        self.assert_cmd_alias("help", "newhelp")

    ####################################################################################################################
    #                                                                                                                  #
    #   CMD GRANT                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def test_cmdgrant_with_invalid_command(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        mike = FakeClient(self.console, name="mike", guid="mikeguid", groupBits=1)
        mike.connects("2")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!cmdgrant mike fakecommand")
        # THEN
        self.assertListEqual(['could not find command fakecommand'], superadmin.message_history)

    def test_cmdgrant_with_lower_group_level(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        mike = FakeClient(self.console, name="mike", guid="mikeguid", groupBits=1)
        mike.connects("2")
        # WHEN
        superadmin.clearMessageHistory()
        mike.clearMessageHistory()
        mike.says("!cmdlevel cmdlevel")
        superadmin.says("!cmdgrant mike cmdlevel")
        mike.says("!cmdlevel cmdlevel")
        # THEN
        grantlist = getattr(mike, GRANT_SET_ATTR, None)
        self.assertIsNotNone(grantlist)
        self.assertIn('cmdlevel', grantlist)
        self.assertLess(mike.maxLevel, self.adminPlugin._commands['cmdlevel'].level[0])
        self.assertListEqual(['mike has now a grant for cmdlevel command'], superadmin.message_history)
        self.assertListEqual(['You need to be in group Full Admin to use !cmdlevel',
                              'command cmdlevel level: fulladmin'], mike.message_history)

    def test_cmdgrant_with_higher_group_level(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        mike = FakeClient(self.console, name="mike", guid="mikeguid", groupBits=64)
        mike.connects("2")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!cmdgrant mike cmdlevel")
        # THEN
        grantlist = getattr(mike, GRANT_SET_ATTR, None)
        self.assertIsNone(grantlist)
        self.assertListEqual(['mike is already able to use cmdlevel command'], superadmin.message_history)

    def test_cmdgrant_with_client_reconnection(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        mike = FakeClient(self.console, id="10", name="mike", guid="mikeguid", groupBits=1)
        mike.connects("2")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!cmdgrant mike cmdlevel")
        mike.disconnects()
        del mike # totally destroy the object
        mike = FakeClient(self.console, id="10", name="mike", guid="mikeguid", groupBits=1)
        mike.connects("2")
        # THEN
        grantlist = getattr(mike, GRANT_SET_ATTR, None)
        self.assertIsNotNone(grantlist)
        self.assertIsInstance(grantlist, set)
        self.assertEqual(1, len(grantlist))

    ####################################################################################################################
    #                                                                                                                  #
    #   CMD REVOKE                                                                                                     #
    #                                                                                                                  #
    ####################################################################################################################

    def test_cmdrevoke_with_no_grant_given(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        mike = FakeClient(self.console, name="mike", guid="mikeguid", groupBits=64)
        mike.connects("2")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!cmdrevoke mike cmdlevel")
        # THEN
        self.assertListEqual(['mike has no grant for cmdlevel command'], superadmin.message_history)

    def test_cmdrevoke_with_previously_given_grant(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        mike = FakeClient(self.console, name="mike", guid="mikeguid", groupBits=1)
        mike.connects("2")
        # WHEN
        superadmin.says("!cmdgrant mike cmdlevel")
        superadmin.clearMessageHistory()
        superadmin.says("!cmdrevoke mike cmdlevel")
        # THEN
        self.assertListEqual(['mike\'s grant for cmdlevel command has been removed'], superadmin.message_history)

    def test_cmdrevoke_with_previously_given_grant_and_high_group_level(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        mike = FakeClient(self.console, name="mike", guid="mikeguid", groupBits=1)
        mike.connects("2")
        # WHEN
        superadmin.says("!cmdgrant mike cmdlevel")
        mike.groupBits = 64     # this 2 lines simulate mike being added as senioradmin
        mike._maxLevel = 80     # after he obtained a grant for command !cmdlevel he couldn't access before
        superadmin.clearMessageHistory()
        superadmin.says("!cmdrevoke mike cmdlevel")
        # THEN
        self.assertListEqual(['mike\'s grant for cmdlevel command has been removed',
                              'but his group level is high enough to access the command'], superadmin.message_history)

    def test_cmdrevoke_with_client_reconnection(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        mike = FakeClient(self.console, id="10", name="mike", guid="mikeguid", groupBits=1)
        mike.connects("2")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!cmdgrant mike cmdlevel")
        superadmin.says("!cmdrevoke mike cmdlevel")
        mike.disconnects()
        del mike # totally destroy the object
        mike = FakeClient(self.console, id="10", name="mike", guid="mikeguid", groupBits=1)
        mike.connects("2")
        # THEN
        grantlist = getattr(mike, GRANT_SET_ATTR, None)
        self.assertIsNotNone(grantlist)
        self.assertIsInstance(grantlist, set)
        self.assertEqual(0, len(grantlist))

    ####################################################################################################################
    #                                                                                                                  #
    #   CMD USE                                                                                                        #
    #                                                                                                                  #
    ####################################################################################################################

    def test_cmduse_no_access(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        mike = FakeClient(self.console, name="mike", guid="mikeguid", groupBits=1)
        mike.connects("2")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!cmduse mike cmdlevel")
        # THEN
        self.assertListEqual(['mike has no access to cmdlevel command'], superadmin.message_history)

    def test_cmduse_access(self):
        # GIVEN
        superadmin = FakeClient(self.console, name="superadmin", guid="superadminguid", groupBits=128)
        superadmin.connects("1")
        mike = FakeClient(self.console, name="mike", guid="mikeguid", groupBits=64)
        mike.connects("2")
        # WHEN
        superadmin.clearMessageHistory()
        superadmin.says("!cmduse mike cmdlevel")
        # THEN
        self.assertListEqual(['mike has access to cmdlevel command'], superadmin.message_history)