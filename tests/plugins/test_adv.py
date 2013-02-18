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
import StringIO
import logging
import os
from mock import patch, call, Mock
from mockito import when, any as mockito_any, unstub
from b3.fake import FakeClient
from b3.lib import feedparser
from b3.plugins.admin import AdminPlugin
from tests import B3TestCase
import unittest2 as unittest

from b3.plugins.adv import AdvPlugin, MessageLoop
from b3.config import XmlConfigParser

from b3 import __file__ as b3_module__file__
ADMIN_CONFIG_FILE = os.path.normpath(os.path.join(os.path.dirname(b3_module__file__), "conf/plugin_admin.xml"))
ADMIN_CONFIG = None

default_plugin_file = os.path.normpath(os.path.join(os.path.dirname(__file__), "../../b3/conf/plugin_adv.xml"))
default_plugin_content = None

timer_patcher = None
feedparser_patcher = None


def setUpModule():
    global default_plugin_content, default_plugin_file, ADMIN_CONFIG, ADMIN_CONFIG_FILE, timer_patcher, feedparser_patcher
    if os.path.exists(default_plugin_file):
        with open(default_plugin_file, 'r') as f:
            default_plugin_content = f.read()

    ADMIN_CONFIG = XmlConfigParser()
    ADMIN_CONFIG.load(ADMIN_CONFIG_FILE)

    timer_patcher = patch('threading.Timer')
    timer_patcher.start()

    feedparser_patcher = patch.object(feedparser, 'parse')
    feedparser_patcher.start()


def tearDownModule():
    global timer_patcher, feedparser_patcher
    timer_patcher.stop()
    feedparser_patcher.stop()


class AdvTestCase(B3TestCase):
    """ Ease test cases that need an working B3 console and need to control the ADV plugin config """

    def setUp(self):
        self.log = logging.getLogger('output')
        self.log.propagate = False

        B3TestCase.setUp(self)

        self.adminPlugin = AdminPlugin(self.console, ADMIN_CONFIG)
        when(self.console).getPlugin("admin").thenReturn(self.adminPlugin)
        self.adminPlugin.onLoadConfig()
        self.adminPlugin.onStartup()

        self.console.startup()
        self.log.propagate = True

    def tearDown(self):
        B3TestCase.tearDown(self)
        unstub()

    def init_plugin(self, config_content=None):
        conf = None
        if config_content:
            conf = XmlConfigParser()
            conf.setXml(config_content)
        elif default_plugin_content:
            conf = XmlConfigParser()
            conf.setXml(default_plugin_content)
        else:
            unittest.skip("cannot get default plugin config file at %s" % default_plugin_file)

        self.p = AdvPlugin(self.console, conf)
        self.p.save = Mock()
        self.conf = self.p.config
        self.log.setLevel(logging.DEBUG)
        self.log.info("============================= Adv plugin: loading config ============================")
        self.p.onLoadConfig()
        self.log.info("============================= Adv plugin: starting  =================================")
        self.p.onStartup()


