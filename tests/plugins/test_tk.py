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
import os
from mock import Mock, patch, sentinel
import unittest

import b3
from b3.plugins.tk import TkPlugin, TkInfo
from b3.config import XmlConfigParser

from tests import B3TestCase


default_plugin_file = os.path.normpath(os.path.join(os.path.dirname(__file__), "../../b3/conf/plugin_tk.xml"))

@patch("threading.Timer")
class Test_Tk_plugin(B3TestCase):

    def setUp(self):
        super(Test_Tk_plugin, self).setUp()
        self.conf = XmlConfigParser()
        self.p = TkPlugin(b3.console, self.conf)


    def test_onLoadConfig_minimal(self, timer_patcher):
        self.conf.setXml(r"""
        <configuration plugin="tk">
            <settings name="settings">
                <set name="max_points">400</set>
                <set name="levels">0</set>
                <set name="round_grace">7</set>
                <set name="issue_warning">sfire</set>
            </settings>
            <settings name="level_0">
                <set name="kill_multiplier">2</set>
                <set name="damage_multiplier">1</set>
                <set name="ban_length">2</set>
            </settings>
        </configuration>
        """)
        self.p = TkPlugin(b3.console, self.conf)
        self.p.onLoadConfig()
        self.assertEqual(400, self.p._maxPoints)
        self.assertEqual(0, self.p._maxLevel)
        self.assertEqual(7, self.p._round_grace)
        self.assertEqual('sfire', self.p._issue_warning)
        self.assertTrue(self.p._private_messages)


    def test_onLoadConfig(self, timer_patcher):
        self.conf.setXml(r"""
        <configuration plugin="tk">
            <settings name="settings">
                <set name="max_points">350</set>
                <set name="levels">0,1,2</set>
                <set name="round_grace">3</set>
                <set name="issue_warning">foo</set>
                <set name="private_messages">off</set>
            </settings>
            <settings name="level_0">
                <set name="kill_multiplier">2</set>
                <set name="damage_multiplier">1</set>
                <set name="ban_length">2</set>
            </settings>
            <settings name="level_1">
                <set name="kill_multiplier">2</set>
                <set name="damage_multiplier">1</set>
                <set name="ban_length">2</set>
            </settings>
            <settings name="level_2">
                <set name="kill_multiplier">1</set>
                <set name="damage_multiplier">0.5</set>
                <set name="ban_length">1</set>
            </settings>
        </configuration>
        """)
        self.p = TkPlugin(b3.console, self.conf)
        self.p.onLoadConfig()
        self.assertEqual(350, self.p._maxPoints)
        self.assertEqual(2, self.p._maxLevel)
        self.assertEqual(3, self.p._round_grace)
        self.assertEqual('foo', self.p._issue_warning)
        self.assertFalse(self.p._private_messages)





@unittest.skipUnless(os.path.exists(default_plugin_file), reason="cannot get default plugin config file at %s" % default_plugin_file)
class Test_Tk_default_config(B3TestCase):

    def setUp(self):
        super(Test_Tk_default_config, self).setUp()
        self.conf = XmlConfigParser()
        self.conf.load(default_plugin_file)
        self.p = TkPlugin(b3.console, self.conf)
        self.p.onLoadConfig()


    def test(self):
        self.assertEqual("sfire", self.p._issue_warning)
        self.assertEqual(7, self.p._round_grace)
        self.assertEqual(40, self.p._maxLevel)
        self.assertEqual(400, self.p._maxPoints)
        self.assertEqual({
                0: (2.0, 1.0, 2),
                1: (2.0, 1.0, 2),
                2: (1.0, 0.5, 1),
                20: (1.0, 0.5, 0),
                40: (0.75, 0.5, 0)
        }, self.p._levels)
        self.assertTrue(self.p._private_messages)




