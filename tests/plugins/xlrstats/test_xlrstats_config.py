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

import logging
import os

from b3.config import CfgConfigParser
from b3.plugins.xlrstats import XlrstatsPlugin
from b3 import __file__ as b3_module__file__
from tests import B3TestCase


DEFAULT_XLRSTATS_CONFIG_FILE = os.path.join(os.path.dirname(b3_module__file__), 'conf', 'plugin_xlrstats.ini')


class XlrstatsTestCase(B3TestCase):

    def setUp(self):
        """
        This method is called before each test.
        It is meant to set up the SUT (System Under Test) in a manner that will ease the testing of its features.
        """
        # The B3TestCase class provides us a working B3 environment that does not require any database connexion.
        # The B3 console is then accessible with self.console
        B3TestCase.setUp(self)

        # We need a config for the Xlrstats plugin
        self.conf = CfgConfigParser()  # It is an empty config but we can fill it up later

        # Now we create an instance of the SUT (System Under Test) which is the XlrstatsPlugin
        self.p = XlrstatsPlugin(self.console, self.conf)

        # Setup the logging level we'd like to be spammed with during the tests
        logger = logging.getLogger('output')
        logger.setLevel(logging.DEBUG)


class Test_conf(XlrstatsTestCase):

    def test_empty_conf(self):
        """
        Test the behaviors expected when one starts the Xlrstats plugin with an empty config file
        """
        # GIVEN
        self.conf.loadFromString(r"""
        """)
        # WHEN
        self.p.onLoadConfig()
        # THEN
        self.assertFalse(self.p.silent)
        self.assertTrue(self.p.hide_bots)
        self.assertTrue(self.p.exclude_bots)
        self.assertEqual(3, self.p.min_players)
        self.assertEqual('', self.p.webfront_url)
        self.assertEqual(0, self.p.webfront_config_nr)
        self.assertTrue(self.p.keep_history)
        self.assertFalse(self.p.onemaponly)
        self.assertEqual(0, self.p.minlevel)
        self.assertEqual(1000, self.p.defaultskill)
        self.assertEqual(16, self.p.Kfactor_high)
        self.assertEqual(4, self.p.Kfactor_low)
        self.assertEqual(50, self.p.Kswitch_confrontations)
        self.assertEqual(600, self.p.steepness)
        self.assertEqual(0.05, self.p.suicide_penalty_percent)
        self.assertEqual(0.1, self.p.tk_penalty_percent)
        self.assertEqual(2, self.p.assist_timespan)
        self.assertEqual(10, self.p.damage_assist_release)
        self.assertEqual(70, self.p.prematch_maxtime)
        self.assertFalse(self.p.announce)
        self.assertTrue(self.p.keep_time)
        self.assertTrue(self.p.provisional_ranking)
        self.assertTrue(self.p._defaultTableNames)
        self.assertEqual('xlr_playerstats', self.p.playerstats_table)
        self.assertEqual('xlr_weaponstats', self.p.weaponstats_table)
        self.assertEqual('xlr_weaponusage', self.p.weaponusage_table)
        self.assertEqual('xlr_bodyparts', self.p.bodyparts_table)
        self.assertEqual('xlr_playerbody', self.p.playerbody_table)
        self.assertEqual('xlr_opponents', self.p.opponents_table)
        self.assertEqual('xlr_mapstats', self.p.mapstats_table)
        self.assertEqual('xlr_playermaps', self.p.playermaps_table)
        self.assertEqual('xlr_actionstats', self.p.actionstats_table)
        self.assertEqual('xlr_playeractions', self.p.playeractions_table)
        self.assertEqual('xlr_history_monthly', self.p.history_monthly_table)
        self.assertEqual('xlr_history_weekly', self.p.history_weekly_table)
        self.assertEqual('ctime', self.p.ctime_table)

    def test_default_conf(self):
        """
        Test the behaviors expected when one starts the Xlrstats plugin with the default config file
        """
        # GIVEN
        self.conf.load(DEFAULT_XLRSTATS_CONFIG_FILE)
        # WHEN
        self.p.onLoadConfig()
        # THEN
        self.assertFalse(self.p.silent)
        self.assertTrue(self.p.hide_bots)
        self.assertTrue(self.p.exclude_bots)
        self.assertEqual(3, self.p.min_players)
        self.assertEqual('', self.p.webfront_url)
        self.assertEqual(0, self.p.webfront_config_nr)
        self.assertTrue(self.p.keep_history)
        self.assertFalse(self.p.onemaponly)
        self.assertEqual(0, self.p.minlevel)
        self.assertEqual(1000, self.p.defaultskill)
        self.assertEqual(16, self.p.Kfactor_high)
        self.assertEqual(4, self.p.Kfactor_low)
        self.assertEqual(50, self.p.Kswitch_confrontations)
        self.assertEqual(600, self.p.steepness)
        self.assertEqual(0.05, self.p.suicide_penalty_percent)
        self.assertEqual(0.1, self.p.tk_penalty_percent)
        self.assertEqual(2, self.p.assist_timespan)
        self.assertEqual(10, self.p.damage_assist_release)
        self.assertEqual(70, self.p.prematch_maxtime)
        self.assertFalse(self.p.announce)
        self.assertTrue(self.p.keep_time)
        self.assertTrue(self.p.provisional_ranking)
        self.assertTrue(self.p._defaultTableNames)
        self.assertEqual('xlr_playerstats', self.p.playerstats_table)
        self.assertEqual('xlr_weaponstats', self.p.weaponstats_table)
        self.assertEqual('xlr_weaponusage', self.p.weaponusage_table)
        self.assertEqual('xlr_bodyparts', self.p.bodyparts_table)
        self.assertEqual('xlr_playerbody', self.p.playerbody_table)
        self.assertEqual('xlr_opponents', self.p.opponents_table)
        self.assertEqual('xlr_mapstats', self.p.mapstats_table)
        self.assertEqual('xlr_playermaps', self.p.playermaps_table)
        self.assertEqual('xlr_actionstats', self.p.actionstats_table)
        self.assertEqual('xlr_playeractions', self.p.playeractions_table)
        self.assertEqual('xlr_history_monthly', self.p.history_monthly_table)
        self.assertEqual('xlr_history_weekly', self.p.history_weekly_table)
        self.assertEqual('ctime', self.p.ctime_table)


