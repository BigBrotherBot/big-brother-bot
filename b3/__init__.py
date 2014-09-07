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
# 2014/09/06 - 1.2.1    - Fenix     - removed external_dir configuration value loading from b3 main configuration file
#                                     as it is not needed anymore

import os
import re
import sys
import pkg_handler
import traceback
import time
import signal
import platform
import config

from b3.functions import main_is_frozen
from b3.update import checkUpdate
from b3.setup import Setup
from ConfigParser import NoOptionError
from ConfigParser import NoSectionError

__author__ = 'ThorN'
__version__ = pkg_handler.version(__name__)

modulePath = pkg_handler.resource_directory(__name__)

versionOs = os.name
versionId = 'v%s [%s]' % (__version__, versionOs)
version = '^8www.bigbrotherbot.net ^0(^8b3^0) ^9%s ^9[^3PoisonIvy^9]^3' % versionId

_confDir = None
console = None

# some constants
TEAM_UNKNOWN = -1
TEAM_FREE = 0
TEAM_SPEC = 1
TEAM_RED = 2
TEAM_BLUE = 3

STATE_DEAD = 1
STATE_ALIVE = 2
STATE_UNKNOWN = 3


def loadParser(pname, configFile, nosetup=False):
    """
    Load the parser module given it's name.
    :param pname: The parser name
    :param configFile: The parser configuration file (namely b3.xml)
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

def getB3versionString():
    """
    Return the B3 version as a string.
    """
    sversion = re.sub(r'\^[0-9a-z]', '', version)
    if main_is_frozen():
        sversion = "%s [Win32 standalone]" % sversion
    return sversion

def getB3Path():
    """
    Return the path to the main B3 directory.
    """
    if main_is_frozen():
        # which happens when running from the py2exe build
        return os.path.dirname(sys.executable)
    return modulePath

def getConfPath():
    """
    Return the path to the main configuration file.
    """
    if _confDir is not None:
        return _confDir
    else:
        # try to get info from b3.console (assuming it is loaded)
        return os.path.dirname(console.config.fileName)


def getAbsolutePath(path):
    """
    Return an absolute path name and expand the user prefix (~).
    """
    if path[0:4] == '@b3/':
        #print "B3 path: %s" % getB3Path()
        path = os.path.join(getB3Path(), path[4:])
    elif path[0:6] == '@conf/':
        path = os.path.join(getConfPath(), path[6:])
    return os.path.normpath(os.path.expanduser(path))

def start(configFile, nosetup=False):
    """
    Main B3 startup.
    :param configFile: The B3 configuration file
    :param nosetup: Whether or not to run the B3 setup
    """
    configFile = getAbsolutePath(configFile)
    clearScreen()

    print 'Starting %s\n' % getB3versionString()

    conf = None
    if os.path.exists(configFile):
        print 'Using config file: %s' % configFile
        global _confDir
        _confDir = os.path.dirname(configFile)
        conf = config.MainConfig(config.load(configFile))
    else:
        # this happens when a config was entered on
        # the commandline, but it does not exist
        if nosetup:
            raise SystemExit('ERROR: could not find config file %s' % configFile)
        Setup(configFile)

    # check if a newer version of B3 is available
    update_channel = None

    try:
        update_channel = conf.get('update', 'channel')
    except (NoSectionError, NoOptionError):
        pass

    if update_channel == 'skip':
        print "Skipping check if a update is available."
    else:
        _update = checkUpdate(__version__, channel=update_channel, singleLine=False, showErrormsg=True)
        if _update:
            print _update
            time.sleep(5)
        else:
            print "...no update available."
            time.sleep(1)

    try:

        parserType = conf.get('b3', 'parser')
        if not parserType:
            raise SystemExit('ERROR: you must supply a parser')

        try:
            parser = loadParser(parserType, configFile, nosetup)
        except ImportError, err:
            raise SystemExit("CRITICAL: could not find parser '%s': check you main config file (b3.xml)\n"
                             "B3 failed to start.\n%r" % (parserType, err))
        
        global console
        console = parser(conf)

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
    except:
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
    if platform.system() in ('Windows', 'Microsoft'):
        os.system('cls')
    else:
        os.system('clear')