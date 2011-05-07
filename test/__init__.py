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
from mock import Mock
import b3
import b3.events # needed due to the fact that all B3 events (even natives) are created at module load time
import time
import unittest

class B3TestCase(unittest.TestCase):
    '''
    setup different mocks that are useful to lots of B3 test :
        * b3.console
    '''

    def setUp(self):
        b3.console = Mock()
        b3.console.stripColors.side_effect = lambda x:x
        b3.console.time = time.time
