#!/usr/bin/env python
#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2010 Michael "ThorN" Thornton
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
#
# 2010-09-07 - v1.2 - GrosBedo
#    * added the special debug switchs, like debug, profile save and load.

__author__  = 'ThorN, GrosBedo'
__version__ = '1.2'

import b3.run
import b3_debug

def main():
    b3.run.main()

if __name__ == '__main__':
    try:
        result = b3_debug.parse_cmdline_args() # we parse here for special debug switchs, if there are none, the program will continue normally
        if result: # result will be False if we launched the profiler, or any function that should activate a special behaviour that could conflict with the normal main function
            main()
    except ImportError:
        # it seems some distribution of python are bugged and cannot import pstats
        main()
    