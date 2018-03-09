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

__author__ = 'ThorN, xlr8or, courgette, Fenix'
__version__ = '3.7'

import re
import os
import sys
import shutil
import stat
import zipfile
import setuptools
import platform

from distutils import dir_util, log
from setuptools.command.egg_info import egg_info as orig_egg_info
from time import strftime


def getPlatform():
    """
    Return the current platform name.
    :return: nt || darwin || linux
    """
    if sys.platform in ('win32', 'win64'):
        # Windows family
        return 'nt'
    elif sys.platform in ('darwin', 'mac'):
        # OS X faimily
        return 'darwin'
    else:
        # Fallback linux distro
        return 'linux'
        
        
def getB3versionInfo():
    """
    Returns a tuple with B3 version information.
    :return: version, platform, architecture :type: tuple
    """
    def right_cut(text, cut):
        """
        Remove 'cut' from 'text' if found as ending suffix
        :param text: The string we want to clean
        :param cut: The suffix of the string
        :return: A string with the given suffix removed
        """
        if text.endswith(cut):
            return text[:-len(cut)]
        return text
    return __version__, getPlatform(), right_cut(platform.architecture()[0], 'bit')
    
    
b3_version = '1.12'
b3_version_info = getB3versionInfo()

PROJECT_DIR = os.path.abspath(os.path.dirname(__file__))  # directory where this file is in
DIST_DIR = os.path.join(PROJECT_DIR, 'dist')  # directory where all the final builds will be found
BUILD_DIR = os.path.join(PROJECT_DIR, 'build')  # directory where all work will be done
BUILD_TIME = strftime('%Y%m%d')  # current build time (for distribution zip name)
BUILD_PATH = os.path.join(BUILD_DIR, 'b3-%s-%s-%s%s' % (b3_version, BUILD_TIME, b3_version_info[1], b3_version_info[2]))  # frozen distribution path

settings = {
    'nt': {
        'binary_name': 'b3.exe',
        'icon': os.path.join(PROJECT_DIR, 'installer/assets_common', 'b3.ico'),
    },
    'darwin': {
        'binary_name': 'b3',
        'icon': os.path.join(PROJECT_DIR, 'installer/assets_common', 'b3.icns'),
    },
    'linux': {
        'binary_name': 'b3',
        'icon': None,
    }
}

class CleanCommand(setuptools.Command):
    """Custom clean command to tidy up the project root."""
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        if os.path.isdir(BUILD_DIR):
            dir_util.remove_tree(BUILD_DIR, verbose=1)
        _egg_info_dir = os.path.join(PROJECT_DIR, 'b3.egg-info')
        if os.path.isdir(_egg_info_dir):
            dir_util.remove_tree(_egg_info_dir, verbose=1)


class my_egg_info(orig_egg_info):
    """
    Override egg_info command to copy the b3.egg-info/PKG-INFO file into the b3 directory
    """

    def run(self):
        orig_egg_info.run(self)
        shutil.copy('b3.egg-info/PKG-INFO', 'b3/PKG-INFO')


cmdclass = {
    'egg_info': my_egg_info,
    'clean': CleanCommand,
}

executables = None

if len(sys.argv) == len(set(sys.argv) - {'build_exe'}):
    from setuptools import setup
