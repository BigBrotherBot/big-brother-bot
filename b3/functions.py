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
# 17/06/2012 - 1.5   - Courgette - add getStuffSoundingLike()
# 19/10/2012 - 1.6   - Courgette - improve getStuffSoundingLike() so it discards non letter/digit characters
# 20/10/2012 - 1.7   - Courgette - fix soundex() error when input string is unicode
# 26/11/2012 - 1.8   - Courgette - add hash_password()
#
__author__    = 'ThorN, xlr8or'
__version__   = '1.8'

import b3
import re
import os
import sys
import imp
import string
import urllib2
from hashlib import md5
import collections


def getModule(name):
    mod = __import__(name)
    components = name.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod




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
    mins = float(time2minutes(timeStr))

    if mins < 1:
        num = round(mins * 60, 1)
        s = '%s second'
    elif mins < 60:
        num = round(mins, 1)
        s = '%s minute'
    elif mins < 1440:
        num = round(mins / 60, 1)
        s = '%s hour'
    elif mins < 10080:
        num = round((mins / 60) / 24, 1)
        s = '%s day'
    elif mins < 525600:
        num = round(((mins / 60) / 24) / 7, 1)
        s = '%s week'
    else:
        num = round(((mins / 60) / 24) / 365, 1)
        s = '%s year'

    # convert to int if num is whole
    num = int(num) if num%1==0 else num

    if num >= 2:
        s += 's'

    return s % num

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
    str = string.translate(str.encode('ascii', 'ignore'), TABLE, IGNORE)
    if not str:
        return "Z000"
    prev = str[0]
    for x in str[1:]:
        if x != prev and x != "0":
                str2 = str2 + x
        prev = x
    # pad with zeros
    str2 += "0000"
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
    if s:
        return re.sub(r'[\x00-\x1F]|[\x7F-\xff]', '?', s)
    else:
        return ''

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


def getStuffSoundingLike(stuff, expected_stuff):
    """found matching stuff for the given expected_stuff list.
    If no exact match is found, then return close candidates using by substring match.
    If no subtring matches, then use soundex and then LevenshteinDistance algorithms
    """
    re_not_text = re.compile("[^a-z0-9]", re.IGNORECASE)
    def clean(txt):
        return re.sub(re_not_text, '', txt.lower())
    clean_stuff = clean(stuff)
    soundex1 = soundex(stuff)

    clean_expected_stuff = dict()
    for i in expected_stuff:
        clean_expected_stuff[clean(i)] = i

    match = []
    # given stuff could be the exact match
    if stuff in expected_stuff:
        match = [stuff]
    elif clean_stuff in clean_expected_stuff:
        match = [clean_expected_stuff[clean_stuff]]
    else:
        # stuff could be a substring of one of the expected value
        matching_subset = filter(lambda x: x.lower().find(clean_stuff) >= 0, clean_expected_stuff.keys())
        if len(matching_subset) == 1:
            match = [clean_expected_stuff[matching_subset[0]]]
        elif len(matching_subset) > 1:
            match = [clean_expected_stuff[i] for i in matching_subset]
        else:
            # no luck with subset lookup, fallback on soundex magic
            for m in clean_expected_stuff.keys():
                s = soundex(m)
                if s == soundex1:
                    match.append(clean_expected_stuff[m])

    if not len(match):
        match = expected_stuff
        match.sort(key=lambda _map: levenshteinDistance(clean_stuff, _map.strip()))
    return match


def hash_password(password):
    return md5(password).hexdigest()

# simplified spell checker from Peter Norvig
# http://www.norvig.com/spell-correct.html
def corrent_spell(c_word, wordbook):

    def words(text): return re.findall('[a-z]+', text.lower())

    def train(features):
        model = collections.defaultdict(lambda: 1)
        for f in features:
            model[f] += 1
        return model

    NWORDS = train(words(wordbook))

    alphabet = 'abcdefghijklmnopqrstuvwxyz'

    def edits1(word):
        splits     = [(word[:i], word[i:]) for i in range(len(word) + 1)]
        deletes    = [a + b[1:] for a, b in splits if b]
        transposes = [a + b[1] + b[0] + b[2:] for a, b in splits if len(b)>1]
        replaces   = [a + c + b[1:] for a, b in splits for c in alphabet if b]
        inserts    = [a + c + b     for a, b in splits for c in alphabet]
        return set(deletes + transposes + replaces + inserts)

    def known_edits2(word):
        return set(e2 for e1 in edits1(word) for e2 in edits1(e1) if e2 in NWORDS)

    def known(words): return set(w for w in words if w in NWORDS)

    def correct(word):
        candidates = known([word]) or known(edits1(word)) or known_edits2(word) or [word]
        return max(candidates, key=NWORDS.get)

    result = correct(c_word)
    if result == c_word:
        result = False

    return result

