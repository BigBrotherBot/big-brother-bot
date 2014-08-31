#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2010 Courgette <courgette@bigbrotherbot.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA

import logging
import sys
import os
import thread
import time
import unittest2 as unittest

from mock import Mock
from mock import call
from mock import patch
from mock import ANY
from mockito import when

from b3 import __file__ as b3_module__file__
from b3 import TEAM_BLUE
from b3 import TEAM_RED
from b3.clients import Group
from b3.clients import Client

from tests import B3TestCase
from tests import InstantTimer
from b3.fake import FakeClient
from b3.config import CfgConfigParser
from b3.plugins.admin import AdminPlugin
from b3.plugins.admin import __author__ as admin_author
from b3.plugins.admin import __version__ as admin_version
from b3.plugins.adv import __author__ as adv_author
from b3.plugins.adv import __version__ as adv_version

ADMIN_CONFIG_FILE = os.path.join(os.path.dirname(b3_module__file__), "conf/plugin_admin.ini")


class Admin_functional_test(B3TestCase):
    """ tests from a class inheriting from Admin_functional_test must call self.init() """
    def setUp(self):
        B3TestCase.setUp(self)
        self.conf = CfgConfigParser()
        self.p = AdminPlugin(self.console, self.conf)

    def init(self, config_content=None):
        """ optionally specify a config for the plugin. If called with no parameter, then the default config is loaded """
        if config_content is None:
            if not os.path.isfile(ADMIN_CONFIG_FILE):
                B3TestCase.tearDown(self) # we are skipping the test at a late stage after setUp was called
                raise unittest.SkipTest("%s is not a file" % ADMIN_CONFIG_FILE)
            else:
                self.conf.load(ADMIN_CONFIG_FILE)
        else:
            self.conf.loadFromString(config_content)

        self.p._commands = {}
        self.p.onLoadConfig()
        self.p.onStartup()

        self.joe = FakeClient(self.console, name="Joe", exactName="Joe", guid="joeguid", groupBits=128, team=TEAM_RED)
        self.mike = FakeClient(self.console, name="Mike", exactName="Mike", guid="mikeguid", groupBits=1, team=TEAM_BLUE)


class Cmd_baninfo(Admin_functional_test):

    def test_no_parameter(self):
        # GIVEN
        self.init()
        self.joe.connects(0)
        # WHEN
        self.joe.says('!baninfo')
        # THEN
        self.assertListEqual(['Invalid parameters'], self.joe.message_history)

    def test_no_ban(self):
        # GIVEN
        self.init()
        self.joe.connects(0)
        self.mike.connects(1)
        # WHEN
        self.joe.says('!baninfo mike')
        # THEN
        self.assertListEqual(['Mike has no active bans'], self.joe.message_history)

    def test_perm_ban(self):
        # GIVEN
        self.init()
        self.joe.connects(0)
        self.mike.connects(1)
        self.joe.says('!permban mike f00')
        # WHEN
        self.joe.says('!baninfo @%s' % self.mike.id)
        # THEN
        self.assertListEqual(['Mike has 1 active bans'], self.joe.message_history)

    def test_temp_ban(self):
        # GIVEN
        self.init()
        self.joe.connects(0)
        self.mike.connects(1)
        self.joe.says('!ban mike f00')
        # WHEN
        self.joe.says('!baninfo @%s' % self.mike.id)
        # THEN
        self.assertListEqual(['Mike has 1 active bans'], self.joe.message_history)

    def test_multiple_bans(self):
        # GIVEN
        self.init()
        self.joe.connects(0)
        self.mike.connects(1)
        self.joe.says('!ban @%s f00' % self.mike.id)
        self.joe.says('!permban @%s f00' % self.mike.id)
        # WHEN
        self.joe.says('!baninfo @%s' % self.mike.id)
        # THEN
        self.assertListEqual(['Mike has 2 active bans'], self.joe.message_history)

    def test_no_ban_custom_message(self):
        # WHEN
        self.init("""
[commands]
baninfo: mod
[messages]
baninfo_no_bans: %(name)s is not banned
""")
        self.joe.connects(0)
        self.mike.connects(1)
        self.joe.says('!baninfo mike')
        # THEN
        self.assertListEqual(['Mike is not banned'], self.joe.message_history)

    def test_perm_ban_custom_message(self):
        # GIVEN
        self.init("""
[commands]
permban: fulladmin
baninfo: mod
[messages]
baninfo: %(name)s is banned
""")
        self.joe.connects(0)
        self.mike.connects(1)
        self.joe.says('!permban mike f00')
        # WHEN
        self.joe.says('!baninfo @%s' % self.mike.id)
        # THEN
        self.assertListEqual(['Mike is banned'], self.joe.message_history)


class Cmd_putgroup(Admin_functional_test):

    def setUp(self):
        Admin_functional_test.setUp(self)
        # GIVEN
        self.init("""
[commands]
putgroup: admin
[messages]
group_unknown: Unkonwn group: %(group_name)s
group_beyond_reach: You can't assign players to group %(group_name)s
""")
        self.joe.connects(0)
        self.mike.connects(1)
        self.assertEqual('user', self.mike.maxGroup.keyword)

    def test_nominal(self):
        # WHEN
        self.joe.clearMessageHistory()
        self.joe.says('!putgroup mike fulladmin')
        # THEN
        self.assertListEqual(['Mike put in group Full Admin'], self.joe.message_history)
        self.assertEqual('fulladmin', self.mike.maxGroup.keyword)

    def test_non_existing_group(self):
        # WHEN
        self.joe.clearMessageHistory()
        self.joe.says('!putgroup mike f00')
        # THEN
        self.assertListEqual(['Unkonwn group: f00'], self.joe.message_history)
        self.assertEqual('user', self.mike.maxGroup.keyword)

    def test_non_existing_player(self):
        # WHEN
        self.joe.clearMessageHistory()
        self.joe.says('!putgroup f00 admin')
        # THEN
        self.assertListEqual(['No players found matching f00'], self.joe.message_history)
        self.assertEqual('user', self.mike.maxGroup.keyword)

    def test_no_parameter(self):
        # WHEN
        self.joe.clearMessageHistory()
        self.joe.says('!putgroup')
        # THEN
        self.assertListEqual(['Invalid parameters'], self.joe.message_history)
        self.assertEqual('user', self.mike.maxGroup.keyword)

    def test_one_parameter(self):
        # WHEN
        self.joe.clearMessageHistory()
        self.joe.says('!putgroup mike')
        # THEN
        self.assertListEqual(['Invalid parameters'], self.joe.message_history)
        self.assertEqual('user', self.mike.maxGroup.keyword)

    def test_too_many_parameters(self):
        # WHEN
        self.joe.clearMessageHistory()
        self.joe.says('!putgroup mike fulladmin 5')
        # THEN
        self.assertListEqual(['Invalid parameters'], self.joe.message_history)
        self.assertEqual('user', self.mike.maxGroup.keyword)

    def test_already_in_group(self):
        # WHEN
        self.joe.clearMessageHistory()
        self.joe.says('!putgroup mike user')
        # THEN
        self.assertListEqual(['Mike is already in group User'], self.joe.message_history)
        self.assertEqual('user', self.mike.maxGroup.keyword)

    def test_group_beyond_reach(self):
        # GIVEN
        jack = FakeClient(self.console, name="Jack", guid="jackguid", groupBits=40, team=TEAM_RED)
        jack.connects(3)
        self.assertEqual('fulladmin', jack.maxGroup.keyword)
        # WHEN
        jack.clearMessageHistory()
        jack.says('!putgroup mike fulladmin')
        # THEN
        self.assertEqual('user', self.mike.maxGroup.keyword)
        self.assertListEqual(["You can't assign players to group Full Admin"], jack.message_history)
        # WHEN
        jack.clearMessageHistory()
        jack.says('!putgroup mike admin')
        # THEN
        self.assertEqual('admin', self.mike.maxGroup.keyword)
        self.assertListEqual(['Mike put in group Admin'], jack.message_history)


