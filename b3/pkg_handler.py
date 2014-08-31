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
# 05/01/2009 - 1.1.1 - Courgette - make PkgResourcesStandIn.version('b3') work with py2exe build
# 20/03/2010 - 1.2   - Courgette - make sure to read the version from the PKG-INFO file if found in the b3
#                                  module even when setup_tools are installed on the system
# 21/10/2010 - 1.2.1 - Courgette - fix an issue that broke the b3_run.exe when frozen on a machine that have pkg_
#                                  resources available
# 21/07/2014 - 1.3   - Fenix     - syntax cleanup

__author__  = 'ThorN'
__version__ = '1.3'

import os
import re
import sys

from b3.functions import main_is_frozen

__all__ = ['version', 'resource_directory']


class PkgResources:
    """
    Use this class if pkg_resources is installed
    """
    def version(self, module):
        v = '<unknown>'
        try:
            if os.path.isfile(os.path.join(self.resource_directory(module), 'PKG-INFO')):
                ## we need this in the case the user installed B3 from sources (copying the b3.egg-in
                ## folder) and then updates just the b3 folder but still have setup_tools installed
                ## on his system 
                v = getVersionFromFile(os.path.join(self.resource_directory(module), 'PKG-INFO'))
            else:
                v = pkg_resources.get_distribution(module).version
        except pkg_resources.DistributionNotFound:
            # must not be installed as an egg
            h = PkgResourcesStandIn()
            v = h.version(module)

        return v

    def resource_directory(self, module):
        return pkg_resources.resource_filename(module, '')


class PkgResourcesStandIn:
    """
    Use this class if pkg_resources is NOT installed
    """
    def version(self, module):
        v = '<unknown>'
        searchdir = ['PKG-INFO',
                     os.path.join(self.resource_directory(module), 'PKG-INFO'),
                     os.path.join(self.resource_directory(module), '..', 'PKG-INFO'),
                     os.path.join(self.resource_directory(module), '..', 'b3.egg-info', 'PKG-INFO')]

        if module == 'b3':
            searchdir.insert(0, os.path.join(self.getB3Path(), 'PKG-INFO'))

        for p in searchdir:
            if os.path.isfile(p):
                v = getVersionFromFile(p)

        return v

    def resource_directory(self, module):
        return os.path.dirname(sys.modules[module].__file__)
    
    def getB3Path(self):
        if main_is_frozen():
            # which happens when running from the py2exe build
            return os.path.dirname(sys.executable)
        return self.resource_directory('b3')

def getVersionFromFile(filename):
    v = None
    if os.path.isfile(filename):
        f = file(filename)
        for line in f:
            if line.lower().startswith('version:'):
                v = re.sub('[^A-Za-z0-9.]+', '-', line.split(':', 1)[1].strip().replace(' ', '.'))
                break
        f.close()
    return v

pkg_handler = None

if main_is_frozen():
    # avoid issues when frozen with py2exe on a windows machine
    # that have phg_resources importable.
    pkg_handler = PkgResourcesStandIn()
else:
    try:
        import pkg_resources
    except ImportError:
        # package tools is not intalled
        pkg_resources = None
        pkg_handler = PkgResourcesStandIn()
    else:
        # package tools is installed
        pkg_handler = PkgResources()

version = pkg_handler.version
resource_directory = pkg_handler.resource_directory