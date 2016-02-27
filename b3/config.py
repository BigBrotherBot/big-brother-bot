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
# 06/09/2014 - 1.5.1 - Courgette - remove duplicated code by using b3.getAbsolutePath
# 07/09/2014 - 1.6   - Fenix     - added 'allow_no_value' keyword to CfgConfigParser constructor so we can load
#                                  plugins which don't specify a configuration file
# 07/09/2014 - 1.7   - Courgette - added MainConfig class to parser B3 main configuration file from .xml and .ini format
# 07/09/2014 - 1.7.1 - Fenix     - patch the RawConfigParser class when python 2.6 is used to run b3: this allows
#                                  python 2.6 to make use of the new feature of the RawConfigParser class that load
#                                  keys from configuration files with non specified values
#                                - return empty string instead of None in get() method: this fixes possible failures in
#                                  string replacements when we retrieve empty option from a .ini configuration file
# 15/01/2015 - 1.7.2 - Fenix     - Make sure users can't load 'admin', 'publist', 'ftpytail', 'sftpytail', 'httpytail'
#                                  as disabled from main B3 configuration file
# 22/01/2015 - 1.7.3 - Fenix     - added add_comment method to CfgConfigParser and overridden write() method
#                                  to properly write comments in a newly generated configuration file
# 03/03/2015 - 1.7.4 - Fenix     - removed python 2.6 support
# 03/03/2015 - 1.7.5 - Fenix     - moved exception classes in a separate module
# 19/03/2015 - 1.7.6 - Fenix     - raise NotImplementedError instead of NotImplemented
# 22/04/2015 - 1.7.7 - Fenix     - raise ConfigFileNotValid in ConfigParser.readfp for consistency with XmlConfigParser
#                                - added 'analyze()' method in MainConfig
# 26/05/2015 - 1.7.8 - Fenix     - changed analyze() to validate also storage protocol
# 17/06/2015 - 1.7.9 - Fenix     - fixed bad indent which was causing analyze() to generate false positives on admin plugin

__author__  = 'ThorN, Courgette, Fenix'
__version__ = '1.7.9'

import os
import re
import time
import b3
import b3.functions
import b3.exceptions
import b3.storage
import ConfigParser

try:
    from xml.etree import cElementTree as ElementTree
except ImportError:
    from xml.etree import ElementTree


ConfigFileNotFound = b3.exceptions.ConfigFileNotFound
ConfigFileNotValid = b3.exceptions.ConfigFileNotValid
NoOptionError = b3.exceptions.NoOptionError
NoSectionError = b3.exceptions.NoSectionError

# list of plugins that cannot be loaded as disabled from configuration file
MUST_HAVE_PLUGINS = ('admin', 'publist', 'ftpytail', 'sftpytail', 'httpytail')

class B3ConfigParserMixin(object):
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
        return b3.getAbsolutePath(self.get(section, setting), decode=True)

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

    def add_comment(self, section, comment):
        """
        Add a comment
        :param section: The section where to place the comment
        :param comment: The comment to add
        """
        if not section or section == "DEFAULT":
            sectdict = self._defaults
        else:
            try:
                sectdict = self._sections[section]
            except KeyError:
                raise ConfigParser.NoSectionError(section)
        sectdict['; %s' % (comment,)] = None

    def get(self, section, option, *args, **kwargs):
        """
        Return a configuration value as a string.
        """
        try:
            value = ConfigParser.ConfigParser.get(self, section, option, *args, **kwargs)
            if value is None:
                return ""
            return value
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

    def readfp(self, fp, filename=None):
        """
        Inherits from ConfigParser.ConfigParser to throw our custom exception if needed
        """
        try:
            ConfigParser.ConfigParser.readfp(self, fp, filename)
        except Exception, e:
            raise ConfigFileNotValid("%s" % e)

    def save(self):
        """
        Save the configuration file.
        """
        f = file(self.fileName, 'w')
        self.write(f)
        f.close()
        return True

    def write(self, fp):
        """
        Write an .ini-format representation of the configuration state.
        """
        if self._defaults:
            fp.write("[%s]\n" % ConfigParser.DEFAULTSECT)
            for (key, value) in self._defaults.items():
                self._write_item(fp, key, value)
            fp.write("\n")
        for section in self._sections:
            fp.write("[%s]\n" % section)
            for (key, value) in self._sections[section].items():
                self._write_item(fp, key, value)
            fp.write("\n")

    @staticmethod
    def _write_item(fp, key, value):
        if (key.startswith(';') or key.startswith('#')) and value is None:
            # consider multiline comments
            for line in key.split('\n'):
                line = b3.functions.left_cut(line, ';')
                line = b3.functions.left_cut(line, '#')
                fp.write("; %s\n" % (line.strip(),))
        else:
            if value is not None and str(value).strip() != '':
                fp.write("%s: %s\n" % (key, str(value).replace('\n', '\n\t')))
            else:
                fp.write("%s: \n" % key)

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

    filename = b3.getAbsolutePath(filename, True)

    # return the config if it can be loaded
    return config if config.load(filename) else None


