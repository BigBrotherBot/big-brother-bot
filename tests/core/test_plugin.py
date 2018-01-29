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


import b3
import imp
import logging
import os
from ConfigParser import NoOptionError

from mock import patch
from mock import call
from mock import ANY
from mockito import when

from b3.config import CfgConfigParser
from b3.plugin import Plugin
from b3.events import Event
from tests import B3TestCase
from tests.plugins.fakeplugins import __file__ as external_plugins__file__
from textwrap import dedent

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

        fp, pathname, description = imp.find_module('testplugin1', [os.path.join(b3.getB3Path(True), '..', 'tests', 'plugins', 'fakeplugins')])
        pluginModule1 = imp.load_module('testplugin1', fp, pathname, description)
        if fp:
            fp.close()

        fp, pathname, description = imp.find_module('testplugin2', [os.path.join(b3.getB3Path(True), '..', 'tests', 'plugins', 'fakeplugins')])
        pluginModule2 = imp.load_module('testplugin2', fp, pathname, description)
        if fp:
            fp.close()

        fp, pathname, description = imp.find_module('admin', [os.path.join(b3.getB3Path(True), 'plugins')])
        adminModule = imp.load_module('admin', fp, pathname, description)
        if fp:
            fp.close()

        when(self.console.config).get_plugins().thenReturn(self.plugin_list)
        when(self.console).pluginImport('admin', ANY).thenReturn(adminModule)
        when(self.console).pluginImport('testplugin1', ANY).thenReturn(pluginModule1)
        when(self.console).pluginImport('testplugin2', ANY).thenReturn(pluginModule2)

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


class Test_Plugin_getSetting(B3TestCase):

    def setUp(self):
        B3TestCase.setUp(self)
        self.conf = CfgConfigParser()
        self.conf.loadFromString(dedent("""
        [section_foo]
        option_str: string value with spaces
        option_int: 7
        option_bool1: false
        option_bool2: true
        option_bool3: 0
        option_bool4: 1
        option_bool5: 2
        option_float: 0.97
        option_level1: senioradmin
        option_level2: guest
        option_level3: badkeyword
        option_duration1: 300
        option_duration2: 3h
        option_path: @b3/conf/b3.distribution.ini
        """))

        self.p = MyPlugin(self.console, self.conf)

    def test_value_retrieval_valid(self):
        self.assertEqual(self.p.getSetting('section_foo', 'option_str', b3.STRING), 'string value with spaces')
        self.assertEqual(self.p.getSetting('section_foo', 'option_int', b3.STRING), '7')
        self.assertEqual(self.p.getSetting('section_foo', 'option_int', b3.INTEGER), 7)
        self.assertEqual(self.p.getSetting('section_foo', 'option_bool1', b3.BOOLEAN), False)
        self.assertEqual(self.p.getSetting('section_foo', 'option_bool2', b3.BOOLEAN), True)
        self.assertEqual(self.p.getSetting('section_foo', 'option_bool3', b3.BOOLEAN), False)
        self.assertEqual(self.p.getSetting('section_foo', 'option_bool4', b3.BOOLEAN), True)
        self.assertEqual(self.p.getSetting('section_foo', 'option_float', b3.STRING), '0.97')
        self.assertEqual(self.p.getSetting('section_foo', 'option_float', b3.FLOAT), 0.97)
        self.assertEqual(self.p.getSetting('section_foo', 'option_level1', b3.LEVEL), 80)
        self.assertEqual(self.p.getSetting('section_foo', 'option_level2', b3.LEVEL), 0)
        self.assertEqual(self.p.getSetting('section_foo', 'option_duration1', b3.DURATION), 300)
        self.assertEqual(self.p.getSetting('section_foo', 'option_duration2', b3.DURATION), 180)
        self.assertEqual(self.p.getSetting('section_foo', 'option_path', b3.PATH), b3.getAbsolutePath('@b3/conf/b3.distribution.ini', decode=True))

    def test_value_retrieval_invalid(self):
        self.assertEqual(self.p.getSetting('section_foo', 'option_path', b3.INTEGER, 40), 40)
        self.assertEqual(self.p.getSetting('section_foo', 'option_bool5', b3.BOOLEAN, True), True)
        self.assertEqual(self.p.getSetting('section_foo', 'option_level3', b3.LEVEL, 100), 100)
        self.assertEqual(self.p.getSetting('section_foo', 'my_bad_option', b3.STRING, 'my string'), 'my string')
        self.assertEqual(self.p.getSetting('section_foo', 'option_int', 90, 40), 40)
        self.assertEqual(self.p.getSetting('my_bad_section', 'my_bad_option', b3.STRING, 'my string'), 'my string')

    def test_value_retrieval_invalid_no_default(self):
        self.assertEqual(self.p.getSetting('section_foo', 'option_path', b3.INTEGER), None)
        self.assertEqual(self.p.getSetting('section_foo', 'option_bool5', b3.BOOLEAN), None)
        self.assertEqual(self.p.getSetting('section_foo', 'option_level3', b3.LEVEL), None)
        self.assertEqual(self.p.getSetting('section_foo', 'my_bad_option', b3.STRING), None)
        self.assertEqual(self.p.getSetting('section_foo', 'option_int', 90), None)
        self.assertEqual(self.p.getSetting('my_bad_section', 'my_bad_option', b3.STRING), None)

    def test_with_no_config(self):
        self.p.config = None
        self.assertEqual(self.p.getSetting('section_foo', 'option_str', b3.STRING, 'string value with spaces'), 'string value with spaces')
        self.assertEqual(self.p.getSetting('section_foo', 'option_int', b3.STRING, '7'), '7')
        self.assertEqual(self.p.getSetting('section_foo', 'option_int', b3.INTEGER, 7), 7)
        self.assertEqual(self.p.getSetting('section_foo', 'option_bool1', b3.BOOLEAN, False), False)
        self.assertEqual(self.p.getSetting('section_foo', 'option_bool2', b3.BOOLEAN, True), True)
        self.assertEqual(self.p.getSetting('section_foo', 'option_bool3', b3.BOOLEAN, False), False)
        self.assertEqual(self.p.getSetting('section_foo', 'option_bool4', b3.BOOLEAN, True), True)

