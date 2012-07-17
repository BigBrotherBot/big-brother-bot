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
import logging

from mock import Mock, call, patch
import sys, os, thread
import time
import unittest2 as unittest

from b3 import __file__ as b3_module__file__, TEAM_BLUE, TEAM_RED

from tests import B3TestCase
from b3.fake import FakeClient
from b3.config import XmlConfigParser
from b3.plugins.admin import AdminPlugin

ADMIN_CONFIG_FILE = os.path.join(os.path.dirname(b3_module__file__), "conf/plugin_admin.xml")

class Admin_functional_test(B3TestCase):
    """ tests from a class inherithing from Admin_functional_test must call self.init() """
    def setUp(self):
        B3TestCase.setUp(self)
        self.conf = XmlConfigParser()
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
        self.p.onLoadConfig()
        self.p.onStartup()

        self.joe = FakeClient(self.console, name="Joe", exactName="Joe", guid="joeguid", groupBits=128, team=TEAM_RED)
        self.mike = FakeClient(self.console, name="Mike", exactName="Mike", guid="mikeguid", groupBits=1, team=TEAM_BLUE)


class Cmd_tempban(Admin_functional_test):

    def setUp(self):
        Admin_functional_test.setUp(self)
        self.init()

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
    def setUp(self):
        Admin_functional_test.setUp(self)
        self.init()

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


@unittest.skipUnless(os.path.isfile(ADMIN_CONFIG_FILE), "%s is not a file" % ADMIN_CONFIG_FILE)
class Test_config(Admin_functional_test):
    def setUp(self):
        Admin_functional_test.setUp(self)
        logging.getLogger('output').setLevel(logging.INFO)

    def test_no_generic_or_default_warn_readon(self):

        # load the default plugin_admin.xml file after having remove the 'generic' setting from section 'warn_reasons'
        from b3.lib.elementtree import ElementTree as ET
        root = ET.parse(ADMIN_CONFIG_FILE).getroot()
        warn_reasons_nodes = [x for x in root.findall('settings') if x.get('name') == 'warn_reasons' ][0]
        if len(warn_reasons_nodes):
            generic_nodes = [x for x in warn_reasons_nodes[0].findall('set') if x.get('name') == "generic"]
            if len(generic_nodes):
                warn_reasons_nodes[0].remove(generic_nodes[0])
            default_nodes = [x for x in warn_reasons_nodes[0].findall('set') if x.get('name') == "default"]
            if len(default_nodes):
                warn_reasons_nodes[0].remove(default_nodes[0])
        self.init(ET.tostring(root))

        self.joe.message = Mock(lambda x: sys.stdout.write("message to Joe: " + x + "\n"))
        self.joe.connects(0)
        self.joe.says('!warntest')
        self.joe.message.assert_called_once_with('^2TEST: ^1WARNING^7 [^31^7]: ^7behave yourself')
        self.joe.message.reset_mock()
        self.joe.says('!warntest argue')
        self.joe.message.assert_called_once_with('^2TEST: ^1WARNING^7 [^31^7]: ^3Rule #3: No arguing with admins (listen and learn or leave)')


    def test_bad_format_for_generic_and_default(self):
        self.init("""<configuration>
                        <settings name="warn_reasons">
                            <set name="generic">1h</set>
                            <set name="default">/</set>
                        </settings>
                    </configuration>""")
        self.assertEqual((60, "^7"), self.p.warn_reasons['generic'])
        self.assertEqual((60, "^7behave yourself"), self.p.warn_reasons['default'])

    def test_bad_format_1(self):
        self.init("""<configuration>
                        <settings name="warn_reasons">
                            <set name="foo">foo</set>
                            <set name="bar">5d</set>
                        </settings>
                    </configuration>""")
        self.assertNotIn('foo', self.p.warn_reasons)

    def test_bad_format_2(self):
        self.init("""<configuration>
                        <settings name="warn_reasons">
                            <set name="foo">/foo bar</set>
                        </settings>
                    </configuration>""")
        self.assertNotIn('foo', self.p.warn_reasons)

    def test_bad_format_3(self):
        self.init("""<configuration>
                        <settings name="warn_reasons">
                            <set name="foo">/spam#</set>
                            <set name="bar">/spam# qsdf sq</set>
                        </settings>
                    </configuration>""")
        self.assertNotIn('foo', self.p.warn_reasons)

    def test_reference_to_warn_reason(self):
        self.init("""<configuration>
                        <settings name="warn_reasons">
                            <set name="foo">2h, foo</set>
                            <set name="bar">/foo</set>
                        </settings>
                    </configuration>""")
        self.assertIn('foo', self.p.warn_reasons)
        self.assertEqual((120, 'foo'), self.p.warn_reasons['foo'])
        self.assertIn('bar', self.p.warn_reasons)
        self.assertEqual((120, 'foo'), self.p.warn_reasons['bar'])


    def test_invalid_reference_to_warn_reason(self):
        self.init("""<configuration>
                        <settings name="warn_reasons">
                            <set name="foo">2h, foo</set>
                            <set name="bar">/nonexisting</set>
                        </settings>
                    </configuration>""")
        self.assertIn('foo', self.p.warn_reasons)
        self.assertEqual((120, 'foo'), self.p.warn_reasons['foo'])
        self.assertNotIn('bar', self.p.warn_reasons)


    def test_reference_to_spamage(self):
        self.init("""<configuration>
                        <settings name="spamages">
                            <set name="foo">fOO fOO</set>
                        </settings>
                        <settings name="warn_reasons">
                            <set name="bar">4h, /spam#foo</set>
                        </settings>
                    </configuration>""")
        self.assertIn('bar', self.p.warn_reasons)
        self.assertEqual((240, 'fOO fOO'), self.p.warn_reasons['bar'])


    def test_invalid_reference_to_spamage(self):
        self.init("""<configuration>
                        <settings name="warn_reasons">
                            <set name="bar">4h, /spam#foo</set>
                        </settings>
                    </configuration>""")
        self.assertNotIn('bar', self.p.warn_reasons)