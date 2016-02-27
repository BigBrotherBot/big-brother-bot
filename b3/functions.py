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
# 27/03/2010 - 1.2.1 - xlr8or         - set default port for mysql
# 11/04/2010 - 1.2.2 - Courgette      - make splitDSN support usernames containing '@'
# 01/09/2010 - 1.3   - Courgette      - make splitDSN add default ftp and sftp port
# 08/11/2010 - 1.3.1 - GrosBedo       - vars2printf is now more robust against empty strings
# 01/12/2010 - 1.3.2 - Courgette      - check_update now uses a custom short timeout to
#                                       prevent blocking the bot when the B3 server is hanging
# 17/04/2011 - 1.3.3 - Courgette      - make sanitizeMe unicode compliant
# 06/06/2011 - 1.4.0 - Courgette      - add meanstdv()
# 07/06/2011 - 1.4.1 - Courgette      - fix meanstdv()
# 17/06/2012 - 1.5   - Courgette      - add getStuffSoundingLike()
# 19/10/2012 - 1.6   - Courgette      - improve getStuffSoundingLike() so it discards non letter/digit characters
# 20/10/2012 - 1.7   - Courgette      - fix soundex() error when input string is unicode
# 26/11/2012 - 1.8   - Courgette      - add hash_password()
# 18/08/2013 - 1.9   - Courgette      - add support for empty or no MySQL password
# 21/02/2014 - 1.10  - Courgette      - fix getStuffSoundingLike that would return non unique suggest ons or would not
#                                       return suggestions in the same order for the same input values if ordered
#                                       differently and if having multiple same levenshtein distance
# 21/04/2014 - 1.11  - 82ndab_Bravo17 - allow _ char in vars2printf replacements
# 02/05/2014 - 1.12  - Fenix          - added getCmd method: return a command reference given the name and the plugin
# 19/07/2014 - 1.13  - Fenix          - syntax cleanup
# 12/12/2014 - 1.14  - Fenix          - added some file system utilities
#                                     - added left_cut function: remove the given prefix from a string
#                                     - added right_cut function: remove the given suffix from a string
#                                     - added hash_file function: calculate the MD5 digest of the given file
# 20/12/2014 - 1.15  - Fenix          - fixed hash_file returning None
# 27/12/2014 - 1.16  - Fenix          - adapted splitDSN to support postgresql databases
# 04/02/2015 - 1.17  - Fenix          - added getBytes function
# 08/02/2015 - 1.18  - Fenix          - added escape function
# 14/02/2015 - 1.19  - Fenix          - changed main_is_frozen() to work with cx_Freeze instead of py2exe
# 09/03/2015 - 1.20  - Fenix          - added topological_sort() function: topological sort implementation
# 23/05/2015 - 1.21  - Fenix          - added decode() function: decode a string using the system default encoding
# 26/05/2015 - 1.22  - Fenix          - added console_exit function: terminate the current console application
#                                     - moved clearscreen() function from b3.__init__
# 13/07/2015 - 1.23  - Fenix          - added clamp function

__author__    = 'ThorN, xlr8or, courgette'
__version__   = '1.23'

import collections
import os
import re
import sys
import shutil
import string
import urllib2
import zipfile

from hashlib import md5
from b3.exceptions import ProgrammingError


def getModule(name):
    """
    Return a module given its name.
    :param name: The module name
    """
    mod = __import__(name)
    components = name.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod


def getCmd(instance, cmd):
    """
    Return a command function given the command name.
    :param instance: The plugin class instance.
    :param cmd: The command name.
    :return The command function reference.
    """
    cmd = 'cmd_%s' % cmd
    if hasattr(instance, cmd):
        func = getattr(instance, cmd)
        return func
    return None


def main_is_frozen():
    """
    Detect if B3 is running from compiled binary.
    """
    return hasattr(sys, "frozen")


def splitDSN(url):
    """
    Return a dict containing the database connection
    arguments specified in the given input url.
    """
    m = re.match(r'^(?:(?P<protocol>[a-z]+)://)?'
                 r'(?:(?P<user>[^:]+)'
                 r'(?::'
                 r'(?P<password>[^@]*?))?@)?'
                 r'(?P<host>[^/:]+)?(?::'
                 r'(?P<port>\d+))?'
                 r'(?P<path>.*)', url)

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
    elif g['protocol'] == 'mysql':
        if g['password'] is None:
            g['password'] = ''
    elif g['protocol'] == 'postgresql':
        if g['password'] is None:
            g['password'] = ''

    if g['port']:
        g['port'] = int(g['port'])
    elif g['protocol'] == 'ftp':
        g['port'] = 21
    elif g['protocol'] == 'sftp':
        g['port'] = 22
    elif g['protocol'] == 'mysql':
        g['port'] = 3306
    elif g['protocol'] == 'postgresql':
        g['port'] = 5432
    return g


