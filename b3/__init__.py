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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA

__author__ = 'ThorN'

import pkg_handler
from b3.functions import main_is_frozen

__version__ = pkg_handler.version(__name__)
modulePath = pkg_handler.resource_directory(__name__)

import os, re, sys, traceback
import platform
import config

versionOs = os.name
versionId = 'v%s [%s]' % (__version__, versionOs)
version = '^8www.BigBrotherBot.com ^0(^8b3^0) ^9%s ^9(^3Daniel^9)^3' % versionId
sversion = re.sub(r'\^[0-9a-z]', '', version)

console = None
_confDir = None

# some constants
TEAM_UNKNOWN = -1
TEAM_SPEC = 1
TEAM_RED = 2
TEAM_BLUE = 3

STATE_DEAD = 1
STATE_ALIVE = 2
STATE_UNKNOWN = 3

#-----------------------------------------------------------------------------------------------------------------------
def loadParser(pname):
    if pname == 'changeme':
        raise SystemExit('ERROR: Please edit b3/conf/b3.xml before starting me up!')
    name = 'b3.parsers.%s' % pname
    mod = __import__(name)
    components = name.split('.')
    components.append('%sParser' % pname.title())
    for comp in components[1:]:
        mod = getattr(mod, comp)

    return mod

#-----------------------------------------------------------------------------------------------------------------------
def getB3Path():
    if main_is_frozen():
        # which happens when running from the py2exe build
        return os.path.dirname(sys.executable)
    return modulePath

def getConfPath():
    return _confDir


def getAbsolutePath(path):
    """Return an absolute path name and expand the user prefix (~)"""
    if path[0:4] == '@b3/':
        #print "B3 path: %s" % getB3Path()
        path = os.path.join(getB3Path(), path[4:])

    return os.path.normpath(os.path.expanduser(path))

def start(configFile):
    configFile = getAbsolutePath(configFile)
    if platform.system() != 'Windows':
        os.system('clear')
    print 'Starting %s\n' % sversion

    if os.path.exists(configFile):
        print 'Using config file: %s' % configFile
        global _confDir
        _confDir = os.path.dirname(configFile)
        #print 'Config dir is        : %s' % _confDir
        conf = config.load(configFile)
    else:
        raise SystemExit('Could not find config file %s' % configFile)

    parserType = conf.get('b3', 'parser')

    if not parserType:
        raise SystemExit('You must supply a parser')

    parser = loadParser(parserType)

    global console
    console = parser(conf)

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
        print 'Error: %s\n%s' % (msg, ''.join(traceback.format_list(traceback.extract_tb(sys.exc_info()[2]))))
        sys.exit(223)