class Conf_settings_test_case(XlrstatsTestCase):

    def init(self, option_snippet=''):
        """
        Load the XLRstats plugin with an empty config file except for the option_snippet given as a parameter which will
        be injected in the "settings" section.
        Then call the plugin onLoadConfig method.
        """
        self.conf.loadFromString(r"""
[settings]
%s
""" % option_snippet)
        self.p.onLoadConfig()


class Test_conf_settings_silent(Conf_settings_test_case):

    def test_missing(self):
        # WHEN
        self.init('')
        # THEN
        self.assertFalse(self.p.silent)

    def test_empty(self):
        # WHEN
        self.init('silent:')
        # THEN
        self.assertFalse(self.p.silent)

    def test_junk(self):
        # WHEN
        self.init('silent: f00')
        # THEN
        self.assertFalse(self.p.silent)

    def test_true(self):
        # WHEN
        self.init('silent: true')
        # THEN
        self.assertTrue(self.p.silent)

    def test_on(self):
        # WHEN
        self.init('silent: on')
        # THEN
        self.assertTrue(self.p.silent)

    def test_1(self):
        # WHEN
        self.init('silent: 1')
        # THEN
        self.assertTrue(self.p.silent)

    def test_yes(self):
        # WHEN
        self.init('silent: yes')
        # THEN
        self.assertTrue(self.p.silent)

    def test_false(self):
        # WHEN
        self.init('silent: false')
        # THEN
        self.assertFalse(self.p.silent)

    def test_off(self):
        # WHEN
        self.init('silent:off')
        # THEN
        self.assertFalse(self.p.silent)

    def test_0(self):
        # WHEN
        self.init('silent: 0')
        # THEN
        self.assertFalse(self.p.silent)

    def test_no(self):
        # WHEN
        self.init('silent: false')
        # THEN
        self.assertFalse(self.p.silent)


class Test_conf_settings_hide_bots(Conf_settings_test_case):

    def test_missing(self):
        # WHEN
        self.init('')
        # THEN
        self.assertTrue(self.p.hide_bots)

    def test_empty(self):
        # WHEN
        self.init('hide_bots: ')
        # THEN
        self.assertTrue(self.p.hide_bots)

    def test_junk(self):
        # WHEN
        self.init('hide_bots: f00')
        # THEN
        self.assertTrue(self.p.hide_bots)

    def test_true(self):
        # WHEN
        self.init('hide_bots: true')
        # THEN
        self.assertTrue(self.p.hide_bots)

    def test_on(self):
        # WHEN
        self.init('hide_bots: on')
        # THEN
        self.assertTrue(self.p.hide_bots)

    def test_1(self):
        # WHEN
        self.init('hide_bots: 1')
        # THEN
        self.assertTrue(self.p.hide_bots)

    def test_yes(self):
        # WHEN
        self.init('hide_bots: yes')
        # THEN
        self.assertTrue(self.p.hide_bots)

    def test_false(self):
        # WHEN
        self.init('hide_bots: false')
        # THEN
        self.assertFalse(self.p.hide_bots)

    def test_off(self):
        # WHEN
        self.init('hide_bots: off')
        # THEN
        self.assertFalse(self.p.hide_bots)

    def test_0(self):
        # WHEN
        self.init('hide_bots: 0')
        # THEN
        self.assertFalse(self.p.hide_bots)

    def test_no(self):
        # WHEN
        self.init('hide_bots: false')
        # THEN
        self.assertFalse(self.p.hide_bots)


class Test_conf_settings_exclude_bots(Conf_settings_test_case):

    def test_missing(self):
        # WHEN
        self.init('')
        # THEN
        self.assertTrue(self.p.exclude_bots)

    def test_empty(self):
        # WHEN
        self.init('exclude_bots: ')
        # THEN
        self.assertTrue(self.p.exclude_bots)

    def test_junk(self):
        # WHEN
        self.init('exclude_bots: f00')
        # THEN
        self.assertTrue(self.p.exclude_bots)

    def test_true(self):
        # WHEN
        self.init('exclude_bots: true')
        # THEN
        self.assertTrue(self.p.exclude_bots)

    def test_on(self):
        # WHEN
        self.init('exclude_bots: on')
        # THEN
        self.assertTrue(self.p.exclude_bots)

    def test_1(self):
        # WHEN
        self.init('exclude_bots: 1')
        # THEN
        self.assertTrue(self.p.exclude_bots)

    def test_yes(self):
        # WHEN
        self.init('exclude_bots: yes')
        # THEN
        self.assertTrue(self.p.exclude_bots)

    def test_false(self):
        # WHEN
        self.init('exclude_bots: false')
        # THEN
        self.assertFalse(self.p.exclude_bots)

    def test_off(self):
        # WHEN
        self.init('exclude_bots: off')
        # THEN
        self.assertFalse(self.p.exclude_bots)

    def test_0(self):
        # WHEN
        self.init('exclude_bots: 0')
        # THEN
        self.assertFalse(self.p.exclude_bots)

    def test_no(self):
        # WHEN
        self.init('exclude_bots: false')
        # THEN
        self.assertFalse(self.p.exclude_bots)


