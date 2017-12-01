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

from b3.config import CfgConfigParser
from b3.plugins.poweradminurt import PoweradminurtPlugin, __file__ as poweradminurt_file
from tests.plugins.poweradminurt.iourt41 import Iourt41TestCase
from tests.plugins.poweradminurt.iourt42 import Iourt42TestCase

class mixin_conf(object):

    def setUp(self):
        super(mixin_conf, self).setUp()
        self.conf = CfgConfigParser()
        self.p = PoweradminurtPlugin(self.console, self.conf)
        self.init_default_cvar()
        logger = logging.getLogger('output')
        logger.setLevel(logging.INFO)



    def test_empty_config(self):
        self.conf.loadFromString("""
[foo]
        """)
        self.p.onLoadConfig()
        # should not raise any error


    ####################################### matchmode #######################################

    def test_matchmode__plugins_disable(self):
        # empty
        self.conf.loadFromString("""
[matchmode]
plugins_disable:
        """)
        self.p.loadMatchMode()
        self.assertEqual([], self.p._match_plugin_disable)

        # one element
        self.conf.loadFromString("""
[matchmode]
plugins_disable: foo
        """)
        self.p.loadMatchMode()
        self.assertEqual(['foo'], self.p._match_plugin_disable)

        # many
        self.conf.loadFromString("""
[matchmode]
plugins_disable: foo, bar
        """)
        self.p.loadMatchMode()
        self.assertEqual(['foo', 'bar'], self.p._match_plugin_disable)






##############################################################################
class Test_41(mixin_conf, Iourt41TestCase):
    """
    call the mixin tests using the Iourt41TestCase parent class
    """

class Test_42(mixin_conf, Iourt42TestCase):
    """
    call the mixin tests using the Iourt42TestCase parent class
    """
