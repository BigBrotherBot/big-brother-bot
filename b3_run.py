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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
#
# CHANGELOG
#
# 2014/09/01 - 1.1.2 - Fenix         - syntax cleanup
# 2015/03/06 - 1.2   - Thomas LEVEIL - drop support for python 2.6

__author__  = 'ThorN'
__version__ = '1.2'


import sys

if sys.version_info >= (3,):
    raise SystemExit("Sorry, cannot continue: B3 is not yet compatible with python version 3!")

if sys.version_info < (2, 7):
    raise SystemExit("Sorry, cannot continue: B3 is not compatible with python versions earlier than 2.7!")
    
import b3.run    


def main():
    b3.run.main()

if __name__ == '__main__':
    main()
