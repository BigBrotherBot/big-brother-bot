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
# 22/02/2009 - 1.2.1 - Courgette - fix the compatibility issue with ElementTree  and display an explicit
#                                  error message to avoid noobish questions on B3 forums :P
# 14/11/2009 - 1.2.2 - Courgette - detect xml parsing errors and raise a specific exception in that case
# 22/11/2009 - 1.2.3 - Courgette - fix bug with resolution of @conf on linux
# 29/11/2009 - 1.3.0 - Courgette - XmlConfigParser can also be parsed from string
# 20/12/2009 - 1.3.1 - Courgette - fix bug in resolving @b3 which was failing for the win32 standalone release
# 03/12/2011 - 1.3.2 - Courgette - fixes xlr8or/big-brother-bot#18 : @conf in XML only works when b3_run.py config
#                                  parameter contains path component
# 31/03/2012 - 1.3.3 - Courgette - change behavior of XmlConfigParser methods getboolean, getint, getfloat when
#                                  config value is an empty string
# 11/04/2012 - 1.4   - Courgette - CfgConfigParser now implements methods getDuration, getboolean,
#                                  getpath, load_from_string
# 10/04/2013 - 1.4.1 - Courgette - fix ConfigFileNotFound and ConfigFileNotValid __str__ method
# 19/07/2014 - 1.5   - Fenix     - syntax cleanup
#                                - declared get method in B3ConfigParserMixin for design consistency
#                                - added stub constructor in XmlConfigParser
# 06/09/2014 - 1.6   - Fenix     - added 'allow_no_value' keyword to CfgConfigParser constructor so we can load
#                                  plugins which don't specify a configuration file

__author__  = 'ThorN, Courgette, Fenix'
__version__ = '1.6'

import os
import time
import b3
import b3.functions
import ConfigParser

try:
    from xml.etree import cElementTree as ElementTree
except ImportError:
    from xml.etree import ElementTree


class B3ConfigParserMixin:
    """
    Mixin implementing ConfigParser methods more useful for B3 business.
    """
    def get(self, *args, **kwargs):
        """
        Return a configuration value as a string.
        """
        raise NotImplementedError

    def getboolean(self, section, setting):
        """
        Return a configuration value as a boolean.
        :param section: The configuration file section.
        :param setting: The configuration file setting.
        """
        value_raw = self.get(section, setting)
        value = value_raw.lower() if value_raw else ''
        if value in ('yes', '1', 'on', 'true'):
            return True
        elif value in ('no', '0', 'off', 'false'):
            return False
        else:
            raise ValueError("%s.%s : '%s' is not a boolean value" % (section, setting, value))

    def getDuration(self, section, setting=None):
        """
        Return a configuration value parsing the duration time
        notation and converting the value into minutes.
        :param section: The configuration file section.
        :param setting: The configuration file setting.
        """
        value = self.get(section, setting).strip()
        return b3.functions.time2minutes(value)

    def getpath(self, section, setting):
        """
        Return an absolute path name and expand the user prefix (~).
        :param section: The configuration file section.
        :param setting: The configuration file setting.
        """
        path = self.get(section, setting)
        if path[0:3] == '@b3':
            path = "%s/%s" % (b3.getB3Path(), path[3:])
        elif path[0:6] == '@conf/' or path[0:6] == '@conf\\':
            path = os.path.join(b3.getConfPath(), path[6:])
        return os.path.normpath(os.path.expanduser(path))

    def getTextTemplate(self, section, setting=None, **kwargs):
        """
        Return a text template from the configuration file: will
        substitute all the tokens with the given kwargs.
        :param section: The configuration file section.
        :param setting: The configuration file setting.
        :param kwargs: A dict with variables used for string substitution.
        """
        value = b3.functions.vars2printf(self.get(section, setting, True)).strip()
        if len(kwargs):
            return value % kwargs
        return value