class Test_Plugin_requiresStorage(B3TestCase):

    def setUp(self):
        B3TestCase.setUp(self)
        when(self.console.config).get_external_plugins_dir().thenReturn(external_plugins_dir)
        self.conf = CfgConfigParser(testplugin_config_file)

        self.plugin_list = [
            {'name': 'admin', 'conf': '@b3/conf/plugin_admin.ini', 'path': None, 'disabled': False},
        ]

        fp, pathname, description = imp.find_module('testplugin1', [os.path.join(b3.getB3Path(True), '..', 'tests', 'plugins', 'fakeplugins')])
        pluginModule1 = imp.load_module('testplugin1', fp, pathname, description)
        if fp:
            fp.close()

        fp, pathname, description = imp.find_module('testplugin3', [os.path.join(b3.getB3Path(True), '..', 'tests', 'plugins', 'fakeplugins')])
        pluginModule3 = imp.load_module('testplugin3', fp, pathname, description)
        if fp:
            fp.close()

        fp, pathname, description = imp.find_module('admin', [os.path.join(b3.getB3Path(True), 'plugins')])
        adminModule = imp.load_module('admin', fp, pathname, description)
        if fp:
            fp.close()

        when(self.console.config).get_plugins().thenReturn(self.plugin_list)
        when(self.console).pluginImport('admin', ANY).thenReturn(adminModule)
        when(self.console).pluginImport('testplugin1', ANY).thenReturn(pluginModule1)
        when(self.console).pluginImport('testplugin3', ANY).thenReturn(pluginModule3)

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

    def test_correct_storage(self):
        # GIVEN
        self.console.storage.protocol = 'postgresql'
        self.plugin_list.append(
            {'name': 'testplugin3', 'conf': None, 'path': external_plugins_dir, 'disabled': False}
        )
        # WHEN
        with patch.object(self.console, 'error') as error_mock:
            self.console.loadPlugins()
        # THEN
        self.assertListEqual([], error_mock.mock_calls)

    def test_wrong_storage(self):
        # GIVEN
        self.console.storage.protocol = 'mysql'
        self.plugin_list.append(
            {'name': 'testplugin3', 'conf': None, 'path': external_plugins_dir, 'disabled': False}
        )
        # WHEN
        with patch.object(self.console, 'error') as error_mock:
            self.console.loadPlugins()
        # THEN
        self.assertListEqual([call('Could not load plugin testplugin3', exc_info=ANY)], error_mock.mock_calls)
