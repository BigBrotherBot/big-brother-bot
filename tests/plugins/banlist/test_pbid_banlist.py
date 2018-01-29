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
import xml.etree.ElementTree as ET
from mock import Mock
from b3.plugins.banlist import PbidBanlist
from tests.plugins.banlist import BanlistTestCase

class Test_PbidBanlist(BanlistTestCase):

    def setUp(self):
        BanlistTestCase.setUp(self)

        console = Mock()
        self.banlist = PbidBanlist(console, ET.fromstring(r"""
            <pbid_banlist>
                <name>Banlist_name</name>
                <file>F:\temp\banlist.txt</file>
                <force_ip_range>no</force_ip_range>
                <message>$name is BANNED $pbid</message>
            </pbid_banlist>
        """))
#        self.banlist.getModifiedTime = Mock(return_value=time.time())
        self.banlist.plugin.info = Mock(wraps=lambda x: sys.stdout.write(x + "\n"))



    def isBanned(self, pbid):
        client = Mock()
        client.pbid = pbid
        return self.banlist.isBanned(client)


    def assertBanned(self, pbid, expected_debug=None):
        self.banlist.plugin.info.reset_mock()
        self.assertTrue(self.isBanned(pbid))
        self.assertTrue(self.banlist.plugin.info.called)
        if expected_debug:
            self.banlist.plugin.info.assert_called_with("PBid '%s' matches banlist entry %r (Banlist_name 2000-01-01 00:00:00)" % (pbid, expected_debug))
        else:
            args = self.banlist.plugin.info.call_args[0][0]
            self.assertTrue(args.startswith("PBid '%s' matches banlist entry " % pbid), args)

    def assertNotBanned(self, pbid):
        self.banlist.plugin.info.reset_mock()
        self.assertFalse(self.isBanned(pbid))
        self.banlist.plugin.verbose.assert_called_with("PBid '%s' not found in banlist (Banlist_name 2000-01-01 00:00:00)" % pbid)


    ##############################################################################################

    def test_empty_banlist(self):
        self.file_content = ""
        self.assertNotBanned("1234567890abcdef1234567890abcdef")


    def test_match(self):
        self.file_content = '''\
1234567890abcdef1234567890abc000
1234567890abcdef1234567890abc111
1234567890abcdef1234567890abc222
1234567890abcdef1234567890abc333
1234567890abcdef1234567890abc444
1234567890abcdef1234567890abc555
'''
        self.assertBanned("1234567890abcdef1234567890abc000")
        self.assertBanned("1234567890ABCDEF1234567890ABC000")
        self.assertBanned("1234567890abcdef1234567890abc111")
        self.assertBanned("1234567890ABCDEF1234567890ABC111")
        self.assertBanned("1234567890abcdef1234567890abc222")
        self.assertBanned("1234567890ABCDEF1234567890ABC222")
        self.assertBanned("1234567890abcdef1234567890abc333")
        self.assertBanned("1234567890ABCDEF1234567890ABC333")
        self.assertBanned("1234567890abcdef1234567890abc444")
        self.assertBanned("1234567890ABCDEF1234567890ABC444")
        self.assertBanned("1234567890abcdef1234567890abc555")
        self.assertBanned("1234567890ABCDEF1234567890ABC555")
        self.assertNotBanned("1234567890abcdef1234567890abc00")


    def test_commented_entries(self):
        self.file_content = '''\
//1234567890abcdef1234567890abc000
// 1234567890abcdef1234567890abc111
# 1234567890abcdef1234567890abc222
## 1234567890abcdef1234567890abc333
'''
        self.assertNotBanned("1234567890abcdef1234567890abc000")
        self.assertNotBanned("1234567890abcdef1234567890abc111")
        self.assertNotBanned("1234567890abcdef1234567890abc222")
        self.assertNotBanned("1234567890abcdef1234567890abc333")

