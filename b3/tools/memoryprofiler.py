#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2010 Grosbedo
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
#
# CHANGELOG
#
# 2014-08-31 - v0.1.2 - Fenix    - syntax cleanup
#                                - fixed unresolved reference in memoryprofile()
# 2010-09-17 - v0.1.1 - GrosBedo - fixed import bug
# 2010-09-11 - v0.1   - GrosBedo - initial version

__author__  = 'GrosBedo'
__version__ = '0.1.1'

import os, sys
pathname = os.path.dirname(sys.argv[0])
sys.path.append(os.path.join(pathname, 'b3','lib'))

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

def memoryprofile(val):
    hpy().heap().stat.dump(val)
    time.sleep(0.1)

def runmemoryprofile(val):
    memorythread = threading.Thread(target=memoryprofile, args=(val,))
    memorythread.start()

def memoryinteractive():
    hpy().monitor()

def memorygui(val):
    hpy().pb(val)