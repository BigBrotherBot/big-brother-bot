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
from tests import B3TestCase
import unittest

import b3
from b3.plugins.admin import AdminPlugin, Command
from b3.config import XmlConfigParser
from b3.fake import fakeConsole
from b3.clients import Client

 
class Test_parseUserCmd(B3TestCase):

    def setUp(self):
        B3TestCase.setUp(self)
        self.conf = XmlConfigParser()
        self.conf.setXml("""
            <configuration plugin="admin">
            </configuration>
        """)
        self.p = AdminPlugin(b3.console, self.conf)


    @unittest.expectedFailure
    def test_clientinfo_bad_arg(self):
        self.assertIsNone(self.p.parseUserCmd(None))

    def test_clientinfo_empty_arg(self):
        self.assertIsNone(self.p.parseUserCmd(''))

    def test_clientinfo_only_1_arg(self):
        self.assertEqual(('someone', None), self.p.parseUserCmd('someone'))
        # see https://github.com/xlr8or/big-brother-bot/issues/54
        self.assertIsNone(self.p.parseUserCmd('someone', req=True))

    def test_clientinfo_2_args(self):
        self.assertEqual(('someone', 'param1'), self.p.parseUserCmd('someone param1'))
        self.assertEqual(('someone', 'param1'), self.p.parseUserCmd('someone param1', req=True))

    def test_clientinfo_3_args(self):
        self.assertEqual(('someone', 'param1 param2'), self.p.parseUserCmd('someone param1 param2'))
        self.assertEqual(('someone', 'param1 param2'), self.p.parseUserCmd('someone param1 param2', req=True))

    def test_clientinfo_int(self):
        self.assertEqual(('45', None), self.p.parseUserCmd('45'))
        self.assertEqual(('45', None), self.p.parseUserCmd("'45'"))
        self.assertEqual(('45', 'some param'), self.p.parseUserCmd("'45' some param"))


class Test_getGroupLevel(B3TestCase):

    def setUp(self):
        B3TestCase.setUp(self)
        self.conf = XmlConfigParser()
        self.conf.setXml("""
                <configuration plugin="admin">
                </configuration>
            """)
        self.p = AdminPlugin(fakeConsole, self.conf)

    def test_nominal(self):
        for test_data, expected in {
            'NONE': 'none',
            '0': 0,
            '1': 1,
            'guest': 0,
            'user': 1,
            'reg': 2,
            'mod': 20,
            'admin': 40,
            'fulladmin': 60,
            'senioradmin': 80,
            'superadmin': 100,
            '1-20': '1-20',
            '40-20': '40-20',
            'user-admin': '1-40',
        }.items():
            result = self.p.getGroupLevel(test_data)
            if expected != result:
                self.fail("%r, expecting %r but got %r" % (test_data, expected, result))

    def test_failures(self):
        self.p.error = Mock()
        for test_data in ('foo', 'mod-foo', 'foo-mod'):
            self.assertFalse(self.p.getGroupLevel(test_data))
            assert self.p.error.called



class Test_misc_cmd(B3TestCase):

    def setUp(self):
        B3TestCase.setUp(self)
        self.conf = XmlConfigParser()
        self.conf.setXml("""
            <configuration plugin="admin">
            </configuration>
        """)
        self.p = AdminPlugin(b3.console, self.conf)


    def test_die(self):
        self.p.cmd_die(None, None, Mock())
        assert b3.console.die.called

    def test_restart(self):
        self.p.cmd_restart(None, None, Mock())
        assert b3.console.restart.called

    def test_reconfig(self):
        self.p.cmd_reconfig(None, None, Mock())
        assert b3.console.reloadConfigs.called

    def test_map(self):
        mock_client = Mock(spec=Client, name="client")

        # no data
        self.p.cmd_map(data=None, client=mock_client, cmd=Mock(spec=Command))
        mock_client.message.assert_called_once_with('^7You must supply a map to change to.')
        assert not b3.console.changeMap.called

        # correct data
        mock_client.reset_mock()
        b3.console.reset_mock()
        b3.console.changeMap = Mock(return_value='foo')
        self.p.cmd_map(data='bar', client=mock_client, cmd=Mock(spec=Command))
        b3.console.changeMap.assert_called_once_with('bar')
        assert not mock_client.message.called

        # incorrect data
        mock_client.reset_mock()
        b3.console.reset_mock()
        b3.console.changeMap = Mock(return_value=['foo1', 'foo2', 'foo3'])
        self.p.cmd_map(data='bar', client=mock_client, cmd=Mock(spec=Command))
        b3.console.changeMap.assert_called_once_with('bar')
        assert mock_client.message.called

    def test_maprotate(self):
        self.p.cmd_maprotate(None, None, Mock(spec=Command))
        assert b3.console.rotateMap.called

    def test_b3(self):
        self.p.config = Mock(name="config")
        self.p.config.getint = Mock(return_value=10)

        mock_client = Mock(spec=Client, name="client")
        mock_command = Mock(spec=Command, name='cmd')

        mock_client.maxLevel = 0
        self.p.cmd_b3(data='', client=mock_client, cmd=mock_command)
        assert mock_command.sayLoudOrPM.called

        mock_client.maxLevel = 20
        mock_client.reset_mock()
        b3.console.reset_mock()
        self.p.cmd_b3(data='', client=mock_client, cmd=mock_command)
        assert mock_command.sayLoudOrPM.called

        for param in ('poke', 'expose', 'stare', 'stab', 'triangulate', 'bite', 'fuck', 'slap', 'fight', 'feed',
                      'throw', 'furniture', 'indeed', 'flog', 'sexor', 'hate', 'smoke', 'maul', 'procreate',
                      'shoot'):
            mock_client.reset_mock()
            b3.console.reset_mock()
            self.p.cmd_b3(data=param, client=mock_client, cmd=mock_command)
            if not b3.console.say.called:
                self.fail("b3.console.say was not called for %r" % param)






if __name__ == '__main__':
    unittest.main()