class Cmd_tempban(Admin_functional_test):

    def setUp(self):
        Admin_functional_test.setUp(self)
        self.init()
        self.joe.message = Mock()
        self.joe.connects(0)

    def test_no_duration(self):
        self.mike.connects(1)
        self.joe.says('!tempban mike')
        self.joe.message.assert_called_with('^7Invalid parameters')

    def test_bad_duration(self):
        self.mike.connects(1)
        self.mike.tempban = Mock()
        self.joe.says('!tempban mike 5hour')
        self.joe.message.assert_called_with('^7Invalid parameters')
        assert not self.mike.tempban.called

    def test_non_existing_player(self):
        self.mike.connects(1)
        self.joe.says('!tempban foo 5h')
        self.joe.message.assert_called_with('^7No players found matching foo')

    def test_no_reason(self):
        self.mike.connects(1)
        self.mike.tempban = Mock()
        self.joe.says('!tempban mike 5h')
        self.mike.tempban.assert_called_with('', None, 5*60, self.joe)


class Cmd_pluginfo(Admin_functional_test):

    def setUp(self):
        Admin_functional_test.setUp(self)
        self.init()
        self.joe.message = Mock()
        self.joe.connects(0)

    def test_invalid_parameters(self):
        self.joe.says("!pluginfo")
        self.joe.message.assert_called_with('^7Invalid parameters')

    def test_invalid_plugin(self):
        self.joe.says('!pluginfo foo')
        self.joe.message.assert_called_with('^7No plugin named ^1foo ^7loaded')

    def test_admin_plugin(self):
        self.joe.says('!pluginfo admin')
        self.joe.message.assert_called_with('^7AdminPlugin ^7v^3%s ^7by ^3%s' % (admin_version, admin_author))

    def test_adv_plugin(self):
        self.joe.says('!pluginfo adv')
        self.joe.message.assert_called_with('^7AdvPlugin ^7v^3%s ^7by ^3%s' % (adv_version, adv_author))


class Cmd_lastbans(Admin_functional_test):

    def setUp(self):
        Admin_functional_test.setUp(self)
        self.init()
        self.joe.message = Mock()
        self.joe.connects(0)

    def test_no_ban(self):
        self.joe.says('!lastbans')
        self.joe.message.assert_called_with('^7There are no active bans')

    @patch('time.time', return_value=0)
    def test_one_tempban(self, mock_time):
        # GIVEN
        self.mike.connects(1)
        # WHEN
        self.joe.says('!tempban mike 5h test reason')
        self.joe.says('!lastbans')
        # THEN
        self.joe.message.assert_called_with(u'^2@2^7 Mike^7^7 (5 hours remaining) test reason')
        # WHEN
        self.joe.says('!unban @2')
        self.joe.says('!lastbans')
        # THEN
        self.joe.message.assert_called_with('^7There are no active bans')


class Cmd_help(Admin_functional_test):

    def setUp(self):
        Admin_functional_test.setUp(self)
        self.p._commands = {}  # make sure to empty the commands list as _commands is a wrongly a class property
        self.init()
        self.joe.message = Mock()
        self.joe.connects(0)

    def test_non_existing_cmd(self):
        self.joe.says('!help fo0')
        self.joe.message.assert_called_with('^7Command not found fo0')

    def test_existing_cmd(self):
        self.joe.says('!help help')
        self.joe.message.assert_called_with('^2!help ^7%s' % self.p.cmd_help.__doc__.strip())

    def test_no_arg(self):
        self.joe.says('!help')
        self.joe.message.assert_called_with('^7Available commands: admins, admintest, aliases, b3, ban, banall, baninfo'
                                            ', clear, clientinfo, die, disable, enable, find, help, iamgod, kick, kicka'
                                            'll, lastbans, leveltest, list, lookup, makereg, map, maprotate, maps, mask'
                                            ', nextmap, notice, pause, permban, pluginfo, poke, putgroup, rebuild, reco'
                                            'nfig, regtest, regulars, restart, rules, runas, say, scream, seen, spam, s'
                                            'pams, spank, spankall, status, tempban, time, unban, ungroup, unmask, unre'
                                            'g, warn, warnclear, warninfo, warnremove, warns, warntest')
        self.mike.message = Mock()
        self.mike.connects(0)
        self.mike.says('!help')
        self.mike.message.assert_called_with('^7Available commands: help, iamgod, regtest, regulars, rules, time')

    def test_joker(self):
        self.joe.says('!help *ban')
        self.joe.message.assert_called_with('^7Available commands: ban, banall, baninfo, lastbans, permban, tempban, unban')


class Cmd_mask(Admin_functional_test):

    def setUp(self):
        Admin_functional_test.setUp(self)
        self.init()

    def test_nominal(self):
        self.joe.message = Mock(wraps=lambda x: sys.stdout.write("\t\t" + x + "\n"))
        self.joe.connects(0)
        # only superadmin joe is connected
        self.joe.says('!admins')
        self.joe.message.assert_called_with('^7Admins online: Joe^7^7 [^3100^7]')
        # introducing mike (senioradmin)
        self.mike.connects(1)
        self.joe.says('!putgroup mike senioradmin')
        # we know have 2 admins connected
        self.joe.says('!admins')
        self.joe.message.assert_called_with('^7Admins online: Joe^7^7 [^3100^7], Mike^7^7 [^380^7]')
        # joe masks himself as a user
        self.joe.says('!mask user')
        self.joe.says('!admins')
        self.joe.message.assert_called_with('^7Admins online: Mike^7^7 [^380^7]')
        # joe unmasks himself
        self.joe.says('!unmask')
        self.joe.says('!admins')
        self.joe.message.assert_called_with('^7Admins online: Joe^7^7 [^3100^7], Mike^7^7 [^380^7]')
        # joe masks mike as a user
        self.joe.says('!mask user mike')
        self.joe.says('!admins')
        self.joe.message.assert_called_with('^7Admins online: Joe^7^7 [^3100^7]')
        # joe unmasks mike
        self.joe.says('!unmask mike')
        self.joe.says('!admins')
        self.joe.message.assert_called_with('^7Admins online: Joe^7^7 [^3100^7], Mike^7^7 [^380^7]')

    def _test_persistence_for_group(self, group_keyword):
        """
        Makes sure that a user with group 'superadmin', when masked as the given group is still masked with
        that given group once he reconnects. Hence making sure we persists the mask group between connections.
        :param group_keyword: str
        """
        group_to_mask_as = self.console.storage.getGroup(Group(keyword=group_keyword))
        self.assertIsNotNone(group_to_mask_as)
        ## GIVEN that joe masks himself
        self.joe.connects(0)
        self.joe.says('!mask ' + group_keyword)
        self.assertEqual(128, self.joe.maxGroup.id)
        self.assertEqual(100, self.joe.maxGroup.level)
        self.assertIsNotNone(self.joe.maskGroup, "expecting Joe to have a masked group")
        self.assertEqual(group_to_mask_as.id, self.joe.maskGroup.id, "expecting Joe2 to have %s for the mask group id" % group_to_mask_as.id)
        self.assertEqual(group_to_mask_as.level, self.joe.maskGroup.level, "expecting Joe2 to have %s for the mask group level" % group_to_mask_as.level)
        self.assertEqual(group_to_mask_as.id, self.joe.maskedGroup.id, "expecting Joe2 to have %s for the masked group id" % group_to_mask_as.id)
        self.assertEqual(group_to_mask_as.level, self.joe.maskedGroup.level, "expecting Joe2 to have %s for the masked group level" % group_to_mask_as.level)
        ## WHEN joe reconnects
        self.joe.disconnects()
        client = self.console.storage.getClient(Client(id=self.joe.id))
        joe2 = FakeClient(self.console, **client.__dict__)
        joe2.connects(1)
        ## THEN joe is still masked
        self.assertEqual(128, joe2.maxGroup.id)
        self.assertEqual(100, joe2.maxGroup.level)
        self.assertIsNotNone(joe2.maskGroup, "expecting Joe2 to have a masked group")
        self.assertEqual(group_to_mask_as.id, joe2.maskGroup.id, "expecting Joe2 to have %s for the mask group id" % group_to_mask_as.id)
        self.assertEqual(group_to_mask_as.level, joe2.maskGroup.level, "expecting Joe2 to have %s for the mask group level" % group_to_mask_as.level)
        self.assertEqual(group_to_mask_as.id, joe2.maskedGroup.id, "expecting Joe2 to have %s for the masked group id" % group_to_mask_as.id)
        self.assertEqual(group_to_mask_as.level, joe2.maskedGroup.level, "expecting Joe2 to have %s for the masked group level" % group_to_mask_as.level)
        ## THEN the content of the mask_level column in the client table must be correct
        client_data = self.console.storage.getClient(Client(id=joe2.id))
        self.assertIsNotNone(client_data)
        self.assertEqual(group_to_mask_as.level, client_data._maskLevel, "expecting %s to be the value in the mask_level column in database" % group_to_mask_as.level)

    def test_persistence(self):
        self._test_persistence_for_group("user")
        self._test_persistence_for_group("reg")
        self._test_persistence_for_group("mod")
        self._test_persistence_for_group("admin")
        self._test_persistence_for_group("fulladmin")
        self._test_persistence_for_group("senioradmin")
        self._test_persistence_for_group("superadmin")


