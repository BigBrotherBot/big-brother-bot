#
# BigBrotherBot(B3) (www.bigbrotherbot.com)
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
# 27/03/2010 - 1.2.1 - xlr8or - set default port for mysql

__author__    = 'ThorN, xlr8or'
__version__ = '1.2.1'

import re, os, sys, imp, string, urllib2
from lib.elementtree import ElementTree
from distutils import version
import time




def checkUpdate(currentVersion, singleLine=True, showErrormsg=False):
    """
    check if an update of B3 is available
    """
    if not singleLine:
        sys.stdout.write("checking for updates... \n")

    message = None
    errorMessage = None
    try:
        f = urllib2.urlopen('http://www.bigbrotherbot.com/version.xml')
        _xml = ElementTree.parse(f)
        latestVersion = _xml.getroot().text
        _lver = version.LooseVersion(latestVersion)
        _cver = version.LooseVersion(currentVersion)
        if _cver < _lver:
            if singleLine:
                message = "*** NOTICE: A newer version of B3 is available. See www.bigbrotherbot.com! ***"
            else:
                message = """
         _\|/_
         (o o)
 +----oOO-{_}-OOo---------------------+
 |                                    |
 |                                    |
 | A newer version of B3 is available |
 |     See www.bigbrotherbot.com      |
 |                                    |
 |                                    |
 +------------------------------------+
 
"""
    except IOError, e:
        if hasattr(e, 'reason'):
            errorMessage = "%s" % e.reason
        elif hasattr(e, 'code'):
            errorMessage = "error code: %s" % e.code
        else:
            errorMessage = "%s" % e
    
    if errorMessage and showErrormsg:
        return errorMessage
    elif message:
        return message
    else:
        return None


#--------------------------------------------------------------------------------------------------
def main_is_frozen():
    """detect if b3 is running from b3_run.exe"""
    return (hasattr(sys, "frozen") or # new py2exe
        hasattr(sys, "importers") or # old py2exe
        imp.is_frozen("__main__")) # tools/freeze

#--------------------------------------------------------------------------------------------------
def splitDSN(url):
    m = re.match(r'^(?:(?P<protocol>[a-z]+)://)?(?:(?P<user>[^@:]+)(?::(?P<password>[^@]+))?@)?(?P<host>[^/:]+)?(?::(?P<port>\d+))?(?P<path>.*)', url)
    if not m:
        return None

    g = m.groupdict()

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

    if g['port']:
        g['port'] = int(g['port'])
    elif g['protocol'] == 'mysql':
        g['port'] = 3306

    return g
#--------------------------------------------------------------------------------------------------

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

#--------------------------------------------------------------------------------------------------
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
  
#--------------------------------------------------------------------------------------------------
def levenshteinDistance(a,b):
    c = {}
    n = len(a); m = len(b)

    for i in range(0,n+1):
        c[i,0] = i
    for j in range(0,m+1):
        c[0,j] = j

    for i in range(1,n+1):
        for j in range(1,m+1):
            x = c[i-1,j]+1
            y = c[i,j-1]+1
            if a[i-1] == b[j-1]:
                z = c[i-1,j-1]
            else:
                z = c[i-1,j-1]+1
            c[i,j] = min(x,y,z)
    return c[n,m]


def soundex(str):
    """Return the soundex value to a string argument."""
    
    IGNORE = "~!@#$%^&*()_+=-`[]\|;:'/?.,<>\" \t\f\v"
    TABLE  = string.maketrans('ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                          '01230120022455012623010202')

    str = string.strip(string.upper(str))
    if not str:
        return "Z000"
    str2 = str[0]
    str = string.translate(str, TABLE, IGNORE)
    if not str:
        return "Z000"
    prev = str[0]
    for x in str[1:]:
        if x != prev and x != "0":
                str2 = str2 + x
        prev = x
    # pad with zeros
    str2 = str2+"0000"
    return str2[:4]


def fuzzyGuidMatch(a, b):
    a = a.upper()
    b = b.upper()

    if a == b:
        return True
    
    # put the longest first
    if len(b) > len(a):
        a, b = b, a

    if len(a) == 32 and len(b) == 31:
        # Looks like a truncated id, check using levenshtein
        # Use levenshteinDistance to find GUIDs off by 1 char, as caused by a bug in COD Punkbuster
        distance = levenshteinDistance(a, b)
        if distance <= 1:
            return True
    
    return False

#--------------------------------------------------------------------------------------------------
def sanitizeMe(s):
    sanitized = re.sub(r'[\x00-\x1F]|[\x7F-\xff]', '?', str(s))
    return sanitized



if __name__ == '__main__':
    print splitDSN('sqlite://c|/mydatabase/test.db')

    compare = [
        ('098f6bcd4621d373cade4e832627b4f6', '098f6bcd4621d373cade4e832627b4f6'),
        ('098f6bcd4621d373cade4e832627b4f6', '098f6bcd4621d373cade4e832627b4f'),
        ('098f6bcd4621d373cade4e832627bf6', '098f6bcd4621d373cade4e832627b4f6'),
        ('098f6bcd4621d373cade4e832627b4f6', '098f6bcd4621d373cde4e832627b4f6'),
        ('098f6bcd4621d373cade4e832627b4f6', '098f6bcd46d373cade4e832627b4f6'),
        ('098f6bcd4621d373cade4832627b4f6', '098f6bcd4621d73cade4e832627b4f6'),
        ('098F6BCD4621D373CADE4E832627B4F6', '098f6bcd4621d373cade4e832627b4f6'),
    ]


    for a,b in compare:
        print '%s <> %s = %s' % (a, b, fuzzyGuidMatch(a,b))