class Test_conf_settings_minPlayers(Conf_settings_test_case):
    DEFAULT_VALUE = 3

    def test_missing(self):
        # WHEN
        self.init('')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.min_players)

    def test_empty(self):
        # WHEN
        self.init('minplayers: ')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.min_players)

    def test_junk(self):
        # WHEN
        self.init('minplayers: f00')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.min_players)

    def test_negative(self):
        # WHEN
        self.init('minplayers: -5')
        # THEN
        self.assertEqual(0, self.p.min_players)

    def test_0(self):
        # WHEN
        self.init('minplayers: 0')
        # THEN
        self.assertEqual(0, self.p.min_players)

    def test_1(self):
        # WHEN
        self.init('minplayers: 1')
        # THEN
        self.assertEqual(1, self.p.min_players)

    def test_8(self):
        # WHEN
        self.init('minplayers: 8')
        # THEN
        self.assertEqual(8, self.p.min_players)

    def test_float(self):
        # WHEN
        self.init('minplayers: 0.5')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.min_players)


class Test_conf_settings_webfronturl(Conf_settings_test_case):

    def test_missing(self):
        # WHEN
        self.init('')
        # THEN
        self.assertEqual('', self.p.webfront_url)

    def test_empty(self):
        # WHEN
        self.init('webfronturl: ')
        # THEN
        self.assertEqual('', self.p.webfront_url)

    def test_junk(self):
        # WHEN
        self.init('webfronturl: f00')
        # THEN
        self.assertEqual('f00', self.p.webfront_url)

    def test_nominal(self):
        # WHEN
        self.init('webfronturl: http://somewhere.com')
        # THEN
        self.assertEqual("http://somewhere.com", self.p.webfront_url)


class Test_conf_settings_servernumber(Conf_settings_test_case):
    DEFAULT_VALUE = 0

    def test_missing(self):
        # WHEN
        self.init('')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.webfront_config_nr)

    def test_empty(self):
        # WHEN
        self.init('servernumber: ')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.webfront_config_nr)

    def test_junk(self):
        # WHEN
        self.init('servernumber: f00')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.webfront_config_nr)

    def test_negative(self):
        # WHEN
        self.init('servernumber: -5')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.webfront_config_nr)

    def test_0(self):
        # WHEN
        self.init('servernumber: 0')
        # THEN
        self.assertEqual(0, self.p.webfront_config_nr)

    def test_1(self):
        # WHEN
        self.init('servernumber: 1')
        # THEN
        self.assertEqual(1, self.p.webfront_config_nr)

    def test_8(self):
        # WHEN
        self.init('servernumber: 8')
        # THEN
        self.assertEqual(8, self.p.webfront_config_nr)

    def test_float(self):
        # WHEN
        self.init('servernumber: 0.5')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.webfront_config_nr)


class Test_conf_settings_keep_history(Conf_settings_test_case):

    def test_missing(self):
        # WHEN
        self.init('')
        # THEN
        self.assertTrue(self.p.keep_history)

    def test_empty(self):
        # WHEN
        self.init('keep_history: ')
        # THEN
        self.assertTrue(self.p.keep_history)

    def test_junk(self):
        # WHEN
        self.init('keep_history: f00')
        # THEN
        self.assertTrue(self.p.keep_history)

    def test_true(self):
        # WHEN
        self.init('keep_history: true')
        # THEN
        self.assertTrue(self.p.keep_history)

    def test_on(self):
        # WHEN
        self.init('keep_history: on')
        # THEN
        self.assertTrue(self.p.keep_history)

    def test_1(self):
        # WHEN
        self.init('keep_history: 1')
        # THEN
        self.assertTrue(self.p.keep_history)

    def test_yes(self):
        # WHEN
        self.init('keep_history: yes')
        # THEN
        self.assertTrue(self.p.keep_history)

    def test_false(self):
        # WHEN
        self.init('keep_history: false')
        # THEN
        self.assertFalse(self.p.keep_history)

    def test_off(self):
        # WHEN
        self.init('keep_history: off')
        # THEN
        self.assertFalse(self.p.keep_history)

    def test_0(self):
        # WHEN
        self.init('keep_history: 0')
        # THEN
        self.assertFalse(self.p.keep_history)

    def test_no(self):
        # WHEN
        self.init('keep_history: false')
        # THEN
        self.assertFalse(self.p.keep_history)


class Test_conf_settings_onemaponly(Conf_settings_test_case):

    def test_missing(self):
        # WHEN
        self.init('')
        # THEN
        self.assertFalse(self.p.onemaponly)

    def test_empty(self):
        # WHEN
        self.init('onemaponly: ')
        # THEN
        self.assertFalse(self.p.onemaponly)

    def test_junk(self):
        # WHEN
        self.init('onemaponly: f00')
        # THEN
        self.assertFalse(self.p.onemaponly)

    def test_true(self):
        # WHEN
        self.init('onemaponly: true')
        # THEN
        self.assertTrue(self.p.onemaponly)

    def test_on(self):
        # WHEN
        self.init('onemaponly: on')
        # THEN
        self.assertTrue(self.p.onemaponly)

    def test_1(self):
        # WHEN
        self.init('onemaponly: 1')
        # THEN
        self.assertTrue(self.p.onemaponly)

    def test_yes(self):
        # WHEN
        self.init('onemaponly: yes')
        # THEN
        self.assertTrue(self.p.onemaponly)

    def test_false(self):
        # WHEN
        self.init('onemaponly: false')
        # THEN
        self.assertFalse(self.p.onemaponly)

    def test_off(self):
        # WHEN
        self.init('onemaponly: off')
        # THEN
        self.assertFalse(self.p.onemaponly)

    def test_0(self):
        # WHEN
        self.init('onemaponly: 0')
        # THEN
        self.assertFalse(self.p.onemaponly)

    def test_no(self):
        # WHEN
        self.init('onemaponly: false')
        # THEN
        self.assertFalse(self.p.onemaponly)


