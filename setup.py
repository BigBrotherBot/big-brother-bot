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
# setup.py release (for a release)
# setup.py beta (for a beta package)
#

# This section is DoxuGen information. More information on how to comment your code
# is available at http://wiki.bigbrotherbot.net/doku.php/customize:doxygen_rules
## @file
# The setuptools package creator for pypi.python.org

__author__  = 'ThorN, xlr8or'
__version__ = '2.3'


import os, glob
import ez_setup, shutil, sys
ez_setup.use_setuptools()
from setuptools import setup, find_packages
from setuptools.command.egg_info import egg_info as orig_egg_info
from distutils import dir_util, file_util
try:
    import py2exe
    has_py2exe = True
except:
    has_py2exe = False

b3version = "1.9.2"

# override egg_info command to copy the b3.egg-info/PKG-INFO file into the b3 directory
class my_egg_info(orig_egg_info):
    def run(self):
        orig_egg_info.run(self)
        shutil.copy ('b3.egg-info/PKG-INFO', 'b3/PKG-INFO')

cmdclass = {
    'egg_info': my_egg_info,
}


def listdirectory(path):
    def istocopy(path):
        return (
            os.path.isfile(path)
            and not path.endswith('.pyc')
            and not path.endswith('.pyo')
            )
    return map(os.path.normpath, filter(istocopy, glob.glob(path + os.sep + '*')))

py2exe_dataFiles = [
    ('', ['README.md']),
    ('', ['b3/PKG-INFO']),
    ('docs', listdirectory('b3/docs/')),
    ('sql', listdirectory('b3/sql/')),
    ('sql/sqlite', listdirectory('b3/sql/sqlite')),
    ('conf', listdirectory('b3/conf/')),
    ('conf/templates', listdirectory('b3/conf/templates/')),
    ('extplugins', ['b3/extplugins/xlrstats.py']),
    ('extplugins/conf', listdirectory('b3/extplugins/conf/')),
    ]


if has_py2exe:
    # override egg_info command so it deletes py2exe build destination directory first
    class my_py2exe(py2exe.build_exe.py2exe):
        def run(self):
            dist_py2exe_path = os.path.normpath(os.path.join(os.path.abspath(os.path.dirname(__file__)), "py2exe_builder/dist_py2exe"))

            # clean destination directory
            if os.path.isdir(dist_py2exe_path):
                dir_util.remove_tree(dist_py2exe_path)

            # build with py2exe
            py2exe.build_exe.py2exe.run(self)

            # copy data files
            src_base = os.path.dirname(__file__)
            for dst, src_files in py2exe_dataFiles:
                dst_abs = os.path.normpath(os.path.join(dist_py2exe_path, dst))
                for src in src_files:
                    try:
                        src_abs = os.path.normpath(os.path.join(src_base, src))
                        dir_util.create_tree(dst_abs, src_abs)
                        file_util.copy_file(src_abs, dst_abs, dry_run=self.dry_run)
                    except Exception, e:
                        sys.stderr.write("%s\n" % e)
    cmdclass['py2exe'] = my_py2exe


setup(cmdclass=cmdclass,
    name="b3",
    version=b3version,
    tests_requires=['nose>=1.0', 'nose-exclude', 'mockito', 'pysqlite'],
    packages=find_packages(),
    extras_require={ 'mysql' : 'MySQL-python' },
    package_data={
        '': ['conf/*.xml', 'conf/templates/*.tpl', 'extplugins/xlrstats.py', 'extplugins/conf/*.xml', 'sql/*.*', 'sql/sqlite/*', 'docs/*', 'README.md']
    },
    zip_safe=False,
    author='Michael Thornton (ThorN), Tim ter Laak (ttlogic), Mark Weirath (xlr8or), Thomas Leveil (Courgette)',
    author_email="info@bigbrotherbot.net",
    description="BigBrotherBot (B3) is a cross-platform, cross-game game administration bot. Features in-game administration of game servers, multiple user access levels, and database storage. Currently include parsers for Call of Duty 1 to 8, Urban Terror (ioUrT 4.1 and 4.2), BF3, Arma II, CS:GO, Red Orchestra 2, BFBC2, MOH 2010, World of Padman, ETpro, Smokin' Guns, HomeFront, Open Arena, Altitude.",
    long_description="""\
Big Brother Bot B3 is a complete and total server administration package for online games. B3 is designed primarily to keep your server free from the derelicts of online gaming, but offers more, much more. With the stock configuration files, B3 will will keep your server free from offensive language, and team killers alike. A completely automated and customizable warning system will warn the offending players that this type of behavior is not allowed on your server, and ultimately kick, and or ban them for a predetermined time limit.

B3 was designed to be easily ported to other online games. Currently, B3 is in production for the Call of Duty series, Urban Terror (ioUrT), etpro, World of Padman and Smokin' Guns since these games are based on the Quake III Arena engine, conversion to any game using the engine should be easy.

Plugins provide much of the functionality for B3. These plugins can easily be configured. An SDK will be provided to make your own plugins.
""",
    license="GPL",
    url="http://www.bigbrotherbot.net",
    entry_points={
        'console_scripts': [
            'b3_run = b3.run:main',
        ]
    },
    classifiers=[
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
    ],
    console=[
        {
            "script" : "b3_run.py",
            "icon_resources": [(0, "py2exe_builder/assets_common/b3.ico")]
        }
    ],
    zipfile="b3.lib",
    options={
        "py2exe": {
            "dist_dir": "py2exe_builder/dist_py2exe",
            "bundle_files": 1,
            "optimize": 1,
            "includes": [
                "b3.lib.*",
                "b3.plugins.*",
                "b3.parsers.*",
                "b3.parsers.homefront",
                "b3.parsers.ravaged",
                "b3.parsers.frostbite.*",
                "b3.extplugins.__init__",
                ### additional modules for popular/useful 3rd party plugins ###
                "smtplib", "email.*", "calendar", "email.mime.*", # contact plugin
                "telnetlib", # teamspeak* plugins
                "dbhash", # to make anydbm imports work with py2exe
                "uuid", # metabans, ggcstream and telnet plugins
                "SocketServer", # telnet plugin
                "paramiko", # sftpytail plugin
            ],
        }
    }
)