class Cmd_makereg_unreg(Admin_functional_test):
    def setUp(self):
        Admin_functional_test.setUp(self)
        self.init()
        self.group_user = self.console.storage.getGroup(Group(keyword='user'))
        self.group_reg = self.console.storage.getGroup(Group(keyword='reg'))
        self.joe.message = Mock(wraps=lambda x: sys.stdout.write("\t\t" + x + "\n"))
        self.joe.connects(0)
        self.mike.connects(1)

    def test_nominal(self):
        # GIVEN
        self.assertTrue(self.mike.inGroup(self.group_user))
        self.assertFalse(self.mike.inGroup(self.group_reg))
        # WHEN
        self.joe.says("!makereg mike")
        # THEN
        self.assertFalse(self.mike.inGroup(self.group_user))
        self.assertTrue(self.mike.inGroup(self.group_reg))
        self.joe.message.assert_called_with('^7Mike^7 ^7put in group Regular')
        # WHEN
        self.joe.says("!unreg mike")
        # THEN
        self.assertTrue(self.mike.inGroup(self.group_user))
        self.assertFalse(self.mike.inGroup(self.group_reg))
        self.joe.message.assert_called_with('^7Mike^7^7 removed from group Regular')


    def test_unreg_when_not_regular(self):
        # GIVEN
        self.assertTrue(self.mike.inGroup(self.group_user))
        self.assertFalse(self.mike.inGroup(self.group_reg))
        # WHEN
        self.joe.says("!unreg mike")
        # THEN
        self.assertTrue(self.mike.inGroup(self.group_user))
        self.assertFalse(self.mike.inGroup(self.group_reg))
        self.joe.message.assert_called_with('^7Mike^7^7 is not in group Regular')


    def test_makereg_when_already_regular(self):
        # GIVEN
        self.mike.addGroup(self.group_reg)
        self.mike.remGroup(self.group_user)
        self.assertTrue(self.mike.inGroup(self.group_reg))
        # WHEN
        self.joe.says("!makereg mike")
        # THEN
        self.assertFalse(self.mike.inGroup(self.group_user))
        self.assertTrue(self.mike.inGroup(self.group_reg))
        self.joe.message.assert_called_with('^7Mike^7^7 is already in group Regular')


    def test_makereg_no_parameter(self):
        # WHEN
        self.joe.says("!makereg")
        # THEN
        self.joe.message.assert_called_with('^7Invalid parameters')


    def test_unreg_no_parameter(self):
        # WHEN
        self.joe.says("!unreg")
        # THEN
        self.joe.message.assert_called_with('^7Invalid parameters')


    def test_makereg_unknown_player(self):
        # WHEN
        self.joe.says("!makereg foo")
        # THEN
        self.joe.message.assert_called_with('^7No players found matching foo')


    def test_unreg_unknown_player(self):
        # WHEN
        self.joe.says("!unreg foo")
        # THEN
        self.joe.message.assert_called_with('^7No players found matching foo')


def _start_new_thread(callable, args_list, kwargs_dict):
    """ used to patch thread.start_new_thread so it won't create a new thread but call the callable synchronously """
    callable(*args_list, **kwargs_dict)

@patch.object(time, "sleep")
@patch.object(thread, "start_new_thread", wraps=_start_new_thread)
class Cmd_rules(Admin_functional_test):
    def setUp(self):
        Admin_functional_test.setUp(self)
        self.init()

    def test_nominal(self, start_new_thread_mock, sleep_mock):
        self.joe.message = Mock(wraps=lambda x: sys.stdout.write("\t\t" + x + "\n"))
        self.joe.connects(0)
        self.joe.says('!rules')
        self.joe.message.assert_has_calls([call('^3Rule #1: No racism of any kind'),
                                           call('^3Rule #2: No clan stacking, members must split evenly between the teams'),
                                           call('^3Rule #3: No arguing with admins (listen and learn or leave)'),
                                           call('^3Rule #4: No abusive language or behavior towards admins or other players'),
                                           call('^3Rule #5: No offensive or potentially offensive names, annoying names, or in-game (double caret (^)) color in names'),
                                           call('^3Rule #6: No recruiting for your clan, your server, or anything else'),
                                           call('^3Rule #7: No advertising or spamming of websites or servers'),
                                           call('^3Rule #8: No profanity or offensive language (in any language)'),
                                           call('^3Rule #9: Do ^1NOT ^3fire at teammates or within 10 seconds of spawning'),
                                           call('^3Rule #10: Offense players must play for the objective and support their team')])

    def test_nominal_loud(self, start_new_thread_mock, sleep_mock):
        self.console.say = Mock(wraps=lambda x: sys.stdout.write("\t\t" + x + "\n"))
        self.joe.connects(0)
        self.joe.says('@rules')
        self.console.say.assert_has_calls([call('^3Rule #1: No racism of any kind'),
                                           call('^3Rule #2: No clan stacking, members must split evenly between the teams'),
                                           call('^3Rule #3: No arguing with admins (listen and learn or leave)'),
                                           call('^3Rule #4: No abusive language or behavior towards admins or other players'),
                                           call('^3Rule #5: No offensive or potentially offensive names, annoying names, or in-game (double caret (^)) color in names'),
                                           call('^3Rule #6: No recruiting for your clan, your server, or anything else'),
                                           call('^3Rule #7: No advertising or spamming of websites or servers'),
                                           call('^3Rule #8: No profanity or offensive language (in any language)'),
                                           call('^3Rule #9: Do ^1NOT ^3fire at teammates or within 10 seconds of spawning'),
                                           call('^3Rule #10: Offense players must play for the objective and support their team')])

    def test_nominal_bigtext(self, start_new_thread_mock, sleep_mock):
        self.console.saybig = Mock(wraps=lambda x: sys.stdout.write("\t\t" + x + "\n"))
        self.joe.connects(0)
        self.joe.says('&rules')
        self.console.saybig.assert_has_calls([call('^3Rule #1: No racism of any kind'),
                                           call('^3Rule #2: No clan stacking, members must split evenly between the teams'),
                                           call('^3Rule #3: No arguing with admins (listen and learn or leave)'),
                                           call('^3Rule #4: No abusive language or behavior towards admins or other players'),
                                           call('^3Rule #5: No offensive or potentially offensive names, annoying names, or in-game (double caret (^)) color in names'),
                                           call('^3Rule #6: No recruiting for your clan, your server, or anything else'),
                                           call('^3Rule #7: No advertising or spamming of websites or servers'),
                                           call('^3Rule #8: No profanity or offensive language (in any language)'),
                                           call('^3Rule #9: Do ^1NOT ^3fire at teammates or within 10 seconds of spawning'),
                                           call('^3Rule #10: Offense players must play for the objective and support their team')])

    def test_nominal_to_player(self, start_new_thread_mock, sleep_mock):
        self.joe.message = Mock(wraps=lambda x: sys.stdout.write("\t\t" + x + "\n"))
        self.joe.connects(0)
        self.mike.message = Mock(wraps=lambda x: sys.stdout.write("\t\t" + x + "\n"))
        self.mike.connects(1)
        self.joe.says('!rules mike')
        self.mike.message.assert_has_calls([call('^3Rule #1: No racism of any kind'),
                                           call('^3Rule #2: No clan stacking, members must split evenly between the teams'),
                                           call('^3Rule #3: No arguing with admins (listen and learn or leave)'),
                                           call('^3Rule #4: No abusive language or behavior towards admins or other players'),
                                           call('^3Rule #5: No offensive or potentially offensive names, annoying names, or in-game (double caret (^)) color in names'),
                                           call('^3Rule #6: No recruiting for your clan, your server, or anything else'),
                                           call('^3Rule #7: No advertising or spamming of websites or servers'),
                                           call('^3Rule #8: No profanity or offensive language (in any language)'),
                                           call('^3Rule #9: Do ^1NOT ^3fire at teammates or within 10 seconds of spawning'),
                                           call('^3Rule #10: Offense players must play for the objective and support their team')])

    def test_unknown_player(self, start_new_thread_mock, sleep_mock):
        self.joe.message = Mock(wraps=lambda x: sys.stdout.write("\t\t" + x + "\n"))
        self.joe.connects(0)
        self.joe.says('!rules fOO')
        self.joe.message.assert_has_calls([call('^7No players found matching fOO')])


