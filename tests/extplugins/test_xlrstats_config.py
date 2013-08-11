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
import logging
import os
from b3.config import XmlConfigParser
from b3.extplugins.xlrstats import XlrstatsPlugin, __file__ as xlrstats__file__
from tests import B3TestCase

DEFAULT_XLRSTATS_CONFIG_FILE = os.path.join(os.path.dirname(xlrstats__file__), 'conf/xlrstats.xml')


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
        self.conf = XmlConfigParser()  # It is an empty config but we can fill it up later

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
        self.conf.setXml(r"""
        <configuration plugin="xlrstats">
        </configuration>
        """)
        # WHEN
        self.p.onLoadConfig()
        # THEN
        self.assertFalse(self.p.silent)
        self.assertTrue(self.p.hide_bots)
        self.assertTrue(self.p.exclude_bots)
        self.assertEqual(3, self.p.minPlayers)
        self.assertEqual('', self.p.webfrontUrl)
        self.assertEqual(0, self.p.webfrontConfigNr)
        self.assertTrue(self.p.keep_history)
        self.assertFalse(self.p.onemaponly)
        self.assertEqual(1, self.p.minlevel)
        self.assertEqual(1000, self.p.defaultskill)
        self.assertEqual(16, self.p.Kfactor_high)
        self.assertEqual(4, self.p.Kfactor_low)
        self.assertEqual(100, self.p.Kswitch_kills)
        self.assertEqual(600, self.p.steepness)
        self.assertEqual(0.05, self.p.suicide_penalty_percent)
        self.assertEqual(0.1, self.p.tk_penalty_percent)
        self.assertEqual(2, self.p.assist_timespan)
        self.assertEqual(10, self.p.damage_assist_release)
        self.assertEqual(70, self.p.prematch_maxtime)
        self.assertFalse(self.p.announce)
        self.assertTrue(self.p.keep_time)
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
        self.assertEqual(3, self.p.minPlayers)
        self.assertEqual('', self.p.webfrontUrl)
        self.assertEqual(0, self.p.webfrontConfigNr)
        self.assertTrue(self.p.keep_history)
        self.assertFalse(self.p.onemaponly)
        self.assertEqual(0, self.p.minlevel)
        self.assertEqual(1000, self.p.defaultskill)
        self.assertEqual(16, self.p.Kfactor_high)
        self.assertEqual(4, self.p.Kfactor_low)
        self.assertEqual(100, self.p.Kswitch_kills)
        self.assertEqual(600, self.p.steepness)
        self.assertEqual(0.05, self.p.suicide_penalty_percent)
        self.assertEqual(0.1, self.p.tk_penalty_percent)
        self.assertEqual(2, self.p.assist_timespan)
        self.assertEqual(10, self.p.damage_assist_release)
        self.assertEqual(70, self.p.prematch_maxtime)
        self.assertFalse(self.p.announce)
        self.assertTrue(self.p.keep_time)
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

    def init(self, xml_snippet=''):
        """
        Load the XLRstats plugin with an empty config file except for the xml_snippet given as a parameter which will
        be injected in the "settings" section.
        Then call the plugin onLoadConfig method.
        """
        self.conf.setXml(r"""
<configuration plugin="xlrstats">
    <settings name="settings">
        %s
    </settings>
</configuration>
""" % xml_snippet)
        self.p.onLoadConfig()