class Test_default_config(AdvTestCase):
    """ test that bad words from the default config are detected """

    def test_default_config(self):
        self.init_plugin()
        self.assertEqual('2', self.p._rate)
        self.assertIsNone(self.p._fileName)
        self.assertEqual(10, len(self.p._msg.items))
        self.assertEqual("http://forum.bigbrotherbot.net/news-2/?type=rss;action=.xml", self.p._feed)
        self.assertEqual("News: ", self.p._feedpre)
        self.assertEqual(4, self.p._feedmaxitems)
        self.assertEqual('News: ', self.p._feedpre)
        self.assertIsNotNone(self.p._cronTab)
        self.assertTupleEqual((0, range(0, 59, 2), -1, -1, -1, -1),
                              (self.p._cronTab.second, self.p._cronTab.minute, self.p._cronTab.hour,
                               self.p._cronTab.day, self.p._cronTab.month, self.p._cronTab.dow))

    def test_empty(self):
        self.init_plugin("""<configuration plugin="adv" />""")
        self.assertIsNone(self.p._rate)
        self.assertIsNone(self.p._fileName)
        self.assertEqual(0, len(self.p._msg.items))
        self.assertEqual("http://forum.bigbrotherbot.net/news-2/?type=rss;action=.xml", self.p._feed)
        self.assertEqual("News: ", self.p._feedpre)
        self.assertEqual(5, self.p._feedmaxitems)
        self.assertEqual('News: ', self.p._feedpre)
        self.assertIsNone(self.p._cronTab)

    def test_rate_nominal(self):
        self.init_plugin("""\
<configuration plugin="adv">
    <settings name="settings">
        <set name="rate">1</set>
    </settings>
</configuration>
""")
        self.assertEqual('1', self.p._rate)
        self.assertIsNotNone(self.p._cronTab)
        self.assertTupleEqual((0, range(60), -1, -1, -1, -1),
                              (self.p._cronTab.second, self.p._cronTab.minute, self.p._cronTab.hour,
                               self.p._cronTab.day, self.p._cronTab.month, self.p._cronTab.dow))

    def test_rate_nominal_second(self):
        self.init_plugin("""\
<configuration plugin="adv">
    <settings name="settings">
        <set name="rate">40s</set>
    </settings>
</configuration>
""")
        self.assertEqual('40s', self.p._rate)
        self.assertIsNotNone(self.p._cronTab)
        self.assertTupleEqual(([0, 40], -1, -1, -1, -1, -1),
                              (self.p._cronTab.second, self.p._cronTab.minute, self.p._cronTab.hour,
                               self.p._cronTab.day, self.p._cronTab.month, self.p._cronTab.dow))

    def test_rate_junk(self):
        try:
            self.init_plugin("""\
<configuration plugin="adv">
    <settings name="settings">
        <set name="rate">f00</set>
    </settings>
</configuration>
""")
        except TypeError, err:
            print err
        except Exception:
            raise
        self.assertEqual('f00', self.p._rate)
        self.assertIsNone(self.p._cronTab)