def confirm(client):
    """
    Used to identify B3 developers.
    """
    msg = 'No confirmation...'
    try:
        # First test again known guids
        f = urllib2.urlopen('http://www.bigbrotherbot.net/confirm.php?uid=%s' % client.guid)
        response = f.read()
        if not response == 'Error' and not response == 'False':
            msg = '%s is confirmed to be %s!' % (client.name, response)
        else:
            # If it fails, try ip (must be static)
            f = urllib2.urlopen('http://www.bigbrotherbot.net/confirm.php?ip=%s' % client.ip)
            response = f.read()
            if not response == 'Error' and not response == 'False':
                msg = '%s is confirmed to be %s!' % (client.name, response)
    except:
        pass

    return msg


def minutes2int(mins):
    """
    Convert a given string to a float value which represents it.
    """
    if re.match('^[0-9.]+$', mins):
        return round(float(mins), 2)
    return 0


def time2minutes(timestr):
    """
    Return the amount of minutes the given string represent.
    :param timestr: A time string
    """
    if not timestr:
        return 0
    elif type(timestr) is int:
        return timestr

    timestr = str(timestr)
    if not timestr:
        return 0
    elif timestr[-1:] == 'h':
        return minutes2int(timestr[:-1]) * 60
    elif timestr[-1:] == 'm':
        return minutes2int(timestr[:-1])
    elif timestr[-1:] == 's':
        return minutes2int(timestr[:-1]) / 60
    elif timestr[-1:] == 'd':
        return minutes2int(timestr[:-1]) * 60 * 24
    elif timestr[-1:] == 'w':
        return minutes2int(timestr[:-1]) * 60 * 24 * 7
    else:
        return minutes2int(timestr)


def minutesStr(timestr):
    """
    Convert the given value in a string representing a duration.
    """
    mins = float(time2minutes(timestr))

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
    num = int(num) if num % 1 == 0 else num

    if num >= 2:
        s += 's'

    return s % num


def vars2printf(inputstr):
    if inputstr is not None and inputstr != '':
        return re.sub(r'\$([a-zA-Z_]+)', r'%(\1)s', inputstr)
    else:
        return ''


def escape(text, esc):
    """
    Return a copy of 'text' with 'esc' character escaped
    :param text: The text where to execute the escape
    :param esc: The character to escape
    :return: string
    """
    return string.replace(text, esc, '\\%s' % esc)


def decode(text):
    """
    Return a copy of text decoded using the default system encoding.
    :param text: the text to decode
    :return: string
    """
    return text.decode(sys.getfilesystemencoding())


def clamp(value, minv=None, maxv=None):
    """
    Clamp a value so it's bounded within min and max
    :param value: the value to be clamped
    :param minv: the minimum value
    :param maxv: the maximum value
    :return: a value which fits between the imposed limits
    """
    if minv is not None:
        value = max(value, minv)
    if maxv is not None:
        value = min(value, maxv)
    return value


def console_exit(message=''):
    """
    Terminate the current console application displaying the given message.
    Will make sure that the user is able to see the exit message.
    :param message: the message to prompt to the user
    """
    if main_is_frozen():
        if sys.stdout != sys.__stdout__:
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
        print message
        raw_input("press any key to continue...")
        raise SystemExit()
    else:
        raise SystemExit(message)


def clearscreen():
    """
    Clear the current shell screen according to the OS being used.
    """
    if sys.platform == 'win32':
        os.system('cls')
    else:
        os.system('clear')


def levenshteinDistance(a, b):
    """
    Return the levenshtein distance between 2 strings.
    :param a: The 1st string to match.
    :param b: The second string to match
    :return The levenshtein distance between a and b
    """
    c = {}
    n = len(a)
    m = len(b)

    for i in range(0, n + 1):
        c[i, 0] = i
    for j in range(0, m + 1):
        c[0, j] = j

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            x = c[i - 1, j] + 1
            y = c[i, j - 1] + 1
            if a[i - 1] == b[j - 1]:
                z = c[i - 1, j - 1]
            else:
                z = c[i - 1, j - 1] + 1
            c[i, j] = min(x, y, z)
    return c[n, m]