class Test_conf_settings_silent(Conf_settings_test_case):

    def test_missing(self):
        # WHEN
        self.init('')
        # THEN
        self.assertFalse(self.p.silent)

    def test_empty(self):
        # WHEN
        self.init('<set name="silent"></set>')
        # THEN
        self.assertFalse(self.p.silent)

    def test_junk(self):
        # WHEN
        self.init('<set name="silent">f00</set>')
        # THEN
        self.assertFalse(self.p.silent)

    def test_true(self):
        # WHEN
        self.init('<set name="silent">true</set>')
        # THEN
        self.assertTrue(self.p.silent)

    def test_on(self):
        # WHEN
        self.init('<set name="silent">on</set>')
        # THEN
        self.assertTrue(self.p.silent)

    def test_1(self):
        # WHEN
        self.init('<set name="silent">1</set>')
        # THEN
        self.assertTrue(self.p.silent)

    def test_yes(self):
        # WHEN
        self.init('<set name="silent">yes</set>')
        # THEN
        self.assertTrue(self.p.silent)

    def test_false(self):
        # WHEN
        self.init('<set name="silent">false</set>')
        # THEN
        self.assertFalse(self.p.silent)

    def test_off(self):
        # WHEN
        self.init('<set name="silent">off</set>')
        # THEN
        self.assertFalse(self.p.silent)

    def test_0(self):
        # WHEN
        self.init('<set name="silent">0</set>')
        # THEN
        self.assertFalse(self.p.silent)

    def test_no(self):
        # WHEN
        self.init('<set name="silent">false</set>')
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
        self.init('<set name="hide_bots"></set>')
        # THEN
        self.assertTrue(self.p.hide_bots)

    def test_junk(self):
        # WHEN
        self.init('<set name="hide_bots">f00</set>')
        # THEN
        self.assertTrue(self.p.hide_bots)

    def test_true(self):
        # WHEN
        self.init('<set name="hide_bots">true</set>')
        # THEN
        self.assertTrue(self.p.hide_bots)

    def test_on(self):
        # WHEN
        self.init('<set name="hide_bots">on</set>')
        # THEN
        self.assertTrue(self.p.hide_bots)

    def test_1(self):
        # WHEN
        self.init('<set name="hide_bots">1</set>')
        # THEN
        self.assertTrue(self.p.hide_bots)

    def test_yes(self):
        # WHEN
        self.init('<set name="hide_bots">yes</set>')
        # THEN
        self.assertTrue(self.p.hide_bots)

    def test_false(self):
        # WHEN
        self.init('<set name="hide_bots">false</set>')
        # THEN
        self.assertFalse(self.p.hide_bots)

    def test_off(self):
        # WHEN
        self.init('<set name="hide_bots">off</set>')
        # THEN
        self.assertFalse(self.p.hide_bots)

    def test_0(self):
        # WHEN
        self.init('<set name="hide_bots">0</set>')
        # THEN
        self.assertFalse(self.p.hide_bots)

    def test_no(self):
        # WHEN
        self.init('<set name="hide_bots">false</set>')
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
        self.init('<set name="exclude_bots"></set>')
        # THEN
        self.assertTrue(self.p.exclude_bots)

    def test_junk(self):
        # WHEN
        self.init('<set name="exclude_bots">f00</set>')
        # THEN
        self.assertTrue(self.p.exclude_bots)

    def test_true(self):
        # WHEN
        self.init('<set name="exclude_bots">true</set>')
        # THEN
        self.assertTrue(self.p.exclude_bots)

    def test_on(self):
        # WHEN
        self.init('<set name="exclude_bots">on</set>')
        # THEN
        self.assertTrue(self.p.exclude_bots)

    def test_1(self):
        # WHEN
        self.init('<set name="exclude_bots">1</set>')
        # THEN
        self.assertTrue(self.p.exclude_bots)

    def test_yes(self):
        # WHEN
        self.init('<set name="exclude_bots">yes</set>')
        # THEN
        self.assertTrue(self.p.exclude_bots)

    def test_false(self):
        # WHEN
        self.init('<set name="exclude_bots">false</set>')
        # THEN
        self.assertFalse(self.p.exclude_bots)

    def test_off(self):
        # WHEN
        self.init('<set name="exclude_bots">off</set>')
        # THEN
        self.assertFalse(self.p.exclude_bots)

    def test_0(self):
        # WHEN
        self.init('<set name="exclude_bots">0</set>')
        # THEN
        self.assertFalse(self.p.exclude_bots)

    def test_no(self):
        # WHEN
        self.init('<set name="exclude_bots">false</set>')
        # THEN
        self.assertFalse(self.p.exclude_bots)


