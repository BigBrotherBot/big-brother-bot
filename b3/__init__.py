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
#
# 2010/02/20 - Courgette
#    * user friendly handlling of parser import error. Prints a detailled
#      message and exits.
# 2010/02/24 - Courgette
#    * user friendly message on missing config file option
# 2010/03/20 - 1.1.0 - xl8or (added version)
#    * ability to disable automatic setup procedure when option -n, --nosetup is passed
# 2010/09/16 - 1.1.1 - GrosBedo
#    * can now run in a thread (functions profiler mode)
# 2010/10/20 - 1.1.2 - GrosBedo
#    * added TEAM_FREE for non team based gametypes (eg: deathmatch)
#


__author__ = 'ThorN'
__version__ = '1.1.2'

import pkg_handler
from b3.functions import main_is_frozen
from b3.update import checkUpdate
from b3.setup import Setup

__version__ = pkg_handler.version(__name__)
modulePath = pkg_handler.resource_directory(__name__)

import os, re, sys, traceback, time
import signal
import platform
import config
import ConfigParser

versionOs = os.name
versionId = 'v%s [%s]' % (__version__, versionOs)
version = '^8www.bigbrotherbot.net ^0(^8b3^0) ^9%s ^9[^3PoisonIvy^9]^3' % versionId


console = None
_confDir = None

# some constants
TEAM_UNKNOWN = -1
TEAM_FREE = 0 # Team free = no team based game (eg: deathmatch)
TEAM_SPEC = 1
TEAM_RED = 2
TEAM_BLUE = 3

STATE_DEAD = 1
STATE_ALIVE = 2
STATE_UNKNOWN = 3

#-----------------------------------------------------------------------------------------------------------------------
def loadParser(pname, configFile, nosetup=False):
    if pname == 'changeme':
        if nosetup:
            raise SystemExit('ERROR: Configfile not setup properly, Please run B3 with option: --setup or -s')
        else:
            Setup(configFile)
    name = 'b3.parsers.%s' % pname
    mod = __import__(name)
    components = name.split('.')
    components.append('%sParser' % pname.title())
    for comp in components[1:]:
        mod = getattr(mod, comp)

    return mod

#-----------------------------------------------------------------------------------------------------------------------
def getB3versionString():
    sversion = re.sub(r'\^[0-9a-z]', '', version)
    if main_is_frozen():
        sversion = "%s [Win32 standalone]" % sversion
    return sversion

def getB3Path():
    if main_is_frozen():
        # which happens when running from the py2exe build
        return os.path.dirname(sys.executable)
    return modulePath

def getConfPath():
    if _confDir is not None:
        return _confDir
    else:
        # try to get info from b3.console (assuming it is loaded)
        return os.path.dirname(console.config.fileName)


def getAbsolutePath(path):
    """Return an absolute path name and expand the user prefix (~)"""
    if path[0:4] == '@b3/':
        #print "B3 path: %s" % getB3Path()
        path = os.path.join(getB3Path(), path[4:])
    elif path[0:6] == '@conf/':
        path = os.path.join(getConfPath(), path[6:])
    return os.path.normpath(os.path.expanduser(path))

def start(configFile, nosetup=False):
    configFile = getAbsolutePath(configFile)
    clearScreen()

    print 'Starting %s\n' % getB3versionString()

    conf = None
    if os.path.exists(configFile):
        print 'Using config file: %s' % configFile
        global _confDir
        _confDir = os.path.dirname(configFile)
        #print 'Config dir is        : %s' % _confDir
        conf = config.load(configFile)
    else:
        # This happens when a config was entered on the commandline, but it does not exist
        if nosetup:
            raise SystemExit('Could not find config file %s' % configFile)
        else:
            Setup(configFile)


    # Check if a newer version of B3 is available
    update_channel = None
    try:
        update_channel = conf.get('update', 'channel')
    except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
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
            raise SystemExit('You must supply a parser')

        try:
            parser = loadParser(parserType, configFile, nosetup)
        except ImportError, err:
            raise SystemExit("CRITICAL: Cannot find parser '%s'. Check you main config file (b3.xml)\nB3 failed to start.\n%r"% (parserType, err))
    
        extplugins_dir = conf.getpath('plugins', 'external_dir')
        print "Using external plugin directory: %s" % extplugins_dir
        
        global console
        console = parser(conf)

    except ConfigParser.NoOptionError, err:
        raise SystemExit("CRITICAL: option %r not found in section %r. Correct your config file %s" % (err.option, err.section, configFile))


    def termSignalHandler(signum, frame):
        console.bot("TERM signal received. Shutting down")
        console.shutdown()
        raise SystemExit(222)
    try: # necessary if using the functions profiler, because signal.signal cannot be used in threads
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
    if platform.system() in ('Windows', 'Microsoft'):
        os.system('cls')
    else:
        os.system('clear')
