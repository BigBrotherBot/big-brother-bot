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
# 27/03/2010 - 1.2.1 - xlr8or - set default port for mysql
# 11/04/2010 - 1.2.2 - Courgette - make splitDSN support usernames containing '@'
# 01/09/2010 - 1.3 - Courgette - make splitDSN add default ftp and sftp port
# 08/11/2010 - 1.3.1 - GrosBedo - vars2printf is now more robust against empty strings
# 01/12/2010 - 1.3.2 - Courgette - checkUpdate now uses a custom short timeout to
#   prevent blocking the bot when the B3 server is hanging
# 17/04/2011 - 1.3.3 - Courgette - make sanitizeMe unicode compliant
# 06/06/2011 - 1.4.0 - Courgette - add meanstdv()
# 07/06/2011 - 1.4.1 - Courgette - fix meanstdv()

__author__    = 'ThorN, xlr8or'
__version__   = '1.4.1'

import b3
import re
import os
import sys
import imp
import string
import urllib2
import json
from distutils import version


## url from where we can get the latest B3 version number
#URL_B3_LATEST_VERSION = 'http://www.bigbrotherbot.net/version.json'
URL_B3_LATEST_VERSION = 'http://www.cucurb.net/b3-version.json' # TODO: revert back to official website before public release

# supported update channels
UPDATE_CHANNEL_STABLE = 'stable'
UPDATE_CHANNEL_BETA = 'beta'
UPDATE_CHANNEL_DEV = 'dev'



def getModule(name):
    mod = __import__(name)
    components = name.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod




def checkUpdate(currentVersion, channel=UPDATE_CHANNEL_STABLE, singleLine=True, showErrormsg=False):
    """
    check if an update of B3 is available

    """

    class B3version(version.StrictVersion):
        """
        Version numbering for BigBrotherBot.
        Compared to version.StrictVersion this class allows version numbers such as :
            1.0dev
            1.0dev2
            1.0a
            1.0alpha
            1.0alpha34
            1.0b
            1.0b1
            1.0beta3
        And make sure that any 'dev' prerelease is inferior to any 'alpha' prerelease
        """
        def __init__(self, vstring=None):
            version.StrictVersion.__init__(self, vstring)

        version_re = re.compile(r'^(\d+) \. (\d+) (\. (\d+))? (([ab]|dev)(\d+)?)?$',
                                re.VERBOSE)

        def parse (self, vstring):
            match = self.version_re.match(vstring)
            if not match:
                raise ValueError, "invalid version number '%s'" % vstring

            (major, minor, patch, prerelease, prerelease_num) = \
                match.group(1, 2, 4, 6, 7)

            if patch:
                self.version = tuple(map(string.atoi, [major, minor, patch]))
            else:
                self.version = tuple(map(string.atoi, [major, minor]) + [0])

            if prerelease:
                if prerelease == "dev":
                    prerelease = "*" # we want that dev < [a]lpha < [b]eta
                self.prerelease = (prerelease[0], string.atoi(prerelease_num if prerelease_num else '0'))
            else:
                self.prerelease = None

    timeout = 4

    if not singleLine:
        sys.stdout.write("checking for updates... \n")

    message = None
    errorMessage = None
    version_info = None
    try:
        json_data = urllib2.urlopen(URL_B3_LATEST_VERSION, timeout=timeout).read()
        version_info = json.loads(json_data)
    except IOError, e:
        if hasattr(e, 'reason'):
            errorMessage = "%s" % e.reason
        elif hasattr(e, 'code'):
            errorMessage = "error code: %s" % e.code
        else:
            errorMessage = "%s" % e
    except Exception, e:
        errorMessage = repr(e)
    else:
        latestVersion = None
        latestUrl = None
        channels = {}
        try:
            channels = version_info['B3']['channels']
        except KeyError, err:
            errorMessage = repr(err) + ". %s" % version_info
        else:
            if channel not in channels:
                errorMessage = "unknown channel '%s'. Expecting one of '%s'"  % (channel, ", '".join(channels.keys()))
            else:
                try:
                    latestVersion = channels[channel]['latest-version']
                except KeyError:
                    errorMessage = repr(err) + ". %s" % version_info

        if not errorMessage:
            try:
                latestUrl = version_info['B3']['channels'][channel]['url']
            except KeyError:
                latestUrl = "www.bigbrotherbot.net"

            not singleLine and sys.stdout.write("latest B3 %s version is %s\n" % (channel, latestVersion))
            _lver = B3version(latestVersion)
            _cver = B3version(currentVersion)
            if _cver < _lver:
                if singleLine:
                    message = "*** NOTICE: B3 %s is available. See %s ! ***" % (latestVersion, latestUrl)
                else:
                    message = """
                 _\|/_
                 (o o)    {version:^21}
         +----oOO---OOo-----------------------+
         |                                    |
         |                                    |
         | A newer version of B3 is available |
         |                                    |
         | {url:^34} |
         |                                    |
         +------------------------------------+

        """.format(version=latestVersion, url=latestUrl)

    if errorMessage and showErrormsg:
        return "Could not check updates. %s" % errorMessage
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
    m = re.match(r'^(?:(?P<protocol>[a-z]+)://)?(?:(?P<user>[^:]+)(?::(?P<password>[^@]+))?@)?(?P<host>[^/:]+)?(?::(?P<port>\d+))?(?P<path>.*)', url)
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
    elif g['protocol'] == 'ftp':
        g['port'] = 21
    elif g['protocol'] == 'sftp':
        g['port'] = 22
    elif g['protocol'] == 'mysql':
        g['port'] = 3306

    return g

