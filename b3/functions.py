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

__author__    = 'ThorN, xlr8or'
__version__   = '1.3.2'

import re, sys, imp, string, urllib2
from lib.elementtree import ElementTree
from distutils import version

## url from where we can get the latest B3 version number
URL_B3_LATEST_VERSION = 'http://www.bigbrotherbot.net/version.xml'


def getModule(name):
    mod = __import__(name)
    components = name.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod

def checkUpdate(currentVersion, singleLine=True, showErrormsg=False):
    """
    check if an update of B3 is available
    """
    timeout = 5
    ## urllib2.urlopen support the timeout argument only from 2.6... too bad
    ## instead we alter the default socket timeout
    import socket
    original_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(timeout)
    
    if not singleLine:
        sys.stdout.write("checking for updates... \n")

    message = None
    errorMessage = None
    try:
        f = urllib2.urlopen(URL_B3_LATEST_VERSION)
        _xml = ElementTree.parse(f)
        latestVersion = _xml.getroot().text
        not singleLine and sys.stdout.write("latest B3 version is %s\n" % latestVersion)
        _lver = version.LooseVersion(latestVersion)
        _cver = version.LooseVersion(currentVersion)
        if _cver < _lver:
            if singleLine:
                message = "*** NOTICE: A newer version of B3 is available. See www.bigbrotherbot.net! ***"
            else:
                message = """
         _\|/_
         (o o)
 +----oOO-{_}-OOo---------------------+
 |                                    |
 |                                    |
 | A newer version of B3 is available |
 |     See www.bigbrotherbot.net      |
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
    except Exception, e:
        errorMessage = "%s" % e
    finally:
        socket.setdefaulttimeout(original_timeout)
        
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
    
    import unittest, time
    
    class TestSpliDSN(unittest.TestCase):
        def assertDsnEqual(self, url, expected):
            tmp = splitDSN(url)
            self.assertEqual(tmp, expected)
    
        def test_sqlite(self):
            self.assertDsnEqual('sqlite://c|/mydatabase/test.db', 
            {'protocol': 'sqlite', 'host': 'c|', 'user': None, 
            'path': '/mydatabase/test.db', 'password': None, 'port': None })
    
        def test_ftp(self):
            self.assertDsnEqual('ftp://username@domain.com/index.html', 
            {'protocol': 'ftp', 'host': 'domain.com', 'user': 'username', 
             'path': '/index.html', 'password': None, 'port': None })
            
        def test_ftp2(self):
            self.assertDsnEqual('ftp://username:password@domain.com/index.html', 
            {'protocol': 'ftp', 'host': 'domain.com', 'user': 'username', 
             'path': '/index.html', 'password': 'password', 'port': None })
            
        def test_ftp3(self):
            self.assertDsnEqual('ftp://username@domain.com:password@domain.com/index.html', 
            {'protocol': 'ftp', 'host': 'domain.com', 'user': 'username@domain.com', 
             'path': '/index.html', 'password': 'password', 'port': None })
            
        def test_mysql(self):
            self.assertDsnEqual('mysql://b3:password@localhost/b3', 
            {'protocol': 'mysql', 'host': 'localhost', 'user': 'b3', 
             'path': '/b3', 'password': 'password', 'port': 3306} )
            
    class TestFuzziGuidMatch(unittest.TestCase):
        def test_1(self):
            self.assertTrue(fuzzyGuidMatch( '098f6bcd4621d373cade4e832627b4f6', '098f6bcd4621d373cade4e832627b4f6'))
            self.assertTrue(fuzzyGuidMatch( '098f6bcd4621d373cade4e832627b4f6', '098f6bcd4621d373cade4e832627b4f'))
            self.assertTrue(fuzzyGuidMatch( '098f6bcd4621d373cade4e832627b4f6', '098f6bcd4621d373cde4e832627b4f6'))
            self.assertTrue(fuzzyGuidMatch( '098f6bcd4621d373cade4e832627bf6',  '098f6bcd4621d373cade4e832627b4f6'))
            self.assertFalse(fuzzyGuidMatch('098f6bcd4621d373cade4e832627b4f6', '098f6bcd46d373cade4e832627b4f6'))
            self.assertFalse(fuzzyGuidMatch('098f6bcd4621d373cade4832627b4f6',  '098f6bcd4621d73cade4e832627b4f6'))
        
        def test_caseInsensitive(self):
            self.assertTrue(fuzzyGuidMatch( '098F6BCD4621D373CADE4E832627B4F6', '098f6bcd4621d373cade4e832627b4f6'))
            self.assertTrue(fuzzyGuidMatch( '098F6BCD4621D373CADE4E832627B4F6', '098f6bcd4621d373cade4e832627b4f'))
            self.assertTrue(fuzzyGuidMatch( '098F6BCD4621D373CADE4E832627B4F6', '098f6bcd4621d373cde4e832627b4f6'))
            self.assertFalse(fuzzyGuidMatch('098F6BCD4621D373CADE4E832627B4F6', '098f6bcd46d373cade4e832627b4f6'))
            self.assertTrue(fuzzyGuidMatch( '098F6BCD4621D373CADE4E832627BF6', '098f6bcd4621d373cade4e832627b4f6'))
            self.assertFalse(fuzzyGuidMatch('098F6BCD4621D373CADE4832627B4F6', '098f6bcd4621d73cade4e832627b4f6'))
            
    class TestMinutes2int(unittest.TestCase):
        def test_NaN(self):
            self.assertEqual(minutes2int('mlkj'), 0)
            self.assertEqual(minutes2int(''), 0)
            self.assertEqual(minutes2int('50,654'), 0)
        def test_int(self):
            self.assertEqual(minutes2int('50'), 50)
            self.assertEqual(minutes2int('50.654'), 50.65)
          
    class TestTime2minutes(unittest.TestCase):
        def test_None(self):
            self.assertEqual(time2minutes(None), 0)
        def test_int(self):
            self.assertEqual(time2minutes(0), 0)
            self.assertEqual(time2minutes(1), 1)
            self.assertEqual(time2minutes(154), 154)
        def test_str(self):
            self.assertEqual(time2minutes(''), 0)
        def test_str_h(self):
            self.assertEqual(time2minutes('145h'), 145*60)
            self.assertEqual(time2minutes('0 h'), 0)
            self.assertEqual(time2minutes('0    h'), 0)
            self.assertEqual(time2minutes('5h'), 5*60)
        def test_str_m(self):
            self.assertEqual(time2minutes('145m'), 145)
            self.assertEqual(time2minutes('0 m'), 0)
            self.assertEqual(time2minutes('0    m'), 0)
            self.assertEqual(time2minutes('5m'), 5)
        def test_str_s(self):
            self.assertEqual(time2minutes('0 s'), 0)
            self.assertEqual(time2minutes('0    s'), 0)
            self.assertEqual(time2minutes('60s'), 1)
            self.assertEqual(time2minutes('120s'), 2)
            self.assertEqual(time2minutes('5s'), 5.0/60)
            self.assertEqual(time2minutes('90s'), 1.5)
        def test_str_d(self):
            self.assertEqual(time2minutes('0 d'), 0)
            self.assertEqual(time2minutes('0    d'), 0)
            self.assertEqual(time2minutes('60d'), 60*24*60)
            self.assertEqual(time2minutes('120d'), 120*24*60)
            self.assertEqual(time2minutes('5d'), 5*24*60)
            self.assertEqual(time2minutes('90d'), 90*24*60)
        def test_str_w(self):
            self.assertEqual(time2minutes('0 w'), 0)
            self.assertEqual(time2minutes('0    w'), 0)
            self.assertEqual(time2minutes('60w'), 60*7*24*60)
            self.assertEqual(time2minutes('120w'), 120*7*24*60)
            self.assertEqual(time2minutes('5w'), 5*7*24*60)
            self.assertEqual(time2minutes('90w'), 90*7*24*60)

    class TestCheckUpdate(unittest.TestCase):
        _time_start = 0
        def setUp(self):
            self._time_start = time.time()
        def tearDown(self):
            ms = ((time.time() - self._time_start)*1000)
            print "test took %0.1f ms" % ms
            self.assertTrue(ms < 5500, "Test exceeded timeout")
        def test_1(self):
            self.assertNotEqual(None, checkUpdate('1.2', False, True))
        def test_2(self):
            self.assertNotEqual(None, checkUpdate('1.4', False, True))
        def test_3(self):
            self.assertEqual(None, checkUpdate('1.4.1', False, True))
        def test_4(self):
            sys.modules[__name__].URL_B3_LATEST_VERSION = 'http://no.where.lol/'
            self.assertNotEqual(None, checkUpdate('1.2', False, True))
        def test_5(self):
            sys.modules[__name__].URL_B3_LATEST_VERSION = 'http://localhost:9000/'
            self.assertNotEqual(None, checkUpdate('1.2', False, True))
    
    #unittest.main()
    mytests = unittest.TestLoader().loadTestsFromTestCase(TestCheckUpdate)
    unittest.TextTestRunner().run(mytests)

