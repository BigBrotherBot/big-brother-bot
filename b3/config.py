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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
# $Id: config.py 6 2005-11-18 05:36:17Z thorn $

__author__  = 'ThorN'
__version__ = '1.2.0'

from elementtree import ElementTree
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
		self._xml = ElementTree.parse(fp)

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
			# releative path to the b3 module directory
			# TODO: use actual module path
			path = path[1:]

		return os.path.normpath(os.path.expanduser(path))

	def load(self, fileName):
		f = file(fileName, 'r')
		self.readfp(f)
		f.close()

		self.fileName  = fileName
		self.fileMtime = os.path.getmtime(self.fileName)

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

	def getpath(self, section, setting):
		"""Return an absolute path name and expand the user prefix (~)"""
		path = self.get(section, setting)

		if path[0:3] == '@b3':
			# releative path to the b3 module directory
			# TODO: use actual module path
			path = path[1:]

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

	if config.load(fileName):
		return config
	else:
		return None

if __name__ == '__main__':
    c = load(r'c:\temp\cod.xml')
    print c.get('server', 'punkbuster')

    if not c.has_option('server', 'punkbuster') or c.getboolean('server', 'punkbuster'):
        print 'Use PB'