#--------------------------------------------------------------------------------------------------
def confirm(client):
    msg = 'No confirmation...'
    try:
        #first test again known guids
        f = urllib2.urlopen('http://www.bigbrotherbot.net/confirm.php?uid=%s' %client.guid)
        response = f.read()
        if not response == 'Error' and not response == 'False':
            msg = '%s is confirmed to be %s!' %(client.name, response)
        else:
            #if it fails, try ip (must be static)
            f = urllib2.urlopen('http://www.bigbrotherbot.net/confirm.php?ip=%s' %client.ip)
            response = f.read()
            if not response == 'Error' and not response == 'False':
                msg = '%s is confirmed to be %s!' %(client.name, response)
    except:
        pass
    return msg

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
    if inputStr is not None and inputStr != '':
        return re.sub(r'\$([a-zA-Z]+)', r'%(\1)s', inputStr)
    else:
        return ''

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


"""
Calculate mean and standard deviation of data x[]:
    mean = {\sum_i x_i \over n}
    std = sqrt(\sum_i (x_i - mean)^2 \over n-1)
credit: http://www.physics.rutgers.edu/~masud/computing/WPark_recipes_in_python.html
"""
def meanstdv(x):
    from math import sqrt
    n, mean, std = len(x), 0, 0
    for a in x:
        mean = mean + a
    try:
        mean = mean / float(n)
    except ZeroDivisionError:
        mean = 0
    for a in x:
        std = std + (a - mean)**2
    try:
        std = sqrt(std / float(n-1))
    except ZeroDivisionError:
        std = 0
    return mean, std

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
    sanitized = re.sub(r'[\x00-\x1F]|[\x7F-\xff]', '?', s)
    return sanitized

#--------------------------------------------------------------------------------------------------
## @todo see if functions.executeSQL() and storage.DatabaseStorage.queryFromFile() can be combined.
def executeSql(db, file):
    """This method executes an external sql file on the current database
    A similar function can be found in storage.DatabaseStorage.queryFromFile()
    This one returns if a file is not found.
    """
    sqlFile = b3.getAbsolutePath(file)
    if os.path.exists(sqlFile):
        try:
            f = open(sqlFile, 'r')
        except Exception:
            return 'couldnotopen'
        sql_text = f.read()
        f.close()
        sql_statements = sql_text.split(';')
        for s in sql_statements:
            try:
                db.query(s)
            except Exception:
                pass
    else:
        return 'notfound'
    return 'success'
#--------------------------------------------------------------------------------------------------

