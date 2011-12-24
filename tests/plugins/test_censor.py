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
from mock import Mock, patch
from tests import B3TestCase
import unittest

import b3
from b3.plugins.censor import CensorPlugin
from b3.config import XmlConfigParser


class CensorTestCase(B3TestCase):
    """base class for TestCase to apply to the Censor plugin"""

    def setUp(self):
        # Timer needs to be patched or the Censor plugin would schedule a 2nd check one minute after
        # penalizing a player.
        self.timer_patcher = patch('threading.Timer')
        self.timer_patcher.start()

        super(CensorTestCase, self).setUp()
        self.conf = XmlConfigParser()
        self.conf.setXml(r"""
            <configuration plugin="censor">
                <badwords>
                    <penalty type="warning" reasonkeyword="racist"/>
                </badwords>
                <badnames>
                    <penalty type="warning" reasonkeyword="badname"/>
                </badnames>
            </configuration>
        """)
        self.p = CensorPlugin(b3.console, self.conf)
        self.p.onLoadConfig()

    def tearDown(self):
        self.timer_patcher.stop()

    def assert_name_penalized_count(self, name, count):
        self.p.penalizeClientBadname = Mock()

        mock_client = Mock()
        mock_client.connected = True
        mock_client.exactName = name

        self.p.checkBadName(mock_client)
        self.assertEquals(count, self.p.penalizeClientBadname.call_count, "name '%s' should have been penalized %s time" % (name, count))

    def assert_name_is_penalized(self, name):
        self.assert_name_penalized_count(name, 1)

    def assert_name_is_not_penalized(self, name):
        self.assert_name_penalized_count(name, 0)



class Test_Censor_badname(CensorTestCase):
    def test_regexp(self):

        def my_info(text):
            print("INFO\t%s" % text)
        self.p.info = my_info

        self.p._badNames = []
        self.assert_name_is_not_penalized('Joe')

        self.p._badNames = []
        self.p._add_bad_name(rulename='ass', regexp=r'\b[a@][s$]{2}\b')
        self.assert_name_is_penalized('ass')
        self.assert_name_is_penalized('a$s')
        self.assert_name_is_penalized(' a$s ')
        self.assert_name_is_penalized('kI$$ my a$s n00b')
        self.assert_name_is_penalized('right in the ass')
        #self.assert_name_is_not_penalized('_a$s_')

        self.p._badNames = []
        self.p._add_bad_name(rulename='dot or less than 10', regexp=r'^([.]$|^.{2,9})$')
        self.assert_name_is_penalized('.')
        self.assert_name_is_penalized('123456789')
        self.assert_name_is_not_penalized('1234567890')



default_plugin_file = os.path.normpath(os.path.join(os.path.dirname(__file__), "../../b3/conf/plugin_censor.xml"))
@unittest.skipUnless(os.path.exists(default_plugin_file), reason="cannot get default plugin_censor.xml config file at %s" % default_plugin_file)
class Test_Censor_badname_default_config(CensorTestCase):

    def setUp(self):
        super(Test_Censor_badname_default_config, self).setUp()

        def my_info(text):
            print("INFO\t%s" % text)
        self.p.info = my_info

        def my_warning(text):
            print("WARNING\t%s" % text)
        self.p.warning = my_warning

        self.p.config.load(default_plugin_file)
        self.p.onLoadConfig()
        self.assertEqual(17, len(self.p._badNames))



    def test_doublecolor(self):
        self.assert_name_is_penalized('j^^33oe')

    def test_ass(self):
        self.assert_name_is_not_penalized('jassica')
        self.assert_name_is_penalized('ass')
        self.assert_name_is_penalized('a$s')
        self.assert_name_is_penalized('big a$s joe')
        self.assert_name_is_penalized('big ass joe')

    def test_fuck(self):
        self.assert_name_is_penalized('fuck')
        self.assert_name_is_penalized('fUck')
        self.assert_name_is_penalized('f*ck')
        self.assert_name_is_penalized('f.ck')
        self.assert_name_is_penalized('fuckkkkk')
        self.assert_name_is_penalized('watdafuck?')

    def test_shit(self):
        self.assert_name_is_penalized('shit')
        self.assert_name_is_penalized('shIt')
        self.assert_name_is_penalized('sh!t')
        self.assert_name_is_penalized('sh.t')

    def test_bitch(self):
        self.assert_name_is_penalized('bitch')
        self.assert_name_is_penalized('b*tch')
        self.assert_name_is_penalized('b!tch')
        self.assert_name_is_penalized('b.tch')
        self.assert_name_is_penalized('daBiTch')

    def test_pussy(self):
        self.assert_name_is_penalized('pussy')
        self.assert_name_is_penalized('pu$sy')
        self.assert_name_is_penalized('pus$y')
        self.assert_name_is_penalized('pu$$y')
        self.assert_name_is_penalized('DaPussyKat')

    def test_nigger(self):
        self.assert_name_is_penalized('nigger')
        self.assert_name_is_penalized('n1gger')
        self.assert_name_is_penalized('n.gger')
        self.assert_name_is_penalized('n!gger')

    def test_cunt(self):
        self.skipTest("TODO")

    def test_nazi(self):
        self.skipTest("TODO")

    def test_jihad(self):
        self.skipTest("TODO")

    def test_admin(self):
        self.skipTest("TODO")

    def test_hitler(self):
        self.skipTest("TODO")

    def test_asshole(self):
        self.skipTest("TODO")

    def test_kut(self):
        self.skipTest("TODO")

    def test_hoer(self):
        self.skipTest("TODO")

    def test_huor(self):
        self.skipTest("TODO")

    def test_puta(self):
        self.skipTest("TODO")


if __name__ == '__main__':
    unittest.main()