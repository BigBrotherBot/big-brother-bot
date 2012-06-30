#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2011 Courgette
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

from mock import Mock
import unittest2 as unittest

import os

from b3 import __file__ as b3_module__file__, TEAM_BLUE, TEAM_RED

from tests import B3TestCase
from b3.fake import FakeClient
from b3.config import XmlConfigParser
from b3.plugins.admin import AdminPlugin

ADMIN_CONFIG_FILE = os.path.join(os.path.dirname(b3_module__file__), "conf/plugin_admin.xml")

@unittest.skipUnless(os.path.isfile(ADMIN_CONFIG_FILE), "%s is not a file" % ADMIN_CONFIG_FILE)
class Admin_functional_test(B3TestCase):

    def setUp(self):
        B3TestCase.setUp(self)
        self.conf = XmlConfigParser()
        self.conf.load(ADMIN_CONFIG_FILE)
        self.p = AdminPlugin(self.console, self.conf)
        self.p.onLoadConfig()
        self.p.onStartup()

        self.joe = FakeClient(self.console, name="Joe", exactName="Joe", guid="joeguid", groupBits=128, team=TEAM_RED)
        self.mike = FakeClient(self.console, name="Mike", exactName="Mike", guid="mikeguid", groupBits=1, team=TEAM_BLUE)


class Cmd_tempban(Admin_functional_test):
    def test_no_duration(self):
        self.joe.message = Mock()
        self.joe.connects(0)
        self.mike.connects(1)

        self.joe.says('!tempban mike')
        self.joe.message.assert_called_with('^7Invalid parameters')


    def test_bad_duration(self):
        self.joe.message = Mock()
        self.joe.connects(0)
        self.mike.connects(1)
        self.mike.tempban = Mock()

        self.joe.says('!tempban mike 5hour')
        self.joe.message.assert_called_with('^7Invalid parameters')
        assert not self.mike.tempban.called


    def test_non_existing_player(self):
        self.joe.message = Mock()
        self.joe.connects(0)
        self.mike.connects(1)

        self.joe.says('!tempban foo 5h')
        self.joe.message.assert_called_with('^7No players found matching foo')


    def test_no_reason(self):
        self.joe.message = Mock()
        self.joe.connects(0)
        self.mike.connects(1)
        self.mike.tempban = Mock()

        self.joe.says('!tempban mike 5h')
        self.mike.tempban.assert_called_with('', None, 5*60, self.joe)


class Cmd_help(Admin_functional_test):
    def test_non_existing_cmd(self):
        self.joe.message = Mock()
        self.joe.connects(0)
        self.joe.says('!help fo0')
        self.joe.message.assert_called_with('^7Command not found fo0')

    def test_existing_cmd(self):
        self.joe.message = Mock()
        self.joe.connects(0)
        self.joe.says('!help help')
        self.joe.message.assert_called_with('^2!help ^7%s' % self.p.cmd_help.__doc__.strip())

    def test_no_arg(self):
        self.joe.message = Mock()
        self.joe.connects(0)
        self.joe.says('!help')
        self.joe.message.assert_called_with('^7Available commands: admins, admintest, aliases, b3, ban, banall, baninfo,'
                                            ' clear, clientinfo, die, disable, enable, find, help, iamgod, kick, kickall'
                                            ', leveltest, list, lookup, makereg, map, maprotate, maps, mask, nextmap, no'
                                            'tice, pause, permban, poke, putgroup, rebuild, reconfig, regtest, restart, '
                                            'rules, runas, say, scream, seen, spam, spams, spank, spankall, status, temp'
                                            'ban, time, unban, ungroup, unmask, warn, warnclear, warninfo, warnremove, w'
                                            'arns, warntest')
        self.mike.message = Mock()
        self.mike.connects(0)
        self.mike.says('!help')
        self.mike.message.assert_called_with('^7Available commands: help, iamgod, regtest, rules, time')

    def test_joker(self):
        self.joe.message = Mock()
        self.joe.connects(0)
        self.joe.says('!help *ban')
        self.joe.message.assert_called_with('^7Available commands: ban, banall, baninfo, permban, tempban, unban')


if __name__ == '__main__':
    unittest.main()