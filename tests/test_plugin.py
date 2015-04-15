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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
#
import logging
import os

from mock import patch
from mock import call
from mock import ANY
from ConfigParser import NoOptionError
from mockito import when
from b3.config import CfgConfigParser
from b3.plugin import Plugin
from b3.events import Event
from tests import B3TestCase
from tests.fakeplugins_tmp import __file__ as external_plugins__file__

external_plugins_dir = os.path.dirname(external_plugins__file__)
testplugin_config_file = os.path.join(external_plugins_dir, "testplugin/conf/plugin_testplugin.ini")


class MyPlugin(Plugin):

    stub_not_callable = 0

    def __init__(self, console, config=None):
        Plugin.__init__(self, console, config=config)
        self._messages = {}
        self.stub_method_call_count = 0
        self.stub_method2_call_count = 0
        self.onEvent_call_count = 0

    def stub_method(self, event):
        self.stub_method_call_count += 1
        logging.debug("stub_method called")

    def stub_method2(self, event):
        self.stub_method2_call_count += 1
        logging.debug("stub_method2 called")

    def onEvent(self, event):
        self.onEvent_call_count += 1
        logging.debug("onEvent called")


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
        self.assertListEqual([call('failed to format message %r (%r) with parameters %r: %s', 'f00', 'bar -%s- bar', (),
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
        self.assertListEqual([call('failed to format message %r (%r) with parameters %r: %s', 'f00', 'bar -%s- bar',
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
        self.assertListEqual([call('failed to format message %r (%r) with parameters %r: missing value for %s', 'f00',
                                   'bar -%(param1)s- bar', ({'param_foo': 'foo'},), ANY)], error_mock.mock_calls)


class Test_Plugin_registerEvent(B3TestCase):

    def setUp(self):
        B3TestCase.setUp(self)
        self.conf = CfgConfigParser()

    def test_register_event_no_hook(self):
        # GIVEN
        k = self.console.getEventID('EVT_CLIENT_SAY')
        p = MyPlugin(self.console, self.conf)
        p.registerEvent(k)
        # THEN
        self.assertIn(k, self.console._handlers.keys())
        self.assertIn(p, self.console._handlers[k])
        self.assertIn(k, p.eventmap.keys())
        # WHEN
        self.console.queueEvent(Event(k, None))
        # THEN
        self.assertEqual(1, p.onEvent_call_count)
        self.assertEqual(0, p.stub_method_call_count)
        self.assertEqual(0, p.stub_method2_call_count)

    def test_register_event_with_not_valid_hook(self):
        # GIVEN
        k = self.console.getEventID('EVT_CLIENT_SAY')
        p = MyPlugin(self.console, self.conf)
        p.registerEvent(k, p.stub_not_callable)
        # THEN
        self.assertIn(k, self.console._handlers.keys())
        self.assertIn(p, self.console._handlers[k])
        self.assertNotIn(k, p.eventmap.keys())
        # WHEN
        self.console.queueEvent(Event(k, None))
        # THEN
        self.assertEqual(0, p.onEvent_call_count)
        self.assertEqual(0, p.stub_method_call_count)
        self.assertEqual(0, p.stub_method2_call_count)

    def test_register_event_with_valid_hook(self):
        # GIVEN
        k = self.console.getEventID('EVT_CLIENT_SAY')
        p = MyPlugin(self.console, self.conf)
        p.registerEvent(k, p.stub_method)
        # THEN
        self.assertIn(k, self.console._handlers.keys())
        self.assertIn(p, self.console._handlers[k])
        self.assertIn(k, p.eventmap.keys())
        self.assertIn(p.stub_method, p.eventmap[k])
        # WHEN
        self.console.queueEvent(Event(k, None))
        # THEN
        self.assertEqual(0, p.onEvent_call_count)
        self.assertEqual(1, p.stub_method_call_count)
        self.assertEqual(0, p.stub_method2_call_count)

    def test_register_event_with_sequential_valid_hooks(self):
        # GIVEN
        k = self.console.getEventID('EVT_CLIENT_SAY')
        p = MyPlugin(self.console, self.conf)
        p.registerEvent(k, p.stub_method)
        p.registerEvent(k, p.stub_method2)
        # THEN
        self.assertIn(k, self.console._handlers.keys())
        self.assertIn(p, self.console._handlers[k])
        self.assertIn(k, p.eventmap.keys())
        self.assertIn(p.stub_method, p.eventmap[k])
        self.assertIn(p.stub_method2, p.eventmap[k])
        # WHEN
        self.console.queueEvent(Event(k, None))
        # THEN
        self.assertEqual(0, p.onEvent_call_count)
        self.assertEqual(1, p.stub_method_call_count)
        self.assertEqual(1, p.stub_method2_call_count)

    def test_register_event_with_sequential_valid_and_invalid_hooks(self):
        # GIVEN
        k = self.console.getEventID('EVT_CLIENT_SAY')
        p = MyPlugin(self.console, self.conf)
        p.registerEvent(k, p.stub_method)
        p.registerEvent(k, p.stub_not_callable)
        # THEN
        self.assertIn(k, self.console._handlers.keys())
        self.assertIn(p, self.console._handlers[k])
        self.assertIn(k, p.eventmap.keys())
        self.assertIn(p.stub_method, p.eventmap[k])
        self.assertNotIn(p.stub_method2, p.eventmap[k])
        # WHEN
        self.console.queueEvent(Event(k, None))
        # THEN
        self.assertEqual(0, p.onEvent_call_count)
        self.assertEqual(1, p.stub_method_call_count)
        self.assertEqual(0, p.stub_method2_call_count)

    def test_register_event_with_list_of_valid_hooks(self):
        # GIVEN
        k = self.console.getEventID('EVT_CLIENT_SAY')
        p = MyPlugin(self.console, self.conf)
        p.registerEvent(k, p.stub_method, p.stub_method2)
        # THEN
        self.assertIn(k, self.console._handlers.keys())
        self.assertIn(p, self.console._handlers[k])
        self.assertIn(k, p.eventmap.keys())
        self.assertIn(p.stub_method, p.eventmap[k])
        self.assertIn(p.stub_method2, p.eventmap[k])
        # WHEN
        self.console.queueEvent(Event(k, None))
        # THEN
        self.assertEqual(0, p.onEvent_call_count)
        self.assertEqual(1, p.stub_method_call_count)
        self.assertEqual(1, p.stub_method2_call_count)

    def test_register_event_with_list_of_valid_and_invalid_hooks(self):
        # GIVEN
        k = self.console.getEventID('EVT_CLIENT_SAY')
        p = MyPlugin(self.console, self.conf)
        p.registerEvent(k, p.stub_method, p.stub_not_callable)
        # THEN
        self.assertIn(k, self.console._handlers.keys())
        self.assertIn(p, self.console._handlers[k])
        self.assertIn(k, p.eventmap.keys())
        self.assertIn(p.stub_method, p.eventmap[k])
        self.assertNotIn(p.stub_method2, p.eventmap[k])
        # WHEN
        self.console.queueEvent(Event(k, None))
        # THEN
        self.assertEqual(0, p.onEvent_call_count)
        self.assertEqual(1, p.stub_method_call_count)
        self.assertEqual(0, p.stub_method2_call_count)

    def test_parse_registered_event_with_multiple_valid_hooks(self):
        # GIVEN
        k = self.console.getEventID('EVT_CLIENT_SAY')
        p = MyPlugin(self.console, self.conf)
        p.registerEvent(k, p.stub_method)   # register the first hook
        p.registerEvent(k, p.stub_method2)  # register the second hook
        # WHEN
        self.console.queueEvent(Event(k, None))
        # THEN
        self.assertEqual(0, p.onEvent_call_count)
        self.assertEqual(1, p.stub_method_call_count)
        self.assertEqual(1, p.stub_method2_call_count)

    def test_parse_registered_event_with_multiple_valid_hooks_and_old_fashion_way(self):
        # GIVEN
        k = self.console.getEventID('EVT_CLIENT_SAY')
        p = MyPlugin(self.console, self.conf)
        p.registerEvent(k)   # old fashion
        p.registerEvent(k, p.stub_method)
        # WHEN
        self.console.queueEvent(Event(k, None))
        # THEN
        self.assertEqual(1, p.onEvent_call_count)
        self.assertEqual(1, p.stub_method_call_count)
        self.assertEqual(0, p.stub_method2_call_count)

    def test_parse_registered_event_with_no_hook_registered(self):
        # GIVEN
        k = self.console.getEventID('EVT_CLIENT_SAY')
        p = MyPlugin(self.console, self.conf)
        # WHEN
        self.console.queueEvent(Event(k, None))
        # THEN
        self.assertEqual(0, p.onEvent_call_count)
        self.assertEqual(0, p.stub_method_call_count)
        self.assertEqual(0, p.stub_method2_call_count)

    def test_register_event_same_hook_registered_multiple_times(self):
        # GIVEN
        k = self.console.getEventID('EVT_CLIENT_SAY')
        p = MyPlugin(self.console, self.conf)
        p.registerEvent(k, p.stub_method)
        p.registerEvent(k, p.stub_method)
        p.registerEvent(k, p.stub_method)
        # WHEN
        self.console.queueEvent(Event(k, None))
        # THEN
        self.assertEqual(0, p.onEvent_call_count)
        self.assertEqual(1, p.stub_method_call_count)
        self.assertEqual(0, p.stub_method2_call_count)

    def test_register_event_by_name_with_valid_hook(self):
        # GIVEN
        evt_name = 'EVT_CLIENT_SAY'
        k = self.console.getEventID(evt_name)
        p = MyPlugin(self.console, self.conf)
        p.registerEvent(evt_name, p.stub_method)
        # THEN
        self.assertIn(k, self.console._handlers.keys())
        self.assertIn(p, self.console._handlers[k])
        self.assertIn(k, p.eventmap.keys())
        self.assertIn(p.stub_method, p.eventmap[k])
        # WHEN
        self.console.queueEvent(Event(k, None))
        # THEN
        self.assertEqual(0, p.onEvent_call_count)
        self.assertEqual(1, p.stub_method_call_count)
        self.assertEqual(0, p.stub_method2_call_count)


class Test_Plugin_requiresParser(B3TestCase):

    def setUp(self):
        B3TestCase.setUp(self)
        when(self.console.config).get_external_plugins_dir().thenReturn(external_plugins_dir)
        self.conf = CfgConfigParser(testplugin_config_file)

        self.plugin_list = [
            {'name': 'admin', 'conf': '@b3/conf/plugin_admin.ini', 'path': None, 'disabled': False},
        ]
        when(self.console.config).get_plugins().thenReturn(self.plugin_list)

    def test_nominal(self):
        # GIVEN
        self.plugin_list.append(
            {'name': 'testplugin1', 'conf': None, 'path': external_plugins_dir, 'disabled': False}
        )
        # WHEN
        with patch.object(self.console, 'error') as error_mock:
            self.console.loadPlugins()
        # THEN
        self.assertListEqual([], error_mock.mock_calls)

    def test_wrong_game(self):
        # GIVEN
        self.plugin_list.append(
            {'name': 'testplugin2', 'conf': None, 'path': external_plugins_dir, 'disabled': False}
        )
        # WHEN
        with patch.object(self.console, 'error') as error_mock:
            self.console.loadPlugins()
        # THEN
        self.assertListEqual([call('Could not load plugin testplugin2', exc_info=ANY)], error_mock.mock_calls)
