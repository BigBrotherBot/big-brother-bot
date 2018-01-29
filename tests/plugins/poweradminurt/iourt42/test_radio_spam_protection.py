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

import sys
from mock import Mock, call
from mockito import when
from b3.config import CfgConfigParser
from b3.plugins.poweradminurt import PoweradminurtPlugin
from tests.plugins.poweradminurt.iourt42 import Iourt42TestCase

class Test_radio_spam_protection(Iourt42TestCase):
    def setUp(self):
        super(Test_radio_spam_protection, self).setUp()
        self.conf = CfgConfigParser()
        self.p = PoweradminurtPlugin(self.console, self.conf)
        self.init_default_cvar()


    def init(self, config_content=None):
        if config_content:
            self.conf.loadFromString(config_content)
        else:
            self.conf.loadFromString("""
[radio_spam_protection]
enable: True
mute_duration: 2
        """)
        self.p.onLoadConfig()
        self.p.onStartup()



    def test_conf_nominal(self):
        self.init("""
[radio_spam_protection]
enable: True
mute_duration: 2
        """)
        self.assertTrue(self.p._rsp_enable)
        self.assertEqual(2, self.p._rsp_mute_duration)


    def test_conf_nominal_2(self):
        self.init("""
[radio_spam_protection]
enable: no
mute_duration: 1
        """)
        self.assertFalse(self.p._rsp_enable)
        self.assertEqual(1, self.p._rsp_mute_duration)


    def test_conf_broken(self):
        self.init("""
[radio_spam_protection]
enable: f00
mute_duration: 0
        """)
        self.assertFalse(self.p._rsp_enable)
        self.assertEqual(1, self.p._rsp_mute_duration)



    def test_spam(self):
        # GIVEN
        self.init("""
[radio_spam_protection]
enable: True
mute_duration: 2
""")
        self.joe.connects("0")
        self.console.write = Mock(wraps=lambda x: sys.stderr.write("%s\n" % x))
        self.joe.warn = Mock()

        def joe_radio(msg_group, msg_id, location, text):
            self.console.parseLine('''Radio: 0 - %s - %s - "%s" - "%s"''' % (msg_group, msg_id, location, text))

        def assertSpampoints(points):
            self.assertEqual(points, self.joe.var(self.p, 'radio_spamins', 0).value)

        assertSpampoints(0)

        # WHEN
        when(self.p).getTime().thenReturn(0)
        joe_radio(3, 3, "Patio Courtyard", "Requesting medic. Status: healthy")
        # THEN
        assertSpampoints(0)
        self.assertEqual(0, self.joe.warn.call_count)
        self.assertEqual(0, self.console.write.call_count)

        # WHEN
        when(self.p).getTime().thenReturn(0)
        joe_radio(3, 3, "Patio Courtyard", "Requesting medic. Status: healthy")
        # THEN
        assertSpampoints(8)
        self.assertEqual(0, self.joe.warn.call_count)
        self.assertEqual(0, self.console.write.call_count)

        # WHEN
        when(self.p).getTime().thenReturn(1)
        joe_radio(3, 1, "Patio Courtyard", "f00")
        # THEN
        assertSpampoints(5)
        self.assertEqual(0, self.joe.warn.call_count)
        self.console.write.assert_has_calls([call("mute 0 2")])
