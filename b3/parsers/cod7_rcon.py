#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2005 Michael "ThorN" Thornton
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
# Changelog :

# 2011/02/01 -1.1.0 - Bravo17
# * Support for cod7 rcon format added 
# 
#
 
__author__ = 'Bravo17'
__version__ = '1.1.0'
 
import socket, sys, select, re, time, thread, threading, Queue
import b3
import b3.parsers.q3a.rcon

#--------------------------------------------------------------------------------------------------
class Cod7Rcon(b3.parsers.q3a.rcon.Rcon):
    rconsendstring = '\xff\xff\xff\xff\x00%s %s\00'
    rconreplystring = '\xff\xff\xff\xff\x01print\n'