class Test_conf_settings_minlevel(Conf_settings_test_case):
    DEFAULT_VALUE = 0

    def test_missing(self):
        # WHEN
        self.init('')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.minlevel)

    def test_empty(self):
        # WHEN
        self.init('minlevel: ')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.minlevel)

    def test_junk(self):
        # WHEN
        self.init('minlevel: f00')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.minlevel)

    def test_negative(self):
        # WHEN
        self.init('minlevel: -5')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.minlevel)

    def test_0(self):
        # WHEN
        self.init('minlevel: 0')
        # THEN
        self.assertEqual(0, self.p.minlevel)

    def test_1(self):
        # WHEN
        self.init('minlevel: 1')
        # THEN
        self.assertEqual(1, self.p.minlevel)

    def test_8(self):
        # WHEN
        self.init('minlevel: 8')
        # THEN
        self.assertEqual(0, self.p.minlevel)

    def test_float(self):
        # WHEN
        self.init('minlevel: 0.5')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.minlevel)


class Test_conf_settings_defaultskill(Conf_settings_test_case):
    DEFAULT_VALUE = 1000

    def test_missing(self):
        # WHEN
        self.init('')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.defaultskill)

    def test_empty(self):
        # WHEN
        self.init('defaultskill: ')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.defaultskill)

    def test_junk(self):
        # WHEN
        self.init('defaultskill: f00')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.defaultskill)

    def test_negative(self):
        # WHEN
        self.init('defaultskill: -5')
        # THEN
        self.assertEqual(-5, self.p.defaultskill)

    def test_0(self):
        # WHEN
        self.init('defaultskill: 0')
        # THEN
        self.assertEqual(0, self.p.defaultskill)

    def test_1(self):
        # WHEN
        self.init('defaultskill: 1')
        # THEN
        self.assertEqual(1, self.p.defaultskill)

    def test_8(self):
        # WHEN
        self.init('defaultskill: 8')
        # THEN
        self.assertEqual(8, self.p.defaultskill)

    def test_float(self):
        # WHEN
        self.init('defaultskill: 0.5')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.defaultskill)


class Test_conf_settings_Kfactor_high(Conf_settings_test_case):
    DEFAULT_VALUE = 16

    def test_missing(self):
        # WHEN
        self.init('')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.Kfactor_high)

    def test_empty(self):
        # WHEN
        self.init('Kfactor_high: ')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.Kfactor_high)

    def test_junk(self):
        # WHEN
        self.init('Kfactor_high: f00')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.Kfactor_high)

    def test_negative(self):
        # WHEN
        self.init('Kfactor_high: -5')
        # THEN
        self.assertEqual(-5, self.p.Kfactor_high)

    def test_0(self):
        # WHEN
        self.init('Kfactor_high: 0')
        # THEN
        self.assertEqual(0, self.p.Kfactor_high)

    def test_1(self):
        # WHEN
        self.init('Kfactor_high: 1')
        # THEN
        self.assertEqual(1, self.p.Kfactor_high)

    def test_8(self):
        # WHEN
        self.init('Kfactor_high: 8')
        # THEN
        self.assertEqual(8, self.p.Kfactor_high)

    def test_float(self):
        # WHEN
        self.init('Kfactor_high: 0.5')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.Kfactor_high)


class Test_conf_settings_Kfactor_low(Conf_settings_test_case):
    DEFAULT_VALUE = 4

    def test_missing(self):
        # WHEN
        self.init('')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.Kfactor_low)

    def test_empty(self):
        # WHEN
        self.init('Kfactor_low: ')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.Kfactor_low)

    def test_junk(self):
        # WHEN
        self.init('Kfactor_low: f00')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.Kfactor_low)

    def test_negative(self):
        # WHEN
        self.init('Kfactor_low: -5')
        # THEN
        self.assertEqual(-5, self.p.Kfactor_low)

    def test_0(self):
        # WHEN
        self.init('Kfactor_low: 0')
        # THEN
        self.assertEqual(0, self.p.Kfactor_low)

    def test_1(self):
        # WHEN
        self.init('Kfactor_low: 1')
        # THEN
        self.assertEqual(1, self.p.Kfactor_low)

    def test_8(self):
        # WHEN
        self.init('Kfactor_low: 8')
        # THEN
        self.assertEqual(8, self.p.Kfactor_low)

    def test_float(self):
        # WHEN
        self.init('Kfactor_low: 0.5')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.Kfactor_low)


class Test_conf_settings_Kswitch_confrontations(Conf_settings_test_case):
    DEFAULT_VALUE = 50

    def test_missing(self):
        # WHEN
        self.init('')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.Kswitch_confrontations)

    def test_empty(self):
        # WHEN
        self.init('Kswitch_confrontations: ')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.Kswitch_confrontations)

    def test_junk(self):
        # WHEN
        self.init('Kswitch_confrontations: f00')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.Kswitch_confrontations)

    def test_negative(self):
        # WHEN
        self.init('Kswitch_confrontations: -5')
        # THEN
        self.assertEqual(-5, self.p.Kswitch_confrontations)

    def test_0(self):
        # WHEN
        self.init('Kswitch_confrontations: 0')
        # THEN
        self.assertEqual(0, self.p.Kswitch_confrontations)

    def test_1(self):
        # WHEN
        self.init('Kswitch_confrontations: 1')
        # THEN
        self.assertEqual(1, self.p.Kswitch_confrontations)

    def test_8(self):
        # WHEN
        self.init('Kswitch_confrontations: 8')
        # THEN
        self.assertEqual(8, self.p.Kswitch_confrontations)

    def test_float(self):
        # WHEN
        self.init('Kswitch_confrontations: 0.5')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.Kswitch_confrontations)