class Cmd_warns(Admin_functional_test):
    def setUp(self):
        Admin_functional_test.setUp(self)
        self.init()

    def test_nominal(self):
        self.joe.message = Mock(wraps=lambda x: sys.stdout.write("\t\t" + x + "\n"))
        self.joe.connects(0)
        self.joe.says('!warns')
        self.joe.message.assert_called_once_with('^7Warnings: adv, afk, argue, badname, camp, ci, color, cuss, fakecmd,'
        ' jerk, lang, language, name, nocmd, obj, profanity, racism, recruit, rule1, rule10, rule2, rule3, rule4, rule5'
        ', rule6, rule7, rule8, rule9, sfire, spam, spawnfire, spec, spectator, stack, tk')


class Test_warn_reasons_default_config(Admin_functional_test):
    def setUp(self):
        Admin_functional_test.setUp(self)
        self.init()
        self.joe.connects(0)
        self.mike.connects(1)

    def test_no_reason(self):
        with patch.object(self.mike, "warn") as mock:
            self.joe.says('!warn mike')
            mock.assert_has_calls([call(60.0, '^7behave yourself', None, self.joe, '')])

    def test_reason_is_not_a_keyword(self):
        with patch.object(self.mike, "warn") as mock:
            self.joe.says('!warn mike f00')
            mock.assert_has_calls([call(60.0, '^7 f00', 'f00', self.joe, '')])

    def test_reason_is_a_keyword(self):
        with patch.object(self.mike, "warn") as warn_mock:
            def assertWarn(keyword, duration, text):
                # GIVEN
                warn_mock.reset_mock()
                self.mike.delvar(self.p, 'warnTime')
                # WHEN
                self.joe.says('!warn mike %s' % keyword)
                # THEN
                warn_mock.assert_has_calls([call(float(duration), text, keyword, self.joe, '')])

            assertWarn("rule1", 14400, '^3Rule #1: No racism of any kind')
            assertWarn("rule2", 1440, '^3Rule #2: No clan stacking, members must split evenly between the teams')
            assertWarn("rule3", 1440, '^3Rule #3: No arguing with admins (listen and learn or leave)')
            assertWarn("rule4", 1440, '^3Rule #4: No abusive language or behavior towards admins or other players')
            assertWarn("rule5", 60, '^3Rule #5: No offensive or potentially offensive names, annoying names, or in-game (double caret (^)) color in names')
            assertWarn("rule6", 1440, '^3Rule #6: No recruiting for your clan, your server, or anything else')
            assertWarn("rule7", 1440, '^3Rule #7: No advertising or spamming of websites or servers')
            assertWarn("rule8", 4320, '^3Rule #8: No profanity or offensive language (in any language)')
            assertWarn("rule9", 180, '^3Rule #9: Do ^1NOT ^3fire at teammates or within 10 seconds of spawning')
            assertWarn("rule10", 4320, '^3Rule #10: Offense players must play for the objective and support their team')
            assertWarn("stack", 1440, '^3Rule #2: No clan stacking, members must split evenly between the teams')
            assertWarn("lang", 4320, '^3Rule #8: No profanity or offensive language (in any language)')
            assertWarn("language", 4320, '^3Rule #8: No profanity or offensive language (in any language)')
            assertWarn("cuss", 4320, '^3Rule #8: No profanity or offensive language (in any language)')
            assertWarn("profanity", 4320, '^3Rule #8: No profanity or offensive language (in any language)')
            assertWarn("name", 60, '^3Rule #5: No offensive or potentially offensive names, annoying names, or in-game (double caret (^)) color in names')
            assertWarn("color", 60, '^7No in-game (double caret (^)) color in names')
            assertWarn("badname", 60, '^7No offensive, potentially offensive, or annoying names')
            assertWarn("spec", 5, '^7spectator too long on full server')
            assertWarn("adv", 1440, '^3Rule #7: No advertising or spamming of websites or servers')
            assertWarn("racism", 14400, '^3Rule #1: No racism of any kind')
            assertWarn("stack", 1440, '^3Rule #2: No clan stacking, members must split evenly between the teams')
            assertWarn("recruit", 1440, '^3Rule #6: No recruiting for your clan, your server, or anything else')
            assertWarn("argue", 1440, '^3Rule #3: No arguing with admins (listen and learn or leave)')
            assertWarn("sfire", 180, '^3Rule #9: Do ^1NOT ^3fire at teammates or within 10 seconds of spawning')
            assertWarn("spawnfire", 180, '^3Rule #9: Do ^1NOT ^3fire at teammates or within 10 seconds of spawning')
            assertWarn("jerk", 1440, '^3Rule #4: No abusive language or behavior towards admins or other players')
            assertWarn("afk", 5, '^7you appear to be away from your keyboard')
            assertWarn("tk", 1440, '^7stop team killing!')
            assertWarn("obj", 60, '^7go for the objective!')
            assertWarn("camp", 60, '^7stop camping or you will be kicked!')
            assertWarn("fakecmd", 60, '^7do not use fake commands')
            assertWarn("nocmd", 60, '^7do not use commands that you do not have access to, try using !help')
            assertWarn("ci", 5, '^7connection interupted, reconnect')
            assertWarn("spectator", 5, '^7spectator too long on full server')
            assertWarn("spam", 60, '^7do not spam, shut-up!')


class Test_reason_keywords(Admin_functional_test):
    def setUp(self):
        Admin_functional_test.setUp(self)
        self.init()
        self.joe.connects(0)
        self.mike.connects(1)
        self.adv_text = "^3Rule #7: No advertising or spamming of websites or servers"


    def test_warn_with_keyword(self):
        with patch.object(self.console, "say") as say_mock:
            self.joe.says('!warn mike adv')
            say_mock.assert_has_calls([call('^1WARNING^7 [^31^7]: Mike^7^7, %s' % self.adv_text)])

    def test_warn_with_unknown_keyword(self):
        with patch.object(self.console, "say") as say_mock:
            self.joe.says('!warn mike f00')
            say_mock.assert_has_calls([call('^1WARNING^7 [^31^7]: Mike^7^7, ^7 f00')])


    def test_notice_with_keyword(self):
        with patch.object(self.mike, "notice") as notice_mock:
            self.joe.says('!notice mike adv')
            notice_mock.assert_has_calls([call('adv', None, self.joe)])

    def test_notice_with_unknown_keyword(self):
        with patch.object(self.mike, "notice") as notice_mock:
            self.joe.says('!notice mike f00')
            notice_mock.assert_has_calls([call('f00', None, self.joe)])


    def test_kick_with_keyword(self):
        with patch.object(self.console, "kick") as kick_mock:
            self.joe.says('!kick mike adv')
            kick_mock.assert_has_calls([call(self.mike, self.adv_text, self.joe, False)])

    def test_kick_with_unknown_keyword(self):
        with patch.object(self.console, "kick") as kick_mock:
            self.joe.says('!kick mike f00')
            kick_mock.assert_has_calls([call(self.mike, 'f00', self.joe, False)])


    def test_ban_with_keyword(self):
        with patch.object(self.mike, "tempban") as tempban_mock:
            self.joe.says('!ban mike adv')
            tempban_mock.assert_has_calls([call(self.adv_text, 'adv', 20160.0, self.joe)])

    def test_ban_with_unknown_keyword(self):
        with patch.object(self.mike, "tempban") as tempban_mock:
            self.joe.says('!ban mike f00')
            tempban_mock.assert_has_calls([call('f00', 'f00', 20160.0, self.joe)])


    def test_permban_with_keyword(self):
        with patch.object(self.mike, "ban") as permban_mock:
            self.joe.says('!permban mike adv')
            permban_mock.assert_has_calls([call(self.adv_text, 'adv', self.joe)])

    def test_permban_with_unknown_keyword(self):
        with patch.object(self.mike, "ban") as permban_mock:
            self.joe.says('!permban mike f00')
            permban_mock.assert_has_calls([call('f00', 'f00', self.joe)])


