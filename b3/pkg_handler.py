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
# 05/01/2009 - 1.1.1 - Courgette     - make PkgResourcesStandIn.version('b3') work with py2exe build
# 20/03/2010 - 1.2   - Courgette     - make sure to read the version from the PKG-INFO file if found in the b3
#                                      module even when setup_tools are installed on the system
# 21/10/2010 - 1.2.1 - Courgette     - fix an issue that broke the b3_run.exe when frozen on a machine that have pkg_
#                                      resources available
# 21/07/2014 - 1.3   - Fenix         - syntax cleanup
# 2015/03/08 - 1.4   - Thomas LEVEIL - remove `version` and refactor `resource_directory`

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
