#
# Soldier of Fortune 2 parser for BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2011 Mark Weirath (xlr8or@xlr8or.com)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
#
# CHANGELOG

__author__ = 'xlr8or, cGs-clan'
__version__ = '1.0.0'

from b3.parsers.sof2 import Sof2Parser

#----------------------------------------------------------------------------------------------------------------------------------------------
class Sof2PmParser(Sof2Parser):
    gameName = 'sof2pm'
    privateMsg = True