@unittest.skipUnless(os.path.isfile(ADMIN_CONFIG_FILE), "%s is not a file" % ADMIN_CONFIG_FILE)
class Test_config(Admin_functional_test):
    def setUp(self):
        Admin_functional_test.setUp(self)
        logging.getLogger('output').setLevel(logging.INFO)

    def test_no_generic_or_default_warn_reason(self):

        # load the default plugin_admin.ini file after having remove the 'generic' setting from section 'warn_reasons'
        new_config_content = ""
        with open(ADMIN_CONFIG_FILE) as config_file:
            is_in_warn_reasons_section = False
            for line in config_file:
                if line == '[warn_reasons]':
                    is_in_warn_reasons_section = True
                if not is_in_warn_reasons_section:
                    new_config_content += (line + '\n')
                else:
                    if line.startswith('['):
                        new_config_content += (line + '\n')
                        is_in_warn_reasons_section = False
                    else:
                        if line.startswith("generic") or line.startswith("default"):
                            pass
                        else:
                            new_config_content += (line + '\n')
        self.init(new_config_content)

        self.joe.message = Mock(lambda x: sys.stdout.write("message to Joe: " + x + "\n"))
        self.joe.connects(0)
        self.joe.says('!warntest')
        self.joe.message.assert_called_once_with('^2TEST: ^1WARNING^7 [^31^7]: ^7behave yourself')
        self.joe.message.reset_mock()
        self.joe.says('!warntest argue')
        self.joe.message.assert_called_once_with('^2TEST: ^1WARNING^7 [^31^7]: ^3Rule #3: No arguing with admins (listen and learn or leave)')


    def test_bad_format_for_generic_and_default(self):
        self.init("""[warn_reasons]
generic: 1h
default: /
""")
        self.assertEqual((60, "^7"), self.p.warn_reasons['generic'])
        self.assertEqual((60, "^7behave yourself"), self.p.warn_reasons['default'])

    def test_bad_format_1(self):
        self.init("""[warn_reasons]
foo: foo
bar: 5d
""")
        self.assertNotIn('foo', self.p.warn_reasons)

    def test_bad_format_2(self):
        self.init("""[warn_reasons]
foo: /foo bar
""")
        self.assertNotIn('foo', self.p.warn_reasons)

    def test_bad_format_3(self):
        self.init("""[warn_reasons]
foo: /spam#
bar: /spam# qsdf sq
""")
        self.assertNotIn('foo', self.p.warn_reasons)

    def test_reference_to_warn_reason(self):
        self.init("""[warn_reasons]
foo: 2h, foo
bar: /foo
""")
        self.assertIn('foo', self.p.warn_reasons)
        self.assertEqual((120, 'foo'), self.p.warn_reasons['foo'])
        self.assertIn('bar', self.p.warn_reasons)
        self.assertEqual((120, 'foo'), self.p.warn_reasons['bar'])


    def test_invalid_reference_to_warn_reason(self):
        self.init("""[warn_reasons]
foo: 2h, foo
bar: /nonexisting
""")
        self.assertIn('foo', self.p.warn_reasons)
        self.assertEqual((120, 'foo'), self.p.warn_reasons['foo'])
        self.assertNotIn('bar', self.p.warn_reasons)


    def test_reference_to_spamage(self):
        self.init("""[spamages]
foo: fOO fOO
[warn_reasons]
bar: 4h, /spam#foo
""")
        self.assertIn('bar', self.p.warn_reasons)
        self.assertEqual((240, 'fOO fOO'), self.p.warn_reasons['bar'])


    def test_invalid_reference_to_spamage(self):
        self.init("""[warn_reasons]
bar: 4h, /spam#foo
""")
        self.assertNotIn('bar', self.p.warn_reasons)


class Cmd_admins(Admin_functional_test):

    def test_no_admin(self):
        # GIVEN
        self.init("""
[commands]
admins: user
""")
        self.mike.connects(0)
        # only user Mike is connected
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says('!admins')
        # THEN
        self.assertListEqual(['There are no admins online'], self.mike.message_history)

    def test_no_admin_custom_message(self):
        # GIVEN
        self.init("""
[commands]
admins: user
[messages]
no_admins: no admins
""")
        self.mike.connects(0)
        # only user Mike is connected
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says('!admins')
        # THEN
        self.assertListEqual(['no admins'], self.mike.message_history)

    def test_no_admin_blank_message(self):
        # GIVEN
        self.init("""
[commands]
admins: user
[messages]
no_admins:
""")
        self.mike.connects(0)
        # only user Mike is connected
        # WHEN
        self.mike.clearMessageHistory()
        self.mike.says('!admins')
        # THEN
        self.assertListEqual([], self.mike.message_history)

    def test_one_admin(self):
        # GIVEN
        self.init()
        self.joe.connects(0)
        # only superadmin joe is connected
        # WHEN
        self.joe.clearMessageHistory()
        self.joe.says('!admins')
        # THEN
        self.assertListEqual(['Admins online: Joe [100]'], self.joe.message_history)

    def test_one_admin_custom_message(self):
        # GIVEN
        self.init("""
[commands]
admins: mod
[messages]
admins: online admins: %s
""")
        self.joe.connects(0)
        # WHEN
        self.joe.clearMessageHistory()
        self.joe.says('!admins')
        # THEN
        self.assertListEqual(['online admins: Joe [100]'], self.joe.message_history)

    def test_two_admins(self):
        # GIVEN
        self.init()
        self.joe.connects(0)
        self.mike.connects(1)
        self.joe.says('!putgroup mike senioradmin')
        # WHEN
        self.joe.clearMessageHistory()
        self.joe.says('!admins')
        # THEN
        self.assertListEqual(['Admins online: Joe [100], Mike [80]'], self.joe.message_history)


class Cmd_regulars(Admin_functional_test):
    def setUp(self):
        Admin_functional_test.setUp(self)
        self.init()
        self.joe.message = Mock(wraps=lambda x: sys.stdout.write("\t\t" + x + "\n"))
        self.joe.connects(0)

    def test_no_regular(self):
        # only superadmin joe is connected
        self.joe.says('!regulars')
        self.joe.message.assert_called_with('^7There are no regular players online')

    def test_one_regular(self):
        # GIVEN
        self.mike.connects(1)
        self.joe.says('!makereg mike')
        # WHEN
        self.joe.says('!regs')
        # THEN
        self.joe.message.assert_called_with('^7Regular players online: Mike^7')

    def test_two_regulars(self):
        # GIVEN
        self.mike.connects(1)
        self.joe.says('!makereg mike')
        self.jack = FakeClient(self.console, name="Jack", guid="jackguid", groupBits=1)
        self.jack.connects(2)
        self.joe.says('!makereg jack')
        # WHEN
        self.joe.says('!regs')
        # THEN
        self.joe.message.assert_called_with('^7Regular players online: Mike^7, Jack^7')



class Cmd_map(Admin_functional_test):
    def setUp(self):
        Admin_functional_test.setUp(self)
        self.init()

    def test_missing_param(self):
        self.joe.message = Mock(wraps=lambda x: sys.stdout.write("\t\t" + x + "\n"))
        self.joe.connects(0)
        self.joe.says('!map')
        self.joe.message.assert_called_once_with('^7You must supply a map to change to')

    def test_suggestions(self):
        self.joe.message = Mock(wraps=lambda x: sys.stdout.write("\t\t" + x + "\n"))
        self.joe.connects(0)
        when(self.console).changeMap('f00').thenReturn(["bar1", "bar2", "bar3", "bar4", "bar5", "bar6", "bar7", "bar8", "bar9", "bar10", "bar11", "bar"])
        self.joe.says('!map f00')
        self.joe.message.assert_called_once_with('do you mean: bar1, bar2, bar3, bar4, bar5?')

    def test_nominal(self):
        self.joe.message = Mock(wraps=lambda x: sys.stdout.write("\t\t" + x + "\n"))
        self.joe.connects(0)
        when(self.console).changeMap('f00').thenReturn(None)
        self.joe.says('!map f00')
        self.assertEqual(0, self.joe.message.call_count)