class Test_conf_settings_minPlayers(Conf_settings_test_case):
    DEFAULT_VALUE = 3

    def test_missing(self):
        # WHEN
        self.init('')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.minPlayers)

    def test_empty(self):
        # WHEN
        self.init('<set name="minplayers"></set>')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.minPlayers)

    def test_junk(self):
        # WHEN
        self.init('<set name="minplayers">f00</set>')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.minPlayers)

    def test_negative(self):
        # WHEN
        self.init('<set name="minplayers">-5</set>')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.minPlayers)

    def test_0(self):
        # WHEN
        self.init('<set name="minplayers">0</set>')
        # THEN
        self.assertEqual(0, self.p.minPlayers)

    def test_1(self):
        # WHEN
        self.init('<set name="minplayers">1</set>')
        # THEN
        self.assertEqual(1, self.p.minPlayers)

    def test_8(self):
        # WHEN
        self.init('<set name="minplayers">8</set>')
        # THEN
        self.assertEqual(8, self.p.minPlayers)

    def test_float(self):
        # WHEN
        self.init('<set name="minplayers">0.5</set>')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.minPlayers)


class Test_conf_settings_webfronturl(Conf_settings_test_case):

    def test_missing(self):
        # WHEN
        self.init('')
        # THEN
        self.assertEqual('', self.p.webfrontUrl)

    def test_empty(self):
        # WHEN
        self.init('<set name="webfronturl"></set>')
        # THEN
        self.assertEqual('', self.p.webfrontUrl)

    def test_junk(self):
        # WHEN
        self.init('<set name="webfronturl">f00</set>')
        # THEN
        self.assertEqual('f00', self.p.webfrontUrl)

    def test_nominal(self):
        # WHEN
        self.init('<set name="webfronturl">http://somewhere.com</set>')
        # THEN
        self.assertEqual("http://somewhere.com", self.p.webfrontUrl)


class Test_conf_settings_servernumber(Conf_settings_test_case):
    DEFAULT_VALUE = 0

    def test_missing(self):
        # WHEN
        self.init('')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.webfrontConfigNr)

    def test_empty(self):
        # WHEN
        self.init('<set name="servernumber"></set>')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.webfrontConfigNr)

    def test_junk(self):
        # WHEN
        self.init('<set name="servernumber">f00</set>')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.webfrontConfigNr)

    def test_negative(self):
        # WHEN
        self.init('<set name="servernumber">-5</set>')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.webfrontConfigNr)

    def test_0(self):
        # WHEN
        self.init('<set name="servernumber">0</set>')
        # THEN
        self.assertEqual(0, self.p.webfrontConfigNr)

    def test_1(self):
        # WHEN
        self.init('<set name="servernumber">1</set>')
        # THEN
        self.assertEqual(1, self.p.webfrontConfigNr)

    def test_8(self):
        # WHEN
        self.init('<set name="servernumber">8</set>')
        # THEN
        self.assertEqual(8, self.p.webfrontConfigNr)

    def test_float(self):
        # WHEN
        self.init('<set name="servernumber">0.5</set>')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.webfrontConfigNr)


