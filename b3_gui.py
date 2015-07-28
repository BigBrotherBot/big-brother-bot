#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2015 Thomas LEVEIL
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

__author__ = 'Thomas LEVEIL'


import sys

if sys.version_info >= (3,):
    raise SystemExit("Sorry, cannot continue: B3 is not yet compatible with python version 3!")

if sys.version_info < (2, 7):
    raise SystemExit("Sorry, cannot continue: B3 is not compatible with python versions earlier than 2.7!")
    

if __name__ == '__main__':
    from b3.run import run_gui
    run_gui()