else:
    from cx_Freeze import setup
    from cx_Freeze import Executable
    from cx_Freeze import build_exe

    class my_build_exe(build_exe):
        """extends the build_exe command to:
           - add option 'dist_dir' (or --dist-dir as a command line parameter)
           - add option 'linux_binary_name' to define the name of the B3 binary file
           - produce a zip file
           - produce an installer with InnoSetup
        """
        dist_dir = None
        linux_binary_name = None
        user_options = build_exe.user_options
        user_options.extend([('dist-dir=', 'd', "directory to put final built distributions in [default: dist]")])
        user_options.extend([('linux-binary-name=', None, "file name of the Linux B3 binary [default: b3_run]")])

        def initialize_options(self):
            self.dist_dir = None
            self.linux_binary_name = None
            build_exe.initialize_options(self)

        def finalize_options(self):
            if self.dist_dir is None:
                self.dist_dir = self.build_exe
            if self.linux_binary_name is None:
                self.linux_binary_name = 'b3_run'
            build_exe.finalize_options(self)

        def run(self):
            if not os.path.isdir(self.dist_dir):
                os.mkdir(self.dist_dir)

            build_exe.run(self)  # call original build_exe run method

            current_b3_version_part1, current_b3_version_part2 = self.get_version()
            self.clean_compiled_files()
            self.chmod_exec()
            self.unix2dos()
            release_name = 'b3-%s%s-%s%s' % (current_b3_version_part1, current_b3_version_part2, b3_version_info[1], b3_version_info[2])

            self.make_zip(release_name)
            self.make_innosetup(current_b3_version_part1, current_b3_version_part2)

        def get_version(self):
            """extract version number from the b3.egg-info/PKG-INFO file"""
            log.info(">>> parse B3 version")
            pkginfo_file = os.path.join(self.build_exe, 'PKG-INFO')
            pkginfo_version = re.compile(
                r'^\s*Version:\s*(?P<version>(?P<numbers>\d+\.\d+(?:\.\d+)?)(?P<pre_release>(?:a|b|dev|d)\d*)?(?P<suffix>.*?))\s*$',
                re.MULTILINE)
            with open(pkginfo_file, 'r') as f:
                match = pkginfo_version.search(f.read())
                if not match:
                    log.error("could not find version from %s" % pkginfo_file)
                    sys.exit(1)

            current_b3_version_part1 = match.group("numbers")
            current_b3_version_part2 = ""
            if match.group("pre_release"):
                current_b3_version_part2 += match.group("pre_release")
            if match.group("suffix"):
                current_b3_version_part2 += match.group("suffix")

            return current_b3_version_part1, current_b3_version_part2

        def clean_compiled_files(self):
            """remove python compiled files (if any got left in)"""
            log.info(">>> clean pyc/pyo")
            for root, dirs, files in os.walk(self.build_exe):
                for filename in files:
                    path = os.path.abspath(os.path.join(root, filename))
                    if path.endswith('.pyc') or path.endswith('.pyo'):
                        os.remove(path)

        def chmod_exec(self):
            """set +x flag on compiled binary if on Linux"""
            if getPlatform() == 'linux':
                log.info(">>> chmod")
                filename = os.path.join(self.build_exe, self.linux_binary_name)
                st = os.stat(filename)
                os.chmod(filename, st.st_mode | stat.S_IEXEC)

        def unix2dos(self):
            """makes sure text files from directory have 'Windows style' end of lines"""
            if getPlatform() == 'nt':
                log.info(">>> unix2dos")
                for root, dirs, files in os.walk(self.build_exe):
                    for filename in files:
                        path = os.path.abspath(os.path.join(root, filename))
                        if not os.path.isdir(path) and path.rsplit('.', 1)[-1] in (
                                'sql', 'txt', 'md', 'cfg', 'ini', 'txt', 'xml', 'tpl'):
                            with open(path, mode='rb') as f:
                                data = f.read()
                            new_data = re.sub("\r?\n", "\r\n", data)
                            if new_data != data:
                                with open(path, mode='wb') as f:
                                    f.write(new_data)

        def make_zip(self, release_name):
            zip_file = os.path.join(self.dist_dir, '%s.zip' % release_name)
            log.info(">>> create zip %s from content of %s" % (zip_file, self.build_exe))
            log.info('creating zip distribution: %s' % zip_file)
            zipf = zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED)
            for root, dirs, files in os.walk(self.build_exe):
                for filename in files:
                    path = os.path.abspath(os.path.join(root, filename))
                    zipf.write(path, arcname=os.path.join('b3', path[len(self.build_exe):]))
            zipf.close()

        def make_innosetup(self, current_b3_version_part1, current_b3_version_part2):
            """create windows installer"""
            if getPlatform() == 'nt':
                log.info(">>> InnoSetup")
                import subprocess
                import yaml

                innosetup_dir = 'installer/innosetup'
                yaml_config_file = os.path.join(innosetup_dir, 'build.yaml')
                with open(yaml_config_file, 'r') as f:
                    yaml_config = yaml.load(f)
                if 'innosetup_scripts' not in yaml_config:
                    log.error("invalid config file: could not find 'innosetup_scripts'")
                    sys.exit(1)
                if not len(yaml_config['innosetup_scripts']):
                    log.error("invalid config file: no script found in 'innosetup_scripts' section")
                    sys.exit(1)
                if 'iscc' not in yaml_config:
                    log.error("invalid config file: could not find 'iscc'")
                    sys.exit(1)
                if not os.path.isfile(os.path.join(innosetup_dir, yaml_config['iscc'])):
                    log.error("invalid config file: '%s' is not a file" % yaml_config['iscc'])
                    sys.exit(1)

                # location of the InnoSetup Compiler program taken from environment
                # variable ISCC_EXE if exists, else from the yaml config file
                yaml_config['iscc'] = os.environ.get('ISCC_EXE', yaml_config['iscc'])
                if not yaml_config['iscc'].lower().endswith('iscc.exe'):
                    log.error("invalid location for the ISCC.exe program: '%s' is not a iscc.exe" % yaml_config['iscc'])
                    sys.exit(1)

                # build each given innosetup script
                for filename in yaml_config['innosetup_scripts']:
                    script_file = os.path.join(innosetup_dir, filename)
                    log.info("building %s" % script_file)

                    try:
                        cmd = [
                            yaml_config['iscc'],
                            script_file, '/Q',
                            '/O' + DIST_DIR,
                            '/dB3_VERSION_NUMBER=' + current_b3_version_part1,
                            '/dB3_VERSION_SUFFIX=' + current_b3_version_part2,
                            '/dB3_VERSION_PLATFORM=' + b3_version_info[1],
                            '/dB3_VERSION_ARCHITECTURE=' + b3_version_info[2],
                            '/dB3_BUILD_PATH=' + self.build_exe,
                        ]
                        subprocess.call(cmd)
                    except Exception, e:
                        log.error('could not build %s: %s' % (script_file, e))

    cmdclass['build_exe'] = my_build_exe

    executables = [
        Executable(
            script='b3_run.py',
            base='console' if getPlatform() == 'nt' else None,
            compress=True,
            copyDependentFiles=True,
            targetName=settings[getPlatform()]['binary_name'],
            icon=settings[getPlatform()]['icon'],
        )
    ]