class Test_conf_settings_steepness(Conf_settings_test_case):
    DEFAULT_VALUE = 600

    def test_missing(self):
        # WHEN
        self.init('')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.steepness)

    def test_empty(self):
        # WHEN
        self.init('steepness: ')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.steepness)

    def test_junk(self):
        # WHEN
        self.init('steepness: f00')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.steepness)

    def test_negative(self):
        # WHEN
        self.init('steepness: -5')
        # THEN
        self.assertEqual(-5, self.p.steepness)

    def test_0(self):
        # WHEN
        self.init('steepness: 0')
        # THEN
        self.assertEqual(0, self.p.steepness)

    def test_1(self):
        # WHEN
        self.init('steepness: 1')
        # THEN
        self.assertEqual(1, self.p.steepness)

    def test_8(self):
        # WHEN
        self.init('steepness: 8')
        # THEN
        self.assertEqual(8, self.p.steepness)

    def test_float(self):
        # WHEN
        self.init('steepness: 0.5')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.steepness)


class Test_conf_settings_suicide_penalty_percent(Conf_settings_test_case):
    DEFAULT_VALUE = 0.05

    def test_missing(self):
        # WHEN
        self.init('')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.suicide_penalty_percent)

    def test_empty(self):
        # WHEN
        self.init('suicide_penalty_percent: ')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.suicide_penalty_percent)

    def test_junk(self):
        # WHEN
        self.init('suicide_penalty_percent: f00')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.suicide_penalty_percent)

    def test_negative(self):
        # WHEN
        self.init('suicide_penalty_percent: -5')
        # THEN
        self.assertEqual(-5.0, self.p.suicide_penalty_percent)

    def test_0(self):
        # WHEN
        self.init('suicide_penalty_percent: 0')
        # THEN
        self.assertEqual(0.0, self.p.suicide_penalty_percent)

    def test_1(self):
        # WHEN
        self.init('suicide_penalty_percent: 1')
        # THEN
        self.assertEqual(1.0, self.p.suicide_penalty_percent)

    def test_8(self):
        # WHEN
        self.init('suicide_penalty_percent: 8')
        # THEN
        self.assertEqual(8.0, self.p.suicide_penalty_percent)

    def test_float(self):
        # WHEN
        self.init('suicide_penalty_percent: 0.5')
        # THEN
        self.assertEqual(0.5, self.p.suicide_penalty_percent)


class Test_conf_settings_tk_penalty_percent(Conf_settings_test_case):
    DEFAULT_VALUE = 0.1

    def test_missing(self):
        # WHEN
        self.init('')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.tk_penalty_percent)

    def test_empty(self):
        # WHEN
        self.init('tk_penalty_percent: ')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.tk_penalty_percent)

    def test_junk(self):
        # WHEN
        self.init('tk_penalty_percent: f00')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.tk_penalty_percent)

    def test_negative(self):
        # WHEN
        self.init('tk_penalty_percent: -5')
        # THEN
        self.assertEqual(-5.0, self.p.tk_penalty_percent)

    def test_0(self):
        # WHEN
        self.init('tk_penalty_percent: 0')
        # THEN
        self.assertEqual(0.0, self.p.tk_penalty_percent)

    def test_1(self):
        # WHEN
        self.init('tk_penalty_percent: 1')
        # THEN
        self.assertEqual(1.0, self.p.tk_penalty_percent)

    def test_8(self):
        # WHEN
        self.init('tk_penalty_percent: 8')
        # THEN
        self.assertEqual(8.0, self.p.tk_penalty_percent)

    def test_float(self):
        # WHEN
        self.init('tk_penalty_percent: 0.5')
        # THEN
        self.assertEqual(0.5, self.p.tk_penalty_percent)


class Test_conf_settings_assist_timespan(Conf_settings_test_case):
    DEFAULT_VALUE = 2

    def test_missing(self):
        # WHEN
        self.init('')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.assist_timespan)

    def test_empty(self):
        # WHEN
        self.init('assist_timespan: ')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.assist_timespan)

    def test_junk(self):
        # WHEN
        self.init('assist_timespan: f00')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.assist_timespan)

    def test_negative(self):
        # WHEN
        self.init('assist_timespan: -5')
        # THEN
        self.assertEqual(-5, self.p.assist_timespan)

    def test_0(self):
        # WHEN
        self.init('assist_timespan: 0')
        # THEN
        self.assertEqual(0, self.p.assist_timespan)

    def test_1(self):
        # WHEN
        self.init('assist_timespan: 1')
        # THEN
        self.assertEqual(1, self.p.assist_timespan)

    def test_8(self):
        # WHEN
        self.init('assist_timespan: 8')
        # THEN
        self.assertEqual(8, self.p.assist_timespan)

    def test_float(self):
        # WHEN
        self.init('assist_timespan: 0.5')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.assist_timespan)


class Test_conf_settings_damage_assist_release(Conf_settings_test_case):
    DEFAULT_VALUE = 10

    def test_missing(self):
        # WHEN
        self.init('')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.damage_assist_release)

    def test_empty(self):
        # WHEN
        self.init('damage_assist_release: ')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.damage_assist_release)

    def test_junk(self):
        # WHEN
        self.init('damage_assist_release: f00')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.damage_assist_release)

    def test_negative(self):
        # WHEN
        self.init('damage_assist_release: -5')
        # THEN
        self.assertEqual(-5, self.p.damage_assist_release)

    def test_0(self):
        # WHEN
        self.init('damage_assist_release: 0')
        # THEN
        self.assertEqual(0, self.p.damage_assist_release)

    def test_1(self):
        # WHEN
        self.init('damage_assist_release: 1')
        # THEN
        self.assertEqual(1, self.p.damage_assist_release)

    def test_8(self):
        # WHEN
        self.init('damage_assist_release: 8')
        # THEN
        self.assertEqual(8, self.p.damage_assist_release)

    def test_float(self):
        # WHEN
        self.init('damage_assist_release: 0.5')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.damage_assist_release)


