# coding=utf-8
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
# 2010/02/20            - Courgette - user friendly handling of parser import error: prints a detailed message and exits
# 2010/02/24            - Courgette - user friendly message on missing config file option
# 2010/03/20 - 1.1.0    - xl8or     - ability to disable automatic setup procedure when option -n, --nosetup is passed
# 2010/09/16 - 1.1.1    - GrosBedo  - can now run in a thread (functions profiler mode)
# 2010/10/20 - 1.1.2    - GrosBedo  - added TEAM_FREE for non team based gametypes (eg: deathmatch)
# 2014/07/20 - 1.2      - Fenix     - syntax cleanup
# 2014/09/07 - 1.2.1    - Courgette - fix getAbsolutePath @b3 and @conf expansion on path using windows style separators
# 2014/12/14 - 1.3      - Fenix     - let the parser know if we are running B3 in auto-restart mode or not
# 2015/05/04 - 1.4      - Fenix     - added getPlatform() function: return the current platform name
#                                   - better update data printing in stdout
#                                   - added getWritableFilePath function: return a valid writable filepath
# 2015/05/22 - 1.5      - Fenix     - allow system filepaths to be decoded using default filesystem encoding

import os
import re
import sys
import pkg_handler
import traceback
import time
import signal
import config

from b3.functions import main_is_frozen
from b3.update import checkUpdate
from b3.setup import Setup
from tempfile import TemporaryFile
from ConfigParser import NoOptionError
from ConfigParser import NoSectionError

__author__ = 'ThorN'
__version__ = pkg_handler.version(__name__)

modulePath = pkg_handler.resource_directory(__name__)

versionOs = os.name
versionId = 'v%s [%s]' % (__version__, versionOs)
version = '^8www.bigbrotherbot.net ^0(^8b3^0) ^9%s ^9[^3PoisonIvy^9]^3' % versionId

confdir = None
console = None

# TEAMS
TEAM_UNKNOWN = -1
TEAM_FREE = 0
TEAM_SPEC = 1
TEAM_RED = 2
TEAM_BLUE = 3

# PLAYER STATE
STATE_DEAD = 1
STATE_ALIVE = 2
STATE_UNKNOWN = 3

# APP HOME DIRECTORY
HOMEDIR = os.path.normpath(os.path.expanduser('~/BigBrotherBot')).decode(sys.getfilesystemencoding())
if not os.path.isdir(HOMEDIR):
    os.mkdir(HOMEDIR)


def loadParser(pname, configFile, nosetup=False):
    """
    Load the parser module given it's name.
    :param pname: The parser name
    :param configFile: The parser configuration file
    :param nosetup: Whether or not to run the B3 setup
    :return The parser module
    """
    if pname == 'changeme':
        if nosetup:
            raise SystemExit('ERROR: configuration file not setup properly: please run B3 with option: --setup or -s')
        Setup(configFile)
    name = 'b3.parsers.%s' % pname
    mod = __import__(name)
    components = name.split('.')
    components.append('%sParser' % pname.title())
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod


def getPlatform():
    """
    Return the current platform name.
    :return: win32, darwin, linux
    """
    if sys.platform not in ('win32', 'darwin'):
        return 'linux'
    return sys.platform


def getB3versionString():
    """
    Return the B3 version as a string.
    """
    sversion = re.sub(r'\^[0-9a-z]', '', version)
    if main_is_frozen():
        sversion = "%s [%s standalone]" % (sversion, getPlatform())
    return sversion


def getB3Path(decode=False):
    """
    Return the path to the main B3 directory.
    :param decode: if True will decode the path string using the default file system encoding before returning it
    """
    if main_is_frozen():
        path = os.path.dirname(sys.executable)
    else:
        path = modulePath
    if not decode:
        return os.path.normpath(os.path.expanduser(path))
    return os.path.normpath(os.path.expanduser(path)).decode(sys.getfilesystemencoding())


def getConfPath(decode=False):
    """
    Return the path to the B3 main configuration directory.
    :param decode: if True will decode the path string using the default file system encoding before returning it
    """
    path = confdir or os.path.dirname(console.config.fileName)
    if not decode:
        return path
    return path.decode(sys.getfilesystemencoding())