class spell_checker(Admin_functional_test):
    def setUp(self):
        Admin_functional_test.setUp(self)
        self.init()
        self.joe.connects(0)

    def test_existing_command(self):
        self.joe.says('!map')
        self.assertEqual(['You must supply a map to change to'], self.joe.message_history)

    def test_misspelled_command(self):
        self.joe.says('!mip')
        self.assertEqual(['Unrecognized command mip. Did you mean !map?'], self.joe.message_history)

    def test_unrecognized_command(self):
        self.joe.says('!qfsmlkjazemlrkjazemrlkj')
        self.assertEqual(['Unrecognized command qfsmlkjazemlrkjazemrlkj'], self.joe.message_history)

    def test_existing_command_loud(self):
        self.joe.says('@map')
        self.assertEqual(['You must supply a map to change to'], self.joe.message_history)

    def test_misspelled_command_loud(self):
        self.joe.says('@mip')
        self.assertEqual(['Unrecognized command mip. Did you mean @map?'], self.joe.message_history)

    def test_unrecognized_command_loud(self):
        self.joe.says('@qfsmlkjazemlrkjazemrlkj')
        self.assertEqual(['Unrecognized command qfsmlkjazemlrkjazemrlkj'], self.joe.message_history)

    def test_existing_command_private(self):
        self.joe.says('/map')
        self.assertEqual(['You must supply a map to change to'], self.joe.message_history)

    def test_misspelled_command_private(self):
        self.joe.says('/mip')
        self.assertEqual(['Unrecognized command mip. Did you mean /map?'], self.joe.message_history)

    def test_unrecognized_command_private(self):
        self.joe.says('/qfsmlkjazemlrkjazemrlkj')
        self.assertEqual(['Unrecognized command qfsmlkjazemlrkjazemrlkj'], self.joe.message_history)

class Cmd_register(Admin_functional_test):
    def setUp(self):
        Admin_functional_test.setUp(self)
        self.p._commands = {}  # make sure to empty the commands list as _commands is a wrongly a class property
        self.say_patcher = patch.object(self.console, "say")
        self.say_mock = self.say_patcher.start()
        self.player = FakeClient(self.console, name="TestPlayer", guid="player_guid", groupBits=0)
        self.player.connects("0")

    def tearDown(self):
        Admin_functional_test.tearDown(self)
        self.say_patcher.stop()

    def test_nominal_with_defaults(self):
        # GIVEN
        self.init(r"""
[commands]
register: guest
[messages]
regme_annouce: %s put in group %s
""")
        # WHEN
        self.player.says('!register')
        # THEN
        self.assertListEqual(['Thanks for your registration. You are now a member of the group User'],
                             self.player.message_history)
        self.assertListEqual([call('TestPlayer^7 put in group User')], self.say_mock.mock_calls)

    def test_custom_messages(self):
        # GIVEN
        self.init(r"""
[commands]
register: guest
[settings]
announce_registration: yes
[messages]
regme_confirmation: You are now a member of the group %s
regme_annouce: %s is now a member of group %s
""")
        # WHEN
        self.player.says('!register')
        # THEN
        self.assertListEqual(['You are now a member of the group User'], self.player.message_history)
        self.assertListEqual([call('TestPlayer^7 is now a member of group User')], self.say_mock.mock_calls)

    def test_no_announce(self):
        # GIVEN
        self.init(r"""
[commands]
register: guest
[settings]
announce_registration: no
[messages]
regme_confirmation: You are now a member of the group %s
regme_annouce: %s is now a member of group %s
""")
        # WHEN
        self.player.says('!register')
        # THEN
        self.assertListEqual(['You are now a member of the group User'], self.player.message_history)
        self.assertListEqual([], self.say_mock.mock_calls)


@patch("time.sleep")
class Cmd_spams(Admin_functional_test):

    def test_nominal(self, sleep_mock):
        # GIVEN
        self.init(r"""
[commands]
spams: 20
[spamages]
foo: foo
rule1: this is rule #1
rule2: this is rule #2
bar: bar
""")
        self.joe.connects(0)
        # WHEN
        self.joe.says('!spams')
        # THEN
        self.assertListEqual(['Spamages: bar, foo, rule1, rule2'], self.joe.message_history)

    def test_no_spamage(self, sleep_mock):
        # GIVEN
        self.init(r"""
[commands]
spams: 20
[spamages]
""")
        self.joe.connects(0)
        # WHEN
        self.joe.says('!spams')
        # THEN
        self.assertListEqual(['No spamage message defined'], self.joe.message_history)

    def test_reconfig_loads_new_spamages(self, sleep_mock):
        # GIVEN
        first_config = r"""
[commands]
spams: 20
[spamages]
foo: foo
rule1: this is rule #1
"""
        second_config = r"""
[commands]
spams: 20
[spamages]
bar: bar
rule2: this is rule #2
"""
        self.init(first_config)
        self.joe.connects(0)
        self.joe.says('!spams')
        self.assertListEqual(['Spamages: foo, rule1'], self.joe.message_history)
        # WHEN the config file content is changed
        self.p.config = CfgConfigParser()
        self.p.config.loadFromString(second_config)
        # THEN
        self.joe.clearMessageHistory()
        self.joe.says('!spams')
        self.assertListEqual(['Spamages: bar, rule2'], self.joe.message_history)


@patch("time.sleep")
class Cmd_warn_and_clear(Admin_functional_test):

    def setUp(self):
        Admin_functional_test.setUp(self)
        # GIVEN
        self.init(r"""
[commands]
warn: user
clear: user
[messages]
warn_too_fast: Only one warning every %(num_second)s seconds can be given
warn_self: %s, you cannot give yourself a warning
warn_denied: %s, %s is a higher level admin, you can't warn him
cleared_warnings: %(admin)s has cleared %(player)s of all warnings
cleared_warnings_for_all: %(admin)s has cleared everyone's warnings and tk points
[warn]
tempban_num: 3
duration_divider: 30
max_duration: 1d
alert: ^1ALERT^7: $name^7 auto-kick from warnings if not cleared [^3$warnings^7] $reason
alert_kick_num: 3
reason: ^7too many warnings: $reason
message: ^1WARNING^7 [^3$warnings^7]: $reason
""")
        self.joe.connects(0)
        self.mike.connects(1)
        self.say_patcher = patch.object(self.console, "say")
        self.say_mock = self.say_patcher.start()
        self.mike_warn_patcher = patch.object(self.mike, "warn", wraps=self.mike.warn)
        self.mike_warn_mock = self.mike_warn_patcher.start()

    def tearDown(self):
        Admin_functional_test.tearDown(self)
        self.say_patcher.stop()
        self.mike_warn_patcher.stop()

    def test_warn(self, sleep_mock):
        # GIVEN
        self.joe.says('!warn mike')
        # THEN
        self.assertEqual(1, self.mike.numWarnings)
        self.assertListEqual([call(60.0, '^7behave yourself', None, self.joe, '')], self.mike_warn_mock.mock_calls)
        self.assertListEqual([call('^1WARNING^7 [^31^7]: Mike^7^7, ^7behave yourself')], self.say_mock.mock_calls)
        self.assertListEqual([], self.joe.message_history)
        self.assertListEqual([], self.mike.message_history)

    @patch('threading.Timer', new_callable=lambda: InstantTimer)
    def test_warn_then_auto_kick(self, instant_timer, sleep_mock):
        # GIVEN
        self.p.warn_delay = 0
        self.assertEqual(0, self.mike.numWarnings)
        # WHEN
        with patch.object(self.mike, 'tempban') as mike_tempban_mock:
            self.joe.says('!warn mike')
            self.joe.says('!warn mike')
            self.joe.says('!warn mike')
        # THEN Mike has 3 active warnings
        self.assertEqual(3, self.mike.numWarnings)
        # THEN appropriate messages were sent
        self.assertListEqual([
            call('^1WARNING^7 [^31^7]: Mike^7^7, ^7behave yourself'),
            call('^1WARNING^7 [^32^7]: Mike^7^7, ^7behave yourself'),
            call('^1WARNING^7 [^33^7]: Mike^7^7, ^7behave yourself'),
            call(u'^1ALERT^7: Mike^7^7 auto-kick from warnings if not cleared [^33^7] ^7behave yourself'),
        ], self.say_mock.mock_calls)
        # THEN Mike was kicked for having too many warnings
        self.assertListEqual([
            call(u'^7too many warnings: ^7behave yourself', u'None', 6, self.joe, False, '')
        ], mike_tempban_mock.mock_calls)
        # THEN No private message was sent
        self.assertListEqual([], self.joe.message_history)
        self.assertListEqual([], self.mike.message_history)


    @patch('threading.Timer', new_callable=lambda: InstantTimer)
    def test_warn_then_auto_kick_duration_divider_60(self, instant_timer, sleep_mock):
        # GIVEN
        self.p.config._sections['warn']['duration_divider'] = '60'
        self.p.warn_delay = 0
        self.assertEqual(0, self.mike.numWarnings)
        # WHEN
        with patch.object(self.mike, 'tempban') as mike_tempban_mock:
            self.joe.says('!warn mike')
            self.joe.says('!warn mike')
            self.joe.says('!warn mike')
        # THEN Mike has 3 active warnings
        self.assertEqual(3, self.mike.numWarnings)
        # THEN appropriate messages were sent
        self.assertListEqual([
            call('^1WARNING^7 [^31^7]: Mike^7^7, ^7behave yourself'),
            call('^1WARNING^7 [^32^7]: Mike^7^7, ^7behave yourself'),
            call('^1WARNING^7 [^33^7]: Mike^7^7, ^7behave yourself'),
            call(u'^1ALERT^7: Mike^7^7 auto-kick from warnings if not cleared [^33^7] ^7behave yourself'),
        ], self.say_mock.mock_calls)
        # THEN Mike was kicked for having too many warnings
        self.assertListEqual([
            call(u'^7too many warnings: ^7behave yourself', u'None', 3, self.joe, False, '')
        ], mike_tempban_mock.mock_calls)
        # THEN No private message was sent
        self.assertListEqual([], self.joe.message_history)
        self.assertListEqual([], self.mike.message_history)

    def test_warn_self(self, sleep_mock):
        # GIVEN
        self.joe.says('!warn joe')
        # THEN
        self.assertEqual(0, self.joe.numWarnings)
        self.assertListEqual(['Joe, you cannot give yourself a warning'], self.joe.message_history)

    def test_warn_denied(self, sleep_mock):
        # GIVEN
        self.mike.says('!warn joe')
        # THEN
        self.assertEqual(0, self.joe.numWarnings)
        self.assertListEqual(["Mike, Joe is a higher level admin, you can't warn him"], self.mike.message_history)

    def test_clear_player(self, sleep_mock):
        # GIVEN
        self.joe.says('!warn mike')
        self.assertEqual(1, self.mike.numWarnings)
        # WHEN
        self.joe.says('!clear mike')
        # THEN
        self.assertListEqual([call('^1WARNING^7 [^31^7]: Mike^7^7, ^7behave yourself'),
                              call('Joe^7 has cleared Mike^7 of all warnings')], self.say_mock.mock_calls)
        self.assertEqual(0, self.mike.numWarnings)

    def test_clear__all_players(self, sleep_mock):
        # GIVEN
        self.joe.says('!warn mike')
        self.assertEqual(1, self.mike.numWarnings)
        # WHEN
        self.joe.says('!clear')
        # THEN
        self.assertListEqual([call('^1WARNING^7 [^31^7]: Mike^7^7, ^7behave yourself'),
                              call("Joe^7 has cleared everyone's warnings and tk points")], self.say_mock.mock_calls)
        self.assertEqual(0, self.mike.numWarnings)