########################################################################################################################
#                                                                                                                      #
#   SETUP                                                                                                              #
#                                                                                                                      #
########################################################################################################################

setup(
    cmdclass=cmdclass,
    name="b3",
    version=b3_version,
    author='Michael Thornton (ThorN), Tim ter Laak (ttlogic), Mark Weirath (xlr8or), Thomas Leveil (Courgette), Daniele Pantaleone (Fenix)',
    author_email="info@bigbrotherbot.net",
    description="BigBrotherBot (B3) is a cross-platform, cross-game game administration bot. "
                "Features in-game administration of game servers, multiple user access levels, and database storage. "
                "Currently include parsers for Altitude, Arma II, Arma III, Battlefield 3, Battlefield 4, Battlefield "
                "Bad Company 2, Battlefield Hardline, Chivalry Medieval Warfare, Call of Duty 1 to 8, Counter-Strike: "
                "Global Offensive, Ennemy Territory, Ennemy Territory Pro, Insurgency,  Urban Terror (ioUrT 4.1 and "
                "4.2), Medal of Honor 2010, Medal of Honor Warfighter, Open Arena, Red Orchestra 2, Smokin' Guns, "
                "Soldier of Fortune 2, World of Padman.",
    long_description="Big Brother Bot B3 is a complete and total server administration package for online games. "
                     "B3 is designed primarily to keep your server free from the derelicts of online gaming, but offers "
                     "more, much more. With the stock configuration files, B3 will will keep your server free from "
                     "offensive language, and team killers alike. A completely automated and customizable warning "
                     "system will warn the offending players that this type of behavior is not allowed on your server, "
                     "and ultimately kick, and or ban them for a predetermined time limit. B3 was designed to be easily "
                     "ported to other online games. Currently, B3 is in production for the Call of Duty series, "
                     "Urban Terror (ioUrT), etpro, World of Padman and Smokin' Guns since these games are based on "
                     "the Quake III Arena engine, conversion to any game using the engine should be easy. Plugins "
                     "provide much of the functionality for B3. These plugins can easily be configured. An SDK will "
                     "be provided to make your own plugins.",
    license="GPL",
    url="http://www.bigbrotherbot.net",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Topic :: System :: Logging',
        'Topic :: Utilities'
    ],
    install_requires=[
        'pymysql>=0.6.6,<2',
        'python-dateutil>=2.4.1,<3',
        'feedparser>=4.1,<6',
        'requests>=2.6.0'
    ],
    packages=setuptools.find_packages(),
    package_data={'': [
        'conf/*.xml',
        'conf/*.ini',
        'conf/templates/*.tpl',
        'conf/templates/autodoc/*.html',
        'docs/*.txt',
        'docs/*.pdf',
        'extplugins/*.*',
        'plugins/*.*',
        'sql/*.*',
        'sql/sqlite/*',
        'sql/mysql/*',
        'sql/postgresql/*',
        '../CHANGELOG',
        '../README.md',
        '../b3_debug.py',
        '../b3_run.py',
        '../scripts/*.*',
        '../examples/*.*',
    ]
    },
    entry_points={
        'console_scripts': [
            'b3_run = b3.run:main',
        ]
    },
    options={
        'sdist': {
            'dist_dir': DIST_DIR,
        },
        'bdist_egg': {
            'dist_dir': DIST_DIR,
        },
        'bdist_mac': {
            'iconfile': settings[getPlatform()]['icon'],
            'bundle_name': 'BigBrotherBot (B3) %s' % b3_version,
        },
        'bdist_dmg': {
            'dist_dir': DIST_DIR,
            'volume_label': 'BigBrotherBot (B3) %s' % b3_version,
            'applications_shortcut': False,
        },
        'build_exe': {
            'dist_dir': DIST_DIR,
            'linux_binary_name': settings[getPlatform()]['binary_name'],
            'build_exe': BUILD_PATH,
            'silent': False,
            'optimize': 1,
            'compressed': True,
            'create_shared_zip': False,
            'append_script_to_exe': True,
            'packages': [
                'b3.lib',
                'b3.parsers',
                'b3.tools',
            ],
            'excludes': ['tcl', 'ttk', 'tkinter', 'Tkinter'],
            'includes': [
                ### storage modules
                'pymysql',
                'psycopg2',
                ### additional modules for popular/useful 3rd party plugins ###
                'feedparser', # adv plugin
                'smtplib', 'email', 'calendar',  # contact plugin
                'telnetlib',  # teamspeak* plugins
                'dbhash',  # to make anydbm imports work with py2exe
                'uuid',  # metabans, ggcstream and telnet plugins
                'SocketServer',  # telnet plugin
                'paramiko',  # sftpytail plugin
                'fileinput',  # badrcon plugin
                'requests', # geolocation, jumper
            ],
            'include_files': [
                ('README.md', 'README.md'),
                ('b3/PKG-INFO', 'PKG-INFO'),
                ('b3/docs/', 'docs'),
                ('b3/conf', 'conf'),
                ('b3/conf/templates', 'conf/templates'),
                ('b3/conf/templates/autodoc', 'conf/templates/autodoc'),
                ('b3/extplugins/', 'extplugins'),
                ('b3/plugins/', 'plugins/'),
                ('b3/sql', 'sql'),
                ('b3/sql/mysql', 'sql/mysql'),
                ('b3/sql/postgresql', 'sql/postgresql'),
                ('b3/sql/sqlite', 'sql/sqlite'),
                ('examples', 'examples'),
                ('scripts', 'scripts'),
            ],
        }
    },
    executables=executables
)