class Test_commands(AdvTestCase):

    def setUp(self):
        AdvTestCase.setUp(self)
        self.joe = FakeClient(self.console, name="Joe", guid="joeguid", groupBits=128)

    def tearDown(self):
        AdvTestCase.tearDown(self)

    #################### advlist ####################
    def test_advlist_empty(self):
        self.init_plugin("""
            <configuration>
                <settings name="settings">
                    <set name="rate">30s</set>
                </settings>
                <ads>
                </ads>
            </configuration>
        """)
        self.joe.clearMessageHistory()
        self.p.cmd_advlist(data=None, client=self.joe)
        self.assertEqual([], self.p._msg.items)
        self.assertEqual(['Adv: No ads loaded'], self.joe.message_history)

    def test_advlist_one_item(self):
        self.init_plugin("""
            <configuration>
                <settings name="settings">
                    <set name="rate">30s</set>
                </settings>
                <ads>
                    <ad>f00</ad>
                </ads>
            </configuration>
        """)
        self.joe.clearMessageHistory()
        self.p.cmd_advlist(data=None, client=self.joe)
        self.assertEqual(['f00'], self.p._msg.items)
        self.assertEqual(['Adv: [1] f00'], self.joe.message_history)

    def test_advlist_many_items(self):
        self.init_plugin("""
            <configuration>
                <settings name="settings">
                    <set name="rate">30s</set>
                </settings>
                <ads>
                    <ad>f00</ad>
                    <ad>bar</ad>
                    <ad>test</ad>
                </ads>
            </configuration>
        """)
        self.joe.clearMessageHistory()
        self.p.cmd_advlist(data=None, client=self.joe)
        self.assertEqual(['f00', 'bar', 'test'], self.p._msg.items)
        self.assertEqual(['Adv: [1] f00', 'Adv: [2] bar', 'Adv: [3] test'], self.joe.message_history)

    #################### advrate ####################

    def test_advrate_no_arg_30s(self):
        self.init_plugin("""
            <configuration>
                <settings name="settings">
                    <set name="rate">30s</set>
                </settings>
                <ads>
                    <ad>f00</ad>
                    <ad>bar</ad>
                    <ad>test</ad>
                </ads>
            </configuration>
        """)
        self.joe.clearMessageHistory()
        self.p.cmd_advrate(data='', client=self.joe)
        self.assertEqual('30s', self.p._rate)
        self.assertEqual(['Current rate is every 30 seconds'], self.joe.message_history)

    def test_advrate_no_arg_2min(self):
        self.init_plugin("""
            <configuration>
                <settings name="settings">
                    <set name="rate">2</set>
                </settings>
                <ads>
                    <ad>f00</ad>
                    <ad>bar</ad>
                    <ad>test</ad>
                </ads>
            </configuration>
        """)
        self.joe.clearMessageHistory()
        self.p.cmd_advrate(data=None, client=self.joe)
        self.assertEqual('2', self.p._rate)
        self.assertEqual(['Current rate is every 2 minutes'], self.joe.message_history)

    def test_advrate_set_20s(self):
        self.init_plugin("""
            <configuration>
                <settings name="settings">
                    <set name="rate">45s</set>
                </settings>
                <ads>
                    <ad>f00</ad>
                    <ad>bar</ad>
                    <ad>test</ad>
                </ads>
            </configuration>
        """)
        self.assertEqual('45s', self.p._rate)
        self.joe.clearMessageHistory()
        self.p.cmd_advrate(data="20s", client=self.joe)
        self.assertEqual('20s', self.p._rate)
        self.assertEqual(['Adv: Rate set to 20 seconds'], self.joe.message_history)

    def test_advrate_set_3min(self):
        self.init_plugin("""
            <configuration>
                <settings name="settings">
                    <set name="rate">45s</set>
                </settings>
                <ads>
                    <ad>f00</ad>
                    <ad>bar</ad>
                    <ad>test</ad>
                </ads>
            </configuration>
        """)
        self.assertEqual('45s', self.p._rate)
        self.joe.clearMessageHistory()
        self.p.cmd_advrate(data="3", client=self.joe)
        self.assertEqual('3', self.p._rate)
        self.assertEqual(['Adv: Rate set to 3 minutes'], self.joe.message_history)

    #################### advrem ####################

    def test_advrem_nominal(self):
        self.init_plugin("""
            <configuration>
                <settings name="settings">
                    <set name="rate">45s</set>
                </settings>
                <ads>
                    <ad>f00</ad>
                    <ad>bar</ad>
                    <ad>test</ad>
                </ads>
            </configuration>
        """)
        self.assertEqual(['f00', 'bar', 'test'], self.p._msg.items)
        self.joe.clearMessageHistory()
        self.p.cmd_advrem(data="2", client=self.joe)
        self.assertEqual(['f00', 'test'], self.p._msg.items)
        self.assertEqual(['Adv: Removed item: bar'], self.joe.message_history)

    def test_advrem_no_arg(self):
        self.init_plugin("""
            <configuration>
                <settings name="settings">
                    <set name="rate">45s</set>
                </settings>
                <ads>
                    <ad>f00</ad>
                    <ad>bar</ad>
                    <ad>test</ad>
                </ads>
            </configuration>
        """)
        self.assertEqual(['f00', 'bar', 'test'], self.p._msg.items)
        self.joe.clearMessageHistory()
        self.p.cmd_advrem(data=None, client=self.joe)
        self.assertEqual(['f00', 'bar', 'test'], self.p._msg.items)
        self.assertEqual(['Invalid data, use the !advlist command to list valid items numbers'], self.joe.message_history)

    def test_advrem_junk(self):
        self.init_plugin("""
            <configuration>
                <settings name="settings">
                    <set name="rate">45s</set>
                </settings>
                <ads>
                    <ad>f00</ad>
                    <ad>bar</ad>
                    <ad>test</ad>
                </ads>
            </configuration>
        """)
        self.assertEqual(['f00', 'bar', 'test'], self.p._msg.items)
        self.joe.clearMessageHistory()
        self.p.cmd_advrem(data='f00', client=self.joe)
        self.assertEqual(['f00', 'bar', 'test'], self.p._msg.items)
        self.assertEqual(['Invalid data, use the !advlist command to list valid items numbers'], self.joe.message_history)

    def test_advrem_invalid_index(self):
        self.init_plugin("""
            <configuration>
                <settings name="settings">
                    <set name="rate">45s</set>
                </settings>
                <ads>
                    <ad>f00</ad>
                    <ad>bar</ad>
                    <ad>test</ad>
                </ads>
            </configuration>
        """)
        self.assertEqual(['f00', 'bar', 'test'], self.p._msg.items)
        self.joe.clearMessageHistory()
        self.p.cmd_advrem(data='-18', client=self.joe)
        self.assertEqual(['f00', 'bar', 'test'], self.p._msg.items)
        self.assertEqual(['Invalid data, use the !advlist command to list valid items numbers'], self.joe.message_history)

    #################### advadd ####################

    def test_advadd_nominal(self):
        self.init_plugin("""
            <configuration>
                <settings name="settings">
                    <set name="rate">45s</set>
                </settings>
                <ads>
                    <ad>f00</ad>
                </ads>
            </configuration>
        """)
        self.assertEqual(['f00'], self.p._msg.items)
        self.joe.clearMessageHistory()
        self.p.cmd_advadd(data="bar", client=self.joe)
        self.assertEqual(['f00', 'bar'], self.p._msg.items)
        self.assertEqual(['Adv: "bar" added'], self.joe.message_history)

    def test_advadd_no_arg(self):
        self.init_plugin("""
            <configuration>
                <settings name="settings">
                    <set name="rate">45s</set>
                </settings>
                <ads>
                    <ad>f00</ad>
                </ads>
            </configuration>
        """)
        self.assertEqual(['f00'], self.p._msg.items)
        self.joe.clearMessageHistory()
        self.p.cmd_advadd(data=None, client=self.joe)
        self.assertEqual(['f00'], self.p._msg.items)
        self.assertEqual(['Invalid data, specify the message to add'], self.joe.message_history)


