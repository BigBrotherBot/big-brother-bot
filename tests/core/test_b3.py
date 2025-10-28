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

from __future__ import absolute_import
from tests import B3TestCase
import unittest
import b3
import os
    
class Test_getConfPath(B3TestCase, unittest.TestCase):

    def test_getConfPath(self):
        self.console.config.fileName = "/some/where/conf/b3.xml"
        self.assertEqual('/some/where/conf', b3.getConfPath(conf=self.console.config))
        self.console.config.fileName = "./b3.xml"
        self.assertEqual('.', b3.getConfPath(conf=self.console.config))

    def test_pathResolution(self):
        cwd = os.getcwd()
        self.assertEqual(os.path.join(cwd,"b3","conf", "plugin_admin.ini"), b3.getAbsolutePath("@b3/conf/plugin_admin.ini"))
        self.assertEqual(os.path.join(cwd,"b3","conf", "plugin_admin.ini"), b3.getAbsolutePath("@conf/plugin_admin.ini"))
        homedir = os.path.expanduser("~")
        self.assertEqual(os.path.join(homedir, ".b3"), b3.getAbsolutePath("@home/"))
