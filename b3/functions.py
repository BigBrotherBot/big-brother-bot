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
# $Id: functions.py 102 2006-04-14 06:46:03Z thorn $

__author__  = 'ThorN'
__version__ = '1.0.0'

import re

#--------------------------------------------------------------------------------------------------
def splitDSN(url):
	m = re.match(r'^(?:(?P<protocol>[a-z]+)://)?(?:(?P<user>[^@:]+)(?::(?P<password>[^@]+))?@)?(?P<host>[^/:]+)?(?::(?P<port>\d+))?(?P<path>.*)', url)
	if not m:
		return None

	g = m.groupdict()
	if g['port']:
		g['port'] = int(g['port'])

	if not g['protocol']:
		g['protocol'] = 'file'
	if g['protocol'] == 'file':
		if g['host'] and g['path']:
			g['path'] = '%s%s' % (g['host'], g['path'])
			g['host'] = None
		elif g['host']:
			g['path'] = g['host']
			g['host'] = None
	elif g['protocol'] == 'exec':
		if g['host'] and g['path']:
			g['path'] = '%s/%s' % (g['host'], g['path'])
			g['host'] = None
		elif g['host']:
			g['path'] = g['host']
			g['host'] = None

	return g

#--------------------------------------------------------------------------------------------------
def minutes2int(mins):
	if re.match('^[0-9.]+$', mins):
		return round(float(mins), 2)
	else:
		return 0

#--------------------------------------------------------------------------------------------------
def time2minutes(timeStr):
	if not timeStr:
		return 0
	elif type(timeStr) is int:
		return timeStr

	timeStr = str(timeStr)
	if not timeStr:
		return 0
	elif timeStr[-1:] == 'h':
		return minutes2int(timeStr[:-1]) * 60
	elif timeStr[-1:] == 'm':
		return minutes2int(timeStr[:-1])
	elif timeStr[-1:] == 's':
		return minutes2int(timeStr[:-1]) / 60
	elif timeStr[-1:] == 'd':
		return minutes2int(timeStr[:-1]) * 60 * 24
	elif timeStr[-1:] == 'w':
		return minutes2int(timeStr[:-1]) * 60 * 24 * 7
	else:
		return minutes2int(timeStr)

def minutesStr(timeStr):
	mins = time2minutes(timeStr)

	s = ''
	if mins < 1:
		num = round(mins * 60, 2)
		s = '%s second' % num
	elif mins < 60:
		num = round(mins, 2)
		s = '%s minute' % num
	elif mins < 1440:
		num = round(mins / 60, 2)
		s = '%s hour' % num
	elif mins < 10080:
		num = round((mins / 60) / 24, 2)
		s = '%s day' % num
	elif mins < 525600:
		num = round(((mins / 60) / 24) / 7, 2)
		s = '%s week' % num
	else:
		num = round(((mins / 60) / 24) / 365, 2)
		s = '%s year' % num

	if num != 1.0:
		s += 's'

	return s

def vars2printf(inputStr):
	return re.sub(r'\$([a-zA-Z]+)', r'%(\1)s', inputStr)
	
if __name__ == '__main__':
    print splitDSN('sqlite://c|/mydatabase/test.db')