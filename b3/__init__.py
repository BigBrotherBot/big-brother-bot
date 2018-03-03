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


import os
import re
import sys
import platform
import pkg_handler
import traceback
import time
import signal
import shutil

from tempfile import TemporaryFile
from ConfigParser import NoOptionError
from ConfigParser import NoSectionError

__author__ = 'ThorN'
__version__ = '1.12'

modulePath = pkg_handler.resource_directory(__name__)

versionId = 'v%s' % __version__
version = '^8www.bigbrotherbot.net ^0(^8b3^0) ^9%s ^9[^IronPigeon^9]^3' % versionId

confdir = None
console = None

# STRINGS
B3_TITLE = 'BigBrotherBot (B3) %s' % versionId
B3_TITLE_SHORT = 'B3 %s' % versionId
B3_COPYRIGHT = 'Copyright © 2005 Michael "ThorN" Thornton'
B3_LICENSE = 'GNU General Public License v2'
B3_FORUM = 'http://forum.bigbrotherbot.net/'
B3_WEBSITE = 'http://www.bigbrotherbot.net'
B3_WIKI = 'http://wiki.bigbrotherbot.net/'
B3_CONFIG_GENERATOR = 'http://config.bigbrotherbot.net/'
B3_DOCUMENTATION = 'http://doc.bigbrotherbot.net/'
B3_DONATE = 'http://www.bigbrotherbot.net/donate'
B3_XLRSTATS = 'http://www.xlrstats.com/'
B3_PLUGIN_REPOSITORY = 'http://forum.bigbrotherbot.net/downloads/?cat=4'
B3_RSS = 'http://forum.bigbrotherbot.net/news-2/?type=rss;action=.xml'

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

# CUSTOM TYPES FOR DYNAMIC CASTING
STRING = STR = 1                        ## built-in string
INTEGER = INT = 2                       ## built-in integer
BOOLEAN = BOOL = 3                      ## built-in boolean
FLOAT = 4                               ## built-in float
LEVEL = 5                               ## b3.clients.Group level
DURATION = 6                            ## b3.functions.time2minutes conversion
PATH = 7                                ## b3.getAbsolutePath path conversion
TEMPLATE = 8                            ## b3.functions.vars2printf conversion
LIST = 9                                ## string split into list of tokens


def getHomePath():
    """
    Return the path to the B3 home directory.
    """
    path = os.path.normpath(os.path.expanduser('~/.b3')).decode(sys.getfilesystemencoding())

    ## RENAME v1.10.1 -> v1.10.7
    path_1 = os.path.normpath(os.path.expanduser('~/BigBrotherBot')).decode(sys.getfilesystemencoding())
    if os.path.isdir(path_1):
        shutil.move(path_1, path)

    ## CREATE IT IF IT DOESN'T EXISTS
    if not os.path.isdir(path):
        os.mkdir(path)

    return path


# APP HOME DIRECTORY
HOMEDIR = getHomePath()


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
    return decode_(os.path.normpath(os.path.expanduser(path)))


def getConfPath(decode=False, conf=None):
    """
    Return the path to the B3 main configuration directory.
    :param decode: if True will decode the path string using the default file system encoding before returning it.
    :param conf: the current configuration being used :type XmlConfigParser|CfgConfigParser|MainConfig|str:
    """
    if conf:
        if isinstance(conf, str):
            path = os.path.dirname(conf)
        elif isinstance(conf, XmlConfigParser) or isinstance(conf, CfgConfigParser) or isinstance(conf, MainConfig):
            path = os.path.dirname(conf.fileName)
        else:
            raise TypeError('invalid configuration type specified: expected str|XmlConfigParser|CfgConfigParser|MainConfig, got %s instead' % type(conf))
    else:
        path = confdir

    if not decode:
        return path
    return decode_(path)