@patch("time.sleep")
class Test_warn_command_abusers(Admin_functional_test):

    def setUp(self):
        Admin_functional_test.setUp(self)
        self.player = FakeClient(self.console, name="ThePlayer", guid="theplayerguid", groupBits=0)
        self.player_warn_patcher = patch.object(self.player, "warn")
        self.player_warn_mock = self.player_warn_patcher.start()

    def tearDown(self):
        Admin_functional_test.tearDown(self)
        self.player_warn_patcher.stop()

    def test_conf_empty(self, sleep_mock):
        # WHEN
        self.init(r"""
[commands]
[warn]
""")
        # THEN
        self.assertFalse(self.p._warn_command_abusers)
        self.assertIsNone(self.p.getWarning("fakecmd"))
        self.assertIsNone(self.p.getWarning("nocmd"))

    def test_warn_reasons(self, sleep_mock):
        # WHEN
        self.init(r"""
[warn_reasons]
fakecmd: 1h, ^7do not use fake commands
nocmd: 1h, ^7do not use commands that you do not have access to, try using !help
""")
        # THEN
        self.assertTupleEqual((60.0, '^7do not use commands that you do not have access to, try using !help'),
                              self.p.getWarning("nocmd"))
        self.assertTupleEqual((60.0, '^7do not use fake commands'), self.p.getWarning("fakecmd"))

    def test_warn_no__no_sufficient_access(self, sleep_mock):
        # WHEN
        self.init(r"""
[commands]
help: 2
[warn]
warn_command_abusers: no
""")
        self.assertFalse(self.p._warn_command_abusers)
        self.player.connects("0")
        # WHEN
        with patch.object(self.p, "info") as info_mock:
            self.player.says("!help")
        # THEN
        self.assertListEqual([call('ThePlayer does not have sufficient rights to use !help. Required level: 2')], info_mock.mock_calls)
        # message section not loaded so this will fallback on the default warn message
        self.assertListEqual(['You do not have sufficient access to use !help'], self.player.message_history)
        self.assertFalse(self.player_warn_mock.called)

    def test_warn_yes__no_sufficient_access(self, sleep_mock):
        # GIVEN
        self.init(r"""
[commands]
help: 2
[warn]
warn_command_abusers: yes
""")
        self.assertTrue(self.p._warn_command_abusers)
        self.player.connects("0")
        # WHEN
        with patch.object(self.p, "info") as info_mock:
            self.player.says("!help")
        # THEN
        self.assertListEqual([call('ThePlayer does not have sufficient rights to use !help. Required level: 2')], info_mock.mock_calls)
        # message section not loaded so this will fallback on the default warn message
        self.assertListEqual(['You do not have sufficient access to use !help'], self.player.message_history)
        self.assertFalse(self.player_warn_mock.called)

    def test_warn_yes__no_sufficient_access_abuser(self, sleep_mock):
        # GIVEN
        self.init(r"""
[commands]
help: 2
[warn]
warn_command_abusers: yes
[warn_reasons]
nocmd: 90s, do not use commands you do not have access to, try using !help
""")
        self.player.connects("0")
        # WHEN
        with patch.object(self.p, "info") as info_mock:
            self.player.says("!help")
            self.player.says("!help")
            self.player.says("!help")
        # THEN
        self.assertListEqual([call('ThePlayer does not have sufficient rights to use !help. Required level: 2'),
                              call('ThePlayer does not have sufficient rights to use !help. Required level: 2')], info_mock.mock_calls)
        # message section not loaded so this will fallback on the default warn message
        self.assertListEqual(['You do not have sufficient access to use !help',
                              'You do not have sufficient access to use !help'], self.player.message_history)
        self.assertListEqual([call(1.5, 'do not use commands you do not have access to, try using !help',
                                   'nocmd', ANY, ANY)], self.player_warn_mock.mock_calls)


    def test_warn_no__unknown_cmd(self, sleep_mock):
        # GIVEN
        self.init(r"""
[commands]
help: 0
[warn]
warn_command_abusers: no
""")
        self.assertFalse(self.p._warn_command_abusers)
        self.player.connects("0")
        # WHEN
        self.player.says("!hzlp")
        # THEN
        self.assertListEqual(['Unrecognized command hzlp. Did you mean !help?'], self.player.message_history)
        self.assertFalse(self.player_warn_mock.called)

    def test_warn_yes__unknown_cmd(self, sleep_mock):
        # GIVEN
        self.init(r"""
[commands]
help: 0
[warn]
warn_command_abusers: yes
""")
        self.assertTrue(self.p._warn_command_abusers)
        self.player.connects("0")
        # WHEN
        self.player.says("!hzlp")
        # THEN
        self.assertListEqual(['Unrecognized command hzlp. Did you mean !help?'], self.player.message_history)
        self.assertFalse(self.player_warn_mock.called)

    def test_warn_yes__unknown_cmd_abuser(self, sleep_mock):
        # GIVEN
        self.init(r"""
[commands]
help: 0
[warn]
warn_command_abusers: yes
[warn_reasons]
fakecmd: 2h, do not use fake commands
""")
        self.assertTrue(self.p._warn_command_abusers)
        self.player.connects("0")
        self.player.setvar(self.p, 'fakeCommand', 2)  # simulate already 2 use of the !help command
        # WHEN
        self.player.says("!hzlp")
        self.player.says("!hzlp")
        self.player.says("!hzlp")
        # THEN
        self.assertListEqual(['Unrecognized command hzlp. Did you mean !help?',
                              'Unrecognized command hzlp. Did you mean !help?',
                              'Unrecognized command hzlp. Did you mean !help?'], self.player.message_history)
        self.assertListEqual([call(120.0, 'do not use fake commands', 'fakecmd', ANY, ANY)],
                             self.player_warn_mock.mock_calls)


