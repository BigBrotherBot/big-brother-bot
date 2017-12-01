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
import logging
import sys

from mock import patch, call, Mock
from tests.plugins.admin import Admin_TestCase, Admin_functional_test


class Config_reading_TestCase(Admin_TestCase):
    """
    Test case base class that ease assertions against calls to self.p.warning and self.p.error methods.
    """
    MESSAGE_BEACON = None

    def __init__(self, *args, **kwargs):
        Admin_TestCase.__init__(self, *args, **kwargs)
        if not self.__class__.MESSAGE_BEACON:
            raise NotImplementedError("you are supposed to set MESSAGE_BEACON with a string to look for in warning "
                                      "and error messages when inheriting from Config_reading_TestCase")

    def setUp(self):
        Admin_TestCase.setUp(self)
        self.warning_patcher = patch.object(self.p, "warning", wraps=self.p.warning)
        self.warning_mock = self.warning_patcher.start()
        self.error_patcher = patch.object(self.p, "error", wraps=self.p.error)
        self.error_mock = self.error_patcher.start()

    def tearDown(self):
        Admin_TestCase.tearDown(self)
        self.warning_patcher.stop()
        self.error_patcher.stop()

    def assertNoWarningMessage(self):
        """
        assert that the word 'announce_registration' is not found in any message of the call to self.warning_mock
        """
        found_calls = []
        for the_call in self.warning_mock.mock_calls:
            try:
                if self.MESSAGE_BEACON in the_call[1][0]:
                    found_calls.append(the_call)
            except IndexError:
                pass
        self.assertListEqual([], found_calls, "'%s' was found mentioned in some warning calls %r"
                                              % (self.MESSAGE_BEACON, found_calls))

    def assertNoErrorMessage(self):
        """
        assert that the word 'announce_registration' is not found in any message of the call to self.error_mock
        """
        found_calls = []
        for the_call in self.error_mock.mock_calls:
            try:
                if self.MESSAGE_BEACON in the_call[1][0]:
                    found_calls.append(the_call)
            except IndexError:
                pass
        self.assertListEqual([], found_calls, "'%s' was found mentioned in some warning calls %r"
                                              % (self.MESSAGE_BEACON, found_calls))


class Test_conf_announce_registration(Config_reading_TestCase):
    """
    test the correct reading of admin config option 'announce_registration' from config section 'settings'
    """
    MESSAGE_BEACON = 'announce_registration'

    def test_missing(self):
        # GIVEN
        self.conf.loadFromString(r"""[settings]""")
        # WHEN
        self.p.onLoadConfig()
        # THEN
        self.assertTrue(self.p._announce_registration)
        self.assertIn(call('could not find settings/announce_registration in config file, using default: True'),
                      self.warning_mock.mock_calls)
        self.assertNoErrorMessage()

    def test_yes(self):
        # GIVEN
        self.conf.loadFromString(r"""[settings]
announce_registration: yes
""")
        # WHEN
        self.p.onLoadConfig()
        # THEN
        self.assertTrue(self.p._announce_registration)
        self.assertNoWarningMessage()
        self.assertNoErrorMessage()

    def test_no(self):
        # GIVEN
        self.conf.loadFromString(r"""[settings]
announce_registration: no
""")
        # WHEN
        self.p.onLoadConfig()
        # THEN
        self.assertFalse(self.p._announce_registration)
        self.assertNoWarningMessage()
        self.assertNoErrorMessage()

    def test_on(self):
        # GIVEN
        self.conf.loadFromString(r"""[settings]
announce_registration: on
""")
        # WHEN
        self.p.onLoadConfig()
        # THEN
        self.assertTrue(self.p._announce_registration)
        self.assertNoWarningMessage()
        self.assertNoErrorMessage()

    def test_off(self):
        # GIVEN
        self.conf.loadFromString(r"""[settings]
announce_registration: OFF
""")
        # WHEN
        self.p.onLoadConfig()
        # THEN
        self.assertFalse(self.p._announce_registration)
        self.assertNoWarningMessage()
        self.assertNoErrorMessage()

    def test_empty(self):
        # GIVEN
        self.conf.loadFromString(r"""[settings]
announce_registration:
""")
        # WHEN
        self.p.onLoadConfig()
        # THEN
        self.assertTrue(self.p._announce_registration)
        self.assertNoWarningMessage()
        self.assertIn(call("could not load settings/announce_registration config value: settings.announce_registration : "
                           "'' is not a boolean value"), self.error_mock.mock_calls)

    def test_junk(self):
        # GIVEN
        self.conf.loadFromString(r"""[settings]
announce_registration: xxxxxxxxx
""")
        # WHEN
        self.p.onLoadConfig()
        # THEN
        self.assertTrue(self.p._announce_registration)
        self.assertNoWarningMessage()
        self.assertIn(call("could not load settings/announce_registration config value: settings.announce_registration : "
                           "'xxxxxxxxx' is not a boolean value"), self.error_mock.mock_calls)


class Test_conf_regme_confirmation(Config_reading_TestCase):
    """
    test the correct reading of admin config option 'regme_confirmation' from config section 'messages'
    """
    MESSAGE_BEACON = 'regme_confirmation'

    def test_missing(self):
        # GIVEN
        self.conf.loadFromString(r"""[messages]
""")
        # WHEN
        self.p.onLoadConfig()
        # THEN
        self.assertEqual('^7Thanks for your registration. You are now a member of the group f00',
                         self.p.getMessage('regme_confirmation', 'f00'))
        self.assertIn(call("could not find messages/regme_confirmation in config file, using default: ^7Thanks for your "
                           "registration. You are now a member of the group %s"), self.warning_mock.mock_calls)
        self.assertNoErrorMessage()

    def test_nominal(self):
        # GIVEN
        self.conf.loadFromString(r"""[messages]
regme_confirmation: Nice, you are now a member of the group %s
""")
        # WHEN
        self.p.onLoadConfig()
        # THEN
        self.assertEqual('Nice, you are now a member of the group f00', self.p.getMessage('regme_confirmation', 'f00'))
        self.assertNoWarningMessage()
        self.assertNoErrorMessage()

    def test_no_place_holder(self):
        # GIVEN
        self.conf.loadFromString(r"""[messages]
regme_confirmation: ^7Thanks for your registration
""")
        # WHEN
        self.p.onLoadConfig()
        # THEN
        self.assertEqual('^7Thanks for your registration. You are now a member of the group f00',
                         self.p.getMessage('regme_confirmation', 'f00'))
        self.assertNoWarningMessage()
        self.assertIn(call("could not load messages/regme_confirmation config value: message regme_confirmation must "
                           "have a placeholder \'%%s\' for the group name"), self.error_mock.mock_calls)


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



class Test_config(Admin_functional_test):

    def setUp(self):
        Admin_functional_test.setUp(self)
        logging.getLogger('output').setLevel(logging.INFO)

    def test_no_generic_or_default_warn_reason(self):

        # load the default plugin_admin.ini file after having remove the 'generic' setting from section 'warn_reasons'
        new_config_content = ""
        with open(b3.getAbsolutePath('@b3/conf/plugin_admin.ini')) as config_file:
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