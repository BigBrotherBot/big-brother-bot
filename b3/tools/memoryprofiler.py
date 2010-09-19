#!/usr/bin/env python
#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2010 GrosBedo
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
# CHANGELOG:
# 2010-09-17 - v0.1.1 - GrosBedo
#   * fixed import bug
# 2010-09-11 - v0.1 - GrosBedo
#    * Initial version.

__author__  = 'GrosBedo'
__version__ = '0.1.1'

import os, sys
pathname = os.path.dirname(sys.argv[0])
sys.path.append(os.path.join(pathname, 'b3','lib')) # we add the b3/lib path for the import to work for some complex libraries (like guppy)

import threading
import time

try:
    from guppy import hpy
except:
    pass

#from sizer import code
#from sizer.sizer import scanner
#objs = scanner.Objects()
#code.interact(local = {'objs': objs})


def memoryprofile(output):
    hpy().heap().stat.dump(filename)
    time.sleep(0.1)

def runmemoryprofile(output):
    memorythread = threading.Thread(target=memoryprofile, args=(output,))
    memorythread.start()

def memoryinteractive():
    hpy().monitor()

def memorygui(input):
    hpy().pb(input)