def getAbsolutePath(path, decode=False):
    """
    Return an absolute path name and expand the user prefix (~).
    :param path: the relative path we want to expand
    :param decode: if True will decode the path string using the default file system encoding before returning it
    """
    if path[0:4] == '@b3\\' or path[0:4] == '@b3/':
        path = os.path.join(getB3Path(decode=False), path[4:])
    elif path[0:6] == '@conf\\' or path[0:6] == '@conf/':
        path = os.path.join(getConfPath(decode=False), path[6:])
    if not decode:
        return os.path.normpath(os.path.expanduser(path))
    return os.path.normpath(os.path.expanduser(path)).decode(sys.getfilesystemencoding())


def getWritableFilePath(filepath, decode=False):
    """
    Return an absolute filepath making sure the current user can write it.
    If the given path is not writable by the current user, the path will be converted
    into an absolute path pointing inside the B3 home directory (defined in the `HOMEDIR` global
    variable) which is assumed to be writable.
    :param filepath: the relative path we want to expand
    :param decode: if True will decode the path string using the default file system encoding before returning it
    """
    filepath = getAbsolutePath(filepath, decode)
    if not filepath.startswith(HOMEDIR):
        try:
            tmp = TemporaryFile(dir=os.path.dirname(filepath))
        except (OSError, IOError):
            # no need to decode again since HOMEDIR is already decoded
            # and os.path.join will handle everything itself
            filepath = os.path.join(HOMEDIR, os.path.basename(filepath))
        else:
            tmp.close()
    return filepath


def start(configFile, nosetup=False, autorestart=False):
    """
    Main B3 startup.
    :param configFile: The B3 configuration file
    :param nosetup: Whether or not to run the B3 setup
    :param autorestart: If the bot is running in auto-restart mode
    """
    configFile = getAbsolutePath(configFile)
    clearScreen()

    print 'Starting %s\n' % getB3versionString()

    conf = None
    if os.path.exists(configFile):
        print 'Using config file: %s' % configFile
        global confdir
        confdir = os.path.dirname(configFile)
        conf = config.MainConfig(config.load(configFile))
    else:
        # this happens when a config was entered on
        # the commandline, but it does not exist
        if nosetup:
            raise SystemExit('ERROR: could not find config file %s' % configFile)
        Setup(configFile)

    try:
        update_channel = conf.get('update', 'channel')
    except (NoSectionError, NoOptionError):
        pass
    else:
        sys.stdout.write('Checking update  : ')
        sys.stdout.flush()
        if update_channel == 'skip':
            sys.stdout.write('SKIP\n')
            sys.stdout.flush()
        else:
            updatetext = checkUpdate(__version__, channel=update_channel, singleLine=True, showErrormsg=True)
            if updatetext:
                sys.stdout.write('%s\n' % updatetext)
                sys.stdout.flush()
                time.sleep(2)
            else:
                sys.stdout.write('no update available\n')
                sys.stdout.flush()
                time.sleep(1)

    try:

        parserType = conf.get('b3', 'parser')
        if not parserType:
            raise SystemExit('ERROR: you must supply a parser')

        try:
            parser = loadParser(parserType, configFile, nosetup)
        except ImportError, err:
            raise SystemExit("CRITICAL: could not find parser '%s': check you main config file\n"
                             "B3 failed to start.\n%r" % (parserType, err))
        
        global console
        console = parser(conf, autorestart)

    except NoOptionError, err:
        raise SystemExit("CRITICAL: option %r not found in section %r: "
                         "correct your config file %s" % (err.option, err.section, configFile))


    def termSignalHandler(signum, frame):
        """
        Define the signal handler so to handle B3 shutdown properly.
        """
        console.bot("TERM signal received: shutting down")
        console.shutdown()
        raise SystemExit(222)

    try:
        # necessary if using the functions profiler,
        # because signal.signal cannot be used in threads
        signal.signal(signal.SIGTERM, termSignalHandler)
    except Exception:
        pass

    try:
        console.start()
    except KeyboardInterrupt:
        console.shutdown()
        print 'Goodbye'
        return
    except SystemExit, msg:
        print 'Exiting: %s' % msg
        raise
    except Exception, msg:
        print 'Error: %s' % msg
        traceback.print_exc()
        sys.exit(223)


def clearScreen():
    """
    Clear the current shell screen according to the OS being used.
    """
    if getPlatform() == 'win32':
        os.system('cls')
    else:
        os.system('clear')