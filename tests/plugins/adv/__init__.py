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
import unittest2 as unittest

from b3.plugins.admin import AdminPlugin
from tests import B3TestCase
from mock import patch,  Mock
from mockito import when, unstub
from b3.plugins.adv import AdvPlugin
from b3.config import XmlConfigParser, CfgConfigParser
from b3 import __file__ as b3_module__file__

ADMIN_CONFIG_FILE = os.path.normpath(os.path.join(os.path.dirname(b3_module__file__), "conf/plugin_admin.ini"))
ADV_CONFIG_FILE = os.path.normpath(os.path.join(os.path.dirname(__file__), "../../../b3/conf/plugin_adv.xml"))
ADV_CONFIG_CONTENT = None

timer_patcher = None

RSS_FEED_CONTENT = """\
<?xml version="1.0" encoding="UTF-8"?>
<rss version="0.92" xml:lang="en-US">
    <channel>
        <title>Big Brother Bot Forum - News (Read Only)</title>
        <link>http://forum.bigbrotherbot.net/index.php</link>
        <description><![CDATA[Live information from Big Brother Bot Forum]]></description>
        <item>
            <title>f00 bar item title</title>
            <link>http://forum.bigbrotherbot.net/news-2/f00-item-link</link>
            <description>
                <![CDATA[f00 bar item description]]>
            </description>
            <pubDate>Sun, 08 Feb 2015 08:53:37 GMT</pubDate>
            <guid>http://forum.bigbrotherbot.net/news-2/123456798</guid>
        </item>
    </channel>
</rss>
"""


class AdvTestCase(B3TestCase):
    """
    Ease test cases that need an working B3 console and need to control the ADV plugin config
    """
    def setUp(self):
        self.log = logging.getLogger('output')
        self.log.propagate = False

        B3TestCase.setUp(self)

        global ADV_CONFIG_CONTENT, ADV_CONFIG_FILE, ADMIN_CONFIG_FILE, timer_patcher
        if os.path.exists(ADV_CONFIG_FILE):
            with open(ADV_CONFIG_FILE, 'r') as f:
                ADV_CONFIG_CONTENT = f.read()

        self.adminPluginConf = CfgConfigParser()
        self.adminPluginConf.load(ADMIN_CONFIG_FILE)
        self.adminPlugin = AdminPlugin(self.console, self.adminPluginConf)
        when(self.console).getPlugin("admin").thenReturn(self.adminPlugin)

        self.adminPlugin.onLoadConfig()
        self.adminPlugin.onStartup()

        self.console.startup()
        self.log.propagate = True

        timer_patcher = patch('threading.Timer')
        timer_patcher.start()

    def tearDown(self):
        B3TestCase.tearDown(self)
        timer_patcher.stop()
        unstub()

    def init_plugin(self, config_content=None):
        conf = None
        if config_content:
            conf = XmlConfigParser()
            conf.setXml(config_content)
        elif ADV_CONFIG_CONTENT:
            conf = XmlConfigParser()
            conf.setXml(ADV_CONFIG_CONTENT)
        else:
            unittest.skip("cannot get default plugin config file at %s" % ADV_CONFIG_FILE)

        self.p = AdvPlugin(self.console, conf)
        self.p.save = Mock()
        self.conf = self.p.config
        self.log.setLevel(logging.DEBUG)
        self.log.info("============================= Adv plugin: loading config ============================")
        self.p.onLoadConfig()
        self.log.info("============================= Adv plugin: starting  =================================")
        self.p.onStartup()