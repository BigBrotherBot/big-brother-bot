#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2013 Courgette
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
from mock import patch, call, ANY
from ConfigParser import NoOptionError
from b3.config import CfgConfigParser
from b3.plugin import Plugin
from tests import B3TestCase


class MyPlugin(Plugin):
    def __init__(self, console, config=None):
        Plugin.__init__(self, console, config=config)
        self._messages = {}


class Test_Plugin_getMessage(B3TestCase):
    
    def setUp(self):
        B3TestCase.setUp(self)
        self.conf = CfgConfigParser()

    def test_no_default_no_message(self):
        # GIVEN
        self.conf.loadFromString("""
[messages]

        """)
        p = MyPlugin(self.console, self.conf)
        # THEN
        with patch.object(p, "warning") as warning_mock:
            self.assertRaises(NoOptionError, p.getMessage, 'f00')
        self.assertListEqual([call("config file is missing 'f00' in section 'messages'")], warning_mock.mock_calls)

    def test_no_message(self):
        # GIVEN
        self.conf.loadFromString("""
[messages]

        """)
        p = MyPlugin(self.console, self.conf)
        p._default_messages = {
            'f00': "bar"
        }
        # WHEN
        with patch.object(p, "warning") as warning_mock:
            msg = p.getMessage('f00')
        # THEN
        self.assertEqual('bar', msg)
        self.assertListEqual([call("config file is missing 'f00' in section 'messages'")], warning_mock.mock_calls)
        self.assertIn('f00', p._messages)
        self.assertEqual('bar', p._messages['f00'])

    def test_nominal(self):
        # GIVEN
        self.conf.loadFromString("""
[messages]
f00: bar
        """)
        p = MyPlugin(self.console, self.conf)
        # WHEN
        with patch.object(p, "warning") as warning_mock:
            msg = p.getMessage('f00')
        # THEN
        self.assertEqual('bar', msg)
        self.assertListEqual([], warning_mock.mock_calls)
        self.assertIn('f00', p._messages)

    def test_with_parameter__nominal(self):
        # GIVEN
        self.conf.loadFromString("""
[messages]
f00: bar -%s- bar
        """)
        p = MyPlugin(self.console, self.conf)
        # WHEN
        msg = p.getMessage('f00', 'blah')
        # THEN
        self.assertEqual('bar -blah- bar', msg)

    def test_with_parameter__too_few(self):
        # GIVEN
        self.conf.loadFromString("""
[messages]
f00: bar -%s- bar
        """)
        p = MyPlugin(self.console, self.conf)
        # WHEN
        with patch.object(p, "error") as error_mock:
            self.assertRaises(TypeError, p.getMessage, 'f00')
        # THEN
        self.assertListEqual([call('failed to format message %r (%r) with parameters %r. %s', 'f00', 'bar -%s- bar', (),
                                   ANY)], error_mock.mock_calls)

    def test_with_parameter__too_many(self):
        # GIVEN
        self.conf.loadFromString("""
[messages]
f00: bar -%s- bar
        """)
        p = MyPlugin(self.console, self.conf)
        # WHEN
        with patch.object(p, "error") as error_mock:
            self.assertRaises(TypeError, p.getMessage, 'f00', 'param1', 'param2')
        # THEN
        self.assertListEqual([call('failed to format message %r (%r) with parameters %r. %s', 'f00', 'bar -%s- bar',
                                   ('param1', 'param2'), ANY)], error_mock.mock_calls)

    def test_with_named_parameter__nominal(self):
        # GIVEN
        self.conf.loadFromString("""
[messages]
f00: bar -%(param1)s- bar
        """)
        p = MyPlugin(self.console, self.conf)
        # WHEN
        msg = p.getMessage('f00', {'param1': 'blah'})
        # THEN
        self.assertEqual('bar -blah- bar', msg)

    def test_with_named_parameter__too_few(self):
        # GIVEN
        self.conf.loadFromString("""
[messages]
f00: bar -%(param1)s- bar
        """)
        p = MyPlugin(self.console, self.conf)
        # WHEN
        with patch.object(p, "error") as error_mock:
            self.assertRaises(KeyError, p.getMessage, 'f00', {'param_foo': 'foo'})
        # THEN
        self.assertListEqual([call('failed to format message %r (%r) with parameters %r. Missing value for %s', 'f00',
                                   'bar -%(param1)s- bar', ({'param_foo': 'foo'},), ANY)],
                             error_mock.mock_calls)
