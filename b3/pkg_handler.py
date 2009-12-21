#
# BigBrotherBot(B3) (www.bigbrotherbot.com)
# Copyright (C) 2005 Michael "ThorN" Thornton
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

__author__  = 'ThorN'
__version__ = '1.1.0'

import os, sys, re

__all__ = ['version', 'resource_directory']

# use this class if pkg_resources is installed
class PkgResources:
    def version(self, module):
        version = '<unknown>'

        try:
            version = pkg_resources.get_distribution(module).version
        except pkg_resources.DistributionNotFound:
            # must not be installed as an egg
            pkg_handler = PkgResourcesStandIn()
            version = pkg_handler.version(module)

        return version

    def resource_directory(self, module):
        return pkg_resources.resource_filename(module, '')

# use this class if pkg_resources is NOT installed
class PkgResourcesStandIn:
    def version(self, module):
        # find package info
        version = '<unknown>'
        for p in ('PKG-INFO' , os.path.join(self.resource_directory(module), 'PKG-INFO'), os.path.join(self.resource_directory(module), '..', 'PKG-INFO'), os.path.join(self.resource_directory(module), '..', 'b3.egg-info', 'PKG-INFO')):
            if os.path.isfile(p):            
                f = file(p, 'r')                
                for line in f:
                    if line.lower().startswith('version:'):
                        version = re.sub('[^A-Za-z0-9.]+', '-', line.split(':',1)[1].strip().replace(' ','.'))
                        break
                f.close()
                break

        return version

    def resource_directory(self, module):
        return os.path.dirname(sys.modules[module].__file__)

pkg_handler = None
try:
    import pkg_resources
except ImportError:
    # package tools is not intalled
    pkg_handler = PkgResourcesStandIn()
else:
    # package tools is installed
    pkg_handler = PkgResources()

version = pkg_handler.version
resource_directory = pkg_handler.resource_directory