class Test_conf_settings_prematch_maxtime(Conf_settings_test_case):
    DEFAULT_VALUE = 70

    def test_missing(self):
        # WHEN
        self.init('')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.prematch_maxtime)

    def test_empty(self):
        # WHEN
        self.init('prematch_maxtime: ')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.prematch_maxtime)

    def test_junk(self):
        # WHEN
        self.init('prematch_maxtime: f00')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.prematch_maxtime)

    def test_negative(self):
        # WHEN
        self.init('prematch_maxtime: -5')
        # THEN
        self.assertEqual(-5, self.p.prematch_maxtime)

    def test_0(self):
        # WHEN
        self.init('prematch_maxtime: 0')
        # THEN
        self.assertEqual(0, self.p.prematch_maxtime)

    def test_1(self):
        # WHEN
        self.init('prematch_maxtime: 1')
        # THEN
        self.assertEqual(1, self.p.prematch_maxtime)

    def test_8(self):
        # WHEN
        self.init('prematch_maxtime:8')
        # THEN
        self.assertEqual(8, self.p.prematch_maxtime)

    def test_float(self):
        # WHEN
        self.init('prematch_maxtime: 0.5')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.prematch_maxtime)


class Test_conf_settings_announce(Conf_settings_test_case):

    def test_missing(self):
        # WHEN
        self.init('')
        # THEN
        self.assertFalse(self.p.announce)

    def test_empty(self):
        # WHEN
        self.init('announce: ')
        # THEN
        self.assertFalse(self.p.announce)

    def test_junk(self):
        # WHEN
        self.init('announce: f00')
        # THEN
        self.assertFalse(self.p.announce)

    def test_true(self):
        # WHEN
        self.init('announce: true')
        # THEN
        self.assertTrue(self.p.announce)

    def test_on(self):
        # WHEN
        self.init('announce: on')
        # THEN
        self.assertTrue(self.p.announce)

    def test_1(self):
        # WHEN
        self.init('announce: 1')
        # THEN
        self.assertTrue(self.p.announce)

    def test_yes(self):
        # WHEN
        self.init('announce: yes')
        # THEN
        self.assertTrue(self.p.announce)

    def test_false(self):
        # WHEN
        self.init('announce: false')
        # THEN
        self.assertFalse(self.p.announce)

    def test_off(self):
        # WHEN
        self.init('announce: off')
        # THEN
        self.assertFalse(self.p.announce)

    def test_0(self):
        # WHEN
        self.init('announce: 0')
        # THEN
        self.assertFalse(self.p.announce)

    def test_no(self):
        # WHEN
        self.init('announce: false')
        # THEN
        self.assertFalse(self.p.announce)


class Test_conf_settings_keep_time(Conf_settings_test_case):

    def test_missing(self):
        # WHEN
        self.init('')
        # THEN
        self.assertTrue(self.p.keep_time)

    def test_empty(self):
        # WHEN
        self.init('keep_time: ')
        # THEN
        self.assertTrue(self.p.keep_time)

    def test_junk(self):
        # WHEN
        self.init('keep_time: f00')
        # THEN
        self.assertTrue(self.p.keep_time)

    def test_true(self):
        # WHEN
        self.init('keep_time: true')
        # THEN
        self.assertTrue(self.p.keep_time)

    def test_on(self):
        # WHEN
        self.init('keep_time: on')
        # THEN
        self.assertTrue(self.p.keep_time)

    def test_1(self):
        # WHEN
        self.init('keep_time: 1')
        # THEN
        self.assertTrue(self.p.keep_time)

    def test_yes(self):
        # WHEN
        self.init('keep_time: yes')
        # THEN
        self.assertTrue(self.p.keep_time)

    def test_false(self):
        # WHEN
        self.init('keep_time: false')
        # THEN
        self.assertFalse(self.p.keep_time)

    def test_off(self):
        # WHEN
        self.init('keep_time: off')
        # THEN
        self.assertFalse(self.p.keep_time)

    def test_0(self):
        # WHEN
        self.init('keep_time: 0')
        # THEN
        self.assertFalse(self.p.keep_time)

    def test_no(self):
        # WHEN
        self.init('keep_time: false')
        # THEN
        self.assertFalse(self.p.keep_time)


class Test_conf_settings_provisional_ranking(Conf_settings_test_case):

    def test_missing(self):
        # WHEN
        self.init('')
        # THEN
        self.assertTrue(self.p.provisional_ranking)

    def test_empty(self):
        # WHEN
        self.init('provisional_ranking: ')
        # THEN
        self.assertTrue(self.p.provisional_ranking)

    def test_junk(self):
        # WHEN
        self.init('provisional_ranking: f00')
        # THEN
        self.assertTrue(self.p.provisional_ranking)

    def test_true(self):
        # WHEN
        self.init('provisional_ranking: true')
        # THEN
        self.assertTrue(self.p.provisional_ranking)

    def test_on(self):
        # WHEN
        self.init('provisional_ranking: on')
        # THEN
        self.assertTrue(self.p.provisional_ranking)

    def test_1(self):
        # WHEN
        self.init('provisional_ranking: 1')
        # THEN
        self.assertTrue(self.p.provisional_ranking)

    def test_yes(self):
        # WHEN
        self.init('provisional_ranking: yes')
        # THEN
        self.assertTrue(self.p.provisional_ranking)

    def test_false(self):
        # WHEN
        self.init('provisional_ranking: false')
        # THEN
        self.assertFalse(self.p.provisional_ranking)

    def test_off(self):
        # WHEN
        self.init('provisional_ranking: off')
        # THEN
        self.assertFalse(self.p.provisional_ranking)

    def test_0(self):
        # WHEN
        self.init('provisional_ranking: 0')
        # THEN
        self.assertFalse(self.p.provisional_ranking)

    def test_no(self):
        # WHEN
        self.init('provisional_ranking: false')
        # THEN
        self.assertFalse(self.p.provisional_ranking)