class Test_conf_settings_keep_history(Conf_settings_test_case):

    def test_missing(self):
        # WHEN
        self.init('')
        # THEN
        self.assertTrue(self.p.keep_history)

    def test_empty(self):
        # WHEN
        self.init('<set name="keep_history"></set>')
        # THEN
        self.assertTrue(self.p.keep_history)

    def test_junk(self):
        # WHEN
        self.init('<set name="keep_history">f00</set>')
        # THEN
        self.assertTrue(self.p.keep_history)

    def test_true(self):
        # WHEN
        self.init('<set name="keep_history">true</set>')
        # THEN
        self.assertTrue(self.p.keep_history)

    def test_on(self):
        # WHEN
        self.init('<set name="keep_history">on</set>')
        # THEN
        self.assertTrue(self.p.keep_history)

    def test_1(self):
        # WHEN
        self.init('<set name="keep_history">1</set>')
        # THEN
        self.assertTrue(self.p.keep_history)

    def test_yes(self):
        # WHEN
        self.init('<set name="keep_history">yes</set>')
        # THEN
        self.assertTrue(self.p.keep_history)

    def test_false(self):
        # WHEN
        self.init('<set name="keep_history">false</set>')
        # THEN
        self.assertFalse(self.p.keep_history)

    def test_off(self):
        # WHEN
        self.init('<set name="keep_history">off</set>')
        # THEN
        self.assertFalse(self.p.keep_history)

    def test_0(self):
        # WHEN
        self.init('<set name="keep_history">0</set>')
        # THEN
        self.assertFalse(self.p.keep_history)

    def test_no(self):
        # WHEN
        self.init('<set name="keep_history">false</set>')
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
        self.init('<set name="onemaponly"></set>')
        # THEN
        self.assertFalse(self.p.onemaponly)

    def test_junk(self):
        # WHEN
        self.init('<set name="onemaponly">f00</set>')
        # THEN
        self.assertFalse(self.p.onemaponly)

    def test_true(self):
        # WHEN
        self.init('<set name="onemaponly">true</set>')
        # THEN
        self.assertTrue(self.p.onemaponly)

    def test_on(self):
        # WHEN
        self.init('<set name="onemaponly">on</set>')
        # THEN
        self.assertTrue(self.p.onemaponly)

    def test_1(self):
        # WHEN
        self.init('<set name="onemaponly">1</set>')
        # THEN
        self.assertTrue(self.p.onemaponly)

    def test_yes(self):
        # WHEN
        self.init('<set name="onemaponly">yes</set>')
        # THEN
        self.assertTrue(self.p.onemaponly)

    def test_false(self):
        # WHEN
        self.init('<set name="onemaponly">false</set>')
        # THEN
        self.assertFalse(self.p.onemaponly)

    def test_off(self):
        # WHEN
        self.init('<set name="onemaponly">off</set>')
        # THEN
        self.assertFalse(self.p.onemaponly)

    def test_0(self):
        # WHEN
        self.init('<set name="onemaponly">0</set>')
        # THEN
        self.assertFalse(self.p.onemaponly)

    def test_no(self):
        # WHEN
        self.init('<set name="onemaponly">false</set>')
        # THEN
        self.assertFalse(self.p.onemaponly)


class Test_conf_settings_minlevel(Conf_settings_test_case):
    DEFAULT_VALUE = 1

    def test_missing(self):
        # WHEN
        self.init('')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.minlevel)

    def test_empty(self):
        # WHEN
        self.init('<set name="minlevel"></set>')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.minlevel)

    def test_junk(self):
        # WHEN
        self.init('<set name="minlevel">f00</set>')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.minlevel)

    def test_negative(self):
        # WHEN
        self.init('<set name="minlevel">-5</set>')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.minlevel)

    def test_0(self):
        # WHEN
        self.init('<set name="minlevel">0</set>')
        # THEN
        self.assertEqual(0, self.p.minlevel)

    def test_1(self):
        # WHEN
        self.init('<set name="minlevel">1</set>')
        # THEN
        self.assertEqual(1, self.p.minlevel)

    def test_8(self):
        # WHEN
        self.init('<set name="minlevel">8</set>')
        # THEN
        self.assertEqual(8, self.p.minlevel)

    def test_float(self):
        # WHEN
        self.init('<set name="minlevel">0.5</set>')
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
        self.init('<set name="defaultskill"></set>')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.defaultskill)

    def test_junk(self):
        # WHEN
        self.init('<set name="defaultskill">f00</set>')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.defaultskill)

    def test_negative(self):
        # WHEN
        self.init('<set name="defaultskill">-5</set>')
        # THEN
        self.assertEqual(-5, self.p.defaultskill)

    def test_0(self):
        # WHEN
        self.init('<set name="defaultskill">0</set>')
        # THEN
        self.assertEqual(0, self.p.defaultskill)

    def test_1(self):
        # WHEN
        self.init('<set name="defaultskill">1</set>')
        # THEN
        self.assertEqual(1, self.p.defaultskill)

    def test_8(self):
        # WHEN
        self.init('<set name="defaultskill">8</set>')
        # THEN
        self.assertEqual(8, self.p.defaultskill)

    def test_float(self):
        # WHEN
        self.init('<set name="defaultskill">0.5</set>')
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
        self.init('<set name="Kfactor_high"></set>')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.Kfactor_high)

    def test_junk(self):
        # WHEN
        self.init('<set name="Kfactor_high">f00</set>')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.Kfactor_high)

    def test_negative(self):
        # WHEN
        self.init('<set name="Kfactor_high">-5</set>')
        # THEN
        self.assertEqual(-5, self.p.Kfactor_high)

    def test_0(self):
        # WHEN
        self.init('<set name="Kfactor_high">0</set>')
        # THEN
        self.assertEqual(0, self.p.Kfactor_high)

    def test_1(self):
        # WHEN
        self.init('<set name="Kfactor_high">1</set>')
        # THEN
        self.assertEqual(1, self.p.Kfactor_high)

    def test_8(self):
        # WHEN
        self.init('<set name="Kfactor_high">8</set>')
        # THEN
        self.assertEqual(8, self.p.Kfactor_high)

    def test_float(self):
        # WHEN
        self.init('<set name="Kfactor_high">0.5</set>')
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
        self.init('<set name="Kfactor_low"></set>')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.Kfactor_low)

    def test_junk(self):
        # WHEN
        self.init('<set name="Kfactor_low">f00</set>')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.Kfactor_low)

    def test_negative(self):
        # WHEN
        self.init('<set name="Kfactor_low">-5</set>')
        # THEN
        self.assertEqual(-5, self.p.Kfactor_low)

    def test_0(self):
        # WHEN
        self.init('<set name="Kfactor_low">0</set>')
        # THEN
        self.assertEqual(0, self.p.Kfactor_low)

    def test_1(self):
        # WHEN
        self.init('<set name="Kfactor_low">1</set>')
        # THEN
        self.assertEqual(1, self.p.Kfactor_low)

    def test_8(self):
        # WHEN
        self.init('<set name="Kfactor_low">8</set>')
        # THEN
        self.assertEqual(8, self.p.Kfactor_low)

    def test_float(self):
        # WHEN
        self.init('<set name="Kfactor_low">0.5</set>')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.Kfactor_low)


