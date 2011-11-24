# -*- encoding: utf-8 -*-
#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2011 Thomas "Courgette" LÉVEIL <courgette@bigbrotherbot.net>
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
from exceptions import ValueError, IOError, Exception, KeyError
import json
import re
import string
import sys
import urllib2
from distutils import version
from types import StringType


## url from where we can get the latest B3 version number
URL_B3_LATEST_VERSION = 'http://master.bigbrotherbot.net/version.json'

# supported update channels
UPDATE_CHANNEL_STABLE = 'stable'
UPDATE_CHANNEL_BETA = 'beta'
UPDATE_CHANNEL_DEV = 'dev'



class B3version(version.StrictVersion):
        """
        Version numbering for BigBrotherBot.
        Compared to version.StrictVersion this class allows version numbers such as :
            1.0dev
            1.0dev2
            1.0a
            1.0a
            1.0a34
            1.0b
            1.0b1
            1.0b3
        And make sure that any 'dev' prerelease is inferior to any 'alpha' prerelease
        """

        version_re = re.compile(r'^(\d+) \. (\d+) (\. (\d+))? (([ab]|dev)(\d+)?)?$',
                                re.VERBOSE)
        prerelease_order = {'dev': 0, 'a': 1, 'b': 2}


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
                self.prerelease = (prerelease, string.atoi(prerelease_num if prerelease_num else '0'))
            else:
                self.prerelease = None


        def __cmp__ (self, other):
            if isinstance(other, StringType):
                other = B3version(other)

            compare = cmp(self.version, other.version)
            if compare == 0:              # have to compare prerelease

                # case 1: neither has prerelease; they're equal
                # case 2: self has prerelease, other doesn't; other is greater
                # case 3: self doesn't have prerelease, other does: self is greater
                # case 4: both have prerelease: must compare them!

                if not self.prerelease and not other.prerelease:
                    return 0
                elif self.prerelease and not other.prerelease:
                    return -1
                elif not self.prerelease and other.prerelease:
                    return 1
                elif self.prerelease and other.prerelease:
                    return cmp((self.prerelease_order[self.prerelease[0]], self.prerelease[1]),
                        (self.prerelease_order[other.prerelease[0]], other.prerelease[1]))

            else:                           # numeric versions don't match --
                return compare              # prerelease stuff doesn't matter

def getDefaultChannel(currentVersion):
    if currentVersion is None:
        return UPDATE_CHANNEL_STABLE
    m = re.match(r'^\d+\.\d+(\.\d+)?(?i)(?P<prerelease>[ab]|dev)\d*$', currentVersion)
    if not m:
        return UPDATE_CHANNEL_STABLE
    elif m.group('prerelease').lower() in ('dev', 'a'):
        return UPDATE_CHANNEL_DEV
    elif m.group('prerelease').lower() == 'b':
        return UPDATE_CHANNEL_BETA


def checkUpdate(currentVersion, channel=None, singleLine=True, showErrormsg=False, timeout=4):
    """
    check if an update of B3 is available

    """

    if channel is None:
        channel = getDefaultChannel(currentVersion)

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