@patch("time.sleep")
class Test_command_parsing(Admin_functional_test):

    def setUp(self):
        Admin_functional_test.setUp(self)
        self.init(r"""
[commands]
help: 0
""")
        self.joe.connects("0")

    def test_normal_chat(self, sleep_mock):
        # GIVEN
        self.joe.says("f00")
        self.assertListEqual([], self.joe.message_history)
        # WHEN
        self.joe.says("!help")
        # THEN
        self.assertListEqual(["Available commands: help, iamgod"], self.joe.message_history)

    def test_team_chat(self, sleep_mock):
        # GIVEN
        self.joe.says("f00")
        self.assertListEqual([], self.joe.message_history)
        # WHEN
        self.joe.says2team("!help")
        # THEN
        self.assertListEqual(["Available commands: help, iamgod"], self.joe.message_history)

    def test_squad_chat(self, sleep_mock):
        # GIVEN
        self.joe.says("f00")
        self.assertListEqual([], self.joe.message_history)
        # WHEN
        self.joe.says2squad("!help")
        # THEN
        self.assertListEqual(["Available commands: help, iamgod"], self.joe.message_history)

    def test_private_chat(self, sleep_mock):
        # GIVEN
        self.joe.says("f00")
        self.assertListEqual([], self.joe.message_history)
        # WHEN
        self.joe.says2private("!help")
        # THEN
        self.assertListEqual(["Available commands: help, iamgod"], self.joe.message_history)



class Cmd_kick(Admin_functional_test):

    def setUp(self):
        Admin_functional_test.setUp(self)
        self.init()
        # superadmin joe is connected on slot '0'
        self.joe.connects('0')
        self.kick_patcher = patch.object(self.console, 'kick')
        self.kick_mock = self.kick_patcher.start()

    def tearDown(self):
        Admin_functional_test.tearDown(self)
        self.kick_patcher.stop()

    def test_no_parameter(self):
        # WHEN
        self.joe.says('!kick')
        # THEN
        self.assertListEqual(['Invalid parameters'], self.joe.message_history)
        self.assertListEqual([], self.kick_mock.mock_calls)

    def test_self_kick(self):
        # WHEN
        with patch.object(self.console, "say") as say_mock:
            self.joe.says('!kick joe')
        # THEN
        self.assertListEqual([], self.kick_mock.mock_calls)
        self.assertListEqual([call("^7Joe^7 ^7Can't kick yourself newb!")], say_mock.mock_calls)

    def test_no_reason_when_required(self):
        # GIVEN
        self.joe._groupBits = 16
        # WHEN
        self.joe.says('!kick f00')
        # THEN
        self.assertListEqual(['ERROR: You must supply a reason'], self.joe.message_history)
        self.assertListEqual([], self.kick_mock.mock_calls)

    def test_kick_higher_level_admin(self):
        # GIVEN
        self.mike._groupBits = 16
        self.mike.connects("1")
        # WHEN
        with patch.object(self.console, "say") as say_mock:
            self.mike.says('!kick joe reason1')
        # THEN
        self.assertListEqual([call("^7Joe^7^7 gets 1 point, Mike^7^7 gets none, Joe^7^7 wins, can't kick")], say_mock.mock_calls)
        self.assertListEqual([], self.kick_mock.mock_calls)

    def test_kick_masked_higher_level_admin(self):
        # GIVEN
        self.mike._groupBits = 16
        self.mike.connects("1")
        self.joe.says("!mask reg")
        # WHEN
        self.mike.says('!kick joe reason1')
        # THEN
        self.assertListEqual(["Joe is a masked higher level player, action cancelled"], self.mike.message_history)
        self.assertListEqual([], self.kick_mock.mock_calls)

    def test_existing_player_name(self):
        # GIVEN
        self.mike.connects('1')
        # WHEN
        self.joe.says('!kick mike the reason')
        # THEN
        self.assertListEqual([call(self.mike, 'the reason', self.joe, False)], self.kick_mock.mock_calls)
        self.assertEqual(1, self.console.storage.numPenalties(self.mike, 'Kick'))

    def test_unknown_player_name(self):
        # GIVEN
        self.mike.connects('6')
        # WHEN
        self.joe.says('!kick f00')
        # THEN
        self.assertListEqual(['No players found matching f00'], self.joe.message_history)
        self.assertListEqual([], self.kick_mock.mock_calls)

    def test_kick_by_slot_id(self):
        # GIVEN
        self.mike.connects('6')
        # WHEN
        self.joe.says('!kick 6')
        # THEN
        self.assertListEqual([call(self.mike, '', self.joe, False)], self.kick_mock.mock_calls)
        self.assertEqual(1, self.console.storage.numPenalties(self.mike, 'Kick'))

    def test_kick_by_slot_id_when_no_known_player_is_on_that_slot(self):
        # GIVEN
        self.mike.connects('6')
        # WHEN
        self.joe.says('!kick 4')
        # THEN
        self.assertListEqual([call('4', '', self.joe)], self.kick_mock.mock_calls)

    def test_kick_by_database_id(self):
        # GIVEN
        self.mike.connects('6')
        mike_from_db = self.console.storage.getClient(Client(guid=self.mike.guid))
        self.assertIsNotNone(mike_from_db)
        # WHEN
        self.joe.says('!kick @%s' % mike_from_db.id)
        # THEN
        self.assertListEqual([call(ANY, '', self.joe, False)], self.kick_mock.mock_calls)
        kick_call = self.kick_mock.mock_calls[0]
        kicked_player = kick_call[1][0]
        self.assertIsNotNone(kicked_player)
        self.assertIsNotNone(kicked_player.cid)

    def test_existing_player_by_name_containing_spaces(self):
        # GIVEN
        self.mike.connects('1')
        self.mike.name = "F 0 0"
        # WHEN
        self.joe.says('!kick f00 the reason')
        # THEN
        self.assertListEqual([call(self.mike, 'the reason', self.joe, False)], self.kick_mock.mock_calls)

    def test_existing_player_by_name_containing_spaces_2(self):
        # GIVEN
        self.mike.connects('1')
        self.mike.name = "F 0 0"
        # WHEN
        self.joe.says("!kick 'f 0 0' the reason")
        # THEN
        self.assertListEqual([call(self.mike, 'the reason', self.joe, False)], self.kick_mock.mock_calls)


class Cmd_spam(Admin_functional_test):

    def setUp(self):
        Admin_functional_test.setUp(self)
        self.init()
        self.joe.connects(0)
        self.mike.connects(1)

    def test_no_parameter(self):
        with patch.object(self.console, "say") as say_mock:
            self.joe.says('!spam')
        self.assertListEqual([], say_mock.mock_calls)
        self.assertListEqual(['Invalid parameters'], self.joe.message_history)

    def test_unknown_spammage_keyword(self):
        with patch.object(self.console, "say") as say_mock:
            self.joe.says('!spam f00')
        self.assertListEqual([], say_mock.mock_calls)
        self.assertListEqual(['Could not find spam message f00'], self.joe.message_history)

    def test_nominal_to_all_players(self):
        with patch.object(self.console, "say") as say_mock:
            self.joe.says('!spam rule1')
        self.assertListEqual([call('^3Rule #1: No racism of any kind')], say_mock.mock_calls)
        self.assertListEqual([], self.joe.message_history)

    def test_nominal_to_mike(self):
        with patch.object(self.console, "say") as say_mock:
            self.joe.says('!spam mike rule1')
        self.assertListEqual([], say_mock.mock_calls)
        self.assertListEqual([], self.joe.message_history)
        self.assertListEqual(['Rule #1: No racism of any kind'], self.mike.message_history)

    def test_nominal_to_unknown_player(self):
        with patch.object(self.console, "say") as say_mock:
            self.joe.says('!spam f00 rule1')
        self.assertListEqual([], say_mock.mock_calls)
        self.assertListEqual(["No players found matching f00"], self.joe.message_history)
        self.assertListEqual([], self.mike.message_history)

    def test_nominal_to_all_players_big(self):
        with patch.object(self.console, "saybig") as saybig_mock:
            self.joe.says('&spam rule1')
        self.assertListEqual([call('^3Rule #1: No racism of any kind')], saybig_mock.mock_calls)
        self.assertListEqual([], self.joe.message_history)