class Test_TkInfo(unittest.TestCase):

    def setUp(self):
        self.my_cid = 1
        self.mock_plugin = Mock(name="plugin", spec=TkPlugin)
        self.info = TkInfo(self.mock_plugin, self.my_cid)

    def test_construct(self):
        self.assertIsNone(self.info.lastAttacker)
        self.assertEqual({}, self.info.attackers)
        self.assertEqual({}, self.info.attacked)
        self.assertEqual(0, self.info.points)

    def test_damage(self):
        self.assertNotIn(2, self.info._attacked)
        self.info.damage(cid=2, points=5)
        self.assertTrue(self.info._attacked[2])

    def test_damaged(self):
        cidA = 3
        self.assertNotIn(cidA, self.info._attackers)
        self.info.damaged(cidA, points=15)
        self.assertEqual(15, self.info._attackers[cidA])

        self.info.damaged(cidA, points=5)
        self.assertEqual(20, self.info._attackers[cidA])

        cidB = 2
        self.info.damaged(cidB, points=7)
        self.assertEqual(20, self.info._attackers[cidA])
        self.assertEqual(7, self.info._attackers[cidB])

    def test_grudge(self):
        cid = 4
        self.assertNotIn(cid, self.info._grudged)
        self.assertFalse(self.info.isGrudged(cid))
        self.info.grudge(cid=cid)
        self.assertIn(cid, self.info._grudged)
        self.assertTrue(self.info.isGrudged(cid))

    def test_getAttackerPoints(self):
        cidA = 2
        s = sentinel
        self.info._attackers[cidA] = s
        self.assertEqual(s, self.info.getAttackerPoints(cidA))

        cidB = 3
        self.assertEqual(0, self.info.getAttackerPoints(cidB))

    def test_points(self):
        self.assertEqual(0, self.info.points)

        cid2 = 2
        cid3 = 3
        infos = {
            cid2: TkInfo(self.mock_plugin, cid2),
            cid3: TkInfo(self.mock_plugin, cid3)
        }
        self.mock_plugin.console.clients.getByCID = Mock(side_effect=lambda cid:cid)
        self.mock_plugin.getClientTkInfo = Mock(side_effect=lambda cid:infos[cid])

        points_2 = 45
        self.info.damage(cid2, points_2)
        infos[cid2].damaged(self.my_cid, points_2)
        self.assertEqual(points_2, self.info.points)

        points_3 = 21
        self.info.damage(cid3, points_3)
        infos[cid3].damaged(self.my_cid, points_3)
        self.assertEqual(points_2 + points_3, self.info.points)

    def test_lastAttacker(self):
        self.assertIsNone(self.info.lastAttacker)
        cid2 = 2
        self.info.damaged(cid2, 32)
        self.assertEqual(cid2, self.info.lastAttacker)

    def test_forgive(self):
        cid2 = 2
        cid3 = 3
        self.info.damaged(cid2, 75)
        self.info.damaged(cid3, 47)
        self.assertEqual(75, self.info.getAttackerPoints(cid2))
        self.assertEqual(47, self.info.getAttackerPoints(cid3))
        self.info.forgive(cid2)
        self.assertEqual(0, self.info.getAttackerPoints(cid2))
        self.assertEqual(47, self.info.getAttackerPoints(cid3))

    def test_forgive_last_attacker(self):
        cid2 = 2
        cid3 = 3
        self.info.damaged(cid2, 75)
        self.info.damaged(cid3, 47)
        self.assertEqual(75, self.info.getAttackerPoints(cid2))
        self.assertEqual(47, self.info.getAttackerPoints(cid3))
        self.assertEqual(cid3, self.info.lastAttacker)
        self.info.forgive(cid3)
        self.assertEqual(75, self.info.getAttackerPoints(cid2))
        self.assertEqual(0, self.info.getAttackerPoints(cid3))
        self.assertNotEqual(cid3, self.info.lastAttacker)

    def test_forgiven(self):
        self.mock_plugin.console = Mock()
        cid2 = 2
        self.info._attacked[cid2] = True
        self.info._warnings[cid2] = mock_warn = Mock()

        self.info.forgiven(cid2)

        self.assertNotIn(cid2, self.info._attacked)
        self.assertEqual(1, mock_warn.inactive)
        mock_warn.save.assert_called_once_with(self.mock_plugin.console)





if __name__ == '__main__':
    unittest.main()