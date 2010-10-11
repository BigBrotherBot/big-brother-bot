# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2010
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
# CHANGELOG
#
# 09/10/2010 - v0.2 - jerbob92 
#  * set sv_hostname at statup
# 02/10/2010 - v0.1 - NTAuthority (http://alteriw.net/)



__author__  = 'NTAuthority'
__version__ = '0.2'

import b3.parsers.cod4
import re

class Cod6Parser(b3.parsers.cod4.Cod4Parser):
    gameName = 'cod6'
    _guidLength = 16
    _regPlayer = re.compile(r'(?P<slot>[0-9]+)[\s\0]+(?P<score>[0-9-]+)[\s\0]+(?P<ping>[0-9]+)[\s\0]+(?P<guid>[a-z0-9]+)[\s\0]+(?P<name>.*?)[\s\0]+(?P<last>[0-9]+)[\s\0]+(?P<ip>[0-9.]+):(?P<port>[0-9-]+)', re.I)

    def startup(self):
        b3.parsers.cod4.Cod4Parser.startup(self)
        try:
            self.game.sv_hostname = self.getCvar('sv_hostname').getString().rstrip('/')
            self.debug('sv_hostname: %s' % self.game.sv_hostname)
        except:
            self.game.sv_hostname = None
            self.warning('Could not query server for sv_hostname')