class Test_conf_settings_Kswitch_kills(Conf_settings_test_case):
    DEFAULT_VALUE = 100

    def test_missing(self):
        # WHEN
        self.init('')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.Kswitch_kills)

    def test_empty(self):
        # WHEN
        self.init('<set name="Kswitch_kills"></set>')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.Kswitch_kills)

    def test_junk(self):
        # WHEN
        self.init('<set name="Kswitch_kills">f00</set>')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.Kswitch_kills)

    def test_negative(self):
        # WHEN
        self.init('<set name="Kswitch_kills">-5</set>')
        # THEN
        self.assertEqual(-5, self.p.Kswitch_kills)

    def test_0(self):
        # WHEN
        self.init('<set name="Kswitch_kills">0</set>')
        # THEN
        self.assertEqual(0, self.p.Kswitch_kills)

    def test_1(self):
        # WHEN
        self.init('<set name="Kswitch_kills">1</set>')
        # THEN
        self.assertEqual(1, self.p.Kswitch_kills)

    def test_8(self):
        # WHEN
        self.init('<set name="Kswitch_kills">8</set>')
        # THEN
        self.assertEqual(8, self.p.Kswitch_kills)

    def test_float(self):
        # WHEN
        self.init('<set name="Kswitch_kills">0.5</set>')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.Kswitch_kills)