class XmlConfigParser(B3ConfigParserMixin):
    """
    A config parser class that mimics the ConfigParser
    settings but reads from an XML format.
    """
    _xml = None
    _settings = None

    fileName = ''
    fileMtime = 0

    def __init__(self):
        """
        Object constructor.
        """
        pass

    def _loadSettings(self):
        """
        Load settings section from the configuration
        file into a dictionary.
        """
        self._settings = {}
        for settings in self._xml.findall("./settings"):
            section = settings.get('name')
            self._settings[section] = {}
            for setting in settings.findall("./set"):
                name = setting.get('name')
                value = setting.text
                self._settings[section][name] = value

    def readfp(self, fp):
        """
        Read the XML config file from a file pointer.
        :param fp: The XML file pointer.
        """
        try:
            self._xml = ElementTree.parse(fp)
        except Exception, e:
            raise ConfigFileNotValid("%s" % e)

        self._loadSettings()

    def setXml(self, xml):
        """
        Read the xml config file from a string.
        :param xml: The XML string.
        """
        self._xml = ElementTree.fromstring(xml)

        self._loadSettings()

    def get(self, section, setting=None, dummy=False):
        """
        Return a configuration value as a string.
        :param section: The configuration file section.
        :param setting: The configuration file setting.
        :return basestring
        """
        if setting is None:
            # parse as xpath
            return self._xml.findall(section)
        else:
            try:
                data = self._settings[section][setting]
                if data is None:
                    return ''
                else:
                    return data
            except KeyError:
                raise ConfigParser.NoOptionError(setting, section)

    def getint(self, section, setting):
        """
        Return a configuration value as an integer.
        :param section: The configuration file section.
        :param setting: The configuration file setting.
        :return int
        """
        value = self.get(section, setting)
        if value is None:
            raise ValueError("%s.%s : is not an integer" % (section, setting))
        return int(self.get(section, setting))

    def getfloat(self, section, setting):
        """
        Return a configuration value as a floating point number.
        :param section: The configuration file section.
        :param setting: The configuration file setting.
        :return float
        """
        value = self.get(section, setting)
        if value is None:
            raise ValueError("%s.%s : is not a number" % (section, setting))
        return float(self.get(section, setting))

    def sections(self):
        """
        Return the list of sections of the configuration file.
        :return list
        """
        return self._settings.keys()

    def options(self, section):
        """
        Return the list of options in the given section.
        :return list
        """
        return self._settings[section].keys()

    def has_section(self, section):
        """
        Tells whether the given section exists in the configuration file.
        :return True if the section exists, False otherwise.
        """
        try:
            self._settings[section]
        except KeyError:
            return False
        else:
            return True

    def has_option(self, section, setting):
        """
        Tells whether the given section/setting combination exists in the configuration file.
        :return True if the section/settings combination exists, False otherwise.
        """
        try:
            self._settings[section][setting]
        except KeyError:
            return False
        else:
            return True

    def items(self, section):
        """
        Return all the elements of the given section.
        """
        return self._settings[section].items()

    def load(self, filename):
        """
        Load a configuration file.
        :param filename: The configuration file name.
        """
        if not os.path.isfile(filename):
            raise ConfigFileNotFound(filename)

        f = file(filename, 'r')
        self.readfp(f)
        f.close()

        self.fileName = filename
        self.fileMtime = os.path.getmtime(self.fileName)
        return True

    def loadFromString(self, xmlstring):
        """
        Read the XML config from a string.
        """
        self.fileName = None
        self.fileMtime = time.time()

        try:
            self._xml = ElementTree.XML(xmlstring)
        except Exception, e:
            raise ConfigFileNotValid("%s" % e)

        self._loadSettings()
        return True

    def save(self):
        # not implemented
        return True

    def set(self, section, option, value):
        # not implemented
        pass


class CfgConfigParser(B3ConfigParserMixin, ConfigParser.ConfigParser):
    """
    A config parser class that mimics the ConfigParser, reads the cfg format.
    """
    fileName = ''
    fileMtime = 0

    def __init__(self, allow_no_value=False):
        """
        Object constructor.
        :param allow_no_value: Whether or not to allow empty values in configuration sections
        """
        ConfigParser.ConfigParser.__init__(self, allow_no_value=allow_no_value)

    def get(self, section, option, *args, **kwargs):
        """
        Return a configuration value as a string.
        """
        try:
            return ConfigParser.ConfigParser.get(self, section, option, *args, **kwargs)
        except ConfigParser.NoSectionError:
            # plugins are used to only catch NoOptionError
            raise ConfigParser.NoOptionError(option, section)

    def load(self, filename):
        """
        Load a configuration file.
        """
        f = file(filename, 'r')
        self.readfp(f)
        f.close()
        self.fileName = filename
        self.fileMtime = os.path.getmtime(self.fileName)
        return True

    def loadFromString(self, cfg_string):
        """
        Read the cfg config from a string.
        """
        import StringIO
        fp = StringIO.StringIO(cfg_string)
        self.readfp(fp)
        fp.close()
        self.fileName = None
        self.fileMtime = time.time()
        return True

    def save(self):
        """
        Save the configuration file.
        """
        f = file(self.fileName, 'w')
        self.write(f)
        f.close()
        return True


def load(filename):
    """
    Load a configuration file.
    Will instantiate the correct configuration object parser.
    """
    if os.path.splitext(filename)[1].lower() == '.xml':
        config = XmlConfigParser()
    else:
        # allow the use of empty keys to support the new b3.ini configuration file
        config = CfgConfigParser(allow_no_value=True)

    filename = os.path.normpath(filename)
    if filename[0:4] == '@b3\\' or filename[0:4] == '@b3/':
        filename = os.path.normpath("%s/%s" % (b3.getB3Path(), filename[3:]))
    elif filename[0:6] == '@conf\\' or filename[0:6] == '@conf/':
        filename = os.path.normpath("%s/%s" % (b3.getConfPath(), filename[5:]))

    # return the config if it can be loaded
    return config if config.load(filename) else None


class ConfigFileNotFound(Exception):
    """
    Raised whenever the configuration file can't be found.
    """
    def __init__(self, message):
        Exception.__init__(self, message)
        
    def __str__(self):
        return repr(self.message)


class ConfigFileNotValid(Exception):
    """
    Raised whenever we are parsing an invalid configuration file.
    """
    def __init__(self, message):
        Exception.__init__(self, message)
        
    def __str__(self):
        return repr(self.message)