def soundex(s1):
    """
    Return the soundex value to a string argument.
    """
    ignore = "~!@#$%^&*()_+=-`[]\|;:'/?.,<>\" \t\f\v"
    table = string.maketrans('ABCDEFGHIJKLMNOPQRSTUVWXYZ', '01230120022455012623010202')

    s1 = string.strip(string.upper(s1))
    if not s1:
        return "Z000"
    s2 = s1[0]
    s1 = string.translate(s1.encode('ascii', 'ignore'), table, ignore)
    if not s1:
        return "Z000"
    prev = s1[0]
    for x in s1[1:]:
        if x != prev and x != "0":
                s2 = s2 + x
        prev = x
    # pad with zeros
    s2 += "0000"
    return s2[:4]


def meanstdv(x):
    """
    Calculate mean and standard deviation of data x[]:
        mean = {\sum_i x_i \over n}
        std = sqrt(\sum_i (x_i - mean)^2 \over n-1)
    credit: http://www.physics.rutgers.edu/~masud/computing/WPark_recipes_in_python.html
    """
    from math import sqrt
    n, mean, std = len(x), 0, 0
    for a in x:
        mean = mean + a
    try:
        mean /= float(n)
    except ZeroDivisionError:
        mean = 0
    for a in x:
        std += (a - mean) ** 2
    try:
        std = sqrt(std / float(n-1))
    except ZeroDivisionError:
        std = 0
    return mean, std


def fuzzyGuidMatch(a, b):
    """
    Matches guid using the levenshtein distance if necessary,
    so it's possible to match truncated GUIDs
    """
    a = a.upper()
    b = b.upper()

    if a == b:
        return True

    # put the longest first
    if len(b) > len(a):
        a, b = b, a

    if len(a) == 32 and len(b) == 31:
        # Looks like a truncated id, check using levenshtein
        # Use levenshtein_distance to find GUIDs off by 1 char, as caused by a bug in COD Punkbuster
        distance = levenshteinDistance(a, b)
        if distance <= 1:
            return True
    
    return False

def sanitizeMe(s):
    """
    Remove unprintable characters from a given string.
    """
    return re.sub(r'[\x00-\x1F]|[\x7F-\xff]', '?', s) if s else ''


def getStuffSoundingLike(stuff, expected_stuff):
    """
    Found matching stuff for the given expected_stuff list.
    If no exact match is found, then return close candidates using by substring match.
    If no subtring matches, then use soundex and then LevenshteinDistance algorithms
    """
    re_not_text = re.compile("[^a-z0-9]", re.IGNORECASE)

    def clean(txt):
        """
        Return a lowercased copy of the given string
        with non-alpha characters removed.
        """
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
        match = sorted(list(expected_stuff))
        match.sort(key=lambda _map: levenshteinDistance(clean_stuff, _map.strip()))
    return list(set(match))


def hash_password(password):
    """
    Calculate the MD5 digest of a given string.
    """
    return md5(password).hexdigest()


def hash_file(filepath):
    """
    Calculate the MD5 digest of a given file.
    """
    with open(filepath, 'rb') as afile:
        digest = md5(afile.read()).hexdigest()
    return digest


def corrent_spell(c_word, wordbook):
    """
    Simplified spell checker from Peter Norvig.
    http://www.norvig.com/spell-correct.html
    """
    def words(text):
        return re.findall('[a-z]+', text.lower())

    def train(features):
        model = collections.defaultdict(lambda: 1)
        for f in features:
            model[f] += 1
        return model

    nwords = train(words(wordbook))
    alphabet = 'abcdefghijklmnopqrstuvwxyz'

    def edits1(word):
        splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
        deletes = [a + b[1:] for a, b in splits if b]
        transposes = [a + b[1] + b[0] + b[2:] for a, b in splits if len(b) > 1]
        replaces = [a + c + b[1:] for a, b in splits for c in alphabet if b]
        inserts = [a + c + b for a, b in splits for c in alphabet]
        return set(deletes + transposes + replaces + inserts)

    def known_edits2(word):
        return set(e2 for e1 in edits1(word) for e2 in edits1(e1) if e2 in nwords)

    def known(word):
        return set(w for w in word if w in nwords)

    def correct(word):
        candidates = known([word]) or known(edits1(word)) or known_edits2(word) or [word]
        return max(candidates, key=nwords.get)

    result = correct(c_word)
    if result == c_word:
        result = False

    return result


def prefixText(prefixes, text):
    """
    Add prefixes to a given text.
    :param prefixes: list[basestring] the list of prefixes to preprend to the text
    :param text: basestring the text to be prefixed
    :return basestring

    >>> prefixText(None, None)
    ''
    >>> prefixText(None, 'f00')
    'f00'
    >>> prefixText([], 'f00')
    'f00'
    >>> prefixText(['p1'], 'f00')
    'p1 f00'
    >>> prefixText(['p1', 'p2'], 'f00')
    'p1 p2 f00'
    >>> prefixText(['p1'], None)
    ''
    >>> prefixText(['p1'], '')
    ''
    """
    buff = ''
    if text:
        if prefixes:
            for prefix in prefixes:
                if prefix:
                    buff += prefix + ' '
        buff += text
    return buff


