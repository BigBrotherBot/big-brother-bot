# -*- coding: utf-8 -*-

# ################################################################### #
#                                                                     #
#  BigBrotherBot(B3) (www.bigbrotherbot.net)                          #
#  Copyright (C) 2005 Michael "ThorN" Thornton                        #
#                                                                     #
#  This program is free software; you can redistribute it and/or      #
#  modify it under the terms of the GNU General Public License        #
#  as published by the Free Software Foundation; either version 2     #
#  of the License, or (at your option) any later version.             #
#                                                                     #
#  This program is distributed in the hope that it will be useful,    #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of     #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the       #
#  GNU General Public License for more details.                       #
#                                                                     #
#  You should have received a copy of the GNU General Public License  #
#  along with this program; if not, write to the Free Software        #
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA      #
#  02110-1301, USA.                                                   #
#                                                                     #
# ################################################################### #

__author__ = 'ThorN'
__version__ = '1.4'

import os
import sys
from b3.functions import main_is_frozen

__all__ = ['resource_directory']


def resource_directory(module):
    """
    Use this if pkg_resources is NOT installed
    """
    return os.path.dirname(sys.modules[module].__file__)


if not main_is_frozen():
    try:
        import pkg_resources
    except ImportError:
        pkg_resources = None
        pass
    else:
        # package tools is installed
        def resource_directory_from_pkg_resources(module):
            """
            Use this if pkg_resources is installed
            """
            return pkg_resources.resource_filename(module, '')

        resource_directory = resource_directory_from_pkg_resources
