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
from b3.config import XmlConfigParser
from b3.extplugins.xlrstats import XlrstatsPlugin
from tests import B3TestCase


class Test_xlrstats(B3TestCase):

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