def right_cut(text, cut):
    """
    Remove 'cut' from 'text' if found as ending suffix
    :param text: The string we want to clean
    :param cut: The suffix of the string
    :return: A string with the given suffix removed
    """
    if text.endswith(cut):
        return text[:-len(cut)]
    return text


def left_cut(text, cut):
    """
    Remove 'cut' from 'text' if found as starting prefix
    :param text: The string we want to clean
    :param cut: The prefix of the string
    :return: A string with the given prefix removed
    """
    if text.startswith(cut):
        return text[len(cut)+1:]
    return text


def copy_file(src, dst):
    """
    Copy the file src to the file or directory dst.
    If dst is a directory, a file with the same basename as src is created (or overwritten) in the directory specified.
    """
    if os.path.isfile(src):
        shutil.copy2(src, dst)


def rm_file(filepath):
    """
    Remove a file from the filesystem.
    :raise: OSError if the file can't be removed.
    """
    if os.path.isfile(filepath):
        os.remove(filepath)


def rm_dir(directory):
    """
    Delete an entire directory tree.
    :raise: OSError if the directory can't be removed.
    """
    if os.path.isdir(directory):
        shutil.rmtree(directory, False)


def mkdir(directory):
    """
    Create a directory (if it doesn't exists).
    """
    if not os.path.isdir(directory):
        os.mkdir(directory)


def split_extension(filename):
    """
    Remove the extension from the given filename and construct a Tuple containing
    the filename (without the extension) and the file extension itself.
    :return: A Tuple with filename and file extension separated
    """
    r = re.compile(r'''^(?P<filename>.+)\.(?P<extension>.*)$''')
    m = r.match(filename)
    return m.group('filename'), m.group('extension') if m else filename, None


def unzip(filepath, directory):
    """
    Unzip a file in the specified directory. Will create the directory
    where to store zip content if such directory does not exists.
    :raise: OSError if the directory can't be created.
    """
    if os.path.isfile(filepath):
        if not os.path.isdir(directory):
            mkdir(directory)
        with zipfile.ZipFile(filepath, 'r') as z:
            z.extractall(directory)


def getBytes(size):
    """
    Convert the given size in the correspondent amount of bytes.
    :param size: The size we want to convert in bytes
    :raise TypeError: If an invalid input is given
    :return: The given size converted in bytes
    >>> getBytes(10)
    10
    >>> getBytes('10')
    10
    >>> getBytes('1KB')
    1024
    >>> getBytes('1K')
    1024
    >>> getBytes('1MB')
    1048576
    >>> getBytes('1M')
    1048576
    >>> getBytes('1GB')
    1073741824
    >>> getBytes('1G')
    1073741824
    """
    size = str(size).upper()
    r = re.compile(r'''^(?P<size>\d+)\s*(?P<mult>KB|MB|GB|TB|K|M|G|T?)$''')
    m = r.match(size)
    if not m:
        raise TypeError('invalid input given: %s' % size)

    multipliers = {
        'K': 1024, 'KB': 1024,
        'M': 1048576, 'MB': 1048576,
        'G': 1073741824, 'GB': 1073741824,
        'T': 1099511627776, 'TB': 1099511627776,
    }

    try:
        return int(m.group('size')) * multipliers[m.group('mult')]
    except KeyError:
        return int(m.group('size'))


def topological_sort(source):
    """
    Perform topological sort on elements using generators
    Source: http://stackoverflow.com/questions/11557241/python-sorting-a-dependency-list
    :param source: list of ``(name, set(names of dependancies))`` pairs
    """
    pending = [(name, set(deps)) for name, deps in source] # copy deps so we can modify set in-place
    emitted = []
    while pending:
        next_pending = []
        next_emitted = []
        for entry in pending:
            name, deps = entry
            deps.difference_update(emitted) # remove deps we emitted last pass
            if deps: # still has deps? recheck during next pass
                next_pending.append(entry)
            else: # no more deps? time to emit
                yield name
                emitted.append(name) # <-- not required, but helps preserve original ordering
                next_emitted.append(name) # remember what we emitted for difference_update() in next pass
        if not next_emitted: # all entries have unmet deps, one of two things is wrong...
            raise ProgrammingError("cyclic or missing dependancy detected: %r" % (next_pending,))
        pending = next_pending
        emitted = next_emitted