def getAbsolutePath(path, decode=False, conf=None):
    """
    Return an absolute path name and expand the user prefix (~).
    :param path: the relative path we want to expand
    :param decode: if True will decode the path string using the default file system encoding before returning it
    :param conf: the current configuration being used :type XmlConfigParser|CfgConfigParser|MainConfig|str:
    """
    if path[0:4] == '@b3\\' or path[0:4] == '@b3/':
        path = os.path.join(getB3Path(decode=False), path[4:])
    elif path[0:6] == '@conf\\' or path[0:6] == '@conf/':
        path = os.path.join(getConfPath(decode=False, conf=conf), path[6:])
    elif path[0:6] == '@home\\' or path[0:6] == '@home/':
        path = os.path.join(HOMEDIR, path[6:])
    if not decode:
        return os.path.normpath(os.path.expanduser(path))
    return decode_(os.path.normpath(os.path.expanduser(path)))


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
    return __version__, getPlatform(), right_cut(platform.architecture()[0], 'bit')


def getB3versionString():
    """
    Return the B3 version as a string.
    """
    sversion = re.sub(r'\^[0-9a-z]', '', version)
    if main_is_frozen():
        vinfo = getB3versionInfo()
        sversion = '%s [%s%s]' % (sversion, vinfo[1], vinfo[2])
    return sversion


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


def getShortPath(filepath, decode=False, first_time=True):
    """
    Convert the given absolute path into a short path.
    Will replace path string with proper tokens (such as @b3, @conf, ~, ...)
    :param filepath: the path to convert
    :param decode: if True will decode the path string using the default file system encoding before returning it
    :param first_time: whether this is the first function call attempt or not
    :return: string
    """
    # NOTE: make sure to have os.path.sep at the end otherwise also files starting with 'b3' will be matched
    homepath = getAbsolutePath('@home/', decode) + os.path.sep
    if filepath.startswith(homepath):
        return filepath.replace(homepath, '@home' + os.path.sep)
    confpath = getAbsolutePath('@conf/', decode) + os.path.sep
    if filepath.startswith(confpath):
        return filepath.replace(confpath, '@conf' + os.path.sep)
    b3path = getAbsolutePath('@b3/', decode) + os.path.sep
    if filepath.startswith(b3path):
        return filepath.replace(b3path, '@b3' + os.path.sep)
    userpath = getAbsolutePath('~', decode) + os.path.sep
    if filepath.startswith(userpath):
        return filepath.replace(userpath, '~' + os.path.sep)
    if first_time:
        return getShortPath(filepath, not decode, False)
    return filepath


def loadParser(pname):
    """
    Load the parser module given it's name.
    :param pname: The parser name
    :return The parser module
    """
    name = 'b3.parsers.%s' % pname
    mod = __import__(name)
    components = name.split('.')
    components.append('%sParser' % pname.title())
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod


def start(mainconfig, options):
    """
    Main B3 startup.
    :param mainconfig: The B3 configuration file instance :type: b3.config.MainConfig
    :param options: command line options
    """
    clearscreen()
    global confdir
    confdir = os.path.dirname(mainconfig.fileName)

    sys.stdout.write('Starting B3      : %s\n' % getB3versionString())
    sys.stdout.write('Autorestart mode : %s\n' % ('ON' if options.autorestart else 'OFF'))

    sys.stdout.flush()

    try:
        update_channel = mainconfig.get('update', 'channel')
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

    # not real loading but the user will get what's configuration he is using
    sys.stdout.write('Loading config   : %s\n' % getShortPath(mainconfig.fileName, True))
    sys.stdout.flush()

    parsertype = mainconfig.get('b3', 'parser')
    sys.stdout.write('Loading parser   : %s\n' % parsertype)
    sys.stdout.flush()

    parser = loadParser(parsertype)
    global console
    console = parser(mainconfig, options)

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
        print 'EXITING: %s' % msg
        raise
    except Exception, msg:
        print 'ERROR: %s' % msg
        traceback.print_exc()
        sys.exit(223)


from b3.config import XmlConfigParser, CfgConfigParser, MainConfig
from b3.functions import clearscreen
from b3.functions import decode as decode_
from b3.functions import main_is_frozen
from b3.functions import right_cut
from b3.update import checkUpdate