class Test_conf_settings_auto_correct(Conf_settings_test_case):

    def test_missing(self):
        # WHEN
        self.init('')
        # THEN
        self.assertTrue(self.p.auto_correct)

    def test_empty(self):
        # WHEN
        self.init('auto_correct: ')
        # THEN
        self.assertTrue(self.p.auto_correct)

    def test_junk(self):
        # WHEN
        self.init('auto_correct: f00')
        # THEN
        self.assertTrue(self.p.auto_correct)

    def test_true(self):
        # WHEN
        self.init('auto_correct: true')
        # THEN
        self.assertTrue(self.p.auto_correct)

    def test_on(self):
        # WHEN
        self.init('auto_correct: on')
        # THEN
        self.assertTrue(self.p.auto_correct)

    def test_1(self):
        # WHEN
        self.init('auto_correct: 1')
        # THEN
        self.assertTrue(self.p.auto_correct)

    def test_yes(self):
        # WHEN
        self.init('auto_correct: yes')
        # THEN
        self.assertTrue(self.p.auto_correct)

    def test_false(self):
        # WHEN
        self.init('auto_correct: false')
        # THEN
        self.assertFalse(self.p.auto_correct)

    def test_off(self):
        # WHEN
        self.init('auto_correct: off')
        # THEN
        self.assertFalse(self.p.auto_correct)

    def test_0(self):
        # WHEN
        self.init('auto_correct: 0')
        # THEN
        self.assertFalse(self.p.auto_correct)

    def test_no(self):
        # WHEN
        self.init('auto_correct: false')
        # THEN
        self.assertFalse(self.p.auto_correct)


class Test_conf_settings_auto_purge(Conf_settings_test_case):

    def test_missing(self):
        # WHEN
        self.init('')
        # THEN
        self.assertFalse(self.p.auto_purge)

    def test_empty(self):
        # WHEN
        self.init('auto_purge: ')
        # THEN
        self.assertFalse(self.p.auto_purge)

    def test_junk(self):
        # WHEN
        self.init('auto_purge: f00')
        # THEN
        self.assertFalse(self.p.auto_purge)

    def test_true(self):
        # WHEN
        self.init('auto_purge: true')
        # THEN
        self.assertTrue(self.p.auto_purge)

    def test_on(self):
        # WHEN
        self.init('auto_purge: on')
        # THEN
        self.assertTrue(self.p.auto_purge)

    def test_1(self):
        # WHEN
        self.init('auto_purge: 1')
        # THEN
        self.assertTrue(self.p.auto_purge)

    def test_yes(self):
        # WHEN
        self.init('auto_purge: yes')
        # THEN
        self.assertTrue(self.p.auto_purge)

    def test_false(self):
        # WHEN
        self.init('auto_purge: false')
        # THEN
        self.assertFalse(self.p.auto_purge)

    def test_off(self):
        # WHEN
        self.init('auto_purge: off')
        # THEN
        self.assertFalse(self.p.auto_purge)

    def test_0(self):
        # WHEN
        self.init('auto_purge: 0')
        # THEN
        self.assertFalse(self.p.auto_purge)

    def test_no(self):
        # WHEN
        self.init('auto_purge: false')
        # THEN
        self.assertFalse(self.p.auto_purge)
        
        
class Conf_tables_test_case(XlrstatsTestCase):

    def init(self, option_snippet=''):
        """
        Load the XLRstats plugin with an empty config file except for the option_snippet given as a parameter which will
        be injected in the "tables" section.
        Then call the plugin onLoadConfig method.
        """
        self.conf.loadFromString(r"""
[tables]
%s
""" % option_snippet)
        self.p.onLoadConfig()


class Test_conf_tables_playerstats(Conf_tables_test_case):
    DEFAULT_VALUE = 'xlr_playerstats'

    def test_missing(self):
        # WHEN
        self.init('')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.playerstats_table)
        self.assertTrue(self.p._defaultTableNames)

    def test_empty(self):
        # WHEN
        self.init('playerstats: ')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.playerstats_table)
        self.assertTrue(self.p._defaultTableNames)

    def test_nominal(self):
        # WHEN
        self.init('playerstats: f00')
        # THEN
        self.assertEqual('f00', self.p.playerstats_table)
        self.assertFalse(self.p._defaultTableNames)


class Test_conf_tables_weaponstats(Conf_tables_test_case):
    DEFAULT_VALUE = 'xlr_weaponstats'

    def test_missing(self):
        # WHEN
        self.init('')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.weaponstats_table)
        self.assertTrue(self.p._defaultTableNames)

    def test_empty(self):
        # WHEN
        self.init('weaponstats: ')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.weaponstats_table)
        self.assertTrue(self.p._defaultTableNames)

    def test_nominal(self):
        # WHEN
        self.init('weaponstats: f00')
        # THEN
        self.assertEqual('f00', self.p.weaponstats_table)
        self.assertFalse(self.p._defaultTableNames)


class Test_conf_tables_weaponusage(Conf_tables_test_case):
    DEFAULT_VALUE = 'xlr_weaponusage'

    def test_missing(self):
        # WHEN
        self.init('')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.weaponusage_table)
        self.assertTrue(self.p._defaultTableNames)

    def test_empty(self):
        # WHEN
        self.init('weaponusage: ')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.weaponusage_table)
        self.assertTrue(self.p._defaultTableNames)

    def test_nominal(self):
        # WHEN
        self.init('weaponusage: f00')
        # THEN
        self.assertEqual('f00', self.p.weaponusage_table)
        self.assertFalse(self.p._defaultTableNames)


class Test_conf_tables_bodyparts(Conf_tables_test_case):
    DEFAULT_VALUE = 'xlr_bodyparts'

    def test_missing(self):
        # WHEN
        self.init('')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.bodyparts_table)
        self.assertTrue(self.p._defaultTableNames)

    def test_empty(self):
        # WHEN
        self.init('bodyparts: ')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.bodyparts_table)
        self.assertTrue(self.p._defaultTableNames)

    def test_nominal(self):
        # WHEN
        self.init('bodyparts: f00')
        # THEN
        self.assertEqual('f00', self.p.bodyparts_table)
        self.assertFalse(self.p._defaultTableNames)