class Test_conf_settings_steepness(Conf_settings_test_case):
    DEFAULT_VALUE = 600

    def test_missing(self):
        # WHEN
        self.init('')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.steepness)

    def test_empty(self):
        # WHEN
        self.init('<set name="steepness"></set>')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.steepness)

    def test_junk(self):
        # WHEN
        self.init('<set name="steepness">f00</set>')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.steepness)

    def test_negative(self):
        # WHEN
        self.init('<set name="steepness">-5</set>')
        # THEN
        self.assertEqual(-5, self.p.steepness)

    def test_0(self):
        # WHEN
        self.init('<set name="steepness">0</set>')
        # THEN
        self.assertEqual(0, self.p.steepness)

    def test_1(self):
        # WHEN
        self.init('<set name="steepness">1</set>')
        # THEN
        self.assertEqual(1, self.p.steepness)

    def test_8(self):
        # WHEN
        self.init('<set name="steepness">8</set>')
        # THEN
        self.assertEqual(8, self.p.steepness)

    def test_float(self):
        # WHEN
        self.init('<set name="steepness">0.5</set>')
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
        self.init('<set name="suicide_penalty_percent"></set>')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.suicide_penalty_percent)

    def test_junk(self):
        # WHEN
        self.init('<set name="suicide_penalty_percent">f00</set>')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.suicide_penalty_percent)

    def test_negative(self):
        # WHEN
        self.init('<set name="suicide_penalty_percent">-5</set>')
        # THEN
        self.assertEqual(-5.0, self.p.suicide_penalty_percent)

    def test_0(self):
        # WHEN
        self.init('<set name="suicide_penalty_percent">0</set>')
        # THEN
        self.assertEqual(0.0, self.p.suicide_penalty_percent)

    def test_1(self):
        # WHEN
        self.init('<set name="suicide_penalty_percent">1</set>')
        # THEN
        self.assertEqual(1.0, self.p.suicide_penalty_percent)

    def test_8(self):
        # WHEN
        self.init('<set name="suicide_penalty_percent">8</set>')
        # THEN
        self.assertEqual(8.0, self.p.suicide_penalty_percent)

    def test_float(self):
        # WHEN
        self.init('<set name="suicide_penalty_percent">0.5</set>')
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
        self.init('<set name="tk_penalty_percent"></set>')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.tk_penalty_percent)

    def test_junk(self):
        # WHEN
        self.init('<set name="tk_penalty_percent">f00</set>')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.tk_penalty_percent)

    def test_negative(self):
        # WHEN
        self.init('<set name="tk_penalty_percent">-5</set>')
        # THEN
        self.assertEqual(-5.0, self.p.tk_penalty_percent)

    def test_0(self):
        # WHEN
        self.init('<set name="tk_penalty_percent">0</set>')
        # THEN
        self.assertEqual(0.0, self.p.tk_penalty_percent)

    def test_1(self):
        # WHEN
        self.init('<set name="tk_penalty_percent">1</set>')
        # THEN
        self.assertEqual(1.0, self.p.tk_penalty_percent)

    def test_8(self):
        # WHEN
        self.init('<set name="tk_penalty_percent">8</set>')
        # THEN
        self.assertEqual(8.0, self.p.tk_penalty_percent)

    def test_float(self):
        # WHEN
        self.init('<set name="tk_penalty_percent">0.5</set>')
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
        self.init('<set name="assist_timespan"></set>')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.assist_timespan)

    def test_junk(self):
        # WHEN
        self.init('<set name="assist_timespan">f00</set>')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.assist_timespan)

    def test_negative(self):
        # WHEN
        self.init('<set name="assist_timespan">-5</set>')
        # THEN
        self.assertEqual(-5, self.p.assist_timespan)

    def test_0(self):
        # WHEN
        self.init('<set name="assist_timespan">0</set>')
        # THEN
        self.assertEqual(0, self.p.assist_timespan)

    def test_1(self):
        # WHEN
        self.init('<set name="assist_timespan">1</set>')
        # THEN
        self.assertEqual(1, self.p.assist_timespan)

    def test_8(self):
        # WHEN
        self.init('<set name="assist_timespan">8</set>')
        # THEN
        self.assertEqual(8, self.p.assist_timespan)

    def test_float(self):
        # WHEN
        self.init('<set name="assist_timespan">0.5</set>')
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
        self.init('<set name="damage_assist_release"></set>')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.damage_assist_release)

    def test_junk(self):
        # WHEN
        self.init('<set name="damage_assist_release">f00</set>')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.damage_assist_release)

    def test_negative(self):
        # WHEN
        self.init('<set name="damage_assist_release">-5</set>')
        # THEN
        self.assertEqual(-5, self.p.damage_assist_release)

    def test_0(self):
        # WHEN
        self.init('<set name="damage_assist_release">0</set>')
        # THEN
        self.assertEqual(0, self.p.damage_assist_release)

    def test_1(self):
        # WHEN
        self.init('<set name="damage_assist_release">1</set>')
        # THEN
        self.assertEqual(1, self.p.damage_assist_release)

    def test_8(self):
        # WHEN
        self.init('<set name="damage_assist_release">8</set>')
        # THEN
        self.assertEqual(8, self.p.damage_assist_release)

    def test_float(self):
        # WHEN
        self.init('<set name="damage_assist_release">0.5</set>')
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
        self.init('<set name="prematch_maxtime"></set>')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.prematch_maxtime)

    def test_junk(self):
        # WHEN
        self.init('<set name="prematch_maxtime">f00</set>')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.prematch_maxtime)

    def test_negative(self):
        # WHEN
        self.init('<set name="prematch_maxtime">-5</set>')
        # THEN
        self.assertEqual(-5, self.p.prematch_maxtime)

    def test_0(self):
        # WHEN
        self.init('<set name="prematch_maxtime">0</set>')
        # THEN
        self.assertEqual(0, self.p.prematch_maxtime)

    def test_1(self):
        # WHEN
        self.init('<set name="prematch_maxtime">1</set>')
        # THEN
        self.assertEqual(1, self.p.prematch_maxtime)

    def test_8(self):
        # WHEN
        self.init('<set name="prematch_maxtime">8</set>')
        # THEN
        self.assertEqual(8, self.p.prematch_maxtime)

    def test_float(self):
        # WHEN
        self.init('<set name="prematch_maxtime">0.5</set>')
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
        self.init('<set name="announce"></set>')
        # THEN
        self.assertFalse(self.p.announce)

    def test_junk(self):
        # WHEN
        self.init('<set name="announce">f00</set>')
        # THEN
        self.assertFalse(self.p.announce)

    def test_true(self):
        # WHEN
        self.init('<set name="announce">true</set>')
        # THEN
        self.assertTrue(self.p.announce)

    def test_on(self):
        # WHEN
        self.init('<set name="announce">on</set>')
        # THEN
        self.assertTrue(self.p.announce)

    def test_1(self):
        # WHEN
        self.init('<set name="announce">1</set>')
        # THEN
        self.assertTrue(self.p.announce)

    def test_yes(self):
        # WHEN
        self.init('<set name="announce">yes</set>')
        # THEN
        self.assertTrue(self.p.announce)

    def test_false(self):
        # WHEN
        self.init('<set name="announce">false</set>')
        # THEN
        self.assertFalse(self.p.announce)

    def test_off(self):
        # WHEN
        self.init('<set name="announce">off</set>')
        # THEN
        self.assertFalse(self.p.announce)

    def test_0(self):
        # WHEN
        self.init('<set name="announce">0</set>')
        # THEN
        self.assertFalse(self.p.announce)

    def test_no(self):
        # WHEN
        self.init('<set name="announce">false</set>')
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
        self.init('<set name="keep_time"></set>')
        # THEN
        self.assertTrue(self.p.keep_time)

    def test_junk(self):
        # WHEN
        self.init('<set name="keep_time">f00</set>')
        # THEN
        self.assertTrue(self.p.keep_time)

    def test_true(self):
        # WHEN
        self.init('<set name="keep_time">true</set>')
        # THEN
        self.assertTrue(self.p.keep_time)

    def test_on(self):
        # WHEN
        self.init('<set name="keep_time">on</set>')
        # THEN
        self.assertTrue(self.p.keep_time)

    def test_1(self):
        # WHEN
        self.init('<set name="keep_time">1</set>')
        # THEN
        self.assertTrue(self.p.keep_time)

    def test_yes(self):
        # WHEN
        self.init('<set name="keep_time">yes</set>')
        # THEN
        self.assertTrue(self.p.keep_time)

    def test_false(self):
        # WHEN
        self.init('<set name="keep_time">false</set>')
        # THEN
        self.assertFalse(self.p.keep_time)

    def test_off(self):
        # WHEN
        self.init('<set name="keep_time">off</set>')
        # THEN
        self.assertFalse(self.p.keep_time)

    def test_0(self):
        # WHEN
        self.init('<set name="keep_time">0</set>')
        # THEN
        self.assertFalse(self.p.keep_time)

    def test_no(self):
        # WHEN
        self.init('<set name="keep_time">false</set>')
        # THEN
        self.assertFalse(self.p.keep_time)