class MainConfig(B3ConfigParserMixin):
    """
    Class to use to parse the B3 main config file.
    Responsible for reading the file either in xml or ini format.
    """
    def __init__(self, config_parser):
        self._config_parser = config_parser
        self._plugins = []
        if isinstance(self._config_parser, XmlConfigParser):
            self._init_plugins_from_xml()
        elif isinstance(self._config_parser, CfgConfigParser):
            self._init_plugins_from_cfg()
        else:
            raise NotImplementedError("unexpected config type: %r" % self._config_parser.__class__)

    def _init_plugins_from_xml(self):
        self._plugins = []
        for p in self._config_parser.get('plugins/plugin'):
            x = p.get('disabled')
            self._plugins.append({
                'name': p.get('name'),
                'conf': p.get('config'),
                'path': p.get('path'),
                'disabled':  x is not None and x not in MUST_HAVE_PLUGINS and x.lower() in ('yes', '1', 'on', 'true')
            })

    def _init_plugins_from_cfg(self):
        ## Load the list of disabled plugins
        try:
            disabled_plugins_raw = self._config_parser.get('b3', 'disabled_plugins')
        except ConfigParser.NoOptionError:
            disabled_plugins = []
        else:
            disabled_plugins = re.split('\W+', disabled_plugins_raw.lower())

        def get_custom_plugin_path(plugin_name):
            try:
                return self._config_parser.get('plugins_custom_path', plugin_name)
            except ConfigParser.NoOptionError:
                return None

        self._plugins = []
        if self._config_parser.has_section('plugins'):
            for name in self._config_parser.options('plugins'):
                self._plugins.append({
                    'name': name,
                    'conf': self._config_parser.get('plugins', name),
                    'path': get_custom_plugin_path(name),
                    'disabled': name.lower() in disabled_plugins and name.lower() not in MUST_HAVE_PLUGINS
                })

    def get_plugins(self):
        """
        :return: list[dict] A list of plugin settings as a dict.
            I.E.:
            [
                {'name': 'admin', 'conf': @conf/plugin_admin.ini, 'path': None, 'disabled': False},
                {'name': 'adv', 'conf': @conf/plugin_adv.xml, 'path': None, 'disabled': False},
            ]
        """
        return self._plugins

    def get_external_plugins_dir(self):
        """
        the directory path (as a string) where additional plugin modules can be found
        :return: str or ConfigParser.NoOptionError
        """
        if isinstance(self._config_parser, XmlConfigParser):
            return self._config_parser.getpath("plugins", "external_dir")
        elif isinstance(self._config_parser, CfgConfigParser):
            return self._config_parser.getpath("b3", "external_plugins_dir")
        else:
            raise NotImplementedError("unexpected config type: %r" % self._config_parser.__class__)

    def get(self, *args, **kwargs):
        """
        Override the get method defined in the B3ConfigParserMixin
        """
        return self._config_parser.get(*args, **kwargs)

    def analyze(self):
        """
        Analyze the main configuration file checking for common mistakes.
        This will mostly check configuration file values and will not perform any futher check related,
        i.e: connection with the database can be established using the provided dsn, rcon password is valid etc.
        Such validations needs to be handled somewhere else.
        :return: A list of strings highlighting problems found (so they can be logged/displayed easily)
        """
        analysis = []

        def _mandatory_option(section, option):
            if not self.has_option(section, option):
                analysis.append('missing configuration value %s::%s' % (section, option))

        _mandatory_option('b3', 'parser')
        _mandatory_option('b3', 'database')
        _mandatory_option('b3', 'bot_name')

        ## PARSER CHECK
        if self.has_option('b3', 'parser'):
            try:
                b3.functions.getModule('b3.parsers.%s' % self.get('b3', 'parser'))
            except ImportError:
                analysis.append('invalid parser specified in b3::parser (%s)' % self.get('b3', 'parser'))

        ## DSN DICT
        if self.has_option('b3', 'database'):
            dsndict = b3.functions.splitDSN(self.get('b3', 'database'))
            if not dsndict:
                analysis.append('invalid database source name specified in b3::database (%s)' % self.get('b3', 'database'))
            elif dsndict['protocol'] not in b3.storage.PROTOCOLS:
                analysis.append('invalid storage protocol specified in b3::database (%s) : '
                                'valid protocols are : %s' % (dsndict['protocol'], ', '.join(b3.storage.PROTOCOLS)))

        ## ADMIN PLUGIN CHECK
        has_admin = False
        has_admin_config = False
        for plugin in self.get_plugins():
            if plugin['name'] == 'admin':
                has_admin = True
                if plugin['conf']:
                    has_admin_config = True
                break

        if not has_admin:
            analysis.append('missing admin plugin in plugins section')
        elif not has_admin_config:
            analysis.append('missing configuration file for admin plugin')

        return analysis

    def __getattr__(self, name):
        """
        Act as a proxy in front of self._config_parser.
        Any attribute or method call which does not exists in this
        object (MainConfig) is then tried on the self._config_parser
        :param name: str Attribute or method name
        """
        if hasattr(self._config_parser, name):
            attr = getattr(self._config_parser, name)
            if hasattr(attr, '__call__'):
                def newfunc(*args, **kwargs):
                    return attr(*args, **kwargs)
                return newfunc
            else:
                return attr
        else:
            raise AttributeError(name)
