# -*- coding: utf-8 -*-
#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
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
#
# Example:
# setup.py (for a release)
# setup.py beta (for a beta package)
#

# This section is DoxuGen information. More information on how to comment your code
# is available at http://wiki.bigbrotherbot.net/doku.php/customize:doxygen_rules
## @file
# The setuptools package creator for pypi.python.org

__author__  = 'ThorN, xlr8or'
__version__ = '2.0.1'


import ez_setup, shutil, sys
ez_setup.use_setuptools()
from setuptools import setup, find_packages

_setupinfo = {
    'name' : "b3",
    'version' : "1.7.1",
    'packages' : find_packages(),
    'extras_require' : { 'mysql' : 'MySQL-python' },
    'package_data' : {
        '': ['conf/*.xml', 'extplugins/conf/*.xml','sql/*.*', 'sql/sqlite/*', 'docs/*', 'README.md']
    },
    'zip_safe' : False,
    'author' : 'Michael Thornton (ThorN), Tim ter Laak (ttlogic), Mark Weirath (xlr8or), Thomas Leveil (Courgette)',
    'author_email' : "info@bigbrotherbot.net",
    'description' : "BigBrotherBot (B3) is a cross-platform, cross-game game administration bot. Features in-game administration of game servers, multiple user access levels, and database storage. Currently include parsers for Call of Duty 1 to 7, Urban Terror (ioUrT), World of Padman, ETpro, Smokin' Guns, BFBC2, MOH, HomeFront, Open Arena, Altitude etc.",
    'long_description': """\
Big Brother Bot B3 is a complete and total server administration package for online games. B3 is designed primarily to keep your server free from the derelicts of online gaming, but offers more, much more. With the stock configuration files, B3 will will keep your server free from offensive language, and team killers alike. A completely automated and customizable warning system will warn the offending players that this type of behavior is not allowed on your server, and ultimately kick, and or ban them for a predetermined time limit.

B3 was designed to be easily ported to other online games. Currently, B3 is in production for the Call of Duty series, Urban Terror (ioUrT), etpro, World of Padman and Smokin' Guns since these games are based on the Quake III Arena engine, conversion to any game using the engine should be easy.

Plugins provide much of the functionality for B3. These plugins can easily be configured. An SDK will be provided to make your own plugins.
""",
    'license' : "GPL",
    'url' : "http://www.bigbrotherbot.net",
    'entry_points' : {
        'console_scripts': [
            'b3_run = b3.run:main',
        ]
    },
    'classifiers' : [
        'Development Status :: 4 - Beta',
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: System :: Logging',
        'Topic :: Utilities'
    ]
}


# use 'register upload' to upload to pypi
if len(sys.argv) == 1 or sys.argv[1] == 'release':
    sys.argv = ['setup.py', 'prepare']
    setup(**_setupinfo)
    shutil.copy ('b3.egg-info/PKG-INFO', 'b3/PKG-INFO')
    sys.argv = ['setup.py', 'release']
    setup(**_setupinfo)
else:
    setup(**_setupinfo)
