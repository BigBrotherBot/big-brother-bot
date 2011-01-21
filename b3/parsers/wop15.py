#
# World of Padman parser for BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2008 Mark Weirath (xlr8or@xlr8or.com)
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
#

__author__  = 'xlr8or'
__version__ = '1.0.0'

from b3.parsers.q3a.abstractParser import AbstractParser
import re
import b3.parsers.wop

#----------------------------------------------------------------------------------------------------------------------------------------------
class Wop15Parser(b3.parsers.wop.WopParser):
    gameName = 'wop15'

    _lineFormats = (
        #Generated with : WOP version 1.5
        #ClientConnect: 0 014D28A78B194CDA9CED1344D47B903B 84.167.190.158
        re.compile(r'^(?P<action>[a-z]+):\s(?P<data>(?P<cid>[0-9]+)\s(?P<cl_guid>[0-9A-Z]{32})\s+(?P<ip>[0-9.]+):(?P<port>[0-9]+))$', re.IGNORECASE),

        #Kill: 3 2 8: Beinchen killed linux suse 10.3 by MOD_PLASMA
        re.compile(r'^(?P<action>[a-z]+):\s*(?P<data>(?P<acid>[0-9]+)\s(?P<cid>[0-9]+)\s(?P<aweap>[0-9]+):\s*(?P<text>.*))$', re.IGNORECASE),
        #ClientConnect: 2  151.16.71.226
        re.compile(r'^(?P<action>[a-z]+):\s(?P<data>(?P<cid>[0-9]+)\s+(?P<ip>[0-9.]+))$', re.IGNORECASE),

        #Say: 0 insta machen?
        re.compile(r'^(?P<action>say):\s*(?P<data>(?P<cid>[0-9]+)\s*(?P<text>.*))$', re.IGNORECASE),
        #Bot connecting
        #ClientConnect: 0
        re.compile(r'^(?P<action>ClientConnect):\s*(?P<data>(?P<bcid>[0-9]+))$', re.IGNORECASE),
        #Falling thru? Item stuff and so forth... still need some other actions from CTF and other gametypes to compare.  
        #Item: 3 ammo_spray_n
        re.compile(r'^(?P<action>[a-z]+):\s*(?P<data>.*)$', re.IGNORECASE)
    )