class Test_keywords(AdvTestCase):

    def setUp(self):
        AdvTestCase.setUp(self)
        self.init_plugin()

    def test_admins(self):
        # GIVEN
        when(self.p._msg).getnext().thenReturn("@admins")
        joe = FakeClient(self.console, name="Joe", guid="joeguid", groupBits=128)
        when(self.p._adminPlugin).getAdmins().thenReturn([joe])
        with patch.object(self.console, "say") as say_mock:
            # WHEN
            self.p.adv()
        # THEN
        say_mock.assert_has_calls([call('^7Admins online: Joe^7^7 [^3100^7]')])

    def test_regulars(self):
        # GIVEN
        when(self.p._msg).getnext().thenReturn("@regulars")
        joe = FakeClient(self.console, name="Joe", guid="joeguid", groupBits=2)
        when(self.p._adminPlugin).getRegulars().thenReturn([joe])
        with patch.object(self.console, "say") as say_mock:
            # WHEN
            self.p.adv()
        # THEN
        say_mock.assert_has_calls([call('^7Regular players online: Joe^7')])

    def test_topstats(self):
        when(self.p._msg).getnext().thenReturn("@topstats")
        self.p._xlrstatsPlugin = Mock()
        with patch.object(self.p._xlrstatsPlugin, "cmd_xlrtopstats") as xlrtopstats_mock:
            self.p.adv()
            xlrtopstats_mock.assert_has_calls([call(ext=True, cmd=None, data='3', client=None)])

    def test_time(self):
        when(self.p._msg).getnext().thenReturn("@time")
        when(self.console).formatTime(mockito_any()).thenReturn("f00")
        with patch.object(self.console, "say") as say_mock:
            self.p.adv()
            say_mock.assert_has_calls([call('^2Time: ^3f00')])

    def test_nextmap(self):
        when(self.p._msg).getnext().thenReturn("@nextmap")
        when(self.console).getNextMap().thenReturn("f00")
        with patch.object(self.console, "say") as say_mock:
            self.p.adv()
            say_mock.assert_has_calls([call('^2Next map: ^3f00')])


class Test_MessageLoop(unittest.TestCase):

    def test_empty(self):
        ml = MessageLoop()
        self.assertEqual([], ml.items)
        self.assertEqual(None, ml.getnext())

    def test_one_element(self):
        ml = MessageLoop()
        ml.items = ['f00']
        self.assertEqual('f00', ml.getnext())
        self.assertEqual('f00', ml.getnext())

    def test_three_elements(self):
        ml = MessageLoop()
        ml.items = ['f001', 'f002', 'f003']
        self.assertEqual('f001', ml.getnext())
        self.assertEqual('f002', ml.getnext())
        self.assertEqual('f003', ml.getnext())
        self.assertEqual('f001', ml.getnext())
        self.assertEqual('f002', ml.getnext())
        self.assertEqual('f003', ml.getnext())

    def test_put(self):
        ml = MessageLoop()
        self.assertEqual([], ml.items)
        ml.put("bar")
        self.assertEqual(["bar"], ml.items)

    def test_getitem(self):
        ml = MessageLoop()
        ml.items = ['f00']
        self.assertEqual("f00", ml.getitem(0))
        self.assertEqual(None, ml.getitem(1))

    def test_remove(self):
        ml = MessageLoop()
        ml.items = ['f00', 'bar']
        self.assertEqual("f00", ml.getitem(0))
        ml.remove(0)
        self.assertEqual(['bar'], ml.items)
        self.assertEqual("bar", ml.getitem(0))

    def test_clear(self):
        ml = MessageLoop()
        ml.items = ['f00', 'bar']
        ml.clear()
        self.assertEqual([], ml.items)