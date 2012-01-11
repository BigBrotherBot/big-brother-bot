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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
# change log :
# 22/02/2009 - 1.2.1 - Courgette
# - fix the compatibility issue with ElementTree  and display an explicit
#    error message to avoid noobish questions on B3 forums :P
# 14/11/2009 - 1.2.2 - Courgette
# - detect xml parsing errors and raise a specific exception in that case
# 22/11/2009 - 1.2.3 - Courgette
# - fix bug with resolution of @conf on linux
# 29/11/2009 - 1.3.0 - Courgette
# XmlConfigParser can also be parsed from string
# 20/12/2009 - 1.3.1 - Courgette
# Fix bug in resolving @b3 which was failing for the win32 standalone release
# 03/12/2011 - 1.3.2 - Courgette
# Fixes xlr8or/big-brother-bot#18 : @conf in XML only works when b3_run.py config parameter contains path component


__author__  = 'ThorN'
__version__ = '1.3.2'

import sys, time
import b3
from xml.parsers.expat import ExpatError

try:
    from b3.lib.elementtree import ElementTree
except ImportError, err:
    from xml.etree import ElementTree
except ImportError, err:
    sys.stderr.write("""FATAL ERROR : Cannot load elementtree
  Check that you have installed ElementTree.
  On Linux Debian : apt-get install python-elementtree
  """)
    sys.exit(1)

import ConfigParser
import os
import b3.functions

class XmlConfigParser:
    """\
    A config parser class that mimics the ConfigParser settings but reads
    from an XML format
    """

    _xml = None
    _settings = None

    fileName = ''
    fileMtime = 0

    def readfp(self, fp):
        """\
        Read the xml config file from a file pointer
        """
        try:
            self._xml = ElementTree.parse(fp)
        except ExpatError, e:
            raise ConfigFileNotValid("%s" % e)

        self._loadSettings()

    def setXml(self, xml):
        """\
        Read the xml config file from a string
        """
        self._xml = ElementTree.fromstring(xml)

        self._loadSettings()

    def _loadSettings(self):
        self._settings = {}
        for settings in self._xml.findall("./settings"):
            section = settings.get('name')

            self._settings[section] = {}

            for setting in settings.findall("./set"):
                name  = setting.get('name')
                value = setting.text

                self._settings[section][name] = value


    def get(self, section, setting=None, dummy=False):
        if setting == None:
            # parse as xpath
            return self._xml.findall(section)
        else:
            try:
                return self._settings[section][setting]
            except KeyError:
                raise ConfigParser.NoOptionError(setting, section)

    def getTextTemplate(self, section, setting=None, **kwargs):
        value = b3.functions.vars2printf(self.get(section, setting, True)).strip()
        if len(kwargs):        
            return value % kwargs
        else:
            return value

    def getDuration(self, section, setting=None):
        value = self.get(section, setting).strip()
        return b3.functions.time2minutes(value)

    def getint(self, section, setting):
        return int(self.get(section, setting))

    def getfloat(self, section, setting):
        return float(self.get(section, setting))

    def getboolean(self, section, setting):
        value = self.get(section, setting).lower()

        if value in ('yes', '1', 'on', 'true'):
            return True
        elif value in ('no', '0', 'off', 'false'):
            return False
        else:
            raise ValueError('[%s].%s = %s is not a boolean value' % (section, setting, value))

    def sections(self):
        return self._settings.keys()

    def options(self, section):
        return self._settings[section].keys()

    def has_section(self, section):
        try:
            self._settings[section]
        except KeyError:
            return False
        else:
            return True

    def has_option(self, section, setting):
        try:
            self._settings[section][setting]
        except KeyError:
            return False
        else:
            return True

    def items(self, section):
        return self._settings[section].items()

    def getpath(self, section, setting):
        """Return an absolute path name and expand the user prefix (~)"""
        path = self.get(section, setting)

        if path[0:3] == '@b3':
            path = "%s/%s" % (b3.getB3Path(), path[3:])
        elif path[0:6] == '@conf/' or path[0:6] == '@conf\\':
            path = os.path.join(b3.getConfPath(), path[6:])

        return os.path.normpath(os.path.expanduser(path))

    def load(self, fileName):

        if not os.path.isfile(fileName):
            raise ConfigFileNotFound(fileName)

        f = file(fileName, 'r')
        self.readfp(f)
        f.close()

        self.fileName  = fileName
        self.fileMtime = os.path.getmtime(self.fileName)

        return True

    def loadFromString(self, xmlstring):
        """\
        Read the xml config from a string
        """
        
        self.fileName  = None
        self.fileMtime = time.time()
        
        try:
            self._xml = ElementTree.XML(xmlstring)
        except ExpatError, e:
            raise ConfigFileNotValid("%s" % e)

        self._loadSettings()
        return True

    def save(self):
        # not implemented
        return True

    def set(self, section, option, value):
        # not implemented
        pass
        

class CfgConfigParser(ConfigParser.ConfigParser):
    """\
    A config parser class that mimics the ConfigParser, reads the cfg format
    """

    fileName = ''
    fileMtime = 0

    ## @todo Use actual module path
    def getpath(self, section, setting):
        """Return an absolute path name and expand the user prefix (~)"""
        path = self.get(section, setting)

        if path[0:3] == '@b3':
            # relative path to the b3 module directory
            path = path[1:]
        elif path[0:6] == '@conf/' or path[0:6] == '@conf\\':
            path = "%s/%s" % (b3.getConfPath(), path[5:])

        return os.path.normpath(os.path.expanduser(path))

    def load(self, fileName):
        f = file(fileName, 'r')
        self.readfp(f)
        f.close()

        self.fileName  = fileName
        self.fileMtime = os.path.getmtime(self.fileName)

        return True

    def save(self):
        f = file(self.fileName, 'w')
        self.write(f)
        f.close()

        return True

    def getTextTemplate(self, section, setting=None, **kwargs):
        value = b3.functions.vars2printf(self.get(section, setting, True)).strip()
        if len(kwargs):        
            return value % kwargs
        else:
            return value


def load(fileName):
    if os.path.splitext(fileName)[1].lower() == '.xml':
        config = XmlConfigParser()
    else:
        config = CfgConfigParser()

    fileName = os.path.normpath(fileName)
    if fileName[0:4] == '@b3\\' or fileName[0:4] == '@b3/':
        fileName = os.path.normpath("%s/%s" % (b3.getB3Path(), fileName[3:]))
    elif fileName[0:6] == '@conf\\' or fileName[0:6] == '@conf/':
        fileName = os.path.normpath("%s/%s" % (b3.getConfPath(), fileName[5:]))

    if config.load(fileName):
        return config
    else:
        return None

class ConfigFileNotFound(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
class ConfigFileNotValid(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

        
if __name__ == '__main__':
    c = load(r'c:\temp\cod.xml')
    print c.get('server', 'punkbuster')

    if not c.has_option('server', 'punkbuster') or c.getboolean('server', 'punkbuster'):
        print 'Use PB'