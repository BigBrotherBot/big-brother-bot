# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2012 Thomas LEVEIL <courgette@bigbrotherbot.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA

import logging

from mock import patch
from b3.config import CfgConfigParser
from b3.plugins.spamcontrol import SpamcontrolPlugin
from tests import B3TestCase


class SpamcontrolTestCase(B3TestCase):
    """
    Ease testcases that need an working B3 console and need to control the Spamcontrol plugin config
    """

    def setUp(self):
        self.timer_patcher = patch('threading.Timer')
        self.timer_patcher.start()

        self.log = logging.getLogger('output')
        self.log.propagate = False

        B3TestCase.setUp(self)
        self.console.startup()
        self.log.propagate = True

    def tearDown(self):
        B3TestCase.tearDown(self)
        self.timer_patcher.stop()

    def init_plugin(self, config_content):
        self.conf = CfgConfigParser()
        self.conf.loadFromString(config_content)
        self.p = SpamcontrolPlugin(self.console, self.conf)

        self.log.setLevel(logging.DEBUG)
        self.log.info("============================= Spamcontrol plugin: loading config ============================")
        self.p.onLoadConfig()
        self.log.info("============================= Spamcontrol plugin: starting  =================================")
        self.p.onStartup()

