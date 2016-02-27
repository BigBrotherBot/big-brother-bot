# -*- coding: utf-8 -*-
#
# Custom Commands Plugin for BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2013 Thomas LEVEIL <courgette@bigbrotherbot.net>
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

from mock import Mock
from unittest2 import TestCase
from b3.config import CfgConfigParser
from b3.plugins.customcommands import CustomcommandsPlugin


class Test_validate_cmd_template(TestCase):

    def setUp(self):
        self.conf = CfgConfigParser()
        self.p = CustomcommandsPlugin(Mock(), self.conf)

    def test_nominal(self):
        try:
            self.p._validate_cmd_template("cookie")
        except (AssertionError, ValueError), err:
            self.fail("expecting no error, got %r" % err)

    def test_None(self):
        self.assertRaises(AssertionError, self.p._validate_cmd_template, None)

    def test_blank(self):
        self.assertRaises(ValueError, self.p._validate_cmd_template, "  ")

    def test_ARG_placeholders(self):
        self.assertRaises(ValueError, self.p._validate_cmd_template, "tell <ARG:FIND_PLAYER:PID> <ARG:FIND_MAP> hi")
        self.p._validate_cmd_template("tell <ARG:FIND_PLAYER:PID> hi")