class Conf_tables_test_case(XlrstatsTestCase):

    def init(self, xml_snippet=''):
        """
        Load the XLRstats plugin with an empty config file except for the xml_snippet given as a parameter which will
        be injected in the "tables" section.
        Then call the plugin onLoadConfig method.
        """
        self.conf.setXml(r"""
<configuration plugin="xlrstats">
    <settings name="tables">
        %s
    </settings>
</configuration>
""" % xml_snippet)
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
        self.init('<set name="playerstats"></set>')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.playerstats_table)
        self.assertTrue(self.p._defaultTableNames)

    def test_nominal(self):
        # WHEN
        self.init('<set name="playerstats">f00</set>')
        # THEN
        self.assertEqual('f00', self.p.playerstats_table)
        self.assertFalse(self.p._defaultTableNames)


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
        self.init('<set name="playerstats"></set>')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.playerstats_table)
        self.assertTrue(self.p._defaultTableNames)

    def test_nominal(self):
        # WHEN
        self.init('<set name="playerstats">f00</set>')
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
        self.init('<set name="weaponstats"></set>')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.weaponstats_table)
        self.assertTrue(self.p._defaultTableNames)

    def test_nominal(self):
        # WHEN
        self.init('<set name="weaponstats">f00</set>')
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
        self.init('<set name="weaponusage"></set>')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.weaponusage_table)
        self.assertTrue(self.p._defaultTableNames)

    def test_nominal(self):
        # WHEN
        self.init('<set name="weaponusage">f00</set>')
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
        self.init('<set name="bodyparts"></set>')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.bodyparts_table)
        self.assertTrue(self.p._defaultTableNames)

    def test_nominal(self):
        # WHEN
        self.init('<set name="bodyparts">f00</set>')
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
        self.init('<set name="playerbody"></set>')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.playerbody_table)
        self.assertTrue(self.p._defaultTableNames)

    def test_nominal(self):
        # WHEN
        self.init('<set name="playerbody">f00</set>')
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
        self.init('<set name="opponents"></set>')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.opponents_table)
        self.assertTrue(self.p._defaultTableNames)

    def test_nominal(self):
        # WHEN
        self.init('<set name="opponents">f00</set>')
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
        self.init('<set name="mapstats"></set>')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.mapstats_table)
        self.assertTrue(self.p._defaultTableNames)

    def test_nominal(self):
        # WHEN
        self.init('<set name="mapstats">f00</set>')
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
        self.init('<set name="playermaps"></set>')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.playermaps_table)
        self.assertTrue(self.p._defaultTableNames)

    def test_nominal(self):
        # WHEN
        self.init('<set name="playermaps">f00</set>')
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
        self.init('<set name="actionstats"></set>')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.actionstats_table)
        self.assertTrue(self.p._defaultTableNames)

    def test_nominal(self):
        # WHEN
        self.init('<set name="actionstats">f00</set>')
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
        self.init('<set name="playeractions"></set>')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.playeractions_table)
        self.assertTrue(self.p._defaultTableNames)

    def test_nominal(self):
        # WHEN
        self.init('<set name="playeractions">f00</set>')
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
        self.init('<set name="history_monthly"></set>')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.history_monthly_table)
        self.assertTrue(self.p._defaultTableNames)

    def test_nominal(self):
        # WHEN
        self.init('<set name="history_monthly">f00</set>')
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
        self.init('<set name="history_weekly"></set>')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.history_weekly_table)
        self.assertTrue(self.p._defaultTableNames)

    def test_nominal(self):
        # WHEN
        self.init('<set name="history_weekly">f00</set>')
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
        self.init('<set name="ctime"></set>')
        # THEN
        self.assertEqual(self.DEFAULT_VALUE, self.p.ctime_table)
        self.assertTrue(self.p._defaultTableNames)

    def test_nominal(self):
        # WHEN
        self.init('<set name="ctime">f00</set>')
        # THEN
        self.assertEqual('f00', self.p.ctime_table)
        self.assertFalse(self.p._defaultTableNames)