class Test_conf_tables_playerbody(Conf_tables_test_case):
    DEFAULT_VALUE = 'xlr_playerbody'

    def test_missing(self):
        # WHEN
        self.init('')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.playerbody_table)
        self.assertTrue(self.p._defaultTableNames)

    def test_empty(self):
        # WHEN
        self.init('playerbody: ')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.playerbody_table)
        self.assertTrue(self.p._defaultTableNames)

    def test_nominal(self):
        # WHEN
        self.init('playerbody: f00')
        # THEN
        self.assertEqual('f00', self.p.playerbody_table)
        self.assertFalse(self.p._defaultTableNames)


class Test_conf_tables_opponents(Conf_tables_test_case):
    DEFAULT_VALUE = 'xlr_opponents'

    def test_missing(self):
        # WHEN
        self.init('')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.opponents_table)
        self.assertTrue(self.p._defaultTableNames)

    def test_empty(self):
        # WHEN
        self.init('opponents: ')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.opponents_table)
        self.assertTrue(self.p._defaultTableNames)

    def test_nominal(self):
        # WHEN
        self.init('opponents: f00')
        # THEN
        self.assertEqual('f00', self.p.opponents_table)
        self.assertFalse(self.p._defaultTableNames)


class Test_conf_tables_mapstats(Conf_tables_test_case):
    DEFAULT_VALUE = 'xlr_mapstats'

    def test_missing(self):
        # WHEN
        self.init('')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.mapstats_table)
        self.assertTrue(self.p._defaultTableNames)

    def test_empty(self):
        # WHEN
        self.init('mapstats: ')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.mapstats_table)
        self.assertTrue(self.p._defaultTableNames)

    def test_nominal(self):
        # WHEN
        self.init('mapstats: f00')
        # THEN
        self.assertEqual('f00', self.p.mapstats_table)
        self.assertFalse(self.p._defaultTableNames)


class Test_conf_tables_playermaps(Conf_tables_test_case):
    DEFAULT_VALUE = 'xlr_playermaps'

    def test_missing(self):
        # WHEN
        self.init('')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.playermaps_table)
        self.assertTrue(self.p._defaultTableNames)

    def test_empty(self):
        # WHEN
        self.init('playermaps: ')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.playermaps_table)
        self.assertTrue(self.p._defaultTableNames)

    def test_nominal(self):
        # WHEN
        self.init('playermaps: f00')
        # THEN
        self.assertEqual('f00', self.p.playermaps_table)
        self.assertFalse(self.p._defaultTableNames)


class Test_conf_tables_actionstats(Conf_tables_test_case):
    DEFAULT_VALUE = 'xlr_actionstats'

    def test_missing(self):
        # WHEN
        self.init('')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.actionstats_table)
        self.assertTrue(self.p._defaultTableNames)

    def test_empty(self):
        # WHEN
        self.init('actionstats: ')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.actionstats_table)
        self.assertTrue(self.p._defaultTableNames)

    def test_nominal(self):
        # WHEN
        self.init('actionstats: f00')
        # THEN
        self.assertEqual('f00', self.p.actionstats_table)
        self.assertFalse(self.p._defaultTableNames)


class Test_conf_tables_playeractions(Conf_tables_test_case):
    DEFAULT_VALUE = 'xlr_playeractions'

    def test_missing(self):
        # WHEN
        self.init('')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.playeractions_table)
        self.assertTrue(self.p._defaultTableNames)

    def test_empty(self):
        # WHEN
        self.init('playeractions: ')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.playeractions_table)
        self.assertTrue(self.p._defaultTableNames)

    def test_nominal(self):
        # WHEN
        self.init('playeractions: f00')
        # THEN
        self.assertEqual('f00', self.p.playeractions_table)
        self.assertFalse(self.p._defaultTableNames)


class Test_conf_tables_history_monthly(Conf_tables_test_case):
    DEFAULT_VALUE = 'xlr_history_monthly'

    def test_missing(self):
        # WHEN
        self.init('')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.history_monthly_table)
        self.assertTrue(self.p._defaultTableNames)

    def test_empty(self):
        # WHEN
        self.init('history_monthly: ')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.history_monthly_table)
        self.assertTrue(self.p._defaultTableNames)

    def test_nominal(self):
        # WHEN
        self.init('history_monthly: f00')
        # THEN
        self.assertEqual('f00', self.p.history_monthly_table)
        self.assertFalse(self.p._defaultTableNames)


class Test_conf_tables_history_weekly(Conf_tables_test_case):
    DEFAULT_VALUE = 'xlr_history_weekly'

    def test_missing(self):
        # WHEN
        self.init('')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.history_weekly_table)
        self.assertTrue(self.p._defaultTableNames)

    def test_empty(self):
        # WHEN
        self.init('history_weekly: ')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.history_weekly_table)
        self.assertTrue(self.p._defaultTableNames)

    def test_nominal(self):
        # WHEN
        self.init('history_weekly: f00')
        # THEN
        self.assertEqual('f00', self.p.history_weekly_table)
        self.assertFalse(self.p._defaultTableNames)


class Test_conf_tables_ctime(Conf_tables_test_case):
    DEFAULT_VALUE = 'ctime'

    def test_missing(self):
        # WHEN
        self.init('')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.ctime_table)
        self.assertTrue(self.p._defaultTableNames)

    def test_empty(self):
        # WHEN
        self.init('ctime: ')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.ctime_table)
        self.assertTrue(self.p._defaultTableNames)

    def test_nominal(self):
        # WHEN
        self.init('ctime: f00')
        # THEN
        self.assertEqual('f00', self.p.ctime_table)
        self.assertFalse(self.p._defaultTableNames)

